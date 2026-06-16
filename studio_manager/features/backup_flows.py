"""Backup management flows"""
from pathlib import Path
from rich.panel import Panel
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info
from .project_tracker import ProjectTracker
from ..utils.helpers import list_all_projects

def backup_project_flow(project_path: Path):
    """Create or restore project backups"""
    clear_screen()
    tracker = ProjectTracker(project_path)
    
    console.print(Panel.fit("[bold white]Project Backup[/bold white]", style="white"))
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Create new backup")
    console.print("  2 - List existing backups")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        engineer = input("Enter engineer name for this backup (or press Enter to skip): ").strip()
        if not engineer:
            engineer = None
        
        custom_path = input("Enter backup path (or press Enter for auto-generated): ").strip()
        if custom_path:
            tracker.create_backup(Path(custom_path), engineer)
        else:
            tracker.create_backup(engineer=engineer)
        input("\nPress Enter to continue...")
    elif choice == "2":
        tracker.list_backups()
        input("\nPress Enter to continue...")

def global_backup_flow():
    """Backup all projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Backup System[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found to backup")
        input("\nPress Enter to continue...")
        return
    
    console.print(f"\n[bold]Backup Options:[/bold]")
    console.print("  [cyan]1[/cyan] - Backup a single project")
    console.print("  [cyan]2[/cyan] - Backup all projects")
    console.print("  [cyan]b[/cyan] - Go back")
    
    backup_choice = input("\nSelect option: ").strip()
    
    if backup_choice == "1":
        projects = list_all_projects()
        if projects:
            print("\n[bold]Select project to backup:[/bold]")
            for i, p in enumerate(projects[:10], 1):
                print(f"  {i}. {p['artist']} - {p['project']}")
            proj_choice = input("\nSelect project: ").strip()
            if proj_choice.isdigit() and 1 <= int(proj_choice) <= len(projects[:10]):
                backup_project_flow(projects[int(proj_choice)-1]["path"])
        else:
            print_warning("No projects found")
    elif backup_choice == "2":
        for project in projects:
            print_info(f"\nBacking up {project['artist']} - {project['project']}...")
            tracker = ProjectTracker(project["path"])
            tracker.create_backup()
        print_success(f"\nBackup complete! All {len(projects)} projects backed up.")
        input("\nPress Enter to continue...")
    elif backup_choice == 'b':
        return