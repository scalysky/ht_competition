[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$securePassword = Read-Host 'Enter the postgres password set during installation' -AsSecureString
$passwordPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)

try {
    $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($passwordPtr)

    Write-Host "`nSetting the ht_eval password ..." -ForegroundColor Cyan
    & $psql -X -h localhost -p 5432 -U postgres -d ht_competition -v ON_ERROR_STOP=1 -f (Join-Path $scriptDir '04_set_eval_password.sql')
    if ($LASTEXITCODE -ne 0) {
        throw "Password setup failed with exit code $LASTEXITCODE"
    }

    Write-Host "`nVerifying imported data and role settings ..." -ForegroundColor Cyan
    & $psql -X -h localhost -p 5432 -U postgres -d ht_competition -v ON_ERROR_STOP=1 -f (Join-Path $scriptDir '05_verify.sql')
    if ($LASTEXITCODE -ne 0) {
        throw "Verification failed with exit code $LASTEXITCODE"
    }

    Write-Host "`nPostgreSQL competition database initialization completed." -ForegroundColor Green
}
finally {
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
    if ($passwordPtr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($passwordPtr)
    }
}

