#Requires -Version 5.1

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up development environment for BrightHive Testing Infrastructure CDK" -ForegroundColor Green

# Check if uv is installed
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ uv is not installed. Installing uv..." -ForegroundColor Red
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Create virtual environment
Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
uv venv

# Activate virtual environment (note for user)
Write-Host "📥 Installing dependencies..." -ForegroundColor Cyan
.\.venv\Scripts\activate
uv pip install -e ".[dev]"

# Install pre-commit hooks
Write-Host "🔗 Installing pre-commit hooks..." -ForegroundColor Cyan
pre-commit install
pre-commit install --hook-type pre-push

# Create .env file if needed
if (-not (Test-Path .env)) {
    Write-Host "📝 Creating .env file from .env.example..." -ForegroundColor Cyan
    Copy-Item .env.example .env
    Write-Host "✏️  Please update .env with your configuration" -ForegroundColor Yellow
}

Write-Host "`n✅ Development environment setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Activate the virtual environment: .\.venv\Scripts\Activate.ps1"
Write-Host "  2. Update .env with your configuration"
Write-Host "  3. Run tests: pytest"
Write-Host "  4. Start coding! 🎉"
