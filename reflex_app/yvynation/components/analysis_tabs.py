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


def _area_basis_note() -> rx.Component:
    """Short honesty note on how area (ha) is computed — every pixelArea-based
    tab below shows this so 'Area (ha)' is never read as a nominal, fixed-scale
    guess."""
    return rx.hstack(
        rx.icon("ruler", size=12, color="gray"),
        rx.text(AppState.tr["area_basis_note"], font_size="2xs", color="gray", line_height="1.4"),
        spacing="1",
        align_items="flex-start",
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
        rx.plotly(data=chart_var, use_resize_handler=True, width="100%"),
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
    """MapBiomas buffer zone section — bar chart + gains/losses + % change, all side-by-side."""
    return rx.cond(
        AppState.buffer_mapbiomas_result != None,
        rx.vstack(
            # ── Header ──────────────────────────────────────────────────
            rx.box(
                _buffer_header(
                    "Buffer Zone — MapBiomas Comparison",
                    AppState.buffer_mapbiomas_summary.get("name", "Buffer"),
                ),
                padding="0.75rem",
                border="2px solid #93C5FD",
                border_radius="md",
                bg="blue.50",
                width="100%",
            ),
            # ── Class distribution side-by-side ─────────────────────────
            rx.box(
                rx.vstack(
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
                        left_label="🟠 Territory — class distribution",
                        right_label="🔵 Buffer — class distribution",
                    ),
                    spacing="3", width="100%",
                ),
                padding="0.75rem",
                border="1px solid #93C5FD",
                border_radius="md",
                bg="white",
                width="100%",
            ),
            # ── Gains / Losses (requires comparison run) ─────────────────
            rx.cond(
                AppState.buffer_mapbiomas_comparison_result != None,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("trending-up", size=14, color="#22C55E"),
                            rx.text(
                                "Gains & Losses — Territory vs Buffer",
                                font_size="sm", font_weight="700",
                            ),
                            spacing="2", align_items="center",
                        ),
                        # Metrics row
                        rx.hstack(
                            rx.box(
                                rx.vstack(
                                    rx.text("Gains", font_size="xs", color="gray"),
                                    rx.hstack(
                                        rx.text(AppState.comparison_total_gains, color="green", font_weight="bold"),
                                        rx.text("vs", font_size="xs", color="gray"),
                                        rx.text(AppState.buffer_compare_total_gains, color="teal", font_weight="bold"),
                                        spacing="1",
                                    ),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="green.50", border_radius="md", flex="1", text_align="center",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Losses", font_size="xs", color="gray"),
                                    rx.hstack(
                                        rx.text(AppState.comparison_total_losses, color="red", font_weight="bold"),
                                        rx.text("vs", font_size="xs", color="gray"),
                                        rx.text(AppState.buffer_compare_total_losses, color="orange", font_weight="bold"),
                                        spacing="1",
                                    ),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Net Change", font_size="xs", color="gray"),
                                    rx.hstack(
                                        rx.text(AppState.comparison_net_change, font_weight="bold"),
                                        rx.text("vs", font_size="xs", color="gray"),
                                        rx.text(AppState.buffer_compare_net_change, font_weight="bold"),
                                        spacing="1",
                                    ),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="blue.50", border_radius="md", flex="1", text_align="center",
                            ),
                            width="100%", spacing="2",
                        ),
                        # Gains/losses charts side-by-side
                        _side_by_side_charts(
                            AppState.gains_losses_chart,
                            AppState.buffer_compare_gains_losses_chart,
                            left_label="🟠 Territory — class gains & losses",
                            right_label="🔵 Buffer — class gains & losses",
                        ),
                        # % change charts side-by-side
                        _side_by_side_charts(
                            AppState.change_pct_chart,
                            AppState.buffer_compare_change_pct_chart,
                            left_label="🟠 Territory — % change per class",
                            right_label="🔵 Buffer — % change per class",
                        ),
                        spacing="3", width="100%",
                    ),
                    padding="0.75rem",
                    border="1px solid #86EFAC",
                    border_radius="md",
                    bg="white",
                    width="100%",
                ),
                rx.box(
                    rx.hstack(
                        rx.icon("info", size=14, color="#93C5FD"),
                        rx.text(
                            "Run '📅 Compare Years' to see gains & losses side-by-side with the buffer zone.",
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
            ),
            spacing="3",
            width="100%",
        ),
        rx.box(),
    )


def _glad_table_compact(data) -> rx.Component:
    """Compact GLAD class table (for side-by-side display)."""
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Class"),
                rx.table.column_header_cell("Area (ha)"),
            )
        ),
        rx.table.body(
            rx.foreach(
                data,
                lambda row: rx.table.row(
                    rx.table.cell(row.get("Class", ""), font_size="xs"),
                    rx.table.cell(row.get("Area_ha", "").to(str), font_size="xs"),
                ),
            )
        ),
        width="100%",
        variant="surface",
        size="1",
    )


def _buffer_comparison_hansen() -> rx.Component:
    """Hansen/GLAD buffer zone section — chart and table side-by-side."""
    return rx.cond(
        AppState.buffer_hansen_result != None,
        rx.vstack(
            rx.box(
                _buffer_header(
                    "Buffer Zone — Hansen/GLAD Comparison",
                    AppState.buffer_hansen_summary.get("name", "Buffer"),
                ),
                padding="0.75rem",
                border="2px solid #93C5FD",
                border_radius="md",
                bg="blue.50",
                width="100%",
            ),
            # Metrics
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
            # Charts side-by-side
            _side_by_side_charts(
                AppState.glad_bar_chart,
                AppState.buffer_hansen_bar_chart,
                left_label="🟠 Territory — class distribution",
                right_label="🔵 Buffer — class distribution",
            ),
            # Tables side-by-side
            rx.hstack(
                rx.box(
                    rx.text("🟠 Territory", font_size="xs", font_weight="700", color="#FF4500", margin_bottom="0.25rem"),
                    _glad_table_compact(AppState.glad_table_data),
                    flex="1", overflow_x="auto",
                ),
                rx.box(
                    rx.text("🔵 Buffer", font_size="xs", font_weight="700", color="#1D4ED8", margin_bottom="0.25rem"),
                    _glad_table_compact(AppState.buffer_glad_table_data),
                    flex="1", overflow_x="auto",
                ),
                width="100%", spacing="2", align_items="flex-start",
            ),
            spacing="3",
            width="100%",
            padding="0.75rem",
            border="1px solid #93C5FD",
            border_radius="md",
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
                # Summary metrics + bar chart side-by-side
                _side_by_side_charts(
                    AppState.gfc_bar_chart,
                    AppState.buffer_gfc_bar_chart,
                    left_label="🟠 Territory — GFC summary",
                    right_label="🔵 Buffer — GFC summary",
                ),
                # Forest Loss by Year — chart + table side-by-side
                rx.cond(
                    AppState.buffer_gfc_loss_by_year.length() > 0,
                    rx.vstack(
                        rx.divider(),
                        rx.hstack(
                            rx.icon("trending-down", size=14, color="#e74c3c"),
                            rx.text("Forest Loss by Year — Territory vs Buffer", font_size="sm", font_weight="700"),
                            spacing="2", align_items="center",
                        ),
                        _side_by_side_charts(
                            AppState.gfc_loss_chart,
                            AppState.buffer_gfc_loss_chart,
                            left_label="🟠 Territory — annual loss",
                            right_label="🔵 Buffer — annual loss",
                        ),
                        # Loss tables side-by-side
                        rx.hstack(
                            rx.box(
                                rx.text("🟠 Territory", font_size="xs", font_weight="700", color="#FF4500", margin_bottom="0.25rem"),
                                rx.table.root(
                                    rx.table.header(rx.table.row(
                                        rx.table.column_header_cell("Year"),
                                        rx.table.column_header_cell("Area (ha)"),
                                    )),
                                    rx.table.body(rx.foreach(
                                        AppState.gfc_loss_by_year,
                                        lambda row: rx.table.row(
                                            rx.table.cell(row.get("Year", ""), font_size="xs"),
                                            rx.table.cell(row.get("Area_ha", "").to(str), font_size="xs"),
                                        ),
                                    )),
                                    width="100%", variant="surface", size="1",
                                ),
                                flex="1", overflow_x="auto",
                            ),
                            rx.box(
                                rx.text("🔵 Buffer", font_size="xs", font_weight="700", color="#1D4ED8", margin_bottom="0.25rem"),
                                rx.table.root(
                                    rx.table.header(rx.table.row(
                                        rx.table.column_header_cell("Year"),
                                        rx.table.column_header_cell("Area (ha)"),
                                    )),
                                    rx.table.body(rx.foreach(
                                        AppState.buffer_gfc_loss_by_year,
                                        lambda row: rx.table.row(
                                            rx.table.cell(row.get("Year", ""), font_size="xs"),
                                            rx.table.cell(row.get("Area_ha", "").to(str), font_size="xs"),
                                        ),
                                    )),
                                    width="100%", variant="surface", size="1",
                                ),
                                flex="1", overflow_x="auto",
                            ),
                            width="100%", spacing="2", align_items="flex-start",
                        ),
                        spacing="3", width="100%",
                    ),
                    rx.box(),
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


def _buffer_compare_label() -> rx.Component:
    """Inline buffer comparison label strip used in the Compare tab."""
    return rx.hstack(
        rx.badge("🟠 Territory", color_scheme="orange", variant="surface", size="1"),
        rx.text("vs", font_size="xs", color="gray"),
        rx.badge("🔵 Buffer zone", color_scheme="blue", variant="surface", size="1"),
        rx.badge(
            AppState.buffer_compare_summary.get("name", "Buffer"),
            color_scheme="gray", variant="outline", size="1",
        ),
        spacing="2",
        align_items="center",
        padding="0.25rem 0",
    )


# -----------------------------------------------------------------------
# Tab 1: MapBiomas Analysis
# -----------------------------------------------------------------------

def mapbiomas_tab() -> rx.Component:
    """MapBiomas land cover analysis tab. Displays mapbiomas_analysis_result or generic analysis_results."""
    return rx.vstack(
        rx.heading(AppState.tr["mapbiomas_analysis_title"], size="3"),
        _area_basis_note(),
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
        _area_basis_note(),
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
                # Show side-by-side when buffer data available
                rx.cond(
                    AppState.buffer_hansen_result != None,
                    _side_by_side_charts(
                        rx.cond(has_glad, AppState.glad_bar_chart, AppState.hansen_balance_chart),
                        AppState.buffer_hansen_bar_chart,
                        left_label="🟠 Territory",
                        right_label="🔵 Buffer",
                    ),
                    rx.box(
                        rx.cond(
                            has_glad,
                            _plotly_safe(AppState.glad_bar_chart),
                            _plotly_safe(AppState.hansen_balance_chart),
                        ),
                        width="100%",
                    ),
                ),
                rx.divider(),
                rx.heading("🌿 Detailed Class Data", size="4"),
                rx.cond(
                    AppState.buffer_hansen_result != None,
                    # Side-by-side tables when buffer available
                    rx.hstack(
                        rx.box(
                            rx.text("🟠 Territory", font_size="xs", font_weight="700", color="#FF4500", margin_bottom="0.25rem"),
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
                                    width="100%", overflow_x="auto",
                                ),
                            ),
                            flex="1", overflow_x="auto",
                        ),
                        rx.box(
                            rx.text("🔵 Buffer", font_size="xs", font_weight="700", color="#1D4ED8", margin_bottom="0.25rem"),
                            _glad_table(AppState.buffer_glad_table_data),
                            flex="1", overflow_x="auto",
                        ),
                        width="100%", spacing="2", align_items="flex-start",
                    ),
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
        _area_basis_note(),
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
                        # Metrics row — show buffer total if available
                        rx.hstack(
                            rx.box(
                                rx.vstack(
                                    rx.text("Total Loss", font_size="xs", color="gray"),
                                    rx.cond(
                                        AppState.buffer_gfc_result != None,
                                        rx.hstack(
                                            rx.text(AppState.gfc_summary_loss, color="red", font_weight="bold"),
                                            rx.text("vs", font_size="xs", color="gray"),
                                            rx.text(AppState.buffer_gfc_summary.get("loss", "…"), color="orange", font_weight="bold"),
                                            spacing="1",
                                        ),
                                        rx.text(AppState.gfc_summary_loss, font_weight="bold", color="red"),
                                    ),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="red.50", border_radius="md", flex="1", text_align="center",
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Years with Loss", font_size="xs", color="gray"),
                                    rx.cond(
                                        AppState.buffer_gfc_result != None,
                                        rx.hstack(
                                            rx.text(AppState.gfc_loss_by_year.length().to(str), color="orange", font_weight="bold"),
                                            rx.text("vs", font_size="xs", color="gray"),
                                            rx.text(AppState.buffer_gfc_loss_by_year.length().to(str), color="blue", font_weight="bold"),
                                            spacing="1",
                                        ),
                                        rx.text(AppState.gfc_loss_by_year.length().to(str), font_weight="bold", color="orange"),
                                    ),
                                    spacing="0", align="center",
                                ),
                                padding="0.5rem", bg="orange.50", border_radius="md", flex="1", text_align="center",
                            ),
                            width="100%", spacing="2",
                        ),
                        # Charts — side-by-side if buffer available
                        rx.cond(
                            AppState.buffer_gfc_result != None,
                            _side_by_side_charts(
                                AppState.gfc_loss_chart,
                                AppState.buffer_gfc_loss_chart,
                                left_label="🟠 Territory — annual loss",
                                right_label="🔵 Buffer — annual loss",
                            ),
                            rx.box(_plotly_safe(AppState.gfc_loss_chart), width="100%"),
                        ),
                        # Tables — side-by-side if buffer available
                        rx.cond(
                            AppState.buffer_gfc_result != None,
                            rx.hstack(
                                rx.box(
                                    rx.text("🟠 Territory", font_size="xs", font_weight="700", color="#FF4500", margin_bottom="0.25rem"),
                                    rx.table.root(
                                        rx.table.header(rx.table.row(
                                            rx.table.column_header_cell("Year"),
                                            rx.table.column_header_cell("Area (ha)"),
                                            rx.table.column_header_cell("Pixels"),
                                        )),
                                        rx.table.body(rx.foreach(
                                            AppState.gfc_loss_by_year,
                                            lambda row: rx.table.row(
                                                rx.table.cell(row.get("Year", "")),
                                                rx.table.cell(row.get("Area_ha", "").to(str)),
                                                rx.table.cell(row.get("Pixels", "").to(str)),
                                            ),
                                        )),
                                        width="100%", variant="surface", size="1",
                                    ),
                                    flex="1", overflow_x="auto",
                                ),
                                rx.box(
                                    rx.text("🔵 Buffer", font_size="xs", font_weight="700", color="#1D4ED8", margin_bottom="0.25rem"),
                                    rx.table.root(
                                        rx.table.header(rx.table.row(
                                            rx.table.column_header_cell("Year"),
                                            rx.table.column_header_cell("Area (ha)"),
                                            rx.table.column_header_cell("Pixels"),
                                        )),
                                        rx.table.body(rx.foreach(
                                            AppState.buffer_gfc_loss_by_year,
                                            lambda row: rx.table.row(
                                                rx.table.cell(row.get("Year", "")),
                                                rx.table.cell(row.get("Area_ha", "").to(str)),
                                                rx.table.cell(row.get("Pixels", "").to(str)),
                                            ),
                                        )),
                                        width="100%", variant="surface", size="1",
                                    ),
                                    flex="1", overflow_x="auto",
                                ),
                                width="100%", spacing="2", align_items="flex-start",
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
                rx.button(
                    AppState.tr["export_as_csv"],
                    on_click=AppState.download_gfc_csv,
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
        _area_basis_note(),
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

def _compare_col_header(label: str, subtitle: rx.Var, bg: str, border: str) -> rx.Component:
    """Sticky column header for the 2-column Compare layout."""
    return rx.box(
        rx.hstack(
            rx.text(label, font_size="sm", font_weight="700", color=border),
            rx.text(subtitle, font_size="xs", color="gray"),
            spacing="2", align_items="center", flex_wrap="wrap",
        ),
        padding="0.4rem 0.75rem",
        bg=bg,
        border="1px solid " + border,
        border_radius="md",
        width="100%",
    )


def _compare_row(left: rx.Component, right: rx.Component) -> rx.Component:
    """Half-width side-by-side row used throughout the Compare tab."""
    return rx.hstack(
        rx.box(left, flex="1", min_width="0"),
        rx.box(right, flex="1", min_width="0"),
        width="100%",
        spacing="3",
        align_items="flex-start",
    )


def _compare_chart_box(label: str, label_color: str, chart_var: rx.Var) -> rx.Component:
    """Labeled chart block for one column of the Compare tab."""
    return rx.vstack(
        rx.text(label, font_size="xs", font_weight="600", color=label_color,
                text_align="center", width="100%"),
        _plotly_safe(chart_var),
        width="100%", spacing="1",
    )


def _compare_transition_block(
    icon_name: str, section_title: str, chart_var: rx.Var,
    color: str = "purple",
) -> rx.Component:
    """Single transition chart block (territory OR buffer version)."""
    return rx.vstack(
        rx.hstack(
            rx.icon(icon_name, size=14, color=color),
            rx.text(section_title, font_weight="bold", font_size="sm"),
            spacing="2", align_items="center",
        ),
        _plotly_safe(chart_var),
        width="100%", spacing="2",
    )


def _compare_metrics_row(has_buffer: rx.Var) -> rx.Component:
    """Summary metrics strip (gains / losses / net change) with optional buffer values."""
    return rx.hstack(
        rx.box(
            rx.vstack(
                rx.text(AppState.tr["total_gains"], font_size="xs", color="gray"),
                rx.cond(
                    has_buffer,
                    rx.hstack(
                        rx.text(AppState.comparison_total_gains, color="green", font_weight="bold"),
                        rx.text("vs", font_size="2xs", color="gray"),
                        rx.text(AppState.buffer_compare_total_gains, color="teal", font_weight="bold"),
                        spacing="1",
                    ),
                    rx.text(AppState.comparison_total_gains, color="green", font_weight="bold"),
                ),
                spacing="0", align="center",
            ),
            padding="0.75rem", bg="green.50", border_radius="md", flex="1", text_align="center",
        ),
        rx.box(
            rx.vstack(
                rx.text(AppState.tr["total_losses"], font_size="xs", color="gray"),
                rx.cond(
                    has_buffer,
                    rx.hstack(
                        rx.text(AppState.comparison_total_losses, color="red", font_weight="bold"),
                        rx.text("vs", font_size="2xs", color="gray"),
                        rx.text(AppState.buffer_compare_total_losses, color="orange", font_weight="bold"),
                        spacing="1",
                    ),
                    rx.text(AppState.comparison_total_losses, color="red", font_weight="bold"),
                ),
                spacing="0", align="center",
            ),
            padding="0.75rem", bg="red.50", border_radius="md", flex="1", text_align="center",
        ),
        rx.box(
            rx.vstack(
                rx.text(AppState.tr["net_change"], font_size="xs", color="gray"),
                rx.cond(
                    has_buffer,
                    rx.hstack(
                        rx.text(AppState.comparison_net_change, font_weight="bold"),
                        rx.text("vs", font_size="2xs", color="gray"),
                        rx.text(AppState.buffer_compare_net_change, font_weight="bold"),
                        spacing="1",
                    ),
                    rx.text(AppState.comparison_net_change, font_weight="bold"),
                ),
                spacing="0", align="center",
            ),
            padding="0.75rem", bg="blue.50", border_radius="md", flex="1", text_align="center",
        ),
        width="100%", spacing="2",
    )


def comparison_tab() -> rx.Component:
    """Year-to-year comparison tab.

    Layout when buffer available:
      Persistent column headers (🟠 Territory | 🔵 Buffer Zone)
      Row 1 – Year-over-year land cover bar chart
      Row 2 – Metrics strip (gains / losses / net)
      Row 3 – Gains & losses chart
      Row 4 – % Change per class chart
      Row 5 – Sankey transition diagram
      Row 6 – Sunburst transition diagram
      Row 7 – Transition matrix heatmap
    """
    has_buffer = AppState.buffer_compare_result != None

    return rx.vstack(
        rx.heading(AppState.tr["year_comparison_results"], size="3"),
        _area_basis_note(),
        rx.cond(
            AppState.comparison_available,
            rx.vstack(
                # ── Column headers (only when buffer is available) ────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_col_header(
                            "🟠 Territory",
                            AppState.selected_territory,
                            "#FFF7ED", "#FF4500",
                        ),
                        _compare_col_header(
                            "🔵 Buffer Zone",
                            AppState.buffer_compare_summary.get("name", "Buffer"),
                            "#EFF6FF", "#1D4ED8",
                        ),
                    ),
                    rx.box(),
                ),

                rx.divider(),

                # ── Row 1: Year-over-year land cover ─────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_chart_box(
                            "Year-over-year land cover",
                            "#FF4500", AppState.comparison_chart,
                        ),
                        _compare_chart_box(
                            "Year-over-year land cover",
                            "#1D4ED8", AppState.buffer_comparison_chart,
                        ),
                    ),
                    rx.box(_plotly_safe(AppState.comparison_chart), width="100%"),
                ),

                rx.divider(),

                # ── Row 2: Metrics strip ──────────────────────────────────────
                rx.text(
                    AppState.tr["total_gains"] + " / " + AppState.tr["total_losses"],
                    font_weight="bold", font_size="sm",
                ),
                _compare_metrics_row(has_buffer),

                rx.divider(),

                # ── Row 3: Gains & losses ─────────────────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_chart_box(
                            "Class gains & losses",
                            "#FF4500", AppState.gains_losses_chart,
                        ),
                        _compare_chart_box(
                            "Class gains & losses",
                            "#1D4ED8", AppState.buffer_compare_gains_losses_chart,
                        ),
                    ),
                    rx.box(_plotly_safe(AppState.gains_losses_chart), width="100%"),
                ),

                # ── Row 4: % Change per class ─────────────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_chart_box(
                            "% change per class",
                            "#FF4500", AppState.change_pct_chart,
                        ),
                        _compare_chart_box(
                            "% change per class",
                            "#1D4ED8", AppState.buffer_compare_change_pct_chart,
                        ),
                    ),
                    rx.box(_plotly_safe(AppState.change_pct_chart), width="100%"),
                ),

                rx.divider(),

                # ── Row 5: Sankey ─────────────────────────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_transition_block(
                            "git-branch",
                            "Land Cover Transitions (Sankey)",
                            AppState.sankey_chart,
                            "purple",
                        ),
                        _compare_transition_block(
                            "git-branch",
                            "Land Cover Transitions (Sankey)",
                            AppState.buffer_sankey_chart,
                            "#1D4ED8",
                        ),
                    ),
                    _compare_transition_block(
                        "git-branch",
                        "Land Cover Transitions (Sankey)",
                        AppState.sankey_chart,
                        "purple",
                    ),
                ),

                rx.divider(),

                # ── Row 6: Sunburst ───────────────────────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_transition_block(
                            "pie-chart",
                            "Class Transitions (Sunburst)",
                            AppState.sunburst_transitions_chart,
                            "purple",
                        ),
                        _compare_transition_block(
                            "pie-chart",
                            "Class Transitions (Sunburst)",
                            AppState.buffer_sunburst_chart,
                            "#1D4ED8",
                        ),
                    ),
                    _compare_transition_block(
                        "pie-chart",
                        "Class Transitions (Sunburst)",
                        AppState.sunburst_transitions_chart,
                        "purple",
                    ),
                ),

                rx.divider(),

                # ── Row 7: Transition Matrix ──────────────────────────────────
                rx.cond(
                    has_buffer,
                    _compare_row(
                        _compare_transition_block(
                            "grid-3x3",
                            "Transition Matrix (Heatmap)",
                            AppState.transition_matrix_chart,
                            "#ed8936",
                        ),
                        _compare_transition_block(
                            "grid-3x3",
                            "Transition Matrix (Heatmap)",
                            AppState.buffer_transition_matrix_chart,
                            "#1D4ED8",
                        ),
                    ),
                    _compare_transition_block(
                        "grid-3x3",
                        "Transition Matrix (Heatmap)",
                        AppState.transition_matrix_chart,
                        "#ed8936",
                    ),
                ),

                rx.hstack(
                    rx.button(
                        AppState.tr["download_comparison_csv"],
                        on_click=AppState.download_comparison_csv,
                        size="1",
                        color_scheme="blue",
                        variant="outline",
                    ),
                    # When buffer data is also available, the download bundles both
                    # territory + buffer CSVs in a ZIP so the filename is self-descriptive.
                    rx.cond(
                        AppState.buffer_mapbiomas_comparison_result != None,
                        rx.text(
                            "↳ Includes territory + buffer (ZIP)",
                            font_size="2xs",
                            color="gray",
                            align_self="center",
                        ),
                        rx.box(),
                    ),
                    spacing="3",
                    align_items="center",
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

# -----------------------------------------------------------------------
# Advanced viz tabs (ported from Batch Processing) — Maps / Multi-window /
# Deforestation timeline.  Config + on-demand Run controls live in-tab so the
# sidebars stay untouched; both geometry & territory pages get them via
# analysis_tabs().
# -----------------------------------------------------------------------

_ADV_ORANGE = "#EA580C"
_ADV_ORANGE_DARK = "#C2410C"
_ADV_ORANGE_LIGHT = "#FFF7ED"
_ADV_ORANGE_BORDER = "#FDBA74"
_ADV_GREEN = "#1a472a"


def _adv_run_button(label: str, handler, pending_var: rx.Var,
                    pending_label: str) -> rx.Component:
    """Orange on-demand Run/Generate button with a busy state."""
    return rx.cond(
        pending_var,
        rx.button(
            rx.hstack(rx.spinner(size="2"), rx.text(pending_label), spacing="2",
                      align_items="center"),
            is_disabled=True, size="3", bg="#9CA3AF", color="white",
            font_weight="bold",
        ),
        rx.button(
            label, on_click=handler, size="3", bg=_ADV_ORANGE, color="white",
            font_weight="bold", _hover={"bg": _ADV_ORANGE_DARK}, cursor="pointer",
        ),
    )


def _adv_chart_section(title: str, chart_var: rx.Var,
                       min_height: str = "420px") -> rx.Component:
    return rx.vstack(
        rx.text(title, font_size="sm", font_weight="700", color="#374151"),
        _plotly_safe(chart_var, min_height),
        spacing="1", width="100%",
    )


def maps_tab() -> rx.Component:
    """PNG maps & charts: satellite + MapBiomas y1/y2 (+ aux rasters)."""
    aux = (
        ("🌳 Deforestation & secondary veg.", AppState.map_aux_deforestation,
         AppState.toggle_map_aux_deforestation),
        ("🔥 Annual burned area", AppState.map_aux_fire_scar,
         AppState.toggle_map_aux_fire_scar),
        ("📊 Fire frequency (1985–2024)", AppState.map_aux_fire_frequency,
         AppState.toggle_map_aux_fire_frequency),
        ("📅 Year of last fire", AppState.map_aux_fire_year_last,
         AppState.toggle_map_aux_fire_year_last),
        ("⛏️ Mining substances", AppState.map_aux_mining,
         AppState.toggle_map_aux_mining),
        ("🌾 Agriculture — cycles", AppState.map_aux_agriculture,
         AppState.toggle_map_aux_agriculture),
    )
    return rx.vstack(
        rx.hstack(
            rx.heading("🗺️ Maps & Charts (satellite + MapBiomas y1/y2)",
                       size="3", color=_ADV_GREEN),
            rx.spacer(),
            rx.badge(
                AppState.comparison_year1.to(str) + " / " + AppState.comparison_year2.to(str),
                color_scheme="orange", variant="soft",
            ),
            width="100%", align_items="center",
        ),
        rx.text(
            "Render publication-quality PNG maps — satellite basemap and "
            "MapBiomas land cover for the two comparison years, plus any "
            "auxiliary rasters below. Buffer overlay is included when a buffer "
            "zone is active. Preview inline and download as a ZIP.",
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.box(
            rx.vstack(
                rx.text("Extra MapBiomas rasters (year 2)", font_size="xs",
                        font_weight="600", color="#374151",
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.flex(
                    *[
                        rx.checkbox(lbl, checked=val, on_change=tog,
                                    color_scheme="orange")
                        for lbl, val, tog in aux
                    ],
                    wrap="wrap", gap="0.75rem 1.5rem",
                ),
                spacing="2", width="100%",
            ),
            padding="0.75rem", bg=_ADV_ORANGE_LIGHT,
            border="1px solid " + _ADV_ORANGE_BORDER, border_radius="md",
            width="100%",
        ),
        rx.hstack(
            _adv_run_button("🗺️ Generate maps", AppState.generate_map_set,
                            AppState.mapset_pending, "Generating maps…"),
            rx.cond(
                AppState.mapset_images.length() > 0,
                rx.button(
                    "⬇️ Download ZIP", on_click=AppState.download_map_set_zip,
                    size="3", bg="#16A34A", color="white", font_weight="bold",
                    _hover={"bg": "#15803D"}, cursor="pointer",
                ),
                rx.box(),
            ),
            spacing="3", width="100%",
        ),
        rx.divider(),
        rx.cond(
            AppState.mapset_images.length() > 0,
            rx.grid(
                rx.foreach(
                    AppState.mapset_images,
                    lambda m: rx.vstack(
                        rx.text(m["name"], font_size="xs", font_weight="600",
                                color="#374151"),
                        rx.image(src=m["data_uri"], width="100%",
                                 border="1px solid #e5e7eb", border_radius="md"),
                        spacing="1", width="100%",
                    ),
                ),
                columns="2", spacing="3", width="100%",
            ),
            _no_data_placeholder("Generate maps to preview them here"),
        ),
        spacing="3", width="100%", padding="0.5rem",
    )


def multi_window_tab() -> rx.Component:
    """Multi-time-window MapBiomas: multi-stage Sankey + per-pair Sunbursts."""
    return rx.vstack(
        rx.heading("🌀 Multiple time-window MapBiomas (Sankey + Sunburst)",
                   size="3", color=_ADV_GREEN),
        rx.text(
            "Chain MapBiomas land-cover transitions across 3–N years into a "
            "single multi-stage Sankey, with one Sunburst per consecutive "
            "year-pair. Buffer-ring variants render when a buffer is active.",
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Mode:", font_size="xs", color="#6B7280", width="60px"),
                    rx.select(["constant", "custom"], value=AppState.mw_mode,
                              on_change=AppState.set_mw_mode, size="2", width="130px"),
                    spacing="2", align_items="center",
                ),
                rx.cond(
                    AppState.mw_mode == "constant",
                    rx.hstack(
                        rx.text("Step (years):", font_size="xs", color="#6B7280",
                                width="100px"),
                        rx.select(["1", "2", "4", "5", "8"], value=AppState.mw_step,
                                  on_change=AppState.set_mw_step, size="2", width="80px"),
                        rx.text("1985 → 2024 forced as last year", font_size="xs",
                                color="#9CA3AF"),
                        spacing="2", align_items="center",
                    ),
                    rx.vstack(
                        rx.text("Custom years (3 to 10, comma-separated, 1985–2024)",
                                font_size="xs", color="#6B7280"),
                        rx.input(value=AppState.mw_custom_years,
                                 on_change=AppState.set_mw_custom_years,
                                 placeholder="1985, 1994, 2004, 2014, 2024", size="2",
                                 width="100%"),
                        spacing="1", width="100%",
                    ),
                ),
                rx.text("Active years: " + AppState.mw_resolved_years.to(str),
                        font_size="xs", color="#374151"),
                spacing="2", width="100%",
            ),
            padding="0.75rem", bg=_ADV_ORANGE_LIGHT,
            border="1px solid " + _ADV_ORANGE_BORDER, border_radius="md",
            width="100%",
        ),
        _adv_run_button("🌀 Run multi-window analysis",
                        AppState.run_multi_window_analysis,
                        AppState.mw_pending, "Computing transitions…"),
        rx.divider(),
        rx.cond(
            AppState.mw_has_result,
            rx.vstack(
                _adv_chart_section("🟠 Territory — multi-stage Sankey",
                                   AppState.multi_window_sankey_chart, "440px"),
                rx.cond(
                    AppState.mw_sunburst_figs.length() > 0,
                    rx.vstack(
                        rx.text("Per-pair Sunbursts", font_size="sm",
                                font_weight="700", color="#374151"),
                        rx.grid(
                            rx.foreach(
                                AppState.mw_sunburst_figs,
                                lambda f: rx.box(
                                    rx.plotly(data=f, use_resize_handler=True),
                                    width="100%",
                                ),
                            ),
                            columns="2", spacing="3", width="100%",
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.box(),
                ),
                rx.cond(
                    AppState.mw_has_buffer,
                    _buffer_box(
                        rx.vstack(
                            _adv_chart_section("🔵 Buffer — multi-stage Sankey",
                                               AppState.buffer_multi_window_sankey_chart,
                                               "440px"),
                            rx.cond(
                                AppState.buffer_mw_sunburst_figs.length() > 0,
                                rx.grid(
                                    rx.foreach(
                                        AppState.buffer_mw_sunburst_figs,
                                        lambda f: rx.box(
                                            rx.plotly(data=f, use_resize_handler=True),
                                            width="100%",
                                        ),
                                    ),
                                    columns="2", spacing="3", width="100%",
                                ),
                                rx.box(),
                            ),
                            spacing="2", width="100%",
                        )
                    ),
                    rx.box(),
                ),
                spacing="4", width="100%",
            ),
            _no_data_placeholder("Run multi-window analysis to see Sankey + Sunburst"),
        ),
        spacing="3", width="100%", padding="0.5rem",
    )


def treemap_tab() -> rx.Component:
    """Faceted per-class transition treemaps.

    Two views over the same transition data that feeds the Sankey/Sunburst:
      • Whole period — from the year comparison (territory, + buffer if active).
      • Per-step — one faceted treemap per consecutive year-pair, populated by
        running the multi-window analysis (🌀 tab).
    Each facet is a single class; its tiles are what that class *became*.
    """
    has_buffer = AppState.buffer_compare_result != None

    return rx.vstack(
        rx.heading("🟦 Transition treemaps by class", size="3", color=_ADV_GREEN),
        rx.text(
            "For each land-cover class, a treemap of what it became over the "
            "period — the same transition data as the Sankey/Sunburst, packed "
            "as area rectangles (facet titles report how much of the class "
            "stayed). The whole-period view uses the year comparison; the "
            "per-step views use the multi-window pairs (run the 🌀 Multi-window "
            "tab to populate them).",
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.divider(),

        # ── Whole period ─────────────────────────────────────────────────────
        rx.text("Whole period", font_size="sm", font_weight="700", color="#374151"),
        rx.cond(
            AppState.comparison_available,
            rx.cond(
                has_buffer,
                _compare_row(
                    _compare_transition_block(
                        "grid-3x3", "🟠 Territory",
                        AppState.treemap_transitions_chart, "purple",
                    ),
                    _compare_transition_block(
                        "grid-3x3", "🔵 Buffer Zone",
                        AppState.buffer_treemap_chart, "#1D4ED8",
                    ),
                ),
                _compare_transition_block(
                    "grid-3x3", "Class transition treemaps",
                    AppState.treemap_transitions_chart, "purple",
                ),
            ),
            _no_data_placeholder("Run a year comparison to see whole-period treemaps"),
        ),

        rx.divider(),

        # ── Per-step (multi-window) ──────────────────────────────────────────
        rx.text("Per-step (multi-window)", font_size="sm", font_weight="700",
                color="#374151"),
        rx.cond(
            AppState.mw_treemap_figs.length() > 0,
            rx.vstack(
                rx.grid(
                    rx.foreach(
                        AppState.mw_treemap_figs,
                        lambda f: rx.box(
                            rx.plotly(data=f, use_resize_handler=True),
                            width="100%",
                        ),
                    ),
                    columns="1", spacing="3", width="100%",
                ),
                rx.cond(
                    AppState.mw_has_buffer & (AppState.buffer_mw_treemap_figs.length() > 0),
                    _buffer_box(
                        rx.vstack(
                            rx.text("🔵 Buffer ring", font_size="sm",
                                    font_weight="700", color="#1D4ED8"),
                            rx.grid(
                                rx.foreach(
                                    AppState.buffer_mw_treemap_figs,
                                    lambda f: rx.box(
                                        rx.plotly(data=f, use_resize_handler=True),
                                        width="100%",
                                    ),
                                ),
                                columns="1", spacing="3", width="100%",
                            ),
                            spacing="2", width="100%",
                        )
                    ),
                    rx.box(),
                ),
                spacing="3", width="100%",
            ),
            _no_data_placeholder(
                "Run the 🌀 Multi-window analysis to see per-step treemaps"
            ),
        ),
        spacing="3", width="100%", padding="0.5rem",
    )


def timeline_tab() -> rx.Component:
    """Deforestation timeline: Hansen + MapBiomas + Fire with policy context."""
    incl = (
        ("🌲 Hansen forest loss", AppState.tl_include_hansen,
         AppState.toggle_tl_include_hansen),
        ("🌳 MapBiomas primary defor.", AppState.tl_include_defor,
         AppState.toggle_tl_include_defor),
        ("🌱 Secondary regrowth", AppState.tl_include_secondary,
         AppState.toggle_tl_include_secondary),
        ("🔥 Fire scar", AppState.tl_include_fire,
         AppState.toggle_tl_include_fire),
    )
    return rx.vstack(
        rx.heading("📈 Deforestation timeline (Hansen + MapBiomas + Fire)",
                   size="3", color=_ADV_GREEN),
        rx.text(
            "Annual deforestation, regrowth and fire indicators across the "
            "comparison year range, framed by Brazilian political context "
            "(president / governor stripes, top), the ENSO Oceanic Niño Index "
            "(El Niño / La Niña strip) and forest-policy milestones (bottom). "
            "Three views: raw values, 5-year moving average, and "
            "first/second derivatives.",
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.box(
            rx.vstack(
                rx.text("Indicators", font_size="xs", font_weight="600",
                        color="#374151", text_transform="uppercase",
                        letter_spacing="0.05em"),
                rx.flex(
                    *[
                        rx.checkbox(lbl, checked=val, on_change=tog,
                                    color_scheme="orange")
                        for lbl, val, tog in incl
                    ],
                    wrap="wrap", gap="0.75rem 1.5rem",
                ),
                spacing="2", width="100%",
            ),
            padding="0.75rem", bg=_ADV_ORANGE_LIGHT,
            border="1px solid " + _ADV_ORANGE_BORDER, border_radius="md",
            width="100%",
        ),
        rx.text(
            "ℹ️ Hansen loss uses the Hansen GFC result — run the Hansen GFC "
            "analysis first for a non-zero forest-loss line.",
            font_size="xs", color="#9CA3AF",
        ),
        _adv_run_button("📈 Run deforestation timeline",
                        AppState.run_deforestation_timeline,
                        AppState.timeline_pending, "Building timeline…"),
        rx.divider(),
        rx.cond(
            AppState.timeline_has_data,
            rx.vstack(
                _adv_chart_section("Raw annual values", AppState.timeline_raw_chart),
                _adv_chart_section("5-year moving average", AppState.timeline_ma_chart),
                _adv_chart_section("Derivatives (1st & 2nd difference)",
                                   AppState.timeline_deriv_chart),
                rx.cond(
                    AppState.timeline_has_buffer,
                    _buffer_box(
                        rx.vstack(
                            rx.text("🔵 Buffer zone", font_size="sm",
                                    font_weight="700", color="#1D4ED8"),
                            _adv_chart_section("Raw annual values",
                                               AppState.buffer_timeline_raw_chart),
                            _adv_chart_section("5-year moving average",
                                               AppState.buffer_timeline_ma_chart),
                            _adv_chart_section("Derivatives",
                                               AppState.buffer_timeline_deriv_chart),
                            spacing="2", width="100%",
                        )
                    ),
                    rx.box(),
                ),
                spacing="4", width="100%",
            ),
            _no_data_placeholder(
                "Run the timeline to see Hansen + MapBiomas + Fire with "
                "political/policy context"
            ),
        ),
        spacing="3", width="100%", padding="0.5rem",
    )


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
                rx.tabs.trigger("🟦 Treemaps", value="treemaps"),
                rx.tabs.trigger("🗺️ Maps", value="maps"),
                rx.tabs.trigger("🌀 Multi-window", value="multiwindow"),
                rx.tabs.trigger("📈 Timeline", value="timeline"),
                rx.tabs.trigger(AppState.tr["about_tab"], value="about"),
                # Ten triggers do not fit a phone, and Radix's own tab list
                # wraps them into a four-line block that eats most of a
                # 45vh sheet before any content shows. Scroll them instead:
                # one line, swipe sideways.
                overflow_x="auto",
                flex_shrink="0",
                style={"whiteSpace": "nowrap", "scrollbarWidth": "thin"},
            ),
            rx.tabs.content(mapbiomas_tab(), value="mapbiomas"),
            rx.tabs.content(hansen_tab(), value="hansen"),
            rx.tabs.content(hansen_gfc_tab(), value="gfc"),
            rx.tabs.content(aafc_tab(), value="aafc"),
            rx.tabs.content(comparison_tab(), value="comparison"),
            rx.tabs.content(treemap_tab(), value="treemaps"),
            rx.tabs.content(maps_tab(), value="maps"),
            rx.tabs.content(multi_window_tab(), value="multiwindow"),
            rx.tabs.content(timeline_tab(), value="timeline"),
            rx.tabs.content(about_tab(), value="about"),
            value=AppState.active_analysis_tab,
            on_change=AppState.set_active_analysis_tab,
            width="100%",
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
        # `hidden` used to clip a wide chart or table outright, with no
        # scrollbar and no way to reach it — this panel sits inside a
        # sheet/drawer narrower than its own min-content width on a phone.
        overflow="auto",
    )
