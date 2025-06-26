# Strip压缩工具套件

本目录包含了一套完整的Strip压缩工具，用于优化pandoc-ui项目的二进制文件大小，同时确保应用的稳定性和功能完整性。

## 🎯 概述

Strip压缩通过移除二进制文件中的调试符号和非必需符号来减小文件大小。对于PySide6/Qt应用，我们提供了安全的保守策略，确保压缩后应用仍能正常运行。

## 📁 工具文件

### 核心工具
- **`strip_manager.sh`** - 统一管理脚本，提供所有Strip功能的入口
- **`strip_optimize.sh`** - 跨平台Strip优化脚本
- **`integrity_validator.py`** - 完整性验证工具
- **`strip_benchmark.py`** - 基准测试工具
- **`strip_rollback_manager.py`** - 回滚管理器

### 集成和演示
- **`build_with_strip.sh`** - 集成Strip的增强构建脚本
- **`strip_demo.sh`** - 演示脚本，展示所有功能
- **`README_STRIP.md`** - 本文档

### 研究文档
- **`../docs/STRIP_COMPRESSION_RESEARCH.md`** - 详细的Strip压缩研究文档

## 🚀 快速开始

### 1. 基本使用

```bash
# 对单个二进制文件进行保守Strip优化（推荐）
./scripts/strip_manager.sh optimize dist/linux/pandoc-ui --level conservative

# 运行基准测试，了解不同策略的效果
./scripts/strip_manager.sh benchmark dist/linux/pandoc-ui

# 查看操作历史
./scripts/strip_manager.sh list-operations
```

### 2. 集成构建

```bash
# 使用增强构建脚本（自动包含Strip优化）
./scripts/build_with_strip.sh

# 自定义Strip级别
./scripts/build_with_strip.sh --strip-level moderate

# 禁用Strip优化
./scripts/build_with_strip.sh --no-strip
```

### 3. 演示体验

```bash
# 运行完整的演示，了解所有功能
./scripts/strip_demo.sh
```

## 📊 Strip级别说明

| 级别 | 描述 | 安全性 | 压缩效果 | 推荐场景 |
|------|------|--------|----------|----------|
| **conservative** | 仅移除调试符号 | 🟢 高 | 🔵 低-中 | PySide6/Qt应用生产环境 |
| **moderate** | 移除调试符号和非必需符号 | 🟡 中 | 🔵 中 | 非GUI应用生产环境 |
| **aggressive** | 移除所有可移除符号 | 🔴 低 | 🔵 高 | 测试环境或特殊需求 |

## 🛠️ 主要功能

### Strip优化管理
```bash
# 基本优化
./scripts/strip_manager.sh optimize <binary> --level conservative

# 批量处理
./scripts/strip_manager.sh batch dist/* --level conservative --parallel 4

# 带基准测试的优化
./scripts/strip_manager.sh optimize <binary> --level conservative
./scripts/strip_manager.sh benchmark <binary>
```

### 操作历史管理
```bash
# 列出操作历史
./scripts/strip_manager.sh list-operations --limit 10

# 列出备份文件
./scripts/strip_manager.sh list-backups

# 回滚最新操作
./scripts/strip_manager.sh rollback

# 回滚指定操作
./scripts/strip_manager.sh rollback --operation-id strip_20240625_143022_001
```

### 维护和清理
```bash
# 显示统计信息
./scripts/strip_manager.sh stats

# 清理旧备份（模拟运行）
./scripts/strip_manager.sh cleanup --days 30 --dry-run

# 实际清理
./scripts/strip_manager.sh cleanup --days 30

# 生成综合报告
./scripts/strip_manager.sh report
```

## 🔧 高级用法

### 自定义Strip策略

```bash
# 仅对特定类型文件进行Strip
find dist/ -name "pandoc-ui*" -executable | xargs -I {} \
  ./scripts/strip_manager.sh optimize {} --level conservative

# 并行批量处理
./scripts/strip_manager.sh batch dist/linux/* dist/macos/* \
  --level conservative --parallel 8 --continue-on-error
```

### 完整性验证

```bash
# 手动创建基线
python3 scripts/integrity_validator.py create-baseline dist/linux/pandoc-ui

# 验证完整性
python3 scripts/integrity_validator.py verify dist/linux/pandoc-ui \
  dist/linux/pandoc-ui.baseline.json --strip-level conservative

# 批量验证
python3 scripts/integrity_validator.py batch-verify dist/linux/* \
  --baseline-dir .strip_manager/baselines
```

### 性能基准测试

```bash
# 详细基准测试
python3 scripts/strip_benchmark.py dist/linux/pandoc-ui \
  -o benchmark_results.json -v

# 查看结果摘要
cat benchmark_results_summary.txt
```

## ⚠️  注意事项

### PySide6/Qt应用特别说明
- **强烈推荐**使用`conservative`级别
- Qt插件系统依赖符号信息，激进Strip可能导致插件加载失败
- 信号/槽机制可能受到Strip影响

### 平台兼容性
- **Linux**: 完全支持所有Strip功能
- **macOS**: 支持基本Strip功能，参数略有不同
- **Windows**: 不支持Strip，工具会自动跳过

### 生产环境建议
1. **始终创建备份** - 使用`--backup`选项（默认启用）
2. **功能验证** - 使用`--verify`选项验证Strip后功能
3. **渐进部署** - 先在测试环境验证，再部署到生产
4. **监控性能** - 部署后监控应用性能和错误率

## 📈 效果期望

基于我们的测试，不同Strip策略的预期效果：

| 应用类型 | conservative | moderate | aggressive |
|----------|--------------|----------|------------|
| PySide6应用 | 5-15% | 10-25% | 15-40% |
| CLI工具 | 10-20% | 15-30% | 20-50% |
| 纯C应用 | 15-25% | 20-35% | 25-60% |

**注意**: 实际效果取决于应用的符号表大小和编译选项。

## 🔄 回滚和恢复

Strip工具提供完整的回滚机制：

```bash
# 查看可回滚的操作
./scripts/strip_manager.sh list-operations

# 快速回滚最新操作
./scripts/strip_manager.sh rollback

# 从备份恢复特定文件
python3 scripts/strip_rollback_manager.py restore backup_20240625_143022_001

# 验证备份完整性
python3 scripts/strip_rollback_manager.py verify backup_20240625_143022_001
```

## 🚨 故障排除

### 常见问题

1. **Strip后应用无法启动**
   ```bash
   # 立即回滚
   ./scripts/strip_manager.sh rollback
   
   # 使用更保守的策略
   ./scripts/strip_manager.sh optimize <binary> --level conservative
   ```

2. **功能验证失败**
   ```bash
   # 检查应用依赖
   ldd <binary>  # Linux
   otool -L <binary>  # macOS
   
   # 运行详细测试
   <binary> --help
   <binary> --version
   ```

3. **基准测试失败**
   ```bash
   # 检查平台支持
   uname -s
   
   # 验证strip命令可用
   which strip
   strip --version
   ```

### 日志和调试

所有操作都会记录详细日志：

```bash
# 查看操作历史
./scripts/strip_manager.sh list-operations --limit 20

# 查看详细统计
./scripts/strip_manager.sh stats

# 生成调试报告
./scripts/strip_manager.sh report --output debug_report.json
```

## 📚 进一步阅读

- **详细研究文档**: `docs/STRIP_COMPRESSION_RESEARCH.md`
- **项目构建文档**: `CLAUDE.md`
- **Git提交规范**: 遵循项目的Conventional Commits规范

## 🤝 贡献和反馈

如果您发现任何问题或有改进建议，请：

1. 查看现有的操作记录和日志
2. 运行`strip_demo.sh`重现问题
3. 生成详细报告用于问题诊断
4. 按照项目的提交规范提交问题报告

## 📄 许可

这些工具脚本遵循项目的MIT许可证。