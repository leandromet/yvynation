"""
Main application layout and routing for Yvynation Reflex app.
"""

import reflex as rx
from ..state import AppState
from ..components.sidebar import sidebar
from ..components.map import leaflet_map, map_metrics
from ..components.analysis_results import analysis_results
from ..components.results_panel import results_panel
from ..components.geometry_popup import geometry_info_popup
from ..utils.translations import t


def navbar() -> rx.Component:
    """Modern top navigation bar."""
    return rx.hstack(
        # Left side - toggle & branding
        rx.hstack(
            rx.vstack(
                rx.button(
                    rx.cond(
                        AppState.sidebar_open,
                        "☰ Hide",
                        "☰ Show",
                    ),
                    on_click=AppState.toggle_sidebar,
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                ),
                # Sidebar resize preset buttons
                rx.cond(
                    AppState.sidebar_open,
                    rx.hstack(
                        rx.button(
                            "◀",
                            on_click=lambda: AppState.update_sidebar_width(200),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Narrow",
                        ),
                        rx.button(
                            "resize",
                            on_click=lambda: AppState.update_sidebar_width(300),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Normal",
                        ),
                        rx.button(
                            "▶",
                            on_click=lambda: AppState.update_sidebar_width(600),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Wide",
                        ),
                        spacing="1",
                        font_size="xs",
                    ),
                    rx.box(),
                ),
                spacing="1",
                padding="0",
                margin="0",
            ),
            rx.vstack(
                rx.heading("🏞️ Yvynation", size="3"),
                rx.text(
                    "Indigenous Land Monitoring",
                    font_size="xs",
                    color="gray",
                ),
                spacing="0",
                margin="0",
            ),
            width="auto",
            align_items="center",
            spacing="2",
        ),
        # Center - empty spacer
        rx.spacer(),
        # Right side - info
        rx.hstack(
            rx.text(
                "🌍 Global Forest Monitoring Platform",
                font_size="sm",
                color="gray",
                display=rx.cond(AppState.sidebar_open, "block", "none"),
            ),
            align_items="center",
            spacing="3",
        ),
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%)",
        border_bottom="2px solid #e8f0e8",
        align_items="center",
        width="100%",
        height="70px",
        position="sticky",
        top="0",
        z_index="100",
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
    """Main application layout with modern design."""
    return rx.vstack(
        navbar(),
        rx.cond(
            AppState.data_loaded,
            rx.hstack(
                # Sidebar (collapsible and resizable)
                rx.cond(
                    AppState.sidebar_open,
                    rx.box(
                        sidebar(),
                        width=rx.cond(
                            AppState.sidebar_width != 0,
                            f"{AppState.sidebar_width}px",
                            "300px",
                        ),
                        max_width="500px",
                        min_width="200px",
                        overflow_y="auto",
                        overflow_x="hidden",
                        border_right="2px solid #d0d0d0",
                        bg="white",
                        position="relative",
                    ),
                    rx.box(),
                ),
                # Main content area
                rx.vstack(
                    # Stats/Metrics
                    rx.box(
                        map_metrics(),
                        padding="1rem",
                        width="100%",
                        border_bottom="1px solid #e0e0e0",
                    ),
                    
                    # Map and Results area (stacked vertically)
                    rx.cond(
                        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                        # Vertical layout: map on top, results below
                        rx.vstack(
                            # Map
                            rx.box(
                                leaflet_map(),
                                width="100%",
                                height="600px",
                                overflow_y="auto",
                                overflow_x="hidden",
                                border_bottom="1px solid #e0e0e0",
                            ),
                            # Results panel
                            rx.box(
                                results_panel(),
                                width="100%",
                                flex="1",
                                overflow_y="auto",
                                overflow_x="hidden",
                            ),
                            width="100%",
                            flex="1",
                            spacing="0",
                        ),
                        # Map only
                        rx.box(
                            leaflet_map(),
                            width="100%",
                            flex="1",
                            overflow_y="auto",
                            overflow_x="hidden",
                        ),
                    ),
                    
                    width="100%",
                    height="100%",
                    spacing="0",
                    overflow="hidden",
                ),
                
                width="100%",
                height="calc(100vh - 70px)",
                spacing="0",
            ),
            # Loading state
            rx.vstack(
                rx.spinner(color="green", size="3"),
                rx.text("Initializing Yvynation Platform..."),
                align_items="center",
                justify_content="center",
                height="calc(100vh - 70px)",
                spacing="4",
            ),
        ),
        error_toast(AppState),
        loading_overlay(AppState),
        geometry_info_popup(),
        width="100%",
        height="100vh",
        spacing="0",
    )


      

