"""
Map component for Yvynation Reflex app.
Renders Folium map with Earth Engine layers using reactive state.
"""

import reflex as rx
from ..state import AppState
import folium
from folium.plugins import Draw
import logging

logger = logging.getLogger(__name__)


def create_base_map():
    """
    Create a base Folium map (fallback, not used in normal flow).
    The actual map is generated via AppState.map_html computed property.
    """
    try:
        m = folium.Map(
            location=[-5, -60],
            zoom_start=4,
            tiles="OpenStreetMap"
        )
        
        # Add layer control
        folium.LayerControl(position='topright').add_to(m)
        
        return m._repr_html_()
    except Exception as e:
        logger.error(f"Error creating base map: {e}")
        m = folium.Map(location=[-5, -60], zoom_start=4, tiles="OpenStreetMap")
        folium.LayerControl().add_to(m)
        return m._repr_html_()


def leaflet_map() -> rx.Component:
    """
    Interactive map with Earth Engine layers.
    Uses AppState.map_html computed property which auto-updates when layers change.
    """
    return rx.vstack(
        rx.box(
            # Display the reactive map HTML from AppState.map_html
            rx.html(AppState.map_html, width="100%", height="100%"),
            width="100%",
            height="800px",
            overflow_y="auto",
        ),
        
        # Layer status badge - shows count of selected layers
        rx.box(
            rx.vstack(
                rx.text("📊 Selected Layers:", font_weight="bold", font_size="sm"),
                rx.hstack(
                    rx.cond(
                        AppState.mapbiomas_displayed_years.length() > 0,
                        rx.badge(
                            rx.text(
                                f"🗺️ MapBiomas: ",
                                AppState.mapbiomas_displayed_years.length(),
                            ),
                            color_scheme="green",
                        ),
                        rx.box(),
                    ),
                    rx.cond(
                        AppState.hansen_displayed_layers.length() > 0,
                        rx.badge(
                            rx.text(
                                f"🌲 Hansen: ",
                                AppState.hansen_displayed_layers.length(),
                            ),
                            color_scheme="blue",
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                ),
                spacing="1",
            ),
            padding="1rem",
            bg="blue.50",
            border_left="4px solid #3b82f6",
            width="100%",
            display=rx.cond(
                AppState.mapbiomas_displayed_years.length() > 0,
                "block",
                rx.cond(
                    AppState.hansen_displayed_layers.length() > 0,
                    "block",
                    "none",
                ),
            ),
        ),
        
        rx.hstack(
            rx.button(
                "🗑️ Clear All",
                on_click=AppState.clear_all_layers,
                color_scheme="red",
                size="2"
            ),
            width="100%",
            padding="1rem",
            bg="white",
            border_top="1px solid #e0e0e0",
        ),
        
        width="100%",
        spacing="0",
    )


def map_metrics() -> rx.Component:
    """Display map metrics."""
    return rx.hstack(
        rx.badge(
            rx.cond(
                AppState.mapbiomas_displayed_years.length() > 0,
                rx.text(
                    f"🗺️ MapBiomas (",
                    AppState.mapbiomas_displayed_years.length(),
                    ")",
                ),
                "MapBiomas",
            ),
            color_scheme="green",
        ),
        rx.badge(
            rx.cond(
                AppState.hansen_displayed_layers.length() > 0,
                rx.text(
                    f"🌲 Hansen (",
                    AppState.hansen_displayed_layers.length(),
                    ")",
                ),
                "Hansen",
            ),
            color_scheme="blue",
        ),
        spacing="2",
    )
