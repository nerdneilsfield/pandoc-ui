# CLAUDE.md

IMPORT: THINKING USING sequential-thiking mcp

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**pandoc-ui**: A PySide6-based graphical interface for Pandoc that makes document format conversion accessible to non-technical users. Supports single file and batch folder conversions across Windows, macOS, and Linux.

## Development Commands

### Environment Setup with uv

```bash
# Create virtual environment
uv venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies in editable mode
uv pip install --editable .

# Sync all dependencies (including dev)
uv sync

# Sync only production dependencies
uv sync --no-dev
```

### Installing Dependencies with uv

```bash
# Add production dependency
uv add requests

# Add multiple production dependencies
uv add pyside6 click pathlib

# Add development dependency
uv add --dev pytest

# Add multiple dev dependencies
uv add --dev pytest pytest-cov flake8 black mypy

# Remove a dependency
uv remove package-name

# Show installed packages
uv pip list
```

### Running Commands with uv

```bash
# Run the main application
uv run python -m pandoc_ui.main

# Run in WSL with explicit platform (if needed)
QT_QPA_PLATFORM=xcb uv run python -m pandoc_ui.main

# Run any Python script
uv run python scripts/demo_cli.py

# Run development tools
uv run black pandoc_ui tests
uv run flake8 pandoc_ui
uv run mypy pandoc_ui
```

### Testing with uv

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_runner.py

# Run with coverage
uv run pytest --cov=pandoc_ui

# Run with verbose output
uv run pytest -v

# Run tests matching a pattern
uv run pytest -k "test_conversion"

# Run tests in parallel (requires pytest-xdist)
uv run pytest -n auto
```

### Building with Nuitka

#### Automated Build Scripts (Recommended)

**Linux/macOS:**
```bash
# Basic optimized build
./scripts/build.sh

# Build with AppImage for distribution
./scripts/build.sh --appimage

# Build without optimization
./scripts/build.sh --no-strip

# Build with different optimization levels
./scripts/build.sh --strip-level moderate
./scripts/build.sh --appimage --strip-level conservative
```

**Windows:**
```powershell
# Basic optimized build
.\scripts\windows_build.ps1

# Build with professional installer
.\scripts\windows_build.ps1 -CreateInstaller

# Build without optimization
.\scripts\windows_build.ps1 -NoStrip

# Build with different optimization levels
.\scripts\windows_build.ps1 -StripLevel Moderate
.\scripts\windows_build.ps1 -CreateInstaller -StripLevel Conservative
```

#### Manual Nuitka Commands (Advanced)

```bash
# Basic standalone build
uv run python -m nuitka --standalone --enable-plugin=pyside6 pandoc_ui/main.py

# One-file build for production
uv run python -m nuitka \
  --onefile \
  --enable-plugin=pyside6 \
  --disable-console \
  --output-dir=dist \
  --output-file=pandoc-ui \
  pandoc_ui/main.py

# Windows build with icon and metadata
uv run python -m nuitka \
  --onefile \
  --enable-plugin=pyside6 \
  --disable-console \
  --windows-icon-from-ico=resources/icons/app.ico \
  --company-name="pandoc-ui" \
  --product-name="Pandoc UI" \
  --file-version="1.0.0.0" \
  --product-version="1.0.0.0" \
  --file-description="Graphical interface for Pandoc" \
  --copyright="MIT License" \
  --output-dir=dist \
  --output-file=pandoc-ui.exe \
  pandoc_ui/main.py

# Include data directories
uv run python -m nuitka \
  --onefile \
  --enable-plugin=pyside6 \
  --include-data-dir=resources=resources \
  --include-data-dir=templates=templates \
  pandoc_ui/main.py

# Development build (faster, with console)
uv run python -m nuitka \
  --standalone \
  --enable-plugin=pyside6 \
  --output-dir=build \
  pandoc_ui/main.py
```

#### Build Optimization Features

**Strip Binary Optimization:**
- **Conservative**: 5-15% size reduction, safe for PySide6 (default)
- **Moderate**: 10-25% size reduction, test before production use
- **Aggressive**: 15-40% size reduction, high risk for Qt applications

**Distribution Packages:**
- **Linux AppImage**: Portable, self-contained packages for all distributions
- **Windows NSIS Installer**: Professional installer with Modern UI, file associations, and context menu integration
- **Binary Optimization**: Automatic symbol stripping with safety checks

For detailed information, see: `docs/BUILD_OPTIMIZATION_GUIDE.md`

## Git Commit Conventions

This project follows the Conventional Commits specification. All commit messages must follow this format:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

- **feat**: New feature or enhancement
- **fix**: Bug fix
- **docs**: Documentation changes only
- **style**: Code style changes (formatting, semicolons, etc.)
- **refactor**: Code restructuring without changing functionality
- **perf**: Performance improvements
- **test**: Adding or modifying tests
- **chore**: Maintenance tasks (updating dependencies, build scripts, etc.)
- **ci**: CI/CD configuration changes
- **build**: Build system or external dependency changes

### Examples

```bash
# Feature
git commit -m "feat(gui): add dark mode toggle to settings"

# Bug fix
git commit -m "fix(converter): handle unicode filenames correctly"

# Documentation
git commit -m "docs: update installation instructions for macOS"

# Refactoring
git commit -m "refactor(app): extract conversion logic to separate service"

# Breaking change (note the !)
git commit -m "feat(api)!: change conversion API to async-only"

# Commit with scope and body
git commit -m "fix(batch): prevent UI freeze during large batch operations

- Move conversion to background thread
- Add progress callback mechanism
- Update UI through Qt signals"
```

### Commit Message Rules

1. Use imperative mood ("add" not "added" or "adds")
2. First line max 50 characters
3. Body lines max 72 characters
4. Reference issues: "Closes #123" or "Fixes #456"
5. For breaking changes, add "BREAKING CHANGE:" in the footer

## Important Development Requirements

### Update docs/CLAUDE_LOG.md After Each Task

**IMPORTANT**: After completing any task, you MUST update `docs/CLAUDE_LOG.md` with:

1. The task description
2. What was implemented
3. Any important decisions made
4. Files created or modified
5. Next steps or pending items
6. TITLE with current date, YYYY-MM-DD-HH:MM

Example entry:

```markdown
## 2024-06-24-13:24 - Implement Pandoc Runner

### Task
Implement the core pandoc execution module in infra/pandoc_runner.py

### Implementation
- Created PandocRunner class with async execution support
- Added command building logic for common conversion options
- Implemented progress callback mechanism using subprocess pipes

### Files Modified
- Created: `pandoc_ui/infra/pandoc_runner.py`
- Created: `tests/test_pandoc_runner.py`
- Modified: `pandoc_ui/app/conversion_service.py`

### Decisions
- Used asyncio.subprocess for non-blocking execution
- Parse pandoc progress output using regex for percentage extraction

### Next Steps
- Add support for custom templates
- Implement pandoc installation detection
```

## Architecture

The project follows a 3-layer clean architecture:

```
UI Layer (PySide6)
  gui/main_window.py     � Emits signals to Application layer
  gui/dialogs/           � Settings, profiles, etc.
  Resources (icons, translations)
    � signals/slots
Application Layer (Business Logic)
  app/conversion_service.py  � Orchestrates conversions
  app/task_queue.py         � Manages batch operations
  app/profile_repository.py � Conversion profiles
  app/folder_scanner.py     � Directory traversal
    � dependency injection
Infrastructure Layer
  infra/pandoc_runner.py    � Executes pandoc commands
  infra/pandoc_detector.py  � Locates pandoc installation
  infra/settings_store.py   � Persists user preferences
  infra/downloader.py       � Downloads pandoc if needed
```

Key principles:

- UI layer never directly imports Infrastructure
- Application layer is UI-agnostic for testability
- Dependency injection via constructors
- Signals/slots for async communication

## Current Implementation Status

The project is in initial development following a phased approach:

- **Phase 0**: Environment setup 
- **Phase 1**: CLI core (in progress)
- **Phase 2**: GUI MVP
- **Phase 3**: Batch processing
- **Phase 4**: Profile management
- **Phase 5**: Packaging
- **Phase 6**: Documentation

## Key Files to Understand

1. **docs/PRD.md**: Product requirements and user stories
2. **docs/TODOS.md**: Detailed implementation phases with acceptance criteria
3. **docs/STRUCTURE.md**: Planned directory structure and component responsibilities
4. **.cursor/rules/pyside.mdc**: PySide6 best practices and conventions

## Development Guidelines

### Code Style

- Follow PEP 8 with 4-space indentation
- Use Qt's CamelCase for Qt-derived methods (e.g., `loadItems()`)
- Prefer specific imports over wildcards
- Add docstrings for public methods

### PySide6 Conventions

- Use signals/slots for component communication
- Offload long operations to QThread/QThreadPool
- Manage QObject parenting for proper cleanup
- Use layouts instead of hardcoded positions
- **IMPORTANT**: Inherit from QMainWindow in main.py, not in gui/ modules
- GUI components should be composition-based, not inheritance-based

### Error Handling

- Gracefully handle missing Pandoc installation
- Single file failures shouldn't stop batch operations
- Display user-friendly error messages in GUI
- Log detailed errors for debugging

### Testing Strategy

- **ALL tests go in `tests/` directory and use pytest**
- Unit tests for business logic (app/ layer)
- Integration tests for pandoc execution  
- GUI tests using QTest and mock displays
- Mock external dependencies (pandoc binary)
- Target 90% test coverage
- **NO test files in scripts/ directory**

## External Dependencies

- **Pandoc**: External binary (not bundled)
  - Detected via PATH and common install locations
  - Minimum version: 2.0
  - Prompts download if missing
  
- **Python packages**:
  - PySide6 >= 6.9.1 (Qt bindings)
  - pytest (testing)
  - Nuitka (packaging)

## Platform Considerations

- Use `QStandardPaths` for user data directories
- Handle path separators via `pathlib`
- Test UI scaling on different DPIs
- Ensure consistent behavior across Windows/macOS/Linux

### WSL (Windows Subsystem for Linux) Setup

When running on WSL with WSLg for GUI applications:

```bash
# Fix Qt/PySide6 display issues in WSL
sudo apt-get install -y libxcb-cursor-dev

# Ensure WSLg is properly configured
# WSLg should be available by default in WSL2
# If experiencing blank windows, try setting Qt platform plugin:
export QT_QPA_PLATFORM=xcb

# For debugging Qt platform issues:
export QT_DEBUG_PLUGINS=1
export QT_LOGGING_RULES="qt.qpa.*=true"
```

**Common WSL Issues:**
- **Blank/empty windows**: Usually caused by Qt platform plugin detection issues
- **Wayland errors**: WSLg uses X11 by default, force xcb platform if needed
- **Missing cursor**: Install `libxcb-cursor-dev` package
- **High DPI issues**: WSLg handles DPI scaling automatically

## Pandoc Detection Troubleshooting

### Windows Pandoc Detection Issues

If pandoc is not being detected on Windows:

```bash
# Run the Windows-specific debug script
uv run python windows_pandoc_debug.py
```

**Common Solutions:**
1. **Install pandoc**: Download from https://pandoc.org/installing.html
2. **Add to PATH**: Ensure pandoc.exe is in your PATH environment variable
3. **Restart terminal**: After installation, restart Command Prompt/PowerShell
4. **Check installation locations**:
   - `C:\Program Files\Pandoc\pandoc.exe`
   - `C:\ProgramData\chocolatey\bin\pandoc.exe` (Chocolatey)
   - `%USERPROFILE%\scoop\shims\pandoc.exe` (Scoop)

**Manual PATH Check:**
```cmd
# Windows Command Prompt
where pandoc
pandoc --version

# PowerShell  
Get-Command pandoc
pandoc --version
```

### Cross-Platform Detection

The application uses multiple detection methods:
1. **PATH search** using `shutil.which()` 
2. **Common installation locations** per platform
3. **Manual PATH traversal** (Windows fallback)
4. **Alternative executable names** (Windows: .exe, .cmd, .bat)

**Debug logging** is available by setting log level to DEBUG.
