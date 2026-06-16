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
    daw_info = get_daw_info(daw_code)
    
    if not daw_info:
        print_warning(f"Unknown DAW: {daw_code}")
        return False
    
    # Find the session file - check in stage folders (production, mix, master)
    session_files = []
    for stage in ["production", "mix", "master"]:
        stage_path = project_path / stage / daw_info.get("folder", "")
        if stage_path.exists():
            session_files.extend(list(stage_path.glob(f"*{daw_info.get('ext', '')}")))
    
    # Also check for old structure (DAW folder at root)
    if not session_files:
        session_dir = project_path / daw_info.get("folder", "")
        if session_dir.exists():
            session_files = list(session_dir.glob(f"*{daw_info.get('ext', '')}"))
    
    if not session_files:
        print_warning(f"No {daw_info['name']} session file found in project")
        print_info(f"Checked in: production/{daw_info.get('folder', '')}, mix/{daw_info.get('folder', '')}, master/{daw_info.get('folder', '')}")
        return False
    
    # Use the most recent session file
    session_file = sorted(session_files, key=lambda x: x.stat().st_mtime)[-1]
    print_info(f"Found session: {session_file.name}")
    
    # Open based on OS
    if system == "Darwin":  # macOS
        app_path = daw_info.get("mac")
        if app_path:
            print_info(f"Opening {daw_info['name']} with {session_file.name}...")
            subprocess.run(["open", "-a", app_path, str(session_file)])
            return True
    elif system == "Windows": # windows
        exe_path = daw_info.get("win")
        if exe_path:
            print_info(f"Opening {daw_info['name']} with {session_file.name}...")
            subprocess.run([exe_path, str(session_file)])
            return True
    
    print_warning(f"Auto-open not configured for {daw_info['name']} on {system}")
    print_info(f"Session file located at: {session_file}")
    return False