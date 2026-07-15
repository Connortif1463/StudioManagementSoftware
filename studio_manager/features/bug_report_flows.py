# studio_manager/features/bug_report_flows.py

"""Bug report flow for capturing and saving bug reports"""
import json
import sys
import platform
from pathlib import Path
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from ..cli.display import console, clear_screen, print_success, print_error, print_warning, print_info, print_separator
from ..cli.prompts import get_text_input, get_choice, get_confirmation, get_raw_input


BUG_REPORTS_DIR = Path.cwd() / "bug_reports"


def ensure_bug_reports_dir():
    """Ensure the bug reports directory exists"""
    BUG_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_system_info() -> dict:
    """Gather system information for the bug report"""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor()
    }


def get_available_options() -> dict:
    """Get available options for bug report fields"""
    return {
        "severity": ["Critical", "High", "Medium", "Low", "Suggestion"],
        "area": [
            "Project Creation",
            "Project Opening",
            "Session Memo",
            "DAW Integration",
            "File System",
            "Album Management",
            "Backup System",
            "Search/Filter",
            "UI/Display",
            "Template System",
            "Task Management",
            "Other"
        ],
        "status": ["Open", "In Progress", "Fixed", "Closed", "Needs Info"]
    }


def write_bug_report(bug_data: dict) -> Path:
    """Write a bug report to file"""
    ensure_bug_reports_dir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"bug_report_{timestamp}.json"
    filepath = BUG_REPORTS_DIR / filename
    
    # Add metadata
    bug_data["report_id"] = f"BUG-{timestamp}"
    bug_data["created_at"] = datetime.now().isoformat()
    bug_data["created_at_pretty"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bug_data["status"] = bug_data.get("status", "Open")
    
    with open(filepath, 'w') as f:
        json.dump(bug_data, f, indent=2)
    
    return filepath


def list_bug_reports() -> list:
    """List all bug reports"""
    ensure_bug_reports_dir()
    reports = []
    
    for file in BUG_REPORTS_DIR.glob("bug_report_*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                data["_file"] = str(file)
                reports.append(data)
        except:
            pass
    
    return sorted(reports, key=lambda x: x.get("created_at", ""), reverse=True)


def view_bug_report(report: dict):
    """Display a single bug report"""
    clear_screen()
    
    console.print(Panel.fit(
        f"[bold white]Bug Report: {report.get('report_id', 'Unknown')}[/bold white]",
        style="white"
    ))
    
    console.print(f"\n[bold]Title:[/bold] [yellow]{report.get('title', 'No title')}[/yellow]")
    console.print(f"[bold]Severity:[/bold] {report.get('severity', 'Unknown')}")
    console.print(f"[bold]Area:[/bold] {report.get('area', 'Unknown')}")
    console.print(f"[bold]Status:[/bold] {report.get('status', 'Open')}")
    console.print(f"[bold]Created:[/bold] {report.get('created_at_pretty', 'Unknown')}")
    
    print_separator()
    console.print("[bold]Description:[/bold]")
    console.print(f"  {report.get('description', 'No description')}")
    
    if report.get("steps_to_reproduce"):
        print_separator()
        console.print("[bold]Steps to Reproduce:[/bold]")
        for i, step in enumerate(report.get("steps_to_reproduce", []), 1):
            console.print(f"  {i}. {step}")
    
    if report.get("expected_behavior"):
        print_separator()
        console.print("[bold]Expected Behavior:[/bold]")
        console.print(f"  {report['expected_behavior']}")
    
    if report.get("actual_behavior"):
        print_separator()
        console.print("[bold]Actual Behavior:[/bold]")
        console.print(f"  {report['actual_behavior']}")
    
    if report.get("environment"):
        print_separator()
        console.print("[bold]Environment:[/bold]")
        for key, value in report.get("environment", {}).items():
            console.print(f"  {key}: {value}")
    
    if report.get("notes"):
        print_separator()
        console.print("[bold]Additional Notes:[/bold]")
        console.print(f"  {report['notes']}")
    
    print_separator()
    input("\nPress Enter to continue...")


def bug_report_flow():
    """Main bug report flow"""
    clear_screen()
    console.print(Panel.fit("[bold white]Bug Report System[/bold white]", style="white"))
    
    while True:
        console.print("\n[bold]Options:[/bold]")
        console.print("  [cyan]1[/cyan] - Submit a new bug report")
        console.print("  [cyan]2[/cyan] - View existing bug reports")
        console.print("  [cyan]3[/cyan] - View bug report details")
        console.print("  [cyan]b[/cyan] - Go back")
        
        choice = get_raw_input("\nSelect option: ").strip().lower()
        
        if choice == 'b':
            return
        elif choice == "1":
            write_bug_report_flow()
        elif choice == "2":
            view_bug_reports_list_flow()
        elif choice == "3":
            view_bug_report_details_flow()
        else:
            print_error("Invalid option")
            input("\nPress Enter to continue...")


def write_bug_report_flow():
    """Flow for writing a new bug report"""
    clear_screen()
    console.print(Panel.fit("[bold white]Submit Bug Report[/bold white]", style="white"))
    print_info("\nHelp us improve by reporting bugs and issues.")
    
    try:
        # Get title
        title = get_text_input("\nBug title (brief description)", allow_empty=False)
        if title == "##BACKTRACK##":
            return
        
        # Get severity
        severity_options = ["Critical", "High", "Medium", "Low", "Suggestion"]
        console.print("\n[bold]Severity:[/bold]")
        for i, opt in enumerate(severity_options, 1):
            console.print(f"  [cyan]{i}[/cyan] - {opt}")
        severity_choice = get_raw_input("\nSelect severity (1-5): ").strip()
        
        severity_map = {"1": "Critical", "2": "High", "3": "Medium", "4": "Low", "5": "Suggestion"}
        severity = severity_map.get(severity_choice, "Medium")
        
        # Get area
        area_options = [
            "Project Creation", "Project Opening", "Session Memo", "DAW Integration",
            "File System", "Album Management", "Backup System", "Search/Filter",
            "UI/Display", "Template System", "Task Management", "Other"
        ]
        console.print("\n[bold]Area:[/bold]")
        for i, opt in enumerate(area_options, 1):
            console.print(f"  [cyan]{i}[/cyan] - {opt}")
        area_choice = get_raw_input("\nSelect area (1-12): ").strip()
        
        try:
            idx = int(area_choice) - 1
            area = area_options[idx] if 0 <= idx < len(area_options) else "Other"
        except:
            area = "Other"
        
        # Get description
        console.print("\n[bold]Description:[/bold]")
        print_info("Describe the bug in detail. Press Enter twice to finish.")
        description_lines = []
        while True:
            line = get_raw_input("> ").strip()
            if not line and description_lines:
                break
            if line:
                description_lines.append(line)
        description = "\n".join(description_lines) if description_lines else "No description provided"
        
        # Get steps to reproduce
        console.print("\n[bold]Steps to Reproduce:[/bold]")
        print_info("Enter each step. Press Enter twice to finish.")
        steps = []
        step_num = 1
        while True:
            step = get_raw_input(f"Step {step_num}: ").strip()
            if not step and steps:
                break
            if step:
                steps.append(step)
                step_num += 1
        
        # Get expected behavior
        console.print("\n[bold]Expected Behavior:[/bold]")
        print_info("What should have happened?")
        expected = get_text_input("Expected", allow_empty=True)
        if expected == "##BACKTRACK##":
            return
        
        # Get actual behavior
        console.print("\n[bold]Actual Behavior:[/bold]")
        print_info("What actually happened?")
        actual = get_text_input("Actual", allow_empty=True)
        if actual == "##BACKTRACK##":
            return
        
        # Get additional notes
        console.print("\n[bold]Additional Notes:[/bold]")
        notes = get_text_input("Notes (optional)", allow_empty=True)
        if notes == "##BACKTRACK##":
            return
        
        # Gather system info
        system_info = get_system_info()
        
        # Build bug data
        bug_data = {
            "title": title,
            "severity": severity,
            "area": area,
            "description": description,
            "steps_to_reproduce": steps,
            "expected_behavior": expected,
            "actual_behavior": actual,
            "notes": notes,
            "environment": system_info
        }
        
        # Show summary
        clear_screen()
        console.print(Panel.fit("[bold white]Bug Report Summary[/bold white]", style="white"))
        console.print(f"\n[bold]Title:[/bold] [yellow]{title}[/yellow]")
        console.print(f"[bold]Severity:[/bold] {severity}")
        console.print(f"[bold]Area:[/bold] {area}")
        console.print(f"[bold]Description:[/bold] {description[:100]}{'...' if len(description) > 100 else ''}")
        
        if get_confirmation("\nSubmit this bug report?"):
            filepath = write_bug_report(bug_data)
            print_success(f"\nBug report saved to: {filepath}")
            input("\nPress Enter to continue...")
        else:
            print_warning("Bug report cancelled")
            input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        print_warning("\nCancelled")
        input("\nPress Enter to continue...")


def view_bug_reports_list_flow():
    """View a list of all bug reports"""
    clear_screen()
    console.print(Panel.fit("[bold white]Bug Reports List[/bold white]", style="white"))
    
    reports = list_bug_reports()
    
    if not reports:
        print_info("\nNo bug reports found")
        input("\nPress Enter to continue...")
        return
    
    table = Table(title=f"Bug Reports ({len(reports)})", style="white")
    table.add_column("#", style="cyan", width=4)
    table.add_column("ID", style="yellow")
    table.add_column("Title", style="green")
    table.add_column("Severity", style="red")
    table.add_column("Status", style="magenta")
    table.add_column("Created", style="dim")
    
    for idx, report in enumerate(reports, 1):
        severity_colors = {
            "Critical": "red",
            "High": "orange1",
            "Medium": "yellow",
            "Low": "green",
            "Suggestion": "blue"
        }
        severity_color = severity_colors.get(report.get("severity", "Medium"), "white")
        
        status_colors = {
            "Open": "red",
            "In Progress": "yellow",
            "Fixed": "green",
            "Closed": "dim",
            "Needs Info": "cyan"
        }
        status_color = status_colors.get(report.get("status", "Open"), "white")
        
        table.add_row(
            str(idx),
            report.get("report_id", "Unknown"),
            report.get("title", "No title")[:40],
            f"[{severity_color}]{report.get('severity', 'Unknown')}[/{severity_color}]",
            f"[{status_color}]{report.get('status', 'Open')}[/{status_color}]",
            report.get("created_at_pretty", "Unknown")[:16]
        )
    
    console.print(table)
    input("\nPress Enter to continue...")


def view_bug_report_details_flow():
    """View details of a specific bug report"""
    clear_screen()
    console.print(Panel.fit("[bold white]View Bug Report Details[/bold white]", style="white"))
    
    reports = list_bug_reports()
    
    if not reports:
        print_info("\nNo bug reports found")
        input("\nPress Enter to continue...")
        return
    
    # Show list of reports
    for i, report in enumerate(reports, 1):
        console.print(f"  [cyan]{i}[/cyan] - {report.get('report_id', 'Unknown')}: {report.get('title', 'No title')[:50]}")
    
    choice = get_raw_input("\nSelect report number (or 'b' to go back): ").strip()
    
    if choice.lower() == 'b':
        return
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(reports):
            view_bug_report(reports[idx])
        else:
            print_error("Invalid selection")
            input("\nPress Enter to continue...")
    else:
        print_error("Please enter a valid number")
        input("\nPress Enter to continue...")


def update_bug_report_status(report_id: str, new_status: str) -> bool:
    """Update the status of a bug report"""
    ensure_bug_reports_dir()
    
    for file in BUG_REPORTS_DIR.glob(f"*{report_id}*.json"):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
            
            data["status"] = new_status
            data["updated_at"] = datetime.now().isoformat()
            data["updated_at_pretty"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except:
            pass
    
    return False