"""
End-to-end integration tests.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from pandoc_ui.main import PandocUIMainWindow
from pandoc_ui.models import OutputFormat

# QApplication fixture is now in conftest.py


@pytest.fixture
def main_window(qapp):
    """Create main window fixture."""
    with patch("pandoc_ui.gui.ui_components.MainWindowUI.checkPandocAvailability"):
        window = PandocUIMainWindow()
        yield window
        window.close()


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample markdown file for testing."""
    content = """# Test Document

This is a test markdown file for end-to-end testing.

## Features

- Lists work
- **Bold text** works
- *Italic text* works

### Code blocks

```python
def hello():
    print("Hello, World!")
```

## Conclusion

This document tests basic markdown conversion.
"""

    file_path = tmp_path / "test_document.md"
    file_path.write_text(content)
    return file_path


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_gui_workflow_mock(self, main_window, sample_markdown_file):
        """Test complete GUI workflow with mocked conversion."""
        handler = main_window.ui_handler

        # Step 1: Set input file
        handler.input_file_path = sample_markdown_file
        handler.ui.inputPathEdit.setText(str(sample_markdown_file))

        # Step 2: Set output directory
        output_dir = sample_markdown_file.parent
        handler.ui.outputDirEdit.setText(str(output_dir))

        # Step 3: Select format
        handler.ui.formatComboBox.setCurrentText("HTML")

        # Step 4: Update button state
        handler.updateConvertButtonState()
        assert handler.ui.convertButton.isEnabled()

        # Step 5: Mock conversion process
        with patch("pandoc_ui.gui.ui_components.ConversionWorker") as mock_worker_class:
            mock_worker = Mock()
            mock_worker.start = Mock()
            mock_worker.isRunning.return_value = False
            mock_worker_class.return_value = mock_worker

            # Start conversion
            handler.startConversion()

            # Verify worker was created and started
            mock_worker_class.assert_called_once()
            mock_worker.start.assert_called_once()

            # Verify UI state during conversion
            # (Note: startWorkerConversion changes these immediately)
            # These would be reset by onWorkerFinished()

    def test_file_selection_to_conversion_ready(self, main_window, sample_markdown_file):
        """Test file selection makes conversion ready."""
        handler = main_window.ui_handler

        # Initially not ready
        assert not handler.ui.convertButton.isEnabled()

        # Select file
        handler.input_file_path = sample_markdown_file
        handler.ui.inputPathEdit.setText(str(sample_markdown_file))
        handler.updateConvertButtonState()

        # Now ready for conversion
        assert handler.ui.convertButton.isEnabled()

        # Verify file info in log
        # The checkPandocAvailability is mocked, so we mainly check UI state

    def test_format_selection_workflow(self, main_window, sample_markdown_file):
        """Test format selection affects conversion profile."""
        handler = main_window.ui_handler

        # Set up for conversion
        handler.input_file_path = sample_markdown_file
        handler.ui.inputPathEdit.setText(str(sample_markdown_file))

        # Test different formats
        formats_to_test = ["HTML", "PDF", "Microsoft Word"]

        for format_name in formats_to_test:
            handler.ui.formatComboBox.setCurrentText(format_name)

            # Trigger format change handler
            handler.onFormatChanged()

            # Check log message
            log_text = handler.ui.logTextEdit.toPlainText()
            assert format_name in log_text

    def test_pandoc_detection_workflow(self, main_window):
        """Test pandoc detection affects UI state."""
        handler = main_window.ui_handler

        # Test direct status and log updates (simulating successful pandoc check)
        handler.ui.statusLabel.setText("Ready - Pandoc available")
        handler.addLogMessage("✅ Pandoc detected: /usr/bin/pandoc (v3.1.3)")

        # Check UI reflects pandoc availability
        status_text = handler.ui.statusLabel.text()
        assert "Ready - Pandoc available" in status_text

        log_text = handler.ui.logTextEdit.toPlainText()
        assert "Pandoc detected" in log_text
        assert "3.1.3" in log_text

    def test_progress_and_logging_workflow(self, main_window):
        """Test progress and logging throughout workflow."""
        handler = main_window.ui_handler

        # Test progress updates
        progress_values = [0, 25, 50, 75, 100]
        for value in progress_values:
            handler.updateProgress(value)
            assert handler.ui.progressBar.value() == value

        # Test status updates
        status_messages = ["Ready", "Validating input...", "Converting...", "Conversion completed"]

        for status in status_messages:
            handler.updateStatus(status)
            assert handler.ui.statusLabel.text() == status

        # Test log accumulation
        initial_log_length = len(handler.ui.logTextEdit.toPlainText())

        log_messages = [
            "Starting conversion",
            "Pandoc detected",
            "Input file validated",
            "Conversion completed",
        ]

        for message in log_messages:
            handler.addLogMessage(message)

        final_log = handler.ui.logTextEdit.toPlainText()
        assert len(final_log) > initial_log_length

        # All messages should be in log
        for message in log_messages:
            assert message in final_log

    def test_error_handling_workflow(self, main_window):
        """Test error handling throughout workflow."""
        handler = main_window.ui_handler

        # Test invalid file handling
        with patch("pandoc_ui.gui.ui_components.QMessageBox") as mock_msgbox:
            # Try conversion without file
            handler.startConversion()
            mock_msgbox.warning.assert_called_once()

        # Test file validation
        handler.input_file_path = Path("nonexistent_file.md")
        handler.ui.inputPathEdit.setText("nonexistent_file.md")

        with patch("pandoc_ui.gui.ui_components.QMessageBox") as mock_msgbox:
            handler.startConversion()
            mock_msgbox.warning.assert_called_once()

    def test_window_lifecycle(self, qapp):
        """Test complete window lifecycle."""
        # Create window
        with patch("pandoc_ui.gui.ui_components.MainWindowUI.checkPandocAvailability"):
            window = PandocUIMainWindow()

            # Show window
            window.show()
            qapp.processEvents()
            assert window.isVisible()

            # Test window has proper title
            assert "Pandoc UI" in window.windowTitle()

            # Test UI handler is initialized
            assert window.ui_handler is not None

            # Test close event handling
            can_close = window.ui_handler.handleWindowClose()
            assert can_close is True

            # Close window
            window.close()
            qapp.processEvents()

    def test_conversion_profile_creation(self, main_window, sample_markdown_file):
        """Test conversion profile creation from UI inputs."""
        handler = main_window.ui_handler

        # Set up inputs
        handler.input_file_path = sample_markdown_file
        handler.ui.inputPathEdit.setText(str(sample_markdown_file))
        handler.ui.outputDirEdit.setText(str(sample_markdown_file.parent))
        handler.ui.formatComboBox.setCurrentText("PDF")

        # Mock the worker creation to capture the profile
        captured_profile = None

        def mock_worker_init(profile, service=None, parent=None):
            nonlocal captured_profile
            captured_profile = profile
            mock_worker = Mock()
            mock_worker.start = Mock()
            return mock_worker

        with patch("pandoc_ui.gui.ui_components.ConversionWorker", side_effect=mock_worker_init):
            handler.startConversion()

            # Verify profile was created correctly
            assert captured_profile is not None
            assert captured_profile.input_path == sample_markdown_file
            assert captured_profile.output_format == OutputFormat.PDF
            assert captured_profile.output_path.suffix == ".pdf"
            assert captured_profile.output_path.parent == sample_markdown_file.parent

    def test_ui_state_consistency(self, main_window, sample_markdown_file):
        """Test UI state remains consistent throughout operations."""
        handler = main_window.ui_handler

        # Initial state
        assert not handler.ui.convertButton.isEnabled()
        assert handler.ui.progressBar.value() == 0
        assert handler.ui.statusLabel.text() in ["Ready", ""]

        # After file selection
        handler.input_file_path = sample_markdown_file
        handler.ui.inputPathEdit.setText(str(sample_markdown_file))
        handler.updateConvertButtonState()

        assert handler.ui.convertButton.isEnabled()
        assert handler.ui.convertButton.text() == "Start Conversion"

        # During conversion (simulated)
        handler.ui.convertButton.setEnabled(False)
        handler.ui.convertButton.setText("Converting...")
        handler.updateProgress(50)
        handler.updateStatus("Converting...")

        assert not handler.ui.convertButton.isEnabled()
        assert handler.ui.convertButton.text() == "Converting..."
        assert handler.ui.progressBar.value() == 50
        assert handler.ui.statusLabel.text() == "Converting..."

        # After conversion (simulated)
        handler.ui.convertButton.setEnabled(True)
        handler.ui.convertButton.setText("Start Conversion")
        handler.updateProgress(100)
        handler.updateStatus("Conversion completed")

        assert handler.ui.convertButton.isEnabled()
        assert handler.ui.convertButton.text() == "Start Conversion"
        assert handler.ui.progressBar.value() == 100
        assert handler.ui.statusLabel.text() == "Conversion completed"
