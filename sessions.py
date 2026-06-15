import os
import sys
import shutil
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from typing import Optional

console = Console()
logging.basicConfig(level=logging.INFO)

# Template paths
templates_base = Path.cwd() / "templates"
ableton_template_full_path = templates_base / "ableton templates" / "ableton template.als"
protools_template_full_path = templates_base / "protools templates" / "protools template.ptx"
logic_template_full_path = templates_base / "logic templates" / "logic template.logicx"

class SessionError(Exception):
    """Custom exception for session operations"""
    pass

def checkForSessionTemplates() -> bool:
    """Check for session templates with user-friendly error handling"""
    try:
        templates_exist = all([
            protools_template_full_path.is_file(),
            ableton_template_full_path.is_file(),
            logic_template_full_path.is_file()
        ])
        
        if templates_exist:
            console.print("[green]All session templates found[/green]")
            logging.info("Session templates verified")
            return True
        else:
            console.print("[yellow]Warning: Templates not found[/yellow]")
            return handle_missing_templates()
            
    except Exception as e:
        logging.error(f"Error checking templates: {e}")
        console.print(f"[red]Error checking templates: {e}[/red]")
        return False

def handle_missing_templates() -> bool:
    """Handle missing templates with user interaction"""
    from rich.prompt import Confirm
    
    if Confirm.ask("\n[yellow]Do you want to create template folders?[/yellow]"):
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[white]Creating templates...", total=None)
                
                templates_base.mkdir(exist_ok=True)
                
                # Create DAW template folders
                for daw_folder in ["protools templates", "ableton templates", "logic templates"]:
                    (templates_base / daw_folder).mkdir(exist_ok=True)
                
                # Create empty template files
                protools_template_full_path.touch(exist_ok=True)
                ableton_template_full_path.touch(exist_ok=True)
                logic_template_full_path.touch(exist_ok=True)
                
                progress.update(task, completed=True)
            
            console.print("[green]Templates created successfully[/green]")
            logging.info("New templates created")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create templates: {e}")
            console.print(f"[red]Failed to create templates: {e}[/red]")
            return False
    else:
        console.print("[red]Cannot proceed without templates. Please create template files and try again.[/red]")
        return False

def createNewSessionFromTemplate(name: str, artist: str, daw: str) -> bool:
    """Create a new session from template with proper error handling"""
    try:
        if not checkForSessionTemplates():
            raise SessionError("Templates not available")
        
        # Map DAW codes to folder names
        daw_map = {
            "A": ("ableton", ableton_template_full_path),
            "P": ("protools", protools_template_full_path),
            "L": ("logic", logic_template_full_path)
        }
        
        if daw not in daw_map:
            raise ValueError(f"Invalid DAW selection: {daw}")
        
        daw_folder, template_path = daw_map[daw]
        
        # Create session directory
        session_dir = Path.cwd() / "artists" / artist / name / daw_folder
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy template with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"[white]Copying {daw_folder} template...", total=None)
            destination = session_dir / template_path.name
            shutil.copy2(template_path, destination)
            progress.update(task, completed=True)
        
        console.print(f"[green]{daw_folder.capitalize()} template copied to: {destination}[/green]")
        logging.info(f"Session created: {name} for {artist} using {daw}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to create session: {e}")
        console.print(f"[red]Error creating session: {e}[/red]")
        return False