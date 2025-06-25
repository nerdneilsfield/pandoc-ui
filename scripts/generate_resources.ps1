# Qt resources generation script for pandoc-ui (PowerShell)
# Compiles Qt resource files into Python modules

param(
    [switch]$Force  # Force regeneration even if files are up to date
)

$ErrorActionPreference = "Stop"

Write-Host "🎨 Generating Qt resources..." -ForegroundColor Yellow

# Check if pyside6-rcc is available
$RccCmd = ""
if (Get-Command pyside6-rcc -ErrorAction SilentlyContinue) {
    $RccCmd = "pyside6-rcc"
} elseif (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "❌ pyside6-rcc not found. Trying with uv..." -ForegroundColor Yellow
    $RccCmd = "uv run pyside6-rcc"
} else {
    Write-Host "❌ Neither pyside6-rcc nor uv found. Please install PySide6." -ForegroundColor Red
    exit 1
}

# Check if QRC file exists
$QrcPath = "pandoc_ui\resources\resources.qrc"
if (-not (Test-Path $QrcPath)) {
    Write-Host "❌ QRC file not found: $QrcPath" -ForegroundColor Red
    Write-Host "   Please create the QRC file first or run generate_icons.sh" -ForegroundColor Red
    exit 1
}

# Check if resources need regeneration
$OutputPath = "pandoc_ui\resources\resources_rc.py"
$ShouldGenerate = $Force

if (-not $Force) {
    if (-not (Test-Path $OutputPath)) {
        $ShouldGenerate = $true
        Write-Host "🔄 Output file doesn't exist, generating..." -ForegroundColor Cyan
    } elseif ((Get-Item $QrcPath).LastWriteTime -gt (Get-Item $OutputPath).LastWriteTime) {
        $ShouldGenerate = $true
        Write-Host "🔄 QRC file is newer, regenerating..." -ForegroundColor Cyan
    } else {
        Write-Host "✅ Qt resources are up to date" -ForegroundColor Green
        Write-Host "   Use -Force to regenerate anyway" -ForegroundColor Gray
        return
    }
}

if ($ShouldGenerate) {
    try {
        # Generate Python resource module
        Write-Host "📦 Compiling resources.qrc to resources_rc.py..." -ForegroundColor Cyan
        
        # Split command for proper execution
        if ($RccCmd -eq "pyside6-rcc") {
            & pyside6-rcc $QrcPath -o $OutputPath
        } else {
            & uv run pyside6-rcc $QrcPath -o $OutputPath
        }
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to compile Qt resources" -ForegroundColor Red
            exit 1
        }
        
        if (Test-Path $OutputPath) {
            Write-Host "✅ Qt resources compiled successfully!" -ForegroundColor Green
            Write-Host "   → $OutputPath" -ForegroundColor White
            
            # Get file size
            $FileSize = [math]::Round((Get-Item $OutputPath).Length / 1KB, 1)
            Write-Host "📊 Generated file size: $FileSize KB" -ForegroundColor White
            
            Write-Host "" -ForegroundColor White
            Write-Host "📝 You can now import resources in your code:" -ForegroundColor White
            Write-Host "   from pandoc_ui.resources import resources_rc" -ForegroundColor Cyan
            Write-Host "   icon = QIcon(':/icons/logo')" -ForegroundColor Cyan
        } else {
            Write-Host "❌ Failed to generate $OutputPath" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "❌ Error during resource compilation: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}