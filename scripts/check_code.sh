#!/usr/bin/env bash
set -euo pipefail

# BrightAgent CDK Code Quality Checker
# Runs all code quality checks: ruff, mypy, tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if running in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "⚠️  Warning: Not running in a virtual environment"
    echo "   Activate .venv first: source .venv/bin/activate"
    exit 1
fi

EXIT_CODE=0

echo "🔍 Running code quality checks..."
echo ""

# 1. Ruff linting
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Ruff Linting"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run ruff check src tests; then
    echo "✓ Ruff linting passed"
else
    echo "✗ Ruff linting failed"
    EXIT_CODE=1
fi
echo ""

# 2. Ruff formatting check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Ruff Formatting Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run ruff format --check src tests; then
    echo "✓ Formatting check passed"
else
    echo "✗ Formatting check failed (run: make format)"
    EXIT_CODE=1
fi
echo ""

# 3. Type checking with mypy
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Type Checking (mypy)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if uv run mypy src; then
    echo "✓ Type checking passed"
else
    echo "✗ Type checking failed"
    EXIT_CODE=1
fi
echo ""

# 4. Tests with coverage
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Tests with Coverage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if bash "$SCRIPT_DIR/test.sh"; then
    echo "✓ Tests passed"
else
    echo "✗ Tests failed"
    EXIT_CODE=1
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo "✅ All code quality checks passed!"
else
    echo "❌ Some checks failed (exit code: $EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
