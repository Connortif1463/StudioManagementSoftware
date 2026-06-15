from pathlib import Path
from ..cli.display import print_header, print_error, print_info, clear_screen
from ..cli.menu import show_file_tree_options

def file_tree_flow():
    """Handle file tree display flow"""
    from ..core.file_system import print_directory_tree, print_full_project_tree
    
    print_header("File Tree Viewer")
    
    while True:
        show_file_tree_options()
        
        choice = input("\nSelect an option: ").strip()
        
        if choice.lower() in ['b', 'back', 'backtrack']:
            return
        elif choice == "1":
            clear_screen()
            print_full_project_tree()
            input("\nPress Enter to continue...")
            print_header("File Tree Viewer")
        elif choice == "2":
            clear_screen()
            print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            print_header("File Tree Viewer")
        elif choice == "3":
            path_input = input("Enter directory path (or press Enter for current directory): ").strip()
            clear_screen()
            if path_input:
                print_directory_tree(Path(path_input), max_depth=3)
            else:
                print_directory_tree(Path.cwd(), max_depth=3)
            input("\nPress Enter to continue...")
            print_header("File Tree Viewer")
        else:
            print_error("Invalid option")