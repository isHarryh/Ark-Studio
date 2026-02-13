# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from nicegui import ui

from ark_studio.routers import files, persist, tasks
from ark_studio.exceptions import TaskConflictError
from ark_studio.ui import index as ui_index
from ark_studio.utils.logger import logger


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("FastAPI application startup")
    yield
    logger.info("FastAPI application shutdown")


def init_app():
    """Initializes the application instance."""
    logger.info("Initializing Ark Studio application")

    # Create FastAPI app
    app = FastAPI(lifespan=lifespan, title="Ark Studio API")

    # Register exception handlers
    @app.exception_handler(TaskConflictError)
    async def task_conflict_handler(request: Request, exc: TaskConflictError):
        logger.warning(f"Task conflict: {exc}")
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc)},
        )

    logger.debug("Registered exception handlers")

    # Register FastAPI routes
    app.include_router(files.router)
    app.include_router(persist.router)
    app.include_router(tasks.router)
    logger.debug("Registered API routes")

    # Initialize UI (imports pages)
    ui_index.init()
    logger.debug("Initialized UI")

    return app


app = init_app()

ui.run_with(app, title="Ark Studio", favicon="🔧", mount_path="/ui")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
