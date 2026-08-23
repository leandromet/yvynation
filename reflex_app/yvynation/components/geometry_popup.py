"""
Geometry information popup component.
Displays detailed information about selected drawn geometries.
"""

import reflex as rx
from ..state import AppState


def geometry_info_popup() -> rx.Component:
    """Display popup with detailed geometry information."""
    return rx.cond(
        AppState.show_geometry_popup,
        rx.box(
            # Overlay background
            rx.box(
                width="100%",
                height="100%",
                bg="rgba(0,0,0,0.5)",
                position="fixed",
                top="0",
                left="0",
                z_index="999",
                on_click=AppState.hide_geometry_info,
            ),
            # Modal content box
            rx.box(
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.text("📍 Geometry Information", font_weight="bold", font_size="lg"),
                        rx.spacer(),
                        rx.button(
                            "✕",
                            on_click=AppState.hide_geometry_info,
                            size="1",
                            variant="ghost",
                        ),
                        width="100%",
                    ),
                    rx.divider(),
                    
                    # Content
                    rx.vstack(
                        # Geometry name/title
                        rx.hstack(
                            rx.text("Name:", font_weight="bold", width="120px"),
                            rx.text(
                                AppState.geometry_popup_info.get("name", "Unknown"),
                                color="gray",
                            ),
                            width="100%",
                        ),
                        
                        # Geometry type
                        rx.hstack(
                            rx.text("Type:", font_weight="bold", width="120px"),
                            rx.badge(
                                AppState.geometry_popup_info.get("type", "Unknown"),
                                color_scheme="blue",
                            ),
                            width="100%",
                        ),
                        
                        # Area in km²
                        rx.hstack(
                            rx.text("Area:", font_weight="bold", width="120px"),
                            rx.text(
                                AppState.geometry_popup_info.get("area_km2", "0"),
                                color="gray",
                            ),
                            rx.text("km²", color="gray"),
                            width="100%",
                        ),
                        
                        # Number of coordinates
                        rx.hstack(
                            rx.text("Coordinates:", font_weight="bold", width="120px"),
                            rx.text(
                                str(AppState.geometry_popup_info.get("coordinates_count", 0)),
                                color="gray",
                            ),
                            width="100%",
                        ),
                        
                        # Created at
                        rx.hstack(
                            rx.text("Created:", font_weight="bold", width="120px"),
                            rx.text(
                                AppState.geometry_popup_info.get("created_at", "Unknown"),
                                font_size="xs",
                                color="gray",
                            ),
                            width="100%",
                        ),
                        
                        spacing="2",
                        width="100%",
                    ),
                    
                    rx.divider(),
                    
                    # Footer buttons
                    rx.hstack(
                        rx.button(
                            "🗑️ Delete",
                            on_click=lambda: [
                                AppState.remove_geometry(
                                    AppState.geometry_popup_info.get("index", 0)
                                ),
                                AppState.hide_geometry_info(),
                            ],
                            color_scheme="red",
                            size="1",
                        ),
                        rx.button(
                            "Analyze",
                            on_click=lambda: [
                                AppState.set_selected_geometry(
                                    AppState.geometry_popup_info.get("index", 0)
                                ),
                                AppState.hide_geometry_info(),
                            ],
                            color_scheme="green",
                            size="1",
                        ),
                        rx.button(
                            "Close",
                            on_click=AppState.hide_geometry_info,
                            size="1",
                        ),
                        spacing="2",
                        width="100%",
                        justify_content="flex-end",
                    ),
                    
                    spacing="3",
                    width="100%",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                width="500px",
                bg="white",
                border="1px solid #e0e0e0",
                border_radius="8px",
                padding="2rem",
                box_shadow="0 4px 6px rgba(0,0,0,0.1)",
                z_index="1000",
            ),
            width="100%",
            height="100%",
        ),
        rx.box(),
    )
