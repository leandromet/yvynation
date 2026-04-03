"""
Analysis execution and multi-result management event handlers.
Covers territory/geometry MapBiomas & Hansen analysis, comparison, and
the result-store (switch / remove result).
"""
import logging
from typing import Any, Dict, Optional

import reflex as rx

logger = logging.getLogger(__name__)


class AnalysisMixin(rx.State, mixin=True):
    """Event handlers for running analyses and managing results."""

    # ====================================================================
    # Multi-result store
    # ====================================================================

    def _store_result(
        self,
        key: str,
        result: Dict[str, Any],
        comparison: Dict[str, Any] = None,
        geojson_feature: Dict[str, Any] = None,
    ):
        """Persist an analysis bundle under *key* and activate it."""
        bundle = {"result": result, "comparison": comparison, "geojson": geojson_feature}
        self.all_analysis_results[key] = bundle
        if key not in self.result_keys_list:
            self.result_keys_list = self.result_keys_list + [key]
        self.active_result_key = key
        self.analysis_results = result
        if comparison:
            self.mapbiomas_comparison_result = comparison

    def switch_result(self, key: str):
        """Activate a previously stored result and zoom to its geometry."""
        if key not in self.all_analysis_results:
            return
        bundle = self.all_analysis_results[key]
        self.active_result_key = key
        self.analysis_results = bundle.get("result", {})
        self.mapbiomas_comparison_result = bundle.get("comparison")

        geojson = bundle.get("geojson")
        if geojson:
            geom = geojson.get("geometry", geojson)
            coords = geom.get("coordinates", [])
            if coords:
                all_pts: list = []

                def _flatten(c):
                    if isinstance(c, list) and c:
                        if isinstance(c[0], (int, float)):
                            all_pts.append(c[:2])
                        else:
                            for sub in c:
                                _flatten(sub)

                _flatten(coords)
                if all_pts:
                    lons = [p[0] for p in all_pts]
                    lats = [p[1] for p in all_pts]
                    self.map_zoom_bounds = {
                        "min_lat": min(lats), "max_lat": max(lats),
                        "min_lon": min(lons), "max_lon": max(lons),
                        "center_lat": (min(lats) + max(lats)) / 2,
                        "center_lon": (min(lons) + max(lons)) / 2,
                    }

    def remove_result(self, key: str):
        """Remove a stored result; activate the most recent remaining one."""
        if key in self.all_analysis_results:
            del self.all_analysis_results[key]
        self.result_keys_list = [k for k in self.result_keys_list if k != key]
        if self.active_result_key == key:
            if self.result_keys_list:
                self.switch_result(self.result_keys_list[-1])
            else:
                self.active_result_key = ""
                self.analysis_results = {}
                self.mapbiomas_comparison_result = None

    def set_analysis_results(self, results: Dict[str, Any]):
        """Directly set the active analysis results dict."""
        self.analysis_results = results

    # ====================================================================
    # Comparison year setters
    # ====================================================================

    def set_comparison_year1(self, year: str):
        """Set the first comparison year."""
        try:
            self.comparison_year1 = int(year)
        except (ValueError, TypeError):
            pass

    def set_comparison_year2(self, year: str):
        """Set the second comparison year."""
        try:
            self.comparison_year2 = int(year)
        except (ValueError, TypeError):
            pass

    # ====================================================================
    # Territory-level analysis (MapBiomas & Hansen)
    # ====================================================================

    def run_mapbiomas_analysis(self):
        """Run MapBiomas analysis for the selected territory (synchronous path)."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.mapbiomas_analysis_pending = True
            self.loading_type = "ee"
            self.loading_message = f"Fetching {self.selected_territory} from Earth Engine..."
            self.error_message = ""

            ee_service = get_ee_service()
            territory_geom = ee_service.get_territory_geometry(self.selected_territory)
            if territory_geom is None:
                self.error_message = f"Could not find territory: {self.selected_territory}"
                self.mapbiomas_analysis_pending = False
                self.loading_type = ""
                self.loading_message = ""
                return

            self.loading_type = "processing"
            self.loading_message = f"Processing MapBiomas {self.mapbiomas_current_year} data..."

            analysis_df = ee_service.analyze_mapbiomas(territory_geom, self.mapbiomas_current_year)

            if analysis_df.empty:
                self.error_message = (
                    f"No MapBiomas data found for {self.selected_territory} "
                    f"in {self.mapbiomas_current_year}"
                )
            else:
                self.loading_type = "preparing"
                self.loading_message = "Preparing visualizations..."
                result_dict = {
                    "type": "mapbiomas",
                    "summary": {"total_area_ha": analysis_df["Area_ha"].sum(), "classes": len(analysis_df)},
                    "territory": self.selected_territory,
                    "year": self.mapbiomas_current_year,
                    "data": analysis_df.to_dict("records"),
                }
                self.analysis_results = result_dict
                self.mapbiomas_analysis_result = result_dict
                self.territory_analysis_year = self.mapbiomas_current_year
                self.loading_message = f"✓ {len(analysis_df)} classes found"
                logger.info(f"✓ MapBiomas analysis: {len(analysis_df)} classes")

            self.mapbiomas_analysis_pending = False
            self.clear_loading()

        except Exception as e:
            logger.error(f"MapBiomas analysis error: {e}", exc_info=True)
            self.error_message = f"Analysis failed: {e}"
            self.mapbiomas_analysis_pending = False
            self.clear_loading()

    def run_hansen_analysis(self):
        """Run Hansen analysis for the selected territory (synchronous path)."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.hansen_analysis_pending = True
            self.loading_type = "ee"
            self.loading_message = f"Fetching {self.selected_territory} from Earth Engine..."
            self.error_message = ""

            ee_service = get_ee_service()
            territory_geom = ee_service.get_territory_geometry(self.selected_territory)
            if territory_geom is None:
                self.error_message = f"Could not find territory: {self.selected_territory}"
                self.hansen_analysis_pending = False
                self.loading_type = ""
                self.loading_message = ""
                return

            self.loading_type = "processing"
            self.loading_message = f"Processing Hansen {self.hansen_current_year} data..."

            analysis_df = ee_service.analyze_hansen(territory_geom, self.hansen_current_year)

            if analysis_df.empty:
                self.error_message = "No data found for this territory"
            else:
                self.loading_type = "preparing"
                self.loading_message = "Preparing visualizations..."
                result_dict = {
                    "type": "hansen",
                    "territory": self.selected_territory,
                    "year": self.hansen_current_year,
                    "data": analysis_df.to_dict("records"),
                }
                self.analysis_results = result_dict
                self.hansen_analysis_result = result_dict
                self.loading_message = "✓ Analysis complete"
                logger.info(f"✓ Hansen analysis for {self.selected_territory}")

            self.hansen_analysis_pending = False
            self.clear_loading()

        except Exception as e:
            self.error_message = f"Analysis failed: {e}"
            self.hansen_analysis_pending = False
            self.clear_loading()

    async def run_mapbiomas_analysis_on_territory(self):
        """Run MapBiomas analysis on selected territory (async, generates tile layer)."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.mapbiomas_analysis_pending = True
            self.loading_type = "ee"
            self.loading_message = f"Fetching {self.selected_territory} from Earth Engine..."
            self.error_message = ""

            ee_service = get_ee_service()
            ee_geom = ee_service.get_territory_geometry(self.selected_territory)

            if not ee_geom:
                self.error_message = f"Territory geometry not found: {self.selected_territory}"
                self.mapbiomas_analysis_pending = False
                self.loading_type = ""
                self.loading_message = ""
                return

            self.loading_type = "processing"
            self.loading_message = f"Processing MapBiomas {self.mapbiomas_current_year} data..."

            result_df = ee_service.analyze_mapbiomas(ee_geom, self.mapbiomas_current_year)

            if result_df.empty:
                self.error_message = f"No MapBiomas data found for {self.selected_territory}"
            else:
                self.loading_type = "preparing"
                self.loading_message = "Preparing visualizations..."
                result_dict = {
                    "type": "mapbiomas",
                    "territory": self.selected_territory,
                    "year": self.mapbiomas_current_year,
                    "data": result_df.to_dict("records"),
                    "summary": {"total_area_ha": result_df["Area_ha"].sum(), "classes": len(result_df)},
                }
                self.mapbiomas_analysis_result = result_dict
                self.analysis_results = result_dict
                self.territory_analysis_year = self.mapbiomas_current_year
                self.loading_message = f"✓ {len(result_df)} classes found"
                logger.info(f"✓ Territory MapBiomas: {len(result_df)} classes")

                # Generate clipped tile layer
                try:
                    from ..utils.ee_layers import _cached_get_map_id, MAPBIOMAS_PALETTE

                    mapbiomas_img = ee_service.get_mapbiomas()
                    year = self.mapbiomas_current_year
                    territory = self.selected_territory
                    clipped = mapbiomas_img.select(f"classification_{year}").clip(ee_geom)
                    vis_params = {"min": 0, "max": 62, "palette": MAPBIOMAS_PALETTE}
                    tile_url = _cached_get_map_id(
                        f"analysis_mapbiomas_{territory}_{year}", lambda: clipped, vis_params
                    )
                    if tile_url:
                        self.analysis_tile_layers = [
                            {"url": tile_url, "name": f"MapBiomas {year} - {territory}", "attr": "MapBiomas"}
                        ]
                        self.geometry_version += 1
                except Exception as tile_e:
                    logger.warning(f"Could not generate MapBiomas tile layer: {tile_e}")

            self.mapbiomas_analysis_pending = False
            self.clear_loading()

        except Exception as e:
            self.error_message = f"Territory analysis failed: {e}"
            self.mapbiomas_analysis_pending = False
            self.clear_loading()
            logger.error(f"MapBiomas territory analysis error: {e}", exc_info=True)

    async def run_hansen_analysis_on_territory(self):
        """Run Hansen analysis on selected territory (async, generates tile layer)."""
        try:
            import ee
            from ..utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.hansen_analysis_pending = True
            self.loading_type = "ee"
            self.loading_message = f"Fetching {self.selected_territory} from Earth Engine..."
            self.error_message = ""

            ee_service = get_ee_service()
            ee_geom = ee_service.get_territory_geometry(self.selected_territory)

            if not ee_geom:
                self.error_message = f"Territory geometry not found: {self.selected_territory}"
                self.hansen_analysis_pending = False
                self.loading_type = ""
                self.loading_message = ""
                return

            self.loading_type = "processing"
            self.loading_message = f"Processing Hansen {self.hansen_current_year} data..."

            result_df = ee_service.analyze_hansen(ee_geom, self.hansen_current_year)

            if result_df is None or result_df.empty:
                self.error_message = (
                    f"No Hansen data for {self.selected_territory} in {self.hansen_current_year}"
                )
            else:
                self.loading_type = "preparing"
                self.loading_message = "Preparing visualizations..."
                result_dict = {
                    "type": "hansen",
                    "territory": self.selected_territory,
                    "year": self.hansen_current_year,
                    "data": result_df.to_dict("records"),
                    "summary": {"total_area_ha": result_df["Area_ha"].sum(), "classes": len(result_df)},
                }
                self.hansen_analysis_result = result_dict
                self.analysis_results = result_dict
                self.loading_message = "✓ Analysis complete"
                logger.info(f"✓ Hansen territory analysis for {self.selected_territory}")

                # Generate clipped tile layer
                try:
                    from ..utils.ee_layers import _cached_get_map_id, HANSEN_PALETTE
                    from ..config import HANSEN_DATASETS, HANSEN_OCEAN_MASK

                    year_key = str(self.hansen_current_year)
                    territory = self.selected_territory
                    landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
                    hansen_img = ee.Image(HANSEN_DATASETS[year_key]).updateMask(landmask)
                    clipped = hansen_img.clip(ee_geom)
                    vis_params = {"min": 0, "max": 255, "palette": HANSEN_PALETTE}
                    tile_url = _cached_get_map_id(
                        f"analysis_hansen_{territory}_{year_key}", lambda: clipped, vis_params
                    )
                    if tile_url:
                        current_layers = list(self.analysis_tile_layers)
                        current_layers.append(
                            {"url": tile_url, "name": f"Hansen {year_key} - {territory}", "attr": "Hansen/GLAD"}
                        )
                        self.analysis_tile_layers = current_layers
                        self.geometry_version += 1
                except Exception as tile_e:
                    logger.warning(f"Could not generate Hansen tile layer: {tile_e}")

            self.hansen_analysis_pending = False
            self.clear_loading()

        except Exception as e:
            self.error_message = f"Hansen analysis failed: {e}"
            self.hansen_analysis_pending = False
            self.clear_loading()
            logger.error(f"Hansen territory analysis error: {e}", exc_info=True)

    # ====================================================================
    # Geometry-level analysis (drawn features)
    # ====================================================================

    async def run_geometry_analysis(self):
        """Dispatch geometry analysis (MapBiomas or Hansen) for selected feature."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            self.error_message = "Please select a geometry first"
            return

        # Auto-zoom to geometry bounds if available
        try:
            feature = self.drawn_features[self.selected_geometry_idx]
            if "bounds" in feature:
                bounds = feature["bounds"]
                self.map_zoom_bounds = {
                    "min_lat": bounds["min_lat"], "max_lat": bounds["max_lat"],
                    "min_lon": bounds["min_lon"], "max_lon": bounds["max_lon"],
                    "center_lat": (bounds["min_lat"] + bounds["max_lat"]) / 2,
                    "center_lon": (bounds["min_lon"] + bounds["max_lon"]) / 2,
                }
        except Exception as e:
            logger.warning(f"Could not zoom to geometry: {e}")

        if self.geometry_analysis_type == "mapbiomas":
            await self.run_geometry_mapbiomas_analysis()
        elif self.geometry_analysis_type == "hansen":
            await self.run_geometry_hansen_analysis()

    async def run_geometry_mapbiomas_analysis(self):
        """Run MapBiomas analysis on the selected drawn geometry (quick single-year)."""
        try:
            from ..utils.ee_service_extended import get_ee_service

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            self.geometry_analysis_pending = True
            self.loading_message = f"Analyzing MapBiomas {self.geometry_analysis_year}..."
            self.error_message = ""

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                self.geometry_analysis_pending = False
                return

            ee_service = get_ee_service()
            analysis_df = ee_service.analyze_mapbiomas(ee_geom, self.geometry_analysis_year)

            if analysis_df.empty:
                self.error_message = f"No MapBiomas data found for year {self.geometry_analysis_year}"
            else:
                result_dict = {
                    "type": "mapbiomas",
                    "year": self.geometry_analysis_year,
                    "num_classes": len(analysis_df),
                    "total_area_ha": float(analysis_df["Area_ha"].sum()),
                    "data": analysis_df.to_dict("records"),
                }
                self.geometry_analysis_results[self.selected_geometry_idx] = result_dict
                self.analysis_results = {
                    "type": "mapbiomas",
                    "geometry": f"Custom Geometry #{self.selected_geometry_idx + 1}",
                    "year": self.geometry_analysis_year,
                    "data": analysis_df.to_dict("records"),
                    "summary": {
                        "total_area_ha": float(analysis_df["Area_ha"].sum()),
                        "classes": len(analysis_df),
                    },
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Geometry MapBiomas: {len(analysis_df)} classes")

            self.geometry_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {e}"
            self.geometry_analysis_pending = False
            logger.error(f"Geometry MapBiomas analysis error: {e}")

    async def run_geometry_hansen_analysis(self):
        """Run Hansen analysis on the selected drawn geometry (area distribution)."""
        try:
            from ..utils.hansen_analysis import get_hansen_analyzer

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            self.geometry_analysis_pending = True
            self.loading_message = f"Analyzing Hansen {self.geometry_analysis_year}..."

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                self.geometry_analysis_pending = False
                return

            analyzer = get_hansen_analyzer()
            if not analyzer.is_available():
                self.error_message = "Hansen dataset not available"
                self.geometry_analysis_pending = False
                return

            result_df = analyzer.get_area_distribution(
                ee_geom, year=str(self.geometry_analysis_year), scale=30
            )

            if result_df is None or result_df.empty:
                self.error_message = f"No Hansen data found for year {self.geometry_analysis_year}"
            else:
                result_dict = {
                    "type": "hansen",
                    "year": str(self.geometry_analysis_year),
                    "num_classes": len(result_df),
                    "total_area_ha": float(result_df["Area_ha"].sum()),
                    "data": result_df.to_dict("records"),
                }
                self.geometry_analysis_results[self.selected_geometry_idx] = result_dict
                self.analysis_results = {
                    "type": "hansen",
                    "geometry": f"Custom Geometry #{self.selected_geometry_idx + 1}",
                    "year": str(self.geometry_analysis_year),
                    "data": result_df.to_dict("records"),
                    "summary": {
                        "year": str(self.geometry_analysis_year),
                        "num_classes": len(result_df),
                        "total_area_ha": float(result_df["Area_ha"].sum()),
                    },
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Geometry Hansen: {len(result_df)} classes")

            self.geometry_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {e}"
            self.geometry_analysis_pending = False
            logger.error(f"Geometry Hansen analysis error: {e}")

    async def run_mapbiomas_analysis_on_geometry(self):
        """Run MapBiomas (single year) on selected geometry and store in result system."""
        try:
            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return

            self.mapbiomas_analysis_pending = True
            self.loading_message = f"Analyzing MapBiomas {self.mapbiomas_current_year}..."

            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return

            result_df = analyzer.analyze_single_year(ee_geom, self.mapbiomas_current_year, scale=30)

            if result_df.empty:
                self.error_message = "No MapBiomas data found for this area"
            else:
                geom_name = self.drawn_features[self.selected_geometry_idx].get(
                    "name", "Selected Geometry"
                )
                result_dict = {
                    "type": "mapbiomas",
                    "geometry": geom_name,
                    "year": self.mapbiomas_current_year,
                    "data": result_df.to_dict("records"),
                    "summary": {
                        "total_area_ha": result_df["Area_ha"].sum(),
                        "num_classes": len(result_df),
                        "top_class": result_df.iloc[0]["Class_Name"] if len(result_df) > 0 else "Unknown",
                    },
                }
                key = f"geometry::{self.selected_geometry_idx}"
                feat = self.drawn_features[self.selected_geometry_idx]
                self._store_result(key, result_dict, geojson_feature=feat)
                self.set_active_tab("analysis")
                self.loading_message = ""

            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {e}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas geometry analysis error: {e}")

    async def run_hansen_analysis_on_geometry(self):
        """Run Hansen area-distribution on selected geometry and store in result system."""
        try:
            from ..utils.hansen_analysis import get_hansen_analyzer

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return

            self.hansen_analysis_pending = True
            self.loading_message = f"Analyzing Hansen {self.hansen_current_year}..."

            analyzer = get_hansen_analyzer()
            if not analyzer.is_available():
                self.error_message = "Hansen dataset not available"
                self.hansen_analysis_pending = False
                return

            result_df = analyzer.get_area_distribution(ee_geom, year=self.hansen_current_year, scale=30)

            if result_df is None or result_df.empty:
                self.error_message = "No Hansen data found for this area"
            else:
                geom_name = self.drawn_features[self.selected_geometry_idx].get(
                    "name", "Selected Geometry"
                )
                result_dict = {
                    "type": "hansen",
                    "geometry": geom_name,
                    "data": result_df.to_dict("records"),
                    "summary": {
                        "year": self.hansen_current_year,
                        "num_classes": len(result_df),
                        "total_area_ha": float(result_df["Area_ha"].sum()),
                    },
                }
                key = f"geometry::{self.selected_geometry_idx}"
                feat = self.drawn_features[self.selected_geometry_idx]
                self._store_result(key, result_dict, geojson_feature=feat)
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Hansen geometry analysis: {len(result_df)} classes")

            self.hansen_analysis_pending = False

        except Exception as e:
            self.error_message = f"Hansen analysis failed: {e}"
            self.hansen_analysis_pending = False
            logger.error(f"Hansen geometry analysis error: {e}")

    async def run_full_analysis_on_geometry(self):
        """Run full MapBiomas comparison (two years) on selected geometry."""
        try:
            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from ..utils.visualization import calculate_gains_losses

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return

            self.mapbiomas_analysis_pending = True
            geom_name = self.drawn_features[self.selected_geometry_idx].get(
                "name", f"Geometry {self.selected_geometry_idx + 1}"
            )
            self.loading_message = f"Full analysis on {geom_name}..."

            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return

            y1, y2 = self.comparison_year1, self.comparison_year2
            df1 = analyzer.analyze_single_year(ee_geom, y1, scale=30)
            df2 = analyzer.analyze_single_year(ee_geom, y2, scale=30)

            if df2.empty:
                self.error_message = f"No MapBiomas data for year {y2}"
                self.mapbiomas_analysis_pending = False
                return

            name_col = "Class_Name" if "Class_Name" in df2.columns else "Class"
            result_dict = {
                "type": "mapbiomas",
                "geometry": geom_name,
                "year": y2,
                "data": df2.to_dict("records"),
                "summary": {
                    "total_area_ha": df2["Area_ha"].sum(),
                    "num_classes": len(df2),
                    "top_class": df2.iloc[0][name_col] if len(df2) > 0 else "Unknown",
                },
            }

            comparison_dict = None
            if not df1.empty:
                comparison_df = calculate_gains_losses(df1, df2)
                comparison_dict = {
                    "year_start": y1,
                    "year_end": y2,
                    "territory": geom_name,
                    "data": comparison_df.to_dict("records"),
                }

            key = f"geometry::{self.selected_geometry_idx}"
            feat = self.drawn_features[self.selected_geometry_idx]
            self._store_result(key, result_dict, comparison=comparison_dict, geojson_feature=feat)

            self.show_change_mask = True
            self.change_mask_year1 = y1
            self.change_mask_year2 = y2
            self.geometry_version += 1
            self.set_active_tab("analysis")
            self.loading_message = ""
            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Full analysis failed: {e}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"Full geometry analysis error: {e}")

    # ====================================================================
    # Territory comparison (two-year MapBiomas with transitions)
    # ====================================================================

    async def run_territory_comparison(self):
        """Compare MapBiomas land cover between two years for selected territory."""
        try:
            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from ..utils.ee_service_extended import get_ee_service
            from ..utils.visualization import calculate_gains_losses

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.mapbiomas_analysis_pending = True
            y1, y2 = self.comparison_year1, self.comparison_year2
            self.loading_message = f"Comparing {self.selected_territory}: {y1} vs {y2}..."

            ee_service = get_ee_service()
            ee_geom = ee_service.get_territory_geometry(self.selected_territory)
            if not ee_geom:
                self.error_message = f"Territory geometry not found: {self.selected_territory}"
                self.mapbiomas_analysis_pending = False
                return

            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return

            df1 = analyzer.analyze_single_year(ee_geom, y1, scale=30)
            df2 = analyzer.analyze_single_year(ee_geom, y2, scale=30)

            if df1.empty or df2.empty:
                self.error_message = "Could not get data for one or both years"
                self.mapbiomas_analysis_pending = False
                return

            comparison_df = calculate_gains_losses(df1, df2)

            self.territory_result = {
                "data": df1.to_dict("records"),
                "summary": {
                    "year": y1,
                    "num_classes": len(df1),
                    "total_area_ha": df1["Area_ha"].sum() if "Area_ha" in df1.columns else 0,
                },
            }
            self.territory_result_year2 = {
                "data": df2.to_dict("records"),
                "summary": {
                    "year": y2,
                    "num_classes": len(df2),
                    "total_area_ha": df2["Area_ha"].sum() if "Area_ha" in df2.columns else 0,
                },
            }
            self.territory_name = self.selected_territory
            self.territory_year = y1
            self.territory_year2 = y2
            self.territory_source = "MapBiomas"

            # Pixel-level transitions for Sankey / transition matrix
            self.loading_message = f"Computing transitions {y1} → {y2}..."
            transitions = analyzer.compute_transitions(ee_geom, y1, y2, scale=30)
            self.territory_transitions = transitions if transitions else None

            comparison_dict = {
                "year_start": y1,
                "year_end": y2,
                "territory": self.selected_territory,
                "data": comparison_df.to_dict("records"),
                "transitions": transitions if transitions else None,
            }
            self.mapbiomas_comparison_result = comparison_dict

            name_col = "Class_Name" if "Class_Name" in df2.columns else "Class"
            result_dict = {
                "type": "mapbiomas",
                "geometry": self.selected_territory,
                "year": y2,
                "data": df2.to_dict("records"),
                "summary": {
                    "total_area_ha": df2["Area_ha"].sum(),
                    "num_classes": len(df2),
                    "top_class": df2.iloc[0][name_col] if len(df2) > 0 else "Unknown",
                },
            }

            key = f"territory::{self.selected_territory}"
            geojson_feat = self.territory_geojson_features[0] if self.territory_geojson_features else None
            self._store_result(key, result_dict, comparison=comparison_dict, geojson_feature=geojson_feat)

            self.loading_message = ""
            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Comparison failed: {e}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"Territory comparison error: {e}")

    async def run_mapbiomas_comparison(self):
        """Compare MapBiomas years for a drawn/uploaded geometry (legacy path)."""
        try:
            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from ..utils.buffer_utils import convert_geojson_to_ee_geometry

            if not self.selected_territory:
                self.error_message = "Please select or upload a geometry first"
                return

            geom_feature = None
            for feat in self.all_drawn_features:
                if feat.get("properties", {}).get("name") == self.selected_territory:
                    geom_feature = feat
                    break

            if not geom_feature:
                self.error_message = f"Geometry not found: {self.selected_territory}"
                return

            self.mapbiomas_analysis_pending = True
            year1 = self.mapbiomas_current_year - 5
            self.loading_message = f"Comparing MapBiomas {year1} vs {self.mapbiomas_current_year}..."

            ee_geom = convert_geojson_to_ee_geometry(geom_feature)
            if not ee_geom:
                self.error_message = "Failed to process geometry"
                self.mapbiomas_analysis_pending = False
                return

            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return

            comparison_df = analyzer.compare_years(
                ee_geom, year1, self.mapbiomas_current_year, scale=30
            )

            if comparison_df.empty:
                self.error_message = "Could not compare years"
            else:
                self.mapbiomas_comparison_result = {
                    "year_start": year1,
                    "year_end": self.mapbiomas_current_year,
                    "data": comparison_df.to_dict("records"),
                }
                self.loading_message = ""

            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Comparison failed: {e}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas comparison error: {e}")
