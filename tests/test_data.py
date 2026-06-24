# tests/test_data.py

import unittest
import json
from pathlib import Path
import tempfile
import shutil
import os
from datetime import datetime

class TestData(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_history_creation(self):
        from studio_manager.data.history import ProjectHistory
        
        history = ProjectHistory("test_history.json")
        self.assertIsNotNone(history.data)
        self.assertEqual(history.data["projects"], [])
        self.assertEqual(history.data["session_stats"]["total_songs"], 0)
    
    def test_add_project(self):
        from studio_manager.data.history import ProjectHistory
        
        history = ProjectHistory("test_history.json")
        history.add_project(
            name="test_song",
            project_type="S",
            artist="test_artist",
            engineers=["engineer1"],
            daw="A"
        )
        
        self.assertEqual(len(history.data["projects"]), 1)
        self.assertEqual(history.data["projects"][0]["name"], "test_song")
        self.assertEqual(history.data["session_stats"]["total_songs"], 1)
    
    def test_history_save_load(self):
        from studio_manager.data.history import ProjectHistory
        
        # Create and save history
        history = ProjectHistory("test_history.json")
        history.add_project(
            name="test_song",
            project_type="S",
            artist="test_artist",
            engineers=["engineer1"],
            daw="A"
        )
        history.save()
        
        # Load new history from same file
        new_history = ProjectHistory("test_history.json")
        self.assertEqual(len(new_history.data["projects"]), 1)
        self.assertEqual(new_history.data["projects"][0]["name"], "test_song")
    
    def test_logger_creation(self):
        from studio_manager.data.logger import SessionLogger
        
        logger = SessionLogger("test_logs")
        self.assertTrue(logger.log_dir.exists())
    
    def test_logger_log_action(self):
        from studio_manager.data.logger import SessionLogger
        
        logger = SessionLogger("test_logs")
        logger.start_session()
        logger.log_action("TEST_ACTION", "Test description", {"key": "value"})
        
        self.assertEqual(len(logger.actions), 2)  # SESSION_START + TEST_ACTION
        self.assertEqual(logger.actions[1]["action_type"], "TEST_ACTION")
    
    def test_logger_save(self):
        from studio_manager.data.logger import SessionLogger
        
        logger = SessionLogger("test_logs")
        logger.start_session()
        logger.log_action("TEST_ACTION", "Test description")
        logger.save_session()
        
        # Check that a log file was created
        log_files = list(logger.log_dir.glob("session_*.json"))
        self.assertTrue(len(log_files) >= 1)

def run_data_tests():
    """Run the data tests"""
    import unittest
    
    print("\n[4/6] Testing Data modules...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestData)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()