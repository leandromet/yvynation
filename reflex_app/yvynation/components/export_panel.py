"""
Phase 5: Export panel component.
Provides UI for exporting analysis data as ZIP bundles and PDF maps.
"""

import reflex as rx
from ..state import AppState


def export_manifest() -> rx.Component:
    """Show what will be included in the export."""
    return rx.vstack(
        rx.text("Export Contents:", font_weight="bold", font_size="sm"),
        rx.vstack(
            # Analysis data
            rx.cond(
                (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                rx.hstack(
                    rx.icon("check-circle", size=14, color="green"),
                    rx.text("Analysis data (CSV)", font_size="xs"),
                    spacing="1",
                ),
                rx.hstack(
                    rx.icon("circle", size=14, color="gray"),
                    rx.text("Analysis data (no data yet)", font_size="xs", color="gray"),
                    spacing="1",
                ),
            ),
            # Comparison data
            rx.cond(
                AppState.comparison_available,
                rx.hstack(
                    rx.icon("check-circle", size=14, color="green"),
                    rx.text("Year comparison (CSV)", font_size="xs"),
                    spacing="1",
                ),
                rx.box(),
            ),
            # Geometries
            rx.cond(
                AppState.drawn_features.length() > 0,
                rx.hstack(
                    rx.icon("check-circle", size=14, color="green"),
                    rx.text(
                        rx.cond(
                            AppState.drawn_features.length() == 1,
                            "1 geometry (GeoJSON)",
                            AppState.drawn_features.length().to(str) + " geometries (GeoJSON)",
                        ),
                        font_size="xs",
                    ),
                    spacing="1",
                ),
                rx.box(),
            ),
            # Charts
            rx.hstack(
                rx.icon("check-circle", size=14, color="green"),
                rx.text("Interactive charts (HTML)", font_size="xs"),
                spacing="1",
            ),
            # Metadata
            rx.hstack(
                rx.icon("check-circle", size=14, color="green"),
                rx.text("Metadata & README", font_size="xs"),
                spacing="1",
            ),
            spacing="1",
            width="100%",
        ),
        spacing="2",
        width="100%",
        padding="0.75rem",
        bg="gray.50",
        border_radius="md",
        border="1px solid #e0e0e0",
    )


def export_zip_section() -> rx.Component:
    """ZIP export section with button and manifest."""
    return rx.vstack(
        rx.text("Data & Figures Export", font_weight="bold", font_size="sm"),
        rx.text(
            "Download all analysis data, charts, and geometries as a ZIP file.",
            font_size="xs", color="gray",
        ),
        export_manifest(),
        rx.cond(
            AppState.export_pending,
            rx.button(
                rx.hstack(rx.spinner(size="1"), rx.text("Preparing..."), spacing="2"),
                is_disabled=True, width="100%", size="2", color_scheme="blue",
            ),
            rx.button(
                "Export All Data & Visualizations (ZIP)",
                on_click=AppState.export_analysis_zip,
                width="100%",
                size="2",
                color_scheme="green",
                variant="solid",
            ),
        ),
        spacing="2",
        width="100%",
    )


def export_maps_section() -> rx.Component:
    """PDF map export section."""
    return rx.vstack(
        rx.text("PDF Map Export", font_weight="bold", font_size="sm"),
        rx.text(
            "Generate publication-quality PDF maps with overlays.",
            font_size="xs", color="gray",
        ),
        rx.vstack(
            # What will be generated
            rx.cond(
                AppState.mapbiomas_displayed_years.length() > 0,
                rx.hstack(
                    rx.icon("map", size=14, color="green"),
                    rx.text(
                        "MapBiomas maps: " + AppState.mapbiomas_displayed_years.length().to(str),
                        font_size="xs",
                    ),
                    spacing="1",
                ),
                rx.box(),
            ),
            rx.cond(
                AppState.hansen_displayed_layers.length() > 0,
                rx.hstack(
                    rx.icon("map", size=14, color="blue"),
                    rx.text(
                        "Hansen maps: " + AppState.hansen_displayed_layers.length().to(str),
                        font_size="xs",
                    ),
                    spacing="1",
                ),
                rx.box(),
            ),
            rx.hstack(
                rx.icon("map", size=14, color="purple"),
                rx.text("Satellite basemap", font_size="xs"),
                spacing="1",
            ),
            spacing="1",
            padding="0.5rem",
            bg="gray.50",
            border_radius="md",
            width="100%",
        ),
        rx.cond(
            AppState.map_export_pending,
            rx.button(
                rx.hstack(rx.spinner(size="1"), rx.text("Generating maps..."), spacing="2"),
                is_disabled=True, width="100%", size="2", color_scheme="blue",
            ),
            rx.button(
                "Generate & Download PDF Maps",
                on_click=AppState.export_pdf_maps,
                width="100%",
                size="2",
                color_scheme="purple",
                variant="solid",
            ),
        ),
        spacing="2",
        width="100%",
    )


def export_panel() -> rx.Component:
    """
    Main export panel with tabs for ZIP and PDF export.
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("Export & Download", size="3"),
                rx.spacer(),
                rx.badge(
                    rx.cond(
                        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                        "Ready",
                        "No Data",
                    ),
                    color_scheme=rx.cond(
                        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                        "green",
                        "gray",
                    ),
                ),
                width="100%",
                align_items="center",
            ),
            rx.divider(),
            rx.tabs.root(
                rx.tabs.list(
                    rx.tabs.trigger("Data & Figures", value="zip"),
                    rx.tabs.trigger("PDF Maps", value="pdf"),
                ),
                rx.tabs.content(
                    export_zip_section(),
                    value="zip",
                    padding_top="0.5rem",
                ),
                rx.tabs.content(
                    export_maps_section(),
                    value="pdf",
                    padding_top="0.5rem",
                ),
                default_value="zip",
                width="100%",
            ),
            spacing="2",
            width="100%",
            padding="1rem",
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
    )
