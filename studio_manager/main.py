import sys
import readline
from pathlib import Path
from rich.panel import Panel

from .cli.display import clear_screen, console, print_success, print_error, print_warning, print_info, print_dim, print_separator, show_recent_projects_table, show_statistics_table
from .cli.menu import show_main_menu
from .data.history import ProjectHistory
from .data.logger import SessionLogger
from .features.file_tree import file_tree_flow
from .features.session_memo import set_history
from .features.project_flows import new_project_flow
from .features.backup_flows import global_backup_flow
from .features.tasks_flows import tasks_and_projects_flow
from .features.browser_flows import project_browser_flow
from .features.album_flows import album_management_flow
from .utils.helpers import list_all_projects

# Initialize
history = ProjectHistory()
session_logger = SessionLogger()
set_history(history)

def main():
    """Main program entry point"""
    session_logger.start_session()
    session_logger.log_action("APPLICATION_START", "Studio Management System started")
    
    clear_screen()
    console.print(Panel.fit("[bold white]Studio Management System[/bold white]", 
                          subtitle="Version 1.0.0", style="white"))
    input("\nPress Enter to continue...")
    
    while True:
        try:
            clear_screen()
            show_main_menu()
            
            console.print("[bold]Select an option: [/bold]", end="")
            objective = input().strip()
            
            if objective.lower() == 'q':
                session_logger.log_action("APPLICATION_EXIT", "User exited")
                session_logger.save_session()
                clear_screen()
                print_success("EXITED SUCCESSFULLY.")
                sys.exit(0)
            elif objective == "1":
                new_project_flow(history)
            elif objective == "2":
                tasks_and_projects_flow(history)
            elif objective == "3":
                project_browser_flow(history)
            elif objective == "4":
                album_management_flow()
            elif objective == "5":
                file_tree_flow()
            elif objective == "6":
                global_backup_flow()
            else:
                print_error("\nInvalid option. Please choose 1, 2, 3, 4, 5, 6, or q")
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            session_logger.log_action("APPLICATION_EXIT", "Keyboard interrupt")
            session_logger.save_session()
            clear_screen()
            print_warning("\nEXITED.")
            sys.exit(0)
        except Exception as e:
            session_logger.log_action("APPLICATION_ERROR", f"Error: {str(e)}")
            session_logger.save_session()
            print_error(f"\nAn unexpected error occurred: {e}")
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()