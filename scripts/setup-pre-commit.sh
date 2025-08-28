#!/bin/bash

# Pre-commit Hook Setup Script for Inscribe Data Processing Service
# This script sets up pre-commit hooks that mirror the CircleCI pipeline checks

set -e

echo "Setting up pre-commit hooks for Inscribe Data Processing Service..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: This script must be run from the root of a git repository"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Install pre-commit if not already installed
if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
else
    echo "pre-commit is already installed"
fi

# Install development dependencies needed for hooks
echo "Installing development dependencies..."
pip install -r requirements.txt
pip install -r test-requirements.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Test individual hooks first
echo "Testing individual hooks..."

echo "  - Testing black formatter..."
if pre-commit run black --all-files; then
    echo "    Black passed"
else
    echo "    Black made formatting changes (this is normal)"
fi

echo "  - Testing isort import sorting..."
if pre-commit run isort --all-files; then
    echo "    isort passed"
else
    echo "    isort made import changes (this is normal)"
fi

echo "  - Testing flake8 linting..."
if pre-commit run flake8 --all-files; then
    echo "    flake8 passed"
else
    echo "    flake8 found issues - please fix them manually"
fi

echo "  - Testing pytest..."
if pre-commit run pytest --all-files; then
    echo "    pytest passed"
else
    echo "    pytest failed - please fix failing tests"
fi

echo ""
echo "Pre-commit hooks setup complete!"
echo ""
echo "What happens now:"
echo "   • Every git commit will run these checks automatically"
echo "   • If any check fails, the commit will be blocked"
echo "   • You can run 'pre-commit run --all-files' to check all files manually"
echo "   • You can run 'pre-commit run <hook-name>' to run a specific hook"
echo ""
echo "Available commands:"
echo "   pre-commit run --all-files     # Run all hooks on all files"
echo "   pre-commit run black           # Run only black formatter"
echo "   pre-commit run flake8          # Run only flake8 linter"
echo "   pre-commit run pytest          # Run only unit tests"
echo "   pre-commit run isort           # Run only import sorting"
echo ""
echo "Tips:"
echo "   • Use 'git commit --no-verify' to skip pre-commit hooks if needed"
echo "   • Run 'pre-commit run --all-files' before committing to catch issues early"
echo ""
echo "Next steps:"
echo "   1. Fix any flake8 or pytest issues reported above"
echo "   2. Run 'git add .' to stage any formatting changes"
echo "   3. Try making a test commit to see the hooks in action"
