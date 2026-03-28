"""
Analysis controls section - shows analysis buttons for drawn/selected geometry.
"""

import reflex as rx
from ..state import AppState


def analysis_controls() -> rx.Component:
    """Analysis controls for drawn/selected geometry."""
    has_geometry = AppState.selected_geometry_idx != None

    return rx.vstack(
        rx.cond(
            has_geometry,
            rx.vstack(
                # Full analysis button (MapBiomas comparison + change mask)
                rx.cond(
                    AppState.mapbiomas_analysis_pending,
                    rx.button(
                        rx.hstack(rx.spinner(size="1"), rx.text("Analyzing..."), spacing="2"),
                        is_disabled=True,
                        width="100%",
                        color_scheme="purple",
                        size="1",
                    ),
                    rx.button(
                        "Analyze Custom Geometry",
                        on_click=AppState.run_full_analysis_on_geometry,
                        width="100%",
                        color_scheme="purple",
                        size="1",
                    ),
                ),
                rx.text(
                    "Runs MapBiomas comparison + change mask",
                    font_size="10px", color="gray",
                ),
                rx.divider(),
                # Individual analysis buttons
                rx.text("Individual layers:", font_size="xs", color="gray"),
                rx.hstack(
                    rx.button(
                        "MapBiomas",
                        on_click=AppState.run_mapbiomas_analysis_on_geometry,
                        size="1",
                        color_scheme="green",
                        flex="1",
                    ),
                    rx.button(
                        "Hansen",
                        on_click=AppState.run_hansen_analysis_on_geometry,
                        size="1",
                        color_scheme="blue",
                        flex="1",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="2",
                width="100%",
            ),
            rx.text(
                "Select a geometry above to analyze",
                font_size="xs",
                color="gray",
                text_align="center",
                padding="0.5rem",
            ),
        ),
        spacing="2",
        width="100%",
    )
