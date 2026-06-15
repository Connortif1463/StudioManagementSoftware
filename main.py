import filesys
from history import ProjectHistory
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich import print as rprint
import logging
import sys
from typing import List, Optional

console = Console()
history = ProjectHistory()

# DAW mapping
daw_map = {
    "P": "Pro Tools",
    "A": "Ableton",
    "L": "Logic"
}

def get_input_with_suggestions(prompt: str, field: str, history_obj: ProjectHistory) -> str:
    """Get user input with autocorrect suggestions"""
    while True:
        user_input = Prompt.ask(prompt).strip().lower()
        
        if not user_input:
            rprint("[red]Input cannot be empty. Please try again.[/red]")
            continue
        
        # Get suggestions
        suggestions = history_obj.get_suggestions(field, user_input)
        
        if suggestions:
            rprint("[yellow]Did you mean one of these?[/yellow]")
            for i, suggestion in enumerate(suggestions, 1):
                rprint(f"  {i}. {suggestion}")
            
            choice = Prompt.ask("Use suggestion? (number/yes/no)", default="no")
            if choice.isdigit() and 1 <= int(choice) <= len(suggestions):
                return suggestions[int(choice) - 1]
            elif choice.lower() in ['y', 'yes']:
                return suggestions[0]
        
        return user_input

def get_engineers() -> List[str]:
    """Get engineer names with validation"""
    while True:
        num_input = Prompt.ask("\nEnter the number of engineers on this session", 
                              default="1")
        
        if not num_input.isdigit():
            rprint("[red]Please enter a valid number[/red]")
            continue
        
        num_engineers = int(num_input)
        if num_engineers < 0 or num_engineers > 20:
            rprint("[red]Number of engineers must be between 1 and 20[/red]")
            continue
        
        engineers = []
        for i in range(num_engineers):
            prompt = f"Enter the name of engineer #{i+1}"
            engineer = get_input_with_suggestions(prompt, "engineer", history)
            engineers.append(engineer)
        
        return engineers

def get_project_type() -> str:
    """Get and validate project type"""
    while True:
        type_input = Prompt.ask("\nEnter S for Song, or A for Album", 
                               choices=["S", "A"], 
                               default="S")
        return type_input

def get_daw() -> Optional[str]:
    """Get and validate DAW selection"""
    while True:
        daw_input = Prompt.ask("\nEnter the DAW you're using", 
                              choices=["P", "A", "L"],
                              show_choices=True,
                              show_default=True)
        return daw_input

def new_project_flow():
    """Handle new project creation flow"""
    console.print(Panel.fit("[bold white]Create New Project[/bold white]", style="white"))
    
    try:
        # Get engineers
        engineers = get_engineers()
        
        # Get project name
        name = Prompt.ask("\nEnter the name of your project").strip()
        while not name:
            rprint("[red]Project name cannot be empty[/red]")
            name = Prompt.ask("Enter the name of your project").strip()
        
        # Get project type
        project_type = get_project_type()
        
        # Get artist name with suggestions
        artist = get_input_with_suggestions("\nEnter the name of the artist", "artist", history)
        
        # Get DAW for songs
        daw = ""
        if project_type == "S":
            daw = get_daw()
        
        # Confirm before creating
        rprint("\n[bold]Project Summary:[/bold]")
        rprint(f"  Name: [green]{name}[/green]")
        rprint(f"  Type: [green]{'Song' if project_type == 'S' else 'Album'}[/green]")
        rprint(f"  Artist: [green]{artist}[/green]")
        rprint(f"  Engineers: [green]{', '.join(engineers)}[/green]")
        if daw:
            daw_name = daw_map.get(daw, daw)
            rprint(f"  DAW: [green]{daw_name}[/green]")
        
        if Confirm.ask("\nCreate this project?"):
            # Create the project
            success = filesys.createNewProject(name, project_type, artist, daw)
            
            if success:
                # Add to history
                history.add_project(name, project_type, artist, engineers, daw)
                rprint(f"\n[bold green]Project '{name}' created successfully![/bold green]")
                
                # Show recent projects
                show_recent_projects()
            else:
                rprint("\n[bold red]Failed to create project. Check the logs for details.[/bold red]")
        else:
            rprint("[yellow]Project creation cancelled[/yellow]")
            
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user[/yellow]")
    except Exception as e:
        logging.error(f"Unexpected error in new project flow: {e}")
        rprint(f"[red]An unexpected error occurred: {e}[/red]")

def open_project_flow():
    """Handle opening existing projects"""
    console.print(Panel.fit("[bold white]Open Project[/bold white]", style="white"))
    rprint("[yellow]This feature is coming soon![/yellow]")

def show_tasks():
    """Show current tasks and statistics"""
    console.print(Panel.fit("[bold white]Current Tasks & Statistics[/bold white]", style="white"))
    
    # Show statistics
    history.show_statistics()
    
    # Show recent projects
    show_recent_projects()

def show_recent_projects():
    """Display recent projects from history with full datetime"""
    recent = history.get_recent_projects()
    
    if recent:
        table = Table(title="Recent Projects", style="white")
        table.add_column("Date & Time", style="cyan")
        table.add_column("Project Name", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Engineers", style="white")
        
        for project in recent:
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
        
        # Show additional details for the most recent project
        if recent:
            latest = recent[0]
            rprint("\n[bold]Most Recent Project Details:[/bold]")
            rprint(f"  Created on: {latest.get('date_created_pretty', 'Unknown')}")
            rprint(f"  Weekday: {latest.get('weekday', 'Unknown')}")
            rprint(f"  Week number: {latest.get('week_number', 'Unknown')}")
    else:
        rprint("[dim]No projects found in history[/dim]")

def show_menu():
    """Display the main menu with clear descriptions"""
    menu_text = """
[bold white]Main Menu[/bold white]

  [cyan]1[/cyan] - Create New Project
       Create a new song or album project with session templates

  [cyan]2[/cyan] - Open Existing Project  
       Load and work on an existing project (coming soon)

  [cyan]3[/cyan] - View Tasks & Statistics
       See project history, statistics, and recent activity

  [cyan]q[/cyan] - Quit
       Exit the application

"""
    console.print(Panel(menu_text, title="Project Management System", border_style="white"))

def main():
    """Main program entry point"""
    console.print(Panel.fit("[bold white]Project Management System[/bold white]", 
                          subtitle="Audio Production Suite", style="white"))
    
    while True:
        try:
            show_menu()
            
            objective = Prompt.ask(
                "[bold]Select an option[/bold]",
                choices=["1", "2", "3", "q"],
                default="1"
            )
            
            if objective == "q":
                rprint("[green]Exited successfully![/green]")
                sys.exit(0)
            elif objective == "1":
                new_project_flow()
            elif objective == "2":
                open_project_flow()
            elif objective == "3":
                show_tasks()
                
            # Pause before showing menu again
            if objective != "q":
                Prompt.ask("\nPress Enter to continue", default="")
                
        except KeyboardInterrupt:
            rprint("\n[yellow]Exiting...[/yellow]")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            rprint(f"[red]An unexpected error occurred: {e}[/red]")

if __name__ == "__main__":
    main()