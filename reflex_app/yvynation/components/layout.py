"""
Main page layout for Yvynation Reflex app.
Includes sidebar navigation and main content areas.
"""

import reflex as rx
from ..state import AppState
from .geometry_manager import geometry_manager, geometry_analysis_panel


def main_page() -> rx.Component:
    """
    Main page layout with sidebar and content areas.
    Similar to Streamlit's sidebar + main content pattern.
    """
    return rx.vstack(
        # Title & header
        rx.box(
            rx.vstack(
                rx.heading(
                    "🌍 Yvynation",
                    size="xl",
                    color="white",
                ),
                rx.text(
                    "Territory & Land Cover Analysis",
                    color="gray.200",
                    font_size="sm",
                ),
                spacing="0",
            ),
            bg="linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            padding="1.5rem",
            width="100%",
        ),
        
        # Main content area with sidebar
        rx.hstack(
            # Sidebar - Geometry Manager
            rx.box(
                rx.vstack(
                    geometry_manager(),
                    spacing="2",
                    width="100%",
                ),
                width="25%",
                height="calc(100vh - 120px)",
                overflow_y="auto",
                border_right="1px solid #e5e7eb",
                bg="gray.50",
                padding="1rem",
            ),
            
            # Main content - Map and analysis
            rx.vstack(
                # Map display
                rx.box(
                    rx.html(AppState.map_html, width="100%", height="100%"),
                    width="100%",
                    height="600px",
                    overflow="hidden",
                    border_radius="md",
                    border="1px solid #e5e7eb",
                ),
                
                # Analysis panel below map
                geometry_analysis_panel(),
                
                width="45%",
                height="calc(100vh - 120px)",
                overflow_y="auto",
                padding="1rem",
                spacing="2",
            ),
            
            width="100%",
            spacing="0",
            height="calc(100vh - 120px)",
        ),
        
        width="100%",
        height="100vh",
        spacing="0",
        font_family="system-ui, -apple-system, sans-serif",
    )
