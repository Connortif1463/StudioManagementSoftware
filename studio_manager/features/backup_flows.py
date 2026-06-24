# studio_manager/features/backup_flows.py

"""Backup management flows"""
from pathlib import Path
from rich.panel import Panel
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info
from ..cli.prompts import get_raw_input
from .project_tracker import ProjectTracker
from ..utils.helpers import list_all_projects


def backup_project_flow(project_path: Path):
    """Create or restore project backups"""
    clear_screen()
    tracker = ProjectTracker(project_path)
    
    console.print(Panel.fit("[bold white]Project Backup[/bold white]", style="white"))
    
    # Shows current stage
    console.print(f"\nProject: [green]{tracker.data['project_name']}[/green]")
    console.print(f"Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
    
    console.print("\n[bold]Backup Options:[/bold]")
    console.print("  [cyan]1[/cyan] - Backup current stage")
    console.print("  [cyan]2[/cyan] - Backup a specific stage")
    console.print("  [cyan]3[/cyan] - List existing backups")
    console.print("  [blue]b[/blue] - Go back")
    
    choice = get_raw_input("\nSelect option: ").strip()
    
    if choice == "1":
        engineer = get_raw_input("Enter engineer name for this backup (or press Enter to skip): ").strip()
        if not engineer:
            engineer = None
        
        custom_path = get_raw_input("Enter backup path (or press Enter for auto-generated): ").strip()
        if custom_path:
            tracker.create_backup(Path(custom_path), engineer)
        else:
            tracker.create_backup(engineer=engineer)
        input("\nPress Enter to continue...")
    
    elif choice == "2":
        console.print("\n[bold]Available Stages:[/bold]")
        for i, stage in enumerate(ProjectTracker.STAGES, 1):
            stage_path = project_path / stage
            exists = "✓" if stage_path.exists() else "✗"
            current = " [current]" if stage == tracker.get_current_stage() else ""
            console.print(f"  [cyan]{i}[/cyan] - {stage}{current} [{exists}]")
        
        stage_choice = get_raw_input("\nSelect stage number: ").strip()
        if stage_choice.isdigit():
            idx = int(stage_choice) - 1
            if 0 <= idx < len(ProjectTracker.STAGES):
                selected_stage = ProjectTracker.STAGES[idx]
                engineer = get_raw_input("Enter engineer name (or press Enter to skip): ").strip()
                if not engineer:
                    engineer = None
                custom_path = get_raw_input("Enter backup path (or press Enter for auto-generated): ").strip()
                if custom_path:
                    tracker.create_backup(Path(custom_path), engineer, selected_stage)
                else:
                    tracker.create_backup(engineer=engineer, stage=selected_stage)
                input("\nPress Enter to continue...")
        else:
            print_error("Invalid stage selection")
            input("\nPress Enter to continue...")
    
    elif choice == "3":
        tracker.list_backups()
        input("\nPress Enter to continue...")
    
    elif choice == 'b':
        return
    else:
        print_error("Invalid option")
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
    console.print("  [blue]b[/blue] - Go back")
    
    backup_choice = get_raw_input("\nSelect option: ").strip()
    
    if backup_choice == "1":
        projects = list_all_projects()
        if projects:
            console.print("\n[bold]Select project to backup:[/bold]")
            for i, p in enumerate(projects[:10], 1):
                console.print(f"  [cyan]{i}[/cyan] - {p['artist']} - {p['project']}")
            if len(projects) > 10:
                console.print(f"  [dim]... and {len(projects) - 10} more[/dim]")
            
            proj_choice = get_raw_input("\nSelect project: ").strip()
            if proj_choice.isdigit() and 1 <= int(proj_choice) <= len(projects[:10]):
                backup_project_flow(projects[int(proj_choice)-1]["path"])
            else:
                print_error("Invalid selection")
                input("\nPress Enter to continue...")
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
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")