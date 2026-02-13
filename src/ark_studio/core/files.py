# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from ark_studio.persist.workspace import WorkspaceDatabase
from ark_studio.utils.logger import logger

LazySubtree = bool | list["TreeInfo"]
"""Lazy subtree type.
- `True`: not loaded, has subtree
- `False`: not loaded, no subtree
- `list`: loaded, has subtree or no subtree (empty list)
"""


@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    is_directory: bool
    children_count: int = 0
    parent: str | None = None


@dataclass
class TreeInfo:
    name: str
    path: str
    subtree: LazySubtree = False
    children_count: int = 0


class WorkspaceManager:

    def __init__(self):
        self._workspace_path: Optional[Path] = None
        self._db: Optional[WorkspaceDatabase] = None

    @property
    def workspace_path(self) -> Optional[Path]:
        return self._workspace_path

    def open_workspace(self, path: str) -> bool:
        """Opens a workspace."""
        workspace = Path(path)
        if not workspace.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if not workspace.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        self._workspace_path = workspace

        # Initialize database
        self._db = WorkspaceDatabase(workspace)
        self._db.initialize()

        logger.info(f"Opened workspace: {path}")
        return True

    def close_workspace(self):
        """Closes the workspace and clear caches."""
        if self._workspace_path:
            self._workspace_path = None
        if self._db:
            self._db.close()
            self._db = None
        logger.info(f"Closed workspace: {self._workspace_path}")

    def list_files(self, relative_path: str = "", offset: int = 0, limit: int = 100) -> tuple[list[FileInfo], int]:
        """Lists files in a directory with pagination from database."""
        if not self._db:
            return [], 0

        # Get files from database
        logger.info(f"Listing files in '{relative_path}' with offset {offset} and limit {limit}")
        records, total = self._db.get_files_by_parent(
            parent_path=relative_path if relative_path else None, offset=offset, limit=limit
        )

        # Convert to FileInfo
        files = []
        for record in records:
            # Get children count
            children_count = 0
            if record.type == "folder":
                children_count = self._db.count_children(record.path)

            files.append(
                FileInfo(
                    name=record.name,
                    path=record.path,
                    size=record.size,
                    is_directory=record.type == "folder",
                    parent=record.parent,
                    children_count=children_count,
                )
            )

        return files, total

    def get_file_tree(self, relative_path: str = "") -> list[TreeInfo]:
        """Gets a single layer of the file tree for a specific path from database.

        Args:
            relative_path: Path relative to workspace root

        Returns:
            List of tree nodes (subdirectories)
        """
        if not self._db:
            return []

        # Get subdirectories from database
        logger.info(f"Getting file tree for '{relative_path}'")
        records = self._db.get_subdirectories(parent_path=relative_path if relative_path else None)

        # Convert to TreeInfo
        trees = []
        for record in records:
            has_sub = self._db.has_subdirectories(record.path)
            children_count = self._db.count_children(record.path)

            trees.append(
                TreeInfo(
                    name=record.name,
                    path=record.path,
                    subtree=True if has_sub else False,
                    children_count=children_count,
                )
            )

        return trees

    def search_files(
        self, search_pattern: str, field: str = "path", offset: int = 0, limit: int = 100
    ) -> tuple[list[FileInfo], int]:
        """Searches files by field pattern.

        Args:
            search_pattern: Search pattern (will match files containing this string)
            field: Field to search in ('name' or 'path')
            offset: Offset for pagination
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of file info, total count)
        """
        if not self._db:
            return [], 0

        # Search in database
        logger.info(f"Searching files by '{field}' with pattern '{search_pattern}', offset {offset}, limit {limit}")
        records, total = self._db.search_files_by_field(search_pattern, field, offset, limit)

        # Convert to FileInfo
        files = []
        for record in records:
            # Get children count
            children_count = 0
            if record.type == "folder":
                children_count = self._db.count_children(record.path)

            files.append(
                FileInfo(
                    name=record.name,
                    path=record.path,
                    size=record.size,
                    is_directory=record.type == "folder",
                    parent=record.parent,
                    children_count=children_count,
                )
            )

        return files, total


# Global instance
workspace_manager = WorkspaceManager()
