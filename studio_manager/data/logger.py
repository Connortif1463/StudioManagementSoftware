import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class SessionLogger:
    """Logs all session activities"""
    
    def __init__(self, log_dir: str = "session_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.session_start = None
        self.actions = []
        
    def start_session(self):
        """Start a new session log"""
        self.session_start = datetime.now()
        self.actions = []
        self.log_action("SESSION_START", "Application started")
    
    def log_action(self, action_type: str, description: str, details: Dict = None):
        """Log an action"""
        self.actions.append({
            "timestamp": datetime.now().isoformat(),
            "timestamp_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action_type": action_type,
            "description": description,
            "details": details or {}
        })
    
    def save_session(self):
        """Save the session log to file"""
        if not self.session_start:
            return
        
        session_id = f"session_{self.session_start.strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            "session_id": session_id,
            "session_start": self.session_start.isoformat(),
            "session_start_pretty": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "session_end": datetime.now().isoformat(),
            "session_end_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": (datetime.now() - self.session_start).total_seconds(),
            "actions": self.actions
        }
        
        log_file = self.log_dir / f"{session_id}.json"
        with open(log_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        # Update summary
        summary_file = self.log_dir / "session_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                summary = json.load(f)
        else:
            summary = {"sessions": []}
        
        summary["sessions"].append({
            "session_id": session_id,
            "start_time": session_data["session_start_pretty"],
            "duration": session_data["duration_seconds"],
            "action_count": len(self.actions)
        })
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)