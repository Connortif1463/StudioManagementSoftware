# tests/test_utils.py

import unittest
from pathlib import Path
import tempfile
import shutil
import os

class TestUtils(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_sanitize_filename(self):
        from studio_manager.utils.helpers import sanitize_filename
        
        # Test with invalid characters
        result = sanitize_filename("test<>:\"/\\|?*file")
        self.assertEqual(result, "test________file")
        
        # Test with valid filename
        result = sanitize_filename("valid_filename")
        self.assertEqual(result, "valid_filename")
    
    def test_format_file_size(self):
        from studio_manager.utils.helpers import format_file_size
        
        # Test bytes
        self.assertEqual(format_file_size(500), "500.0 B")
        
        # Test KB
        self.assertEqual(format_file_size(1024), "1.0 KB")
        
        # Test MB
        self.assertEqual(format_file_size(1048576), "1.0 MB")
    
    def test_get_project_path(self):
        from studio_manager.utils.helpers import get_project_path
        
        # Create test artist and project
        artist = "test_artist"
        project = "test_project"
        
        result = get_project_path(artist, project)
        self.assertEqual(result.name, "test_project")
        self.assertEqual(result.parent.name, "test_artist")
    
    def test_list_all_projects(self):
        from studio_manager.utils.helpers import list_all_projects
        
        # Create test projects
        artists_dir = Path.cwd() / "artists"
        artists_dir.mkdir(exist_ok=True)
        
        artist1_dir = artists_dir / "artist1"
        artist1_dir.mkdir(exist_ok=True)
        project1 = artist1_dir / "project1"
        project1.mkdir(exist_ok=True)
        
        artist2_dir = artists_dir / "artist2"
        artist2_dir.mkdir(exist_ok=True)
        project2 = artist2_dir / "project2"
        project2.mkdir(exist_ok=True)
        
        # Also create a backup folder (should be excluded)
        project_backup = artist2_dir / "project2_backup_20240624"
        project_backup.mkdir(exist_ok=True)
        
        projects = list_all_projects()
        
        # Should only find the non-backup projects
        self.assertEqual(len(projects), 2)
        
        project_names = [p["project"] for p in projects]
        self.assertIn("project1", project_names)
        self.assertIn("project2", project_names)

def run_utils_tests():
    """Run the utils tests and print results"""
    import unittest
    
    print("\n[3/6] Testing Utils modules...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestUtils)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    run_utils_tests()