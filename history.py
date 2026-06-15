import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict, Counter
from difflib import get_close_matches
from rich.console import Console
from rich.table import Table

console = Console()
logging.basicConfig(level=logging.INFO)

class ProjectHistory:
    """Manages project history ledger with autocorrect functionality"""
    
    def __init__(self, history_file: str = "project_history.json"):
        self.history_file = Path(history_file)
        self.data = self.load_history()
        
    def load_history(self) -> Dict:
        """Load history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.warning("History file corrupted, creating new one")
                return self.create_empty_history()
        return self.create_empty_history()
    
    def create_empty_history(self) -> Dict:
        """Create empty history structure"""
        return {
            "projects": [],
            "artists": set(),
            "engineers": set(),
            "daws_used": [],
            "session_stats": {
                "total_songs": 0,
                "total_albums": 0,
                "by_daw": defaultdict(int),
                "by_artist": defaultdict(int)
            }
        }
    
    def save_history(self):
        """Save history to JSON file"""
        try:
            # Convert sets to lists for JSON serialization
            save_data = self.data.copy()
            save_data["artists"] = list(save_data["artists"])
            save_data["engineers"] = list(save_data["engineers"])
            save_data["session_stats"]["by_daw"] = dict(save_data["session_stats"]["by_daw"])
            save_data["session_stats"]["by_artist"] = dict(save_data["session_stats"]["by_artist"])
            
            with open(self.history_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            logging.info("History saved successfully")
        except Exception as e:
            logging.error(f"Failed to save history: {e}")
    
    def add_project(self, name: str, project_type: str, artist: str, engineers: List[str], daw: str = ""):
        """Add a new project to the ledger with full datetime tracking"""
        now = datetime.now()
        project_entry = {
            "name": name,
            "type": project_type,
            "artist": artist,
            "engineers": engineers,
            "daw": daw if daw else "N/A",
            "date_created": now.isoformat(),
            "date_created_pretty": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": now.timestamp(),
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
            "week_number": now.isocalendar()[1]
        }
        
        self.data["projects"].append(project_entry)
        self.data["artists"].add(artist)
        self.data["engineers"].update(engineers)
        
        if project_type == "S":
            self.data["session_stats"]["total_songs"] += 1
            if daw:
                self.data["session_stats"]["by_daw"][daw] += 1
        else:
            self.data["session_stats"]["total_albums"] += 1
        
        self.data["session_stats"]["by_artist"][artist] += 1
        self.save_history()
    
    def get_suggestions(self, field: str, query: str, max_suggestions: int = 3) -> List[str]:
        """Get autocorrect suggestions based on history"""
        if field == "artist":
            candidates = list(self.data["artists"])
        elif field == "engineer":
            candidates = list(self.data["engineers"])
        else:
            return []
        
        if not query or not candidates:
            return []
        
        # Get close matches
        matches = get_close_matches(query.lower(), [c.lower() for c in candidates], 
                                   n=max_suggestions, cutoff=0.6)
        
        # Return original case versions
        suggestions = []
        for match in matches:
            for candidate in candidates:
                if candidate.lower() == match:
                    suggestions.append(candidate)
                    break
        
        return suggestions
    
    def show_statistics(self):
        """Display project statistics"""
        table = Table(title="Project Statistics", style="white")
        table.add_column("Metric", style="bold")
        table.add_column("Value", style="white")
        
        table.add_row("Total Songs", str(self.data["session_stats"]["total_songs"]))
        table.add_row("Total Albums", str(self.data["session_stats"]["total_albums"]))
        table.add_row("Unique Artists", str(len(self.data["artists"])))
        table.add_row("Unique Engineers", str(len(self.data["engineers"])))
        
        console.print(table)
        
        if self.data["session_stats"]["by_daw"]:
            daw_table = Table(title="DAW Usage", style="white")
            daw_table.add_column("DAW", style="bold")
            daw_table.add_column("Projects", style="white")
            
            for daw, count in self.data["session_stats"]["by_daw"].items():
                daw_name = {"A": "Ableton", "P": "Pro Tools", "L": "Logic"}.get(daw, daw)
                daw_table.add_row(daw_name, str(count))
            
            console.print(daw_table)
    
    def get_recent_projects(self, limit: int = 5) -> List[Dict]:
        """Get recent projects from history sorted by timestamp"""
        sorted_projects = sorted(self.data["projects"], 
                                key=lambda x: x.get("timestamp", 0), 
                                reverse=True)
        return sorted_projects[:limit]
    
    def export_full_ledger(self, output_file: str = "full_ledger.json"):
        """Export complete ledger with all details"""
        try:
            with open(output_file, 'w') as f:
                json.dump(self.data, f, indent=2, default=str)
            console.print(f"[green]Full ledger exported to {output_file}[/green]")
        except Exception as e:
            logging.error(f"Failed to export ledger: {e}")
            console.print(f"[red]Failed to export ledger: {e}[/red]")