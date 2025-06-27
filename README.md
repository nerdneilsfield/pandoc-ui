# pandoc-ui

A PySide6-based graphical interface for Pandoc that makes document format conversion accessible to non-technical users. Supports single file and batch folder conversions across Windows, macOS, and Linux.

## Features

- 🖥️ **Cross-platform GUI** - Works on Windows, macOS, and Linux
- 📄 **Single file conversion** - Convert individual documents with ease
- 📁 **Batch processing** - Convert entire folders of documents
- 🎯 **45+ input formats** - Support for all major document formats
- 📊 **64+ output formats** - Convert to any format Pandoc supports
- ⚙️ **Custom profiles** - Save and reuse conversion settings
- 🚀 **Standalone executables** - No Python installation required

## Quick Start

### Download Pre-built Executables
- Download from [Releases](../../releases) page
- No installation required - just run the executable

### Build from Source
```bash
# Clone repository
git clone https://github.com/nerdneilsfield/pandoc-ui.git
cd pandoc-ui

# Install dependencies
uv sync

# Run from source
uv run python -m pandoc_ui.main

# Or build standalone executable
./scripts/build.sh              # Linux/Windows
./scripts/macos_build_dmg.sh    # macOS (creates DMG)
```

## Build Instructions

See [BUILD.md](BUILD.md) for detailed build instructions and platform-specific requirements.

### macOS DMG Distribution
```bash
# Build unsigned universal binary DMG for open source distribution
./scripts/macos_build_dmg.sh --universal

# Users install by dragging app to Applications folder
# No Apple Developer account required!
```

## Development

### Setup Development Environment
```bash
# Create virtual environment and install dependencies
uv sync

# Run development tools
./scripts/lint.sh     # Code quality checks
./scripts/format.sh   # Auto-format code
./scripts/test_gui.sh # GUI tests
```

### Project Structure
- `pandoc_ui/` - Main application code
- `scripts/` - Build and development tools
- `tests/` - Test suite
- `docs/` - Documentation

## Requirements

### Runtime
- **Pandoc** - The document converter engine
- **Python 3.12+** (if running from source)
- **PySide6** (if running from source)

### For Building
- **uv** package manager
- **Nuitka** (automatically installed)
- Platform-specific build tools (see BUILD.md)

## License

MIT License - see [LICENSE](LICENSE) for details.
