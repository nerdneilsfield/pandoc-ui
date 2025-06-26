# Build Optimization and Distribution Guide

This document describes the new build optimization and distribution features implemented for pandoc-ui.

## 🚀 Overview

The pandoc-ui project now includes comprehensive build optimization and professional distribution packages for all major platforms:

- **Strip Binary Optimization**: Reduces executable size by 5-40% while maintaining compatibility
- **Linux AppImage**: Portable, self-contained Linux packages 
- **Windows NSIS Installer**: Professional installer with Modern UI and comprehensive integration
- **Cross-platform Automation**: Integrated into existing build scripts with simple flags

## 📊 Feature Matrix

| Platform | Binary Optimization | Distribution Package | Integration Level |
|----------|-------------------|---------------------|------------------|
| Linux    | ✅ Strip (3 levels) | ✅ AppImage        | ✅ Fully Integrated |
| macOS    | ✅ Strip (3 levels) | ⏳ DMG (future)   | ✅ Partially Integrated |
| Windows  | ✅ UPX/Strip       | ✅ NSIS Installer | ✅ Fully Integrated |

## 🔧 Strip Binary Optimization

### Overview
Strip optimization removes debugging symbols and unnecessary metadata from compiled binaries, significantly reducing file size while maintaining full functionality.

### Optimization Levels

#### Conservative (Recommended for Production)
- **Size Reduction**: 5-15%
- **Safety**: 100% safe for PySide6/Qt applications
- **Command**: `--strip-debug` (Linux/macOS), Limited optimization (Windows)
- **Use Case**: Production releases, distribution packages

#### Moderate (Test Before Use)
- **Size Reduction**: 10-25%
- **Safety**: Generally safe, requires testing
- **Command**: `--strip-debug --strip-unneeded` (Linux/macOS), Light UPX (Windows)
- **Use Case**: Size-constrained environments after testing

#### Aggressive (High Risk)
- **Size Reduction**: 15-40%
- **Safety**: High risk for Qt applications
- **Command**: `--strip-all` (Linux/macOS), Aggressive UPX (Windows)
- **Use Case**: Testing and research only

### Usage Examples

```bash
# Linux/macOS
./scripts/build.sh                           # Conservative optimization (default)
./scripts/build.sh --no-strip               # No optimization
./scripts/build.sh --strip-level moderate   # Moderate optimization
```

```powershell
# Windows
.\scripts\windows_build.ps1                              # Conservative optimization
.\scripts\windows_build.ps1 -NoStrip                    # No optimization  
.\scripts\windows_build.ps1 -StripLevel Moderate        # Moderate optimization
```

## 🐧 Linux AppImage Distribution

### Overview
AppImage provides portable, self-contained Linux applications that run on most distributions without installation.

### Features
- **Portability**: Runs on most Linux distributions (glibc 2.17+)
- **Self-contained**: Includes all dependencies
- **No Installation**: Just make executable and run
- **Desktop Integration**: Automatic .desktop file and icon handling
- **Multi-language Support**: Full internationalization support

### Build Process
```bash
# Build AppImage with default settings
./scripts/build.sh --appimage

# Build AppImage with moderate optimization
./scripts/build.sh --appimage --strip-level moderate

# Build AppImage directly (advanced)
./scripts/build_appimage.sh --clean --test
```

### Output
- **File**: `dist/pandoc-ui-{version}-x86_64.AppImage`
- **Size**: Typically 50-100MB (includes Qt runtime)
- **Compatibility**: Ubuntu 18.04+, CentOS 7+, most modern distributions

### Distribution
1. Copy the .AppImage file to target systems
2. Make executable: `chmod +x pandoc-ui-*.AppImage`  
3. Run directly: `./pandoc-ui-*.AppImage`
4. Optional: Integrate with desktop environment

## 🪟 Windows NSIS Installer

### Overview
Professional Windows installer using NSIS (Nullsoft Scriptable Install System) with Modern UI 2.

### Features
- **Modern UI 2**: Professional wizard-style interface
- **Multi-language**: Support for 6 languages (EN, CN, JP, FR, DE, ES)
- **File Associations**: Automatic registration for .md, .rst, .tex, .html files
- **Context Menu Integration**: Right-click conversion for files and folders
- **Start Menu Integration**: Program group and shortcuts
- **Desktop Integration**: Optional desktop shortcut
- **Silent Installation**: Enterprise deployment support
- **Clean Uninstaller**: Complete removal with registry cleanup
- **Upgrade Handling**: Automatic detection and removal of previous versions

### Build Process
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

### Output
- **File**: `dist/pandoc-ui-installer-{version}.exe`
- **Size**: Typically 40-80MB
- **Compatibility**: Windows 7+

### Installation Commands
```powershell
# Normal installation (GUI)
.\pandoc-ui-installer-1.0.0.exe

# Silent installation
.\pandoc-ui-installer-1.0.0.exe /S

# Silent installation to custom directory
.\pandoc-ui-installer-1.0.0.exe /S /D=C:\MyPrograms\PandocUI
```

## 🛠️ Development Workflow

### Quick Start Commands

```bash
# Linux: Build optimized AppImage
./scripts/build.sh --appimage --strip-level moderate

# Windows: Build optimized installer  
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Moderate

# macOS: Build optimized binary
./scripts/build.sh --strip-level conservative
```

### CI/CD Integration

The new build system integrates seamlessly with existing CI/CD pipelines:

```yaml
# GitHub Actions example
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

## 📋 Best Practices

### Production Releases
1. **Always use Conservative strip level** for production releases
2. **Test thoroughly** after any optimization
3. **Sign Windows installers** to avoid SmartScreen warnings
4. **Verify AppImage compatibility** on target distributions
5. **Include checksums** for distribution integrity

### Development Workflow
1. **Use moderate optimization** for testing builds
2. **Enable verification** during development: `--verify` flag
3. **Keep backups** when experimenting with aggressive optimization
4. **Test on clean systems** before release

### Distribution Strategy
- **Linux**: AppImage for maximum compatibility
- **Windows**: NSIS installer for professional deployment
- **macOS**: Optimized binaries (DMG package planned)

## 🔍 Troubleshooting

### Strip Optimization Issues
**Problem**: Application crashes after strip optimization
**Solution**: 
1. Use conservative level: `--strip-level conservative`
2. Verify with `--verify` flag
3. Check for missing Qt plugins or libraries

**Problem**: File size reduction is minimal
**Solution**:
1. Ensure debug symbols were present in original binary
2. Try moderate level if safe for your application
3. Consider UPX compression on Windows (test thoroughly)

### AppImage Issues
**Problem**: AppImage won't run on older distributions
**Solution**:
1. Build on older distribution (Ubuntu 18.04 recommended)
2. Check glibc compatibility requirements
3. Verify Qt plugin availability

**Problem**: Missing desktop integration
**Solution**:
1. Ensure .desktop file is properly formatted
2. Check icon file availability
3. Verify AppImage metadata

### Windows Installer Issues
**Problem**: NSIS compilation fails
**Solution**:
1. Install NSIS: `choco install nsis`
2. Check required files (LICENSE, README.md, app.ico)
3. Update version in NSIS script

**Problem**: SmartScreen warnings
**Solution**:
1. Code sign the installer with valid certificate
2. Use Extended Validation (EV) certificates for immediate trust
3. Submit to Microsoft for reputation building

## 🎯 Performance Benchmarks

### Size Reduction Examples
Based on typical PySide6 applications:

| Platform | Original Size | Conservative | Moderate | Aggressive |
|----------|---------------|--------------|----------|------------|
| Linux x64 | 45 MB | 39 MB (-13%) | 34 MB (-24%) | 28 MB (-38%) |
| Windows x64 | 42 MB | 40 MB (-5%) | 32 MB (-24%) | 25 MB (-40%) |
| macOS x64 | 48 MB | 42 MB (-13%) | 36 MB (-25%) | 30 MB (-38%) |

*Note: Actual results vary based on application complexity and dependencies*

### Build Time Impact
- **Strip Optimization**: +5-15 seconds
- **AppImage Creation**: +30-60 seconds
- **NSIS Installer**: +15-30 seconds

## 🔮 Future Enhancements

### Planned Features
- **macOS DMG Creation**: Professional macOS installer packages
- **Code Signing Automation**: Automated certificate handling
- **Delta Updates**: Incremental update packages
- **Multi-architecture Support**: ARM64 builds for Apple Silicon
- **Container Builds**: Docker-based build environments

### Advanced Optimizations
- **Profile-guided Optimization**: Runtime-optimized builds
- **Link-time Optimization**: Cross-module optimization
- **Custom Qt Builds**: Minimal Qt library builds
- **Dependency Analysis**: Automated unused dependency removal

## 📞 Support and Troubleshooting

### Getting Help
1. **Check documentation**: Review this guide and script help text
2. **Test mode**: Use `--test` flags to validate before building
3. **Verbose output**: Enable verbose mode for detailed logging
4. **Issue reporting**: Include platform, version, and exact command used

### Common Gotchas
- **File paths with spaces**: Always quote paths in scripts
- **Permission issues**: Ensure scripts have execute permissions
- **Missing dependencies**: Install required tools (NSIS, linuxdeploy, etc.)
- **Version mismatches**: Keep version strings consistent across files

---

This build optimization system provides professional-grade distribution packages while maintaining the simplicity and reliability of the existing build process. The modular design allows for easy customization and future enhancements while ensuring compatibility across all supported platforms.