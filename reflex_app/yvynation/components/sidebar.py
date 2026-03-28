"""
Sidebar component for Yvynation Reflex app.
Clean, compact layout with collapsible sections for layer management,
territory selection, geometry analysis, and comparison controls.
"""

import reflex as rx
from ..state import AppState
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .geometry_upload import geometry_file_upload
from .analysis_controls import analysis_controls
from .geometry_selector import geometry_selector, drawing_instructions


# ---------------------------------------------------------------------------
# Reusable helpers
# ---------------------------------------------------------------------------

def _section(
    title: str,
    content: rx.Component,
    is_expanded,
    on_toggle,
    badge: rx.Component = None,
) -> rx.Component:
    """Compact collapsible section with optional status badge."""
    return rx.box(
        rx.button(
            rx.hstack(
                rx.text(rx.cond(is_expanded, "v", ">"), font_size="xs", width="12px"),
                rx.text(title, font_weight="600", font_size="sm"),
                rx.spacer(),
                badge if badge else rx.fragment(),
                width="80%",
                align_items="center",
                spacing="2",
            ),
            on_click=on_toggle,
            width="100%",
            size="1",
            variant="ghost",
            padding="0.6rem 0.75rem",
        ),
        rx.cond(
            is_expanded,
            rx.box(content, padding="0.25rem 0.5rem 0.5rem 1rem", border_left="2px solid #d4edda"),
            rx.box(),
        ),
        width="100%",
        border_bottom="1px solid #f0f0f0",
    )


def _active_count_badge(count, color_scheme="green") -> rx.Component:
    """Small badge showing active layer count."""
    return rx.cond(
        count > 0,
        rx.badge(count.to(str), color_scheme=color_scheme, size="1", variant="solid"),
        rx.box(),
    )


# ---------------------------------------------------------------------------
# MapBiomas section
# ---------------------------------------------------------------------------

def mapbiomas_section() -> rx.Component:
    """MapBiomas layer selection - year grid + add/remove."""
    return rx.vstack(
        # Year grid
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
                "Add to map",
                on_click=lambda: AppState.add_mapbiomas_layer(),
                size="1",
                color_scheme="green",
                flex="1",
            ),
            rx.button(
                "Clear all",
                on_click=AppState.clear_all_layers,
                size="1",
                variant="outline",
                color_scheme="gray",
                flex="1",
            ),
            spacing="2",
        ),
        # Active layers
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
    )


# ---------------------------------------------------------------------------
# Hansen section
# ---------------------------------------------------------------------------

def hansen_section() -> rx.Component:
    """Hansen GFC layer controls - year + layer type toggles."""
    return rx.vstack(
        # GFC layer toggles (compact)
        rx.text("Data layers", font_size="xs", font_weight="600", color="gray"),
        rx.hstack(
            rx.button(
                "Tree Cover",
                on_click=lambda: AppState.add_hansen_layer("cover"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("cover"), "solid", "outline"),
                color_scheme="green",
                flex="1",
            ),
            rx.button(
                "Loss",
                on_click=lambda: AppState.add_hansen_layer("loss"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("loss"), "solid", "outline"),
                color_scheme="red",
                flex="1",
            ),
            rx.button(
                "Gain",
                on_click=lambda: AppState.add_hansen_layer("gain"),
                size="1",
                variant=rx.cond(AppState.hansen_displayed_layers.contains("gain"), "solid", "outline"),
                color_scheme="teal",
                flex="1",
            ),
            spacing="1",
        ),
        # Year selection
        rx.text("Year layers", font_size="xs", font_weight="600", color="gray"),
        rx.hstack(
            rx.select(
                HANSEN_YEARS,
                value=AppState.hansen_current_year,
                on_change=AppState.set_hansen_year,
                size="1",
                flex="1",
            ),
            rx.button(
                "Add",
                on_click=AppState.add_hansen_selected_year,
                size="1",
                color_scheme="blue",
                flex="0 1 auto",
            ),
            spacing="1",
        ),
        # Active layers
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
    )


# ---------------------------------------------------------------------------
# Territory section
# ---------------------------------------------------------------------------

def territory_section() -> rx.Component:
    """Territory search, selection, and analysis triggers."""
    return rx.vstack(
        # Indigenous lands toggle
        rx.hstack(
            rx.button(
                rx.cond(AppState.show_indigenous_lands, "Hide All Lands", "Show All Lands"),
                on_click=AppState.toggle_indigenous_lands,
                size="1",
                variant=rx.cond(AppState.show_indigenous_lands, "solid", "outline"),
                color_scheme="violet",
                flex="1",
            ),
            rx.text("Click map markers to select", font_size="9px", color="gray"),
            width="100%",
            spacing="1",
            align_items="center",
        ),
        # Search + select (territories auto-load on page load)
        rx.input(
            placeholder="Search territories...",
            value=AppState.territory_search_query,
            on_change=AppState.set_territory_search_query,
            size="1",
        ),
        rx.select(
            items=AppState.filtered_territories,
            value=AppState.selected_territory,
            on_change=AppState.set_selected_territory,
            placeholder="Select territory",
            size="1",
        ),
        # Analysis controls (only when territory selected)
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.badge(AppState.selected_territory, color_scheme="green", variant="solid", size="1"),
                # MapBiomas analysis
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
                # Hansen analysis
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
                rx.text("Compare years", font_size="xs", font_weight="600", color="gray"),
                rx.hstack(
                    rx.select(
                        [str(y) for y in range(1985, 2024)],
                        value=AppState.comparison_year1_str,
                        on_change=AppState.set_comparison_year1,
                        size="1",
                        flex="1",
                    ),
                    rx.text("vs", font_size="xs", color="gray", flex="0 0 auto"),
                    rx.select(
                        [str(y) for y in range(1985, 2024)],
                        value=AppState.comparison_year2_str,
                        on_change=AppState.set_comparison_year2,
                        size="1",
                        flex="1",
                    ),
                    spacing="1",
                    align_items="center",
                ),
                rx.cond(
                    AppState.mapbiomas_analysis_pending,
                    rx.button(
                        rx.hstack(rx.spinner(size="1"), rx.text("Comparing..."), spacing="1"),
                        is_disabled=True, size="1", color_scheme="purple",
                    ),
                    rx.button(
                        "Compare MapBiomas Years",
                        on_click=AppState.run_territory_comparison,
                        size="1",
                        color_scheme="purple",
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            rx.text("Select a territory above", font_size="xs", color="gray"),
        ),
        spacing="2",
    )


# ---------------------------------------------------------------------------
# Geometry section
# ---------------------------------------------------------------------------

def geometry_section() -> rx.Component:
    """Drawn geometry list, upload, analysis controls, and map overlay toggles."""
    return rx.vstack(
        drawing_instructions(),
        geometry_selector(),
        rx.divider(),
        rx.text("Upload geometry file", font_size="xs", font_weight="600", color="gray"),
        geometry_file_upload(),
        rx.divider(),
        rx.text("Analyze selected geometry", font_size="xs", font_weight="600", color="gray"),
        analysis_controls(),
        rx.divider(),
        # Map overlay toggles
        rx.text("Map overlays", font_size="xs", font_weight="600", color="gray"),
        rx.hstack(
            rx.button(
                rx.cond(AppState.show_geometries_on_map, "Hide Geometries", "Show Geometries"),
                on_click=AppState.toggle_geometries_on_map,
                size="1",
                variant=rx.cond(AppState.show_geometries_on_map, "solid", "outline"),
                color_scheme="purple",
                flex="1",
            ),
            rx.button(
                rx.cond(AppState.show_change_mask, "Hide Change", "Show Change"),
                on_click=AppState.toggle_change_mask,
                size="1",
                variant=rx.cond(AppState.show_change_mask, "solid", "outline"),
                color_scheme="red",
                flex="1",
            ),
            spacing="1",
        ),
        # Change mask year selection (only visible when enabled)
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
                rx.text("vs", font_size="xs", color="gray", flex="0 0 auto"),
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
    )


# ---------------------------------------------------------------------------
# Quick settings row
# ---------------------------------------------------------------------------

def quick_settings() -> rx.Component:
    """Compact language + region row."""
    return rx.hstack(
        # Language
        rx.hstack(
            rx.button(
                "EN",
                on_click=lambda: AppState.set_language("en"),
                size="1",
                variant=rx.cond(AppState.language == "en", "solid", "outline"),
                color_scheme=rx.cond(AppState.language == "en", "green", "gray"),
            ),
            rx.button(
                "PT",
                on_click=lambda: AppState.set_language("pt"),
                size="1",
                variant=rx.cond(AppState.language == "pt", "solid", "outline"),
                color_scheme=rx.cond(AppState.language == "pt", "green", "gray"),
            ),
            spacing="1",
        ),
        rx.spacer(),
        # Region
        rx.hstack(
            rx.button(
                "Brazil",
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
            spacing="1",
        ),
        width="100%",
        padding="0.5rem 0.75rem",
        border_bottom="1px solid #e8e8e8",
        align_items="center",
    )


# ---------------------------------------------------------------------------
# Main sidebar
# ---------------------------------------------------------------------------

def sidebar() -> rx.Component:
    """Modern sidebar with compact collapsible sections."""
    return rx.box(
        rx.vstack(
            # Header
            rx.box(
                rx.hstack(
                    rx.heading("Yvynation", size="3"),
                    rx.spacer(),
                    rx.badge("Controls", color_scheme="green", variant="surface", size="1"),
                    width="100%",
                    align_items="center",
                ),
                padding="0.75rem",
                border_bottom="1px solid #e0e0e0",
                bg="linear-gradient(135deg, #f5f9ff 0%, #ffffff 100%)",
            ),

            # Quick settings
            quick_settings(),

            # Scrollable sections
            rx.box(
                rx.vstack(
                    # MapBiomas layers
                    _section(
                        "MapBiomas Layers",
                        mapbiomas_section(),
                        AppState.sidebar_mapbiomas_expanded,
                        lambda: AppState.toggle_sidebar_section("mapbiomas"),
                        badge=_active_count_badge(AppState.mapbiomas_displayed_years.length(), "green"),
                    ),

                    # Hansen layers
                    _section(
                        "Hansen GFC",
                        hansen_section(),
                        AppState.sidebar_hansen_expanded,
                        lambda: AppState.toggle_sidebar_section("hansen"),
                        badge=_active_count_badge(AppState.hansen_displayed_layers.length(), "blue"),
                    ),

                    # Territory analysis
                    _section(
                        "Territory Analysis",
                        territory_section(),
                        AppState.sidebar_territory_expanded,
                        lambda: AppState.toggle_sidebar_section("territory"),
                        badge=rx.cond(
                            AppState.selected_territory != "",
                            rx.badge("1", color_scheme="purple", size="1", variant="solid"),
                            rx.box(),
                        ),
                    ),

                    # Geometry & Drawing
                    _section(
                        "Geometry & Drawing",
                        geometry_section(),
                        AppState.sidebar_geometry_expanded,
                        lambda: AppState.toggle_sidebar_section("geometry"),
                        badge=_active_count_badge(AppState.drawn_features.length(), "orange"),
                    ),

                    spacing="0",
                    width="100%",
                ),
                flex="1",
                overflow_y="auto",
                width="100%",
            ),

            spacing="0",
            height="100%",
            width="100%",
        ),
        width="100%",
        height="100%",
        bg="white",
    )
