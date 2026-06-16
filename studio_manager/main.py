import sys
import readline
from pathlib import Path
from typing import List, Optional
from rich.panel import Panel

from .cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_dim, print_separator, show_recent_projects_table, show_statistics_table
from .cli.menu import show_main_menu, show_file_tree_options
from .cli.prompts import get_choice, get_confirmation, get_text_input
from .core.project_manager import create_project
from .data.history import ProjectHistory
from .data.logger import SessionLogger
from .features.file_tree import file_tree_flow
from .features.session_memo import SessionMemo, prompt_for_session_memo, set_history
from .features.daw_integration import open_daw_project
from .features.project_tracker import ProjectTracker, AlbumManager
from .utils.helpers import get_project_path, list_all_projects
from .utils.constants import DAW_MAP

# Initialize
history = ProjectHistory()
session_logger = SessionLogger()

# Initialize session_memo with history for name suggestions
set_history(history)

class Completer:
    """Custom completer for tab completion"""
    def __init__(self, options):
        self.options = sorted(options)
    
    def complete(self, text, state):
        matches = [opt for opt in self.options if opt.startswith(text)]
        try:
            return matches[state]
        except IndexError:
            return None

def setup_tab_completion(field: str, history_obj: ProjectHistory):
    """Setup tab completion for a specific field"""
    if field == "artist":
        options = list(history_obj.data["artists"])
    elif field == "engineer":
        options = list(history_obj.data["engineers"])
    else:
        options = []
    
    if options:
        completer = Completer(options)
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
    else:
        readline.set_completer(None)

def get_input_with_completion(prompt: str, field: str, history_obj: ProjectHistory, allow_backtrack: bool = True) -> str:
    """Get user input with tab completion, suggestions, and backtracking"""
    while True:
        # Show available completions if there are any
        completions = history_obj.get_completions(field, "")
        if completions:
            print_info(f"Available {field}s: {', '.join(completions[:5])}{'...' if len(completions) > 5 else ''}")
        
        # Setup tab completion only if there are options
        if len(history_obj.data.get(f"{field}s", [])) > 0:
            setup_tab_completion(field, history_obj)
        else:
            readline.set_completer(None)
        
        # Get input
        user_input = input(f"{prompt}: ").strip()
        
        # Check for backtrack command
        if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not user_input:
            print_error("Input cannot be empty. Please try again.")
            continue
        
        # First try exact match from history
        if field == "artist" and user_input in history_obj.data["artists"]:
            return user_input
        elif field == "engineer" and user_input in history_obj.data["engineers"]:
            return user_input
        
        # Get suggestions based on partial input
        suggestions = history_obj.get_suggestions(field, user_input)
        
        if suggestions:
            print_warning("Did you mean one of these?")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")
            print("  0. None of the above")
            print("  b. Backtrack to previous step")
            
            choice = input("Use suggestion? (number/0/b): ").strip().lower()
            
            if choice == 'b' or choice == 'backtrack':
                return "##BACKTRACK##"
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(suggestions):
                    return suggestions[idx]
                elif int(choice) == 0:
                    confirm = input(f"Enter '{user_input}' as a new {field}? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return user_input
                    else:
                        continue
            else:
                confirm = input(f"Create new {field} '{user_input}'? (y/n/b for backtrack): ").strip().lower()
                if confirm == 'b':
                    return "##BACKTRACK##"
                elif confirm in ['y', 'yes']:
                    return user_input
        else:
            print_warning(f"No existing {field} found matching '{user_input}'")
            confirm = input(f"Create new {field} '{user_input}'? (y/n/b for backtrack): ").strip().lower()
            if confirm == 'b':
                return "##BACKTRACK##"
            elif confirm in ['y', 'yes']:
                return user_input

def get_engineers() -> List[str]:
    """Get engineer names with validation and backtracking"""
    engineers = []
    
    while True:
        num_input = input("\nEnter the number of engineers on this session (or 'b' to go back): ").strip()
        
        if num_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not num_input.isdigit():
            print_error("Please enter a valid number")
            continue
        
        num_engineers = int(num_input)
        if num_engineers < 0 or num_engineers > 20:
            print_error("Number of engineers must be between 1 and 20")
            continue
        
        for i in range(num_engineers):
            while True:
                prompt = f"\nEnter the name of engineer #{i+1}"
                engineer = get_input_with_completion(prompt, "engineer", history, allow_backtrack=True)
                
                if engineer == "##BACKTRACK##":
                    if i > 0:
                        print_warning("Going back to previous engineer...")
                        engineers.pop() if engineers else None
                        i -= 1
                        continue
                    else:
                        print_warning("Going back to number of engineers...")
                        engineers = []
                        break
                else:
                    engineers.append(engineer)
                    break
            
            if engineer == "##BACKTRACK##" and not engineers:
                break
        
        if engineers:
            return engineers

def get_project_name() -> str:
    """Get project name with backtracking"""
    while True:
        name = input("\nEnter the name of your project: ").strip()
        
        if name.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not name:
            print_error("Project name cannot be empty")
            continue
        
        return name

def get_project_type() -> str:
    """Get and validate project type with backtracking"""
    while True:
        type_input = input("\nEnter S for Song, or A for Album: ").strip().upper()
        
        if type_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if type_input in ["S", "A"]:
            return type_input
        
        print_error("Invalid entry. Enter S for Song, or A for Album")

def get_daw() -> Optional[str]:
    """Get and validate DAW selection with backtracking"""
    while True:
        daw_input = input("\nEnter the DAW you're using (P for Pro Tools, A for Ableton, L for Logic): ").strip().upper()
        
        if daw_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if daw_input in ["P", "A", "L"]:
            return daw_input
        
        print_error("Invalid entry. Enter P, A, or L")

def new_project_flow():
    """Handle new project creation flow with backtracking support"""
    clear_screen()
    console.print(Panel.fit("[bold white]Create New Project[/bold white]", style="white"))
    print_info("\nAt any prompt, enter 'b' or 'backtrack' to go back to the previous step")
    
    try:
        # Step 1: Get engineers
        engineers = get_engineers()
        if engineers == "##BACKTRACK##":
            return
        
        # Step 2: Get project name
        name = get_project_name()
        if name == "##BACKTRACK##":
            return
        
        # Step 3: Get project type
        project_type = get_project_type()
        if project_type == "##BACKTRACK##":
            return
        
        # Step 4: Get artist name
        if len(history.data["artists"]) > 0:
            print_info("\nTip: Press TAB to see available artists from history")
        artist = get_input_with_completion("\nEnter the name of the artist", "artist", history, allow_backtrack=True)
        if artist == "##BACKTRACK##":
            return
        
        # Step 5: Get DAW for songs
        daw = ""
        if project_type == "S":
            daw = get_daw()
            if daw == "##BACKTRACK##":
                return
        
        # Confirm before creating
        clear_screen()
        console.print(Panel.fit("[bold white]Project Summary[/bold white]", style="white"))
        console.print(f"\n  Name: [green]{name}[/green]")
        console.print(f"  Type: [green]{'Song' if project_type == 'S' else 'Album'}[/green]")
        console.print(f"  Artist: [green]{artist}[/green]")
        console.print(f"  Engineers: [green]{', '.join(engineers)}[/green]")
        if daw:
            daw_name = DAW_MAP.get(daw, daw)
            console.print(f"  DAW: [green]{daw_name}[/green]")
        
        confirm = input("\nCreate this project? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            success = create_project(name, project_type, artist, daw)
            
            if success:
                history.add_project(name, project_type, artist, engineers, daw)
                console.print(f"\n[green]Project '{name}' created successfully![/green]")
                
                # Initialize project tracker for song projects (only if new)
                if project_type == "S":
                    project_path = get_project_path(artist, name)
                    tracker = ProjectTracker(project_path)
                    # Only set initial stage if it's not already set
                    if tracker.get_current_stage() == "production" and not tracker.data.get("stage_history"):
                        # This is a new project, don't print the stage change message
                        tracker.data["current_stage"] = "production"
                        tracker.save()
                    else:
                        tracker.update_stage("production", "Project created")
                
                input("\nPress Enter to continue...")

            else:
                print_error("\nFailed to create project. Check the logs for details.")
                input("\nPress Enter to continue...")
        else:
            print_warning("\nProject creation cancelled")
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        input("\nPress Enter to continue...")
    except Exception as e:
        print_error(f"\nAn unexpected error occurred: {e}")
        input("\nPress Enter to continue...")

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

def add_songs_to_album_flow(album_path: Path):
    """Add songs to an album"""
    manager = AlbumManager(album_path)
    unassigned = manager.get_unassigned_songs(Path.cwd())
    
    if not unassigned:
        print_info("No unassigned songs found")
        return
    
    console.print("\n[bold]Unassigned Songs:[/bold]")
    for i, song in enumerate(unassigned, 1):
        console.print(f"  [cyan]{i}[/cyan] - {song.parent.name}/{song.name}")
    
    choice = input("\nSelect song to add (or 'a' to add all, 'b' to go back): ").strip()
    
    if choice.lower() == 'a':
        for song in unassigned:
            manager.add_song(song)
    elif choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(unassigned):
            position = input(f"Position in album (1-{len(manager.data['songs']) + 1}, Enter for end): ").strip()
            pos = int(position) if position.isdigit() else None
            manager.add_song(unassigned[idx], pos)
    
    manager.list_songs()

def manage_album_flow(album_path: Path):
    """Manage an existing album"""
    manager = AlbumManager(album_path)
    manager.list_songs()
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Add songs")
    console.print("  2 - Remove song")
    console.print("  3 - Reorder songs")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        add_songs_to_album_flow(album_path)
    elif choice == "2":
        if manager.data["songs"]:
            idx = int(input(f"Select song to remove (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= idx < len(manager.data["songs"]):
                manager.remove_song(Path(manager.data["songs"][idx]["path"]))
    elif choice == "3":
        if manager.data["songs"]:
            manager.list_songs()
            song_idx = int(input(f"Select song to move (1-{len(manager.data['songs'])}): ")) - 1
            if 0 <= song_idx < len(manager.data["songs"]):
                new_pos = int(input("New position: "))
                song_path = Path(manager.data["songs"][song_idx]["path"])
                manager.reorder_song(song_path, new_pos)
                manager.list_songs()

def view_unassigned_songs_flow():
    """View all songs not assigned to an album"""
    clear_screen()
    console.print(Panel.fit("[bold white]Unassigned Songs[/bold white]", style="white"))
    
    manager = AlbumManager(Path.cwd())
    unassigned = manager.get_unassigned_songs(Path.cwd())
    
    if not unassigned:
        print_info("All songs are assigned to albums")
    else:
        from rich.table import Table
        table = Table(title="Songs Not in Any Album", style="white")
        table.add_column("Artist", style="cyan")
        table.add_column("Song Name", style="green")
        table.add_column("Path", style="dim")
        
        for song in unassigned:
            table.add_row(song.parent.name, song.name, str(song))
        
        console.print(table)
    
    input("\nPress Enter to continue...")

def album_management_flow():
    """Manage albums and song organization"""
    clear_screen()
    console.print(Panel.fit("[bold white]Album Management[/bold white]", style="white"))
    
    # Find all albums
    albums_path = Path.cwd() / "artists"
    albums = []
    
    if albums_path.exists():
        for artist_dir in albums_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir() and (project_dir / ".album.json").exists():
                        albums.append(project_dir)
    
    if albums:
        console.print("\n[bold]Existing Albums:[/bold]")
        for i, album in enumerate(albums, 1):
            manager = AlbumManager(album)
            console.print(f"  [cyan]{i}[/cyan] - {manager.data['name']} ({manager.data['total_tracks']} tracks)")
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Create new album")
    console.print("  2 - Manage existing album")
    console.print("  3 - View unassigned songs")
    console.print("  b - Go back")
    
    choice = input("\nSelect option: ").strip()
    
    if choice == "1":
        artist = input("Artist name: ").strip()
        album_name = input("Album name: ").strip()
        
        artist_path = Path.cwd() / "artists" / artist
        album_path = artist_path / album_name
        
        if album_path.exists():
            print_warning("Album already exists")
        else:
            album_path.mkdir(parents=True, exist_ok=True)
            manager = AlbumManager(album_path)
            manager.save()
            print_success(f"Album '{album_name}' created for {artist}")
            
            if get_confirmation("Add songs to this album now?"):
                add_songs_to_album_flow(album_path)
        
        input("\nPress Enter to continue...")
    elif choice == "2" and albums:
        idx = int(input(f"Select album (1-{len(albums)}): ")) - 1
        if 0 <= idx < len(albums):
            manage_album_flow(albums[idx])
        input("\nPress Enter to continue...")
    elif choice == "3":
        view_unassigned_songs_flow()

def show_album_contents(album_path: Path):
    """Display the contents of an album (its songs)"""
    clear_screen()
    manager = AlbumManager(album_path)
    
    console.print(Panel.fit(f"[bold white]Album: {manager.data['name']}[/bold white]", style="white"))
    
    if not manager.data["songs"]:
        print_warning("\nNo songs in this album yet")
        if get_confirmation("\nAdd songs to this album?"):
            add_songs_to_album_flow(album_path)
    else:
        from rich.table import Table
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

def show_song_project_details(selected: dict):
    """Show details for a song project"""
    clear_screen()
    console.print(Panel.fit("[bold white]Project Details[/bold white]", style="white"))
    console.print(f"\n  Project: [green]{selected['project']}[/green]")
    console.print(f"  Artist: [green]{selected['artist']}[/green]")
    console.print(f"  Path: [dim]{selected['path']}[/dim]")
    
    # Show current stage
    tracker = ProjectTracker(selected["path"])
    console.print(f"  Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
    
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
        open_daw_project(project_path, daw_found, selected['project'])
        print_info("\nDAW session closed.")
        prompt_for_session_memo(project_path, history)
    elif action == "2":
        prompt_for_session_memo(project_path, history, is_manual=True)
    elif action == "3":
        manage_project_stage_flow(project_path)
    elif action == "4":
        backup_project_flow(project_path)
    elif action == "5":
        release_date = input("Enter expected release date (YYYY-MM-DD): ").strip()
        if release_date:
            tracker.set_release_date(release_date)
            input("\nPress Enter to continue...")

def open_project_flow():
    """Handle opening existing projects - only show active projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Browse Projects[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("\nNo projects found. Create a project first.")
        input("\nPress Enter to continue...")
        return
    
    # Separate active and finished projects
    active_projects = []
    finished_projects = []
    
    for project in projects:
        is_album = (project["path"] / ".album.json").exists()
        if is_album:
            # Albums always go to active
            active_projects.append((project, "Album", "N/A"))
        else:
            # Check stage for songs
            tracker = ProjectTracker(project["path"])
            stage = tracker.get_current_stage()
            if stage == "finished":
                # Get completion date for sorting
                completed_date = "9999-99-99"  # Default for sorting
                for stage_entry in tracker.data.get("stage_history", []):
                    if stage_entry.get("stage") == "finished":
                        completed_date = stage_entry.get("started", "9999-99-99")[:10]
                        break
                finished_projects.append((project, "Song", stage, completed_date))
            else:
                active_projects.append((project, "Song", stage))
    
    # Show Active Projects only
    if active_projects:
        from rich.table import Table
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
    
    # Show note about finished projects
    if finished_projects:
        print_separator()
        console.print(f"[dim]Note: {len(finished_projects)} finished project(s) not shown.[/dim]")
        console.print("[dim]To view or reopen finished projects, go to Tasks menu → View finished projects[/dim]")
        print_separator()
        console.print("[bold]Options:[/bold]")
        console.print("  [cyan]1[/cyan] - Select a project to open")
        console.print("  [cyan]2[/cyan] - Show all projects (including finished)")
        console.print("  [cyan]b[/cyan] - Go back")
        
        sub_choice = input("\nSelect option: ").strip().lower()
        
        if sub_choice == 'b':
            return
        elif sub_choice == "2":
            # Sort finished projects by completion date (newest first)
            finished_projects.sort(key=lambda x: x[3], reverse=True)
            
            from rich.table import Table
            table = Table(title="All Projects (Finished at bottom)", style="white")
            table.add_column("#", style="cyan", width=4)
            table.add_column("Project Name", style="green")
            table.add_column("Artist", style="yellow")
            table.add_column("Type", style="blue")
            table.add_column("Stage", style="magenta")
            table.add_column("Completed", style="dim")
            table.add_column("Path", style="dim")
            
            # Show active projects first
            for idx, (project, ptype, stage) in enumerate(active_projects, 1):
                table.add_row(
                    str(idx),
                    project["project"],
                    project["artist"],
                    ptype,
                    stage,
                    "—",
                    str(project["path"])
                )
            
            # Then finished projects
            for idx, (project, ptype, stage, completed_date) in enumerate(finished_projects, len(active_projects) + 1):
                table.add_row(
                    str(idx),
                    f"[dim]{project['project']}[/dim]",
                    f"[dim]{project['artist']}[/dim]",
                    f"[dim]{ptype}[/dim]",
                    f"[dim]{stage}[/dim]",
                    f"[dim]{completed_date[:10]}[/dim]",
                    f"[dim]{project['path']}[/dim]"
                )
            
            console.print(table)
            console.print("[dim]Finished projects shown in dim text. To modify, reopen from Tasks menu.[/dim]")
            
            while True:
                choice = input("\nEnter project number (or 'b' to go back): ").strip()
                
                if choice.lower() in ['b', 'back', 'backtrack']:
                    return
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if idx < len(active_projects):
                        project, ptype, stage = active_projects[idx]
                        show_song_project_details(project)
                        return
                    elif idx < len(active_projects) + len(finished_projects):
                        finished_idx = idx - len(active_projects)
                        project, ptype, stage, completed_date = finished_projects[finished_idx]
                        # Show read-only view for finished projects
                        clear_screen()
                        console.print(Panel.fit("[bold white]Finished Project (Read Only)[/bold white]", style="white"))
                        console.print(f"\n  Project: [green]{project['project']}[/green]")
                        console.print(f"  Artist: [green]{project['artist']}[/green]")
                        console.print(f"  Stage: [cyan]{stage}[/cyan]")
                        console.print(f"  Completed: [dim]{completed_date[:10]}[/dim]")
                        console.print(f"  Path: [dim]{project['path']}[/dim]")
                        console.print("\n[yellow]This project is marked as finished.[/yellow]")
                        console.print("To modify, go to Tasks menu → View finished projects → Reopen.")
                        input("\nPress Enter to continue...")
                        return
                    else:
                        print_error("Invalid project number")
                else:
                    print_error("Please enter a valid number")
            return
        elif sub_choice == "1":
            # Continue to project selection
            pass
        else:
            print_error("Invalid option")
            input("\nPress Enter to continue...")
            return
    
    # If no finished projects or user chose option 1, allow selection from active
    if active_projects:
        while True:
            choice = input("\nEnter project number (or 'b' to go back): ").strip()
            
            if choice.lower() in ['b', 'back', 'backtrack']:
                return
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(active_projects):
                    project, ptype, stage = active_projects[idx]
                    show_song_project_details(project)
                    return
                else:
                    print_error("Invalid project number")
            else:
                print_error("Please enter a valid number")
    else:
        print_warning("No active projects available")
        input("\nPress Enter to continue...")
        return

def show_file_tree_flow():
    """Handle file tree display"""
    from .core.file_system import print_directory_tree, print_full_project_tree
    
    clear_screen()
    console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
    
    while True:
        show_file_tree_options()
        
        choice = input("\nSelect an option: ").strip()
        
        if choice.lower() in ['b', 'back', 'backtrack']:
            return
        elif choice == "1":
            clear_screen()
            print_full_project_tree()
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        elif choice == "2":
            clear_screen()
            print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        elif choice == "3":
            path_input = input("\nEnter directory path (or press Enter for current directory): ").strip()
            clear_screen()
            if path_input:
                print_directory_tree(Path(path_input), max_depth=3)
            else:
                print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        else:
            print_error("Invalid option")

def view_project_memos_flow():
    """Flow for viewing memos from a project"""
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        return
    
    # Show only song projects (not albums)
    song_projects = [p for p in projects if not (p["path"] / ".album.json").exists()]
    
    if not song_projects:
        print_warning("No song projects found")
        return
    
    from rich.table import Table
    table = Table(title="Select Project", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    
    for idx, project in enumerate(song_projects[:15], 1):
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        table.add_row(str(idx), project["project"], project["artist"], stage)
    
    console.print(table)
    
    proj_choice = input("\nSelect project number (or 'b' to go back): ").strip()
    if proj_choice.lower() != 'b' and proj_choice.isdigit():
        idx = int(proj_choice) - 1
        if 0 <= idx < len(song_projects[:15]):
            project_path = song_projects[idx]["path"]
            memo = SessionMemo(project_path)
            
            view_choice = input("\nInteractive navigation? (y/n, default y): ").strip().lower()
            if view_choice == 'n':
                memo.view_memos(interactive=False)
            else:
                memo.view_memos(interactive=True)

def set_release_date_flow():
    """Flow for setting expected release date on a project"""
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        return
    
    # Show only active song projects (not finished, not albums)
    active_songs = []
    for p in projects:
        if (p["path"] / ".album.json").exists():
            continue  # Skip albums
        tracker = ProjectTracker(p["path"])
        stage = tracker.get_current_stage()
        if stage != "finished":
            active_songs.append((p, tracker))
    
    if not active_songs:
        print_warning("No active song projects found")
        return
    
    from rich.table import Table
    table = Table(title="Set Release Date", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Current Release", style="dim")
    
    for idx, (project, tracker) in enumerate(active_songs[:15], 1):
        current = tracker.data.get("release_date", "Not set")
        if current:
            current = current[:10]
        table.add_row(str(idx), project["project"], project["artist"], tracker.get_current_stage(), current)
    
    console.print(table)
    
    proj_choice = input("\nSelect project number (or 'b' to go back): ").strip()
    if proj_choice.lower() != 'b' and proj_choice.isdigit():
        idx = int(proj_choice) - 1
        if 0 <= idx < len(active_songs[:15]):
            project, tracker = active_songs[idx]
            release_date = input("Enter expected release date (YYYY-MM-DD) or press Enter to skip: ").strip()
            if release_date:
                tracker.set_release_date(release_date)
                print_success(f"Release date set for {project['project']}")

def view_finished_projects_flow():
    """View all finished projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Finished Projects[/bold white]", style="white"))
    
    projects = list_all_projects()
    finished_songs = []
    
    for project in projects:
        # Skip albums
        if (project["path"] / ".album.json").exists():
            continue
        
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        if stage == "finished":
            finished_songs.append(project)
    
    if not finished_songs:
        print_info("No finished projects found")
        return
    
    from rich.table import Table
    table = Table(title="Completed Projects", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date Completed", style="green")
    table.add_column("Song", style="yellow")
    table.add_column("Artist", style="cyan")
    
    for idx, project in enumerate(finished_songs, 1):
        # Try to get completion date from stage history
        project_path = get_project_path(project["artist"], project["name"])
        tracker = ProjectTracker(project_path)
        completed_date = "Unknown"
        for stage in tracker.data.get("stage_history", []):
            if stage.get("stage") == "finished":
                completed_date = stage.get("started", "Unknown")[:16]
                break
        
        table.add_row(
            str(idx),
            completed_date,
            project.get("name", "Unknown"),
            project.get("artist", "Unknown")
        )
    
    console.print(table)
    
    # Option to reopen a finished project
    if get_confirmation("\nReopen a finished project?"):
        choice = input("Enter project number to reopen: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(finished_songs):
                project = finished_songs[idx]
                project_path = get_project_path(project["artist"], project["name"])
                tracker = ProjectTracker(project_path)
                if get_confirmation(f"Move '{project['name']}' back to mastering?"):
                    tracker.update_stage("mastering", "Reopened from finished")
                    print_success(f"Project '{project['name']}' moved back to mastering")
                    # Refresh the view
                    view_finished_projects_flow()
                    return
                
def search_projects_flow():
    """Search for projects by name, artist, or stage"""
    clear_screen()
    console.print(Panel.fit("[bold white]Search Projects[/bold white]", style="white"))
    
    console.print("\n[bold]Search by:[/bold]")
    console.print("  [cyan]1[/cyan] - Project name")
    console.print("  [cyan]2[/cyan] - Artist name")
    console.print("  [cyan]3[/cyan] - Stage (production/mixing/mastering/finished)")
    console.print("  [cyan]b[/cyan] - Go back")
    
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
    
    # Get all projects
    all_projects = history.get_recent_projects(limit=200)
    results = []
    
    for project in all_projects:
        if project.get("type") != "S":
            continue
        
        project_path = get_project_path(project["artist"], project["name"])
        tracker = ProjectTracker(project_path)
        stage = tracker.get_current_stage()
        
        if field == "name" and search_term in project.get("name", "").lower():
            results.append((project, stage))
        elif field == "artist" and search_term in project.get("artist", "").lower():
            results.append((project, stage))
        elif field == "stage" and search_term == stage:
            results.append((project, stage))
    
    if not results:
        print_warning(f"No projects found matching '{search_term}'")
        input("\nPress Enter to continue...")
        return
    
    from rich.table import Table
    table = Table(title=f"Search Results: '{search_term}'", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Created", style="dim")
    
    for idx, (project, stage) in enumerate(results[:20], 1):
        table.add_row(
            str(idx),
            project.get("name", "Unknown"),
            project.get("artist", "Unknown"),
            stage,
            project.get("date_created_pretty", "Unknown")[:16]
        )
    
    console.print(table)
    
    if len(results) > 20:
        console.print(f"[dim]... and {len(results) - 20} more results[/dim]")
    
    # Option to view project details
    if results and get_confirmation("\nView project details?"):
        choice = input("Enter project number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results[:20]):
                project, stage = results[idx]
                project_path = get_project_path(project["artist"], project["name"])
                show_song_project_details({
                    "project": project.get("name"),
                    "artist": project.get("artist"),
                    "path": project_path
                })

def show_tasks():
    """Show current tasks and statistics - separate songs from albums, filter finished"""
    clear_screen()
    console.print(Panel.fit("[bold white]Current Tasks & Statistics[/bold white]", style="white"))
    
    # Get all projects
    all_projects = history.get_recent_projects(limit=50)
    
    # Separate songs from albums, and filter out finished
    active_songs = []
    finished_songs = []
    albums = []
    
    for project in all_projects:
        if project.get("type") == "S":
            # Check stage from project tracker
            project_path = get_project_path(project["artist"], project["name"])
            tracker = ProjectTracker(project_path)
            stage = tracker.get_current_stage()
            project["stage"] = stage
            
            if stage == "finished":
                finished_songs.append(project)
            else:
                # Calculate priority for sorting
                tracker.calculate_priority()
                project["priority"] = tracker.data.get("priority_score", 0)
                project["release_date"] = tracker.data.get("release_date")
                active_songs.append(project)
        else:
            albums.append(project)
    
    # Sort active songs by priority (higher first)
    active_songs.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    # Show Active Songs (not finished)
    if active_songs:
        from rich.table import Table
        table = Table(title="Active Songs", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Priority", style="red", width=10, justify="center")
        table.add_column("Date", style="cyan")
        table.add_column("Song", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Stage", style="magenta")
        table.add_column("Release", style="dim", width=12)
        
        for idx, project in enumerate(active_songs, 1):
            priority_display = "★" * min(project.get("priority", 0), 4) if project.get("priority", 0) > 0 else "•"
            priority_display = priority_display.center(6)
            release = project.get("release_date", "TBD")
            if release and release != "TBD":
                release = release[:10]
            else:
                release = "TBD"
            table.add_row(
                str(idx),
                priority_display,
                project.get("date_created_pretty", "Unknown")[:16],
                project.get("name", "Unknown"),
                project.get("artist", "Unknown"),
                project.get("stage", "production"),
                release
            )
        
        console.print(table)
    else:
        console.print("[dim]No active songs in progress[/dim]")
    
    # Show Albums
    if albums:
        print_separator()
        table = Table(title="Albums", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="cyan")
        table.add_column("Album Name", style="green")
        table.add_column("Artist", style="yellow")
        
        for idx, project in enumerate(albums, 1):
            table.add_row(
                str(idx),
                project.get("date_created_pretty", "Unknown")[:16],
                project.get("name", "Unknown"),
                project.get("artist", "Unknown")
            )
        
        console.print(table)
    
    # Show statistics
    print_separator()
    stats = history.get_stats()
    show_statistics_table(stats)
    
    # Numeric menu for additional options
    print_separator()
    console.print("[bold]Additional Options:[/bold]")
    console.print("  [cyan]1[/cyan] - View session memos from a project")
    console.print("  [cyan]2[/cyan] - Set expected release date for a project")
    console.print("  [cyan]3[/cyan] - View finished projects")
    console.print("  [cyan]4[/cyan] - Search for a project")
    console.print("  [cyan]b[/cyan] - Go back")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == "1":
        view_project_memos_flow()
    elif choice == "2":
        set_release_date_flow()
    elif choice == "3":
        view_finished_projects_flow()
    elif choice == "4":
        search_projects_flow()
    elif choice == 'b':
        return
    
    input("\nPress Enter to continue...")

def global_backup_flow():
    """Backup all projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Global Backup[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found to backup")
        input("\nPress Enter to continue...")
        return
    
    console.print(f"\n[bold]Found {len(projects)} projects to backup[/bold]")
    
    if get_confirmation("Create backups for all projects?"):
        for project in projects:
            print_info(f"\nBacking up {project['artist']} - {project['project']}...")
            tracker = ProjectTracker(project["path"])
            tracker.create_backup()
        
        print_success(f"\nBackup complete! All {len(projects)} projects backed up.")
    
    input("\nPress Enter to continue...")

def main():
    """Main program entry point"""
    session_logger.start_session()
    session_logger.log_action("APPLICATION_START", "Studio Management System started")
    
    clear_screen()
    console.print(Panel.fit("[bold white]Studio Management System[/bold white]", 
                          subtitle="Version 1.0.0", style="white"))
    input("\nPress Enter to continue...")
    
    while True:
        try:
            show_main_menu()
            
            console.print("[bold]Select an option: [/bold]", end="")
            objective = input().strip()
            
            if objective.lower() == 'q':
                session_logger.log_action("APPLICATION_EXIT", "User exited")
                session_logger.save_session()
                clear_screen()
                print_success("EXITED SUCCESSFULLY.")
                sys.exit(0)
            elif objective == "1":
                new_project_flow()
            elif objective == "2":
                open_project_flow()
            elif objective == "3":
                show_file_tree_flow()
            elif objective == "4":
                show_tasks()
            elif objective == "5":
                album_management_flow()
            elif objective == "6":
                console.print("\n[bold]Backup Options:[/bold]")
                console.print("  1 - Backup a single project")
                console.print("  2 - Backup all projects")
                backup_choice = input("\nSelect option: ").strip()
                if backup_choice == "1":
                    projects = list_all_projects()
                    if projects:
                        print("\n[bold]Select project to backup:[/bold]")
                        for i, p in enumerate(projects[:10], 1):
                            print(f"  {i}. {p['artist']} - {p['project']}")
                        proj_choice = input("\nSelect project: ").strip()
                        if proj_choice.isdigit() and 1 <= int(proj_choice) <= len(projects[:10]):
                            tracker = ProjectTracker(projects[int(proj_choice)-1]["path"])
                            backup_project_flow(projects[int(proj_choice)-1]["path"])
                    else:
                        print_warning("No projects found")
                elif backup_choice == "2":
                    global_backup_flow()
                else:
                    print_warning("Invalid option")
            else:
                print_error("\nInvalid option. Please choose 1, 2, 3, 4, 5, 6, or q")
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            session_logger.log_action("APPLICATION_EXIT", "Keyboard interrupt")
            session_logger.save_session()
            clear_screen()
            print_warning("\nEXITED.")
            sys.exit(0)
        except Exception as e:
            session_logger.log_action("APPLICATION_ERROR", f"Error: {str(e)}")
            session_logger.save_session()
            print_error(f"\nAn unexpected error occurred: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()