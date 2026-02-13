# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from nicegui import ui

from ark_studio.core.files import workspace_manager
from ark_studio.core.tasking import task_manager
from ark_studio.utils.logger import logger


async def fetch_tasks():
    """Fetch task list from core task manager"""
    task_infos = task_manager.get_all_task_info()
    return [
        {
            "id": info.id,
            "title": info.title,
            "message": info.message,
            "progress": info.progress,
            "progress_percent": info.progress_percent,
            "running": info.running,
            "completed": info.completed,
            "success": info.success,
            "error": info.error,
            "eta": info.eta,
        }
        for info in task_infos
    ]


def create_header():
    """Create page header"""
    with ui.header().classes("items-center justify-between"):
        ui.label("Ark Studio").classes("text-h5 font-bold")

        with ui.row().classes("gap-4 items-center"):
            workspace_label = ui.label("No workspace opened").classes("text-subtitle2")

            async def open_workspace_dialog():
                """Open workspace dialog"""
                with ui.dialog() as dialog, ui.card():
                    ui.label("Open Workspace").classes("text-h6")
                    path_input = ui.input("Workspace Path", placeholder="Enter workspace path").classes("w-96")

                    with ui.row().classes("w-full justify-end gap-2 mt-4"):
                        ui.button("Cancel", on_click=dialog.close).props("flat")

                        async def confirm_open():
                            if not path_input.value:
                                ui.notify("Please enter workspace path", type="warning")
                                return

                            try:
                                workspace_manager.open_workspace(path_input.value)
                                workspace_label.set_text(f"Workspace: {workspace_manager.workspace_path}")
                                ui.notify("Workspace opened successfully", type="positive")
                                logger.info(f"UI: Workspace opened at {workspace_manager.workspace_path}")
                                dialog.close()
                            except Exception as e:
                                ui.notify(f"Failed to open: {str(e)}", type="negative")
                                logger.error(f"UI: Exception while opening workspace: {e}")

                        ui.button("Confirm", on_click=confirm_open).props("color=primary")

                dialog.open()

            ui.button("Open Workspace", on_click=open_workspace_dialog, icon="folder_open")

            # Check and display current workspace
            async def update_workspace_status():
                workspace_path = str(workspace_manager.workspace_path) if workspace_manager.workspace_path else None
                if workspace_path:
                    workspace_label.set_text(f"Workspace: {workspace_path}")

            ui.timer(0.1, update_workspace_status, once=True)


def create_navigation():
    """Create navigation drawer"""
    with ui.left_drawer(value=True).classes("bg-gray-100"):
        with ui.column().classes("w-full h-full no-wrap"):
            with ui.column().classes("w-full"):
                ui.label("Navigation").classes("text-h6 q-pa-sm")
                ui.separator()
                ui.button("Files", on_click=lambda: ui.navigate.to("/files"), icon="folder").props(
                    "flat align=left"
                ).classes("w-full")

            ui.space()
            ui.separator()

            # Tasks header with clear button
            with ui.row().classes("w-full items-center justify-between q-px-sm q-pt-sm"):
                ui.label("Tasks").classes("text-subtitle2")
                ui.button(icon="cleaning_services", on_click=task_manager.cleanup_completed_tasks).props(
                    "flat dense round size=sm"
                ).tooltip("Clear completed tasks")

            with ui.column().classes("w-full q-pa-sm gap-1").style("max-height: 35vh; overflow-y: auto") as task_panel:
                ui.label("No tasks").classes("text-caption text-grey-6")

            # Task UI state management
            task_ui_state = {}

            def _create_task_ui(task: dict):
                """Create task UI components and return references"""
                with ui.card().classes("w-full q-pa-xs") as card:
                    with ui.row().classes("w-full items-center justify-between"):
                        title_label = ui.label().classes("text-caption")
                        with ui.row().classes("gap-2 items-center"):
                            eta_label = ui.label().classes("text-caption text-grey-7")
                            percent_label = ui.label().classes("text-caption")

                    # Create two progress bars: one indeterminate, one normal
                    progress_bar_indeterminate = (
                        ui.linear_progress(value=0.0, show_value=False).props("indeterminate").classes("w-full")
                    )
                    progress_bar_normal = ui.linear_progress(value=0.0, show_value=False).classes("w-full")

                    with ui.row().classes("w-full text-caption text-grey-7"):
                        message_label = ui.label()

                components = {
                    "card": card,
                    "title": title_label,
                    "eta": eta_label,
                    "percent": percent_label,
                    "progress_bar_indeterminate": progress_bar_indeterminate,
                    "progress_bar_normal": progress_bar_normal,
                    "message": message_label,
                }

                _update_task_ui(task, components)
                return components

            def _update_task_ui(task: dict, ui_components: dict):
                """Update task UI component values"""
                ui_components["title"].set_text(task.get("title") or "Unnamed Task")

                # Update ETA display
                eta = task.get("eta")
                if eta is not None and eta > 0:
                    minutes = int(eta // 60)
                    seconds = int(eta % 60)
                    ui_components["eta"].set_text(f"ETA {minutes}:{seconds:02d}")
                else:
                    ui_components["eta"].set_text("")

                # Update progress percent (now in 0.0~1.0 range, display as percentage)
                progress_percent = task.get("progress_percent")
                if progress_percent is not None:
                    ui_components["percent"].set_text(f"{progress_percent*100:.1f}%")
                else:
                    ui_components["percent"].set_text("")

                progress = task.get("progress")
                if progress is None:
                    ui_components["progress_bar_indeterminate"].visible = True
                    ui_components["progress_bar_normal"].visible = False
                else:
                    ui_components["progress_bar_indeterminate"].visible = False
                    ui_components["progress_bar_normal"].visible = True
                    done, total = progress
                    value = (done / total) if total > 0 else 0.0
                    ui_components["progress_bar_normal"].set_value(value)

                message = task.get("message")
                done, total = progress if progress is not None else (None, None)
                if total is not None and total != 1.0:
                    msg_text = f"({done:.0f}/{total:.0f})" + (f" {message}" if message else "")
                elif message:
                    msg_text = message
                else:
                    msg_text = ""
                ui_components["message"].set_text(msg_text)

            async def refresh_tasks():
                try:
                    tasks = await fetch_tasks()

                    current_task_ids = {task["id"] for task in tasks}
                    existing_task_ids = set(task_ui_state.keys())

                    # Remove tasks that no longer exist
                    for task_id in existing_task_ids - current_task_ids:
                        ui_components = task_ui_state.pop(task_id)
                        ui_components["card"].delete()

                    # Clear placeholder when first task appears
                    if tasks and not existing_task_ids:
                        task_panel.clear()

                    # Update or create task UIs
                    for task in tasks:
                        task_id = task["id"]
                        if task_id in task_ui_state:
                            # Update existing UI
                            _update_task_ui(task, task_ui_state[task_id])
                        else:
                            # Create new UI
                            with task_panel:
                                task_ui_state[task_id] = _create_task_ui(task)

                    # Show placeholder when all tasks are gone
                    if not tasks and existing_task_ids:
                        with task_panel:
                            ui.label("No tasks").classes("text-caption text-grey-6")
                finally:
                    ui.timer(0.5, refresh_tasks, once=True)

            ui.timer(0.1, refresh_tasks, once=True)
