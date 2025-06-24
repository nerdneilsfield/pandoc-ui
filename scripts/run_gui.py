#!/usr/bin/env python3
"""
GUI launcher script for pandoc-ui.

Usage:
    python scripts/run_gui.py
    uv run python scripts/run_gui.py
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandoc_ui.main import main

if __name__ == "__main__":
    sys.exit(main())
