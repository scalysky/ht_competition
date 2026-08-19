# psql_ro.ps1 — 无 at2s 基线专用只读 PostgreSQL 封装
# 用法：.\psql_ro.ps1 [-Sql <string>] [-File <path>] [-MaxRows <int>]

[CmdletBinding()]
param(
    [Parameter(ParameterSetName = "sql")] [string]$Sql,
    [Parameter(ParameterSetName = "file")] [string]$File,
    [int]$MaxRows = 100
)

$ErrorActionPreference = "Stop"

function Get-EnvFile {
    param([string]$Path)
    $vars = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $t = $line.Trim()
        if ($t -eq "" -or $t.StartsWith("#")) { continue }
        if ($t -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') { continue }
        $key = $Matches[1]
        $value = $Matches[2].Trim()
        if ($value.Length -ge 2 -and $value.StartsWith('"') -and $value.EndsWith('"')) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        $vars[$key] = $value
    }
    $vars
}

$workspaceRoot = [System.IO.Path]::GetFullPath((Get-Location).Path)
$workspacePrefix = $workspaceRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$envPath = Join-Path $workspaceRoot '.env'
$tempRoot = Join-Path $workspaceRoot 'generated\.tmp'
$scriptRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)

if (-not ($scriptRoot -eq $workspaceRoot -or $scriptRoot.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "Run this wrapper from the model workspace that contains it: $scriptRoot"
}
if (-not (Test-Path -LiteralPath $envPath -PathType Leaf)) {
    throw "Missing .env in current model workspace: $envPath"
}

$envVars = Get-EnvFile -Path $envPath
foreach ($key in "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD") {
    if (-not $envVars.ContainsKey($key)) { throw "missing $key in $envPath" }
}

$env:PGHOST = $envVars["PGHOST"]
$env:PGPORT = $envVars["PGPORT"]
$env:PGDATABASE = $envVars["PGDATABASE"]
$env:PGUSER = $envVars["PGUSER"]
$env:PGPASSWORD = $envVars["PGPASSWORD"]
if ($envVars.ContainsKey("PGSSLMODE")) { $env:PGSSLMODE = $envVars["PGSSLMODE"] }
if ($envVars.ContainsKey("PGCLIENTENCODING")) { $env:PGCLIENTENCODING = $envVars["PGCLIENTENCODING"] }
if ($envVars.ContainsKey("PGCONNECT_TIMEOUT")) { $env:PGCONNECT_TIMEOUT = $envVars["PGCONNECT_TIMEOUT"] }

$statementTimeout = if ($envVars.ContainsKey("PGSTATEMENT_TIMEOUT_MS")) {
    $envVars["PGSTATEMENT_TIMEOUT_MS"]
}
else {
    "30000"
}

$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path -LiteralPath $psql -PathType Leaf)) {
    throw "psql.exe does not exist: $psql"
}

$env:PGRRO_MAXROWS = "$MaxRows"
$sessionPrelude = @(
    "SET default_transaction_read_only = on;",
    "SET statement_timeout = $statementTimeout;",
    "SET search_path = public;"
) -join " "

if ($File) {
    $sourceFile = [System.IO.Path]::GetFullPath($File)
    if (-not $sourceFile.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "SQL file must be inside the current model workspace: $sourceFile"
    }
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "SQL file does not exist: $sourceFile"
    }

    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $temporarySql = Join-Path $tempRoot ("psql_ro_" + [guid]::NewGuid().ToString("N") + ".sql")
    try {
        $sessionPrelude | Set-Content -LiteralPath $temporarySql -Encoding UTF8
        Get-Content -LiteralPath $sourceFile | Add-Content -LiteralPath $temporarySql -Encoding UTF8
        & $psql -w -v ON_ERROR_STOP=1 -f $temporarySql
        $exitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item -LiteralPath $temporarySql -ErrorAction SilentlyContinue
    }
}
else {
    $command = @($sessionPrelude, $Sql) -join " "
    & $psql -w -v ON_ERROR_STOP=1 -c $command
    $exitCode = $LASTEXITCODE
}

exit $exitCode
