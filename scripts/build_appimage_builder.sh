#!/bin/bash

# 使用appimage-builder构建pandoc-ui AppImage
# 这是一个高级自动化构建方案

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

print_info "🚀 Building AppImage for pandoc-ui using appimage-builder..."

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
export VERSION

print_info "📦 Building version: $VERSION"

# 检查必要工具
print_info "🔍 Checking required tools..."

# 检查Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

# 检查uv
if ! command -v uv &> /dev/null; then
    print_error "uv is not installed. Please install uv first."
    exit 1
fi

# 检查或安装appimage-builder
if ! command -v appimage-builder &> /dev/null; then
    print_info "📥 Installing appimage-builder..."
    
    # 尝试使用pip安装
    if command -v pip3 &> /dev/null; then
        pip3 install --user appimage-builder
        
        # 添加到PATH
        export PATH="$HOME/.local/bin:$PATH"
        
        if ! command -v appimage-builder &> /dev/null; then
            print_error "Failed to install appimage-builder via pip"
            print_info "Please install appimage-builder manually:"
            print_info "  pip3 install --user appimage-builder"
            exit 1
        fi
    else
        print_error "pip3 not found. Please install appimage-builder manually."
        exit 1
    fi
fi

# 检查Docker（用于测试）
DOCKER_AVAILABLE=false
if command -v docker &> /dev/null && docker info &> /dev/null; then
    DOCKER_AVAILABLE=true
    print_info "🐳 Docker is available for testing"
else
    print_warning "Docker not available - skipping automated tests"
fi

# 清理之前的构建
print_info "🧹 Cleaning previous builds..."
rm -rf AppDir
rm -rf dist
mkdir -p dist

# 确保配置文件存在
APPIMAGE_BUILDER_CONFIG="scripts/AppImageBuilder.yml"
if [ ! -f "$APPIMAGE_BUILDER_CONFIG" ]; then
    print_error "AppImageBuilder.yml not found at $APPIMAGE_BUILDER_CONFIG"
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

# 创建应用图标（如果不存在）
print_info "🎨 Setting up application icon..."
ICON_FILE="pandoc-ui.png"

if [ ! -f "$ICON_FILE" ]; then
    # 查找图标文件
    for icon_path in "resources/logo.png" "resources/icons/app.png" "assets/icon.png" "icon.png"; do
        if [ -f "$icon_path" ]; then
            cp "$icon_path" "$ICON_FILE"
            print_info "📸 Found and copied icon: $icon_path"
            break
        fi
    done
    
    # 如果还是没有图标，创建一个简单的占位符
    if [ ! -f "$ICON_FILE" ]; then
        if command -v convert &> /dev/null; then
            convert -size 256x256 xc:lightblue -pointsize 48 -fill black -gravity center -annotate 0 "PU" "$ICON_FILE"
            print_info "🎨 Created placeholder icon"
        else
            print_warning "No icon found and ImageMagick not available to create placeholder"
        fi
    fi
fi

# 创建desktop文件
print_info "📄 Creating desktop file..."
DESKTOP_FILE="pandoc-ui.desktop"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Pandoc UI
Comment=Graphical interface for Pandoc document conversion
Comment[zh_CN]=Pandoc 文档转换的图形界面
GenericName=Document Converter
GenericName[zh_CN]=文档转换器
Exec=pandoc-ui
Icon=pandoc-ui
Terminal=false
Categories=Office;Publishing;Utility;
MimeType=text/plain;text/markdown;text/x-markdown;
Keywords=pandoc;converter;document;markdown;
Version=$VERSION
X-AppImage-Version=$VERSION
StartupNotify=true
EOF

# 运行appimage-builder
print_info "🔨 Running appimage-builder..."

# 根据是否有Docker调整构建参数
if [ "$DOCKER_AVAILABLE" = true ]; then
    # 完整构建包含测试
    appimage-builder --recipe "$APPIMAGE_BUILDER_CONFIG"
else
    # 跳过测试的构建
    appimage-builder --recipe "$APPIMAGE_BUILDER_CONFIG" --skip-test
fi

# 检查构建结果
APPIMAGE_FILE="pandoc-ui-${VERSION}-x86_64.AppImage"
if [ ! -f "$APPIMAGE_FILE" ]; then
    print_error "AppImage build failed - output file not found"
    print_info "Expected: $APPIMAGE_FILE"
    ls -la *.AppImage 2>/dev/null || print_info "No AppImage files found"
    exit 1
fi

# 移动到dist目录
mv "$APPIMAGE_FILE" "dist/"
FINAL_APPIMAGE="dist/$APPIMAGE_FILE"

# 使AppImage可执行
chmod +x "$FINAL_APPIMAGE"

# 清理临时文件
rm -f "$DESKTOP_FILE"
rm -f "$ICON_FILE" 2>/dev/null || true

# 测试AppImage
print_info "🧪 Testing AppImage..."
if "$FINAL_APPIMAGE" --help &>/dev/null; then
    print_success "AppImage basic test passed"
else
    print_warning "AppImage basic test failed, but AppImage was created"
fi

# 获取文件信息
FILE_SIZE=$(du -h "$FINAL_APPIMAGE" | cut -f1)

print_success "🎉 AppImage build completed successfully!"
print_info "📁 Output: $FINAL_APPIMAGE"
print_info "📊 File size: $FILE_SIZE"

echo ""
print_info "💡 Usage instructions:"
echo "   1. Make executable: chmod +x $FINAL_APPIMAGE"
echo "   2. Run directly: ./$FINAL_APPIMAGE"
echo "   3. Or double-click in file manager"
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
if command -v file &> /dev/null; then
    file "$FINAL_APPIMAGE"
fi

print_success "✨ All done!"