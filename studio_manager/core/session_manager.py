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
    if daw == "A":
        return TEMPLATES_BASE / "ableton templates" / "ableton template.als"
    elif daw == "P":
        return TEMPLATES_BASE / "protools templates" / "protools template.ptx"
    elif daw == "L":
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
        
        daw_info = DAW_PATHS.get(daw, {})
        daw_folder = daw_info.get("folder", "")
        template_path = get_template_path(daw)
        
        if not template_path:
            print_error(f"No template found for DAW: {daw}")
            return False
        
        # Create session inside the stage folder (production/mix/master)
        session_dir = Path.cwd() / "artists" / artist / name / stage / daw_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
            task = progress.add_task(f"[white]Copying {daw_folder} template to {stage} folder...", total=None)
            destination = session_dir / f"{name}_{stage}_session{daw_info.get('ext', '')}"
            shutil.copy2(template_path, destination)
            progress.update(task, completed=True)
        
        print_success(f"{daw_folder.capitalize()} template copied to: {destination}")
        logging.debug(f"Session created: {name} for {artist} using {daw} in {stage} stage")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create session: {e}")
        print_error(f"Error creating session: {e}")
        return False