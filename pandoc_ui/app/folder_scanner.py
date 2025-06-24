"""
Folder scanner for recursive file enumeration with extension filtering.
"""

import logging
from typing import List, Set, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from ..models import OutputFormat


logger = logging.getLogger(__name__)


class ScanMode(Enum):
    """File scanning mode."""
    RECURSIVE = "recursive"
    SINGLE_LEVEL = "single_level"


@dataclass
class ScanResult:
    """Results from folder scanning operation."""
    files: List[Path]
    total_count: int
    filtered_count: int
    errors: List[str]
    scan_duration_seconds: float
    
    @property
    def success(self) -> bool:
        """Check if scan was successful."""
        return len(self.errors) == 0
    
    @property
    def summary(self) -> str:
        """Get summary of scan results."""
        return (f"Found {self.total_count} files, "
                f"{self.filtered_count} matching filters, "
                f"{len(self.errors)} errors")


class FolderScanner:
    """Scans directories for files matching specified criteria."""
    
    # Common input formats that can be converted by pandoc
    DEFAULT_EXTENSIONS = {
        'markdown': {'.md', '.markdown', '.mdown', '.mkd', '.mkdn'},
        'restructuredtext': {'.rst', '.rest'},
        'asciidoc': {'.adoc', '.asciidoc'},
        'textile': {'.textile'},
        'html': {'.html', '.htm'},
        'latex': {'.tex', '.latex'},
        'docx': {'.docx'},
        'odt': {'.odt'},
        'epub': {'.epub'},
        'org': {'.org'},
        'mediawiki': {'.wiki'},
        'twiki': {'.twiki'},
        'opml': {'.opml'},
        'json': {'.json'},  # For pandoc JSON format
    }
    
    def __init__(self):
        """Initialize folder scanner."""
        self._scan_stats = {
            'total_scanned': 0,
            'last_scan_duration': 0.0,
            'errors_encountered': []
        }
    
    def scan_folder(self, 
                   folder_path: Path, 
                   extensions: Optional[Set[str]] = None,
                   mode: ScanMode = ScanMode.RECURSIVE,
                   max_files: int = 10000,
                   ignore_patterns: Optional[Set[str]] = None) -> ScanResult:
        """
        Scan folder for files matching criteria.
        
        Args:
            folder_path: Directory to scan
            extensions: File extensions to include (e.g. {'.md', '.rst'})
            mode: Scanning mode (recursive or single level)
            max_files: Maximum number of files to return
            ignore_patterns: Directory/file patterns to ignore
            
        Returns:
            ScanResult with found files and statistics
        """
        import time
        start_time = time.time()
        
        errors = []
        all_files = []
        filtered_files = []
        
        # Default extensions if none provided
        if extensions is None:
            extensions = set()
            for ext_set in self.DEFAULT_EXTENSIONS.values():
                extensions.update(ext_set)
        
        # Normalize extensions (ensure they start with '.')
        extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in extensions}
        
        # Default ignore patterns
        if ignore_patterns is None:
            ignore_patterns = {
                '.git', '.svn', '.hg', '__pycache__', 
                'node_modules', '.venv', 'venv', 'env',
                '.DS_Store', 'Thumbs.db'
            }
        
        try:
            # Validate input folder
            if not folder_path.exists():
                errors.append(f"Folder does not exist: {folder_path}")
                return ScanResult([], 0, 0, errors, time.time() - start_time)
            
            if not folder_path.is_dir():
                errors.append(f"Path is not a directory: {folder_path}")
                return ScanResult([], 0, 0, errors, time.time() - start_time)
            
            logger.info(f"Scanning folder: {folder_path} (mode: {mode.value})")
            logger.debug(f"Extensions: {sorted(extensions)}")
            logger.debug(f"Ignore patterns: {sorted(ignore_patterns)}")
            
            # Scan files
            if mode == ScanMode.RECURSIVE:
                all_files = self._scan_recursive(folder_path, ignore_patterns, max_files)
            else:
                all_files = self._scan_single_level(folder_path, ignore_patterns, max_files)
            
            # Filter by extensions
            for file_path in all_files:
                if len(filtered_files) >= max_files:
                    logger.warning(f"Reached max_files limit ({max_files}), stopping scan")
                    break
                
                if file_path.suffix.lower() in extensions:
                    filtered_files.append(file_path)
            
            # Sort files for consistent results
            filtered_files.sort()
            
            scan_duration = time.time() - start_time
            self._scan_stats['total_scanned'] = len(all_files)
            self._scan_stats['last_scan_duration'] = scan_duration
            
            logger.info(f"Scan completed: {len(all_files)} total, "
                       f"{len(filtered_files)} filtered, "
                       f"{scan_duration:.2f}s")
            
            return ScanResult(
                files=filtered_files,
                total_count=len(all_files),
                filtered_count=len(filtered_files),
                errors=errors,
                scan_duration_seconds=scan_duration
            )
            
        except PermissionError as e:
            error_msg = f"Permission denied accessing {folder_path}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error scanning {folder_path}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return ScanResult(
            files=[],
            total_count=0,
            filtered_count=0,
            errors=errors,
            scan_duration_seconds=time.time() - start_time
        )
    
    def _scan_recursive(self, folder_path: Path, ignore_patterns: Set[str], max_files: int) -> List[Path]:
        """Recursively scan directory for all files."""
        files = []
        
        try:
            for item in folder_path.rglob('*'):
                if len(files) >= max_files:
                    break
                
                # Skip if any parent directory matches ignore patterns
                if any(parent.name in ignore_patterns for parent in item.parents):
                    continue
                
                # Skip if item name matches ignore patterns
                if item.name in ignore_patterns:
                    continue
                
                # Skip hidden files/directories (starting with .)
                if any(part.startswith('.') for part in item.parts if part != '.'):
                    continue
                
                # Only include files, not directories
                if item.is_file():
                    files.append(item)
                    
        except PermissionError as e:
            logger.warning(f"Permission denied in recursive scan: {e}")
        except Exception as e:
            logger.warning(f"Error in recursive scan: {e}")
        
        return files
    
    def _scan_single_level(self, folder_path: Path, ignore_patterns: Set[str], max_files: int) -> List[Path]:
        """Scan only the immediate directory level."""
        files = []
        
        try:
            for item in folder_path.iterdir():
                if len(files) >= max_files:
                    break
                
                # Skip if item name matches ignore patterns
                if item.name in ignore_patterns:
                    continue
                
                # Skip hidden files (starting with .)
                if item.name.startswith('.'):
                    continue
                
                # Only include files, not directories
                if item.is_file():
                    files.append(item)
                    
        except PermissionError as e:
            logger.warning(f"Permission denied in single level scan: {e}")
        except Exception as e:
            logger.warning(f"Error in single level scan: {e}")
        
        return files
    
    def get_supported_extensions(self, output_format: Optional[OutputFormat] = None) -> Set[str]:
        """
        Get supported input extensions for pandoc.
        
        Args:
            output_format: If specified, return extensions optimized for this output
            
        Returns:
            Set of file extensions (with dots)
        """
        if output_format is None:
            # Return all supported extensions
            extensions = set()
            for ext_set in self.DEFAULT_EXTENSIONS.values():
                extensions.update(ext_set)
            return extensions
        
        # Return extensions commonly used for specific output formats
        if output_format == OutputFormat.PDF:
            # LaTeX and Markdown work well for PDF
            return (self.DEFAULT_EXTENSIONS['markdown'] | 
                   self.DEFAULT_EXTENSIONS['latex'] |
                   self.DEFAULT_EXTENSIONS['restructuredtext'])
        elif output_format == OutputFormat.HTML:
            # Most formats work well for HTML
            return (self.DEFAULT_EXTENSIONS['markdown'] |
                   self.DEFAULT_EXTENSIONS['restructuredtext'] |
                   self.DEFAULT_EXTENSIONS['asciidoc'] |
                   self.DEFAULT_EXTENSIONS['textile'])
        elif output_format == OutputFormat.DOCX:
            # Markdown and similar work well for DOCX
            return (self.DEFAULT_EXTENSIONS['markdown'] |
                   self.DEFAULT_EXTENSIONS['restructuredtext'] |
                   self.DEFAULT_EXTENSIONS['html'])
        else:
            # Default to common text formats
            return (self.DEFAULT_EXTENSIONS['markdown'] |
                   self.DEFAULT_EXTENSIONS['restructuredtext'])
    
    def get_extension_categories(self) -> Dict[str, Set[str]]:
        """
        Get categorized extensions for UI selection.
        
        Returns:
            Dictionary mapping category names to extension sets
        """
        return self.DEFAULT_EXTENSIONS.copy()
    
    def estimate_batch_size(self, folder_path: Path, extensions: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        Estimate batch processing requirements without full scan.
        
        Args:
            folder_path: Directory to estimate
            extensions: File extensions to count
            
        Returns:
            Dictionary with size estimates and recommendations
        """
        try:
            # Sample scan to estimate
            sample_result = self.scan_folder(
                folder_path=folder_path,
                extensions=extensions,
                mode=ScanMode.SINGLE_LEVEL,
                max_files=100
            )
            
            # Try recursive sample
            recursive_sample = self.scan_folder(
                folder_path=folder_path,
                extensions=extensions,
                mode=ScanMode.RECURSIVE,
                max_files=500
            )
            
            # Estimate total size
            single_level_count = sample_result.filtered_count
            recursive_count = recursive_sample.filtered_count
            
            # Calculate recommended settings
            if recursive_count > 1000:
                recommended_mode = ScanMode.SINGLE_LEVEL
                recommended_batch_size = min(50, single_level_count)
            elif recursive_count > 100:
                recommended_mode = ScanMode.RECURSIVE
                recommended_batch_size = min(20, recursive_count)
            else:
                recommended_mode = ScanMode.RECURSIVE
                recommended_batch_size = recursive_count
            
            return {
                'single_level_estimate': single_level_count,
                'recursive_estimate': recursive_count,
                'recommended_mode': recommended_mode,
                'recommended_batch_size': recommended_batch_size,
                'estimated_duration_minutes': max(1, recursive_count // 100)
            }
            
        except Exception as e:
            logger.error(f"Error estimating batch size: {e}")
            return {
                'single_level_estimate': 0,
                'recursive_estimate': 0,
                'recommended_mode': ScanMode.SINGLE_LEVEL,
                'recommended_batch_size': 10,
                'estimated_duration_minutes': 1
            }
    
    @property
    def scan_statistics(self) -> Dict[str, Any]:
        """Get scanning statistics."""
        return self._scan_stats.copy()