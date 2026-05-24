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

    # ---- Initialization & Reset -------------------------------------------------

    def clear_all_state(self):
        """Clear all analysis data and geometries, restart fresh."""
        # Clear territories and selections
        self.selected_territory = None
        self.pending_territory = None
        self.territory_name = ""
        self.territory_geojson_features = []

        # Clear drawn features and geometry selections
        self.drawn_features = []
        self.selected_geometry_idx = None
        self.selected_geometry_is_territory = False
        self.show_geometry_popup = False
        self.geometry_popup_info = {}

        # Clear buffer overlays and results
        self.buffer_geojson_features = []
        self.buffer_geometries = {}
        self.current_buffer_for_analysis = None
        self.buffer_mapbiomas_result = None
        self.buffer_hansen_result = None
        self.buffer_compare_result = None
        self.buffer_gfc_result = None

        # Clear territory-level analysis results (back to Optional defaults)
        self.territory_result = None
        self.territory_result_year2 = None
        self.territory_transitions = None

        # Clear general analysis results
        self.analysis_results = {}
        self.mapbiomas_analysis_result = None
        self.hansen_analysis_result = None
        self.mapbiomas_comparison_result = None
        self.hansen_comparison_result = None
        self.all_analysis_results = {}
        self.analysis_figures = {}
        self.active_result_key = ""
        self.result_keys_list = []

        # Clear geometry-level analysis results (back to Optional defaults)
        self.geometry_analysis_results = {}
        self.geometry_glad_result = None
        self.geometry_gfc_result = None
        self.geometry_analysis_pending = False

        # Clear analysis pending flags
        self.mapbiomas_analysis_pending = False
        self.hansen_analysis_pending = False

        # Clear UI state
        self.error_message = ""
        self.loading_message = ""
        self.loading_type = ""

        # Reset geometry tracking
        self.geometry_version += 1
        self.territory_geometry_displayed = False
        self.map_zoom_bounds = {}
        self.analysis_tile_layers = []

        logger.info("Application state cleared and reset")

    def initialize_app(self):
        """Show UI immediately, mark as initializing, then dispatch background load."""
        if self.ee_initialized:
            return
        self.data_loaded = True
        self.ee_initialized = True
        self.loading_message = "Loading territory data…"
        self.loading_type = "ee"
        # Return an EventSpec so the caller can yield/return it to Reflex,
        # which then dispatches the background task without blocking.
        return type(self).load_territories_background()

    @rx.event(background=True)
    async def load_territories_background(self):
        """Load territory list and indigenous lands tile URL without blocking the event loop.

        Uses ``@rx.background`` so all EE network calls happen in a worker thread
        while the frontend stays fully interactive.  State mutations are batched
        inside ``async with self`` blocks to minimise the number of map rebuilds.
        """
        import asyncio

        try:
            from ..utils.ee_service_extended import get_ee_service

            # ------------------------------------------------------------------
            # Phase 1 – territory list (one EE round-trip)
            # ------------------------------------------------------------------
            ee_service = get_ee_service()
            try:
                success, territories = await asyncio.get_event_loop().run_in_executor(
                    None, ee_service.load_territories
                )
            except Exception:
                success, territories = False, []

            fallback = [
                "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná",
            ]
            territory_list = list(territories) if (success and territories) else fallback

            async with self:
                self.available_territories = territory_list
                logger.info(f"[INIT] Territory list ready: {len(territory_list)} entries")

            # ------------------------------------------------------------------
            # Phase 2 – indigenous lands tile URL (second EE round-trip)
            # ------------------------------------------------------------------
            tile_url = ""
            name_property = "name"
            try:
                tile_url = await asyncio.get_event_loop().run_in_executor(
                    None, ee_service.get_indigenous_lands_tile_url
                )
                name_property = await asyncio.get_event_loop().run_in_executor(
                    None, ee_service.get_name_property
                )
            except Exception as tile_err:
                logger.warning(f"[INIT] Could not load indigenous lands tiles: {tile_err}")

            # ------------------------------------------------------------------
            # Phase 3 – commit tile URL + bump geometry_version exactly once
            # ------------------------------------------------------------------
            async with self:
                if tile_url:
                    self.indigenous_lands_tile_url = tile_url
                    logger.info("[INIT] Indigenous lands tile layer cached")
                self.territory_name_property = name_property
                self.geometry_version += 1
                self.loading_message = ""
                self.loading_type = ""
                logger.info(f"[INIT] App initialised with {len(self.available_territories)} territories")

        except Exception as e:
            logger.error(f"[INIT] Failed to load territory data: {e}", exc_info=True)
            async with self:
                self.available_territories = [
                    "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                    "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná",
                ]
                self.loading_message = ""
                self.loading_type = ""

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
                return self.set_selected_territory(matched)
            else:
                self.error_message = f"Territory '{territory_name}' not found"
                logger.warning(f"[MAP_SELECTION #{call_num}] Not found: {territory_name}")

        except Exception as e:
            logger.error(f"[MAP_SELECTION] Error: {e}", exc_info=True)
            self.error_message = f"Error selecting territory from map: {e}"

    def set_selected_territory(self, territory: str):
        """Select a territory: clear stale state immediately, then dispatch async geometry load.

        All blocking Earth Engine calls (getInfo, bounds, buffer GeoJSON) are
        moved to ``load_territory_geometry_bg`` so the event loop is never
        stalled and the sidebar stays fully interactive during the load.
        """
        if not territory:
            return

        logger.info(f"[TERRITORY_SET] Dispatching background load for: {territory}")

        # Clear stale results instantly so the UI reflects the new selection
        self.territory_result = None
        self.territory_result_year2 = None
        self.selected_territory = territory
        self.pending_territory = None
        self.territory_name = territory
        self.territory_geojson_features = []
        self.map_zoom_bounds = {}
        self.territory_geometry_displayed = False
        self.buffer_geojson_features = []
        self.buffer_geometries = {}
        self.current_buffer_for_analysis = None
        self.error_message = ""
        self.loading_message = f"Loading {territory}…"
        self.loading_type = "territory"

        # Dispatch background task — all blocking EE calls happen there
        return type(self).load_territory_geometry_bg()

    @rx.event(background=True)
    async def load_territory_geometry_bg(self):
        """Load territory GeoJSON, bounds, and auto-buffer without blocking the event loop.

        All ``.getInfo()`` / EE network calls run in a thread pool via
        ``run_in_executor``.  State is mutated only inside ``async with self``
        blocks so Reflex batches the updates correctly.
        """
        import asyncio
        import datetime

        # --- Read the vars we need under lock (snapshot) ---------------------
        async with self:
            territory = self.selected_territory
            buffer_km = float(self.auto_buffer_km)
            buffer_enabled = bool(self.auto_buffer_enabled)

        if not territory:
            return

        # ------------------------------------------------------------------
        # Phase 1 – load territory geometry (contains size().getInfo() call)
        # ------------------------------------------------------------------
        def _load_geom():
            from ..utils.ee_service_extended import get_ee_service
            ee_service = get_ee_service()
            geom = ee_service.get_territory_geometry(territory)
            if not geom and "(" in territory and ")" in territory:
                base_name = territory.split("(")[0].strip()
                geom = ee_service.get_territory_geometry(base_name)
            return geom

        try:
            geom = await asyncio.get_event_loop().run_in_executor(None, _load_geom)
        except Exception as load_err:
            logger.error(f"[TERRITORY_BG] Geometry load error: {load_err}", exc_info=True)
            async with self:
                self.error_message = f"Error loading territory: {load_err}"
                self.loading_message = ""
                self.loading_type = ""
            return

        if not geom:
            async with self:
                self.error_message = f"Could not load geometry for: {territory}"
                self.loading_message = ""
                self.loading_type = ""
            return

        # ------------------------------------------------------------------
        # Phase 2 – GeoJSON + bounds (two blocking getInfo() calls)
        # ------------------------------------------------------------------
        def _fetch_geojson_and_bounds():
            raw_geojson = geom.getInfo()
            bounds_info = geom.bounds().getInfo()
            return raw_geojson, bounds_info

        try:
            raw_geojson, bounds_info = await asyncio.get_event_loop().run_in_executor(
                None, _fetch_geojson_and_bounds
            )
        except Exception as fetch_err:
            logger.warning(f"[TERRITORY_BG] getInfo failed: {fetch_err}")
            raw_geojson, bounds_info = None, None

        # Build territory GeoJSON feature
        territory_geojson_features = []
        if raw_geojson:
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
            territory_geojson_features = [territory_feature]
            logger.info(
                f"[TERRITORY_BG] GeoJSON ready: {clean_geom['type']} "
                f"with {len(clean_geom.get('coordinates', []))} coord groups"
            )

        # Build zoom-bounds dict
        map_zoom_bounds = {}
        if bounds_info and "coordinates" in bounds_info:
            coords = bounds_info["coordinates"][0]
            if coords:
                min_lat = min(c[1] for c in coords)
                max_lat = max(c[1] for c in coords)
                min_lon = min(c[0] for c in coords)
                max_lon = max(c[0] for c in coords)
                map_zoom_bounds = {
                    "min_lat": min_lat, "max_lat": max_lat,
                    "min_lon": min_lon, "max_lon": max_lon,
                    "center_lat": (min_lat + max_lat) / 2,
                    "center_lon": (min_lon + max_lon) / 2,
                }

        # Commit territory geometry data
        async with self:
            self.territory_geojson_features = territory_geojson_features
            self.map_zoom_bounds = map_zoom_bounds
            self.territory_geometry_displayed = bool(map_zoom_bounds)
            self.geometry_version += 1
            if not territory_geojson_features:
                self.error_message = f"Could not load geometry for: {territory}"

        # ------------------------------------------------------------------
        # Phase 3 – Auto-buffer (optional, non-fatal)
        # ------------------------------------------------------------------
        if buffer_enabled and territory_geojson_features:
            try:
                from ..utils.buffer_utils import (
                    create_external_buffer,
                    create_buffer_geometry_dict,
                    convert_geojson_to_ee_geometry,
                )

                # Build EE geometry from cached GeoJSON — no extra network call
                ee_geom = convert_geojson_to_ee_geometry(territory_geojson_features[0])
                if ee_geom:
                    # create_external_buffer is pure EE construction (no network)
                    buffer_geom = create_external_buffer(ee_geom, buffer_km)
                    if buffer_geom:
                        buffer_name = f"Buffer {buffer_km}km - {territory}"
                        buffer_dict = create_buffer_geometry_dict(
                            name=buffer_name,
                            ee_geometry=buffer_geom,
                            buffer_size_km=buffer_km,
                            source_name=territory,
                            created_at=datetime.datetime.now().isoformat(),
                        )

                        # getInfo() for buffer GeoJSON map overlay (blocking)
                        def _get_buffer_geojson():
                            return buffer_geom.getInfo()

                        buffer_geojson_feat = None
                        try:
                            buffer_info = await asyncio.get_event_loop().run_in_executor(
                                None, _get_buffer_geojson
                            )
                            buffer_geojson_feat = {
                                "type": "Feature",
                                "geometry": buffer_info,
                                "properties": {
                                    "name": buffer_name,
                                    "source": territory,
                                    "buffer_km": buffer_km,
                                },
                                "name": buffer_name,
                                "_source": "buffer",
                            }
                        except Exception as bgi_err:
                            logger.warning(f"[TERRITORY_BG] Buffer GeoJSON failed: {bgi_err}")

                        async with self:
                            self.add_buffer_geometry(buffer_name, buffer_dict)
                            self.current_buffer_for_analysis = buffer_name
                            if buffer_geojson_feat:
                                self.buffer_geojson_features = [buffer_geojson_feat]
                                self.geometry_version += 1
                            self.error_message = f"✅ Buffer ({buffer_km} km) created around {territory}"
                            logger.info(f"[TERRITORY_BG] Auto-buffer ready: {buffer_name}")

            except Exception as buf_err:
                logger.warning(f"[TERRITORY_BG] Auto-buffer failed (non-fatal): {buf_err}")

        # ------------------------------------------------------------------
        # Done
        # ------------------------------------------------------------------
        async with self:
            self.loading_message = ""
            self.loading_type = ""
            logger.info(f"[TERRITORY_BG] Completed for {territory}")

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
                    # For MultiPolygon, validate each ring has at least 3 points
                    if geom_type == "MultiPolygon":
                        # Filter out invalid rings (< 3 points)
                        valid_polygons = []
                        for polygon in coords:
                            valid_rings = []
                            for ring in polygon:
                                if len(ring) >= 3:
                                    valid_rings.append(ring)
                            if valid_rings:
                                valid_polygons.append(valid_rings)
                        if valid_polygons:
                            return ee.Geometry.MultiPolygon(valid_polygons)
                        else:
                            logger.warning("[TERRITORY_GEOM] All rings filtered out, falling back to EE service")
                    elif geom_type == "Polygon":
                        # Validate polygon rings
                        valid_rings = []
                        for ring in coords:
                            if len(ring) >= 3:
                                valid_rings.append(ring)
                        if valid_rings:
                            return ee.Geometry.Polygon(valid_rings)
                        else:
                            logger.warning("[TERRITORY_GEOM] Polygon has no valid rings, falling back to EE service")
                    elif geom_type == "Point":
                        return ee.Geometry.Point(coords)
                    elif geom_type == "LineString":
                        if len(coords) >= 2:
                            return ee.Geometry.LineString(coords)
                except Exception as e:
                    logger.warning(f"[TERRITORY_GEOM] Failed to reconstruct from cache: {e}")

        # Slow path: re-fetch from EE service (more reliable)
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
