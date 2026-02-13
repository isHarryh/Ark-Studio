# Copyright (c) 2024-2026, Harry Huang
# @ BSD 3-Clause License
from nicegui import ui

from ark_studio.ui.components.common import create_header, create_navigation


@ui.page("/")
def index_page():
    """Home page."""
    create_header()
    create_navigation()

    with ui.column().classes("w-full items-center justify-center q-pa-xl"):
        ui.label("Welcome to Ark Studio").classes("text-h3")
        ui.label("Select a feature from the navigation drawer").classes("text-subtitle1 text-grey-6")


def init():
    """Initializes UI pages.

    Import file page module to trigger page registration.
    """
    from ark_studio.ui.pages.files import index as files_page
