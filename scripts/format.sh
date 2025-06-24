#!/bin/bash

# Format Python code using multiple tools
# This script runs ruff, black, and isort to format the codebase

set -e

echo "🔧 Formatting Python code..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    exit 1
fi

# Run isort to sort imports
echo "📦 Sorting imports with isort..."
uv run isort pandoc_ui tests scripts

# Run black to format code
echo "🖤 Formatting code with black..."
uv run black pandoc_ui tests scripts

# Run ruff to fix auto-fixable issues
echo "🦀 Running ruff auto-fixes..."
uv run ruff check --fix pandoc_ui tests scripts

# Run ruff format as well (alternative to black)
echo "🦀 Running ruff format..."
uv run ruff format pandoc_ui tests scripts

echo "✅ Code formatting completed!"
echo ""
echo "📋 Summary:"
echo "  - Imports sorted with isort"
echo "  - Code formatted with black"
echo "  - Auto-fixable issues resolved with ruff"
echo "  - Code formatted with ruff format"
echo ""
echo "💡 Next steps:"
echo "  - Run ./scripts/lint.sh to check for remaining issues"
echo "  - Review changes before committing"