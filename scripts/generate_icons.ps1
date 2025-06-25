# Icon generation script for pandoc-ui (PowerShell)
# Generates multiple resolution icons from resources/logo.png
# Creates both:
# - resources/icons/ (for Nuitka builds)
# - pandoc_ui/resources/icons/ (for Qt internal resources)

param(
    [switch]$Force  # Force regeneration even if files exist
)

$ErrorActionPreference = "Stop"

Write-Host "🎨 Generating icons from resources/logo.png..." -ForegroundColor Yellow

# Check if source logo exists
if (-not (Test-Path "resources\logo.png")) {
    Write-Host "❌ Source logo not found: resources\logo.png" -ForegroundColor Red
    exit 1
}

# Check if ImageMagick is available
$ConvertCmd = ""
if (Get-Command convert -ErrorAction SilentlyContinue) {
    $ConvertCmd = "convert"
} elseif (Get-Command magick -ErrorAction SilentlyContinue) {
    # ImageMagick 7+ on Windows often uses 'magick' command
    $ConvertCmd = "magick convert"
} else {
    Write-Host "❌ ImageMagick not found. Please install ImageMagick." -ForegroundColor Red
    Write-Host "   Download from: https://imagemagick.org/script/download.php#windows" -ForegroundColor Red
    Write-Host "   Or via chocolatey: choco install imagemagick" -ForegroundColor Red
    exit 1
}

# Create both icon directories
New-Item -ItemType Directory -Force -Path "resources\icons" | Out-Null
New-Item -ItemType Directory -Force -Path "pandoc_ui\resources\icons" | Out-Null

# Define standard icon sizes
$Sizes = @(16, 24, 32, 48, 64, 128, 256, 512, 1024)

Write-Host "📐 Generating PNG icons at multiple resolutions..." -ForegroundColor Cyan

# Generate PNG icons at different sizes (for both directories)
foreach ($Size in $Sizes) {
    # For Nuitka builds
    $NuitkaFile = "resources\icons\logo_$Size.png"
    Write-Host "   → ${Size}x${Size} px: $NuitkaFile" -ForegroundColor White
    
    if ($ConvertCmd -eq "convert") {
        & convert "resources\logo.png" -resize "${Size}x${Size}" $NuitkaFile
    } else {
        & magick convert "resources\logo.png" -resize "${Size}x${Size}" $NuitkaFile
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to generate $NuitkaFile" -ForegroundColor Red
        exit 1
    }
    
    # For Qt resources
    $QtFile = "pandoc_ui\resources\icons\logo_$Size.png"
    Write-Host "   → ${Size}x${Size} px: $QtFile" -ForegroundColor White
    Copy-Item $NuitkaFile $QtFile
}

# Generate Windows ICO file (contains multiple sizes)
Write-Host "🪟 Generating Windows ICO file..." -ForegroundColor Cyan
$IcoFiles = @()
foreach ($Size in @(16, 24, 32, 48, 64, 128, 256)) {
    $IcoFiles += "resources\icons\logo_$Size.png"
}

try {
    if ($ConvertCmd -eq "convert") {
        & convert @IcoFiles "resources\icons\app.ico"
    } else {
        & magick convert @IcoFiles "resources\icons\app.ico"
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   → resources\icons\app.ico" -ForegroundColor Green
    } else {
        Write-Host "⚠️  ICO generation failed, but continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  ICO generation failed: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Generate macOS ICNS file (basic attempt on Windows)
Write-Host "🍎 Preparing macOS iconset structure..." -ForegroundColor Cyan
$IconsetDir = "resources\icons\app.iconset"
New-Item -ItemType Directory -Force -Path $IconsetDir | Out-Null

# macOS iconset requires specific naming convention
Copy-Item "resources\icons\logo_16.png" "$IconsetDir\icon_16x16.png"
Copy-Item "resources\icons\logo_32.png" "$IconsetDir\icon_16x16@2x.png"
Copy-Item "resources\icons\logo_32.png" "$IconsetDir\icon_32x32.png"
Copy-Item "resources\icons\logo_64.png" "$IconsetDir\icon_32x32@2x.png"
Copy-Item "resources\icons\logo_128.png" "$IconsetDir\icon_128x128.png"
Copy-Item "resources\icons\logo_256.png" "$IconsetDir\icon_128x128@2x.png"
Copy-Item "resources\icons\logo_256.png" "$IconsetDir\icon_256x256.png"
Copy-Item "resources\icons\logo_512.png" "$IconsetDir\icon_256x256@2x.png"
Copy-Item "resources\icons\logo_512.png" "$IconsetDir\icon_512x512.png"
Copy-Item "resources\icons\logo_1024.png" "$IconsetDir\icon_512x512@2x.png"

Write-Host "   → $IconsetDir (iconutil not available on Windows)" -ForegroundColor Yellow

# Create PNG version for Linux compatibility
Write-Host "🐧 Preparing Linux icons..." -ForegroundColor Cyan
Copy-Item "resources\icons\logo_256.png" "resources\icons\app.png"

# Copy main logo files for convenience
Copy-Item "resources\icons\logo_256.png" "resources\icons\app.png"
Copy-Item "pandoc_ui\resources\icons\logo_256.png" "pandoc_ui\resources\icons\app.png"

Write-Host ""
Write-Host "✅ Icon generation completed!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Generated files:" -ForegroundColor White
Write-Host ""
Write-Host "🔧 For Nuitka builds (external resources):" -ForegroundColor White
Write-Host "   resources\icons\logo_*.png     - Individual PNG files (16px to 1024px)" -ForegroundColor Gray
Write-Host "   resources\icons\app.ico        - Windows ICO file" -ForegroundColor Gray
Write-Host "   resources\icons\app.iconset    - macOS iconset directory" -ForegroundColor Gray
Write-Host "   resources\icons\app.png        - Main PNG (256px)" -ForegroundColor Gray
Write-Host ""
Write-Host "🎨 For Qt internal resources:" -ForegroundColor White
Write-Host "   pandoc_ui\resources\icons\logo_*.png - Individual PNG files (16px to 1024px)" -ForegroundColor Gray
Write-Host "   pandoc_ui\resources\icons\app.png    - Main PNG (256px)" -ForegroundColor Gray
Write-Host ""
Write-Host "🔧 Next steps:" -ForegroundColor White
Write-Host "   1. Run: .\scripts\generate_resources.ps1 (to compile Qt resources)" -ForegroundColor Cyan
Write-Host "   2. Build scripts will automatically use external icons" -ForegroundColor Cyan
Write-Host ""