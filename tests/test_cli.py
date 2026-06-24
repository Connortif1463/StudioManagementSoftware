# tests/test_cli.py

import unittest
from pathlib import Path
import tempfile
import shutil
import os

class TestCLI(unittest.TestCase):
    
    def test_display_imports(self):
        """Test that display module can be imported"""
        from studio_manager.cli import display
        self.assertTrue(hasattr(display, "console"))
        self.assertTrue(hasattr(display, "print_success"))
        self.assertTrue(hasattr(display, "print_error"))
        self.assertTrue(hasattr(display, "print_warning"))
    
    def test_menu_imports(self):
        """Test that menu module can be imported"""
        from studio_manager.cli import menu
        self.assertTrue(hasattr(menu, "show_main_menu"))
    
    def test_prompts_imports(self):
        """Test that prompts module can be imported"""
        from studio_manager.cli import prompts
        self.assertTrue(hasattr(prompts, "get_choice"))
        self.assertTrue(hasattr(prompts, "get_confirmation"))
        self.assertTrue(hasattr(prompts, "get_text_input"))

def run_cli_tests():
    """Run the CLI tests"""
    import unittest
    
    print("\n[1/6] Testing CLI modules...")
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCLI)
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    return result.wasSuccessful()