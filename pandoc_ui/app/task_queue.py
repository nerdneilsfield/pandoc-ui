"""
Task queue manager for batch processing with QThreadPool.
"""

import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import time
import threading

from PySide6.QtCore import QObject, Signal, QThreadPool, QRunnable, QMutex, QMutexLocker

from ..models import ConversionProfile, ConversionResult


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchTask:
    """Individual task in the batch queue."""
    id: str
    profile: ConversionProfile
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[ConversionResult] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class ConversionTask(QRunnable):
    """Runnable task for conversion work."""
    
    def __init__(self, task: BatchTask, task_queue: 'TaskQueue'):
        """
        Initialize conversion task.
        
        Args:
            task: BatchTask to execute
            task_queue: TaskQueue instance for callbacks
        """
        super().__init__()
        self.task = task
        self.task_queue = task_queue
        self.setAutoDelete(True)
    
    def run(self):
        """Execute the conversion task."""
        try:
            # Update task status to running
            with QMutexLocker(self.task_queue._mutex):
                self.task.status = TaskStatus.RUNNING
                self.task.start_time = time.time()
                self.task_queue._active_jobs += 1
            
            # Emit task started signal
            self.task_queue.task_started.emit(self.task.id, self.task.profile.input_path.name)
            
            # Perform conversion using shared service
            result = self.task_queue._conversion_service.convert(self.task.profile)
            
            # Update task with result
            with QMutexLocker(self.task_queue._mutex):
                self.task.result = result
                self.task.end_time = time.time()
                self.task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
                if not result.success:
                    self.task.error_message = result.error_message
                self.task_queue._active_jobs -= 1
            
            # Emit appropriate signals
            if result.success:
                self.task_queue.task_completed.emit(
                    self.task.id, 
                    str(result.output_path) if result.output_path else "",
                    self.task.duration or 0.0
                )
            else:
                self.task_queue.task_failed.emit(
                    self.task.id,
                    self.task.profile.input_path.name,
                    result.error_message or "Unknown error"
                )
            
        except Exception as e:
            # Handle unexpected errors
            with QMutexLocker(self.task_queue._mutex):
                self.task.status = TaskStatus.FAILED
                self.task.end_time = time.time()
                self.task.error_message = f"Task execution error: {str(e)}"
                self.task_queue._active_jobs -= 1
            
            self.task_queue.task_failed.emit(
                self.task.id,
                self.task.profile.input_path.name,
                str(e)
            )
            
            logger.error(f"Task {self.task.id} failed with error: {str(e)}")
        
        finally:
            # Check if queue is finished
            self.task_queue._check_queue_completion()


class TaskQueue(QObject):
    """Manages batch conversion tasks using QThreadPool."""
    
    # Signals
    task_started = Signal(str, str)  # task_id, filename
    task_completed = Signal(str, str, float)  # task_id, output_path, duration
    task_failed = Signal(str, str, str)  # task_id, filename, error_message
    queue_progress = Signal(int, int)  # completed_count, total_count
    queue_finished = Signal(int, int, float)  # total_tasks, successful_tasks, total_duration
    
    def __init__(self, max_concurrent_jobs: int = 4, parent=None):
        """
        Initialize task queue.
        
        Args:
            max_concurrent_jobs: Maximum number of concurrent tasks
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self._thread_pool = QThreadPool()
        self._thread_pool.setMaxThreadCount(max_concurrent_jobs)
        
        self._tasks: Dict[str, BatchTask] = {}
        self._task_order: List[str] = []
        self._active_jobs = 0
        self._mutex = QMutex()
        
        # Shared conversion service to avoid repeated initialization overhead
        from ..app.conversion_service import ConversionService
        self._conversion_service = ConversionService()
        
        logger.info(f"TaskQueue initialized with {max_concurrent_jobs} max concurrent jobs")
    
    def set_max_concurrent_jobs(self, count: int):
        """
        Set maximum number of concurrent jobs.
        
        Args:
            count: Maximum concurrent jobs (1-16)
        """
        count = max(1, min(16, count))  # Clamp between 1 and 16
        self._thread_pool.setMaxThreadCount(count)
        logger.info(f"TaskQueue max concurrent jobs set to {count}")
    
    def add_task(self, task_id: str, profile: ConversionProfile) -> bool:
        """
        Add a task to the queue.
        
        Args:
            task_id: Unique identifier for the task
            profile: Conversion profile
            
        Returns:
            True if task was added, False if task_id already exists
        """
        with QMutexLocker(self._mutex):
            if task_id in self._tasks:
                logger.warning(f"Task {task_id} already exists in queue")
                return False
            
            task = BatchTask(id=task_id, profile=profile)
            self._tasks[task_id] = task
            self._task_order.append(task_id)
            
            logger.debug(f"Task {task_id} added to queue: {profile.input_path.name}")
            return True
    
    def start_queue(self):
        """Start processing all tasks in the queue."""
        with QMutexLocker(self._mutex):
            pending_tasks = [task for task in self._tasks.values() 
                           if task.status == TaskStatus.PENDING]
            
            if not pending_tasks:
                logger.warning("No pending tasks to start")
                return
            
            logger.info(f"Starting queue with {len(pending_tasks)} tasks")
            
            # Submit all pending tasks to thread pool
            for task in pending_tasks:
                runnable_task = ConversionTask(task, self)
                self._thread_pool.start(runnable_task)
    
    def cancel_queue(self):
        """Cancel all pending and running tasks."""
        with QMutexLocker(self._mutex):
            # Mark pending tasks as cancelled
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
            
            # Clear the thread pool (running tasks will continue but won't report back)
            self._thread_pool.clear()
            
            logger.info("Task queue cancelled")
    
    def clear_queue(self):
        """Clear all tasks from the queue."""
        with QMutexLocker(self._mutex):
            self._tasks.clear()
            self._task_order.clear()
            self._active_jobs = 0
            
            logger.info("Task queue cleared")
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get status of a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            TaskStatus or None if task doesn't exist
        """
        with QMutexLocker(self._mutex):
            task = self._tasks.get(task_id)
            return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[ConversionResult]:
        """
        Get result of a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            ConversionResult or None if task doesn't exist or hasn't completed
        """
        with QMutexLocker(self._mutex):
            task = self._tasks.get(task_id)
            return task.result if task else None
    
    def get_queue_summary(self) -> Dict[str, int]:
        """
        Get summary of queue status.
        
        Returns:
            Dictionary with counts for each status
        """
        with QMutexLocker(self._mutex):
            summary = {status.value: 0 for status in TaskStatus}
            
            for task in self._tasks.values():
                summary[task.status.value] += 1
            
            summary['total'] = len(self._tasks)
            summary['active_jobs'] = self._active_jobs
            
            return summary
    
    def get_completed_tasks(self) -> List[BatchTask]:
        """
        Get list of completed tasks.
        
        Returns:
            List of completed BatchTask objects
        """
        with QMutexLocker(self._mutex):
            return [task for task in self._tasks.values() 
                   if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
    
    def get_successful_tasks(self) -> List[BatchTask]:
        """
        Get list of successfully completed tasks.
        
        Returns:
            List of successful BatchTask objects
        """
        with QMutexLocker(self._mutex):
            return [task for task in self._tasks.values() 
                   if task.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[BatchTask]:
        """
        Get list of failed tasks.
        
        Returns:
            List of failed BatchTask objects
        """
        with QMutexLocker(self._mutex):
            return [task for task in self._tasks.values() 
                   if task.status == TaskStatus.FAILED]
    
    def _check_queue_completion(self):
        """Check if queue processing is complete and emit signal if so."""
        with QMutexLocker(self._mutex):
            # Check if all tasks are completed or failed
            pending_running = sum(1 for task in self._tasks.values() 
                                if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING])
            
            if pending_running == 0 and self._tasks:
                # Queue is finished
                total_tasks = len(self._tasks)
                successful_tasks = sum(1 for task in self._tasks.values() 
                                     if task.status == TaskStatus.COMPLETED)
                
                # Calculate total duration
                total_duration = sum(task.duration or 0.0 for task in self._tasks.values())
                
                self.queue_finished.emit(total_tasks, successful_tasks, total_duration)
                logger.info(f"Queue finished: {successful_tasks}/{total_tasks} successful, "
                          f"total duration: {total_duration:.2f}s")
            else:
                # Emit progress update
                completed = sum(1 for task in self._tasks.values() 
                              if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED])
                total = len(self._tasks)
                self.queue_progress.emit(completed, total)
    
    @property
    def active_jobs_count(self) -> int:
        """Get current number of active jobs."""
        with QMutexLocker(self._mutex):
            return self._active_jobs
    
    @property
    def max_thread_count(self) -> int:
        """Get maximum thread count."""
        return self._thread_pool.maxThreadCount()
    
    def wait_for_completion(self, timeout_ms: int = 30000) -> bool:
        """
        Wait for all tasks to complete.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            True if all tasks completed within timeout
        """
        return self._thread_pool.waitForDone(timeout_ms)