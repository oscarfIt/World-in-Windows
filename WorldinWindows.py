#!/usr/bin/env python
"""
Launcher script for World in Windows D&D DM Helper
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the package
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

# Import and run the main function from the package
from world_in_windows import main

if __name__ == "__main__":
    main()
