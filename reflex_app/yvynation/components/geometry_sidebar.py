"""
Sidebar component for geometry-focused analysis.
Shows only geometry drawing/upload, buffer, and layer controls.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .geometry_upload import geometry_file_upload
from .analysis_controls import analysis_controls
from .geometry_selector import geometry_selector, drawing_instructions
from .sidebar import _section, _active_count_badge


def geometry_sidebar() -> rx.Component:
    """Sidebar optimized for geometry analysis workflow."""
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
        
        # Geometry section - expanded by default
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
        ),
        
        # Buffer controls section
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
        
        width="100%",
        spacing="0",
        padding="0.5rem",
    )
