"""
Analysis results display component for Yvynation Reflex app.
Shows MapBiomas, Hansen, and other analysis results.
"""

import reflex as rx
from ..state import AppState
from ..utils.translations import t


def analysis_results() -> rx.Component:
    """Display analysis results when available."""
    return rx.cond(
        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
        rx.vstack(
            # Header with clear button
            rx.hstack(
                rx.heading("📊 Analysis Results", size="2"),
                rx.spacer(),
                rx.button(
                    "✕ Clear",
                    on_click=lambda: AppState.set_analysis_results({}),
                    size="1",
                    color_scheme="gray",
                ),
                width="100%",
            ),
            rx.divider(),
            
            # Analysis type and metadata
            rx.hstack(
                rx.cond(
                    AppState.analysis_results.get("type") == "mapbiomas",
                    rx.vstack(
                        rx.text("🌿 MapBiomas Analysis", font_weight="bold", font_size="sm"),
                        rx.text(
                            f"Year: {AppState.analysis_results.get('year', 'N/A')}",
                            font_size="xs", color="gray"
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("🌲 Hansen Forest Analysis", font_weight="bold", font_size="sm"),
                        rx.text(
                            "2000-2023",
                            font_size="xs", color="gray"
                        ),
                        spacing="1",
                    ),
                ),
                rx.spacer(),
                rx.badge(
                    AppState.analysis_results.get('geometry', 'N/A'),
                    color_scheme="green",
                    variant="outline",
                ),
                width="100%",
            ),
            
            rx.divider(),
            
            # Summary statistics
            rx.box(
                rx.vstack(
                    rx.text("Summary Statistics", font_weight="bold", font_size="sm"),
                    rx.cond(
                        AppState.analysis_results.get("type") == "mapbiomas",
                        rx.vstack(
                            rx.hstack(
                                rx.text("Total Area:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    f"{AppState.analysis_results.get('summary', {}).get('total_area_ha', 0):,.0f} ha",
                                    font_size="xs"
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Classes Found:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    str(AppState.analysis_results.get('summary', {}).get('num_classes', 0)),
                                    font_size="xs"
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Top Class:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    AppState.analysis_results.get('summary', {}).get('top_class', 'N/A'),
                                    font_size="xs"
                                ),
                                width="100%",
                            ),
                            spacing="1",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.text("Tree Cover 2000:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    f"{AppState.analysis_results.get('summary', {}).get('total_tree_cover_2000_ha', 0):,.0f} ha",
                                    font_size="xs"
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Total Loss:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    f"{AppState.analysis_results.get('summary', {}).get('total_loss_ha', 0):,.0f} ha",
                                    font_size="xs", color="red"
                                ),
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Total Gain:", font_size="xs", font_weight="bold"),
                                rx.text(
                                    f"{AppState.analysis_results.get('summary', {}).get('total_gain_ha', 0):,.0f} ha",
                                    font_size="xs", color="green"
                                ),
                                width="100%",
                            ),
                            spacing="1",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),
                width="100%",
                padding="1rem",
                bg="blue.50",
                border_radius="md",
                border="1px solid #bee3f8",
            ),
            
            width="100%",
            spacing="2",
            padding="1rem",
            bg="white",
            border="1px solid #e0e0e0",
            border_radius="md",
        ),
        rx.vstack(
            rx.text(
                "👈 Select a territory and run analysis",
                font_size="sm",
                color="gray",
                text_align="center",
            ),
            rx.text(
                "Results will appear here when analysis completes",
                font_size="xs",
                color="gray",
                text_align="center",
            ),
            padding="2rem",
            width="100%",
            align="center",
        ),
    )
