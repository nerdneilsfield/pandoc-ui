# Translation generation script for pandoc-ui (PowerShell)
# Extracts translatable strings and generates .ts/.qm files

param(
    [switch]$Force  # Force regeneration even if files exist
)

# Don't exit on error immediately, we'll handle failures
$ErrorActionPreference = "Continue"

Write-Host "🌍 Generating translations for pandoc-ui..." -ForegroundColor Yellow

# Check if pyside6-lupdate is available
$PylupdateCmd = ""
$LreleaseCmd = ""
if (Get-Command pyside6-lupdate -ErrorAction SilentlyContinue) {
    $PylupdateCmd = "pyside6-lupdate"
    $LreleaseCmd = "pyside6-lrelease"
} elseif (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Host "❌ pyside6-lupdate not found. Trying with uv..." -ForegroundColor Yellow
    $PylupdateCmd = "uv run pyside6-lupdate"
    $LreleaseCmd = "uv run pyside6-lrelease"
} else {
    Write-Host "❌ Neither pyside6-lupdate nor uv found. Please install PySide6." -ForegroundColor Red
    exit 1
}

# Create translations directory
New-Item -ItemType Directory -Force -Path "pandoc_ui\translations" | Out-Null

# Define supported languages
$Languages = @("zh_CN", "ja_JP", "ko_KR", "fr_FR", "de_DE", "es_ES", "zh_TW")
$LanguageNames = @("简体中文", "日本語", "한국어", "Français", "Deutsch", "Español", "繁體中文")

Write-Host "📝 Extracting translatable strings..." -ForegroundColor Cyan

# Collect all Python files
$PythonFiles = Get-ChildItem -Path "pandoc_ui" -Filter "*.py" -Recurse | Where-Object { $_.FullName -notlike "*__pycache__*" } | ForEach-Object { $_.FullName }

# Collect all UI files
$UiFiles = Get-ChildItem -Path "pandoc_ui" -Filter "*.ui" -Recurse | ForEach-Object { $_.FullName }

# Combine all source files
$AllSources = $PythonFiles + $UiFiles
Write-Host "📊 Found $($AllSources.Count) files to scan" -ForegroundColor Cyan

# Generate .ts files for each language
for ($i = 0; $i -lt $Languages.Length; $i++) {
    $Lang = $Languages[$i]
    $LangName = $LanguageNames[$i]
    $TsFile = "pandoc_ui\translations\pandoc_ui_$Lang.ts"
    
    Write-Host "🔍 Extracting strings for $Lang..." -ForegroundColor White
    Write-Host "   Trying pyside6-lupdate..." -ForegroundColor Gray
    
    try {
        if ($PylupdateCmd -eq "pyside6-lupdate") {
            & pyside6-lupdate -no-obsolete @AllSources -ts $TsFile 2>$null
        } else {
            & uv run pyside6-lupdate -no-obsolete @AllSources -ts $TsFile 2>$null
        }
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $TsFile)) {
            $FileSize = (Get-Item $TsFile).Length
            if ($FileSize -gt 100) {
                Write-Host "   ✅ Updated $TsFile ($([math]::Round($FileSize/1KB, 1))KB)" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Generated $TsFile but it seems empty" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   ❌ pyside6-lupdate failed for $TsFile" -ForegroundColor Red
            Write-Host "   🔧 Note: lupdate may fail due to segmentation faults" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ❌ Error generating $TsFile : $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🔄 Updating translations from JSON..." -ForegroundColor Cyan
# Update .ts files with translations from JSON
if (Test-Path "pandoc_ui\translations\translations.json") {
    try {
        if (Get-Command uv -ErrorAction SilentlyContinue) {
            & uv run python scripts\update_translations.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Successfully updated translations from JSON" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Failed to update translations from JSON" -ForegroundColor Yellow
            }
        } else {
            & python scripts\update_translations.py
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ Successfully updated translations from JSON" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Failed to update translations from JSON" -ForegroundColor Yellow
            }
        }
    } catch {
        Write-Host "   ⚠️  Error updating translations: $($_.Exception.Message)" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️  translations.json not found, skipping JSON update" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "⚙️  Compiling .qm files..." -ForegroundColor Cyan

# Compile .ts files to .qm files
foreach ($Lang in $Languages) {
    $TsFile = "pandoc_ui\translations\pandoc_ui_$Lang.ts"
    $QmFile = "pandoc_ui\translations\pandoc_ui_$Lang.qm"
    
    if (Test-Path $TsFile) {
        Write-Host "   Compiling $Lang..." -ForegroundColor White
        
        try {
            if ($LreleaseCmd -eq "pyside6-lrelease") {
                & pyside6-lrelease $TsFile -qm $QmFile 2>$null
            } else {
                & uv run pyside6-lrelease $TsFile -qm $QmFile 2>$null
            }
            
            if ($LASTEXITCODE -eq 0 -and (Test-Path $QmFile)) {
                Write-Host "   ✅ Generated $QmFile" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Failed to generate $QmFile" -ForegroundColor Red
                # Try fallback with system lrelease if available
                if (Get-Command lrelease -ErrorAction SilentlyContinue) {
                    Write-Host "   Trying system lrelease..." -ForegroundColor Yellow
                    & lrelease $TsFile -qm $QmFile
                    if ($LASTEXITCODE -eq 0 -and (Test-Path $QmFile)) {
                        Write-Host "   ✅ Generated $QmFile with system lrelease" -ForegroundColor Green
                    }
                }
            }
        } catch {
            Write-Host "   ❌ Error compiling $QmFile : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠️  Skipping $TsFile (not found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Translation files generated!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "1. Edit pandoc_ui\translations\translations.json to add/update translations" -ForegroundColor Cyan
Write-Host "2. Run this script again to apply translations and compile .qm files" -ForegroundColor Cyan
Write-Host "3. Or use Qt Linguist for visual editing of .ts files" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor White
foreach ($Lang in $Languages) {
    Write-Host "  - pandoc_ui\translations\pandoc_ui_$Lang.ts (source)" -ForegroundColor Gray
    Write-Host "  - pandoc_ui\translations\pandoc_ui_$Lang.qm (compiled)" -ForegroundColor Gray
}
Write-Host ""