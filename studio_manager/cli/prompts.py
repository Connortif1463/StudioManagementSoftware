from rich.prompt import Prompt, Confirm
from rich import print as rprint
from .display import print_error

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