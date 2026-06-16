#!/usr/bin/env python3
"""
Test Runner for Studio Management System
Run this file from the root directory to test all features
"""

import sys
import os
from pathlib import Path

# Add the current directory to path so we can import studio_manager and tests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run all tests
if __name__ == "__main__":
    print("=" * 60)
    print("STUDIO MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 60)
    print("\nRunning all tests...\n")
    
    # Import and run each test module
    from tests.test_cli import run_cli_tests
    from tests.test_core import run_core_tests
    from tests.test_features import run_features_tests
    from tests.test_data import run_data_tests
    from tests.test_integration import run_integration_tests
    
    results = []
    
    print("\n[1/5] Testing CLI modules...")
    results.append(("CLI", run_cli_tests()))
    
    print("\n[2/5] Testing Core modules...")
    results.append(("Core", run_core_tests()))
    
    print("\n[3/5] Testing Features modules...")
    results.append(("Features", run_features_tests()))
    
    print("\n[4/5] Testing Data modules...")
    results.append(("Data", run_data_tests()))
    
    print("\n[5/5] Running Integration tests...")
    results.append(("Integration", run_integration_tests()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for module_name, (passed, failed, errors) in results:
        total_tests += passed + failed + errors
        total_passed += passed
        total_failed += failed + errors
        status = "✅" if failed == 0 and errors == 0 else "❌"
        print(f"{status} {module_name}: {passed} passed, {failed} failed, {errors} errors")
    
    print("-" * 60)
    print(f"Total: {total_passed} passed, {total_failed} failed out of {total_tests} tests")
    print("=" * 60)