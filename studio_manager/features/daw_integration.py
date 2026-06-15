import subprocess
import platform
from pathlib import Path
from ..cli.display import print_success, print_warning, print_info
from ..utils.constants import DAW_PATHS

def get_daw_info(daw_code: str) -> dict:
    """Get DAW information by code"""
    return DAW_PATHS.get(daw_code, {})

def open_daw_project(project_path: Path, daw_code: str, project_name: str) -> bool:
    """Attempt to open the DAW with the project file"""
    system = platform.system()
    
    # Handle both single letter codes and full names
    daw_map_full = {
        "A": "Ableton",
        "P": "Pro Tools", 
        "L": "Logic"
    }
    
    daw_name = daw_map_full.get(daw_code, daw_code)
    daw_info = DAW_PATHS.get(daw_code, {})
    
    if not daw_info:
        print_warning(f"Unknown DAW: {daw_code}")
        return False
    
    # Find the session file
    session_dir = project_path / daw_info.get("folder", "")
    if not session_dir.exists():
        print_warning(f"Session folder not found: {session_dir}")
        return False
    
    session_files = list(session_dir.glob(f"*{daw_info.get('ext', '')}"))
    if not session_files:
        print_warning(f"No {daw_info['name']} session file found")
        return False
    
    session_file = session_files[0]
    
    # Open based on OS
    if system == "Darwin":  # macOS
        app_path = daw_info.get("mac")
        if app_path:
            print_info(f"Opening {daw_info['name']} with {session_file.name}...")
            subprocess.run(["open", "-a", app_path, str(session_file)])
            return True
    elif system == "Windows":
        exe_path = daw_info.get("win")
        if exe_path:
            print_info(f"Opening {daw_info['name']} with {session_file.name}...")
            subprocess.run([exe_path, str(session_file)])
            return True
    
    print_warning(f"Auto-open not configured for {daw_info['name']} on {system}")
    print_info(f"Session file located at: {session_file}")
    return False