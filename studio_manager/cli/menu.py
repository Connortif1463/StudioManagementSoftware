# studio_manager/cli/menu.py

from rich.panel import Panel
from rich import print as rprint
from .display import console, print_menu

def show_main_menu():
    """Display the main menu with clear descriptions"""
    menu_text = """[bold white]Main Menu[/bold white]

[cyan]1[/cyan] - Create New Project
    Create a new song or album project with session templates

[cyan]2[/cyan] - Open Recent Projects/Tasks
    View statistics, session memos, finished projects, and search

[cyan]3[/cyan] - Project Browser
    Browse and search all active/finished projects

[cyan]4[/cyan] - Album Management
    Organize songs into albums and manage track order

[cyan]5[/cyan] - File Tree Viewer
    Visualize the file directory structure and project organization

[cyan]6[/cyan] - Backup System
    Create and manage project backups

[cyan]7[/cyan] - Bug Report
    Submit and view bug reports

[cyan]q[/cyan] - Quit
    Exit the application
"""
    print_menu(menu_text, title="Studio Management System")