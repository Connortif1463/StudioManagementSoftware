from .display import console, print_menu, clear_screen

def show_main_menu():
    """Display the main menu with clear descriptions"""
    clear_screen()
    menu_text = """
[bold white]Main Menu[/bold white]

  [cyan]1[/cyan] - Create New Project
       Create a new song or album project with session templates

  [cyan]2[/cyan] - Open Existing Project  
       Load and work on an existing project

  [cyan]3[/cyan] - View File Tree
       Browse directory structure and project organization

  [cyan]4[/cyan] - View Tasks & Statistics
       See project history, statistics, and recent activity

  [cyan]5[/cyan] - Album Management
       Organize songs into albums and manage track order

  [cyan]6[/cyan] - Backup System
       Create and manage project backups

  [cyan]q[/cyan] - Quit
       Exit the application

"""
    print_menu(menu_text, title="Studio Management System")

def show_file_tree_options():
    """Display file tree options"""
    console.print("\n[bold]Options:[/bold]")
    console.print("  1 - Show full project structure (artists folder)")
    console.print("  2 - Show current working directory tree")
    console.print("  3 - Show specific directory tree")
    console.print("  b - Return to main menu")