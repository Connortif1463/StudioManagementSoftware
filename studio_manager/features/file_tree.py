from pathlib import Path
from rich.panel import Panel
from ..cli.display import console, clear_screen, print_error
from ..cli.menu import show_file_tree_options
from ..features.project_tracker import ProjectTracker

def file_tree_flow():
    """Handle file tree display flow"""
    from ..core.file_system import print_directory_tree, print_full_project_tree
    
    clear_screen()
    console.print(Panel.fit("[bold white]File Tree Viewer[/bold white]", style="white"))
    
    while True:
        show_file_tree_options()
        
        choice = input("\nSelect an option: ").strip()
        
        if choice.lower() in ['b', 'back', 'backtrack']:
            return
        elif choice == "1":
            clear_screen()
            print_full_project_tree()  # This will show colored current stage
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
            path_input = input("\nEnter directory path (or press Enter for current directory): ").strip()
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