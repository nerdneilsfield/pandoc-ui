#!/bin/bash

# Unix build script for pandoc-ui (Linux and macOS)
# For Windows, use scripts/windows_build.ps1

set -e

# Get script directory for relative paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
OPTIMIZE_BINARY=true
STRIP_LEVEL="conservative"
BUILD_APPIMAGE=false
BUILD_MODE="onefile"  # Default to onefile, standalone for packaging
HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-strip)
            OPTIMIZE_BINARY=false
            shift
            ;;
        --strip-level)
            STRIP_LEVEL="$2"
            shift 2
            ;;
        --appimage)
            BUILD_APPIMAGE=true
            shift
            ;;
        --standalone)
            BUILD_MODE="standalone"
            shift
            ;;
        --help|-h)
            HELP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            HELP=true
            shift
            ;;
    esac
done

if [[ "$HELP" = true ]]; then
    cat << EOF
Unix Build Script for pandoc-ui

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --no-strip              Skip binary optimization with strip
    --strip-level LEVEL     Set strip optimization level (conservative, moderate, aggressive)
                           Default: conservative
    --appimage              Build AppImage after creating binary (Linux only)
    --standalone            Use standalone mode instead of onefile (recommended for packaging)
    --help, -h              Show this help message

STRIP LEVELS:
    conservative           Safe for PySide6 applications (5-15% reduction)
    moderate              Test before production (10-25% reduction)  
    aggressive            High risk for Qt apps (15-40% reduction)

EXAMPLES:
    $0                                    # Build with conservative optimization
    $0 --no-strip                        # Build without optimization
    $0 --strip-level moderate           # Build with moderate optimization
    $0 --appimage                        # Build binary and create AppImage
    $0 --appimage --strip-level moderate # Build optimized AppImage

NOTES:
    - AppImage creation requires Linux and downloads required tools automatically
    - AppImage includes all dependencies and runs on most Linux distributions
    - Use --appimage for distribution-ready Linux packages

EOF
    exit 0
fi

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

# Generate translations if needed
echo "🌍 Ensuring translations are up to date..."
NEED_TRANSLATIONS=false

# Check if .qm files exist
for lang in zh_CN en_US ja_JP; do
    qm_file="pandoc_ui/translations/pandoc_ui_$lang.qm"
    ts_file="pandoc_ui/translations/pandoc_ui_$lang.ts"
    
    if [ ! -f "$qm_file" ] || ([ -f "$ts_file" ] && [ "$ts_file" -nt "$qm_file" ]); then
        NEED_TRANSLATIONS=true
        break
    fi
done

if [ "$NEED_TRANSLATIONS" = true ]; then
    echo "📦 Generating translations..."
    ./scripts/generate_translations.sh
else
    echo "✅ Translations are up to date"
fi

# Generate Qt resources if needed
echo "🎨 Ensuring Qt resources are up to date..."
if [ ! -f "pandoc_ui/resources/resources_rc.py" ] || [ "pandoc_ui/resources/resources.qrc" -nt "pandoc_ui/resources/resources_rc.py" ]; then
    echo "📦 Generating Qt resources..."
    ./scripts/generate_resources.sh
else
    echo "✅ Qt resources are up to date"
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
    --${BUILD_MODE}
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
    --include-data-file=pandoc_ui/gui/main_window.ui=pandoc_ui/gui/main_window.ui
    --include-data-dir=pandoc_ui/resources=pandoc_ui/resources
)

# Add optimization flags based on strip level (Nuitka build-time optimization)
# Note: LTO is enabled by default for all levels as it's safe and effective
NUITKA_ARGS+=(--lto=yes)

case "$STRIP_LEVEL" in
    conservative)
        # Default Nuitka behavior with LTO
        echo "🔧 Using conservative optimization (LTO enabled)"
        ;;
    moderate)
        # Add additional moderate optimizations
        echo "🔧 Using moderate optimization (LTO + enhanced optimizations)"
        # Additional flags can be added here as Nuitka develops
        ;;
    aggressive)
        # Maximum optimization
        echo "🔧 Using aggressive optimization (LTO + maximum optimizations)"
        # More aggressive flags can be added here as Nuitka develops
        ;;
esac

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
BUILD_SUCCESS=false

echo "🔍 Checking build output in $DIST_DIR..."
echo "Expected output file/dir: $OUTPUT_FILE"
echo "Contents of $DIST_DIR:"
ls -la "$DIST_DIR/" || echo "Directory does not exist"

if [ "$BUILD_MODE" = "standalone" ]; then
    # For standalone mode, Nuitka might create different directory structures
    # Try multiple possible locations
    POSSIBLE_PATHS=(
        "$DIST_DIR/$OUTPUT_FILE"           # Our expected path
        "$DIST_DIR/$OUTPUT_FILE.dist"      # Nuitka default with .dist suffix
        "$DIST_DIR/main.dist"              # Default when using main.py
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [ -d "$path" ]; then
            echo "✅ Found standalone directory: $path"
            BUILD_SUCCESS=true
            OUTPUT_PATH="$path"
            
            # Look for executable inside the directory
            POSSIBLE_EXECUTABLES=(
                "$path/$OUTPUT_FILE"
                "$path/main"
                "$path/pandoc_ui"
                "$path/$(basename "$path")"
            )
            
            for exe in "${POSSIBLE_EXECUTABLES[@]}"; do
                if [ -f "$exe" ] && [ -x "$exe" ]; then
                    echo "✅ Found executable: $exe"
                    EXECUTABLE_PATH="$exe"
                    break
                fi
            done
            
            # If no specific executable found, find any executable
            if [ -z "$EXECUTABLE_PATH" ]; then
                EXECUTABLE_PATH=$(find "$path" -type f -executable | head -1)
                if [ -n "$EXECUTABLE_PATH" ]; then
                    echo "✅ Found executable: $EXECUTABLE_PATH"
                fi
            fi
            break
        fi
    done
else
    # For onefile mode, check for single executable file
    POSSIBLE_FILES=(
        "$DIST_DIR/$OUTPUT_FILE"
        "$DIST_DIR/$OUTPUT_FILE.exe"
        "$DIST_DIR/main"
        "$DIST_DIR/main.exe"
    )
    
    for file in "${POSSIBLE_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "✅ Found onefile executable: $file"
            BUILD_SUCCESS=true
            OUTPUT_PATH="$file"
            EXECUTABLE_PATH="$file"
            break
        fi
    done
fi

if [ "$BUILD_SUCCESS" = false ]; then
    echo "❌ No build output found. Checking for any pandoc-ui related files..."
    find "$DIST_DIR" -name "*pandoc*" -o -name "*main*" 2>/dev/null || echo "No related files found"
fi

if [ "$BUILD_SUCCESS" = true ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📁 Output: $OUTPUT_PATH"
    
    # Get file size
    if [ "$BUILD_MODE" = "standalone" ]; then
        DIR_SIZE=$(du -sh "$OUTPUT_PATH" | cut -f1)
        echo "📊 Directory size: $DIR_SIZE"
        echo "📄 Executable: $EXECUTABLE_PATH"
    else
        FILE_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
        echo "📊 File size: $FILE_SIZE"
    fi
    
    # Make executable
    chmod +x "$EXECUTABLE_PATH"
    
    # Test if the executable works before optimization
    echo "🧪 Testing executable..."
    if "$EXECUTABLE_PATH" --help > /dev/null 2>&1; then
        echo "✅ Executable test passed"
        EXECUTABLE_WORKS=true
    else
        echo "⚠️  Executable test failed, but build completed"
        EXECUTABLE_WORKS=false
    fi
    
    # Binary optimization with strip (WARNING: NOT for onefile binaries)
    if [[ "$OPTIMIZE_BINARY" = true ]]; then
        echo ""
        echo "ℹ️  Post-build optimization analysis..."
        
        # Detect if this is a Nuitka onefile binary
        if strings "$EXECUTABLE_PATH" | grep -q "NUITKA_ONEFILE_PARENT\|__onefile_tmpdir__\|attached.*data"; then
            echo "🔍 Detected Nuitka onefile binary"
            echo "⚠️  Post-build stripping DISABLED for onefile binaries"
            echo "💡 Nuitka onefile binaries contain attached data that would be corrupted by strip"
            echo "💡 Optimization was applied during Nuitka build process instead"
            
            case "$STRIP_LEVEL" in
                conservative)
                    echo "✅ Conservative optimization: Nuitka LTO + default stripping applied"
                    ;;
                moderate)
                    echo "✅ Moderate optimization: Nuitka LTO + enhanced optimizations applied"
                    ;;
                aggressive)
                    echo "✅ Aggressive optimization: Nuitka LTO + maximum optimizations applied"
                    ;;
            esac
        else
            echo "🔍 Detected standalone binary - post-build stripping available"
            echo "🔧 Applying post-build strip optimization (level: $STRIP_LEVEL)..."
            
            # Check if strip optimization script exists
            STRIP_SCRIPT="scripts/strip_optimize.sh"
            if [[ -f "$STRIP_SCRIPT" ]]; then
                # Make strip script executable
                chmod +x "$STRIP_SCRIPT"
                
                # Run strip optimization
                if [[ "$EXECUTABLE_WORKS" = true ]]; then
                    # Use verification if the executable was working before
                    "$STRIP_SCRIPT" --verify "$EXECUTABLE_PATH" "$STRIP_LEVEL"
                else
                    # Skip verification if executable wasn't working before
                    "$STRIP_SCRIPT" "$EXECUTABLE_PATH" "$STRIP_LEVEL"
                fi
                
                # Update file size after optimization
                if [ "$BUILD_MODE" = "standalone" ]; then
                    DIR_SIZE=$(du -sh "$OUTPUT_PATH" | cut -f1)
                    echo "📊 Optimized directory size: $DIR_SIZE"
                else
                    FILE_SIZE=$(du -h "$OUTPUT_PATH" | cut -f1)
                    echo "📊 Optimized file size: $FILE_SIZE"
                fi
            else
                echo "⚠️  Strip optimization script not found: $STRIP_SCRIPT"
                echo "💡 Post-build strip optimization skipped"
            fi
        fi
    else
        echo ""
        echo "ℹ️  Binary optimization skipped (--no-strip specified)"
        echo "💡 Note: Nuitka applies default optimizations during build regardless"
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
        if [[ "$OPTIMIZE_BINARY" = true ]]; then
            echo ""
            echo "🔧 Optimization applied:"
            echo "   - Strip level: $STRIP_LEVEL"
            echo "   - Binary symbols optimized for smaller size"
        fi
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
        if [[ "$OPTIMIZE_BINARY" = true ]]; then
            echo ""
            echo "🔧 Optimization applied:"
            echo "   - Strip level: $STRIP_LEVEL"
            echo "   - Binary symbols optimized for smaller size"
        fi
    fi
    
    # AppImage creation (Linux only)
    if [[ "$BUILD_APPIMAGE" = true ]]; then
        if [[ "$PLATFORM" = "linux" ]]; then
            echo ""
            echo "📦 Creating AppImage..."
            
            # Check if AppImage build script exists
            APPIMAGE_SCRIPT="scripts/build_appimage.sh"
            if [[ -f "$APPIMAGE_SCRIPT" ]]; then
                # Make AppImage script executable
                chmod +x "$APPIMAGE_SCRIPT"
                
                # Prepare AppImage build arguments
                APPIMAGE_ARGS=("--version" "$VERSION")
                
                if [[ "$OPTIMIZE_BINARY" = false ]]; then
                    APPIMAGE_ARGS+=("--no-strip")
                else
                    APPIMAGE_ARGS+=("--strip-level" "$STRIP_LEVEL")
                fi
                
                # Run AppImage build (it will use our already built binary)
                "$APPIMAGE_SCRIPT" "${APPIMAGE_ARGS[@]}"
                
                if [[ $? -eq 0 ]]; then
                    # Find the created AppImage
                    APPIMAGE_FILE="$DIST_DIR/pandoc-ui-$VERSION-x86_64.AppImage"
                    if [[ -f "$APPIMAGE_FILE" ]]; then
                        APPIMAGE_SIZE=$(du -h "$APPIMAGE_FILE" | cut -f1)
                        echo ""
                        echo "✅ AppImage created successfully!"
                        echo "📁 AppImage: $APPIMAGE_FILE"
                        echo "📊 AppImage size: $APPIMAGE_SIZE"
                        echo ""
                        echo "💡 AppImage distribution:"
                        echo "   - Copy the .AppImage file to target Linux systems"
                        echo "   - Make executable: chmod +x $(basename "$APPIMAGE_FILE")"
                        echo "   - Run directly: ./$(basename "$APPIMAGE_FILE")"
                        echo "   - No installation required"
                        echo "   - Self-contained with all dependencies"
                    else
                        echo "⚠️  AppImage file not found after build"
                    fi
                else
                    echo "⚠️  AppImage creation failed, but main build succeeded"
                fi
            else
                echo "⚠️  AppImage build script not found: $APPIMAGE_SCRIPT"
                echo "💡 AppImage creation skipped"
            fi
        else
            echo ""
            echo "⚠️  AppImage creation is only supported on Linux"
            echo "💡 Current platform: $PLATFORM"
            echo "💡 AppImage creation skipped"
        fi
    fi
    
else
    echo "❌ Build failed! Output file not found."
    exit 1
fi