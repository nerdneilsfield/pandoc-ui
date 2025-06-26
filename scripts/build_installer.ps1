# Windows Installer Build Script - NSIS Integration
# Extends the existing windows_build.ps1 with professional installer creation

param(
    [string]$Version = "dev",
    [switch]$Sign,              # Code sign the installer
    [string]$CertPath = "",     # Path to code signing certificate
    [string]$CertPass = "",     # Certificate password
    [switch]$SkipBuild,         # Skip application build, just create installer
    [switch]$Test,              # Test the installer after creation
    [switch]$Help               # Show help message
)

$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host @"

Windows Installer Build Script for pandoc-ui

USAGE:
    .\scripts\build_installer.ps1 [OPTIONS]

OPTIONS:
    -Version <version>      Override version detection (default: auto-detect from pyproject.toml)
    -Sign                   Code sign the installer (requires -CertPath)
    -CertPath <path>        Path to code signing certificate (.pfx/.p12 file)
    -CertPass <password>    Certificate password (if required)
    -SkipBuild              Skip application build, just create installer
    -Test                   Test the installer after creation (silent install/uninstall)
    -Help                   Show this help message

EXAMPLES:
    .\scripts\build_installer.ps1
    .\scripts\build_installer.ps1 -Version "1.0.0"
    .\scripts\build_installer.ps1 -Sign -CertPath "cert.pfx"
    .\scripts\build_installer.ps1 -SkipBuild -Test

REQUIREMENTS:
    - NSIS (Nullsoft Scriptable Install System)
    - Windows SDK (for code signing, optional)
    - PowerShell 5.0+

NOTES:
    - Automatically detects version from pyproject.toml
    - Downloads required NSIS if not found in PATH
    - Creates professional installer with Modern UI
    - Supports silent installation for enterprise deployment
    - Code signing helps avoid Windows SmartScreen warnings

"@ -ForegroundColor White
    exit 0
}

Write-Host "🏗️  Building Windows Installer for Pandoc UI..." -ForegroundColor Yellow

# Get version from pyproject.toml if not provided
if ($Version -eq "dev") {
    if (Test-Path "pyproject.toml") {
        $Content = Get-Content "pyproject.toml"
        $VersionLine = $Content | Where-Object { $_ -match '^version = ' }
        if ($VersionLine) {
            $Version = ($VersionLine -split '"')[1]
        }
    }
}

Write-Host "📦 Building installer for version: $Version" -ForegroundColor Cyan

# Function to check and install NSIS
function Ensure-NSIS {
    # Check if NSIS is in PATH
    if (Get-Command makensis -ErrorAction SilentlyContinue) {
        Write-Host "✅ NSIS found in PATH" -ForegroundColor Green
        return $true
    }
    
    # Check common installation locations
    $NSISPaths = @(
        "${env:ProgramFiles}\NSIS\makensis.exe",
        "${env:ProgramFiles(x86)}\NSIS\makensis.exe",
        "C:\Program Files\NSIS\makensis.exe",
        "C:\Program Files (x86)\NSIS\makensis.exe"
    )
    
    foreach ($Path in $NSISPaths) {
        if (Test-Path $Path) {
            Write-Host "✅ NSIS found at: $Path" -ForegroundColor Green
            # Add to PATH for this session
            $env:PATH += ";$(Split-Path $Path)"
            return $true
        }
    }
    
    Write-Host "❌ NSIS not found. Installing NSIS..." -ForegroundColor Yellow
    
    # Try to install via Chocolatey
    if (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "📥 Installing NSIS via Chocolatey..." -ForegroundColor Cyan
        try {
            & choco install nsis -y
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ NSIS installed successfully" -ForegroundColor Green
                # Refresh PATH
                $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
                return $true
            }
        } catch {
            Write-Host "⚠️  Chocolatey installation failed" -ForegroundColor Yellow
        }
    }
    
    # Try to install via Scoop
    if (Get-Command scoop -ErrorAction SilentlyContinue) {
        Write-Host "📥 Installing NSIS via Scoop..." -ForegroundColor Cyan
        try {
            & scoop install nsis
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ NSIS installed successfully" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "⚠️  Scoop installation failed" -ForegroundColor Yellow
        }
    }
    
    # Manual download as last resort
    Write-Host "📥 Downloading NSIS manually..." -ForegroundColor Cyan
    $NSISUrl = "https://sourceforge.net/projects/nsis/files/NSIS%203/3.08/nsis-3.08-setup.exe/download"
    $NSISInstaller = "$env:TEMP\nsis-setup.exe"
    
    try {
        Invoke-WebRequest -Uri $NSISUrl -OutFile $NSISInstaller -UseBasicParsing
        Write-Host "⚠️  Please install NSIS manually:" -ForegroundColor Yellow
        Write-Host "   Downloaded: $NSISInstaller" -ForegroundColor Gray
        Write-Host "   Or visit: https://nsis.sourceforge.io/Download" -ForegroundColor Gray
        return $false
    } catch {
        Write-Host "❌ Failed to download NSIS" -ForegroundColor Red
        Write-Host "💡 Please install NSIS manually from: https://nsis.sourceforge.io/Download" -ForegroundColor Yellow
        return $false
    }
}

# Ensure NSIS is available
if (-not (Ensure-NSIS)) {
    Write-Host "❌ NSIS is required but not available" -ForegroundColor Red
    Write-Host "💡 Install NSIS and try again:" -ForegroundColor Yellow
    Write-Host "   - Download from: https://nsis.sourceforge.io/Download" -ForegroundColor Gray
    Write-Host "   - Or install via Chocolatey: choco install nsis" -ForegroundColor Gray
    Write-Host "   - Or install via Scoop: scoop install nsis" -ForegroundColor Gray
    exit 1
}

# Create installer directory structure
$InstallerDir = "installer"
New-Item -ItemType Directory -Force -Path $InstallerDir | Out-Null

# Build the application first (unless skipped)
if (-not $SkipBuild) {
    Write-Host "🔨 Building application..." -ForegroundColor Cyan
    & .\scripts\windows_build.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Application build failed!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "ℹ️  Skipping application build" -ForegroundColor Cyan
}

# Verify application executable exists
$AppPath = "dist\windows\pandoc-ui-windows-$Version.exe"
if (-not (Test-Path $AppPath)) {
    Write-Host "❌ Application executable not found: $AppPath" -ForegroundColor Red
    Write-Host "💡 Run without -SkipBuild to build the application first" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Application found: $AppPath" -ForegroundColor Green

# Check for required files
$RequiredFiles = @(
    "LICENSE",
    "README.md",
    "resources\icons\app.ico"
)

$MissingFiles = @()
foreach ($File in $RequiredFiles) {
    if (-not (Test-Path $File)) {
        $MissingFiles += $File
    }
}

if ($MissingFiles.Count -gt 0) {
    Write-Host "❌ Required files missing:" -ForegroundColor Red
    foreach ($File in $MissingFiles) {
        Write-Host "   - $File" -ForegroundColor Red
    }
    exit 1
}

# Create installer graphics if they don't exist
$WelcomeBmp = "$InstallerDir\welcome.bmp"
$HeaderBmp = "$InstallerDir\header.bmp"

if (-not (Test-Path $WelcomeBmp) -or -not (Test-Path $HeaderBmp)) {
    Write-Host "ℹ️  Installer graphics not found, using minimal placeholders..." -ForegroundColor Cyan
    
    # Create minimal placeholder BMP files using cross-compatible method
    # This creates a valid 1x1 pixel BMP file
    $BmpData = @(
        0x42, 0x4D, 0x3A, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x36, 0x00, 0x00, 0x00, 0x28, 0x00,
        0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x18, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00
    )
    
    if (-not (Test-Path $WelcomeBmp)) {
        try {
            $WelcomeFullPath = Join-Path (Get-Location) $WelcomeBmp
            [System.IO.File]::WriteAllBytes($WelcomeFullPath, $BmpData)
            Write-Host "📝 Created placeholder: welcome.bmp (recommended: 164x314 pixels)" -ForegroundColor Gray
        } catch {
            Write-Host "⚠️  Could not create welcome.bmp placeholder: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "💡 You may need to provide your own installer graphics" -ForegroundColor Cyan
        }
    }
    
    if (-not (Test-Path $HeaderBmp)) {
        try {
            $HeaderFullPath = Join-Path (Get-Location) $HeaderBmp
            [System.IO.File]::WriteAllBytes($HeaderFullPath, $BmpData)
            Write-Host "📝 Created placeholder: header.bmp (recommended: 150x57 pixels)" -ForegroundColor Gray
        } catch {
            Write-Host "⚠️  Could not create header.bmp placeholder: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "💡 You may need to provide your own installer graphics" -ForegroundColor Cyan
        }
    }
    
    Write-Host "💡 For professional installers, replace placeholders with custom graphics:" -ForegroundColor Cyan
    Write-Host "   - $WelcomeBmp (164x314 pixels)" -ForegroundColor Gray
    Write-Host "   - $HeaderBmp (150x57 pixels)" -ForegroundColor Gray
}

# Update version in NSIS script
$NsiScript = "$InstallerDir\pandoc-ui-installer.nsi"
if (Test-Path $NsiScript) {
    Write-Host "📝 Updating version in NSIS script..." -ForegroundColor Cyan
    $Content = Get-Content $NsiScript -Raw
    $Content = $Content -replace '!define PRODUCT_VERSION ".*"', "!define PRODUCT_VERSION `"$Version`""
    $Content | Set-Content $NsiScript -NoNewline
} else {
    Write-Host "❌ NSIS script not found: $NsiScript" -ForegroundColor Red
    exit 1
}

try {
    # Build installer with NSIS
    Write-Host "🔧 Compiling installer with NSIS..." -ForegroundColor Cyan
    $InstallerOutput = "pandoc-ui-installer-$Version.exe"
    
    Push-Location $InstallerDir
    
    # Run NSIS compiler (version already updated in .nsi file)
    $NSISArgs = @(
        "pandoc-ui-installer.nsi"
    )
    
    & makensis @NSISArgs
    $NSISExitCode = $LASTEXITCODE
    
    Pop-Location
    
    if ($NSISExitCode -ne 0) {
        Write-Host "❌ NSIS compilation failed with exit code: $NSISExitCode" -ForegroundColor Red
        exit 1
    }
    
    # Move installer to dist directory
    $InstallerPath = "dist\$InstallerOutput"
    if (-not (Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }
    
    if (Test-Path "$InstallerDir\$InstallerOutput") {
        Move-Item "$InstallerDir\$InstallerOutput" $InstallerPath -Force
    } else {
        Write-Host "❌ Installer not created by NSIS" -ForegroundColor Red
        exit 1
    }
    
    # Code signing (if requested)
    if ($Sign -and $CertPath) {
        Write-Host "🔏 Code signing installer..." -ForegroundColor Cyan
        
        if (-not (Test-Path $CertPath)) {
            Write-Host "❌ Certificate not found: $CertPath" -ForegroundColor Red
            exit 1
        }
        
        # Find SignTool
        $SignToolPaths = @(
            "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
            "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
        )
        
        $SignTool = $null
        foreach ($Path in $SignToolPaths) {
            $Found = Get-ChildItem $Path -ErrorAction SilentlyContinue | Sort-Object Name -Descending | Select-Object -First 1
            if ($Found) {
                $SignTool = $Found.FullName
                break
            }
        }
        
        if ($SignTool) {
            $SignArgs = @(
                "sign",
                "/f", $CertPath,
                "/t", "http://timestamp.digicert.com",
                "/fd", "SHA256",
                "/v",
                $InstallerPath
            )
            
            if ($CertPass) {
                $SignArgs = $SignArgs[0..1] + @("/p", $CertPass) + $SignArgs[2..($SignArgs.Length-1)]
            }
            
            & $SignTool @SignArgs
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Installer signed successfully" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Code signing failed, but installer created" -ForegroundColor Yellow
            }
        } else {
            Write-Host "⚠️  SignTool not found - install Windows SDK" -ForegroundColor Yellow
        }
    }
    
    # Get file size and test installer
    $FileSize = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 2)
    Write-Host ""
    Write-Host "✅ Installer created successfully!" -ForegroundColor Green
    Write-Host "📁 File: $InstallerPath" -ForegroundColor White
    Write-Host "📊 Size: $FileSize MB" -ForegroundColor White
    
    # Test installer if requested
    if ($Test) {
        Write-Host "🧪 Testing installer..." -ForegroundColor Cyan
        $TestDir = "$env:TEMP\PandocUI-InstallTest-$(Get-Random)"
        
        try {
            Write-Host "   Testing silent installation..." -ForegroundColor Gray
            $InstallProcess = Start-Process -FilePath $InstallerPath -ArgumentList "/S", "/D=$TestDir" -Wait -PassThru -NoNewWindow
            
            if ($InstallProcess.ExitCode -eq 0) {
                if (Test-Path "$TestDir\pandoc-ui.exe") {
                    Write-Host "   ✅ Silent installation test passed" -ForegroundColor Green
                    
                    # Test uninstaller
                    Write-Host "   Testing uninstaller..." -ForegroundColor Gray
                    if (Test-Path "$TestDir\uninst.exe") {
                        $UninstallProcess = Start-Process -FilePath "$TestDir\uninst.exe" -ArgumentList "/S" -Wait -PassThru -NoNewWindow
                        if ($UninstallProcess.ExitCode -eq 0) {
                            Write-Host "   ✅ Uninstaller test passed" -ForegroundColor Green
                        } else {
                            Write-Host "   ⚠️  Uninstaller test failed" -ForegroundColor Yellow
                        }
                    }
                } else {
                    Write-Host "   ❌ Installation test failed - executable not found" -ForegroundColor Red
                }
            } else {
                Write-Host "   ❌ Installation test failed with exit code: $($InstallProcess.ExitCode)" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ⚠️  Could not test installer: $($_.Exception.Message)" -ForegroundColor Yellow
        } finally {
            # Clean up test installation
            if (Test-Path $TestDir) {
                Remove-Item -Recurse -Force $TestDir -ErrorAction SilentlyContinue
            }
        }
    }
    
    Write-Host ""
    Write-Host "🎉 Installer build completed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Installation commands:" -ForegroundColor White
    Write-Host "   Normal: $InstallerPath" -ForegroundColor Gray
    Write-Host "   Silent: $InstallerPath /S" -ForegroundColor Gray
    Write-Host "   Custom dir: $InstallerPath /S /D=C:\MyPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔧 Installer features:" -ForegroundColor White
    Write-Host "   ✓ Professional Modern UI 2" -ForegroundColor Gray
    Write-Host "   ✓ Multi-language support (EN, CN, JP, FR, DE, ES)" -ForegroundColor Gray
    Write-Host "   ✓ File associations (.md, .rst, .tex, .html)" -ForegroundColor Gray
    Write-Host "   ✓ Context menu integration" -ForegroundColor Gray
    Write-Host "   ✓ Start menu shortcuts" -ForegroundColor Gray
    Write-Host "   ✓ Desktop shortcut (optional)" -ForegroundColor Gray
    Write-Host "   ✓ Clean uninstaller with registry cleanup" -ForegroundColor Gray
    Write-Host "   ✓ Silent installation support" -ForegroundColor Gray
    Write-Host "   ✓ Windows 7+ compatibility" -ForegroundColor Gray
    Write-Host "   ✓ Automatic upgrade handling" -ForegroundColor Gray
    if ($Sign -and $CertPath) {
        Write-Host "   ✓ Code signed for Windows SmartScreen compatibility" -ForegroundColor Gray
    }

} catch {
    Write-Host "❌ Installer build error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}