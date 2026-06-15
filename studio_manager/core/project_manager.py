import logging
from pathlib import Path
from ..cli.display import print_success, print_error
from ..utils.helpers import get_project_path
from .file_system import create_project_folders, create_project_subfolders
from .session_manager import create_session_from_template

logging.basicConfig(level=logging.INFO)

def create_project(name: str, project_type: str, artist: str, daw: str = "") -> bool:
    """Create a new project"""
    try:
        if not name or not artist:
            raise ValueError("Project name and artist name cannot be empty")
        
        project_dir = create_project_folders(artist, name)
        print_success(f"Project folder created/verified: {project_dir}")
        
        if project_type == "S":
            if not daw:
                raise ValueError("DAW selection required for song projects")
            
            create_project_subfolders(project_dir)
            return create_session_from_template(name, artist, daw)
        elif project_type == "A":
            print_success("Album directory created successfully")
            return True
        else:
            raise ValueError(f"Invalid project type: {project_type}")
            
    except Exception as e:
        logging.error(f"Failed to create project: {e}")
        print_error(f"Error creating project: {e}")
        return False