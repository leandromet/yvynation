"""
Geometry analysis page for Yvynation Reflex app.
Focused on drawing, uploading, and analyzing custom geometries.
"""

import reflex as rx
from ..state import AppState
from ..components.sidebar import sidebar
from ..components.geometry_sidebar import geometry_sidebar
from ..components.map import leaflet_map, map_metrics
from ..components.results_panel import results_panel
from ..components.export_panel import export_panel
from ..components.geometry_popup import geometry_info_popup
from ..components.tutorial import tutorial_section
from ..components.layer_reference import layer_reference_guide
from ..components.loading_indicator import loading_indicator
from .index import navbar, active_layers_summary, comparison_results_section, main_content_area, error_toast


def geometry_analysis() -> rx.Component:
    """Geometry analysis page layout."""
    return rx.vstack(
        navbar(),
        rx.hstack(
            # Geometry-focused sidebar
            rx.cond(
                AppState.sidebar_open,
                rx.box(
                    geometry_sidebar(),
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
