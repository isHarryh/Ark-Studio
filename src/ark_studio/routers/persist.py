# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ark_studio.core.files import workspace_manager
from ark_studio.core.tasking import task_manager
from ark_studio.exceptions import TaskConflictError
from ark_studio.persist.workspace import BuildFileIndexTask, BuildFileIndexParam
from ark_studio.utils.logger import logger


router = APIRouter(prefix="/api/persist", tags=["persist"])


class BuildFilesResponse(BaseModel):
    task_id: str
    message: str


@router.post("/build/files")
async def build_files() -> BuildFilesResponse:
    """Builds file index in database by scanning workspace (as background task)."""
    try:
        if not workspace_manager.workspace_path:
            raise HTTPException(status_code=400, detail="No workspace opened")

        # Create and start task
        task = BuildFileIndexTask()
        data = BuildFileIndexParam(workspace_path=workspace_manager.workspace_path)

        task_id = await task_manager.start_task(task, data)
        logger.info(f"API: Started file index build task {task_id}")

        return BuildFilesResponse(task_id=task_id, message="File index build task started")

    except TaskConflictError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to start file index build task: {e}")
        raise HTTPException(status_code=500, detail=str(e))
