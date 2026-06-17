# studio_manager/features/open_project.py

import os
import subprocess
import platform
import time
import psutil
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.console import Console
from datetime import datetime

from ..cli.display import console, print_success, print_error, print_warning, print_info, clear_screen
from ..cli.prompts import get_choice, get_confirmation
from ..utils.config import UserConfig
from ..utils.daw_discovery import DAWDiscovery
from ..features.daw_setup import get_daw_path_manually, run_daw_setup_wizard
from .project_tracker import ProjectTracker
from ..utils.constants import DAW_MAP, DAW_PATHS


def get_daw_process_identifiers(daw_code: str) -> dict:
    """
    Get process identifiers for a DAW.
    Returns a dict with process names and bundle IDs for better detection.
    """
    identifiers = {
        "A": {
            "names": ["Ableton Live", "Ableton Live 11", "Ableton Live 11 Suite", 
                     "Ableton Live 12", "Ableton Live 12 Suite", "Ableton"],
            "bundle_ids": ["com.ableton.live", "com.ableton.Live", "com.ableton.Live11", "com.ableton.Live12"]
        },
        "P": {
            "names": ["Pro Tools", "ProTools", "Pro Tools Ultimate"],
            "bundle_ids": ["com.avid.ProTools", "com.avid.ProToolsUltimate"]
        },
        "L": {
            "names": ["Logic Pro X", "Logic Pro", "Logic"],
            "bundle_ids": ["com.apple.logic10", "com.apple.logic"]
        }
    }
    return identifiers.get(daw_code, {"names": ["DAW"], "bundle_ids": []})


def get_daw_process_name(daw_code: str) -> str:
    """Get the display name for a DAW"""
    display_names = {
        "A": "Ableton Live",
        "P": "Pro Tools",
        "L": "Logic Pro"
    }
    return display_names.get(daw_code, "DAW")


def is_daw_running(daw_code: str, check_bundle: bool = True) -> Tuple[bool, str]:
    """
    Check if a DAW process is running.
    Returns (is_running, process_name)
    """
    identifiers = get_daw_process_identifiers(daw_code)
    names_to_check = identifiers.get("names", [])
    bundle_ids = identifiers.get("bundle_ids", [])
    
    system = platform.system()
    
    # On macOS, we can also check via AppleScript for bundle ID
    if system == "Darwin" and check_bundle:
        try:
            for bundle_id in bundle_ids:
                # Check if app with bundle ID is running
                result = subprocess.run(
                    ["osascript", "-e", f'tell application "System Events" to get name of every process whose bundle identifier is "{bundle_id}"'],
                    capture_output=True, text=True, timeout=2
                )
                if result.returncode == 0 and result.stdout.strip():
                    return True, result.stdout.strip().split(",")[0].strip()
        except:
            pass
    
    # Check via psutil
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            proc_name = proc.info['name']
            if proc_name:
                for name in names_to_check:
                    if name.lower() in proc_name.lower():
                        return True, proc_name
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return False, ""


def wait_for_daw_close(daw_code: str, timeout_minutes: int = 60):
    """
    Wait for the DAW process to close with a live spinner display.
    Uses multiple detection methods.
    """
    display_name = get_daw_process_name(daw_code)
    identifiers = get_daw_process_identifiers(daw_code)
    
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]{display_name} is Open[/bold cyan]\n\n"
        f"[dim]Work in your DAW. Close it when you're done.[/dim]\n"
        f"[dim]The program will automatically continue.[/dim]",
        style="white"
    ))
    
    # Wait a moment for the DAW to fully launch
    time.sleep(3)
    
    start_time = time.time()
    max_seconds = timeout_minutes * 60
    check_interval = 2
    found_first = False
    current_process = ""
    
    with Live(console=console, refresh_per_second=10) as live:
        while True:
            is_running, process_name = is_daw_running(daw_code)
            
            if is_running:
                found_first = True
                current_process = process_name
            else:
                # If we found it before and now it's gone, DAW closed
                if found_first:
                    live.update("[bold green]DAW closed! Continuing...[/bold green]")
                    break
                # If we haven't found it yet, wait longer (still launching)
                else:
                    time.sleep(1)
                    continue
            
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner = spinner_chars[elapsed % len(spinner_chars)]
            
            live.update(
                f"[yellow]{spinner}[/yellow] Waiting for {display_name} to close... "
                f"[dim]({minutes:02d}:{seconds:02d} elapsed)[/dim]\n"
                f"[dim]Detected: {current_process}[/dim]\n"
                f"[dim]Press Ctrl+C to stop waiting and continue[/dim]"
            )
            
            if time.time() - start_time > max_seconds:
                live.update("[bold yellow]Timeout reached. Continuing...[/bold yellow]")
                break
            
            time.sleep(check_interval)


class ProjectOpener:
    """Handles opening projects and their DAW sessions"""
    
    DAW_CODE_MAP = {
        "Ableton": "A",
        "Pro Tools": "P",
        "Logic": "L"
    }
    
    def __init__(self, config: Optional[UserConfig] = None):
        self.config = config or UserConfig()
        self.os_type = DAWDiscovery.get_os()
    
    def find_project(self, artist: str, project_name: str) -> Optional[Path]:
        """Find a project by artist and name"""
        project_path = Path.cwd() / "artists" / artist / project_name
        if project_path.exists() and project_path.is_dir():
            return project_path
        return None
    
    def get_all_projects(self) -> List[Dict]:
        """Get all projects from the filesystem"""
        projects = []
        artists_path = Path.cwd() / "artists"
        
        if not artists_path.exists():
            return projects
        
        for artist_dir in artists_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir():
                        tracker_file = project_dir / ".project_tracker.json"
                        if tracker_file.exists():
                            try:
                                import json
                                with open(tracker_file, 'r') as f:
                                    data = json.load(f)
                                    projects.append({
                                        "name": project_dir.name,
                                        "artist": artist_dir.name,
                                        "path": project_dir,
                                        "stage": data.get("current_stage", "production"),
                                        "category": data.get("project_category", "unknown"),
                                        "tracker": ProjectTracker(project_dir)
                                    })
                            except:
                                projects.append({
                                    "name": project_dir.name,
                                    "artist": artist_dir.name,
                                    "path": project_dir,
                                    "stage": "unknown",
                                    "category": "unknown",
                                    "tracker": None
                                })
        
        return projects
    
    def find_als_files(self, directory: Path) -> List[Path]:
        """Recursively find all .als files in a directory"""
        als_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.als'):
                    als_files.append(Path(root) / file)
        
        return als_files
    
    def get_session_files(self, project_path: Path, daw_code: str = None) -> List[Dict]:
        """Find all session files in a project, including those in subfolders.
        Sorted by last modified (most recent first)."""
        sessions = []
        
        stages = ["production", "mix", "master"]
        
        if daw_code:
            daw_info = DAW_PATHS.get(daw_code, {})
            daw_folder = daw_info.get("folder", "")
            daws_to_check = [daw_folder] if daw_folder else []
        else:
            daws_to_check = ["ableton", "protools", "logic"]
        
        for stage in stages:
            for daw_folder in daws_to_check:
                session_dir = project_path / stage / daw_folder
                if session_dir.exists():
                    als_files = self.find_als_files(session_dir)
                    
                    for file in als_files:
                        ext = file.suffix.lower()
                        daw_code_from_ext = {
                            ".als": "A",
                            ".ptx": "P",
                            ".logicx": "L",
                            ".sesx": "P",
                            ".cpr": "C"
                        }.get(ext, "Unknown")
                        
                        daw_name = DAW_MAP.get(daw_code_from_ext, daw_code_from_ext)
                        
                        stat = file.stat()
                        last_modified = datetime.fromtimestamp(stat.st_mtime)
                        file_size = stat.st_size
                        
                        rel_path = file.relative_to(project_path)
                        is_project_folder = file.parent.name.endswith(" Project") or "Project" in file.parent.name
                        
                        sessions.append({
                            "path": file,
                            "name": file.name,
                            "stage": stage,
                            "daw_code": daw_code_from_ext,
                            "daw_name": daw_name,
                            "folder": daw_folder,
                            "relative_path": rel_path,
                            "parent_folder": file.parent.name,
                            "last_modified": last_modified,
                            "last_modified_pretty": last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                            "size_mb": file_size / (1024 * 1024),
                            "is_project_folder": is_project_folder
                        })
        
        return sorted(sessions, key=lambda x: x["last_modified"], reverse=True)
    
    def open_session(self, session_path: Path, daw_code: str) -> bool:
        """Open a DAW session and wait for it to close"""
        
        daw_path = self.config.get_daw_path(daw_code)
        
        if not daw_path:
            print_warning(f"DAW ({get_daw_process_name(daw_code)}) not configured.")
            print_info("Let's set it up now.")
            from ..features.daw_setup import run_daw_setup_wizard
            run_daw_setup_wizard(self.config)
            daw_path = self.config.get_daw_path(daw_code)
            
            if not daw_path:
                print_error("DAW setup cancelled or failed.")
                return False
        
        if not DAWDiscovery.validate_path(daw_path):
            print_error(f"DAW not found at: {daw_path}")
            print_info("This might be because the DAW was moved, updated, or uninstalled.")
            
            if get_confirmation("\nWould you like to update the path?"):
                daw_name = get_daw_process_name(daw_code)
                new_path = get_daw_path_manually(daw_name, self.os_type)
                
                if new_path and new_path != "##BACKTRACK##":
                    if DAWDiscovery.validate_path(new_path):
                        self.config.set_daw_path(daw_code, new_path)
                        daw_path = new_path
                        print_success("DAW path updated successfully!")
                    else:
                        print_error("Invalid path. Please try again.")
                        return False
                else:
                    print_warning("Path update cancelled.")
                    return False
            else:
                print_info("You can open the session manually from your DAW.")
                return False
        
        display_name = get_daw_process_name(daw_code)
        print_info(f"Opening {display_name} with {session_path.name}...")
        
        try:
            if self.os_type == "windows":
                subprocess.Popen([daw_path, str(session_path)], shell=True)
                wait_for_daw_close(daw_code)
                
            elif self.os_type == "mac":
                # Launch the app using open
                subprocess.Popen(["open", "-a", daw_path, str(session_path)])
                # Wait for the app to launch before starting the wait loop
                time.sleep(4)
                wait_for_daw_close(daw_code)
                
            else:
                print_error(f"Unsupported operating system: {self.os_type}")
                return False
                
        except KeyboardInterrupt:
            print_info("\nWaiting cancelled by user.")
            return True
            
        except FileNotFoundError:
            print_error(f"Could not find DAW at: {daw_path}")
            return False
        except Exception as e:
            print_error(f"Failed to open DAW: {e}")
            return False
        
        return True
    
    def prompt_for_current_session(self, project_path: Path, opened_session: Dict, history) -> Tuple[Dict, List[Dict]]:
        """AFTER the DAW session, ask which session file is now the current one."""
        
        # Get all sessions (refreshed after DAW closed)
        all_sessions = self.get_session_files(project_path)
        
        if not all_sessions:
            print_warning("No session files found. Something went wrong.")
            return None, []
        
        newest_session = all_sessions[0]
        
        # Show the session file that was opened
        console.print("\n[bold]Session File You Opened:[/bold]")
        console.print(f"  [cyan]{opened_session['name']}[/cyan]")
        console.print(f"  Location: [dim]{opened_session['parent_folder']}[/dim]")
        console.print(f"  Stage: [yellow]{opened_session['stage']}[/yellow]")
        
        opened_exists = opened_session['path'].exists()
        if not opened_exists:
            print_warning(f"The session file '{opened_session['name']}' no longer exists.")
            print_info("It may have been moved, renamed, or deleted.")
        
        # Display all sessions with the newest one highlighted
        console.print("\n[bold]All Session Files (including new/modified):[/bold]")
        table = Table(style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("File", style="white")
        table.add_column("Stage", style="yellow")
        table.add_column("Location", style="dim")
        table.add_column("Last Modified", style="dim")
        table.add_column("Status", style="green")
        
        for idx, session in enumerate(all_sessions, 1):
            status = ""
            
            if idx == 1:
                status = "[bold green]<< NEWEST[/bold green]"
            elif session["path"] == opened_session["path"] and opened_exists:
                status = "[bold cyan]<< OPENED[/bold cyan]"
            elif opened_exists and session["last_modified"] > opened_session["last_modified"]:
                status = "[yellow]NEWER[/yellow]"
            
            table.add_row(
                str(idx),
                session["name"],
                session["stage"],
                session["parent_folder"],
                session["last_modified_pretty"],
                status
            )
        
        console.print(table)
        
        console.print("\n[bold]Which session file is now the current one?[/bold]")
        console.print(f"[dim]Press Enter to select the newest file: [green]{newest_session['name']}[/green][/dim]")
        console.print("[dim]Or enter a number to select a specific file.[/dim]")
        
        while True:
            choice = input("\nSelect current session: ").strip()
            
            if not choice:
                selected_session = newest_session
                print_info(f"Selected newest file: {selected_session['name']}")
                break
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(all_sessions):
                    selected_session = all_sessions[idx]
                    break
                else:
                    print_error(f"Invalid selection. Please enter a number between 1 and {len(all_sessions)}")
            else:
                print_error("Invalid input. Enter a number or press Enter for the newest file.")
        
        # Ask if any other sessions were affected
        affected = [selected_session]
        other_sessions = [s for s in all_sessions if s["path"] != selected_session["path"]]
        
        if other_sessions:
            print_info("\nWere any other sessions affected during this session?")
            print_info("Select all that apply (enter numbers separated by spaces, or press Enter to skip):")
            
            table2 = Table(style="white")
            table2.add_column("#", style="cyan", width=4)
            table2.add_column("File", style="white")
            table2.add_column("Stage", style="yellow")
            table2.add_column("Last Modified", style="dim")
            
            for idx, session in enumerate(other_sessions, 1):
                table2.add_row(
                    str(idx),
                    session["name"],
                    session["stage"],
                    session["last_modified_pretty"]
                )
            
            console.print(table2)
            
            while True:
                choice = input("\nEnter numbers (e.g., '1 3 5') or press Enter to skip: ").strip()
                
                if not choice:
                    break
                
                try:
                    indices = [int(x.strip()) - 1 for x in choice.split() if x.strip().isdigit()]
                    
                    for idx in indices:
                        if 0 <= idx < len(other_sessions):
                            if other_sessions[idx]["path"] not in [a["path"] for a in affected]:
                                affected.append(other_sessions[idx])
                        else:
                            print_warning(f"Invalid selection: {idx + 1}")
                            continue
                    break
                except ValueError:
                    print_error("Please enter numbers separated by spaces (e.g., '1 3 5')")
                    continue
        
        console.print("\n[bold]Session Tracking Summary:[/bold]")
        console.print(f"  Current Session: [green]{selected_session['name']}[/green]")
        if len(affected) > 1:
            console.print(f"  Other Affected: [yellow]{len(affected) - 1}[/yellow]")
        
        return selected_session, affected
    
    def open_project_interactive(self, project_path: Path, history=None):
        """Interactive project opening with session selection"""
        clear_screen()
        console.print(Panel.fit(f"[bold white]Open Project: {project_path.name}[/bold white]", style="white"))
        
        tracker = ProjectTracker(project_path)
        print_info(f"\nArtist: [cyan]{project_path.parent.name}[/cyan]")
        print_info(f"Stage: [yellow]{tracker.get_current_stage()}[/yellow]")
        print_info(f"Category: [cyan]{tracker.get_project_category().replace('_', ' ').title()}[/cyan]")
        
        sessions = self.get_session_files(project_path)
        
        if not sessions:
            print_warning("\nNo session files found in this project.")
            print_info("Make sure you've created a session in production, mix, or master.")
            input("\nPress Enter to continue...")
            return None, None
        
        console.print("\n[bold]Available Sessions (most recent first):[/bold]")
        table = Table(style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Stage", style="yellow")
        table.add_column("DAW", style="green")
        table.add_column("File", style="white")
        table.add_column("Location", style="dim")
        table.add_column("Last Modified", style="dim")
        table.add_column("Size", style="dim", width=10)
        
        for idx, session in enumerate(sessions, 1):
            size_str = f"{session['size_mb']:.1f} MB" if session['size_mb'] > 0.1 else "< 0.1 MB"
            
            stage_display = session["stage"]
            if session["stage"] == tracker.get_current_stage():
                stage_display = f"[bold cyan]{session['stage']}[/bold cyan]"
            
            location = session["parent_folder"]
            if session.get("is_project_folder"):
                location = f"[dim]{location}[/dim]"
            
            table.add_row(
                str(idx),
                stage_display,
                session["daw_name"],
                session["name"],
                location,
                session["last_modified_pretty"],
                size_str
            )
        
        console.print(table)
        
        while True:
            print_info("\nEnter a number to open a session, or press Enter to open the most recent.")
            print_info("[dim]Enter 'b' to go back[/dim]")
            choice = input("\nSelect session: ").strip().lower()
            
            if choice == 'b':
                return None, None
            
            if not choice:
                selected = sessions[0]
                break
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(sessions):
                    selected = sessions[idx]
                    break
                else:
                    print_error(f"Invalid selection. Please enter a number between 1 and {len(sessions)}")
            else:
                print_error("Invalid input. Enter a number, press Enter for most recent, or 'b' to go back.")
        
        opened_session = selected
        
        success = self.open_session(selected["path"], selected["daw_code"])
        
        if not success:
            print_error("Failed to open DAW session.")
            return None, None
        
        current_session, affected_sessions = self.prompt_for_current_session(
            project_path, opened_session, history
        )
        
        return current_session, affected_sessions
    
    def open_from_browser(self, history=None):
        """Open a project from the browser flow"""
        clear_screen()
        console.print(Panel.fit("[bold white]Browse & Open Project[/bold white]", style="white"))
        
        projects = self.get_all_projects()
        
        if not projects:
            print_warning("\nNo projects found.")
            print_info("Create a new project first.")
            input("\nPress Enter to continue...")
            return None, None
        
        console.print("\n[bold]Projects:[/bold]")
        table = Table(style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Project", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Stage", style="magenta")
        table.add_column("Category", style="blue")
        
        for idx, project in enumerate(projects, 1):
            table.add_row(
                str(idx),
                project["name"],
                project["artist"],
                project["stage"],
                project["category"].replace("_", " ").title()
            )
        
        console.print(table)
        
        while True:
            choice = input("\nSelect project number (or 'b' to go back): ").strip().lower()
            
            if choice == 'b':
                return None, None
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(projects):
                    selected = projects[idx]
                    return self.open_project_interactive(selected["path"], history)
                else:
                    print_error("Invalid selection. Please try again.")
            else:
                print_error("Please enter a number or 'b' to go back.")
    
    def open_from_tasks(self, task_data: Dict, history=None):
        """Open a project from the tasks flow"""
        project_name = task_data.get("project")
        artist = task_data.get("artist")
        
        if not project_name or not artist:
            print_error("Task missing project or artist information.")
            return None, None
        
        project_path = self.find_project(artist, project_name)
        
        if not project_path:
            print_error(f"Project '{project_name}' not found for artist '{artist}'.")
            return None, None
        
        return self.open_project_interactive(project_path, history)


# Convenience functions for easy import

def open_project_browser(config: UserConfig = None, history=None):
    """Open the project browser"""
    opener = ProjectOpener(config)
    return opener.open_from_browser(history)

def open_project_from_task(task_data: Dict, config: UserConfig = None, history=None):
    """Open a project from task data"""
    opener = ProjectOpener(config)
    return opener.open_from_tasks(task_data, history)

def open_project_by_path(project_path: Path, config: UserConfig = None, history=None):
    """Open a project by path"""
    opener = ProjectOpener(config)
    return opener.open_project_interactive(project_path, history)

def open_session_direct(session_path: Path, daw_code: str, config: UserConfig = None):
    """Open a session directly"""
    opener = ProjectOpener(config)
    return opener.open_session(session_path, daw_code)