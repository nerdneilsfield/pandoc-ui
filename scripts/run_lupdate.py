#!/usr/bin/env python
"""Run lupdate for translation extraction."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run lupdate with the given arguments."""
    # Get the project root
    project_root = Path(__file__).parent.parent
    
    # Build lupdate command
    cmd = [sys.executable, "-m", "PySide6.scripts.pyside_tool", "lupdate"] + sys.argv[1:]
    
    # Run the command
    result = subprocess.run(cmd, cwd=project_root)
    
    # Return the same exit code
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()