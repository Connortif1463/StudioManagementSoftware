# studio_manager/data/history.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from collections import defaultdict
from difflib import get_close_matches


class ProjectHistory:
    """Manages project history ledger"""
    
    def __init__(self, history_file: str = "project_history.json"):
        self.history_file = Path(history_file)
        self.data = self.load_history()
        
    def load_history(self) -> Dict:
        """Load history from JSON file"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    data["artists"] = set(data.get("artists", []))
                    data["engineers"] = set(data.get("engineers", []))
                    return data
            except json.JSONDecodeError:
                return self.create_empty_history()
        return self.create_empty_history()
    
    def create_empty_history(self) -> Dict:
        """Create empty history structure"""
        return {
            "projects": [],
            "artists": set(),
            "engineers": set(),
            "session_stats": {
                "total_songs": 0,
                "total_albums": 0,
                "by_daw": defaultdict(int),
                "by_artist": defaultdict(int)
            }
        }
    
    def save(self):
        """Save history to file"""
        save_data = {
            "projects": self.data["projects"],
            "artists": list(self.data["artists"]),
            "engineers": list(self.data["engineers"]),
            "session_stats": {
                "total_songs": self.data["session_stats"]["total_songs"],
                "total_albums": self.data["session_stats"]["total_albums"],
                "by_daw": dict(self.data["session_stats"]["by_daw"]),
                "by_artist": dict(self.data["session_stats"]["by_artist"])
            }
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(save_data, f, indent=2)
    
    def add_project(self, name: str, project_type: str, artist: str, engineers: List[str], daw: str = "", release_date: str = None):
        """Add a new project to history"""
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
            "weekday": now.strftime("%A"),
            "week_number": now.isocalendar()[1],
            "release_date": release_date,
            "stage": "production"
        }
        
        self.data["projects"].append(project_entry)
        self.data["artists"].add(artist)
        
        # IMPORTANT: Add engineers to the engineers set for autocomplete
        if engineers:
            self.data["engineers"].update(engineers)
        
        if project_type == "S":
            self.data["session_stats"]["total_songs"] += 1
            if daw:
                # Safely increment DAW count
                self.data["session_stats"]["by_daw"][daw] = self.data["session_stats"]["by_daw"].get(daw, 0) + 1
        else:
            self.data["session_stats"]["total_albums"] += 1
        
        # Safely increment artist count
        self.data["session_stats"]["by_artist"][artist] = self.data["session_stats"]["by_artist"].get(artist, 0) + 1
        self.save()
    
    def get_completions(self, field: str, query: str) -> List[str]:
        """Get tab completions based on partial input"""
        candidates = list(self.data.get(f"{field}s", []))
        if not query:
            return sorted(candidates)[:10]
        
        query_lower = query.lower()
        matches = [c for c in candidates if c.lower().startswith(query_lower)]
        partial_matches = [c for c in candidates if query_lower in c.lower() and c not in matches]
        
        return (sorted(matches) + sorted(partial_matches))[:10]
    
    def get_suggestions(self, field: str, query: str) -> List[str]:
        """Get autocorrect suggestions"""
        candidates = list(self.data.get(f"{field}s", []))
        if not query or not candidates:
            return []
        
        matches = get_close_matches(query.lower(), [c.lower() for c in candidates], n=3, cutoff=0.4)
        
        suggestions = []
        for match in matches:
            for candidate in candidates:
                if candidate.lower() == match:
                    suggestions.append(candidate)
                    break
        return suggestions
    
    def get_stats(self) -> dict:
        """Get formatted statistics - scans filesystem for accurate album counts"""
        # Get stats from history
        total_songs = self.data["session_stats"]["total_songs"]
        unique_artists = len(self.data["artists"])
        unique_engineers = len(self.data["engineers"])
        
        # Scan filesystem for albums to get accurate count
        albums_path = Path.cwd() / "artists"
        fs_albums = 0
        
        if albums_path.exists():
            for artist_dir in albums_path.iterdir():
                if artist_dir.is_dir():
                    for project_dir in artist_dir.iterdir():
                        if project_dir.is_dir() and (project_dir / ".album.json").exists():
                            fs_albums += 1
        
        # Use the filesystem count for albums (more accurate)
        total_albums = fs_albums
        
        return {
            "total_songs": total_songs,
            "total_albums": total_albums,
            "unique_artists": unique_artists,
            "unique_engineers": unique_engineers,
            "by_daw": self.data["session_stats"]["by_daw"],
            "by_artist": self.data["session_stats"]["by_artist"]
        }