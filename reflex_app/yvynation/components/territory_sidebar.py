"""
Sidebar component for territory-focused analysis.
Shows only territory selection, comparison, and layer controls.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .analysis_controls import analysis_controls
from .sidebar import _section, _active_count_badge


def territory_selector_section() -> rx.Component:
    """Territory search and selection controls."""
    return rx.vstack(
        # Country selector
        rx.vstack(
            rx.text(AppState.tr["country"], font_size="sm", font_weight="600"),
            rx.select(
                ["Brazil", "Colombia", "Peru"],
                value=AppState.selected_country,
                on_change=AppState.set_country,
                size="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        
        # Territory search
        rx.vstack(
            rx.text(AppState.tr["territory_search"], font_size="sm", font_weight="600"),
            rx.input(
                placeholder=AppState.tr["search_territory"],
                value=AppState.territory_search_query,
                on_change=AppState.set_territory_search_query,
                size="1",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        
        # Territory list (scrollable)
        rx.box(
            rx.vstack(
                rx.foreach(
                    AppState.filtered_territories,
                    lambda territory: rx.button(
                        rx.hstack(
                            rx.icon(
                                rx.cond(
                                    AppState.selected_territory == territory,
                                    "check-circle-2",
                                    "circle",
                                ),
                                color=rx.cond(
                                    AppState.selected_territory == territory,
                                    "green",
                                    "gray",
                                ),
                            ),
                            rx.text(
                                territory,
                                font_size="sm",
                                text_align="left",
                                flex="1",
                            ),
                            width="100%",
                            spacing="2",
                        ),
                        on_click=lambda t=territory: AppState.set_selected_territory(t),
                        size="1",
                        variant=rx.cond(
                            AppState.selected_territory == territory,
                            "solid",
                            "ghost",
                        ),
                        color_scheme=rx.cond(
                            AppState.selected_territory == territory,
                            "green",
                            "gray",
                        ),
                        width="100%",
                    ),
                ),
                rx.cond(
                    AppState.filtered_territories.length() == 0,
                    rx.text(
                        AppState.tr["no_results"],
                        font_size="sm",
                        color="gray",
                        text_align="center",
                        padding="1rem",
                    ),
                    rx.box(),
                ),
                width="100%",
                spacing="1",
            ),
            width="100%",
            height="300px",
            overflow_y="auto",
            border="1px solid #d0d0d0",
            border_radius="md",
            padding="0.5rem",
        ),
        
        spacing="3",
        width="100%",
    )


def territory_sidebar() -> rx.Component:
    """Sidebar optimized for territory analysis workflow."""
    return rx.vstack(
        # Back to portal button
        rx.button(
            "← Back to Portal",
            on_click=AppState.go_to_portal,
            size="1",
            variant="outline",
            color_scheme="gray",
            width="100%",
            margin_bottom="0.5rem",
        ),
        
        rx.divider(),
        
        # Territory selection section
        _section(
            "territory_selection",
            territory_selector_section(),
            AppState.sidebar_territory_expanded,
            lambda: AppState.toggle_sidebar_section("territory"),
        ),
        
        # Analysis controls
        _section(
            "analysis_settings",
            analysis_controls(),
            AppState.sidebar_mapbiomas_expanded,
            lambda: AppState.toggle_sidebar_section("mapbiomas"),
        ),
        
        # MapBiomas layers section
        _section(
            "mapbiomas_section",
            rx.vstack(
                rx.flex(
                    rx.foreach(
                        MAPBIOMAS_YEARS,
                        lambda year: rx.button(
                            year.to(str),
                            on_click=lambda *a, y=year: AppState.set_mapbiomas_year(y),
                            size="1",
                            padding="4px 6px",
                            font_size="10px",
                            variant=rx.cond(AppState.mapbiomas_current_year == year, "solid", "outline"),
                            color_scheme=rx.cond(AppState.mapbiomas_current_year == year, "green", "gray"),
                        ),
                    ),
                    flex_wrap="wrap",
                    gap="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        AppState.tr["add_to_map"],
                        on_click=lambda: AppState.add_mapbiomas_layer(),
                        size="1",
                        color_scheme="green",
                        flex="1",
                    ),
                    rx.button(
                        AppState.tr["clear_all"],
                        on_click=AppState.clear_all_layers,
                        size="1",
                        color_scheme="red",
                        variant="outline",
                        flex="1",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="3",
                width="100%",
            ),
            AppState.sidebar_mapbiomas_expanded,
            lambda: AppState.toggle_sidebar_section("mapbiomas"),
            _active_count_badge(
                rx.cond(
                    AppState.mapbiomas_displayed_years.length() > 0,
                    AppState.mapbiomas_displayed_years.length(),
                    0,
                ),
                "green",
            ),
        ),
        
        # Hansen layers section
        _section(
            "hansen_section",
            rx.vstack(
                rx.flex(
                    rx.foreach(
                        HANSEN_YEARS,
                        lambda year: rx.button(
                            year.to(str),
                            on_click=lambda *a, y=year: AppState.set_hansen_year(y),
                            size="1",
                            padding="4px 6px",
                            font_size="10px",
                            variant=rx.cond(AppState.hansen_current_year == year, "solid", "outline"),
                            color_scheme=rx.cond(AppState.hansen_current_year == year, "orange", "gray"),
                        ),
                    ),
                    flex_wrap="wrap",
                    gap="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        AppState.tr["add_to_map"],
                        on_click=lambda: AppState.add_hansen_layer(),
                        size="1",
                        color_scheme="orange",
                        flex="1",
                    ),
                    rx.button(
                        AppState.tr["remove"],
                        on_click=lambda: AppState.remove_hansen_layer(AppState.hansen_current_year),
                        size="1",
                        color_scheme="red",
                        variant="outline",
                        flex="1",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="3",
                width="100%",
            ),
            AppState.sidebar_hansen_expanded,
            lambda: AppState.toggle_sidebar_section("hansen"),
            _active_count_badge(
                rx.cond(
                    AppState.hansen_displayed_layers.length() > 0,
                    AppState.hansen_displayed_layers.length(),
                    0,
                ),
                "orange",
            ),
        ),
        
        # Comparison controls (only visible for territories)
        rx.cond(
            AppState.selected_territory != None,
            rx.box(
                rx.vstack(
                    rx.heading(AppState.tr["comparison_controls"], size="4"),
                    rx.text(AppState.tr["compare_label"], font_size="sm", font_weight="600"),
                    rx.hstack(
                        rx.select(
                            [str(y) for y in range(1985, 2024)],
                            value=AppState.comparison_year1.to(str),
                            on_change=AppState.set_comparison_year1,
                            size="1",
                            flex="1",
                        ),
                        rx.text("vs", font_size="sm", color="gray", padding="0.5rem"),
                        rx.select(
                            [str(y) for y in range(1985, 2024)],
                            value=AppState.comparison_year2.to(str),
                            on_change=AppState.set_comparison_year2,
                            size="1",
                            flex="1",
                        ),
                        width="100%",
                        spacing="2",
                    ),
                    rx.cond(
                        AppState.mapbiomas_analysis_pending,
                        rx.button(
                            rx.spinner(size="1"),
                            is_disabled=True,
                            size="1",
                            color_scheme="blue",
                            width="100%",
                        ),
                        rx.button(
                            AppState.tr["compare_btn"],
                            on_click=AppState.run_territory_comparison,
                            size="1",
                            color_scheme="green",
                            variant="solid",
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                padding="0.75rem",
                border="1px solid #f0f0f0",
                border_radius="md",
                margin_bottom="1rem",
            ),
            rx.box(),
        ),
        
        width="100%",
        spacing="0",
        padding="0.5rem",
    )
