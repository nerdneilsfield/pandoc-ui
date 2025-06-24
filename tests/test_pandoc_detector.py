"""
Tests for pandoc detector functionality.
"""

from pathlib import Path
from unittest.mock import Mock, patch

from pandoc_ui.infra.pandoc_detector import PandocDetector, PandocInfo


class TestPandocDetector:
    """Test cases for PandocDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = PandocDetector()

    def test_init(self):
        """Test detector initialization."""
        assert self.detector._cached_info is None

    @patch("shutil.which")
    @patch("pandoc_ui.infra.pandoc_detector.PandocDetector._get_version")
    def test_detect_from_path_success(self, mock_get_version, mock_which):
        """Test successful detection from PATH."""
        mock_which.return_value = "/usr/bin/pandoc"
        mock_get_version.return_value = "3.1.8"

        result = self.detector.detect()

        assert result.available is True
        assert result.path == Path("/usr/bin/pandoc")
        assert result.version == "3.1.8"
        mock_which.assert_called_once_with("pandoc")
        mock_get_version.assert_called_once_with(Path("/usr/bin/pandoc"))

    @patch("shutil.which")
    @patch("pandoc_ui.infra.pandoc_detector.PandocDetector._get_version")
    @patch("pandoc_ui.infra.pandoc_detector.PandocDetector._get_search_paths")
    def test_detect_from_search_paths(self, mock_search_paths, mock_get_version, mock_which):
        """Test detection from search paths when not in PATH."""
        mock_which.return_value = None
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.is_file.return_value = True
        mock_search_paths.return_value = [mock_path]
        mock_get_version.return_value = "3.1.8"

        result = self.detector.detect()

        assert result.available is True
        assert result.path == mock_path
        assert result.version == "3.1.8"

    @patch("shutil.which")
    @patch("pandoc_ui.infra.pandoc_detector.PandocDetector._get_search_paths")
    def test_detect_not_found(self, mock_search_paths, mock_which):
        """Test detection when pandoc is not found."""
        mock_which.return_value = None
        mock_search_paths.return_value = []

        result = self.detector.detect()

        assert result.available is False
        assert result.path == Path("pandoc")
        assert result.version == "unknown"

    def test_detect_uses_cache(self):
        """Test that detection results are cached."""
        cached_info = PandocInfo(Path("/test/pandoc"), "3.1.8")
        self.detector._cached_info = cached_info

        result = self.detector.detect()

        assert result is cached_info

    @patch("platform.system")
    @patch.dict(
        "os.environ",
        {
            "PROGRAMFILES": "C:\\Program Files",
            "PROGRAMFILES(X86)": "C:\\Program Files (x86)",
            "USERPROFILE": "C:\\Users\\test",
        },
    )
    def test_get_search_paths_windows(self, mock_system):
        """Test search paths generation on Windows."""
        mock_system.return_value = "Windows"

        paths = self.detector._get_search_paths()

        path_strings = [str(p) for p in paths]
        # On Linux, Path uses forward slashes even for Windows-style paths
        assert any(
            "Program Files" in p and "Pandoc" in p and "pandoc.exe" in p for p in path_strings
        )
        assert any(
            "Program Files (x86)" in p and "pandoc" in p and "pandoc.exe" in p for p in path_strings
        )
        assert "C:\\ProgramData\\chocolatey\\bin\\pandoc.exe" in path_strings

    @patch("platform.system")
    def test_get_search_paths_macos(self, mock_system):
        """Test search paths generation on macOS."""
        mock_system.return_value = "Darwin"

        paths = self.detector._get_search_paths()

        path_strings = [str(p) for p in paths]
        assert "/usr/local/bin/pandoc" in path_strings
        assert "/opt/homebrew/bin/pandoc" in path_strings
        assert "/opt/local/bin/pandoc" in path_strings

    @patch("platform.system")
    @patch.dict("os.environ", {"HOME": "/home/test"})
    def test_get_search_paths_linux(self, mock_system):
        """Test search paths generation on Linux."""
        mock_system.return_value = "Linux"

        paths = self.detector._get_search_paths()

        path_strings = [str(p) for p in paths]
        assert "/usr/bin/pandoc" in path_strings
        assert "/usr/local/bin/pandoc" in path_strings
        assert "/snap/bin/pandoc" in path_strings

    @patch("subprocess.run")
    def test_get_version_success(self, mock_run):
        """Test successful version extraction."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "pandoc 3.1.8\nCompiled with pandoc-types..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        version = self.detector._get_version(Path("/usr/bin/pandoc"))

        assert version == "3.1.8"

    @patch("subprocess.run")
    def test_get_version_failure(self, mock_run):
        """Test version extraction when command fails."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        version = self.detector._get_version(Path("/usr/bin/pandoc"))

        assert version is None

    @patch("subprocess.run")
    def test_get_version_timeout(self, mock_run):
        """Test version extraction with timeout."""
        mock_run.side_effect = TimeoutError()

        version = self.detector._get_version(Path("/usr/bin/pandoc"))

        assert version is None

    def test_is_available_true(self):
        """Test is_available when pandoc is detected."""
        self.detector._cached_info = PandocInfo(Path("/usr/bin/pandoc"), "3.1.8", True)

        assert self.detector.is_available() is True

    def test_is_available_false(self):
        """Test is_available when pandoc is not detected."""
        self.detector._cached_info = PandocInfo(Path("pandoc"), "unknown", False)

        assert self.detector.is_available() is False

    def test_clear_cache(self):
        """Test cache clearing."""
        self.detector._cached_info = PandocInfo(Path("/usr/bin/pandoc"), "3.1.8")

        self.detector.clear_cache()

        assert self.detector._cached_info is None
