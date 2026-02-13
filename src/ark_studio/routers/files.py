# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ark_studio.core.files import workspace_manager, FileInfo, TreeInfo
from ark_studio.utils.logger import logger


router = APIRouter(prefix="/api/files", tags=["files"])


class WorkspaceRequest(BaseModel):
    path: str


class WorkspaceResponse(BaseModel):
    path: str | None


class FileInfoResponse(BaseModel):
    name: str
    path: str
    size: int
    is_directory: bool
    parent: str | None
    children_count: int


class FilesListResponse(BaseModel):
    files: list[FileInfoResponse]
    total: int


class TreeInfoResponse(BaseModel):
    name: str
    path: str
    subtree: bool  # True if has subdirectories, False if not
    children_count: int


def _to_file_info_response(file_info: FileInfo) -> FileInfoResponse:
    return FileInfoResponse(
        name=file_info.name,
        path=file_info.path,
        size=file_info.size,
        is_directory=file_info.is_directory,
        parent=file_info.parent,
        children_count=file_info.children_count,
    )


def _to_tree_info_response(tree_info: TreeInfo) -> TreeInfoResponse:
    return TreeInfoResponse(
        name=tree_info.name,
        path=tree_info.path,
        subtree=bool(tree_info.subtree),
        children_count=tree_info.children_count,
    )


@router.post("/workspace/open")
async def open_workspace(request: WorkspaceRequest) -> WorkspaceResponse:
    """Opens a workspace."""
    try:
        workspace_manager.open_workspace(request.path)
        logger.info(f"API: Workspace opened at {request.path}")
        return WorkspaceResponse(path=str(workspace_manager.workspace_path))
    except ValueError as e:
        logger.error(f"API: Failed to open workspace at {request.path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workspace")
async def get_workspace() -> WorkspaceResponse:
    """Gets current workspace."""
    return WorkspaceResponse(path=str(workspace_manager.workspace_path) if workspace_manager.workspace_path else None)


@router.post("/workspace/close")
async def close_workspace() -> WorkspaceResponse:
    """Closes the workspace."""
    workspace_manager.close_workspace()
    logger.info("API: Workspace closed")
    return WorkspaceResponse(path=None)


@router.get("/list")
async def list_files(path: str = "", page: int = 1, page_size: int = 100) -> FilesListResponse:
    """Lists files in a directory with pagination."""
    try:
        # Handle "All" selection (Quasar sets rowsPerPage to 0 for "All")
        actual_page_size = page_size if page_size > 0 else 1000000
        offset = (page - 1) * actual_page_size
        files, total = workspace_manager.list_files(path, offset, actual_page_size)
        return FilesListResponse(
            files=[_to_file_info_response(f) for f in files],
            total=total,
        )
    except ValueError as e:
        logger.error(f"API: Failed to list files at {path}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tree")
async def get_file_tree(path: str = ""):
    """Gets a single layer of the file tree for a specific path."""
    trees = workspace_manager.get_file_tree(path)
    return [_to_tree_info_response(t) for t in trees]


@router.get("/search")
async def search_files(query: str = "", field: str = "path", page: int = 1, page_size: int = 100) -> FilesListResponse:
    """Searches files by field pattern with pagination.

    Args:
        query: Search pattern
        field: Field to search in ('name' or 'path')
        page: Page number
        page_size: Page size
    """
    try:
        # Handle "All" selection (Quasar sets rowsPerPage to 0 for "All")
        actual_page_size = page_size if page_size > 0 else 1000000
        offset = (page - 1) * actual_page_size
        files, total = workspace_manager.search_files(query, field, offset, actual_page_size)
        return FilesListResponse(
            files=[_to_file_info_response(f) for f in files],
            total=total,
        )
    except ValueError as e:
        logger.error(f"API: Failed to search files with query {query}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
