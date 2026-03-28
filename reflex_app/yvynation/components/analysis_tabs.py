"""
Phase 4: Analysis tabs component - 6 analysis tabs matching Streamlit app.
Tabs: MapBiomas | Hansen/GLAD | Hansen GFC | AAFC | Comparison | About
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
                    rx.text("Total Area", font_size="xs", color="gray"),
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
                    rx.text("Classes", font_size="xs", color="gray"),
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
                    rx.text("Top Class", font_size="xs", color="gray"),
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
                    rx.text("Total Area", font_size="xs", color="gray"),
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
                    rx.text("Classes Found", font_size="xs", color="gray"),
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
                    rx.text("Analysis Year", font_size="xs", color="gray"),
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
    """MapBiomas land cover analysis tab."""
    return rx.vstack(
        rx.heading("MapBiomas Land Cover Analysis", size="3"),
        # Analysis info
        rx.cond(
            AppState.analysis_info_text != "",
            rx.box(
                rx.text(AppState.analysis_info_text, font_size="sm", color="gray"),
                padding="1rem",
                bg="gray.50",
                border_radius="md",
                border_left="4px solid #3182ce",
            ),
            rx.box(),
        ),
        rx.cond(
            AppState.analysis_results.get("type") == "mapbiomas",
            rx.vstack(
                _summary_metrics_row(AppState.analysis_results),
                rx.divider(),
                # Bar chart
                rx.box(
                    rx.text("Land Cover Distribution", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.mapbiomas_bar_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Pie chart
                rx.box(
                    rx.text("Composition", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.mapbiomas_pie_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Data table
                rx.box(
                    rx.text("Data Table", font_weight="bold", font_size="sm"),
                    rx.data_table(
                        data=AppState.analysis_table_data,
                        columns=AppState.analysis_table_columns,
                        pagination=True,
                        search=True,
                    ),
                    width="100%",
                    overflow_x="auto",
                ),
                rx.divider(),
                # CSV Download
                rx.button(
                    "Download CSV",
                    on_click=AppState.download_analysis_csv,
                    color_scheme="blue",
                    size="2",
                    variant="outline",
                ),
                # Quick link to Hansen if available
                rx.cond(
                    AppState.hansen_analysis_result != None,
                    rx.box(
                        rx.text("Hansen results available", font_size="xs", color="orange"),
                        rx.button(
                            "View Hansen Analysis",
                            on_click=lambda: AppState.set_active_tab("hansen"),
                            size="1",
                            color_scheme="orange",
                            variant="outline",
                        ),
                        spacing="2",
                    ),
                    rx.box(),
                ),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder("Select a territory and run MapBiomas analysis"),
        ),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 2: Hansen/GLAD Analysis
# -----------------------------------------------------------------------

def hansen_tab() -> rx.Component:
    """Hansen/GLAD forest change analysis tab."""
    return rx.vstack(
        rx.heading("Hansen/GLAD Forest Change", size="3"),
        # Analysis info
        rx.cond(
            AppState.analysis_info_text != "",
            rx.box(
                rx.text(AppState.analysis_info_text, font_size="sm", color="gray"),
                padding="1rem",
                bg="gray.50",
                border_radius="md",
                border_left="4px solid #ed8936",
            ),
            rx.box(),
        ),
        rx.cond(
            AppState.analysis_results.get("type") == "hansen",
            rx.vstack(
                _hansen_summary_metrics(),
                rx.divider(),
                # Forest balance chart
                rx.box(
                    rx.text("Forest Dynamics Summary", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.hansen_balance_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Data table
                rx.box(
                    rx.text("Data Table", font_weight="bold", font_size="sm"),
                    rx.data_table(
                        data=AppState.analysis_table_data,
                        columns=AppState.analysis_table_columns,
                        pagination=True,
                        search=True,
                    ),
                    width="100%",
                    overflow_x="auto",
                ),
                rx.divider(),
                rx.button(
                    "Download CSV",
                    on_click=AppState.download_analysis_csv,
                    color_scheme="blue",
                    size="2",
                    variant="outline",
                ),
                # Quick link to MapBiomas if available
                rx.cond(
                    AppState.mapbiomas_analysis_result != None,
                    rx.box(
                        rx.text("MapBiomas results available", font_size="xs", color="green"),
                        rx.button(
                            "View MapBiomas Analysis",
                            on_click=lambda: AppState.set_active_tab("mapbiomas"),
                            size="1",
                            color_scheme="green",
                            variant="outline",
                        ),
                        spacing="2",
                    ),
                    rx.box(),
                ),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder("Select a territory and run Hansen analysis"),
        ),
        width="100%",
        spacing="3",
        padding="1rem",
    )


# -----------------------------------------------------------------------
# Tab 3: Hansen GFC
# -----------------------------------------------------------------------

def hansen_gfc_tab() -> rx.Component:
    """Hansen Global Forest Change (tree cover/loss/gain) tab."""
    return rx.vstack(
        rx.heading("Hansen GFC Analysis", size="3"),
        rx.text(
            "Global Forest Change layers: Tree Cover 2000, Tree Loss, Tree Gain",
            font_size="sm", color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.analysis_results.get("type") == "hansen",
            rx.vstack(
                rx.plotly(data=AppState.hansen_balance_chart, use_resize_handler=True),
                spacing="3",
                width="100%",
            ),
            _no_data_placeholder("Run Hansen analysis to see GFC results"),
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
        rx.heading("AAFC Crop Inventory (Canada)", size="3"),
        rx.text(
            "Annual crop inventory data for Canadian territories.",
            font_size="sm", color="gray",
        ),
        rx.divider(),
        rx.cond(
            AppState.selected_country == "Canada",
            _no_data_placeholder("AAFC analysis coming soon - select Canadian territory"),
            rx.vstack(
                rx.icon("info", size=24, color="blue"),
                rx.text(
                    "AAFC data is only available for Canada. Switch country in the sidebar.",
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
        rx.heading("Year Comparison", size="3"),
        rx.cond(
            AppState.comparison_available,
            rx.vstack(
                # Comparison chart
                rx.box(
                    rx.text("Side-by-Side Comparison", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.comparison_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Gains/Losses
                rx.box(
                    rx.text("Gains and Losses", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.gains_losses_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Change percentage
                rx.box(
                    rx.text("Percentage Change", font_weight="bold", font_size="sm"),
                    rx.plotly(data=AppState.change_pct_chart, use_resize_handler=True),
                    width="100%",
                ),
                rx.divider(),
                # Summary stats
                rx.hstack(
                    rx.box(
                        rx.vstack(
                            rx.text("Gains", font_size="xs", color="gray"),
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
                            rx.text("Losses", font_size="xs", color="gray"),
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
                            rx.text("Net Change", font_size="xs", color="gray"),
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
                    rx.text("Land Cover Transitions (Sankey)", font_weight="bold", font_size="sm"),
                    rx.cond(
                        AppState.sankey_chart != None,
                        rx.plotly(data=AppState.sankey_chart, use_resize_handler=True),
                        rx.text(
                            "No transition data available. Run comparison with transition tracking enabled.",
                            font_size="xs", color="gray", padding="1rem",
                        ),
                    ),
                    width="100%",
                ),
                rx.divider(),
                # Transition Matrix
                rx.box(
                    rx.text("Transition Matrix (Heatmap)", font_weight="bold", font_size="sm"),
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
                spacing="3",
                width="100%",
            ),
            rx.vstack(
                _no_data_placeholder("Run a comparison analysis to see year-over-year changes"),
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
# Tab 6: About / Territory Info
# -----------------------------------------------------------------------

def about_tab() -> rx.Component:
    """About / territory info tab."""
    return rx.vstack(
        rx.heading("Territory Information", size="3"),
        rx.divider(),
        rx.cond(
            AppState.selected_territory != None,
            rx.vstack(
                rx.hstack(
                    rx.text("Territory:", font_weight="bold", min_width="120px"),
                    rx.text(AppState.selected_territory),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Country:", font_weight="bold", min_width="120px"),
                    rx.text(AppState.selected_country),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Analysis Year:", font_weight="bold", min_width="120px"),
                    rx.text(AppState.mapbiomas_current_year.to(str)),
                    width="100%",
                ),
                rx.divider(),
                rx.text("Available Datasets", font_weight="bold", font_size="sm"),
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
            rx.text("No territory selected", font_size="sm", color="gray"),
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
                rx.tabs.trigger("MapBiomas", value="mapbiomas"),
                rx.tabs.trigger("Hansen/GLAD", value="hansen"),
                rx.tabs.trigger("Hansen GFC", value="gfc"),
                rx.tabs.trigger("AAFC", value="aafc"),
                rx.tabs.trigger("Comparison", value="comparison"),
                rx.tabs.trigger("About", value="about"),
            ),
            rx.tabs.content(mapbiomas_tab(), value="mapbiomas"),
            rx.tabs.content(hansen_tab(), value="hansen"),
            rx.tabs.content(hansen_gfc_tab(), value="gfc"),
            rx.tabs.content(aafc_tab(), value="aafc"),
            rx.tabs.content(comparison_tab(), value="comparison"),
            rx.tabs.content(about_tab(), value="about"),
            default_value="mapbiomas",
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
        overflow="hidden",
    )
