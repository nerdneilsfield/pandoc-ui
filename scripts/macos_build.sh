#!/bin/bash

# macOS Build Script for pandoc-ui
# Creates unsigned universal binary DMG for open source distribution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="Pandoc UI"
BUNDLE_ID="com.pandoc-ui.app"
VERSION="1.0.0"
DIST_DIR="dist"
BUILD_DIR="build"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPTS_DIR")"

# Parse command line arguments
UNIVERSAL=false
CREATE_DMG=true
CLEAN_BUILD=false
STRIP_LEVEL="none"

while [[ $# -gt 0 ]]; do
    case $1 in
        --universal)
            UNIVERSAL=true
            shift
            ;;
        --no-dmg)
            CREATE_DMG=false
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --strip-level)
            STRIP_LEVEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --universal     Build universal binary (ARM64 + Intel)"
            echo "  --no-dmg        Skip DMG creation"
            echo "  --clean         Clean build directories first"
            echo "  --strip-level   Optimization level (none|conservative|moderate|aggressive)"
            echo "  --help          Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        log_error "This script must be run on macOS"
        exit 1
    fi
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        log_error "uv is not installed. Please install uv first."
        exit 1
    fi
    
    # Check if we're in a project directory
    if [[ ! -f "$PROJECT_ROOT/pyproject.toml" ]]; then
        log_error "pyproject.toml not found. Please run from project root."
        exit 1
    fi
    
    # Check if hdiutil is available (for DMG creation)
    if [[ "$CREATE_DMG" == true ]] && ! command -v hdiutil &> /dev/null; then
        log_error "hdiutil not found. DMG creation requires macOS."
        exit 1
    fi
    
    log_success "Dependencies check passed"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Install PyInstaller if not already installed
    if ! uv pip list | grep -q pyinstaller; then
        log_info "Installing PyInstaller..."
        uv add --dev pyinstaller
    fi
    
    # Install dmgbuild if not already installed and DMG creation is enabled
    if [[ "$CREATE_DMG" == true ]] && ! uv pip list | grep -q dmgbuild; then
        log_info "Installing dmgbuild..."
        uv add --dev dmgbuild
    fi
    
    log_success "Dependencies installed"
}

# Clean build directories
clean_build() {
    if [[ "$CLEAN_BUILD" == true ]]; then
        log_info "Cleaning build directories..."
        rm -rf "$PROJECT_ROOT/$BUILD_DIR"
        rm -rf "$PROJECT_ROOT/$DIST_DIR"
        log_success "Build directories cleaned"
    fi
}

# Generate app icon
generate_icon() {
    log_info "Generating app icon..."
    
    ICON_DIR="$PROJECT_ROOT/resources/icons"
    ICONSET_DIR="$ICON_DIR/app.iconset"
    
    if [[ -d "$ICONSET_DIR" ]]; then
        # Convert iconset to icns
        iconutil -c icns "$ICONSET_DIR" -o "$ICON_DIR/app.icns"
        log_success "App icon generated: $ICON_DIR/app.icns"
    else
        log_warning "Iconset not found at $ICONSET_DIR. Using default icon."
    fi
}

# Build with PyInstaller
build_app() {
    log_info "Building application with PyInstaller..."
    
    cd "$PROJECT_ROOT"
    
    # Prepare build arguments
    BUILD_ARGS=(
        --name="$APP_NAME"
        --windowed
        --onedir
        --distpath="$DIST_DIR"
        --workpath="$BUILD_DIR"
        --specpath="$BUILD_DIR"
    )
    
    # Add universal binary support if requested
    if [[ "$UNIVERSAL" == true ]]; then
        BUILD_ARGS+=(--target-arch=universal2)
        log_info "Building universal binary (ARM64 + Intel)"
    else
        log_info "Building for current architecture"
    fi
    
    # Add icon if available
    if [[ -f "resources/icons/app.icns" ]]; then
        BUILD_ARGS+=(--icon=resources/icons/app.icns)
    fi
    
    # Add data files
    BUILD_ARGS+=(
        --add-data="resources:resources"
        --add-data="pandoc_ui/locales:pandoc_ui/locales"
    )
    
    # Add hidden imports for PySide6
    BUILD_ARGS+=(
        --hidden-import=PySide6.QtCore
        --hidden-import=PySide6.QtGui
        --hidden-import=PySide6.QtWidgets
        --collect-submodules=PySide6
    )
    
    # Run PyInstaller
    uv run pyinstaller "${BUILD_ARGS[@]}" pandoc_ui/main.py
    
    if [[ $? -eq 0 ]]; then
        log_success "Application built successfully"
    else
        log_error "Build failed"
        exit 1
    fi
}

# Create DMG
create_dmg() {
    if [[ "$CREATE_DMG" == false ]]; then
        log_info "Skipping DMG creation"
        return
    fi
    
    log_info "Creating DMG..."
    
    cd "$PROJECT_ROOT"
    
    APP_PATH="$DIST_DIR/$APP_NAME.app"
    DMG_PATH="$DIST_DIR/pandoc-ui-macos.dmg"
    TEMP_DMG_PATH="$DIST_DIR/temp.dmg"
    
    if [[ ! -d "$APP_PATH" ]]; then
        log_error "App bundle not found at $APP_PATH"
        exit 1
    fi
    
    # Remove existing DMG
    rm -f "$DMG_PATH" "$TEMP_DMG_PATH"
    
    # Create temporary DMG
    hdiutil create -size 200m -fs HFS+ -volname "$APP_NAME" "$TEMP_DMG_PATH"
    
    # Mount temporary DMG
    MOUNT_POINT=$(hdiutil attach "$TEMP_DMG_PATH" | grep -E '^/dev/' | sed 1q | awk '{print $3}')
    
    if [[ -z "$MOUNT_POINT" ]]; then
        log_error "Failed to mount temporary DMG"
        exit 1
    fi
    
    # Copy app to DMG
    cp -R "$APP_PATH" "$MOUNT_POINT/"
    
    # Create Applications symlink
    ln -s /Applications "$MOUNT_POINT/Applications"
    
    # Create background and setup if available
    if [[ -f "$SCRIPTS_DIR/macos/background.png" ]]; then
        mkdir -p "$MOUNT_POINT/.background"
        cp "$SCRIPTS_DIR/macos/background.png" "$MOUNT_POINT/.background/"
    fi
    
    # Unmount temporary DMG
    hdiutil detach "$MOUNT_POINT"
    
    # Convert to compressed DMG
    hdiutil convert "$TEMP_DMG_PATH" -format UDZO -o "$DMG_PATH"
    
    # Clean up
    rm -f "$TEMP_DMG_PATH"
    
    if [[ -f "$DMG_PATH" ]]; then
        log_success "DMG created: $DMG_PATH"
    else
        log_error "DMG creation failed"
        exit 1
    fi
}

# Create installation instructions
create_readme() {
    log_info "Creating installation instructions..."
    
    README_PATH="$PROJECT_ROOT/$DIST_DIR/INSTALL_MACOS.md"
    
    cat > "$README_PATH" << 'EOF'
# macOS Installation Instructions

## Installing Pandoc UI

1. **Download**: Download the `pandoc-ui-macos.dmg` file
2. **Mount**: Double-click the DMG file to mount it
3. **Install**: Drag "Pandoc UI.app" to the Applications folder
4. **Eject**: Eject the DMG from Finder

## First Launch (Important!)

Since this app is unsigned, macOS will prevent it from opening initially. Follow these steps:

### Method 1: Right-click Override
1. Right-click on "Pandoc UI.app" in Applications
2. Select "Open" from the context menu
3. Click "Open" in the security dialog
4. The app will now open and be whitelisted for future launches

### Method 2: Terminal Command
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Pandoc UI.app"
```

### Method 3: System Preferences
1. Try to open the app normally (it will be blocked)
2. Go to System Preferences → Security & Privacy → General
3. Click "Open Anyway" next to the blocked app message
4. Confirm by clicking "Open"

## System Requirements

- macOS 10.15 (Catalina) or later
- Pandoc installed (the app will guide you if not installed)

## Troubleshooting

### App won't open after following steps above
- Make sure you're running macOS 10.15 or later
- Try restarting your Mac after installation
- Check Console.app for error messages

### Performance issues
- The first launch may be slower as macOS verifies the app
- Subsequent launches will be faster

### Pandoc not found
- Install Pandoc via Homebrew: `brew install pandoc`
- Or download from: https://pandoc.org/installing.html

## Support

For issues, please visit: https://github.com/your-username/pandoc-ui/issues
EOF

    log_success "Installation instructions created: $README_PATH"
}

# Main execution
main() {
    log_info "Starting macOS build for $APP_NAME v$VERSION"
    
    check_macos
    check_dependencies
    clean_build
    install_dependencies
    generate_icon
    build_app
    create_dmg
    create_readme
    
    log_success "Build completed successfully!"
    
    if [[ "$CREATE_DMG" == true ]]; then
        echo
        log_info "Distribution files created:"
        echo "  - $DIST_DIR/pandoc-ui-macos.dmg"
        echo "  - $DIST_DIR/INSTALL_MACOS.md"
        echo
        log_warning "IMPORTANT: This is an unsigned application."
        log_warning "Users will need to manually allow it in System Preferences."
        log_warning "See INSTALL_MACOS.md for detailed instructions."
    fi
}

# Run main function
main "$@"