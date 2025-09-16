#!/bin/bash

# FinTech Multi-Agent System Startup Script

set -e  # Exit on any error

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "FinTech Multi-Agent System Startup"
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
    echo "Warning: requirements.txt not found. Some dependencies may be missing."
fi

echo ""
echo "Starting FinTech Multi-Agent System..."
echo "=========================================="

# Set PYTHONPATH to include src directory
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Run the main application
python3 src/main.py

# Check exit status
EXIT_CODE=$?

echo ""
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "FinTech Multi-Agent System completed successfully."
else
    echo "FinTech Multi-Agent System exited with error code: $EXIT_CODE"
fi
echo "=========================================="

exit $EXIT_CODE