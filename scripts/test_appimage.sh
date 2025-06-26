#!/bin/bash

# AppImage测试和验证脚本
# 用于测试构建的AppImage是否正常工作

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

print_info "🧪 Testing AppImage for pandoc-ui..."

# 检查参数
if [ $# -eq 0 ]; then
    print_error "Usage: $0 <path-to-appimage>"
    print_info "Example: $0 dist/pandoc-ui-0.1.0-x86_64.AppImage"
    exit 1
fi

APPIMAGE_FILE="$1"

# 检查文件是否存在
if [ ! -f "$APPIMAGE_FILE" ]; then
    print_error "AppImage file not found: $APPIMAGE_FILE"
    exit 1
fi

print_info "📁 Testing: $APPIMAGE_FILE"

# 检查文件权限
if [ ! -x "$APPIMAGE_FILE" ]; then
    print_warning "AppImage is not executable, fixing permissions..."
    chmod +x "$APPIMAGE_FILE"
fi

# 测试计数器
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# 测试函数
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit_code="${3:-0}"
    
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
    print_info "🔬 Test $TESTS_TOTAL: $test_name"
    
    if eval "$test_command" &>/dev/null; then
        local exit_code=$?
        if [ $exit_code -eq $expected_exit_code ]; then
            print_success "  Passed"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            print_error "  Failed (exit code: $exit_code, expected: $expected_exit_code)"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    else
        print_error "  Failed to execute"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# 基本测试
print_info "📋 Basic Tests"
echo "----------------------------------------"

# 测试1：文件类型检查
run_test "File type check" "file '$APPIMAGE_FILE' | grep -q 'ELF.*executable'"

# 测试2：AppImage特征检查
run_test "AppImage signature check" "hexdump -C '$APPIMAGE_FILE' | head -n 20 | grep -q 'AI'"

# 测试3：帮助信息
run_test "Help command" "'$APPIMAGE_FILE' --help"

# 测试4：版本信息
run_test "Version check" "'$APPIMAGE_FILE' --version"

# 测试5：AppImage内置命令
run_test "AppImage extract info" "'$APPIMAGE_FILE' --appimage-help"

# 功能测试
print_info "📋 Functionality Tests"
echo "----------------------------------------"

# 测试6：提取AppImage内容
EXTRACT_DIR="/tmp/appimage_test_$$"
run_test "Extract AppImage contents" "'$APPIMAGE_FILE' --appimage-extract-and-run --help"

# 测试7：检查依赖
print_info "🔍 Dependency Analysis"
if command -v ldd &> /dev/null; then
    print_info "📊 Shared library dependencies:"
    ldd "$APPIMAGE_FILE" 2>/dev/null | head -n 10 || print_warning "Could not analyze dependencies"
fi

# 测试8：文件大小检查
FILE_SIZE=$(stat -f%z "$APPIMAGE_FILE" 2>/dev/null || stat -c%s "$APPIMAGE_FILE" 2>/dev/null)
FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))
print_info "📊 File size: ${FILE_SIZE_MB}MB"

if [ $FILE_SIZE_MB -gt 200 ]; then
    print_warning "AppImage is quite large (${FILE_SIZE_MB}MB)"
elif [ $FILE_SIZE_MB -lt 10 ]; then
    print_warning "AppImage seems unusually small (${FILE_SIZE_MB}MB)"
else
    print_success "AppImage size is reasonable (${FILE_SIZE_MB}MB)"
fi

# 测试9：运行时测试
print_info "🏃 Runtime Tests"
echo "----------------------------------------"

# 创建临时目录进行运行时测试
RUNTIME_TEST_DIR="/tmp/appimage_runtime_test_$$"
mkdir -p "$RUNTIME_TEST_DIR"
cd "$RUNTIME_TEST_DIR"

# 测试在不同目录中运行
run_test "Run from different directory" "'$APPIMAGE_FILE' --help"

# 清理
cd - > /dev/null
rm -rf "$RUNTIME_TEST_DIR"

# 兼容性测试
print_info "📋 Compatibility Tests"
echo "----------------------------------------"

# 检查系统信息
print_info "🖥️  System Information:"
echo "  OS: $(uname -s) $(uname -r)"
echo "  Architecture: $(uname -m)"
echo "  Distribution: $(lsb_release -d 2>/dev/null | cut -f2 || echo "Unknown")"

# 检查桌面环境
if [ ! -z "$DESKTOP_SESSION" ]; then
    print_info "🖥️  Desktop Session: $DESKTOP_SESSION"
fi

if [ ! -z "$XDG_CURRENT_DESKTOP" ]; then
    print_info "🖥️  Current Desktop: $XDG_CURRENT_DESKTOP"
fi

# 检查显示服务器
if [ ! -z "$DISPLAY" ]; then
    print_info "🖥️  X11 Display: $DISPLAY"
    run_test "X11 availability" "xdpyinfo > /dev/null"
elif [ ! -z "$WAYLAND_DISPLAY" ]; then
    print_info "🖥️  Wayland Display: $WAYLAND_DISPLAY"
else
    print_warning "No display server detected - GUI tests may fail"
fi

# 安全测试
print_info "📋 Security Tests"
echo "----------------------------------------"

# 检查AppImage是否有执行权限但不是setuid
if [ -u "$APPIMAGE_FILE" ]; then
    print_warning "AppImage has setuid bit set - this is unusual and potentially unsafe"
else
    print_success "AppImage does not have setuid bit set"
fi

# 测试结果总结
echo ""
print_info "📊 Test Results Summary"
echo "========================================"
echo "Total tests: $TESTS_TOTAL"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"

if [ $TESTS_FAILED -eq 0 ]; then
    print_success "🎉 All tests passed! AppImage appears to be working correctly."
    EXIT_CODE=0
else
    print_error "❌ Some tests failed. AppImage may have issues."
    EXIT_CODE=1
fi

# 建议
echo ""
print_info "💡 Recommendations:"
if [ $TESTS_FAILED -gt 0 ]; then
    echo "  - Review failed tests and investigate issues"
    echo "  - Test on different Linux distributions"
    echo "  - Check application logs for detailed error messages"
fi
echo "  - Test GUI functionality manually"
echo "  - Verify file associations work correctly"
echo "  - Test with different user permissions"
echo "  - Validate on target deployment systems"

echo ""
print_info "🔍 Additional Testing:"
echo "  - Manual GUI testing: Double-click the AppImage in file manager"
echo "  - Integration testing: Test document conversion features"
echo "  - Performance testing: Monitor resource usage during operation"
echo "  - Network testing: Test any network-dependent features"

exit $EXIT_CODE