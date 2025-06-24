"""
Data models for pandoc-ui application.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum


class OutputFormat(Enum):
    """Supported output formats."""
    HTML = "html"
    PDF = "pdf"
    DOCX = "docx" 
    ODT = "odt"
    EPUB = "epub"
    LATEX = "latex"
    RTF = "rtf"


@dataclass
class ConversionProfile:
    """Configuration for a pandoc conversion."""
    input_path: Path
    output_path: Optional[Path] = None
    output_format: OutputFormat = OutputFormat.HTML
    options: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = {}
        
        # Auto-generate output path if not provided
        if self.output_path is None:
            suffix = f".{self.output_format.value}"
            self.output_path = self.input_path.with_suffix(suffix)


@dataclass 
class ConversionResult:
    """Result of a pandoc conversion operation."""
    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    command: Optional[str] = None