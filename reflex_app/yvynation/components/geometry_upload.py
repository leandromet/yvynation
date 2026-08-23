"""
Geometry file upload component for Yvynation Reflex app.
Handles uploading and parsing KML, GeoJSON files.
"""

import reflex as rx
from ..state import AppState
from ..utils.translations import t
from ..utils.geometry_handler import parse_geojson, parse_kml, validate_geometry


def geometry_file_upload() -> rx.Component:
    """
    File upload widget for geometry files (KML, GeoJSON).
    Displays in sidebar or as a dialog.
    """
    return rx.vstack(
        # Upload instructions
        rx.heading(
            "📤 Upload Geometry",
            size="4",
        ),
        rx.text(
            "Supported formats: GeoJSON (.json), KML (.kml)",
            font_size="sm",
            color="gray",
        ),
        
        # File upload component
        rx.upload(
            rx.vstack(
                rx.button(
                    "📁 Choose File or Drop Here",
                    is_loading=False,
                    width="100%",
                    color_scheme="blue",
                ),
                rx.text(
                    "Support for .json, .kml files",
                    text_align="center",
                    font_size="xs",
                    color="gray",
                ),
                width="100%",
                spacing="2",
            ),
            id="geometry_upload",
            multiple=False,
            accept={
                "application/json": [".json", ".geojson"],
                "application/vnd.google-earth.kml+xml": [".kml"],
                "text/plain": [".kml"],
            },
            max_height="200px",
            on_drop=AppState.handle_geometry_upload,
        ),
        
        # File info display
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.callout(
                    rx.hstack(
                        rx.text("✅", font_size="lg"),
                        rx.vstack(
                            rx.heading("Geometry Loaded", size="5"),
                            rx.text(
                                AppState.selected_territory,
                                font_size="sm",
                            ),
                            spacing="0",
                        ),
                    ),
                    icon="check_circle_2",
                    color_scheme="green",
                    width="100%",
                ),
                rx.divider(),
                spacing="2",
            )
        ),
        
        # Buffer distance input state (store in session)
        rx.input(
            placeholder="Distance in km (e.g., 5)",
            type_="number",
            min_="0.1",
            max_="100",
            step="0.5",
            value=AppState.buffer_distance_input,
            on_change=AppState.set_buffer_distance_input,
            width="100%",
            display="none",  # Hidden - we'll use a separate input in the UI
        ),
        
        # Buffer creation section
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.heading("🔄 Create Buffer", size="4"),
                rx.text(
                    "Create a buffer zone around the geometry for edge analysis",
                    font_size="sm",
                    color="gray",
                ),
                
                rx.hstack(
                    rx.input(
                        placeholder="Distance in km (e.g., 5)",
                        type_="number",
                        min_="0.1",
                        max_="100",
                        step="0.5",
                        value=AppState.buffer_distance_input,
                        on_change=AppState.set_buffer_distance_input,
                        width="100%",
                    ),
                    rx.button(
                        "Create Buffer",
                        on_click=lambda: AppState.handle_create_buffer(
                            AppState.buffer_distance_input
                        ),
                        color_scheme="green",
                        width="auto",
                    ),
                    width="100%",
                    spacing="2",
                ),
                
                rx.divider(),
                spacing="2",
            )
        ),
        
        # Error display
        rx.cond(
            AppState.error_message != "",
            rx.callout(
                rx.text(AppState.error_message),
                icon="alert_circle",
                color_scheme="red",
                width="100%",
            )
        ),
        
        width="100%",
        padding="1rem",
        border="1px solid #e0e0e0",
        border_radius="8px",
        spacing="3",
    )


def geometry_selector() -> rx.Component:
    """
    Dropdown to select from available geometries (territories and uploaded).
    """
    return rx.vstack(
        rx.heading("📍 Select Geometry", size="4"),
        
        # Territory selector
        rx.select(
            AppState.available_territories,
            value=AppState.selected_territory,
            on_change=AppState.set_selected_territory,
            placeholder="Choose a territory...",
        ),
        
        rx.divider(),
        
        width="100%",
        spacing="2",
    )


def geometry_list() -> rx.Component:
    """
    Display list of all available geometries with options.
    """
    return rx.vstack(
        rx.heading("📚 Available Geometries", size="4"),
        
        rx.cond(
            rx.cond(
                AppState.all_drawn_features,
                True,
                False
            ),
            rx.foreach(
                AppState.all_drawn_features,
                lambda feature: rx.hstack(
                    rx.text(
                        feature.get("properties", {}).get("name", "Unknown"),
                        flex="1",
                    ),
                    rx.button(
                        "×",
                        size="sm",
                        color_scheme="red",
                        on_click=lambda: None,  # TODO: Delete handler
                    ),
                    width="100%",
                    padding="0.5rem",
                    border_bottom="1px solid #f0f0f0",
                ),
            ),
            rx.text(
                "No geometries loaded yet",
                color="gray",
                font_size="sm",
            ),
        ),
        
        width="100%",
        spacing="2",
    )
