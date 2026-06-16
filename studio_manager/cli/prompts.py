from rich.prompt import Prompt, Confirm
from rich import print as rprint
from .display import print_separator, print_dim, print_error, print_info

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

def get_input_with_completion(prompt: str, field: str, history_obj, allow_backtrack: bool = True) -> str:
    """Get user input with tab completion, suggestions, and backtracking"""
    import readline
    from ..data.history import ProjectHistory
    
    # This is a simplified version - the full version needs the Completer class
    # For now, just get regular input
    while True:
        user_input = input(f"{prompt}: ").strip()
        
        if allow_backtrack and user_input.lower() in ['b', 'back', 'backtrack', '..']:
            return "##BACKTRACK##"
        
        if not user_input:
            print_error("Input cannot be empty. Please try again.")
            continue
        
        return user_input