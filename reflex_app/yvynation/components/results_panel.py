"""
Results panel component for displaying analysis results and charts.
Part of Phase 4: Visualization layer.
"""

import reflex as rx
from ..state import AppState
from ..utils.visualization import get_chart_for_analysis
import json


def results_table() -> rx.Component:
    """Display analysis results as a table."""
    return rx.cond(
        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
        rx.vstack(
            rx.heading("📋 Data Table", size="3"),
            rx.divider(),
            # Table wrapper
            rx.box(
                rx.vstack(
                    rx.text(
                        "Analysis Results Summary",
                        font_weight="bold",
                        font_size="sm",
                    ),
                    rx.text(
                        "Data values displayed in Summary tab",
                        font_size="xs",
                        color="gray",
                        font_style="italic",
                    ),
                    spacing="1",
                ),
                width="100%",
                padding="1rem",
                bg="blue.50",
                border_radius="md",
                border="1px solid #bee3f8",
            ),
            spacing="2",
            width="100%",
        ),
        rx.box(),
    )


def results_chart() -> rx.Component:
    """Display visualization chart for analysis results."""
    return rx.cond(
        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
        rx.vstack(
            rx.heading("📊 Visualization", size="3"),
            rx.divider(),
            rx.box(
                # This would need Plotly integration via rx.plotly()
                # For now, show a placeholder that explains what chart would be displayed
                rx.vstack(
                    rx.text(
                        rx.cond(
                            AppState.analysis_results.get("type") == "mapbiomas",
                            f"📈 MapBiomas {AppState.analysis_results.get('year', 'N/A')} - Land Cover Distribution",
                            "🌲 Hansen Forest Dynamics (2000-2023)"
                        ),
                        font_weight="bold",
                        font_size="sm",
                    ),
                    rx.text(
                        "Interactive chart visualization (Plotly)",
                        font_size="xs",
                        color="gray",
                        font_style="italic",
                    ),
                    spacing="1",
                    width="100%",
                    padding="2rem",
                    align="center",
                    bg="cyan.50",
                    border_radius="md",
                    border="1px solid #6dd5ed",
                ),
                width="100%",
                overflow_y="auto",
                max_height="400px",
            ),
            spacing="2",
            width="100%",
        ),
        rx.box(),
    )


def results_panel() -> rx.Component:
    """Main results panel with tabs for data, charts, and download."""
    return rx.vstack(
        # Header with title and close button
        rx.hstack(
            rx.heading("📊 Analysis Results", size="2"),
            rx.spacer(),
            rx.button(
                "✕",
                on_click=lambda: AppState.set_analysis_results({}),
                size="1",
                color_scheme="gray",
                variant="soft",
            ),
            width="100%",
            align_items="center",
        ),
        rx.divider(),
        
        # Simple results display
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Region:", font_weight="bold", min_width="120px"),
                    rx.text("Analysis complete"),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Type:", font_weight="bold", min_width="120px"),
                    rx.cond(
                        AppState.analysis_results.get("type") == "mapbiomas",
                        rx.text("🌿 MapBiomas Land Cover"),
                        rx.text("🌲 Hansen Forest Change"),
                    ),
                    width="100%",
                ),
                spacing="2",
                padding="1rem",
                width="100%",
            ),
            width="100%",
            bg="green.50",
            border_radius="md",
            border="1px solid #c6f6d5",
        ),
        
        rx.divider(),
        
        rx.text(
            "📈 Results visualization and detailed data available above",
            font_size="sm",
            color="gray",
            text_align="center",
            padding="1rem",
        ),
        
        width="100%",
        spacing="1",
        padding="1.5rem",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
    )
