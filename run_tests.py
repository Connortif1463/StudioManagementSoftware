#!/usr/bin/env python3
"""
Test Runner for Studio Management System
Run this file from the root directory to test all features
"""

import sys
import os
from pathlib import Path

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("STUDIO MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 60)
    print("\nRunning all tests...\n")
    
    from tests.test_cli import run_cli_tests
    from tests.test_core import run_core_tests
    from tests.test_features import run_features_tests
    from tests.test_data import run_data_tests
    from tests.test_integration import run_integration_tests
    from tests.test_stage_migration import run_stage_migration_tests
    
    results = []
    
    print("\n[1/6] Testing CLI modules...")
    results.append(("CLI", run_cli_tests()))
    
    print("\n[2/6] Testing Core modules...")
    results.append(("Core", run_core_tests()))
    
    print("\n[3/6] Testing Features modules...")
    results.append(("Features", run_features_tests()))
    
    print("\n[4/6] Testing Data modules...")
    results.append(("Data", run_data_tests()))
    
    print("\n[5/6] Testing Integration...")
    results.append(("Integration", run_integration_tests()))
    
    print("\n[6/6] Testing Stage Migration...")
    results.append(("Stage Migration", run_stage_migration_tests()))
    
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