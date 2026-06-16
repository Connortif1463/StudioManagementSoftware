import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from rich.table import Table
from ..cli.display import console, print_header, print_success, print_info, print_warning, print_error

class ProjectTracker:
    """Tracks project stage, backups, and album organization"""
    
    STAGES = ["production", "mixing", "mastering", "finished"]
    
    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.tracker_file = self.project_path / ".project_tracker.json"
        self.data = self.load()
    
    def load(self) -> Dict:
        """Load project tracking data"""
        if self.tracker_file.exists():
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        return self.create_default()
    
    def create_default(self) -> Dict:
        """Create default tracking structure"""
        return {
            "project_name": self.project_path.name,
            "current_stage": "production",
            "stage_history": [
                {
                    "stage": "production",
                    "started": datetime.now().isoformat(),
                    "notes": "Project created"
                }
            ],
            "files": [],
            "album": None,
            "album_position": None,
            "backups": [],
            "last_modified": datetime.now().isoformat(),
            "release_date": None,
            "priority_score": 0
        }
    
    def save(self):
        """Save tracking data"""
        self.data["last_modified"] = datetime.now().isoformat()
        with open(self.tracker_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def update_stage(self, new_stage: str, notes: str = ""):
        """Update project stage"""
        if new_stage not in self.STAGES:
            print_error(f"Invalid stage. Choose from: {', '.join(self.STAGES)}")
            return False
        
        old_stage = self.data["current_stage"]
        self.data["current_stage"] = new_stage
        self.data["stage_history"].append({
            "stage": new_stage,
            "started": datetime.now().isoformat(),
            "notes": notes,
            "from_stage": old_stage
        })
        
        # Create stage folder if it doesn't exist
        stage_folder = self.project_path / new_stage
        stage_folder.mkdir(exist_ok=True)
        
        self.save()
        print_success(f"Project moved from {old_stage} to {new_stage}")
        return True
    
    def track_file(self, file_path: Path, file_type: str, stage: str):
        """Track a file in the project"""
        rel_path = str(file_path.relative_to(self.project_path))
        
        file_entry = {
            "path": rel_path,
            "type": file_type,
            "stage": stage,
            "created": datetime.now().isoformat(),
            "size": file_path.stat().st_size if file_path.exists() else 0
        }
        
        # Remove old entry if exists
        self.data["files"] = [f for f in self.data["files"] if f["path"] != rel_path]
        self.data["files"].append(file_entry)
        self.save()
    
    def get_current_stage(self) -> str:
        """Get current project stage"""
        return self.data["current_stage"]
    
    def get_stage_summary(self) -> Dict:
        """Get summary of files by stage"""
        summary = {stage: [] for stage in self.STAGES}
        for file in self.data["files"]:
            summary[file["stage"]].append(file["path"])
        return summary
    
    def calculate_priority(self) -> int:
        """Calculate priority score based on stage and release date"""
        # Stage weights: production=4, mixing=3, mastering=2, finished=0
        stage_weights = {
            "production": 4,
            "mixing": 3,
            "mastering": 2,
            "finished": 0
        }
        
        score = stage_weights.get(self.data["current_stage"], 0)
        
        # Add release date urgency (closer date = higher priority)
        if self.data.get("release_date"):
            try:
                release = datetime.fromisoformat(self.data["release_date"])
                days_until = (release - datetime.now()).days
                if days_until <= 7:
                    score += 3  # Very urgent
                elif days_until <= 30:
                    score += 2  # Urgent
                elif days_until <= 90:
                    score += 1  # Normal
            except:
                pass
        
        self.data["priority_score"] = score
        self.save()
        return score
    
    def set_release_date(self, release_date: str):
        """Set expected release date"""
        try:
            # Validate date format
            release = datetime.fromisoformat(release_date)
            self.data["release_date"] = release_date
            self.calculate_priority()
            self.save()
            print_success(f"Release date set to {release_date}")
            return True
        except ValueError:
            print_error("Invalid date format. Use YYYY-MM-DD")
            return False
    
    def create_backup(self, backup_path: Path = None, engineer: str = None) -> bool:
        """Create a backup of the project with metadata"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.project_path.parent / f"{self.project_path.name}_backup_{timestamp}"
        
        try:
            print_info(f"Creating backup at {backup_path}...")
            shutil.copytree(self.project_path, backup_path, 
                        ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.DS_Store', '*.backup'))
            
            # Calculate size
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file()) / (1024 * 1024)
            
            # Create metadata file
            metadata = {
                "backup_created": datetime.now().isoformat(),
                "backup_created_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "original_project_path": str(self.project_path),
                "project_name": self.data["project_name"],
                "current_stage": self.data["current_stage"],
                "engineer": engineer or "Unknown",
                "size_mb": total_size,
                "files_backed_up": len(list(backup_path.rglob('*'))),
                "stage_history": self.data["stage_history"][-3:],  # Last 3 stages
                "most_recent_version": max(
                    [f.stat().st_mtime for f in self.project_path.rglob('*') if f.is_file()],
                    default=0
                )
            }
            
            # Convert timestamp to readable date
            if metadata["most_recent_version"]:
                metadata["most_recent_version_pretty"] = datetime.fromtimestamp(
                    metadata["most_recent_version"]
                ).strftime("%Y-%m-%d %H:%M:%S")
            
            # Write metadata file
            metadata_file = backup_path / "BACKUP_INFO.txt"
            with open(metadata_file, 'w') as f:
                f.write(f"BACKUP INFORMATION\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Backup Created: {metadata['backup_created_pretty']}\n")
                f.write(f"Engineer: {metadata['engineer']}\n")
                f.write(f"Project: {metadata['project_name']}\n")
                f.write(f"Stage at Backup: {metadata['current_stage']}\n")
                f.write(f"Backup Size: {metadata['size_mb']:.2f} MB\n")
                f.write(f"Files Backed Up: {metadata['files_backed_up']}\n\n")
                
                if metadata.get("most_recent_version_pretty"):
                    f.write(f"Most Recent Project File: {metadata['most_recent_version_pretty']}\n\n")
                
                f.write(f"Stage History:\n")
                for stage in metadata['stage_history']:
                    f.write(f"  - {stage.get('stage')} (started: {stage.get('started', 'Unknown')[:19]})\n")
                
                f.write(f"\nOriginal Project Path: {metadata['original_project_path']}\n")
            
            backup_entry = {
                "path": str(backup_path),
                "created": datetime.now().isoformat(),
                "created_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "size_mb": total_size,
                "engineer": engineer or "Unknown",
                "metadata_file": str(metadata_file)
            }
            self.data["backups"].append(backup_entry)
            self.save()
            
            print_success(f"Backup created: {backup_path}")
            print_info(f"Size: {total_size:.2f} MB")
            print_info(f"Backup info saved to: {metadata_file}")
            return True
        except Exception as e:
            print_error(f"Backup failed: {e}")
            return False
    
    def list_backups(self):
        """List all backups for this project"""
        if not self.data["backups"]:
            print_info("No backups found for this project")
            return
        
        table = Table(title=f"Backups for {self.data['project_name']}", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Date", style="green")
        table.add_column("Path", style="dim")
        table.add_column("Size (MB)", style="yellow", width=10)
        
        for idx, backup in enumerate(reversed(self.data["backups"]), 1):
            date = datetime.fromisoformat(backup["created"]).strftime("%Y-%m-%d %H:%M:%S")
            table.add_row(str(idx), date, backup["path"], f"{backup['size_mb']:.2f}")
        
        console.print(table)


class AlbumManager:
    """Manages albums and song organization"""
    
    def __init__(self, album_path: Path):
        self.album_path = Path(album_path)
        self.album_file = self.album_path / ".album.json"
        self.data = self.load()
    
    def load(self) -> Dict:
        """Load album data"""
        if self.album_file.exists():
            with open(self.album_file, 'r') as f:
                return json.load(f)
        return {
            "name": self.album_path.name,
            "songs": [],
            "created": datetime.now().isoformat(),
            "total_tracks": 0,
            "status": "in_progress"
        }
    
    def save(self):
        """Save album data"""
        with open(self.album_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_song(self, song_path: Path, position: int = None):
        """Add a song to the album"""
        song_entry = {
            "path": str(song_path),
            "name": song_path.name,
            "artist": song_path.parent.name,
            "added": datetime.now().isoformat()
        }
        
        # Check if already in album
        existing = [s for s in self.data["songs"] if s["path"] == str(song_path)]
        if existing:
            print_warning(f"Song already in album")
            return False
        
        if position is None:
            position = len(self.data["songs"]) + 1
        
        self.data["songs"].insert(position - 1, song_entry)
        self.data["total_tracks"] = len(self.data["songs"])
        
        # Update the song's tracker to reference the album
        song_tracker = ProjectTracker(song_path)
        song_tracker.data["album"] = str(self.album_path)
        song_tracker.data["album_position"] = position
        song_tracker.save()
        
        self.save()
        print_success(f"Added {song_path.name} to album at position {position}")
        return True
    
    def remove_song(self, song_path: Path):
        """Remove a song from the album"""
        self.data["songs"] = [s for s in self.data["songs"] if s["path"] != str(song_path)]
        
        # Update positions of remaining songs
        for idx, song in enumerate(self.data["songs"], 1):
            song_tracker = ProjectTracker(Path(song["path"]))
            song_tracker.data["album_position"] = idx
            song_tracker.save()
        
        # Remove album reference from song
        song_tracker = ProjectTracker(song_path)
        song_tracker.data["album"] = None
        song_tracker.data["album_position"] = None
        song_tracker.save()
        
        self.data["total_tracks"] = len(self.data["songs"])
        self.save()
        print_success(f"Removed {song_path.name} from album")
    
    def reorder_song(self, song_path: Path, new_position: int):
        """Change a song's position in the album"""
        # Remove and re-insert
        self.remove_song(song_path)
        self.add_song(song_path, new_position)
    
    def list_songs(self):
        """List all songs in the album in order"""
        if not self.data["songs"]:
            print_info("No songs in this album yet")
            return
        
        table = Table(title=f"Album: {self.data['name']}", style="white")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Song Name", style="green")
        table.add_column("Artist", style="yellow")
        table.add_column("Added", style="dim")
        
        for idx, song in enumerate(self.data["songs"], 1):
            added = datetime.fromisoformat(song["added"]).strftime("%Y-%m-%d")
            table.add_row(str(idx), song["name"], song["artist"], added)
        
        console.print(table)
    
    def get_unassigned_songs(self, projects_root: Path) -> List[Path]:
        """Get songs that aren't assigned to any album"""
        unassigned = []
        artists_path = projects_root / "artists"
        
        if not artists_path.exists():
            return unassigned
        
        for artist_dir in artists_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir():
                        tracker = ProjectTracker(project_dir)
                        if tracker.data.get("album") is None and tracker.data.get("project_name"):
                            # Check if it's a song project (has DAW folders)
                            if any((project_dir / f).exists() for f in ["ableton", "protools", "logic"]):
                                unassigned.append(project_dir)
        
        return unassigned