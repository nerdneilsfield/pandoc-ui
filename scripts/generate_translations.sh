#!/bin/bash
# Translation generation script for pandoc-ui
# Extracts strings using lupdate and compiles .qm files with lrelease

# Don't exit on error immediately, we'll handle failures
set +e

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo "🔧 Generating translations for pandoc-ui..."

# Create translations directory if it doesn't exist
mkdir -p pandoc_ui/translations

# Languages to support
LANGUAGES=("zh_CN" "ja_JP" "ko_KR" "fr_FR" "de_DE" "es_ES" "zh_TW")

# Find all Python files and UI files for translation
echo "📝 Searching for translatable files..."

# Create a temporary file list
FILE_LIST=$(mktemp)

# Add all .py files in pandoc_ui (excluding __pycache__ and .pyc)
find pandoc_ui -name "*.py" -type f | grep -v __pycache__ | sort > "$FILE_LIST"

# Add all .ui files
find pandoc_ui -name "*.ui" -type f | sort >> "$FILE_LIST"

FILE_COUNT=$(wc -l < "$FILE_LIST")
echo "📊 Found $FILE_COUNT files to scan"

# Build complete file list first
echo "📄 Building complete file list..."
ALL_FILES=""

# Add UI files
for uifile in $(find pandoc_ui -name "*.ui" -type f | sort); do
    ALL_FILES="$ALL_FILES $uifile"
done

# Add Python files
for pyfile in $(find pandoc_ui -name "*.py" -type f | grep -v __pycache__ | sort); do
    ALL_FILES="$ALL_FILES $pyfile"
done

echo "   Found $(echo $ALL_FILES | wc -w) files total"

# Extract translatable strings for each language
for lang in "${LANGUAGES[@]}"; do
    echo "🔍 Extracting strings for $lang..."
    ts_file="pandoc_ui/translations/pandoc_ui_${lang}.ts"
    
    # Try pyside6-lupdate with all files at once
    echo "   Trying pyside6-lupdate..."
    uv run pyside6-lupdate $ALL_FILES -no-obsolete -ts "$ts_file" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "   pyside6-lupdate failed, trying system lupdate..."
        # Try system lupdate as fallback
        if command -v lupdate &> /dev/null; then
            lupdate $ALL_FILES -no-obsolete -ts "$ts_file"
            if [ $? -ne 0 ]; then
                echo "   ❌ Both pyside6-lupdate and lupdate failed for $ts_file"
                continue
            fi
        else
            echo "   ❌ pyside6-lupdate failed and system lupdate not found"
            echo "   🔧 Please install Qt linguistic tools:"
            echo "      Ubuntu/Debian: sudo apt-get install qttools5-dev-tools"
            echo "      Fedora: sudo dnf install qt5-linguist"
            echo "      macOS: brew install qt"
            continue
        fi
    fi
    
    # Check if the file was created/updated
    if [ -f "$ts_file" ]; then
        file_size=$(stat -c%s "$ts_file" 2>/dev/null || stat -f%z "$ts_file" 2>/dev/null || echo "0")
        if [ "$file_size" -gt 100 ]; then
            echo "   ✓ Updated $ts_file ($(echo $file_size | numfmt --to=iec-i --suffix=B 2>/dev/null || echo "${file_size} bytes"))"
        else
            echo "   ⚠️  Generated $ts_file but it seems empty"
        fi
    else
        echo "   ❌ Failed to create $ts_file"
    fi
done

echo ""
echo "🔄 Updating translations from JSON..."
# Update .ts files with translations from JSON
if [ -f "pandoc_ui/translations/translations.json" ]; then
    uv run python scripts/update_translations.py
    if [ $? -ne 0 ]; then
        echo "   ⚠️  Failed to update translations from JSON"
    fi
else
    echo "   ⚠️  translations.json not found, skipping JSON update"
fi

echo ""
echo "⚙️  Compiling .qm files..."

# Compile all .ts files to .qm files
for lang in "${LANGUAGES[@]}"; do
    ts_file="pandoc_ui/translations/pandoc_ui_${lang}.ts"
    qm_file="pandoc_ui/translations/pandoc_ui_${lang}.qm"
    
    if [ -f "$ts_file" ]; then
        echo "   Compiling $lang..."
        
        # Try pyside6-lrelease first
        uv run pyside6-lrelease "$ts_file" -qm "$qm_file" 2>/dev/null
        
        if [ $? -ne 0 ]; then
            # Try system lrelease as fallback
            if command -v lrelease &> /dev/null; then
                lrelease "$ts_file" -qm "$qm_file"
                if [ $? -ne 0 ]; then
                    echo "   ❌ Both pyside6-lrelease and lrelease failed for $qm_file"
                    continue
                fi
            else
                echo "   ❌ pyside6-lrelease failed and system lrelease not found"
                continue
            fi
        fi
        
        if [ -f "$qm_file" ]; then
            echo "   ✓ Generated $qm_file"
        else
            echo "   ❌ Failed to generate $qm_file"
        fi
    fi
done

echo ""
echo "✅ Translation files generated!"
echo ""
echo "📝 Next steps:"
echo "1. Edit pandoc_ui/translations/translations.json to add/update translations"
echo "2. Run this script again to apply translations and compile .qm files"
echo "3. Or use Qt Linguist for visual editing of .ts files"
echo ""
echo "Generated files:"
for lang in "${LANGUAGES[@]}"; do
    echo "  - pandoc_ui/translations/pandoc_ui_${lang}.ts (source)"
    echo "  - pandoc_ui/translations/pandoc_ui_${lang}.qm (compiled)"
done

# Clean up temporary file
rm -f "$FILE_LIST"