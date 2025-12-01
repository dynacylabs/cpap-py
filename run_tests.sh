#!/bin/bash
#
# Test runner script for cpap-py.
#
# Usage:
#     ./run_tests.sh              # Run all tests
#     ./run_tests.sh unit         # Run only unit tests (fast)
#     ./run_tests.sh integration  # Run only integration tests
#     ./run_tests.sh coverage     # Run with coverage report
#     ./run_tests.sh quick        # Run unit tests only (same as 'unit')
#     ./run_tests.sh <file>       # Run specific test file
#     ./run_tests.sh --help       # Show this help

set -e

print_header() {
    echo ""
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
    echo ""
}

# Parse arguments
MODE="${1:-all}"

if [[ "$MODE" == "--help" || "$MODE" == "-h" || "$MODE" == "help" ]]; then
    sed -n '2,12p' "$0" | sed 's/^# //'
    exit 0
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed!"
    echo ""
    echo "Install dependencies:"
    echo "  pip install pytest pytest-cov pytest-mock coverage"
    echo "  or"
    echo "  pip install -e \".[test]\""
    exit 1
fi

# Check if pytest-cov is installed
COVERAGE_AVAILABLE=false
if python -c "import pytest_cov" 2>/dev/null; then
    COVERAGE_AVAILABLE=true
fi

# Build pytest command based on mode
case "$MODE" in
    unit|mock|mocked|quick)
        print_header "Running Unit Tests (Fast)"
        if [ "$COVERAGE_AVAILABLE" = true ]; then
            pytest tests/ -v -m unit --cov=cpap_py --cov-report=term-missing
        else
            pytest tests/ -v -m unit
        fi
        ;;
    
    integration|live)
        print_header "Running Integration Tests"
        if [ "$COVERAGE_AVAILABLE" = true ]; then
            pytest tests/ -v -m integration --cov=cpap_py --cov-report=term-missing
        else
            pytest tests/ -v -m integration
        fi
        ;;
    
    coverage|cov)
        print_header "Running All Tests with Coverage"
        if [ "$COVERAGE_AVAILABLE" = true ]; then
            pytest tests/ -v --cov=cpap_py --cov-report=term-missing --cov-report=html
            echo ""
            echo "📊 Coverage report generated in htmlcov/"
            echo "   Open htmlcov/index.html in your browser to view"
        else
            echo "❌ pytest-cov is not installed!"
            echo ""
            echo "Install coverage dependencies:"
            echo "  pip install pytest-cov coverage"
            exit 1
        fi
        ;;
    
    all|"")
        print_header "Running All Tests"
        if [ "$COVERAGE_AVAILABLE" = true ]; then
            pytest tests/ -v --cov=cpap_py --cov-report=term-missing
        else
            echo "⚠️  pytest-cov not installed, running without coverage"
            pytest tests/ -v
        fi
        ;;
    
    slow)
        print_header "Running Slow Tests"
        if [ "$COVERAGE_AVAILABLE" = true ]; then
            pytest tests/ -v -m slow --cov=cpap_py --cov-report=term-missing
        else
            pytest tests/ -v -m slow
        fi
        ;;
    
    *)
        # Assume it's a file path or specific test
        if [[ -f "$MODE" || "$MODE" == tests/* || "$MODE" == *::* ]]; then
            print_header "Running Specific Tests: $MODE"
            if [ "$COVERAGE_AVAILABLE" = true ]; then
                pytest "$MODE" -v --cov=cpap_py --cov-report=term-missing
            else
                pytest "$MODE" -v
            fi
        else
            echo "❌ Unknown mode: $MODE"
            echo ""
            echo "Run './run_tests.sh --help' for usage information"
            exit 1
        fi
        ;;
esac

# Print summary
echo ""
echo "✅ Tests completed successfully!"
echo ""
