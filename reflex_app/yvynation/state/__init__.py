"""
Global state management for the Yvynation Reflex app.

AppState is composed of six domain-specific mixin classes (each a proper
``rx.State, mixin=True`` subclass) so that each concern lives in its own
file while all reactive state variables and computed properties remain
here in one place.

Mixin files (rx.State, mixin=True — event handlers only):
    _ui.py        – sidebar, tabs, language, tutorial, error/loading
    _map.py       – MapBiomas/Hansen layers, GFC, change mask, base layer
    _territory.py – territory selection, search, EE geometry loading
    _geometry.py  – drawn features, buffers, upload, popup
    _analysis.py  – analysis execution (territory & geometry), result store
    _export.py    – CSV / ZIP / PDF export
"""

import logging
from typing import Any, Dict, List, Optional, Union

import reflex as rx
import plotly.graph_objects as pgo
from plotly.graph_objs import Figure

# BufferGeometry lives in _geometry.py so it's available without circular imports
from ._geometry import BufferGeometry, GeometryMixin
from ._ui import UIMixin
from ._map import MapMixin
from ._territory import TerritoryMixin
from ._analysis import AnalysisMixin
from ._export import ExportMixin
from ._batch import BatchMixin
from ._advanced_viz import AdvancedVizMixin

logger = logging.getLogger(__name__)


class AppState(
    BatchMixin,
    AdvancedVizMixin,
    ExportMixin,
    AnalysisMixin,
    GeometryMixin,
    TerritoryMixin,
    MapMixin,
    UIMixin,
    rx.State,
):
    """
    Global reactive application state.

    All state *variables* and *computed properties* live here.
    Event handlers are inherited from the mixin classes above.
    """

    # ====================================================================
    # Debug / tracking
    # ====================================================================
    _selection_call_count: int = 0
    _selection_timestamp: float = 0.0

    # ====================================================================
    # Initialisation
    # ====================================================================
    data_loaded: bool = True
    ee_initialized: bool = False
    loading_message: str = ""
    #: "ee" | "processing" | "preparing" | "" (none)
    loading_type: str = ""
    error_message: str = ""

    # ====================================================================
    # Language & preferences
    # ====================================================================
    language: str = "en"  # "en" | "pt" | "es"
    auto_detect_enabled: bool = True

    # ====================================================================
    # Map view
    # ====================================================================
    map_center: tuple = (0.0, 0.0)
    map_zoom: int = 3
    map_bounds: Optional[List] = None
    #: Keys: min_lat, max_lat, min_lon, max_lon, center_lat, center_lon
    map_zoom_bounds: Dict[str, float] = {}
    selected_base_layer: str = "openstreetmap"

    # ====================================================================
    # Layer configuration
    # ====================================================================
    mapbiomas_years_enabled: Dict[int, bool] = {}
    mapbiomas_current_year: int = 2024  # Collection 10.1 adds 2024
    mapbiomas_displayed_years: List[int] = []

    hansen_years_enabled: Dict[str, bool] = {}
    hansen_current_year: str = "2020"
    hansen_displayed_layers: List[str] = []

    aafc_years_enabled: Dict[int, bool] = {}
    aafc_current_year: int = 2023

    # GFC layers (Global Forest Change)
    show_hansen_gfc_tree_cover: bool = False
    show_hansen_gfc_tree_loss: bool = False
    show_hansen_gfc_tree_gain: bool = False

    # ====================================================================
    # Territory & geometry selection
    # ====================================================================
    selected_territory: Optional[str] = None
    selected_country: str = "Brazil"
    territory_filter_state: Optional[str] = None
    available_territories: List[str] = []
    territory_search_query: str = ""

    # ====================================================================
    # Drawn features & buffers
    # ====================================================================
    drawn_features: List[Dict[str, Any]] = []
    all_drawn_features: List[Dict[str, Any]] = []
    selected_geometry_idx: Optional[int] = None
    selected_geometry_is_territory: bool = False
    #: Track geometry hashes to avoid duplicates when "Save Drawing" is clicked repeatedly
    _processed_geometry_hashes: set = rx.Field(default_factory=set)
    buffer_geometries: Dict[str, BufferGeometry] = {}
    current_buffer_for_analysis: Optional[str] = None
    buffer_compare_mode: bool = False
    #: GeoJSON features for active buffer overlays on the map
    buffer_geojson_features: List[Dict[str, Any]] = []

    # ---- Active analysis target + area registry -------------------------
    #: Subject kind every run acts on: "territory" | "drawing" | "".
    active_target_kind: str = ""
    #: Registry of every selected/drawn area, keyed by a stable id.  Each entry:
    #: {id, kind, label, geojson (feature), buffer_geojson, buffer_name,
    #:  result_key, has_results}.  The entry's geojson is the canonical geometry
    #: (zoom / resolve / download / re-activation all read it), so switching
    #: between territories restores each one without re-fetching.
    analysis_targets: Dict[str, Dict[str, Any]] = {}
    #: id of the active registry entry.
    active_target_id: str = ""
    #: Cache of buffer overlay features keyed by source geometry name, so
    #: switching the active target reuses a buffer without recomputing it.
    buffer_overlays_by_source: Dict[str, Dict[str, Any]] = {}

    # Per-geometry analysis cache
    geometry_analysis_results: Dict[int, Dict[str, Any]] = {}
    geometry_analysis_type: str = "mapbiomas"   # "mapbiomas" | "hansen_glad" | "hansen_gfc"
    geometry_analysis_year: Union[int, str] = 2023
    geometry_hansen_glad_year: str = "2020"  # For Hansen GLAD (forest cover) analysis on geometry - year options: 2000, 2005, 2010, 2015, 2020
    geometry_analysis_pending: bool = False

    # Geometry info popup
    show_geometry_popup: bool = False
    geometry_popup_info: Dict[str, Any] = {}

    # ====================================================================
    # Analysis results
    # ====================================================================
    analysis_results: Dict[str, Any] = {}
    mapbiomas_analysis_result: Optional[Dict[str, Any]] = None
    hansen_analysis_result: Optional[Dict[str, Any]] = None
    mapbiomas_comparison_result: Optional[Dict[str, Any]] = None
    hansen_comparison_result: Optional[Dict[str, Any]] = None
    analysis_figures: Dict[str, Any] = {}
    #: Analysis run on the active buffer (shown side-by-side with territory results)
    buffer_mapbiomas_result: Optional[Dict[str, Any]] = None
    buffer_hansen_result: Optional[Dict[str, Any]] = None
    #: Buffer result for comparison year2 (populated by run_territory_comparison_bg)
    buffer_compare_result: Optional[Dict[str, Any]] = None
    #: Buffer gains/losses comparison (year1 vs year2 in the buffer ring)
    buffer_mapbiomas_comparison_result: Optional[Dict[str, Any]] = None
    #: Buffer result from Hansen GFC analysis
    buffer_gfc_result: Optional[Dict[str, Any]] = None
    #: Transition table for the buffer ring (year1 → year2), populated by run_territory_comparison_bg
    buffer_territory_transitions: Optional[Dict[str, Any]] = None

    # Multi-result store  key → bundle
    # Key format: "territory::Xingu" or "geometry::0"
    all_analysis_results: Dict[str, Dict[str, Any]] = {}
    active_result_key: str = ""
    result_keys_list: List[str] = []

    # Territory display info
    territory_analysis_year: int = 2024
    territory_geometry_displayed: bool = False
    territory_geojson_features: List[Dict[str, Any]] = []

    # Indigenous lands
    indigenous_lands_tile_url: str = ""
    show_indigenous_lands: bool = True
    territory_name_property: str = "name"

    # Comparison year selection
    comparison_year1: int = 2019
    comparison_year2: int = 2024  # Collection 10.1 includes 2024

    # Territory analysis storage
    territory_result: Optional[Dict[str, Any]] = None
    territory_result_year2: Optional[Dict[str, Any]] = None
    territory_name: str = ""
    territory_year: int = 2024
    territory_year2: Optional[int] = None
    territory_source: str = "MapBiomas"
    territory_transitions: Optional[Dict[str, Any]] = None

    # ====================================================================
    # Map overlay state
    # ====================================================================
    show_geometries_on_map: bool = True
    show_change_mask: bool = False
    change_mask_year1: int = 2018
    change_mask_year2: int = 2024
    #: Incremented to force map HTML rebuild
    geometry_version: int = 0
    analysis_tile_layers: List[Dict[str, str]] = []

    # ====================================================================
    # Pending flags
    # ====================================================================
    mapbiomas_analysis_pending: bool = False
    hansen_analysis_pending: bool = False
    export_pending: bool = False
    map_export_pending: bool = False

    # ====================================================================
    # UI state
    # ====================================================================
    active_tab: str = "map"   # "map" | "analysis" | "tutorial" | "about"
    analysis_mode: str = "portal"  # "portal" | "geometry" | "territory"
    sidebar_open: bool = True
    sidebar_width: int = 300
    is_resizing_sidebar: bool = False
    show_tutorial: bool = False
    tutorial_expanded_steps: List[int] = []
    show_layer_reference: bool = False
    use_consolidated_classes: bool = True
    buffer_distance_input: str = ""
    #: Default buffer distance used by the auto-buffer feature (km)
    auto_buffer_km: float = 10.0
    #: Whether to automatically create a buffer when a territory is selected
    auto_buffer_enabled: bool = True

    # Sidebar section expansion
    sidebar_mapbiomas_expanded: bool = False
    sidebar_hansen_expanded: bool = False
    sidebar_territory_expanded: bool = False
    sidebar_geometry_expanded: bool = False
    upload_file_expanded: bool = False

    # Pending territory confirmation
    pending_territory: Optional[str] = None

    # Per-analysis-type geometry results (so GFC and GLAD tabs don't overwrite each other)
    geometry_glad_result: Optional[Dict[str, Any]] = None
    geometry_gfc_result: Optional[Dict[str, Any]] = None

    # Which sub-tab is active inside the analysis panel (persists across Reflex re-renders)
    active_analysis_tab: str = "mapbiomas"

    #: Full-screen panel toggle: "" (split) | "map" | "results"
    fullscreen_panel: str = ""

    # ====================================================================
    # Computed properties
    # ====================================================================

    @rx.var(auto_deps=False, deps=["language"])
    def tr(self) -> Dict[str, str]:
        """Current translations dict, reactive to language changes."""
        from ..utils.translations import TRANSLATIONS

        return TRANSLATIONS.get(self.language, TRANSLATIONS["en"])

    @rx.var
    def filtered_territories(self) -> List[str]:
        """Territory list filtered by the search query."""
        if not self.territory_search_query:
            return self.available_territories
        query_lower = self.territory_search_query.lower()
        return [t for t in self.available_territories if query_lower in t.lower()]

    @rx.var(
        auto_deps=False,
        deps=[
            "mapbiomas_displayed_years", "hansen_displayed_layers",
            "geometry_version", "show_geometries_on_map",
            "show_change_mask", "change_mask_year1", "change_mask_year2",
            "territory_geojson_features", "show_indigenous_lands",
            "available_territories",
            "analysis_tile_layers",
            "show_hansen_gfc_tree_cover", "show_hansen_gfc_tree_loss",
            "show_hansen_gfc_tree_gain",
            "buffer_geojson_features",
        ],
    )
    def map_html(self) -> str:
        """
        Full Folium/Leaflet HTML for the map panel.
        Rebuilt whenever layer selection, geometry overlays, or the
        indigenous-lands toggle changes.  Territory boundaries are now
        served from the local GeoPackage (no EE tile URL required).

        IMPORTANT: the indigenous lands GeoJSON layer (all 657 territories) is
        only injected AFTER ``available_territories`` is populated by
        ``load_territories_background()``.  At startup the list is empty so no
        territory GeoJSON ends up in the initial state / context.js — this keeps
        the initial page payload small and prevents the module-parse errors that
        occur when context.js exceeds ~5 MB.
        """
        try:
            from ..utils.map_builder import build_map

            all_overlay = []
            if self.show_geometries_on_map and self.drawn_features:
                all_overlay.extend(self.drawn_features)
            if self.territory_geojson_features:
                all_overlay.extend(self.territory_geojson_features)

            geom_features = all_overlay or None

            change_years = None
            change_geom = None
            if self.show_change_mask:
                change_years = (self.change_mask_year1, self.change_mask_year2)
                if self.territory_geojson_features:
                    change_geom = self.territory_geojson_features[0].get("geometry")
                elif self.drawn_features:
                    change_geom = self.drawn_features[0].get("geometry")

            # Gate territory GeoJSON on available_territories being populated.
            # At startup this list is empty, so the initial map is small (< 1 MB).
            # Once load_territories_background() finishes it bumps geometry_version,
            # triggering a map rebuild that adds the interactive territory layer.
            territories_ready = bool(self.available_territories)
            show_il = self.show_indigenous_lands and territories_ready

            return build_map(
                mapbiomas_years=self.mapbiomas_displayed_years or [],
                hansen_layers=self.hansen_displayed_layers or [],
                geometry_features=geom_features,
                change_mask_years=change_years,
                change_mask_geometry=change_geom,
                show_indigenous_lands=show_il,
                analysis_tile_layers=self.analysis_tile_layers or [],
                show_gfc_tree_cover=self.show_hansen_gfc_tree_cover,
                show_gfc_tree_loss=self.show_hansen_gfc_tree_loss,
                show_gfc_tree_gain=self.show_hansen_gfc_tree_gain,
                buffer_features=self.buffer_geojson_features or [],
                fit_bounds=self.active_fit_bounds,
            )

        except Exception as e:
            logger.error(f"Error generating map HTML: {e}", exc_info=True)
            import folium

            m = folium.Map(location=[-10, -52], zoom_start=5, tiles="OpenStreetMap")
            folium.LayerControl().add_to(m)
            return m._repr_html_()

    # ---- Active analysis target (drives every run + the top-bar switcher)

    @rx.var
    def active_geometry_feature(self) -> Dict[str, Any]:
        """GeoJSON feature of the active registry entry (canonical geometry)."""
        try:
            entry = self.analysis_targets.get(self.active_target_id)
            if entry and entry.get("geojson"):
                return entry["geojson"]
        except Exception:
            pass
        return {}

    @rx.var
    def active_target_label(self) -> str:
        """Human label for the active subject (top bar + menu button)."""
        entry = self.analysis_targets.get(self.active_target_id)
        if entry:
            return entry.get("label") or "Unnamed area"
        return "Nothing selected"

    @rx.var
    def active_target_kind_label(self) -> str:
        entry = self.analysis_targets.get(self.active_target_id)
        kind = entry.get("kind") if entry else self.active_target_kind
        if kind == "territory":
            return "Territory"
        if kind == "drawing":
            return "Drawing"
        return "—"

    @rx.var
    def active_buffer_label(self) -> str:
        """Name of the buffer currently attached to the active subject."""
        try:
            if self.buffer_geojson_features:
                return self.buffer_geojson_features[0].get("name") or "Buffer"
        except Exception:
            pass
        return "—"

    @rx.var
    def has_active_target(self) -> bool:
        # Reference active_target_id (public) so the client updates reactively.
        return bool(self.active_target_id) and bool(self.active_geometry_feature)

    @rx.var
    def active_target_options(self) -> List[Dict[str, str]]:
        """Switcher options — every registered area (territories + drawings).

        Each option carries ``id`` (matched by ``set_active_target``), a
        display ``label`` (with a ✓ when it has results), and ``kind``.
        """
        opts: List[Dict[str, str]] = []
        for tid, e in self.analysis_targets.items():
            kind = e.get("kind", "")
            icon = "🗺️" if kind == "territory" else "✏️"
            mark = "  ✓" if e.get("has_results") else ""
            opts.append({
                "id": tid,
                "label": icon + " " + (e.get("label") or tid) + mark,
                "kind": kind,
            })
        return opts

    @rx.var
    def analyzed_target_count(self) -> int:
        """How many registered areas have results (drives Download-all)."""
        try:
            return sum(1 for e in self.analysis_targets.values() if e.get("has_results"))
        except Exception:
            return 0

    @rx.var
    def active_fit_bounds(self) -> Optional[List]:
        """``[[min_lat,min_lon],[max_lat,max_lon]]`` of the active subject.

        Passed to ``build_map(fit_bounds=…)`` so the map frames the active
        geometry instead of the union of all overlays.
        """
        feat = self.active_geometry_feature
        if not feat:
            return None
        geom = feat.get("geometry") or feat
        coords = geom.get("coordinates")
        if not coords:
            return None
        acc: List = []

        def _flat(c):
            if c and isinstance(c[0], (int, float)):
                acc.append(c[:2])
            else:
                for s in c:
                    _flat(s)

        try:
            _flat(coords)
            if not acc:
                return None
            lons = [p[0] for p in acc]
            lats = [p[1] for p in acc]
            return [[min(lats), min(lons)], [max(lats), max(lons)]]
        except Exception:
            return None

    # ---- Geometry selection helpers ------------------------------------

    @rx.var
    def selected_geometry_type(self) -> str:
        """Type string of the currently selected drawn geometry."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return ""
        return self.drawn_features[self.selected_geometry_idx].get("type", "Unknown")

    @rx.var
    def selected_geometry_coords_preview(self) -> str:
        """Short coordinate preview for the selected geometry."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return ""
        feature = self.drawn_features[self.selected_geometry_idx]
        coords = feature.get("coordinates", [])
        if not coords:
            return "[No coordinates]"
        
        # Flatten nested coordinate arrays to get the first coordinate pair
        first_coord = coords[0]
        while isinstance(first_coord, list) and len(first_coord) > 0:
            first_coord = first_coord[0]
        
        # Check if we have a valid coordinate pair [lon, lat]
        if isinstance(first_coord, (int, float)):
            # Single coordinate - shouldn't happen but handle it
            return f"[{first_coord:.4f}, ...]"
        
        try:
            if len(first_coord) >= 2 and isinstance(first_coord[0], (int, float)) and isinstance(first_coord[1], (int, float)):
                return f"[{first_coord[0]:.4f}, {first_coord[1]:.4f}] ({len(coords)} ...)"
        except (TypeError, IndexError):
            pass
        
        return "[Invalid coordinates]"

    # ---- Analysis summary (generic active result) ----------------------

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_total_area(self) -> str:
        try:
            val = self.analysis_results.get("summary", {}).get("total_area_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_classes(self) -> str:
        try:
            return str(self.analysis_results.get("summary", {}).get("num_classes", 0))
        except Exception:
            return "0"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_top_class(self) -> str:
        try:
            return self.analysis_results.get("summary", {}).get("top_class", "N/A")
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_cover(self) -> str:
        try:
            val = self.analysis_results.get("summary", {}).get("total_area_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_loss(self) -> str:
        try:
            num = self.analysis_results.get("summary", {}).get("num_classes", 0)
            return f"{num} classes" if num else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_gain(self) -> str:
        try:
            year = self.analysis_results.get("summary", {}).get("year", "")
            return f"Year {year}" if year else "N/A"
        except Exception:
            return "N/A"

    # ---- Data tables ---------------------------------------------------

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_table_data(self) -> List[Dict[str, Any]]:
        try:
            import pandas as pd

            data = self.analysis_results.get("data", [])
            if not data:
                return []
            df = pd.DataFrame(data)
            display_cols = [
                c for c in ["Class_Name", "Class", "Class_ID", "Area_ha", "Pixels", "Percentage"]
                if c in df.columns
            ] or list(df.columns)[:6]
            return df[display_cols].to_dict("records")
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_table_columns(self) -> List[str]:
        try:
            import pandas as pd

            data = self.analysis_results.get("data", [])
            if not data:
                return []
            df = pd.DataFrame(data)
            return (
                [c for c in ["Class_Name", "Class", "Class_ID", "Area_ha", "Pixels", "Percentage"]
                 if c in df.columns]
                or list(df.columns)[:6]
            )
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["mapbiomas_analysis_result"])
    def mapbiomas_table_data(self) -> List[Dict[str, Any]]:
        if not self.mapbiomas_analysis_result:
            return []
        return self.mapbiomas_analysis_result.get("data", [])

    @rx.var(auto_deps=False, deps=["mapbiomas_analysis_result"])
    def mapbiomas_table_columns(self) -> List[str]:
        if not self.mapbiomas_analysis_result:
            return []
        try:
            import pandas as pd

            data = self.mapbiomas_analysis_result.get("data", [])
            if not data:
                return []
            df = pd.DataFrame(data)
            return (
                [c for c in ["Class_Name", "Class", "Class_ID", "Area_ha", "Pixels", "Percentage"]
                 if c in df.columns]
                or list(df.columns)[:6]
            )
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["hansen_analysis_result"])
    def hansen_table_data(self) -> List[Dict[str, Any]]:
        # Territory Hansen analysis only (geometry GLAD now uses glad_table_data)
        if not self.hansen_analysis_result:
            return []
        return self.hansen_analysis_result.get("data", [])

    @rx.var(auto_deps=False, deps=["hansen_analysis_result"])
    def hansen_table_columns(self) -> List[str]:
        if not self.hansen_analysis_result:
            return []
        try:
            import pandas as pd

            data = self.hansen_analysis_result.get("data", [])
            if not data:
                return []
            df = pd.DataFrame(data)
            return (
                [c for c in ["Class_Name", "Class", "Class_ID", "Area_ha", "Pixels", "Percentage"]
                 if c in df.columns]
                or list(df.columns)[:6]
            )
        except Exception:
            return []

    # ---- Charts --------------------------------------------------------

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def mapbiomas_bar_chart(self) -> Figure:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.mapbiomas_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"MapBiomas bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def mapbiomas_pie_chart(self) -> Figure:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.mapbiomas_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="pie") or pgo.Figure()
        except Exception as e:
            logger.error(f"MapBiomas pie chart error: {e}")
            return pgo.Figure()

    # ---- GFC-specific computed vars (read from geometry_gfc_result) ----

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_summary_cover(self) -> str:
        try:
            val = (self.geometry_gfc_result or {}).get("summary", {}).get("tree_cover_2000_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_summary_loss(self) -> str:
        try:
            val = (self.geometry_gfc_result or {}).get("summary", {}).get("forest_loss_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_summary_gain(self) -> str:
        try:
            val = (self.geometry_gfc_result or {}).get("summary", {}).get("forest_gain_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_summary_net(self) -> str:
        try:
            val = (self.geometry_gfc_result or {}).get("summary", {}).get("net_change_ha")
            if val is None:
                return "N/A"
            sign = "+" if val > 0 else ""
            return f"{sign}{val:,.0f} ha"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_table_data(self) -> List[Dict[str, Any]]:
        try:
            return (self.geometry_gfc_result or {}).get("data", [])
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_loss_by_year(self) -> List[Dict[str, Any]]:
        """Tree loss rows filtered to Year_Code > 0, sorted by year."""
        try:
            records = [
                r for r in (self.geometry_gfc_result or {}).get("tree_loss_data", [])
                if r.get("Year_Code", 0) > 0
            ]
            return sorted(records, key=lambda r: r["Year_Code"])
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_gain_summary(self) -> List[Dict[str, Any]]:
        """All tree gain rows (Gain_Code 0 and 1) for the gain table."""
        try:
            return (self.geometry_gfc_result or {}).get("tree_gain_data", [])
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_cover_categories(self) -> List[Dict[str, Any]]:
        """Tree cover 2000 bucketed into 5 categories matching the Streamlit display."""
        try:
            cover_data = (self.geometry_gfc_result or {}).get("tree_cover_data", [])
            if not cover_data:
                return []
            total_ha = sum(r["Area_ha"] for r in cover_data)
            buckets: Dict[str, float] = {
                "No Tree Cover (0%)": 0.0,
                "Low Cover (1–25%)": 0.0,
                "Medium Cover (26–50%)": 0.0,
                "High Cover (51–75%)": 0.0,
                "Very High Cover (76–100%)": 0.0,
            }
            for r in cover_data:
                pct = r.get("Percent_Cover", 0)
                ha = r.get("Area_ha", 0.0)
                if pct == 0:
                    buckets["No Tree Cover (0%)"] += ha
                elif pct <= 25:
                    buckets["Low Cover (1–25%)"] += ha
                elif pct <= 50:
                    buckets["Medium Cover (26–50%)"] += ha
                elif pct <= 75:
                    buckets["High Cover (51–75%)"] += ha
                else:
                    buckets["Very High Cover (76–100%)"] += ha
            return [
                {
                    "Category": cat,
                    "Area_ha": round(ha, 1),
                    "Percentage": f"{ha / total_ha * 100:.1f}%" if total_ha > 0 else "0%",
                }
                for cat, ha in buckets.items()
                if ha > 0
            ]
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_bar_chart(self) -> Figure:
        try:
            if not self.geometry_gfc_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.geometry_gfc_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"GFC bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["geometry_gfc_result"])
    def gfc_loss_chart(self) -> Figure:
        """Bar chart of tree loss area by year."""
        try:
            rows = self.gfc_loss_by_year
            if not rows:
                return pgo.Figure()
            years = [r["Year"] for r in rows]
            areas = [r["Area_ha"] for r in rows]
            fig = pgo.Figure(data=[
                pgo.Bar(
                    x=years, y=areas,
                    marker_color="#e74c3c",
                    text=[f"{a:,.0f} ha" for a in areas],
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>",
                )
            ])
            fig.update_layout(
                title="Annual Tree Loss (2001–2023)",
                xaxis_title="Year", yaxis_title="Loss Area (ha)",
                template="plotly_white", height=350, showlegend=False,
            )
            return fig
        except Exception as e:
            logger.error(f"GFC loss chart error: {e}")
            return pgo.Figure()

    # ---- GLAD-specific computed vars (read from geometry_glad_result) ---

    @rx.var(auto_deps=False, deps=["geometry_glad_result"])
    def glad_bar_chart(self) -> Figure:
        try:
            if not self.geometry_glad_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.geometry_glad_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"GLAD bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["geometry_glad_result"])
    def glad_table_data(self) -> List[Dict[str, Any]]:
        try:
            return (self.geometry_glad_result or {}).get("data", [])
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["geometry_glad_result"])
    def glad_summary_area(self) -> str:
        try:
            val = (self.geometry_glad_result or {}).get("summary", {}).get("total_area_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_glad_result"])
    def glad_summary_classes(self) -> str:
        try:
            val = (self.geometry_glad_result or {}).get("summary", {}).get("num_classes", 0)
            return str(val) if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["geometry_glad_result"])
    def glad_summary_year(self) -> str:
        try:
            val = (self.geometry_glad_result or {}).get("summary", {}).get("year", "")
            return str(val) if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_balance_chart(self) -> Figure:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.hansen_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"Hansen chart error: {e}")
            return pgo.Figure()

    # ---- Analysis info text --------------------------------------------

    @rx.var(auto_deps=False, deps=["analysis_results", "selected_territory", "territory_analysis_year"])
    def analysis_info_text(self) -> str:
        if not self.analysis_results:
            return ""
        analysis_type = self.analysis_results.get("type", "Unknown")
        year = self.analysis_results.get("year") or self.analysis_results.get("summary", {}).get("year")
        territory = self.selected_territory
        if territory and year:
            return f"📍 {territory} • {analysis_type.upper()} {year}"
        elif territory:
            return f"📍 {territory}"
        return ""

    # ---- Multi-result helpers ------------------------------------------

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_available(self) -> bool:
        return self.mapbiomas_comparison_result is not None and bool(self.mapbiomas_comparison_result)

    @rx.var(auto_deps=False, deps=["result_keys_list"])
    def result_tab_labels(self) -> List[str]:
        labels = []
        for key in self.result_keys_list:
            if "::" in key:
                prefix, name = key.split("::", 1)
                labels.append(name if prefix == "territory" else f"Geom {name}")
            else:
                labels.append(key)
        return labels

    # ---- Year string helpers for UI binding ----------------------------

    @rx.var(auto_deps=False, deps=["comparison_year1"])
    def comparison_year1_str(self) -> str:
        return str(self.comparison_year1)

    @rx.var(auto_deps=False, deps=["comparison_year2"])
    def comparison_year2_str(self) -> str:
        return str(self.comparison_year2)

    @rx.var(auto_deps=False, deps=["mapbiomas_current_year"])
    def mapbiomas_current_year_str(self) -> str:
        return str(self.mapbiomas_current_year) if self.mapbiomas_current_year > 0 else "2024"

    @rx.var(auto_deps=False, deps=["geometry_analysis_year"])
    def geometry_analysis_year_str(self) -> str:
        return str(self.geometry_analysis_year) if self.geometry_analysis_year else "2024"

    # ---- Comparison charts ---------------------------------------------

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_chart(self) -> Figure:
        try:
            if not self.mapbiomas_comparison_result:
                return pgo.Figure()
            import pandas as pd

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Area_Year1" in df.columns and "Area_Year2" in df.columns:
                name_col = next((c for c in ["Class_Name", "Class"] if c in df.columns), "Class_ID")
                fig = pgo.Figure(data=[
                    pgo.Bar(name=str(year1), x=df[name_col], y=df["Area_Year1"]),
                    pgo.Bar(name=str(year2), x=df[name_col], y=df["Area_Year2"]),
                ])
                fig.update_layout(
                    title=f"Comparison: {year1} vs {year2}",
                    barmode="group", template="plotly_white", height=400,
                )
                return fig
            return pgo.Figure()
        except Exception as e:
            logger.error(f"Comparison chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def gains_losses_chart(self) -> Figure:
        try:
            if not self.mapbiomas_comparison_result:
                return pgo.Figure()
            from ..utils.visualization import create_gains_losses_chart
            import pandas as pd

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Change_km2" not in df.columns and "Change_ha" in df.columns:
                df["Change_km2"] = df["Change_ha"] / 100
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_gains_losses_chart(df, year1, year2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Gains/losses chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def change_pct_chart(self) -> Figure:
        try:
            if not self.mapbiomas_comparison_result:
                return pgo.Figure()
            from ..utils.visualization import create_change_percentage_chart
            import pandas as pd

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_change_percentage_chart(df, year1, year2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Change pct chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_total_gains(self) -> str:
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd

            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                val = df[df["Change_km2"] > 0]["Change_km2"].sum()
                return f"{val:,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_total_losses(self) -> str:
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd

            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                val = abs(df[df["Change_km2"] < 0]["Change_km2"].sum())
                return f"{val:,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_net_change(self) -> str:
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd

            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                val = df["Change_km2"].sum()
                return f"{val:+,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    # ---- Territory year-2 summary (used by Compare tab buffer panel) ----

    @rx.var(auto_deps=False, deps=["territory_result_year2"])
    def territory_year2_area(self) -> str:
        """Formatted area string for territory analysis year 2."""
        try:
            if not self.territory_result_year2:
                return "…"
            ha = self.territory_result_year2.get("summary", {}).get("total_area_ha", 0)
            return f"{float(ha):,.0f} ha"
        except Exception:
            return "…"

    @rx.var(auto_deps=False, deps=["territory_result_year2"])
    def territory_year2_classes(self) -> str:
        """Number of classes for territory analysis year 2."""
        try:
            if not self.territory_result_year2:
                return "0"
            n = self.territory_result_year2.get("summary", {}).get("num_classes", 0)
            return str(n) + " classes"
        except Exception:
            return "0 classes"

    # ---- Transition charts ---------------------------------------------

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def sankey_chart(self) -> Figure:
        try:
            transitions = self.territory_transitions
            logger.info(f"sankey_chart: territory_transitions has {len(transitions) if transitions else 0} sources")
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
                logger.info(f"sankey_chart: got transitions from comparison_result, {len(transitions) if transitions else 0} sources")
            if not transitions:
                logger.warning(f"sankey_chart: no transitions found in either territory or comparison")
                return pgo.Figure()

            year1 = self.mapbiomas_comparison_result.get("year_start", self.comparison_year1) \
                if self.mapbiomas_comparison_result else self.comparison_year1
            year2 = self.mapbiomas_comparison_result.get("year_end", self.comparison_year2) \
                if self.mapbiomas_comparison_result else self.comparison_year2

            logger.info(f"sankey_chart: calling create_sankey_transitions({len(transitions)} sources, {year1}->{year2})")
            from ..utils.visualization import create_sankey_transitions

            result = create_sankey_transitions(transitions, year1, year2)
            logger.info(f"sankey_chart: create_sankey_transitions returned {type(result).__name__}")
            return result or pgo.Figure()
        except Exception as e:
            logger.error(f"Sankey chart error: {e}", exc_info=True)
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def sunburst_transitions_chart(self) -> Figure:
        """Sunburst (rings) chart showing class transitions between years."""
        try:
            transitions = self.territory_transitions
            logger.info(f"sunburst_transitions_chart: territory_transitions has {len(transitions) if transitions else 0} sources")
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
                logger.info(f"sunburst_transitions_chart: got transitions from comparison_result, {len(transitions) if transitions else 0} sources")
            if not transitions:
                logger.warning(f"sunburst_transitions_chart: no transitions found in either territory or comparison")
                return pgo.Figure()

            year1 = self.mapbiomas_comparison_result.get("year_start", self.comparison_year1) \
                if self.mapbiomas_comparison_result else self.comparison_year1
            year2 = self.mapbiomas_comparison_result.get("year_end", self.comparison_year2) \
                if self.mapbiomas_comparison_result else self.comparison_year2

            logger.info(f"sunburst_transitions_chart: calling create_sunburst_transitions({len(transitions)} sources, {year1}->{year2})")
            from ..utils.visualization import create_sunburst_transitions

            result = create_sunburst_transitions(transitions, year1, year2)
            logger.info(f"sunburst_transitions_chart: create_sunburst_transitions returned {type(result).__name__}")
            return result or pgo.Figure()
        except Exception as e:
            logger.error(f"Sunburst chart error: {e}", exc_info=True)
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def treemap_transitions_chart(self) -> Figure:
        """Faceted per-class transition treemaps (whole comparison period)."""
        try:
            transitions = self.territory_transitions
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
            if not transitions:
                return pgo.Figure()

            year1 = self.mapbiomas_comparison_result.get("year_start", self.comparison_year1) \
                if self.mapbiomas_comparison_result else self.comparison_year1
            year2 = self.mapbiomas_comparison_result.get("year_end", self.comparison_year2) \
                if self.mapbiomas_comparison_result else self.comparison_year2

            from ..utils.visualization import create_class_transition_treemaps

            return create_class_transition_treemaps(transitions, year1, year2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Treemap chart error: {e}", exc_info=True)
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def transition_matrix_chart(self) -> Figure:
        try:
            transitions = self.territory_transitions
            logger.info(f"transition_matrix_chart: territory_transitions has {len(transitions) if transitions else 0} sources")
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
                logger.info(f"transition_matrix_chart: got transitions from comparison_result, {len(transitions) if transitions else 0} sources")
            if not transitions:
                logger.warning(f"transition_matrix_chart: no transitions found")
                return pgo.Figure()

            all_classes: set = set()
            for src, tgt_dict in transitions.items():
                if isinstance(tgt_dict, dict):
                    all_classes.add(str(src))
                    all_classes.update(str(t) for t in tgt_dict)
            classes = sorted(all_classes)
            logger.info(f"transition_matrix_chart: found {len(classes)} classes: {classes[:5]}...")
            if not classes:
                logger.warning(f"transition_matrix_chart: no valid classes after processing")
                return pgo.Figure()

            try:
                from ..utils.visualization import _get_mapbiomas_labels

                labels = _get_mapbiomas_labels()
            except Exception:
                labels = {}

            display_names = []
            for c in classes:
                try:
                    display_names.append(labels.get(int(c), c))
                except (ValueError, TypeError):
                    display_names.append(labels.get(c, c))

            matrix = []
            for src in classes:
                row = []
                for tgt in classes:
                    src_dict = transitions.get(
                        src, transitions.get(int(src) if src.isdigit() else src, {})
                    )
                    if isinstance(src_dict, dict):
                        val = src_dict.get(tgt, src_dict.get(int(tgt) if tgt.isdigit() else tgt, 0))
                    else:
                        val = 0
                    row.append(float(val) if isinstance(val, (int, float)) else 0)
                matrix.append(row)

            year1 = self.mapbiomas_comparison_result.get("year_start", self.comparison_year1) \
                if self.mapbiomas_comparison_result else self.comparison_year1
            year2 = self.mapbiomas_comparison_result.get("year_end", self.comparison_year2) \
                if self.mapbiomas_comparison_result else self.comparison_year2

            fig = pgo.Figure(
                data=pgo.Heatmap(
                    z=matrix,
                    x=display_names,
                    y=display_names,
                    colorscale="YlOrRd",
                    text=[[f"{v:,.0f}" for v in row] for row in matrix],
                    texttemplate="%{text}",
                    hovertemplate="From: %{y}<br>To: %{x}<br>Area: %{z:,.0f} ha<extra></extra>",
                )
            )
            fig.update_layout(
                title=f"Transition Matrix ({year1} to {year2}) - Area (ha)",
                xaxis_title=f"Class ({year2})",
                yaxis_title=f"Class ({year1})",
                height=600,
                template="plotly_white",
            )
            logger.info(f"transition_matrix_chart: successfully created matrix with {len(classes)}x{len(classes)} cells")
            return fig
        except Exception as e:
            logger.error(f"Transition matrix error: {e}", exc_info=True)
            return pgo.Figure()

    # ---- Advanced viz: multi-window Sankey (ports batch visuals) --------

    @rx.var(auto_deps=False, deps=["mw_result"])
    def multi_window_sankey_chart(self) -> Figure:
        """Multi-stage Sankey across the resolved multi-window years."""
        return self._build_multi_window_sankey(self.mw_result)

    @rx.var(auto_deps=False, deps=["buffer_mw_result"])
    def buffer_multi_window_sankey_chart(self) -> Figure:
        """Multi-stage Sankey for the external buffer ring."""
        return self._build_multi_window_sankey(self.buffer_mw_result)

    def _build_multi_window_sankey(self, mw_result) -> Figure:
        try:
            pairs = (mw_result or {}).get("pairs") or []
            if not pairs:
                return pgo.Figure()
            from ..utils.visualization import create_multi_stage_sankey
            stages = [
                (p["year_from"], p["year_to"], p.get("transitions") or {})
                for p in pairs
            ]
            return create_multi_stage_sankey(stages) or pgo.Figure()
        except Exception as e:
            logger.error(f"multi_window_sankey_chart error: {e}", exc_info=True)
            return pgo.Figure()

    # ---- Advanced viz: deforestation timeline (Hansen + MapBiomas + Fire)

    @rx.var(auto_deps=False, deps=["timeline_series", "timeline_state_code"])
    def timeline_raw_chart(self) -> Figure:
        return self._build_timeline_chart(self.timeline_series, "raw")

    @rx.var(auto_deps=False, deps=["timeline_series", "timeline_state_code"])
    def timeline_ma_chart(self) -> Figure:
        return self._build_timeline_chart(self.timeline_series, "moving_avg")

    @rx.var(auto_deps=False, deps=["timeline_series", "timeline_state_code"])
    def timeline_deriv_chart(self) -> Figure:
        return self._build_timeline_chart(self.timeline_series, "derivatives")

    @rx.var(auto_deps=False, deps=["buffer_timeline_series", "timeline_state_code"])
    def buffer_timeline_raw_chart(self) -> Figure:
        return self._build_timeline_chart(self.buffer_timeline_series, "raw")

    @rx.var(auto_deps=False, deps=["buffer_timeline_series", "timeline_state_code"])
    def buffer_timeline_ma_chart(self) -> Figure:
        return self._build_timeline_chart(self.buffer_timeline_series, "moving_avg")

    @rx.var(auto_deps=False, deps=["buffer_timeline_series", "timeline_state_code"])
    def buffer_timeline_deriv_chart(self) -> Figure:
        return self._build_timeline_chart(self.buffer_timeline_series, "derivatives")

    def _build_timeline_chart(self, series, variant: str) -> Figure:
        try:
            if not series:
                return pgo.Figure()
            from ..utils.visualization import create_deforestation_timeline_chart
            fig = create_deforestation_timeline_chart(
                series,
                state_code=self.timeline_state_code or None,
                year_start=self.timeline_year_start or self.comparison_year1,
                year_end=self.timeline_year_end or self.comparison_year2,
                variant=variant,
                moving_window=5,
                title_suffix=self.timeline_territory_name,
                territory_name=self.timeline_territory_name,
                territory_type=self.timeline_territory_type or "indigenous",
            )
            if fig is not None:
                # Render full container width interactively (the figure ships a
                # fixed height but no width → Plotly would default to ~700px).
                fig.update_layout(autosize=True, width=None)
            return fig or pgo.Figure()
        except Exception as e:
            logger.error(f"timeline chart ({variant}) error: {e}", exc_info=True)
            return pgo.Figure()

    # ---- Buffer comparison computed vars --------------------------------

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_result"])
    def buffer_mapbiomas_bar_chart(self) -> Figure:
        """Bar chart for the buffer MapBiomas result."""
        try:
            if not self.buffer_mapbiomas_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.buffer_mapbiomas_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer MapBiomas bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_result"])
    def buffer_mapbiomas_summary(self) -> Dict[str, str]:
        """Summary stats for the buffer MapBiomas analysis."""
        try:
            if not self.buffer_mapbiomas_result:
                return {}
            s = self.buffer_mapbiomas_result.get("summary", {})
            return {
                "area": f"{s.get('total_area_ha', 0):,.0f} ha",
                "classes": str(s.get("classes", 0)),
                "year": str(self.buffer_mapbiomas_result.get("year", "")),
                "name": self.buffer_mapbiomas_result.get("territory", "Buffer"),
            }
        except Exception:
            return {}

    @rx.var(auto_deps=False, deps=["buffer_hansen_result"])
    def buffer_hansen_bar_chart(self) -> Figure:
        """Bar chart for the buffer Hansen GLAD result."""
        try:
            if not self.buffer_hansen_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.buffer_hansen_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer Hansen bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_hansen_result"])
    def buffer_hansen_summary(self) -> Dict[str, str]:
        """Summary stats for the buffer Hansen GLAD analysis."""
        try:
            if not self.buffer_hansen_result:
                return {}
            s = self.buffer_hansen_result.get("summary", {})
            return {
                "area": f"{s.get('total_area_ha', 0):,.0f} ha",
                "classes": str(s.get("num_classes", 0)),
                "year": str(s.get("year", "")),
                "name": self.buffer_hansen_result.get("geometry_name", "Buffer"),
            }
        except Exception:
            return {}

    # ── Buffer Comparison (year-over-year Compare tab) ─────────────────────

    @rx.var(auto_deps=False, deps=["buffer_compare_result"])
    def buffer_compare_bar_chart(self) -> Figure:
        """Bar chart for the buffer comparison year-2 result."""
        try:
            if not self.buffer_compare_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.buffer_compare_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer compare bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_compare_result"])
    def buffer_compare_summary(self) -> Dict[str, str]:
        """Summary stats for the buffer comparison result."""
        try:
            if not self.buffer_compare_result:
                return {}
            s = self.buffer_compare_result.get("summary", {})
            return {
                "area": f"{s.get('total_area_ha', 0):,.0f} ha",
                "classes": str(s.get("classes", 0)),
                "year": str(self.buffer_compare_result.get("year", "")),
                "name": self.buffer_compare_result.get("territory", "Buffer"),
            }
        except Exception:
            return {}

    # ── Buffer GFC ─────────────────────────────────────────────────────────

    @rx.var(auto_deps=False, deps=["buffer_gfc_result"])
    def buffer_gfc_bar_chart(self) -> Figure:
        """Bar chart for the buffer Hansen GFC result."""
        try:
            if not self.buffer_gfc_result:
                return pgo.Figure()
            from ..utils.visualization import get_chart_for_analysis
            return get_chart_for_analysis(self.buffer_gfc_result, chart_type="bar") or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer GFC bar chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_gfc_result"])
    def buffer_gfc_summary(self) -> Dict[str, str]:
        """Summary stats for the buffer GFC analysis."""
        try:
            if not self.buffer_gfc_result:
                return {}
            s = self.buffer_gfc_result.get("summary", {})
            cover = s.get("tree_cover_2000_ha", 0)
            loss = s.get("forest_loss_ha", 0)
            gain = s.get("forest_gain_ha", 0)
            return {
                "cover": f"{cover:,.0f} ha",
                "loss": f"{loss:,.0f} ha",
                "gain": f"{gain:,.0f} ha",
                "name": self.buffer_gfc_result.get("geometry_name", "Buffer"),
            }
        except Exception:
            return {}

    # ── Buffer MapBiomas comparison charts (year1 vs year2 in the buffer ring) ─

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_compare_gains_losses_chart(self) -> Figure:
        """Gains/losses chart for the buffer ring (year1 → year2)."""
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return pgo.Figure()
            from ..utils.visualization import create_gains_losses_chart
            import pandas as pd
            data = self.buffer_mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            y1 = self.buffer_mapbiomas_comparison_result.get("year_start", 0)
            y2 = self.buffer_mapbiomas_comparison_result.get("year_end", 0)
            if "Change_km2" not in df.columns and "Change_ha" in df.columns:
                df["Change_km2"] = df["Change_ha"] / 100
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_gains_losses_chart(df, y1, y2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer compare gains/losses chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_compare_change_pct_chart(self) -> Figure:
        """Percentage-change chart for the buffer ring (year1 → year2)."""
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return pgo.Figure()
            from ..utils.visualization import create_change_percentage_chart
            import pandas as pd
            data = self.buffer_mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            y1 = self.buffer_mapbiomas_comparison_result.get("year_start", 0)
            y2 = self.buffer_mapbiomas_comparison_result.get("year_end", 0)
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_change_percentage_chart(df, y1, y2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer compare pct chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_compare_total_gains(self) -> str:
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.buffer_mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                return f"{df[df['Change_km2'] > 0]['Change_km2'].sum():,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_compare_total_losses(self) -> str:
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.buffer_mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                return f"{abs(df[df['Change_km2'] < 0]['Change_km2'].sum()):,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_compare_net_change(self) -> str:
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.buffer_mapbiomas_comparison_result.get("data", []))
            if "Change_km2" in df.columns:
                return f"{df['Change_km2'].sum():+,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["buffer_mapbiomas_comparison_result"])
    def buffer_comparison_chart(self) -> Figure:
        """Grouped bar chart (year1 vs year2) for the buffer ring — mirrors comparison_chart."""
        try:
            if not self.buffer_mapbiomas_comparison_result:
                return pgo.Figure()
            import pandas as pd

            data = self.buffer_mapbiomas_comparison_result.get("data", [])
            if not data:
                return pgo.Figure()
            df = pd.DataFrame(data)
            y1 = self.buffer_mapbiomas_comparison_result.get("year_start", 0)
            y2 = self.buffer_mapbiomas_comparison_result.get("year_end", 0)
            if "Area_Year1" in df.columns and "Area_Year2" in df.columns:
                name_col = next(
                    (c for c in ["Class_Name", "Class"] if c in df.columns), "Class_ID"
                )
                fig = pgo.Figure(data=[
                    pgo.Bar(name=str(y1), x=df[name_col], y=df["Area_Year1"],
                            marker_color="#FB923C"),
                    pgo.Bar(name=str(y2), x=df[name_col], y=df["Area_Year2"],
                            marker_color="#3B82F6"),
                ])
                fig.update_layout(
                    title=f"Buffer: {y1} vs {y2}",
                    barmode="group", template="plotly_white", height=400,
                )
                return fig
            return pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer comparison chart error: {e}")
            return pgo.Figure()

    # ── Buffer GFC — loss-by-year chart and table ───────────────────────────

    @rx.var(auto_deps=False, deps=["buffer_gfc_result"])
    def buffer_gfc_loss_by_year(self) -> List[Dict[str, Any]]:
        """Tree-loss rows for the buffer ring, sorted by year."""
        try:
            records = [
                r for r in (self.buffer_gfc_result or {}).get("tree_loss_data", [])
                if r.get("Year_Code", 0) > 0
            ]
            return sorted(records, key=lambda r: r["Year_Code"])
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["buffer_gfc_result"])
    def buffer_gfc_loss_chart(self) -> Figure:
        """Annual tree-loss bar chart for the buffer ring."""
        try:
            rows = self.buffer_gfc_loss_by_year
            if not rows:
                return pgo.Figure()
            years = [r["Year"] for r in rows]
            areas = [r["Area_ha"] for r in rows]
            fig = pgo.Figure(data=[
                pgo.Bar(
                    x=years, y=areas,
                    marker_color="#3B82F6",
                    text=[f"{a:,.0f} ha" for a in areas],
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>",
                )
            ])
            fig.update_layout(
                title="Buffer: Annual Tree Loss",
                xaxis_title="Year", yaxis_title="Loss Area (ha)",
                template="plotly_white", height=350, showlegend=False,
            )
            return fig
        except Exception as e:
            logger.error(f"Buffer GFC loss chart error: {e}")
            return pgo.Figure()

    # ── Buffer Hansen GLAD — class distribution table ───────────────────────

    @rx.var(auto_deps=False, deps=["buffer_hansen_result"])
    def buffer_glad_table_data(self) -> List[Dict[str, Any]]:
        """Class distribution rows for the buffer Hansen GLAD result."""
        try:
            return (self.buffer_hansen_result or {}).get("data", [])
        except Exception:
            return []

    # ── Buffer transition charts (Sankey / Sunburst / Matrix) ──────────────

    @rx.var(auto_deps=False, deps=["buffer_territory_transitions", "buffer_mapbiomas_comparison_result"])
    def buffer_sankey_chart(self) -> Figure:
        """Sankey transition chart for the buffer ring — mirrors sankey_chart."""
        try:
            transitions = self.buffer_territory_transitions
            if not transitions:
                return pgo.Figure()
            y1 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_start", self.comparison_year1
            )
            y2 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_end", self.comparison_year2
            )
            from ..utils.visualization import create_sankey_transitions
            return create_sankey_transitions(transitions, y1, y2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer Sankey chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_territory_transitions", "buffer_mapbiomas_comparison_result"])
    def buffer_sunburst_chart(self) -> Figure:
        """Sunburst transition chart for the buffer ring — mirrors sunburst_transitions_chart."""
        try:
            transitions = self.buffer_territory_transitions
            if not transitions:
                return pgo.Figure()
            y1 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_start", self.comparison_year1
            )
            y2 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_end", self.comparison_year2
            )
            from ..utils.visualization import create_sunburst_transitions
            return create_sunburst_transitions(transitions, y1, y2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer Sunburst chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_territory_transitions", "buffer_mapbiomas_comparison_result"])
    def buffer_treemap_chart(self) -> Figure:
        """Faceted per-class transition treemaps for the buffer ring."""
        try:
            transitions = self.buffer_territory_transitions
            if not transitions:
                return pgo.Figure()
            y1 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_start", self.comparison_year1
            )
            y2 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_end", self.comparison_year2
            )
            from ..utils.visualization import create_class_transition_treemaps
            return create_class_transition_treemaps(transitions, y1, y2) or pgo.Figure()
        except Exception as e:
            logger.error(f"Buffer treemap chart error: {e}")
            return pgo.Figure()

    @rx.var(auto_deps=False, deps=["buffer_territory_transitions", "buffer_mapbiomas_comparison_result"])
    def buffer_transition_matrix_chart(self) -> Figure:
        """Transition matrix heatmap for the buffer ring — mirrors transition_matrix_chart."""
        try:
            transitions = self.buffer_territory_transitions
            if not transitions:
                return pgo.Figure()
            all_classes: set = set()
            for src, tgt_dict in transitions.items():
                if isinstance(tgt_dict, dict):
                    all_classes.add(str(src))
                    all_classes.update(str(t) for t in tgt_dict)
            classes = sorted(all_classes)
            if not classes:
                return pgo.Figure()
            try:
                from ..utils.visualization import _get_mapbiomas_labels
                labels = _get_mapbiomas_labels()
            except Exception:
                labels = {}
            display_names = []
            for c in classes:
                try:
                    display_names.append(labels.get(int(c), c))
                except (ValueError, TypeError):
                    display_names.append(labels.get(c, c))
            matrix = []
            for src in classes:
                row = []
                for tgt in classes:
                    src_dict = transitions.get(
                        src, transitions.get(int(src) if str(src).isdigit() else src, {})
                    )
                    if isinstance(src_dict, dict):
                        val = src_dict.get(
                            tgt, src_dict.get(int(tgt) if str(tgt).isdigit() else tgt, 0)
                        )
                    else:
                        val = 0
                    row.append(float(val) if isinstance(val, (int, float)) else 0)
                matrix.append(row)
            y1 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_start", self.comparison_year1
            )
            y2 = (self.buffer_mapbiomas_comparison_result or {}).get(
                "year_end", self.comparison_year2
            )
            fig = pgo.Figure(
                data=pgo.Heatmap(
                    z=matrix, x=display_names, y=display_names,
                    colorscale="Blues",
                    text=[[f"{v:,.0f}" for v in row] for row in matrix],
                    texttemplate="%{text}",
                    hovertemplate="From: %{y}<br>To: %{x}<br>Area: %{z:,.0f} ha<extra></extra>",
                )
            )
            fig.update_layout(
                title=f"Buffer Transition Matrix ({y1} → {y2}) — Area (ha)",
                xaxis_title=f"Class ({y2})",
                yaxis_title=f"Class ({y1})",
                height=600, template="plotly_white",
            )
            return fig
        except Exception as e:
            logger.error(f"Buffer transition matrix error: {e}")
            return pgo.Figure()
