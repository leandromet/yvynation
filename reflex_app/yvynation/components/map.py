"""
Map component for Yvynation Reflex app.
Renders Folium map with Earth Engine layers using reactive state.
Includes drawing capture with Leaflet Draw integration.
"""

import reflex as rx
from ..state import AppState
import folium
from folium.plugins import Draw
import logging
import json

logger = logging.getLogger(__name__)


def extract_and_save_geojson():
    """
    Placeholder for extracting GeoJSON from Leaflet Draw layer.
    
    Due to how Folium renders as a static HTML in Reflex's rx.html(),
    direct JavaScript execution to extract drawn geometries requires
    either:
    1. Custom Leaflet Draw event handler that posts to a Reflex API
    2. Using Folium's built-in export functionality
    3. File upload mechanism for GeoJSON
    
    For now, we show a message and provide a test geometry.
    """
    return AppState.add_test_geometry()


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
    Interactive map with Earth Engine layers and drawing capabilities.
    Uses AppState.map_html computed property which auto-updates when layers change.
    """
    return rx.vstack(
        rx.box(
            # Display the reactive map HTML from AppState.map_html
            rx.html(AppState.map_html, width="100%", height="100%"),
            width="100%",
            height="800px",
            overflow_y="auto",
            id="map-container",
        ),
        
        # Drawing controls
        rx.hstack(
            rx.button(
                "💾 Save Drawing",
                on_click=extract_and_save_geojson,
                color_scheme="green",
                size="1",
                title="Extract geometries from the map and save them for analysis",
            ),
            rx.button(
                "🧪 Test Geometry",
                on_click=AppState.add_test_geometry,
                color_scheme="orange",
                size="1",
                title="Load a sample geometry to test the selection and analysis features",
            ),
            rx.button(
                "🗑️ Clear Drawings",
                on_click=AppState.clear_drawn_features,
                color_scheme="red",
                size="1",
                title="Clear all drawn geometries",
            ),
            width="100%",
            padding="1rem",
            bg="white",
            border_top="1px solid #e0e0e0",
            spacing="2",
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
