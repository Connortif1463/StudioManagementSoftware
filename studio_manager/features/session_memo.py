import json
import readline
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from ..cli.display import console, print_header, print_separator, print_success, print_info, print_error, print_warning, print_dim
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
    
    def view_memos(self):
        """View all session memos"""
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
                console.print(f"  [bold]Notes:[/bold] {memo['notes']}")
            if memo["files_created"]:
                console.print("  [bold]Files:[/bold]")
                for f in memo["files_created"]:
                    console.print(f"    - {f['name']} ({f['type']})")
            if idx < len(self.memos["sessions"]):
                print_separator("-", 50)

def prompt_for_session_memo(project_path: Path, history_obj: ProjectHistory = None):
    """Prompt user for session memo - only called once when DAW session ends"""
    global _history
    _history = history_obj
    
    print_separator()
    if get_confirmation("\nRecord session notes and contributor information?"):
        memo = SessionMemo(project_path)
        return memo.create_memo()
    return None