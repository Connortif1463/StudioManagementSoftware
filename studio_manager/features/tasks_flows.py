# studio_manager/features/tasks_flows.py

"""Tasks and projects flow - statistics, memos, finished projects, search"""
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from rich.panel import Panel
from rich.table import Table
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_separator, show_statistics_table
from ..cli.prompts import get_confirmation
from .project_tracker import ProjectTracker
from .session_memo import SessionMemo, prompt_for_session_memo
from ..utils.helpers import get_project_path, list_all_projects
from .browser_flows import show_song_project_details
from .open_project import ProjectOpener
from .project_flows import manage_project_stage_flow


def view_project_memos_flow():
    """Flow for viewing memos from a project - excludes finished projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]View Session Memos[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        input("\nPress Enter to continue...")
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
        input("\nPress Enter to continue...")
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
        else:
            print_error("Invalid project number")
            input("\nPress Enter to continue...")
    elif proj_choice.lower() == 'b':
        return
    
    # If we get here (user pressed b or invalid), return to tasks menu
    return


def set_release_date_flow():
    """Flow for setting expected release date on a project - excludes finished projects"""
    clear_screen()
    console.print(Panel.fit("[bold white]Set Release Date[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    if not projects:
        print_warning("No projects found")
        input("\nPress Enter to continue...")
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
        input("\nPress Enter to continue...")
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
    if proj_choice.lower() == 'b':
        return
    
    if not proj_choice.isdigit():
        print_error("Please enter a valid number")
        input("\nPress Enter to continue...")
        return
    
    idx = int(proj_choice) - 1
    if idx < 0 or idx >= len(active_songs):
        print_error("Invalid project number")
        input("\nPress Enter to continue...")
        return
    
    project, tracker = active_songs[idx]
    
    while True:
        release_date = input("\nEnter expected release date (YYYY-MM-DD) or press Enter to cancel: ").strip()
        if not release_date:
            print_info("Cancelled")
            input("\nPress Enter to continue...")
            return
        
        # Validate date format
        try:
            datetime.fromisoformat(release_date)
            # Valid date, set it
            tracker.data["release_date"] = release_date
            tracker.calculate_priority()
            tracker.save()
            print_success(f"Release date set for {project['project']} to {release_date}")
            input("\nPress Enter to continue...")
            return
        except ValueError:
            print_error("Invalid date format. Please use YYYY-MM-DD (e.g., 2026-04-20)")
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
        print_info("\n  No finished projects found!")
        input("\nPress Enter to continue...")
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
                    input("\nPress Enter to continue...")
                    return  # Return after reopening
                else:
                    input("\nPress Enter to continue...")
                    return
            else:
                print_error("Invalid project number")
                input("\nPress Enter to continue...")
                return
        else:
            print_error("Please enter a valid number")
            input("\nPress Enter to continue...")
            return
    else:
        # If they don't want to reopen, just return
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
        created_pretty = project.get("date_created_pretty", "Unknown")
        # Format date
        try:
            if created_pretty != "Unknown" and 'T' in created_pretty:
                dt = datetime.fromisoformat(created_pretty)
                created_pretty = dt.strftime('%a %d %b %Y, %I:%M%p')
        except:
            pass
        
        table.add_row(
            str(idx),
            project["project"],
            project["artist"],
            stage,
            created_pretty
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


def filter_by_category_flow(history):
    """Filter active songs by project category and allow actions"""
    clear_screen()
    console.print(Panel.fit("[bold white]Filter by Category[/bold white]", style="white"))
    
    console.print("\n[bold]Categories:\n[/bold]")
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
        input("\nPress Enter to continue...")
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
        print_info(f"\nNo projects found in this category")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Projects - {selected_category.replace('_', ' ').title() if selected_category != 'all' else 'All Categories'}", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Project", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Stage", style="magenta")
    table.add_column("Category", style="dim")
    
    for idx, (project, stage, category) in enumerate(filtered, 1):
        display_category = category.replace('_', ' ').title()
        table.add_row(str(idx), project["project"], project["artist"], stage, display_category)
    
    console.print(table)
    
    print_separator()
    console.print("[bold]Options:[/bold]")
    console.print("  [cyan]1[/cyan] - Open a project from the list")
    console.print("  [cyan]2[/cyan] - View session memos from a project")
    console.print("  [cyan]3[/cyan] - Set release date for a project")
    console.print("  [cyan]b[/cyan] - Go back")
    
    action = input("\nSelect option: ").strip().lower()
    
    if action == 'b':
        return
    
    if action not in ["1", "2", "3"]:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        return
    
    proj_choice = input("\nEnter project number: ").strip()
    if not proj_choice.isdigit():
        print_error("Please enter a valid number")
        input("\nPress Enter to continue...")
        return
    
    idx = int(proj_choice) - 1
    if idx < 0 or idx >= len(filtered):
        print_error("Invalid project number")
        input("\nPress Enter to continue...")
        return
    
    project, stage, category = filtered[idx]
    project_path = project["path"]
    
    if action == "1":
        # Open the project
        opener = ProjectOpener()
        selected_session, affected_sessions = opener.open_project_interactive(project_path, history)
        
        if selected_session:
            print_separator()
            console.print("[bold]Session Complete![/bold]")
            console.print(f"  Project: [green]{project['project']}[/green]")
            
            tracker = ProjectTracker(project_path)
            console.print(f"  Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
            
            if get_confirmation("\nUpdate project stage after this session?"):
                manage_project_stage_flow(project_path)
            
            prompt_for_session_memo(project_path, history, is_manual=False,
                                  selected_session=selected_session,
                                  affected_sessions=affected_sessions)
        else:
            print_warning("No session was opened.")
            
    elif action == "2":
        # View memos
        memo = SessionMemo(project_path)
        view_choice = input("\nInteractive navigation? (y/n, default y): ").strip().lower()
        if view_choice == 'n':
            memo.view_memos(interactive=False)
        else:
            memo.view_memos(interactive=True)
        input("\nPress Enter to continue...")
    elif action == "3":
        # Set release date
        tracker = ProjectTracker(project_path)
        while True:
            release_date = input("\nEnter expected release date (YYYY-MM-DD) or press Enter to cancel: ").strip()
            if not release_date:
                break
            try:
                datetime.fromisoformat(release_date)
                tracker.data["release_date"] = release_date
                tracker.calculate_priority()
                tracker.save()
                print_success(f"Release date set for {project['project']} to {release_date}")
                break
            except ValueError:
                print_error("Invalid date format. Please use YYYY-MM-DD")
                continue
        input("\nPress Enter to continue...")


def tasks_and_projects_flow(history):
    """Tasks and Projects - view statistics, memos, finished projects, search"""
    from .open_project import ProjectOpener
    
    clear_screen()
    console.print(Panel.fit("[bold white]Tasks & Projects[/bold white]", style="white"))
    
    projects = list_all_projects()
    
    active_songs = []
    finished_songs = []
    
    for project in projects:
        # Skip albums - they have .album.json file
        if (project["path"] / ".album.json").exists():
            continue
        
        # Skip backup folders
        if "_backup_" in project["project"]:
            continue
        
        # It's a song project
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
        table = Table(title="Active Songs", style="white", expand=True)
        table.add_column("#", style="cyan", width=4)
        table.add_column("Priority", style="red", width=10, justify="center")
        table.add_column("Date", style="cyan")
        table.add_column("Song", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Stage", style="magenta")
        table.add_column("Release", style="dim", width=12)
        
        for idx, project in enumerate(active_songs, 1):
            created_pretty = project.get("date_created_pretty", "Unknown")
            
            # Format the date properly
            if created_pretty != "Unknown":
                try:
                    if 'T' in created_pretty:
                        dt = datetime.fromisoformat(created_pretty)
                        created_pretty = dt.strftime('%a %d %b %Y, %I:%M%p')
                except:
                    # If parsing fails, try to get from tracker
                    tracker = ProjectTracker(project["path"])
                    if tracker.data.get("stage_history"):
                        created_str = tracker.data["stage_history"][0].get("started", "")
                        if created_str:
                            try:
                                dt = datetime.fromisoformat(created_str)
                                created_pretty = dt.strftime('%a %d %b %Y, %I:%M%p')
                            except:
                                import time
                                mod_time = project["path"].stat().st_ctime
                                created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
                        else:
                            import time
                            mod_time = project["path"].stat().st_ctime
                            created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
                    else:
                        import time
                        mod_time = project["path"].stat().st_ctime
                        created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
            else:
                # Fallback to tracker or file system
                tracker = ProjectTracker(project["path"])
                if tracker.data.get("stage_history"):
                    created_str = tracker.data["stage_history"][0].get("started", "")
                    if created_str:
                        try:
                            dt = datetime.fromisoformat(created_str)
                            created_pretty = dt.strftime('%a %d %b %Y, %I:%M%p')
                        except:
                            import time
                            mod_time = project["path"].stat().st_ctime
                            created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
                    else:
                        import time
                        mod_time = project["path"].stat().st_ctime
                        created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
                else:
                    import time
                    mod_time = project["path"].stat().st_ctime
                    created_pretty = time.strftime("%Y-%m-%d %H:%M", time.localtime(mod_time))
            
            priority_display = "★" * min(project.get("priority", 0), 4) if project.get("priority", 0) > 0 else "•"
            priority_display = priority_display.center(6)
            
            release = project.get("release_date", "TBD")
            if release and release != "TBD":
                try:
                    if 'T' in release:
                        dt = datetime.fromisoformat(release)
                        release = dt.strftime("%Y-%m-%d")
                    else:
                        release = release[:10]
                except:
                    release = "TBD"
            else:
                release = "TBD"
            
            table.add_row(
                str(idx),
                priority_display,
                created_pretty,
                project["project"],
                project["artist"],
                project.get("stage", "production"),
                release
            )
        
        console.print(table)
    else:
        console.print("[dim]No active songs in progress[/dim]")
    
    # Show finished songs count
    if finished_songs:
        print_separator()
        console.print(f"[dim]Note: {len(finished_songs)} finished song(s) not shown.[/dim]")
        console.print("[dim]To view finished songs, go to Project Browser → View finished projects[/dim]")
    
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
        if active_songs:
            proj_choice = input("\nEnter the number of the project to open: ").strip()
            if proj_choice.isdigit():
                idx = int(proj_choice) - 1
                if 0 <= idx < len(active_songs):
                    project = active_songs[idx]
                    project_path = project["path"]
                    
                    # Open the project
                    opener = ProjectOpener()
                    selected_session, affected_sessions = opener.open_project_interactive(project_path, history)
                    
                    # Only proceed if we got a valid session back
                    if selected_session:
                        print_separator()
                        console.print("[bold]Session Complete![/bold]")
                        console.print(f"  Project: [green]{project['project']}[/green]")
                        
                        tracker = ProjectTracker(project_path)
                        console.print(f"  Current Stage: [cyan]{tracker.get_current_stage()}[/cyan]")
                        
                        if get_confirmation("\nUpdate project stage after this session?"):
                            manage_project_stage_flow(project_path)
                        
                        # Pass the session data to the memo prompt
                        prompt_for_session_memo(project_path, history, is_manual=False,
                                              selected_session=selected_session,
                                              affected_sessions=affected_sessions)
                    else:
                        print_warning("No session was opened.")
                    
                    tasks_and_projects_flow(history)
                    return
                else:
                    print_error("Invalid project number")
                    input("\nPress Enter to continue...")
                    tasks_and_projects_flow(history)
                    return
            else:
                print_error("Please enter a valid number")
                input("\nPress Enter to continue...")
                tasks_and_projects_flow(history)
                return
        else:
            print_warning("No active projects to open")
            input("\nPress Enter to continue...")
            tasks_and_projects_flow(history)
            return
    
    elif choice == "2":
        view_project_memos_flow()
        tasks_and_projects_flow(history)
        return
    
    elif choice == "3":
        set_release_date_flow()
        tasks_and_projects_flow(history)
        return
    
    elif choice == "4":
        search_projects_flow()
        tasks_and_projects_flow(history)
        return
    
    elif choice == "5":
        filter_by_category_flow(history)
        tasks_and_projects_flow(history)
        return
    
    elif choice == 'b':
        return
    
    else:
        print_error("Invalid option")
        input("\nPress Enter to continue...")
        tasks_and_projects_flow(history)
        return


# ============================================================================
# Task Action Handler - For use by other modules
# ============================================================================

def handle_task_action(action: str, task_data: Dict, config):
    """
    Handle a task action from the tasks system.
    This is called when a user selects a task from the task list.
    
    Args:
        action: The action to perform ('open_project', 'open_session', etc.)
        task_data: Dictionary containing task information
        config: UserConfig instance
    """
    from .open_project import open_project_from_task, open_session_direct
    
    if not task_data:
        print_error("No task data provided")
        return
    
    try:
        if action == "open_project":
            open_project_from_task(task_data, config)
        elif action == "open_session":
            session_path = task_data.get("session_path")
            daw_code = task_data.get("daw_code")
            
            if not session_path:
                print_error("No session path provided in task data")
                return
                
            if not daw_code:
                print_error("No DAW code provided in task data")
                return
                
            open_session_direct(Path(session_path), daw_code, config)
        else:
            print_warning(f"Unknown task action: {action}")
    except Exception as e:
        print_error(f"Error handling task action: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# Task System Integration Helper
# ============================================================================

class TaskActionHandler:
    """
    Handles task actions from the task system.
    This is a class-based version for easier integration.
    """
    
    def __init__(self, config):
        self.config = config
        self.opener = ProjectOpener(config)
    
    def handle(self, action: str, task_data: Dict) -> bool:
        """
        Handle a task action.
        
        Returns:
            bool: True if action was handled successfully, False otherwise
        """
        if not task_data:
            print_error("No task data provided")
            return False
        
        try:
            if action == "open_project":
                self._open_project(task_data)
                return True
            elif action == "open_session":
                self._open_session(task_data)
                return True
            else:
                print_warning(f"Unknown task action: {action}")
                return False
        except Exception as e:
            print_error(f"Error handling task: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _open_project(self, task_data: Dict):
        """Open a project from task data"""
        project_name = task_data.get("project")
        artist = task_data.get("artist")
        project_path = task_data.get("path")
        
        if project_path:
            # Use path if provided
            self.opener.open_project_interactive(Path(project_path))
        elif project_name and artist:
            # Find project by name and artist
            found_path = self.opener.find_project(artist, project_name)
            if found_path:
                self.opener.open_project_interactive(found_path)
            else:
                print_error(f"Project '{project_name}' not found for artist '{artist}'")
        else:
            print_error("Insufficient task data: need project path or name+artist")
    
    def _open_session(self, task_data: Dict):
        """Open a session from task data"""
        session_path = task_data.get("session_path")
        daw_code = task_data.get("daw_code")
        
        if not session_path:
            print_error("No session path provided")
            return
        
        if not daw_code:
            print_error("No DAW code provided")
            return
        
        self.opener.open_session(Path(session_path), daw_code)