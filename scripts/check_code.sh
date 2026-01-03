#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running code quality checks for BrightHive Testing Infrastructure CDK"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Function to run check and track failures
run_check() {
    local name="$1"
    shift
    echo "➡️  Running $name..."
    if "$@"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        FAILED=1
    fi
    echo ""
}

# Ruff linting
run_check "Ruff linting" ruff check src tests

# Ruff formatting
run_check "Ruff formatting" ruff format --check src tests

# MyPy type checking
run_check "MyPy type checking" mypy src

# Pytest with coverage
run_check "Pytest with coverage" pytest --cov=brighthive_testing_cdk --cov-report=term-missing

# Check for security issues with bandit
if command -v bandit &> /dev/null; then
    run_check "Bandit security check" bandit -r src -c pyproject.toml
else
    echo -e "${YELLOW}⚠️  Bandit not installed, skipping security check${NC}"
fi

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed${NC}"
    exit 1
fi
