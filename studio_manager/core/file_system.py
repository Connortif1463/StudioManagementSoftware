# studio_manager/core/file_system.py

import logging
import shutil
import json
from pathlib import Path
from rich.panel import Panel
from rich.tree import Tree
from ..cli.display import console, print_success, print_error, clear_screen
from ..utils.helpers import sanitize_filename, format_file_size, list_all_projects
from ..utils.constants import PROJECT_SUBFOLDERS, SUBFOLDER_PURPOSES, DAW_PATHS

logging.basicConfig(level=logging.WARNING)

# Don't import ProjectTracker here to avoid circular import
# We'll use a simple function to get stage info


def get_project_stage(project_path: Path) -> str:
    """Get the current stage of a project without importing ProjectTracker"""
    tracker_file = project_path / ".project_tracker.json"
    if tracker_file.exists():
        try:
            with open(tracker_file, 'r') as f:
                data = json.load(f)
                return data.get("current_stage", "production")
        except:
            pass
    return "production"


def create_project_folders(artist: str, name: str) -> Path:
    """Create the base project folders"""
    artist = sanitize_filename(artist)
    name = sanitize_filename(name)
    
    base_path = Path.cwd() / "artists" / artist
    project_dir = base_path / name
    
    base_path.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    
    return project_dir


def create_project_subfolders(project_dir: Path):
    """Create production, mix, and master subfolders"""
    for folder in PROJECT_SUBFOLDERS:
        folder_path = project_dir / folder
        folder_path.mkdir(exist_ok=True)
        
        # Create README file
        readme_path = folder_path / "README.txt"
        if not readme_path.exists():
            readme_path.write_text(f"{folder.upper()} FOLDER\n{SUBFOLDER_PURPOSES[folder]}\nCreated: {Path.cwd()}")
    
    print_success("Production/Mix/Master folders created")


def print_directory_tree(path: Path, max_depth: int = 3):
    """Print a tree view of the directory structure"""
    if not path.exists():
        print_error(f"Path does not exist: {path}")
        return
    
    if not path.is_dir():
        print_error(f"Path is not a directory: {path}")
        return
    
    tree = Tree(f"[bold white]{path.name}[/bold white]")
    
    def add_to_tree(directory: Path, tree_node: Tree, current_depth: int = 0):
        if current_depth >= max_depth:
            tree_node.add("[dim]...[/dim]")
            return
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue
                
                if item.is_dir():
                    if item.name in ["production", "mix", "master"]:
                        branch = tree_node.add(f"[yellow]{item.name}/[/yellow] [dim]({item.name.capitalize()} Phase)[/dim]")
                        add_to_tree(item, branch, current_depth + 1)
                    elif item.name in ["ableton", "protools", "logic"]:
                        branch = tree_node.add(f"[cyan]{item.name}/[/cyan] [dim](DAW Session)[/dim]")
                        add_to_tree(item, branch, current_depth + 1)
                    else:
                        branch = tree_node.add(f"[cyan]{item.name}/[/cyan]")
                        add_to_tree(item, branch, current_depth + 1)
                else:
                    size_str = format_file_size(item.stat().st_size)
                    if item.suffix in ['.als', '.ptx', '.logicx']:
                        tree_node.add(f"[green]{item.name}[/green] [dim]({size_str})[/dim] [dim]🎛️[/dim]")
                    elif item.suffix in ['.wav', '.aif', '.aiff', '.mp3']:
                        tree_node.add(f"[cyan]{item.name}[/cyan] [dim]({size_str})[/dim]")
                    else:
                        tree_node.add(f"[dim]{item.name}[/dim] [dim]({size_str})[/dim]")
        except PermissionError:
            tree_node.add("[red]Permission denied[/red]")
    
    add_to_tree(path, tree)
    console.print(tree)


def print_full_project_tree():
    """Print tree view of all projects with current stage highlighted"""
    artists_path = Path.cwd() / "artists"
    
    if not artists_path.exists():
        print_error("No projects found. Create a project first.")
        return
    
    clear_screen()
    console.print(Panel.fit("[bold white]Project Directory Structure[/bold white]", style="white"))
    
    root = Tree(f"[bold white]{artists_path.name}[/bold white] [dim](Projects Root)[/dim]")
    
    try:
        for artist_dir in sorted(artists_path.iterdir()):
            if artist_dir.is_dir() and not artist_dir.name.startswith('.'):
                artist_branch = root.add(f"[cyan]{artist_dir.name}/[/cyan] [dim](Artist)[/dim]")
                
                for project_dir in sorted(artist_dir.iterdir()):
                    if project_dir.is_dir() and not project_dir.name.startswith('.'):
                        # Use the simple function instead of ProjectTracker
                        current_stage = get_project_stage(project_dir)
                        
                        project_branch = artist_branch.add(f"[green]{project_dir.name}/[/green] [dim](Project)[/dim]")
                        
                        for stage_folder in ["production", "mix", "master"]:
                            stage_path = project_dir / stage_folder
                            if stage_path.exists() and stage_path.is_dir():
                                if stage_folder == current_stage:
                                    stage_branch = project_branch.add(f"[bold green]{stage_folder}/[/bold green] [dim]({stage_folder.capitalize()} Phase)[/dim]")
                                else:
                                    stage_branch = project_branch.add(f"[yellow]{stage_folder}/[/yellow] [dim]({stage_folder.capitalize()} Phase)[/dim]")
                                
                                try:
                                    for item in sorted(stage_path.iterdir()):
                                        if item.is_file() and not item.name.startswith('.'):
                                            if item.suffix in ['.als', '.ptx', '.logicx']:
                                                stage_branch.add(f"[green]{item.name}[/green] [dim](DAW Session)[/dim]")
                                            elif item.suffix in ['.wav', '.aif', '.aiff', '.mp3']:
                                                stage_branch.add(f"[cyan]{item.name}[/cyan]")
                                            elif item.name == "README.txt":
                                                pass
                                            else:
                                                stage_branch.add(f"[dim]{item.name}[/dim]")
                                except PermissionError:
                                    stage_branch.add("[red]Permission denied[/red]")
                        
                        finished_path = project_dir / "finished"
                        if finished_path.exists() and finished_path.is_dir():
                            finished_branch = project_branch.add(f"[dim]finished/[/dim] [dim](Completed)[/dim]")
                            for item in finished_path.iterdir():
                                if item.is_file() and not item.name.startswith('.'):
                                    finished_branch.add(f"[dim]{item.name}[/dim]")
        
        console.print(root)
        
        total_artists = sum(1 for d in artists_path.iterdir() if d.is_dir() and not d.name.startswith('.'))
        total_projects = len(list_all_projects())
        
        console.print(f"\n[bold]Summary:[/bold]")
        console.print(f"  Total Artists: [green]{total_artists}[/green]")
        console.print(f"  Total Projects: [green]{total_projects}[/green]")
        
    except PermissionError:
        print_error("Permission denied to read some directories")
    except Exception as e:
        logging.error(f"Error printing project tree: {e}")
        print_error(f"Error printing project tree: {e}")