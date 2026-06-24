# tests/test_autocomplete.py

import unittest
import json
import tempfile
import shutil
import os
from pathlib import Path
from datetime import datetime

class TestAutocomplete(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with real data"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create artists directory
        (Path(self.test_dir) / "artists").mkdir(parents=True, exist_ok=True)
        
        # Create a test history with real data
        self.history_file = Path(self.test_dir) / "project_history.json"
        
        # Create history with engineers and artists
        self.history_data = {
            "projects": [
                {
                    "name": "test_song_1",
                    "type": "S",
                    "artist": "connor fischetti",
                    "engineers": ["connor fischetti", "devin pierpoint", "aldo bonito"],
                    "daw": "A",
                    "date_created": datetime.now().isoformat(),
                    "date_created_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": datetime.now().timestamp(),
                    "weekday": "Wednesday",
                    "week_number": 25,
                    "release_date": None,
                    "stage": "production"
                },
                {
                    "name": "test_song_2",
                    "type": "S",
                    "artist": "mkgee",
                    "engineers": ["devin pierpoint", "aldo bonito"],
                    "daw": "A",
                    "date_created": datetime.now().isoformat(),
                    "date_created_pretty": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "timestamp": datetime.now().timestamp(),
                    "weekday": "Wednesday",
                    "week_number": 25,
                    "release_date": None,
                    "stage": "production"
                }
            ],
            "artists": ["connor fischetti", "mkgee"],
            "engineers": ["connor fischetti", "devin pierpoint", "aldo bonito"],
            "session_stats": {
                "total_songs": 2,
                "total_albums": 0,
                "by_daw": {"A": 2},
                "by_artist": {"connor fischetti": 1, "mkgee": 1}
            }
        }
        
        with open(self.history_file, 'w') as f:
            json.dump(self.history_data, f, indent=2)
        
        # Create a project with session memos
        self.project_path = Path(self.test_dir) / "artists" / "connor fischetti" / "test_song_1"
        self.project_path.mkdir(parents=True, exist_ok=True)
        
        # Create session memos with contributors
        self.memo_data = {
            "sessions": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "session_files": [],
                    "contributors": [
                        {"name": "connor fischetti", "role": "Engineer"},
                        {"name": "devin pierpoint", "role": "Producer"},
                        {"name": "aldo bonito", "role": "Musician", "instrument": "Piano"}
                    ],
                    "tasks_completed": ["Recorded vocals", "Mixed track"],
                    "notes": "Great session",
                    "files_created": []
                }
            ]
        }
        
        memo_file = self.project_path / "session_memos.json"
        with open(memo_file, 'w') as f:
            json.dump(self.memo_data, f, indent=2)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_get_candidates_engineers(self):
        """Test that engineer candidates are properly gathered"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history
        
        # Load the test history
        history = ProjectHistory(str(self.history_file))
        
        # Get engineer candidates
        candidates = get_candidates_from_history("engineer", history)
        
        # Should have all engineers from history and projects
        expected = ["aldo bonito", "connor fischetti", "devin pierpoint"]
        self.assertEqual(sorted(candidates), sorted(expected))
    
    def test_get_candidates_artists(self):
        """Test that artist candidates are properly gathered"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history
        
        history = ProjectHistory(str(self.history_file))
        
        # Get artist candidates
        candidates = get_candidates_from_history("artist", history)
        
        # Should have all artists from history and projects
        expected = ["connor fischetti", "mkgee"]
        self.assertEqual(sorted(candidates), sorted(expected))
    
    def test_get_candidates_with_session_memos(self):
        """Test that session memo contributors are included"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history
        
        history = ProjectHistory(str(self.history_file))
        
        # Get engineer candidates (should include memo contributors)
        candidates = get_candidates_from_history("engineer", history)
        
        # Should include contributors from memos
        self.assertIn("aldo bonito", candidates)
        self.assertIn("devin pierpoint", candidates)
        self.assertIn("connor fischetti", candidates)
    
    def test_get_candidates_returns_set(self):
        """Test that candidates are returned as a sorted set (no duplicates)"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history
        
        history = ProjectHistory(str(self.history_file))
        
        candidates = get_candidates_from_history("engineer", history)
        
        # Should be a list
        self.assertIsInstance(candidates, list)
        # Should have no duplicates
        self.assertEqual(len(candidates), len(set(candidates)))
        # Should be sorted
        self.assertEqual(candidates, sorted(candidates))
    
    def test_get_candidates_history_matches_projects(self):
        """Test that history sets and project entries match"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history
        
        history = ProjectHistory(str(self.history_file))
        
        # Engineers from history set
        history_engineers = list(history.data.get("engineers", set()))
        
        # Engineers from projects
        project_engineers = []
        for project in history.data.get("projects", []):
            project_engineers.extend(project.get("engineers", []))
        
        # Should be consistent
        self.assertEqual(sorted(set(history_engineers)), sorted(set(project_engineers)))
    
    def test_get_candidates_engineer_autocomplete(self):
        """Test that engineers can be autocompleted properly"""
        from studio_manager.data.history import ProjectHistory
        from studio_manager.cli.prompts import get_candidates_from_history, get_input_with_completion
        
        history = ProjectHistory(str(self.history_file))
        
        candidates = get_candidates_from_history("engineer", history)
        
        # Test that common prefixes work
        self.assertIn("connor fischetti", candidates)
        self.assertIn("devin pierpoint", candidates)
        self.assertIn("aldo bonito", candidates)
        
        # Test that partial matches work
        partial_matches = [c for c in candidates if c.startswith("c")]
        self.assertTrue(len(partial_matches) > 0)


def run_autocomplete_tests():
    """Run the autocomplete tests"""
    import unittest
    
    print("\n[7/7] Testing Autocomplete...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAutocomplete)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_autocomplete_tests()