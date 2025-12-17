#!/bin/bash

# run_tests.sh - Comprehensive test runner for cpap-py library
# This script runs all tests with coverage reporting and ensures 95% coverage threshold

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "CPAP-PY Test Suite Runner"
echo "========================================="
echo ""

# Ensure we're in the project root
cd "$(dirname "$0")"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Please install dev dependencies: pip install -e \".[dev]\""
    exit 1
fi

# Clean previous coverage data
echo "Cleaning previous coverage data..."
rm -rf .coverage htmlcov/ .pytest_cache/
echo ""

# Run tests with coverage
echo "========================================="
echo "Running Test Suite"
echo "========================================="
echo ""

# Run pytest with coverage
pytest tests/ \
    -v \
    --cov=cpap_py \
    --cov-report=term-missing \
    --strict-markers \
    --tb=short \
    -p no:warnings

# Capture exit code
PYTEST_EXIT=$?

echo ""
echo "========================================="
echo "Coverage Summary"
echo "========================================="
echo ""

# Generate coverage report
python -m coverage report

echo ""
echo "========================================="
echo "Checking Coverage Threshold (95%)"
echo "========================================="
echo ""

# Check if coverage meets 95% threshold
if python -m coverage report --fail-under=95; then
    echo -e "${GREEN}✓ Coverage threshold met (≥95%)${NC}"
    COVERAGE_PASS=0
else
    echo -e "${RED}✗ Coverage below 95% threshold${NC}"
    COVERAGE_PASS=1
fi

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo ""

if [ $PYTEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

if [ $COVERAGE_PASS -eq 0 ]; then
    echo -e "${GREEN}✓ Coverage threshold met (≥95%)${NC}"
else
    echo -e "${YELLOW}⚠ Coverage below 95% threshold${NC}"
fi

echo ""

# Exit with combined status
if [ $PYTEST_EXIT -ne 0 ] || [ $COVERAGE_PASS -ne 0 ]; then
    exit 1
fi

echo -e "${GREEN}All checks passed!${NC}"
exit 0
