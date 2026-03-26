"""
Analysis tabs component for Yvynation Reflex app.
Handles territory analysis and visualization.
"""

import reflex as rx
from ..state import AppState
from ..utils.translations import t


def mapbiomas_analysis_tab() -> rx.Component:
    """MapBiomas analysis tab content."""
    return rx.vstack(
        rx.heading("MapBiomas Land Cover Analysis", size="3"),
        rx.text(
            "Analyze land cover changes from 1985-2023",
            font_size="1",
            color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.badge(f"Territory: {AppState.selected_territory}", color_scheme="green"),
                rx.select(
                    items=["1985", "1990", "1995", "2000", "2005", "2010", "2015", "2020", "2023"],
                    value="2023",
                    placeholder="Select year",
                    size="1",
                ),
                rx.button(
                    "▶️ Run Analysis",
                    on_click=lambda: AppState.set_loading("Analyzing MapBiomas data..."),
                    width="100%",
                    color_scheme="green",
                ),
                rx.divider(),
                rx.text(
                    "Results will appear here...",
                    font_size="1",
                    color="gray",
                    font_style="italic",
                ),
                width="100%",
            ),
            rx.box(
                rx.text(
                    "Please select a territory first",
                    text_align="center",
                    color="gray",
                ),
                padding="2rem",
                bg="gray.50",
                border_radius="md",
                width="100%",
            ),
        ),
        width="100%",
        spacing="4",
    )


def hansen_analysis_tab() -> rx.Component:
    """Hansen Global Forest Change analysis tab content."""
    return rx.vstack(
        rx.heading("Hansen Global Forest Change Analysis", size="3"),
        rx.text(
            "Analyze forest cover loss and gain since 2000",
            font_size="1",
            color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.badge(f"Territory: {AppState.selected_territory}", color_scheme="green"),
                rx.select(
                    items=["2000", "2010", "2015", "2020"],
                    value="2020",
                    placeholder="Select year",
                    size="1",
                ),
                rx.hstack(
                    rx.checkbox(
                        "Use consolidated classes",
                        is_checked=AppState.use_consolidated_classes,
                        on_change=AppState.toggle_consolidated_classes,
                    ),
                    width="100%",
                ),
                rx.button(
                    "▶️ Run Analysis",
                    on_click=lambda: AppState.set_loading("Analyzing Hansen data..."),
                    width="100%",
                    color_scheme="green",
                ),
                rx.divider(),
                rx.text(
                    "Results will appear here...",
                    font_size="1",
                    color="gray",
                    font_style="italic",
                ),
                width="100%",
            ),
            rx.box(
                rx.text(
                    "Please select a territory first",
                    text_align="center",
                    color="gray",
                ),
                padding="2rem",
                bg="gray.50",
                border_radius="md",
                width="100%",
            ),
        ),
        width="100%",
        spacing="4",
    )


def buffer_analysis_tab() -> rx.Component:
    """Buffer and custom geometry analysis tab."""
    return rx.vstack(
        rx.heading("Custom Area Analysis", size="3"),
        rx.text(
            "Draw or upload areas for detailed analysis",
            font_size="1",
            color="gray",
        ),
        rx.divider(),
        rx.cond(
            len(AppState.drawn_features) > 0,
            rx.vstack(
                rx.badge(f"Drawn areas: {len(AppState.drawn_features)}", color_scheme="blue"),
                rx.button(
                    "🗑️ Clear All",
                    on_click=AppState.clear_drawn_features,
                    width="100%",
                    color_scheme="red",
                    size="1",
                ),
                width="100%",
            ),
            rx.text(
                "Draw areas on the map to analyze",
                font_size="1",
                color="gray",
                font_style="italic",
            ),
        ),
        width="100%",
        spacing="4",
    )


def analysis_content() -> rx.Component:
    """Main analysis content area with tabs."""
    return rx.vstack(
        rx.tabs(
            rx.tab_list(
                rx.tab("🌿 MapBiomas"),
                rx.tab("🌲 Hansen"),
                rx.tab("📍 Custom Areas"),
            ),
            rx.tab_panels(
                rx.tab_panel(mapbiomas_analysis_tab()),
                rx.tab_panel(hansen_analysis_tab()),
                rx.tab_panel(buffer_analysis_tab()),
            ),
        ),
        width="100%",
        padding="1rem",
    )
