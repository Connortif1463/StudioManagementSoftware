import json
import readline
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from rich.panel import Panel
from ..cli.display import console, print_header, print_separator, print_success, print_info, print_error, print_warning, print_dim, clear_screen
from ..cli.prompts import get_text_input, get_choice, get_confirmation
from ..data.history import ProjectHistory

# Available roles for tab completion
AVAILABLE_ROLES = ["Engineer", "Producer", "Artist", "Musician", "Vocalist", "Other"]

# Available instruments for musicians
AVAILABLE_INSTRUMENTS = [
    "Guitar", "Bass", "Drums", "Piano", "Keyboard", "Vocals", "Backing Vocals",
    "Violin", "Viola", "Cello", "Trumpet", "Saxophone", "Flute", "Clarinet",
    "Synth", "Sampler", "Drum Machine", "Percussion", "DJ", "Producer",
    "String Arrangement", "Horn Arrangement", "Orchestration"
]

# Global history reference for name suggestions
_history = None

def set_history(history_obj: ProjectHistory):
    """Set the history object for name suggestions"""
    global _history
    _history = history_obj

def get_all_names_from_history() -> List[str]:
    """Get all unique names from history"""
    if not _history:
        return []
    
    all_names = set()
    all_names.update(_history.data.get("artists", set()))
    all_names.update(_history.data.get("engineers", set()))
    
    # Also add all contributors from session memos
    for project in _history.data.get("projects", []):
        if "contributors" in project:
            for contributor in project.get("contributors", []):
                if isinstance(contributor, dict):
                    all_names.add(contributor.get("name", ""))
                elif isinstance(contributor, str):
                    all_names.add(contributor)
    
    return [name for name in all_names if name]

class CustomCompleter:
    """Custom completer that cycles through options on tab"""
    def __init__(self, options):
        self.options = sorted(set(options))
        self.matches = []
        self.index = -1
        self.last_text = ""
    
    def complete(self, text, state):
        # Check if text has changed from last call
        if text != self.last_text:
            self.last_text = text
            self.index = -1
            if not text:
                self.matches = self.options[:]
            else:
                self.matches = [opt for opt in self.options if opt.lower().startswith(text.lower())]
            self.index = -1
        
        # Cycle through matches
        if state == 0:
            self.index = (self.index + 1) % len(self.matches) if self.matches else -1
        
        if state < len(self.matches) and self.index >= 0:
            return self.matches[self.index]
        return None

def setup_completion(options):
    """Setup tab completion with proper cycling"""
    if options:
        completer = CustomCompleter(options)
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set show-all-if-ambiguous on")
    else:
        readline.set_completer(None)

def get_input_with_completion(prompt: str, options: List[str], allow_new: bool = True, allow_empty: bool = False) -> str:
    """Get input with tab completion that cycles through options"""
    # Setup completion
    setup_completion(options)
    
    while True:
        user_input = input(f"{prompt}: ").strip()
        
        if user_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not user_input:
            if allow_empty:
                return ""
            print_error("Input cannot be empty")
            continue
        
        # Check if input matches an existing option (case insensitive)
        matched = None
        for opt in options:
            if opt.lower() == user_input.lower():
                matched = opt
                break
        
        if matched:
            return matched
        
        # Check for partial matches
        partial_matches = [opt for opt in options if opt.lower().startswith(user_input.lower())]
        if partial_matches:
            print_warning("Did you mean one of these?")
            for i, match in enumerate(partial_matches[:5], 1):
                console.print(f"  {i}. {match}")
            if allow_new:
                console.print("  0. Use as new")
            
            choice = input("\nSelect option: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(partial_matches[:5]):
                    return partial_matches[idx]
                elif int(choice) == 0 and allow_new:
                    return user_input
            continue
        
        # No matches, ask to create new
        if allow_new:
            return user_input
        
        return user_input

def get_role_input(prompt: str) -> str:
    """Get role input with tab cycling"""
    setup_completion(AVAILABLE_ROLES)
    
    while True:
        role_input = input(f"{prompt}: ").strip()
        
        if role_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not role_input:
            print_error("Role cannot be empty")
            continue
        
        # Match case-insensitively
        matched = None
        for role in AVAILABLE_ROLES:
            if role.lower() == role_input.lower():
                matched = role
                break
        
        # Check partial matches
        if not matched:
            for role in AVAILABLE_ROLES:
                if role.lower().startswith(role_input.lower()):
                    matched = role
                    break
        
        if matched:
            return matched
        
        print_error(f"'{role_input}' is not a valid role")
        print_info(f"Please choose from: {', '.join(AVAILABLE_ROLES)}")

def get_instrument_input(prompt: str) -> str:
    """Get instrument input with autocomplete for musicians"""
    setup_completion(AVAILABLE_INSTRUMENTS)
    
    while True:
        instrument = input(f"{prompt}: ").strip()
        
        if instrument.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not instrument:
            print_error("Instrument cannot be empty")
            continue
        
        # Check if instrument exists in list
        matched = None
        for inst in AVAILABLE_INSTRUMENTS:
            if inst.lower() == instrument.lower():
                matched = inst
                break
        
        if matched:
            return matched
        
        # Check partial matches
        partial_matches = [inst for inst in AVAILABLE_INSTRUMENTS if inst.lower().startswith(instrument.lower())]
        if partial_matches:
            print_warning("Did you mean one of these?")
            for i, match in enumerate(partial_matches[:5], 1):
                console.print(f"  {i}. {match}")
            console.print("  0. Use as new instrument")
            
            choice = input("\nSelect option: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(partial_matches[:5]):
                    return partial_matches[idx]
                elif int(choice) == 0:
                    return instrument
        
        # Accept custom instrument
        confirm = input(f"Use '{instrument}' as custom instrument? (y/n): ").strip().lower()
        if confirm in ['y', 'yes']:
            return instrument

class SessionMemo:
    """Handles session memos"""
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.memo_file = self.project_path / "session_memos.json"
        self.memos = self.load_memos()
    
    def load_memos(self) -> Dict:
        """Load existing memos"""
        if self.memo_file.exists():
            with open(self.memo_file, 'r') as f:
                return json.load(f)
        return {"sessions": []}
    
    def save_memos(self):
        """Save memos to file"""
        with open(self.memo_file, 'w') as f:
            json.dump(self.memos, f, indent=2)
    
    def create_memo(self):
        """Create a new session memo with database suggestions"""
        print_header("Session Memo")
        
        memo = {
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "contributors": [],
            "tasks_completed": [],
            "notes": "",
            "files_created": []
        }
        
        # Get all names from history for suggestions
        all_names = get_all_names_from_history()
        
        # Get contributors with name suggestions from database
        console.print("\n[bold]Who was at this session?[/bold]")
        print_info("Enter names one by one. Press Enter with no name to finish.")
        
        if all_names:
            print_info(f"Press TAB to cycle through {len(all_names)} names from previous sessions")
        
        while True:
            # Allow empty input to exit the loop
            name = get_input_with_completion("\nContributor name", all_names, allow_new=True, allow_empty=True)
            if name == "##BACKTRACK##":
                continue
            if not name:
                break  # Exit the loop on empty input
            
            # Get role
            role_prompt = f"Role for {name}"
            role = get_role_input(role_prompt)
            
            if role == "##BACKTRACK##":
                continue
            
            # If role is Musician, ask for instrument
            instrument = None
            if role == "Musician":
                print_info("Press TAB for instrument suggestions")
                instrument = get_instrument_input(f"Instrument for {name}")
                if instrument == "##BACKTRACK##":
                    continue
            
            contributor_entry = {"name": name, "role": role}
            if instrument:
                contributor_entry["instrument"] = instrument
                print_success(f"Added {name} as {role} ({instrument})")
            else:
                print_success(f"Added {name} as {role}")
            
            memo["contributors"].append(contributor_entry)
            
            # Add this name to the list for future suggestions in this session
            if name not in all_names:
                all_names.append(name)
        
        if not memo["contributors"]:
            print_warning("No contributors added. Skipping memo.")
            return None
        
        # Get tasks
        console.print("\n[bold]What was accomplished?[/bold]")
        print_info("Enter tasks one by one. Press Enter with no text to finish.")
        while True:
            task = input("\nTask completed: ").strip()
            if not task:
                break
            memo["tasks_completed"].append(task)
            print_success(f"Added task: {task}")
        
        # Get notes
        notes = input("\nAdditional notes (or press Enter to skip): ").strip()
        if notes:
            memo["notes"] = notes
        
        # Get files
        console.print("\n[bold]Files created/modified:[/bold]")
        print_info("Enter file names one by one. Press Enter with no name to finish.")
        
        while True:
            file_name = input("\nFile name: ").strip()
            if not file_name:
                break
            
            # File type selection
            file_type_options = ["Session", "Audio", "MIDI", "Export", "Other"]
            print_info(f"Available types: {', '.join(file_type_options)}")
            
            while True:
                file_type = input(f"File type for {file_name}: ").strip().lower()
                
                matched_type = None
                for ft in file_type_options:
                    if ft.lower() == file_type:
                        matched_type = ft
                        break
                
                if matched_type:
                    if matched_type == "Other":
                        custom_type = input("Specify file type: ").strip()
                        memo["files_created"].append({"name": file_name, "type": custom_type})
                    else:
                        memo["files_created"].append({"name": file_name, "type": matched_type})
                    print_success(f"Added file: {file_name} ({matched_type})")
                    break
                
                print_error(f"'{file_type}' is not a valid type")
                print_info(f"Please choose from: {', '.join(file_type_options)}")
        
        self.memos["sessions"].append(memo)
        self.save_memos()
        
        print_separator()
        print_success("Session memo saved successfully!")
        
        # Summary - using console.print for all Rich markup
        console.print("\n[bold]Session Summary:[/bold]")
        console.print(f"  Date: [cyan]{memo['date']} at {memo['time']}[/cyan]")
        console.print(f"  Contributors: [green]{', '.join([c['name'] for c in memo['contributors']])}[/green]")
        console.print(f"  Tasks: [green]{len(memo['tasks_completed'])} completed[/green]")
        
        return memo
    
    def view_last_memo(self):
        """View the most recent session memo without editing"""
        if not self.memos["sessions"]:
            print_warning("No session memos found for this project")
            return None
        
        # Get the most recent memo
        last_memo = self.memos["sessions"][-1]
        
        print_header(f"Most Recent Memo - {last_memo['date']} at {last_memo['time']}")
        
        # Display memo content
        console.print("\n[bold]Contributors:[/bold]")
        for c in last_memo["contributors"]:
            if "instrument" in c:
                console.print(f"  - {c['name']} ({c['role']} - {c['instrument']})")
            else:
                console.print(f"  - {c['name']} ({c['role']})")
        
        if last_memo["tasks_completed"]:
            console.print("\n[bold]Tasks Completed:[/bold]")
            for task in last_memo["tasks_completed"]:
                console.print(f"  - {task}")
        
        if last_memo["notes"]:
            console.print("\n[bold]Notes:[/bold]")
            note_lines = last_memo["notes"].split('\n')
            for line in note_lines:
                console.print(f"  {line}")
        
        if last_memo["files_created"]:
            console.print("\n[bold]Files Created/Modified:[/bold]")
            for f in last_memo["files_created"]:
                console.print(f"  - {f['name']} ({f['type']})")
        
        if last_memo.get("last_edited"):
            console.print(f"\n[dim]Last edited: {last_memo['last_edited_pretty']}[/dim]")
        
        return last_memo
    
    def edit_last_memo(self):
        """Edit the most recent session memo"""
        if not self.memos["sessions"]:
            print_warning("No session memos found to edit")
            return None
        
        # Get the most recent memo
        last_memo = self.memos["sessions"][-1]
        
        print_header(f"Editing Memo from {last_memo['date']} at {last_memo['time']}")
        
        console.print("\n[bold cyan]Current Content:[/bold cyan]")
        console.print(f"  Contributors: {', '.join([c['name'] for c in last_memo['contributors']])}")
        console.print(f"  Tasks: {len(last_memo['tasks_completed'])} tasks")
        if last_memo['notes']:
            console.print(f"  Notes: {last_memo['notes']}")
        
        print_separator()
        
        if not get_confirmation("\nWould you like to add to this memo?"):
            return None
        
        # Add new tasks
        console.print("\n[bold]Add new tasks completed:[/bold]")
        print_info("Enter tasks one by one. Press Enter with no text to finish.")
        while True:
            task = input("\nTask completed: ").strip()
            if not task:
                break
            last_memo["tasks_completed"].append(task)
            print_success(f"Added task: {task}")
        
        # Add to notes
        additional_notes = input("\nAdd to notes (or press Enter to skip): ").strip()
        if additional_notes:
            if last_memo["notes"]:
                last_memo["notes"] += f"\n{additional_notes}"
            else:
                last_memo["notes"] = additional_notes
            print_success("Notes updated")
        
        # Add new files
        console.print("\n[bold]Add new files created/modified:[/bold]")
        print_info("Enter file names one by one. Press Enter with no name to finish.")
        
        file_type_options = ["Session", "Audio", "MIDI", "Export", "Other"]
        
        while True:
            file_name = input("\nFile name: ").strip()
            if not file_name:
                break
            
            print_info(f"Available types: {', '.join(file_type_options)}")
            
            while True:
                file_type = input(f"File type for {file_name}: ").strip().lower()
                
                matched_type = None
                for ft in file_type_options:
                    if ft.lower() == file_type:
                        matched_type = ft
                        break
                
                if matched_type:
                    if matched_type == "Other":
                        custom_type = input("Specify file type: ").strip()
                        last_memo["files_created"].append({"name": file_name, "type": custom_type})
                    else:
                        last_memo["files_created"].append({"name": file_name, "type": matched_type})
                    print_success(f"Added file: {file_name} ({matched_type})")
                    break
                
                print_error(f"'{file_type}' is not a valid type")
                print_info(f"Please choose from: {', '.join(file_type_options)}")
        
        # Update timestamp to show when edited
        last_memo["last_edited"] = datetime.now().isoformat()
        last_memo["last_edited_pretty"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.save_memos()
        print_success("\nMemo updated successfully!")
        
        # Show updated summary
        console.print("\n[bold]Updated Session Summary:[/bold]")
        console.print(f"  Contributors: [green]{', '.join([c['name'] for c in last_memo['contributors']])}[/green]")
        console.print(f"  Tasks: [green]{len(last_memo['tasks_completed'])} completed[/green]")
        
        return last_memo
    
    def edit_existing_memo(self, memo):
        """Edit an existing memo (not just the last one)"""
        print_header(f"Editing Memo from {memo['date']} at {memo['time']}")
        
        console.print("\n[bold cyan]Current Content:[/bold cyan]")
        console.print(f"  Contributors: {', '.join([c['name'] for c in memo['contributors']])}")
        console.print(f"  Tasks: {len(memo['tasks_completed'])} tasks")
        if memo['notes']:
            console.print(f"  Notes: {memo['notes']}")
        
        print_separator()
        
        if not get_confirmation("\nWould you like to add to this memo?"):
            return None
        
        # Add new tasks
        console.print("\n[bold]Add new tasks completed:[/bold]")
        print_info("Enter tasks one by one. Press Enter with no text to finish.")
        while True:
            task = input("\nTask completed: ").strip()
            if not task:
                break
            memo["tasks_completed"].append(task)
            print_success(f"Added task: {task}")
        
        # Add to notes
        additional_notes = input("\nAdd to notes (or press Enter to skip): ").strip()
        if additional_notes:
            if memo["notes"]:
                memo["notes"] += f"\n{additional_notes}"
            else:
                memo["notes"] = additional_notes
            print_success("Notes updated")
        
        # Add new files
        console.print("\n[bold]Add new files created/modified:[/bold]")
        print_info("Enter file names one by one. Press Enter with no name to finish.")
        
        file_type_options = ["Session", "Audio", "MIDI", "Export", "Other"]
        
        while True:
            file_name = input("\nFile name: ").strip()
            if not file_name:
                break
            
            print_info(f"Available types: {', '.join(file_type_options)}")
            
            while True:
                file_type = input(f"File type for {file_name}: ").strip().lower()
                
                matched_type = None
                for ft in file_type_options:
                    if ft.lower() == file_type:
                        matched_type = ft
                        break
                
                if matched_type:
                    if matched_type == "Other":
                        custom_type = input("Specify file type: ").strip()
                        memo["files_created"].append({"name": file_name, "type": custom_type})
                    else:
                        memo["files_created"].append({"name": file_name, "type": matched_type})
                    print_success(f"Added file: {file_name} ({matched_type})")
                    break
                
                print_error(f"'{file_type}' is not a valid type")
                print_info(f"Please choose from: {', '.join(file_type_options)}")
        
        # Update timestamp to show when edited
        memo["last_edited"] = datetime.now().isoformat()
        memo["last_edited_pretty"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.save_memos()
        print_success("\nMemo updated successfully!")
        
        # Show updated summary
        console.print("\n[bold]Updated Session Summary:[/bold]")
        console.print(f"  Contributors: [green]{', '.join([c['name'] for c in memo['contributors']])}[/green]")
        console.print(f"  Tasks: [green]{len(memo['tasks_completed'])} completed[/green]")
        
        return memo
    
    def view_memos_interactive(self):
        """View session memos with interactive navigation (most recent first)"""
        if not self.memos["sessions"]:
            print_dim("No session memos found for this project")
            return
        
        # Reverse to show most recent first
        sessions = list(reversed(self.memos["sessions"]))
        total = len(sessions)
        current_idx = 0  # Start at most recent
        
        while True:
            clear_screen()
            memo = sessions[current_idx]
            
            # Calculate display number: most recent = total, oldest = 1
            display_num = total - current_idx
            
            # Header with navigation info
            if current_idx == 0:
                console.print(Panel.fit(
                    f"[bold white]Session Memo {display_num} of {total} (Most Recent)[/bold white]", 
                    style="white"
                ))
            else:
                console.print(Panel.fit(
                    f"[bold white]Session Memo {display_num} of {total}[/bold white]", 
                    style="white"
                ))
            
            # Display memo content
            console.print(f"\n[bold cyan]Date:[/bold cyan] [yellow]{memo['date']} at {memo['time']}[/yellow]")
            
            # Contributors
            console.print("\n[bold]Contributors:[/bold]")
            for c in memo["contributors"]:
                if "instrument" in c:
                    console.print(f"  - {c['name']} ({c['role']} - {c['instrument']})")
                else:
                    console.print(f"  - {c['name']} ({c['role']})")
            
            # Tasks
            if memo["tasks_completed"]:
                console.print("\n[bold]Tasks Completed:[/bold]")
                for task in memo["tasks_completed"]:
                    console.print(f"  - {task}")
            
            # Notes - with proper indentation for multi-line
            if memo["notes"]:
                console.print("\n[bold]Notes:[/bold]")
                note_lines = memo["notes"].split('\n')
                for line in note_lines:
                    console.print(f"  {line}")
            
            # Files
            if memo["files_created"]:
                console.print("\n[bold]Files Created/Modified:[/bold]")
                for f in memo["files_created"]:
                    console.print(f"  - {f['name']} ({f['type']})")
            
            # Navigation controls
            print_separator()
            console.print("\n[bold]Navigation:[/bold]")
            
            nav_options = []
            if current_idx > 0:
                nav_options.append("[cyan]p[/cyan] - Newer")
            if current_idx < total - 1:
                nav_options.append("[cyan]n[/cyan] - Older")
            nav_options.append("[cyan]f[/cyan] - First (Most Recent)")
            nav_options.append("[cyan]l[/cyan] - Last (Oldest)")
            nav_options.append("[cyan]e[/cyan] - Edit this memo")
            nav_options.append("[cyan]q[/cyan] - Quit")
            
            console.print("  ".join(nav_options))
            
            choice = input("\nChoice: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'p' and current_idx > 0:
                current_idx -= 1  # Go to newer memo (decrease index)
            elif choice == 'n' and current_idx < total - 1:
                current_idx += 1  # Go to older memo (increase index)
            elif choice == 'f':
                current_idx = 0  # Jump to first (most recent)
            elif choice == 'l':
                current_idx = total - 1  # Jump to last (oldest)
            elif choice == 'e':
                # Edit the current memo
                self.edit_existing_memo(memo)
                # Reload memos after editing
                self.memos = self.load_memos()
                sessions = list(reversed(self.memos["sessions"]))
                total = len(sessions)
                if current_idx >= total:
                    current_idx = total - 1
            else:
                if choice:
                    print_error("Invalid choice")
                    input("\nPress Enter to continue...")
        
        clear_screen()

    def view_memos(self, interactive: bool = True):
        """View all session memos - interactive mode by default"""
        if interactive:
            self.view_memos_interactive()
        else:
            # Original non-interactive view
            if not self.memos["sessions"]:
                print_dim("No session memos found for this project")
                return
            
            print_header("Session History")
            
            for idx, memo in enumerate(reversed(self.memos["sessions"]), 1):
                console.print(f"\n[bold cyan]Session #{idx}[/bold cyan] - [yellow]{memo['date']} at {memo['time']}[/yellow]")
                console.print("  [bold]Contributors:[/bold]")
                for c in memo["contributors"]:
                    if "instrument" in c:
                        console.print(f"    - {c['name']} ({c['role']} - {c['instrument']})")
                    else:
                        console.print(f"    - {c['name']} ({c['role']})")
                console.print("  [bold]Tasks:[/bold]")
                for task in memo["tasks_completed"]:
                    console.print(f"    - {task}")
                if memo["notes"]:
                    console.print("  [bold]Notes:[/bold]")
                    note_lines = memo["notes"].split('\n')
                    for line in note_lines:
                        console.print(f"    {line}")
                if memo["files_created"]:
                    console.print("  [bold]Files:[/bold]")
                    for f in memo["files_created"]:
                        console.print(f"    - {f['name']} ({f['type']})")
                if idx < len(self.memos["sessions"]):
                    print_separator("-", 50)

def prompt_for_session_memo(project_path: Path, history_obj: ProjectHistory = None, is_manual: bool = False):
    """
    Prompt user for session memo.
    - If called after DAW session (is_manual=False): create new memo
    - If called manually from menu (is_manual=True): ONLY view/edit existing memos, no new creation
    """
    global _history
    _history = history_obj
    
    memo = SessionMemo(project_path)
    
    if is_manual:
        # Manual view from menu - ONLY view/edit existing memos
        print_separator()
        
        if not memo.memos["sessions"]:
            print_warning("No session memos found for this project")
            return None
        
        # Show the last memo
        memo.view_last_memo()
        
        print_separator()
        console.print("\n[bold]Options:[/bold]")
        console.print("  [cyan]1[/cyan] - Add to this memo")
        console.print("  [cyan]2[/cyan] - View all memos")
        console.print("  [cyan]b[/cyan] - Go back")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == "1":
            return memo.edit_last_memo()
        elif choice == "2":
            memo.view_memos(interactive=True)
            return None
        else:
            return None
    else:
        # Called after DAW session - create new memo
        print_separator()
        if get_confirmation("\nRecord session notes and contributor information?"):
            return memo.create_memo()
        return None