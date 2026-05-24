"""
Phase 4: Analysis tabs component - 6 analysis tabs matching Streamlit app.
Tabs: MapBiomas | Hansen/GLAD | Hansen GFC | AAFC | Comparison | About
All text uses AppState.tr for i18n support.
"""

import reflex as rx
from ..state import AppState


def _no_data_placeholder(message: str = "Run analysis to see results") -> rx.Component:
    """Placeholder shown when no analysis data is available."""
    return rx.vstack(
        rx.icon("bar-chart-2", size=32, color="gray"),
        rx.text(message, font_size="sm", color="gray"),
        align="center",
        padding="2rem",
        width="100%",
    )


def _summary_metrics_row(analysis_results: dict) -> rx.Component:
    """Summary metrics row (Total Area, Classes, Top Class)."""
    return rx.cond(
        AppState.analysis_results.get("summary") != None,
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["area_hectares"], font_size="xs", color="gray"),
                    rx.text(
                        AppState.analysis_summary_total_area,
                        font_weight="bold", font_size="lg",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="green.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["class"], font_size="xs", color="gray"),
                    rx.text(
                        AppState.analysis_summary_classes,
                        font_weight="bold", font_size="lg",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="blue.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text("Top", font_size="xs", color="gray"),
                    rx.text(
                        AppState.analysis_summary_top_class,
                        font_weight="bold", font_size="sm",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="orange.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            width="100%",
            spacing="2",
        ),
        rx.box(),
    )


def _hansen_summary_metrics() -> rx.Component:
    """Hansen-specific summary metrics."""
    return rx.cond(
        AppState.analysis_results.get("summary") != None,
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["area_hectares"], font_size="xs", color="gray"),
                    rx.text(
                        AppState.hansen_summary_cover,
                        font_weight="bold", font_size="lg", color="blue",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="blue.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["class"], font_size="xs", color="gray"),
                    rx.text(
                        AppState.hansen_summary_loss,
                        font_weight="bold", font_size="lg", color="orange",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="orange.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["year"], font_size="xs", color="gray"),
                    rx.text(
                        AppState.hansen_summary_gain,
                        font_weight="bold", font_size="lg", color="purple",
                    ),
                    spacing="0", align="center",
                ),
                padding="0.75rem",
                bg="purple.50",
                border_radius="md",
                flex="1",
                text_align="center",
            ),
            width="100%",
            spacing="2",
        ),
        rx.box(),
    )


# -----------------------------------------------------------------------
# Shared buffer comparison header / badge
# -----------------------------------------------------------------------

def _buffer_header(title: str, badge_text: rx.Var) -> rx.Component:
    """Reusable header row for every buffer comparison box."""
    return rx.vstack(
        rx.hstack(
            rx.icon("circle", color="#3B82F6", size=14),
            rx.heading(title, size="3", color="#1D4ED8"),
            rx.badge(badge_text, color_scheme="blue", variant="surface", size="1"),
            spacing="2",
            align_items="center",
        ),
        rx.text(
            "🟠 Territory (inside boundary)  vs  🔵 Buffer zone (external ring)",
            font_size="xs",
            color="gray.600",
        ),
        spacing="1",
        width="100%",
    )


def _territory_card(area: rx.Var, classes: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("🟠 Territory", font_size="xs", font_weight="700", color="#FF4500"),
            rx.text(area, font_weight="bold", font_size="lg"),
            rx.text(classes, font_size="xs", color="gray"),
            spacing="1", align="center",
        ),
        flex="1", padding="0.75rem", bg="orange.50",
        border_radius="md", border="1px solid #FF4500", text_align="center",
    )


def _buffer_card(area: rx.Var, extra: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("🔵 Buffer", font_size="xs", font_weight="700", color="#1D4ED8"),
            rx.text(area, font_weight="bold", font_size="lg"),
            rx.text(extra, font_size="xs", color="gray"),
            spacing="1", align="center",
        ),
        flex="1", padding="0.75rem", bg="blue.50",
        border_radius="md", border="1px solid #1D4ED8", text_align="center",
    )


def _plotly_safe(chart_var: rx.Var, min_height: str = "180px") -> rx.Component:
    """Render rx.plotly only when the chart var is not null.

    rx.plotly crashes with 'WeakMap key null' if its data prop is null/None.
    This wrapper guards against that by rendering a placeholder instead.
    """
    return rx.cond(
        chart_var != None,
        rx.plotly(data=chart_var, use_resize_handler=True),
        rx.box(
            rx.text("No data", font_size="xs", color="gray"),
            min_height=min_height,
            display="flex",
            align_items="center",
            justify_content="center",
        ),
    )


def _side_by_side_charts(left_chart: rx.Var, right_chart: rx.Var,
                          left_label: str = "Territory",
                          right_label: str = "Buffer") -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(left_label, font_size="xs", color="gray", text_align="center"),
            _plotly_safe(left_chart),
            flex="1",
        ),
        rx.box(
            rx.text(right_label, font_size="xs", color="gray", text_align="center"),
            _plotly_safe(right_chart),
            flex="1",
        ),
        width="100%",
        spacing="2",
        align_items="flex-start",
    )


def _buffer_box(content: rx.Component) -> rx.Component:
    return rx.box(
        content,
        padding="0.75rem",
        border="2px solid #93C5FD",
        border_radius="md",
        bg="blue.50",
        width="100%",
    )


# -----------------------------------------------------------------------
# Buffer comparison helpers — one per tab
# -----------------------------------------------------------------------

def _buffer_comparison_mapbiomas() -> rx.Component:
    """Side-by-side MapBiomas territory vs buffer comparison."""
    return rx.cond(
        AppState.buffer_mapbiomas_result != None,
        _buffer_box(
            rx.vstack(
                _buffer_header(
                    "Buffer Zone — MapBiomas Comparison",
                    AppState.buffer_mapbiomas_summary.get("name", "Buffer"),
                ),
                rx.hstack(
                    _territory_card(
                        AppState.analysis_summary_total_area,
                        AppState.analysis_summary_classes + " classes",
                    ),
                    rx.text("vs", font_size="md", color="gray", font_weight="bold"),
                    _buffer_card(
                        AppState.buffer_mapbiomas_summary.get("area", "…"),
                        AppState.buffer_mapbiomas_summary.get("classes", "0") + " classes",
                    ),
                    width="100%", spacing="2", align_items="center",
                ),
                _side_by_side_charts(
                    AppState.mapbiomas_bar_chart,
                    AppState.buffer_mapbiomas_bar_chart,
                ),
                spacing="3",
                width="100%",
            )
        ),
        rx.box(),
    )


def _buffer_comparison_hansen() -> rx.Component:
    """Side-by-side Hansen GLAD territory vs buffer comparison."""
    return rx.cond(
        AppState.buffer_hansen_result != None,
        _buffer_box(
            rx.vstack(
                _buffer_header(
                    "Buffer Zone — Hansen/GLAD Comparison",
                    AppState.buffer_hansen_summary.get("name", "Buffer"),
                ),
                rx.hstack(
                    _territory_card(
                        AppState.glad_summary_area,
                        AppState.glad_summary_classes + " classes",
                    ),
                    rx.text("vs", font_size="md", color="gray", font_weight="bold"),
                    _buffer_card(
                        AppState.buffer_hansen_summary.get("area", "…"),
                        AppState.buffer_hansen_summary.get("classes", "0") + " classes",
                    ),
                    width="100%", spacing="2", align_items="center",
                ),
                _side_by_side_charts(
                    AppState.glad_bar_chart,
                    AppState.buffer_hansen_bar_chart,
                ),
                spacing="3",
                width="100%",
            )
        ),
        rx.box(),
    )


def _buffer_comparison_gfc() -> rx.Component:
    """Side-by-side Hansen GFC territory vs buffer comparison."""
    return rx.cond(
        AppState.buffer_gfc_result != None,
        _buffer_box(
            rx.vstack(
                _buffer_header(
                    "Buffer Zone — Hansen GFC Comparison",
                    AppState.buffer_gfc_summary.get("name", "Buffer"),
                ),
                # Three-metric row for GFC (Cover / Loss / Gain)
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("🌳 Tree Cover 2000", font_size="xs", color="gray"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Territory", font_size="xs", color="#FF4500"),
                                    rx.text(AppState.gfc_summary_cover, font_weight="bold", color="green"),
                                    spacing="0", align="center",
                                ),
                                rx.text("vs", font_size="xs", color="gray"),
                                rx.vstack(
                                    rx.text("Buffer", font_size="xs", color="#1D4ED8"),
                                    rx.text(AppState.buffer_gfc_summary.get("cover", "…"), font_weight="bold", color="teal"),
                                    spacing="0", align="center",
                                ),
                                spacing="2", align_items="center",
                            ),
                            spacing="1", align="center",
                        ),
                        padding="0.75rem", bg="green.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("📉 Forest Loss", font_size="xs", color="gray"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Territory", font_size="xs", color="#FF4500"),
                                    rx.text(AppState.gfc_summary_loss, font_weight="bold", color="red"),
                                    spacing="0", align="center",
                                ),
                                rx.text("vs", font_size="xs", color="gray"),
                                rx.vstack(
                                    rx.text("Buffer", font_size="xs", color="#1D4ED8"),
                                    rx.text(AppState.buffer_gfc_summary.get("loss", "…"), font_weight="bold", color="orange"),
                                    spacing="0", align="center",
                                ),
                                spacing="2", align_items="center",
                            ),
                            spacing="1", align="center",
                        ),
                        padding="0.75rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("📈 Forest Gain", font_size="xs", color="gray"),
                            rx.hstack(
                                rx.vstack(
                                    rx.text("Territory", font_size="xs", color="#FF4500"),
                                    rx.text(AppState.gfc_summary_gain, font_weight="bold", color="teal"),
                                    spacing="0", align="center",
                                ),
                                rx.text("vs", font_size="xs", color="gray"),
                                rx.vstack(
                                    rx.text("Buffer", font_size="xs", color="#1D4ED8"),
                                    rx.text(AppState.buffer_gfc_summary.get("gain", "…"), font_weight="bold", color="purple"),
                                    spacing="0", align="center",
                                ),
                                spacing="2", align_items="center",
                            ),
                            spacing="1", align="center",
                        ),
                        padding="0.75rem", bg="teal.50", border_radius="md", flex="1", text_align="center",
                    ),
                    width="100%", spacing="2",
                ),
                _side_by_side_charts(
                    AppState.gfc_bar_chart,
                    AppState.buffer_gfc_bar_chart,
                ),
                spacing="3",
                width="100%",
            )
        ),
        # No buffer GFC data yet — show helpful hint
        rx.box(
            rx.hstack(
                rx.icon("info", size=14, color="#93C5FD"),
                rx.text(
                    "Buffer zone GFC comparison will appear here after running "
                    "Territory Analysis → Hansen GFC with an active buffer.",
                    font_size="xs", color="#1D4ED8",
                ),
                spacing="2", align_items="center",
            ),
            padding="0.5rem 0.75rem",
            border="1px dashed #93C5FD",
            border_radius="md",
            bg="blue.50",
            width="100%",
        ),
    )


def _buffer_comparison_compare() -> rx.Component:
    """Side-by-side comparison year-2 territory vs buffer for the Compare tab."""
    return rx.cond(
        AppState.buffer_compare_result != None,
        _buffer_box(
            rx.vstack(
                _buffer_header(
                    "Buffer Zone — Year Comparison",
                    AppState.buffer_compare_summary.get("name", "Buffer"),
                ),
                rx.text(
                    "Land cover in the external buffer ring — year " +
                    AppState.buffer_compare_summary.get("year", ""),
                    font_size="xs", color="gray.600",
                ),
                rx.hstack(
                    # Territory card — uses pre-computed vars (no chained .get())
                    _territory_card(
                        AppState.territory_year2_area,
                        AppState.territory_year2_classes,
                    ),
                    rx.text("vs", font_size="md", color="gray", font_weight="bold"),
                    _buffer_card(
                        AppState.buffer_compare_summary.get("area", "…"),
                        AppState.buffer_compare_summary.get("classes", "0") + " classes",
                    ),
                    width="100%", spacing="2", align_items="center",
                ),
                _side_by_side_charts(
                    AppState.mapbiomas_bar_chart,
                    AppState.buffer_compare_bar_chart,
                    left_label="Territory (year 2)",
                    right_label="Buffer (year 2)",
                ),
                spacing="3",
                width="100%",
            )
        ),
        rx.box(),
    )


# -----------------------------------------------------------------------
# Tab 1: MapBiomas Analysis
# -----------------------------------------------------------------------

def mapbiomas_tab() -> rx.Component:
    """MapBiomas land cover analysis tab. Displays mapbiomas_analysis_result or generic analysis_results."""
    return rx.vstack(
        rx.heading(AppState.tr["mapbiomas_analysis_title"], size="3"),
        # Analysis info
        rx.cond(
            (AppState.mapbiomas_analysis_result != None) | (AppState.analysis_results.get("type") == "mapbiomas"),
            rx.box(
                rx.text(
                    rx.cond(
                        AppState.mapbiomas_analysis_result != None,
                        rx.cond(
                            AppState.selected_territory != "",
                            f"📍 {AppState.selected_territory} • MapBiomas {AppState.territory_analysis_year}",
                            "MapBiomas Analysis Ready"
                        ),
                        f"🔍 {AppState.analysis_results.get('geometry', 'Geometry')} • MapBiomas {AppState.analysis_results.get('year', 'N/A')}",
                    ),
                    font_size="sm", color="gray"
                ),
                padding="1rem",
                bg="gray.50",
                border_radius="md",
                border_left="4px solid #3182ce",
            ),
            rx.box(),
        ),
        rx.cond(
            (AppState.mapbiomas_analysis_result != None) | (AppState.analysis_results.get("type") == "mapbiomas"),
            rx.vstack(
                rx.cond(
                    AppState.mapbiomas_analysis_result != None,
                    _summary_metrics_row(AppState.mapbiomas_analysis_result),
                    _summary_metrics_row(AppState.analysis_results),
                ),
                rx.divider(),
                rx.box(
                    _plotly_safe(AppState.mapbiomas_bar_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    _plotly_safe(AppState.mapbiomas_pie_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    rx.data_table(
                        data=AppState.mapbiomas_table_data,
                        columns=AppState.mapbiomas_table_columns,
                        pagination=True,
                        search=True,
                    ),
                    width="100%",
                    overflow_x="auto",
                ),
                rx.divider(),
                rx.button(
                    AppState.tr["export_as_csv"],
                    on_click=AppState.download_mapbiomas_csv,
                    color_scheme="blue",
                    size="2",
                    variant="outline",
                ),
                rx.cond(
                    (AppState.hansen_analysis_result != None) | (AppState.analysis_results.get("type") == "hansen"),
                    rx.button(
                        "→ View Hansen Results",
                        on_click=AppState.set_active_tab("hansen"),
                        size="1",
                        color_scheme="orange",
                        variant="solid",
                    ),
                    rx.box(),
                ),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder(AppState.tr["mapbiomas_no_data"]),
        ),
        # Buffer comparison (shown below when buffer analysis has run)
        _buffer_comparison_mapbiomas(),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 2: Hansen/GLAD Analysis
# -----------------------------------------------------------------------

def _glad_table(data) -> rx.Component:
    """Render GLAD class distribution as a Radix table (dynamic-column-safe)."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Class"),
                rx.table.column_header_cell("Class ID"),
                rx.table.column_header_cell("Area (ha)"),
                rx.table.column_header_cell("Pixels"),
            )
        ),
        rx.table.body(
            rx.foreach(
                data,
                lambda row: rx.table.row(
                    rx.table.cell(row.get("Class", "")),
                    rx.table.cell(row.get("Class_ID", "").to(str)),
                    rx.table.cell(row.get("Area_ha", "").to(str)),
                    rx.table.cell(row.get("Pixels", "").to(str)),
                ),
            )
        ),
        width="100%",
        variant="surface",
        size="1",
    )


def hansen_tab() -> rx.Component:
    """Hansen/GLAD forest cover analysis tab."""
    has_glad = AppState.geometry_glad_result != None
    has_territory = AppState.hansen_analysis_result != None
    has_data = has_glad | has_territory

    return rx.vstack(
        rx.heading(AppState.tr["hansen_analysis"], size="3"),
        rx.box(
            rx.hstack(
                rx.box(rx.icon("info", size=20, color="#ed8936"), width="auto"),
                rx.vstack(
                    rx.text("Hansen GLAD / Forest Cover Snapshots", font_weight="bold", font_size="sm"),
                    rx.text(
                        "Data shows land cover classification for specific years (2000, 2005, 2010, 2015, 2020). "
                        "Numbers represent mapped forest cover (%) for each class.",
                        font_size="xs", color="gray", line_height="1.5",
                    ),
                    spacing="1",
                ),
                spacing="3",
                align_items="flex_start",
            ),
            padding="1rem",
            bg="orange.50",
            border_radius="md",
            border_left="4px solid #ed8936",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.cond(
            has_data,
            rx.box(
                rx.text(
                    rx.cond(
                        has_territory,
                        f"📍 {AppState.selected_territory} • Hansen {AppState.hansen_current_year}",
                        f"🔍 {AppState.geometry_glad_result.get('geometry_name', 'Geometry')} • Hansen GLAD {AppState.glad_summary_year}",
                    ),
                    font_size="sm", color="gray",
                ),
                padding="0.75rem 1rem",
                bg="gray.50",
                border_radius="md",
                border_left="4px solid #ed8936",
                width="100%",
            ),
            rx.box(),
        ),
        rx.cond(
            has_data,
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("Total Area", font_size="xs", color="gray"),
                            rx.text(AppState.glad_summary_area, font_weight="bold", font_size="lg", color="blue"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="blue.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("Classes", font_size="xs", color="gray"),
                            rx.text(AppState.glad_summary_classes, font_weight="bold", font_size="lg", color="orange"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="orange.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("Year", font_size="xs", color="gray"),
                            rx.text(AppState.glad_summary_year, font_weight="bold", font_size="lg", color="purple"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="purple.50", border_radius="md", flex="1", text_align="center",
                    ),
                    width="100%", spacing="2",
                ),
                rx.divider(),
                rx.heading("📊 Class Distribution by Area", size="4"),
                rx.box(
                    rx.cond(
                        has_glad,
                        _plotly_safe(AppState.glad_bar_chart),
                        _plotly_safe(AppState.hansen_balance_chart),
                    ),
                    width="100%",
                ),
                rx.divider(),
                rx.heading("🌿 Detailed Class Data", size="4"),
                rx.cond(
                    has_glad,
                    _glad_table(AppState.glad_table_data),
                    rx.box(
                        rx.data_table(
                            data=AppState.hansen_table_data,
                            columns=AppState.hansen_table_columns,
                            pagination=True,
                            search=True,
                        ),
                        width="100%",
                        overflow_x="auto",
                    ),
                ),
                rx.divider(),
                rx.button(
                    AppState.tr["export_as_csv"],
                    on_click=AppState.download_hansen_csv,
                    color_scheme="blue",
                    size="2",
                    variant="outline",
                ),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder(AppState.tr["hansen_no_data"]),
        ),
        # Buffer comparison
        _buffer_comparison_hansen(),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 3: Hansen GFC
# -----------------------------------------------------------------------

def _gfc_simple_table(data, cols) -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.foreach(cols, lambda c: rx.table.column_header_cell(c))
            )
        ),
        rx.table.body(
            rx.foreach(
                data,
                lambda row: rx.table.row(
                    rx.foreach(cols, lambda c: rx.table.cell(row.get(c, "").to(str)))
                ),
            )
        ),
        width="100%",
        variant="surface",
        size="1",
    )


def hansen_gfc_tab() -> rx.Component:
    """Hansen GFC (Global Forest Change) tab: cover 2000, loss 2000-2023, gain 2000-2012."""
    return rx.vstack(
        rx.heading(AppState.tr["hansen_gfc_label"], size="3"),
        rx.box(
            rx.hstack(
                rx.box(rx.icon("info", size=20, color="#ed8936"), width="auto"),
                rx.vstack(
                    rx.text("Hansen GFC / Global Forest Change", font_weight="bold", font_size="sm"),
                    rx.text(
                        "Tracks continuous forest dynamics using three layers: "
                        "(1) Tree Cover 2000 baseline, (2) Annual tree loss (2000–2023 by year), (3) Forest gain (2000–2012). "
                        "Captures detailed year-by-year loss patterns and regrowth.",
                        font_size="xs", color="gray", line_height="1.5",
                    ),
                    spacing="1",
                ),
                spacing="3",
                align_items="flex_start",
            ),
            padding="1rem",
            bg="orange.50",
            border_radius="md",
            border_left="4px solid #ed8936",
            width="100%",
            margin_bottom="1rem",
        ),
        rx.text(
            "Tree Cover 2000 (baseline) | Tree Loss 2000–2023 | Tree Gain 2000–2012",
            font_size="sm", color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.geometry_gfc_result != None,
            rx.vstack(
                rx.box(
                    rx.text(
                        f"🔍 {AppState.geometry_gfc_result.get('geometry_name', 'Geometry')} • Hansen GFC",
                        font_size="sm", color="gray",
                    ),
                    padding="0.75rem 1rem",
                    bg="gray.50",
                    border_radius="md",
                    border_left="4px solid #ed8936",
                    width="100%",
                ),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("🌳 Tree Cover 2000", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_cover, font_weight="bold", font_size="lg", color="green"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="green.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("📉 Forest Loss", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_loss, font_weight="bold", font_size="lg", color="red"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("📈 Forest Gain", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_gain, font_weight="bold", font_size="lg", color="teal"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="teal.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("⚖️ Net Change", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_net, font_weight="bold", font_size="lg", color="purple"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="purple.50", border_radius="md", flex="1", text_align="center",
                    ),
                    width="100%", spacing="2",
                ),
                rx.divider(),
                rx.box(
                    _plotly_safe(AppState.gfc_bar_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.heading("📊 Summary", size="4"),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Metric"),
                            rx.table.column_header_cell("Area (ha)"),
                            rx.table.column_header_cell("Percent"),
                            rx.table.column_header_cell("Description"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            AppState.gfc_table_data,
                            lambda row: rx.table.row(
                                rx.table.cell(row.get("Metric", "")),
                                rx.table.cell(row.get("Area_ha", "").to(str)),
                                rx.table.cell(row.get("Percent", "")),
                                rx.table.cell(row.get("Description", "")),
                            ),
                        )
                    ),
                    width="100%", variant="surface", size="1",
                ),
                rx.divider(),
                rx.cond(
                    AppState.gfc_cover_categories.length() > 0,
                    rx.vstack(
                        rx.heading("🌳 Tree Cover 2000 — Distribution", size="4"),
                        rx.text("Canopy cover grouped into 5 categories", font_size="xs", color="gray"),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Category"),
                                    rx.table.column_header_cell("Area (ha)"),
                                    rx.table.column_header_cell("% of Total"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AppState.gfc_cover_categories,
                                    lambda row: rx.table.row(
                                        rx.table.cell(row.get("Category", "")),
                                        rx.table.cell(row.get("Area_ha", "").to(str)),
                                        rx.table.cell(row.get("Percentage", "")),
                                    ),
                                )
                            ),
                            width="100%", variant="surface", size="1",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.box(),
                ),
                rx.divider(),
                rx.cond(
                    AppState.gfc_loss_by_year.length() > 0,
                    rx.vstack(
                        rx.heading("🔥 Forest Loss by Year", size="4"),
                        rx.hstack(
                            rx.box(
                                rx.vstack(
                                    rx.text("Total Loss", font_size="xs", color="gray"),
                                    rx.text(AppState.gfc_summary_loss, font_weight="bold", color="red"),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Years with Loss", font_size="xs", color="gray"),
                                    rx.text(AppState.gfc_loss_by_year.length().to(str), font_weight="bold", color="orange"),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="orange.50", border_radius="md", flex="1", text_align="center",
                            ),
                            width="100%", spacing="2",
                        ),
                        rx.box(
                            _plotly_safe(AppState.gfc_loss_chart),
                            width="100%",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Year"),
                                    rx.table.column_header_cell("Area (ha)"),
                                    rx.table.column_header_cell("Pixels"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AppState.gfc_loss_by_year,
                                    lambda row: rx.table.row(
                                        rx.table.cell(row.get("Year", "")),
                                        rx.table.cell(row.get("Area_ha", "").to(str)),
                                        rx.table.cell(row.get("Pixels", "").to(str)),
                                    ),
                                )
                            ),
                            width="100%", variant="surface", size="1",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.box(
                        rx.text("✅ No tree loss detected in this area.", font_size="sm", color="green"),
                        padding="0.5rem",
                    ),
                ),
                rx.divider(),
                rx.cond(
                    AppState.gfc_gain_summary.length() > 0,
                    rx.vstack(
                        rx.heading("🌲 Tree Gain (2000–2012)", size="4"),
                        rx.hstack(
                            rx.box(
                                rx.vstack(
                                    rx.text("Area with Gain", font_size="xs", color="gray"),
                                    rx.text(AppState.gfc_summary_gain, font_weight="bold", color="teal"),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="teal.50", border_radius="md", flex="1", text_align="center",
                            ),
                            width="100%", spacing="2",
                        ),
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Status"),
                                    rx.table.column_header_cell("Area (ha)"),
                                    rx.table.column_header_cell("Pixels"),
                                )
                            ),
                            rx.table.body(
                                rx.foreach(
                                    AppState.gfc_gain_summary,
                                    lambda row: rx.table.row(
                                        rx.table.cell(row.get("Status", "")),
                                        rx.table.cell(row.get("Area_ha", "").to(str)),
                                        rx.table.cell(row.get("Pixels", "").to(str)),
                                    ),
                                )
                            ),
                            width="100%", variant="surface", size="1",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.box(),
                ),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder(AppState.tr["hansen_no_data"]),
        ),
        # Buffer comparison
        _buffer_comparison_gfc(),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 4: AAFC (Canada)
# -----------------------------------------------------------------------

def aafc_tab() -> rx.Component:
    """AAFC Annual Crop Inventory analysis tab (Canada)."""
    return rx.vstack(
        rx.heading(AppState.tr["aafc_legend"], size="3"),
        rx.divider(),
        rx.cond(
            AppState.selected_country == "Canada",
            _no_data_placeholder("AAFC analysis coming soon"),
            rx.vstack(
                rx.icon("info", size=24, color="blue"),
                rx.text(
                    "AAFC data is only available for Canada. Switch region in the sidebar.",
                    font_size="sm", color="gray",
                ),
                align="center",
                padding="2rem",
            ),
        ),
        # Buffer note for AAFC (Canada-only, territories in Brazil)
        rx.box(
            rx.hstack(
                rx.icon("info", size=14, color="#93C5FD"),
                rx.text(
                    "Buffer zone comparison for AAFC is not applicable to Brazilian indigenous territories. "
                    "Buffer analysis uses MapBiomas (Brazil) and Hansen (global) datasets.",
                    font_size="xs", color="#1D4ED8",
                ),
                spacing="2", align_items="center",
            ),
            padding="0.5rem 0.75rem",
            border="1px dashed #93C5FD",
            border_radius="md",
            bg="blue.50",
            width="100%",
        ),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 5: Comparison
# -----------------------------------------------------------------------

def comparison_tab() -> rx.Component:
    """Year-to-year comparison tab with gains/losses, Sankey, and transition matrix."""
    return rx.vstack(
        rx.heading(AppState.tr["year_comparison_results"], size="3"),
        rx.cond(
            AppState.comparison_available,
            rx.vstack(
                rx.box(
                    _plotly_safe(AppState.comparison_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    rx.text(AppState.tr["total_gains"] + " / " + AppState.tr["total_losses"], font_weight="bold", font_size="sm"),
                    _plotly_safe(AppState.gains_losses_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    _plotly_safe(AppState.change_pct_chart),
                    width="100%",
                ),
                rx.divider(),
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["total_gains"], font_size="xs", color="gray"),
                            rx.text(AppState.comparison_total_gains, font_weight="bold", color="green"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="green.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["total_losses"], font_size="xs", color="gray"),
                            rx.text(AppState.comparison_total_losses, font_weight="bold", color="red"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["net_change"], font_size="xs", color="gray"),
                            rx.text(AppState.comparison_net_change, font_weight="bold"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="blue.50", border_radius="md", flex="1", text_align="center",
                    ),
                    width="100%", spacing="2",
                ),
                rx.divider(),
                rx.box(
                    rx.hstack(
                        rx.icon("git-branch", size=16, color="purple"),
                        rx.text("Land Cover Transitions (Sankey)", font_weight="bold", font_size="sm"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.sankey_chart != None,
                        _plotly_safe(AppState.sankey_chart),
                        rx.vstack(
                            rx.icon("info", size=20, color="gray"),
                            rx.text(
                                "No transition data available. Transition data is computed during comparison analysis.",
                                font_size="xs", color="gray",
                            ),
                            align="center",
                            padding="1rem",
                        ),
                    ),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    rx.hstack(
                        rx.icon("pie-chart", size=16, color="purple"),
                        rx.text("Class Transitions (Sunburst)", font_weight="bold", font_size="sm"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.sunburst_transitions_chart != None,
                        _plotly_safe(AppState.sunburst_transitions_chart),
                        rx.vstack(
                            rx.icon("info", size=20, color="gray"),
                            rx.text(
                                "Sunburst chart shows how each class in the first year transitions to classes in the second year. "
                                "Run comparison analysis to generate this visualization.",
                                font_size="xs", color="gray",
                            ),
                            align="center",
                            padding="1rem",
                        ),
                    ),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    rx.hstack(
                        rx.icon("grid-3x3", size=16, color="orange"),
                        rx.text("Transition Matrix (Heatmap)", font_weight="bold", font_size="sm"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.transition_matrix_chart != None,
                        _plotly_safe(AppState.transition_matrix_chart),
                        rx.text(
                            "No transition data available.",
                            font_size="xs", color="gray", padding="1rem",
                        ),
                    ),
                    width="100%",
                ),
                rx.button(
                    AppState.tr["download_comparison_csv"],
                    on_click=AppState.download_comparison_csv,
                    size="1",
                    color_scheme="blue",
                    variant="outline",
                ),
                spacing="3",
                width="100%",
            ),
            rx.vstack(
                _no_data_placeholder("Run a comparison to see year-over-year changes"),
                rx.text(
                    "Use 'Compare Years' in the sidebar or analysis controls.",
                    font_size="xs", color="gray", text_align="center",
                ),
                width="100%",
            ),
        ),
        # Buffer comparison for compare tab
        _buffer_comparison_compare(),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 6: About / Project Info
# -----------------------------------------------------------------------

def about_tab() -> rx.Component:
    """About tab: territory info + full project context, etymology, data sources, buffer guide."""
    return rx.vstack(
        # --- Territory Info Section ---
        rx.cond(
            AppState.selected_territory != None,
            rx.vstack(
                rx.heading(AppState.tr["selected_territory"], size="3"),
                rx.hstack(
                    rx.text(AppState.tr["selected_territory"] + ":", font_weight="bold", min_width="120px"),
                    rx.text(AppState.selected_territory),
                    width="100%",
                ),
                rx.hstack(
                    rx.text(AppState.tr["territory_by_country"] + ":", font_weight="bold", min_width="120px"),
                    rx.text(AppState.selected_country),
                    width="100%",
                ),
                rx.hstack(
                    rx.text(AppState.tr["year"] + ":", font_weight="bold", min_width="120px"),
                    rx.text(AppState.mapbiomas_current_year.to(str)),
                    width="100%",
                ),
                rx.divider(),
                rx.text(AppState.tr["data_sources_title"], font_weight="bold", font_size="sm"),
                rx.vstack(
                    rx.hstack(
                        rx.badge("MapBiomas 10.1", color_scheme="green"),
                        rx.text("Land cover 1985–2024 (Brazil)", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("Hansen", color_scheme="blue"),
                        rx.text("Forest change 2000–2023 (Global)", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("AAFC", color_scheme="orange"),
                        rx.text("Crop inventory 2009–2023 (Canada)", font_size="xs"),
                        spacing="2",
                    ),
                    spacing="2",
                ),
                spacing="3",
                width="100%",
            ),
            rx.text(AppState.tr["no_territory_selected"], font_size="sm", color="gray"),
        ),
        rx.divider(),

        # --- Project Overview Section ---
        rx.vstack(
            rx.heading(AppState.tr["about_overview"], size="3"),
            rx.text(AppState.tr["about_desc"], font_size="sm", line_height="1.6"),
            spacing="2",
            width="100%",
        ),
        rx.divider(),

        # --- Author & Etymology ---
        rx.vstack(
            rx.hstack(
                rx.icon("user", size=16, color="green"),
                rx.text(AppState.tr["about_author"], font_weight="bold", font_size="sm"),
                spacing="2",
                align_items="center",
            ),
            rx.text(
                AppState.tr["about_role"] + " - " + AppState.tr["about_university"],
                font_size="xs", color="gray",
            ),
            rx.text(AppState.tr["about_supervisor"], font_size="xs", color="gray"),
            rx.divider(),
            rx.hstack(
                rx.icon("globe", size=16, color="teal"),
                rx.text(AppState.tr["about_app_name"], font_weight="bold", font_size="sm"),
                rx.text(AppState.tr["about_app_note"], font_size="xs", color="gray"),
                spacing="2",
                align_items="center",
                flex_wrap="wrap",
            ),
            rx.box(
                rx.vstack(
                    rx.text(AppState.tr["yvynation_meaning"], font_size="xs", font_style="italic", line_height="1.5"),
                    rx.text(AppState.tr["nation_meaning"], font_size="xs", font_style="italic", line_height="1.5"),
                    spacing="2",
                ),
                padding="0.75rem",
                bg="green.50",
                border_radius="md",
                border_left="3px solid #38a169",
            ),
            spacing="2",
            width="100%",
        ),
        rx.divider(),

        # --- Data Sources ---
        rx.vstack(
            rx.heading(AppState.tr["data_sources_title"], size="3"),
            rx.vstack(
                rx.hstack(
                    rx.badge("MapBiomas 10.1", color_scheme="green", variant="solid"),
                    rx.vstack(
                        rx.text(AppState.tr["mapbiomas_desc"], font_size="xs"),
                        rx.text(
                            "Collection 10.1 · Resolution: 30 m · Period: 1985–2024 · Brazil coverage · "
                            "Asset: mapbiomas-public/assets/brazil/lulc/collection10_1/…coverage_v1",
                            font_size="xs", color="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("Hansen/GLAD", color_scheme="blue", variant="solid"),
                    rx.vstack(
                        rx.text("Global Forest Change — forest cover snapshots", font_size="xs"),
                        rx.text(
                            "GLCLU2020 v2 · Resolution: 30 m · Snapshots: 2000, 2005, 2010, 2015, 2020 · Global coverage",
                            font_size="xs", color="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("Hansen GFC", color_scheme="teal", variant="solid"),
                    rx.vstack(
                        rx.text("Global Forest Change — continuous loss/gain tracking", font_size="xs"),
                        rx.text(
                            "UMD/hansen/global_forest_change_2025_v1_13 · Resolution: 30 m · "
                            "Cover 2000 | Loss 2001–2024 (annual) | Gain 2000–2012 · Global coverage",
                            font_size="xs", color="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("AAFC", color_scheme="orange", variant="solid"),
                    rx.vstack(
                        rx.text("Annual Crop Inventory — Canada land cover", font_size="xs"),
                        rx.text(
                            "Resolution: 30 m · Period: 2009–2023 · Canada coverage only",
                            font_size="xs", color="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("Territories", color_scheme="purple", variant="solid"),
                    rx.vstack(
                        rx.text(AppState.tr["territories_desc"], font_size="xs"),
                        rx.text(
                            "FUNAI indigenous territories · "
                            "Asset: mapbiomas-workspace/AUXILIAR/territories/indigenous_territories_funai",
                            font_size="xs", color="gray",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                spacing="3",
            ),
            spacing="2",
            width="100%",
        ),
        rx.divider(),

        # --- Buffer Zone Analysis Guide ---
        rx.vstack(
            rx.hstack(
                rx.icon("circle-dashed", size=16, color="#3B82F6"),
                rx.heading("Buffer Zone Analysis", size="3"),
                spacing="2",
                align_items="center",
            ),
            rx.text(
                "Yvynation automatically creates a configurable buffer ring around every selected territory "
                "and runs the same analyses in parallel, enabling direct comparison of land cover dynamics "
                "inside the territory vs its immediate surroundings.",
                font_size="sm", line_height="1.6",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.badge("MapBiomas", color_scheme="green", variant="surface"),
                        rx.text("Buffer land cover for selected year — auto-runs alongside territory", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("Hansen/GLAD", color_scheme="blue", variant="surface"),
                        rx.text("Buffer forest cover snapshot — auto-runs alongside territory", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("Hansen GFC", color_scheme="teal", variant="surface"),
                        rx.text("Buffer tree cover/loss/gain — runs when Territory → Hansen GFC is executed", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("Compare", color_scheme="orange", variant="surface"),
                        rx.text("Buffer land cover for comparison year 2 — auto-runs during year-to-year comparison", font_size="xs"),
                        spacing="2",
                    ),
                    spacing="2",
                ),
                padding="0.75rem",
                bg="blue.50",
                border_radius="md",
                border_left="3px solid #3B82F6",
            ),
            rx.text(
                "Buffer distance (default: 10 km) is configurable in the sidebar under Buffer Controls. "
                "The buffer ring excludes the territory itself — it represents the external influence zone.",
                font_size="xs", color="gray",
            ),
            spacing="2",
            width="100%",
        ),
        rx.divider(),

        # --- Technologies ---
        rx.vstack(
            rx.heading(AppState.tr["tech_title"], size="3"),
            rx.flex(
                rx.badge("Python 3.8+", color_scheme="blue", variant="surface"),
                rx.badge("Google Earth Engine", color_scheme="green", variant="surface"),
                rx.badge("Reflex 0.8", color_scheme="purple", variant="surface"),
                rx.badge("Plotly", color_scheme="red", variant="surface"),
                rx.badge("Folium / Leaflet", color_scheme="teal", variant="surface"),
                rx.badge("Pandas", color_scheme="orange", variant="surface"),
                rx.badge("MapBiomas Collection 10.1", color_scheme="green", variant="surface"),
                flex_wrap="wrap",
                gap="2",
            ),
            spacing="2",
            width="100%",
        ),

        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Main: 6-tab layout
# -----------------------------------------------------------------------

def analysis_tabs() -> rx.Component:
    """
    Full analysis panel with 6 tabs matching the Streamlit app:
    MapBiomas | Hansen/GLAD | Hansen GFC | AAFC | Comparison | About
    """
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger(AppState.tr["mapbiomas_label"], value="mapbiomas"),
                rx.tabs.trigger("Hansen/GLAD", value="hansen"),
                rx.tabs.trigger("Hansen GFC", value="gfc"),
                rx.tabs.trigger("AAFC", value="aafc"),
                rx.tabs.trigger(AppState.tr["compare_btn"], value="comparison"),
                rx.tabs.trigger(AppState.tr["about_tab"], value="about"),
            ),
            rx.tabs.content(mapbiomas_tab(), value="mapbiomas"),
            rx.tabs.content(hansen_tab(), value="hansen"),
            rx.tabs.content(hansen_gfc_tab(), value="gfc"),
            rx.tabs.content(aafc_tab(), value="aafc"),
            rx.tabs.content(comparison_tab(), value="comparison"),
            rx.tabs.content(about_tab(), value="about"),
            value=AppState.active_analysis_tab,
            on_change=AppState.set_active_analysis_tab,
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
        overflow="hidden",
    )
