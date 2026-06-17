# studio_manager/utils/daw_discovery.py

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
import platform

class DAWDiscovery:
    """Discover and validate DAW installations"""
    
    # Common installation paths for different OS
    COMMON_PATHS = {
        "windows": {
            "Ableton": [
                r"C:\ProgramData\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe",
                r"C:\ProgramData\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe",
                r"C:\ProgramData\Ableton\Live 10 Suite\Program\Ableton Live 10 Suite.exe",
                r"C:\Program Files\Ableton\Live 12 Suite\Program\Ableton Live 12 Suite.exe",
                r"C:\Program Files\Ableton\Live 11 Suite\Program\Ableton Live 11 Suite.exe",
                r"C:\Program Files\Ableton\Live 10 Suite\Program\Ableton Live 10 Suite.exe",
                r"C:\Program Files\Ableton\Live 12\Program\Ableton Live 12.exe",
            ],
            "Pro Tools": [
                r"C:\Program Files\Avid\Pro Tools\ProTools.exe",
                r"C:\Program Files\Avid\Pro Tools\Pro Tools.exe",
                r"C:\Program Files (x86)\Avid\Pro Tools\ProTools.exe",
            ],
            "Logic": []  # Not available on Windows
        },
        "mac": {
            "Ableton": [
                "/Applications/Ableton Live 12 Suite.app",
                "/Applications/Ableton Live 11 Suite.app",
                "/Applications/Ableton Live 10 Suite.app",
                "/Applications/Ableton Live 12.app",
                "/Applications/Ableton Live 11.app",
            ],
            "Pro Tools": [
                "/Applications/Pro Tools.app",
                "/Applications/Pro Tools Ultimate.app",
            ],
            "Logic": [
                "/Applications/Logic Pro X.app",
                "/Applications/Logic Pro.app",
            ]
        }
    }
    
    @staticmethod
    def get_os() -> str:
        """Detect operating system"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "mac"
        else:
            return "linux"  # Not officially supported
    
    @classmethod
    def find_daw_paths(cls, daw_name: str) -> List[str]:
        """Find all possible paths for a DAW on current system"""
        os_type = cls.get_os()
        paths = cls.COMMON_PATHS.get(os_type, {}).get(daw_name, [])
        
        # Filter to only existing paths
        existing_paths = [p for p in paths if Path(p).exists()]
        
        # If on Mac, also check for .app bundles
        if os_type == "mac":
            # Check if any .app exists with variations
            app_dir = Path("/Applications")
            if app_dir.exists():
                for app in app_dir.glob(f"*{daw_name}*.app"):
                    if str(app) not in existing_paths:
                        existing_paths.append(str(app))
        
        return existing_paths
    
    @classmethod
    def validate_path(cls, path: str) -> bool:
        """Validate that a path exists and is executable"""
        path_obj = Path(path)
        
        # On Windows, .exe files need to exist
        if cls.get_os() == "windows":
            return path_obj.exists() and path_obj.suffix.lower() == ".exe"
        # On Mac, .app bundles need to exist
        elif cls.get_os() == "mac":
            return path_obj.exists() and (path_obj.suffix == ".app" or path_obj.is_file())
        
        return path_obj.exists()
    
    @classmethod
    def get_daw_display_name(cls, daw_code: str) -> str:
        """Get display name for a DAW code"""
        names = {
            "A": "Ableton Live",
            "P": "Pro Tools",
            "L": "Logic Pro"
        }
        return names.get(daw_code, daw_code)