"""
Worker thread for performing conversions without blocking the GUI.
"""

from PySide6.QtCore import QThread, Signal

from ..app.conversion_service import ConversionService
from ..models import ConversionProfile, ConversionResult


class ConversionWorker(QThread):
    """Worker thread for document conversion."""

    # Signals
    progress_updated = Signal(int)  # Progress percentage
    status_updated = Signal(str)  # Status message
    log_message = Signal(str)  # Log message
    conversion_finished = Signal(ConversionResult)  # Final result

    def __init__(self, profile: ConversionProfile, service=None, parent=None):
        """
        Initialize worker with conversion profile.

        Args:
            profile: Conversion configuration
            service: ConversionService instance (optional, creates new if None)
            parent: Parent QObject
        """
        super().__init__(parent)
        self.profile = profile
        self.service = service or ConversionService()

    def run(self):
        """Execute conversion in background thread."""
        try:
            self.status_updated.emit("Initializing conversion...")
            self.log_message.emit(f"🚀 Starting conversion: {self.profile.input_path.name}")
            self.progress_updated.emit(10)

            # Check pandoc availability
            if not self.service.is_pandoc_available():
                result = ConversionResult(
                    success=False, error_message="Pandoc is not available on this system"
                )
                self.conversion_finished.emit(result)
                return

            pandoc_info = self.service.get_pandoc_info()
            self.log_message.emit(
                f"✅ Pandoc detected: {pandoc_info.path} (v{pandoc_info.version})"
            )
            self.progress_updated.emit(25)

            # Validate input file
            self.status_updated.emit("Validating input file...")
            if not self.service.validate_input_file(self.profile.input_path):
                result = ConversionResult(
                    success=False, error_message=f"Invalid input file: {self.profile.input_path}"
                )
                self.conversion_finished.emit(result)
                return

            self.log_message.emit(f"📄 Input file validated: {self.profile.input_path}")
            self.progress_updated.emit(40)

            # Perform conversion
            self.status_updated.emit(f"Converting to {self.profile.output_format.value.upper()}...")
            self.log_message.emit(f"🔄 Converting to {self.profile.output_format.value}...")
            self.progress_updated.emit(50)

            result = self.service.convert(self.profile)

            if result.success:
                self.progress_updated.emit(90)
                self.log_message.emit(f"✅ Conversion completed in {result.duration_seconds:.2f}s")
                self.log_message.emit(f"📁 Output saved to: {result.output_path}")

                # Verify output file
                if result.output_path and result.output_path.exists():
                    file_size = result.output_path.stat().st_size
                    self.log_message.emit(f"📊 Output file size: {file_size:,} bytes")
                    self.status_updated.emit("Conversion completed successfully!")
                else:
                    self.log_message.emit("⚠️ Output file not found after conversion")
                    self.status_updated.emit("Conversion completed with warnings")

                self.progress_updated.emit(100)
            else:
                self.log_message.emit(f"❌ Conversion failed: {result.error_message}")
                self.status_updated.emit("Conversion failed")

                if result.command:
                    self.log_message.emit(f"🔧 Command: {result.command}")

            self.conversion_finished.emit(result)

        except Exception as e:
            error_msg = f"Worker thread error: {str(e)}"
            self.log_message.emit(f"❌ {error_msg}")
            self.status_updated.emit("Conversion failed")

            result = ConversionResult(success=False, error_message=error_msg)
            self.conversion_finished.emit(result)
