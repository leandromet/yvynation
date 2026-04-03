"""
Main application layout and routing for Yvynation Reflex app.
Phase 4-5: Analysis tabs, Plotly visualizations, export functionality.
"""

import reflex as rx
from ..state import AppState
from ..components.geometry_sidebar import geometry_sidebar
from ..components.territory_sidebar import territory_sidebar
from ..components.map import leaflet_map, map_metrics
from ..components.results_panel import results_panel
from ..components.export_panel import export_panel
from ..components.geometry_popup import geometry_info_popup
from ..components.tutorial import tutorial_section
from ..components.layer_reference import layer_reference_guide
from ..components.loading_indicator import loading_indicator
from .portal import portal


def navbar() -> rx.Component:
    """Modern top navigation bar."""
    return rx.hstack(
        # Left side - toggle & branding
        rx.hstack(
            rx.vstack(
                rx.button(
                    rx.cond(
                        AppState.sidebar_open,
                        "☰ Hide",
                        "☰ Show",
                    ),
                    on_click=AppState.toggle_sidebar,
                    size="1",
                    variant="ghost",
                    color_scheme="green",
                ),
                # Sidebar resize preset buttons
                rx.cond(
                    AppState.sidebar_open,
                    rx.hstack(
                        rx.button(
                            "◀",
                            on_click=lambda: AppState.update_sidebar_width(200),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Narrow",
                        ),
                        rx.button(
                            "resize",
                            on_click=lambda: AppState.update_sidebar_width(300),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Normal",
                        ),
                        rx.button(
                            "▶",
                            on_click=lambda: AppState.update_sidebar_width(600),
                            size="1",
                            variant="ghost",
                            padding="0.25rem 0.5rem",
                            title="Wide",
                        ),
                        spacing="1",
                        font_size="xs",
                    ),
                    rx.box(),
                ),
                spacing="1",
                padding="0",
                margin="0",
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(AppState.tr["app_title"], size="3"),
                    rx.cond(
                        AppState.analysis_mode != "portal",
                        rx.hstack(
                            rx.text("•", color="#4a7c59", font_weight="bold"),
                            rx.text(
                                rx.cond(
                                    AppState.analysis_mode == "geometry",
                                    "🔷 Geometry Analysis",
                                    "🗺️ Territory Analysis",
                                ),
                                font_size="sm",
                                color="#1a472a",
                                font_weight="500",
                            ),
                            spacing="1",
                            align_items="center",
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                    align_items="center",
                ),
                rx.text(
                    AppState.tr["app_subtitle"],
                    font_size="xs",
                    color="gray",
                ),
                spacing="0",
                margin="0",
            ),
            width="auto",
            align_items="center",
            spacing="2",
        ),
        # Center spacer
        rx.spacer(),
        # Right side - back button and analysis indicator
        rx.hstack(
            rx.button(
                "← Back to Portal",
                on_click=lambda: AppState.go_to_portal(),
                size="1",
                variant="outline",
                color_scheme="green",
            ),
            rx.cond(
                (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                rx.badge(
                    AppState.tr["analysis_active_badge"],
                    color_scheme="green",
                    variant="solid",
                    size="1",
                ),
                rx.text(
                    AppState.tr["app_description"],
                    font_size="sm",
                    color="gray",
                    display=rx.cond(AppState.sidebar_open, "block", "none"),
                ),
            ),
            align_items="center",
            spacing="3",
        ),
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%)",
        border_bottom="2px solid #e8f0e8",
        align_items="center",
        width="100%",
        height="70px",
        position="sticky",
        top="0",
        z_index="100",
    )


def active_layers_summary() -> rx.Component:
    """Show active layer counts and current configuration."""
    return rx.hstack(
        map_metrics(),
        # Comparison controls (visible when analysis results exist)
        rx.cond(
            AppState.selected_territory != None,
            rx.hstack(
                rx.text("|", color="gray", font_size="sm"),
                rx.text(AppState.tr["compare_label"], font_size="xs", color="gray"),
                rx.select(
                    [str(y) for y in range(1985, 2024)],
                    value=AppState.comparison_year1.to(str),
                    on_change=AppState.set_comparison_year1,
                    size="1",
                    width="80px",
                ),
                rx.text(AppState.tr["vs_label"], font_size="xs", color="gray"),
                rx.select(
                    [str(y) for y in range(1985, 2024)],
                    value=AppState.comparison_year2.to(str),
                    on_change=AppState.set_comparison_year2,
                    size="1",
                    width="80px",
                ),
                rx.cond(
                    AppState.mapbiomas_analysis_pending,
                    rx.button(
                        rx.spinner(size="1"),
                        is_disabled=True,
                        size="1",
                        color_scheme="blue",
                    ),
                    rx.button(
                        AppState.tr["compare_btn"],
                        on_click=AppState.run_territory_comparison,
                        size="1",
                        color_scheme="green",
                        variant="solid",
                    ),
                ),
                spacing="2",
                align_items="center",
            ),
            rx.box(),
        ),
        width="100%",
        padding="0.5rem 1rem",
        border_bottom="1px solid #e0e0e0",
        align_items="center",
        flex_wrap="wrap",
        gap="2",
    )


def error_toast(state: AppState) -> rx.Component:
    """Display error messages."""
    return rx.cond(
        state.error_message != "",
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("alert-circle", color="red"),
                    rx.text(state.error_message),
                    width="100%",
                ),
                rx.button(
                    AppState.tr["dismiss"],
                    size="1",
                    on_click=state.clear_error,
                ),
                width="100%",
            ),
            padding="1rem",
            bg="red.50",
            border="1px solid red",
            border_radius="md",
            position="fixed",
            bottom="1rem",
            right="1rem",
            z_index="9999",
            max_width="400px",
        ),
        rx.box(),
    )





def comparison_results_section() -> rx.Component:
    """Year comparison results: charts + summary cards."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(AppState.tr["year_comparison_results"], size="3"),
                rx.spacer(),
                rx.button(
                    AppState.tr["download_comparison_csv"],
                    on_click=AppState.download_comparison_csv,
                    size="1",
                    color_scheme="blue",
                    variant="outline",
                ),
                width="100%",
                align_items="center",
            ),
            rx.divider(),
            rx.plotly(data=AppState.gains_losses_chart, use_resize_handler=True),
            rx.divider(),
            rx.plotly(data=AppState.change_pct_chart, use_resize_handler=True),
            rx.divider(),
            # Summary cards
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["total_gains"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_total_gains,
                                font_weight="bold", color="green"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="green.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["total_losses"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_total_losses,
                                font_weight="bold", color="red"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="red.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["net_change"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_net_change,
                                font_weight="bold"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="blue.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                width="100%",
                spacing="2",
            ),
            spacing="3",
            width="100%",
            padding="1rem",
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
    )


def main_content_area() -> rx.Component:
    """
    Main content area using CSS grid so the map gets a fixed-size row
    and the results section scrolls independently below it.
    """
    has_analysis = (AppState.analysis_results != {}) & (AppState.analysis_results != None)

    return rx.box(
        # Row 1: layer summary bar (auto height)
        active_layers_summary(),

        # Row 1.5: Tutorial section (collapsible)
        rx.box(
            tutorial_section(),
            padding="0.5rem 1rem 0",
        ),

        # Row 2: map (fixed height via grid row)
        leaflet_map(),

        # Row 2.5: Layer reference guide (collapsible)
        rx.box(
            layer_reference_guide(),
            padding="0 1rem",
        ),

        # Row 3: results area (scrollable, takes remaining space)
        rx.cond(
            has_analysis,
            rx.box(
                rx.vstack(
                    # Analysis results tabs
                    results_panel(),

                    # Comparison results
                    rx.cond(
                        AppState.comparison_available,
                        comparison_results_section(),
                        rx.box(),
                    ),

                    # Export panel
                    export_panel(),

                    width="100%",
                    spacing="3",
                    padding="0.5rem",
                ),
                width="100%",
                overflow_y="auto",
                overflow_x="auto",
            ),
            rx.box(),
        ),

        # CSS Grid layout: 5 rows
        # - auto: layer bar
        # - auto: tutorial
        # - map row: big when no analysis, smaller when analysis shown
        # - auto: layer reference guide
        # - 1fr: results (or 0 if hidden)
        display="grid",
        grid_template_rows=rx.cond(
            has_analysis,
            "auto auto minmax(400px, 50vh) auto 1fr",
            "auto auto 1fr auto 0px",
        ),
        width="100%",
        height="100%",
        overflow="hidden",
    )


def index() -> rx.Component:
    """Main application layout with dynamic content based on analysis mode."""
    return rx.cond(
        AppState.analysis_mode == "portal",
        portal(),
        # Analysis pages (geometry or territory mode)
        rx.vstack(
            navbar(),
            rx.hstack(
                # Sidebar (collapsible and resizable)
                rx.cond(
                    AppState.sidebar_open,
                    rx.box(
                        # Choose sidebar based on analysis mode
                        rx.cond(
                            AppState.analysis_mode == "geometry",
                            geometry_sidebar(),
                            territory_sidebar(),
                        ),
                        width=rx.cond(
                            AppState.sidebar_width != 0,
                            f"{AppState.sidebar_width}px",
                            "300px",
                        ),
                        max_width="500px",
                        min_width="200px",
                        overflow_y="auto",
                        overflow_x="hidden",
                        border_right="2px solid #d0d0d0",
                        bg="white",
                        position="relative",
                    ),
                    rx.box(),
                ),
                # Main content area
                main_content_area(),
                width="100%",
                height="calc(220vh - 70px)",
                spacing="0",
            ),
            error_toast(AppState),
            loading_indicator(),
            geometry_info_popup(),
            width="100%",
            height="120vh",
            spacing="0",
        ),
    )
