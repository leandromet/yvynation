"""
Custom Leaflet component for Reflex.
Provides interactive mapping with drawing and multiple layers.

This replaces streamlit-folium in pure Python with Reflex-native approach.
"""

import reflex as rx
from typing import Dict, Any, List, Optional
import json


class LeafletMapState(rx.State):
    """State for Leaflet map interactions."""
    
    map_bounds: Optional[List] = None
    map_zoom: int = 4
    map_center: tuple = (-5.0, -60.0)  # Default to Amazon region
    drawn_items: List[Dict[str, Any]] = []
    last_click_coords: Optional[tuple] = None


def leaflet_js_init() -> rx.Component:
    """Initialize Leaflet map with JavaScript."""
    return rx.script("""
    // Initialize Leaflet map only once
    if (!window.leafletMapInitialized) {
        window.leafletMapInitialized = true;
        
        // Create map
        const map = L.map('map').setView([-5, -60], 4);
        
        // Add OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19,
        }).addTo(map);
        
        // Add drawing toolbar
        const drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);
        
        const drawControl = new L.Control.Draw({
            draw: {
                polygon: true,
                polyline: false,
                rectangle: true,
                circle: false,
                marker: false,
            },
            edit: {
                featureGroup: drawnItems,
            }
        });
        map.addControl(drawControl);
        
        // Store map reference
        window.leafletMap = map;
        window.drawnItems = drawnItems;
    }
    """)


def leaflet_map_container() -> rx.Component:
    """Leaflet map container with HTML/CSS."""
    return rx.box(
        # The actual map will be rendered here by JavaScript
        id="map",
        width="100%",
        height="600px",
        border_radius="md",
        overflow="hidden",
    )


def leaflet_integration() -> rx.Component:
    """Full Leaflet map integration with controls."""
    return rx.vstack(
        # Include Leaflet CSS and JS libraries
        rx.script(src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"),
        rx.script(src="https://unpkg.com/@leaflet/draw@1.0.4/dist/leaflet.draw.js"),
        rx.html(
            '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />'
            '<link rel="stylesheet" href="https://unpkg.com/@leaflet/draw@1.0.4/dist/leaflet.draw.css" />'
        ),
        
        # Map container
        leaflet_map_container(),
        
        # Initialize map
        leaflet_js_init(),
        
        # Controls below map
        rx.hstack(
            rx.button("📍 Clear Drawings", color_scheme="red", size="1"),
            rx.button("📤 Export GeoJSON", color_scheme="blue", size="1"),
            rx.button("📥 Import GeoJSON", color_scheme="green", size="1"),
            width="100%",
            spacing="2",
        ),
        
        width="100%",
        spacing="4",
    )
