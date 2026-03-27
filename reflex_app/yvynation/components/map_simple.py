"""
Simplified map component for Yvynation Reflex app.
Shows base map with basemap options and indicates selected layers.
"""

import reflex as rx
from ..state import AppState
import folium
from folium.plugins import Draw
import logging

logger = logging.getLogger(__name__)


def create_base_map():
    """Create a base Folium map with basemap options."""
    m = folium.Map(
        location=[-5, -60],
        zoom_start=4,
        tiles="OpenStreetMap"
    )
    
    # Add alternative basemaps
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Street',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    # Add Leaflet Draw for geometry drawing
    Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': True,
            'polygon': True,
            'rectangle': True,
            'circle': False,
            'circlemarker': False,
            'marker': True,
        }
    ).add_to(m)
    
    # Add layer control
    folium.LayerControl(position='topright').add_to(m)
    
    return m._repr_html_()


def leaflet_map() -> rx.Component:
    """
    Interactive map with basemap options, drawing tools, and layer indicators.
    """
    return rx.vstack(
        # Map HTML container
        rx.box(
            rx.html(
                create_base_map(),
                width="100%",
                height="100%",
            ),
            width="100%",
            height="800px",
            overflow_y="auto",
            overflow_x="hidden",
        ),
        
        # Layer indicators
        rx.cond(
            rx.or_(
                AppState.mapbiomas_displayed_years.length() > 0,
                AppState.hansen_displayed_layers.length() > 0,
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "📊 Selected Layers (see sidebar for details):",
                        font_weight="bold",
                        font_size="sm",
                    ),
                    rx.hstack(
                        rx.cond(
                            AppState.mapbiomas_displayed_years.length() > 0,
                            rx.badge(
                                f"🗺️ MapBiomas: {AppState.mapbiomas_displayed_years.length()} years",
                                color_scheme="green",
                            ),
                            rx.box(),
                        ),
                        rx.cond(
                            AppState.hansen_displayed_layers.length() > 0,
                            rx.badge(
                                f"🌲 Hansen: {AppState.hansen_displayed_layers.length()} types",
                                color_scheme="blue",
                            ),
                            rx.box(),
                        ),
                        spacing="2",
                    ),
                    spacing="2",
                ),
                padding="1rem",
                bg="blue.50",
                border_left="4px solid #3b82f6",
                width="100%",
            ),
            rx.box(),
        ),
        
        # Control buttons
        rx.hstack(
            rx.button(
                "📍 Clear Drawings",
                on_click=AppState.clear_drawn_features,
                color_scheme="red",
                size="2",
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
    return rx.vstack(
        rx.hstack(
            rx.badge(
                rx.cond(
                    AppState.mapbiomas_displayed_years.length() > 0,
                    rx.text(f"🗺️ MapBiomas ({AppState.mapbiomas_displayed_years.length()})"),
                    rx.text("No MapBiomas"),
                ),
                color_scheme="green",
            ),
            rx.badge(
                rx.cond(
                    AppState.hansen_displayed_layers.length() > 0,
                    rx.text(f"🌲 Hansen ({AppState.hansen_displayed_layers.length()})"),
                    rx.text("No Hansen"),
                ),
                color_scheme="blue",
            ),
            spacing="2",
        ),
        width="100%",
    )
