"""
Tests for pandoc runner functionality.
"""

import subprocess
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from pandoc_ui.infra.pandoc_runner import PandocRunner
from pandoc_ui.models import ConversionProfile, OutputFormat


class TestPandocRunner:
    """Test cases for PandocRunner."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.pandoc_path = Path('/usr/bin/pandoc')
        self.runner = PandocRunner(self.pandoc_path)
    
    def test_init(self):
        """Test runner initialization."""
        assert self.runner.pandoc_path == self.pandoc_path
    
    def test_build_command_basic(self):
        """Test basic command building."""
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_path=Path('output.html'),
            output_format=OutputFormat.HTML
        )
        
        cmd = self.runner.build_command(profile)
        
        expected = [
            '/usr/bin/pandoc',
            'input.md',
            '-t', 'html',
            '-o', 'output.html',
            '--standalone'
        ]
        assert cmd == expected
    
    def test_build_command_pdf(self):
        """Test command building for PDF output."""
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_path=Path('output.pdf'),
            output_format=OutputFormat.PDF
        )
        
        cmd = self.runner.build_command(profile)
        
        assert '--pdf-engine' in cmd
        assert 'pdflatex' in cmd
    
    def test_build_command_with_options(self):
        """Test command building with custom options."""
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_path=Path('output.html'),
            output_format=OutputFormat.HTML,
            options={
                'toc': True,
                'css': 'style.css',
                'metadata': 'title=Test'
            }
        )
        
        cmd = self.runner.build_command(profile)
        
        assert '--toc' in cmd
        assert '--css' in cmd
        assert 'style.css' in cmd
        assert '--metadata' in cmd
        assert 'title=Test' in cmd
    
    def test_build_command_boolean_false_option(self):
        """Test that False boolean options are ignored."""
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML,
            options={'toc': False, 'standalone': False}
        )
        
        cmd = self.runner.build_command(profile)
        
        assert '--toc' not in cmd
        # Note: --standalone is added by default for HTML, but custom False shouldn't add it again
    
    @patch('pathlib.Path.exists')
    def test_execute_input_not_exists(self, mock_exists):
        """Test execution when input file doesn't exist."""
        mock_exists.return_value = False
        
        profile = ConversionProfile(
            input_path=Path('nonexistent.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.runner.execute(profile)
        
        assert result.success is False
        assert 'does not exist' in result.error_message
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.mkdir')
    @patch('subprocess.run')
    def test_execute_success(self, mock_run, mock_mkdir, mock_exists):
        """Test successful execution."""
        mock_exists.return_value = True
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_path=Path('output/result.html'),
            output_format=OutputFormat.HTML
        )
        
        result = self.runner.execute(profile)
        
        assert result.success is True
        assert result.output_path == Path('output/result.html')
        assert result.duration_seconds >= 0
        mock_mkdir.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_execute_pandoc_failure(self, mock_run, mock_exists):
        """Test execution when pandoc command fails."""
        mock_exists.return_value = True
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = 'pandoc: input.md: openBinaryFile: does not exist'
        mock_run.return_value = mock_result
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.runner.execute(profile)
        
        assert result.success is False
        assert 'does not exist' in result.error_message
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_execute_timeout(self, mock_run, mock_exists):
        """Test execution timeout handling."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('pandoc', 300)
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.runner.execute(profile)
        
        assert result.success is False
        assert 'timed out' in result.error_message
    
    @patch('pathlib.Path.exists')
    @patch('subprocess.run')
    def test_execute_exception(self, mock_run, mock_exists):
        """Test execution exception handling."""
        mock_exists.return_value = True
        mock_run.side_effect = Exception('Test exception')
        
        profile = ConversionProfile(
            input_path=Path('input.md'),
            output_format=OutputFormat.HTML
        )
        
        result = self.runner.execute(profile)
        
        assert result.success is False
        assert 'Test exception' in result.error_message
    
    def test_validate_output_format_valid(self):
        """Test validation of valid output formats."""
        assert self.runner.validate_output_format('html') is True
        assert self.runner.validate_output_format('pdf') is True
        assert self.runner.validate_output_format('docx') is True
    
    def test_validate_output_format_invalid(self):
        """Test validation of invalid output formats."""
        assert self.runner.validate_output_format('invalid') is False
        assert self.runner.validate_output_format('') is False