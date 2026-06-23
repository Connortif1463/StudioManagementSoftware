"""Project creation and management flows"""
import traceback
from pathlib import Path
from rich.panel import Panel
from ..cli.display import clear_screen, console, print_success, print_error, print_warning, print_info
from ..cli.prompts import get_confirmation, get_text_input, get_choice, get_number_input, get_input_with_completion
from ..core.project_manager import create_project
from .project_tracker import ProjectTracker
from ..utils.helpers import get_project_path
from ..utils.constants import DAW_MAP
from .open_project import ProjectOpener


def get_engineers(history):
    """Get engineer names with validation and backtracking"""
    engineers = []
    
    while True:
        num_input = get_number_input("\nEnter the number of engineers on this session", min_val=1, max_val=20)
        
        if num_input == "##BACKTRACK##":
            return "##BACKTRACK##"
        
        for i in range(num_input):
            while True:
                # Use get_input_with_completion for engineer names (with tab completion from history)
                engineer = get_input_with_completion(
                    f"\nEnter the name of engineer #{i+1}", 
                    "engineer",
                    history, 
                    allow_backtrack=True
                )
                
                if engineer == "##BACKTRACK##":
                    if i > 0:
                        print_warning("Going back to previous engineer...")
                        engineers.pop() if engineers else None
                        continue
                    else:
                        print_warning("Going back to number of engineers...")
                        engineers = []
                        break
                else:
                    engineers.append(engineer)
                    break
            
            if engineer == "##BACKTRACK##" and not engineers:
                break
        
        if engineers:
            return engineers


def get_project_name():
    """Get project name with backtracking"""
    while True:
        name = get_text_input("\nEnter the name of your project", allow_empty=False, allow_backtrack=True)
        if name == "##BACKTRACK##":
            return "##BACKTRACK##"
        return name


def get_project_type():
    """Get and validate project type with backtracking"""
    return get_choice("\nEnter S for Song, or A for Album", ["S", "A"])


def get_daw():
    """Get and validate DAW selection with backtracking"""
    return get_choice("\nEnter the DAW you're using (P for Pro Tools, A for Ableton, L for Logic)", ["P", "A", "L"])


def get_project_category():
    """Get project category from user"""
    console.print("\n[bold]Project Category:[/bold]")
    console.print("  [cyan]1[/cyan] - Studio Session (serious music production)")
    console.print("  [cyan]2[/cyan] - Live Recording")
    console.print("  [cyan]3[/cyan] - Demo")
    console.print("  [cyan]4[/cyan] - Equipment Test")
    console.print("  [cyan]5[/cyan] - Fun / Experiment")
    console.print("  [cyan]b[/cyan] - Go back")
    
    category_choice = input("\nSelect category: ").strip().lower()
    category_map = {
        "1": "studio_session",
        "2": "live_recording",
        "3": "demo",
        "4": "test",
        "5": "fun"
    }
    if category_choice == 'b':
        return "##BACKTRACK##"
    return category_map.get(category_choice, "studio_session")


def manage_project_stage_flow(project_path: Path):
    """Manage the stage of a project"""
    clear_screen()
    tracker = ProjectTracker(project_path)
    
    console.print(Panel.fit(f"[bold white]Project Stage: {tracker.get_current_stage().upper()}[/bold white]", style="white"))
    
    console.print("\n[bold]Stages:[/bold]")
    for i, stage in enumerate(ProjectTracker.STAGES, 1):
        current = " [current]" if stage == tracker.get_current_stage() else ""
        console.print(f"  [cyan]{i}[/cyan] - {stage}{current}")
    
    choice = input("\nSelect new stage (or 'b' to go back): ").strip()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(ProjectTracker.STAGES):
            new_stage = ProjectTracker.STAGES[idx]
            if new_stage != tracker.get_current_stage():
                notes = input("Any notes about this stage change? (press Enter to skip): ").strip()
                tracker.update_stage(new_stage, notes)
                input("\nPress Enter to continue...")


def new_project_flow(history):
    """Handle new project creation flow with backtracking support"""
    clear_screen()
    console.print(Panel.fit("[bold white]Create New Project[/bold white]", style="white"))
    print_info("\nAt any prompt, enter 'b' or 'backtrack' to go back to the previous step")
    
    try:
        engineers = get_engineers(history)
        if engineers == "##BACKTRACK##":
            return
        
        name = get_project_name()
        if name == "##BACKTRACK##":
            return
        
        project_type = get_project_type()
        if project_type == "##BACKTRACK##":
            return
        
        # Use get_input_with_completion for artist names (with tab completion from history)
        artist = get_input_with_completion("\nEnter the name of the artist", "artist", history, allow_backtrack=True)
        if artist == "##BACKTRACK##":
            return
        
        daw = ""
        if project_type == "S":
            daw = get_daw()
            if daw == "##BACKTRACK##":
                return
        
        project_category = get_project_category()
        if project_category == "##BACKTRACK##":
            return
        
        clear_screen()
        console.print(Panel.fit("[bold white]Project Summary[/bold white]", style="white"))
        console.print(f"\n  Name: [green]{name}[/green]")
        console.print(f"  Type: [green]{'Song' if project_type == 'S' else 'Album'}[/green]")
        console.print(f"  Artist: [green]{artist}[/green]")
        console.print(f"  Engineers: [green]{', '.join(engineers)}[/green]")
        console.print(f"  Category: [green]{project_category.replace('_', ' ').title()}[/green]")
        if daw:
            daw_name = DAW_MAP.get(daw, daw)
            console.print(f"  DAW: [green]{daw_name}[/green]")
        
        confirm = get_confirmation("\nCreate this project?")
        if confirm:
            success = create_project(name, project_type, artist, daw)
            
            if success:
                history.add_project(name, project_type, artist, engineers, daw)
                console.print(f"\n[green]Project '{name}' created successfully![/green]")
                
                if project_type == "S":
                    project_path = get_project_path(artist, name)
                    tracker = ProjectTracker(project_path)
                    tracker.set_project_category(project_category)
                    if tracker.get_current_stage() == "production" and not tracker.data.get("stage_history"):
                        tracker.data["current_stage"] = "production"
                        tracker.save()
                    
                    # Ask if user wants to open the project
                    if get_confirmation("\nOpen the project now?"):
                        opener = ProjectOpener()
                        opener.open_project_interactive(project_path, history)
                
                input("\nPress Enter to continue...")
            else:
                print_error("\nFailed to create project. Check the logs for details.")
                input("\nPress Enter to continue...")
        else:
            print_warning("\nProject creation cancelled")
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        input("\nPress Enter to continue...")
    except Exception as e:
        print_error(f"\nAn unexpected error occurred: {e}")
        traceback.print_exc()
        input("\nPress Enter to continue...")