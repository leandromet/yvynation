"""
Geometry Selector Component
Allows users to select and manage drawn geometries for analysis.
Similar to the Streamlit render_polygon_selector() function.
"""

import reflex as rx
from ..state import AppState


def geometry_selector() -> rx.Component:
    """
    Display selector for drawn geometries.
    Allows user to choose which geometry to analyze.
    Uses _idx field stored in each feature for tracking.
    """
    return rx.cond(
        AppState.drawn_features.length() > 0,
        rx.vstack(
            rx.divider(),
            rx.heading("📍 Your Geometries", size="4"),
            
            # Geometry list
            rx.vstack(
                rx.foreach(
                    AppState.drawn_features,
                    lambda feature: rx.cond(
                        AppState.selected_geometry_idx == feature.get("_idx"),
                        # Selected geometry - highlight it
                        rx.box(
                            rx.hstack(
                                rx.badge(
                                    f"#{feature.get('_display_idx')}",
                                    color_scheme="green",
                                    variant="solid",
                                ),
                                rx.vstack(
                                    rx.text(
                                        feature.get("name", "Geometry"),
                                        font_weight="bold",
                                    ),
                                    rx.text(
                                        f"Type: {feature.get('type', 'Unknown')}",
                                        font_size="xs",
                                        color="gray",
                                    ),
                                    spacing="1",
                                ),
                                rx.spacer(),
                                rx.button(
                                    "✕",
                                    on_click=lambda f=feature: AppState.remove_geometry(f.get("_idx")),
                                    size="1",
                                    color_scheme="red",
                                    variant="ghost",
                                ),
                                width="100%",
                                spacing="2",
                                padding="0.75rem",
                            ),
                            bg="green.50",
                            border="2px solid #48bb78",
                            border_radius="md",
                            width="100%",
                        ),
                        # Unselected geometry - clickable
                        rx.box(
                            rx.hstack(
                                rx.badge(
                                    f"#{feature.get('_display_idx')}",
                                    color_scheme="gray",
                                ),
                                rx.vstack(
                                    rx.text(
                                        feature.get("name", "Geometry"),
                                    ),
                                    rx.text(
                                        f"Type: {feature.get('type', 'Unknown')}",
                                        font_size="xs",
                                        color="gray",
                                    ),
                                    spacing="1",
                                ),
                                rx.spacer(),
                                rx.button(
                                    "✕",
                                    on_click=lambda f=feature: AppState.remove_geometry(f.get("_idx")),
                                    size="1",
                                    color_scheme="red",
                                    variant="ghost",
                                ),
                                width="100%",
                                spacing="2",
                                padding="0.75rem",
                            ),
                            bg="white",
                            border="1px solid #e0e0e0",
                            border_radius="md",
                            width="100%",
                            cursor="pointer",
                            on_click=lambda f=feature: AppState.set_selected_geometry(f.get("_idx")),
                            _hover={"bg": "gray.50"},
                        ),
                    ),
                ),
                spacing="2",
                width="100%",
            ),
            
            # Selected geometry info
            rx.cond(
                AppState.selected_geometry_idx is not None,
                rx.box(
                    rx.vstack(
                        rx.heading("Selected for Analysis", size="2"),
                        rx.button(
                            "📊 Analyze Against Active Layers",
                            width="100%",
                            color_scheme="blue",
                            size="1",
                        ),
                        spacing="2",
                    ),
                    bg="blue.50",
                    padding="1rem",
                    border_radius="md",
                    width="100%",
                    border="1px solid #3b82f6",
                ),
                rx.box(),
            ),
            
            spacing="3",
            width="100%",
        ),
        # No geometries yet
        rx.box(
            rx.vstack(
                rx.text(
                    "📍 No geometries drawn yet.",
                    color="gray",
                    font_size="sm",
                ),
                rx.text(
                    "Draw polygons or rectangles on the map using the drawing tools.",
                    color="gray",
                    font_size="xs",
                ),
                spacing="1",
            ),
            padding="1rem",
            bg="gray.50",
            border_radius="md",
            width="100%",
        ),
    )


def drawing_instructions() -> rx.Component:
    """Show instructions for drawing geometries."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="info", color="blue.500"),
                rx.text("How to draw:", font_weight="bold", font_size="sm"),
                spacing="2",
            ),
            rx.ordered_list(
                rx.list_item("Look for the draw tool icons in the map toolbar"),
                rx.list_item("Click polygon or rectangle tool"),
                rx.list_item("Click on the map to add points/corners"),
                rx.list_item("Complete your shape by finishing the drawing"),
                rx.list_item("Use 'Save Drawing' button below the map"),
                font_size="xs",
            ),
            spacing="2",
            width="100%",
        ),
        padding="1rem",
        bg="blue.50",
        border_radius="md",
        border="1px solid #3b82f6",
        width="100%",
    )
