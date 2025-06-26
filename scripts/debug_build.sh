#!/bin/bash

# Debug build script to help diagnose Nuitka build issues
# Usage: ./scripts/debug_build.sh

set -e

echo "🔍 Debugging Nuitka Build Issues"
echo "================================="

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
if [ -z "$VERSION" ]; then
    VERSION="dev"
fi

PLATFORM="linux"
BUILD_MODE="standalone"  # Force standalone for debugging
DIST_DIR="dist/$PLATFORM"
OUTPUT_FILE="pandoc-ui-$PLATFORM-$VERSION"

echo "📦 Version: $VERSION"
echo "🏗️  Build mode: $BUILD_MODE"
echo "📁 Expected output: $DIST_DIR/$OUTPUT_FILE"

# Clean previous builds
echo ""
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/
mkdir -p "$DIST_DIR"

# Check memory and system resources
echo ""
echo "💻 System Resources:"
echo "Memory: $(free -h | grep '^Mem:' | awk '{print $2 " total, " $7 " available"}')"
echo "Disk space: $(df -h . | tail -1 | awk '{print $4 " available"}')"

# Run minimal Nuitka build with verbose output
echo ""
echo "🔨 Running minimal Nuitka build..."
echo "Command: uv run python -m nuitka --standalone --output-dir=$DIST_DIR --output-filename=$OUTPUT_FILE --low-memory --jobs=1 --show-progress --show-memory pandoc_ui/main.py"
echo ""

uv run python -m nuitka \
    --standalone \
    --output-dir="$DIST_DIR" \
    --output-filename="$OUTPUT_FILE" \
    --low-memory \
    --jobs=1 \
    --show-progress \
    --show-memory \
    --enable-plugin=pyside6 \
    --assume-yes-for-downloads \
    pandoc_ui/main.py

echo ""
echo "🔍 Checking build results..."

# Check what was actually created
echo "Contents of $DIST_DIR:"
ls -la "$DIST_DIR/" || echo "Directory does not exist"

# Look for any pandoc-ui related files
echo ""
echo "Looking for pandoc-ui files in dist/:"
find dist/ -name "*pandoc*" -type f -o -name "*pandoc*" -type d 2>/dev/null || echo "No pandoc-ui files found"

# Check if standalone directory exists
if [ -d "$DIST_DIR/$OUTPUT_FILE" ]; then
    echo "✅ Standalone directory found: $DIST_DIR/$OUTPUT_FILE"
    echo "Contents:"
    ls -la "$DIST_DIR/$OUTPUT_FILE/" | head -10
    
    # Look for executable
    if [ -f "$DIST_DIR/$OUTPUT_FILE/$OUTPUT_FILE" ]; then
        echo "✅ Executable found: $DIST_DIR/$OUTPUT_FILE/$OUTPUT_FILE"
        ls -lh "$DIST_DIR/$OUTPUT_FILE/$OUTPUT_FILE"
    else
        echo "❌ Executable not found at expected location"
        echo "Looking for any executable files in the directory:"
        find "$DIST_DIR/$OUTPUT_FILE" -type f -executable | head -5
    fi
else
    echo "❌ Standalone directory not found"
fi

echo ""
echo "🏁 Debug complete"