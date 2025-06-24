# Windows build script using Nuitka via uv
# Builds pandoc-ui into a single executable file for Windows distribution
# For Linux and macOS, use scripts/build.sh

$ErrorActionPreference = "Stop"

Write-Host "🪟 Building pandoc-ui for Windows..." -ForegroundColor Yellow

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

# Set build directories
$BuildDir = "build\windows"
$DistDir = "dist\windows"
$OutputFile = "pandoc-ui-windows-$Version.exe"

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
        "--onefile",
        "--enable-plugin=pyside6",
        "--disable-console",
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
        "--show-memory"
    )
    
    # Add icon if found
    if ($IconPath) {
        $NuitkaArgs += "--windows-icon-from-ico=$IconPath"
    }
    
    # Add entry point
    $NuitkaArgs += "pandoc_ui\main.py"
    
    & uv @NuitkaArgs

    # Check if build was successful
    $OutputPath = Join-Path $DistDir $OutputFile
    if (Test-Path $OutputPath) {
        Write-Host ""
        Write-Host "✅ Build successful!" -ForegroundColor Green
        Write-Host "📁 Output: $OutputPath" -ForegroundColor White
        
        # Get file size
        $FileSize = [math]::Round((Get-Item $OutputPath).Length / 1MB, 2)
        Write-Host "📊 File size: $FileSize MB" -ForegroundColor White
        
        # Test if the executable works
        Write-Host "🧪 Testing executable..." -ForegroundColor Cyan
        try {
            $TestResult = & $OutputPath --help 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Executable test passed" -ForegroundColor Green
            } else {
                Write-Host "⚠️  Executable test failed, but build completed" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "⚠️  Could not test executable, but build completed" -ForegroundColor Yellow
        }
        
        Write-Host ""
        Write-Host "🎉 Windows build completed successfully!" -ForegroundColor Green
        Write-Host "📦 Package: $OutputPath" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 To distribute:" -ForegroundColor White
        Write-Host "   - Copy the .exe file to target Windows systems" -ForegroundColor Gray
        Write-Host "   - No additional dependencies required" -ForegroundColor Gray
        Write-Host "   - No Python installation required on target systems" -ForegroundColor Gray
        
    } else {
        Write-Host "❌ Build failed! Output file not found." -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "❌ Build error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}