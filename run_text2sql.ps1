[CmdletBinding(DefaultParameterSetName = 'Limited')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Limited')]
    [ValidateRange(1, 2147483647)]
    [int]$Limit,

    [Parameter(Mandatory = $true, ParameterSetName = 'Full')]
    [switch]$Full,

    [Parameter(Mandatory = $true, ParameterSetName = 'Help')]
    [switch]$Help,

    [switch]$GenerateOnly,
    [switch]$EvaluateOnly,
    [switch]$NoResume,

    [ValidatePattern('^[A-Za-z0-9._-]+$')]
    [string]$RunName = 'latest',

    [string]$OutputRoot,

    [string]$PsqlPath
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    @'
Competition PostgreSQL Text-to-SQL runner

Usage:
  .\run_text2sql.ps1 -Limit 1 -RunName smoke
  .\run_text2sql.ps1 -Full -RunName baseline

Scope (choose exactly one):
  -Limit N        Run the first N questions
  -Full           Run all competition questions

Modes:
  -GenerateOnly   Generate SQL without evaluation
  -EvaluateOnly   Evaluate an existing RunName
  -NoResume       Do not reuse checkpoints; create a timestamped run by default

Other:
  -RunName NAME   Run directory name; default: latest
  -OutputRoot DIR Root directory for run outputs
  -PsqlPath PATH  Explicit psql.exe path
  -Help           Show help without reading .env
'@ | Write-Output
    exit 0
}

if ($GenerateOnly -and $EvaluateOnly) {
    throw '-GenerateOnly and -EvaluateOnly cannot be used together'
}
if ($EvaluateOnly -and $NoResume) {
    throw '-EvaluateOnly cannot be used with -NoResume'
}
if ($NoResume -and -not $PSBoundParameters.ContainsKey('RunName')) {
    $RunName = Get-Date -Format 'yyyyMMdd-HHmmss'
}

$repoRoot = $PSScriptRoot
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $repoRoot 'workspace\standard\eval_runs\competition'
}
elseif (-not [System.IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot = Join-Path $repoRoot $OutputRoot
}
$runDirectory = Join-Path $OutputRoot $RunName
$predictionsPath = Join-Path $runDirectory 'predictions.json'
$goldSubsetPath = Join-Path $runDirectory 'gold_subset.json'
$evaluationPath = Join-Path $runDirectory 'evaluation.json'
$generationExitCode = 0

Push-Location $repoRoot
try {
    $env:PYTHONIOENCODING = 'utf-8'
    if (-not $EvaluateOnly) {
        $generationArgs = @(
            '-m',
            'workspace.standard.text2sql_runner.generate',
            '--output-dir',
            $runDirectory
        )
        if ($PSCmdlet.ParameterSetName -eq 'Full') {
            $generationArgs += '--full'
        }
        else {
            $generationArgs += @('--limit', [string]$Limit)
        }
        if ($NoResume) {
            $generationArgs += '--no-resume'
        }
        if ($PsqlPath) {
            $generationArgs += @('--psql-path', $PsqlPath)
        }

        & python @generationArgs
        $generationExitCode = $LASTEXITCODE
        if ($generationExitCode -notin @(0, 2)) {
            throw "SQL generation failed with exit code $generationExitCode"
        }
    }

    if ($GenerateOnly) {
        Write-Output "Generation output: $runDirectory"
        exit $generationExitCode
    }

    if (-not (Test-Path -LiteralPath $predictionsPath -PathType Leaf)) {
        throw "Predictions file does not exist: $predictionsPath"
    }
    if (-not (Test-Path -LiteralPath $goldSubsetPath -PathType Leaf)) {
        throw "Aligned gold subset does not exist: $goldSubsetPath"
    }

    $evaluationArgs = @(
        'workspace/standard/competition_eval/evaluate.py',
        '--gold',
        $goldSubsetPath,
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

    & python @evaluationArgs
    $evaluationExitCode = $LASTEXITCODE
    if ($evaluationExitCode -ne 0) {
        throw "SQL evaluation failed with exit code $evaluationExitCode"
    }

    Write-Output "Run output: $runDirectory"
    if ($generationExitCode -eq 2) {
        Write-Warning 'Some questions failed. Evaluation completed with missing predictions.'
        exit 2
    }
    exit 0
}
finally {
    Pop-Location
}
