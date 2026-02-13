# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from nicegui import ui

from ark_studio.core.files import workspace_manager
from ark_studio.core.tasking import task_manager
from ark_studio.exceptions import TaskConflictError
from ark_studio.persist.workspace import BuildFileIndexParam, BuildFileIndexTask
from ark_studio.utils.logger import logger
from ark_studio.utils.repr import format_size


async def fetch_files(path: str = "", page: int = 1, page_size: int = 20):
    """Fetch file list from core with pagination"""
    try:
        actual_page_size = page_size if page_size > 0 else 1000000
        offset = (page - 1) * actual_page_size
        files, total = workspace_manager.list_files(path, offset, actual_page_size)
        return [
            {
                "name": f.name,
                "path": f.path,
                "size": f.size,
                "is_directory": f.is_directory,
                "parent": f.parent,
                "children_count": f.children_count,
            }
            for f in files
        ], total
    except Exception as e:
        logger.error(f"UI: Exception while fetching files: {e}")
        return [], 0


async def search_files(query: str = "", field: str = "path", page: int = 1, page_size: int = 20):
    """Search files from core with pagination"""
    try:
        actual_page_size = page_size if page_size > 0 else 1000000
        offset = (page - 1) * actual_page_size
        files, total = workspace_manager.search_files(query, field, offset, actual_page_size)
        return [
            {
                "name": f.name,
                "path": f.path,
                "size": f.size,
                "is_directory": f.is_directory,
                "parent": f.parent,
                "children_count": f.children_count,
            }
            for f in files
        ], total
    except Exception as e:
        logger.error(f"UI: Exception while searching files: {e}")
        return [], 0


async def fetch_file_tree(path: str = ""):
    """Fetch a single layer of the file tree from core"""
    try:
        trees = workspace_manager.get_file_tree(path)
        return [
            {
                "name": t.name,
                "path": t.path,
                "subtree": bool(t.subtree),
                "children_count": t.children_count,
            }
            for t in trees
        ]
    except Exception as e:
        logger.error(f"UI: Exception while fetching file tree: {e}")
        return []


async def build_file_index():
    """Start file index build task via core task manager"""
    try:
        if not workspace_manager.workspace_path:
            return None, "No workspace opened"

        task = BuildFileIndexTask()
        data = BuildFileIndexParam(workspace_path=workspace_manager.workspace_path)
        task_id = await task_manager.start_task(task, data)
        return task_id, None
    except TaskConflictError as e:
        return None, str(e)
    except Exception as e:
        logger.error(f"UI: Exception while starting file index build: {e}")
        return None, str(e)


async def get_task_status(task_id: str):
    """Get task status from core task manager"""
    try:
        info = task_manager.get_task_info(task_id)
        if not info:
            return None
        return {
            "id": info.id,
            "title": info.title,
            "message": info.message,
            "progress": info.progress,
            "progress_percent": info.progress_percent,
            "running": info.running,
            "completed": info.completed,
            "success": info.success,
            "error": info.error,
        }
    except Exception as e:
        logger.error(f"UI: Exception while getting task status: {e}")
        return None


@ui.page("/files")
async def files_page():
    """File browser page with pagination and lazy loading tree"""
    from ark_studio.ui.components.common import create_header, create_navigation

    create_header()
    create_navigation()

    # State variables
    state = {
        "path": "",
        "page": 1,
        "page_size": 20,
        "selected_file": None,
        "search_query": "",
        "search_field": "path",  # 'name' or 'path'
        "search_mode": False,  # False: tree mode, True: search mode
    }

    workspace_path = workspace_manager.workspace_path

    if not workspace_path:
        with ui.column().classes("w-full items-center justify-center q-pa-xl"):
            ui.label("No workspace opened").classes("text-h4 text-grey-6")
            ui.label("Click 'Open Workspace' button in the top-right and refresh").classes("text-subtitle1 text-grey-7")
        return

    # Build file index dialog
    with ui.dialog() as build_dialog, ui.card().classes("q-pa-md"):
        ui.label("Building File Index").classes("text-h6 q-mb-md")
        build_progress_bar = ui.linear_progress(value=0.0, show_value=False).classes("q-mb-sm")
        build_status = ui.label("Starting...").classes("text-body2")
        ui.button("Hide", on_click=lambda: build_dialog.close()).props("flat")

    async def do_build_index():
        """Build file index and show progress"""
        import asyncio

        # Start task
        task_id, error = await build_file_index()
        if error:
            ui.notify(f"Failed to start task: {error}", type="negative")
            return
        if not task_id:
            ui.notify("Failed to start file index build", type="negative")
            return

        # Show dialog
        build_dialog.open()

        # Poll task status
        while True:
            await asyncio.sleep(0.5)

            status = await get_task_status(task_id)
            if not status:
                build_status.set_text("Failed to get task status")
                break

            # Update progress
            if status.get("progress_percent") is not None:
                progress_pct = status["progress_percent"]
                build_progress_bar.set_value(progress_pct)
                build_progress_bar.props.pop("indeterminate", None)
            else:
                build_progress_bar.props("indeterminate")

            # Update message
            message = status.get("message", "Running...")
            build_status.set_text(message)

            # Check if completed
            if status.get("completed"):
                if status.get("success"):
                    ui.notify("File index built successfully", type="positive")
                    build_status.set_text("Completed successfully")
                    await update_table()
                else:
                    error_msg = status.get("error", "Unknown error")
                    ui.notify(f"Failed to build file index: {error_msg}", type="negative")
                    build_status.set_text(f"Failed: {error_msg}")
                break

    # Main container - use absolute positioning to fill the entire page container
    # The page container (q-page) already excludes header, so we fill it completely
    with (
        ui.element("div")
        .classes("column no-wrap")
        .style(
            """
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 8px 16px;
        gap: 8px;
        display: flex;
        flex-direction: column;
    """
        )
    ):

        # Build index button row (fixed height, reduced padding)
        with ui.row().classes("w-full items-center shrink-0").style("margin: 4px 0"):
            ui.button("Build File Index", on_click=do_build_index, icon="refresh").props("color=primary")
            ui.label("Click to scan workspace and build file index in database").classes("text-caption text-grey-7")

        async def update_table():
            """Update the file table based on current state"""
            if state["search_mode"]:
                # Search mode
                files, total = await search_files(
                    state["search_query"], state["search_field"], state["page"], state["page_size"]
                )
            else:
                # Tree mode
                files, total = await fetch_files(state["path"], state["page"], state["page_size"])

            new_rows = [
                {
                    "name": f["name"],
                    "type": "Folder" if f["is_directory"] else "File",
                    "size": f["size"],
                    "size_formatted": format_size(f["size"]) if not f["is_directory"] else "-",
                    "items": f["children_count"] if f["is_directory"] else "-",
                    "path": f["path"],
                    "is_directory": f["is_directory"],
                }
                for f in files
            ]

            table.rows = new_rows
            table.pagination["rowsNumber"] = total
            table.pagination["page"] = state["page"]
            table.pagination["rowsPerPage"] = state["page_size"]
            table.update()

            if state["search_mode"]:
                current_path_label.set_text(f"Search ({state['search_field']}): {state['search_query']}")
                back_button.set_enabled(False)
            else:
                current_path_label.set_text(f"Current: /{state['path']}" if state["path"] else "Current: /")
                back_button.set_enabled(bool(state["path"]))

        async def load_folder(path: str):
            """Change current directory and reload table"""
            state["path"] = path
            state["page"] = 1
            state["search_mode"] = False
            await update_table()

        async def do_search(query: str):
            """Perform search and update table"""
            state["search_query"] = query
            state["page"] = 1
            state["search_mode"] = True
            await update_table()

        # Layout Splitter with flex-grow to fill remaining vertical space
        with ui.splitter(value=25).classes("w-full").style("flex: 1 1 auto; min-height: 0") as splitter:
            with splitter.before:
                # Tabs for Tree and Search
                with ui.tabs().classes("w-full") as tabs:
                    tree_tab = ui.tab("Tree", icon="folder_open")
                    search_tab = ui.tab("Search", icon="search")

                with ui.tab_panels(tabs, value=tree_tab).classes("w-full h-full").style("overflow-y: auto"):
                    # Tree Tab Panel
                    with ui.tab_panel(tree_tab):

                        def map_node(info: dict):
                            node = {"id": info["path"], "label": info["name"]}
                            if info.get("subtree") is True:
                                node["lazy"] = True  # Quasar lazy load indicator
                            return node

                        root_dirs = await fetch_file_tree("")
                        tree_nodes = [{"id": "", "label": "/", "children": [map_node(d) for d in root_dirs]}]

                        async def handle_lazy_load(e):
                            # e.args = {'node': {...}, 'key': '...'}
                            args = e.args if isinstance(e.args, dict) else {}
                            node_to_load = args.get("node")
                            if not node_to_load:
                                return

                            node_id = node_to_load.get("id", "")
                            logger.debug(f"UI: Lazy-load event for node: {node_id}")

                            def find_node_by_id(nodes, target_id):
                                # Find real reference node
                                for n in nodes:
                                    if n.get("id") == target_id:
                                        return n
                                    if "children" in n and n["children"]:
                                        result = find_node_by_id(n["children"], target_id)
                                        if result:
                                            return result
                                return None

                            real_node = find_node_by_id(tree._props["nodes"], node_id)
                            if not real_node:
                                logger.warning(f"UI: Could not find node {node_id} in tree")
                                return

                            logger.debug(f"UI: Loading children for: {node_id}")
                            sub_dirs = await fetch_file_tree(node_id)
                            real_node["children"] = [map_node(d) for d in sub_dirs]
                            real_node["lazy"] = False

                            tree.expand([node_id])
                            tree.update()

                        tree = (
                            ui.tree(
                                tree_nodes,
                                label_key="label",
                                on_select=lambda e: load_folder(e.value or ""),
                            )
                            .classes("w-full")
                            .props("dense")
                        )

                        tree.expand([""])  # Expand root by default
                        tree.on("lazy-load", handle_lazy_load)

                    # Search Tab Panel
                    with ui.tab_panel(search_tab):
                        ui.label("Search Files").classes("text-subtitle2 q-mb-md")

                        # Search by field selector with badges
                        with ui.row().classes("items-center gap-2 q-mb-sm"):
                            ui.label("Search by:").classes("text-caption")

                            name_badge = ui.badge(
                                "Name",
                                color="grey" if state["search_field"] != "name" else "primary",
                            ).classes("cursor-pointer")

                            path_badge = ui.badge(
                                "Path",
                                color="grey" if state["search_field"] != "path" else "primary",
                            ).classes("cursor-pointer")

                            def select_field(field: str):
                                state["search_field"] = field
                                name_badge.props(f"color={'primary' if field == 'name' else 'grey'}")
                                path_badge.props(f"color={'primary' if field == 'path' else 'grey'}")

                            name_badge.on("click", lambda: select_field("name"))
                            path_badge.on("click", lambda: select_field("path"))

                        search_input = ui.input(
                            label="Search Pattern",
                            placeholder="Enter search pattern...",
                        ).classes("w-full")

                        search_button = (
                            ui.button(
                                "Search",
                                icon="search",
                                on_click=lambda: do_search(search_input.value),
                            )
                            .props("color=primary")
                            .classes("w-full q-mt-sm")
                        )

                        # Add Enter key support
                        search_input.on("keydown.enter", lambda: do_search(search_input.value))

            with splitter.after:
                # Right panel: fills height with flex column
                with ui.column().classes("w-full h-full gap-1 no-wrap").style("min-height: 0"):
                    # Navigation row
                    with ui.row().classes("w-full items-center gap-2 shrink-0").style("padding: 4px 12px"):
                        back_button = (
                            ui.button(
                                icon="arrow_upward",
                                on_click=lambda: load_folder(
                                    "/".join(state["path"].split("/")[:-1]) if "/" in state["path"] else ""
                                ),
                            )
                            .props("flat dense")
                            .classes("q-mr-sm")
                        )
                        current_path_label = ui.label("Current: /").classes("text-subtitle2 text-grey-7")

                    # Table container (grows to fill available space)
                    with (
                        ui.column()
                        .classes("w-full")
                        .style("flex: 1 1 auto; min-height: 0; overflow: hidden; padding: 0 12px")
                    ):
                        columns = [
                            {
                                "name": "name",
                                "label": "Name",
                                "field": "name",
                                "required": True,
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "type",
                                "label": "Type",
                                "field": "type",
                                "align": "left",
                                "sortable": True,
                            },
                            {
                                "name": "items",
                                "label": "Items",
                                "field": "items",
                                "align": "right",
                                "sortable": True,
                            },
                            {
                                "name": "size",
                                "label": "Size",
                                "field": "size_formatted",
                                "align": "right",
                                "sortable": True,
                            },
                        ]

                        def on_table_select(selection: list[dict] | None):
                            if selection:
                                file_info = selection[0]
                                state["selected_file"] = file_info

                                # Update file info panel
                                info_icon.set_name("folder" if file_info["is_directory"] else "description")
                                file_name_label.set_text(file_info["name"])
                                file_path_label.set_text(f"Path: {file_info['path']}")
                                file_type_label.set_text(f"Type: {file_info['type']}")

                                # Display size or item count
                                if file_info["is_directory"]:
                                    size_text = (
                                        f"Items: {file_info['items']}" if file_info["items"] != "-" else "Items: 0"
                                    )
                                else:
                                    size_text = f"Size: {file_info['size_formatted']}"
                                file_size_label.set_text(size_text)
                            else:
                                # Clear selection
                                state["selected_file"] = None
                                info_icon.set_name("info")
                                file_name_label.set_text("No selection")
                                file_path_label.set_text("Select a file or folder to view details")
                                file_type_label.set_text("Type: None")
                                file_size_label.set_text("")

                        # File table
                        table = (
                            ui.table(
                                columns=columns,
                                rows=[],
                                row_key="name",
                                pagination={"rowsPerPage": 20, "rowsNumber": 0, "page": 1},
                                selection="single",
                                on_select=lambda e: on_table_select(e.selection),
                            )
                            .classes("w-full h-full")
                            .props("dense flat")
                        )

                        def on_row_click(e):
                            if e.args and len(e.args) >= 2:
                                row_data = e.args[1]
                                table.selected = [row_data]
                                table.update()
                                on_table_select([row_data])

                        table.on("row-click", on_row_click)

                        async def on_row_dblclick(e):
                            if e.args and len(e.args) >= 2:
                                if e.args[1]["is_directory"]:
                                    await load_folder(e.args[1]["path"])

                        table.on("rowDblclick", on_row_dblclick)

                        async def on_table_request(e):
                            state["page"] = e.args["pagination"]["page"]
                            state["page_size"] = e.args["pagination"]["rowsPerPage"]
                            await update_table()

                        table.on("request", on_table_request)

        # File info panel (fixed at bottom, reduced padding)
        with (
            ui.row()
            .classes("w-full border bg-blue-grey-1 items-center no-wrap shrink-0")
            .props("flat bordered")
            .style("padding: 8px 12px")
        ):
            info_icon = ui.icon("info", color="grey-6").classes("text-4xl q-pa-sm")
            with ui.column().classes("gap-1 grow"):
                file_name_label = ui.label().classes("font-bold")
                file_path_label = ui.label().classes("text-caption text-grey-7")
                with ui.row().classes("gap-4"):
                    file_type_label = ui.label().classes("text-body2")
                    file_size_label = ui.label().classes("text-body2")

        # Initial load
        on_table_select(None)
        await update_table()
