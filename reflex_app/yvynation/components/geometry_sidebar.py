"""
Sidebar component for geometry-focused analysis.
Draw/upload geometries, buffer, analysis with year comparison,
MapBiomas/Hansen/AAFC layers, and map overlay controls.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .geometry_upload import geometry_file_upload
from .geometry_selector import geometry_selector, drawing_instructions
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


def _analysis_settings_section() -> rx.Component:
    """Analysis controls with comparison year pickers for the selected geometry."""
    has_geometry = AppState.selected_geometry_idx != None
    return rx.vstack(
        rx.cond(
            has_geometry,
            rx.vstack(
                # Comparison year selectors
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
                # Full analysis (comparison + change mask)
                rx.cond(
                    AppState.mapbiomas_analysis_pending,
                    rx.button(
                        rx.hstack(rx.spinner(size="1"), rx.text("Analyzing..."), spacing="2"),
                        is_disabled=True,
                        width="100%",
                        color_scheme="purple",
                        size="1",
                    ),
                    rx.button(
                        "Analyze Custom Geometry",
                        on_click=AppState.run_full_analysis_on_geometry,
                        width="100%",
                        color_scheme="purple",
                        size="1",
                    ),
                ),
                rx.text("MapBiomas comparison + change mask", font_size="10px", color="gray"),
                rx.divider(),
                rx.text("Individual layers:", font_size="xs", color="gray"),
                rx.hstack(
                    rx.button(
                        "MapBiomas",
                        on_click=AppState.run_mapbiomas_analysis_on_geometry,
                        size="1",
                        color_scheme="green",
                        flex="1",
                    ),
                    rx.button(
                        "Hansen",
                        on_click=AppState.run_hansen_analysis_on_geometry,
                        size="1",
                        color_scheme="blue",
                        flex="1",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="2",
                width="100%",
            ),
            rx.text(
                "Select a geometry above to analyze",
                font_size="xs",
                color="gray",
                text_align="center",
                padding="0.5rem",
            ),
        ),
        spacing="2",
        width="100%",
    )


def _map_overlays_section() -> rx.Component:
    """Show/hide geometry overlays and change mask with year range."""
    return rx.vstack(
        rx.hstack(
            rx.button(
                rx.cond(AppState.show_geometries_on_map, AppState.tr["hide_geometries"], AppState.tr["show_geometries"]),
                on_click=AppState.toggle_geometries_on_map,
                size="1",
                variant=rx.cond(AppState.show_geometries_on_map, "solid", "outline"),
                color_scheme="purple",
                flex="1",
            ),
            rx.button(
                rx.cond(AppState.show_change_mask, AppState.tr["hide_change"], AppState.tr["show_change"]),
                on_click=AppState.toggle_change_mask,
                size="1",
                variant=rx.cond(AppState.show_change_mask, "solid", "outline"),
                color_scheme="red",
                flex="1",
            ),
            spacing="1",
        ),
        rx.cond(
            AppState.show_change_mask,
            rx.hstack(
                rx.select(
                    [str(y) for y in range(1985, 2024)],
                    value=AppState.change_mask_year1.to(str),
                    on_change=AppState.set_change_mask_year1,
                    size="1",
                    flex="1",
                ),
                rx.text(AppState.tr["vs_label"], font_size="xs", color="gray", flex="0 0 auto"),
                rx.select(
                    [str(y) for y in range(1985, 2024)],
                    value=AppState.change_mask_year2.to(str),
                    on_change=AppState.set_change_mask_year2,
                    size="1",
                    flex="1",
                ),
                spacing="1",
                align_items="center",
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


def geometry_sidebar() -> rx.Component:
    """Sidebar for geometry analysis: draw/upload, buffer, analysis, layers, overlays."""
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

        # Geometry tools (draw + upload)
        _section(
            "geometry_tools",
            rx.vstack(
                drawing_instructions(),
                geometry_selector(),
                geometry_file_upload(),
                spacing="4",
                width="100%",
            ),
            AppState.sidebar_geometry_expanded,
            lambda: AppState.toggle_sidebar_section("geometry"),
            _active_count_badge(AppState.drawn_features.length(), "orange"),
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

        # Analysis settings (year comparison + full + individual buttons)
        _section(
            "analysis_settings",
            _analysis_settings_section(),
            AppState.sidebar_mapbiomas_expanded,
            lambda: AppState.toggle_sidebar_section("mapbiomas"),
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

        # Map overlays (show/hide geometries + change mask)
        _section(
            "map_overlays",
            _map_overlays_section(),
            AppState.sidebar_geometry_expanded,
            lambda: AppState.toggle_sidebar_section("geometry"),
        ),

        width="100%",
        spacing="0",
        padding="0.5rem",
    )
