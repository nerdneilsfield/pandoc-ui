#!/bin/bash

# Icon generation script for pandoc-ui
# Generates multiple resolution icons from resources/logo.png
# Creates both:
# - resources/icons/ (for Nuitka builds)
# - pandoc_ui/resources/icons/ (for Qt internal resources)

set -e

echo "🎨 Generating icons from resources/logo.png..."

# Check if source logo exists
if [ ! -f "resources/logo.png" ]; then
    echo "❌ Source logo not found: resources/logo.png"
    exit 1
fi

# Check if ImageMagick is available
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick 'convert' command not found. Please install ImageMagick."
    echo "   Ubuntu/Debian: sudo apt-get install imagemagick"
    echo "   macOS: brew install imagemagick"
    exit 1
fi

# Create both icon directories
mkdir -p resources/icons
mkdir -p pandoc_ui/resources/icons

# Define standard icon sizes
SIZES=(16 24 32 48 64 128 256 512 1024)

echo "📐 Generating PNG icons at multiple resolutions..."

# Generate PNG icons at different sizes (for both directories)
for size in "${SIZES[@]}"; do
    # For Nuitka builds
    nuitka_file="resources/icons/logo_${size}.png"
    echo "   → ${size}x${size} px: $nuitka_file"
    convert "resources/logo.png" -resize "${size}x${size}" "$nuitka_file"
    
    # For Qt resources
    qt_file="pandoc_ui/resources/icons/logo_${size}.png"
    echo "   → ${size}x${size} px: $qt_file"
    cp "$nuitka_file" "$qt_file"
done

# Generate Windows ICO file (contains multiple sizes)
echo "🪟 Generating Windows ICO file..."
ico_files=""
for size in 16 24 32 48 64 128 256; do
    ico_files="$ico_files resources/icons/logo_${size}.png"
done
convert $ico_files resources/icons/app.ico
echo "   → resources/icons/app.ico"

# Generate macOS ICNS file
echo "🍎 Generating macOS ICNS file..."
iconset_dir="resources/icons/app.iconset"
mkdir -p "$iconset_dir"

# macOS iconset requires specific naming convention
cp "resources/icons/logo_16.png" "$iconset_dir/icon_16x16.png"
cp "resources/icons/logo_32.png" "$iconset_dir/icon_16x16@2x.png"
cp "resources/icons/logo_32.png" "$iconset_dir/icon_32x32.png"
cp "resources/icons/logo_64.png" "$iconset_dir/icon_32x32@2x.png"
cp "resources/icons/logo_128.png" "$iconset_dir/icon_128x128.png"
cp "resources/icons/logo_256.png" "$iconset_dir/icon_128x128@2x.png"
cp "resources/icons/logo_256.png" "$iconset_dir/icon_256x256.png"
cp "resources/icons/logo_512.png" "$iconset_dir/icon_256x256@2x.png"
cp "resources/icons/logo_512.png" "$iconset_dir/icon_512x512.png"
cp "resources/icons/logo_1024.png" "$iconset_dir/icon_512x512@2x.png"

# Generate ICNS if iconutil is available (macOS only)
if command -v iconutil &> /dev/null; then
    iconutil -c icns "$iconset_dir" -o "resources/icons/app.icns"
    echo "   → resources/icons/app.icns"
    rm -rf "$iconset_dir"
else
    echo "   → $iconset_dir (iconutil not available, keeping iconset directory)"
fi

# Create SVG version for Linux (if not already SVG)
echo "🐧 Preparing Linux icons..."
if [ ! -f "resources/icons/app.svg" ]; then
    # Convert PNG to SVG (basic conversion, manual SVG is better)
    echo "   → Creating basic SVG from PNG"
    convert "resources/logo.png" "resources/icons/app.svg" 2>/dev/null || {
        echo "   ⚠️  SVG conversion failed, copying PNG as fallback"
        cp "resources/logo.png" "resources/icons/app.png"
    }
fi

# Copy main logo files for convenience
cp "resources/icons/logo_256.png" "resources/icons/app.png"
cp "pandoc_ui/resources/icons/logo_256.png" "pandoc_ui/resources/icons/app.png"

echo ""
echo "✅ Icon generation completed!"
echo ""
echo "📁 Generated files:"
echo ""
echo "🔧 For Nuitka builds (external resources):"
echo "   resources/icons/logo_*.png     - Individual PNG files (16px to 1024px)"
echo "   resources/icons/app.ico        - Windows ICO file"
echo "   resources/icons/app.icns       - macOS ICNS file (if iconutil available)"
echo "   resources/icons/app.png        - Main PNG (256px)"
echo ""
echo "🎨 For Qt internal resources:"
echo "   pandoc_ui/resources/icons/logo_*.png - Individual PNG files (16px to 1024px)"
echo "   pandoc_ui/resources/icons/app.png    - Main PNG (256px)"
echo ""
echo "🔧 Next steps:"
echo "   1. Run: ./scripts/generate_resources.sh (to compile Qt resources)"
echo "   2. Build scripts will automatically use external icons"
echo ""