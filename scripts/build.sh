#!/bin/bash

# Unix build script for pandoc-ui (Linux and macOS)
# For Windows, use scripts/windows_build.ps1

set -e

# Detect platform
PLATFORM=""
case "$(uname -s)" in
    Linux*)     PLATFORM="linux";;
    Darwin*)    PLATFORM="macos";;
    *)          
        echo "❌ Error: This script only supports Linux and macOS"
        echo "💡 For Windows, please use: scripts/windows_build.ps1"
        exit 1
        ;;
esac

echo "🚀 Building pandoc-ui for $PLATFORM..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install uv first."
    exit 1
fi

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
if [ -z "$VERSION" ]; then
    VERSION="dev"
fi

echo "📦 Building version: $VERSION"

# Set build directories
BUILD_DIR="build/$PLATFORM"
DIST_DIR="dist/$PLATFORM"
OUTPUT_FILE="pandoc-ui-$PLATFORM-$VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# Check if Nuitka is available
echo "🔍 Checking Nuitka availability..."
if ! uv run python -c "import nuitka" 2>/dev/null; then
    echo "📥 Installing Nuitka..."
    uv add --dev nuitka
fi

# Ensure PySide6 is available
echo "🔍 Checking PySide6 availability..."
if ! uv run python -c "import PySide6" 2>/dev/null; then
    echo "❌ Error: PySide6 not found. Please install it first."
    exit 1
fi

# Platform-specific preparations
if [ "$PLATFORM" = "linux" ]; then
    echo "🐧 Preparing Linux-specific build settings..."
    PLATFORM_EMOJI="🐧"
    PLATFORM_ARGS="--static-libpython=no"
    ICON_ARG=""
    
elif [ "$PLATFORM" = "macos" ]; then
    echo "🍎 Preparing macOS-specific build settings..."
    PLATFORM_EMOJI="🍎"
    
    # Detect macOS version and architecture
    MACOS_VERSION=$(sw_vers -productVersion | cut -d. -f1,2)
    ARCH=$(uname -m)
    echo "🔍 Detected macOS $MACOS_VERSION on $ARCH"
    
    # Set deployment target for compatibility
    export MACOSX_DEPLOYMENT_TARGET="10.14"  # Support macOS Mojave and later
    
    PLATFORM_ARGS="--macos-target-arch=$ARCH"
    
    # Look for icon file
    ICON_ARG=""
    if [ -f "resources/icons/app.icns" ]; then
        ICON_ARG="--macos-app-icon=resources/icons/app.icns"
        echo "🎨 Found icon: resources/icons/app.icns"
    elif [ -f "assets/app.icns" ]; then
        ICON_ARG="--macos-app-icon=assets/app.icns"
        echo "🎨 Found icon: assets/app.icns"
    elif [ -f "icon.icns" ]; then
        ICON_ARG="--macos-app-icon=icon.icns"
        echo "🎨 Found icon: icon.icns"
    else
        echo "ℹ️  No icon found, building without custom icon"
    fi
    
    # Check for code signing
    if command -v security &> /dev/null; then
        SIGNING_IDENTITY=$(security find-identity -v -p codesigning | grep -E "Developer ID Application|Apple Development" | head -n1 | awk '{print $2}' || echo "")
        if [ ! -z "$SIGNING_IDENTITY" ]; then
            echo "🔐 Found signing identity: $SIGNING_IDENTITY"
            PLATFORM_ARGS="$PLATFORM_ARGS --macos-sign-identity=$SIGNING_IDENTITY"
        else
            echo "ℹ️  No signing identity found, building unsigned binary"
        fi
    fi
fi

# Build with Nuitka
echo "🔨 Building with Nuitka..."

NUITKA_ARGS=(
    --onefile
    --enable-plugin=pyside6
    --disable-console
    --output-dir="$DIST_DIR"
    --output-filename="$OUTPUT_FILE"
    --company-name="pandoc-ui"
    --product-name="Pandoc UI"
    --file-version="$VERSION"
    --product-version="$VERSION"
    --file-description="Graphical interface for Pandoc document conversion"
    --copyright="MIT License"
    --assume-yes-for-downloads
    --show-progress
    --show-memory
)

# Add platform-specific arguments
if [ ! -z "$PLATFORM_ARGS" ]; then
    NUITKA_ARGS+=($PLATFORM_ARGS)
fi

# Add icon if found (macOS)
if [ ! -z "$ICON_ARG" ]; then
    NUITKA_ARGS+=($ICON_ARG)
fi

# Add entry point
uv run python -m nuitka "${NUITKA_ARGS[@]}" pandoc_ui/main.py

# Check if build was successful
if [ -f "$DIST_DIR/$OUTPUT_FILE" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📁 Output: $DIST_DIR/$OUTPUT_FILE"
    
    # Get file size
    FILE_SIZE=$(du -h "$DIST_DIR/$OUTPUT_FILE" | cut -f1)
    echo "📊 File size: $FILE_SIZE"
    
    # Make executable
    chmod +x "$DIST_DIR/$OUTPUT_FILE"
    
    # Test if the executable works
    echo "🧪 Testing executable..."
    if "$DIST_DIR/$OUTPUT_FILE" --help > /dev/null 2>&1; then
        echo "✅ Executable test passed"
    else
        echo "⚠️  Executable test failed, but build completed"
    fi
    
    # Platform-specific post-build checks
    if [ "$PLATFORM" = "macos" ]; then
        # Check if binary is properly signed (for distribution)
        if command -v codesign &> /dev/null; then
            echo "🔍 Checking code signature..."
            if codesign -dv "$DIST_DIR/$OUTPUT_FILE" 2>/dev/null; then
                echo "✅ Binary is signed"
            else
                echo "ℹ️  Binary is not signed (required for distribution outside App Store)"
            fi
        fi
    fi
    
    echo ""
    echo "$PLATFORM_EMOJI $PLATFORM build completed successfully!"
    echo "📦 Package: $DIST_DIR/$OUTPUT_FILE"
    echo ""
    
    # Platform-specific distribution notes
    if [ "$PLATFORM" = "linux" ]; then
        echo "💡 To distribute:"
        echo "   - Copy the executable to target Linux systems"
        echo "   - Ensure target systems have basic GUI libraries (Qt will be bundled)"
        echo "   - No Python installation required on target systems"
    elif [ "$PLATFORM" = "macos" ]; then
        echo "💡 To distribute:"
        echo "   - Copy the executable to target macOS systems"
        echo "   - For wider distribution, consider code signing with Apple Developer account"
        echo "   - Users may need to allow execution in System Preferences > Security & Privacy"
        echo "   - No Python installation required on target systems"
        echo ""
        echo "🔧 Architecture compatibility:"
        echo "   - Built for: $ARCH"
        echo "   - Deployment target: $MACOSX_DEPLOYMENT_TARGET+"
    fi
    
else
    echo "❌ Build failed! Output file not found."
    exit 1
fi