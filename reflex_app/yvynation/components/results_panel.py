"""
Phase 4: Results panel component - integrates analysis tabs with Plotly charts.
Includes multi-result navigation for switching between territory/geometry analyses.
"""

import reflex as rx
from ..state import AppState
from .analysis_tabs import analysis_tabs


def _result_nav_tabs() -> rx.Component:
    """Navigation bar for switching between multiple analysis results."""
    return rx.cond(
        AppState.result_keys_list.length() > 1,
        rx.hstack(
            rx.foreach(
                AppState.result_keys_list,
                lambda key: rx.button(
                    # Display label: extract name from "territory::Xingu" or "geometry::0"
                    rx.cond(
                        key.contains("territory"),
                        key.split("::")[1],
                        rx.cond(
                            key.contains("geometry"),
                            "Geom " + key.split("::")[1],
                            key,
                        ),
                    ),
                    on_click=AppState.switch_result(key),
                    size="1",
                    variant=rx.cond(AppState.active_result_key == key, "solid", "outline"),
                    color_scheme=rx.cond(key.contains("territory"), "green", "purple"),
                ),
            ),
            spacing="1",
            flex_wrap="wrap",
            padding="0.5rem",
            border_bottom="1px solid #e0e0e0",
            width="100%",
        ),
        rx.box(),
    )


def results_panel() -> rx.Component:
    """Main results panel with multi-result navigation and analysis tabs."""
    return rx.vstack(
        # Header with title and close button
        rx.hstack(
            rx.heading("Analysis Results", size="2"),
            rx.spacer(),
            rx.badge(
                AppState.analysis_results.get("geometry", ""),
                color_scheme="green",
                variant="outline",
            ),
            rx.button(
                "Close",
                on_click=lambda: AppState.set_analysis_results({}),
                size="1",
                color_scheme="gray",
                variant="soft",
            ),
            width="100%",
            align_items="center",
        ),
        # Multi-result navigation tabs
        _result_nav_tabs(),
        rx.divider(),
        # Analysis tabs (6 tabs: MapBiomas, Hansen, GFC, AAFC, Comparison, About)
        analysis_tabs(),
        width="100%",
        spacing="2",
        padding="1rem",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
    )
