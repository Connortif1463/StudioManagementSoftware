# tests/test_debug_names.py

import sys
from pathlib import Path

# Add project root to path - works whether run from root or tests folder
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root so paths work correctly
import os
os.chdir(project_root)

from studio_manager.cli.prompts import get_all_names_from_session_memos
from studio_manager.data.history import ProjectHistory


def debug_names():
    """Debug function to check what names are available for autocomplete"""
    print("=" * 60)
    print("DEBUG: Session Memo Names")
    print("=" * 60)
    print(f"Working directory: {Path.cwd()}")
    print()

    names = get_all_names_from_session_memos()
    print(f"Names found in session memos: {len(names)}")
    if names:
        print(f"Names: {names}")
    else:
        print("No names found in session memos")

    print("\n" + "=" * 60)
    print("DEBUG: History Data")
    print("=" * 60)

    history = ProjectHistory()

    print(f"Artists set: {history.data.get('artists', set())}")
    print(f"Engineers set: {history.data.get('engineers', set())}")
    print(f"Total projects: {len(history.data.get('projects', []))}")

    print("\nProjects:")
    projects = history.data.get('projects', [])
    if projects:
        for project in projects:
            print(f"  - {project.get('name')}")
            print(f"    Artist: {project.get('artist')}")
            print(f"    Engineers: {project.get('engineers', [])}")
            print()
    else:
        print("  No projects found")

    # Check if there are any session_memos.json files
    print("=" * 60)
    print("DEBUG: Session Memo Files")
    print("=" * 60)

    artists_path = Path.cwd() / "artists"
    if artists_path.exists():
        found_memos = False
        for artist_dir in artists_path.iterdir():
            if artist_dir.is_dir():
                for project_dir in artist_dir.iterdir():
                    if project_dir.is_dir():
                        memo_file = project_dir / "session_memos.json"
                        if memo_file.exists():
                            found_memos = True
                            print(f"Found: {memo_file}")
                            import json
                            with open(memo_file, 'r') as f:
                                data = json.load(f)
                                for session in data.get('sessions', []):
                                    for contributor in session.get('contributors', []):
                                        print(f"  Contributor: {contributor.get('name')} ({contributor.get('role')})")
        if not found_memos:
            print("No session_memos.json files found")
    else:
        print("No artists folder found")

    print("\n" + "=" * 60)
    print("DEBUG: History File")
    print("=" * 60)
    
    history_file = Path.cwd() / "project_history.json"
    if history_file.exists():
        print(f"History file exists: {history_file}")
        import json
        with open(history_file, 'r') as f:
            data = json.load(f)
            print(f"  Total projects in file: {len(data.get('projects', []))}")
            print(f"  Artists: {data.get('artists', [])}")
            print(f"  Engineers: {data.get('engineers', [])}")
    else:
        print(f"History file not found: {history_file}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    debug_names()