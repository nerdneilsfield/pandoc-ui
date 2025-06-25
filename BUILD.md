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

- **Dependencies**: Xcode Command Line Tools (for code signing, optional)
- **Output**: `dist/macos/pandoc-ui-macos-<version>`
- **Code Signing**: Automatically detects and uses available Developer ID
- **Compatibility**: Targets macOS 10.14+ (Mojave and later)

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

```
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
- Copy executable to target systems
- Users may need to allow execution: System Preferences > Security & Privacy
- For wider distribution, code signing recommended

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

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build for Linux
  run: ./scripts/linux_build.sh
  
- name: Upload Linux Artifact
  uses: actions/upload-artifact@v3
  with:
    name: pandoc-ui-linux
    path: dist/linux/
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