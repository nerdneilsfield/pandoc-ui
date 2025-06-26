#!/bin/bash
# strip_manager.sh - Strip压缩综合管理脚本
# 集成所有Strip工具，提供统一的管理接口

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 默认配置
DEFAULT_STRIP_LEVEL="conservative"
DEFAULT_VERIFY=true
DEFAULT_BACKUP=true
DEFAULT_BENCHMARK=false

# 日志函数
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
Strip压缩综合管理脚本

用法: $0 <命令> [选项] [参数]

命令:
  optimize <binary>     对单个二进制文件进行Strip优化
  benchmark <binary>    对二进制文件进行Strip基准测试
  batch <files...>      批量处理多个二进制文件
  rollback [operation]  回滚Strip操作（默认回滚最新操作）
  list-operations       列出Strip操作历史
  list-backups         列出备份文件
  cleanup              清理旧备份文件
  stats                显示统计信息
  report               生成综合报告
  help                 显示此帮助信息

optimize 选项:
  --level LEVEL        Strip级别: conservative, moderate, aggressive (默认: conservative)
  --no-verify         跳过功能验证
  --no-backup         不创建备份
  --notes "文本"       添加操作备注

benchmark 选项:
  --output FILE       指定输出报告文件
  --verbose           详细输出

batch 选项:
  --level LEVEL       Strip级别
  --continue-on-error 遇到错误继续处理
  --parallel JOBS     并行处理数量

rollback 选项:
  --operation-id ID   指定要回滚的操作ID

cleanup 选项:
  --days DAYS         保留天数 (默认: 30)
  --dry-run          模拟运行

report 选项:
  --output FILE       输出文件路径
  --format FORMAT     报告格式: json, text (默认: both)

示例:
  $0 optimize dist/pandoc-ui --level conservative --notes "生产环境优化"
  $0 benchmark dist/pandoc-ui --output benchmark_results.json
  $0 batch dist/* --level moderate --parallel 4
  $0 rollback --operation-id strip_20240625_143022_001
  $0 cleanup --days 7 --dry-run

环境变量:
  STRIP_MANAGER_WORK_DIR   工作目录 (默认: .strip_manager)
  STRIP_MANAGER_PARALLEL   默认并行数 (默认: 2)
  STRIP_MANAGER_LOG_LEVEL  日志级别: debug, info, warning, error (默认: info)

注意事项:
  - PySide6/Qt应用强烈建议使用conservative级别
  - 生产环境部署前务必进行完整测试
  - 定期清理旧备份文件以释放存储空间
EOF
}

# 检查依赖
check_dependencies() {
    local missing_deps=()
    
    # 检查Python脚本
    local required_scripts=(
        "strip_optimize.sh"
        "integrity_validator.py"
        "strip_benchmark.py"
        "strip_rollback_manager.py"
    )
    
    for script in "${required_scripts[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$script" ]; then
            missing_deps+=("$script")
        fi
    done
    
    # 检查系统命令
    local required_commands=("python3")
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "缺少以下依赖:"
        for dep in "${missing_deps[@]}"; do
            echo "  - $dep"
        done
        return 1
    fi
    
    return 0
}

# 初始化工作环境
init_workspace() {
    local work_dir="${STRIP_MANAGER_WORK_DIR:-.strip_manager}"
    
    if [ ! -d "$work_dir" ]; then
        mkdir -p "$work_dir"
        log_info "创建工作目录: $work_dir"
    fi
    
    # 确保脚本可执行
    chmod +x "$SCRIPT_DIR/strip_optimize.sh" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/integrity_validator.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/strip_benchmark.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/strip_rollback_manager.py" 2>/dev/null || true
}

# 单文件优化
optimize_single() {
    local binary="$1"
    local strip_level="${2:-$DEFAULT_STRIP_LEVEL}"
    local verify="${3:-$DEFAULT_VERIFY}"
    local backup="${4:-$DEFAULT_BACKUP}"
    local notes="$5"
    
    log_header "单文件Strip优化: $(basename "$binary")"
    
    if [ ! -f "$binary" ]; then
        log_error "文件不存在: $binary"
        return 1
    fi
    
    # 准备Strip操作
    log_info "准备Strip操作..."
    local operation_id
    operation_id=$(python3 "$SCRIPT_DIR/strip_rollback_manager.py" prepare "$binary" --method "$strip_level" $([ "$backup" != "true" ] && echo "--no-backup"))
    
    if [ $? -ne 0 ]; then
        log_error "操作准备失败"
        return 1
    fi
    
    # 提取操作ID
    operation_id=$(echo "$operation_id" | grep "操作ID:" | cut -d' ' -f2)
    log_info "操作ID: $operation_id"
    
    # 创建基线
    log_info "创建完整性基线..."
    python3 "$SCRIPT_DIR/integrity_validator.py" create-baseline "$binary" -o "${binary}.baseline.json"
    
    # 执行Strip优化
    log_info "执行Strip优化..."
    local strip_args=()
    strip_args+=("--level" "$strip_level")
    
    if [ "$verify" = "true" ]; then
        strip_args+=("--verify")
    fi
    
    if [ "$backup" = "true" ]; then
        strip_args+=("--backup")
    fi
    
    if bash "$SCRIPT_DIR/strip_optimize.sh" "${strip_args[@]}" "$binary"; then
        strip_success=true
        log_success "Strip优化完成"
    else
        strip_success=false
        log_error "Strip优化失败"
    fi
    
    # 验证完整性
    local verification_passed=false
    if [ "$verify" = "true" ] && [ -f "${binary}.baseline.json" ]; then
        log_info "验证完整性..."
        if python3 "$SCRIPT_DIR/integrity_validator.py" verify "$binary" "${binary}.baseline.json" --strip-level "$strip_level"; then
            verification_passed=true
            log_success "完整性验证通过"
        else
            log_warning "完整性验证失败"
        fi
    fi
    
    # 完成操作记录
    local complete_args=("$operation_id")
    if [ "$strip_success" = "true" ]; then
        complete_args+=("--success")
    fi
    
    if [ "$verification_passed" = "true" ]; then
        complete_args+=("--verified")
    fi
    
    if [ -n "$notes" ]; then
        complete_args+=("--notes" "$notes")
    fi
    
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" complete "${complete_args[@]}"
    
    # 清理基线文件
    rm -f "${binary}.baseline.json"
    
    if [ "$strip_success" = "true" ]; then
        log_success "优化操作完成: $operation_id"
        return 0
    else
        log_error "优化操作失败: $operation_id"
        return 1
    fi
}

# 基准测试
run_benchmark() {
    local binary="$1"
    local output_file="$2"
    local verbose="$3"
    
    log_header "Strip基准测试: $(basename "$binary")"
    
    if [ ! -f "$binary" ]; then
        log_error "文件不存在: $binary"
        return 1
    fi
    
    local benchmark_args=("$binary")
    
    if [ -n "$output_file" ]; then
        benchmark_args+=("-o" "$output_file")
    fi
    
    if [ "$verbose" = "true" ]; then
        benchmark_args+=("-v")
    fi
    
    log_info "开始基准测试..."
    if python3 "$SCRIPT_DIR/strip_benchmark.py" "${benchmark_args[@]}"; then
        log_success "基准测试完成"
        return 0
    else
        log_error "基准测试失败"
        return 1
    fi
}

# 批量处理
batch_process() {
    local files=("$@")
    local strip_level="${BATCH_STRIP_LEVEL:-$DEFAULT_STRIP_LEVEL}"
    local continue_on_error="${BATCH_CONTINUE_ON_ERROR:-false}"
    local parallel_jobs="${BATCH_PARALLEL:-${STRIP_MANAGER_PARALLEL:-2}}"
    
    log_header "批量Strip处理: ${#files[@]} 个文件"
    
    log_info "配置:"
    log_info "  Strip级别: $strip_level"
    log_info "  并行数: $parallel_jobs"
    log_info "  遇错继续: $continue_on_error"
    
    local total_files=${#files[@]}
    local processed=0
    local successful=0
    local failed=0
    
    # 创建临时脚本用于并行处理
    local temp_script=$(mktemp)
    cat > "$temp_script" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$1"
file="$2"
strip_level="$3"
index="$4"
total="$5"

source "$SCRIPT_DIR/strip_manager.sh"

echo "[$index/$total] 处理: $(basename "$file")"

if optimize_single "$file" "$strip_level" "true" "true" "批量处理"; then
    echo "[$index/$total] ✅ 成功: $(basename "$file")"
    exit 0
else
    echo "[$index/$total] ❌ 失败: $(basename "$file")"
    exit 1
fi
EOF
    chmod +x "$temp_script"
    
    # 并行处理文件
    export -f optimize_single log_info log_success log_error log_warning
    
    printf '%s\n' "${files[@]}" | nl | xargs -n2 -P"$parallel_jobs" bash -c '
        index="$1"
        file="$2"
        total="'"$total_files"'"
        
        if bash "'"$temp_script"'" "'"$SCRIPT_DIR"'" "$file" "'"$strip_level"'" "$index" "$total"; then
            echo "SUCCESS:$file"
        else
            echo "FAILED:$file"
            if [ "'"$continue_on_error"'" != "true" ]; then
                exit 1
            fi
        fi
    ' _ | while read result; do
        case "$result" in
            SUCCESS:*)
                ((successful++))
                ;;
            FAILED:*)
                ((failed++))
                ;;
        esac
        ((processed++))
        
        if [ $processed -eq $total_files ]; then
            log_success "批量处理完成:"
            log_info "  总文件数: $total_files"
            log_info "  成功处理: $successful"
            log_info "  失败处理: $failed"
        fi
    done
    
    rm -f "$temp_script"
}

# 回滚操作
rollback_operation() {
    local operation_id="$1"
    
    log_header "回滚Strip操作"
    
    if [ -n "$operation_id" ]; then
        log_info "回滚指定操作: $operation_id"
        python3 "$SCRIPT_DIR/strip_rollback_manager.py" rollback "$operation_id"
    else
        log_info "回滚最新操作"
        python3 "$SCRIPT_DIR/strip_rollback_manager.py" rollback
    fi
}

# 列出操作
list_operations() {
    local limit="${1:-10}"
    local success_only="$2"
    
    log_header "Strip操作历史"
    
    local args=("list-operations" "--limit" "$limit")
    if [ "$success_only" = "true" ]; then
        args+=("--success-only")
    fi
    
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" "${args[@]}"
}

# 列出备份
list_backups() {
    local limit="${1:-10}"
    
    log_header "备份文件列表"
    
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" list-backups --limit "$limit"
}

# 清理备份
cleanup_backups() {
    local days="${1:-30}"
    local dry_run="$2"
    
    log_header "清理旧备份文件"
    
    local args=("cleanup" "--days" "$days")
    if [ "$dry_run" = "true" ]; then
        args+=("--dry-run")
    fi
    
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" "${args[@]}"
}

# 显示统计信息
show_stats() {
    log_header "Strip管理器统计信息"
    
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" stats
}

# 生成综合报告
generate_report() {
    local output_file="$1"
    local format="${2:-both}"
    
    log_header "生成Strip管理综合报告"
    
    # 生成回滚管理器报告
    log_info "生成回滚管理报告..."
    local rollback_report="${output_file:-strip_manager_report}.rollback.json"
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" report -o "$rollback_report"
    
    # 生成综合摘要
    log_info "生成综合摘要..."
    local summary_file="${output_file:-strip_manager_report}_summary.txt"
    
    cat > "$summary_file" << EOF
🎯 Strip压缩管理综合报告
生成时间: $(date '+%Y-%m-%d %H:%M:%S')
========================================

EOF
    
    # 添加统计信息
    echo "📊 总体统计:" >> "$summary_file"
    python3 "$SCRIPT_DIR/strip_rollback_manager.py" stats | sed 's/^/   /' >> "$summary_file"
    
    echo "" >> "$summary_file"
    echo "📋 详细报告文件:" >> "$summary_file"
    echo "   回滚管理报告: $rollback_report" >> "$summary_file"
    echo "   综合摘要: $summary_file" >> "$summary_file"
    
    log_success "报告生成完成:"
    log_info "  综合摘要: $summary_file"
    log_info "  详细报告: $rollback_report"
}

# 主函数
main() {
    # 检查是否被source
    if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
        # 被source，只定义函数
        return 0
    fi
    
    local command="$1"
    shift
    
    # 显示标题
    if [ "$command" != "help" ] && [ -n "$command" ]; then
        echo -e "${CYAN}🛠️  Strip压缩综合管理脚本${NC}"
        echo -e "${CYAN}   时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo -e "${CYAN}   平台: $(uname -s)${NC}"
        echo ""
    fi
    
    # 检查命令
    case "$command" in
        ""|help|--help|-h)
            show_usage
            exit 0
            ;;
        optimize)
            if [ $# -lt 1 ]; then
                log_error "optimize命令需要指定二进制文件"
                show_usage
                exit 1
            fi
            ;;
        benchmark)
            if [ $# -lt 1 ]; then
                log_error "benchmark命令需要指定二进制文件"
                show_usage
                exit 1
            fi
            ;;
        batch)
            if [ $# -lt 1 ]; then
                log_error "batch命令需要指定文件列表"
                show_usage
                exit 1
            fi
            ;;
        rollback|list-operations|list-backups|cleanup|stats|report)
            # 这些命令不需要额外参数检查
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
    
    # 检查依赖和初始化
    if ! check_dependencies; then
        exit 1
    fi
    
    init_workspace
    
    # 解析参数并执行命令
    case "$command" in
        optimize)
            local binary="$1"
            local strip_level="$DEFAULT_STRIP_LEVEL"
            local verify="$DEFAULT_VERIFY"
            local backup="$DEFAULT_BACKUP"
            local notes=""
            
            shift
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --level)
                        strip_level="$2"
                        shift 2
                        ;;
                    --no-verify)
                        verify=false
                        shift
                        ;;
                    --no-backup)
                        backup=false
                        shift
                        ;;
                    --notes)
                        notes="$2"
                        shift 2
                        ;;
                    *)
                        log_error "optimize命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            optimize_single "$binary" "$strip_level" "$verify" "$backup" "$notes"
            ;;
        
        benchmark)
            local binary="$1"
            local output_file=""
            local verbose=false
            
            shift
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --output)
                        output_file="$2"
                        shift 2
                        ;;
                    --verbose)
                        verbose=true
                        shift
                        ;;
                    *)
                        log_error "benchmark命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            run_benchmark "$binary" "$output_file" "$verbose"
            ;;
        
        batch)
            local files=()
            local strip_level="$DEFAULT_STRIP_LEVEL"
            local continue_on_error=false
            local parallel_jobs="${STRIP_MANAGER_PARALLEL:-2}"
            
            # 收集文件参数
            while [[ $# -gt 0 ]] && [[ "$1" != --* ]]; do
                files+=("$1")
                shift
            done
            
            # 解析选项
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --level)
                        strip_level="$2"
                        shift 2
                        ;;
                    --continue-on-error)
                        continue_on_error=true
                        shift
                        ;;
                    --parallel)
                        parallel_jobs="$2"
                        shift 2
                        ;;
                    *)
                        log_error "batch命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            BATCH_STRIP_LEVEL="$strip_level" \
            BATCH_CONTINUE_ON_ERROR="$continue_on_error" \
            BATCH_PARALLEL="$parallel_jobs" \
            batch_process "${files[@]}"
            ;;
        
        rollback)
            local operation_id=""
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --operation-id)
                        operation_id="$2"
                        shift 2
                        ;;
                    *)
                        operation_id="$1"
                        shift
                        ;;
                esac
            done
            
            rollback_operation "$operation_id"
            ;;
        
        list-operations)
            local limit=10
            local success_only=false
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --limit)
                        limit="$2"
                        shift 2
                        ;;
                    --success-only)
                        success_only=true
                        shift
                        ;;
                    *)
                        log_error "list-operations命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            list_operations "$limit" "$success_only"
            ;;
        
        list-backups)
            local limit=10
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --limit)
                        limit="$2"
                        shift 2
                        ;;
                    *)
                        log_error "list-backups命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            list_backups "$limit"
            ;;
        
        cleanup)
            local days=30
            local dry_run=false
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --days)
                        days="$2"
                        shift 2
                        ;;
                    --dry-run)
                        dry_run=true
                        shift
                        ;;
                    *)
                        log_error "cleanup命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            cleanup_backups "$days" "$dry_run"
            ;;
        
        stats)
            show_stats
            ;;
        
        report)
            local output_file=""
            local format="both"
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --output)
                        output_file="$2"
                        shift 2
                        ;;
                    --format)
                        format="$2"
                        shift 2
                        ;;
                    *)
                        log_error "report命令未知选项: $1"
                        exit 1
                        ;;
                esac
            done
            
            generate_report "$output_file" "$format"
            ;;
    esac
}

# 执行主函数
main "$@"