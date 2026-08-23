"""
Feature Capture Component for Yvynation Reflex app.
Handles capturing drawn geometries from the map and storing them in state.
"""

import reflex as rx
from ..state import AppState
import json


def feature_capture_panel() -> rx.Component:
    """
    Panel for capturing and managing drawn features from the Folium map.
    Provides instructions and manual input options.
    """
    return rx.vstack(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="pencil", color="blue.500"),
                    rx.heading("Draw Geometries", size="md"),
                    spacing="2",
                ),
                
                rx.text(
                    "Use the draw tools on the map (top-left) to create polygons, rectangles, polylines, or markers.",
                    color="gray.600",
                    font_size="sm",
                ),
                
                # Instructions
                rx.vstack(
                    rx.text("📍 Drawing Steps:", font_weight="bold", font_size="sm"),
                    rx.ordered_list(
                        rx.list_item("Click the draw tool icons in the top-left corner of the map"),
                        rx.list_item("Click on the map to create geometry vertices"),
                        rx.list_item("Complete your shape and save it"),
                        rx.list_item("Use 'Add to Manager' button below to save it"),
                        color="gray.600",
                        font_size="xs",
                    ),
                    spacing="2",
                    width="100%",
                ),
                
                spacing="2",
                width="100%",
            ),
            padding="1rem",
            bg="blue.50",
            border="1px solid #bfdbfe",
            border_radius="md",
            width="100%",
        ),
        
        # Manual GeoJSON input
        rx.box(
            rx.vstack(
                rx.heading("Or Paste GeoJSON", size="sm"),
                
                rx.textarea(
                    id="geojson_input",
                    placeholder='{"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [...]}}',
                    rows=6,
                    width="100%",
                    font_size="xs",
                    font_family="monospace",
                ),
                
                rx.button(
                    "+ Add GeoJSON Geometry",
                    on_click=AppState.add_geojson_feature,
                    width="100%",
                    color_scheme="blue",
                ),
                
                spacing="2",
                width="100%",
            ),
            padding="1rem",
            border="1px solid #e5e7eb",
            border_radius="md",
            width="100%",
        ),
        
        # Feature extraction instructions
        rx.callout(
            rx.text(
                "💡 Tip: Most map drawing tools export drawn features as GeoJSON. You can export and paste them above, or click 'Capture Drawings' to attempt automatic extraction.",
                font_size="sm",
            ),
            icon="info",
            color_scheme="blue",
        ),
        
        spacing="3",
        width="100%",
        padding="1rem",
        bg="white",
        border_radius="md",
        border="1px solid #e5e7eb",
    )


def drawing_quick_actions() -> rx.Component:
    """Quick action buttons for drawing management."""
    return rx.hstack(
        rx.button(
            "🎯 Quick Draw Test",
            on_click=AppState.add_test_geometry,
            size="1",
            color_scheme="purple",
            variant="outline",
        ),
        
        rx.button(
            "📥 Import File",
            size="1",
            variant="outline",
            is_disabled=True,  # TODO: Implement file upload
        ),
        
        rx.text(
            AppState.drawn_features.length(),
            font_weight="bold",
            color="blue.600",
        ),
        rx.text("geometries", color="gray.600", font_size="sm"),
        
        spacing="2",
        width="100%",
    )
