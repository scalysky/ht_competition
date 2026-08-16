[CmdletBinding(DefaultParameterSetName = 'Evaluate')]
param(
    [Parameter(Mandatory = $true, Position = 0, ParameterSetName = 'Evaluate')]
    [string]$Predictions,

    [Parameter(Mandatory = $true, ParameterSetName = 'Help')]
    [switch]$Help,

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$RunName = 'latest',

    [string]$OutputRoot,

    [string]$PsqlPath
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    @(
        'Competition SQL evaluator (EM, EX, R-VES)'
        ''
        'Usage:'
        '  .\run_text2sql.ps1 -Predictions C:\path\answers.json -RunName json_test'
        '  .\run_text2sql.ps1 -Predictions C:\path\answers.txt  -RunName txt_test'
        ''
        'Input files:'
        '  JSON  Supports [{"id":1,"sql":"SELECT ..."}] or {"1":"SELECT ..."}'
        '  TXT   Separate SQL answers with a line containing exactly 40 hyphens'
        ''
        'Options:'
        '  -Predictions FILE  JSON or TXT file to evaluate (required)'
        '  -RunName NAME      Report directory name; default: latest'
        '  -OutputRoot DIR    Custom report root directory'
        '  -PsqlPath PATH     Explicit psql.exe path'
        '  -Help              Show help without connecting to PostgreSQL'
        ''
        'This script only evaluates existing SQL. It uses no model API or knowledge base.'
    ) | Write-Output
    exit 0
}

$repoRoot = $PSScriptRoot
if ([System.IO.Path]::IsPathRooted($Predictions)) {
    $predictionsPath = [System.IO.Path]::GetFullPath($Predictions)
}
else {
    $predictionsPath = [System.IO.Path]::GetFullPath(
        (Join-Path (Get-Location).Path $Predictions)
    )
}

if (-not (Test-Path -LiteralPath $predictionsPath -PathType Leaf)) {
    throw "Input file does not exist: $predictionsPath"
}

$extension = [System.IO.Path]::GetExtension($predictionsPath).ToLowerInvariant()
switch ($extension) {
    '.json' { $inputFormat = 'JSON' }
    '.txt' { $inputFormat = 'TXT' }
    default { throw "Unsupported input format; use .json or .txt: $predictionsPath" }
}

if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repoRoot 'workspace\standard\eval_runs\competition'
}
elseif (-not [System.IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot = Join-Path $repoRoot $OutputRoot
}

$runDirectory = Join-Path $OutputRoot $RunName
$evaluationPath = Join-Path $runDirectory 'evaluation.json'
New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null

Write-Output "Input file: $predictionsPath"
Write-Output "Input format: $inputFormat"
Write-Output 'Metrics: EM, EX, R-VES'
Write-Output 'Knowledge base/API: not used'

$evaluationArgs = @(
    'workspace/standard/competition_eval/evaluate.py',
    '--predictions',
    $predictionsPath,
    '--metrics',
    'em,ex,rves',
    '--output',
    $evaluationPath
)
if ($PsqlPath) {
    $evaluationArgs += @('--psql-path', $PsqlPath)
}

Push-Location $repoRoot
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & python @evaluationArgs
    $evaluationExitCode = $LASTEXITCODE
    if ($evaluationExitCode -ne 0) {
        throw "SQL evaluation failed with exit code $evaluationExitCode"
    }

    Write-Output "Evaluation output: $runDirectory"
    exit 0
}
finally {
    Pop-Location
}
