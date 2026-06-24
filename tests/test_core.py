# tests/test_core.py

import os
import shutil
import tempfile
from pathlib import Path
from unittest import TestCase, skip

# ============================================================
# CONFIGURE WHICH DAWS TO TEST
# ============================================================
# Set to True for DAWs you want to test, False to skip
# This makes it easy to test only the DAWs you have installed
TEST_DAWS = {
    "Ableton": True,     
    "Pro Tools": False,   
    "Logic": False,       
}
# ============================================================

class TestCore(TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create the artists folder
        (Path(self.test_dir) / "artists").mkdir(parents=True, exist_ok=True)
        
        # Create templates folder with test templates
        self.templates_dir = Path(self.test_dir) / "templates"
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Create template files for each DAW that's being tested
        if TEST_DAWS.get("Ableton", False):
            ableton_template_dir = self.templates_dir / "ableton templates"
            ableton_template_dir.mkdir(exist_ok=True)
            self.ableton_template = ableton_template_dir / "ableton template.als"
            self.ableton_template.touch()
        
        if TEST_DAWS.get("Pro Tools", False):
            protools_template_dir = self.templates_dir / "protools templates"
            protools_template_dir.mkdir(exist_ok=True)
            self.protools_template = protools_template_dir / "protools template.ptx"
            self.protools_template.touch()
        
        if TEST_DAWS.get("Logic", False):
            logic_template_dir = self.templates_dir / "logic templates"
            logic_template_dir.mkdir(exist_ok=True)
            self.logic_template = logic_template_dir / "logic template.logicx"
            self.logic_template.touch()
        
        # Create a test artist directory
        self.artist_name = "test_artist"
        self.project_name = "test_song"
        self.artist_dir = Path(self.test_dir) / "artists" / self.artist_name
        self.artist_dir.mkdir(parents=True, exist_ok=True)
        self.project_dir = self.artist_dir / self.project_name
        self.project_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_project_folders(self):
        """Test creating project folders"""
        from studio_manager.core.file_system import create_project_folders
        
        result = create_project_folders("test_artist", "test_project")
        self.assertIsInstance(result, Path)
        self.assertTrue(result.exists())
        self.assertEqual(result.parent.name, "test_artist")
        self.assertEqual(result.name, "test_project")
    
    def test_create_project_subfolders(self):
        """Test creating project subfolders"""
        from studio_manager.core.file_system import create_project_subfolders
        
        project_dir = Path(self.test_dir) / "artists" / "test_artist" / "test_subfolders"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        create_project_subfolders(project_dir)
        
        for folder in ["production", "mix", "master"]:
            folder_path = project_dir / folder
            self.assertTrue(folder_path.exists())
            self.assertTrue(folder_path.is_dir())
            
            readme = folder_path / "README.txt"
            self.assertTrue(readme.exists())
    
    def test_create_project_manager(self):
        """Test project manager creation"""
        from studio_manager.core.project_manager import create_project
        
        # Only test if Ableton is enabled
        if not TEST_DAWS.get("Ableton", False):
            self.skipTest("Ableton not enabled for testing")
        
        result = create_project(
            name="test_song",
            project_type="S",
            artist="test_artist",
            daw="A"
        )
        self.assertTrue(result)
    
    def test_create_session_from_template(self):
        """Test session creation from template"""
        from studio_manager.core.session_manager import create_session_from_template
        
        # Only test if Ableton is enabled
        if not TEST_DAWS.get("Ableton", False):
            self.skipTest("Ableton not enabled for testing")
        
        result = create_session_from_template(
            name="test_song",
            artist="test_artist",
            daw="A",
            stage="production"
        )
        self.assertTrue(result)
        
        # Check that the session file was created
        session_path = Path(self.test_dir) / "artists" / "test_artist" / "test_song" / "production" / "ableton" / "test_song_production_session.als"
        self.assertTrue(session_path.exists())
    
    def test_get_template_path(self):
        """Test getting template paths for different DAWs"""
        from studio_manager.core.session_manager import get_template_path
        
        # Test Ableton
        if TEST_DAWS.get("Ableton", False):
            path = get_template_path("A")
            self.assertIsNotNone(path)
            self.assertEqual(path.name, "ableton template.als")
        
        # Test Pro Tools
        if TEST_DAWS.get("Pro Tools", False):
            path = get_template_path("P")
            self.assertIsNotNone(path)
            self.assertEqual(path.name, "protools template.ptx")
        
        # Test Logic
        if TEST_DAWS.get("Logic", False):
            path = get_template_path("L")
            self.assertIsNotNone(path)
            self.assertEqual(path.name, "logic template.logicx")


def run_core_tests():
    """Run the core tests and print results"""
    import unittest
    
    print("\n[2/6] Testing Core modules...")
    
    # Show which DAWs are being tested
    print("  DAWs enabled for testing:")
    for daw, enabled in TEST_DAWS.items():
        status = "✅" if enabled else "❌ (skipped)"
        print(f"    {status} {daw}")
    print()
    
    # Run the tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCore)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()