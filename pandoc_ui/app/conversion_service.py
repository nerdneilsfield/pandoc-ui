"""
Conversion service - orchestrates pandoc detection and execution.
"""

import logging
from pathlib import Path
from typing import Optional

from ..infra.pandoc_detector import PandocDetector, PandocInfo
from ..infra.pandoc_runner import PandocRunner
from ..models import ConversionProfile, ConversionResult


logger = logging.getLogger(__name__)


class ConversionService:
    """Orchestrates document conversion using pandoc."""
    
    def __init__(self):
        """Initialize conversion service."""
        self.detector = PandocDetector()
        self._runner: Optional[PandocRunner] = None
        self._pandoc_info: Optional[PandocInfo] = None
    
    def is_pandoc_available(self) -> bool:
        """
        Check if pandoc is available on the system.
        
        Returns:
            True if pandoc is detected and usable
        """
        return self.detector.is_available()
    
    def get_pandoc_info(self) -> PandocInfo:
        """
        Get information about detected pandoc installation.
        
        Returns:
            PandocInfo with path, version, and availability
        """
        if self._pandoc_info is None:
            self._pandoc_info = self.detector.detect()
        return self._pandoc_info
    
    def _get_runner(self) -> PandocRunner:
        """
        Get pandoc runner instance.
        
        Returns:
            PandocRunner configured with detected pandoc path
            
        Raises:
            RuntimeError: If pandoc is not available
        """
        if self._runner is None:
            pandoc_info = self.get_pandoc_info()
            if not pandoc_info.available:
                raise RuntimeError("Pandoc is not available on this system")
            
            self._runner = PandocRunner(pandoc_info.path)
        
        return self._runner
    
    def convert(self, profile: ConversionProfile) -> ConversionResult:
        """
        Convert document using the provided profile.
        
        Args:
            profile: Conversion configuration
            
        Returns:
            ConversionResult with success status and details
        """
        logger.info(f"Starting conversion: {profile.input_path} -> {profile.output_format.value}")
        
        try:
            runner = self._get_runner()
            result = runner.execute(profile)
            
            if result.success:
                logger.info(f"Conversion completed successfully in {result.duration_seconds:.2f}s")
                logger.info(f"Output saved to: {result.output_path}")
            else:
                logger.error(f"Conversion failed: {result.error_message}")
            
            return result
        
        except Exception as e:
            logger.error(f"Conversion service error: {str(e)}")
            return ConversionResult(
                success=False,
                error_message=f"Service error: {str(e)}"
            )
    
    def convert_async(self, profile: ConversionProfile) -> ConversionResult:
        """
        Convert document asynchronously (placeholder for Phase 1).
        
        For Phase 1, this is a synchronous implementation.
        Will be enhanced with proper async support in later phases.
        
        Args:
            profile: Conversion configuration
            
        Returns:
            ConversionResult with success status and details
        """
        # For Phase 1, delegate to synchronous implementation
        return self.convert(profile)
    
    def validate_input_file(self, file_path: Path) -> bool:
        """
        Validate input file for conversion.
        
        Args:
            file_path: Path to input file
            
        Returns:
            True if file is suitable for conversion
        """
        if not file_path.exists():
            logger.warning(f"Input file does not exist: {file_path}")
            return False
        
        if not file_path.is_file():
            logger.warning(f"Input path is not a file: {file_path}")
            return False
        
        # Check if file has a supported extension (basic check)
        supported_extensions = {'.md', '.markdown', '.rst', '.txt', '.html', '.docx', '.odt'}
        if file_path.suffix.lower() not in supported_extensions:
            logger.warning(f"File extension may not be supported: {file_path.suffix}")
            # Don't return False - let pandoc decide
        
        return True
    
    def refresh_pandoc_detection(self):
        """Force re-detection of pandoc installation."""
        self.detector.clear_cache()
        self._pandoc_info = None
        self._runner = None
        logger.info("Pandoc detection cache cleared")