"""
Territory analysis page for Yvynation Reflex app.
Focused on indigenous territories and lands analysis.
"""

import reflex as rx
from ..state import AppState
from ..components.territory_sidebar import territory_sidebar
from ..components.loading_indicator import loading_indicator
from .index import navbar, main_content_area, error_toast
from ..components.geometry_popup import geometry_info_popup


def territory_analysis() -> rx.Component:
    """Territory analysis page layout."""
    return rx.vstack(
        navbar(),
        rx.hstack(
            # Territory-focused sidebar
            rx.cond(
                AppState.sidebar_open,
                rx.box(
                    territory_sidebar(),
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
            # Main content area (reused from index)
            main_content_area(),
            width="100%",
            height="calc(100vh - 70px)",
            spacing="0",
        ),
        error_toast(AppState),
        loading_indicator(),
        geometry_info_popup(),
        width="100%",
        height="100vh",
        spacing="0",
    )
