# AppImage构建脚本使用指南

本目录包含了为pandoc-ui创建Linux AppImage的多种构建方案和工具。

## 🚀 快速开始

### 方案1：简单构建（推荐新手）
使用Nuitka的内置AppImage支持，最简单的方法：

```bash
./scripts/build_simple_appimage.sh
```

### 方案2：高级构建（推荐经验用户）
使用linuxdeploy进行更精细的依赖管理：

```bash
./scripts/build_appimage.sh
```

### 方案3：专业构建（推荐复杂项目）
使用appimage-builder进行最大自动化：

```bash
./scripts/build_appimage_builder.sh
```

## 📁 文件说明

### 主要构建脚本
- **`build_simple_appimage.sh`** - 使用Nuitka --onefile的简单方案
- **`build_appimage.sh`** - 使用linuxdeploy的完整方案  
- **`build_appimage_builder.sh`** - 使用appimage-builder的自动化方案

### 配置文件
- **`AppImageBuilder.yml`** - appimage-builder的配置文件
- **`templates/AppRun.template`** - AppRun脚本模板
- **`templates/desktop.template`** - .desktop文件模板

### 测试和验证
- **`test_appimage.sh`** - AppImage测试和验证脚本

## 🔧 系统要求

### 基本要求
- Linux操作系统（Ubuntu 18.04+ 推荐）
- Python 3.12+
- uv包管理器
- PySide6已安装

### 额外工具（按需安装）
```bash
# linuxdeploy方案需要
wget  # 用于下载linuxdeploy工具

# appimage-builder方案需要
pip3 install --user appimage-builder

# 可选工具
sudo apt install imagemagick  # 用于图标处理
sudo apt install file         # 用于文件类型检查
```

## 📊 方案比较

| 特性 | 简单构建 | 高级构建 | 专业构建 |
|------|----------|----------|----------|
| **复杂度** | 低 | 中 | 高 |
| **构建时间** | 快 | 中等 | 慢 |
| **文件大小** | 中等 | 小 | 最小 |
| **兼容性** | 好 | 很好 | 最好 |
| **依赖管理** | 自动 | 精细 | 最优 |
| **调试能力** | 低 | 中 | 高 |
| **推荐场景** | 快速测试 | 生产发布 | 专业分发 |

## 🛠️ 使用方法

### 准备工作
```bash
# 确保在项目根目录
cd /path/to/pandoc-ui

# 安装依赖
uv sync

# 生成必要的资源文件
./scripts/generate_translations.sh
./scripts/generate_resources.sh
```

### 选择构建方案

#### 1. 简单构建（推荐首次使用）
```bash
# 直接运行，无需额外配置
./scripts/build_simple_appimage.sh

# 输出位置：dist/pandoc-ui-simple-VERSION-x86_64.AppImage
```

#### 2. 高级构建（推荐生产环境）
```bash
# 自动下载所需工具并构建
./scripts/build_appimage.sh

# 输出位置：dist/pandoc-ui-VERSION-x86_64.AppImage
```

#### 3. 专业构建（最大自定化）
```bash
# 需要先安装appimage-builder
pip3 install --user appimage-builder

# 运行构建
./scripts/build_appimage_builder.sh

# 输出位置：dist/pandoc-ui-VERSION-x86_64.AppImage
```

### 测试AppImage
```bash
# 测试构建的AppImage
./scripts/test_appimage.sh dist/pandoc-ui-*-x86_64.AppImage

# 手动测试
./dist/pandoc-ui-*-x86_64.AppImage --help
```

## 🔍 故障排除

### 常见问题

#### 1. 构建失败：缺少依赖
```bash
# 安装系统依赖
sudo apt update
sudo apt install python3-dev build-essential

# 安装Python依赖
uv sync
```

#### 2. Nuitka构建问题
```bash
# 清理缓存
rm -rf ~/.nuitka
rm -rf build/

# 重新构建
./scripts/build_simple_appimage.sh
```

#### 3. linuxdeploy下载失败
```bash
# 手动下载
mkdir -p build/appimage
cd build/appimage
wget https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
chmod +x linuxdeploy-x86_64.AppImage
```

#### 4. AppImage运行失败
```bash
# 检查权限
chmod +x your-app.AppImage

# 查看详细错误
./your-app.AppImage --verbose

# 提取并检查内容
./your-app.AppImage --appimage-extract
ls squashfs-root/
```

### 调试技巧

#### 查看AppImage内容
```bash
# 提取AppImage内容
./your-app.AppImage --appimage-extract

# 检查目录结构
find squashfs-root/ -type f | head -20

# 检查主要组件
ls -la squashfs-root/AppRun
ls -la squashfs-root/*.desktop
ls -la squashfs-root/usr/bin/
```

#### 调试运行时问题
```bash
# 启用Qt调试
export QT_DEBUG_PLUGINS=1
export QT_LOGGING_RULES="*.debug=true"
./your-app.AppImage

# 检查依赖
ldd squashfs-root/usr/bin/your-app
```

## 📈 性能优化

### 减小文件大小
1. **排除不必要的文件**：编辑AppImageBuilder.yml中的exclude部分
2. **优化Python打包**：使用--static-libpython=no
3. **移除调试信息**：添加strip命令

### 提高兼容性
1. **使用旧版基础系统**：在Ubuntu 18.04上构建
2. **静态链接关键库**：避免系统差异
3. **测试多个发行版**：使用Docker测试

### 加速构建
1. **缓存下载文件**：保留build目录中的工具
2. **并行构建**：使用--parallel选项
3. **增量构建**：只重新构建变更部分

## 🚀 CI/CD集成

### GitHub Actions示例
```yaml
name: Build AppImage
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-20.04
    steps:
    - uses: actions/checkout@v3
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - name: Install uv
      run: pip install uv
    - name: Build AppImage
      run: ./scripts/build_appimage.sh
    - name: Test AppImage
      run: ./scripts/test_appimage.sh dist/*.AppImage
    - name: Upload AppImage
      uses: actions/upload-artifact@v3
      with:
        name: pandoc-ui-appimage
        path: dist/*.AppImage
```

## 📋 最佳实践

### 1. 构建环境
- 使用Docker确保构建环境一致性
- 在较旧的Linux发行版上构建以提高兼容性
- 定期更新构建工具

### 2. 测试策略
- 在多个Linux发行版上测试
- 测试不同的桌面环境
- 验证文件关联和MIME类型

### 3. 分发建议
- 提供校验和文件
- 使用GitHub Releases或类似平台
- 提供安装和使用说明

### 4. 维护更新
- 实现自动更新机制
- 监控用户反馈
- 定期重新打包以包含安全更新

## 🆘 获取帮助

如果遇到问题，请按以下顺序寻求帮助：

1. **查看日志**：构建脚本会提供详细的错误信息
2. **运行测试**：使用test_appimage.sh诊断问题
3. **检查文档**：参考docs/APPIMAGE_GUIDE.md
4. **搜索已知问题**：查看项目issue或相关工具的文档
5. **提交问题**：如果是项目特定问题，请创建issue

## 📚 参考资源

- [AppImage官方文档](https://docs.appimage.org/)
- [Nuitka用户手册](https://nuitka.net/user-documentation/user-manual.html)
- [linuxdeploy用户指南](https://docs.appimage.org/packaging-guide/from-source/linuxdeploy-user-guide.html)
- [appimage-builder文档](https://appimage-builder.readthedocs.io/)
- [Desktop Entry规范](https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html)