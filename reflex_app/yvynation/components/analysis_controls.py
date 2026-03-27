"""
Analysis controls section - shows analysis buttons for drawn/selected geometry.
"""

import reflex as rx
from ..state import AppState


def analysis_controls() -> rx.Component:
    """Analysis controls for drawn/selected geometry."""
    return rx.vstack(
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.text(
                    f"Selected: {AppState.selected_territory}",
                    font_weight="bold",
                    font_size="sm",
                ),
                
                rx.divider(),
                
                rx.text(
                    "Analyze against active layers:",
                    font_size="xs",
                    color="gray",
                ),
                
                # MapBiomas analysis
                rx.cond(
                    AppState.mapbiomas_displayed_years.length() > 0,
                    rx.cond(
                        AppState.mapbiomas_analysis_pending,
                        rx.button(
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Analyzing MapBiomas..."),
                                spacing="2",
                            ),
                            is_disabled=True,
                            width="100%",
                            color_scheme="blue",
                            size="1",
                        ),
                        rx.button(
                            "📊 Analyze MapBiomas",
                            on_click=AppState.run_mapbiomas_analysis_on_geometry,
                            width="100%",
                            color_scheme="green",
                            size="1",
                        ),
                    ),
                    rx.text(
                        "Add a MapBiomas layer first",
                        font_size="xs",
                        color="gray",
                        font_style="italic",
                    ),
                ),
                
                # Hansen analysis
                rx.cond(
                    AppState.hansen_displayed_layers.length() > 0,
                    rx.cond(
                        AppState.hansen_analysis_pending,
                        rx.button(
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Analyzing Hansen..."),
                                spacing="2",
                            ),
                            is_disabled=True,
                            width="100%",
                            color_scheme="blue",
                            size="1",
                        ),
                        rx.button(
                            "🌲 Analyze Hansen",
                            on_click=AppState.run_hansen_analysis_on_geometry,
                            width="100%",
                            color_scheme="green",
                            size="1",
                        ),
                    ),
                    rx.text(
                        "Add a Hansen layer first",
                        font_size="xs",
                        color="gray",
                        font_style="italic",
                    ),
                ),
                
                spacing="2",
                width="100%",
            ),
            rx.text(
                "👇 Draw or select a geometry to analyze",
                font_size="xs",
                color="gray",
                text_align="center",
                padding="1rem",
            ),
        ),
        spacing="2",
        width="100%",
    )
