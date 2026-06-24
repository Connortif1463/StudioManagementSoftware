# tests/test_integration.py

import unittest
from pathlib import Path
import tempfile
import shutil
import os

class TestIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create project structure
        (Path(self.test_dir) / "artists").mkdir(exist_ok=True)
        (Path(self.test_dir) / "templates").mkdir(exist_ok=True)
    
    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        """Test a full workflow: create project → create session → verify"""
        from studio_manager.core.project_manager import create_project
        from studio_manager.core.session_manager import create_session_from_template
        from studio_manager.utils.helpers import get_project_path
        
        # Create a test template
        templates_dir = Path(self.test_dir) / "templates" / "ableton templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        (templates_dir / "ableton template.als").touch()
        
        # Create a project
        result = create_project(
            name="integration_test",
            project_type="S",
            artist="test_artist",
            daw="A"
        )
        self.assertTrue(result)
        
        # Verify project exists
        project_path = get_project_path("test_artist", "integration_test")
        self.assertTrue(project_path.exists())
        
        # Verify session was created
        session_path = project_path / "production" / "ableton" / "integration_test_production_session.als"
        self.assertTrue(session_path.exists())

def run_integration_tests():
    """Run the integration tests"""
    import unittest
    
    print("\n[5/6] Testing Integration...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()