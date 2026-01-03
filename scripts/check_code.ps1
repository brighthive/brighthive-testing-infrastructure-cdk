#Requires -Version 5.1

$ErrorActionPreference = "Stop"

Write-Host "🔍 Running code quality checks for BrightHive Testing Infrastructure CDK" -ForegroundColor Cyan
Write-Host ""

$FAILED = 0

function Run-Check {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host "➡️  Running $Name..." -ForegroundColor Cyan
    try {
        & $Command
        Write-Host "✅ $Name passed" -ForegroundColor Green
    } catch {
        Write-Host "❌ $Name failed" -ForegroundColor Red
        $script:FAILED = 1
    }
    Write-Host ""
}

# Ruff linting
Run-Check "Ruff linting" { ruff check src tests }

# Ruff formatting
Run-Check "Ruff formatting" { ruff format --check src tests }

# MyPy type checking
Run-Check "MyPy type checking" { mypy src }

# Pytest with coverage
Run-Check "Pytest with coverage" { pytest --cov=brighthive_testing_cdk --cov-report=term-missing }

# Check for security issues with bandit
if (Get-Command bandit -ErrorAction SilentlyContinue) {
    Run-Check "Bandit security check" { bandit -r src -c pyproject.toml }
} else {
    Write-Host "⚠️  Bandit not installed, skipping security check" -ForegroundColor Yellow
}

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ($FAILED -eq 0) {
    Write-Host "✅ All checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some checks failed" -ForegroundColor Red
    exit 1
}
