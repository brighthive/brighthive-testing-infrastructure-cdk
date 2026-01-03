#Requires -Version 5.1

[CmdletBinding()]
param(
    [switch]$NoCov,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Running tests for BrightHive Testing Infrastructure CDK" -ForegroundColor Cyan
Write-Host ""

$args = @()

if ($Verbose) {
    $args += "-vv"
}

if ($NoCov) {
    pytest @args
} else {
    pytest @args --cov=brighthive_testing_cdk --cov-report=term-missing --cov-report=html
    Write-Host ""
    Write-Host "📊 Coverage report generated in htmlcov/index.html" -ForegroundColor Green
}
