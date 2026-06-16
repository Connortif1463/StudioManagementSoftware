"""Tests for Features modules"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_features_tests():
    """Run all Features tests"""
    passed = 0
    failed = 0
    errors = 0
    
    # Create temporary test directory
    test_dir = Path(tempfile.mkdtemp())
    original_cwd = Path.cwd()
    os.chdir(test_dir)
    
    try:
        print("  Testing features.project_tracker...")
        from studio_manager.features.project_tracker import ProjectTracker, AlbumManager
        print("    ✅ Import successful")
        passed += 1
    except Exception as e:
        print(f"    ❌ Import failed: {e}")
        failed += 1
    
    try:
        print("  Testing ProjectTracker...")
        from studio_manager.features.project_tracker import ProjectTracker
        
        # Create a test project
        test_project = Path("test_artist/test_project")
        test_project.mkdir(parents=True)
        
        tracker = ProjectTracker(test_project)
        assert tracker.get_current_stage() == "production"
        
        # Test stage update
        tracker.update_stage("mixing", "Moving to mixing")
        assert tracker.get_current_stage() == "mixing"
        
        # Test priority calculation
        priority = tracker.calculate_priority()
        assert priority >= 0
        
        # Test release date
        tracker.set_release_date("2025-01-01")
        assert tracker.data.get("release_date") == "2025-01-01"
        
        # Test category
        tracker.set_project_category("demo")
        assert tracker.get_project_category() == "demo"
        
        print("    ✅ ProjectTracker works")
        passed += 1
    except Exception as e:
        print(f"    ❌ ProjectTracker failed: {e}")
        failed += 1
    
    try:
        print("  Testing AlbumManager...")
        from studio_manager.features.project_tracker import AlbumManager, ProjectTracker
        
        # Create album
        album_path = Path("test_artist/test_album")
        album_path.mkdir(parents=True)
        manager = AlbumManager(album_path)
        assert manager.data["name"] == "test_album"
        
        # Create songs with production folders (to be recognized as songs)
        for i in range(3):
            song_path = Path(f"test_artist/song_{i}")
            song_path.mkdir(parents=True)
            # Create production folder to mark as song project
            (song_path / "production").mkdir(exist_ok=True)
            tracker = ProjectTracker(song_path)
            tracker.save()
        
        # Test get_unassigned_songs
        unassigned = manager.get_unassigned_songs(Path.cwd())
        # Should find at least some songs
        if len(unassigned) > 0:
            # Test add_song
            manager.add_song(unassigned[0], 1)
            assert len(manager.data["songs"]) >= 1
        
        print("    ✅ AlbumManager works")
        passed += 1
    except Exception as e:
        print(f"    ❌ AlbumManager failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.session_memo...")
        from studio_manager.features.session_memo import SessionMemo, set_history
        from studio_manager.data.history import ProjectHistory
        
        history = ProjectHistory("test_history.json")
        set_history(history)
        
        # Create test project with session memos
        test_project = Path("test_artist/test_memo_project")
        test_project.mkdir(parents=True)
        
        memo = SessionMemo(test_project)
        assert memo.memos == {"sessions": []}
        
        print("    ✅ SessionMemo imports work")
        passed += 1
    except Exception as e:
        print(f"    ❌ SessionMemo failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.daw_integration...")
        from studio_manager.features.daw_integration import open_daw_project, get_daw_info
        
        # Test get_daw_info
        info = get_daw_info("A")
        assert info is not None
        assert info.get("name") == "Ableton"
        
        # Test without actually opening DAW
        info = get_daw_info("P")
        assert info.get("name") == "Pro Tools"
        
        print("    ✅ daw_integration works")
        passed += 1
    except Exception as e:
        print(f"    ❌ daw_integration failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.file_tree...")
        from studio_manager.features.file_tree import file_tree_flow
        print("    ✅ file_tree_flow imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ file_tree_flow failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.project_flows...")
        from studio_manager.features.project_flows import (
            new_project_flow, get_engineers, get_project_name,
            get_project_type, get_daw, get_project_category,
            manage_project_stage_flow
        )
        print("    ✅ project_flows imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ project_flows failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.tasks_flows...")
        from studio_manager.features.tasks_flows import (
            tasks_and_projects_flow, view_project_memos_flow,
            set_release_date_flow, view_finished_projects_flow,
            search_projects_flow, filter_by_category_flow
        )
        print("    ✅ tasks_flows imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ tasks_flows failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.browser_flows...")
        from studio_manager.features.browser_flows import (
            project_browser_flow, show_song_project_details,
            show_album_contents
        )
        print("    ✅ browser_flows imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ browser_flows failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.backup_flows...")
        from studio_manager.features.backup_flows import (
            backup_project_flow, global_backup_flow
        )
        print("    ✅ backup_flows imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ backup_flows failed: {e}")
        failed += 1
    
    try:
        print("  Testing features.album_flows...")
        from studio_manager.features.album_flows import (
            album_management_flow, add_songs_to_album_flow,
            manage_album_flow, view_unassigned_songs_flow
        )
        print("    ✅ album_flows imported successfully")
        passed += 1
    except Exception as e:
        print(f"    ❌ album_flows failed: {e}")
        failed += 1
    
    # Cleanup
    os.chdir(original_cwd)
    shutil.rmtree(test_dir, ignore_errors=True)
    
    return (passed, failed, errors)