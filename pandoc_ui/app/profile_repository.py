"""
Profile repository for managing conversion configuration snapshots.
"""

import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

from ..models import ConversionProfile, OutputFormat
from ..infra.config_manager import get_config_manager


logger = logging.getLogger(__name__)


@dataclass
class UIProfile:
    """UI configuration profile for saving/loading snapshots."""
    name: str
    created_at: str
    modified_at: str
    
    # Single file mode settings
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    output_format: str = OutputFormat.HTML.value
    
    # Batch mode settings
    is_batch_mode: bool = False
    input_folder: Optional[str] = None
    output_folder: Optional[str] = None
    extensions: str = ".md"
    scan_recursive: bool = True
    max_files: int = 1000
    
    # Advanced options
    pdf_engine: Optional[str] = None
    html_standalone: bool = True
    custom_options: Optional[Dict[str, Any]] = None
    
    # Processing settings
    max_concurrent_jobs: int = 4
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIProfile':
        """Create profile from dictionary."""
        return cls(**data)


class ProfileRepository:
    """Repository for managing UI configuration profiles."""
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize profile repository.
        
        Args:
            profiles_dir: Directory for storing profiles (uses ConfigManager if None)
        """
        if profiles_dir is None:
            config_manager = get_config_manager()
            profiles_dir = config_manager.get_profiles_dir()
        
        self.profiles_dir = profiles_dir
        
        logger.info(f"ProfileRepository initialized with directory: {self.profiles_dir}")
    
    def save_profile(self, profile: UIProfile) -> bool:
        """
        Save a UI profile to disk.
        
        Args:
            profile: UIProfile to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Update modified timestamp
            profile.modified_at = datetime.now().isoformat()
            
            # Generate safe filename
            safe_name = self._sanitize_filename(profile.name)
            profile_path = self.profiles_dir / f"{safe_name}.json"
            
            # Save to JSON
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Profile '{profile.name}' saved to {profile_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save profile '{profile.name}': {str(e)}")
            return False
    
    def load_profile(self, name: str) -> Optional[UIProfile]:
        """
        Load a UI profile from disk.
        
        Args:
            name: Profile name to load
            
        Returns:
            UIProfile if found and loaded successfully, None otherwise
        """
        try:
            safe_name = self._sanitize_filename(name)
            profile_path = self.profiles_dir / f"{safe_name}.json"
            
            if not profile_path.exists():
                logger.warning(f"Profile '{name}' not found at {profile_path}")
                return None
            
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = UIProfile.from_dict(data)
            logger.info(f"Profile '{name}' loaded from {profile_path}")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load profile '{name}': {str(e)}")
            return None
    
    def list_profiles(self) -> List[UIProfile]:
        """
        List all available profiles.
        
        Returns:
            List of UIProfile objects sorted by modification time (newest first)
        """
        profiles = []
        
        try:
            for profile_file in self.profiles_dir.glob("*.json"):
                try:
                    with open(profile_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    profile = UIProfile.from_dict(data)
                    profiles.append(profile)
                    
                except Exception as e:
                    logger.warning(f"Failed to load profile from {profile_file}: {str(e)}")
                    continue
            
            # Sort by modification time (newest first)
            profiles.sort(key=lambda p: p.modified_at, reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list profiles: {str(e)}")
        
        return profiles
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a profile from disk.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            safe_name = self._sanitize_filename(name)
            profile_path = self.profiles_dir / f"{safe_name}.json"
            
            if not profile_path.exists():
                logger.warning(f"Profile '{name}' not found for deletion")
                return False
            
            profile_path.unlink()
            logger.info(f"Profile '{name}' deleted from {profile_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete profile '{name}': {str(e)}")
            return False
    
    def profile_exists(self, name: str) -> bool:
        """
        Check if a profile exists.
        
        Args:
            name: Profile name to check
            
        Returns:
            True if profile exists, False otherwise
        """
        safe_name = self._sanitize_filename(name)
        profile_path = self.profiles_dir / f"{safe_name}.json"
        return profile_path.exists()
    
    def get_profile_count(self) -> int:
        """
        Get the number of profiles.
        
        Returns:
            Number of profile files in the directory
        """
        try:
            return len(list(self.profiles_dir.glob("*.json")))
        except Exception:
            return 0
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a profile name for use as a filename.
        
        Args:
            name: Profile name to sanitize
            
        Returns:
            Safe filename string
        """
        # Replace unsafe characters with underscores
        unsafe_chars = '<>:"/\\|?* '  # Added space to unsafe chars
        safe_name = name
        
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limit length and strip whitespace
        safe_name = safe_name.strip()[:100]
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = "unnamed_profile"
        
        return safe_name
    
    def create_profile_from_ui_state(self, 
                                   name: str,
                                   ui_state: Dict[str, Any]) -> UIProfile:
        """
        Create a UIProfile from current UI state.
        
        Args:
            name: Profile name
            ui_state: Dictionary containing UI widget values
            
        Returns:
            UIProfile object
        """
        now = datetime.now().isoformat()
        
        return UIProfile(
            name=name,
            created_at=now,
            modified_at=now,
            
            # Single file mode
            input_file=ui_state.get('input_file'),
            output_file=ui_state.get('output_file'),
            output_format=ui_state.get('output_format', OutputFormat.HTML.value),
            
            # Batch mode
            is_batch_mode=ui_state.get('is_batch_mode', False),
            input_folder=ui_state.get('input_folder'),
            output_folder=ui_state.get('output_folder'),
            extensions=ui_state.get('extensions', '.md'),
            scan_recursive=ui_state.get('scan_recursive', True),
            max_files=ui_state.get('max_files', 1000),
            
            # Advanced options
            pdf_engine=ui_state.get('pdf_engine'),
            html_standalone=ui_state.get('html_standalone', True),
            custom_options=ui_state.get('custom_options'),
            
            # Processing settings
            max_concurrent_jobs=ui_state.get('max_concurrent_jobs', 4)
        )
    
    def get_default_profile(self) -> UIProfile:
        """
        Create a default profile with sensible defaults.
        
        Returns:
            UIProfile with default settings
        """
        now = datetime.now().isoformat()
        
        return UIProfile(
            name="Default",
            created_at=now,
            modified_at=now,
            
            output_format=OutputFormat.HTML.value,
            is_batch_mode=False,
            extensions=".md",
            scan_recursive=True,
            max_files=1000,
            html_standalone=True,
            max_concurrent_jobs=4
        )