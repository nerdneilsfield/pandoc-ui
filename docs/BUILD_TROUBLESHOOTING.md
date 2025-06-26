# Build Troubleshooting Guide

## Issue: "Build failed! Output file not found" with Nuitka Memory Consumption

### Problem Description
Nuitka compilation fails with high memory usage and the output files are not found at expected locations. Memory usage information shows:
```
F:\WinFile\Source\langs\python\pandoc-ui\.venv\Lib\site-packages\nuitka\nodes\FunctionNodes.py:505: size=450 KiB
...
❌ Build failed! Output file not found.
```

### Root Causes

#### 1. Nuitka Memory Exhaustion
- **Problem**: Nuitka consumes excessive memory during compilation
- **Symptoms**: Memory usage tracking shown, but compilation fails
- **Solution**: Added `--low-memory` and `--jobs=1` flags

#### 2. Incorrect Output Path Detection
- **Problem**: Build scripts look for wrong file/directory paths
- **Symptoms**: Build succeeds but script reports "Output file not found"
- **Solution**: Fixed path detection logic for standalone vs onefile modes

#### 3. Missing Memory Management Options
- **Problem**: No memory constraints on Nuitka compilation
- **Symptoms**: System runs out of memory during large builds
- **Solution**: Added memory management flags

### Solutions Implemented

#### 1. Memory Management Flags
Added to all build scripts:
```bash
# Linux/macOS (build.sh)
NUITKA_ARGS+=(--low-memory)
NUITKA_ARGS+=(--jobs=1)

# Windows (windows_build.ps1)
$NuitkaArgs += "--low-memory"
$NuitkaArgs += "--jobs=1"
```

#### 2. Correct Path Detection
Fixed output detection logic:
```bash
# Check for standalone directory vs single file
if [ "$BUILD_MODE" = "standalone" ]; then
    if [ -d "$DIST_DIR/$OUTPUT_FILE" ]; then
        BUILD_SUCCESS=true
        OUTPUT_PATH="$DIST_DIR/$OUTPUT_FILE"
        EXECUTABLE_PATH="$OUTPUT_PATH/$OUTPUT_FILE"
    fi
else
    if [ -f "$DIST_DIR/$OUTPUT_FILE" ]; then
        BUILD_SUCCESS=true
        OUTPUT_PATH="$DIST_DIR/$OUTPUT_FILE"
        EXECUTABLE_PATH="$OUTPUT_PATH"
    fi
fi
```

#### 3. Debug Script
Created `scripts/debug_build.sh` for diagnosis:
- Minimal Nuitka build with verbose output
- System resource checking
- Detailed output path analysis
- Memory usage monitoring

### Debugging Steps

#### 1. Run Debug Build
```bash
./scripts/debug_build.sh
```

#### 2. Check System Resources
Ensure sufficient memory and disk space:
```bash
# Check memory
free -h

# Check disk space
df -h .

# Check for resource limits
ulimit -a
```

#### 3. Monitor Memory Usage
During build, monitor with:
```bash
# Monitor memory usage
watch -n 1 'ps aux | grep nuitka | head -5'

# Check system memory
watch -n 1 'free -h'
```

#### 4. Try Minimal Build
Test with minimal options:
```bash
uv run python -m nuitka \
    --standalone \
    --low-memory \
    --jobs=1 \
    --show-progress \
    pandoc_ui/main.py
```

### Alternative Approaches

#### 1. Use Docker with Memory Limits
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y build-essential
# Set memory limits
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
RUN uv run python -m nuitka --standalone --low-memory pandoc_ui/main.py
```

#### 2. Cross-Compilation
Build on a more powerful machine:
```bash
# On a machine with more memory
git clone <repo>
cd pandoc-ui
uv sync
./scripts/build.sh --standalone
```

#### 3. Incremental Building
Use Nuitka caching:
```bash
# Enable caching for faster rebuilds
export NUITKA_CACHE_DIR=~/.nuitka-cache
uv run python -m nuitka --standalone --low-memory --enable-plugin=pyside6 pandoc_ui/main.py
```

### System Requirements

#### Minimum Requirements
- **RAM**: 4GB available during build
- **Disk**: 2GB free space
- **CPU**: Single core (with --jobs=1)

#### Recommended Requirements  
- **RAM**: 8GB+ for comfortable building
- **Disk**: 5GB+ free space for build artifacts
- **CPU**: Multi-core for faster builds (without --jobs=1)

### Common Issues and Solutions

#### Issue: "ImportError during compilation"
**Solution**: Ensure all dependencies are installed
```bash
uv sync
uv run python -c "import PySide6; print('PySide6 OK')"
```

#### Issue: "Permission denied"
**Solution**: Check file permissions
```bash
chmod +x scripts/*.sh
sudo chown -R $USER:$USER .
```

#### Issue: "Out of disk space"
**Solution**: Clean build artifacts
```bash
rm -rf build/ dist/ .nuitka/
```

#### Issue: "Killed" during compilation
**Solution**: Increase swap space or use smaller builds
```bash
# Check memory limits
ulimit -v
# Increase swap (Linux)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Recovery Steps

#### 1. Clean Build Environment
```bash
rm -rf build/ dist/ .nuitka/
rm -rf __pycache__/ */__pycache__/
```

#### 2. Verify Dependencies
```bash
uv sync --reinstall
uv run python -m pip list | grep -E "(nuitka|pyside6)"
```

#### 3. Test Minimal Application
```bash
uv run python pandoc_ui/main.py --help
```

#### 4. Gradual Build Complexity
Start with minimal flags, then add features:
```bash
# Step 1: Basic build
uv run python -m nuitka --standalone pandoc_ui/main.py

# Step 2: Add PySide6
uv run python -m nuitka --standalone --enable-plugin=pyside6 pandoc_ui/main.py

# Step 3: Add resources
uv run python -m nuitka --standalone --enable-plugin=pyside6 --include-data-dir=pandoc_ui/resources=pandoc_ui/resources pandoc_ui/main.py
```

### Getting Help

If issues persist:
1. Run `scripts/debug_build.sh` and capture output
2. Check system resources and limits
3. Try on a different machine with more memory
4. Consider using Docker for consistent build environment
5. Report issue with debug output and system specifications