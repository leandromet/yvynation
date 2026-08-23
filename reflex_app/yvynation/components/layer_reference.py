"""
Layer Reference Guide component for Yvynation Reflex app.
Displays legend/color information for all data layers.
"""

import reflex as rx
from ..state import AppState


def _color_swatch(color: str, label: str) -> rx.Component:
    """A small color swatch with label."""
    return rx.hstack(
        rx.box(
            width="14px",
            height="14px",
            bg=color,
            border_radius="2px",
            border="1px solid #ccc",
            flex_shrink="0",
        ),
        rx.text(label, font_size="xs"),
        spacing="2",
        align_items="center",
    )


def _legend_section(title: str, items: list, icon_name: str = "layers", color: str = "green") -> rx.Component:
    """A collapsible legend section with colored swatches."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(icon_name, size=14, color=color),
                rx.text(title, font_weight="600", font_size="sm"),
                spacing="2",
                align_items="center",
            ),
            rx.flex(
                *[_color_swatch(c, l) for c, l in items],
                flex_wrap="wrap",
                gap="2",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        padding="0.5rem 0",
        width="100%",
    )


def layer_reference_guide() -> rx.Component:
    """Complete layer reference guide with all dataset legends."""
    return rx.box(
        # Main collapsible header
        rx.button(
            rx.hstack(
                rx.icon("book-marked", size=16, color="teal"),
                rx.text(
                    AppState.tr["layer_reference"],
                    font_weight="600",
                    font_size="md",
                ),
                rx.spacer(),
                rx.text(
                    rx.cond(AppState.show_layer_reference, "v", ">"),
                    font_size="xs",
                    color="gray",
                    font_family="monospace",
                ),
                width="100%",
                align_items="center",
                spacing="2",
            ),
            on_click=AppState.toggle_layer_reference,
            width="100%",
            variant="ghost",
            padding="0.75rem 1rem",
        ),
        rx.cond(
            AppState.show_layer_reference,
            rx.box(
                rx.vstack(
                    # Indigenous Territories
                    _legend_section(
                        AppState.tr["indigenous_territories_label"],
                        [
                            ("#4B0082", "Regularizada (Regularized)"),
                            ("#FF0000", "Homologada (Approved)"),
                            ("#0033FF", "Declarada (Declared)"),
                            ("#00BFFF", "Em estudo (Under Study)"),
                        ],
                        icon_name="map-pin",
                        color="indigo",
                    ),
                    rx.divider(),

                    # MapBiomas Land Cover Classes
                    _legend_section(
                        AppState.tr["mapbiomas_legend"],
                        [
                            ("#1f8d49", "Forest"),
                            ("#7dc975", "Savanna"),
                            ("#04381d", "Mangrove"),
                            ("#519799", "Wetland"),
                            ("#d6bc74", "Grassland"),
                            ("#edde8e", "Pasture"),
                            ("#e974ed", "Agriculture"),
                            ("#db7093", "Sugarcane"),
                            ("#d4271e", "Urban"),
                            ("#2532e4", "Water"),
                        ],
                        icon_name="leaf",
                        color="green",
                    ),
                    rx.divider(),

                    # Hansen Consolidated
                    _legend_section(
                        AppState.tr["hansen_legend"],
                        [
                            ("#1F8040", "Dense Forest Cover"),
                            ("#90C090", "Open Forest Cover"),
                            ("#B8D4A8", "Dense Vegetation"),
                            ("#D4D4A8", "Unvegetated"),
                            ("#4CAF50", "Forest Gain"),
                            ("#E53935", "Forest Loss"),
                            ("#FFD700", "Cropland"),
                            ("#FF6B35", "Built-up"),
                            ("#2196F3", "Water"),
                        ],
                        icon_name="trees",
                        color="blue",
                    ),
                    rx.divider(),

                    # Hansen GFC
                    _legend_section(
                        AppState.tr["gfc_legend"],
                        [
                            ("#228B22", "Tree Cover 2000 (0-100%)"),
                            ("#FF4500", "Tree Loss Year (2001-2024)"),
                            ("#32CD32", "Tree Gain (2000-2012)"),
                        ],
                        icon_name="tree-pine",
                        color="darkgreen",
                    ),
                    rx.divider(),

                    # AAFC (Canada)
                    _legend_section(
                        AppState.tr["aafc_legend"],
                        [
                            ("#cc6600", "Agriculture"),
                            ("#ff9933", "Cropland"),
                            ("#ffcc33", "Pasture/Forage"),
                            ("#660000", "Cereals"),
                            ("#a7b34d", "Wheat"),
                            ("#d6ff70", "Canola"),
                            ("#ffff99", "Corn"),
                            ("#cc9933", "Soybeans"),
                            ("#cccc00", "Grassland"),
                            ("#009900", "Forest"),
                            ("#3333ff", "Water"),
                            ("#cc6699", "Urban/Developed"),
                        ],
                        icon_name="wheat",
                        color="orange",
                    ),
                    rx.divider(),

                    # Map overlays legend
                    rx.vstack(
                        rx.hstack(
                            rx.icon("map", size=14, color="gray"),
                            rx.text("Map Overlays", font_weight="600", font_size="sm"),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.flex(
                            _color_swatch("#FF6600", AppState.tr["selected_territory_label"]),
                            _color_swatch("#3388ff", AppState.tr["drawn_polygon_label"]),
                            _color_swatch("#87CEEB", AppState.tr["buffer_zone_label"]),
                            flex_wrap="wrap",
                            gap="2",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    rx.divider(),

                    # Controls info
                    rx.vstack(
                        rx.hstack(
                            rx.icon("settings", size=14, color="gray"),
                            rx.text("Controls", font_weight="600", font_size="sm"),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.text("Layer Control: top-right corner of the map", font_size="xs", color="gray"),
                        rx.text("Drawing Tools: top-left corner of the map", font_size="xs", color="gray"),
                        rx.text("Opacity: Adjust in sidebar layer settings", font_size="xs", color="gray"),
                        spacing="1",
                        width="100%",
                    ),

                    spacing="2",
                    width="100%",
                    padding="0.5rem 1rem",
                ),
            ),
            rx.box(),
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
        margin_top="0.5rem",
    )
