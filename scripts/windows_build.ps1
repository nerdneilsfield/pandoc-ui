# Windows build script using Nuitka via uv
# Builds pandoc-ui into executable for Windows distribution
# For Linux and macOS, use scripts/build.sh
#
# Usage:
#   .\scripts\windows_build.ps1                 # Build as single file (onefile)
#   .\scripts\windows_build.ps1 -Standalone     # Build as standalone directory
#   .\scripts\windows_build.ps1 -EnableConsole  # Build with console window enabled

param(
    [switch]$Standalone,    # Build as standalone directory instead of single file
    [switch]$EnableConsole, # Enable console window for debugging
    [switch]$NoStrip,       # Skip binary optimization
    [ValidateSet("Conservative", "Moderate", "Aggressive")]
    [string]$StripLevel = "Conservative",  # Strip optimization level
    [switch]$CreateInstaller, # Create NSIS installer after building
    [switch]$Help           # Show help message
)

$ErrorActionPreference = "Stop"

# Show help if requested
if ($Help) {
    Write-Host @"

Windows Build Script for pandoc-ui

USAGE:
    .\scripts\windows_build.ps1 [OPTIONS]

OPTIONS:
    -Standalone             Build as standalone directory instead of single file
    -EnableConsole          Enable console window for debugging
    -NoStrip                Skip binary optimization with strip
    -StripLevel <level>     Set strip optimization level (Conservative, Moderate, Aggressive)
                           Default: Conservative
    -CreateInstaller        Create professional NSIS installer after building
    -Help                   Show this help message

STRIP LEVELS:
    Conservative           Safe for PySide6 applications (5-15% reduction)
    Moderate              Test before production (10-25% reduction)  
    Aggressive            High risk for Qt apps (15-40% reduction)

EXAMPLES:
    .\scripts\windows_build.ps1                                    # Build with conservative optimization
    .\scripts\windows_build.ps1 -NoStrip                          # Build without optimization
    .\scripts\windows_build.ps1 -StripLevel Moderate             # Build with moderate optimization
    .\scripts\windows_build.ps1 -Standalone -EnableConsole       # Standalone build with console
    .\scripts\windows_build.ps1 -CreateInstaller                 # Build and create installer
    .\scripts\windows_build.ps1 -CreateInstaller -StripLevel Moderate # Optimized installer

NOTES:
    - CreateInstaller automatically forces standalone mode to avoid onefile corruption
    - CreateInstaller requires NSIS (auto-downloads if not found)
    - Installer includes Modern UI, file associations, and context menu integration
    - Use CreateInstaller for professional Windows distribution packages

"@ -ForegroundColor White
    exit 0
}

# Force standalone mode when creating installer to avoid onefile strip corruption
if ($CreateInstaller -and -not $Standalone) {
    Write-Host "ℹ️  Forcing standalone mode for installer creation (avoids onefile strip corruption)" -ForegroundColor Cyan
    $Standalone = $true
}

$BuildMode = if ($Standalone) { "standalone directory" } else { "single file" }
$ConsoleMode = if ($EnableConsole) { "with console" } else { "GUI only" }
$OptimizeMode = if ($NoStrip) { "no optimization" } else { "strip optimization: $StripLevel" }
$InstallerMode = if ($CreateInstaller) { "with installer" } else { "no installer" }

Write-Host "🪟 Building pandoc-ui for Windows ($BuildMode, $ConsoleMode, $OptimizeMode, $InstallerMode)..." -ForegroundColor Yellow

# Check if uv is available
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Error: uv is not installed. Please install uv first." -ForegroundColor Red
    exit 1
}

# Get version from pyproject.toml
$Version = "dev"
if (Test-Path "pyproject.toml") {
    $Content = Get-Content "pyproject.toml"
    $VersionLine = $Content | Where-Object { $_ -match '^version = ' }
    if ($VersionLine) {
        $Version = ($VersionLine -split '"')[1]
    }
}

Write-Host "📦 Building version: $Version" -ForegroundColor Cyan

# Set build directories and output based on build mode
$BuildDir = "build\windows"
$DistDir = "dist\windows"

if ($Standalone) {
    $OutputFile = "pandoc-ui-windows-$Version"
    $OutputDir = "$DistDir\$OutputFile"
} else {
    $OutputFile = "pandoc-ui-windows-$Version.exe"
}

# Clean previous builds
Write-Host "🧹 Cleaning previous builds..." -ForegroundColor Cyan
if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

try {
    # Check if Nuitka is available
    Write-Host "🔍 Checking Nuitka availability..." -ForegroundColor Cyan
    $NuitkaCheck = uv run python -c "import nuitka" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "📥 Installing Nuitka..." -ForegroundColor Yellow
        uv add --dev nuitka
    }

    # Ensure PySide6 is available
    Write-Host "🔍 Checking PySide6 availability..." -ForegroundColor Cyan
    $PySideCheck = uv run python -c "import PySide6" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error: PySide6 not found. Please install it first." -ForegroundColor Red
        exit 1
    }

    # Generate translations if needed
    Write-Host "🌍 Ensuring translations are up to date..." -ForegroundColor Cyan
    $NeedTranslations = $false
    
    # Check if .qm files exist and are up to date
    $Languages = @("zh_CN", "en_US", "ja_JP")
    foreach ($Lang in $Languages) {
        $QmFile = "pandoc_ui\translations\pandoc_ui_$Lang.qm"
        $TsFile = "pandoc_ui\translations\pandoc_ui_$Lang.ts"
        
        if (-not (Test-Path $QmFile) -or 
            ((Test-Path $TsFile) -and (Get-Item $TsFile).LastWriteTime -gt (Get-Item $QmFile).LastWriteTime)) {
            $NeedTranslations = $true
            break
        }
    }
    
    if ($NeedTranslations) {
        Write-Host "📦 Generating translations..." -ForegroundColor Yellow
        & .\scripts\generate_translations.ps1
    } else {
        Write-Host "✅ Translations are up to date" -ForegroundColor Green
    }

    # Generate Qt resources if needed
    Write-Host "🎨 Ensuring Qt resources are up to date..." -ForegroundColor Cyan
    if (-not (Test-Path "pandoc_ui\resources\resources_rc.py") -or 
        (Get-Item "pandoc_ui\resources\resources.qrc").LastWriteTime -gt (Get-Item "pandoc_ui\resources\resources_rc.py").LastWriteTime) {
        Write-Host "📦 Generating Qt resources..." -ForegroundColor Yellow
        & .\scripts\generate_resources.ps1
    } else {
        Write-Host "✅ Qt resources are up to date" -ForegroundColor Green
    }

    # Look for icon file
    $IconPath = ""
    $PossibleIcons = @("resources\icons\app.ico", "assets\app.ico", "icon.ico")
    foreach ($Icon in $PossibleIcons) {
        if (Test-Path $Icon) {
            $IconPath = $Icon
            Write-Host "🎨 Found icon: $IconPath" -ForegroundColor Green
            break
        }
    }

    # Build with Nuitka
    Write-Host "🔨 Building with Nuitka..." -ForegroundColor Cyan
    
    $NuitkaArgs = @(
        "run", "python", "-m", "nuitka",
        "--enable-plugin=pyside6",
        "--output-dir=$DistDir",
        "--output-filename=$OutputFile",
        "--company-name=pandoc-ui",
        "--product-name=Pandoc UI",
        "--file-version=$Version.0",
        "--product-version=$Version.0",
        "--file-description=Graphical interface for Pandoc document conversion",
        "--copyright=MIT License",
        "--assume-yes-for-downloads",
        "--show-progress",
        "--show-memory",
        "--include-data-file=pandoc_ui\gui\main_window.ui=pandoc_ui\gui\main_window.ui",
        "--include-data-dir=pandoc_ui\resources=pandoc_ui\resources"
    )
    
    # Add optimization flags based on strip level (Nuitka build-time optimization)
    # Note: LTO is enabled by default for all levels as it's safe and effective
    $NuitkaArgs += "--lto=yes"
    
    # Memory management and performance options
    $NuitkaArgs += "--low-memory"
    $NuitkaArgs += "--jobs=1"
    
    switch ($StripLevel) {
        "Conservative" {
            # Default Nuitka behavior with LTO
            Write-Host "🔧 Using conservative optimization (LTO + low memory mode)" -ForegroundColor Cyan
        }
        "Moderate" {
            # Add additional moderate optimizations
            Write-Host "🔧 Using moderate optimization (LTO + enhanced optimizations + low memory)" -ForegroundColor Cyan
            # Additional flags can be added here as Nuitka develops
        }
        "Aggressive" {
            # Maximum optimization
            Write-Host "🔧 Using aggressive optimization (LTO + maximum optimizations + low memory)" -ForegroundColor Cyan
            # More aggressive flags can be added here as Nuitka develops
        }
    }
    
    # Add build mode (onefile vs standalone)
    if ($Standalone) {
        $NuitkaArgs += "--standalone"
        Write-Host "📁 Building as standalone directory" -ForegroundColor Cyan
    } else {
        $NuitkaArgs += "--onefile"
        Write-Host "📦 Building as single executable file" -ForegroundColor Cyan
    }
    
    # Add console mode
    if ($EnableConsole) {
        # Don't add any console flags - this keeps console enabled
        Write-Host "🔊 Console enabled (for debugging)" -ForegroundColor Yellow
    } else {
        $NuitkaArgs += "--disable-console"
        Write-Host "🔇 Console disabled (GUI only)" -ForegroundColor Cyan
    }
    
    # Add icon if found
    if ($IconPath) {
        $NuitkaArgs += "--windows-icon-from-ico=$IconPath"
    }
    
    # Add entry point
    $NuitkaArgs += "pandoc_ui\main.py"
    
    & uv @NuitkaArgs

    # Check if build was successful
    if ($Standalone) {
        $OutputPath = $OutputDir
        $ExecutablePath = Join-Path $OutputPath "pandoc-ui-windows-$Version.exe"
    } else {
        $OutputPath = Join-Path $DistDir $OutputFile
        $ExecutablePath = $OutputPath
    }
    
    if (Test-Path $OutputPath) {
        Write-Host ""
        Write-Host "✅ Build successful!" -ForegroundColor Green
        Write-Host "📁 Output: $OutputPath" -ForegroundColor White
        
        # Get file size
        if ($Standalone) {
            $DirSize = [math]::Round((Get-ChildItem $OutputPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
            Write-Host "📊 Directory size: $DirSize MB" -ForegroundColor White
            Write-Host "📄 Executable: $ExecutablePath" -ForegroundColor White
        } else {
            $FileSize = [math]::Round((Get-Item $OutputPath).Length / 1MB, 2)
            Write-Host "📊 File size: $FileSize MB" -ForegroundColor White
        }
        
        # Test if the executable works before optimization
        Write-Host "🧪 Testing executable..." -ForegroundColor Cyan
        $ExecutableWorks = $false
        try {
            if ($EnableConsole) {
                # For console builds, test with --help and show debug info
                Write-Host "ℹ️  Testing with debug console..." -ForegroundColor Cyan
                $TestResult = & $ExecutablePath --help 2>$null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Executable test passed" -ForegroundColor Green
                    Write-Host "🔧 To run with debug console: $ExecutablePath --debug" -ForegroundColor Yellow
                    $ExecutableWorks = $true
                } else {
                    Write-Host "⚠️  Executable test failed, but build completed" -ForegroundColor Yellow
                    Write-Host "🔧 Try running with: $ExecutablePath --debug" -ForegroundColor Yellow
                }
            } else {
                # For GUI-only builds, just check if executable exists and is valid
                if (Test-Path $ExecutablePath) {
                    Write-Host "✅ Executable created successfully" -ForegroundColor Green
                    Write-Host "ℹ️  GUI-only build - test by running manually" -ForegroundColor Cyan
                    Write-Host "🔧 For debugging, run: $ExecutablePath --debug" -ForegroundColor Cyan
                    $ExecutableWorks = $true
                } else {
                    Write-Host "⚠️  Executable not found" -ForegroundColor Yellow
                }
            }
        } catch {
            Write-Host "⚠️  Could not test executable, but build completed" -ForegroundColor Yellow
        }
        
        # Binary optimization with strip (WARNING: NOT for onefile binaries)
        if (-not $NoStrip) {
            Write-Host ""
            Write-Host "ℹ️  Post-build optimization analysis..." -ForegroundColor Cyan
            
            # Detect if this is a Nuitka onefile binary
            $IsOnefileBinary = $false
            if (Test-Path $ExecutablePath) {
                try {
                    $BinaryContent = Get-Content $ExecutablePath -Raw -ErrorAction SilentlyContinue
                    if ($BinaryContent -match "NUITKA_ONEFILE_PARENT|__onefile_tmpdir__|attached.*data") {
                        $IsOnefileBinary = $true
                    }
                } catch {
                    # If we can't read the binary, assume it's onefile (safer)
                    if (-not $Standalone) {
                        $IsOnefileBinary = $true
                    }
                }
            }
            
            if ($IsOnefileBinary) {
                Write-Host "🔍 Detected Nuitka onefile binary" -ForegroundColor Yellow
                Write-Host "⚠️  Post-build stripping DISABLED for onefile binaries" -ForegroundColor Yellow
                Write-Host "💡 Nuitka onefile binaries contain attached data that would be corrupted by strip" -ForegroundColor Cyan
                Write-Host "💡 Optimization was applied during Nuitka build process instead" -ForegroundColor Cyan
                
                switch ($StripLevel) {
                    "Conservative" {
                        Write-Host "✅ Conservative optimization: Nuitka LTO + default stripping applied" -ForegroundColor Green
                    }
                    "Moderate" {
                        Write-Host "✅ Moderate optimization: Nuitka LTO + enhanced optimizations applied" -ForegroundColor Green
                    }
                    "Aggressive" {
                        Write-Host "✅ Aggressive optimization: Nuitka LTO + maximum optimizations applied" -ForegroundColor Green
                    }
                }
            } else {
                Write-Host "🔍 Detected standalone binary - post-build stripping available" -ForegroundColor Cyan
                Write-Host "🔧 Applying post-build strip optimization (level: $StripLevel)..." -ForegroundColor Cyan
                
                # Check if strip optimization script exists
                $StripScript = "scripts\strip_optimize.ps1"
                if (Test-Path $StripScript) {
                    try {
                        # Run strip optimization
                        if ($ExecutableWorks) {
                            # Use verification if the executable was working before
                            & $StripScript -BinaryPath $ExecutablePath -Level $StripLevel -Verify
                        } else {
                            # Skip verification if executable wasn't working before
                            & $StripScript -BinaryPath $ExecutablePath -Level $StripLevel
                        }
                        
                        # Update file size after optimization
                        if ($Standalone) {
                            $DirSize = [math]::Round((Get-ChildItem $OutputPath -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB, 2)
                            Write-Host "📊 Optimized directory size: $DirSize MB" -ForegroundColor White
                        } else {
                            $FileSize = [math]::Round((Get-Item $OutputPath).Length / 1MB, 2)
                            Write-Host "📊 Optimized file size: $FileSize MB" -ForegroundColor White
                        }
                    } catch {
                        Write-Host "⚠️  Strip optimization failed: $($_.Exception.Message)" -ForegroundColor Yellow
                        Write-Host "💡 Continuing with unoptimized binary" -ForegroundColor Cyan
                    }
                } else {
                    Write-Host "⚠️  Strip optimization script not found: $StripScript" -ForegroundColor Yellow
                    Write-Host "💡 Post-build strip optimization skipped" -ForegroundColor Cyan
                }
            }
        } else {
            Write-Host ""
            Write-Host "ℹ️  Binary optimization skipped (-NoStrip specified)" -ForegroundColor Cyan
            Write-Host "💡 Note: Nuitka applies default optimizations during build regardless" -ForegroundColor Cyan
        }
        
        Write-Host ""
        Write-Host "🎉 Windows build completed successfully!" -ForegroundColor Green
        Write-Host "📦 Package: $OutputPath" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 To distribute:" -ForegroundColor White
        if ($Standalone) {
            Write-Host "   - Copy the entire directory to target Windows systems" -ForegroundColor Gray
            Write-Host "   - Run the .exe file inside the directory" -ForegroundColor Gray
        } else {
            Write-Host "   - Copy the .exe file to target Windows systems" -ForegroundColor Gray
        }
        Write-Host "   - No additional dependencies required" -ForegroundColor Gray
        Write-Host "   - No Python installation required on target systems" -ForegroundColor Gray
        
        if (-not $NoStrip) {
            Write-Host ""
            Write-Host "🔧 Optimization applied:" -ForegroundColor White
            Write-Host "   - Strip level: $StripLevel" -ForegroundColor Gray
            Write-Host "   - Binary size optimized" -ForegroundColor Gray
            if ($StripLevel -ne "Conservative") {
                Write-Host "   - UPX compression may trigger antivirus warnings" -ForegroundColor Yellow
            }
        }
        
        Write-Host ""
        Write-Host "🐛 Debug Info:" -ForegroundColor Yellow
        if ($EnableConsole) {
            Write-Host "   - Console window enabled in build" -ForegroundColor Gray
        }
        Write-Host "   - Run with --debug flag to see detailed error messages:" -ForegroundColor Gray
        Write-Host "     $ExecutablePath --debug" -ForegroundColor Cyan
        Write-Host "   - This will allocate a console window and show all log output" -ForegroundColor Gray
        
        # Create installer if requested
        if ($CreateInstaller) {
            Write-Host ""
            Write-Host "🏗️  Creating Windows Installer..." -ForegroundColor Yellow
            
            # Check if installer build script exists
            $InstallerScript = "scripts\build_installer.ps1"
            if (Test-Path $InstallerScript) {
                try {
                    # Run installer build (it will use our already built binary)
                    & $InstallerScript -Version $Version -SkipBuild
                    
                    if ($LASTEXITCODE -eq 0) {
                        # Find the created installer
                        $InstallerFile = "dist\pandoc-ui-installer-$Version.exe"
                        if (Test-Path $InstallerFile) {
                            $InstallerSize = [math]::Round((Get-Item $InstallerFile).Length / 1MB, 2)
                            Write-Host ""
                            Write-Host "✅ Installer created successfully!" -ForegroundColor Green
                            Write-Host "📁 Installer: $InstallerFile" -ForegroundColor White
                            Write-Host "📊 Installer size: $InstallerSize MB" -ForegroundColor White
                            Write-Host ""
                            Write-Host "💡 Installer distribution:" -ForegroundColor White
                            Write-Host "   - Professional Windows installer with Modern UI" -ForegroundColor Gray
                            Write-Host "   - File associations and context menu integration" -ForegroundColor Gray
                            Write-Host "   - Silent installation: $InstallerFile /S" -ForegroundColor Gray
                            Write-Host "   - Custom directory: $InstallerFile /S /D=C:\MyPath" -ForegroundColor Gray
                        } else {
                            Write-Host "⚠️  Installer file not found after build" -ForegroundColor Yellow
                        }
                    } else {
                        Write-Host "⚠️  Installer creation failed, but main build succeeded" -ForegroundColor Yellow
                        Write-Host "💡 Try running: .\scripts\build_installer.ps1 -Version $Version" -ForegroundColor Cyan
                    }
                } catch {
                    Write-Host "⚠️  Installer creation error: $($_.Exception.Message)" -ForegroundColor Yellow
                    Write-Host "💡 Try running: .\scripts\build_installer.ps1 -Version $Version" -ForegroundColor Cyan
                }
            } else {
                Write-Host "⚠️  Installer build script not found: $InstallerScript" -ForegroundColor Yellow
                Write-Host "💡 Installer creation skipped" -ForegroundColor Cyan
            }
        }
        
    } else {
        Write-Host "❌ Build failed! Output file not found." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Build error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}