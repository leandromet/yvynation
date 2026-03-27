"""
Sidebar component for Yvynation Reflex app.
Handles layer selection, territory filtering, and map controls.
"""

import reflex as rx
from ..state import AppState
from ..utils.translations import t, TRANSLATIONS
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS
from .geometry_upload import geometry_file_upload
from .analysis_controls import analysis_controls
from .year_selector import year_selector_grid


def collapsible_section(
    title: str,
    content: rx.Component,
    is_expanded: bool,
    on_toggle,
    icon: str = "▼",
) -> rx.Component:
    """Reusable collapsible section component."""
    return rx.box(
        rx.vstack(
            # Header
            rx.button(
                rx.hstack(
                    rx.text(
                        rx.cond(is_expanded, icon, "▶"),
                        font_size="sm",
                    ),
                    rx.text(
                        title,
                        font_weight="bold",
                        font_size="1",
                    ),
                    width="100%",
                    spacing="2",
                ),
                on_click=on_toggle,
                width="100%",
                size="1",
                variant="ghost",
                justify_content="flex-start",
                padding="0.5rem",
            ),
            # Content
            rx.cond(
                is_expanded,
                rx.box(
                    content,
                    padding="0.5rem 0rem 0.5rem 1.5rem",
                    border_left="3px solid #e8f0e8",
                ),
                rx.box(),
            ),
            spacing="0",
            width="100%",
        ),
        padding="0.5rem 0",
        width="100%",
    )


def language_selector() -> rx.Component:
    """Language selection buttons."""
    return rx.vstack(
        rx.text("🌐 Language", font_weight="bold", font_size="sm"),
        rx.hstack(
            rx.button(
                "EN",
                on_click=lambda: AppState.set_language("en"),
                size="2",
                width="100%",
                is_outline=rx.cond(AppState.language == "en", False, True),
                color_scheme=rx.cond(AppState.language == "en", "green", "gray"),
            ),
            rx.button(
                "PT",
                on_click=lambda: AppState.set_language("pt"),
                size="2",
                width="100%",
                is_outline=rx.cond(AppState.language == "pt", False, True),
                color_scheme=rx.cond(AppState.language == "pt", "green", "gray"),
            ),
           
            width="100%",
            spacing="1",
        ),
        width="100%",
        padding="0.75rem",
    )


def country_selector() -> rx.Component:
    """Country selection buttons."""
    return rx.vstack(
        rx.text("🌍 Region", font_weight="bold", font_size="sm"),
        rx.hstack(
            rx.button(
                "Brazil",
                on_click=lambda: AppState.set_country("Brazil"),
                size="2",
                width="100%",
                is_outline=rx.cond(AppState.selected_country == "Brazil", False, True),
                color_scheme=rx.cond(AppState.selected_country == "Brazil", "green", "gray"),
            ),
            rx.button(
                "Canada",
                on_click=lambda: AppState.set_country("Canada"),
                size="2",
                width="100%",
                is_outline=rx.cond(AppState.selected_country == "Canada", False, True),
                color_scheme=rx.cond(AppState.selected_country == "Canada", "green", "gray"),
            ),
            width="100%",
            spacing="1",
        ),
        width="100%",
        padding="0.75rem",
    )


def map_controls_help() -> rx.Component:
    """Map controls help section."""
    return rx.box(
        rx.vstack(
            rx.text("🗺️ Map Controls", font_weight="bold", font_size="sm"),
            rx.vstack(
                rx.text("🖱️ Click layers to toggle", font_size="xs", color="gray"),
                rx.text("🎨 Choose base map at top right", font_size="xs", color="gray"),
                rx.text("📍 Draw to analyze custom areas", font_size="xs", color="gray"),
                spacing="1",
            ),
            spacing="2",
        ),
        padding="0.75rem",
        bg="blue.50",
        border_radius="md",
        border="1px solid #bee3f8",
    )


def about_section() -> rx.Component:
    """About/Info section."""
    return rx.vstack(
        rx.text("🏞️ Yvynation Platform", font_weight="bold", font_size="sm"),
        rx.text(
            "Global Forest Monitoring & Indigenous Territory Analysis",
            font_size="xs",
            color="gray",
        ),
        rx.divider(),
        rx.vstack(
            rx.text("📊 Datasets", font_weight="bold", font_size="xs"),
            rx.text("🌿 MapBiomas: Land cover 1985-2023", font_size="xs"),
            rx.text("🌲 Hansen GFC: Forest change 2000-2023", font_size="xs"),
            rx.text("🗺️ Indigenous Territories & Protected Areas", font_size="xs"),
            spacing="1",
        ),
        rx.divider(),
        rx.vstack(
            rx.text("✨ Features", font_weight="bold", font_size="xs"),
            rx.text("✅ Real-time spatial analysis", font_size="xs"),
            rx.text("✅ Multi-year comparison", font_size="xs"),
            rx.text("✅ Custom area analysis", font_size="xs"),
            rx.text("✅ Data export", font_size="xs"),
            spacing="1",
        ),
        rx.divider(),
        rx.text(
            "Built with Reflex, Earth Engine & Geospatial Science",
            font_size="xs",
            color="gray",
            font_style="italic",
        ),
        spacing="2",
        padding="0.75rem",
        bg="green.50",
        border_radius="md",
        border="1px solid #c6f6d5",
    )


def mapbiomas_layer_controls() -> rx.Component:
    """MapBiomas layer selection and display controls."""
    return rx.vstack(
        rx.text(
            "🌿 MapBiomas Land Cover (1985-2023)",
            font_size="xs",
            color="gray",
            margin="0",
            font_weight="bold",
        ),
        
        # Year selection grid
        rx.vstack(
            rx.text(
                "📅 Select Year",
                font_weight="bold",
                font_size="sm",
            ),
            rx.text(
                f"{len(MAPBIOMAS_YEARS)} years available ({min(MAPBIOMAS_YEARS)} - {max(MAPBIOMAS_YEARS)})",
                font_size="xs",
                color="gray",
            ),
            # Wrap of year buttons
            rx.flex(
                rx.foreach(
                    MAPBIOMAS_YEARS,
                    lambda year: rx.button(
                        rx.cond(
                            AppState.mapbiomas_current_year == year,
                            rx.text(f"✓{year}", font_weight="bold"),
                            rx.text(f"{year}"),
                        ),
                        on_click=lambda *args, y=year: AppState.set_mapbiomas_year(y),
                        size="1",
                        padding="6px 10px",
                        font_size="11px",
                        is_outline=rx.cond(
                            AppState.mapbiomas_current_year == year,
                            False,
                            True,
                        ),
                        color_scheme=rx.cond(
                            AppState.mapbiomas_current_year == year,
                            "green",
                            "gray",
                        ),
                    ),
                ),
                spacing="1",
                width="100%",
                flex_wrap="wrap",
            ),
            width="100%",
            spacing="2",
        ),
        
        # Add to map button
        rx.button(
            "➕ Add Layer to Map",
            on_click=lambda: AppState.add_mapbiomas_layer(),
            width="100%",
            color_scheme="green",
            size="2",
        ),
        
        # Show active layers
        rx.cond(
            AppState.mapbiomas_displayed_years.length() > 0,
            rx.vstack(
                rx.text("Active Layers:", font_size="xs", font_weight="bold", color="green"),
                rx.foreach(
                    AppState.mapbiomas_displayed_years,
                    lambda year: rx.hstack(
                        rx.badge(
                            rx.text(year),
                            color_scheme="green",
                            variant="solid",
                        ),
                        rx.button(
                            "✕",
                            on_click=lambda *args, y=year: AppState.remove_mapbiomas_layer(y),
                            size="1",
                            color_scheme="red",
                        ),
                        width="100%",
                        spacing="1",
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            rx.text(
                "No layers added",
                font_size="xs",
                color="gray",
                font_style="italic",
            ),
        ),
        
        spacing="2",
        width="100%",
    )


def hansen_layer_controls() -> rx.Component:
    """Hansen forest change layer selection and display controls."""
    return rx.vstack(
        rx.text(
            "🌲 Hansen Forest Change (2000-2023)",
            font_size="xs",
            color="gray",
            margin="0",
            font_weight="bold",
        ),
        
        # Year selection
        rx.box(
            rx.vstack(
                rx.text("📅 Select Year", font_weight="bold", font_size="sm"),
                rx.flex(
                    rx.foreach(
                        HANSEN_YEARS,
                        lambda year: rx.button(
                            rx.cond(
                                AppState.hansen_current_year == year,
                                rx.text(f"✓{year}", font_weight="bold"),
                                rx.text(f"{year}"),
                            ),
                            on_click=lambda *args, y=year: AppState.set_hansen_year(y),
                            size="1",
                            padding="6px 10px",
                            font_size="11px",
                            is_outline=rx.cond(
                                AppState.hansen_current_year == year,
                                False,
                                True,
                            ),
                            color_scheme=rx.cond(
                                AppState.hansen_current_year == year,
                                "blue",
                                "gray",
                            ),
                        ),
                    ),
                    spacing="1",
                    width="100%",
                    flex_wrap="wrap",
                ),
                rx.button(
                    "➕ Add Selected Year",
                    on_click=AppState.add_hansen_selected_year,
                    width="100%",
                    color_scheme="blue",
                    size="1",
                ),
                width="100%",
                spacing="2",
            ),
            padding="1rem",
            border="1px solid #e0e0e0",
            border_radius="md",
            bg="blue.50",
            width="100%",
        ),
        
        # Layer type selection
        rx.vstack(
            rx.text("📊 Select Data Type", font_weight="bold", font_size="sm"),
            rx.vstack(
                rx.hstack(
                    rx.button(
                        "📊 Tree Cover 2000",
                        on_click=lambda: AppState.add_hansen_layer("cover"),
                        width="100%",
                        color_scheme=rx.cond(
                            AppState.hansen_displayed_layers.contains("cover"),
                            "green",
                            "blue",
                        ),
                        size="2",
                    ),
                    rx.button(
                        "✕",
                        on_click=lambda: AppState.remove_hansen_layer("cover"),
                        width="auto",
                        color_scheme="gray",
                        size="2",
                    ),
                    width="100%",
                    spacing="1",
                ),
                rx.hstack(
                    rx.button(
                        "🔴 Tree Loss",
                        on_click=lambda: AppState.add_hansen_layer("loss"),
                        width="100%",
                        color_scheme=rx.cond(
                            AppState.hansen_displayed_layers.contains("loss"),
                            "green",
                            "red",
                        ),
                        size="2",
                    ),
                    rx.button(
                        "✕",
                        on_click=lambda: AppState.remove_hansen_layer("loss"),
                        width="auto",
                        color_scheme="gray",
                        size="2",
                    ),
                    width="100%",
                    spacing="1",
                ),
                rx.hstack(
                    rx.button(
                        "🟢 Tree Gain",
                        on_click=lambda: AppState.add_hansen_layer("gain"),
                        width="100%",
                        color_scheme=rx.cond(
                            AppState.hansen_displayed_layers.contains("gain"),
                            "green",
                            "green",
                        ),
                        size="2",
                    ),
                    rx.button(
                        "✕",
                        on_click=lambda: AppState.remove_hansen_layer("gain"),
                        width="auto",
                        color_scheme="gray",
                        size="2",
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="1",
                width="100%",
            ),
            width="100%",
            spacing="2",
        ),
        
        # Show active layers
        rx.cond(
            AppState.hansen_displayed_layers.length() > 0,
            rx.vstack(
                rx.text("Active Layers:", font_size="xs", font_weight="bold", color="green"),
                rx.foreach(
                    AppState.hansen_displayed_layers,
                    lambda layer: rx.badge(
                        rx.cond(
                            layer == "cover",
                            "📊 Tree Cover",
                            rx.cond(
                                layer == "loss",
                                "🔴 Tree Loss",
                                "🟢 Tree Gain"
                            )
                        ),
                        color_scheme="green",
                        variant="solid",
                    ),
                ),
                spacing="1",
                width="100%",
            ),
            rx.text(
                "No layers added",
                font_size="xs",
                color="gray",
                font_style="italic",
            ),
        ),
        
        spacing="2",
        width="100%",
    )


def territory_selection_controls() -> rx.Component:
    """Territory and analysis controls with searchable selection."""
    return rx.vstack(
        # Load territories button (if not loaded yet)
        rx.cond(
            AppState.available_territories.length() == 0,
            rx.button(
                "📍 Load Territories from EE",
                on_click=AppState.initialize_app,
                width="100%",
                color_scheme="green",
                size="2",
            ),
            rx.box(),
        ),
        
        # Search input
        rx.input(
            placeholder="🔍 Search territories...",
            value=AppState.territory_search_query,
            on_change=AppState.set_territory_search_query,
            size="2",
            width="100%",
        ),
        
        # Territory selector with filtered results
        rx.select(
            items=AppState.filtered_territories,
            value=AppState.selected_territory,
            on_change=AppState.set_selected_territory,
            placeholder="Select a territory",
            size="2",
            width="100%",
        ),
        
        # Territory info and analysis buttons
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.badge(
                    AppState.selected_territory,
                    color_scheme="green",
                    variant="solid",
                ),
                rx.text(
                    "Analyze territory area",
                    font_size="xs",
                    color="gray",
                ),
                rx.vstack(
                    # MapBiomas analysis
                    rx.cond(
                        AppState.mapbiomas_analysis_pending,
                        rx.button(
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Analyzing..."),
                                spacing="1",
                            ),
                            is_disabled=True,
                            size="2",
                            width="100%",
                            color_scheme="blue",
                        ),
                        rx.button(
                            "📊 MapBiomas",
                            on_click=AppState.run_mapbiomas_analysis_on_territory,
                            size="2",
                            width="100%",
                            color_scheme="green",
                        ),
                    ),
                    # Hansen analysis  
                    rx.cond(
                        AppState.hansen_analysis_pending,
                        rx.button(
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text("Analyzing..."),
                                spacing="1",
                            ),
                            is_disabled=True,
                            size="2",
                            width="100%",
                            color_scheme="blue",
                        ),
                        rx.button(
                            "🌲 Hansen",
                            on_click=AppState.run_hansen_analysis_on_territory,
                            size="2",
                            width="100%",
                            color_scheme="green",
                        ),
                    ),
                    width="100%",
                    spacing="1",
                ),
                spacing="2",
                width="100%",
            ),
            rx.text(
                "👇 Select a territory",
                font_size="xs",
                color="gray",
            ),
        ),
        spacing="2",
        width="100%",
    )


def sidebar() -> rx.Component:
    """Modern sidebar with collapsible sections."""
    return rx.box(
        rx.vstack(
            # Header
            rx.box(
                rx.vstack(
                    rx.heading("🛠️ Controls", size="3"),
                    rx.text(
                        "Manage layers & analyze territories",
                        font_size="xs",
                        color="gray",
                    ),
                    spacing="0",
                ),
                padding="1rem",
                border_bottom="1px solid #e0e0e0",
                background="linear-gradient(135deg, #f5f9ff 0%, #ffffff 100%)",
            ),
            
            # Main content scrollable
            rx.box(
                rx.vstack(
                    # Quick access section
                    rx.box(
                        rx.vstack(
                            language_selector(),
                            country_selector(),
                            spacing="0",
                        ),
                        padding="0.5rem",
                        background="white",
                        border_bottom="1px solid #e8e8e8",
                    ),
                    
                    # Collapsible MapBiomas section
                    collapsible_section(
                        "🌿 MapBiomas Layers",
                        mapbiomas_layer_controls(),
                        AppState.sidebar_mapbiomas_expanded,
                        lambda: AppState.toggle_sidebar_section("mapbiomas"),
                    ),
                    
                    # Collapsible Hansen section
                    collapsible_section(
                        "🌲 Hansen Global Forest",
                        hansen_layer_controls(),
                        AppState.sidebar_hansen_expanded,
                        lambda: AppState.toggle_sidebar_section("hansen"),
                    ),
                    
                    # Collapsible Analysis section (analyze drawn geometry)
                    collapsible_section(
                        "🔬 Analyze Geometry",
                        analysis_controls(),
                        AppState.sidebar_territory_expanded,
                        lambda: AppState.toggle_sidebar_section("territory"),
                    ),
                    
                    # Collapsible Territory section
                    collapsible_section(
                        "🗺️ Territory Selection",
                        territory_selection_controls(),
                        AppState.sidebar_geometry_expanded,
                        lambda: AppState.toggle_sidebar_section("geometry"),
                    ),
                    
                    # Collapsible Geometry Upload section (Phase 2)
                    collapsible_section(
                        "📤 Upload Geometry",
                        geometry_file_upload(),
                        AppState.sidebar_geometry_expanded,
                        lambda: AppState.toggle_sidebar_section("geometry"),
                    ),
                    
                    # Map controls help section (always visible)
                    rx.box(
                        map_controls_help(),
                        padding="0.5rem",
                        border_top="1px solid #e8e8e8",
                    ),
                    
                    # About section (always visible)
                    rx.box(
                        about_section(),
                        padding="0.5rem",
                    ),
                    
                    spacing="0",
                    width="100%",
                ),
                padding="0",
                height="calc(100vh - 140px)",
                overflow_y="auto",
            ),
            
            spacing="0",
            height="100vh",
            width="100%",
        ),
        width="340px",
        height="100vh",
        bg="white",
        border_right="2px solid #e0e0e0",
        box_shadow="0 2px 8px rgba(0,0,0,0.1)",
    )
