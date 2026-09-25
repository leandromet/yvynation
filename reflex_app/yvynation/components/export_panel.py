"""
Phase 5: Export panel component.
Provides UI for exporting analysis data as ZIP bundles, PDF maps and the
laid-out territory report (docs/PDF_REPORT.md).
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


def export_report_section() -> rx.Component:
    """The laid-out report block — same anatomy as Naturametrics/Camposcope
    (docs/PDF_REPORT.md §2.9): options, PDF (primary) + HTML (secondary),
    a stage line, and the reason when the buttons are disabled."""
    disabled = AppState.report_disabled_reason != ""

    def _chk(label, checked, handler):
        return rx.checkbox(label, checked=checked, on_change=handler, size="1",
                           color_scheme="green")

    return rx.vstack(
        rx.text(AppState.tr["report_heading"], font_weight="bold", font_size="sm"),
        rx.text(AppState.tr["report_intro"], font_size="xs", color="gray"),
        rx.flex(
            _chk(AppState.tr["report_chk_maps"], AppState.exp_report_maps,
                 AppState.toggle_exp_report_maps),
            _chk(AppState.tr["report_chk_figures"], AppState.exp_report_figures,
                 AppState.toggle_exp_report_figures),
            _chk(AppState.tr["report_chk_tables"], AppState.exp_report_tables,
                 AppState.toggle_exp_report_tables),
            _chk(AppState.tr["report_chk_appendix"], AppState.exp_report_appendix,
                 AppState.toggle_exp_report_appendix),
            wrap="wrap", spacing="3", width="100%",
        ),
        rx.hstack(
            rx.button(
                rx.cond(AppState.report_busy, rx.spinner(size="1"), rx.icon("file-text", size=14)),
                AppState.tr["report_btn_pdf"],
                on_click=AppState.start_report("pdf"),
                disabled=disabled, size="2", color_scheme="green", variant="solid",
                flex="1",
            ),
            rx.button(
                rx.icon("code", size=14),
                AppState.tr["report_btn_html"],
                on_click=AppState.start_report("html"),
                disabled=disabled, size="2", color_scheme="green", variant="outline",
                flex="1",
            ),
            width="100%", spacing="2",
        ),
        rx.cond(
            AppState.report_stage != "",
            rx.text(AppState.report_stage, font_size="xs", color="#374151"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.report_error != "",
            rx.text(AppState.report_error, font_size="xs", color="#b91c1c"),
            rx.fragment(),
        ),
        rx.cond(
            disabled & ~AppState.report_busy,
            rx.hstack(
                rx.icon("info", size=12, color="gray"),
                rx.text(AppState.report_disabled_reason, font_size="xs", color="gray"),
                spacing="1", align="start",
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
        align="stretch",
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
                    rx.tabs.trigger(AppState.tr["export_tab_data"], value="zip"),
                    rx.tabs.trigger(AppState.tr["export_tab_maps"], value="pdf"),
                    rx.tabs.trigger(AppState.tr["export_tab_report"], value="report"),
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
                rx.tabs.content(
                    export_report_section(),
                    value="report",
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
