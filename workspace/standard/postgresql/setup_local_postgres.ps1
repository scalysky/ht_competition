[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataLink = 'C:\Code\Fin_tech_match\.pg_import_data'

if (-not (Test-Path -LiteralPath $psql)) {
    throw "psql was not found: $psql"
}

if (-not (Test-Path -LiteralPath $dataLink)) {
    throw "ASCII data link was not found: $dataLink"
}

function Invoke-PsqlFile {
    param(
        [Parameter(Mandatory)] [string] $Database,
        [Parameter(Mandatory)] [string] $File
    )

    Write-Host "`nRunning $([System.IO.Path]::GetFileName($File)) ..." -ForegroundColor Cyan
    & $psql -X -h localhost -p 5432 -U postgres -d $Database -v ON_ERROR_STOP=1 -f $File
    if ($LASTEXITCODE -ne 0) {
        throw "psql failed with exit code $LASTEXITCODE"
    }
}

$securePassword = Read-Host 'Enter the postgres password set during installation' -AsSecureString
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)

    Invoke-PsqlFile -Database 'postgres' -File (Join-Path $scriptDir '01_bootstrap.sql')
    Invoke-PsqlFile -Database 'ht_competition' -File (Join-Path $scriptDir '02_schema.sql')
    Invoke-PsqlFile -Database 'ht_competition' -File (Join-Path $scriptDir '03_import.sql')
    Invoke-PsqlFile -Database 'ht_competition' -File (Join-Path $scriptDir '04_set_eval_password.sql')
    Invoke-PsqlFile -Database 'ht_competition' -File (Join-Path $scriptDir '05_verify.sql')

    Write-Host "`nPostgreSQL competition database initialization completed." -ForegroundColor Green
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if ($passwordPtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
    }
}
