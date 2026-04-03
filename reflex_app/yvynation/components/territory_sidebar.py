"""
Sidebar component for territory-focused analysis.
Select indigenous territories by map click or list, run analysis,
buffer, MapBiomas/Hansen/AAFC layers.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .sidebar import _section, _active_count_badge


def _region_selector() -> rx.Component:
    """Compact Brazil/Canada region toggle."""
    return rx.hstack(
        rx.text("Region:", font_size="xs", color="gray", font_weight="600"),
        rx.button(
            "Brasil",
            on_click=lambda: AppState.set_country("Brazil"),
            size="1",
            variant=rx.cond(AppState.selected_country == "Brazil", "solid", "outline"),
            color_scheme=rx.cond(AppState.selected_country == "Brazil", "green", "gray"),
        ),
        rx.button(
            "Canada",
            on_click=lambda: AppState.set_country("Canada"),
            size="1",
            variant=rx.cond(AppState.selected_country == "Canada", "solid", "outline"),
            color_scheme=rx.cond(AppState.selected_country == "Canada", "green", "gray"),
        ),
        width="100%",
        spacing="1",
        align_items="center",
        padding="0.5rem 0.25rem",
    )


def _territory_selector_section() -> rx.Component:
    """Indigenous lands toggle, search, and territory list."""
    return rx.vstack(
        # Show/hide all indigenous lands overlay + click-to-select hint
        rx.hstack(
            rx.button(
                rx.cond(
                    AppState.show_indigenous_lands,
                    AppState.tr["hide_all_lands"],
                    AppState.tr["show_all_lands"],
                ),
                on_click=AppState.toggle_indigenous_lands,
                size="1",
                variant=rx.cond(AppState.show_indigenous_lands, "solid", "outline"),
                color_scheme="violet",
                flex="1",
            ),
            rx.text(AppState.tr["click_map_to_select"], font_size="9px", color="gray"),
            width="100%",
            spacing="1",
            align_items="center",
        ),

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
        rx.input(
            placeholder=AppState.tr["search_territories"],
            value=AppState.territory_search_query,
            on_change=AppState.set_territory_search_query,
            size="1",
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
                            rx.text(territory, font_size="sm", text_align="left", flex="1"),
                            width="100%",
                            spacing="2",
                        ),
                        on_click=lambda t=territory: AppState.set_selected_territory(t),
                        size="1",
                        variant=rx.cond(AppState.selected_territory == territory, "solid", "ghost"),
                        color_scheme=rx.cond(AppState.selected_territory == territory, "green", "gray"),
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
            height="250px",
            overflow_y="auto",
            border="1px solid #d0d0d0",
            border_radius="md",
            padding="0.5rem",
        ),

        spacing="3",
        width="100%",
    )


def _territory_analysis_section() -> rx.Component:
    """Individual MapBiomas/Hansen analysis + year comparison for selected territory."""
    return rx.vstack(
        rx.cond(
            AppState.selected_territory != None,
            rx.vstack(
                rx.badge(AppState.selected_territory, color_scheme="green", variant="solid", size="1"),

                # MapBiomas single-year analysis
                rx.hstack(
                    rx.select(
                        [str(y) for y in range(1985, 2024)],
                        value=AppState.mapbiomas_current_year_str,
                        on_change=AppState.set_mapbiomas_year,
                        size="1",
                        flex="1",
                    ),
                    rx.cond(
                        AppState.mapbiomas_analysis_pending,
                        rx.button(rx.spinner(size="1"), is_disabled=True, size="1", color_scheme="green", flex="0 1 auto"),
                        rx.button(
                            "MapBiomas",
                            on_click=AppState.run_mapbiomas_analysis_on_territory,
                            size="1",
                            color_scheme="green",
                            flex="0 1 auto",
                        ),
                    ),
                    spacing="1",
                ),

                # Hansen single-year analysis
                rx.hstack(
                    rx.select(
                        HANSEN_YEARS,
                        value=AppState.hansen_current_year,
                        on_change=AppState.set_hansen_year,
                        size="1",
                        flex="1",
                    ),
                    rx.cond(
                        AppState.hansen_analysis_pending,
                        rx.button(rx.spinner(size="1"), is_disabled=True, size="1", color_scheme="blue", flex="0 1 auto"),
                        rx.button(
                            "Hansen",
                            on_click=AppState.run_hansen_analysis_on_territory,
                            size="1",
                            color_scheme="blue",
                            flex="0 1 auto",
                        ),
                    ),
                    spacing="1",
                ),

                rx.divider(),

                # Year comparison
                rx.text(AppState.tr["compare_years"], font_size="xs", font_weight="600", color="gray"),
                rx.hstack(
                    rx.select(
                        [str(y) for y in range(1985, 2024)],
                        value=AppState.comparison_year1_str,
                        on_change=AppState.set_comparison_year1,
                        size="1",
                        flex="1",
                    ),
                    rx.text(AppState.tr["vs_label"], font_size="xs", color="gray", flex="0 0 auto"),
                    rx.select(
                        [str(y) for y in range(1985, 2024)],
                        value=AppState.comparison_year2_str,
                        on_change=AppState.set_comparison_year2,
                        size="1",
                        flex="1",
                    ),
                    spacing="1",
                    align_items="center",
                    width="100%",
                ),
                rx.cond(
                    AppState.mapbiomas_analysis_pending,
                    rx.button(
                        rx.hstack(rx.spinner(size="1"), rx.text(AppState.tr["comparing_label"]), spacing="1"),
                        is_disabled=True,
                        size="1",
                        color_scheme="purple",
                        width="100%",
                    ),
                    rx.button(
                        AppState.tr["compare_mapbiomas_years"],
                        on_click=AppState.run_territory_comparison,
                        size="1",
                        color_scheme="purple",
                        width="100%",
                    ),
                ),

                spacing="2",
                width="100%",
            ),
            rx.text(AppState.tr["select_territory_above"], font_size="xs", color="gray"),
        ),
        spacing="2",
        width="100%",
    )


def _mapbiomas_layers_section() -> rx.Component:
    """MapBiomas year grid with add/clear and active badges with per-year removal."""
    return rx.vstack(
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
        rx.cond(
            AppState.mapbiomas_displayed_years.length() > 0,
            rx.flex(
                rx.foreach(
                    AppState.mapbiomas_displayed_years,
                    lambda year: rx.badge(
                        rx.hstack(
                            rx.text(year.to(str), font_size="xs"),
                            rx.text(
                                "x",
                                font_size="xs",
                                cursor="pointer",
                                on_click=lambda *a, y=year: AppState.remove_mapbiomas_layer(y),
                                color="red",
                                _hover={"font_weight": "bold"},
                            ),
                            spacing="1",
                            align_items="center",
                        ),
                        color_scheme="green",
                        variant="surface",
                        size="1",
                    ),
                ),
                flex_wrap="wrap",
                gap="1",
            ),
            rx.box(),
        ),
        spacing="2",
        width="100%",
    )


def _hansen_layers_section() -> rx.Component:
    """Hansen GFC with cover/loss/gain type toggles, year selector, and active badges."""
    return rx.vstack(
        rx.text(AppState.tr["data_layers"], font_size="xs", font_weight="600", color="gray"),
        rx.hstack(
            rx.button(
                AppState.tr["tree_cover_btn"],
                on_click=lambda: AppState.add_hansen_layer("cover"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("cover"), "solid", "outline"),
                color_scheme="green",
                flex="1",
            ),
            rx.button(
                AppState.tr["loss_btn"],
                on_click=lambda: AppState.add_hansen_layer("loss"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("loss"), "solid", "outline"),
                color_scheme="red",
                flex="1",
            ),
            rx.button(
                AppState.tr["gain_btn"],
                on_click=lambda: AppState.add_hansen_layer("gain"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("gain"), "solid", "outline"),
                color_scheme="teal",
                flex="1",
            ),
            spacing="1",
        ),
        rx.text(AppState.tr["year_layers"], font_size="xs", font_weight="600", color="gray"),
        rx.hstack(
            rx.select(
                HANSEN_YEARS,
                value=AppState.hansen_current_year,
                on_change=AppState.set_hansen_year,
                size="1",
                flex="1",
            ),
            rx.button(
                AppState.tr["add_btn"],
                on_click=AppState.add_hansen_selected_year,
                size="1",
                color_scheme="blue",
                flex="0 1 auto",
            ),
            spacing="1",
        ),
        rx.cond(
            AppState.hansen_displayed_layers.length() > 0,
            rx.flex(
                rx.foreach(
                    AppState.hansen_displayed_layers,
                    lambda lyr: rx.badge(
                        rx.hstack(
                            rx.text(lyr, font_size="xs"),
                            rx.text(
                                "x",
                                font_size="xs",
                                cursor="pointer",
                                on_click=lambda *a, l=lyr: AppState.remove_hansen_layer(l),
                                color="red",
                                _hover={"font_weight": "bold"},
                            ),
                            spacing="1",
                            align_items="center",
                        ),
                        color_scheme="blue",
                        variant="surface",
                        size="1",
                    ),
                ),
                flex_wrap="wrap",
                gap="1",
            ),
            rx.box(),
        ),
        spacing="2",
        width="100%",
    )


def _aafc_placeholder() -> rx.Component:
    """AAFC section: active when Canada is selected, placeholder otherwise."""
    return rx.cond(
        AppState.selected_country == "Canada",
        rx.vstack(
            rx.text("AAFC Annual Crop Inventory (2009–2023)", font_size="xs", color="#555"),
            rx.badge(
                "Coming soon: Indigenous reserve boundaries",
                color_scheme="orange",
                variant="surface",
                size="1",
            ),
            spacing="2",
            width="100%",
        ),
        rx.text(
            "Switch to Canada region to access AAFC crop inventory data.",
            font_size="xs",
            color="gray",
            text_align="center",
        ),
    )


def territory_sidebar() -> rx.Component:
    """Sidebar for territory analysis: select, analyze, buffer, layers."""
    return rx.vstack(
        # Back to portal
        rx.button(
            "← Back to Portal",
            on_click=AppState.go_to_portal,
            size="1",
            variant="outline",
            color_scheme="gray",
            width="100%",
            margin_bottom="0.5rem",
        ),

        # Region selector
        _region_selector(),

        rx.divider(),

        # Territory selection (with indigenous lands toggle + search + list)
        _section(
            "territory_selection",
            _territory_selector_section(),
            AppState.sidebar_territory_expanded,
            lambda: AppState.toggle_sidebar_section("territory"),
            rx.cond(
                AppState.selected_territory != None,
                rx.badge("1", color_scheme="purple", size="1", variant="solid"),
                rx.box(),
            ),
        ),

        # Analysis settings (MapBiomas, Hansen, year comparison)
        _section(
            "analysis_settings",
            _territory_analysis_section(),
            AppState.sidebar_mapbiomas_expanded,
            lambda: AppState.toggle_sidebar_section("mapbiomas"),
        ),

        # Buffer controls
        _section(
            "buffer_controls",
            rx.vstack(
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["buffer_distance"], font_size="sm", font_weight="600"),
                        rx.hstack(
                            rx.input(
                                value=AppState.buffer_distance_input,
                                on_change=AppState.set_buffer_distance_input,
                                type_="number",
                                placeholder=AppState.tr["enter_distance"],
                                size="1",
                                flex="1",
                            ),
                            rx.text("m", font_size="sm", color="gray"),
                            width="100%",
                            spacing="1",
                        ),
                        width="100%",
                    ),
                    border="1px solid #d0d0d0",
                    padding="0.75rem",
                    border_radius="md",
                    width="100%",
                ),
                rx.button(
                    AppState.tr["create_buffer"],
                    on_click=AppState.handle_create_buffer,
                    size="1",
                    color_scheme="green",
                    variant="solid",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            AppState.sidebar_geometry_expanded,
            lambda: AppState.toggle_sidebar_section("geometry"),
        ),

        # MapBiomas layers
        _section(
            "mapbiomas_section_title",
            _mapbiomas_layers_section(),
            AppState.sidebar_mapbiomas_expanded,
            lambda: AppState.toggle_sidebar_section("mapbiomas"),
            _active_count_badge(AppState.mapbiomas_displayed_years.length(), "green"),
        ),

        # Hansen GFC layers
        _section(
            "hansen_section_title",
            _hansen_layers_section(),
            AppState.sidebar_hansen_expanded,
            lambda: AppState.toggle_sidebar_section("hansen"),
            _active_count_badge(AppState.hansen_displayed_layers.length(), "blue"),
        ),

        # AAFC (Canada)
        _section(
            "aafc_section_title",
            _aafc_placeholder(),
            AppState.sidebar_hansen_expanded,
            lambda: AppState.toggle_sidebar_section("hansen"),
        ),

        width="100%",
        spacing="0",
        padding="0.5rem",
    )
