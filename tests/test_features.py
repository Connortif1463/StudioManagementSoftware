# tests/test_features.py

import unittest
from pathlib import Path
import tempfile
import shutil
import os
import json
from datetime import datetime

class TestFeatures(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create a test project
        self.artist = "test_artist"
        self.project = "test_project"
        self.project_path = Path(self.test_dir) / "artists" / self.artist / self.project
        self.project_path.mkdir(parents=True, exist_ok=True)
        
        # Create tracker file
        self.tracker_file = self.project_path / ".project_tracker.json"
        self.tracker_data = {
            "project_name": self.project,
            "project_category": "studio_session",
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
        with open(self.tracker_file, 'w') as f:
            json.dump(self.tracker_data, f, indent=2)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_project_tracker_load(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        self.assertEqual(tracker.data["project_name"], self.project)
        self.assertEqual(tracker.get_current_stage(), "production")
    
    def test_project_tracker_save(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        tracker.data["project_name"] = "new_name"
        tracker.save()
        
        # Reload and verify
        new_tracker = ProjectTracker(self.project_path)
        self.assertEqual(new_tracker.data["project_name"], "new_name")
    
    def test_project_tracker_update_stage(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        tracker.update_stage("mixing", "Moving to mixing")
        
        self.assertEqual(tracker.get_current_stage(), "mixing")
        self.assertEqual(len(tracker.data["stage_history"]), 2)
    
    def test_project_tracker_priority(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        priority = tracker.calculate_priority()
        self.assertEqual(priority, 4)
        
        # Set release date and check priority changes
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=5)).isoformat()
        tracker.set_release_date(future_date)
        priority = tracker.calculate_priority()
        self.assertGreater(priority, 4)
    
    def test_album_manager(self):
        from studio_manager.features.project_tracker import AlbumManager
        
        album_path = Path(self.test_dir) / "test_album"
        album_path.mkdir(exist_ok=True)
        
        manager = AlbumManager(album_path)
        self.assertEqual(manager.data["name"], "test_album")
        self.assertEqual(manager.data["total_tracks"], 0)
    
    def test_session_memo(self):
        from studio_manager.features.session_memo import SessionMemo
        
        memo = SessionMemo(self.project_path)
        self.assertIsNotNone(memo.memos)
        self.assertEqual(memo.memos["sessions"], [])

def run_features_tests():
    """Run the features tests"""
    import unittest
    
    print("\n[5/6] Testing Features modules...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFeatures)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()