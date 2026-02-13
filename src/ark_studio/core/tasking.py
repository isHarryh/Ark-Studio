# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass
from collections import deque
import asyncio
import time
import traceback

from ark_studio.utils.logger import logger


PT = TypeVar("PT")  # Param type for task


class Task(ABC, Generic[PT]):
    """Abstract base class for asynchronous tasks with progress tracking."""

    _MAX_PROGRESS_RECORDS = 10

    def __init__(self, *, initial_title: str | None = None, exclusive_keys: set[str] | None = None):
        self._title: str = initial_title or ""
        self._progress: tuple[float, float] | None = None  # (done, total)
        self._message: str = ""
        self._exclusive_keys: set[str] = exclusive_keys or set()

        self._running: bool = False
        self._completed: bool = False
        self._success: bool = False
        self._exception: Optional[Exception] = None
        self._progress_percent_records: deque[tuple[float, float]] = deque(
            maxlen=Task._MAX_PROGRESS_RECORDS
        )  # (timestamp, progress_percent)

    @property
    def title(self) -> str:
        """Task title."""
        return self._title

    @property
    def progress(self) -> tuple[float, float] | None:
        """Task progress as (done, total) or None."""
        return self._progress

    @property
    def progress_percent(self) -> float | None:
        """Task progress as fraction (0.0-1.0) or None."""
        if self._progress is None:
            return None
        done, total = self._progress
        if total == 0:
            return 0.0
        return done / total

    @property
    def message(self) -> str:
        """Current task message."""
        return self._message

    @property
    def running(self) -> bool:
        """Whether task is currently running."""
        return self._running

    @property
    def completed(self) -> bool:
        """Whether task has completed."""
        return self._completed

    @property
    def success(self) -> bool:
        """Whether task completed successfully."""
        return self._success

    @property
    def exception(self) -> Optional[Exception]:
        """Exception if task failed, None otherwise."""
        return self._exception

    def update_title(self, new_value: str) -> None:
        self._title = new_value
        logger.trace(f"Task '{self._title}' title updated")

    def update_progress(self, done: float, total: float) -> None:
        self._progress = (done, total)
        percent = self.progress_percent
        if percent is not None:
            self._progress_percent_records.append((time.time(), percent))
            logger.trace(f"Task '{self._title}' progress: {done}/{total} ({percent*100:.1f}%)")
        else:
            logger.trace(f"Task '{self._title}' progress: {done}/{total}")

    def update_message(self, new_value: str) -> None:
        self._message = new_value
        logger.trace(f"Task '{self._title}' message: {new_value}")

    @abstractmethod
    async def run_impl(self, param: PT) -> None:
        """Implementation of task execution.

        Args:
            param: Task-specific param

        This method should be implemented by subclasses to define
        the actual task logic. It can call update_title, update_progress,
        and update_message to report progress.
        """

    async def run(self, param: PT) -> None:
        """Runs the task with proper state management.

        Args:
            param: Task-specific param

        This method handles task state transitions and exception handling.
        """
        if self._running:
            raise RuntimeError(f"Task '{self._title}' is already running")

        if self._completed:
            raise RuntimeError(f"Task '{self._title}' has already completed")

        self._running = True
        logger.info(f"Task '{self._title}': Starting")

        try:
            await self.run_impl(param)
            self._success = True
            logger.info(f"Task '{self._title}': Completed successfully")
        except Exception as e:
            self._exception = e
            self._success = False
            logger.error(f"Task '{self._title}': Failed with exception: {e}")
            logger.debug(traceback.format_exc())
        finally:
            self._running = False
            self._completed = True

    def is_conflicted_with(self, other: "Task") -> bool:
        """Checks if this task conflicts with another task.

        Args:
            other: Another task to check conflict with

        Returns:
            True if tasks have overlapping exclusive keys, False otherwise
        """
        if not self._exclusive_keys or not other._exclusive_keys:
            return False

        return bool(self._exclusive_keys & other._exclusive_keys)

    def get_eta(self) -> float | None:
        """Gets estimated time remaining in seconds.

        Returns:
            Estimated seconds remaining, or None if not available or non-positive
        """
        if len(self._progress_percent_records) < 2:
            return None

        current_percent = self.progress_percent
        if current_percent is None or current_percent >= 1.0:
            return None

        # Calculate average rate from recent records
        records = list(self._progress_percent_records)
        oldest_time, oldest_percent = records[0]
        newest_time, newest_percent = records[-1]

        time_elapsed = newest_time - oldest_time
        if time_elapsed <= 0:
            return None

        progress_made = newest_percent - oldest_percent
        if progress_made <= 0:
            return None

        # Calculate rate and estimate remaining time
        rate = progress_made / time_elapsed  # percent per second
        remaining_percent = 1.0 - current_percent
        eta_seconds = remaining_percent / rate

        if eta_seconds <= 0:
            return None

        return eta_seconds


@dataclass
class TaskInfo:
    """Task information for API responses."""

    id: str
    title: str
    message: str
    progress: tuple[float, float] | None
    progress_percent: float | None
    running: bool
    completed: bool
    success: bool
    error: str | None
    eta: float | None  # Estimated seconds remaining


class TaskManager:
    """Manager for tracking and coordinating tasks."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._task_counter: int = 0
        self._lock = asyncio.Lock()

    def _generate_task_id(self) -> str:
        self._task_counter += 1
        return f"task_{self._task_counter}"

    async def register_task(self, task: Task) -> str:
        """Registers a new task.

        Args:
            task: Task to register

        Returns:
            Task ID

        Raises:
            TaskConflictError: If task conflicts with running tasks
        """
        from ark_studio.exceptions import TaskConflictError

        async with self._lock:
            # Check for conflicts with running tasks
            for existing_id, existing_task in self._tasks.items():
                if existing_task.running and task.is_conflicted_with(existing_task):
                    raise TaskConflictError(
                        f"Task conflicts with running task '{existing_task.title}' (ID: {existing_id})"
                    )

            # Generate ID and register
            task_id = self._generate_task_id()
            self._tasks[task_id] = task
            logger.info(f"Task registered: {task_id} - '{task.title}'")
            return task_id

    async def run_task(self, task_id: str, data) -> None:
        """Runs a registered task.

        Args:
            task_id: ID of the task to run
            data: Task-specific data

        Raises:
            KeyError: If task ID not found
        """
        async with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            task = self._tasks[task_id]

        # Run task outside lock to allow concurrent operations
        await task.run(data)

    async def start_task(self, task: Task, data) -> str:
        """Registers and immediately start a task.

        Args:
            task: Task to start
            data: Task-specific data

        Returns:
            Task ID
        """
        task_id = await self.register_task(task)

        # Start task in background
        asyncio.create_task(self.run_task(task_id, data))

        return task_id

    def get_task(self, task_id: str) -> Task | None:
        """Gets a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task instance or None if not found
        """
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> dict[str, Task]:
        """Gets all registered tasks.

        Returns:
            Dictionary of task ID to Task instance
        """
        return self._tasks.copy()

    def get_task_info(self, task_id: str) -> TaskInfo | None:
        """Gets task information by ID.

        Args:
            task_id: Task ID

        Returns:
            TaskInfo or None if not found
        """
        task = self.get_task(task_id)
        if not task:
            return None

        return TaskInfo(
            id=task_id,
            title=task.title,
            message=task.message,
            progress=task.progress,
            progress_percent=task.progress_percent,
            running=task.running,
            completed=task.completed,
            success=task.success,
            error=str(task.exception) if task.exception else None,
            eta=task.get_eta(),
        )

    def get_all_task_info(self) -> list[TaskInfo]:
        """Gets information for all tasks.

        Returns:
            List of TaskInfo objects
        """
        return [
            TaskInfo(
                id=task_id,
                title=task.title,
                message=task.message,
                progress=task.progress,
                progress_percent=task.progress_percent,
                running=task.running,
                completed=task.completed,
                success=task.success,
                error=str(task.exception) if task.exception else None,
                eta=task.get_eta(),
            )
            for task_id, task in self._tasks.items()
        ]

    async def cleanup_completed_tasks(self) -> int:
        """Cleans up old completed tasks.

        Returns:
            Number of tasks removed
        """
        async with self._lock:
            completed = [(task_id, task) for task_id, task in self._tasks.items() if task.completed]

            for task_id, _ in completed:
                del self._tasks[task_id]

            logger.info(f"Cleaned up {len(completed)} completed tasks")
            return len(completed)


# Global task manager instance
task_manager = TaskManager()
