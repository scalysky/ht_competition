# psql_ro.ps1 — 只读 psql 封装（db-access 条目 pg-local）
# 用法：.\psql_ro.ps1 [-Sql <string>] [-File <path>] [-MaxRows <int>]
# 强制：会话只读（default_transaction_read_only=on）、语句超时、单次最多 MaxRows 行。

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
        $k = $Matches[1]
        $v = $Matches[2].Trim()
        if ($v.Length -ge 2 -and $v.StartsWith('"') -and $v.EndsWith('"')) { $v = $v.Substring(1, $v.Length - 2) }
        $vars[$k] = $v
    }
    $vars
}

$workspaceRoot = [System.IO.Path]::GetFullPath((Get-Location).Path)
$envRoot = Join-Path $workspaceRoot '.env'
$workspacePrefix = $workspaceRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
$tempRoot = Join-Path $workspaceRoot 'generated\.tmp'
$scriptRoot = [System.IO.Path]::GetFullPath($PSScriptRoot)
if (-not ($scriptRoot -eq $workspaceRoot -or $scriptRoot.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase))) {
    throw "Run this wrapper from the model workspace that contains it: $scriptRoot"
}
if (-not (Test-Path -LiteralPath $envRoot -PathType Leaf)) {
    throw "Missing .env in current model workspace: $envRoot"
}
$envVars = Get-EnvFile -Path $envRoot

foreach ($k in "PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD") {
    if (-not $envVars.ContainsKey($k)) { throw "missing $k in $envRoot" }
}

$env:PGHOST = $envVars["PGHOST"]
$env:PGPORT = $envVars["PGPORT"]
$env:PGDATABASE = $envVars["PGDATABASE"]
$env:PGUSER = $envVars["PGUSER"]
$env:PGPASSWORD = $envVars["PGPASSWORD"]
if ($envVars.ContainsKey("PGSSLMODE")) { $env:PGSSLMODE = $envVars["PGSSLMODE"] }
if ($envVars.ContainsKey("PGCLIENTENCODING")) { $env:PGCLIENTENCODING = $envVars["PGCLIENTENCODING"] }
if ($envVars.ContainsKey("PGCONNECT_TIMEOUT")) { $env:PGCONNECT_TIMEOUT = $envVars["PGCONNECT_TIMEOUT"] }

$stmtTimeout = if ($envVars.ContainsKey("PGSTATEMENT_TIMEOUT_MS")) { $envVars["PGSTATEMENT_TIMEOUT_MS"] } else { "30000" }

$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

# 启动参数：会话只读 + 超时 + 行数上限（LimitAll 为每查询最多 N 行，非 psql 标准，这里用通用方式：以 FETCH/limit 兜底）
# psql 无全局行数上限参数，通过 -R 不适用；行数上限由调用方在 SQL 中保证，此处以变量 PGRRO_MAXROWS 供 SQL 引用。
$env:PGRRO_MAXROWS = "$MaxRows"

$sessionPrelude = @(
    "SET default_transaction_read_only = on;",
    "SET statement_timeout = $stmtTimeout;",
    "SET search_path = public;"
) -join " "
$cmd = @($sessionPrelude, $Sql) -join " "

if ($File) {
    $sourceFile = [System.IO.Path]::GetFullPath($File)
    if (-not $sourceFile.StartsWith($workspacePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "SQL file must be inside the current model workspace: $sourceFile"
    }
    if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
        throw "SQL file does not exist: $sourceFile"
    }

    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
    $tmp = Join-Path $tempRoot ("psql_ro_" + [guid]::NewGuid().ToString("N") + ".sql")
    try {
        $sessionPrelude | Set-Content -LiteralPath $tmp -Encoding UTF8
        Get-Content -LiteralPath $sourceFile | Add-Content -LiteralPath $tmp -Encoding UTF8
        & $psql -w -v ON_ERROR_STOP=1 -f $tmp
        $exitCode = $LASTEXITCODE
    }
    finally {
        Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
    }
}
else {
    & $psql -w -v ON_ERROR_STOP=1 -c $cmd
    $exitCode = $LASTEXITCODE
}

exit $exitCode
