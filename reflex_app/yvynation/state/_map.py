"""
Map layer event handlers: MapBiomas/Hansen layer management, GFC toggles,
change mask, map center, indigenous lands overlay.
"""
import logging
from typing import Optional

import reflex as rx

logger = logging.getLogger(__name__)


class MapMixin(rx.State, mixin=True):
    """Event handlers for map display and layer management."""

    # ---- Map center / zoom ----------------------------------------------

    def set_map_center(self, lat: float, lng: float, zoom: int = None):
        """Update map center and optional zoom level."""
        self.map_center = (lat, lng)
        if zoom is not None:
            self.map_zoom = zoom

    def refresh_map(self):
        """Force a map refresh by bumping geometry_version."""
        self.geometry_version += 1
        logger.info("Map refresh triggered")

    # ---- Base layer -----------------------------------------------------

    def set_selected_base_layer(self, layer: str):
        """Change the base tile layer."""
        self.selected_base_layer = layer

    # ---- MapBiomas layers -----------------------------------------------

    def set_mapbiomas_year(self, year):
        """Change the active MapBiomas year (accepts int or str)."""
        try:
            self.mapbiomas_current_year = int(year)
        except (ValueError, TypeError):
            self.mapbiomas_current_year = 0

    def toggle_mapbiomas_year(self, year: int):
        """Toggle the enabled state for a specific MapBiomas year."""
        self.mapbiomas_years_enabled[year] = not self.mapbiomas_years_enabled.get(year, False)

    def add_mapbiomas_layer(self, year: Optional[int] = None):
        """Add a MapBiomas year to the map display."""
        if year is None:
            year = self.mapbiomas_current_year
        if year not in self.mapbiomas_displayed_years:
            self.mapbiomas_displayed_years.append(year)
            self.mapbiomas_displayed_years.sort()
            logger.info(f"Added MapBiomas {year} to display")

    def remove_mapbiomas_layer(self, year: int):
        """Remove a MapBiomas year from the map display."""
        if year in self.mapbiomas_displayed_years:
            self.mapbiomas_displayed_years.remove(year)
            logger.info(f"Removed MapBiomas {year} from display")

    # ---- Hansen layers --------------------------------------------------

    def set_hansen_year(self, year: str):
        """Change the active Hansen year."""
        self.hansen_current_year = year

    def toggle_hansen_year(self, year: str):
        """Toggle the enabled state for a specific Hansen year."""
        self.hansen_years_enabled[year] = not self.hansen_years_enabled.get(year, False)

    def add_hansen_layer(self, layer_type: str = "loss"):
        """Add a Hansen layer type to the map display."""
        if layer_type not in self.hansen_displayed_layers:
            self.hansen_displayed_layers.append(layer_type)
            logger.info(f"Added Hansen {layer_type} to display")

    def add_hansen_selected_year(self):
        """Add the currently selected Hansen year to the map display."""
        self.add_hansen_layer(self.hansen_current_year)

    def remove_hansen_layer(self, layer_type: str):
        """Remove a Hansen layer type from the map display."""
        if layer_type in self.hansen_displayed_layers:
            self.hansen_displayed_layers.remove(layer_type)
            logger.info(f"Removed Hansen {layer_type} from display")

    def clear_all_layers(self):
        """Clear all MapBiomas and Hansen layers from the map."""
        self.mapbiomas_displayed_years = []
        self.hansen_displayed_layers = []
        logger.info("All layers cleared")

    # ---- GFC (Global Forest Change) layers ------------------------------

    def toggle_gfc_layer(self, layer_type: str):
        """Toggle a GFC layer (tree_cover / tree_loss / tree_gain) and rebuild map."""
        if layer_type == "tree_cover":
            self.show_hansen_gfc_tree_cover = not self.show_hansen_gfc_tree_cover
        elif layer_type == "tree_loss":
            self.show_hansen_gfc_tree_loss = not self.show_hansen_gfc_tree_loss
        elif layer_type == "tree_gain":
            self.show_hansen_gfc_tree_gain = not self.show_hansen_gfc_tree_gain
        self.geometry_version += 1

    # ---- Indigenous lands -----------------------------------------------

    def toggle_indigenous_lands(self):
        """Toggle the indigenous lands base layer."""
        self.show_indigenous_lands = not self.show_indigenous_lands
        self.geometry_version += 1

    # ---- Geometry overlay -----------------------------------------------

    def toggle_geometries_on_map(self):
        """Toggle visibility of drawn geometry overlays."""
        self.show_geometries_on_map = not self.show_geometries_on_map
        self.geometry_version += 1

    # ---- Change mask ----------------------------------------------------

    def toggle_change_mask(self):
        """Toggle the MapBiomas change mask layer."""
        self.show_change_mask = not self.show_change_mask
        self.geometry_version += 1

    def set_change_mask_year1(self, year: str):
        """Set the start year for the change mask."""
        self.change_mask_year1 = int(year)
        if self.show_change_mask:
            self.geometry_version += 1

    def set_change_mask_year2(self, year: str):
        """Set the end year for the change mask."""
        self.change_mask_year2 = int(year)
        if self.show_change_mask:
            self.geometry_version += 1
