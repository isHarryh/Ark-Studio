# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License


class StudioException(Exception):
    """Base exception for Ark Studio."""


class TaskConflictError(StudioException):
    """Raised when a task conflicts with another running task."""
