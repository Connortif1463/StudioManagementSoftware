# studio_manager/features/daw_setup.py

from pathlib import Path
from rich.panel import Panel
from ..cli.display import console, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_text_input, get_confirmation
from ..utils.daw_discovery import DAWDiscovery
from ..utils.config import UserConfig
from ..utils.constants import DAW_MAP

def run_daw_setup_wizard(config: UserConfig, skip_header: bool = False) -> bool:
    """Run the DAW setup wizard for first-time users"""
    from ..cli.display import clear_screen
    
    if not skip_header:
        clear_screen()
        console.print(Panel.fit("[bold white]DAW Setup Wizard[/bold white]", style="white"))
        print_info("\nWelcome! Let's set up your Digital Audio Workstation (DAW) paths.")
        print_info("This will allow the program to open your sessions directly.")
    
    os_type = DAWDiscovery.get_os()
    print_info(f"\nDetected operating system: [cyan]{os_type.title()}[/cyan]")
    
    if os_type not in ["windows", "mac"]:
        print_warning("Your operating system is not officially supported.")
        return False
    
    # Map DAW codes to names
    daws_to_setup = [
        ("A", "Ableton Live"),
        ("P", "Pro Tools"),
    ]
    
    # Add Logic only on Mac
    if os_type == "mac":
        daws_to_setup.append(("L", "Logic Pro"))
    
    success = True
    
    for daw_code, daw_name in daws_to_setup:
        print_separator()
        
        # Try to auto-discover
        found_paths = DAWDiscovery.find_daw_paths(daw_name)
        
        if found_paths:
            print_success(f"Found {daw_name} at: {found_paths[0]}")
            use_found = get_confirmation(f"Use this path for {daw_name}?")
            
            if use_found:
                config.set_daw_path(daw_code, found_paths[0])
                print_success(f"✓ {daw_name} configured successfully!")
                continue
            else:
                print_info(f"Let's manually find your {daw_name} installation.")
        else:
            print_warning(f"Could not automatically find {daw_name}.")
            print_info(f"Please locate your {daw_name} executable.")
        
        # Manual path entry with helpful instructions
        path = get_daw_path_manually(daw_name, os_type)
        
        if path and path != "##BACKTRACK##":
            # Validate the path
            if DAWDiscovery.validate_path(path):
                config.set_daw_path(daw_code, path)
                print_success(f"✓ {daw_name} configured successfully!")
            else:
                print_error(f"Invalid path: {path}")
                print_info("You can set this up later using the 'Configure DAWs' option in the menu.")
                success = False
        else:
            print_warning(f"Skipping {daw_name} setup for now.")
            print_info("You can set this up later using the 'Configure DAWs' option in the menu.")
    
    if success and not skip_header:
        print_success("\n✓ DAW setup complete!")
    elif not success:
        print_warning("\nSome DAWs were not configured. You can set them up later.")
    
    if not skip_header:
        input("\nPress Enter to continue...")
    return success

def get_daw_path_manually(daw_name: str, os_type: str) -> str:
    """Guide user through manual DAW path entry"""
    
    print_info(f"\nFinding {daw_name} on {os_type.title()}")
    
    if os_type == "windows":
        print_info("\n[bold]Instructions for Windows:[/bold]")
        print_info(f"1. Find your {daw_name} shortcut or .exe file")
        print_info("2. Right-click it and select 'Open file location'")
        print_info("3. Copy the full path from the address bar")
        print_info("4. If you see the .exe file, right-click it and select 'Copy as path'")
        print_info(f"\n[dim]Example: C:\\Program Files\\Ableton\\Live 12\\Program\\Ableton Live 12.exe[/dim]")
    
    elif os_type == "mac":
        print_info("\n[bold]Instructions for Mac:[/bold]")
        print_info("1. Open Finder")
        print_info("2. Navigate to the Applications folder")
        print_info(f"3. Find {daw_name}.app")
        print_info("4. Right-click it and select 'Get Info'")
        print_info("5. Copy the path from 'Where:' section")
        print_info(f"\n[dim]Example: /Applications/Ableton Live 12 Suite.app[/dim]")
    
    print_info("\n[bold yellow]Tip:[/bold yellow] You can also just type the path if you know it.")
    print_info("[dim]Enter 'b' to skip this DAW for now.[/dim]")
    
    while True:
        path = get_text_input(f"\nEnter the full path to {daw_name}", 
                             allow_empty=False, 
                             allow_backtrack=True)
        
        if path == "##BACKTRACK##":
            return path
        
        # Check if path exists
        if Path(path).exists():
            return path
        else:
            print_error(f"Path not found: {path}")
            retry = get_confirmation("Try again?")
            if not retry:
                return "##BACKTRACK##"