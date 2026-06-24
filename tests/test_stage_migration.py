# tests/test_stage_migration.py

import unittest
from pathlib import Path
import tempfile
import shutil
import os
import json
from datetime import datetime

class TestStageMigration(unittest.TestCase):
    
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
    
    def test_stage_creation(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        self.assertEqual(tracker.get_current_stage(), "production")
    
    def test_stage_update(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        tracker.update_stage("mixing", "Moving to mixing")
        
        self.assertEqual(tracker.get_current_stage(), "mixing")
        self.assertEqual(len(tracker.data["stage_history"]), 2)
    
    def test_stage_folder_creation(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        tracker.update_stage("mixing", "Moving to mixing")
        
        mixing_folder = self.project_path / "mixing"
        self.assertTrue(mixing_folder.exists())
    
    def test_priority_calculation(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        priority = tracker.calculate_priority()
        self.assertEqual(priority, 4)  # production = 4
    
    def test_stage_flow(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        # Import STAGES from project_tracker to use the same list
        from studio_manager.features.project_tracker import ProjectTracker as PT
        
        tracker = ProjectTracker(self.project_path)
        
        # Get the actual stages from the STAGES list
        stages = PT.STAGES
        
        # Move through stages (skip the first one since we're already there)
        for stage in stages[1:]:
            tracker.update_stage(stage, f"Moved to {stage}")
            self.assertEqual(tracker.get_current_stage(), stage)
            
            # Check that the stage folder was created
            stage_folder = self.project_path / stage
            self.assertTrue(stage_folder.exists(), f"Folder '{stage}' was not created")
    
    def test_invalid_stage(self):
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        
        # Try to set an invalid stage - should not change
        result = tracker.update_stage("invalid_stage", "This shouldn't work")
        self.assertFalse(result)
        self.assertEqual(tracker.get_current_stage(), "production")
    
    def test_all_stages_exist(self):
        """Test that all stages from STAGES list have folders created"""
        from studio_manager.features.project_tracker import ProjectTracker
        
        tracker = ProjectTracker(self.project_path)
        stages = ["production", "mixing", "mastering", "finished"]
        
        # Create all stage folders
        for stage in stages:
            tracker.update_stage(stage, f"Moving to {stage}")
        
        # Verify all folders exist
        for stage in stages:
            stage_folder = self.project_path / stage
            self.assertTrue(stage_folder.exists(), f"Folder '{stage}' does not exist")

def run_stage_migration_tests():
    """Run the stage migration tests"""
    import unittest
    
    print("\n[6/6] Testing Stage Migration...")
    
    # Show which stages are expected
    from studio_manager.features.project_tracker import ProjectTracker
    print(f"  Expected stages: {ProjectTracker.STAGES}")
    print()
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestStageMigration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()