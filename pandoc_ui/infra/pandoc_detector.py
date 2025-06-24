"""
Pandoc detector - locates pandoc installation across platforms.
"""

import os
import platform
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
            logger.debug("Using cached pandoc info")
            return self._cached_info
        
        logger.info("Starting pandoc detection...")
        
        # Debug: Show environment info
        system = platform.system()
        logger.debug(f"Operating system: {system}")
        logger.debug(f"PATH environment variable: {os.environ.get('PATH', 'Not set')[:200]}...")
        
        # First check PATH using shutil.which
        logger.debug("Checking PATH for pandoc...")
        pandoc_path = shutil.which('pandoc')
        logger.debug(f"shutil.which('pandoc') returned: {pandoc_path}")
        
        if pandoc_path:
            logger.info(f"Found pandoc in PATH: {pandoc_path}")
            version = self._get_version(Path(pandoc_path))
            if version:
                logger.info(f"Pandoc version detected: {version}")
                self._cached_info = PandocInfo(Path(pandoc_path), version)
                return self._cached_info
            else:
                logger.warning(f"Found pandoc at {pandoc_path} but could not get version")
        else:
            logger.debug("Pandoc not found in PATH")
        
        # Check common installation locations
        logger.debug("Checking common installation locations...")
        search_paths = self._get_search_paths()
        logger.debug(f"Searching {len(search_paths)} locations: {[str(p) for p in search_paths[:5]]}...")
        
        for path in search_paths:
            logger.debug(f"Checking: {path}")
            if path.exists() and path.is_file():
                logger.debug(f"Found file at: {path}")
                version = self._get_version(path)
                if version:
                    logger.info(f"Found working pandoc at: {path} (version: {version})")
                    self._cached_info = PandocInfo(path, version)
                    return self._cached_info
                else:
                    logger.debug(f"File exists but version check failed: {path}")
            else:
                logger.debug(f"Not found: {path}")
        
        # Try alternative names on Windows and manual PATH search
        if system.lower() == "windows":
            logger.debug("Trying alternative pandoc executable names on Windows...")
            for alt_name in ['pandoc.exe', 'pandoc.cmd', 'pandoc.bat']:
                alt_path = shutil.which(alt_name)
                if alt_path:
                    logger.info(f"Found {alt_name} in PATH: {alt_path}")
                    version = self._get_version(Path(alt_path))
                    if version:
                        logger.info(f"Alternative pandoc working: {alt_path} (version: {version})")
                        self._cached_info = PandocInfo(Path(alt_path), version)
                        return self._cached_info
            
            # Manual PATH search for Windows (sometimes shutil.which fails)
            logger.debug("Performing manual PATH search on Windows...")
            path_found = self._manual_path_search_windows()
            if path_found:
                version = self._get_version(path_found)
                if version:
                    logger.info(f"Manual PATH search found working pandoc: {path_found} (version: {version})")
                    self._cached_info = PandocInfo(path_found, version)
                    return self._cached_info
        
        # Not found
        logger.warning("Pandoc not found on system")
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
                # Try multiple variations
                paths.extend([
                    pf / "Pandoc" / "pandoc.exe",
                    pf / "pandoc" / "pandoc.exe",
                    pf / "Pandoc" / "bin" / "pandoc.exe",
                    pf / "pandoc" / "bin" / "pandoc.exe",
                ])
            
            # Chocolatey locations
            paths.extend([
                Path("C:\\ProgramData\\chocolatey\\bin\\pandoc.exe"),
                Path("C:\\tools\\pandoc\\pandoc.exe"),
            ])
            
            # Scoop locations
            if "USERPROFILE" in os.environ:
                userprofile = Path(os.environ["USERPROFILE"])
                paths.extend([
                    userprofile / "scoop" / "apps" / "pandoc" / "current" / "pandoc.exe",
                    userprofile / "scoop" / "shims" / "pandoc.exe",
                ])
            
            # AppData local installations
            if "LOCALAPPDATA" in os.environ:
                localappdata = Path(os.environ["LOCALAPPDATA"])
                paths.extend([
                    localappdata / "Pandoc" / "pandoc.exe",
                    localappdata / "Programs" / "Pandoc" / "pandoc.exe",
                ])
            
            # System32 and other system paths (less common but possible)
            paths.extend([
                Path("C:\\Windows\\System32\\pandoc.exe"),
                Path("C:\\Windows\\pandoc.exe"),
            ])
        
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
            logger.debug(f"Getting version for: {pandoc_path}")
            
            # Check if file is executable
            if not pandoc_path.exists():
                logger.debug(f"File does not exist: {pandoc_path}")
                return None
            
            # On Windows, check for executable extensions (case insensitive)
            if platform.system().lower() == "windows":
                path_str = str(pandoc_path).lower()
                if not path_str.endswith(('.exe', '.cmd', '.bat')):
                    logger.debug(f"Windows file without executable extension: {pandoc_path}")
                else:
                    logger.debug(f"Windows executable file: {pandoc_path}")
            
            result = subprocess.run(
                [str(pandoc_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=pandoc_path.parent if pandoc_path.parent.exists() else None
            )
            
            logger.debug(f"Command exit code: {result.returncode}")
            logger.debug(f"Command stdout: {result.stdout[:100]}...")
            logger.debug(f"Command stderr: {result.stderr[:100]}...")
            
            if result.returncode == 0:
                # Parse version from first line: "pandoc 3.1.8" or "pandoc.exe 3.7.0.2"
                first_line = result.stdout.strip().split('\n')[0]
                logger.debug(f"First line of output: {first_line}")
                
                # Handle different pandoc executable names
                pandoc_prefixes = ["pandoc.exe ", "pandoc.cmd ", "pandoc.bat ", "pandoc "]
                version = None
                
                for prefix in pandoc_prefixes:
                    if first_line.startswith(prefix):
                        parts = first_line.split()
                        if len(parts) >= 2:
                            version = parts[1]
                            logger.debug(f"Extracted version using prefix '{prefix}': {version}")
                            break
                
                if version:
                    return version
                else:
                    logger.debug(f"Could not parse version from output: {first_line}")
                    # Try alternative parsing - look for version pattern in the line
                    import re
                    version_match = re.search(r'\b(\d+\.\d+(?:\.\d+)*(?:\.\d+)?)\b', first_line)
                    if version_match:
                        version = version_match.group(1)
                        logger.debug(f"Extracted version using regex: {version}")
                        return version
                    else:
                        logger.debug(f"No version pattern found in: {first_line}")
            else:
                logger.debug(f"Non-zero exit code: {result.returncode}")
            
        except subprocess.TimeoutExpired:
            logger.debug(f"Timeout getting version for: {pandoc_path}")
        except subprocess.SubprocessError as e:
            logger.debug(f"Subprocess error for {pandoc_path}: {e}")
        except OSError as e:
            logger.debug(f"OS error for {pandoc_path}: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error for {pandoc_path}: {e}")
        
        return None
    
    def _manual_path_search_windows(self) -> Optional[Path]:
        """
        Manually search PATH for pandoc on Windows.
        Sometimes shutil.which fails on Windows due to permissions or other issues.
        """
        try:
            path_env = os.environ.get('PATH', '')
            if not path_env:
                logger.debug("PATH environment variable is empty")
                return None
            
            path_dirs = path_env.split(os.pathsep)
            logger.debug(f"Manually searching {len(path_dirs)} PATH directories")
            
            pandoc_names = ['pandoc.exe', 'pandoc.cmd', 'pandoc.bat', 'pandoc']
            
            for path_dir in path_dirs:
                if not path_dir.strip():
                    continue
                    
                try:
                    path_obj = Path(path_dir.strip())
                    if not path_obj.exists() or not path_obj.is_dir():
                        continue
                    
                    for pandoc_name in pandoc_names:
                        pandoc_path = path_obj / pandoc_name
                        logger.debug(f"Checking manual path: {pandoc_path}")
                        
                        if pandoc_path.exists() and pandoc_path.is_file():
                            logger.debug(f"Found potential pandoc: {pandoc_path}")
                            
                            # Try to verify it's executable
                            try:
                                # Quick test - try to run it with --version
                                result = subprocess.run(
                                    [str(pandoc_path), "--version"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                if result.returncode == 0 and "pandoc" in result.stdout.lower():
                                    logger.info(f"Manual search verified working pandoc: {pandoc_path}")
                                    return pandoc_path
                                else:
                                    logger.debug(f"File exists but not working pandoc: {pandoc_path}")
                            except Exception as e:
                                logger.debug(f"Error testing {pandoc_path}: {e}")
                                
                except Exception as e:
                    logger.debug(f"Error checking directory {path_dir}: {e}")
                    continue
            
            logger.debug("Manual PATH search completed, no working pandoc found")
            return None
            
        except Exception as e:
            logger.debug(f"Error in manual PATH search: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if pandoc is available on the system."""
        return self.detect().available
    
    def clear_cache(self):
        """Clear cached detection results."""
        self._cached_info = None