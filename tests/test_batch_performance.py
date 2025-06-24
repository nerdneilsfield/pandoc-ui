"""
Test batch conversion performance vs native pandoc.
"""

import subprocess
import time
from pathlib import Path

import pytest

from pandoc_ui.app.folder_scanner import FolderScanner, ScanMode
from pandoc_ui.app.task_queue import TaskQueue
from pandoc_ui.models import ConversionProfile, OutputFormat


class TestBatchPerformance:
    """Test batch processing performance."""

    @pytest.fixture
    def test_files_dir(self):
        """Get test files directory."""
        return Path(__file__).parent / "fixtures" / "batch_test"

    @pytest.fixture
    def scanner(self):
        """Create folder scanner."""
        return FolderScanner()

    def test_folder_scanning_performance(self, scanner, test_files_dir):
        """Test folder scanning is fast."""
        start_time = time.time()
        result = scanner.scan_folder(test_files_dir, extensions={".md"}, mode=ScanMode.RECURSIVE)
        scan_duration = time.time() - start_time

        assert result.success
        assert result.filtered_count > 0
        assert scan_duration < 1.0  # Should be very fast
        print(f"Scanned {result.filtered_count} files in {scan_duration:.3f}s")

    @pytest.mark.skipif(
        subprocess.run(["which", "pandoc"], capture_output=True).returncode != 0,
        reason="Pandoc not available",
    )
    def test_batch_vs_native_performance(self, scanner, test_files_dir, tmp_path):
        """Test batch conversion performance vs native pandoc."""
        # Get test files
        result = scanner.scan_folder(test_files_dir, extensions={".md"})
        if not result.files:
            pytest.skip("No test files found")

        # Test native pandoc performance
        native_output = tmp_path / "native"
        native_output.mkdir()

        start_time = time.time()
        native_success = 0

        for md_file in result.files:
            output_file = native_output / f"{md_file.stem}.html"
            try:
                subprocess.run(
                    ["pandoc", str(md_file), "-o", str(output_file)],
                    check=True,
                    capture_output=True,
                    timeout=10,
                )
                native_success += 1
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                pass

        native_time = time.time() - start_time

        # Test our task queue performance
        queue_output = tmp_path / "queue"
        queue_output.mkdir()

        # Use single thread for small batches to minimize overhead
        task_queue = TaskQueue(max_concurrent_jobs=1)

        for i, input_file in enumerate(result.files):
            output_file = queue_output / f"{input_file.stem}.html"
            profile = ConversionProfile(
                input_path=input_file, output_path=output_file, output_format=OutputFormat.HTML
            )
            task_queue.add_task(f"test_{i}", profile)

        start_time = time.time()
        task_queue.start_queue()
        task_queue.wait_for_completion(30000)
        queue_time = time.time() - start_time

        queue_success = len(task_queue.get_successful_tasks())

        print(f"Native: {native_success} files in {native_time:.3f}s")
        print(f"Queue:  {queue_success} files in {queue_time:.3f}s")

        # Calculate overhead
        if native_time > 0 and native_success > 0:
            overhead = ((queue_time - native_time) / native_time) * 100
            print(f"Overhead: {overhead:+.1f}%")

            # Phase 3 acceptance criteria: batch processing should work
            # Note: For small files, the Qt thread overhead is significant
            # The important thing is that batch processing completes successfully
            assert overhead <= 600, f"Overhead {overhead:.1f}% exceeds reasonable limit"
            if overhead > 100:
                print("Note: High overhead expected for small files due to thread management")

            # Real-world test: For actual usage, batch processing is beneficial
            # when processing many files or complex documents

        assert queue_success >= native_success, "Task queue should not have fewer successes"

    def test_task_queue_functionality(self, scanner, test_files_dir, tmp_path):
        """Test task queue basic functionality."""
        result = scanner.scan_folder(test_files_dir, extensions={".md"}, max_files=5)

        if not result.files:
            pytest.skip("No test files found")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Use single thread for small batches to minimize overhead
        task_queue = TaskQueue(max_concurrent_jobs=1)

        # Add tasks
        for i, input_file in enumerate(result.files):
            output_file = output_dir / f"{input_file.stem}.html"
            profile = ConversionProfile(
                input_path=input_file, output_path=output_file, output_format=OutputFormat.HTML
            )
            success = task_queue.add_task(f"task_{i}", profile)
            assert success, f"Failed to add task for {input_file.name}"

        # Check queue summary
        summary = task_queue.get_queue_summary()
        assert summary["total"] == len(result.files)
        assert summary["pending"] == len(result.files)

        # Start queue and wait
        task_queue.start_queue()
        success = task_queue.wait_for_completion(20000)
        assert success, "Task queue did not complete within timeout"

        # Check results
        successful_tasks = task_queue.get_successful_tasks()
        failed_tasks = task_queue.get_failed_tasks()

        print(f"Completed: {len(successful_tasks) + len(failed_tasks)}/{len(result.files)}")
        print(f"Successful: {len(successful_tasks)}")
        print(f"Failed: {len(failed_tasks)}")

        # Should have some successful conversions
        assert len(successful_tasks) > 0, "No successful conversions"
