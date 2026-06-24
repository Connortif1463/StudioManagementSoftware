# studio_manager/cli/prompts.py

import sys
import json
from pathlib import Path
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from .display import print_separator, print_dim, print_error, print_info, print_warning

# Define DummyReadline at the module level FIRST
class DummyReadline:
    """Dummy readline class for when no real readline is available"""
    def set_completer(self, *args, **kwargs): pass
    def parse_and_bind(self, *args, **kwargs): pass
    def set_completer_delims(self, *args, **kwargs): pass
    def get_line_buffer(self, *args, **kwargs): return ""
    def insert_text(self, *args, **kwargs): pass
    def redisplay(self, *args, **kwargs): pass

# Try to import readline with proper platform-specific handling (matching session_memo.py)
readline = DummyReadline()

if sys.platform == 'win32':
    try:
        import pyreadline3 as readline
    except ImportError:
        try:
            import readline
        except ImportError:
            pass
elif sys.platform == 'darwin':
    try:
        import gnureadline as readline
    except ImportError:
        try:
            import readline  # Built-in libedit on macOS
        except ImportError:
            pass
else:
    try:
        import readline
    except ImportError:
        pass

# If we still don't have a real readline, use DummyReadline
if readline is None or isinstance(readline, type) and readline.__name__ == 'DummyReadline':
    readline = DummyReadline()

# Track which tips have been shown for each field
_tip_shown = {}

def reset_tip_tracking():
    """Reset the tip tracking for a new session"""
    global _tip_shown
    _tip_shown = {}


class CustomCompleter:
    """Custom completer that cycles through options on tab"""
    def __init__(self, options):
        self.options = sorted(set(options))
        self.matches = []
        self.index = -1
        self.last_text = ""
    
    def complete(self, text, state):
        if text != self.last_text:
            self.last_text = text
            self.index = -1
            if not text:
                self.matches = self.options[:]
            else:
                self.matches = [opt for opt in self.options if opt.lower().startswith(text.lower())]
            self.index = -1
        
        if state == 0 and self.matches:
            self.index = (self.index + 1) % len(self.matches)
        
        if state < len(self.matches) and self.index >= 0:
            return self.matches[self.index]
        return None


def setup_completion(options):
    """Setup tab completion with proper cycling for both Windows and macOS"""
    # Check if we have a real readline (not DummyReadline)
    is_real_readline = not isinstance(readline, DummyReadline)
    
    if not is_real_readline or not readline:
        return
    
    try:
        if options:
            completer = CustomCompleter(options)
            readline.set_completer(completer.complete)
            
            # macOS (libedit) needs different binding
            if sys.platform == 'darwin':
                try:
                    readline.parse_and_bind("bind ^I rl_complete")
                except:
                    pass
                # Also try standard binding
                try:
                    readline.parse_and_bind("tab: complete")
                except:
                    pass
                # Set delimiter to handle spaces in names
                try:
                    if hasattr(readline, 'set_completer_delims'):
                        readline.set_completer_delims(" \t\n;")
                except:
                    pass
            else:
                # Windows/Linux
                readline.parse_and_bind("tab: complete")
                readline.parse_and_bind("set show-all-if-ambiguous on")
        else:
            if hasattr(readline, 'set_completer'):
                readline.set_completer(None)
    except Exception as e:
        pass


def get_choice(prompt: str, choices: list, default: str = None) -> str:
    return Prompt.ask(prompt, choices=choices, default=default)


def get_confirmation(prompt: str) -> bool:
    return Confirm.ask(prompt)


def get_text_input(prompt: str, allow_empty: bool = False, allow_backtrack: bool = True) -> str:
    user_input = input(f"{prompt}: ").strip()
    
    if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
        return "##BACKTRACK##"
    
    if not allow_empty and not user_input:
        print_error("Input cannot be empty")
        return get_text_input(prompt, allow_empty, allow_backtrack)
    
    return user_input


def get_number_input(prompt: str, min_val: int = None, max_val: int = None, allow_backtrack: bool = True):
    user_input = input(f"{prompt}: ").strip()
    
    if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
        return "##BACKTRACK##"
    
    if not user_input.isdigit():
        print_error("Please enter a valid number")
        return get_number_input(prompt, min_val, max_val, allow_backtrack)
    
    num = int(user_input)
    
    if min_val is not None and num < min_val:
        print_error(f"Number must be at least {min_val}")
        return get_number_input(prompt, min_val, max_val, allow_backtrack)
    
    if max_val is not None and num > max_val:
        print_error(f"Number must be at most {max_val}")
        return get_number_input(prompt, min_val, max_val, allow_backtrack)
    
    return num


def get_all_names_from_session_memos() -> list:
    """Scan all session memos and extract contributor names"""
    names = []
    artists_path = Path.cwd() / "artists"
    
    if not artists_path.exists():
        return names
    
    for artist_dir in artists_path.iterdir():
        if artist_dir.is_dir():
            for project_dir in artist_dir.iterdir():
                if project_dir.is_dir():
                    memo_file = project_dir / "session_memos.json"
                    if memo_file.exists():
                        try:
                            with open(memo_file, 'r') as f:
                                data = json.load(f)
                                for session in data.get("sessions", []):
                                    for contributor in session.get("contributors", []):
                                        if contributor.get("name"):
                                            names.append(contributor.get("name"))
                        except:
                            pass
    
    return list(set(names))


def get_candidates_from_history(field: str, history_obj) -> list:
    """
    Get candidates from history for a given field.
    This properly gathers names from both sets, project entries, AND session memos.
    """
    candidates = []
    
    # Always include names from session memos
    memo_names = get_all_names_from_session_memos()
    candidates.extend(memo_names)
    
    if field == "artist":
        candidates.extend(list(history_obj.data.get("artists", set())))
        for project in history_obj.data.get("projects", []):
            if project.get("artist"):
                candidates.append(project.get("artist"))
    
    elif field == "engineer":
        candidates.extend(list(history_obj.data.get("engineers", set())))
        for project in history_obj.data.get("projects", []):
            for eng in project.get("engineers", []):
                if eng:
                    candidates.append(eng)
    
    else:
        candidates.extend(list(history_obj.data.get(f"{field}s", [])))
        for project in history_obj.data.get("projects", []):
            if project.get(field):
                if isinstance(project[field], list):
                    candidates.extend(project[field])
                else:
                    candidates.append(project[field])
    
    return sorted(set(candidates))


def get_input_with_completion(prompt: str, field: str, history_obj, allow_backtrack: bool = True) -> str:
    """
    Get user input with tab completion from history data.
    Works on both Windows (pyreadline3) and macOS (libedit).
    """
    global _tip_shown
    
    # Get candidates from history
    candidates = get_candidates_from_history(field, history_obj)
    
    # Setup tab completion with candidates
    setup_completion(candidates)
    
    # Show tip only ONCE per field per session
    if candidates and not _tip_shown.get(field, False):
        field_display = field.capitalize()
        print_info(f"\nTip: Press TAB to autocomplete {field_display} names from history")
        _tip_shown[field] = True
    
    while True:
        user_input = input(f"{prompt}: ").strip()
        
        if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not user_input:
            print_error("Input cannot be empty. Please try again.")
            continue
        
        # Check if the input matches a candidate (case-insensitive)
        for candidate in candidates:
            if candidate.lower() == user_input.lower():
                return candidate
        
        # If no match, return user input as-is
        return user_input