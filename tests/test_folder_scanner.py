"""
Tests for folder scanner functionality.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from pandoc_ui.app.folder_scanner import FolderScanner, ScanMode, ScanResult
from pandoc_ui.models import OutputFormat


class TestFolderScanner:
    """Test cases for FolderScanner."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def scanner(self):
        """Create FolderScanner instance."""
        return FolderScanner()

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        files = {
            "document.md": "Sample markdown",
            "readme.rst": "RestructuredText",
            "article.txt": "Plain text",
            "notes.html": "<html>Notes</html>",
            "data.json": '{"key": "value"}',
            "image.png": b"fake image data",  # Binary file
            "script.py": 'print("hello")',
        }

        created_files = {}
        for filename, content in files.items():
            file_path = temp_dir / filename
            if isinstance(content, str):
                file_path.write_text(content)
            else:
                file_path.write_bytes(content)
            created_files[filename] = file_path

        return created_files

    @pytest.fixture
    def nested_structure(self, temp_dir):
        """Create nested directory structure."""
        structure = {
            "root.md": "Root markdown",
            "subdir1/file1.md": "Subdir 1 markdown",
            "subdir1/file2.rst": "Subdir 1 rst",
            "subdir2/nested/deep.md": "Deep markdown",
            "subdir2/other.txt": "Other file",
            ".git/config": "Git config",
            "__pycache__/cache.pyc": "Cache file",
            "node_modules/package.json": '{"name": "test"}',
        }

        created_files = {}
        for filepath, content in structure.items():
            full_path = temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            created_files[filepath] = full_path

        return created_files

    def test_init(self, scanner):
        """Test scanner initialization."""
        assert scanner is not None
        assert hasattr(scanner, "DEFAULT_EXTENSIONS")
        assert "markdown" in scanner.DEFAULT_EXTENSIONS
        assert ".md" in scanner.DEFAULT_EXTENSIONS["markdown"]

    def test_scan_nonexistent_folder(self, scanner):
        """Test scanning non-existent folder."""
        result = scanner.scan_folder(Path("/nonexistent/path"))

        assert not result.success
        assert len(result.errors) > 0
        assert "does not exist" in result.errors[0]
        assert result.total_count == 0
        assert result.filtered_count == 0

    def test_scan_file_instead_of_folder(self, scanner, temp_dir):
        """Test scanning a file instead of directory."""
        test_file = temp_dir / "test.md"
        test_file.write_text("Test content")

        result = scanner.scan_folder(test_file)

        assert not result.success
        assert len(result.errors) > 0
        assert "not a directory" in result.errors[0]

    def test_scan_empty_folder(self, scanner, temp_dir):
        """Test scanning empty folder."""
        result = scanner.scan_folder(temp_dir)

        assert result.success
        assert result.total_count == 0
        assert result.filtered_count == 0
        assert len(result.files) == 0

    def test_scan_single_level(self, scanner, temp_dir, sample_files):
        """Test single level scanning."""
        result = scanner.scan_folder(
            temp_dir, extensions={".md", ".rst", ".html"}, mode=ScanMode.SINGLE_LEVEL
        )

        assert result.success
        assert result.total_count == len(sample_files)  # All files in directory
        assert result.filtered_count == 3  # .md, .rst, .html files
        assert len(result.files) == 3

        # Check specific files are found
        found_names = {f.name for f in result.files}
        assert "document.md" in found_names
        assert "readme.rst" in found_names
        assert "notes.html" in found_names
        assert "article.txt" not in found_names  # Filtered out

    def test_scan_recursive(self, scanner, temp_dir, nested_structure):
        """Test recursive scanning."""
        result = scanner.scan_folder(temp_dir, extensions={".md", ".rst"}, mode=ScanMode.RECURSIVE)

        assert result.success
        assert result.filtered_count == 4  # 4 .md/.rst files

        # Check all markdown files found
        found_paths = [str(f.relative_to(temp_dir)) for f in result.files]
        assert "root.md" in found_paths
        assert "subdir1/file1.md" in found_paths
        assert "subdir1/file2.rst" in found_paths
        assert "subdir2/nested/deep.md" in found_paths

        # Check ignored directories not scanned
        assert not any(".git" in str(f) for f in result.files)
        assert not any("__pycache__" in str(f) for f in result.files)
        assert not any("node_modules" in str(f) for f in result.files)

    def test_extension_normalization(self, scanner, temp_dir, sample_files):
        """Test that extensions are normalized properly."""
        # Test with and without dots
        result1 = scanner.scan_folder(temp_dir, extensions={"md", "rst"})
        result2 = scanner.scan_folder(temp_dir, extensions={".md", ".rst"})

        assert result1.filtered_count == result2.filtered_count
        assert len(result1.files) == len(result2.files)

    def test_max_files_limit(self, scanner, temp_dir):
        """Test max_files limit."""
        # Create many files
        for i in range(20):
            (temp_dir / f"file{i}.md").write_text(f"Content {i}")

        result = scanner.scan_folder(temp_dir, extensions={".md"}, max_files=10)

        assert result.success
        assert len(result.files) == 10
        assert result.total_count >= 10  # Could be more if limit hit during total count

    def test_ignore_patterns(self, scanner, temp_dir):
        """Test custom ignore patterns."""
        # Create files with custom patterns to ignore
        files_to_create = ["good.md", "ignore_me.md", "temp/file.md", "backup/old.md"]

        for filepath in files_to_create:
            full_path = temp_dir / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("Content")

        result = scanner.scan_folder(
            temp_dir,
            extensions={".md"},
            mode=ScanMode.RECURSIVE,
            ignore_patterns={"temp", "backup", "ignore_me.md"},
        )

        assert result.success
        assert result.filtered_count == 1  # Only good.md
        assert result.files[0].name == "good.md"

    def test_get_supported_extensions(self, scanner):
        """Test getting supported extensions."""
        # Test all extensions
        all_extensions = scanner.get_supported_extensions()
        assert ".md" in all_extensions
        assert ".rst" in all_extensions
        assert ".html" in all_extensions

        # Test PDF-specific extensions
        pdf_extensions = scanner.get_supported_extensions(OutputFormat.PDF)
        assert ".md" in pdf_extensions
        assert ".tex" in pdf_extensions

        # Test HTML-specific extensions
        html_extensions = scanner.get_supported_extensions(OutputFormat.HTML)
        assert ".md" in html_extensions
        assert ".rst" in html_extensions

    def test_get_extension_categories(self, scanner):
        """Test getting extension categories."""
        categories = scanner.get_extension_categories()

        assert "markdown" in categories
        assert "html" in categories
        assert "latex" in categories
        assert ".md" in categories["markdown"]
        assert ".html" in categories["html"]

    def test_estimate_batch_size(self, scanner, temp_dir, nested_structure):
        """Test batch size estimation."""
        estimate = scanner.estimate_batch_size(temp_dir, extensions={".md", ".rst"})

        assert "single_level_estimate" in estimate
        assert "recursive_estimate" in estimate
        assert "recommended_mode" in estimate
        assert "recommended_batch_size" in estimate
        assert "estimated_duration_minutes" in estimate

        assert estimate["recursive_estimate"] >= estimate["single_level_estimate"]
        assert estimate["recommended_batch_size"] > 0

    def test_scan_statistics(self, scanner, temp_dir, sample_files):
        """Test scan statistics tracking."""
        initial_stats = scanner.scan_statistics
        assert "total_scanned" in initial_stats
        assert initial_stats["total_scanned"] == 0

        # Perform scan
        scanner.scan_folder(temp_dir, extensions={".md"})

        # Check stats updated
        updated_stats = scanner.scan_statistics
        assert updated_stats["total_scanned"] > 0
        assert updated_stats["last_scan_duration"] > 0

    def test_scan_result_properties(self):
        """Test ScanResult properties."""
        # Successful result
        result = ScanResult(
            files=[Path("test.md")],
            total_count=5,
            filtered_count=1,
            errors=[],
            scan_duration_seconds=1.5,
        )

        assert result.success is True
        assert "Found 5 files" in result.summary
        assert "1 matching filters" in result.summary

        # Failed result
        failed_result = ScanResult(
            files=[],
            total_count=0,
            filtered_count=0,
            errors=["Permission denied"],
            scan_duration_seconds=0.1,
        )

        assert failed_result.success is False
        assert "1 errors" in failed_result.summary

    def test_permission_error_handling(self, scanner, temp_dir):
        """Test handling of permission errors."""
        # Mock permission error
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.rglob", side_effect=PermissionError("Access denied")),
        ):
            result = scanner.scan_folder(temp_dir)

            # Should handle gracefully
            assert len(result.files) == 0
            # Error might be logged but not necessarily in result.errors for this case

    def test_default_extensions_comprehensive(self, scanner):
        """Test that all expected default extensions are present."""
        expected_formats = {
            "markdown",
            "restructuredtext",
            "asciidoc",
            "textile",
            "html",
            "latex",
            "docx",
            "odt",
            "epub",
            "org",
        }

        for format_name in expected_formats:
            assert format_name in scanner.DEFAULT_EXTENSIONS
            assert len(scanner.DEFAULT_EXTENSIONS[format_name]) > 0

            # Check all extensions start with dot
            for ext in scanner.DEFAULT_EXTENSIONS[format_name]:
                assert ext.startswith(".")

    def test_scan_mode_enum(self):
        """Test ScanMode enum values."""
        assert ScanMode.RECURSIVE.value == "recursive"
        assert ScanMode.SINGLE_LEVEL.value == "single_level"

    def test_hidden_files_ignored(self, scanner, temp_dir):
        """Test that hidden files are ignored."""
        # Create hidden files
        (temp_dir / ".hidden.md").write_text("Hidden file")
        (temp_dir / "visible.md").write_text("Visible file")

        # Create hidden directory with file
        hidden_dir = temp_dir / ".hidden_dir"
        hidden_dir.mkdir()
        (hidden_dir / "file.md").write_text("File in hidden dir")

        result = scanner.scan_folder(temp_dir, extensions={".md"}, mode=ScanMode.RECURSIVE)

        assert result.success
        assert result.filtered_count == 1  # Only visible.md
        assert result.files[0].name == "visible.md"

    def test_large_directory_performance(self, scanner, temp_dir):
        """Test performance with larger directory structures."""
        # Create moderate number of files to test performance
        subdirs = ["dir1", "dir2", "dir3"]
        files_per_dir = 20

        for subdir in subdirs:
            subdir_path = temp_dir / subdir
            subdir_path.mkdir()
            for i in range(files_per_dir):
                (subdir_path / f"file{i}.md").write_text(f"Content {i}")
                (subdir_path / f"other{i}.txt").write_text(f"Other {i}")

        # Time the scan
        import time

        start_time = time.time()

        result = scanner.scan_folder(temp_dir, extensions={".md"}, mode=ScanMode.RECURSIVE)

        scan_time = time.time() - start_time

        assert result.success
        assert result.filtered_count == len(subdirs) * files_per_dir
        assert scan_time < 5.0  # Should complete within 5 seconds
        assert result.scan_duration_seconds > 0
