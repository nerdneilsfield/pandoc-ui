#!/bin/bash

# Enhanced macOS Build Script for pandoc-ui
# Creates unsigned universal binary DMG using dmgbuild for better customization

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
USE_SPEC=false

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
        --use-spec)
            USE_SPEC=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --universal     Build universal binary (ARM64 + Intel)"
            echo "  --no-dmg        Skip DMG creation"
            echo "  --clean         Clean build directories first"
            echo "  --use-spec      Use PyInstaller spec file for more control"
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
    
    # Check if iconutil is available (for icon generation)
    if ! command -v iconutil &> /dev/null; then
        log_warning "iconutil not found. Icon generation may not work."
    fi
    
    log_success "Dependencies check passed"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Sync macOS dependencies
    uv sync --group macos
    
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
    ICNS_FILE="$ICON_DIR/app.icns"
    
    if [[ -d "$ICONSET_DIR" ]]; then
        if command -v iconutil &> /dev/null; then
            # Convert iconset to icns
            iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE"
            log_success "App icon generated: $ICNS_FILE"
        else
            log_warning "iconutil not available. Using existing icon if present."
        fi
    else
        log_warning "Iconset not found at $ICONSET_DIR. Using default icon."
    fi
}

# Build with PyInstaller using spec file
build_app_with_spec() {
    log_info "Building application with PyInstaller spec file..."
    
    cd "$PROJECT_ROOT"
    
    SPEC_FILE="$SCRIPTS_DIR/macos/pandoc-ui.spec"
    
    if [[ ! -f "$SPEC_FILE" ]]; then
        log_error "Spec file not found: $SPEC_FILE"
        exit 1
    fi
    
    # Build arguments for spec file
    BUILD_ARGS=(--distpath="$DIST_DIR" --workpath="$BUILD_DIR")
    
    if [[ "$UNIVERSAL" == true ]]; then
        log_info "Building universal binary (ARM64 + Intel)"
        # Note: Universal build needs to be configured in the spec file
    else
        log_info "Building for current architecture"
    fi
    
    # Run PyInstaller with spec file
    uv run pyinstaller "${BUILD_ARGS[@]}" "$SPEC_FILE"
    
    if [[ $? -eq 0 ]]; then
        log_success "Application built successfully with spec file"
    else
        log_error "Build failed"
        exit 1
    fi
}

# Build with PyInstaller using command line
build_app_cmdline() {
    log_info "Building application with PyInstaller command line..."
    
    cd "$PROJECT_ROOT"
    
    # Prepare build arguments
    BUILD_ARGS=(
        --name="$APP_NAME"
        --windowed
        --onedir
        --distpath="$DIST_DIR"
        --workpath="$BUILD_DIR"
        --specpath="$BUILD_DIR"
        --clean
    )
    
    # Add universal binary support if requested
    if [[ "$UNIVERSAL" == true ]]; then
        BUILD_ARGS+=(--target-arch=universal2)
        log_info "Building universal binary (ARM64 + Intel)"
    else
        log_info "Building for current architecture"
    fi
    
    # Add icon if available
    ICON_PATH="$PROJECT_ROOT/resources/icons/app.icns"
    if [[ -f "$ICON_PATH" ]]; then
        BUILD_ARGS+=(--icon="$ICON_PATH")
        log_info "Using app icon: $ICON_PATH"
    else
        log_warning "App icon not found at: $ICON_PATH"
    fi
    
    # Add data files (only if they exist) - use absolute paths
    RESOURCES_PATH="$PROJECT_ROOT/resources"
    LOCALES_PATH="$PROJECT_ROOT/pandoc_ui/locales"
    
    if [[ -d "$RESOURCES_PATH" ]]; then
        BUILD_ARGS+=(--add-data="$RESOURCES_PATH:resources")
        log_info "Including resources directory: $RESOURCES_PATH"
    else
        log_warning "Resources directory not found at: $RESOURCES_PATH"
    fi
    
    if [[ -d "$LOCALES_PATH" ]]; then
        BUILD_ARGS+=(--add-data="$LOCALES_PATH:pandoc_ui/locales")
        log_info "Including locales directory: $LOCALES_PATH"
    else
        log_warning "Locales directory not found at: $LOCALES_PATH"
    fi
    
    # Add hidden imports for PySide6
    BUILD_ARGS+=(
        --hidden-import=PySide6.QtCore
        --hidden-import=PySide6.QtGui
        --hidden-import=PySide6.QtWidgets
        --collect-submodules=PySide6
    )
    
    # Exclude unnecessary modules that may cause universal binary issues
    BUILD_ARGS+=(
        --exclude-module=mypy
        --exclude-module=pytest
        --exclude-module=black
        --exclude-module=ruff
        --exclude-module=isort
        --exclude-module=coverage
        --exclude-module=setuptools
        --exclude-module=pip
        --exclude-module=wheel
    )
    
    # Additional optimization
    BUILD_ARGS+=(
        --optimize=2
        --strip
    )
    
    # Debug: Show current directory and files
    log_info "Current directory: $(pwd)"
    log_info "Project root: $PROJECT_ROOT"
    
    # Run PyInstaller with absolute path to main script
    MAIN_SCRIPT="$PROJECT_ROOT/pandoc_ui/main.py"
    log_info "Main script: $MAIN_SCRIPT"
    
    uv run pyinstaller "${BUILD_ARGS[@]}" "$MAIN_SCRIPT"
    
    if [[ $? -eq 0 ]]; then
        log_success "Application built successfully"
    else
        if [[ "$UNIVERSAL" == true ]]; then
            log_warning "Universal binary build failed, trying current architecture only..."
            
            # Remove universal binary flag and retry
            NEW_BUILD_ARGS=()
            for arg in "${BUILD_ARGS[@]}"; do
                if [[ "$arg" != "--target-arch=universal2" ]]; then
                    NEW_BUILD_ARGS+=("$arg")
                fi
            done
            
            log_info "Retrying with current architecture only"
            uv run pyinstaller "${NEW_BUILD_ARGS[@]}" "$MAIN_SCRIPT"
            
            if [[ $? -eq 0 ]]; then
                log_success "Application built successfully (current architecture)"
                log_warning "Note: This is not a universal binary"
            else
                log_error "Build failed even with current architecture"
                exit 1
            fi
        else
            log_error "Build failed"
            exit 1
        fi
    fi
}

# Create DMG using dmgbuild
create_dmg_with_dmgbuild() {
    if [[ "$CREATE_DMG" == false ]]; then
        log_info "Skipping DMG creation"
        return
    fi
    
    log_info "Creating DMG with dmgbuild..."
    
    cd "$PROJECT_ROOT"
    
    APP_PATH="$DIST_DIR/$APP_NAME.app"
    DMG_PATH="$DIST_DIR/pandoc-ui-macos.dmg"
    SETTINGS_FILE="$SCRIPTS_DIR/macos/dmg_settings.py"
    
    if [[ ! -d "$APP_PATH" ]]; then
        log_error "App bundle not found at $APP_PATH"
        exit 1
    fi
    
    if [[ ! -f "$SETTINGS_FILE" ]]; then
        log_error "DMG settings file not found at $SETTINGS_FILE"
        exit 1
    fi
    
    # Remove existing DMG
    rm -f "$DMG_PATH"
    
    # Run dmgbuild
    uv run dmgbuild -s "$SETTINGS_FILE" "$APP_NAME" "$DMG_PATH"
    
    if [[ $? -eq 0 && -f "$DMG_PATH" ]]; then
        log_success "DMG created: $DMG_PATH"
        
        # Get DMG size
        DMG_SIZE=$(ls -lh "$DMG_PATH" | awk '{print $5}')
        log_info "DMG size: $DMG_SIZE"
    else
        log_error "DMG creation failed"
        exit 1
    fi
}

# Verify the app bundle
verify_app() {
    log_info "Verifying app bundle..."
    
    APP_PATH="$PROJECT_ROOT/$DIST_DIR/$APP_NAME.app"
    
    if [[ ! -d "$APP_PATH" ]]; then
        log_error "App bundle not found: $APP_PATH"
        return 1
    fi
    
    # Check Info.plist
    PLIST_PATH="$APP_PATH/Contents/Info.plist"
    if [[ -f "$PLIST_PATH" ]]; then
        log_success "Info.plist found"
    else
        log_warning "Info.plist missing"
    fi
    
    # Check executable
    EXEC_PATH="$APP_PATH/Contents/MacOS"
    if [[ -d "$EXEC_PATH" ]] && [[ -n "$(ls -A "$EXEC_PATH")" ]]; then
        log_success "Executable found"
    else
        log_warning "Executable missing"
    fi
    
    # Check icon
    ICON_PATH="$APP_PATH/Contents/Resources/app.icns"
    if [[ -f "$ICON_PATH" ]]; then
        log_success "App icon embedded"
    else
        log_warning "App icon missing"
    fi
    
    log_success "App bundle verification completed"
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

Since this app is **unsigned**, macOS will prevent it from opening initially. Follow these steps:

### Method 1: Right-click Override (Recommended)
1. Right-click on "Pandoc UI.app" in Applications
2. Select "Open" from the context menu
3. Click "Open" in the security dialog
4. The app will now open and be whitelisted for future launches

### Method 2: Terminal Command (Advanced)
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Pandoc UI.app"
```

### Method 3: System Preferences (Alternative)
1. Try to open the app normally (it will be blocked)
2. Go to System Preferences → Security & Privacy → General
3. Click "Open Anyway" next to the blocked app message
4. Confirm by clicking "Open"

## System Requirements

- **macOS**: 10.15 (Catalina) or later
- **Architecture**: Universal binary (supports both Intel and Apple Silicon Macs)
- **Pandoc**: Required for document conversion (app will guide installation if missing)

## Installing Pandoc

### Option 1: Homebrew (Recommended)
```bash
brew install pandoc
```

### Option 2: Direct Download
Visit https://pandoc.org/installing.html and download the macOS installer

### Option 3: MacPorts
```bash
sudo port install pandoc
```

## Troubleshooting

### App won't open after following security steps
- Ensure you're running macOS 10.15 or later
- Try restarting your Mac after installation
- Check Console.app for detailed error messages

### Performance issues
- The first launch may be slower as macOS verifies the app
- Subsequent launches will be faster
- Universal binary automatically uses optimal architecture

### Pandoc not detected
- Verify pandoc installation: `pandoc --version`
- Check PATH in Terminal: `echo $PATH`
- Restart the app after installing pandoc

### DMG won't mount
- Right-click DMG and select "Open With" → "DiskImageMounter"
- Check if DMG file was fully downloaded
- Try downloading again if corrupted

## Features

- **Universal Binary**: Optimized for both Intel and Apple Silicon Macs
- **Drag & Drop**: Easy file conversion
- **Batch Processing**: Convert multiple files at once
- **Format Support**: Markdown, LaTeX, HTML, DOCX, PDF, and more
- **Internationalization**: Multiple language support
- **Dark Mode**: Automatic system theme detection

## Uninstalling

To uninstall Pandoc UI:
1. Move "Pandoc UI.app" from Applications to Trash
2. Remove preferences (optional):
   ```bash
   rm -rf ~/Library/Preferences/com.pandoc-ui.app.plist
   rm -rf ~/Library/Application\ Support/Pandoc\ UI
   ```

## Support

- **Issues**: https://github.com/your-username/pandoc-ui/issues
- **Documentation**: https://github.com/your-username/pandoc-ui
- **License**: MIT License

## Security Notice

This application is unsigned and distributed freely. The security warning you see is normal for unsigned applications. The source code is open source and available for review at the GitHub repository.
EOF

    log_success "Installation instructions created: $README_PATH"
}

# Main execution
main() {
    log_info "Starting macOS build for $APP_NAME v$VERSION"
    echo "Configuration:"
    echo "  - Universal Binary: $UNIVERSAL"
    echo "  - Create DMG: $CREATE_DMG"
    echo "  - Use Spec File: $USE_SPEC"
    echo "  - Clean Build: $CLEAN_BUILD"
    echo
    
    check_macos
    check_dependencies
    clean_build
    install_dependencies
    generate_icon
    
    if [[ "$USE_SPEC" == true ]]; then
        build_app_with_spec
    else
        build_app_cmdline
    fi
    
    verify_app
    create_dmg_with_dmgbuild
    create_readme
    
    log_success "Build completed successfully!"
    
    echo
    log_info "Distribution files created:"
    if [[ -f "$PROJECT_ROOT/$DIST_DIR/pandoc-ui-macos.dmg" ]]; then
        echo "  📦 $DIST_DIR/pandoc-ui-macos.dmg"
    fi
    if [[ -d "$PROJECT_ROOT/$DIST_DIR/$APP_NAME.app" ]]; then
        echo "  📱 $DIST_DIR/$APP_NAME.app"
    fi
    if [[ -f "$PROJECT_ROOT/$DIST_DIR/INSTALL_MACOS.md" ]]; then
        echo "  📖 $DIST_DIR/INSTALL_MACOS.md"
    fi
    
    echo
    log_warning "IMPORTANT: This is an unsigned application."
    log_warning "Users will need to manually allow it in System Preferences."
    log_warning "See INSTALL_MACOS.md for detailed user instructions."
    
    echo
    log_info "Next steps:"
    echo "  1. Test the DMG on different Mac architectures"
    echo "  2. Upload to GitHub Releases"
    echo "  3. Consider Homebrew Cask submission"
    echo "  4. Update documentation with download links"
}

# Run main function
main "$@"