"""
Map component with Leaflet integration for Yvynation Reflex app.
Provides interactive mapping with layer controls and drawing capabilities.
"""

import reflex as rx
from ..state import AppState
import json


def leaflet_map() -> rx.Component:
    """
    Leaflet map component with support for multiple layers.
    
    Note: Reflex has built-in Leaflet support through rx.script.
    For advanced features, we can use the plotly map or custom HTML/JS.
    """
    # Using a simplified setup for initial implementation
    # Full Leaflet integration would use custom JS component
    
    return rx.box(
        rx.cond(
            AppState.data_loaded,
            rx.vstack(
                rx.heading("Interactive Map", size="3"),
                rx.text(
                    "Map region: ({:.2f}, {:.2f}) | Zoom: {}".format(
                        AppState.map_center[0],
                        AppState.map_center[1],
                        AppState.map_zoom,
                    ),
                    font_size="1",
                    color="gray",
                ),
                # Placeholder for actual Leaflet map
                rx.box(
                    rx.text("Leaflet Map will render here"),
                    height="600px",
                    bg="#e0e0e0",
                    border="1px solid #999",
                    border_radius="md",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.hstack(
                    rx.button(
                        "📍 Clear Drawing",
                        on_click=AppState.clear_drawn_features,
                        color_scheme="red",
                        size="1",
                    ),
                    rx.button(
                        "📥 Upload GeoJSON",
                        color_scheme="blue",
                        size="1",
                    ),
                    width="100%",
                ),
                width="100%",
                height="100%",
            ),
            rx.vstack(
                rx.spinner(color="green"),
                rx.text("Loading map data..."),
                align_items="center",
                justify_content="center",
                height="600px",
            ),
        ),
        width="100%",
        padding="1rem",
    )


def map_metrics() -> rx.Component:
    """Display active layer metrics and statistics."""
    return rx.box(
        rx.text("Layer metrics placeholder"),
        padding="1rem",
    )

