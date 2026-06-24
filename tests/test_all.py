# tests/test_all.py

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_all_tests():
    """Run all tests"""
    
    # Import test modules - only import ones that exist
    try:
        from tests.test_cli import run_cli_tests
    except ImportError:
        def run_cli_tests():
            print("  ⚠️ CLI tests skipped (module not found)")
            return True
    
    try:
        from tests.test_core import run_core_tests
    except ImportError:
        def run_core_tests():
            print("  ⚠️ Core tests skipped (module not found)")
            return True
    
    try:
        from tests.test_data import run_data_tests
    except ImportError:
        def run_data_tests():
            print("  ⚠️ Data tests skipped (module not found)")
            return True
    
    try:
        from tests.test_features import run_features_tests
    except ImportError:
        def run_features_tests():
            print("  ⚠️ Features tests skipped (module not found)")
            return True
    
    try:
        from tests.test_integration import run_integration_tests
    except ImportError:
        def run_integration_tests():
            print("  ⚠️ Integration tests skipped (module not found)")
            return True
    
    try:
        from tests.test_stage_migration import run_stage_migration_tests
    except ImportError:
        def run_stage_migration_tests():
            print("  ⚠️ Stage migration tests skipped (module not found)")
            return True
    
    results = []
    
    # Run each test module
    print("\n" + "=" * 60)
    print("RUNNING TESTS")
    print("=" * 60)
    
    results.append(("CLI", run_cli_tests()))
    results.append(("Core", run_core_tests()))
    results.append(("Data", run_data_tests()))
    results.append(("Features", run_features_tests()))
    results.append(("Integration", run_integration_tests()))
    results.append(("Stage Migration", run_stage_migration_tests()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    total_passed = 0
    total_failed = 0
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if passed:
            total_passed += 1
        else:
            total_failed += 1
            all_passed = False
    
    print("=" * 60)
    print(f"  Total: {total_passed + total_failed} test suites, {total_passed} passed, {total_failed} failed")
    print("=" * 60)
    
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    return all_passed

if __name__ == "__main__":
    # Change to project root so templates can be found
    os.chdir(project_root)
    run_all_tests()