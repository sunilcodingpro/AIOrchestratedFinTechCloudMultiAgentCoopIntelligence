#!/bin/bash

# FinTech Multi-Agent System Test Runner Script

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "FinTech Multi-Agent System Test Runner"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"
echo "Python Version: $(python3 --version)"
echo "Date: $(date)"
echo ""

# Change to project root directory
cd "$PROJECT_ROOT"

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip3 install -q -r requirements.txt
    echo "Dependencies installed successfully."
else
    echo "Warning: requirements.txt not found. Installing pytest..."
    pip3 install -q pytest
fi

echo ""

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed or not in PATH"
    echo "Please install pytest: pip3 install pytest"
    exit 1
fi

echo "pytest version: $(pytest --version | head -n 1)"
echo ""

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Check if tests directory exists
if [ ! -d "tests" ]; then
    echo "Warning: tests directory not found. Creating basic test structure..."
    mkdir -p tests/test_agents
    echo "Test directory created."
fi

echo "=========================================="
echo "Running Python tests with pytest..."
echo "=========================================="

# Run pytest with verbose output and coverage if available
if command -v coverage &> /dev/null; then
    echo "Running tests with coverage..."
    coverage run -m pytest tests/ -v --tb=short
    echo ""
    echo "Coverage Report:"
    coverage report --show-missing
else
    echo "Running tests without coverage (install coverage for coverage reports)..."
    pytest tests/ -v --tb=short
fi

# Check exit status
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "All tests passed successfully!"
else
    echo "Some tests failed. Exit code: $EXIT_CODE"
fi
echo "=========================================="

exit $EXIT_CODE