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
from plotly.graph_objs import Figure

# BufferGeometry lives in _geometry.py so it's available without circular imports
from ._geometry import BufferGeometry, GeometryMixin
from ._ui import UIMixin
from ._map import MapMixin
from ._territory import TerritoryMixin
from ._analysis import AnalysisMixin
from ._export import ExportMixin

logger = logging.getLogger(__name__)


class AppState(
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
    mapbiomas_current_year: int = 2023
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
    buffer_geometries: Dict[str, BufferGeometry] = {}
    current_buffer_for_analysis: Optional[str] = None
    buffer_compare_mode: bool = False

    # Per-geometry analysis cache
    geometry_analysis_results: Dict[int, Dict[str, Any]] = {}
    geometry_analysis_type: str = "mapbiomas"   # "mapbiomas" | "hansen"
    geometry_analysis_year: Union[int, str] = 2023
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

    # Multi-result store  key → bundle
    # Key format: "territory::Xingu" or "geometry::0"
    all_analysis_results: Dict[str, Dict[str, Any]] = {}
    active_result_key: str = ""
    result_keys_list: List[str] = []

    # Territory display info
    territory_analysis_year: int = 2023
    territory_geometry_displayed: bool = False
    territory_geojson_features: List[Dict[str, Any]] = []

    # Indigenous lands
    indigenous_lands_tile_url: str = ""
    show_indigenous_lands: bool = True
    territory_name_property: str = "name"

    # Comparison year selection
    comparison_year1: int = 2018
    comparison_year2: int = 2023

    # Territory analysis storage
    territory_result: Optional[Dict[str, Any]] = None
    territory_result_year2: Optional[Dict[str, Any]] = None
    territory_name: str = ""
    territory_year: int = 2023
    territory_year2: Optional[int] = None
    territory_source: str = "MapBiomas"
    territory_transitions: Optional[Dict[str, Any]] = None

    # ====================================================================
    # Map overlay state
    # ====================================================================
    show_geometries_on_map: bool = True
    show_change_mask: bool = False
    change_mask_year1: int = 2018
    change_mask_year2: int = 2023
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
    sidebar_open: bool = True
    sidebar_width: int = 300
    is_resizing_sidebar: bool = False
    show_tutorial: bool = False
    tutorial_expanded_steps: List[int] = []
    show_layer_reference: bool = False
    use_consolidated_classes: bool = True
    buffer_distance_input: str = ""

    # Sidebar section expansion
    sidebar_mapbiomas_expanded: bool = False
    sidebar_hansen_expanded: bool = False
    sidebar_territory_expanded: bool = False
    sidebar_geometry_expanded: bool = False

    # Pending territory confirmation
    pending_territory: Optional[str] = None

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
            "territory_geojson_features", "indigenous_lands_tile_url",
            "show_indigenous_lands", "analysis_tile_layers",
        ],
    )
    def map_html(self) -> str:
        """
        Full Folium/Leaflet HTML for the map panel.
        Rebuilt whenever layer selection, geometry overlays, or tile URLs change.
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

            il_tile_url = self.indigenous_lands_tile_url if self.show_indigenous_lands else None

            return build_map(
                mapbiomas_years=self.mapbiomas_displayed_years or [],
                hansen_layers=self.hansen_displayed_layers or [],
                geometry_features=geom_features,
                change_mask_years=change_years,
                change_mask_geometry=change_geom,
                indigenous_lands_tile_url=il_tile_url,
                territory_names=self.available_territories if il_tile_url else None,
                analysis_tile_layers=self.analysis_tile_layers or [],
            )

        except Exception as e:
            logger.error(f"Error generating map HTML: {e}", exc_info=True)
            import folium

            m = folium.Map(location=[-10, -52], zoom_start=5, tiles="OpenStreetMap")
            folium.LayerControl().add_to(m)
            return m._repr_html_()

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
        if isinstance(coords[0], (int, float)):
            return f"[{coords[0]:.4f}, {coords[1]:.4f}]"
        return f"[{coords[0][0]:.4f}, ...] ({len(coords)} points)"

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
    def mapbiomas_bar_chart(self) -> Optional[Figure]:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.mapbiomas_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="bar") or None
        except Exception as e:
            logger.error(f"MapBiomas bar chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def mapbiomas_pie_chart(self) -> Optional[Figure]:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.mapbiomas_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="pie") or None
        except Exception as e:
            logger.error(f"MapBiomas pie chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_balance_chart(self) -> Optional[Figure]:
        try:
            from ..utils.visualization import get_chart_for_analysis

            result = self.hansen_analysis_result or self.analysis_results
            return get_chart_for_analysis(result, chart_type="bar") or None
        except Exception as e:
            logger.error(f"Hansen chart error: {e}")
            return None

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
        return str(self.mapbiomas_current_year) if self.mapbiomas_current_year > 0 else "2023"

    @rx.var(auto_deps=False, deps=["geometry_analysis_year"])
    def geometry_analysis_year_str(self) -> str:
        return str(self.geometry_analysis_year) if self.geometry_analysis_year else "2023"

    # ---- Comparison charts ---------------------------------------------

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_chart(self) -> Optional[Figure]:
        try:
            if not self.mapbiomas_comparison_result:
                return None
            import pandas as pd
            import plotly.graph_objects as go

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Area_Year1" in df.columns and "Area_Year2" in df.columns:
                name_col = next((c for c in ["Class_Name", "Class"] if c in df.columns), "Class_ID")
                fig = go.Figure(data=[
                    go.Bar(name=str(year1), x=df[name_col], y=df["Area_Year1"]),
                    go.Bar(name=str(year2), x=df[name_col], y=df["Area_Year2"]),
                ])
                fig.update_layout(
                    title=f"Comparison: {year1} vs {year2}",
                    barmode="group", template="plotly_white", height=400,
                )
                return fig
            return None
        except Exception as e:
            logger.error(f"Comparison chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def gains_losses_chart(self) -> Optional[Figure]:
        try:
            if not self.mapbiomas_comparison_result:
                return None
            from ..utils.visualization import create_gains_losses_chart
            import pandas as pd

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Change_km2" not in df.columns and "Change_ha" in df.columns:
                df["Change_km2"] = df["Change_ha"] / 100
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_gains_losses_chart(df, year1, year2) or None
        except Exception as e:
            logger.error(f"Gains/losses chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def change_pct_chart(self) -> Optional[Figure]:
        try:
            if not self.mapbiomas_comparison_result:
                return None
            from ..utils.visualization import create_change_percentage_chart
            import pandas as pd

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if "Abs_Change" not in df.columns:
                df["Abs_Change"] = df.get("Change_ha", df.get("Change_km2", 0)).abs()
            return create_change_percentage_chart(df, year1, year2) or None
        except Exception as e:
            logger.error(f"Change pct chart error: {e}")
            return None

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

    # ---- Transition charts ---------------------------------------------

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def sankey_chart(self) -> Optional[Figure]:
        try:
            transitions = self.territory_transitions
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
            if not transitions:
                return None

            year1 = self.mapbiomas_comparison_result.get("year_start", self.comparison_year1) \
                if self.mapbiomas_comparison_result else self.comparison_year1
            year2 = self.mapbiomas_comparison_result.get("year_end", self.comparison_year2) \
                if self.mapbiomas_comparison_result else self.comparison_year2

            from ..utils.visualization import create_sankey_transitions

            return create_sankey_transitions(transitions, year1, year2) or None
        except Exception as e:
            logger.error(f"Sankey chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def transition_matrix_chart(self) -> Optional[Figure]:
        try:
            transitions = self.territory_transitions
            if not transitions and self.mapbiomas_comparison_result:
                transitions = self.mapbiomas_comparison_result.get("transitions")
            if not transitions:
                return None

            import plotly.graph_objects as pgo

            all_classes: set = set()
            for src, tgt_dict in transitions.items():
                if isinstance(tgt_dict, dict):
                    all_classes.add(str(src))
                    all_classes.update(str(t) for t in tgt_dict)
            classes = sorted(all_classes)
            if not classes:
                return None

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
            return fig
        except Exception as e:
            logger.error(f"Transition matrix error: {e}")
            return None
