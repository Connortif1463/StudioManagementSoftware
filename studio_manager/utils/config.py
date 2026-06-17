# studio_manager/utils/config.py

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

class UserConfig:
    """Manages user configuration and first-time setup"""
    
    CONFIG_FILE = Path.home() / ".studio_manager" / "config.json"
    
    def __init__(self):
        self.config_dir = self.CONFIG_FILE.parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data = self.load()
    
    def load(self) -> Dict:
        """Load user configuration"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.create_default()
        return self.create_default()
    
    def create_default(self) -> Dict:
        """Create default configuration"""
        return {
            "first_time": True,
            "daw_paths": {
                "P": "",  # Pro Tools
                "A": "",  # Ableton
                "L": ""   # Logic (Mac only)
            },
            "os": "windows",  # or "mac"
            "last_updated": None
        }
    
    def save(self):
        """Save configuration"""
        self.data["last_updated"] = datetime.now().isoformat()
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def is_first_time(self) -> bool:
        """Check if this is the first time running the program"""
        return self.data.get("first_time", True)
    
    def set_daw_path(self, daw_code: str, path: str):
        """Set a DAW path"""
        self.data["daw_paths"][daw_code] = path
        self.data["first_time"] = False
        self.save()
    
    def get_daw_path(self, daw_code: str) -> Optional[str]:
        """Get a DAW path"""
        path = self.data["daw_paths"].get(daw_code, "")
        # If path is empty, return None
        return path if path else None