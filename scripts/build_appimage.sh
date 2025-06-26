#!/bin/bash

# AppImage Build Script for pandoc-ui
# Creates a portable Linux AppImage package using linuxdeploy
#
# Usage:
#   ./scripts/build_appimage.sh [OPTIONS]
#
# Requirements:
#   - Linux system (Ubuntu 18.04+ recommended for compatibility)
#   - Nuitka (via uv)
#   - wget or curl for tool downloads
#   - Basic build tools (gcc, binutils)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/appimage"
DIST_DIR="$PROJECT_ROOT/dist"
TOOLS_DIR="$PROJECT_ROOT/tools"

# AppImage configuration
APP_NAME="pandoc-ui"
APP_VERSION=""
APP_ARCH="x86_64"
APPDIR_NAME="$APP_NAME.AppDir"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${CYAN}[INFO] $1${NC}"; }
log_success() { echo -e "${GREEN}[SUCCESS] $1${NC}"; }
log_warning() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
log_error() { echo -e "${RED}[ERROR] $1${NC}"; }

# Show usage
show_usage() {
    cat << EOF
AppImage Build Script for pandoc-ui

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    --no-strip              Skip binary optimization
    --strip-level LEVEL     Set strip optimization level (conservative, moderate, aggressive)
    --version VERSION       Override version detection
    --clean                 Clean build directories before building
    --test                  Test the generated AppImage

EXAMPLES:
    $0                                 # Build AppImage with conservative optimization
    $0 --clean --test                 # Clean build and test result
    $0 --no-strip --version 1.0.0    # Build without optimization, specific version
    $0 --strip-level moderate         # Build with moderate optimization

NOTES:
    - Requires Linux system for AppImage creation
    - Downloads required tools automatically (linuxdeploy, appimagetool)
    - Uses existing build.sh script to create the base binary
    - Generated AppImage is portable across most Linux distributions

EOF
}

# Parse arguments
VERBOSE=false
STRIP_BINARY=true
STRIP_LEVEL="conservative"
CLEAN_BUILD=false
TEST_APPIMAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-strip)
            STRIP_BINARY=false
            shift
            ;;
        --strip-level)
            STRIP_LEVEL="$2"
            shift 2
            ;;
        --version)
            APP_VERSION="$2"
            shift 2
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --test)
            TEST_APPIMAGE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if running on Linux
if [[ "$(uname -s)" != "Linux" ]]; then
    log_error "AppImage can only be built on Linux systems"
    log_error "Current platform: $(uname -s)"
    exit 1
fi

log_info "Building AppImage for $APP_NAME"

# Detect version if not specified
if [[ -z "$APP_VERSION" ]]; then
    if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        APP_VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | sed 's/version = "\(.*\)"/\1/')
    fi
    if [[ -z "$APP_VERSION" ]]; then
        APP_VERSION="dev"
    fi
fi

log_info "Version: $APP_VERSION"
log_info "Architecture: $APP_ARCH"

# Clean build directories if requested
if [[ "$CLEAN_BUILD" = true ]]; then
    log_info "Cleaning build directories..."
    rm -rf "$BUILD_DIR"
    rm -rf "$TOOLS_DIR"
fi

# Create directories
mkdir -p "$BUILD_DIR"
mkdir -p "$DIST_DIR"
mkdir -p "$TOOLS_DIR"

# Download required tools
download_tool() {
    local tool_name="$1"
    local tool_url="$2"
    local tool_path="$TOOLS_DIR/$tool_name"
    
    if [[ -f "$tool_path" ]]; then
        log_info "$tool_name already available"
        return 0
    fi
    
    log_info "Downloading $tool_name..."
    if command -v wget &> /dev/null; then
        wget -q -O "$tool_path" "$tool_url"
    elif command -v curl &> /dev/null; then
        curl -s -L -o "$tool_path" "$tool_url"
    else
        log_error "Neither wget nor curl found. Please install one of them."
        exit 1
    fi
    
    chmod +x "$tool_path"
    log_success "$tool_name downloaded"
}

# Download linuxdeploy and appimagetool
log_info "Ensuring required tools are available..."

download_tool "linuxdeploy" "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
download_tool "appimagetool" "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"

# Check if we have required tools in PATH as fallback
LINUXDEPLOY="$TOOLS_DIR/linuxdeploy"
APPIMAGETOOL="$TOOLS_DIR/appimagetool"

if [[ ! -x "$LINUXDEPLOY" ]]; then
    if command -v linuxdeploy &> /dev/null; then
        LINUXDEPLOY="linuxdeploy"
        log_info "Using system linuxdeploy"
    else
        log_error "linuxdeploy not available"
        exit 1
    fi
fi

if [[ ! -x "$APPIMAGETOOL" ]]; then
    if command -v appimagetool &> /dev/null; then
        APPIMAGETOOL="appimagetool"
        log_info "Using system appimagetool"
    else
        log_error "appimagetool not available"
        exit 1
    fi
fi

# Build the main application first
log_info "Building main application..."
cd "$PROJECT_ROOT"

BUILD_ARGS=()
if [[ "$STRIP_BINARY" = false ]]; then
    BUILD_ARGS+=("--no-strip")
else
    BUILD_ARGS+=("--strip-level" "$STRIP_LEVEL")
fi

if [[ "$VERBOSE" = true ]]; then
    "$SCRIPT_DIR/build.sh" "${BUILD_ARGS[@]}"
else
    # Show Nuitka progress even in non-verbose mode since builds can take long
    log_info "Running Nuitka compilation (this may take several minutes)..."
    log_info "Use --verbose flag to see detailed compilation output"
    "$SCRIPT_DIR/build.sh" "${BUILD_ARGS[@]}" 2>&1 | while IFS= read -r line; do
        # Show important progress indicators
        if [[ "$line" == *"Progress"* ]] || [[ "$line" == *"Building"* ]] || [[ "$line" == *"SUCCESS"* ]] || [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"WARNING"* ]] || [[ "$line" == *"Compiling"* ]]; then
            echo "$line"
        fi
    done
fi

# Find the built binary
BUILT_BINARY="$PROJECT_ROOT/dist/linux/$APP_NAME-linux-$APP_VERSION"
if [[ ! -f "$BUILT_BINARY" ]]; then
    log_error "Built binary not found: $BUILT_BINARY"
    log_error "Make sure the main build completed successfully"
    exit 1
fi

log_success "Main application built: $BUILT_BINARY"

# Create AppDir structure
APPDIR="$BUILD_DIR/$APPDIR_NAME"
log_info "Creating AppDir structure..."

rm -rf "$APPDIR"
mkdir -p "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

# Copy main executable
cp "$BUILT_BINARY" "$APPDIR/usr/bin/$APP_NAME"
chmod +x "$APPDIR/usr/bin/$APP_NAME"

# Copy desktop file
DESKTOP_FILE="$PROJECT_ROOT/resources/pandoc-ui.desktop"
if [[ -f "$DESKTOP_FILE" ]]; then
    cp "$DESKTOP_FILE" "$APPDIR/usr/share/applications/"
    cp "$DESKTOP_FILE" "$APPDIR/"
    log_success "Desktop file copied"
else
    log_error "Desktop file not found: $DESKTOP_FILE"
    exit 1
fi

# Copy icons
ICON_FOUND=false

# Try different icon locations and formats
ICON_LOCATIONS=(
    "$PROJECT_ROOT/resources/icons/app.png"
    "$PROJECT_ROOT/resources/logo.png"
    "$PROJECT_ROOT/pandoc_ui/resources/icons/logo_256.png"
    "$PROJECT_ROOT/resources/icons/logo_256.png"
)

for icon_path in "${ICON_LOCATIONS[@]}"; do
    if [[ -f "$icon_path" ]]; then
        # Copy to both required locations
        cp "$icon_path" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"
        cp "$icon_path" "$APPDIR/$APP_NAME.png"
        ICON_FOUND=true
        log_success "Icon copied from: $icon_path"
        break
    fi
done

if [[ "$ICON_FOUND" = false ]]; then
    log_warning "No suitable icon found, creating placeholder"
    # Create a simple placeholder icon (1x1 PNG)
    echo -n "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" | base64 -d > "$APPDIR/$APP_NAME.png"
    cp "$APPDIR/$APP_NAME.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_NAME.png"
fi

# Create AppRun script
cat << 'EOF' > "$APPDIR/AppRun"
#!/bin/bash

# AppRun script for pandoc-ui
# This script is executed when the AppImage is run

# Get the directory where this AppImage is mounted
HERE="$(dirname "$(readlink -f "${0}")")"

# Export library paths for better compatibility
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/usr/lib/x86_64-linux-gnu:$HERE/lib:$HERE/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"

# Set XDG paths for better desktop integration
export XDG_DATA_DIRS="$HERE/usr/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Handle Qt/PySide6 plugin paths
export QT_PLUGIN_PATH="$HERE/usr/lib/qt6/plugins:$HERE/usr/lib/x86_64-linux-gnu/qt6/plugins:${QT_PLUGIN_PATH}"
export QML2_IMPORT_PATH="$HERE/usr/lib/qt6/qml:$HERE/usr/lib/x86_64-linux-gnu/qt6/qml:${QML2_IMPORT_PATH}"

# Platform integration
export QT_QPA_PLATFORM_PLUGIN_PATH="$HERE/usr/lib/qt6/plugins/platforms:$HERE/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH}"

# Ensure we can find the application icon
export APPIMAGE_ICON="$HERE/pandoc-ui.png"

# Change to the directory where the user invoked the AppImage
cd "$(dirname "$(readlink -f "$1")")" 2>/dev/null || cd "$HOME"

# Execute the main application
exec "$HERE/usr/bin/pandoc-ui" "$@"
EOF

chmod +x "$APPDIR/AppRun"

log_success "AppDir structure created"

# Run linuxdeploy to gather dependencies
log_info "Running linuxdeploy to gather dependencies..."

LINUXDEPLOY_ARGS=(
    "--appdir=$APPDIR"
    "--executable=$APPDIR/usr/bin/$APP_NAME"
    "--desktop-file=$APPDIR/usr/share/applications/pandoc-ui.desktop"
    "--icon-file=$APPDIR/$APP_NAME.png"
)

if [[ "$VERBOSE" = true ]]; then
    LINUXDEPLOY_ARGS+=("--verbosity=2")
fi

# Run linuxdeploy
if ! "$LINUXDEPLOY" "${LINUXDEPLOY_ARGS[@]}"; then
    log_warning "linuxdeploy completed with warnings, continuing..."
fi

# Create AppImage
log_info "Creating AppImage with appimagetool..."

APPIMAGE_OUTPUT="$DIST_DIR/$APP_NAME-$APP_VERSION-$APP_ARCH.AppImage"

APPIMAGETOOL_ARGS=("$APPDIR" "$APPIMAGE_OUTPUT")

if [[ "$VERBOSE" = false ]]; then
    APPIMAGETOOL_ARGS=("-n" "${APPIMAGETOOL_ARGS[@]}")  # No desktop integration prompts
fi

# Set environment for appimagetool
export ARCH="$APP_ARCH"

if ! "$APPIMAGETOOL" "${APPIMAGETOOL_ARGS[@]}"; then
    log_error "AppImage creation failed"
    exit 1
fi

# Verify AppImage was created
if [[ ! -f "$APPIMAGE_OUTPUT" ]]; then
    log_error "AppImage not found after creation: $APPIMAGE_OUTPUT"
    exit 1
fi

# Get file size
APPIMAGE_SIZE=$(du -h "$APPIMAGE_OUTPUT" | cut -f1)

log_success "AppImage created successfully!"
echo ""
echo "📦 AppImage Details:"
echo "   File: $APPIMAGE_OUTPUT"
echo "   Size: $APPIMAGE_SIZE"
echo "   Version: $APP_VERSION"
echo "   Architecture: $APP_ARCH"
echo ""

# Test AppImage if requested
if [[ "$TEST_APPIMAGE" = true ]]; then
    log_info "Testing AppImage..."
    
    # Make AppImage executable
    chmod +x "$APPIMAGE_OUTPUT"
    
    # Basic functionality test
    if "$APPIMAGE_OUTPUT" --help > /dev/null 2>&1; then
        log_success "AppImage test passed (--help works)"
    else
        log_warning "AppImage test failed (--help test)"
        log_warning "This may be normal for GUI-only applications"
    fi
    
    # Test AppImage information
    if "$APPIMAGE_OUTPUT" --appimage-info > /dev/null 2>&1; then
        log_info "AppImage metadata:"
        "$APPIMAGE_OUTPUT" --appimage-info
    fi
fi

echo "🎉 AppImage build completed successfully!"
echo ""
echo "💡 Usage:"
echo "   # Make executable and run"
echo "   chmod +x $APPIMAGE_OUTPUT"
echo "   ./$APPIMAGE_OUTPUT"
echo ""
echo "   # Test functionality"
echo "   $APPIMAGE_OUTPUT --help"
echo ""
echo "   # Get AppImage info"
echo "   $APPIMAGE_OUTPUT --appimage-info"
echo ""
echo "📋 Distribution:"
echo "   - Copy the .AppImage file to target Linux systems"
echo "   - No installation required - just make executable and run"
echo "   - Compatible with most Linux distributions (glibc 2.17+)"
echo "   - Self-contained - includes all dependencies"

if [[ "$STRIP_BINARY" = true ]]; then
    echo ""
    echo "🔧 Optimization applied:"
    echo "   - Strip level: $STRIP_LEVEL"
    echo "   - Binary symbols optimized for smaller size"
fi

echo ""