#!/usr/bin/env python3
import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run
from studio_manager.main import main

if __name__ == "__main__":
    main()