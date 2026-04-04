"""
Territory selection and filtering event handlers.
Handles map-click selection, EE geometry loading, zoom bounds, and GeoJSON overlay.
"""
import logging
import time
from typing import Any, Optional

import reflex as rx

logger = logging.getLogger(__name__)


class TerritoryMixin(rx.State, mixin=True):
    """Event handlers for territory selection and management."""

    # ---- Initialization -------------------------------------------------

    def initialize_app(self):
        """Show UI immediately then load EE data in the background."""
        if self.ee_initialized:
            return
        # Clear any stale state from previous sessions
        self.drawn_features = []
        self.selected_territory = None
        self.pending_territory = None
        self.territory_geojson_features = []
        self.territory_result = None
        self.territory_result_year2 = None
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

            # DEBUG: Log all territories and their properties
            try:
                all_terrs = ee_service.debug_all_territories()
                logger.info(f"=== DEBUG: All EE Territories ({len(all_terrs)} total) ===")
                for i, terr in enumerate(all_terrs):
                    logger.info(f"Territory {i}: {terr['all_properties']}")
                logger.info(f"=== Loaded as available_territories ===")
                for t in self.available_territories:
                    logger.info(f"  - {t}")
            except Exception as debug_err:
                logger.warning(f"Could not debug territories: {debug_err}")

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

                # Try exact match first (preserves IDs like "Balaio (5301)" vs "Balaio (5302)")
                geom = ee_service.get_territory_geometry(territory)

                # Fallback: try base name if exact match fails and territory has an ID
                if not geom and "(" in territory and ")" in territory:
                    base_name = territory.split("(")[0].strip()
                    geom = ee_service.get_territory_geometry(base_name)

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

    # ---- EE geometry helper (mirrors get_selected_geometry_ee) ----------

    def get_territory_ee_geom(self) -> Optional[Any]:
        """Return an EE geometry for the selected territory.

        Reconstructs from the cached GeoJSON in ``territory_geojson_features``
        first (fast, no extra EE round-trip), then falls back to re-fetching
        from the EE service if the cache is empty.
        """
        import ee

        # Fast path: reconstruct from cached GeoJSON
        if self.territory_geojson_features:
            feat = self.territory_geojson_features[0]
            geom = feat.get("geometry") or {}
            geom_type = geom.get("type", "")
            coords = geom.get("coordinates")
            if coords:
                try:
                    if geom_type == "Polygon":
                        return ee.Geometry.Polygon(coords)
                    elif geom_type == "MultiPolygon":
                        return ee.Geometry.MultiPolygon(coords)
                    elif geom_type == "Point":
                        return ee.Geometry.Point(coords)
                    elif geom_type == "LineString":
                        return ee.Geometry.LineString(coords)
                except Exception as e:
                    logger.warning(f"[TERRITORY_GEOM] Failed to reconstruct from cache: {e}")

        # Slow path: re-fetch from EE service
        if not self.selected_territory:
            return None
        try:
            from ..utils.ee_service_extended import get_ee_service
            ee_service = get_ee_service()
            geom = ee_service.get_territory_geometry(self.selected_territory)
            if geom:
                logger.info(f"[TERRITORY_GEOM] Re-fetched from EE service: {self.selected_territory}")
            return geom
        except Exception as e:
            logger.error(f"[TERRITORY_GEOM] EE service fallback failed: {e}")
            return None
