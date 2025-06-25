#!/bin/bash

# Qt resources generation script for pandoc-ui
# Compiles Qt resource files into Python modules

set -e

echo "🎨 Generating Qt resources..."

# Check if pyside6-rcc is available
if ! command -v pyside6-rcc &> /dev/null; then
    echo "❌ pyside6-rcc not found. Trying with uv..."
    if command -v uv &> /dev/null; then
        RCC_CMD="uv run pyside6-rcc"
    else
        echo "❌ Neither pyside6-rcc nor uv found. Please install PySide6."
        exit 1
    fi
else
    RCC_CMD="pyside6-rcc"
fi

# Check if QRC file exists
if [ ! -f "pandoc_ui/resources/resources.qrc" ]; then
    echo "❌ QRC file not found: pandoc_ui/resources/resources.qrc"
    echo "   Please create the QRC file first or run generate_icons.sh"
    exit 1
fi

# Generate Python resource module
echo "📦 Compiling resources.qrc to resources_rc.py..."
$RCC_CMD "pandoc_ui/resources/resources.qrc" -o "pandoc_ui/resources/resources_rc.py"

if [ -f "pandoc_ui/resources/resources_rc.py" ]; then
    echo "✅ Qt resources compiled successfully!"
    echo "   → pandoc_ui/resources/resources_rc.py"
    echo ""
    echo "📝 You can now import resources in your code:"
    echo "   from pandoc_ui.resources import resources_rc"
    echo "   icon = QIcon(':/icons/logo')"
else
    echo "❌ Failed to generate resources_rc.py"
    exit 1
fi