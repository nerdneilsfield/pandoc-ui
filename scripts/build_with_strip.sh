#!/bin/bash
# build_with_strip.sh - 集成Strip优化的增强构建脚本
# 在标准构建基础上添加Strip压缩优化

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 默认配置
ENABLE_STRIP="${ENABLE_STRIP:-true}"
STRIP_LEVEL="${STRIP_LEVEL:-conservative}"
STRIP_VERIFY="${STRIP_VERIFY:-true}"
STRIP_BACKUP="${STRIP_BACKUP:-true}"
STRIP_BENCHMARK="${STRIP_BENCHMARK:-false}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

log_header() {
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}  $1${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

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

# 显示使用说明
show_usage() {
    cat << EOF
集成Strip优化的增强构建脚本

用法: $0 [选项]

选项:
  --strip-level LEVEL     Strip级别: conservative, moderate, aggressive (默认: conservative)
  --no-strip             禁用Strip优化
  --no-verify            跳过Strip后功能验证
  --no-backup            不创建Strip前备份
  --enable-benchmark     启用Strip基准测试
  --verbose              详细输出
  --help                 显示此帮助信息

环境变量:
  ENABLE_STRIP=true/false       启用Strip优化 (默认: true)
  STRIP_LEVEL=conservative      Strip级别 (默认: conservative)
  STRIP_VERIFY=true/false       启用功能验证 (默认: true)
  STRIP_BACKUP=true/false       启用备份 (默认: true)
  STRIP_BENCHMARK=true/false    启用基准测试 (默认: false)

Strip级别说明:
  conservative     仅移除调试符号（推荐用于PySide6/Qt应用）
  moderate        移除调试符号和非必需符号
  aggressive      移除所有可移除符号（高风险）

示例:
  $0                                    # 使用默认设置构建
  $0 --strip-level moderate            # 使用中等Strip级别
  $0 --no-strip                        # 禁用Strip优化
  $0 --enable-benchmark --verbose      # 启用基准测试和详细输出
  
  # 环境变量方式
  STRIP_LEVEL=moderate $0               # 设置Strip级别
  ENABLE_STRIP=false $0                 # 禁用Strip

注意事项:
  - PySide6/Qt应用强烈建议使用conservative级别
  - Strip优化仅在Linux和macOS平台有效
  - 生产环境部署前务必进行完整功能测试
  - Strip操作会自动创建备份和操作记录
EOF
}

# 检测平台
detect_platform() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        CYGWIN*|MINGW*|MSYS*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# 执行标准构建
run_standard_build() {
    local platform=$(detect_platform)
    
    log_header "标准Nuitka构建"
    
    log_info "检测平台: $platform"
    
    # 选择相应的构建脚本
    case "$platform" in
        linux|macos)
            if [ -f "$SCRIPT_DIR/build.sh" ]; then
                log_info "使用Unix构建脚本..."
                bash "$SCRIPT_DIR/build.sh"
            else
                log_error "未找到Unix构建脚本: $SCRIPT_DIR/build.sh"
                return 1
            fi
            ;;
        windows)
            if [ -f "$SCRIPT_DIR/windows_build.ps1" ]; then
                log_info "使用Windows构建脚本..."
                powershell -ExecutionPolicy Bypass -File "$SCRIPT_DIR/windows_build.ps1"
            else
                log_error "未找到Windows构建脚本: $SCRIPT_DIR/windows_build.ps1"
                return 1
            fi
            ;;
        *)
            log_error "不支持的平台: $platform"
            return 1
            ;;
    esac
    
    log_success "标准构建完成"
}

# 查找构建的二进制文件
find_built_binaries() {
    local project_root="$(dirname "$SCRIPT_DIR")"
    local binary_files=()
    
    log_info "查找构建的二进制文件..."
    
    # 在dist目录中查找
    if [ -d "$project_root/dist" ]; then
        while IFS= read -r -d '' file; do
            if [ -x "$file" ] && [ ! -d "$file" ]; then
                binary_files+=("$file")
            fi
        done < <(find "$project_root/dist" -type f -print0 2>/dev/null)
    fi
    
    if [ ${#binary_files[@]} -eq 0 ]; then
        log_warning "未找到可执行的二进制文件"
        return 1
    fi
    
    log_success "找到 ${#binary_files[@]} 个二进制文件:"
    for file in "${binary_files[@]}"; do
        local size=$(du -h "$file" | cut -f1)
        echo "  📦 $(basename "$file") ($size) - $file"
    done
    
    # 返回文件列表（通过全局变量）
    FOUND_BINARIES=("${binary_files[@]}")
    return 0
}

# 执行Strip优化
run_strip_optimization() {
    local binary_files=("$@")
    local platform=$(detect_platform)
    
    log_header "Strip压缩优化"
    
    # 检查平台支持
    if [ "$platform" = "windows" ]; then
        log_warning "Windows平台不支持Strip优化，跳过"
        return 0
    fi
    
    if [ "$ENABLE_STRIP" != "true" ]; then
        log_info "Strip优化已禁用，跳过"
        return 0
    fi
    
    # 检查Strip管理器脚本
    if [ ! -f "$SCRIPT_DIR/strip_manager.sh" ]; then
        log_error "Strip管理器脚本不存在: $SCRIPT_DIR/strip_manager.sh"
        return 1
    fi
    
    log_info "Strip配置:"
    log_info "  级别: $STRIP_LEVEL"
    log_info "  验证: $STRIP_VERIFY"
    log_info "  备份: $STRIP_BACKUP"
    log_info "  基准测试: $STRIP_BENCHMARK"
    
    local total_files=${#binary_files[@]}
    local successful_count=0
    local failed_count=0
    local total_size_before=0
    local total_size_after=0
    
    for i in "${!binary_files[@]}"; do
        local file="${binary_files[$i]}"
        local file_index=$((i + 1))
        
        echo ""
        log_info "[$file_index/$total_files] 处理文件: $(basename "$file")"
        
        # 记录原始大小
        local size_before=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        total_size_before=$((total_size_before + size_before))
        
        # 运行基准测试（如果启用）
        if [ "$STRIP_BENCHMARK" = "true" ]; then
            log_info "运行基准测试..."
            local benchmark_output="strip_benchmark_$(basename "$file")_$(date +%Y%m%d_%H%M%S).json"
            
            if bash "$SCRIPT_DIR/strip_manager.sh" benchmark "$file" --output "$benchmark_output"; then
                log_success "基准测试完成: $benchmark_output"
            else
                log_warning "基准测试失败"
            fi
        fi
        
        # 执行Strip优化
        local strip_args=("optimize" "$file" "--level" "$STRIP_LEVEL")
        
        if [ "$STRIP_VERIFY" != "true" ]; then
            strip_args+=("--no-verify")
        fi
        
        if [ "$STRIP_BACKUP" != "true" ]; then
            strip_args+=("--no-backup")
        fi
        
        strip_args+=("--notes" "自动构建Strip优化")
        
        if bash "$SCRIPT_DIR/strip_manager.sh" "${strip_args[@]}"; then
            ((successful_count++))
            
            # 计算大小变化
            local size_after=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
            total_size_after=$((total_size_after + size_after))
            
            local size_reduction=$((size_before - size_after))
            local reduction_percent=$(( size_reduction * 100 / size_before ))
            
            log_success "Strip优化成功"
            log_info "  大小变化: $size_before → $size_after bytes"
            log_info "  减少: $size_reduction bytes ($reduction_percent%)"
        else
            ((failed_count++))
            log_error "Strip优化失败"
            
            # 如果优化失败，使用原始大小
            total_size_after=$((total_size_after + size_before))
        fi
    done
    
    # 显示总体统计
    echo ""
    log_header "Strip优化总结"
    
    log_info "处理统计:"
    log_info "  总文件数: $total_files"
    log_info "  成功处理: $successful_count"
    log_info "  失败处理: $failed_count"
    
    if [ $successful_count -gt 0 ]; then
        local total_reduction=$((total_size_before - total_size_after))
        local total_reduction_percent=$(( total_reduction * 100 / total_size_before ))
        local total_reduction_mb=$(echo "scale=2; $total_reduction / 1024 / 1024" | bc -l 2>/dev/null || echo "N/A")
        
        log_info "大小统计:"
        log_info "  原始总大小: $total_size_before bytes"
        log_info "  优化后总大小: $total_size_after bytes"
        log_info "  总减少量: $total_reduction bytes ($total_reduction_mb MB)"
        log_info "  总减少率: $total_reduction_percent%"
    fi
    
    if [ $failed_count -eq 0 ]; then
        log_success "所有文件Strip优化完成"
        return 0
    else
        log_warning "部分文件Strip优化失败"
        return 1
    fi
}

# 生成构建报告
generate_build_report() {
    local binary_files=("$@")
    
    log_header "生成构建报告"
    
    local report_file="build_with_strip_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log_info "生成构建报告: $report_file"
    
    cat > "$report_file" << EOF
🏗️  pandoc-ui Strip优化构建报告
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
平台: $(detect_platform)
========================================

📦 构建配置:
   Strip优化: $ENABLE_STRIP
   Strip级别: $STRIP_LEVEL
   功能验证: $STRIP_VERIFY
   自动备份: $STRIP_BACKUP
   基准测试: $STRIP_BENCHMARK

📁 构建产物:
EOF
    
    for file in "${binary_files[@]}"; do
        local size=$(du -h "$file" | cut -f1)
        local abs_path=$(realpath "$file")
        echo "   📦 $(basename "$file") ($size)" >> "$report_file"
        echo "      路径: $abs_path" >> "$report_file"
    done
    
    echo "" >> "$report_file"
    
    # 添加Strip操作历史
    if [ "$ENABLE_STRIP" = "true" ] && [ -f "$SCRIPT_DIR/strip_manager.sh" ]; then
        echo "🔧 Strip操作历史:" >> "$report_file"
        bash "$SCRIPT_DIR/strip_manager.sh" list-operations --limit 5 2>/dev/null >> "$report_file" || echo "   无Strip操作记录" >> "$report_file"
        
        echo "" >> "$report_file"
        echo "📊 Strip统计信息:" >> "$report_file"
        bash "$SCRIPT_DIR/strip_manager.sh" stats 2>/dev/null >> "$report_file" || echo "   无统计信息" >> "$report_file"
    fi
    
    echo "" >> "$report_file"
    echo "💡 部署建议:" >> "$report_file"
    echo "   • 生产部署前进行完整功能测试" >> "$report_file"
    echo "   • 保留Strip前备份用于紧急回滚" >> "$report_file"
    echo "   • 监控应用性能确保Strip无负面影响" >> "$report_file"
    
    if grep -q "PySide6\|Qt" "$report_file" 2>/dev/null; then
        echo "   • PySide6/Qt应用已使用保守Strip策略" >> "$report_file"
    fi
    
    log_success "构建报告生成完成: $report_file"
}

# 主函数
main() {
    local VERBOSE=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --strip-level)
                STRIP_LEVEL="$2"
                shift 2
                ;;
            --no-strip)
                ENABLE_STRIP=false
                shift
                ;;
            --no-verify)
                STRIP_VERIFY=false
                shift
                ;;
            --no-backup)
                STRIP_BACKUP=false
                shift
                ;;
            --enable-benchmark)
                STRIP_BENCHMARK=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知选项: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # 验证Strip级别
    case "$STRIP_LEVEL" in
        conservative|moderate|aggressive)
            ;;
        *)
            log_error "无效的Strip级别: $STRIP_LEVEL"
            log_error "有效选项: conservative, moderate, aggressive"
            exit 1
            ;;
    esac
    
    # 显示标题
    echo -e "${CYAN}🚀 pandoc-ui Strip优化构建${NC}"
    echo -e "${CYAN}   时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${CYAN}   平台: $(detect_platform)${NC}"
    echo ""
    
    # 显示配置
    if [ "$VERBOSE" = "true" ]; then
        log_info "构建配置:"
        log_info "  Strip优化: $ENABLE_STRIP"
        log_info "  Strip级别: $STRIP_LEVEL"
        log_info "  功能验证: $STRIP_VERIFY"
        log_info "  自动备份: $STRIP_BACKUP"
        log_info "  基准测试: $STRIP_BENCHMARK"
        echo ""
    fi
    
    # 步骤1: 执行标准构建
    if ! run_standard_build; then
        log_error "标准构建失败"
        exit 1
    fi
    
    # 步骤2: 查找构建的二进制文件
    if ! find_built_binaries; then
        log_error "未找到构建的二进制文件"
        exit 1
    fi
    
    # 步骤3: 执行Strip优化
    strip_success=true
    if ! run_strip_optimization "${FOUND_BINARIES[@]}"; then
        strip_success=false
        log_warning "Strip优化部分失败，但构建继续"
    fi
    
    # 步骤4: 生成构建报告
    generate_build_report "${FOUND_BINARIES[@]}"
    
    # 显示最终结果
    echo ""
    log_header "构建完成"
    
    log_success "🎉 pandoc-ui Strip优化构建完成！"
    
    if [ "$strip_success" = "true" ]; then
        log_success "✅ Strip优化: 成功"
    else
        log_warning "⚠️  Strip优化: 部分失败"
    fi
    
    echo ""
    log_info "📁 构建产物:"
    for file in "${FOUND_BINARIES[@]}"; do
        local size=$(du -h "$file" | cut -f1)
        echo "  📦 $(basename "$file") ($size) - $file"
    done
    
    echo ""
    log_info "🔧 管理命令:"
    echo "  # 查看Strip操作历史"
    echo "  ./scripts/strip_manager.sh list-operations"
    echo ""
    echo "  # 回滚Strip操作"
    echo "  ./scripts/strip_manager.sh rollback"
    echo ""
    echo "  # 生成详细报告"
    echo "  ./scripts/strip_manager.sh report"
    
    echo ""
    log_info "📚 更多信息: docs/STRIP_COMPRESSION_RESEARCH.md"
    
    # 根据Strip结果设置退出码
    if [ "$strip_success" = "true" ]; then
        exit 0
    else
        exit 2  # 构建成功但Strip部分失败
    fi
}

# 执行主函数
main "$@"