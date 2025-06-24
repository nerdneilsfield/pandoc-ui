"""
Tests for conversion service functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pandoc_ui.app.conversion_service import ConversionService
from pandoc_ui.infra.pandoc_detector import PandocInfo
from pandoc_ui.models import ConversionProfile, ConversionResult, OutputFormat


class TestConversionService:
    """Test cases for ConversionService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = ConversionService()
    
    def test_init(self):
        """Test service initialization."""
        assert self.service.detector is not None
        assert self.service._runner is None
        assert self.service._pandoc_info is None
    
    @patch('pandoc_ui.app.conversion_service.PandocDetector.is_available')
    def test_is_pandoc_available_true(self, mock_is_available):
        """Test pandoc availability check when available."""
        mock_is_available.return_value = True
        
        assert self.service.is_pandoc_available() is True
    
    @patch('pandoc_ui.app.conversion_service.PandocDetector.is_available')
    def test_is_pandoc_available_false(self, mock_is_available):
        """Test pandoc availability check when not available."""
        mock_is_available.return_value = False
        
        assert self.service.is_pandoc_available() is False
    
    @patch('pandoc_ui.app.conversion_service.PandocDetector.detect')
    def test_get_pandoc_info_cached(self, mock_detect):
        """Test pandoc info retrieval with caching."""
        expected_info = PandocInfo(Path('/usr/bin/pandoc'), '3.1.8')
        self.service._pandoc_info = expected_info
        
        result = self.service.get_pandoc_info()
        
        assert result is expected_info
        mock_detect.assert_not_called()
    
    @patch('pandoc_ui.app.conversion_service.PandocDetector.detect')
    def test_get_pandoc_info_not_cached(self, mock_detect):
        """Test pandoc info retrieval without cache."""
        expected_info = PandocInfo(Path('/usr/bin/pandoc'), '3.1.8')
        mock_detect.return_value = expected_info
        
        result = self.service.get_pandoc_info()
        
        assert result is expected_info
        assert self.service._pandoc_info is expected_info
        mock_detect.assert_called_once()
    
    def test_get_runner_not_available(self):
        """Test runner creation when pandoc is not available."""
        self.service._pandoc_info = PandocInfo(Path('pandoc'), 'unknown', False)
        
        with pytest.raises(RuntimeError, match='not available'):
            self.service._get_runner()
    
    @patch('pandoc_ui.app.conversion_service.PandocRunner')
    def test_get_runner_available(self, mock_runner_class):
        """Test runner creation when pandoc is available."""
        pandoc_info = PandocInfo(Path('/usr/bin/pandoc'), '3.1.8', True)
        self.service._pandoc_info = pandoc_info
        mock_runner = Mock()
        mock_runner_class.return_value = mock_runner
        
        result = self.service._get_runner()
        
        assert result is mock_runner
        assert self.service._runner is mock_runner
        mock_runner_class.assert_called_once_with(pandoc_info.path)
    
    @patch('pandoc_ui.app.conversion_service.ConversionService._get_runner')
    def test_convert_success(self, mock_get_runner):
        """Test successful conversion."""
        mock_runner = Mock()
        mock_result = ConversionResult(
            success=True,
            output_path=Path('output.html'),
            duration_seconds=1.5
        )
        mock_runner.execute.return_value = mock_result
        mock_get_runner.return_value = mock_runner
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.service.convert(profile)
        
        assert result.success is True
        assert result.output_path == Path('output.html')
        mock_runner.execute.assert_called_once_with(profile)
    
    @patch('pandoc_ui.app.conversion_service.ConversionService._get_runner')
    def test_convert_failure(self, mock_get_runner):
        """Test conversion failure."""
        mock_runner = Mock()
        mock_result = ConversionResult(
            success=False,
            error_message='Conversion failed'
        )
        mock_runner.execute.return_value = mock_result
        mock_get_runner.return_value = mock_runner
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.service.convert(profile)
        
        assert result.success is False
        assert result.error_message == 'Conversion failed'
    
    @patch('pandoc_ui.app.conversion_service.ConversionService._get_runner')
    def test_convert_exception(self, mock_get_runner):
        """Test conversion with exception."""
        mock_get_runner.side_effect = Exception('Test exception')
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.service.convert(profile)
        
        assert result.success is False
        assert 'Test exception' in result.error_message
    
    @patch('pandoc_ui.app.conversion_service.ConversionService.convert')
    def test_convert_async_delegates_to_sync(self, mock_convert):
        """Test that convert_async delegates to convert in Phase 1."""
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        expected_result = ConversionResult(success=True)
        mock_convert.return_value = expected_result
        
        result = self.service.convert_async(profile)
        
        assert result is expected_result
        mock_convert.assert_called_once_with(profile)
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_validate_input_file_success(self, mock_is_file, mock_exists):
        """Test successful input file validation."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        result = self.service.validate_input_file(Path('input.md'))
        
        assert result is True
    
    @patch('pathlib.Path.exists')
    def test_validate_input_file_not_exists(self, mock_exists):
        """Test input file validation when file doesn't exist."""
        mock_exists.return_value = False
        
        result = self.service.validate_input_file(Path('nonexistent.md'))
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_validate_input_file_not_file(self, mock_is_file, mock_exists):
        """Test input file validation when path is not a file."""
        mock_exists.return_value = True
        mock_is_file.return_value = False
        
        result = self.service.validate_input_file(Path('directory'))
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file') 
    def test_validate_input_file_unsupported_extension(self, mock_is_file, mock_exists):
        """Test input file validation with unsupported extension."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Should still return True - let pandoc decide
        result = self.service.validate_input_file(Path('input.xyz'))
        
        assert result is True
    
    @patch('pandoc_ui.app.conversion_service.PandocDetector.clear_cache')
    def test_refresh_pandoc_detection(self, mock_clear_cache):
        """Test pandoc detection refresh."""
        # Set up initial state
        self.service._pandoc_info = Mock()
        self.service._runner = Mock()
        
        self.service.refresh_pandoc_detection()
        
        assert self.service._pandoc_info is None
        assert self.service._runner is None
        mock_clear_cache.assert_called_once()