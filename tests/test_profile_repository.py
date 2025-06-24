"""
Test profile repository functionality.
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from pandoc_ui.app.profile_repository import ProfileRepository, UIProfile
from pandoc_ui.models import OutputFormat


class TestUIProfile:
    """Test UIProfile dataclass."""
    
    def test_profile_creation(self):
        """Test creating a UIProfile."""
        now = datetime.now().isoformat()
        
        profile = UIProfile(
            name="Test Profile",
            created_at=now,
            modified_at=now,
            input_file="/test/input.md",
            output_format=OutputFormat.HTML.value,
            is_batch_mode=False
        )
        
        assert profile.name == "Test Profile"
        assert profile.input_file == "/test/input.md"
        assert profile.output_format == "html"
        assert not profile.is_batch_mode
    
    def test_profile_to_dict(self):
        """Test converting profile to dictionary."""
        now = datetime.now().isoformat()
        
        profile = UIProfile(
            name="Test Profile",
            created_at=now,
            modified_at=now,
            input_file="/test/input.md",
            output_format=OutputFormat.PDF.value,
            is_batch_mode=True,
            extensions=".md,.txt"
        )
        
        data = profile.to_dict()
        
        assert isinstance(data, dict)
        assert data['name'] == "Test Profile"
        assert data['input_file'] == "/test/input.md"
        assert data['output_format'] == "pdf"
        assert data['is_batch_mode'] is True
        assert data['extensions'] == ".md,.txt"
    
    def test_profile_from_dict(self):
        """Test creating profile from dictionary."""
        now = datetime.now().isoformat()
        
        data = {
            'name': "From Dict Profile",
            'created_at': now,
            'modified_at': now,
            'input_file': "/test/from_dict.md",
            'output_format': "docx",
            'is_batch_mode': False,
            'html_standalone': True,
            'max_concurrent_jobs': 8
        }
        
        profile = UIProfile.from_dict(data)
        
        assert profile.name == "From Dict Profile"
        assert profile.input_file == "/test/from_dict.md"
        assert profile.output_format == "docx"
        assert not profile.is_batch_mode
        assert profile.html_standalone is True
        assert profile.max_concurrent_jobs == 8


class TestProfileRepository:
    """Test ProfileRepository functionality."""
    
    @pytest.fixture
    def temp_profiles_dir(self):
        """Create temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def repository(self, temp_profiles_dir):
        """Create profile repository with temp directory."""
        return ProfileRepository(profiles_dir=temp_profiles_dir)
    
    @pytest.fixture
    def sample_profile(self):
        """Create sample profile for testing."""
        now = datetime.now().isoformat()
        
        return UIProfile(
            name="Sample Profile",
            created_at=now,
            modified_at=now,
            input_file="/sample/input.md",
            output_file="/sample/output.html",
            output_format=OutputFormat.HTML.value,
            is_batch_mode=False,
            extensions=".md",
            scan_recursive=True,
            max_files=1000,
            html_standalone=True,
            max_concurrent_jobs=4
        )
    
    def test_repository_initialization(self, temp_profiles_dir):
        """Test repository initialization."""
        repo = ProfileRepository(profiles_dir=temp_profiles_dir)
        
        assert repo.profiles_dir == temp_profiles_dir
        assert temp_profiles_dir.exists()
    
    def test_save_profile(self, repository, sample_profile):
        """Test saving a profile."""
        success = repository.save_profile(sample_profile)
        
        assert success
        
        # Check file was created (spaces become underscores)
        profile_file = repository.profiles_dir / "Sample_Profile.json"
        assert profile_file.exists()
        
        # Check file content
        with open(profile_file, 'r') as f:
            data = json.load(f)
        
        assert data['name'] == "Sample Profile"
        assert data['input_file'] == "/sample/input.md"
        assert data['output_format'] == "html"
    
    def test_load_profile(self, repository, sample_profile):
        """Test loading a profile."""
        # Save first
        repository.save_profile(sample_profile)
        
        # Load it back
        loaded_profile = repository.load_profile("Sample Profile")
        
        assert loaded_profile is not None
        assert loaded_profile.name == sample_profile.name
        assert loaded_profile.input_file == sample_profile.input_file
        assert loaded_profile.output_format == sample_profile.output_format
        assert loaded_profile.is_batch_mode == sample_profile.is_batch_mode
    
    def test_load_nonexistent_profile(self, repository):
        """Test loading a profile that doesn't exist."""
        loaded_profile = repository.load_profile("Nonexistent Profile")
        
        assert loaded_profile is None
    
    def test_list_profiles(self, repository):
        """Test listing profiles."""
        # Initially empty
        profiles = repository.list_profiles()
        assert len(profiles) == 0
        
        # Add some profiles
        now = datetime.now().isoformat()
        
        profile1 = UIProfile(
            name="Profile 1",
            created_at=now,
            modified_at=now,
            output_format="html"
        )
        
        profile2 = UIProfile(
            name="Profile 2", 
            created_at=now,
            modified_at=now,
            output_format="pdf"
        )
        
        repository.save_profile(profile1)
        repository.save_profile(profile2)
        
        # List them
        profiles = repository.list_profiles()
        assert len(profiles) == 2
        
        profile_names = [p.name for p in profiles]
        assert "Profile 1" in profile_names
        assert "Profile 2" in profile_names
    
    def test_delete_profile(self, repository, sample_profile):
        """Test deleting a profile."""
        # Save first
        repository.save_profile(sample_profile)
        
        # Verify it exists
        assert repository.profile_exists("Sample Profile")
        
        # Delete it
        success = repository.delete_profile("Sample Profile")
        assert success
        
        # Verify it's gone
        assert not repository.profile_exists("Sample Profile")
        loaded_profile = repository.load_profile("Sample Profile")
        assert loaded_profile is None
    
    def test_delete_nonexistent_profile(self, repository):
        """Test deleting a profile that doesn't exist."""
        success = repository.delete_profile("Nonexistent Profile")
        assert not success
    
    def test_profile_exists(self, repository, sample_profile):
        """Test checking if profile exists."""
        # Initially doesn't exist
        assert not repository.profile_exists("Sample Profile")
        
        # Save it
        repository.save_profile(sample_profile)
        
        # Now it exists
        assert repository.profile_exists("Sample Profile")
    
    def test_get_profile_count(self, repository):
        """Test getting profile count."""
        # Initially 0
        assert repository.get_profile_count() == 0
        
        # Add profiles
        now = datetime.now().isoformat()
        
        for i in range(3):
            profile = UIProfile(
                name=f"Profile {i+1}",
                created_at=now,
                modified_at=now,
                output_format="html"
            )
            repository.save_profile(profile)
        
        # Should be 3
        assert repository.get_profile_count() == 3
    
    def test_sanitize_filename(self, repository):
        """Test filename sanitization."""
        # Test with unsafe characters
        unsafe_name = 'Test/Profile<>:"|?*'
        safe_name = repository._sanitize_filename(unsafe_name)
        
        assert '/' not in safe_name
        assert '<' not in safe_name
        assert '>' not in safe_name
        assert ':' not in safe_name
        assert '"' not in safe_name
        assert '|' not in safe_name
        assert '?' not in safe_name
        assert '*' not in safe_name
        
        # Should contain underscores instead
        assert '_' in safe_name
    
    def test_create_profile_from_ui_state(self, repository):
        """Test creating profile from UI state."""
        ui_state = {
            'input_file': '/test/input.md',
            'output_file': '/test/output.html',
            'output_format': 'html',
            'is_batch_mode': False,
            'extensions': '.md,.txt',
            'scan_recursive': True,
            'max_files': 500,
            'html_standalone': True,
            'max_concurrent_jobs': 8
        }
        
        profile = repository.create_profile_from_ui_state("UI State Profile", ui_state)
        
        assert profile.name == "UI State Profile"
        assert profile.input_file == '/test/input.md'
        assert profile.output_file == '/test/output.html'
        assert profile.output_format == 'html'
        assert not profile.is_batch_mode
        assert profile.extensions == '.md,.txt'
        assert profile.scan_recursive is True
        assert profile.max_files == 500
        assert profile.html_standalone is True
        assert profile.max_concurrent_jobs == 8
    
    def test_get_default_profile(self, repository):
        """Test getting default profile."""
        default_profile = repository.get_default_profile()
        
        assert default_profile.name == "Default"
        assert default_profile.output_format == "html"
        assert not default_profile.is_batch_mode
        assert default_profile.extensions == ".md"
        assert default_profile.scan_recursive is True
        assert default_profile.max_files == 1000
        assert default_profile.html_standalone is True
        assert default_profile.max_concurrent_jobs == 4
    
    def test_overwrite_existing_profile(self, repository, sample_profile):
        """Test overwriting an existing profile."""
        # Save initial profile
        repository.save_profile(sample_profile)
        
        # Modify and save again
        sample_profile.output_format = "pdf"
        sample_profile.max_concurrent_jobs = 8
        
        success = repository.save_profile(sample_profile)
        assert success
        
        # Load and verify changes
        loaded_profile = repository.load_profile("Sample Profile")
        assert loaded_profile.output_format == "pdf"
        assert loaded_profile.max_concurrent_jobs == 8
        
        # Should still only have one file
        assert repository.get_profile_count() == 1