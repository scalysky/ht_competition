[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$envFile = Join-Path $repoRoot '.env'
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$queryFile = Join-Path $PSScriptRoot 'gold_queries.json'
$reportFile = Join-Path $PSScriptRoot '..\eval_runs\competition_gold_validation.json'

if (-not (Test-Path -LiteralPath $psql)) {
    throw "psql was not found: $psql"
}
if (-not (Test-Path -LiteralPath $envFile)) {
    throw ".env was not found: $envFile"
}

$config = @{}
foreach ($rawLine in Get-Content -LiteralPath $envFile -Encoding UTF8) {
    $line = $rawLine.Trim()
    if (-not $line -or $line.StartsWith('#') -or -not $line.Contains('=')) {
        continue
    }
    $parts = $line.Split('=', 2)
    $config[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
}

$required = @('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD')
$missing = @($required | Where-Object { -not $config[$_] })
if ($missing.Count -gt 0) {
    throw "Missing .env settings: $($missing -join ', ')"
}

$oldEnvironment = @{}
$managedNames = @(
    'PGPASSWORD', 'PGSSLMODE', 'PGCLIENTENCODING', 'PGCONNECT_TIMEOUT', 'PGOPTIONS'
)
foreach ($name in $managedNames) {
    $oldEnvironment[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
}

function Invoke-PsqlQuery {
    param([Parameter(Mandatory)] [string] $Sql)

    $output = & $psql -X -q -A -t `
        -h $config['PGHOST'] `
        -p $config['PGPORT'] `
        -U $config['PGUSER'] `
        -d $config['PGDATABASE'] `
        -v ON_ERROR_STOP=1 `
        -c $Sql 2>&1
    return [PSCustomObject]@{
        ExitCode = $LASTEXITCODE
        Output = @($output)
    }
}

try {
    $env:PGPASSWORD = $config['PGPASSWORD']
    $env:PGSSLMODE = if ($config['PGSSLMODE']) { $config['PGSSLMODE'] } else { 'prefer' }
    $env:PGCLIENTENCODING = if ($config['PGCLIENTENCODING']) { $config['PGCLIENTENCODING'] } else { 'UTF8' }
    $env:PGCONNECT_TIMEOUT = if ($config['PGCONNECT_TIMEOUT']) { $config['PGCONNECT_TIMEOUT'] } else { '10' }
    $timeoutMs = if ($config['PGSTATEMENT_TIMEOUT_MS']) { $config['PGSTATEMENT_TIMEOUT_MS'] } else { '30000' }
    $env:PGOPTIONS = "-c default_transaction_read_only=on -c statement_timeout=$timeoutMs"

    $identity = Invoke-PsqlQuery -Sql @"
SELECT current_user || '|' || current_database() || '|' ||
       current_setting('default_transaction_read_only') || '|' ||
       current_setting('statement_timeout');
"@
    if ($identity.ExitCode -ne 0) {
        throw "Connection check failed: $($identity.Output -join ' ')"
    }
    Write-Host "Connection: $($identity.Output[-1])" -ForegroundColor Green

    $permissionCheck = Invoke-PsqlQuery -Sql @"
SELECT count(*)
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'ads_cust_info_d', 'dim_branch', 'dim_product', 'dim_public',
      'dwd_cust_hold_d', 'dwd_cust_tran_d', 'dws_cust_aset_d', 'dws_cust_fin_d'
  )
  AND has_table_privilege(
      current_user,
      format('%I.%I', table_schema, table_name),
      'SELECT'
  )
  AND NOT has_table_privilege(
      current_user,
      format('%I.%I', table_schema, table_name),
      'INSERT,UPDATE,DELETE,TRUNCATE'
  );
"@
    if ($permissionCheck.ExitCode -ne 0 -or $permissionCheck.Output[-1].Trim() -ne '8') {
        throw "Read-only permission check failed: $($permissionCheck.Output -join ' ')"
    }
    Write-Host 'Permissions: 8/8 tables are SELECT-only' -ForegroundColor Green

    $queries = Get-Content -LiteralPath $queryFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $results = @()
    foreach ($query in $queries) {
        $sqlText = $query.sql.Trim().TrimEnd(';')
        $wrappedSql = "SELECT count(*) FROM ($sqlText) AS _gold_query;"
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        $execution = Invoke-PsqlQuery -Sql $wrappedSql
        $stopwatch.Stop()

        $status = if ($execution.ExitCode -eq 0) { 'ok' } else { 'error' }
        $rowCount = if ($status -eq 'ok') { [long]$execution.Output[-1].Trim() } else { $null }
        $errorText = if ($status -eq 'error') { $execution.Output -join [Environment]::NewLine } else { $null }
        $result = [PSCustomObject]@{
            id = [int]$query.id
            question = [string]$query.question
            status = $status
            row_count = $rowCount
            elapsed_ms = [Math]::Round($stopwatch.Elapsed.TotalMilliseconds, 2)
            error = $errorText
        }
        $results += $result

        $marker = if ($status -eq 'ok') { 'PASS' } else { 'FAIL' }
        Write-Host "[$marker] #$($result.id) rows=$rowCount time=$($result.elapsed_ms)ms"
        if ($errorText) {
            Write-Host $errorText -ForegroundColor Red
        }
    }

    $reportDirectory = Split-Path -Parent $reportFile
    New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
    $results | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $reportFile -Encoding UTF8
    $passed = @($results | Where-Object { $_.status -eq 'ok' }).Count
    Write-Host "`nGold SQL validation: $passed/$($results.Count) passed"
    Write-Host "Report: $reportFile"
    if ($passed -ne $results.Count) {
        exit 1
    }
}
finally {
    foreach ($name in $managedNames) {
        [Environment]::SetEnvironmentVariable($name, $oldEnvironment[$name], 'Process')
    }
}
