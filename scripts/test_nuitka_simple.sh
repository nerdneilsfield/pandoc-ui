#!/bin/bash

# 简单的 Nuitka 测试脚本，逐步测试每个功能
# Simple Nuitka test script to test each feature step by step

set -e

echo "🧪 Testing Nuitka Step by Step"
echo "=============================="

# Clean any previous tests
rm -rf test_build/
mkdir -p test_build/

# Get version
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📦 Version: $VERSION"

cd test_build/

echo ""
echo "🔍 Step 1: Test basic Nuitka compilation"
echo "----------------------------------------"
echo "uv run python -m nuitka --version"
uv run python -m nuitka --version

echo ""
echo "🔍 Step 2: Test basic standalone build"
echo "--------------------------------------"
echo "Command: uv run python -m nuitka --standalone ../pandoc_ui/main.py"
if uv run python -m nuitka --standalone ../pandoc_ui/main.py; then
    echo "✅ Basic standalone build succeeded"
    ls -la
    echo "Files created:"
    find . -name "*main*" -o -name "*pandoc*" | head -10
else
    echo "❌ Basic standalone build failed"
    exit 1
fi

echo ""
echo "🔍 Step 3: Test with custom output filename"
echo "-------------------------------------------"
rm -rf main.dist/
echo "Command: uv run python -m nuitka --standalone --output-filename=test-pandoc-ui ../pandoc_ui/main.py"
if uv run python -m nuitka --standalone --output-filename=test-pandoc-ui ../pandoc_ui/main.py; then
    echo "✅ Custom filename build succeeded"
    ls -la
    echo "Files created:"
    find . -name "*test-pandoc*" -o -name "*pandoc*" | head -10
else
    echo "❌ Custom filename build failed"
    exit 1
fi

echo ""
echo "🔍 Step 4: Test with output directory"
echo "------------------------------------"
rm -rf *.dist/
mkdir -p output_test/
echo "Command: uv run python -m nuitka --standalone --output-dir=output_test --output-filename=pandoc-ui-test ../pandoc_ui/main.py"
if uv run python -m nuitka --standalone --output-dir=output_test --output-filename=pandoc-ui-test ../pandoc_ui/main.py; then
    echo "✅ Output directory build succeeded"
    echo "Contents of output_test/:"
    ls -la output_test/
    echo "Looking for executable:"
    find output_test/ -type f -executable | head -5
else
    echo "❌ Output directory build failed"
    exit 1
fi

echo ""
echo "🔍 Step 5: Test with PySide6 plugin"
echo "-----------------------------------"
rm -rf output_test/
mkdir -p output_test/
echo "Command: uv run python -m nuitka --standalone --enable-plugin=pyside6 --output-dir=output_test --output-filename=pandoc-ui-pyside ../pandoc_ui/main.py"
if uv run python -m nuitka --standalone --enable-plugin=pyside6 --output-dir=output_test --output-filename=pandoc-ui-pyside ../pandoc_ui/main.py; then
    echo "✅ PySide6 plugin build succeeded"
    echo "Contents of output_test/:"
    ls -la output_test/
    echo "Looking for executable:"
    find output_test/ -type f -executable | head -5
    
    # Try to run the executable
    EXECUTABLE=$(find output_test/ -name "pandoc-ui-pyside*" -type f -executable | head -1)
    if [ -n "$EXECUTABLE" ]; then
        echo "🧪 Testing executable: $EXECUTABLE"
        if timeout 10s "$EXECUTABLE" --help 2>/dev/null; then
            echo "✅ Executable runs successfully"
        else
            echo "⚠️  Executable test failed or timed out"
        fi
    fi
else
    echo "❌ PySide6 plugin build failed"
    exit 1
fi

echo ""
echo "🎉 All tests completed successfully!"
echo "The issue is likely in the build script path detection logic."

cd ..
rm -rf test_build/