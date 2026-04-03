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
                        # For geometry analysis
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
                    rx.plotly(data=AppState.mapbiomas_bar_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                rx.box(
                    rx.plotly(data=AppState.mapbiomas_pie_chart, use_resize_handler=True),
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
    """Hansen/GLAD forest cover analysis tab.
    Shows geometry_glad_result for geometry GLAD analysis,
    or hansen_analysis_result for territory Hansen analysis.
    """
    has_glad = AppState.geometry_glad_result != None
    has_territory = AppState.hansen_analysis_result != None
    has_data = has_glad | has_territory

    return rx.vstack(
        rx.heading(AppState.tr["hansen_analysis"], size="3"),
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
                # ---- Summary metrics row --------------------------------
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
                # ---- Area distribution chart ----------------------------
                rx.box(
                    rx.cond(
                        has_glad,
                        rx.plotly(data=AppState.glad_bar_chart, use_resize_handler=True),
                        rx.plotly(data=AppState.hansen_balance_chart, use_resize_handler=True),
                    ),
                    width="100%",
                ),
                rx.divider(),
                # ---- Class table (dynamic — use rx.table not data_table) -
                rx.heading("🌿 Class Distribution", size="4"),
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
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 3: Hansen GFC
# -----------------------------------------------------------------------

def _gfc_simple_table(data, cols) -> rx.Component:
    """Render a simple GFC result table using rx.table (column-safe)."""
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
        rx.text(
            "Tree Cover 2000 (baseline) | Tree Loss 2000–2023 | Tree Gain 2000–2012",
            font_size="sm", color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.geometry_gfc_result != None,
            rx.vstack(
                # Info bar
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
                # 4 summary metrics
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("🌳 Tree Cover 2000", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_cover, font_weight="bold", font_size="lg", color="green"),
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
                            rx.text("📉 Forest Loss", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_loss, font_weight="bold", font_size="lg", color="red"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem",
                        bg="red.50",
                        border_radius="md",
                        flex="1",
                        text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("📈 Forest Gain", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_gain, font_weight="bold", font_size="lg", color="teal"),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem",
                        bg="teal.50",
                        border_radius="md",
                        flex="1",
                        text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("⚖️ Net Change", font_size="xs", color="gray"),
                            rx.text(AppState.gfc_summary_net, font_weight="bold", font_size="lg", color="purple"),
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
                rx.divider(),
                # ---- Summary bar chart (Cover / Loss / Gain) ------------
                rx.box(
                    rx.plotly(data=AppState.gfc_bar_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # ---- Summary table (Metric / Area_ha / Percent / Desc) --
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
                # ---- Tree Cover 2000 Categories -------------------------
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
                # ---- Tree Loss by Year ----------------------------------
                rx.cond(
                    AppState.gfc_loss_by_year.length() > 0,
                    rx.vstack(
                        rx.heading("🔥 Forest Loss by Year", size="4"),
                        # Metrics row
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
                        # Loss by year bar chart
                        rx.box(
                            rx.plotly(data=AppState.gfc_loss_chart, use_resize_handler=True),
                            width="100%",
                        ),
                        # Loss by year table
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
                # ---- Tree Gain 2000–2012 --------------------------------
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
                # Side-by-side comparison chart
                rx.box(
                    rx.plotly(data=AppState.comparison_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Gains/Losses
                rx.box(
                    rx.text(AppState.tr["total_gains"] + " / " + AppState.tr["total_losses"], font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.gains_losses_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Change percentage
                rx.box(
                    rx.plotly(data=AppState.change_pct_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Summary stats
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["total_gains"], font_size="xs", color="gray"),
                            rx.text(
                                AppState.comparison_total_gains,
                                font_weight="bold", color="green",
                            ),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="green.50", border_radius="md", flex="1",
                        text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["total_losses"], font_size="xs", color="gray"),
                            rx.text(
                                AppState.comparison_total_losses,
                                font_weight="bold", color="red",
                            ),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="red.50", border_radius="md", flex="1",
                        text_align="center",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text(AppState.tr["net_change"], font_size="xs", color="gray"),
                            rx.text(
                                AppState.comparison_net_change,
                                font_weight="bold",
                            ),
                            spacing="0", align="center",
                        ),
                        padding="0.75rem", bg="blue.50", border_radius="md", flex="1",
                        text_align="center",
                    ),
                    width="100%",
                    spacing="2",
                ),
                rx.divider(),
                # Sankey Diagram
                rx.box(
                    rx.hstack(
                        rx.icon("git-branch", size=16, color="purple"),
                        rx.text("Land Cover Transitions (Sankey)", font_weight="bold", font_size="sm"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.sankey_chart != None,
                        rx.plotly(data=AppState.sankey_chart, use_resize_handler=True),
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
                # Transition Matrix Heatmap
                rx.box(
                    rx.hstack(
                        rx.icon("grid-3x3", size=16, color="orange"),
                        rx.text("Transition Matrix (Heatmap)", font_weight="bold", font_size="sm"),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.transition_matrix_chart != None,
                        rx.plotly(data=AppState.transition_matrix_chart, use_resize_handler=True),
                        rx.text(
                            "No transition data available.",
                            font_size="xs", color="gray", padding="1rem",
                        ),
                    ),
                    width="100%",
                ),
                # CSV download
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
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 6: About / Project Info
# -----------------------------------------------------------------------

def about_tab() -> rx.Component:
    """About tab: territory info + full project context, etymology, data sources."""
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
                        rx.badge("MapBiomas", color_scheme="green"),
                        rx.text("Land cover 1985-2023 (Brazil)", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("Hansen", color_scheme="blue"),
                        rx.text("Forest change 2000-2023 (Global)", font_size="xs"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.badge("AAFC", color_scheme="orange"),
                        rx.text("Crop inventory 2009-2023 (Canada)", font_size="xs"),
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
            rx.text(
                AppState.tr["about_desc"],
                font_size="sm",
                line_height="1.6",
            ),
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
            rx.text(
                AppState.tr["about_supervisor"],
                font_size="xs", color="gray",
            ),
            rx.divider(),
            rx.hstack(
                rx.icon("globe", size=16, color="teal"),
                rx.text(
                    AppState.tr["about_app_name"],
                    font_weight="bold", font_size="sm",
                ),
                rx.text(
                    AppState.tr["about_app_note"],
                    font_size="xs", color="gray",
                ),
                spacing="2",
                align_items="center",
                flex_wrap="wrap",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        AppState.tr["yvynation_meaning"],
                        font_size="xs",
                        font_style="italic",
                        line_height="1.5",
                    ),
                    rx.text(
                        AppState.tr["nation_meaning"],
                        font_size="xs",
                        font_style="italic",
                        line_height="1.5",
                    ),
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
                    rx.badge("MapBiomas", color_scheme="green", variant="solid"),
                    rx.text(AppState.tr["mapbiomas_desc"], font_size="xs"),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("Hansen/GLAD", color_scheme="blue", variant="solid"),
                    rx.text("Global Forest Change - Resolution: 30m, Period: 2000-2024, Global coverage", font_size="xs"),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("AAFC", color_scheme="orange", variant="solid"),
                    rx.text("Annual Crop Inventory - Resolution: 30m, Period: 2009-2023, Canada coverage", font_size="xs"),
                    spacing="2",
                    align_items="start",
                    flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.badge("Territories", color_scheme="purple", variant="solid"),
                    rx.text(AppState.tr["territories_desc"], font_size="xs"),
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

        # --- Technologies ---
        rx.vstack(
            rx.heading(AppState.tr["tech_title"], size="3"),
            rx.flex(
                rx.badge("Python 3.8+", color_scheme="blue", variant="surface"),
                rx.badge("Google Earth Engine", color_scheme="green", variant="surface"),
                rx.badge("Reflex", color_scheme="purple", variant="surface"),
                rx.badge("Plotly", color_scheme="red", variant="surface"),
                rx.badge("Folium / Leaflet", color_scheme="teal", variant="surface"),
                rx.badge("Pandas", color_scheme="orange", variant="surface"),
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
