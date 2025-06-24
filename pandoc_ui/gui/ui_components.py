"""
UI components for pandoc-ui GUI application.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QTimer, Signal, Slot, QObject
from PySide6.QtWidgets import (
    QFileDialog, QMessageBox, QApplication, QWidget, QVBoxLayout, 
    QHBoxLayout, QGroupBox, QRadioButton, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QLabel, QSpinBox, QCheckBox
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

from ..models import ConversionProfile, ConversionResult, OutputFormat, InputFormat
from ..infra.format_manager import FormatManager
from .conversion_worker import ConversionWorker
from ..app.task_queue import TaskQueue
from ..app.folder_scanner import FolderScanner, ScanMode
from ..app.profile_repository import ProfileRepository, UIProfile
from ..infra.settings_store import SettingsStore, Language
from ..infra.config_manager import initialize_config


logger = logging.getLogger(__name__)


class MainWindowUI(QObject):
    """Main window UI component handler."""
    
    # Signals
    conversion_requested = Signal(ConversionProfile)
    
    def __init__(self, main_window, parent=None):
        """Initialize UI component."""
        super().__init__(parent)
        self.main_window = main_window
        
        # State
        self.current_worker: Optional[ConversionWorker] = None
        self.input_file_path: Optional[Path] = None
        self.input_folder_path: Optional[Path] = None
        self.is_batch_mode: bool = False
        
        # Initialize configuration management first
        initialize_config()
        
        # Initialize format manager
        self.format_manager = FormatManager()
        
        # Batch processing components
        self.task_queue: Optional[TaskQueue] = None
        self.folder_scanner = FolderScanner()
        self.batch_files: list[Path] = []
        
        # Profile and settings management
        self.profile_repository = ProfileRepository()
        self.settings_store = SettingsStore()
        self.current_settings = self.settings_store.load_settings()
        
        # Load UI
        self.setupUi()
        
        # Connect signals
        self.connectSignals()
        
        # Initialize UI state
        self.updateConvertButtonState()
        self.addLogMessage("🚀 Pandoc UI initialized", "INFO")
        
        # Check pandoc availability on startup
        QTimer.singleShot(100, self.checkPandocAvailability)
    
    def setupUi(self):
        """Load and setup UI from .ui file or create programmatically."""
        try:
            # Try to load UI file first
            ui_file_path = Path(__file__).parent / "main_window.ui"
            logger.info(f"Attempting to load UI file from: {ui_file_path}")
            
            success = self._tryLoadUiFile(ui_file_path)
            if not success:
                logger.warning("UI file loading failed, creating programmatic UI")
                self._createProgrammaticUI()
            
            # Set window properties
            self.main_window.setWindowTitle("Pandoc UI - Document Converter")
            self.main_window.resize(800, 600)
            
            # Force visibility and layout
            central_widget = self.main_window.centralWidget()
            if central_widget:
                central_widget.setVisible(True)
                central_widget.show()
                if hasattr(central_widget, 'layout') and central_widget.layout():
                    central_widget.layout().activate()
                    central_widget.layout().update()
            
            logger.info("Window properties set")
            
            # Verify UI components exist
            self._verifyUIComponents()
            
            # Initialize profile management UI
            self.initializeProfileUI()
            logger.info("Profile UI initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup UI: {str(e)}", exc_info=True)
            # Create minimal fallback UI
            self._createMinimalUI()
            
        # Final failsafe - ensure something is visible
        self._ensureUIVisible()
    
    def _tryLoadUiFile(self, ui_file_path: Path) -> bool:
        """Try to load UI from .ui file."""
        try:
            if not ui_file_path.exists():
                logger.warning(f"UI file not found: {ui_file_path}")
                return False
            
            ui_file = QFile(str(ui_file_path))
            if not ui_file.open(QIODevice.ReadOnly):
                logger.warning(f"Cannot open UI file: {ui_file_path}")
                return False
            
            loader = QUiLoader()
            loaded_widget = loader.load(ui_file, None)  # Don't set parent initially
            ui_file.close()
            
            if loaded_widget is None:
                logger.warning("QUiLoader returned None")
                return False
            
            # Extract the central widget from the loaded QMainWindow
            if hasattr(loaded_widget, 'centralWidget') and loaded_widget.centralWidget():
                central_content = loaded_widget.centralWidget()
                # Set parent to prevent deletion
                central_content.setParent(self.main_window)
                # Remove from the loaded window and set as our central widget
                loaded_widget.setCentralWidget(None)
                self.main_window.setCentralWidget(central_content)
                self.ui = loaded_widget  # Keep reference to loaded window for compatibility
                logger.info("Extracted central widget from loaded UI")
            else:
                # Fallback: use the loaded widget directly (shouldn't happen with our .ui file)
                self.main_window.setCentralWidget(loaded_widget)
                self.ui = loaded_widget
                logger.warning("Used loaded widget directly as central widget")
            
            # Force refresh and repaint of central widget
            central_widget = self.main_window.centralWidget()
            if central_widget:
                central_widget.show()
                central_widget.update()
                central_widget.repaint()
            self.main_window.update()
            self.main_window.repaint()
            
            logger.info("UI loaded successfully from .ui file")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load UI file: {str(e)}")
            return False
    
    def _createProgrammaticUI(self):
        """Create UI programmatically as fallback."""
        logger.info("Creating programmatic UI")
        
        # Create central widget
        central_widget = QWidget()
        central_widget.setMinimumSize(600, 400)
        self.main_window.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Input Selection Group
        input_group = QGroupBox("Input Selection")
        input_layout = QVBoxLayout(input_group)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        self.singleFileModeRadio = QRadioButton("Single File")
        self.singleFileModeRadio.setChecked(True)
        self.folderModeRadio = QRadioButton("Folder (Batch)")
        mode_layout.addWidget(self.singleFileModeRadio)
        mode_layout.addWidget(self.folderModeRadio)
        mode_layout.addStretch()
        input_layout.addLayout(mode_layout)
        
        # Input path
        input_path_layout = QHBoxLayout()
        input_path_layout.addWidget(QLabel("Input:"))
        self.inputPathEdit = QLineEdit()
        self.inputPathEdit.setPlaceholderText("Select input file or folder...")
        self.browseInputButton = QPushButton("Browse...")
        input_path_layout.addWidget(self.inputPathEdit)
        input_path_layout.addWidget(self.browseInputButton)
        input_layout.addLayout(input_path_layout)
        
        main_layout.addWidget(input_group)
        
        # Output Selection Group
        output_group = QGroupBox("Output Configuration")
        output_layout = QVBoxLayout(output_group)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(QLabel("Output Directory:"))
        self.outputDirEdit = QLineEdit()
        self.outputDirEdit.setPlaceholderText("Select output directory...")
        self.browseOutputButton = QPushButton("Browse...")
        output_dir_layout.addWidget(self.outputDirEdit)
        output_dir_layout.addWidget(self.browseOutputButton)
        output_layout.addLayout(output_dir_layout)
        
        # Input format selection
        input_format_layout = QHBoxLayout()
        input_format_layout.addWidget(QLabel("Input Format:"))
        self.inputFormatComboBox = QComboBox()
        self.inputFormatComboBox.addItem("Auto-detect", None)  # Auto-detect as default
        for fmt in InputFormat:
            self.inputFormatComboBox.addItem(fmt.value.upper(), fmt)
        input_format_layout.addWidget(self.inputFormatComboBox)
        input_format_layout.addStretch()
        output_layout.addLayout(input_format_layout)
        
        # Output format selection
        output_format_layout = QHBoxLayout()
        output_format_layout.addWidget(QLabel("Output Format:"))
        self.outputFormatComboBox = QComboBox()
        for fmt in OutputFormat:
            self.outputFormatComboBox.addItem(fmt.value.upper(), fmt)
        output_format_layout.addWidget(self.outputFormatComboBox)
        output_format_layout.addStretch()
        output_layout.addLayout(output_format_layout)
        
        main_layout.addWidget(output_group)
        
        # Batch Options Group (initially hidden)
        self.batchOptionsGroupBox = QGroupBox("Batch Options")
        batch_layout = QVBoxLayout(self.batchOptionsGroupBox)
        
        # Extension filter
        ext_layout = QHBoxLayout()
        ext_layout.addWidget(QLabel("Extensions:"))
        self.extensionFilterEdit = QLineEdit()
        self.extensionFilterEdit.setText(".md,.txt,.rst")
        ext_layout.addWidget(self.extensionFilterEdit)
        batch_layout.addLayout(ext_layout)
        
        # Max files
        max_files_layout = QHBoxLayout()
        max_files_layout.addWidget(QLabel("Max Files:"))
        self.maxFilesSpinBox = QSpinBox()
        self.maxFilesSpinBox.setRange(1, 10000)
        self.maxFilesSpinBox.setValue(1000)
        max_files_layout.addWidget(self.maxFilesSpinBox)
        max_files_layout.addStretch()
        batch_layout.addLayout(max_files_layout)
        
        # Recursive option
        self.recursiveCheckBox = QCheckBox("Scan subdirectories recursively")
        self.recursiveCheckBox.setChecked(True)
        batch_layout.addWidget(self.recursiveCheckBox)
        
        self.batchOptionsGroupBox.setVisible(False)
        main_layout.addWidget(self.batchOptionsGroupBox)
        
        # Convert button
        self.convertButton = QPushButton("Convert")
        self.convertButton.setMinimumHeight(40)
        main_layout.addWidget(self.convertButton)
        
        # Log area
        log_group = QGroupBox("Conversion Log")
        log_layout = QVBoxLayout(log_group)
        
        log_buttons_layout = QHBoxLayout()
        self.clearLogButton = QPushButton("Clear Log")
        log_buttons_layout.addWidget(self.clearLogButton)
        log_buttons_layout.addStretch()
        log_layout.addLayout(log_buttons_layout)
        
        self.logTextEdit = QTextEdit()
        self.logTextEdit.setMaximumHeight(150)
        log_layout.addWidget(self.logTextEdit)
        
        main_layout.addWidget(log_group)
        
        # Profile management (simplified)
        profile_group = QGroupBox("Configuration Profiles")
        profile_layout = QHBoxLayout(profile_group)
        
        profile_layout.addWidget(QLabel("Profile:"))
        self.profileComboBox = QComboBox()
        self.saveProfileButton = QPushButton("Save")
        self.loadProfileButton = QPushButton("Load")
        self.deleteProfileButton = QPushButton("Delete")
        
        profile_layout.addWidget(self.profileComboBox)
        profile_layout.addWidget(self.saveProfileButton)
        profile_layout.addWidget(self.loadProfileButton)
        profile_layout.addWidget(self.deleteProfileButton)
        profile_layout.addStretch()
        
        main_layout.addWidget(profile_group)
        
        # Language selector
        lang_layout = QHBoxLayout()
        lang_layout.addStretch()
        lang_layout.addWidget(QLabel("Language:"))
        self.languageComboBox = QComboBox()
        self.languageComboBox.addItems(["English", "中文", "日本語", "한국어", "Français", "Deutsch", "Español"])
        lang_layout.addWidget(self.languageComboBox)
        main_layout.addLayout(lang_layout)
        
        # Create ui object to match expected structure
        class UIWrapper:
            pass
        
        self.ui = UIWrapper()
        # Copy all widgets to ui object for compatibility
        for attr_name in dir(self):
            if attr_name.endswith(('Button', 'Edit', 'ComboBox', 'CheckBox', 'SpinBox', 'TextEdit', 'Radio', 'GroupBox')):
                setattr(self.ui, attr_name, getattr(self, attr_name))
        
        # Force layout and visibility
        central_widget.setVisible(True)
        central_widget.show()
        main_layout.activate()
        main_layout.update()
        central_widget.update()
        central_widget.repaint()
        
        logger.info("Programmatic UI created successfully")
    
    def _createMinimalUI(self):
        """Create minimal UI as last resort."""
        logger.info("Creating minimal fallback UI")
        
        central_widget = QWidget()
        central_widget.setMinimumSize(600, 400)
        central_widget.setStyleSheet("background-color: white; border: 1px solid gray;")
        self.main_window.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Pandoc UI - Minimal Mode")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: blue;")
        layout.addWidget(title_label)
        
        # Basic controls
        self.inputPathEdit = QLineEdit()
        self.browseInputButton = QPushButton("Browse Input")
        self.outputDirEdit = QLineEdit() 
        self.browseOutputButton = QPushButton("Browse Output")
        self.convertButton = QPushButton("Convert")
        self.logTextEdit = QTextEdit()
        
        layout.addWidget(QLabel("Input:"))
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.inputPathEdit)
        input_layout.addWidget(self.browseInputButton)
        layout.addLayout(input_layout)
        
        layout.addWidget(QLabel("Output Directory:"))
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.outputDirEdit)
        output_layout.addWidget(self.browseOutputButton)
        layout.addLayout(output_layout)
        
        layout.addWidget(self.convertButton)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.logTextEdit)
        
        # Create minimal ui object
        class UIWrapper:
            pass
        self.ui = UIWrapper()
        for attr_name in ['inputPathEdit', 'browseInputButton', 'outputDirEdit', 'browseOutputButton', 'convertButton', 'logTextEdit']:
            setattr(self.ui, attr_name, getattr(self, attr_name))
        
        # Force visibility
        central_widget.setVisible(True)
        central_widget.show()
        layout.activate()
        layout.update()
        central_widget.update()
        central_widget.repaint()
        
        logger.info("Minimal UI created")
    
    def _ensureUIVisible(self):
        """Final failsafe to ensure UI is visible."""
        try:
            logger.info("Ensuring UI visibility as failsafe")
            
            central_widget = self.main_window.centralWidget()
            if central_widget is None:
                logger.error("No central widget found! Creating emergency UI")
                
                # Emergency UI creation
                emergency_widget = QWidget()
                emergency_widget.setStyleSheet("background-color: red; color: white;")
                emergency_widget.setMinimumSize(400, 300)
                
                layout = QVBoxLayout(emergency_widget)
                layout.addWidget(QLabel("EMERGENCY UI - Something went wrong"))
                layout.addWidget(QLabel("Please check logs and report this issue"))
                
                emergency_button = QPushButton("Click me to test")
                layout.addWidget(emergency_button)
                
                self.main_window.setCentralWidget(emergency_widget)
                
                # Create minimal ui wrapper
                class UIWrapper:
                    pass
                self.ui = UIWrapper()
                self.ui.convertButton = emergency_button
                self.ui.logTextEdit = QTextEdit()
                layout.addWidget(self.ui.logTextEdit)
                
                emergency_widget.show()
                emergency_widget.update()
                emergency_widget.repaint()
                
                logger.error("Emergency UI created and displayed")
            else:
                logger.info(f"Central widget exists: {type(central_widget).__name__}")
                
                # Force everything to be visible
                central_widget.setVisible(True)
                central_widget.show()
                central_widget.raise_()
                
                if hasattr(central_widget, 'layout') and central_widget.layout():
                    central_widget.layout().activate()
                    central_widget.layout().update()
                
                # Force repaint
                central_widget.update()
                central_widget.repaint()
                self.main_window.update()
                self.main_window.repaint()
                
                logger.info("Forced UI visibility refresh completed")
                
        except Exception as e:
            logger.error(f"Failed to ensure UI visibility: {str(e)}", exc_info=True)
    
    def _verifyUIComponents(self):
        """Verify required UI components exist."""
        required_components = [
            'inputPathEdit', 'browseInputButton', 'outputDirEdit', 
            'browseOutputButton', 'convertButton', 'logTextEdit'
        ]
        
        missing = []
        for component in required_components:
            if not hasattr(self.ui, component):
                missing.append(component)
        
        if missing:
            logger.warning(f"Missing UI components: {missing}")
        else:
            logger.info("All required UI components verified")
        
        # Initialize formats after UI verification
        self._initializeFormats()
    
    def _initializeFormats(self):
        """Initialize format dropdown with comprehensive format support."""
        try:
            # Clear existing items if any
            if hasattr(self.ui, 'formatComboBox'):
                self.ui.formatComboBox.clear()
                
                # Add output formats from format manager
                output_formats = self.format_manager.get_output_formats()
                for format_key, display_name in output_formats:
                    self.ui.formatComboBox.addItem(display_name, format_key)
                
                # Set default to HTML if available
                html_index = self.ui.formatComboBox.findData('html')
                if html_index >= 0:
                    self.ui.formatComboBox.setCurrentIndex(html_index)
                
                logger.info(f"Initialized format dropdown with {len(output_formats)} formats")
            else:
                logger.warning("formatComboBox not found, skipping format initialization")
                
        except Exception as e:
            logger.error(f"Failed to initialize formats: {e}")
    
    def connectSignals(self):
        """Connect UI signals to slots."""
        try:
            # File browsing (required)
            self.ui.browseInputButton.clicked.connect(self.browseInput)
            self.ui.browseOutputButton.clicked.connect(self.browseOutputDirectory)
            
            # Conversion (required)
            self.ui.convertButton.clicked.connect(self.startConversion)
            
            # UI updates (required)
            self.ui.inputPathEdit.textChanged.connect(self.updateConvertButtonState)
            
            # Mode switching (optional)
            if hasattr(self.ui, 'singleFileModeRadio'):
                self.ui.singleFileModeRadio.toggled.connect(self.onModeChanged)
            if hasattr(self.ui, 'folderModeRadio'):
                self.ui.folderModeRadio.toggled.connect(self.onModeChanged)
            
            # Optional components
            if hasattr(self.ui, 'formatComboBox'):
                self.ui.formatComboBox.currentTextChanged.connect(self.onFormatChanged)
            if hasattr(self.ui, 'extensionFilterEdit'):
                self.ui.extensionFilterEdit.textChanged.connect(self.onExtensionFilterChanged)
            if hasattr(self.ui, 'clearLogButton'):
                self.ui.clearLogButton.clicked.connect(self.clearLog)
            
            # Menu actions (optional)
            if hasattr(self.ui, 'actionExit'):
                self.ui.actionExit.triggered.connect(self.main_window.close)
            if hasattr(self.ui, 'actionAbout'):
                self.ui.actionAbout.triggered.connect(self.showAbout)
            
            # Profile management (optional)
            if hasattr(self.ui, 'saveProfileButton'):
                self.ui.saveProfileButton.clicked.connect(self.saveProfile)
            if hasattr(self.ui, 'loadProfileButton'):
                self.ui.loadProfileButton.clicked.connect(self.loadProfile)
            if hasattr(self.ui, 'deleteProfileButton'):
                self.ui.deleteProfileButton.clicked.connect(self.deleteProfile)
            if hasattr(self.ui, 'profileComboBox'):
                self.ui.profileComboBox.currentTextChanged.connect(self.onProfileSelected)
            
            # Language switching (optional)
            if hasattr(self.ui, 'languageComboBox'):
                self.ui.languageComboBox.currentTextChanged.connect(self.onLanguageChanged)
                
            logger.info("UI signals connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect signals: {str(e)}", exc_info=True)
    
    @Slot()
    def browseInput(self):
        """Open dialog to select input file or folder based on mode."""
        if self.is_batch_mode:
            self.browseFolderInput()
        else:
            self.browseFileInput()
    
    def browseFileInput(self):
        """Open file dialog to select input file."""
        file_dialog = QFileDialog(self.main_window)
        file_dialog.setWindowTitle("Select Input File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        
        # Get comprehensive file filters from format manager
        file_filters = self.format_manager.get_file_filters()
        file_dialog.setNameFilters(file_filters)
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = Path(selected_files[0])
                self.input_file_path = file_path
                self.input_folder_path = None
                self.ui.inputPathEdit.setText(str(file_path))
                
                # Auto-set output directory to input file directory
                if not self.ui.outputDirEdit.text():
                    self.ui.outputDirEdit.setText(str(file_path.parent))
                
                self.addLogMessage(f"📁 Input file selected: {file_path.name}")
    
    def browseFolderInput(self):
        """Open directory dialog to select input folder for batch processing."""
        dir_dialog = QFileDialog(self.main_window)
        dir_dialog.setWindowTitle("Select Input Folder")
        dir_dialog.setFileMode(QFileDialog.Directory)
        
        if dir_dialog.exec():
            selected_dir = dir_dialog.selectedFiles()[0]
            folder_path = Path(selected_dir)
            self.input_folder_path = folder_path
            self.input_file_path = None
            self.ui.inputPathEdit.setText(str(folder_path))
            
            # Auto-set output directory to parent of input folder
            if not self.ui.outputDirEdit.text():
                output_dir = folder_path.parent / f"{folder_path.name}_converted"
                self.ui.outputDirEdit.setText(str(output_dir))
            
            self.addLogMessage(f"📂 Input folder selected: {folder_path.name}")
            
            # Scan folder to preview files
            self.scanInputFolder()
    
    @Slot()
    def browseOutputDirectory(self):
        """Open directory dialog to select output directory."""
        dir_dialog = QFileDialog(self.main_window)
        dir_dialog.setWindowTitle("Select Output Directory")
        dir_dialog.setFileMode(QFileDialog.Directory)
        
        if dir_dialog.exec():
            selected_dir = dir_dialog.selectedFiles()[0]
            self.ui.outputDirEdit.setText(selected_dir)
            self.addLogMessage(f"📂 Output directory: {selected_dir}")
    
    @Slot()
    def onModeChanged(self):
        """Handle mode change between single file and batch."""
        self.is_batch_mode = self.ui.folderModeRadio.isChecked()
        
        # Enable/disable batch options
        self.ui.batchOptionsGroupBox.setEnabled(self.is_batch_mode)
        
        # Update placeholder text and button text
        if self.is_batch_mode:
            self.ui.inputPathEdit.setPlaceholderText("Select folder for batch conversion...")
            self.ui.browseInputButton.setText("Browse Folder...")
            self.ui.convertButton.setText("Start Batch Conversion")
        else:
            self.ui.inputPathEdit.setPlaceholderText("Select input file to convert...")
            self.ui.browseInputButton.setText("Browse File...")
            self.ui.convertButton.setText("Start Conversion")
        
        # Clear current input selection
        self.ui.inputPathEdit.clear()
        self.input_file_path = None
        self.input_folder_path = None
        self.batch_files.clear()
        
        self.addLogMessage(f"🔄 Mode changed to: {'Batch' if self.is_batch_mode else 'Single File'}")
        self.updateConvertButtonState()
    
    @Slot()
    def onExtensionFilterChanged(self):
        """Handle extension filter change."""
        if self.is_batch_mode and self.input_folder_path:
            self.scanInputFolder()
    
    def scanInputFolder(self):
        """Scan input folder for files matching criteria."""
        if not self.input_folder_path:
            return
        
        # Get scan parameters
        extensions_text = self.ui.extensionFilterEdit.text().strip()
        if extensions_text:
            # Parse extension filter
            extensions = {ext.strip() for ext in extensions_text.split(',') if ext.strip()}
        else:
            # Auto-detect based on output format
            format_text = self.ui.formatComboBox.currentText().lower()
            try:
                output_format = OutputFormat(format_text if format_text != "latex" else "latex")
                extensions = self.folder_scanner.get_supported_extensions(output_format)
            except ValueError:
                extensions = self.folder_scanner.get_supported_extensions()
        
        # Get scan mode
        scan_mode = ScanMode.RECURSIVE if self.ui.scanModeComboBox.currentIndex() == 0 else ScanMode.SINGLE_LEVEL
        max_files = self.ui.maxFilesSpinBox.value()
        
        # Perform scan
        self.addLogMessage(f"🔍 Scanning folder: {self.input_folder_path.name}")
        scan_result = self.folder_scanner.scan_folder(
            self.input_folder_path,
            extensions=extensions,
            mode=scan_mode,
            max_files=max_files
        )
        
        if scan_result.success:
            self.batch_files = scan_result.files
            self.addLogMessage(f"✅ Found {scan_result.filtered_count} files ({scan_result.scan_duration_seconds:.2f}s)")
            if scan_result.filtered_count != scan_result.total_count:
                self.addLogMessage(f"📊 Total files scanned: {scan_result.total_count}, matching filter: {scan_result.filtered_count}")
        else:
            self.batch_files = []
            for error in scan_result.errors:
                self.addLogMessage(f"❌ Scan error: {error}")
        
        self.updateConvertButtonState()
    
    @Slot()
    def startConversion(self):
        """Start document conversion."""
        if self.is_batch_mode:
            self.startBatchConversion()
        else:
            self.startSingleConversion()
    
    def startSingleConversion(self):
        """Start single file conversion."""
        if not self.input_file_path or not self.input_file_path.exists():
            QMessageBox.warning(self.main_window, "Error", "Please select a valid input file")
            return
        
        # Auto-detect input format from file extension
        input_format_str = self.format_manager.detect_format_from_extension(str(self.input_file_path))
        try:
            input_format_data = InputFormat(input_format_str) if input_format_str else None
        except ValueError:
            input_format_data = None
        
        # Get output format from combo box
        output_format_str = None
        if hasattr(self.ui, 'formatComboBox'):
            output_format_str = self.ui.formatComboBox.currentData()
        
        if not output_format_str:
            QMessageBox.warning(self.main_window, "Error", "Please select a valid output format")
            return
            
        # Verify format compatibility
        if input_format_str and not self.format_manager.can_convert(input_format_str, output_format_str):
            QMessageBox.warning(self.main_window, "Format Compatibility Error", 
                              f"Cannot convert from {input_format_str} to {output_format_str}")
            return
        
        try:
            output_format_data = OutputFormat(output_format_str)
        except ValueError:
            QMessageBox.warning(self.main_window, "Error", f"Unsupported output format: {output_format_str}")
            return
        
        # Determine output path
        output_dir = self.ui.outputDirEdit.text().strip()
        if not output_dir:
            output_dir = str(self.input_file_path.parent)
        
        output_path = Path(output_dir) / f"{self.input_file_path.stem}.{output_format_data.value}"
        
        # Create conversion profile
        profile = ConversionProfile(
            input_path=self.input_file_path,
            output_path=output_path,
            input_format=input_format_data,
            output_format=output_format_data
        )
        
        # Start worker thread
        self.startWorkerConversion(profile)
    
    def startBatchConversion(self):
        """Start batch conversion using task queue."""
        if not self.batch_files:
            QMessageBox.warning(self.main_window, "Error", "No files found for batch conversion. Please select a folder and check your filter settings.")
            return
        
        # Get output format from combo box
        output_format_str = None
        if hasattr(self.ui, 'formatComboBox'):
            output_format_str = self.ui.formatComboBox.currentData()
        
        if not output_format_str:
            QMessageBox.warning(self.main_window, "Error", "Please select a valid output format")
            return
        
        try:
            output_format_data = OutputFormat(output_format_str)
        except ValueError:
            QMessageBox.warning(self.main_window, "Error", f"Unsupported output format: {output_format_str}")
            return
        
        # Get output directory
        output_dir = self.ui.outputDirEdit.text().strip()
        if not output_dir:
            QMessageBox.warning(self.main_window, "Error", "Please specify an output directory for batch conversion")
            return
        
        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True)
                self.addLogMessage(f"📁 Created output directory: {output_path}")
            except Exception as e:
                QMessageBox.critical(self.main_window, "Error", f"Failed to create output directory: {e}")
                return
        
        # Create task queue
        self.task_queue = TaskQueue(max_concurrent_jobs=4, parent=self.main_window)
        
        # Connect task queue signals
        self.task_queue.task_started.connect(self.onBatchTaskStarted)
        self.task_queue.task_completed.connect(self.onBatchTaskCompleted)
        self.task_queue.task_failed.connect(self.onBatchTaskFailed)
        self.task_queue.queue_progress.connect(self.onBatchProgress)
        self.task_queue.queue_finished.connect(self.onBatchFinished)
        
        # Add tasks to queue
        for i, input_file in enumerate(self.batch_files):
            output_file = output_path / f"{input_file.stem}.{output_format_data.value}"
            
            # Auto-detect input format for each file
            input_format_str = self.format_manager.detect_format_from_extension(str(input_file))
            try:
                input_format_data = InputFormat(input_format_str) if input_format_str else None
            except ValueError:
                input_format_data = None
            
            # Check format compatibility
            if input_format_str and not self.format_manager.can_convert(input_format_str, output_format_str):
                self.addLogMessage(f"⚠️ Skipping {input_file.name}: Cannot convert from {input_format_str} to {output_format_str}")
                continue
            
            profile = ConversionProfile(
                input_path=input_file,
                output_path=output_file,
                input_format=input_format_data,
                output_format=output_format_data
            )
            
            task_id = f"batch_{i:04d}_{input_file.name}"
            self.task_queue.add_task(task_id, profile)
        
        # Update UI for batch processing
        self.ui.convertButton.setEnabled(False)
        self.ui.convertButton.setText("Batch Converting...")
        self.ui.progressBar.setValue(0)
        self.ui.statusLabel.setText(f"Starting batch conversion of {len(self.batch_files)} files...")
        
        # Start batch processing
        self.addLogMessage(f"🚀 Starting batch conversion of {len(self.batch_files)} files")
        self.task_queue.start_queue()
    
    def startWorkerConversion(self, profile: ConversionProfile):
        """Start conversion using worker thread."""
        # Disable convert button
        self.ui.convertButton.setEnabled(False)
        self.ui.convertButton.setText("Converting...")
        
        # Reset progress
        self.ui.progressBar.setValue(0)
        self.ui.statusLabel.setText("Starting conversion...")
        
        # Create and start worker
        self.current_worker = ConversionWorker(profile, service=None, parent=self.main_window)
        self.current_worker.progress_updated.connect(self.updateProgress)
        self.current_worker.status_updated.connect(self.updateStatus)
        self.current_worker.log_message.connect(self.addLogMessage)
        self.current_worker.conversion_finished.connect(self.onConversionFinished)
        self.current_worker.finished.connect(self.onWorkerFinished)
        
        self.current_worker.start()
        
        self.addLogMessage("🔄 Starting conversion in background thread...")
    
    @Slot(int)
    def updateProgress(self, value: int):
        """Update progress bar."""
        self.ui.progressBar.setValue(value)
    
    @Slot(str)
    def updateStatus(self, message: str):
        """Update status label."""
        self.ui.statusLabel.setText(message)
    
    @Slot(str)
    def addLogMessage(self, message: str, level: str = "INFO"):
        """Add message to log window."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.ui.logTextEdit.append(formatted_message)
        
        # Auto-scroll to bottom
        cursor = self.ui.logTextEdit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.ui.logTextEdit.setTextCursor(cursor)
        
        # Process events to update UI
        QApplication.processEvents()
    
    @Slot(ConversionResult)
    def onConversionFinished(self, result: ConversionResult):
        """Handle conversion completion."""
        if result.success:
            self.addLogMessage("✅ Conversion completed successfully!")
            QMessageBox.information(
                self.main_window, 
                "Success", 
                f"File converted successfully!\n\nOutput saved to:\n{result.output_path}"
            )
        else:
            self.addLogMessage(f"❌ Conversion failed: {result.error_message}")
            QMessageBox.critical(
                self.main_window,
                "Conversion Failed",
                f"Conversion failed:\n\n{result.error_message}"
            )
    
    @Slot()
    def onWorkerFinished(self):
        """Handle worker thread completion."""
        # Re-enable convert button
        self.ui.convertButton.setEnabled(True)
        self.ui.convertButton.setText("Start Conversion")
        
        # Clean up worker
        if self.current_worker:
            self.current_worker.deleteLater()
            self.current_worker = None
        
        self.addLogMessage("🔄 Conversion thread finished")
    
    @Slot(str, str)
    def onBatchTaskStarted(self, task_id: str, filename: str):
        """Handle batch task started."""
        self.addLogMessage(f"🔄 Started: {filename}")
    
    @Slot(str, str, float)
    def onBatchTaskCompleted(self, task_id: str, output_path: str, duration: float):
        """Handle batch task completed."""
        filename = Path(output_path).name if output_path else task_id
        self.addLogMessage(f"✅ Completed: {filename} ({duration:.2f}s)")
    
    @Slot(str, str, str)
    def onBatchTaskFailed(self, task_id: str, filename: str, error_message: str):
        """Handle batch task failed with red highlighting."""
        # Add message with HTML for red coloring
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] <span style='color: red;'>❌ Failed: {filename} - {error_message}</span>"
        
        # Use insertHtml for colored text
        self.ui.logTextEdit.append("")  # Add empty line first
        cursor = self.ui.logTextEdit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertHtml(formatted_message)
        self.ui.logTextEdit.setTextCursor(cursor)
        
        # Auto-scroll to bottom
        cursor.movePosition(cursor.MoveOperation.End)
        self.ui.logTextEdit.setTextCursor(cursor)
        QApplication.processEvents()
    
    @Slot(int, int)
    def onBatchProgress(self, completed: int, total: int):
        """Handle batch progress update."""
        progress = int((completed / total) * 100) if total > 0 else 0
        self.ui.progressBar.setValue(progress)
        self.ui.statusLabel.setText(f"Converting... ({completed}/{total} files)")
    
    @Slot(int, int, float)
    def onBatchFinished(self, total_tasks: int, successful_tasks: int, total_duration: float):
        """Handle batch conversion completion."""
        failed_tasks = total_tasks - successful_tasks
        
        # Update UI
        self.ui.progressBar.setValue(100)
        self.ui.convertButton.setEnabled(True)
        self.ui.convertButton.setText("Start Batch Conversion" if self.is_batch_mode else "Start Conversion")
        
        # Show completion message
        if failed_tasks == 0:
            self.ui.statusLabel.setText(f"Batch conversion completed successfully!")
            self.addLogMessage(f"🎉 Batch conversion completed: {successful_tasks}/{total_tasks} files successful ({total_duration:.2f}s)")
            QMessageBox.information(
                self.main_window,
                "Batch Conversion Complete",
                f"All {total_tasks} files converted successfully!\n\nTotal time: {total_duration:.2f} seconds"
            )
        else:
            self.ui.statusLabel.setText(f"Batch conversion completed with {failed_tasks} failures")
            self.addLogMessage(f"⚠️ Batch conversion completed: {successful_tasks}/{total_tasks} successful, {failed_tasks} failed ({total_duration:.2f}s)")
            QMessageBox.warning(
                self.main_window,
                "Batch Conversion Complete",
                f"Batch conversion finished with some failures:\n\n"
                f"Successful: {successful_tasks}/{total_tasks} files\n"
                f"Failed: {failed_tasks} files\n"
                f"Total time: {total_duration:.2f} seconds\n\n"
                f"Check the log for details on failed conversions."
            )
        
        # Clean up task queue
        if self.task_queue:
            self.task_queue.deleteLater()
            self.task_queue = None
    
    @Slot()
    def updateConvertButtonState(self):
        """Update convert button enabled state."""
        if self.is_batch_mode:
            has_input = bool(self.batch_files)
            has_output = bool(self.ui.outputDirEdit.text().strip())
            is_not_converting = self.task_queue is None or self.task_queue.active_jobs_count == 0
            self.ui.convertButton.setEnabled(has_input and has_output and is_not_converting)
        else:
            has_input = bool(self.ui.inputPathEdit.text().strip())
            is_not_converting = self.current_worker is None or not self.current_worker.isRunning()
            self.ui.convertButton.setEnabled(has_input and is_not_converting)
    
    @Slot()
    def onFormatChanged(self):
        """Handle output format change."""
        format_name = self.ui.formatComboBox.currentText()
        self.addLogMessage(f"📋 Output format changed to: {format_name}")
    
    @Slot()
    def clearLog(self):
        """Clear log text."""
        self.ui.logTextEdit.clear()
        self.addLogMessage("🧹 Log cleared")
    
    @Slot()
    def showAbout(self):
        """Show about dialog."""
        QMessageBox.about(
            self.main_window,
            "About Pandoc UI",
            """<h3>Pandoc UI v0.1.0</h3>
            <p>A PySide6-based graphical interface for Pandoc document conversion.</p>
            <p>Supports conversion between multiple document formats including:</p>
            <ul>
            <li>Markdown → HTML, PDF, DOCX, ODT, EPUB</li>
            <li>HTML → PDF, DOCX, etc.</li>
            <li>And many more format combinations</li>
            </ul>
            <p><b>Requirements:</b> Pandoc must be installed on your system.</p>
            <p><a href="https://pandoc.org">https://pandoc.org</a></p>
            """
        )
    
    def checkPandocAvailability(self):
        """Check if pandoc is available on startup."""
        from ..app.conversion_service import ConversionService
        
        service = ConversionService()
        if service.is_pandoc_available():
            pandoc_info = service.get_pandoc_info()
            self.addLogMessage(f"✅ Pandoc detected: {pandoc_info.path} (v{pandoc_info.version})")
            self.ui.statusLabel.setText("Ready - Pandoc available")
        else:
            self.addLogMessage("❌ Pandoc not found! Please install Pandoc from https://pandoc.org")
            self.ui.statusLabel.setText("Pandoc not available")
            
            # Show warning
            QMessageBox.warning(
                self.main_window,
                "Pandoc Not Found",
                """Pandoc was not found on your system.
                
Please install Pandoc from:
https://pandoc.org/installing.html

The application will not work without Pandoc."""
            )
    
    def handleWindowClose(self):
        """Handle window close event."""
        # Check for running conversions
        single_running = self.current_worker and self.current_worker.isRunning()
        batch_running = self.task_queue and self.task_queue.active_jobs_count > 0
        
        if single_running or batch_running:
            conversion_type = "batch conversion" if batch_running else "conversion"
            reply = QMessageBox.question(
                self.main_window,
                "Conversion in Progress",
                f"A {conversion_type} is currently running. Do you want to close anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return False
            
            # Stop running conversions if user confirms
            if single_running:
                self.current_worker.terminate()
                self.current_worker.wait(3000)  # Wait up to 3 seconds
            
            if batch_running:
                self.addLogMessage("🛑 Cancelling batch conversion...")
                self.task_queue.cancel_queue()
                self.task_queue.wait_for_completion(3000)  # Wait up to 3 seconds
        
        self.addLogMessage("👋 Closing Pandoc UI")
        return True
    
    # Profile Management Methods
    
    @Slot()
    def saveProfile(self):
        """Save current UI state as a profile."""
        from PySide6.QtWidgets import QInputDialog
        
        # Get profile name from user
        name, ok = QInputDialog.getText(
            self.main_window,
            "Save Profile",
            "Enter profile name:",
            text="My Configuration"
        )
        
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        # Check if profile already exists
        if self.profile_repository.profile_exists(name):
            reply = QMessageBox.question(
                self.main_window,
                "Profile Exists",
                f"Profile '{name}' already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Collect current UI state
        ui_state = self.collectUIState()
        
        # Create and save profile
        profile = self.profile_repository.create_profile_from_ui_state(name, ui_state)
        
        if self.profile_repository.save_profile(profile):
            self.addLogMessage(f"💾 Profile '{name}' saved successfully")
            self.refreshProfileList()
            
            # Select the newly saved profile
            index = self.ui.profileComboBox.findText(name)
            if index >= 0:
                self.ui.profileComboBox.setCurrentIndex(index)
        else:
            QMessageBox.critical(
                self.main_window,
                "Save Error",
                f"Failed to save profile '{name}'"
            )
    
    @Slot()
    def loadProfile(self):
        """Load selected profile configuration."""
        profile_display = self.ui.profileComboBox.currentText()
        
        if not profile_display or profile_display == "-- Select Profile --":
            QMessageBox.information(
                self.main_window,
                "No Profile Selected",
                "Please select a profile to load"
            )
            return
        
        # Extract actual profile name from display text (stored in userData)
        profile_name = self.ui.profileComboBox.currentData()
        if not profile_name:
            # Fallback: extract name from display text
            profile_name = profile_display.split(" (")[0]
        
        profile = self.profile_repository.load_profile(profile_name)
        
        if profile:
            self.applyProfileToUI(profile)
            self.addLogMessage(f"📁 Profile '{profile_name}' loaded successfully")
        else:
            QMessageBox.critical(
                self.main_window,
                "Load Error",
                f"Failed to load profile '{profile_name}'"
            )
            self.refreshProfileList()  # Refresh in case profile was deleted
    
    @Slot()
    def deleteProfile(self):
        """Delete selected profile."""
        profile_display = self.ui.profileComboBox.currentText()
        
        if not profile_display or profile_display == "-- Select Profile --":
            QMessageBox.information(
                self.main_window,
                "No Profile Selected",
                "Please select a profile to delete"
            )
            return
        
        # Extract actual profile name from display text (stored in userData)
        profile_name = self.ui.profileComboBox.currentData()
        if not profile_name:
            # Fallback: extract name from display text
            profile_name = profile_display.split(" (")[0]
        
        reply = QMessageBox.question(
            self.main_window,
            "Delete Profile",
            f"Are you sure you want to delete profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.profile_repository.delete_profile(profile_name):
                self.addLogMessage(f"🗑️ Profile '{profile_name}' deleted successfully")
                self.refreshProfileList()
            else:
                QMessageBox.critical(
                    self.main_window,
                    "Delete Error",
                    f"Failed to delete profile '{profile_name}'"
                )
    
    @Slot(str)
    def onProfileSelected(self, profile_name: str):
        """Handle profile selection change."""
        # Enable/disable buttons based on selection
        has_selection = profile_name and profile_name != "-- Select Profile --"
        self.ui.loadProfileButton.setEnabled(has_selection)
        self.ui.deleteProfileButton.setEnabled(has_selection)
    
    @Slot(str)
    def onLanguageChanged(self, language_text: str):
        """Handle language selection change."""
        language_map = {
            "English": Language.ENGLISH,
            "中文": Language.CHINESE,
            "日本語": Language.JAPANESE,
            "한국어": Language.KOREAN,
            "Français": Language.FRENCH,
            "Deutsch": Language.GERMAN,
            "Español": Language.SPANISH
        }
        
        language = language_map.get(language_text, Language.ENGLISH)
        
        # Update settings
        if self.settings_store.update_setting('language', language.value):
            self.addLogMessage(f"🌐 Language changed to {language_text}")
            
            # TODO: Implement actual UI text refresh when translations are available
            QMessageBox.information(
                self.main_window,
                "Language Changed",
                f"Language changed to {language_text}.\n"
                "UI text refresh will be implemented in a future version."
            )
    
    def collectUIState(self) -> dict:
        """Collect current UI state for profile saving."""
        return {
            'input_file': self.ui.inputPathEdit.text() if not self.is_batch_mode else None,
            'output_file': self.ui.outputPathEdit.text() if not self.is_batch_mode else None,
            'output_format': self.ui.formatComboBox.currentText().lower(),
            
            'is_batch_mode': self.is_batch_mode,
            'input_folder': self.ui.inputPathEdit.text() if self.is_batch_mode else None,
            'output_folder': self.ui.outputPathEdit.text() if self.is_batch_mode else None,
            'extensions': self.ui.extensionFilterEdit.text(),
            'scan_recursive': self.ui.recursiveScanRadio.isChecked(),
            'max_files': self.ui.maxFilesSpinBox.value(),
            
            'html_standalone': True,  # Could be from advanced options if implemented
            'max_concurrent_jobs': self.current_settings.max_concurrent_jobs
        }
    
    def applyProfileToUI(self, profile: UIProfile):
        """Apply profile settings to UI widgets."""
        # Set mode
        if profile.is_batch_mode:
            self.ui.folderModeRadio.setChecked(True)
        else:
            self.ui.singleFileModeRadio.setChecked(True)
        
        # Set paths
        if profile.is_batch_mode:
            if profile.input_folder:
                self.ui.inputPathEdit.setText(profile.input_folder)
            if profile.output_folder:
                self.ui.outputPathEdit.setText(profile.output_folder)
        else:
            if profile.input_file:
                self.ui.inputPathEdit.setText(profile.input_file)
            if profile.output_file:
                self.ui.outputPathEdit.setText(profile.output_file)
        
        # Set format
        format_index = self.ui.formatComboBox.findText(profile.output_format.upper())
        if format_index >= 0:
            self.ui.formatComboBox.setCurrentIndex(format_index)
        
        # Set batch options
        self.ui.extensionFilterEdit.setText(profile.extensions)
        self.ui.recursiveScanRadio.setChecked(profile.scan_recursive)
        self.ui.singleLevelScanRadio.setChecked(not profile.scan_recursive)
        self.ui.maxFilesSpinBox.setValue(profile.max_files)
        
        # Update UI state
        self.onModeChanged()
        self.updateConvertButtonState()
    
    def refreshProfileList(self):
        """Refresh the profile combo box with available profiles."""
        current_text = self.ui.profileComboBox.currentText()
        
        # Clear and repopulate
        self.ui.profileComboBox.clear()
        self.ui.profileComboBox.addItem("-- Select Profile --")
        
        # Get profiles sorted by modification time
        profiles = self.profile_repository.list_profiles()
        
        for profile in profiles:
            display_text = f"{profile.name} ({profile.modified_at[:10]})"  # Name + date
            self.ui.profileComboBox.addItem(display_text, profile.name)
        
        # Try to restore previous selection
        if current_text:
            index = self.ui.profileComboBox.findText(current_text)
            if index >= 0:
                self.ui.profileComboBox.setCurrentIndex(index)
        
        # Update button states
        self.onProfileSelected(self.ui.profileComboBox.currentText())
    
    def initializeProfileUI(self):
        """Initialize profile management UI components."""
        # Load profiles
        self.refreshProfileList()
        
        # Set initial language
        language = self.current_settings.language
        language_map = {
            Language.ENGLISH: "English",
            Language.CHINESE: "中文",
            Language.JAPANESE: "日本語",
            Language.KOREAN: "한국어",
            Language.FRENCH: "Français",
            Language.GERMAN: "Deutsch",
            Language.SPANISH: "Español"
        }
        
        language_text = language_map.get(Language(language), "English")
        index = self.ui.languageComboBox.findText(language_text)
        if index >= 0:
            self.ui.languageComboBox.setCurrentIndex(index)