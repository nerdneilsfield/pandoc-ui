"""
Pandoc runner - builds and executes pandoc commands.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional

from ..models import ConversionProfile, ConversionResult, OutputFormat


class PandocRunner:
    """Builds and executes pandoc commands."""
    
    def __init__(self, pandoc_path: Path):
        """
        Initialize runner with pandoc binary path.
        
        Args:
            pandoc_path: Path to pandoc executable
        """
        self.pandoc_path = pandoc_path
    
    def build_command(self, profile: ConversionProfile) -> List[str]:
        """
        Build pandoc command list from conversion profile.
        
        Args:
            profile: Conversion configuration
            
        Returns:
            List of command arguments for subprocess
        """
        cmd = [str(self.pandoc_path)]
        
        # Input file
        cmd.append(str(profile.input_path))
        
        # Output format
        cmd.extend(["-t", profile.output_format.value])
        
        # Output file
        if profile.output_path:
            cmd.extend(["-o", str(profile.output_path)])
        
        # Add format-specific options
        if profile.output_format == OutputFormat.PDF:
            cmd.extend(["--pdf-engine", "pdflatex"])
        elif profile.output_format == OutputFormat.HTML:
            cmd.append("--standalone")
        
        # Add custom options from profile
        for key, value in profile.options.items():
            if value is True:
                cmd.append(f"--{key}")
            elif value is not False and value is not None:
                cmd.extend([f"--{key}", str(value)])
        
        return cmd
    
    def execute(self, profile: ConversionProfile) -> ConversionResult:
        """
        Execute pandoc conversion synchronously.
        
        Args:
            profile: Conversion configuration
            
        Returns:
            ConversionResult with success status and details
        """
        start_time = time.time()
        
        try:
            # Validate input file exists
            if not profile.input_path.exists():
                return ConversionResult(
                    success=False,
                    error_message=f"Input file does not exist: {profile.input_path}"
                )
            
            # Create output directory if needed
            if profile.output_path and profile.output_path.parent:
                profile.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = self.build_command(profile)
            cmd_str = " ".join(cmd)
            
            # Execute pandoc
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return ConversionResult(
                    success=True,
                    output_path=profile.output_path,
                    duration_seconds=duration,
                    command=cmd_str
                )
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown pandoc error"
                return ConversionResult(
                    success=False,
                    error_message=error_msg,
                    duration_seconds=duration,
                    command=cmd_str
                )
        
        except subprocess.TimeoutExpired:
            return ConversionResult(
                success=False,
                error_message="Pandoc conversion timed out after 5 minutes",
                duration_seconds=time.time() - start_time
            )
        
        except Exception as e:
            return ConversionResult(
                success=False,
                error_message=f"Conversion failed: {str(e)}",
                duration_seconds=time.time() - start_time
            )
    
    def validate_output_format(self, format_str: str) -> bool:
        """
        Validate if output format is supported.
        
        Args:
            format_str: Format string to validate
            
        Returns:
            True if format is supported
        """
        try:
            OutputFormat(format_str)
            return True
        except ValueError:
            return False