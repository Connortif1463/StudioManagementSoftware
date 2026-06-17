import traceback
import logging
import shutil
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..cli.display import console, print_success, print_error, print_warning
from ..utils.constants import DAW_PATHS

logging.basicConfig(level=logging.WARNING)

TEMPLATES_BASE = Path.cwd() / "templates"

def get_template_path(daw: str) -> Path:
    """Get the template path for a given DAW"""
    if daw == "A" or daw == "Ableton":
        return TEMPLATES_BASE / "ableton templates" / "ableton template.als"
    elif daw == "P" or daw == "Pro Tools":
        return TEMPLATES_BASE / "protools templates" / "protools template.ptx"
    elif daw == "L" or daw == "Logic":
        return TEMPLATES_BASE / "logic templates" / "logic template.logicx"
    return None

def check_templates() -> bool:
    """Check if session templates exist"""
    templates_exist = all([
        get_template_path("P") and get_template_path("P").is_file(),
        get_template_path("A") and get_template_path("A").is_file(),
        get_template_path("L") and get_template_path("L").is_file()
    ])
    
    if templates_exist:
        print_success("All session templates found")
        return True
    else:
        print_warning("Templates not found")
        return False

def create_session_from_template(name: str, artist: str, daw: str, stage: str = "production") -> bool:
    """
    Create a new session from template inside the specified stage folder.
    Stages: production, mix, master
    """
    try:
        if not check_templates():
            return False
        
        # Get DAW info using the letter code directly
        daw_info = DAW_PATHS.get(daw, {})  # daw is "A", "P", or "L"
        if not daw_info:
            print_error(f"Unknown DAW: {daw}")
            return False
        
        daw_folder = daw_info.get("folder", "")
        if not daw_folder:
            print_error(f"No folder defined for DAW: {daw}")
            return False
        
        template_path = get_template_path(daw)  # This can handle "A" or "Ableton"
        if not template_path or not template_path.exists():
            print_error(f"Template not found for DAW: {daw}")
            return False
        
        # Create session inside the stage folder
        session_dir = Path.cwd() / "artists" / artist / name / stage / daw_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session filename with stage info
        ext = daw_info.get("ext", "")
        session_filename = f"{name}_{stage}_session{ext}"
        destination = session_dir / session_filename
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
            task = progress.add_task(f"[white]Copying {daw_folder} template to {stage} folder...", total=None)
            shutil.copy2(template_path, destination)
            progress.update(task, completed=True)
        
        print_success(f"{daw_folder.capitalize()} template copied to: {destination}")
        logging.debug(f"Session created: {name} for {artist} using {daw} in {stage} stage")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create session: {e}")
        print_error(f"Error creating session: {e}")
        traceback.print_exc()
        return False