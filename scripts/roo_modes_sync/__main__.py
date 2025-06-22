#!/usr/bin/env python3
"""
Main entry point for the roo_modes_sync package.

This allows the package to be executed as:
    python -m roo_modes_sync
"""

import sys
import os
from pathlib import Path

# Add the parent directory to sys.path so we can import the module
if __name__ == "__main__":
    # Get the directory containing this file
    current_dir = Path(__file__).parent
    # Add it to sys.path if not already there
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    from cli import main
    sys.exit(main())