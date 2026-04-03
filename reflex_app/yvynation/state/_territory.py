"""
Territory selection and filtering event handlers.
Handles map-click selection, EE geometry loading, zoom bounds, and GeoJSON overlay.
"""
import logging
import time
from typing import Optional

import reflex as rx

logger = logging.getLogger(__name__)


class TerritoryMixin(rx.State, mixin=True):
    """Event handlers for territory selection and management."""

    # ---- Initialization -------------------------------------------------

    def initialize_app(self):
        """Show UI immediately then load EE data in the background."""
        if self.ee_initialized:
            return
        self.data_loaded = True
        self.ee_initialized = True
        self._load_territories_background()

    def _load_territories_background(self):
        """Load territory list and indigenous lands tile URL (non-blocking)."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            ee_service = get_ee_service()
            success, territories = ee_service.load_territories()
            if success and territories:
                self.available_territories = list(territories)
            else:
                self.available_territories = [
                    "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                    "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná",
                ]

            try:
                tile_url = ee_service.get_indigenous_lands_tile_url()
                if tile_url:
                    self.indigenous_lands_tile_url = tile_url
                    logger.info("Indigenous lands tile layer cached")
                self.territory_name_property = ee_service.get_name_property()
            except Exception as tile_err:
                logger.warning(f"Could not load indigenous lands tiles: {tile_err}")

            self.geometry_version += 1
            logger.info(f"App initialised with {len(self.available_territories)} territories")

        except Exception as e:
            logger.error(f"Failed to load territory data: {e}")
            self.available_territories = [
                "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná",
            ]

    # ---- Search / filter ------------------------------------------------

    def set_territory_search_query(self, query: str):
        """Update territory search query (reactive filter)."""
        self.territory_search_query = query

    def set_territory_filter(self, state: Optional[str]):
        """Filter territories by administrative state/region."""
        self.territory_filter_state = state

    # ---- Selection ------------------------------------------------------

    def select_territory_from_map(self, territory_name: str):
        """Handle territory selection triggered by a map click (JS bridge)."""
        try:
            current_time = time.time()
            self._selection_call_count += 1
            call_num = self._selection_call_count
            time_since_last = current_time - self._selection_timestamp if self._selection_timestamp else 0
            self._selection_timestamp = current_time

            logger.info(
                f"[MAP_SELECTION #{call_num}] {time_since_last:.3f}s since last: {territory_name}"
            )

            if not territory_name or territory_name == "null" or not isinstance(territory_name, str):
                logger.warning(f"[MAP_SELECTION #{call_num}] Invalid name: {territory_name}")
                return

            territory_name = territory_name.strip()
            if not territory_name:
                return

            if self.selected_territory == territory_name:
                logger.info(f"[MAP_SELECTION #{call_num}] Already selected: {territory_name}")
                return

            matched = None
            if territory_name in self.available_territories:
                matched = territory_name
            else:
                for t in self.available_territories:
                    if territory_name in t or t in territory_name:
                        matched = t
                        break

            if matched:
                self.set_selected_territory(matched)
            else:
                self.error_message = f"Territory '{territory_name}' not found"
                logger.warning(f"[MAP_SELECTION #{call_num}] Not found: {territory_name}")

        except Exception as e:
            logger.error(f"[MAP_SELECTION] Error: {e}", exc_info=True)
            self.error_message = f"Error selecting territory from map: {e}"

    def set_selected_territory(self, territory: str):
        """Select a territory: update state, load EE geometry, cache GeoJSON, zoom."""
        try:
            logger.info(f"[TERRITORY_SET] Starting: {territory}")

            if not territory:
                return

            self.territory_result = None
            self.territory_result_year2 = None
            self.selected_territory = territory
            self.pending_territory = None
            self.territory_name = territory

            try:
                from ..utils.ee_service_extended import get_ee_service

                ee_service = get_ee_service()

                # Handle territory names that embed IDs like "Balaio (5301)"
                territory_for_geometry = territory
                if "(" in territory and ")" in territory:
                    base_name = territory.split("(")[0].strip()
                    if base_name in self.available_territories:
                        territory_for_geometry = base_name
                    else:
                        for available_t in self.available_territories:
                            if base_name in available_t or available_t in base_name:
                                territory_for_geometry = available_t
                                break

                geom = ee_service.get_territory_geometry(territory_for_geometry)

                if not geom and territory_for_geometry != territory:
                    geom = ee_service.get_territory_geometry(territory)

                if not geom:
                    self.error_message = f"Could not load geometry for: {territory}"
                    return

                # Cache GeoJSON for map overlay
                try:
                    raw_geojson = geom.getInfo()
                    clean_geom = {
                        "type": raw_geojson.get("type", "Polygon"),
                        "coordinates": raw_geojson.get("coordinates", []),
                    }
                    territory_feature = {
                        "type": "Feature",
                        "geometry": clean_geom,
                        "properties": {"name": territory, "NAME": territory},
                        "name": territory,
                        "_source": "territory",
                    }
                    self.territory_geojson_features = [territory_feature]
                    self.geometry_version += 1
                    logger.info(
                        f"[TERRITORY_SET] GeoJSON cached: {clean_geom['type']} "
                        f"with {len(clean_geom.get('coordinates', []))} coord groups"
                    )
                except Exception as geojson_err:
                    logger.warning(f"[TERRITORY_SET] GeoJSON conversion failed: {geojson_err}")
                    self.territory_geojson_features = []

                # Compute bounds for auto-zoom
                try:
                    bounds = geom.bounds().getInfo()
                    if bounds and "coordinates" in bounds:
                        coords = bounds["coordinates"][0]
                        if coords:
                            min_lat = min(c[1] for c in coords)
                            max_lat = max(c[1] for c in coords)
                            min_lon = min(c[0] for c in coords)
                            max_lon = max(c[0] for c in coords)
                            self.map_zoom_bounds = {
                                "min_lat": min_lat, "max_lat": max_lat,
                                "min_lon": min_lon, "max_lon": max_lon,
                                "center_lat": (min_lat + max_lat) / 2,
                                "center_lon": (min_lon + max_lon) / 2,
                            }
                            self.territory_geometry_displayed = True
                except Exception as bounds_err:
                    logger.warning(f"[TERRITORY_SET] Bounds calculation failed: {bounds_err}")

            except Exception as e:
                logger.error(f"[TERRITORY_SET] Error loading geometry: {e}", exc_info=True)
                self.error_message = f"Error loading territory: {e}"

            logger.info(f"[TERRITORY_SET] Completed: {territory}")

        except Exception as outer_e:
            logger.error(f"[TERRITORY_SET] Unexpected error: {outer_e}", exc_info=True)
            self.error_message = f"Unexpected error setting territory: {outer_e}"

    def set_pending_territory(self, territory: Optional[str]):
        """Stage a territory pending user confirmation."""
        self.pending_territory = territory

    def confirm_territory(self):
        """Confirm the pending territory selection."""
        if self.pending_territory:
            self.selected_territory = self.pending_territory
            self.pending_territory = None

    def add_territory_geometry(self, territory_name: str):
        """Add a territory as a drawable geometry feature for custom analysis."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            ee_service = get_ee_service()
            territory_geom = ee_service.get_territory_geometry(territory_name)
            if territory_geom is None:
                logger.warning(f"Could not load geometry for: {territory_name}")
                self.error_message = f"Failed to load geometry for {territory_name}"
                return

            territory_feature = {
                "type": "Territory",
                "name": territory_name,
                "territory_name": territory_name,
                "coordinates": [],
                "_ee_geometry": territory_geom,
            }
            self.drawn_features.append(territory_feature)
            self.geometry_version += 1
            logger.info(f"Added territory geometry: {territory_name}")

        except Exception as e:
            logger.error(f"Error adding territory geometry: {e}")
            self.error_message = f"Error loading territory: {e}"
