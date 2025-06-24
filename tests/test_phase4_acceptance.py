#!/usr/bin/env python3
"""
Phase 4 acceptance test: save config → close app → reopen → load snapshot → verify all fields match
"""

import tempfile
from pathlib import Path

from pandoc_ui.app.profile_repository import ProfileRepository
from pandoc_ui.infra.config_manager import ConfigManager
from pandoc_ui.infra.settings_store import Language, SettingsStore


def test_phase4_acceptance():
    """Test the complete Phase 4 acceptance criteria."""
    print("🧪 Testing Phase 4 acceptance criteria...")

    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Initialize config manager with temp directory
        config_manager = ConfigManager(base_dir=temp_path)
        config_manager.ensure_directories()

        # Initialize repositories
        profile_repo = ProfileRepository(profiles_dir=config_manager.get_profiles_dir())
        settings_store = SettingsStore(settings_file=config_manager.get_settings_file())

        print(f"📁 Using temp config directory: {temp_path}")

        # Step 1: Create and save configuration profile
        print("\n📝 Step 1: Creating configuration profile...")

        ui_state = {
            "input_file": "/test/documents/input.md",
            "output_file": "/test/output/result.html",
            "output_format": "html",
            "is_batch_mode": False,
            "extensions": ".md,.txt,.rst",
            "scan_recursive": True,
            "max_files": 500,
            "html_standalone": True,
            "max_concurrent_jobs": 6,
        }

        profile_name = "Test Configuration"
        profile = profile_repo.create_profile_from_ui_state(profile_name, ui_state)

        success = profile_repo.save_profile(profile)
        assert success, "Failed to save profile"
        print(f"✅ Profile '{profile_name}' saved successfully")

        # Step 2: Save application settings
        print("\n⚙️  Step 2: Saving application settings...")

        settings = settings_store.load_settings()
        settings.language = Language.CHINESE
        settings.theme = "dark"
        settings.window_width = 1200
        settings.window_height = 900
        settings.max_concurrent_jobs = 8
        settings.default_output_format = "pdf"

        success = settings_store.save_settings(settings)
        assert success, "Failed to save settings"
        print("✅ Application settings saved successfully")

        # Step 3: Simulate app close by clearing in-memory state
        print("\n🔄 Step 3: Simulating app restart (clearing memory state)...")

        # Clear repositories (simulating app close)
        del profile_repo
        del settings_store
        print("✅ App 'closed' - memory state cleared")

        # Step 4: Simulate app reopen by recreating repositories
        print("\n🚀 Step 4: Simulating app reopen...")

        # Recreate repositories (simulating app restart)
        new_profile_repo = ProfileRepository(profiles_dir=config_manager.get_profiles_dir())
        new_settings_store = SettingsStore(settings_file=config_manager.get_settings_file())
        print("✅ App 'reopened' - repositories recreated")

        # Step 5: Load and verify profile
        print("\n📋 Step 5: Loading and verifying saved profile...")

        # Check profile exists
        assert new_profile_repo.profile_exists(profile_name), f"Profile '{profile_name}' not found"

        # Load profile
        loaded_profile = new_profile_repo.load_profile(profile_name)
        assert loaded_profile is not None, "Failed to load profile"

        # Verify all profile fields match
        assert loaded_profile.name == profile_name
        assert loaded_profile.input_file == ui_state["input_file"]
        assert loaded_profile.output_file == ui_state["output_file"]
        assert loaded_profile.output_format == ui_state["output_format"]
        assert loaded_profile.is_batch_mode == ui_state["is_batch_mode"]
        assert loaded_profile.extensions == ui_state["extensions"]
        assert loaded_profile.scan_recursive == ui_state["scan_recursive"]
        assert loaded_profile.max_files == ui_state["max_files"]
        assert loaded_profile.html_standalone == ui_state["html_standalone"]
        assert loaded_profile.max_concurrent_jobs == ui_state["max_concurrent_jobs"]

        print("✅ All profile fields match original configuration")

        # Step 6: Load and verify settings
        print("\n🔧 Step 6: Loading and verifying application settings...")

        loaded_settings = new_settings_store.load_settings()

        # Verify all settings match
        assert loaded_settings.language == Language.CHINESE
        assert loaded_settings.theme == "dark"
        assert loaded_settings.window_width == 1200
        assert loaded_settings.window_height == 900
        assert loaded_settings.max_concurrent_jobs == 8
        assert loaded_settings.default_output_format == "pdf"

        print("✅ All application settings match original configuration")

        # Step 7: Test profile listing and management
        print("\n📋 Step 7: Testing profile management functionality...")

        profiles = new_profile_repo.list_profiles()
        assert len(profiles) == 1, f"Expected 1 profile, found {len(profiles)}"
        assert profiles[0].name == profile_name

        profile_count = new_profile_repo.get_profile_count()
        assert profile_count == 1, f"Expected profile count 1, got {profile_count}"

        print("✅ Profile management functionality verified")

        # Step 8: Test creating additional profiles
        print("\n📝 Step 8: Testing multiple profile management...")

        # Create second profile
        ui_state_2 = {
            "input_file": "/another/input.md",
            "output_format": "pdf",
            "is_batch_mode": True,
            "input_folder": "/batch/input/",
            "output_folder": "/batch/output/",
            "extensions": ".md",
            "max_concurrent_jobs": 4,
        }

        profile_2 = new_profile_repo.create_profile_from_ui_state("Batch Profile", ui_state_2)
        success = new_profile_repo.save_profile(profile_2)
        assert success, "Failed to save second profile"

        # Verify we now have 2 profiles
        profiles = new_profile_repo.list_profiles()
        assert len(profiles) == 2, f"Expected 2 profiles, found {len(profiles)}"

        profile_names = {p.name for p in profiles}
        assert "Test Configuration" in profile_names
        assert "Batch Profile" in profile_names

        print("✅ Multiple profile management verified")

        # Step 9: Test settings persistence across multiple operations
        print("\n🔄 Step 9: Testing settings persistence...")

        # Create temporary files for recent files test
        temp_file1 = temp_path / "recent_file1.md"
        temp_file2 = temp_path / "recent_file2.md"
        temp_dir1 = temp_path / "recent_output1"

        temp_file1.write_text("test content")
        temp_file2.write_text("test content")
        temp_dir1.mkdir()

        # Add recent files (using actual existing files)
        new_settings_store.add_recent_input_file(str(temp_file1))
        new_settings_store.add_recent_input_file(str(temp_file2))
        new_settings_store.add_recent_output_dir(str(temp_dir1))

        # Update a setting
        new_settings_store.update_setting("ui_update_interval_ms", 200)

        # Create new store instance to test persistence
        third_settings_store = SettingsStore(settings_file=config_manager.get_settings_file())
        reloaded_settings = third_settings_store.load_settings()

        # Verify persistence
        assert str(temp_file1) in reloaded_settings.recent_input_files
        assert str(temp_file2) in reloaded_settings.recent_input_files
        assert str(temp_dir1) in reloaded_settings.recent_output_dirs
        assert reloaded_settings.ui_update_interval_ms == 200

        print("✅ Settings persistence verified")

        print("\n🎉 Phase 4 acceptance test completed successfully!")
        print("\n📊 Summary:")
        print(f"   ✅ Configuration profiles: {len(profiles)} saved and loaded")
        print("   ✅ Application settings: All fields persistent")
        print(f"   ✅ Directory structure: {config_manager.base_dir}")
        print(f"   ✅ Profile files: {profile_count} in {config_manager.profiles_dir}")
        print(f"   ✅ Settings file: {config_manager.get_settings_file()}")

        assert True  # All tests passed


if __name__ == "__main__":
    test_phase4_acceptance()
