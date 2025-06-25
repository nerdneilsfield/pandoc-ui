#!/bin/bash
# Simple translation compilation script for pandoc-ui
# Only compiles existing .ts files to .qm files

set -e  # Exit on any error

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo "🔧 Compiling translations for pandoc-ui..."

# Languages to support
LANGUAGES=("zh_CN" "ja_JP" "ko_KR" "fr_FR" "de_DE" "es_ES" "zh_TW")

# Check if lrelease exists
LRELEASE=""
if [ -f ".venv/lib/python3.12/site-packages/PySide6/lrelease" ]; then
    LRELEASE=".venv/lib/python3.12/site-packages/PySide6/lrelease"
elif command -v lrelease &> /dev/null; then
    LRELEASE="lrelease"
else
    echo "❌ Error: lrelease not found. Please install Qt tools."
    exit 1
fi

echo "⚙️  Compiling .qm files..."

# Compile all .ts files to .qm files
for lang in "${LANGUAGES[@]}"; do
    ts_file="pandoc_ui/translations/pandoc_ui_${lang}.ts"
    qm_file="pandoc_ui/translations/pandoc_ui_${lang}.qm"
    
    if [ -f "$ts_file" ]; then
        echo "   Compiling $lang..."
        $LRELEASE "$ts_file" -qm "$qm_file"
        
        if [ -f "$qm_file" ]; then
            echo "   ✓ Generated $qm_file"
        else
            echo "   ❌ Failed to generate $qm_file"
        fi
    else
        echo "   ⚠️  Skipping $lang - $ts_file not found"
    fi
done

echo ""
echo "✅ Translation compilation complete!"
echo ""
echo "📝 Note: This script only compiles existing .ts files."
echo "To extract new strings, you'll need to:"
echo "1. Use Qt Linguist to update .ts files"
echo "2. Or manually edit the .ts XML files"
echo "3. Then run this script again to compile"