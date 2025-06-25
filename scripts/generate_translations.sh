#!/bin/bash
# Translation generation script for pandoc-ui
# Extracts strings using xgettext and compiles .po files with msgfmt for gettext system

# Don't exit on error immediately, we'll handle failures
set +e

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Run this script from the project root directory"
    exit 1
fi

echo "🔧 Generating translations for pandoc-ui using gettext..."

# Create locales directory structure if it doesn't exist
mkdir -p pandoc_ui/locales

# Languages to support
LANGUAGES=("zh_CN" "ja_JP" "ko_KR" "fr_FR" "de_DE" "es_ES" "zh_TW")

# Find all Python files for translation
echo "📝 Searching for translatable files..."

# Create a temporary file list
FILE_LIST=$(mktemp)

# Add all .py files in pandoc_ui (excluding __pycache__ and .pyc)
find pandoc_ui -name "*.py" -type f | grep -v __pycache__ | sort > "$FILE_LIST"

FILE_COUNT=$(wc -l < "$FILE_LIST")
echo "📊 Found $FILE_COUNT Python files to scan"

# Extract translatable strings using xgettext
echo "🔍 Extracting translatable strings..."
pot_file="pandoc_ui/locales/pandoc_ui.pot"

# Use xgettext to extract strings from Python files
xgettext \
    --language=Python \
    --keyword=_ \
    --keyword=ngettext:1,2 \
    --output="$pot_file" \
    --from-code=UTF-8 \
    --add-comments=TRANSLATORS \
    --copyright-holder="pandoc-ui project" \
    --package-name="pandoc-ui" \
    --package-version="1.0" \
    --msgid-bugs-address="" \
    --files-from="$FILE_LIST"

if [ $? -eq 0 ] && [ -f "$pot_file" ]; then
    string_count=$(grep -c "^msgid" "$pot_file")
    echo "   ✓ Extracted $string_count translatable strings to $pot_file"
else
    echo "   ❌ Failed to create .pot file"
    echo "   🔧 Please install gettext tools:"
    echo "      Ubuntu/Debian: sudo apt-get install gettext"
    echo "      Fedora: sudo dnf install gettext"
    echo "      macOS: brew install gettext"
    exit 1
fi

echo ""
echo "📝 Creating/updating .po files for each language..."

# Create/update .po files for each language
for lang in "${LANGUAGES[@]}"; do
    echo "   Processing $lang..."
    
    # Create directory structure
    lang_dir="pandoc_ui/locales/$lang/LC_MESSAGES"
    mkdir -p "$lang_dir"
    
    po_file="$lang_dir/pandoc_ui.po"
    
    if [ -f "$po_file" ]; then
        # Update existing .po file
        echo "     Updating existing $po_file..."
        msgmerge --update --backup=none "$po_file" "$pot_file"
        if [ $? -eq 0 ]; then
            echo "     ✓ Updated $po_file"
        else
            echo "     ❌ Failed to update $po_file"
            continue
        fi
    else
        # Create new .po file
        echo "     Creating new $po_file..."
        msginit --input="$pot_file" --output-file="$po_file" --locale="$lang" --no-translator
        if [ $? -eq 0 ]; then
            echo "     ✓ Created $po_file"
        else
            echo "     ❌ Failed to create $po_file"
            continue
        fi
    fi
done

echo ""
echo "⚙️  Compiling .mo files..."

# Compile all .po files to .mo files
for lang in "${LANGUAGES[@]}"; do
    lang_dir="pandoc_ui/locales/$lang/LC_MESSAGES"
    po_file="$lang_dir/pandoc_ui.po"
    mo_file="$lang_dir/pandoc_ui.mo"
    
    if [ -f "$po_file" ]; then
        echo "   Compiling $lang..."
        
        msgfmt --output-file="$mo_file" "$po_file"
        
        if [ $? -eq 0 ] && [ -f "$mo_file" ]; then
            echo "   ✓ Generated $mo_file"
        else
            echo "   ❌ Failed to generate $mo_file"
        fi
    else
        echo "   ⚠️  Skipping $lang (no .po file found)"
    fi
done

echo ""
echo "✅ Translation files generated using gettext!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .po files in pandoc_ui/locales/*/LC_MESSAGES/ to add/update translations"
echo "2. Run this script again to compile updated .mo files"
echo "3. Or use a .po editor like Poedit for visual editing"
echo ""
echo "Generated files:"
for lang in "${LANGUAGES[@]}"; do
    echo "  - pandoc_ui/locales/$lang/LC_MESSAGES/pandoc_ui.po (source)"
    echo "  - pandoc_ui/locales/$lang/LC_MESSAGES/pandoc_ui.mo (compiled)"
done

# Clean up temporary files
rm -f "$FILE_LIST"

echo ""
echo "🌍 Translation system successfully migrated to gettext!"