# Translation generation script for pandoc-ui (PowerShell)
# Extracts strings using xgettext and compiles .po files with msgfmt for gettext system

param(
    [switch]$Force  # Force regeneration even if files exist
)

# Don't exit on error immediately, we'll handle failures
$ErrorActionPreference = "Continue"

# Check if we're in the project root
if (!(Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: Run this script from the project root directory" -ForegroundColor Red
    exit 1
}

Write-Host "🔧 Generating translations for pandoc-ui using gettext..." -ForegroundColor Yellow

# Create locales directory structure if it doesn't exist
New-Item -ItemType Directory -Force -Path "pandoc_ui\locales" | Out-Null

# Languages to support
$Languages = @("zh_CN", "ja_JP", "ko_KR", "fr_FR", "de_DE", "es_ES", "zh_TW")

# Find all Python files for translation
Write-Host "📝 Searching for translatable files..." -ForegroundColor Cyan

# Create a temporary file list
$FileList = [System.IO.Path]::GetTempFileName()

# Add all .py files in pandoc_ui (excluding __pycache__ and .pyc)
Get-ChildItem -Path "pandoc_ui" -Filter "*.py" -Recurse | 
    Where-Object { $_.FullName -notlike "*__pycache__*" } | 
    Sort-Object FullName | 
    ForEach-Object { $_.FullName } | 
    Out-File -FilePath $FileList -Encoding UTF8

$FileCount = (Get-Content $FileList).Count
Write-Host "📊 Found $FileCount Python files to scan" -ForegroundColor Cyan

# Extract translatable strings using xgettext
Write-Host "🔍 Extracting translatable strings..." -ForegroundColor Cyan
$PotFile = "pandoc_ui\locales\pandoc_ui.pot"

# Check if xgettext is available
if (!(Get-Command xgettext -ErrorAction SilentlyContinue)) {
    Write-Host "❌ xgettext not found. Please install gettext tools:" -ForegroundColor Red
    Write-Host "   For Windows: Install gettext-tools from GnuWin32 or use WSL" -ForegroundColor Yellow
    Write-Host "   For chocolatey: choco install gettext" -ForegroundColor Yellow
    Write-Host "   For scoop: scoop install gettext" -ForegroundColor Yellow
    exit 1
}

# Use xgettext to extract strings from Python files
try {
    & xgettext `
        --language=Python `
        --keyword=_ `
        --keyword=ngettext:1,2 `
        --output="$PotFile" `
        --from-code=UTF-8 `
        --add-comments=TRANSLATORS `
        --copyright-holder="pandoc-ui project" `
        --package-name="pandoc-ui" `
        --package-version="1.0" `
        --msgid-bugs-address="" `
        --files-from="$FileList"
        
    if ($LASTEXITCODE -eq 0 -and (Test-Path $PotFile)) {
        $StringCount = (Select-String -Path $PotFile -Pattern "^msgid").Count
        Write-Host "   ✓ Extracted $StringCount translatable strings to $PotFile" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to create .pot file" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Error running xgettext: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📝 Creating/updating .po files for each language..." -ForegroundColor Cyan

# Create/update .po files for each language
foreach ($Lang in $Languages) {
    Write-Host "   Processing $Lang..." -ForegroundColor White
    
    # Create directory structure
    $LangDir = "pandoc_ui\locales\$Lang\LC_MESSAGES"
    New-Item -ItemType Directory -Force -Path $LangDir | Out-Null
    
    $PoFile = "$LangDir\pandoc_ui.po"
    
    if (Test-Path $PoFile) {
        # Update existing .po file
        Write-Host "     Updating existing $PoFile..." -ForegroundColor Gray
        try {
            & msgmerge --update --backup=none "$PoFile" "$PotFile"
            if ($LASTEXITCODE -eq 0) {
                Write-Host "     ✓ Updated $PoFile" -ForegroundColor Green
            } else {
                Write-Host "     ❌ Failed to update $PoFile" -ForegroundColor Red
                continue
            }
        } catch {
            Write-Host "     ❌ Error updating $PoFile : $($_.Exception.Message)" -ForegroundColor Red
            continue
        }
    } else {
        # Create new .po file
        Write-Host "     Creating new $PoFile..." -ForegroundColor Gray
        try {
            & msginit --input="$PotFile" --output-file="$PoFile" --locale="$Lang" --no-translator
            if ($LASTEXITCODE -eq 0) {
                Write-Host "     ✓ Created $PoFile" -ForegroundColor Green
            } else {
                Write-Host "     ❌ Failed to create $PoFile" -ForegroundColor Red
                continue
            }
        } catch {
            Write-Host "     ❌ Error creating $PoFile : $($_.Exception.Message)" -ForegroundColor Red
            continue
        }
    }
}

Write-Host ""
Write-Host "⚙️  Compiling .mo files..." -ForegroundColor Cyan

# Compile all .po files to .mo files
foreach ($Lang in $Languages) {
    $LangDir = "pandoc_ui\locales\$Lang\LC_MESSAGES"
    $PoFile = "$LangDir\pandoc_ui.po"
    $MoFile = "$LangDir\pandoc_ui.mo"
    
    if (Test-Path $PoFile) {
        Write-Host "   Compiling $Lang..." -ForegroundColor White
        
        try {
            & msgfmt --output-file="$MoFile" "$PoFile"
            
            if ($LASTEXITCODE -eq 0 -and (Test-Path $MoFile)) {
                Write-Host "   ✓ Generated $MoFile" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Failed to generate $MoFile" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ Error compiling $MoFile : $($_.Exception.Message)" -ForegroundColor Red
        }
    } else {
        Write-Host "   ⚠️  Skipping $Lang (no .po file found)" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ Translation files generated using gettext!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "1. Edit .po files in pandoc_ui\locales\*\LC_MESSAGES\ to add/update translations" -ForegroundColor Cyan
Write-Host "2. Run this script again to compile updated .mo files" -ForegroundColor Cyan
Write-Host "3. Or use a .po editor like Poedit for visual editing" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated files:" -ForegroundColor White
foreach ($Lang in $Languages) {
    Write-Host "  - pandoc_ui\locales\$Lang\LC_MESSAGES\pandoc_ui.po (source)" -ForegroundColor Gray
    Write-Host "  - pandoc_ui\locales\$Lang\LC_MESSAGES\pandoc_ui.mo (compiled)" -ForegroundColor Gray
}

# Clean up temporary files
Remove-Item -Path $FileList -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🌍 Translation system successfully migrated to gettext!" -ForegroundColor Green