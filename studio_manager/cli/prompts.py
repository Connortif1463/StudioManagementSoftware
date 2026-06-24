# studio_manager/cli/prompts.py

import sys
import readline
from rich.prompt import Prompt, Confirm
from rich import print as rprint
from .display import print_separator, print_dim, print_error, print_info, print_warning

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
    try:
        if options:
            completer = CustomCompleter(options)
            readline.set_completer(completer.complete)
            readline.parse_and_bind("tab: complete")
            readline.parse_and_bind("set show-all-if-ambiguous on")
        else:
            readline.set_completer(None)
    except Exception as e:
        # If readline fails, silently continue
        pass


def get_choice(prompt: str, choices: list, default: str = None) -> str:
    """Get a choice from the user"""
    return Prompt.ask(prompt, choices=choices, default=default)


def get_confirmation(prompt: str) -> bool:
    """Get yes/no confirmation"""
    return Confirm.ask(prompt)


def get_text_input(prompt: str, allow_empty: bool = False, allow_backtrack: bool = True) -> str:
    """Get text input with backtrack support"""
    user_input = input(f"{prompt}: ").strip()
    
    if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
        return "##BACKTRACK##"
    
    if not allow_empty and not user_input:
        print_error("Input cannot be empty")
        return get_text_input(prompt, allow_empty, allow_backtrack)
    
    return user_input


def get_number_input(prompt: str, min_val: int = None, max_val: int = None, allow_backtrack: bool = True):
    """Get numeric input with validation"""
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


def get_candidates_from_history(field: str, history_obj) -> list:
    """
    Get candidates from history for a given field.
    This properly gathers names from both sets and project entries.
    """
    candidates = []
    
    if field == "artist":
        # Get artists from the artists set
        candidates = list(history_obj.data.get("artists", set()))
        
        # Also get artists from projects
        for project in history_obj.data.get("projects", []):
            if project.get("artist"):
                candidates.append(project.get("artist"))
    
    elif field == "engineer":
        # Get engineers from the engineers set
        candidates = list(history_obj.data.get("engineers", set()))
        
        # Also get engineers from projects
        for project in history_obj.data.get("projects", []):
            for eng in project.get("engineers", []):
                if eng:
                    candidates.append(eng)
    
    else:
        # Generic field - try to get from data
        candidates = list(history_obj.data.get(f"{field}s", []))
        
        # Also search in projects
        for project in history_obj.data.get("projects", []):
            if project.get(field):
                if isinstance(project[field], list):
                    candidates.extend(project[field])
                else:
                    candidates.append(project[field])
    
    # Remove duplicates and sort
    return sorted(set(candidates))


def get_input_with_completion(prompt: str, field: str, history_obj, allow_backtrack: bool = True) -> str:
    """
    Get user input with tab completion from history data.
    Supports cycling through options with TAB.
    """
    global _tip_shown
    
    # Get candidates from history using the improved function
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
        
        # Check for backtrack
        if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not user_input:
            print_error("Input cannot be empty. Please try again.")
            continue
        
        # If there's a match in candidates, return the matched version (preserves case)
        for candidate in candidates:
            if candidate.lower() == user_input.lower():
                return candidate
        
        # If no match, return the user's input as-is (allows new entries)
        return user_input