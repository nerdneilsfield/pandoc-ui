"""
Test configuration manager functionality.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from pandoc_ui.infra.config_manager import ConfigManager, get_config_manager, initialize_config


class TestConfigManager:
    """Test ConfigManager functionality."""

    @pytest.fixture
    def temp_base_dir(self):
        """Create temporary base directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_base_dir):
        """Create config manager with temp directory."""
        return ConfigManager(base_dir=temp_base_dir)

    def test_config_manager_initialization(self, temp_base_dir):
        """Test config manager initialization."""
        manager = ConfigManager(base_dir=temp_base_dir)

        assert manager.base_dir == temp_base_dir
        assert manager.profiles_dir == temp_base_dir / "profiles"
        assert manager.cache_dir == temp_base_dir / "cache"
        assert manager.logs_dir == temp_base_dir / "logs"

    def test_config_manager_default_initialization(self):
        """Test config manager with default directory."""
        manager = ConfigManager()

        expected_base = Path.home() / ".pandoc_gui"
        assert manager.base_dir == expected_base
        assert manager.profiles_dir == expected_base / "profiles"
        assert manager.cache_dir == expected_base / "cache"
        assert manager.logs_dir == expected_base / "logs"

    def test_ensure_directories(self, config_manager, temp_base_dir):
        """Test ensuring directories exist."""
        success = config_manager.ensure_directories()
        assert success

        # Check all directories were created
        assert config_manager.base_dir.exists()
        assert config_manager.profiles_dir.exists()
        assert config_manager.cache_dir.exists()
        assert config_manager.logs_dir.exists()

        # Check .gitignore was created
        gitignore_path = config_manager.base_dir / ".gitignore"
        assert gitignore_path.exists()

        content = gitignore_path.read_text()
        assert "*" in content
        assert "!.gitignore" in content

    def test_ensure_directories_existing(self, config_manager):
        """Test ensuring directories when they already exist."""
        # Create directories first
        config_manager.ensure_directories()

        # Call again - should still succeed
        success = config_manager.ensure_directories()
        assert success

        # Directories should still exist
        assert config_manager.base_dir.exists()
        assert config_manager.profiles_dir.exists()
        assert config_manager.cache_dir.exists()
        assert config_manager.logs_dir.exists()

    def test_get_profiles_dir(self, config_manager):
        """Test getting profiles directory."""
        profiles_dir = config_manager.get_profiles_dir()

        assert profiles_dir == config_manager.profiles_dir
        assert profiles_dir.exists()

    def test_get_cache_dir(self, config_manager):
        """Test getting cache directory."""
        cache_dir = config_manager.get_cache_dir()

        assert cache_dir == config_manager.cache_dir
        assert cache_dir.exists()

    def test_get_logs_dir(self, config_manager):
        """Test getting logs directory."""
        logs_dir = config_manager.get_logs_dir()

        assert logs_dir == config_manager.logs_dir
        assert logs_dir.exists()

    def test_get_settings_file(self, config_manager):
        """Test getting settings file path."""
        settings_file = config_manager.get_settings_file()

        expected_path = config_manager.base_dir / "settings.json"
        assert settings_file == expected_path
        assert config_manager.base_dir.exists()

    def test_get_directory_info(self, config_manager):
        """Test getting directory information."""
        # Get directory info
        info = config_manager.get_directory_info()

        assert "base_dir" in info
        assert "base_exists" in info
        assert "profiles_dir" in info
        assert "profiles_exists" in info
        assert "cache_dir" in info
        assert "cache_exists" in info
        assert "logs_dir" in info
        assert "logs_exists" in info
        assert "settings_file" in info
        assert "settings_exists" in info

        # Note: directories may already exist from fixture setup
        # What's important is that the info structure is correct

        # After ensuring directories
        config_manager.ensure_directories()
        info = config_manager.get_directory_info()

        assert info["base_exists"]
        assert info["profiles_exists"]
        assert info["cache_exists"]
        assert info["logs_exists"]
        # settings_exists is still False as we haven't created the file
        assert not info["settings_exists"]

    def test_cleanup_old_files(self, config_manager):
        """Test cleaning up old files."""
        import os
        import time

        # Ensure directories exist
        config_manager.ensure_directories()

        # Create some test files
        cache_file = config_manager.cache_dir / "old_cache.txt"
        log_file = config_manager.logs_dir / "old_log.log"
        recent_file = config_manager.cache_dir / "recent_cache.txt"

        cache_file.write_text("old cache data")
        log_file.write_text("old log data")
        recent_file.write_text("recent cache data")

        # Make some files appear old by changing their modification time
        old_time = time.time() - (40 * 24 * 60 * 60)  # 40 days ago
        os.utime(cache_file, (old_time, old_time))
        os.utime(log_file, (old_time, old_time))

        # Clean up files older than 30 days
        deleted_count = config_manager.cleanup_old_files(days=30)

        # Should have deleted 2 old files
        assert deleted_count == 2
        assert not cache_file.exists()
        assert not log_file.exists()
        assert recent_file.exists()  # Recent file should remain

    def test_reset_configuration(self, config_manager):
        """Test resetting configuration."""
        # Create directories and some files
        config_manager.ensure_directories()

        profile_file = config_manager.profiles_dir / "test_profile.json"
        cache_file = config_manager.cache_dir / "test_cache.txt"

        profile_file.write_text('{"name": "test"}')
        cache_file.write_text("test cache")

        assert profile_file.exists()
        assert cache_file.exists()

        # Reset without keeping profiles
        success = config_manager.reset_configuration(keep_profiles=False)
        assert success

        # Directories should be recreated but files should be gone
        assert config_manager.base_dir.exists()
        assert config_manager.profiles_dir.exists()
        assert not profile_file.exists()
        assert not cache_file.exists()

    def test_reset_configuration_keep_profiles(self, config_manager):
        """Test resetting configuration while keeping profiles."""
        # Create directories and files
        config_manager.ensure_directories()

        profile_file = config_manager.profiles_dir / "important_profile.json"
        cache_file = config_manager.cache_dir / "test_cache.txt"

        profile_data = '{"name": "important", "settings": "keep_me"}'
        profile_file.write_text(profile_data)
        cache_file.write_text("test cache")

        # Reset keeping profiles
        success = config_manager.reset_configuration(keep_profiles=True)
        assert success

        # Profile should be restored, cache should be gone
        assert profile_file.exists()
        assert profile_file.read_text() == profile_data
        assert not cache_file.exists()


class TestConfigManagerGlobalFunctions:
    """Test global config manager functions."""

    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton."""
        # Reset global state
        import pandoc_ui.infra.config_manager as cm

        cm._config_manager = None

        # Get manager instances
        manager1 = get_config_manager()
        manager2 = get_config_manager()

        # Should be the same instance
        assert manager1 is manager2

        # Should use default directory
        expected_base = Path.home() / ".pandoc_gui"
        assert manager1.base_dir == expected_base

    def test_initialize_config(self):
        """Test initialize_config function."""
        # Reset global state
        import pandoc_ui.infra.config_manager as cm

        cm._config_manager = None

        # Create temp directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Initialize with custom directory
            success = initialize_config(base_dir=temp_path)
            assert success

            # Get manager and verify it uses custom directory
            manager = get_config_manager()
            assert manager.base_dir == temp_path

            # Directories should be created
            assert manager.profiles_dir.exists()
            assert manager.cache_dir.exists()
            assert manager.logs_dir.exists()

    def test_initialize_config_default(self):
        """Test initialize_config with default directory."""
        # Reset global state
        import pandoc_ui.infra.config_manager as cm

        cm._config_manager = None

        success = initialize_config()
        assert success

        manager = get_config_manager()
        expected_base = Path.home() / ".pandoc_gui"
        assert manager.base_dir == expected_base
