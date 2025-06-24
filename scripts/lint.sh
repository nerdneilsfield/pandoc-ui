#!/bin/bash

# Lint Python code using multiple tools
# This script runs ruff, mypy, and other linting tools to check code quality

set -e

echo "🔍 Linting Python code..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    exit 1
fi

# Track if any linting issues were found
ISSUES_FOUND=0

# Run ruff for linting
echo "🦀 Running ruff linting..."
if ! uv run ruff check pandoc_ui tests scripts; then
    echo "⚠️  Ruff found issues"
    ISSUES_FOUND=1
else
    echo "✅ Ruff: No issues found"
fi

echo ""

# Run mypy for type checking
echo "🔍 Running mypy type checking..."
if ! uv run mypy pandoc_ui; then
    echo "⚠️  MyPy found type issues"
    ISSUES_FOUND=1
else
    echo "✅ MyPy: No type issues found"
fi

echo ""

# Run pytest in multiple sessions to organize test output
echo "🧪 Running tests in multiple sessions..."

# Session 1: Infrastructure layer tests
echo "📚 Session 1: Infrastructure layer tests..."
if ! uv run pytest tests/test_pandoc_detector.py tests/test_pandoc_runner.py -v --tb=short; then
    echo "⚠️  Session 1: Infrastructure tests failed"
    ISSUES_FOUND=1
else
    echo "✅ Session 1: Infrastructure tests passed"
fi

echo ""

# Session 2: Application and config layer tests  
echo "⚙️  Session 2: Application and config layer tests..."
if ! uv run pytest tests/test_conversion_service.py tests/test_folder_scanner.py tests/test_profile_repository.py tests/test_config_manager.py tests/test_settings_store.py -v --tb=short; then
    echo "⚠️  Session 2: Application/config tests failed"
    ISSUES_FOUND=1
else
    echo "✅ Session 2: Application/config tests passed"
fi

echo ""

# Session 3: Integration tests (excluding GUI)
echo "🔗 Session 3: Integration tests..."
if ! uv run pytest tests/test_phase4_acceptance.py tests/test_batch_performance.py -v --tb=short; then
    echo "⚠️  Session 3: Integration tests failed"
    ISSUES_FOUND=1
else
    echo "✅ Session 3: Integration tests passed"
fi

echo ""
echo "📋 Linting Summary:"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ All checks passed! Code is ready for commit."
    echo ""
    echo "💡 Great job! Your code meets all quality standards:"
    echo "  - No linting issues (ruff)"
    echo "  - No type issues (mypy)"
    echo "  - All tests passing (pytest)"
else
    echo "❌ Issues found. Please address them before committing."
    echo ""
    echo "🔧 Quick fixes:"
    echo "  - Run ./scripts/format.sh to auto-fix formatting issues"
    echo "  - Check mypy output for type hints and corrections"
    echo "  - Review failing tests and fix underlying issues"
    exit 1
fi