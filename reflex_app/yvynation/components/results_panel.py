"""
Phase 4: Results panel component - integrates analysis tabs with Plotly charts.
Replaces the previous placeholder with real interactive visualizations.
"""

import reflex as rx
from ..state import AppState
from .analysis_tabs import analysis_tabs


def results_panel() -> rx.Component:
    """Main results panel with analysis tabs, charts, and data tables."""
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
