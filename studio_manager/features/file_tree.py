# studio_manager/features/file_tree.py

from pathlib import Path
from rich.panel import Panel
from ..cli.display import console, clear_screen, print_error
from ..cli.prompts import get_raw_input

def file_tree_flow():
    """Handle file tree display flow"""
    from ..core.file_system import print_directory_tree, print_full_project_tree
    
    clear_screen()
    console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
    
    while True:
        # Show options with Rich formatting
        console.print("\n[bold]Options:[/bold]")
        console.print("  [cyan]1[/cyan] - Show full project structure (artists folder)")
        console.print("  [cyan]2[/cyan] - Show current working directory tree")
        console.print("  [cyan]3[/cyan] - Show specific directory tree")
        console.print("  [cyan]b[/cyan] - Return to main menu")
        
        choice = get_raw_input("\nSelect an option: ").strip().lower()
        
        if choice in ['b', 'back', 'backtrack']:
            return
        elif choice == "1":
            clear_screen()
            print_full_project_tree()
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        elif choice == "2":
            clear_screen()
            print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        elif choice == "3":
            path_input = get_raw_input("\nEnter directory path (or press Enter for current directory): ").strip()
            clear_screen()
            if path_input:
                print_directory_tree(Path(path_input), max_depth=3)
            else:
                print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            clear_screen()
            console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
        else:
            print_error("Invalid option")