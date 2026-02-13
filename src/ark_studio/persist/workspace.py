# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
import asyncio
from dataclasses import dataclass
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine, select, col

from ark_studio.core.tasking import Task
from ark_studio.models.tables.files import FileRecord
from ark_studio.utils.logger import logger


class WorkspaceDatabase:
    """Workspace database manager for file system."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path
        self._db_dir = workspace_path / ".as" / "db"
        self._db_path = self._db_dir / "workspace.db"
        self._db_engine = None
        self._initialized = False

    def initialize(self):
        """Initializes database connection and create tables if needed."""
        if self._initialized:
            return

        # Create directory if not exists
        self._db_dir.mkdir(parents=True, exist_ok=True)

        # Create engine
        db_url = f"sqlite:///{self._db_path}"
        self._db_engine = create_engine(db_url, echo=False)

        # Create tables
        SQLModel.metadata.create_all(self._db_engine)
        self._initialized = True
        logger.info(f"Workspace database initialized at {self._db_path}")

    def close(self):
        """Closes database connection."""
        if self._db_engine:
            self._db_engine.dispose()
            self._db_engine = None
            self._initialized = False
            logger.info("Database connection closed")

    def get_files_by_parent(
        self, parent_path: str | None = None, offset: int = 0, limit: int = 100
    ) -> tuple[list[FileRecord], int]:
        """Gets files by parent path with pagination.

        Args:
            parent_path: Parent directory path (None for root)
            offset: Offset for pagination
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of file records, total count)
        """
        if not self._initialized:
            return [], 0

        with Session(self._db_engine) as session:
            statement = select(FileRecord).where(FileRecord.parent == parent_path)
            total = len(session.exec(statement).all())
            statement = statement.offset(offset).limit(limit)
            results = session.exec(statement).all()
            logger.debug(f"Listed {len(results)} records from database with total {total}")
            return list(results), total

    def get_subdirectories(self, parent_path: str | None = None) -> list[FileRecord]:
        """Gets all subdirectories under a parent path.

        Args:
            parent_path: Parent directory path (None for root)

        Returns:
            List of directory records
        """
        if not self._initialized:
            return []

        with Session(self._db_engine) as session:
            statement = select(FileRecord).where(FileRecord.parent == parent_path).where(FileRecord.type == "folder")
            results = session.exec(statement).all()
            logger.debug(f"Got {len(results)} subdirectory records from database for '{parent_path}'")
            return list(results)

    def count_children(self, parent_path: str) -> int:
        """Counts children files/folders under a path.

        Args:
            parent_path: Parent directory path

        Returns:
            Number of children
        """
        if not self._initialized:
            return 0

        with Session(self._db_engine) as session:
            statement = select(FileRecord).where(FileRecord.parent == parent_path)
            logger.trace(f"Counting children for '{parent_path}' with statement: {statement}")
            return len(session.exec(statement).all())

    def has_subdirectories(self, parent_path: str) -> bool:
        """Checks if a directory has subdirectories.

        Args:
            parent_path: Parent directory path

        Returns:
            True if has subdirectories, False otherwise
        """
        if not self._initialized:
            return False

        with Session(self._db_engine) as session:
            statement = (
                select(FileRecord).where(FileRecord.parent == parent_path).where(FileRecord.type == "folder").limit(1)
            )
            result = session.exec(statement).first()
            logger.trace(f"Checking subdirectories for '{parent_path}' with statement: {statement}, result: {result}")
            return result is not None

    def search_files_by_field(
        self, search_pattern: str, field: str = "path", offset: int = 0, limit: int = 100
    ) -> tuple[list[FileRecord], int]:
        """Searches files by a specific field pattern.

        Args:
            search_pattern: Search pattern (will match files containing this string)
            field: Field to search in ('name' or 'path')
            offset: Offset for pagination
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of file records, total count)
        """
        if not self._initialized:
            return [], 0

        with Session(self._db_engine) as session:
            # Build query with LIKE pattern using col()
            if field == "name":
                statement = select(FileRecord).where(col(FileRecord.name).contains(search_pattern))
            elif field == "path":
                statement = select(FileRecord).where(col(FileRecord.path).contains(search_pattern))
            else:
                # Default to path if invalid field
                statement = select(FileRecord).where(col(FileRecord.path).contains(search_pattern))

            total = len(session.exec(statement).all())
            statement = statement.offset(offset).limit(limit)
            results = session.exec(statement).all()
            logger.debug(
                f"Searched files by '{field}' with pattern '{search_pattern}', got {len(results)} records with total {total}"
            )
            return list(results), total


@dataclass
class BuildFileIndexParam:
    workspace_path: Path


class BuildFileIndexTask(Task[BuildFileIndexParam]):
    """Task to build file index in database."""

    def __init__(self):
        super().__init__()
        self._title = "Build File Index"
        self._exclusive_keys = {"file_index"}  # Prevent concurrent index builds

    async def run_impl(self, param: BuildFileIndexParam) -> None:
        await asyncio.to_thread(self._build_index_sync, param)

    def _build_index_sync(self, param: BuildFileIndexParam) -> None:
        self.update_message("Initializing database...")

        # Initialize database
        db = WorkspaceDatabase(param.workspace_path)
        db.initialize()

        self.update_message("Clearing existing records...")

        # Scan and build index
        count = 0
        try:
            from sqlmodel import Session
            from ark_studio.models.tables.files import FileRecord

            with Session(db._db_engine) as session:
                # Clear existing records
                session.query(FileRecord).delete()
                session.commit()
                logger.info("Cleared existing file records")

                # Count total files first for progress
                total_count = 0

                def count_files(path: Path):
                    nonlocal total_count
                    try:
                        for item in path.iterdir():
                            rel_path = item.relative_to(param.workspace_path).as_posix()
                            if rel_path.startswith("."):
                                continue
                            total_count += 1
                            if total_count % 100 == 0:
                                self.update_message(f"Found {total_count} files to index, scanning...")
                            if item.is_dir():
                                count_files(item)
                    except (PermissionError, Exception):
                        pass

                logger.info("Counting files to index")
                count_files(param.workspace_path)

                # Scan workspace
                logger.info(f"Indexing {total_count} files")
                self.update_progress(0, total_count)
                self.update_message(f"Indexing files, please wait...")

                def scan_directory(path: Path, parent_path: str | None = None):
                    nonlocal count
                    try:
                        for item in path.iterdir():
                            try:
                                rel_path = item.relative_to(param.workspace_path).as_posix()
                                if rel_path.startswith("."):
                                    continue

                                file_type = "folder" if item.is_dir() else "file"
                                size = item.stat().st_size if item.is_file() else 0

                                record = FileRecord(
                                    name=item.name,
                                    path=rel_path,
                                    type=file_type,
                                    size=size,
                                    parent=parent_path,
                                )
                                session.add(record)
                                count += 1

                                # Commit in batches and update progress
                                if count % 100 == 0:
                                    session.commit()
                                    self.update_progress(count, total_count)

                                # Recursive scan for directories
                                if item.is_dir():
                                    scan_directory(item, rel_path)

                            except Exception as e:
                                logger.warning(f"Skipping item {item}: {e}")
                                continue

                    except PermissionError:
                        logger.warning(f"Permission denied for directory: {path}")
                    except Exception as e:
                        logger.error(f"Error scanning directory {path}: {e}")

                # Start scanning from workspace root
                scan_directory(param.workspace_path, None)
                session.commit()

                self.update_progress(1.0, 1.0)
                self.update_message(f"Indexed {count} files, done")

        finally:
            db.close()

        logger.info(f"File index built successfully: {count} files indexed")
