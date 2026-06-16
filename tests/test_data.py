"""Tests for Data modules (history, logger)"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_data_tests():
    """Run all Data tests"""
    passed = 0
    failed = 0
    errors = 0
    
    # Create temporary test directory
    test_dir = Path(tempfile.mkdtemp())
    original_cwd = Path.cwd()
    os.chdir(test_dir)
    
    try:
        print("  Testing data.history...")
        from studio_manager.data.history import ProjectHistory
        history = ProjectHistory("test_history.json")
        print("    ✅ Import successful")
        passed += 1
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        failed += 1
    
    try:
        print("  Testing ProjectHistory.add_project...")
        from studio_manager.data.history import ProjectHistory
        history = ProjectHistory("test_history.json")
        history.add_project("test_song", "S", "test_artist", ["engineer1"], "A")
        assert len(history.data["projects"]) == 1
        assert history.data["projects"][0]["name"] == "test_song"
        assert "test_artist" in history.data["artists"]
        assert "engineer1" in history.data["engineers"]
        print("    ✅ add_project works")
        passed += 1
    except Exception as e:
        print(f"    ❌ add_project failed: {e}")
        failed += 1
    
    try:
        print("  Testing ProjectHistory.save/load...")
        from studio_manager.data.history import ProjectHistory
        # Create a fresh history file
        history = ProjectHistory("test_history_save.json")
        history.add_project("test_song2", "S", "test_artist2", ["engineer2"], "Pro Tools")
        history.save()
        
        # Load new instance
        history2 = ProjectHistory("test_history_save.json")
        # Check that we have at least one project
        assert len(history2.data["projects"]) >= 1
        # Check that the project data was saved correctly
        assert history2.data["projects"][0]["name"] == "test_song2"
        print("    ✅ save/load works")
        passed += 1
    except Exception as e:
        print(f"    ❌ save/load failed: {e}")
        failed += 1
    
    try:
        print("  Testing ProjectHistory.get_completions...")
        from studio_manager.data.history import ProjectHistory
        history = ProjectHistory("test_history_completions.json")
        history.add_project("test_song3", "S", "test_artist3", ["engineer3"], "Logic")
        history.add_project("another_song", "S", "another_artist", ["engineer4"], "Ableton")
        
        # Test completions for artists
        completions = history.get_completions("artist", "test")
        assert len(completions) >= 1
        assert "test_artist3" in completions
        
        # Test completions for engineers
        completions = history.get_completions("engineer", "engineer")
        assert len(completions) >= 1
        print("    ✅ get_completions works")
        passed += 1
    except Exception as e:
        print(f"    ❌ get_completions failed: {e}")
        failed += 1
    
    try:
        print("  Testing ProjectHistory.get_stats...")
        from studio_manager.data.history import ProjectHistory
        history = ProjectHistory("test_history_stats.json")
        history.add_project("test_song4", "S", "test_artist4", ["engineer4"], "Ableton")
        history.add_project("test_song5", "S", "test_artist4", ["engineer5"], "Pro Tools")
        
        stats = history.get_stats()
        assert "total_songs" in stats
        assert stats["total_songs"] >= 2
        assert "unique_artists" in stats
        assert stats["unique_artists"] >= 1
        print("    ✅ get_stats works")
        passed += 1
    except Exception as e:
        print(f"    ❌ get_stats failed: {e}")
        failed += 1
    
    try:
        print("  Testing data.logger...")
        from studio_manager.data.logger import SessionLogger
        logger = SessionLogger("test_logs")
        logger.start_session()
        logger.log_action("TEST_ACTION", "Test action description", {"test": "data"})
        logger.save_session()
        
        # Check if log file was created
        log_files = list(Path("test_logs").glob("session_*.json"))
        assert len(log_files) > 0
        print("    ✅ SessionLogger works")
        passed += 1
    except Exception as e:
        print(f"    ❌ SessionLogger failed: {e}")
        failed += 1
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return (passed, failed, errors)