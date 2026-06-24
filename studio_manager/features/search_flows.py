"""Search and filtering flows"""
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker
from ..utils.helpers import get_project_path, list_all_projects
from .session_memo import SessionMemo

def search_projects_flow():
    """Search for projects by name, artist, or stage"""
    clear_screen()
    console.print(Panel.fit("[bold white]Search Projects[/bold white]", style="white"))
    
    console.print("\n[bold]Search by:[/bold]")
    console.print("  [cyan]1[/cyan] - Project name")
    console.print("  [cyan]2[/cyan] - Artist name")
    console.print("  [cyan]3[/cyan] - Stage (production/mixing/mastering/finished)")
    console.print("  [blue]b[/blue] - Go back")
    
    search_type = input("\nSelect option: ").strip()
    
    if search_type == 'b':
        return
    elif search_type == "1":
        search_term = input("Enter project name (or partial name): ").strip().lower()
        field = "name"
    elif search_type == "2":
        search_term = input("Enter artist name (or partial name): ").strip().lower()
        field = "artist"
    elif search_type == "3":
        search_term = input("Enter stage (production/mixing/mastering/finished): ").strip().lower()
        field = "stage"
    else:
        print_error("Invalid option")
        return
    
    all_projects = list_all_projects()
    results = []
    
    for project in all_projects:
        if (project["path"] / ".album.json").exists():
            continue
        
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        
        if field == "name" and search_term in project["project"].lower():
            results.append((project, stage))
        elif field == "artist" and search_term in project["artist"].lower():
            results.append((project, stage))
        elif field == "stage" and search_term == stage:
            results.append((project, stage))
    
    if not results:
        print_warning(f"No projects found matching '{search_term}'")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Search Results: '{search_term}'", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Created", style="dim")
    
    for idx, (project, stage) in enumerate(results[:20], 1):
        table.add_row(
            str(idx),
            project["project"],
            project["artist"],
            stage,
            project.get("date_created_pretty", "Unknown")[:16]
        )
    
    console.print(table)
    
    if len(results) > 20:
        console.print(f"[dim]... and {len(results) - 20} more results[/dim]")
    
    if results and get_confirmation("\nView project details?"):
        choice = input("Enter project number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results[:20]):
                project, stage = results[idx]
                from .project_flows import show_song_project_details
                show_song_project_details({
                    "project": project["project"],
                    "artist": project["artist"],
                    "path": project["path"]
                })

def filter_by_category_flow():
    """Filter active songs by project category"""
    clear_screen()
    console.print(Panel.fit("[bold white]Filter by Category[/bold white]", style="white"))
    
    console.print("\n[bold]Categories:[/bold]")
    console.print("  [cyan]1[/cyan] - Studio Sessions")
    console.print("  [cyan]2[/cyan] - Live Recordings")
    console.print("  [cyan]3[/cyan] - Demos")
    console.print("  [cyan]4[/cyan] - Tests")
    console.print("  [cyan]5[/cyan] - Fun")
    console.print("  [cyan]a[/cyan] - All categories")
    console.print("  [cyan]b[/cyan] - Go back")
    
    choice = input("\nSelect category: ").strip().lower()
    
    category_map = {
        "1": "studio_session",
        "2": "live_recording",
        "3": "demo",
        "4": "test",
        "5": "fun",
        "a": "all"
    }
    
    if choice == 'b':
        return
    if choice not in category_map:
        print_error("Invalid option")
        return
    
    selected_category = category_map[choice]
    
    projects = list_all_projects()
    filtered = []
    
    for project in projects:
        if (project["path"] / ".album.json").exists():
            continue
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        if stage == "finished":
            continue
        category = tracker.get_project_category()
        if selected_category == "all" or category == selected_category:
            filtered.append((project, stage))
    
    if not filtered:
        print_info(f"No projects found in this category")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Projects - {selected_category.replace('_', ' ').title() if selected_category != 'all' else 'All Categories'}", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    
    for idx, (project, stage) in enumerate(filtered, 1):
        table.add_row(str(idx), project["project"], project["artist"], stage)
    
    console.print(table)
    input("\nPress Enter to continue...")