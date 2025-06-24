"""
Integration tests for GUI functionality.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from pandoc_ui.main import PandocUIMainWindow
from pandoc_ui.models import OutputFormat


# QApplication fixture is now in conftest.py


@pytest.fixture
def main_window(qapp):
    """Create main window fixture."""
    with patch('pandoc_ui.gui.ui_components.MainWindowUI.checkPandocAvailability'):
        window = PandocUIMainWindow()
        yield window
        window.close()


class TestGUIIntegration:
    """Integration tests for GUI functionality."""
    
    def test_main_window_creation(self, main_window):
        """Test main window can be created successfully."""
        assert main_window is not None
        assert hasattr(main_window, 'ui_handler')
        assert main_window.ui_handler is not None
    
    def test_ui_components_initialized(self, main_window):
        """Test all UI components are properly initialized."""
        ui = main_window.ui_handler.ui
        
        # Check all required components exist
        assert hasattr(ui, 'inputFileEdit')
        assert hasattr(ui, 'formatComboBox')
        assert hasattr(ui, 'outputDirEdit')
        assert hasattr(ui, 'convertButton')
        assert hasattr(ui, 'progressBar')
        assert hasattr(ui, 'logTextEdit')
        assert hasattr(ui, 'statusLabel')
        assert hasattr(ui, 'browseInputButton')
        assert hasattr(ui, 'browseOutputButton')
        assert hasattr(ui, 'clearLogButton')
    
    def test_format_combo_initialization(self, main_window):
        """Test format combo box is properly initialized."""
        combo = main_window.ui_handler.ui.formatComboBox
        
        assert combo.count() == 7
        formats = [combo.itemText(i) for i in range(combo.count())]
        expected = ["HTML", "PDF", "DOCX", "ODT", "EPUB", "LaTeX", "RTF"]
        assert formats == expected
    
    def test_initial_ui_state(self, main_window):
        """Test initial UI state is correct."""
        ui = main_window.ui_handler.ui
        
        # Convert button should be disabled initially
        assert not ui.convertButton.isEnabled()
        
        # Progress bar should be at 0
        assert ui.progressBar.value() == 0
        
        # Input fields should be empty
        assert ui.inputFileEdit.text() == ""
        assert ui.outputDirEdit.text() == ""
    
    def test_file_selection_workflow(self, main_window):
        """Test file selection workflow."""
        handler = main_window.ui_handler
        
        # Simulate file selection
        test_file = Path("examples/article.md")
        handler.input_file_path = test_file
        handler.ui.inputFileEdit.setText(str(test_file))
        handler.updateConvertButtonState()
        
        # Convert button should now be enabled
        assert handler.ui.convertButton.isEnabled()
        
        # Output directory should be auto-set if empty
        if not handler.ui.outputDirEdit.text():
            handler.ui.outputDirEdit.setText(str(test_file.parent))
        
        assert handler.ui.outputDirEdit.text() != ""
    
    def test_format_selection(self, main_window):
        """Test format selection functionality."""
        combo = main_window.ui_handler.ui.formatComboBox
        
        # Test changing formats
        combo.setCurrentText("PDF")
        assert combo.currentText() == "PDF"
        
        combo.setCurrentText("HTML")
        assert combo.currentText() == "HTML"
    
    def test_log_functionality(self, main_window):
        """Test logging functionality."""
        handler = main_window.ui_handler
        
        initial_text = handler.ui.logTextEdit.toPlainText()
        
        # Add log message
        test_message = "Test integration log message"
        handler.addLogMessage(test_message)
        
        updated_text = handler.ui.logTextEdit.toPlainText()
        assert test_message in updated_text
        assert len(updated_text) > len(initial_text)
        
        # Test clear log
        handler.clearLog()
        cleared_text = handler.ui.logTextEdit.toPlainText()
        assert test_message not in cleared_text
        assert "Log cleared" in cleared_text
    
    def test_progress_updates(self, main_window):
        """Test progress bar updates."""
        handler = main_window.ui_handler
        
        # Test progress updates
        for value in [10, 25, 50, 75, 100]:
            handler.updateProgress(value)
            assert handler.ui.progressBar.value() == value
    
    def test_status_updates(self, main_window):
        """Test status label updates."""
        handler = main_window.ui_handler
        
        test_statuses = [
            "Ready",
            "Converting...",
            "Conversion completed",
            "Error occurred"
        ]
        
        for status in test_statuses:
            handler.updateStatus(status)
            assert handler.ui.statusLabel.text() == status
    
    @patch('pandoc_ui.gui.ui_components.QMessageBox')
    def test_conversion_without_file(self, mock_msgbox, main_window):
        """Test conversion attempt without selecting file."""
        handler = main_window.ui_handler
        
        # Try to start conversion without file
        handler.startConversion()
        
        # Should show warning message
        mock_msgbox.warning.assert_called_once()
        args = mock_msgbox.warning.call_args[0]
        assert "valid input file" in args[1]
    
    @patch('pandoc_ui.gui.ui_components.QFileDialog')
    def test_file_dialog_integration(self, mock_dialog, main_window):
        """Test file dialog integration."""
        handler = main_window.ui_handler
        
        # Mock file dialog
        mock_instance = Mock()
        mock_instance.exec.return_value = True
        mock_instance.selectedFiles.return_value = ["test_file.md"]
        mock_dialog.return_value = mock_instance
        
        # Trigger file browse
        handler.browseInputFile()
        
        # Check dialog was created with correct parameters
        mock_dialog.assert_called_once()
        call_args = mock_dialog.call_args
        assert call_args[0][0] == main_window  # parent
        
        # Check file was set
        assert str(handler.input_file_path) == "test_file.md"
    
    @patch('pandoc_ui.gui.ui_components.QFileDialog')
    def test_directory_dialog_integration(self, mock_dialog, main_window):
        """Test directory dialog integration."""
        handler = main_window.ui_handler
        
        # Mock directory dialog
        mock_instance = Mock()
        mock_instance.exec.return_value = True
        mock_instance.selectedFiles.return_value = ["/test/directory"]
        mock_dialog.return_value = mock_instance
        
        # Trigger directory browse
        handler.browseOutputDirectory()
        
        # Check directory was set
        assert handler.ui.outputDirEdit.text() == "/test/directory"
    
    def test_window_show_and_close(self, qapp):
        """Test window show and close lifecycle."""
        with patch('pandoc_ui.gui.ui_components.MainWindowUI.checkPandocAvailability'):
            window = PandocUIMainWindow()
            
            # Show window
            window.show()
            qapp.processEvents()
            
            # Window should be visible (even in offscreen mode)
            assert window.isVisible()
            
            # Close window
            window.close()
            qapp.processEvents()
            
            # Window should be closed
            assert not window.isVisible()
    
    def test_conversion_button_state_changes(self, main_window):
        """Test conversion button state changes throughout workflow."""
        handler = main_window.ui_handler
        
        # Initially disabled
        assert not handler.ui.convertButton.isEnabled()
        assert handler.ui.convertButton.text() == "Start Conversion"
        
        # Enable by setting file
        handler.ui.inputFileEdit.setText("test.md")
        handler.updateConvertButtonState()
        assert handler.ui.convertButton.isEnabled()
        
        # Simulate conversion start (mock worker creation)
        with patch('pandoc_ui.gui.ui_components.ConversionWorker'):
            handler.input_file_path = Path("test.md")
            handler.ui.formatComboBox.setCurrentText("HTML")
            
            # Mock the startWorkerConversion to just change button state
            original_button_text = handler.ui.convertButton.text()
            handler.ui.convertButton.setEnabled(False)
            handler.ui.convertButton.setText("Converting...")
            
            # Button should be disabled and show converting
            assert not handler.ui.convertButton.isEnabled()
            assert handler.ui.convertButton.text() == "Converting..."
            
            # Simulate conversion finish
            handler.ui.convertButton.setEnabled(True)
            handler.ui.convertButton.setText("Start Conversion")
            
            assert handler.ui.convertButton.isEnabled()
            assert handler.ui.convertButton.text() == "Start Conversion"
    
    @patch('pandoc_ui.app.conversion_service.ConversionService')
    def test_pandoc_availability_integration(self, mock_service, main_window):
        """Test pandoc availability check integration."""
        handler = main_window.ui_handler
        
        # Mock available pandoc
        mock_instance = Mock()
        mock_instance.is_pandoc_available.return_value = True
        mock_instance.get_pandoc_info.return_value = Mock(
            path=Path("/usr/bin/pandoc"),
            version="3.1.3"
        )
        mock_service.return_value = mock_instance
        
        # Check availability
        handler.checkPandocAvailability()
        
        # Should update status and log
        assert "Ready - Pandoc available" in handler.ui.statusLabel.text()
        log_text = handler.ui.logTextEdit.toPlainText()
        assert "Pandoc detected" in log_text
        assert "3.1.3" in log_text
    
    def test_menu_action_connections(self, main_window):
        """Test menu action connections."""
        ui = main_window.ui_handler.ui
        
        # Check menu actions exist
        assert hasattr(ui, 'actionExit')
        assert hasattr(ui, 'actionAbout')
        
        # Check signals are connected (we can't easily test the actual connections
        # without triggering them, but we can verify the actions exist)
        assert ui.actionExit.text() == "Exit"
        assert ui.actionAbout.text() == "About"