# run_tests.py

import sys
import os
from pathlib import Path

# Ensure the project root is in the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to the project root so templates can be found
os.chdir(project_root)

# Now import and run tests
from tests.test_all import run_all_tests

if __name__ == "__main__":
    print("=" * 60)
    print("STUDIO MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 60)
    print()
    print(f"Working directory: {Path.cwd()}")
    print(f"Templates directory: {Path.cwd() / 'templates'}")
    print()
    
    # Show which DAWs are enabled
    try:
        from tests.test_core import TEST_DAWS
        print("DAWs enabled for testing:")
        for daw, enabled in TEST_DAWS.items():
            status = "✅" if enabled else "❌ (skipped)"
            print(f"  {status} {daw}")
        print()
    except ImportError:
        pass
    
    run_all_tests()