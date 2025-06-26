#!/bin/bash

# 简化的AppImage构建脚本
# 使用Nuitka的内置AppImage支持（--onefile模式）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

print_info "🚀 Building simple AppImage for pandoc-ui using Nuitka..."

# 检查操作系统
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    print_error "This script only works on Linux"
    exit 1
fi

# 获取项目根目录
PROJECT_ROOT=$(dirname $(dirname $(readlink -f $0)))
cd "$PROJECT_ROOT"

# 获取版本信息
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/' || echo "dev")
print_info "📦 Building version: $VERSION"

# 设置构建目录
BUILD_DIR="build/simple-appimage"
DIST_DIR="dist"
OUTPUT_FILE="pandoc-ui-simple-$VERSION-x86_64.AppImage"

# 清理之前的构建
print_info "🧹 Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$BUILD_DIR" "$DIST_DIR"

# 检查必要工具
print_info "🔍 Checking required tools..."

# 检查uv
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first."
    exit 1
fi

# 检查Nuitka
if ! uv run python -c "import nuitka" 2>/dev/null; then
    print_info "📥 Installing Nuitka..."
    uv add --dev nuitka
fi

# 检查PySide6
if ! uv run python -c "import PySide6" 2>/dev/null; then
    print_error "PySide6 not found. Please install it first."
    exit 1
fi

# 生成翻译和资源文件
print_info "🌍 Generating translations..."
if [ -f "scripts/generate_translations.sh" ]; then
    ./scripts/generate_translations.sh || print_warning "Translation generation failed"
fi

print_info "🎨 Generating Qt resources..."
if [ -f "scripts/generate_resources.sh" ]; then
    ./scripts/generate_resources.sh || print_warning "Resource generation failed"
fi

# 查找图标文件
print_info "🎨 Setting up application icon..."
ICON_ARG=""
for icon_path in "resources/logo.png" "resources/icons/app.png" "assets/icon.png" "icon.png"; do
    if [ -f "$icon_path" ]; then
        ICON_ARG="--linux-icon=$icon_path"
        print_info "📸 Found icon: $icon_path"
        break
    fi
done

if [ -z "$ICON_ARG" ]; then
    print_warning "No icon found, building without custom icon"
fi

# 构建Nuitka AppImage
print_info "🔨 Building with Nuitka (onefile mode creates AppImage on Linux)..."

NUITKA_ARGS=(
    --onefile
    --enable-plugin=pyside6
    --disable-console
    --output-dir="$DIST_DIR"
    --output-filename="$OUTPUT_FILE"
    --company-name="pandoc-ui"
    --product-name="Pandoc UI"
    --file-version="$VERSION"
    --product-version="$VERSION"
    --file-description="Graphical interface for Pandoc document conversion"
    --copyright="MIT License"
    --assume-yes-for-downloads
    --show-progress
    --show-memory
    --include-data-file=pandoc_ui/gui/main_window.ui=pandoc_ui/gui/main_window.ui
    --include-data-dir=pandoc_ui/resources=pandoc_ui/resources
    --static-libpython=no
    --linux-icon-recursive
)

# 添加图标参数
if [ ! -z "$ICON_ARG" ]; then
    NUITKA_ARGS+=($ICON_ARG)
fi

# 添加翻译文件
if [ -d "pandoc_ui/translations" ]; then
    NUITKA_ARGS+=(--include-data-dir=pandoc_ui/translations=pandoc_ui/translations)
fi

# 执行Nuitka构建
uv run python -m nuitka "${NUITKA_ARGS[@]}" pandoc_ui/main.py

# 检查构建结果
FINAL_APPIMAGE="$DIST_DIR/$OUTPUT_FILE"
if [ ! -f "$FINAL_APPIMAGE" ]; then
    print_error "AppImage build failed - output file not found"
    print_info "Expected: $FINAL_APPIMAGE"
    ls -la "$DIST_DIR"/ 2>/dev/null || print_info "Dist directory is empty"
    exit 1
fi

# 确保AppImage可执行
chmod +x "$FINAL_APPIMAGE"

# 测试AppImage
print_info "🧪 Testing AppImage..."
if "$FINAL_APPIMAGE" --help &>/dev/null; then
    print_success "AppImage basic test passed"
else
    print_warning "AppImage basic test failed, but AppImage was created"
fi

# 获取文件信息
FILE_SIZE=$(du -h "$FINAL_APPIMAGE" | cut -f1)

print_success "🎉 Simple AppImage build completed successfully!"
print_info "📁 Output: $FINAL_APPIMAGE"
print_info "📊 File size: $FILE_SIZE"

echo ""
print_info "💡 Usage instructions:"
echo "   1. Run directly: ./$FINAL_APPIMAGE"
echo "   2. Or double-click in file manager"
echo "   3. AppImage is already executable"
echo ""
print_info "🚀 Distribution:"
echo "   - Copy the AppImage file to target Linux systems"
echo "   - No installation required"
echo "   - Works on most modern Linux distributions"
echo "   - No Python installation required on target systems"

# 生成校验和
if command -v sha256sum &> /dev/null; then
    CHECKSUM_FILE="${FINAL_APPIMAGE}.sha256"
    sha256sum "$FINAL_APPIMAGE" > "$CHECKSUM_FILE"
    print_info "🔐 Checksum: $CHECKSUM_FILE"
fi

# 显示AppImage信息
print_info "📋 AppImage Information:"
echo "   Built with: Nuitka --onefile (native AppImage support)"
echo "   Architecture: x86_64"
echo "   Python: $(python3 --version)"
echo "   PySide6: $(uv run python -c "import PySide6; print(PySide6.__version__)" 2>/dev/null || echo "unknown")"

print_success "✨ All done! This is the simplest way to create an AppImage with Nuitka."