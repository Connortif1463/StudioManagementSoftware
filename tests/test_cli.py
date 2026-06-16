"""Tests for CLI modules (display, menu, prompts)"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_cli_tests():
    """Run all CLI tests"""
    passed = 0
    failed = 0
    errors = 0
    
    try:
        print("  Testing cli.display...")
        from studio_manager.cli.display import (
            clear_screen, console, print_success, print_error, 
            print_warning, print_info, print_dim, print_separator,
            print_menu, print_header, show_recent_projects_table,
            show_statistics_table
        )
        print("    ✅ Import successful")
        passed += 1
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        failed += 1
    
    try:
        print("  Testing cli.menu...")
        from studio_manager.cli.menu import show_main_menu, show_file_tree_options
        print("    ✅ Import successful")
        passed += 1
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        failed += 1
    
    try:
        print("  Testing cli.prompts...")
        from studio_manager.cli.prompts import (
            get_choice, get_confirmation, get_text_input,
            get_number_input, get_input_with_completion
        )
        print("    ✅ Import successful")
        passed += 1
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        failed += 1
    
    try:
        print("  Testing print functions...")
        # Just test they exist and don't crash
        print_success("Test success message")
        print_error("Test error message")
        print_warning("Test warning message")
        print_info("Test info message")
        print_dim("Test dim message")
        print_separator()
        print("    ✅ Print functions work")
        passed += 1
    except Exception as e:
        print(f"    ❌ Print functions failed: {e}")
        failed += 1
    
    return (passed, failed, errors)