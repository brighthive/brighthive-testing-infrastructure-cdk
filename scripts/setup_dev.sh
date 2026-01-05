#!/usr/bin/env bash
set -euo pipefail

# BrightAgent CDK Development Environment Setup
# Sets up virtual environment and installs all dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🚀 Setting up BrightAgent CDK development environment..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: 'uv' is not installed"
    echo "   Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✓ Found uv: $(uv --version)"
echo ""

# Create virtual environment if it doesn't exist
if [[ ! -d ".venv" ]]; then
    echo "📦 Creating virtual environment..."
    uv venv
    echo "✓ Virtual environment created at .venv"
else
    echo "✓ Virtual environment already exists at .venv"
fi
echo ""

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install development dependencies
echo "📥 Installing development dependencies..."
uv pip install -e ".[dev]"
echo "✓ Development dependencies installed"
echo ""

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
if command -v pre-commit &> /dev/null; then
    pre-commit install
    pre-commit install --hook-type pre-push
    echo "✓ Pre-commit hooks installed"
else
    echo "⚠️  Warning: pre-commit not found, skipping hook installation"
fi
echo ""

# Verify installation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Verifying installation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Python version:"
python --version

echo ""
echo "Installed packages:"
uv pip list | grep -E "(pytest|ruff|mypy|aws-cdk-lib|boto3)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Development environment setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Run tests:"
echo "     make test"
echo ""
echo "  3. Run code quality checks:"
echo "     make check"
echo ""
echo "  4. Deploy CDK stacks:"
echo "     source .env.loadstress"
echo "     cdk deploy --all"
echo ""
