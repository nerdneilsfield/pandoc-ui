"""
Configuration directory management for pandoc-ui.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration directories and structure."""

    def __init__(self, base_dir: Path | None = None):
        """
        Initialize configuration manager.

        Args:
            base_dir: Base configuration directory (default: ~/.pandoc_gui)
        """
        if base_dir is None:
            base_dir = Path.home() / ".pandoc_gui"

        self.base_dir = base_dir
        self.profiles_dir = base_dir / "profiles"
        self.cache_dir = base_dir / "cache"
        self.logs_dir = base_dir / "logs"

        logger.info(f"ConfigManager initialized with base_dir: {self.base_dir}")

    def ensure_directories(self) -> bool:
        """
        Ensure all required directories exist.

        Returns:
            True if all directories were created/exist, False on error
        """
        try:
            directories = [self.base_dir, self.profiles_dir, self.cache_dir, self.logs_dir]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Ensured directory exists: {directory}")

            # Create .gitignore to exclude from version control
            gitignore_path = self.base_dir / ".gitignore"
            if not gitignore_path.exists():
                gitignore_content = """# Pandoc UI user configuration
*
!.gitignore
"""
                gitignore_path.write_text(gitignore_content)
                logger.debug(f"Created .gitignore at {gitignore_path}")

            logger.info("All configuration directories ensured")
            return True

        except Exception as e:
            logger.error(f"Failed to create configuration directories: {str(e)}")
            return False

    def get_profiles_dir(self) -> Path:
        """Get profiles directory, ensuring it exists."""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        return self.profiles_dir

    def get_cache_dir(self) -> Path:
        """Get cache directory, ensuring it exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir

    def get_logs_dir(self) -> Path:
        """Get logs directory, ensuring it exists."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        return self.logs_dir

    def get_settings_file(self) -> Path:
        """Get settings file path, ensuring parent directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir / "settings.json"

    def cleanup_old_files(self, days: int = 30) -> int:
        """
        Clean up old cache and log files.

        Args:
            days: Files older than this many days will be deleted

        Returns:
            Number of files deleted
        """
        try:
            import time

            cutoff_time = time.time() - (days * 24 * 60 * 60)
            deleted_count = 0

            # Clean cache files
            if self.cache_dir.exists():
                for file_path in self.cache_dir.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old cache file: {file_path}")

            # Clean log files (keep recent ones)
            if self.logs_dir.exists():
                for file_path in self.logs_dir.glob("*.log"):
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old log file: {file_path}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old files")

            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0

    def get_directory_info(self) -> dict:
        """
        Get information about configuration directories.

        Returns:
            Dictionary with directory paths and status
        """
        return {
            "base_dir": str(self.base_dir),
            "base_exists": self.base_dir.exists(),
            "profiles_dir": str(self.profiles_dir),
            "profiles_exists": self.profiles_dir.exists(),
            "cache_dir": str(self.cache_dir),
            "cache_exists": self.cache_dir.exists(),
            "logs_dir": str(self.logs_dir),
            "logs_exists": self.logs_dir.exists(),
            "settings_file": str(self.get_settings_file()),
            "settings_exists": self.get_settings_file().exists(),
        }

    def reset_configuration(self, keep_profiles: bool = True) -> bool:
        """
        Reset configuration directories (for testing or user request).

        Args:
            keep_profiles: Whether to preserve existing profiles

        Returns:
            True if reset successfully, False on error
        """
        try:
            import shutil
            import time

            if keep_profiles and self.profiles_dir.exists():
                # Backup profiles
                backup_dir = self.base_dir.parent / f".pandoc_gui_backup_{int(time.time())}"
                backup_profiles = backup_dir / "profiles"
                backup_profiles.mkdir(parents=True, exist_ok=True)

                for profile_file in self.profiles_dir.glob("*.json"):
                    shutil.copy2(profile_file, backup_profiles)

                logger.info(f"Backed up profiles to {backup_profiles}")

            # Remove base directory
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
                logger.info(f"Removed configuration directory: {self.base_dir}")

            # Recreate structure
            success = self.ensure_directories()

            if keep_profiles and "backup_profiles" in locals():
                # Restore profiles
                for profile_file in backup_profiles.glob("*.json"):
                    shutil.copy2(profile_file, self.profiles_dir)

                # Clean up backup
                shutil.rmtree(backup_dir)
                logger.info("Restored profiles from backup")

            return success

        except Exception as e:
            logger.error(f"Failed to reset configuration: {str(e)}")
            return False


# Global instance for easy access
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
        _config_manager.ensure_directories()
    return _config_manager


def initialize_config(base_dir: Path | None = None) -> bool:
    """
    Initialize application configuration.

    Args:
        base_dir: Custom base directory (for testing)

    Returns:
        True if initialization successful, False otherwise
    """
    global _config_manager
    _config_manager = ConfigManager(base_dir)
    return _config_manager.ensure_directories()
