# Build Instructions

This document explains how to build pandoc-ui into standalone executables for different platforms.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) package manager installed
- Python 3.12+ with PySide6
- **ImageMagick** for icon generation (see Icon Generation section)
- Platform-specific requirements (see below)

## Quick Start

### Icon Generation (First Time Setup)

Before building, generate icons from your logo:

```bash
# Linux/macOS
./scripts/generate_icons.sh
./scripts/generate_resources.sh

# Windows (PowerShell)
.\scripts\generate_icons.ps1
.\scripts\generate_resources.ps1
```

### Build by Platform

Choose the appropriate script for your platform:

```bash
# Linux and macOS (unified)
./scripts/build.sh

# Windows (PowerShell only)
.\scripts\windows_build.ps1
```

**Note**: Build scripts automatically generate resources if needed.

## Platform Requirements

### Linux

- **Dependencies**: No additional system packages required
- **Output**: `dist/linux/pandoc-ui-linux-<version>`
- **Notes**: Built with `--static-libpython=no` for broader compatibility

### macOS

#### Standard Build (Nuitka)
- **Dependencies**: Xcode Command Line Tools (for code signing, optional)
- **Output**: `dist/macos/pandoc-ui-macos-<version>`
- **Code Signing**: Automatically detects and uses available Developer ID
- **Compatibility**: Targets macOS 10.14+ (Mojave and later)

#### DMG Distribution (PyInstaller - Recommended for Open Source)
- **Script**: `./scripts/macos_build_dmg.sh`
- **Dependencies**: None (unsigned distribution)
- **Output**: `dist/pandoc-ui-macos.dmg`
- **Features**: 
  - Universal binary (Apple Silicon + Intel)
  - Professional DMG with drag-to-install
  - No Apple Developer account required
  - Detailed user installation instructions

### Windows

- **Dependencies**: None (PowerShell 5.1+ or PowerShell Core)
- **Output**: `dist/windows/pandoc-ui-windows-<version>.exe`
- **Icon**: Automatically includes app icon if found in standard locations

## Build Features

### Unified Unix Script (build.sh)

The `build.sh` script handles both Linux and macOS builds with:

- **Platform Detection**: Automatically configures Linux vs macOS settings
- **Linux Specific**: `--static-libpython=no` for broader compatibility
- **macOS Specific**: Code signing detection, architecture targeting, .icns icon support
- **Shared Logic**: Version detection, dependency checking, post-build validation

### Windows Script (windows_build.ps1)

Separate PowerShell script for Windows with:

- **Windows Metadata**: .exe version info, company details
- **Icon Support**: Automatic .ico file detection and embedding
- **PowerShell Native**: Uses Windows PowerShell features and error handling

### Nuitka Configuration

All builds use Nuitka with these optimizations:

- **One-file**: Single executable with no external dependencies
- **PySide6 Plugin**: Optimized Qt application bundling
- **Console Disabled**: GUI-only application (no console window)
- **Progress Display**: Real-time build progress and memory usage

### Automatic Features

- **Version Detection**: Reads version from `pyproject.toml`
- **Icon Detection**: Platform-specific icon search:
  - Windows: `resources/icons/app.ico`, `assets/app.ico`, `icon.ico`
  - macOS: `resources/icons/app.icns`, `assets/app.icns`, `icon.icns`
  - Linux: No icon support (GUI toolkit will use defaults)
- **Metadata Embedding**: Company name, product info, copyright
- **File Testing**: Basic executable validation after build
- **Code Signing**: Automatic detection and use of available signing identities (macOS)

## Output Structure

```text
dist/
├── linux/
│   └── pandoc-ui-linux-<version>
├── macos/
│   └── pandoc-ui-macos-<version>
└── windows/
    └── pandoc-ui-windows-<version>.exe
```

## Troubleshooting

### Common Issues

**Linux: "python3-dev required"**

```bash
# Add --static-libpython=no (already included in script)
# Or install development headers:
sudo apt-get install python3-dev  # Ubuntu/Debian
sudo yum install python3-devel    # CentOS/RHEL
```

**macOS: "No signing identity"**

```bash
# Optional - for distribution outside development
# Install Xcode and set up Apple Developer account
# Or build will work unsigned for personal use
```

**Windows: "PowerShell not found"**

```powershell
# Use Windows PowerShell or install PowerShell Core
# Run directly: .\scripts\windows_build.ps1
```

### Build Verification

Each build script automatically:

1. ✅ Tests executable with `--help`
2. 📊 Reports file size
3. 🔍 Checks platform-specific requirements

### Performance Notes

- **Build Time**: 2-10 minutes depending on system
- **Output Size**: 80-150 MB (includes Qt libraries)
- **RAM Usage**: 2-4 GB during compilation

## Distribution

### Linux

- Copy executable to target systems
- No Python installation required
- Basic GUI libraries should be present (usually default)

### macOS

#### Standard Binary Distribution
- Copy executable to target systems
- Users may need to allow execution: System Preferences > Security & Privacy
- For wider distribution, code signing recommended

#### DMG Distribution (Recommended for Open Source)
- **Output**: `dist/pandoc-ui-macos.dmg`
- **Features**: Professional disk image with drag-to-install interface
- **No Code Signing Required**: Perfect for open source projects
- **User Installation**: Simple drag-and-drop to Applications folder
- **Gatekeeper Bypass**: Detailed instructions provided for users

### Windows

- Copy .exe to target systems
- No additional dependencies required
- Windows Defender may require approval for unsigned executables

## Advanced Options

### Custom Nuitka Arguments

Modify build scripts to add custom Nuitka options:

```bash
# Example: Add data files
--include-data-dir=resources=resources \
--include-data-dir=templates=templates \
```

### Cross-Platform Building

Each script builds for its host platform only. For cross-platform builds:

- Use platform-specific CI/CD (GitHub Actions, etc.)
- Or use virtual machines/containers for each target platform

## macOS DMG Build Guide

### Overview

The macOS DMG build provides a professional distribution method for open source projects without requiring an Apple Developer account. This creates a universal binary that works on both Apple Silicon and Intel Macs.

### Build Commands

```bash
# Basic DMG build for current architecture
./scripts/macos_build_dmg.sh

# Universal binary for both Apple Silicon and Intel
./scripts/macos_build_dmg.sh --universal

# Clean build with universal binary
./scripts/macos_build_dmg.sh --universal --clean

# Build without DMG (app bundle only)
./scripts/macos_build_dmg.sh --no-dmg

# Use PyInstaller spec file for advanced control
./scripts/macos_build_dmg.sh --universal --use-spec
```

### Build Process

1. **Dependency Installation**: Automatically installs PyInstaller and dmgbuild
2. **Icon Generation**: Converts iconset to .icns format if available
3. **App Bundle Creation**: Builds .app bundle with PyInstaller
4. **Universal Binary**: Combines ARM64 and Intel builds (if --universal)
5. **DMG Creation**: Packages app in professional disk image
6. **Installation Instructions**: Generates detailed user guide

### Output Files

```
dist/
├── Pandoc UI.app                    # macOS app bundle
├── pandoc-ui-macos.dmg             # Disk image for distribution
└── INSTALL_MACOS.md                # User installation instructions
```

### DMG Features

- **Professional Layout**: Drag-to-Applications interface
- **Universal Binary**: Single app works on all Mac architectures
- **Background Image**: Custom DMG background (configurable)
- **Volume Branding**: Proper volume name and icon
- **File Associations**: Supports .md, .rst, .tex files
- **High DPI Support**: Optimized for Retina displays

### User Installation Process

1. **Download**: User downloads `pandoc-ui-macos.dmg`
2. **Mount**: Double-click to mount the disk image
3. **Install**: Drag app to Applications folder
4. **First Launch**: Right-click app → "Open" to bypass Gatekeeper
5. **Future Use**: App launches normally after first approval

### Unsigned App Distribution

Since this method doesn't require code signing, users will see a security warning on first launch. The generated `INSTALL_MACOS.md` provides three methods for users to safely launch the app:

#### Method 1: Right-click Override (Easiest)
```
1. Right-click "Pandoc UI.app" in Applications
2. Select "Open" from context menu
3. Click "Open" in security dialog
```

#### Method 2: Terminal Command (Advanced)
```bash
sudo xattr -rd com.apple.quarantine "/Applications/Pandoc UI.app"
```

#### Method 3: System Preferences (Alternative)
```
1. Try to open app (it will be blocked)
2. System Preferences → Security & Privacy → General
3. Click "Open Anyway"
```

### Technical Specifications

- **Build Tool**: PyInstaller 6.0+ (better macOS support than Nuitka)
- **Target OS**: macOS 10.15+ (Catalina and later)
- **Architectures**: Universal2 (ARM64 + x86_64)
- **Bundle Format**: Standard .app bundle with proper metadata
- **DMG Compression**: UDZO (compressed) for smaller download size
- **Dependencies**: Self-contained (includes PySide6 and all requirements)

### Customization

#### DMG Appearance
Edit `scripts/macos/dmg_settings.py` to customize:
- Window size and position
- Icon locations
- Background image
- Volume settings

#### App Metadata
Edit `scripts/macos/pandoc-ui.spec` to customize:
- Bundle identifier
- Version information
- File associations
- Copyright information

#### Background Image
Create `scripts/macos/background.png` (640x400px) for custom DMG background.

### Troubleshooting

#### Build Issues
- **PyInstaller not found**: Run `uv sync --group macos`
- **Icon missing**: Ensure `resources/icons/app.iconset/` exists
- **Permission denied**: Make sure script is executable (`chmod +x`)

#### Runtime Issues
- **App won't open**: User needs to follow first-launch security steps
- **Missing dependencies**: DMG includes all dependencies
- **Performance slow**: First launch is slower due to macOS verification

### Distribution Strategy

1. **GitHub Releases**: Upload DMG file to releases page
2. **Download Instructions**: Link to `INSTALL_MACOS.md` for user guidance
3. **Homebrew Cask**: Consider submitting to homebrew-cask for easier installation
4. **Website**: Provide direct download link with installation instructions

### Comparison with Signed Distribution

| Feature | Unsigned DMG | Signed Distribution |
|---------|--------------|-------------------|
| **Cost** | Free | $99/year Developer account |
| **User Experience** | Manual security override | Seamless installation |
| **Distribution** | Direct download | App Store or direct |
| **Build Complexity** | Simple | Requires certificates |
| **Open Source** | Perfect fit | Unnecessary complexity |

For open source projects, unsigned DMG distribution is the recommended approach.

## Advanced Build Features

### 🚀 Optimized Build System

The build system now includes professional optimization and distribution features:

- **Strip Binary Optimization**: Reduces executable size by 5-40%
- **Linux AppImage**: Self-contained portable packages
- **Windows NSIS Installer**: Professional installer with Modern UI
- **Cross-platform Integration**: Seamless workflow integration

### Strip Binary Optimization

Binary optimization removes debugging symbols and unnecessary metadata to reduce file size while maintaining functionality.

#### Optimization Levels

**Conservative (Recommended)**

- Size reduction: 5-15%
- 100% safe for PySide6/Qt applications
- Default for production builds

**Moderate (Test Before Use)**

- Size reduction: 10-25%
- Generally safe, requires testing
- Good balance of safety and optimization

**Aggressive (High Risk)**

- Size reduction: 15-40%
- High risk for Qt applications
- Testing and research only

#### Usage Examples

```bash
# Linux/macOS
./scripts/build.sh                           # Conservative optimization (default)
./scripts/build.sh --no-strip               # No optimization
./scripts/build.sh --strip-level moderate   # Moderate optimization
./scripts/build.sh --strip-level aggressive # Aggressive optimization
```

```powershell
# Windows
.\scripts\windows_build.ps1                              # Conservative optimization
.\scripts\windows_build.ps1 -NoStrip                    # No optimization  
.\scripts\windows_build.ps1 -StripLevel Moderate        # Moderate optimization
.\scripts\windows_build.ps1 -StripLevel Aggressive      # Aggressive optimization
```

#### Strip Optimization Principles

**⚠️ IMPORTANT: Nuitka Onefile Binary Handling**

Nuitka onefile binaries contain compressed Python runtime and dependencies attached to the executable. **Post-build stripping will corrupt these binaries** and cause "couldn't find attached data header" errors.

**Correct Optimization Strategy:**
- **Onefile binaries**: Optimization happens during Nuitka build process
  - Conservative: Default Nuitka stripping + LTO (Link-Time Optimization)
  - Moderate: LTO + enhanced Nuitka optimizations
  - Aggressive: LTO + maximum Nuitka optimization flags
- **Standalone binaries**: Post-build stripping is safe
  - Conservative: `--strip-debug` (removes debug symbols only)
  - Moderate: `--strip-debug --strip-unneeded` (removes unnecessary symbols)
  - Aggressive: `--strip-all` (removes all symbols)

**Build System Intelligence:**
- Automatically detects onefile vs standalone binaries
- Disables post-build stripping for onefile to prevent corruption
- Uses Nuitka build-time optimization for onefile binaries
- Applies post-build stripping only to standalone binaries

**Windows Optimization:**
- Onefile: Nuitka LTO + default stripping + optional UPX (risky)
- Standalone: Nuitka LTO + UPX compression with safety levels

**Safety Considerations**

- **Never manually strip Nuitka onefile binaries** - they will break
- Onefile detection prevents accidental corruption
- Qt/PySide6 applications require careful symbol handling
- Build system prioritizes safety over size reduction

### Linux AppImage Distribution

AppImage creates portable, self-contained Linux applications that run on most distributions without installation.

#### AppImage Features

- **Portability**: Runs on Ubuntu 18.04+, CentOS 7+, most modern distributions
- **Self-contained**: Includes all dependencies
- **No Installation**: Just make executable and run
- **Desktop Integration**: Automatic .desktop file and icon handling

#### AppImage Build Process

```bash
# Build AppImage with default settings
./scripts/build.sh --appimage

# Build AppImage with moderate optimization
./scripts/build.sh --appimage --strip-level moderate

# Build AppImage directly (advanced)
./scripts/build_appimage.sh --clean --test

# Alternative AppImage methods:
./scripts/build_simple_appimage.sh        # Simple Nuitka-based method
./scripts/build_appimage_builder.sh       # Professional appimage-builder method
```

#### AppImage Technical Details

**Build Process:**

1. Creates binary with standard build process
2. Downloads linuxdeploy and appimagetool if needed
3. Creates AppDir structure with proper directory layout
4. Copies application binary and dependencies
5. Installs desktop integration files (.desktop, icons)
6. Configures AppRun script for Qt/PySide6 compatibility
7. Packages into .AppImage file with compression

**Output Structure:**

```
dist/linux/
├── pandoc-ui-linux-<version>                    # Standard binary
└── pandoc-ui-<version>-x86_64.AppImage         # AppImage package
```

**Distribution:**

- Copy .AppImage file to target systems
- Make executable: `chmod +x pandoc-ui-*.AppImage`
- Run directly: `./pandoc-ui-*.AppImage`

### Windows NSIS Installer

Professional Windows installer using NSIS (Nullsoft Scriptable Install System) with Modern UI 2.

#### Installer Features

- **Modern UI 2**: Professional wizard-style interface
- **Multi-language**: Support for 6 languages (EN, CN, JP, FR, DE, ES)
- **File Associations**: Automatic registration for .md, .rst, .tex, .html files
- **Context Menu Integration**: Right-click conversion for files and folders
- **Start Menu Integration**: Program group and shortcuts
- **Desktop Integration**: Optional desktop shortcut
- **Silent Installation**: Enterprise deployment support
- **Clean Uninstaller**: Complete removal with registry cleanup

#### Installer Build Process

```powershell
# Build installer with default settings
.\scripts\windows_build.ps1 -CreateInstaller

# Build installer with moderate optimization
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Moderate

# Build installer directly (advanced)
.\scripts\build_installer.ps1 -Version "1.0.0"

# Build and test installer
.\scripts\build_installer.ps1 -Test

# Build and code sign installer
.\scripts\build_installer.ps1 -Sign -CertPath "certificate.pfx"
```

#### Installer Technical Details

**Build Process:**

1. Builds application with standard build process
2. Installs NSIS if not found (via Chocolatey/Scoop)
3. Updates version information in NSIS script
4. Compiles installer with NSIS compiler
5. Optional code signing with Windows SDK
6. Testing with silent install/uninstall

**NSIS Script Features:**

- Modern UI 2 with custom graphics
- Component-based installation
- Registry integration for file associations
- Context menu entries for files and folders
- Start menu shortcuts and program groups
- Desktop shortcuts (optional)
- Visual C++ Redistributable detection
- Windows version compatibility check
- Upgrade handling (automatic uninstall of previous versions)

**Installation Commands:**

```powershell
# Normal installation (GUI)
.\pandoc-ui-installer-1.0.0.exe

# Silent installation
.\pandoc-ui-installer-1.0.0.exe /S

# Silent installation to custom directory
.\pandoc-ui-installer-1.0.0.exe /S /D=C:\MyPrograms\PandocUI
```

### Build System Integration

#### Unified Workflow

The optimization features are seamlessly integrated into existing build scripts:

```bash
# Linux: One command for optimized AppImage
./scripts/build.sh --appimage --strip-level moderate

# Windows: One command for optimized installer  
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Moderate
```

#### Script Architecture

**build.sh (Linux/macOS)**

- Platform detection and configuration
- Strip optimization integration
- AppImage build coordination
- Verification and testing

**windows_build.ps1 (Windows)**

- Windows-specific build configuration
- UPX compression integration
- NSIS installer coordination
- Code signing support

**Helper Scripts**

- `strip_optimize.sh/.ps1`: Cross-platform strip optimization
- `build_appimage.sh`: Linux AppImage creation
- `build_installer.ps1`: Windows NSIS installer creation

#### Automatic Tool Management

The build system automatically handles dependencies:

**Linux AppImage Tools**

- Downloads linuxdeploy if not found
- Downloads appimagetool if not found
- Creates temporary tool directory

**Windows NSIS Tools**

- Installs NSIS via Chocolatey/Scoop if not found
- Downloads Windows SDK for code signing
- Creates installer graphics if missing

### Performance Benchmarks

#### Size Reduction Examples

Based on typical PySide6 applications:

| Platform | Original Size | Conservative | Moderate | Aggressive |
|----------|---------------|--------------|----------|------------|
| Linux x64 | 45 MB | 39 MB (-13%) | 34 MB (-24%) | 28 MB (-38%) |
| Windows x64 | 42 MB | 40 MB (-5%) | 32 MB (-24%) | 25 MB (-40%) |
| macOS x64 | 48 MB | 42 MB (-13%) | 36 MB (-25%) | 30 MB (-38%) |

#### Build Time Impact

- **Strip Optimization**: +5-15 seconds
- **AppImage Creation**: +30-60 seconds
- **NSIS Installer**: +15-30 seconds

### Production Recommendations

#### For Distribution

**Linux:**

```bash
# Production AppImage with conservative optimization
./scripts/build.sh --appimage --strip-level conservative
```

**Windows:**

```powershell
# Production installer with conservative optimization and code signing
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Conservative
.\scripts\build_installer.ps1 -Sign -CertPath "certificate.pfx"
```

#### For Testing

**Linux:**

```bash
# Test build with moderate optimization
./scripts/build.sh --appimage --strip-level moderate
```

**Windows:**

```powershell
# Test installer with moderate optimization
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Moderate -Test
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build Linux AppImage
  run: ./scripts/build.sh --appimage

- name: Build Windows Installer  
  run: .\scripts\windows_build.ps1 -CreateInstaller
  
- name: Upload Artifacts
  uses: actions/upload-artifact@v3
  with:
    name: distribution-packages
    path: |
      dist/*.AppImage
      dist/*.exe
```

See `.github/workflows/` for complete CI/CD examples.

## Icon Generation

### Prerequisites for Icon Generation

**ImageMagick** is required for generating multi-resolution icons:

```bash
# Ubuntu/Debian
sudo apt-get install imagemagick

# macOS
brew install imagemagick

# Windows
# Download from: https://imagemagick.org/script/download.php#windows
# Or via chocolatey: choco install imagemagick
```

### Icon Generation Scripts

#### Linux/macOS

```bash
# Generate all icon formats from resources/logo.png
./scripts/generate_icons.sh

# Compile Qt resources
./scripts/generate_resources.sh
```

#### Windows (PowerShell)

```powershell
# Generate all icon formats from resources/logo.png
.\scripts\generate_icons.ps1

# Compile Qt resources  
.\scripts\generate_resources.ps1
```

### Generated Icon Structure

```
resources/icons/                    # For Nuitka builds
├── logo_16.png ... logo_1024.png  # Individual PNG files
├── app.ico                         # Windows ICO file
├── app.iconset/                    # macOS iconset directory
└── app.png                         # Main PNG (256px)

pandoc_ui/resources/icons/          # For Qt internal resources
├── logo_16.png ... logo_1024.png  # Individual PNG files
└── app.png                         # Main PNG (256px)

pandoc_ui/resources/
├── resources.qrc                   # Qt resource definition
└── resources_rc.py                 # Compiled Qt resources
```

### Icon Usage in Application

Icons are automatically loaded via Qt resources:

```python
from pandoc_ui.resources import resources_rc
icon = QIcon(":/icons/logo")        # Main application icon
icon_small = QIcon(":/icons/logo_16")  # Small icon (16px)
icon_hires = QIcon(":/icons/logo@2x")  # High-DPI icon
```

### Custom Logo

To use your own logo:

1. Replace `resources/logo.png` with your design
2. Run icon generation scripts
3. Build the application

**Logo Requirements:**

- Format: PNG recommended (SVG also supported)
- Size: 1024x1024px or larger for best results
- Background: Transparent recommended
- Style: Should work well at small sizes (16px+)
