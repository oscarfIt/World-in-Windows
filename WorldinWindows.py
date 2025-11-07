#!/usr/bin/env python
"""
Launcher script for World in Windows D&D DM Helper
"""

import sys
from pathlib import Path

# Handle PyInstaller's temporary folder
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    bundle_dir = sys._MEIPASS
else:
    # Running as normal Python script
    bundle_dir = Path(__file__).parent

# Add the bundle directory to the path
sys.path.insert(0, str(bundle_dir))

# Import and run the main function from the package
from WorldInWindows import main

if __name__ == "__main__":
    main()
