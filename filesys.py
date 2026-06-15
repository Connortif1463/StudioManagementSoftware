import os
import logging
from pathlib import Path
from typing import Tuple
from rich.console import Console
from rich.panel import Panel
import sessions

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('project_manager.log'),
        logging.StreamHandler()
    ]
)

console = Console()

class FileSystemError(Exception):
    """Custom exception for filesystem operations"""
    pass

def createNewProject(name: str, project_type: str, artist: str, daw: str) -> bool:
    """Create a new project with proper error handling"""
    try:
        # Validate inputs
        if not name or not artist:
            raise ValueError("Project name and artist name cannot be empty")
        
        # Sanitize names for filesystem
        name = sanitize_filename(name)
        artist = sanitize_filename(artist)
        
        base_path = Path.cwd() / "artists" / artist
        project_dir = base_path / name
        
        # Create directories with exist_ok=True for safety
        base_path.mkdir(parents=True, exist_ok=True)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(Panel.fit(
            f"[green]Project folder created/verified: {project_dir}[/green]",
            title="Success"
        ))
        
        if project_type == "S":
            if not daw:
                raise ValueError("DAW selection required for song projects")
            return sessions.createNewSessionFromTemplate(name, artist, daw)
        elif project_type == "A":
            console.print("[cyan]Album directory created successfully[/cyan]")
            return True
        else:
            raise ValueError(f"Invalid project type: {project_type}")
            
    except Exception as e:
        logging.error(f"Failed to create project: {e}")
        console.print(f"[red]Error creating project: {e}[/red]")
        return False

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def artistFolderExists(artist_directory: str) -> Tuple[bool, str]:
    """Check if artist folder exists with detailed status"""
    path = Path(artist_directory)
    if path.exists() and path.is_dir():
        logging.info(f"Artist folder found: {artist_directory}")
        return True, "Artist folder exists"
    else:
        logging.warning(f"Artist folder not found: {artist_directory}")
        return False, "Artist folder not found"

def projectFolderExists(project_directory: str) -> Tuple[bool, str]:
    """Check if project folder exists with detailed status"""
    path = Path(project_directory)
    if path.exists() and path.is_dir():
        logging.info(f"Project folder found: {project_directory}")
        return True, "Project folder exists"
    else:
        logging.warning(f"Project folder not found: {project_directory}")
        return False, "Project folder not found"
    
def dawFolderExists(project_directory: str, daw: str) -> Tuple[bool, str]:
    """Check if DAW folder exists with detailed status"""
    daw_path = Path(project_directory) / daw
    if daw_path.exists() and daw_path.is_dir():
        logging.info(f"DAW folder found: {daw_path}")
        return True, f"{daw} folder exists"
    else:
        return False, f"{daw} folder not found"