"""
Tests for GUI UI components.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

from pandoc_ui.gui.ui_components import MainWindowUI
from pandoc_ui.models import ConversionProfile, OutputFormat


# QApplication fixture is now in conftest.py


@pytest.fixture
def main_window(qapp):
    """Create main window fixture."""
    window = QMainWindow()
    yield window
    window.close()


@pytest.fixture
def ui_handler(main_window):
    """Create UI handler fixture."""
    with patch.object(MainWindowUI, 'checkPandocAvailability'):
        handler = MainWindowUI(main_window)
        return handler


class TestMainWindowUI:
    """Test cases for MainWindowUI component."""
    
    def test_init(self, ui_handler):
        """Test UI handler initialization."""
        assert ui_handler.main_window is not None
        assert ui_handler.current_worker is None
        assert ui_handler.input_file_path is None
        assert hasattr(ui_handler, 'ui')
    
    def test_ui_components_exist(self, ui_handler):
        """Test that all required UI components exist."""
        assert hasattr(ui_handler.ui, 'inputFileEdit')
        assert hasattr(ui_handler.ui, 'formatComboBox')
        assert hasattr(ui_handler.ui, 'outputDirEdit')
        assert hasattr(ui_handler.ui, 'convertButton')
        assert hasattr(ui_handler.ui, 'progressBar')
        assert hasattr(ui_handler.ui, 'logTextEdit')
        assert hasattr(ui_handler.ui, 'statusLabel')
    
    def test_format_combo_box_contents(self, ui_handler):
        """Test format combo box has correct options."""
        combo = ui_handler.ui.formatComboBox
        assert combo.count() == 7
        
        formats = [combo.itemText(i) for i in range(combo.count())]
        expected = ["HTML", "PDF", "DOCX", "ODT", "EPUB", "LaTeX", "RTF"]
        assert formats == expected
    
    def test_convert_button_initial_state(self, ui_handler):
        """Test convert button initial state."""
        # Should be disabled initially (no input file)
        assert not ui_handler.ui.convertButton.isEnabled()
    
    def test_input_file_selection(self, ui_handler):
        """Test input file selection logic."""
        test_file = Path("examples/article.md")
        
        # Simulate file selection
        ui_handler.input_file_path = test_file
        ui_handler.ui.inputFileEdit.setText(str(test_file))
        ui_handler.updateConvertButtonState()
        
        # Convert button should now be enabled
        assert ui_handler.ui.convertButton.isEnabled()
        assert ui_handler.input_file_path == test_file
    
    def test_log_message_functionality(self, ui_handler):
        """Test log message addition."""
        initial_text = ui_handler.ui.logTextEdit.toPlainText()
        
        ui_handler.addLogMessage("Test log message")
        
        updated_text = ui_handler.ui.logTextEdit.toPlainText()
        assert "Test log message" in updated_text
        assert len(updated_text) > len(initial_text)
    
    def test_clear_log(self, ui_handler):
        """Test log clearing functionality."""
        # Add some log messages
        ui_handler.addLogMessage("Message 1")
        ui_handler.addLogMessage("Message 2")
        
        # Clear log
        ui_handler.clearLog()
        
        # Should only contain the "Log cleared" message
        text = ui_handler.ui.logTextEdit.toPlainText()
        assert "Message 1" not in text
        assert "Message 2" not in text
        assert "Log cleared" in text
    
    def test_format_change_handling(self, ui_handler):
        """Test format change handling."""
        # Change format
        ui_handler.ui.formatComboBox.setCurrentText("PDF")
        ui_handler.onFormatChanged()
        
        # Check log was updated
        log_text = ui_handler.ui.logTextEdit.toPlainText()
        assert "PDF" in log_text
    
    def test_progress_update(self, ui_handler):
        """Test progress bar updates."""
        ui_handler.updateProgress(50)
        assert ui_handler.ui.progressBar.value() == 50
        
        ui_handler.updateProgress(100)
        assert ui_handler.ui.progressBar.value() == 100
    
    def test_status_update(self, ui_handler):
        """Test status label updates."""
        test_status = "Test status message"
        ui_handler.updateStatus(test_status)
        assert ui_handler.ui.statusLabel.text() == test_status
    
    @patch('pandoc_ui.gui.ui_components.QFileDialog')
    def test_browse_input_file(self, mock_dialog, ui_handler):
        """Test input file browsing."""
        # Mock file dialog
        mock_instance = Mock()
        mock_instance.exec.return_value = True
        mock_instance.selectedFiles.return_value = ["examples/article.md"]
        mock_dialog.return_value = mock_instance
        
        # Trigger browse
        ui_handler.browseInputFile()
        
        # Check file was set
        assert str(ui_handler.input_file_path) == "examples/article.md"
        assert ui_handler.ui.inputFileEdit.text() == "examples/article.md"
    
    @patch('pandoc_ui.gui.ui_components.QFileDialog')
    def test_browse_output_directory(self, mock_dialog, ui_handler):
        """Test output directory browsing."""
        # Mock directory dialog
        mock_instance = Mock()
        mock_instance.exec.return_value = True
        mock_instance.selectedFiles.return_value = ["/test/output/dir"]
        mock_dialog.return_value = mock_instance
        
        # Trigger browse
        ui_handler.browseOutputDirectory()
        
        # Check directory was set
        assert ui_handler.ui.outputDirEdit.text() == "/test/output/dir"
    
    @patch('pandoc_ui.gui.ui_components.QMessageBox')
    def test_start_conversion_no_file(self, mock_msgbox, ui_handler):
        """Test conversion start with no input file."""
        # Try to start conversion without file
        ui_handler.startConversion()
        
        # Should show warning
        mock_msgbox.warning.assert_called_once()
    
    def test_convert_button_state_updates(self, ui_handler):
        """Test convert button state updates correctly."""
        # Initially disabled
        assert not ui_handler.ui.convertButton.isEnabled()
        
        # Set input file
        ui_handler.ui.inputFileEdit.setText("test.md")
        ui_handler.updateConvertButtonState()
        
        # Should be enabled
        assert ui_handler.ui.convertButton.isEnabled()
        
        # Clear input
        ui_handler.ui.inputFileEdit.setText("")
        ui_handler.updateConvertButtonState()
        
        # Should be disabled again
        assert not ui_handler.ui.convertButton.isEnabled()
    
    @patch('pandoc_ui.app.conversion_service.ConversionService')
    def test_pandoc_availability_check_available(self, mock_service, ui_handler):
        """Test pandoc availability check when available."""
        # Mock service
        mock_instance = Mock()
        mock_instance.is_pandoc_available.return_value = True
        mock_instance.get_pandoc_info.return_value = Mock(
            path=Path("/usr/bin/pandoc"),
            version="3.1.3"
        )
        mock_service.return_value = mock_instance
        
        # Check availability
        ui_handler.checkPandocAvailability()
        
        # Should show success message
        log_text = ui_handler.ui.logTextEdit.toPlainText()
        assert "Pandoc detected" in log_text
        assert "3.1.3" in log_text
    
    @patch('pandoc_ui.app.conversion_service.ConversionService')
    @patch('pandoc_ui.gui.ui_components.QMessageBox')
    def test_pandoc_availability_check_not_available(self, mock_msgbox, mock_service, ui_handler):
        """Test pandoc availability check when not available."""
        # Mock service
        mock_instance = Mock()
        mock_instance.is_pandoc_available.return_value = False
        mock_service.return_value = mock_instance
        
        # Check availability
        ui_handler.checkPandocAvailability()
        
        # Should show error message and warning dialog
        log_text = ui_handler.ui.logTextEdit.toPlainText()
        assert "Pandoc not found" in log_text
        mock_msgbox.warning.assert_called_once()
    
    def test_window_close_handling_no_worker(self, ui_handler):
        """Test window close handling with no active worker."""
        result = ui_handler.handleWindowClose()
        assert result is True
    
    @patch('pandoc_ui.gui.ui_components.QMessageBox')
    def test_window_close_handling_with_worker(self, mock_msgbox, ui_handler):
        """Test window close handling with active worker."""
        # Mock worker
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        mock_worker.terminate = Mock()
        mock_worker.wait = Mock()
        ui_handler.current_worker = mock_worker
        
        # Mock user chooses to close anyway
        mock_msgbox.question.return_value = mock_msgbox.Yes
        
        result = ui_handler.handleWindowClose()
        
        assert result is True
        mock_worker.terminate.assert_called_once()
        mock_worker.wait.assert_called_once_with(3000)