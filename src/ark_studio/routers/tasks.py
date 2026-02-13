# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ark_studio.core.tasking import task_manager, TaskInfo
from ark_studio.utils.logger import logger


router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskInfoResponse(BaseModel):
    id: str
    title: str
    message: str
    progress: tuple[float, float] | None
    progress_percent: float | None
    running: bool
    completed: bool
    success: bool
    error: str | None


class TaskListResponse(BaseModel):
    tasks: list[TaskInfoResponse]
    total: int


def _to_task_info_response(info: TaskInfo) -> TaskInfoResponse:
    """Converts core task info to router response model."""
    return TaskInfoResponse(
        id=info.id,
        title=info.title,
        message=info.message,
        progress=info.progress,
        progress_percent=info.progress_percent,
        running=info.running,
        completed=info.completed,
        success=info.success,
        error=info.error,
    )


@router.get("/list")
async def list_tasks() -> TaskListResponse:
    """Lists all tasks with their current status."""
    try:
        task_infos = task_manager.get_all_task_info()

        return TaskListResponse(
            tasks=[_to_task_info_response(info) for info in task_infos],
            total=len(task_infos),
        )
    except Exception as e:
        logger.error(f"API: Failed to list tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: str) -> TaskInfoResponse:
    """Gets detailed information about a specific task."""
    try:
        info = task_manager.get_task_info(task_id)

        if not info:
            raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

        return _to_task_info_response(info)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
