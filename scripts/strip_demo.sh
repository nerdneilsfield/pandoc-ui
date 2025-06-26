#!/bin/bash
# strip_demo.sh - Strip压缩工具演示脚本
# 展示如何在pandoc-ui项目中安全使用Strip压缩

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_demo() {
    echo -e "${PURPLE}🎯 演示: $1${NC}"
}

# 演示开始
echo -e "${CYAN}🎬 Strip压缩工具演示${NC}"
echo -e "${CYAN}   项目: pandoc-ui${NC}"
echo -e "${CYAN}   时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# 检查项目是否已构建
if [ ! -d "$PROJECT_ROOT/dist" ]; then
    log_info "项目尚未构建，开始构建..."
    
    cd "$PROJECT_ROOT"
    
    # 检查构建脚本
    if [ -f "scripts/build.sh" ]; then
        log_info "使用Unix构建脚本..."
        ./scripts/build.sh
    else
        log_error "未找到构建脚本，请先构建项目"
        exit 1
    fi
    
    cd "$SCRIPT_DIR"
fi

# 查找构建的二进制文件
log_info "查找构建的二进制文件..."

binary_files=()
for platform_dir in "$PROJECT_ROOT/dist"/*; do
    if [ -d "$platform_dir" ]; then
        for file in "$platform_dir"/*; do
            if [ -f "$file" ] && [ -x "$file" ]; then
                binary_files+=("$file")
            fi
        done
    fi
done

if [ ${#binary_files[@]} -eq 0 ]; then
    log_error "未找到可执行的二进制文件"
    log_info "请先运行构建脚本: ./scripts/build.sh"
    exit 1
fi

log_success "找到 ${#binary_files[@]} 个二进制文件:"
for file in "${binary_files[@]}"; do
    size=$(du -h "$file" | cut -f1)
    echo "  📦 $(basename "$file") ($size)"
done

# 选择第一个文件进行演示
demo_binary="${binary_files[0]}"
log_info "选择演示文件: $(basename "$demo_binary")"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示1: 基本信息分析
log_demo "演示1: 二进制文件分析"
echo ""

log_info "文件基本信息:"
ls -lh "$demo_binary"

log_info "文件类型分析:"
file "$demo_binary"

if command -v nm &> /dev/null; then
    log_info "符号表信息:"
    symbol_count=$(nm -D "$demo_binary" 2>/dev/null | wc -l || echo "0")
    echo "  动态符号数量: $symbol_count"
fi

if command -v strings &> /dev/null; then
    log_info "检查PySide6/Qt依赖:"
    if strings "$demo_binary" 2>/dev/null | grep -q "PySide6\|QtCore\|QtWidgets"; then
        log_warning "检测到PySide6/Qt依赖 - 建议使用保守Strip策略"
    else
        log_info "未检测到PySide6/Qt依赖"
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示2: Strip基准测试
log_demo "演示2: Strip基准测试"
echo ""

log_info "运行Strip基准测试..."
echo "这将测试不同Strip策略的效果，请耐心等待..."

benchmark_output="demo_benchmark_$(date +%Y%m%d_%H%M%S).json"

if python3 "$SCRIPT_DIR/strip_benchmark.py" "$demo_binary" -o "$benchmark_output"; then
    log_success "基准测试完成"
    
    # 显示测试结果摘要
    if [ -f "${benchmark_output%%.json}_summary.txt" ]; then
        log_info "测试结果摘要:"
        echo ""
        head -n 20 "${benchmark_output%%.json}_summary.txt"
        echo ""
        log_info "完整报告: ${benchmark_output%%.json}_summary.txt"
    fi
else
    log_warning "基准测试失败或被跳过"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示3: 安全Strip操作
log_demo "演示3: 安全Strip操作（保守策略）"
echo ""

log_info "使用Strip管理器进行安全优化..."

# 创建测试副本
demo_copy="${demo_binary}.demo_copy"
cp "$demo_binary" "$demo_copy"

log_info "创建测试副本: $(basename "$demo_copy")"

# 记录原始大小
original_size=$(stat -c%s "$demo_copy" 2>/dev/null || stat -f%z "$demo_copy" 2>/dev/null)
original_size_mb=$(echo "scale=2; $original_size / 1024 / 1024" | bc -l 2>/dev/null || echo "N/A")

log_info "原始文件大小: $original_size bytes ($original_size_mb MB)"

# 使用Strip管理器优化
if bash "$SCRIPT_DIR/strip_manager.sh" optimize "$demo_copy" --level conservative --notes "演示优化"; then
    # 检查优化结果
    optimized_size=$(stat -c%s "$demo_copy" 2>/dev/null || stat -f%z "$demo_copy" 2>/dev/null)
    optimized_size_mb=$(echo "scale=2; $optimized_size / 1024 / 1024" | bc -l 2>/dev/null || echo "N/A")
    
    size_reduction=$((original_size - optimized_size))
    reduction_percent=$(echo "scale=1; $size_reduction * 100 / $original_size" | bc -l 2>/dev/null || echo "N/A")
    
    log_success "Strip优化完成"
    log_info "优化后大小: $optimized_size bytes ($optimized_size_mb MB)"
    log_info "大小减少: $size_reduction bytes ($reduction_percent%)"
    
    # 验证功能
    log_info "验证优化后功能..."
    if "$demo_copy" --help &>/dev/null; then
        log_success "功能验证通过"
    else
        log_warning "功能验证失败，建议回滚"
    fi
else
    log_error "Strip优化失败"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示4: 操作管理
log_demo "演示4: 操作历史和管理"
echo ""

log_info "显示Strip操作历史..."
bash "$SCRIPT_DIR/strip_manager.sh" list-operations --limit 5

echo ""
log_info "显示备份文件..."
bash "$SCRIPT_DIR/strip_manager.sh" list-backups --limit 5

echo ""
log_info "显示统计信息..."
bash "$SCRIPT_DIR/strip_manager.sh" stats

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示5: 回滚操作
log_demo "演示5: 回滚操作演示"
echo ""

log_info "回滚最近的Strip操作..."
if bash "$SCRIPT_DIR/strip_manager.sh" rollback; then
    log_success "回滚操作完成"
    
    # 验证回滚结果
    rollback_size=$(stat -c%s "$demo_copy" 2>/dev/null || stat -f%z "$demo_copy" 2>/dev/null)
    if [ "$rollback_size" -eq "$original_size" ]; then
        log_success "文件已恢复到原始大小"
    else
        log_warning "文件大小与原始大小不匹配"
    fi
else
    log_warning "回滚操作失败或无可回滚的操作"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 演示6: 生成综合报告
log_demo "演示6: 生成综合报告"
echo ""

report_output="demo_strip_report_$(date +%Y%m%d_%H%M%S)"
log_info "生成Strip管理综合报告..."

if bash "$SCRIPT_DIR/strip_manager.sh" report --output "$report_output"; then
    log_success "报告生成完成"
    log_info "生成的文件:"
    ls -la ${report_output}* 2>/dev/null || log_warning "报告文件未找到"
else
    log_warning "报告生成失败"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 清理和总结
log_demo "清理和总结"
echo ""

log_info "清理演示文件..."
rm -f "$demo_copy"
log_info "演示副本已删除"

echo ""
log_success "🎉 Strip压缩工具演示完成！"
echo ""
echo "📋 演示总结:"
echo "   1. ✅ 二进制文件分析 - 了解文件特征和依赖"
echo "   2. ✅ Strip基准测试 - 评估不同策略的效果"
echo "   3. ✅ 安全Strip操作 - 使用保守策略优化"
echo "   4. ✅ 操作历史管理 - 跟踪所有操作记录"
echo "   5. ✅ 回滚机制演示 - 安全恢复原始文件"
echo "   6. ✅ 综合报告生成 - 完整的操作统计"
echo ""
echo "💡 使用建议:"
echo "   • 对于PySide6/Qt应用，始终使用conservative级别"
echo "   • 生产部署前进行完整的功能测试"
echo "   • 定期清理旧备份文件释放存储空间"
echo "   • 保留Strip前的备份用于紧急回滚"
echo ""
echo "📚 更多信息请参考:"
echo "   • docs/STRIP_COMPRESSION_RESEARCH.md - 详细研究文档"
echo "   • scripts/strip_manager.sh help - 完整使用说明"
echo ""

# 显示生成的文件
echo "📁 演示生成的文件:"
ls -la demo_* strip_* 2>/dev/null | head -10 || log_info "无演示文件残留"

echo ""
log_info "演示结束。您可以使用以下命令开始实际使用:"
echo ""
echo "  # 优化单个文件（推荐用于PySide6应用）"
echo "  ./scripts/strip_manager.sh optimize dist/linux/pandoc-ui --level conservative"
echo ""
echo "  # 运行基准测试"
echo "  ./scripts/strip_manager.sh benchmark dist/linux/pandoc-ui"
echo ""
echo "  # 查看操作历史"
echo "  ./scripts/strip_manager.sh list-operations"
echo ""
echo "  # 生成综合报告"
echo "  ./scripts/strip_manager.sh report"
echo ""

log_success "感谢您体验Strip压缩工具！"