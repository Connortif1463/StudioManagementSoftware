"""Tasks and projects flow - statistics, memos, finished projects, search"""
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator, show_statistics_table
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker
from .session_memo import SessionMemo
from ..utils.helpers import get_project_path, list_all_projects
from .browser_flows import show_song_project_details

def view_project_memos_flow():
    """Flow for viewing memos from a project - excludes finished projects"""
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        return
    
    active_songs = []
    for project in projects:
        if (project["path"] / ".album.json").exists():
            continue
        
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        if stage != "finished":
            active_songs.append((project, stage))
    
    if not active_songs:
        print_warning("No active song projects with session memos found")
        return
    
    table = Table(title="Select Project", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    
    for idx, (project, stage) in enumerate(active_songs, 1):
        table.add_row(str(idx), project["project"], project["artist"], stage)
    
    console.print(table)
    
    proj_choice = input("\nSelect project number (or 'b' to go back): ").strip()
    if proj_choice.lower() != 'b' and proj_choice.isdigit():
        idx = int(proj_choice) - 1
        if 0 <= idx < len(active_songs):
            project, stage = active_songs[idx]
            project_path = project["path"]
            memo = SessionMemo(project_path)
            
            view_choice = input("\nInteractive navigation? (y/n, default y): ").strip().lower()
            if view_choice == 'n':
                memo.view_memos(interactive=False)
            else:
                memo.view_memos(interactive=True)

def set_release_date_flow():
    """Flow for setting expected release date on a project - excludes finished projects"""
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

def view_finished_projects_flow():
    """View all finished projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Finished Projects[/bold white]", style="white"))
    
    projects = list_all_projects()
    finished_songs = []
    
    for project in projects:
        if (project["path"] / ".album.json").exists():
            continue
        
        tracker = ProjectTracker(project["path"])
        stage = tracker.get_current_stage()
        if stage == "finished":
            finished_songs.append(project)
    
    if not finished_songs:
        print_info("No finished projects found")
        return
    
    table = Table(title="Completed Projects", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Date Completed", style="green")
    table.add_column("Song", style="yellow")
    table.add_column("Artist", style="cyan")
    
    for idx, project in enumerate(finished_songs, 1):
        project_path = get_project_path(project["artist"], project["project"])
        tracker = ProjectTracker(project_path)
        completed_date = "Unknown"
        for stage_entry in tracker.data.get("stage_history", []):
            if stage_entry.get("stage") == "finished":
                completed_date = stage_entry.get("started", "Unknown")[:16]
                break
        
        table.add_row(
            str(idx),
            completed_date,
            project["project"],
            project["artist"],
        )
    
    console.print(table)
    
    if get_confirmation("\nReopen a finished project?"):
        choice = input("Enter project number to reopen: ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(finished_songs):
                project = finished_songs[idx]
                project_path = get_project_path(project["artist"], project["project"])
                tracker = ProjectTracker(project_path)
                if get_confirmation(f"Move '{project['project']}' back to mastering?"):
                    tracker.update_stage("mastering", "Reopened from finished")
                    print_success(f"Project '{project['project']}' moved back to mastering")
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
                from .browser_flows import show_song_project_details
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
            filtered.append((project, tracker.get_current_stage(), category))
    
    if not filtered:
        print_info(f"No projects found in this category")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Projects - {selected_category.replace('_', ' ').title() if selected_category != 'all' else 'All Categories'}", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    
    for idx, (project, stage, category) in enumerate(filtered, 1):
        table.add_row(str(idx), project["project"], project["artist"], stage)
    
    console.print(table)
    input("\nPress Enter to continue...")

def tasks_and_projects_flow(history):
    """Tasks and Projects - view statistics, memos, finished projects, search"""
    clear_screen()
    console.print(Panel.fit("[bold white]Tasks & Projects[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    active_songs = []
    finished_songs = []
    albums = []
    
    for project in projects:
        is_album = (project["path"] / ".album.json").exists()
        if is_album:
            albums.append(project)
        else:
            tracker = ProjectTracker(project["path"])
            stage = tracker.get_current_stage()
            project["stage"] = stage
            
            if stage == "finished":
                finished_songs.append(project)
            else:
                tracker.calculate_priority()
                project["priority"] = tracker.data.get("priority_score", 0)
                project["release_date"] = tracker.data.get("release_date")
                active_songs.append(project)
    
    active_songs.sort(key=lambda x: x.get("priority", 0), reverse=True)
    
    if active_songs:
        table = Table(title="Active Songs", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Priority", style="red", width=10, justify="center")
        table.add_column("Date", style="cyan")
        table.add_column("Song", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Stage", style="magenta")
        table.add_column("Release", style="dim", width=12)
        
        for idx, project in enumerate(active_songs, 1):
            created_pretty = project.get("date_created_pretty", "Unknown")
            if created_pretty == "Unknown":
                tracker = ProjectTracker(project["path"])
                if tracker.data.get("stage_history"):
                    created_pretty = tracker.data["stage_history"][0].get("started", "Unknown")[:16]
                else:
                    import time
                    mod_time = project["path"].stat().st_ctime
                    created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
            
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
                created_pretty[:16],
                project["project"],
                project["artist"],
                project.get("stage", "production"),
                release
            )
        
        console.print(table)
    else:
        console.print("[dim]No active songs in progress[/dim]")
    
    if albums:
        print_separator()
        table = Table(title="Albums", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="cyan")
        table.add_column("Album Name", style="green")
        table.add_column("Artist", style="yellow")
        
        for idx, project in enumerate(albums, 1):
            created_pretty = "Unknown"
            album_file = project["path"] / ".album.json"
            if album_file.exists():
                import json
                with open(album_file, 'r') as f:
                    album_data = json.load(f)
                    created_pretty = album_data.get("created", "Unknown")[:16]
            else:
                import time
                mod_time = project["path"].stat().st_ctime
                created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
            
            table.add_row(
                str(idx),
                created_pretty,
                project["project"],
                project["artist"]
            )
        
        console.print(table)
    
    print_separator()
    stats = history.get_stats()
    show_statistics_table(stats)
    
    print_separator()
    console.print("[bold]Options:[/bold]")
    console.print("  [cyan]1[/cyan] - Open a project from the list above")
    console.print("  [cyan]2[/cyan] - View session memos from a project")
    console.print("  [cyan]3[/cyan] - Set expected release date for a project")
    console.print("  [cyan]4[/cyan] - Search for a project")
    console.print("  [cyan]5[/cyan] - Filter by project category")
    console.print("  [cyan]b[/cyan] - Go back")
    
    choice = input("\nSelect option: ").strip().lower()
    
    if choice == "1":
        # Open a project from the active songs list
        if active_songs:
            proj_choice = input("\nEnter the number of the project to open: ").strip()
            if proj_choice.isdigit():
                idx = int(proj_choice) - 1
                if 0 <= idx < len(active_songs):
                    project = active_songs[idx]
                    from .browser_flows import show_song_project_details
                    show_song_project_details(project, history)
                    tasks_and_projects_flow(history)
                    return
                else:
                    print_error("Invalid project number")
                    input("\nPress Enter to continue...")
            else:
                print_error("Please enter a valid number")
                input("\nPress Enter to continue...")
        else:
            print_warning("No active projects to open")
            input("\nPress Enter to continue...")
    elif choice == "2":
        view_project_memos_flow()
    elif choice == "3":
        set_release_date_flow()
    elif choice == "4":
        search_projects_flow()
    elif choice == "5":
        filter_by_category_flow()
    elif choice == 'b':
        return
    
    input("\nPress Enter to continue...")