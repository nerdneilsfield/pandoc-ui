"""
Main window implementation for pandoc-ui GUI.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QMessageBox, QApplication
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QIODevice

from ..models import ConversionProfile, ConversionResult, OutputFormat
from .conversion_worker import ConversionWorker


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    start_conversion = Signal(ConversionProfile)
    
    def __init__(self, parent=None):
        """Initialize main window."""
        super().__init__(parent)
        
        # Load UI
        self.setupUi()
        
        # State
        self.current_worker: Optional[ConversionWorker] = None
        self.input_file_path: Optional[Path] = None
        
        # Connect signals
        self.connectSignals()
        
        # Initialize UI state
        self.updateConvertButtonState()
        self.addLogMessage("🚀 Pandoc UI initialized", "INFO")
        
        # Check pandoc availability on startup
        QTimer.singleShot(100, self.checkPandocAvailability)
    
    def setupUi(self):
        """Load and setup UI from .ui file."""
        # Load UI file
        ui_file_path = Path(__file__).parent / "main_window.ui"
        ui_file = QFile(str(ui_file_path))
        
        if not ui_file.open(QIODevice.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_file_path}")
        
        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()
        
        # Set as central widget
        self.setCentralWidget(self.ui)
        
        # Set window properties
        self.setWindowTitle("Pandoc UI - Document Converter")
        self.resize(800, 600)
    
    def connectSignals(self):
        """Connect UI signals to slots."""
        # File browsing
        self.ui.browseInputButton.clicked.connect(self.browseInputFile)
        self.ui.browseOutputButton.clicked.connect(self.browseOutputDirectory)
        
        # Conversion
        self.ui.convertButton.clicked.connect(self.startConversion)
        
        # UI updates
        self.ui.inputFileEdit.textChanged.connect(self.updateConvertButtonState)
        self.ui.formatComboBox.currentTextChanged.connect(self.onFormatChanged)
        
        # Log management
        self.ui.clearLogButton.clicked.connect(self.clearLog)
        
        # Menu actions
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.showAbout)
    
    @Slot()
    def browseInputFile(self):
        """Open file dialog to select input file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Input File")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilters([
            "Markdown files (*.md *.markdown)",
            "Text files (*.txt)",
            "ReStructuredText (*.rst)",
            "HTML files (*.html *.htm)",
            "Word documents (*.docx)",
            "All files (*.*)"
        ])
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = Path(selected_files[0])
                self.input_file_path = file_path
                self.ui.inputFileEdit.setText(str(file_path))
                
                # Auto-set output directory to input file directory
                if not self.ui.outputDirEdit.text():
                    self.ui.outputDirEdit.setText(str(file_path.parent))
                
                self.addLogMessage(f"📁 Input file selected: {file_path.name}")
    
    @Slot()
    def browseOutputDirectory(self):
        """Open directory dialog to select output directory."""
        dir_dialog = QFileDialog(self)
        dir_dialog.setWindowTitle("Select Output Directory")
        dir_dialog.setFileMode(QFileDialog.Directory)
        
        if dir_dialog.exec():
            selected_dir = dir_dialog.selectedFiles()[0]
            self.ui.outputDirEdit.setText(selected_dir)
            self.addLogMessage(f"📂 Output directory: {selected_dir}")
    
    @Slot()
    def startConversion(self):
        """Start document conversion."""
        if not self.input_file_path or not self.input_file_path.exists():
            QMessageBox.warning(self, "Error", "Please select a valid input file")
            return
        
        # Get output format
        format_text = self.ui.formatComboBox.currentText().lower()
        if format_text == "latex":
            format_text = "latex"
        
        try:
            output_format = OutputFormat(format_text)
        except ValueError:
            QMessageBox.warning(self, "Error", f"Unsupported output format: {format_text}")
            return
        
        # Determine output path
        output_dir = self.ui.outputDirEdit.text().strip()
        if not output_dir:
            output_dir = str(self.input_file_path.parent)
        
        output_path = Path(output_dir) / f"{self.input_file_path.stem}.{output_format.value}"
        
        # Create conversion profile
        profile = ConversionProfile(
            input_path=self.input_file_path,
            output_path=output_path,
            output_format=output_format
        )
        
        # Start worker thread
        self.startWorkerConversion(profile)
    
    def startWorkerConversion(self, profile: ConversionProfile):
        """Start conversion using worker thread."""
        # Disable convert button
        self.ui.convertButton.setEnabled(False)
        self.ui.convertButton.setText("Converting...")
        
        # Reset progress
        self.ui.progressBar.setValue(0)
        self.ui.statusLabel.setText("Starting conversion...")
        
        # Create and start worker
        self.current_worker = ConversionWorker(profile, self)
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
                self, 
                "Success", 
                f"File converted successfully!\n\nOutput saved to:\n{result.output_path}"
            )
        else:
            self.addLogMessage(f"❌ Conversion failed: {result.error_message}")
            QMessageBox.critical(
                self,
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
    
    @Slot()
    def updateConvertButtonState(self):
        """Update convert button enabled state."""
        has_input = bool(self.ui.inputFileEdit.text().strip())
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
            self,
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
                self,
                "Pandoc Not Found",
                """Pandoc was not found on your system.
                
Please install Pandoc from:
https://pandoc.org/installing.html

The application will not work without Pandoc."""
            )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop any running conversion
        if self.current_worker and self.current_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Conversion in Progress",
                "A conversion is currently running. Do you want to close anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            # Terminate worker if user confirms
            self.current_worker.terminate()
            self.current_worker.wait(3000)  # Wait up to 3 seconds
        
        self.addLogMessage("👋 Closing Pandoc UI")
        event.accept()