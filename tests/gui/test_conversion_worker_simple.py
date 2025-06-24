"""
Simplified tests for conversion worker thread.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from pandoc_ui.gui.conversion_worker import ConversionWorker
from pandoc_ui.models import ConversionProfile, ConversionResult, OutputFormat


@pytest.fixture
def conversion_profile():
    """Create test conversion profile."""
    return ConversionProfile(
        input_path=Path("test_input.md"),
        output_path=Path("test_output.html"),
        output_format=OutputFormat.HTML
    )


class TestConversionWorkerSimple:
    """Simplified test cases for ConversionWorker."""
    
    def test_init(self, qapp, conversion_profile):
        """Test worker initialization."""
        worker = ConversionWorker(conversion_profile)
        
        assert worker.profile == conversion_profile
        assert worker.service is not None
        assert hasattr(worker, 'progress_updated')
        assert hasattr(worker, 'status_updated')
        assert hasattr(worker, 'log_message')
        assert hasattr(worker, 'conversion_finished')
    
    def test_signal_connections(self, qapp, conversion_profile):
        """Test that all signals can be connected."""
        worker = ConversionWorker(conversion_profile)
        
        # Test signal connections
        progress_received = []
        status_received = []
        log_received = []
        result_received = []
        
        worker.progress_updated.connect(lambda x: progress_received.append(x))
        worker.status_updated.connect(lambda x: status_received.append(x))
        worker.log_message.connect(lambda x: log_received.append(x))
        worker.conversion_finished.connect(lambda x: result_received.append(x))
        
        # Emit test signals
        worker.progress_updated.emit(50)
        worker.status_updated.emit("Test status")
        worker.log_message.emit("Test log")
        worker.conversion_finished.emit(ConversionResult(success=True))
        
        # Check signals were received
        assert progress_received == [50]
        assert status_received == ["Test status"]
        assert log_received == ["Test log"]
        assert len(result_received) == 1
        assert result_received[0].success is True
    
    def test_pandoc_not_available(self, qapp, conversion_profile):
        """Test run when pandoc is not available."""
        # Mock service - pandoc not available
        mock_service = Mock()
        mock_service.is_pandoc_available.return_value = False
        
        # Create worker with mock service
        worker = ConversionWorker(conversion_profile, service=mock_service)
        
        # Track result
        result_received = None
        def capture_result(result):
            nonlocal result_received
            result_received = result
        worker.conversion_finished.connect(capture_result)
        
        # Run worker
        worker.run()
        
        # Should have failed result
        assert result_received is not None
        assert result_received.success is False
        assert "not available" in result_received.error_message
    
    def test_conversion_success(self, qapp, conversion_profile):
        """Test successful conversion."""
        # Mock service
        mock_service = Mock()
        mock_service.is_pandoc_available.return_value = True
        mock_service.get_pandoc_info.return_value = Mock(
            path=Path("/usr/bin/pandoc"),
            version="3.1.3"
        )
        mock_service.validate_input_file.return_value = True
        
        # Mock successful conversion result
        mock_result = ConversionResult(
            success=True,
            output_path=Path("test_output.html"),
            duration_seconds=1.5
        )
        mock_service.convert.return_value = mock_result
        
        # Create worker with mock service
        worker = ConversionWorker(conversion_profile, service=mock_service)
        
        # Track result
        result_received = None
        progress_values = []
        
        def capture_result(result):
            nonlocal result_received
            result_received = result
            
        worker.conversion_finished.connect(capture_result)
        worker.progress_updated.connect(lambda x: progress_values.append(x))
        
        # Mock file exists
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.stat', return_value=Mock(st_size=10000)):
            # Run worker
            worker.run()
        
        # Should have successful result
        assert result_received is not None
        assert result_received.success is True
        assert result_received.output_path == Path("test_output.html")
        
        # Should have progress updates
        assert len(progress_values) > 0
        assert 100 in progress_values
    
    def test_conversion_failure(self, qapp, conversion_profile):
        """Test conversion failure."""
        # Mock service
        mock_service = Mock()
        mock_service.is_pandoc_available.return_value = True
        mock_service.get_pandoc_info.return_value = Mock(
            path=Path("/usr/bin/pandoc"),
            version="3.1.3"
        )
        mock_service.validate_input_file.return_value = True
        
        # Mock failed conversion result
        mock_result = ConversionResult(
            success=False,
            error_message="Pandoc conversion failed"
        )
        mock_service.convert.return_value = mock_result
        
        # Create worker with mock service
        worker = ConversionWorker(conversion_profile, service=mock_service)
        
        # Track result
        result_received = None
        def capture_result(result):
            nonlocal result_received
            result_received = result
        worker.conversion_finished.connect(capture_result)
        
        # Run worker
        worker.run()
        
        # Should have failed result
        assert result_received is not None
        assert result_received.success is False
        assert "Pandoc conversion failed" in result_received.error_message