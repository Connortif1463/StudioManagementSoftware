#!/usr/bin/env python3
"""
Studio Management System Launcher
Double-click this file to run the application
"""

import subprocess
import sys
import os

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Run the main application
    try:
        subprocess.run([sys.executable, "-m", "studio_manager.main"])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        input(f"Error: {e}\nPress Enter to exit...")

if __name__ == "__main__":
    main()