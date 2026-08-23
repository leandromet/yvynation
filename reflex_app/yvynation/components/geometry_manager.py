"""
Geometry Manager Component for Yvynation Reflex app.
Handles selection, analysis, and management of drawn and uploaded geometries.
Also manages loading territories from Earth Engine.
"""

import reflex as rx
from ..state import AppState
import ee
import json
import logging

logger = logging.getLogger(__name__)


def geometry_manager() -> rx.Component:
    """
    Geometry manager panel for selecting and analyzing drawn geometries and territories.
    Similar to Streamlit's polygon_analysis_header but for Reflex.
    """
    return rx.vstack(
        # Title
        rx.text(
            "📍 Geometry Manager",
            font_size="lg",
            font_weight="bold",
            color="#1f2937",
        ),
        
        # Load territories button if not loaded
        rx.cond(
            AppState.available_territories.length() == 0,
            rx.button(
                "🏛️ Load Territories",
                on_click=AppState.initialize_app,
                width="100%",
                color_scheme="green",
                size="1",
            ),
            rx.box(),
        ),
        
        # Territory Section
        rx.box(
            rx.vstack(
                rx.text(
                    "🏛️ Territories from Earth Engine",
                    font_size="sm",
                    font_weight="bold",
                    color="#374151",
                ),
                
                rx.text(
                    "Search and add territories for analysis",
                    font_size="xs",
                    color="#6b7280",
                    font_style="italic",
                ),
                
                # Search input
                rx.input(
                    placeholder="Search territories...",
                    value=AppState.territory_search_query,
                    on_change=AppState.set_territory_search_query,
                    width="100%",
                    size="sm",
                ),
                
                # Territory list
                rx.cond(
                    AppState.filtered_territories.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            AppState.filtered_territories,
                            lambda territory: rx.hstack(
                                rx.text(
                                    territory,
                                    font_size="sm",
                                    flex="1",
                                ),
                                rx.button(
                                    "+ Add",
                                    on_click=lambda: AppState.add_territory_geometry(territory),
                                    size="xs",
                                    color_scheme="green",
                                ),
                                width="100%",
                                spacing="2",
                                padding="0.5rem",
                                border_bottom="1px solid #e5e7eb",
                            ),
                        ),
                        spacing="0",
                        width="100%",
                        max_height="200px",
                        overflow_y="auto",
                    ),
                    rx.text(
                        "No territories found",
                        color="#9ca3af",
                        font_size="xs",
                    ),
                ),
                
                spacing="2",
                width="100%",
            ),
            padding="1rem",
            bg="amber.50",
            border="1px solid #fcd34d",
            border_radius="md",
            width="100%",
        ),
        
        rx.divider(),
        
        # Instructions
        rx.text(
            "Drawn / Added Geometries",
            font_size="sm",
            font_weight="bold",
            color="#6b7280",
            font_style="italic",
        ),
        
        # Drawn Geometries List
        rx.cond(
            AppState.drawn_features.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Available:",
                        font_size="sm",
                        font_weight="bold",
                        color="#374151",
                    ),
                    rx.badge(AppState.drawn_features.length(), color_scheme="blue"),
                    width="100%",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            AppState.drawn_features,
                            lambda feature: rx.box(
                                rx.hstack(
                                    rx.text(
                                        f"📌 {feature.get('type', 'Unknown')} - {feature.get('name') or feature.get('territory_name') or 'Geometry'}",
                                        font_size="sm",
                                        font_weight="bold",
                                        flex="1",
                                    ),
                                    rx.spacer(),
                                    rx.button(
                                        "Select",
                                        size="xs",
                                        color_scheme="blue",
                                    ),
                                    rx.button(
                                        "🗑️",
                                        size="xs",
                                        variant="ghost",
                                        color_scheme="red",
                                    ),
                                    width="100%",
                                    spacing="1",
                                ),
                                padding="0.75rem",
                                border="1px solid #e5e7eb",
                                border_radius="md",
                                width="100%",
                                _hover={"bg": "gray.50"},
                            ),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.box(
                rx.text(
                    "No geometries added yet. Draw or add territories above.",
                    color="#9ca3af",
                    font_size="sm",
                ),
                padding="1rem",
                bg="gray.50",
                border_radius="md",
                border="1px dashed #d1d5db",
                width="100%",
            ),
        ),
        
        # Clear all button
        rx.cond(
            AppState.drawn_features.length() > 0,
            rx.button(
                "🗑️ Clear All",
                on_click=AppState.clear_geometries,
                width="100%",
                color_scheme="red",
                variant="outline",
                size="1",
            ),
            rx.box(),
        ),
        
        spacing="3",
        width="100%",
        padding="1rem",
        bg="white",
        border_radius="md",
        border="1px solid #e5e7eb",
    )


def geometry_analysis_panel() -> rx.Component:
    """
    Analysis panel for selected geometry.
    Shows MapBiomas, Hansen, and other analysis for the selected drawn geometry.
    """
    return rx.cond(
        AppState.drawn_features.length() > 0,
        rx.vstack(
            rx.divider(),
            rx.text(
                "📊 Geometry Analysis",
                font_size="lg",
                font_weight="bold",
                color="#1f2937",
            ),
            
            rx.callout(
                rx.text(
                    "Select a geometry from the manager on the left to view detailed analysis.",
                    font_size="sm",
                ),
                icon="info",
                color_scheme="blue",
            ),
            
            spacing="3",
            width="100%",
        ),
        rx.box(),
    )

