"""
Territory selection and filtering event handlers.
Handles map-click selection, EE geometry loading, zoom bounds, and GeoJSON overlay.
"""
import logging
import time
from typing import Any, Optional

import reflex as rx

logger = logging.getLogger(__name__)


def _get_service(territory_type: str):
    """Return the GeoPackage service backing *territory_type*.

    Both services share the same public API (display keys, GeoJSON, bounds,
    EE geometry, info), so callers can use the result interchangeably.
    """
    if territory_type == "conservation":
        from ..utils.conservation_service import get_conservation_unit_service
        return get_conservation_unit_service()
    from ..utils.territory_service import get_territory_service
    return get_territory_service()


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
        self.buffer_mapbiomas_comparison_result = None
        self.buffer_gfc_result = None
        self.buffer_territory_transitions = None

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
        """Load territory list from the local GeoPackage (no EE round-trips).

        The GeoPackage singleton is loaded once on first access; subsequent calls
        return instantly.  State mutations are batched inside ``async with self``
        so the frontend stays fully interactive during the (fast) file read.
        """
        import asyncio

        async with self:
            ttype = self.territory_type

        try:
            # ------------------------------------------------------------------
            # Load territory display-keys from local GeoPackage — instant after
            # the first call (singleton loads the file ~20 MB once).
            # ------------------------------------------------------------------
            def _load_local():
                return _get_service(ttype).get_all_display_keys()

            try:
                territory_list = await asyncio.get_event_loop().run_in_executor(
                    None, _load_local
                )
            except Exception as load_err:
                logger.warning(f"[INIT] GeoPackage load failed: {load_err}")
                territory_list = []

            if not territory_list:
                logger.warning("[INIT] Empty territory list from GeoPackage")

            # ------------------------------------------------------------------
            # Initialise Earth Engine up-front so subsequent ``ee.Geometry(...)``
            # calls (auto-buffer, territory analysis, batch) don't blow up with
            # "client library not initialized". Idempotent — the helper short-
            # circuits when EE is already up. Non-fatal: if init fails we just
            # log it; users can still see the territory list and EE failures
            # will surface with a more specific message later.
            # ------------------------------------------------------------------
            def _ee_init():
                from ..utils.ee_service import initialize_earth_engine
                return initialize_earth_engine()

            try:
                await asyncio.get_event_loop().run_in_executor(None, _ee_init)
                logger.info("[INIT] Earth Engine initialised at startup")
            except Exception as ee_err:
                logger.warning(
                    f"[INIT] Earth Engine init failed at startup (will retry on "
                    f"first analysis): {ee_err}"
                )

            # ------------------------------------------------------------------
            # Commit: update territory list + bump geometry_version so the map
            # rebuilds its interactive indigenous-lands layer from local GeoJSON.
            # ``indigenous_lands_tile_url`` is intentionally left empty — the
            # map_builder now pulls GeoJSON directly from territory_service.
            # ------------------------------------------------------------------
            async with self:
                self.available_territories = territory_list
                self.territory_name_property = "display_key"
                self.geometry_version += 1
                self.loading_message = ""
                self.loading_type = ""
                logger.info(
                    f"[INIT] App initialised with {len(territory_list)} territories "
                    f"from local GeoPackage"
                )

        except Exception as e:
            logger.error(f"[INIT] Failed to load territory data: {e}", exc_info=True)
            async with self:
                self.loading_message = ""
                self.loading_type = ""

    # ---- Search / filter ------------------------------------------------

    def set_territory_search_query(self, query: str):
        """Update territory search query (reactive filter)."""
        self.territory_search_query = query

    def set_territory_filter(self, state: Optional[str]):
        """Filter territories by administrative state/region."""
        self.territory_filter_state = state

    def set_territory_type(self, territory_type: str):
        """Switch the selector between indigenous lands and conservation units.

        Clears the current selection (display keys from the other dataset are
        meaningless) and reloads ``available_territories`` from the matching
        GeoPackage service; the map overlay follows via ``territory_type`` in
        the ``map_html`` deps.
        """
        if territory_type not in ("indigenous", "conservation"):
            return
        if territory_type == self.territory_type:
            return

        self.territory_type = territory_type
        self.selected_territory = None
        self.pending_territory = None
        self.territory_name = ""
        self.territory_search_query = ""
        self.territory_geojson_features = []
        self.map_zoom_bounds = {}
        self.territory_geometry_displayed = False
        self.buffer_geojson_features = []
        self.current_buffer_for_analysis = None
        self.available_territories = []
        self.geometry_version += 1
        self.error_message = ""
        self.loading_message = (
            "Loading conservation units…"
            if territory_type == "conservation"
            else "Loading indigenous lands…"
        )
        self.loading_type = "territory"
        return type(self).load_territories_background()

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
            ttype = self.territory_type
            buffer_km = float(self.auto_buffer_km)
            buffer_enabled = bool(self.auto_buffer_enabled)

        if not territory:
            return

        # ------------------------------------------------------------------
        # Phase 1+2 – GeoJSON + bounds from local GeoPackage (no EE calls)
        # ------------------------------------------------------------------
        def _load_local_geom_data():
            svc = _get_service(ttype)
            geojson = svc.get_geojson_for_key(territory)
            bounds = svc.get_bounds_for_key(territory)
            return geojson, bounds

        try:
            raw_geojson, map_zoom_bounds_local = await asyncio.get_event_loop().run_in_executor(
                None, _load_local_geom_data
            )
        except Exception as load_err:
            logger.error(f"[TERRITORY_BG] Local geometry load error: {load_err}", exc_info=True)
            async with self:
                self.error_message = f"Error loading territory: {load_err}"
                self.loading_message = ""
                self.loading_type = ""
            return

        if not raw_geojson:
            async with self:
                self.error_message = f"Could not load geometry for: {territory}"
                self.loading_message = ""
                self.loading_type = ""
            return

        # Build territory GeoJSON feature from local data
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
                f"[TERRITORY_BG] GeoJSON ready from local GeoPackage: {clean_geom['type']} "
                f"with {len(clean_geom.get('coordinates', []))} coord groups"
            )

        # Build zoom-bounds dict from local bounds
        map_zoom_bounds = map_zoom_bounds_local or {}

        # Commit territory geometry data
        async with self:
            self.territory_geojson_features = territory_geojson_features
            self.map_zoom_bounds = map_zoom_bounds
            self.territory_geometry_displayed = bool(map_zoom_bounds)
            # Register this territory as an area (keeps history of every
            # selected territory) and make it the active analysis subject.
            if territory_geojson_features:
                self._register_target("territory", territory, territory_geojson_features[0])
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
                        buffer_name = f"{territory} - Buffer {buffer_km:g}km"
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
                                # Cache by source so switching back to this
                                # territory reuses the buffer (no recompute), and
                                # persist it onto the registry entry.
                                self.buffer_overlays_by_source = {
                                    **self.buffer_overlays_by_source,
                                    territory: buffer_geojson_feat,
                                }
                                self._save_buffer_to_active_entry(buffer_geojson_feat)
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
            if self.territory_type == "conservation":
                territory_geom = _get_service("conservation").get_ee_geometry(territory_name)
            else:
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

        # Slow path: re-fetch from the backing GeoPackage service
        if not self.selected_territory:
            return None
        try:
            if self.territory_type == "conservation":
                geom = _get_service("conservation").get_ee_geometry(self.selected_territory)
            else:
                from ..utils.ee_service_extended import get_ee_service
                ee_service = get_ee_service()
                geom = ee_service.get_territory_geometry(self.selected_territory)
            if geom:
                logger.info(f"[TERRITORY_GEOM] Re-fetched from service: {self.selected_territory}")
            return geom
        except Exception as e:
            logger.error(f"[TERRITORY_GEOM] Service fallback failed: {e}")
            return None
