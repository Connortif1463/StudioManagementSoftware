"""Project browser flows"""
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker, AlbumManager
from .daw_integration import open_daw_project
from .session_memo import prompt_for_session_memo
from .project_flows import manage_project_stage_flow
from .backup_flows import backup_project_flow
from ..utils.helpers import list_all_projects

def show_album_contents(album_path: Path):
    """Display the contents of an album (its songs)"""
    clear_screen()
    manager = AlbumManager(album_path)
    
    console.print(Panel.fit(f"[bold white]Album: {manager.data['name']}[/bold white]", style="white"))
    
    if not manager.data["songs"]:
        print_warning("\nNo songs in this album yet")
        if get_confirmation("\nAdd songs to this album?"):
            from .album_flows import add_songs_to_album_flow
            add_songs_to_album_flow(album_path)
    else:
        table = Table(title="Track Listing", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Song Name", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Path", style="dim")
        
        for idx, song in enumerate(manager.data["songs"], 1):
            table.add_row(str(idx), song["name"], song["artist"], song["path"])
        
        console.print(table)
        
        console.print("\n[bold]Options:[/bold]")
        console.print("  1 - Add songs to album")
        console.print("  2 - Remove song from album")
        console.print("  3 - Reorder songs")
        console.print("  b - Go back")
        
        action = input("\nSelect option: ").strip()
        
        if action == "1":
            from .album_flows import add_songs_to_album_flow
            add_songs_to_album_flow(album_path)
        elif action == "2":
            idx = int(input(f"Select song to remove (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= idx < len(manager.data["songs"]):
                manager.remove_song(Path(manager.data["songs"][idx]["path"]))
                show_album_contents(album_path)
        elif action == "3":
            manager.list_songs()
            song_idx = int(input(f"Select song to move (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= song_idx < len(manager.data["songs"]):
                new_pos = int(input("New position: "))
                song_path = Path(manager.data["songs"][song_idx]["path"])
                manager.reorder_song(song_path, new_pos)
                show_album_contents(album_path)

def show_song_project_details(selected: dict, history):
    """Show details for a song project"""
    clear_screen()
    console.print(Panel.fit("[bold white]Project Details[/bold white]", style="white"))
    console.print(f"\n  Project: [green]{selected['project']}[/green]")
    console.print(f"  Artist: [green]{selected['artist']}[/green]")
    console.print(f"  Path: [dim]{selected['path']}[/dim]")
    
    tracker = ProjectTracker(selected["path"])
    console.print(f"  Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
    console.print(f"  Category: [green]{tracker.get_project_category().replace('_', ' ').title()}[/green]")
    
    if tracker.data.get("release_date"):
        console.print(f"  Expected Release: [yellow]{tracker.data['release_date'][:10]}[/yellow]")
    
    project_path = selected["path"]
    daw_found = None
    for daw_code, daw_info in {"A": "ableton", "P": "protools", "L": "logic"}.items():
        if (project_path / daw_info).exists():
            daw_found = daw_code
            break
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Open DAW session")
    console.print("  2 - View/record session memo")
    console.print("  3 - Manage project stage")
    console.print("  4 - Create backup")
    console.print("  5 - Set expected release date")
    console.print("  b - Go back")
    
    action = input("\nSelect option: ").strip()
    
    if action == "1" and daw_found:
        try:
            open_daw_project(project_path, daw_found, selected['project'])
            print_info("\nDAW session closed.")
            prompt_for_session_memo(project_path, history)
        except Exception as e:
            print_error(f"Failed to open DAW. Error logged to session_logs/")
            print_info("You can still record session notes manually.")
            if get_confirmation("Record session notes anyway?"):
                prompt_for_session_memo(project_path, history, is_manual=True)
    elif action == "2":
        prompt_for_session_memo(project_path, history, is_manual=True)
    elif action == "3":
        manage_project_stage_flow(project_path)
    elif action == "4":
        backup_project_flow(project_path)
    elif action == "5":
        from .tasks_flows import set_release_date_flow
        set_release_date_flow()
        input("\nPress Enter to continue...")

def project_browser_flow(history):
    """Project Browser - browse and search all projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Project Browser[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("\nNo projects found. Create a project first.")
        input("\nPress Enter to continue...")
        return
    
    active_projects = []
    finished_projects = []
    
    for project in projects:
        is_album = (project["path"] / ".album.json").exists()
        if is_album:
            active_projects.append((project, "Album", "N/A"))
        else:
            tracker = ProjectTracker(project["path"])
            stage = tracker.get_current_stage()
            if stage == "finished":
                finished_projects.append((project, "Song", stage))
            else:
                active_projects.append((project, "Song", stage))
    
    if active_projects:
        table = Table(title="Active Projects", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Project Name", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Stage", style="magenta")
        table.add_column("Path", style="dim")
        
        for idx, (project, ptype, stage) in enumerate(active_projects, 1):
            table.add_row(
                str(idx),
                project["project"],
                project["artist"],
                ptype,
                stage,
                str(project["path"])
            )
        
        console.print(table)
    else:
        console.print("[dim]No active projects found[/dim]")
    
    if finished_projects:
        print_separator()
        console.print(f"[dim]Note: {len(finished_projects)} finished project(s) not shown.[/dim]")
        console.print("[dim]To view or reopen finished projects, go to Tasks & Projects menu[/dim]")
    
    print_separator()
    console.print("[bold]Options:[/bold]")
    console.print("  [cyan]s[/cyan] - Search projects")
    console.print("  [cyan]a[/cyan] - Select project to open")
    console.print("  [cyan]b[/cyan] - Go back")
    
    sub_choice = input("\nSelect option: ").strip().lower()
    
    if sub_choice == 'b':
        return
    elif sub_choice == 's':
        from .tasks_flows import search_projects_flow
        search_projects_flow()
        return
    elif sub_choice == 'a' and active_projects:
        while True:
            choice = input("\nEnter project number to open (or 'b' to go back): ").strip()
            if choice.lower() in ['b', 'back', 'backtrack']:
                return
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(active_projects):
                    project, ptype, stage = active_projects[idx]
                    if ptype == "Album":
                        show_album_contents(project["path"])
                    else:
                        show_song_project_details(project, history)
                    return
                else:
                    print_error("Invalid project number")
            else:
                print_error("Please enter a valid number")
    else:
        print_error("Invalid option")