"""Project browser flows"""
from pathlib import Path
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker, AlbumManager
from .daw_integration import open_daw_project
from .session_memo import prompt_for_session_memo
from .backup_flows import backup_project_flow
from ..utils.helpers import list_all_projects

def show_song_project_details(selected: dict, history):
    """Show details for a song project"""
    from .project_flows import manage_project_stage_flow  # Move import to top of function
    
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
    
    # Check if project is in an album
    album_path = tracker.data.get("album")
    if album_path:
        album_name = Path(album_path).name
        console.print(f"  Album: [magenta]{album_name}[/magenta]")
    
    project_path = selected["path"]
    daw_found = None
    for daw_code, daw_info in {"A": "ableton", "P": "protools", "L": "logic"}.items():
        for stage in ["production", "mix", "master"]:
            if (project_path / stage / daw_info).exists():
                daw_found = daw_code
                break
        if daw_found:
            break
    
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Open DAW session")
    console.print("  2 - View/record session memo")
    console.print("  3 - Manage project stage")
    console.print("  4 - Create backup")
    console.print("  5 - Set expected release date")
    console.print("  b - Go back")
    
    action = input("\nSelect option: ").strip()
    
    if action == "1":
        if daw_found:
            try:
                result = open_daw_project(project_path, daw_found, selected['project'])
                if result:
                    print_info("\nDAW session closed.")
                    
                    print_separator()
                    console.print("[bold]Session Complete![/bold]")
                    console.print(f"  Project: [green]{selected['project']}[/green]")
                    console.print(f"  Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
                    
                    if get_confirmation("\nUpdate project stage after this session?"):
                        manage_project_stage_flow(project_path)
                    
                    prompt_for_session_memo(project_path, history)
                else:
                    print_warning("DAW session did not open. You can still record session notes.")
                    if get_confirmation("Record session notes anyway?"):
                        prompt_for_session_memo(project_path, history, is_manual=True)
            except Exception as e:
                print_error(f"Failed to open DAW: {e}")
                print_info("You can still record session notes manually.")
                if get_confirmation("Record session notes anyway?"):
                    prompt_for_session_memo(project_path, history, is_manual=True)
        else:
            print_warning("No DAW session found for this project.")
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
    elif action == "b":
        return
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")

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

def search_and_open_flow(history):
    """Search for projects and open them - main browser functionality"""
    clear_screen()
    console.print(Panel.fit("[bold white]Search Projects[/bold white]", style="white"))
    
    console.print("\n")
    console.print("        [bold]Search Criteria:[/bold]")
    console.print("")
    console.print("          [cyan]1[/cyan] - Project name")
    console.print("          [cyan]2[/cyan] - Artist name")
    console.print("          [cyan]3[/cyan] - Created date (YYYY-MM-DD)")
    console.print("          [cyan]4[/cyan] - Last modified date (YYYY-MM-DD)")
    console.print("          [cyan]5[/cyan] - Release date (YYYY-MM-DD)")
    console.print("          [cyan]6[/cyan] - Album name")
    console.print("          [cyan]7[/cyan] - Show all projects")
    console.print("          [cyan]b[/cyan] - Go back")
    console.print("\n")
    
    search_type = input("        Select option: ").strip()
    
    if search_type == 'b':
        return
    
    all_projects = list_all_projects()
    results = []
    
    if search_type == "1":
        search_term = input("        Enter project name (or partial name): ").strip().lower()
        console.print("")
        for project in all_projects:
            if search_term in project["project"].lower():
                results.append(project)
    
    elif search_type == "2":
        search_term = input("        Enter artist name (or partial name): ").strip().lower()
        console.print("")
        for project in all_projects:
            if search_term in project["artist"].lower():
                results.append(project)
    
    elif search_type == "3":  # Created date
        date_str = input("        Enter created date (YYYY-MM-DD): ").strip()
        console.print("")
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            for project in all_projects:
                project_path = project["path"]
                import time
                mod_time = project_path.stat().st_ctime
                created_date = datetime.fromtimestamp(mod_time).date()
                if created_date == target_date:
                    results.append(project)
                # Also check tracker
                tracker = ProjectTracker(project_path)
                if tracker.data.get("stage_history"):
                    created_str = tracker.data["stage_history"][0].get("started", "")
                    if created_str:
                        try:
                            created_date = datetime.fromisoformat(created_str).date()
                            if created_date == target_date and project not in results:
                                results.append(project)
                        except:
                            pass
        except ValueError:
            print_error("        Invalid date format. Please use YYYY-MM-DD")
            input("\n        Press Enter to continue...")
            return
    
    elif search_type == "4":  # Last modified date
        date_str = input("        Enter last modified date (YYYY-MM-DD): ").strip()
        console.print("")
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            for project in all_projects:
                project_path = project["path"]
                import time
                # Check last modified time of the project folder
                mod_time = project_path.stat().st_mtime
                modified_date = datetime.fromtimestamp(mod_time).date()
                if modified_date == target_date:
                    results.append(project)
                # Also check tracker's last_modified
                tracker = ProjectTracker(project_path)
                if tracker.data.get("last_modified"):
                    try:
                        modified_str = tracker.data["last_modified"]
                        modified_date = datetime.fromisoformat(modified_str).date()
                        if modified_date == target_date and project not in results:
                            results.append(project)
                    except:
                        pass
        except ValueError:
            print_error("        Invalid date format. Please use YYYY-MM-DD")
            input("\n        Press Enter to continue...")
            return
    
    elif search_type == "5":  # Release date
        date_str = input("        Enter release date (YYYY-MM-DD): ").strip()
        console.print("")
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            for project in all_projects:
                tracker = ProjectTracker(project["path"])
                release_date = tracker.data.get("release_date")
                if release_date:
                    try:
                        release_date_obj = datetime.fromisoformat(release_date).date()
                        if release_date_obj == target_date:
                            results.append(project)
                    except:
                        pass
        except ValueError:
            print_error("        Invalid date format. Please use YYYY-MM-DD")
            input("\n        Press Enter to continue...")
            return
    
    elif search_type == "6":  # Album name
        search_term = input("        Enter album name (or partial name): ").strip().lower()
        console.print("")
        for project in all_projects:
            tracker = ProjectTracker(project["path"])
            album = tracker.data.get("album")
            if album:
                album_name = Path(album).name.lower()
                if search_term in album_name:
                    results.append(project)
    
    elif search_type == "7":  # Show all
        results = all_projects
        console.print("")
    
    else:
        print_error("        Invalid option")
        input("\n        Press Enter to continue...")
        return
    
    if not results:
        print_warning("        No projects found matching your search")
        input("\n        Press Enter to continue...")
        return
    
    # Display results
    from rich.table import Table
    table = Table(title=f"Search Results: {len(results)} project(s) found", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Album", style="magenta")
    table.add_column("Release Date", style="dim")
    table.add_column("Path", style="dim")
    
    for idx, project in enumerate(results, 1):
        tracker = ProjectTracker(project["path"])
        album = tracker.data.get("album")
        album_name = Path(album).name if album else "—"
        release_date = tracker.data.get("release_date", "—")
        if release_date and release_date != "—":
            release_date = release_date[:10]
        table.add_row(str(idx), project["project"], project["artist"], album_name, release_date, str(project["path"]))
    
    console.print(table)
    
    if get_confirmation("\nOpen a project?"):
        choice = input("Enter project number: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                project = results[idx]
                if (project["path"] / ".album.json").exists():
                    show_album_contents(project["path"])
                else:
                    show_song_project_details(project, history)
                return
    
    input("\nPress Enter to continue...")

def project_browser_flow(history):
    """Project Browser - simple search and open interface"""
    clear_screen()
    console.print(Panel.fit("[bold white]Project Browser[/bold white]", style="white"))
    
    console.print("\n[bold]What would you like to do?[/bold]\n")
    console.print("  [cyan]1[/cyan] - Search for a project")
    console.print("  [cyan]2[/cyan] - View finished projects")
    console.print("  [cyan]b[/cyan] - Go back")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == 'b':
        return
    elif choice == "1":
        search_and_open_flow(history)
        # After search, stay in project browser
        project_browser_flow(history)
        return
    elif choice == "2":
        from .tasks_flows import view_finished_projects_flow
        view_finished_projects_flow()
        # After viewing finished projects, return to project browser
        project_browser_flow(history)
        return
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        project_browser_flow(history)
        return