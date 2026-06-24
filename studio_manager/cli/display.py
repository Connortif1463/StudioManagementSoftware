from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint
import os

console = Console()

def clear_screen():
    """Clear the console screen for full-screen experience"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str, subtitle: str = None):
    """Print a styled header panel"""
    clear_screen()
    if subtitle:
        console.print(Panel.fit(f"[bold white]{title}[/bold white]", subtitle=subtitle, style="white"))
    else:
        console.print(Panel.fit(f"[bold white]{title}[/bold white]", style="white"))

def print_separator(char: str = "─", length: int = 60):
    """Print a visual separator"""
    console.print(f"[dim]{char * length}[/dim]")

def print_menu(menu_text: str, title: str = None):
    """Print a menu panel"""
    if title:
        console.print(Panel(menu_text, title=title, border_style="white"))
    else:
        console.print(Panel(menu_text, border_style="white"))

def print_success(message: str):
    """Print a success message"""
    rprint(f"[green]{message}[/green]")

def print_error(message: str):
    """Print an error message"""
    rprint(f"[red]{message}[/red]")

def print_warning(message: str):
    """Print a warning message"""
    rprint(f"[yellow]{message}[/yellow]")

def print_info(message: str):
    """Print an info message"""
    rprint(f"[cyan]{message}[/cyan]")

def print_dim(message: str):
    """Print a dimmed message"""
    rprint(f"[dim]{message}[/dim]")

def show_recent_projects_table(projects: list):
    """Display recent projects in a table"""
    if not projects:
        print_dim("No projects found in history")
        return
    
    table = Table(title="Recent Projects", style="white")
    table.add_column("Date & Time", style="cyan")
    table.add_column("Project Name", style="green")
    table.add_column("Artist", style="yellow")
    table.add_column("Type", style="cyan")
    table.add_column("Engineers", style="white")
    
    for project in projects:
        datetime_str = project.get("date_created_pretty", "Unknown")
        project_type = "Song" if project.get("type") == "S" else "Album"
        engineers = ", ".join(project.get("engineers", []))
        
        table.add_row(
            datetime_str,
            project.get("name", "Unknown"),
            project.get("artist", "Unknown"),
            project_type,
            engineers
        )
    
    console.print(table)

def show_statistics_table(stats: dict):
    """Display statistics in a table"""
    table = Table(title="Project Statistics", style="white", width=60)
    table.add_column("Metric", style="bold")
    table.add_column("Value", style="white")
    
    table.add_row("Total Songs", str(stats.get("total_songs", 0)))
    table.add_row("Total Albums", str(stats.get("total_albums", 0)))
    table.add_row("Unique Artists", str(stats.get("unique_artists", 0)))
    table.add_row("Unique Engineers", str(stats.get("unique_engineers", 0)))
    
    console.print(table)