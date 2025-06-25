"""
Command preview widget for pandoc-ui.
Shows pandoc command preview with custom arguments support.
"""

import logging
import shlex
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..infra.translation_manager import tr

logger = logging.getLogger(__name__)


class CommandPreviewWidget(QWidget):
    """Widget for previewing pandoc commands with custom arguments."""
    
    # Signal emitted when custom arguments change
    custom_args_changed = Signal(str)
    
    def __init__(self, parent=None):
        """Initialize command preview widget."""
        super().__init__(parent)
        
        self.custom_args = ""
        self.current_profile = None
        self.current_input_files = []
        self.current_output_dir = None
        
        # Timer for debounced updates
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._update_preview)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Command preview group (title set in main_window.ui)
        preview_group = QGroupBox()
        preview_layout = QVBoxLayout(preview_group)
        
        # Info label
        self.info_label = QLabel(tr("Preview of pandoc command that will be executed:"))
        self.info_label.setWordWrap(True)
        preview_layout.addWidget(self.info_label)
        
        # Command display
        self.command_display = QTextEdit()
        self.command_display.setReadOnly(True)
        self.command_display.setMaximumHeight(120)
        self.command_display.setMinimumHeight(80)
        
        # Use monospace font for command display
        font = QFont("Consolas", 9)  # Windows
        if not font.exactMatch():
            font = QFont("Monaco", 9)  # macOS
        if not font.exactMatch():
            font = QFont("DejaVu Sans Mono", 9)  # Linux
        if not font.exactMatch():
            font = QFont("monospace", 9)  # Generic fallback
        
        self.command_display.setFont(font)
        self.command_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                color: #212529;
            }
        """)
        
        preview_layout.addWidget(self.command_display)
        
        # Custom arguments section
        args_group = QGroupBox(tr("Custom Arguments"))
        args_layout = QVBoxLayout(args_group)
        
        # Help text
        help_label = QLabel(tr("Add custom pandoc arguments (e.g., --metadata title=\"My Title\" --toc):"))
        help_label.setWordWrap(True)
        args_layout.addWidget(help_label)
        
        # Custom arguments input
        args_input_layout = QHBoxLayout()
        
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText(tr("Enter custom pandoc arguments..."))
        self.args_input.setToolTip(tr("Additional arguments to append to the pandoc command"))
        args_input_layout.addWidget(self.args_input)
        
        # Clear button
        self.clear_args_btn = QPushButton(tr("Clear"))
        self.clear_args_btn.setToolTip(tr("Clear custom arguments"))
        self.clear_args_btn.setMaximumWidth(80)
        args_input_layout.addWidget(self.clear_args_btn)
        
        args_layout.addLayout(args_input_layout)
        
        # Validation label
        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: #dc3545; font-size: 11px;")
        self.validation_label.hide()
        args_layout.addWidget(self.validation_label)
        
        # Add groups to main layout
        layout.addWidget(preview_group)
        layout.addWidget(args_group)
        
        # Initial state
        self._update_preview()
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.args_input.textChanged.connect(self._on_args_changed)
        self.clear_args_btn.clicked.connect(self._clear_args)
    
    def _on_args_changed(self, text: str):
        """Handle custom arguments text change."""
        self.custom_args = text.strip()
        
        # Validate arguments
        self._validate_args()
        
        # Debounced update
        self.update_timer.start(300)  # Update after 300ms of no changes
        
        # Emit signal
        self.custom_args_changed.emit(self.custom_args)
    
    def _clear_args(self):
        """Clear custom arguments."""
        self.args_input.clear()
    
    def _validate_args(self):
        """Validate custom arguments format."""
        if not self.custom_args:
            self.validation_label.hide()
            return True
        
        try:
            # Try to parse the arguments using shell-like parsing
            shlex.split(self.custom_args)
            self.validation_label.hide()
            return True
        except ValueError as e:
            self.validation_label.setText(tr("Invalid argument format: %s") % str(e))
            self.validation_label.show()
            return False
    
    def set_conversion_info(self, profile, input_files: list, output_dir: Optional[Path] = None):
        """
        Set conversion information for preview.
        
        Args:
            profile: Conversion profile
            input_files: List of input file paths
            output_dir: Output directory (optional)
        """
        self.current_profile = profile
        self.current_input_files = input_files
        self.current_output_dir = output_dir
        
        self._update_preview()
    
    def _update_preview(self):
        """Update the command preview display."""
        try:
            command = self._build_preview_command()
            self.command_display.setPlainText(command)
            
            # Update info label based on file count
            if len(self.current_input_files) == 0:
                info_text = tr("No files selected.")
            elif len(self.current_input_files) == 1:
                info_text = tr("Command for single file conversion:")
            else:
                info_text = tr("Sample command for batch conversion (%d files):") % len(self.current_input_files)
            
            self.info_label.setText(info_text)
            
        except Exception as e:
            logger.error(f"Error updating command preview: {e}")
            self.command_display.setPlainText(tr("Error generating command preview"))
    
    def _build_preview_command(self) -> str:
        """
        Build preview command string.
        
        Returns:
            Command string for preview
        """
        if not self.current_profile or not self.current_input_files:
            return tr("# No conversion profile or files selected")
        
        # Use first file as example for batch operations
        input_file = Path(self.current_input_files[0])
        
        # Build basic command
        command_parts = ["pandoc"]
        
        # Input format
        if hasattr(self.current_profile, 'input_format') and self.current_profile.input_format:
            command_parts.extend(["-f", self.current_profile.input_format.value])
        
        # Input file
        command_parts.append(str(input_file))
        
        # Output format
        if hasattr(self.current_profile, 'output_format') and self.current_profile.output_format:
            command_parts.extend(["-t", self.current_profile.output_format.value])
        
        # Output file
        if self.current_output_dir:
            output_file = self.current_output_dir / f"{input_file.stem}.{self._get_output_extension()}"
        else:
            output_file = input_file.parent / f"{input_file.stem}.{self._get_output_extension()}"
        
        command_parts.extend(["-o", str(output_file)])
        
        # Additional options
        if hasattr(self.current_profile, 'standalone') and self.current_profile.standalone:
            command_parts.append("--standalone")
        
        # Custom arguments
        if self.custom_args and self._validate_args():
            try:
                custom_parts = shlex.split(self.custom_args)
                command_parts.extend(custom_parts)
            except ValueError:
                # If parsing fails, add as comment
                pass
        
        # Format command for display
        command_str = " ".join(command_parts)
        
        # Add batch info if multiple files
        if len(self.current_input_files) > 1:
            command_str += "\n\n# " + tr("This command will be executed for each of the %d selected files") % len(self.current_input_files)
        
        # Add custom args validation error if present
        if self.custom_args and not self._validate_args():
            warning_msg = tr('Warning: Custom arguments contain syntax errors')
            command_str += f"\n\n# {warning_msg}"
        
        return command_str
    
    def _get_output_extension(self) -> str:
        """Get output file extension based on output format."""
        if not hasattr(self.current_profile, 'output_format') or not self.current_profile.output_format:
            return "out"
        
        format_extensions = {
            "html": "html",
            "html5": "html",
            "pdf": "pdf",
            "docx": "docx",
            "odt": "odt",
            "epub": "epub",
            "latex": "tex",
            "markdown": "md",
            "rst": "rst",
            "plain": "txt",
        }
        
        format_name = self.current_profile.output_format.value
        return format_extensions.get(format_name, format_name)
    
    def get_custom_args(self) -> str:
        """Get current custom arguments."""
        return self.custom_args
    
    def set_custom_args(self, args: str):
        """Set custom arguments."""
        self.args_input.setText(args)
    
    def retranslateUi(self):
        """Retranslate UI elements (for language switching)."""
        # This will be called when language changes
        # Qt Designer generated classes have this method
        pass