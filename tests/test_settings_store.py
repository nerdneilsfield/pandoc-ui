"""
Test settings store functionality.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path

from pandoc_ui.infra.settings_store import SettingsStore, ApplicationSettings, Language


class TestApplicationSettings:
    """Test ApplicationSettings model."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = ApplicationSettings()
        
        assert settings.language == Language.ENGLISH
        assert settings.theme == "system"
        assert settings.window_width == 800
        assert settings.window_height == 600
        assert settings.max_concurrent_jobs == 4
        assert settings.default_output_format == "html"
        assert settings.default_extensions == ".md,.markdown,.txt"
        assert settings.default_recursive_scan is True
        assert settings.max_batch_files == 1000
        assert settings.pandoc_timeout_seconds == 300
        assert settings.log_level == "INFO"
        assert settings.auto_save_profiles is True
        assert settings.confirm_batch_operations is True
        assert settings.enable_progress_callbacks is True
        assert settings.ui_update_interval_ms == 100
    
    def test_settings_validation(self):
        """Test settings validation."""
        # Test valid settings
        settings = ApplicationSettings(
            window_width=1200,
            window_height=800,
            max_concurrent_jobs=8,
            theme="dark",
            log_level="DEBUG"
        )
        
        assert settings.window_width == 1200
        assert settings.window_height == 800
        assert settings.max_concurrent_jobs == 8
        assert settings.theme == "dark"
        assert settings.log_level == "DEBUG"
    
    def test_settings_validation_errors(self):
        """Test settings validation with invalid values."""
        # Test window size constraints
        with pytest.raises(ValueError):
            ApplicationSettings(window_width=300)  # Too small
        
        with pytest.raises(ValueError):
            ApplicationSettings(window_height=200)  # Too small
        
        with pytest.raises(ValueError):
            ApplicationSettings(max_concurrent_jobs=0)  # Too small
        
        with pytest.raises(ValueError):
            ApplicationSettings(max_concurrent_jobs=20)  # Too large
    
    def test_theme_validation(self):
        """Test theme validation."""
        # Valid themes
        for theme in ['light', 'dark', 'system']:
            settings = ApplicationSettings(theme=theme)
            assert settings.theme == theme
        
        # Invalid theme should default to 'system'
        settings = ApplicationSettings(theme='invalid_theme')
        assert settings.theme == 'system'
    
    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            settings = ApplicationSettings(log_level=level)
            assert settings.log_level == level
        
        # Test case insensitive
        settings = ApplicationSettings(log_level='debug')
        assert settings.log_level == 'DEBUG'
        
        # Invalid log level should default to 'INFO'
        settings = ApplicationSettings(log_level='INVALID')
        assert settings.log_level == 'INFO'
    
    def test_recent_paths_validation(self):
        """Test recent paths validation."""
        # Create temporary files for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create some test files
            file1 = temp_path / "file1.txt"
            file1.write_text("test")
            file2 = temp_path / "file2.txt"
            file2.write_text("test")
            
            # Test with mix of valid and invalid paths
            recent_files = [
                str(file1),  # Valid
                "/nonexistent/file.txt",  # Invalid
                str(file2),  # Valid
                "invalid_path"  # Invalid
            ]
            
            settings = ApplicationSettings(recent_input_files=recent_files)
            
            # Should only contain valid paths
            assert len(settings.recent_input_files) == 2
            assert str(file1) in settings.recent_input_files
            assert str(file2) in settings.recent_input_files
            assert "/nonexistent/file.txt" not in settings.recent_input_files


class TestSettingsStore:
    """Test SettingsStore functionality."""
    
    @pytest.fixture
    def temp_settings_file(self):
        """Create temporary settings file for testing."""
        temp_file = Path(tempfile.mktemp(suffix='.json'))
        yield temp_file
        if temp_file.exists():
            temp_file.unlink()
    
    @pytest.fixture
    def settings_store(self, temp_settings_file):
        """Create settings store with temp file."""
        return SettingsStore(settings_file=temp_settings_file)
    
    def test_store_initialization(self, temp_settings_file):
        """Test settings store initialization."""
        store = SettingsStore(settings_file=temp_settings_file)
        
        assert store.settings_file == temp_settings_file
        assert store._settings is None
    
    def test_load_settings_new_file(self, settings_store):
        """Test loading settings when file doesn't exist."""
        settings = settings_store.load_settings()
        
        # Should create default settings
        assert isinstance(settings, ApplicationSettings)
        assert settings.language == Language.ENGLISH
        assert settings.theme == "system"
        assert settings.max_concurrent_jobs == 4
    
    def test_save_and_load_settings(self, settings_store):
        """Test saving and loading settings."""
        # Create custom settings
        settings = ApplicationSettings(
            language=Language.CHINESE,
            theme="dark",
            window_width=1200,
            window_height=900,
            max_concurrent_jobs=8,
            default_output_format="pdf"
        )
        
        # Save settings
        success = settings_store.save_settings(settings)
        assert success
        assert settings_store.settings_file.exists()
        
        # Load settings back
        loaded_settings = settings_store.load_settings()
        
        assert loaded_settings.language == Language.CHINESE
        assert loaded_settings.theme == "dark"
        assert loaded_settings.window_width == 1200
        assert loaded_settings.window_height == 900
        assert loaded_settings.max_concurrent_jobs == 8
        assert loaded_settings.default_output_format == "pdf"
    
    def test_load_settings_with_existing_file(self, settings_store):
        """Test loading settings from existing file."""
        # Create a settings file manually
        settings_data = {
            "language": "zh",
            "theme": "light",
            "window_width": 1000,
            "window_height": 700,
            "max_concurrent_jobs": 6,
            "default_output_format": "docx",
            "log_level": "WARNING"
        }
        
        with open(settings_store.settings_file, 'w') as f:
            json.dump(settings_data, f)
        
        # Load settings
        settings = settings_store.load_settings()
        
        assert settings.language == Language.CHINESE
        assert settings.theme == "light"
        assert settings.window_width == 1000
        assert settings.window_height == 700
        assert settings.max_concurrent_jobs == 6
        assert settings.default_output_format == "docx"
        assert settings.log_level == "WARNING"
    
    def test_get_settings_caching(self, settings_store):
        """Test settings caching behavior."""
        # First call should load from disk
        settings1 = settings_store.get_settings()
        
        # Second call should return cached version
        settings2 = settings_store.get_settings()
        
        assert settings1 is settings2  # Same object reference
    
    def test_update_setting(self, settings_store):
        """Test updating a single setting."""
        # Load initial settings
        settings_store.load_settings()
        
        # Update a setting
        success = settings_store.update_setting('theme', 'dark')
        assert success
        
        # Verify update
        updated_settings = settings_store.get_settings()
        assert updated_settings.theme == 'dark'
        
        # File should be updated too
        settings_store._settings = None  # Clear cache
        reloaded_settings = settings_store.load_settings()
        assert reloaded_settings.theme == 'dark'
    
    def test_update_invalid_setting(self, settings_store):
        """Test updating with invalid value."""
        settings_store.load_settings()
        
        # Try to update with invalid value
        success = settings_store.update_setting('window_width', 100)  # Too small
        assert not success
        
        # Settings should remain unchanged
        settings = settings_store.get_settings()
        assert settings.window_width == 800  # Default value
    
    def test_add_recent_input_file(self, settings_store):
        """Test adding recent input file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Add file to recent list
            success = settings_store.add_recent_input_file(temp_path)
            assert success
            
            # Verify it's in the list
            settings = settings_store.get_settings()
            assert temp_path in settings.recent_input_files
            assert settings.recent_input_files[0] == temp_path  # Should be first
            
        finally:
            Path(temp_path).unlink()  # Clean up
    
    def test_add_recent_input_file_duplicate(self, settings_store):
        """Test adding duplicate recent input file."""
        # Create temporary files
        files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            files.append(temp_file.name)
            temp_file.close()
        
        try:
            # Add files
            for file_path in files:
                settings_store.add_recent_input_file(file_path)
            
            # Add first file again
            settings_store.add_recent_input_file(files[0])
            
            # Should be moved to front, not duplicated
            settings = settings_store.get_settings()
            assert settings.recent_input_files[0] == files[0]
            assert settings.recent_input_files.count(files[0]) == 1
            assert len(settings.recent_input_files) == 3
            
        finally:
            for file_path in files:
                Path(file_path).unlink()
    
    def test_add_recent_output_dir(self, settings_store):
        """Test adding recent output directory."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Add directory to recent list
            success = settings_store.add_recent_output_dir(temp_dir)
            assert success
            
            # Verify it's in the list
            settings = settings_store.get_settings()
            assert temp_dir in settings.recent_output_dirs
            assert settings.recent_output_dirs[0] == temp_dir
    
    def test_reset_to_defaults(self, settings_store):
        """Test resetting settings to defaults."""
        # Load and modify settings
        settings = settings_store.load_settings()
        settings_store.update_setting('theme', 'dark')
        settings_store.update_setting('max_concurrent_jobs', 8)
        
        # Reset to defaults
        success = settings_store.reset_to_defaults()
        assert success
        
        # Verify defaults
        settings = settings_store.get_settings()
        assert settings.theme == "system"
        assert settings.max_concurrent_jobs == 4
        assert settings.language == Language.ENGLISH
    
    def test_export_settings(self, settings_store, temp_settings_file):
        """Test exporting settings."""
        # Create and save custom settings
        settings = ApplicationSettings(
            language=Language.FRENCH,
            theme="dark",
            max_concurrent_jobs=6
        )
        settings_store.save_settings(settings)
        
        # Export to another file
        export_path = temp_settings_file.parent / "exported_settings.json"
        
        try:
            success = settings_store.export_settings(export_path)
            assert success
            assert export_path.exists()
            
            # Verify exported content
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            assert exported_data['language'] == "fr"
            assert exported_data['theme'] == "dark"
            assert exported_data['max_concurrent_jobs'] == 6
            
        finally:
            if export_path.exists():
                export_path.unlink()
    
    def test_import_settings(self, settings_store, temp_settings_file):
        """Test importing settings."""
        # Create import file
        import_data = {
            "language": "de",
            "theme": "light",
            "window_width": 1400,
            "max_concurrent_jobs": 12,
            "default_output_format": "epub"
        }
        
        import_path = temp_settings_file.parent / "import_settings.json"
        
        try:
            with open(import_path, 'w') as f:
                json.dump(import_data, f)
            
            # Import settings
            success = settings_store.import_settings(import_path)
            assert success
            
            # Verify imported settings
            settings = settings_store.get_settings()
            assert settings.language == Language.GERMAN
            assert settings.theme == "light"
            assert settings.window_width == 1400
            assert settings.max_concurrent_jobs == 12
            assert settings.default_output_format == "epub"
            
        finally:
            if import_path.exists():
                import_path.unlink()
    
    def test_settings_file_properties(self, settings_store):
        """Test settings file property methods."""
        # Initially file doesn't exist
        assert not settings_store.settings_file_exists
        assert settings_store.settings_file_size == 0
        
        # Save settings
        settings_store.save_settings(ApplicationSettings())
        
        # Now file exists
        assert settings_store.settings_file_exists
        assert settings_store.settings_file_size > 0