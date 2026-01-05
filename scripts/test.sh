#!/usr/bin/env bash
set -euo pipefail

# BrightAgent CDK Test Runner
# Runs pytest with configurable coverage options

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if running in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "⚠️  Warning: Not running in a virtual environment"
    echo "   Activate .venv first: source .venv/bin/activate"
    exit 1
fi

# Parse arguments
NO_COV=false
if [[ "${1:-}" == "--no-cov" ]]; then
    NO_COV=true
fi

echo "🧪 Running tests..."
echo "   Project: brighthive_loadstress_cdk"
echo "   Coverage: $([[ $NO_COV == true ]] && echo 'disabled' || echo 'enabled')"
echo ""

if [[ $NO_COV == true ]]; then
    # Fast test run without coverage
    uv run pytest tests/ -v
else
    # Full test run with coverage report
    uv run pytest tests/ \
        --cov=brighthive_loadstress_cdk \
        --cov-report=term-missing \
        --cov-report=html \
        -v

    echo ""
    echo "✓ Coverage report generated: htmlcov/index.html"
fi
