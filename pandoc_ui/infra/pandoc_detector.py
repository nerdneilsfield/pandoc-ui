"""
Pandoc detector - locates pandoc installation across platforms.
"""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class PandocInfo:
    """Information about detected pandoc installation."""
    path: Path
    version: str
    available: bool = True


class PandocDetector:
    """Detects pandoc installation on the system."""
    
    def __init__(self):
        self._cached_info: Optional[PandocInfo] = None
    
    def detect(self) -> PandocInfo:
        """
        Detect pandoc installation and return information.
        
        Returns:
            PandocInfo with path, version, and availability status
        """
        if self._cached_info is not None:
            return self._cached_info
        
        # First check PATH
        pandoc_path = shutil.which('pandoc')
        if pandoc_path:
            version = self._get_version(Path(pandoc_path))
            if version:
                self._cached_info = PandocInfo(Path(pandoc_path), version)
                return self._cached_info
        
        # Check common installation locations
        search_paths = self._get_search_paths()
        for path in search_paths:
            if path.exists() and path.is_file():
                version = self._get_version(path)
                if version:
                    self._cached_info = PandocInfo(path, version)
                    return self._cached_info
        
        # Not found
        self._cached_info = PandocInfo(Path("pandoc"), "unknown", False)
        return self._cached_info
    
    def _get_search_paths(self) -> List[Path]:
        """Get platform-specific search paths for pandoc."""
        system = platform.system().lower()
        paths = []
        
        if system == "windows":
            # Windows common locations
            program_files = [
                Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")),
                Path(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"))
            ]
            
            for pf in program_files:
                paths.extend([
                    pf / "Pandoc" / "pandoc.exe",
                    pf / "pandoc" / "pandoc.exe",
                ])
            
            # Chocolatey location
            paths.append(Path("C:\\ProgramData\\chocolatey\\bin\\pandoc.exe"))
            
            # Scoop location
            if "USERPROFILE" in os.environ:
                userprofile = Path(os.environ["USERPROFILE"])
                paths.append(userprofile / "scoop" / "apps" / "pandoc" / "current" / "pandoc.exe")
        
        elif system == "darwin":
            # macOS common locations
            paths.extend([
                Path("/usr/local/bin/pandoc"),
                Path("/opt/homebrew/bin/pandoc"),
                Path("/usr/bin/pandoc"),
            ])
            
            # MacPorts
            paths.append(Path("/opt/local/bin/pandoc"))
        
        elif system == "linux":
            # Linux common locations
            paths.extend([
                Path("/usr/bin/pandoc"),
                Path("/usr/local/bin/pandoc"),
                Path("/opt/pandoc/bin/pandoc"),
            ])
            
            # Snap location
            paths.append(Path("/snap/bin/pandoc"))
            
            # Flatpak location (usually in PATH but check anyway)
            if "HOME" in os.environ:
                home = Path(os.environ["HOME"])
                paths.append(home / ".local" / "share" / "flatpak" / "exports" / "bin" / "pandoc")
        
        return paths
    
    def _get_version(self, pandoc_path: Path) -> Optional[str]:
        """
        Get pandoc version from binary.
        
        Args:
            pandoc_path: Path to pandoc binary
            
        Returns:
            Version string or None if unable to determine
        """
        try:
            result = subprocess.run(
                [str(pandoc_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse version from first line: "pandoc 3.1.8"
                first_line = result.stdout.strip().split('\n')[0]
                if first_line.startswith("pandoc "):
                    return first_line.split()[1]
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
            pass
        
        return None
    
    def is_available(self) -> bool:
        """Check if pandoc is available on the system."""
        return self.detect().available
    
    def clear_cache(self):
        """Clear cached detection results."""
        self._cached_info = None