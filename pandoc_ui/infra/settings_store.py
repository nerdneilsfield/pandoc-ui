"""
Settings store for persistent application configuration.
"""

import json
import logging
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .config_manager import get_config_manager

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages."""

    ENGLISH = "en"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    FRENCH = "fr"
    GERMAN = "de"
    SPANISH = "es"


class ApplicationSettings(BaseModel):
    """Application settings with validation."""

    # UI Settings
    language: Language = Language.ENGLISH
    theme: str = Field(default="system", description="UI theme: light, dark, system")
    window_width: int = Field(default=800, ge=400, le=2000)
    window_height: int = Field(default=600, ge=300, le=1500)
    window_x: int | None = Field(default=None, description="Window X position")
    window_y: int | None = Field(default=None, description="Window Y position")

    # Default Paths
    default_input_dir: str | None = Field(default=None, description="Default input directory")
    default_output_dir: str | None = Field(default=None, description="Default output directory")
    recent_input_files: list[str] = Field(default_factory=list, max_length=10)
    recent_output_dirs: list[str] = Field(default_factory=list, max_length=10)

    # Processing Settings
    max_concurrent_jobs: int = Field(
        default=4, ge=1, le=16, description="Max concurrent conversion jobs"
    )
    default_output_format: str = Field(default="html", description="Default output format")
    default_extensions: str = Field(
        default=".md,.markdown,.txt", description="Default file extensions for batch"
    )
    default_recursive_scan: bool = Field(
        default=True, description="Default recursive scanning mode"
    )
    max_batch_files: int = Field(default=1000, ge=1, le=10000, description="Maximum files in batch")

    # Advanced Settings
    pandoc_timeout_seconds: int = Field(
        default=300, ge=10, le=3600, description="Pandoc execution timeout"
    )
    log_level: str = Field(default="INFO", description="Logging level")
    auto_save_profiles: bool = Field(default=True, description="Auto-save profiles on changes")
    confirm_batch_operations: bool = Field(
        default=True, description="Confirm large batch operations"
    )

    # Performance Settings
    enable_progress_callbacks: bool = Field(default=True, description="Enable progress reporting")
    ui_update_interval_ms: int = Field(
        default=100, ge=50, le=1000, description="UI update interval"
    )

    @field_validator("recent_input_files", "recent_output_dirs")
    @classmethod
    def validate_recent_paths(cls, v: list[str]) -> list[str]:
        """Validate recent paths exist and are accessible."""
        valid_paths = []
        for path_str in v:
            try:
                path = Path(path_str)
                if path.exists():
                    valid_paths.append(str(path.resolve()))
            except Exception:
                continue
        return valid_paths

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme value."""
        allowed_themes = {"light", "dark", "system"}
        if v not in allowed_themes:
            return "system"
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            return "INFO"
        return v.upper()


class SettingsStore:
    """Persistent settings storage with validation."""

    def __init__(self, settings_file: Path | None = None):
        """
        Initialize settings store.

        Args:
            settings_file: Path to settings file (uses ConfigManager if None)
        """
        if settings_file is None:
            config_manager = get_config_manager()
            settings_file = config_manager.get_settings_file()

        self.settings_file = settings_file
        self._settings: ApplicationSettings | None = None

        logger.info(f"SettingsStore initialized with file: {self.settings_file}")

    def load_settings(self) -> ApplicationSettings:
        """
        Load settings from disk.

        Returns:
            ApplicationSettings object (creates default if file doesn't exist)
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, encoding="utf-8") as f:
                    data = json.load(f)

                # Validate and create settings object
                settings = ApplicationSettings(**data)
                logger.info(f"Settings loaded from {self.settings_file}")

            else:
                # Create default settings
                settings = ApplicationSettings()
                logger.info("Created default settings (file not found)")

            self._settings = settings
            return settings

        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}")
            # Return default settings on error
            settings = ApplicationSettings()
            self._settings = settings
            return settings

    def save_settings(self, settings: ApplicationSettings | None = None) -> bool:
        """
        Save settings to disk.

        Args:
            settings: Settings to save (uses current settings if None)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if settings is None:
                settings = self._settings

            if settings is None:
                logger.error("No settings to save")
                return False

            # Ensure directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Save to JSON with formatting
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False, default=str)

            self._settings = settings
            logger.info(f"Settings saved to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}")
            return False

    def get_settings(self) -> ApplicationSettings:
        """
        Get current settings (loads from disk if not cached).

        Returns:
            ApplicationSettings object
        """
        if self._settings is None:
            return self.load_settings()
        return self._settings

    def update_setting(self, key: str, value: Any) -> bool:
        """
        Update a single setting value.

        Args:
            key: Setting key to update
            value: New value

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            settings = self.get_settings()

            # Create new settings dict and update the key
            settings_dict = settings.model_dump()
            settings_dict[key] = value

            # Validate new settings
            new_settings = ApplicationSettings(**settings_dict)

            # Save if validation passed
            return self.save_settings(new_settings)

        except Exception as e:
            logger.error(f"Failed to update setting '{key}': {str(e)}")
            return False

    def add_recent_input_file(self, file_path: str) -> bool:
        """
        Add a file to recent input files list.

        Args:
            file_path: Path to add

        Returns:
            True if added successfully, False otherwise
        """
        try:
            settings = self.get_settings()
            recent_files = settings.recent_input_files.copy()

            # Remove if already exists
            if file_path in recent_files:
                recent_files.remove(file_path)

            # Add to front
            recent_files.insert(0, file_path)

            # Keep only latest 10
            recent_files = recent_files[:10]

            return self.update_setting("recent_input_files", recent_files)

        except Exception as e:
            logger.error(f"Failed to add recent input file: {str(e)}")
            return False

    def add_recent_output_dir(self, dir_path: str) -> bool:
        """
        Add a directory to recent output directories list.

        Args:
            dir_path: Directory path to add

        Returns:
            True if added successfully, False otherwise
        """
        try:
            settings = self.get_settings()
            recent_dirs = settings.recent_output_dirs.copy()

            # Remove if already exists
            if dir_path in recent_dirs:
                recent_dirs.remove(dir_path)

            # Add to front
            recent_dirs.insert(0, dir_path)

            # Keep only latest 10
            recent_dirs = recent_dirs[:10]

            return self.update_setting("recent_output_dirs", recent_dirs)

        except Exception as e:
            logger.error(f"Failed to add recent output dir: {str(e)}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Reset settings to default values.

        Returns:
            True if reset successfully, False otherwise
        """
        try:
            default_settings = ApplicationSettings()
            return self.save_settings(default_settings)

        except Exception as e:
            logger.error(f"Failed to reset settings: {str(e)}")
            return False

    def export_settings(self, export_path: Path) -> bool:
        """
        Export settings to a file.

        Args:
            export_path: Path to export to

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            settings = self.get_settings()

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(settings.model_dump(), f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"Settings exported to {export_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export settings: {str(e)}")
            return False

    def import_settings(self, import_path: Path) -> bool:
        """
        Import settings from a file.

        Args:
            import_path: Path to import from

        Returns:
            True if imported successfully, False otherwise
        """
        try:
            with open(import_path, encoding="utf-8") as f:
                data = json.load(f)

            # Validate imported data
            settings = ApplicationSettings(**data)

            # Save if validation passed
            success = self.save_settings(settings)
            if success:
                logger.info(f"Settings imported from {import_path}")

            return success

        except Exception as e:
            logger.error(f"Failed to import settings: {str(e)}")
            return False

    @property
    def settings_file_exists(self) -> bool:
        """Check if settings file exists."""
        return self.settings_file.exists()

    @property
    def settings_file_size(self) -> int:
        """Get settings file size in bytes."""
        try:
            return self.settings_file.stat().st_size if self.settings_file.exists() else 0
        except Exception:
            return 0
