#!/usr/bin/env bash
set -euo pipefail

# Parse arguments
COVERAGE=true
VERBOSE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-cov)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE="-vv"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--no-cov] [-v|--verbose]"
            exit 1
            ;;
    esac
done

echo "🧪 Running tests for BrightHive Testing Infrastructure CDK"
echo ""

if [ "$COVERAGE" = true ]; then
    pytest $VERBOSE --cov=brighthive_testing_cdk --cov-report=term-missing --cov-report=html
    echo ""
    echo "📊 Coverage report generated in htmlcov/index.html"
else
    pytest $VERBOSE
fi
