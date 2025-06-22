#!/usr/bin/env python3
"""
Roo Modes Configuration Sync Runner

A convenience script to run the mode sync system without explicitly importing the module.
"""

import os
import sys
from pathlib import Path

# Determine the project root directory
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the project root to Python path to ensure imports work correctly
sys.path.append(str(PROJECT_ROOT))

# Import and run the main function from roo_modes_sync
from scripts.roo_modes_sync.cli import main

if __name__ == "__main__":
    sys.exit(main())