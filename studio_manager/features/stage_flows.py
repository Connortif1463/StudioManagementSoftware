"""Project stage management flows"""
from pathlib import Path
from rich.panel import Panel
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker

def manage_project_stage_flow(project_path: Path):
    """Manage the stage of a project"""
    clear_screen()
    tracker = ProjectTracker(project_path)
    
    console.print(Panel.fit(f"[bold white]Project Stage: {tracker.get_current_stage().upper()}[/bold white]", style="white"))
    
    console.print("\n[bold]Stages:[/bold]")
    for i, stage in enumerate(ProjectTracker.STAGES, 1):
        current = " [current]" if stage == tracker.get_current_stage() else ""
        console.print(f"  [cyan]{i}[/cyan] - {stage}{current}")
    
    choice = input("\nSelect new stage (or 'b' to go back): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(ProjectTracker.STAGES):
            new_stage = ProjectTracker.STAGES[idx]
            if new_stage != tracker.get_current_stage():
                notes = input("Any notes about this stage change? (press Enter to skip): ").strip()
                tracker.update_stage(new_stage, notes)
                input("\nPress Enter to continue...")

def set_release_date_flow():
    """Flow for setting expected release date on a project - excludes finished projects"""
    from rich.table import Table
    from ..utils.helpers import list_all_projects
    from ..cli.prompts import get_choice
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        return
    
    active_songs = []
    for p in projects:
        if (p["path"] / ".album.json").exists():
            continue
        tracker = ProjectTracker(p["path"])
        stage = tracker.get_current_stage()
        if stage != "finished":
            active_songs.append((p, tracker))
    
    if not active_songs:
        print_warning("No active song projects found")
        return
    
    table = Table(title="Set Release Date", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Current Release", style="dim")
    
    for idx, (project, tracker) in enumerate(active_songs, 1):
        current = tracker.data.get("release_date", "Not set")
        if current:
            current = current[:10]
        table.add_row(str(idx), project["project"], project["artist"], tracker.get_current_stage(), current)
    
    console.print(table)
    
    proj_choice = input("\nSelect project number (or 'b' to go back): ").strip()
    if proj_choice.lower() != 'b' and proj_choice.isdigit():
        idx = int(proj_choice) - 1
        if 0 <= idx < len(active_songs):
            project, tracker = active_songs[idx]
            while True:
                release_date = input("Enter expected release date (YYYY-MM-DD) or press Enter to cancel: ").strip()
                if not release_date:
                    break
                if tracker.set_release_date(release_date):
                    print_success(f"Release date set for {project['project']}")
                    break
                else:
                    print_error("Invalid date format. Please use YYYY-MM-DD")
                    continue