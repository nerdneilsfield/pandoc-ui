# PyInstaller spec file for pandoc-ui macOS build
# This provides more control over the build process

import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, BUNDLE
from PyInstaller.building.api import PKG

# Project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
main_script = os.path.join(project_root, 'pandoc_ui', 'main.py')

# Build configuration
app_name = 'Pandoc UI'
bundle_id = 'com.pandoc-ui.app'
version = '1.0.0'

# Data files to include (only if they exist)
datas = []

# Check and add resources directory
resources_path = os.path.join(project_root, 'resources')
if os.path.exists(resources_path):
    datas.append((resources_path, 'resources'))

# Check and add locales directory
locales_path = os.path.join(project_root, 'pandoc_ui', 'locales')
if os.path.exists(locales_path):
    datas.append((locales_path, 'pandoc_ui/locales'))

# Hidden imports for PySide6
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui', 
    'PySide6.QtWidgets',
    'PySide6.QtPrintSupport',
    'pandoc_ui.gui.main_window',
    'pandoc_ui.gui.ui_components',
    'pandoc_ui.gui.command_preview',
    'pandoc_ui.gui.conversion_worker',
    'pandoc_ui.app.conversion_service',
    'pandoc_ui.app.folder_scanner',
    'pandoc_ui.app.profile_repository',
    'pandoc_ui.app.task_queue',
    'pandoc_ui.infra.pandoc_runner',
    'pandoc_ui.infra.pandoc_detector',
    'pandoc_ui.infra.settings_store',
    'pandoc_ui.infra.config_manager',
    'pandoc_ui.infra.format_manager',
]

# Collect all PySide6 modules
collect_submodules = ['PySide6']

# Exclude unnecessary modules that may cause universal binary issues
excludes = [
    'mypy',
    'pytest', 
    'black',
    'ruff',
    'isort',
    'coverage',
    'setuptools',
    'pip',
    'wheel',
    'distutils',
    'tkinter',
    'unittest',
]

# Analysis
a = Analysis(
    [main_script],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    optimize=0,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name.replace(' ', '_').lower(),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name.replace(' ', '_').lower(),
)

# macOS app bundle
app = BUNDLE(
    coll,
    name=f'{app_name}.app',
    icon=os.path.join(project_root, 'resources', 'icons', 'app.icns'),
    bundle_identifier=bundle_id,
    version=version,
    info_plist={
        'CFBundleName': app_name,
        'CFBundleDisplayName': app_name,
        'CFBundleIdentifier': bundle_id,
        'CFBundleVersion': version,
        'CFBundleShortVersionString': version,
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleExecutable': app_name.replace(' ', '_').lower(),
        'CFBundlePackageType': 'APPL',
        'CFBundleIconFile': 'app.icns',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15.0',
        'NSHumanReadableCopyright': '© 2025 pandoc-ui. MIT License.',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['md', 'markdown'],
                'CFBundleTypeName': 'Markdown Document',
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Alternate',
            },
            {
                'CFBundleTypeExtensions': ['rst'],
                'CFBundleTypeName': 'reStructuredText Document', 
                'CFBundleTypeRole': 'Editor',
                'LSHandlerRank': 'Alternate',
            },
            {
                'CFBundleTypeExtensions': ['tex'],
                'CFBundleTypeName': 'LaTeX Document',
                'CFBundleTypeRole': 'Editor', 
                'LSHandlerRank': 'Alternate',
            },
        ],
        'UTExportedTypeDeclarations': [],
        'UTImportedTypeDeclarations': [],
    },
)