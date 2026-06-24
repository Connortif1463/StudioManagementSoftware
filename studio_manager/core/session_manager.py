# studio_manager/core/session_manager.py

import traceback
import logging
import shutil
import json
from pathlib import Path
from typing import List, Optional
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..cli.display import console, print_success, print_error, print_warning, print_info
from ..cli.prompts import get_confirmation
from ..utils.constants import DAW_PATHS

logging.basicConfig(level=logging.WARNING)

TEMPLATES_BASE = Path.cwd() / "templates"


def get_template_config_file() -> Path:
    """Get the template config file path - resolves at runtime"""
    return Path.cwd() / ".template_config.json"


def load_template_config() -> dict:
    """Load the template configuration"""
    config_file = get_template_config_file()
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_template_config(config: dict):
    """Save the template configuration - creates parent directory if needed"""
    config_file = get_template_config_file()
    try:
        # Ensure the parent directory exists
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        # If we can't save, just log and continue - not critical
        logging.debug(f"Could not save template config: {e}")
        pass


def get_template_path(daw: str) -> Path:
    """Get the template path for a given DAW"""
    # First check if we have a saved custom path
    config = load_template_config()
    if daw in config:
        saved_path = Path(config[daw])
        if saved_path.exists():
            return saved_path
    
    # Otherwise use the default path
    if daw == "A" or daw == "Ableton":
        return TEMPLATES_BASE / "ableton templates" / "ableton template.als"
    elif daw == "P" or daw == "Pro Tools":
        return TEMPLATES_BASE / "protools templates" / "protools template.ptx"
    elif daw == "L" or daw == "Logic":
        return TEMPLATES_BASE / "logic templates" / "logic template.logicx"
    return None


def clean_path(path_str: str) -> str:
    """Clean a path string by removing quotes and extra whitespace"""
    path_str = path_str.strip()
    if path_str.startswith('"') and path_str.endswith('"'):
        path_str = path_str[1:-1]
    elif path_str.startswith("'") and path_str.endswith("'"):
        path_str = path_str[1:-1]
    return path_str.strip()


def find_template_files(directory: Path, extension: str, max_depth: int = 5) -> List[Path]:
    """
    Recursively find all template files with a given extension in a directory.
    Searches up to max_depth levels deep.
    """
    templates = []
    
    if not directory.exists():
        return templates
    
    def walk_dir(path: Path, depth: int = 0):
        if depth > max_depth:
            return
        
        try:
            for item in path.iterdir():
                if item.is_file():
                    if item.suffix.lower() == f".{extension.lower()}" or item.suffix.lower() == f".{extension}":
                        templates.append(item)
                elif item.is_dir():
                    walk_dir(item, depth + 1)
        except (PermissionError, OSError):
            pass
    
    walk_dir(directory)
    
    unique_templates = list(set(templates))
    return sorted(unique_templates, key=lambda x: x.stat().st_mtime, reverse=True)


def suggest_template_path(daw: str) -> Optional[Path]:
    """Try to find a template file automatically by recursively searching."""
    daw_info = DAW_PATHS.get(daw, {})
    ext = daw_info.get("ext", "").lstrip(".")
    
    if not ext:
        return None
    
    search_locations = [
        Path.cwd() / "templates",
        Path.cwd(),
        Path.cwd() / ".." / "templates",
    ]
    
    all_found = []
    
    for location in search_locations:
        if location.exists():
            found = find_template_files(location, ext)
            all_found.extend(found)
    
    # Also search for DAW-specific folders by name
    for search_dir in [
        "ableton templates", "protools templates", "logic templates",
        "ableton", "protools", "logic",
        "templates", "Template", "Templates"
    ]:
        location = Path.cwd() / search_dir
        if location.exists():
            found = find_template_files(location, ext)
            all_found.extend(found)
    
    unique_found = list(set(all_found))
    
    if unique_found:
        return sorted(unique_found, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    return None


def check_template(daw: str) -> bool:
    """Check if the template for a specific DAW exists"""
    template_path = get_template_path(daw)
    if template_path and template_path.is_file():
        return True
    return False


def ensure_template_exists(daw: str) -> Optional[Path]:
    """Ensure a template exists for the given DAW."""
    # First check if we have a valid template from saved config
    template_path = get_template_path(daw)
    if template_path and template_path.exists():
        return template_path
    
    # Try to auto-detect recursively
    print_info(f"Searching for template for {daw}...")
    found_path = suggest_template_path(daw)
    
    if found_path:
        config = load_template_config()
        config[daw] = str(found_path)
        save_template_config(config)
        print_success(f"Found template: {found_path}")
        return found_path
    
    # If still not found, try to create a default empty template
    default_path = get_template_path(daw)
    if default_path:
        default_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            default_path.touch()
            print_warning(f"No template found. Created empty template: {default_path}")
            print_warning("Please replace this with a real template file.")
            config = load_template_config()
            config[daw] = str(default_path)
            save_template_config(config)
            return default_path
        except:
            pass
    
    print_error(f"Could not find or create template for {daw}")
    return None


def create_session_from_template(name: str, artist: str, daw: str, stage: str = "production") -> bool:
    """Create a new session from template inside the specified stage folder."""
    try:
        template_path = ensure_template_exists(daw)
        
        if not template_path:
            print_error(f"Could not find or create template for {daw}")
            return False
        
        daw_info = DAW_PATHS.get(daw, {})
        if not daw_info:
            print_error(f"Unknown DAW: {daw}")
            return False
        
        daw_folder = daw_info.get("folder", "")
        if not daw_folder:
            print_error(f"No folder defined for DAW: {daw}")
            return False
        
        session_dir = Path.cwd() / "artists" / artist / name / stage / daw_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        ext = daw_info.get("ext", "")
        session_filename = f"{name}_{stage}_session{ext}"
        destination = session_dir / session_filename
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as progress:
            task = progress.add_task(f"[white]Copying template to {stage} folder...", total=None)
            shutil.copy2(template_path, destination)
            progress.update(task, completed=True)
        
        print_success(f"Session created: {destination}")
        logging.debug(f"Session created: {name} for {artist} using {daw} in {stage} stage")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create session: {e}")
        print_error(f"Error creating session: {e}")
        traceback.print_exc()
        return False


def diagnose_template_issue():
    """Diagnose template issues and print helpful info"""
    print_info("\n[bold]Template Diagnostics:[/bold]")
    print_info(f"Working directory: {Path.cwd()}")
    print_info(f"Templates base: {TEMPLATES_BASE}")
    print_info(f"Config file: {get_template_config_file()}")
    
    if TEMPLATES_BASE.exists():
        print_info(f"Templates folder exists: Yes")
        print_info("Searching for templates recursively...")
        
        found = find_template_files(TEMPLATES_BASE, "als")
        if found:
            print_info(f"Found {len(found)} .als files:")
            for f in found[:10]:
                try:
                    rel_path = f.relative_to(Path.cwd())
                    print_info(f"  📄 {rel_path}")
                except:
                    print_info(f"  📄 {f}")
            if len(found) > 10:
                print_info(f"  ... and {len(found) - 10} more")
        else:
            print_warning("No .als files found in templates folder")
    else:
        print_warning(f"Templates folder does NOT exist: {TEMPLATES_BASE}")
        print_info("Create the templates folder and add template files:")
        print_info(f"  {TEMPLATES_BASE}/ableton templates/ableton template.als")
        print_info(f"  {TEMPLATES_BASE}/protools templates/protools template.ptx")
        print_info(f"  {TEMPLATES_BASE}/logic templates/logic template.logicx")