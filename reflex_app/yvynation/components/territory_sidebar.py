"""
Sidebar component for territory-focused analysis.
Select indigenous territories by map click or list, run analysis,
buffer, MapBiomas/Hansen layers.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .sidebar import _active_count_badge
from .layout import group, sidebar_groups_root, sidebar_shell
from .tutorial import tutorial_section
from .layer_reference import layer_reference_guide


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


def _territory_tools_section() -> rx.Component:
    """Indigenous lands toggle, search, and territory list."""
    return rx.vstack(
        # Show/hide overlay + click hint
        rx.box(
            rx.vstack(
                rx.heading("🗺️ Select Territory", size="4"),
                rx.text(
                    "Click a territory on the map or search the list below.",
                    font_size="xs",
                    color="gray.600",
                ),
                rx.text(
                    "🎯 Tip: Toggle the territory layer to see all indigenous lands or conservation units on the map.",
                    font_size="9px",
                    color="blue.600",
                    font_weight="500",
                ),
                spacing="2",
            ),
            padding="0.75rem",
            bg="blue.50",
            border="1px solid #bfdbfe",
            border_radius="md",
            width="100%",
        ),

        # Show/hide indigenous lands overlay
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

        # Current territory type — fixed for this session, chosen on the
        # portal (no more in-page switch between indigenous lands and
        # conservation units; that choice now happens before entering here).
        rx.hstack(
            rx.text(AppState.tr["territory_type"] + ":", font_size="xs", color="gray", font_weight="600"),
            rx.badge(
                rx.cond(
                    AppState.territory_type == "conservation",
                    AppState.tr["conservation_units_btn"],
                    AppState.tr["indigenous_lands_btn"],
                ),
                color_scheme=rx.cond(AppState.territory_type == "conservation", "green", "violet"),
            ),
            spacing="2",
            align_items="center",
            width="100%",
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
                        on_click=AppState.set_selected_territory(territory),
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
    """Analysis: Year comparison + MapBiomas + Hansen GLAD + Hansen GFC for selected territory."""
    return rx.cond(
        AppState.selected_territory != None,
        rx.box(
            rx.vstack(
                # Selected territory badge
                rx.badge(AppState.selected_territory, color_scheme="green", variant="solid", size="1"),

                # ---- Year comparison ----------------------------------------
                rx.vstack(
                    rx.heading("📅 Year Comparison", size="4"),
                    rx.text(
                        "Compare MapBiomas land cover changes between two years.",
                        font_size="xs",
                        color="gray.600",
                    ),
                    rx.hstack(
                        rx.select(
                            [str(y) for y in range(1985, 2025)],
                            value=AppState.comparison_year1_str,
                            on_change=AppState.set_comparison_year1,
                            size="1",
                            flex="1",
                        ),
                        rx.text("vs", font_size="xs", color="gray", flex="0 0 auto"),
                        rx.select(
                            [str(y) for y in range(1985, 2025)],
                            value=AppState.comparison_year2_str,
                            on_change=AppState.set_comparison_year2,
                            size="1",
                            flex="1",
                        ),
                        width="100%",
                        spacing="1",
                        align_items="center",
                    ),
                    rx.cond(
                        AppState.mapbiomas_analysis_pending,
                        rx.button(
                            rx.hstack(rx.spinner(size="1"), rx.text("Comparing..."), spacing="1"),
                            is_disabled=True,
                            width="100%",
                            color_scheme="purple",
                            size="1",
                        ),
                        rx.button(
                            "🔄 Compare MapBiomas Years",
                            on_click=AppState.run_territory_comparison,
                            width="100%",
                            color_scheme="purple",
                            size="1",
                        ),
                    ),
                    spacing="2",
                    width="100%",
                ),

                rx.divider(),

                # ---- Single layer analysis ----------------------------------
                rx.vstack(
                    rx.heading("🔍 Single Layer Analysis", size="4"),
                    rx.text(
                        "Analyze individual data layers for quick insights.",
                        font_size="xs",
                        color="gray.600",
                    ),

                    # MapBiomas
                    rx.vstack(
                        rx.text("MapBiomas Year:", font_size="xs", color="gray.600", font_weight="600"),
                        rx.hstack(
                            rx.select(
                                [str(y) for y in range(1985, 2025)],
                                value=AppState.mapbiomas_current_year_str,
                                on_change=AppState.set_mapbiomas_year,
                                size="1",
                                flex="1",
                            ),
                            rx.cond(
                                AppState.mapbiomas_analysis_pending,
                                rx.button(rx.spinner(size="1"), is_disabled=True, size="1", color_scheme="green", flex="0 1 auto"),
                                rx.button(
                                    "🌱 MapBiomas",
                                    on_click=AppState.run_mapbiomas_analysis_on_territory,
                                    size="1",
                                    color_scheme="green",
                                    flex="0 1 auto",
                                ),
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),

                    # Hansen GLAD
                    rx.vstack(
                        rx.text("Hansen GLAD — Forest Cover:", font_size="xs", color="gray.600", font_weight="600"),
                        rx.text(
                            "Annual forest cover: 2000, 2005, 2010, 2015, 2020",
                            font_size="9px",
                            color="gray.500",
                        ),
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
                                    "Analyze",
                                    on_click=AppState.run_hansen_glad_analysis_on_territory,
                                    size="1",
                                    color_scheme="blue",
                                    flex="0 1 auto",
                                ),
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),

                    # Hansen GFC
                    rx.vstack(
                        rx.text("Hansen GFC — Global Forest Change:", font_size="xs", color="gray.600", font_weight="600"),
                        rx.text(
                            "Tree cover 2000 baseline · loss · gain layers",
                            font_size="9px",
                            color="gray.500",
                        ),
                        rx.cond(
                            AppState.geometry_analysis_pending,
                            rx.button(rx.spinner(size="1"), is_disabled=True, size="1", color_scheme="purple", width="100%"),
                            rx.button(
                                "🌲 Analyze GFC (area stats)",
                                on_click=AppState.run_hansen_gfc_analysis_on_territory,
                                size="1",
                                color_scheme="purple",
                                width="100%",
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),

                    spacing="2",
                    width="100%",
                ),

                spacing="3",
                width="100%",
            ),
            padding="0.75rem",
            border="1px solid #e5e7eb",
            border_radius="md",
            width="100%",
        ),
        rx.box(
            rx.text(
                "👆 Select a territory above to analyze",
                font_size="xs",
                color="gray.600",
                text_align="center",
            ),
            padding="1rem",
            bg="gray.50",
            border_radius="md",
            width="100%",
        ),
    )


def _buffer_section() -> rx.Component:
    """Create buffer zone around the selected territory."""
    return rx.cond(
        AppState.selected_territory != None,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("🔵 Buffer Zone", size="4"),
                    rx.spacer(),
                    # Active buffer badge
                    rx.cond(
                        AppState.current_buffer_for_analysis != None,
                        rx.badge("Active", color_scheme="blue", size="1", variant="solid"),
                        rx.box(),
                    ),
                    width="100%",
                    align_items="center",
                ),
                rx.text(
                    "External ring buffer around the territory for comparative analysis.",
                    font_size="xs",
                    color="gray.600",
                ),
                # Auto-buffer note
                rx.cond(
                    AppState.auto_buffer_enabled,
                    rx.text(
                        rx.text.span("⚡ Auto-buffer ", font_weight="600"),
                        AppState.auto_buffer_km.to(str),
                        " km created automatically on territory select.",
                        font_size="9px",
                        color="blue.600",
                    ),
                    rx.box(),
                ),
                # Manual buffer controls
                rx.hstack(
                    rx.input(
                        value=AppState.buffer_distance_input,
                        on_change=AppState.set_buffer_distance_input,
                        type_="number",
                        placeholder="10",
                        size="1",
                        flex="1",
                        min_="1",
                        step="1",
                    ),
                    rx.text("km", font_size="sm", color="gray", flex="0 0 auto"),
                    rx.button(
                        "Create",
                        on_click=AppState.handle_create_buffer,
                        size="1",
                        color_scheme="green",
                    ),
                    width="100%",
                    spacing="1",
                    align_items="center",
                ),
                # Active buffer name
                rx.cond(
                    AppState.current_buffer_for_analysis != None,
                    rx.text(
                        "📍 ",
                        AppState.current_buffer_for_analysis,
                        font_size="9px",
                        color="blue.700",
                        word_break="break-all",
                    ),
                    rx.box(),
                ),
                spacing="2",
                width="100%",
            ),
            padding="0.75rem",
            border="1px solid #e5e7eb",
            border_radius="md",
            width="100%",
        ),
        rx.box(),
    )


def _mapbiomas_layers_section() -> rx.Component:
    """MapBiomas year grid with add/clear and active badges with per-year removal."""
    return rx.vstack(
        rx.text(
            "Selected for map display:",
            font_size="xs",
            color="gray.600",
            font_weight="600",
        ),
        rx.flex(
            rx.foreach(
                MAPBIOMAS_YEARS,
                lambda year: rx.button(
                    year.to(str),
                    on_click=AppState.set_mapbiomas_year(year),
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
                                on_click=AppState.remove_mapbiomas_layer(year),
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
            rx.text("(None selected)", font_size="xs", color="gray.500"),
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
                                on_click=AppState.remove_hansen_layer(lyr),
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


def _comparison_controls() -> rx.Component:
    """Pick two MapBiomas years and run the comparison.

    This used to be a row of the layer-summary bar above the map
    (``pages/index.py::active_layers_summary``). It is a control, not a
    status readout, so it belongs with the other analysis controls — and
    moving it out is part of what lets the map own its whole column.
    """
    return rx.cond(
        AppState.selected_territory != None,
        rx.vstack(
            rx.text(AppState.tr["compare_label"], font_size="xs", color="gray",
                    font_weight="600"),
            rx.hstack(
                rx.select(
                    [str(y) for y in range(1985, 2025)],
                    value=AppState.comparison_year1_str,
                    on_change=AppState.set_comparison_year1,
                    size="1",
                    width="90px",
                ),
                rx.text(AppState.tr["vs_label"], font_size="xs", color="gray"),
                rx.select(
                    [str(y) for y in range(1985, 2025)],
                    value=AppState.comparison_year2_str,
                    on_change=AppState.set_comparison_year2,
                    size="1",
                    width="90px",
                ),
                spacing="2",
                align_items="center",
                wrap="wrap",
            ),
            rx.cond(
                AppState.mapbiomas_analysis_pending,
                rx.button(rx.spinner(size="1"), is_disabled=True, size="1",
                          color_scheme="blue", width="100%"),
                rx.button(
                    AppState.tr["compare_btn"],
                    on_click=AppState.run_territory_comparison,
                    size="1", color_scheme="green", variant="solid",
                    width="100%",
                ),
            ),
            spacing="2",
            width="100%",
            align_items="stretch",
        ),
        rx.box(),
    )


def territory_sidebar() -> rx.Component:
    """Sidebar for territory analysis: select, analyze, buffer, layers.

    Four collapsible groups (components/layout.py::group), not the six flat
    sections this replaced — those were driven by only four booleans, so
    opening "MapBiomas layers" also opened "Analysis settings" and opening
    "Hansen GFC" also opened "AAFC". Which groups are open is now one
    controlled list on the state (``AppState.open_groups``), one entry per
    group.

    The "← Back to Portal" button that used to sit at the top is gone: the
    navbar already carries a translated one, and this was the untranslated
    duplicate.
    """
    return sidebar_shell(
        _region_selector(),
        sidebar_groups_root(
            group(
                "study_area", "target", AppState.tr["group_study_area"],
                _territory_tools_section(),
                _buffer_section(),
                badge=rx.cond(
                    AppState.selected_territory != None,
                    rx.badge("1", color_scheme="purple", size="1", variant="solid"),
                    rx.box(),
                ),
            ),
            group(
                "analysis", "chart-column", AppState.tr["group_analysis"],
                _territory_analysis_section(),
                _comparison_controls(),
            ),
            group(
                "layers", "layers", AppState.tr["group_layers"],
                _mapbiomas_layers_section(),
                _hansen_layers_section(),
                _aafc_placeholder(),
                badge=rx.hstack(
                    _active_count_badge(
                        AppState.mapbiomas_displayed_years.length(), "green"),
                    _active_count_badge(
                        AppState.hansen_displayed_layers.length(), "blue"),
                    spacing="1",
                ),
            ),
            group(
                "help", "circle-help", AppState.tr["group_help"],
                tutorial_section(),
                layer_reference_guide(),
            ),
        ),
    )
