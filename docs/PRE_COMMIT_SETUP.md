# Pre-commit Hooks Setup Guide

This document explains how to set up and use pre-commit hooks for the Inscribe Data Processing Service project.

## Overview

Pre-commit hooks automatically run code quality checks before each git commit, ensuring that only properly formatted and tested code is committed to the repository. This helps maintain code quality and catches issues early in the development process.

## Installation

1. **Install pre-commit** (if not already installed):
   ```bash
   pip install pre-commit
   ```

2. **Install the pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Install development dependencies**:
   ```bash
   pip install -r test-requirements.txt
   ```

## Configuration

The pre-commit configuration is defined in `.pre-commit-config.yaml` and includes the following hooks:

### Core Hooks (Always Enabled)

1. **Black** - Code formatter
   - Ensures consistent code formatting
   - Max line length: 100 characters

2. **isort** - Import sorter
   - Organizes imports consistently
   - Uses black profile for compatibility

3. **flake8** - Linter
   - Catches syntax errors and style violations
   - Ignores E203 and W503 for black compatibility

4. **pytest** - Unit tests
   - Runs all unit tests with coverage reporting
   - Fails if any tests fail

### Optional Hooks (Commented Out)

- **bandit** - Security scanner
- **mypy** - Type checker (disabled due to Pydantic v2 compatibility)

## Usage

### Automatic Execution

Once installed, the hooks will run automatically on every `git commit`. If any hook fails, the commit will be blocked until the issues are resolved.

### Manual Execution

You can run the hooks manually at any time:

```bash
# Run all hooks on all files
pre-commit run --all-files

# Run a specific hook
pre-commit run black
pre-commit run flake8
pre-commit run pytest

# Run hooks on staged files only
pre-commit run
```

### Bypassing Hooks

If you need to commit without running the hooks (not recommended), you can use:

```bash
git commit --no-verify -m "your commit message"
```

## CircleCI Integration

The pre-commit hooks mirror the checks performed in the CircleCI pipeline, ensuring that code quality issues are caught locally before pushing to the repository. This includes:

- Code formatting (black)
- Import organization (isort)
- Linting (flake8)
- Unit tests (pytest)

## Troubleshooting

### Common Issues

1. **Hook fails with "command not found"**
   - Ensure all dependencies are installed: `pip install -r test-requirements.txt`

2. **Black reformats code**
   - This is expected behavior. Review the changes and commit them.

3. **Tests fail**
   - Fix the failing tests before committing.
   - Use `pytest tests/ -v` to run tests manually and see detailed output.

4. **Flake8 linting errors**
   - Fix the reported style violations.
   - Common issues: line too long, unused imports, trailing whitespace.

### Updating Hooks

To update to the latest versions of the hooks:

```bash
pre-commit autoupdate
```

## Best Practices

1. **Run hooks before committing**: Use `pre-commit run --all-files` to check your changes.

2. **Keep commits small**: Smaller commits are easier to review when hooks fail.

3. **Fix issues promptly**: Don't ignore hook failures; they indicate real code quality issues.

4. **Update regularly**: Keep pre-commit hooks updated to catch the latest issues.

## Configuration Details

The hooks are configured to:
- Only run on Python files in `src/` and `tests/` directories
- Use consistent line length (100 characters)
- Skip problematic security warnings that are false positives
- Provide detailed output for debugging

For more advanced configuration options, see the [pre-commit documentation](https://pre-commit.com/).
