#!/bin/bash
# Reset and regenerate translation files from scratch

set -e

echo "🔄 Resetting translation files..."

# Backup existing translations
echo "📦 Backing up existing translations..."
mkdir -p pandoc_ui/translations/backup
cp pandoc_ui/translations/*.ts pandoc_ui/translations/backup/ 2>/dev/null || true

# Remove all existing .ts files
echo "🗑️  Removing old .ts files..."
rm -f pandoc_ui/translations/pandoc_ui_*.ts

# Run the generate script
echo "🔧 Regenerating translations from scratch..."
bash scripts/generate_translations.sh

echo "✅ Translation files have been reset!"
echo ""
echo "📝 The new .ts files now contain all current translatable strings."
echo "   You'll need to add translations for each language again."
echo ""
echo "💾 Old translations are backed up in: pandoc_ui/translations/backup/"