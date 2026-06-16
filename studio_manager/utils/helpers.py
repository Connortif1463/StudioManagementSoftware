import os
from pathlib import Path
from typing import List

def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def sanitize_filename(filename: str) -> str:
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    from .constants import SIZE_UNITS
    
    for unit in SIZE_UNITS:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_project_path(artist: str, project_name: str) -> Path:
    """Get the full path for a project"""
    return Path.cwd() / "artists" / sanitize_filename(artist) / sanitize_filename(project_name)

def list_all_projects() -> List[dict]:
    """List all projects in the artists directory (excluding backups)"""
    projects = []
    artists_path = Path.cwd() / "artists"
    
    if not artists_path.exists():
        return projects
    
    for artist_dir in artists_path.iterdir():
        if artist_dir.is_dir():
            for project_dir in artist_dir.iterdir():
                if project_dir.is_dir():
                    # Skip backup folders (folders with "_backup_" in the name)
                    if "_backup_" in project_dir.name:
                        continue
                    projects.append({
                        "artist": artist_dir.name,
                        "project": project_dir.name,
                        "path": project_dir,
                        "modified": project_dir.stat().st_mtime
                    })
    
    return sorted(projects, key=lambda x: x["modified"], reverse=True)