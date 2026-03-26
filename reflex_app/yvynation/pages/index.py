"""
Main application layout and routing for Yvynation Reflex app.
"""

import reflex as rx
from ..state import AppState
from ..components.sidebar import sidebar
from ..components.map import leaflet_map, map_metrics
from ..components.analysis import analysis_content
from ..utils.translations import t


def navbar() -> rx.Component:
    """Top navigation bar."""
    return rx.hstack(
        rx.hstack(
            rx.image(
                src="/logo.png",
                height="2.5rem",
            ),
            rx.vstack(
                rx.heading("🏞️ Yvynation", size="3"),
                rx.text(
                    "Indigenous Land Monitoring Platform",
                    font_size="xs",
                    color="gray",
                ),
            ),
            width="auto",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                rx.cond(
                    AppState.sidebar_open,
                    "◀ Hide Sidebar",
                    "▶ Show Sidebar",
                ),
                on_click=AppState.toggle_sidebar,
                size="1",
                variant="outline",
            ),
            padding="0.5rem",
        ),
        padding="1rem 2rem",
        bg="white",
        border_bottom="1px solid #e0e0e0",
        align_items="center",
        width="100%",
    )


def tutorial_view() -> rx.Component:
    """Tutorial/Getting started view."""
    return rx.vstack(
        rx.heading("🚀 Getting Started", size="2"),
        rx.divider(),
        rx.vstack(
            rx.heading("How to use Yvynation", size="3"),
            rx.ordered_list(
                rx.list_item("Select a language in the sidebar"),
                rx.list_item("Choose layers (MapBiomas, Hansen, etc.)"),
                rx.list_item("Click on a territory on the map or draw your own area"),
                rx.list_item("Run analysis to see land cover changes"),
                rx.list_item("Export results as PDF or data files"),
            ),
            rx.divider(),
            rx.heading("Available Datasets", size="4"),
            rx.unordered_list(
                rx.list_item(
                    rx.vstack(
                        rx.text("🌿 MapBiomas (1985-2023)"),
                        rx.text(
                            "Land cover classification for all of South America",
                            font_size="1",
                            color="gray",
                        ),
                    )
                ),
                rx.list_item(
                    rx.vstack(
                        rx.text("🌲 Hansen Global Forest Change (2000-2023)"),
                        rx.text(
                            "Global forest cover loss and gain",
                            font_size="1",
                            color="gray",
                        ),
                    )
                ),
            ),
        ),
        width="100%",
        max_width="800px",
        padding="2rem",
        margin="auto",
        spacing="6",
    )


def error_toast(state: AppState) -> rx.Component:
    """Display error messages."""
    return rx.cond(
        state.error_message != "",
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("alert-circle", color="red"),
                    rx.text(state.error_message),
                    width="100%",
                ),
                rx.button(
                    "Dismiss",
                    size="1",
                    on_click=state.clear_error,
                ),
                width="100%",
            ),
            padding="1rem",
            bg="red.50",
            border="1px solid red",
            border_radius="md",
            position="fixed",
            bottom="1rem",
            right="1rem",
            z_index="9999",
            max_width="400px",
        ),
        rx.box(),
    )


def loading_overlay(state: AppState) -> rx.Component:
    """Display loading overlay."""
    return rx.cond(
        state.loading_message != "",
        rx.box(
            rx.vstack(
                rx.spinner(color="green", size="3"),
                rx.text(state.loading_message),
                align_items="center",
                justify_content="center",
                height="100vh",
                width="100%",
            ),
            position="fixed",
            top="0",
            left="0",
            width="100%",
            height="100vh",
            bg="rgba(0,0,0,0.5)",
            z_index="10000",
        ),
        rx.box(),
    )


def index() -> rx.Component:
    """Main application layout."""
    return rx.vstack(
        navbar(),
        rx.cond(
            AppState.data_loaded,
            rx.hstack(
                # Sidebar
                rx.cond(
                    AppState.sidebar_open,
                    rx.box(
                        sidebar(),
                        width="25%",
                        height="calc(100vh - 70px)",
                        overflow_y="auto",
                    ),
                    rx.box(),
                ),
                # Main content
                rx.vstack(
                    map_metrics(),
                    leaflet_map(),
                    width="100%",
                    height="calc(100vh - 70px)",
                    overflow_y="auto",
                    padding="1rem",
                ),
                width="100%",
                height="100%",
                spacing="0",
            ),
            rx.vstack(
                rx.spinner(color="green", size="3"),
                rx.text("Loading Yvynation Platform..."),
                align_items="center",
                justify_content="center",
                height="100vh",
            ),
        ),
        error_toast(AppState),  # type: ignore
        loading_overlay(AppState),  # type: ignore
        width="100%",
        height="100vh",
        spacing="0",
    )
