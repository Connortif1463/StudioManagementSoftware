# studio_manager/cli/prompts.py

import sys
import json
from pathlib import Path
from rich import print as rprint
from .display import print_separator, print_dim, print_error, print_info, print_warning, console

# Define DummyReadline at the module level FIRST
class DummyReadline:
    """Dummy readline class for when no real readline is available"""
    def set_completer(self, *args, **kwargs): pass
    def parse_and_bind(self, *args, **kwargs): pass
    def set_completer_delims(self, *args, **kwargs): pass
    def get_line_buffer(self, *args, **kwargs): return ""
    def insert_text(self, *args, **kwargs): pass
    def redisplay(self, *args, **kwargs): pass

# Platform-specific readline import
readline = DummyReadline()
READLINE_TYPE = "Dummy"

if sys.platform == 'win32':
    try:
        import readline as rl
        readline = rl
        READLINE_TYPE = "readline"
    except ImportError:
        try:
            import pyreadline3 as rl
            readline = rl
            READLINE_TYPE = "pyreadline3"
        except ImportError:
            pass
elif sys.platform == 'darwin':
    try:
        import gnureadline as readline
        READLINE_TYPE = "gnureadline"
    except ImportError:
        try:
            import readline
            READLINE_TYPE = "libedit"
        except ImportError:
            pass
else:
    try:
        import readline
        READLINE_TYPE = "readline"
    except ImportError:
        pass

if readline is None:
    readline = DummyReadline()
    READLINE_TYPE = "Dummy"

# Initialize readline - CRITICAL: Unbind 'b' from backward-char on macOS
if not isinstance(readline, DummyReadline):
    try:
        readline.parse_and_bind("tab: self-insert")
        if sys.platform == 'darwin':
            try:
                readline.parse_and_bind('b: self-insert')
                readline.parse_and_bind('B: self-insert')
            except:
                pass
    except:
        pass

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
        
        if state == 0:
            self.index = (self.index + 1) % len(self.matches) if self.matches else -1
        
        if state < len(self.matches) and self.index >= 0:
            return self.matches[self.index]
        return None


def setup_completion(options):
    """Setup tab completion with proper cycling"""
    if isinstance(readline, DummyReadline) or not readline:
        return
    
    try:
        if options:
            completer = CustomCompleter(options)
            readline.set_completer(completer.complete)
            
            if sys.platform == 'darwin':
                try:
                    readline.parse_and_bind("bind ^I rl_complete")
                except:
                    pass
                try:
                    readline.parse_and_bind("tab: complete")
                except:
                    pass
                try:
                    readline.parse_and_bind('b: self-insert')
                    readline.parse_and_bind('B: self-insert')
                except:
                    pass
            else:
                readline.parse_and_bind("tab: complete")
                readline.parse_and_bind("set show-all-if-ambiguous on")
        else:
            if hasattr(readline, 'set_completer'):
                readline.set_completer(None)
    except Exception as e:
        pass


def clear_completion():
    """Clear the completer and restore normal behavior"""
    if isinstance(readline, DummyReadline) or not readline:
        return
    
    try:
        if hasattr(readline, 'set_completer'):
            readline.set_completer(None)
        try:
            readline.parse_and_bind("tab: self-insert")
        except:
            pass
        if sys.platform == 'darwin':
            try:
                readline.parse_and_bind('b: self-insert')
                readline.parse_and_bind('B: self-insert')
            except:
                pass
    except Exception as e:
        pass


# Aliases for session_memo.py
def enable_tab_completion(options):
    """Alias for setup_completion - used by session_memo.py"""
    setup_completion(options)

def disable_tab_completion():
    """Alias for clear_completion - used by session_memo.py"""
    clear_completion()


def get_raw_input(prompt: str) -> str:
    """Get input with completion disabled"""
    clear_completion()
    return input(prompt)


def get_choice(prompt: str, choices: list, default: str = None) -> str:
    clear_completion()
    
    choices_display = "/".join([f"[cyan]{c}[/cyan]" for c in choices])
    console.print(f"{prompt} [{choices_display}]", end=" ")
    
    while True:
        user_input = get_raw_input("").strip().upper()
        if user_input in choices:
            return user_input
        if default and user_input == "":
            return default
        print_error(f"Invalid choice. Please choose from: {', '.join(choices)}")


def get_confirmation(prompt: str) -> bool:
    clear_completion()
    
    console.print(f"{prompt} [cyan]y[/cyan]/[cyan]n[/cyan]: ", end="")
    
    while True:
        user_input = get_raw_input("").strip().lower()
        if user_input in ['y', 'yes']:
            return True
        if user_input in ['n', 'no']:
            return False
        print_error("Please enter 'y' or 'n'")


def get_text_input(prompt: str, allow_empty: bool = False, allow_backtrack: bool = True) -> str:
    user_input = get_raw_input(f"{prompt}: ").strip()
    
    if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
        return "##BACKTRACK##"
    
    if not allow_empty and not user_input:
        print_error("Input cannot be empty")
        return get_text_input(prompt, allow_empty, allow_backtrack)
    
    return user_input


def get_number_input(prompt: str, min_val: int = None, max_val: int = None, allow_backtrack: bool = True):
    user_input = get_raw_input(f"{prompt}: ").strip()
    
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
    candidates = []
    
    # First, get names from session memos (works even with no projects)
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
    Get user input with TAB completion from history.
    On macOS, 'b' is explicitly bound to self-insert so it works as a normal character.
    """
    global _tip_shown
    
    candidates = get_candidates_from_history(field, history_obj)
    setup_completion(candidates)
    
    is_real_readline = not isinstance(readline, DummyReadline)
    
    if candidates and is_real_readline and not _tip_shown.get(field, False):
        field_display = field.capitalize()
        print_info(f"\n[cyan]Tip: Press TAB to autocomplete {field_display} names from history[/cyan]")
        print_info("[dim]Type 'b' and press Enter to go back[/dim]")
        _tip_shown[field] = True
    
    try:
        while True:
            user_input = input(f"{prompt}: ").strip()
            
            if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
                return "##BACKTRACK##"
            
            if not user_input:
                print_error("Input cannot be empty. Please try again.")
                continue
            
            for candidate in candidates:
                if candidate.lower() == user_input.lower():
                    return candidate
            
            return user_input
    finally:
        clear_completion()