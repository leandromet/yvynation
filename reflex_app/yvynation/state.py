"""
Global state management for Yvynation Reflex app.
Reactive state eliminates Streamlit reruns for better performance.
"""

import reflex as rx
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import ee
import logging
from plotly.graph_objs import Figure

logger = logging.getLogger(__name__)


@dataclass
class BufferGeometry:
    """Represents a buffer geometry for analysis."""
    name: str
    geometry: Dict[str, Any]
    created_at: str
    metadata: Dict[str, Any]


class AppState(rx.State):
    """Global application state with reactive updates (no full-page reruns)."""
    
    # Track state update calls for debugging
    _selection_call_count: int = 0
    _selection_timestamp: float = 0.0
    
    # Initialization & Data Loading
    data_loaded: bool = True
    ee_initialized: bool = False
    loading_message: str = ""
    error_message: str = ""
    
    # Language & Preferences
    language: str = "en"  # "en", "pt", "es"
    auto_detect_enabled: bool = True
    
    # Map State
    map_center: tuple = (0.0, 0.0)
    map_zoom: int = 3
    map_bounds: Optional[List] = None
    map_zoom_bounds: Dict[str, float] = {}  # Bounds for territory zoom {'min_lat', 'max_lat', 'min_lon', 'max_lon', 'center_lat', 'center_lon'}
    selected_base_layer: str = "openstreetmap"
    
    # Layer Configuration
    mapbiomas_years_enabled: Dict[int, bool] = {}
    mapbiomas_current_year: int = 2023
    mapbiomas_displayed_years: List[int] = []  # Years currently displayed on map
    
    hansen_years_enabled: Dict[str, bool] = {}
    hansen_current_year: str = "2020"
    hansen_displayed_layers: List[str] = []  # Which Hansen layers shown (loss, gain, cover)
    
    aafc_years_enabled: Dict[int, bool] = {}
    aafc_current_year: int = 2023
    
    # GFC Layers (Global Forest Change)
    show_hansen_gfc_tree_cover: bool = False
    show_hansen_gfc_tree_loss: bool = False
    show_hansen_gfc_tree_gain: bool = False
    
    # Territory & Geometry Selection
    selected_territory: Optional[str] = None
    selected_country: str = "Brazil"
    territory_filter_state: Optional[str] = None  # For state-level filtering
    available_territories: List[str] = []  # Loaded from EE on init
    territory_search_query: str = ""  # For filtering territories
    
    # Drawn Features & Buffers
    drawn_features: List[Dict[str, Any]] = []
    all_drawn_features: List[Dict[str, Any]] = []
    selected_geometry_idx: Optional[int] = None  # Index of selected drawn geometry
    selected_geometry_is_territory: bool = False  # Whether selected geometry is from a territory
    buffer_geometries: Dict[str, BufferGeometry] = {}
    current_buffer_for_analysis: Optional[str] = None
    buffer_compare_mode: bool = False

    # Geometry analysis for drawn features
    geometry_analysis_results: Dict[int, Dict[str, Any]] = {}  # Results by geometry index
    geometry_analysis_type: str = "mapbiomas"  # "mapbiomas" or "hansen"
    geometry_analysis_year: Union[int, str] = 2023  # Year for MapBiomas (int) or Hansen (str "2020")
    geometry_analysis_pending: bool = False

    # Geometry Info Popup
    show_geometry_popup: bool = False  # Show/hide geometry info popup
    geometry_popup_info: Dict[str, Any] = {}  # Info to display in popup
    
    # Analysis Results
    analysis_results: Dict[str, Any] = {}  # Empty dict when no analysis is active
    mapbiomas_analysis_result: Optional[Dict[str, Any]] = None  # Persists MapBiomas results
    hansen_analysis_result: Optional[Dict[str, Any]] = None  # Persists Hansen results
    mapbiomas_comparison_result: Optional[Dict[str, Any]] = None
    hansen_comparison_result: Optional[Dict[str, Any]] = None
    analysis_figures: Dict[str, Any] = {}

    # Multi-result storage: key -> full analysis bundle
    # Key format: "territory::Xingu" or "geometry::0"
    all_analysis_results: Dict[str, Dict[str, Any]] = {}
    active_result_key: str = ""
    result_keys_list: List[str] = []

    # Territory display info
    territory_analysis_year: int = 2023  # Year used for current analysis
    territory_geometry_displayed: bool = False  # Whether territory boundary is on map

    # Territory GeoJSON for map overlay
    territory_geojson_features: List[Dict[str, Any]] = []

    # Indigenous lands base layer (all territories)
    indigenous_lands_tile_url: str = ""
    show_indigenous_lands: bool = True
    territory_name_property: str = "name"  # EE property used for names

    # Comparison year selection
    comparison_year1: int = 2018
    comparison_year2: int = 2023

    # Territory analysis storage (mirrors Streamlit's territory_result etc.)
    territory_result: Optional[Dict[str, Any]] = None
    territory_result_year2: Optional[Dict[str, Any]] = None
    territory_name: str = ""
    territory_year: int = 2023
    territory_year2: Optional[int] = None
    territory_source: str = "MapBiomas"
    territory_transitions: Optional[Dict[str, Any]] = None

    # Map overlay state
    show_geometries_on_map: bool = True  # Whether to overlay drawn features on map
    show_change_mask: bool = False  # Whether to show MapBiomas change mask
    change_mask_year1: int = 2018
    change_mask_year2: int = 2023
    # Incremented to force map rebuild when geometries change
    geometry_version: int = 0

    # Analysis pending/computed flags
    mapbiomas_analysis_pending: bool = False
    hansen_analysis_pending: bool = False
    export_pending: bool = False
    map_export_pending: bool = False
    
    # UI State
    active_tab: str = "map"  # "map", "analysis", "tutorial", "about"
    sidebar_open: bool = True
    sidebar_width: int = 300  # Sidebar width in pixels
    is_resizing_sidebar: bool = False  # Whether currently resizing
    show_tutorial: bool = False
    tutorial_expanded_steps: List[int] = []  # Which tutorial steps are expanded
    use_consolidated_classes: bool = True
    buffer_distance_input: str = ""  # Buffer distance input field
    
    # Sidebar section expansion state
    sidebar_mapbiomas_expanded: bool = False
    sidebar_hansen_expanded: bool = False
    sidebar_territory_expanded: bool = False
    sidebar_geometry_expanded: bool = False
    
    # Pending confirmations (for territory selection)
    pending_territory: Optional[str] = None
    
    # Territory Search & Filtering
    territory_search_query: str = ""
    
    # ========================================================================
    # Computed Properties (Reflex Reactive)
    # ========================================================================

    @rx.var(auto_deps=False, deps=["language"])
    def tr(self) -> Dict[str, str]:
        """Current translations dict, reactive to language changes."""
        from .utils.translations import TRANSLATIONS
        return TRANSLATIONS.get(self.language, TRANSLATIONS["en"])

    @rx.var
    def filtered_territories(self) -> List[str]:
        """Filter territories based on search query (reactive)."""
        if not self.territory_search_query:
            return self.available_territories
        
        query_lower = self.territory_search_query.lower()
        return [
            t for t in self.available_territories 
            if query_lower in t.lower()
        ]
    @rx.var(auto_deps=False, deps=[
        "mapbiomas_displayed_years", "hansen_displayed_layers",
        "geometry_version", "show_geometries_on_map",
        "show_change_mask", "change_mask_year1", "change_mask_year2",
        "territory_geojson_features", "indigenous_lands_tile_url",
        "show_indigenous_lands",
    ])
    def map_html(self) -> str:
        """
        Generate map HTML based on current layer selections, geometry overlays,
        territory overlays, indigenous lands, and optional change mask.
        """
        try:
            from .utils.map_builder import build_map

            # Combine drawn features + territory features for overlay
            all_overlay = []
            if self.show_geometries_on_map and self.drawn_features:
                all_overlay.extend(self.drawn_features)
            if self.territory_geojson_features:
                all_overlay.extend(self.territory_geojson_features)

            geom_features = all_overlay if all_overlay else None

            # Change mask params - use territory or drawn geometry as clip
            change_years = None
            change_geom = None
            if self.show_change_mask:
                change_years = (self.change_mask_year1, self.change_mask_year2)
                if self.territory_geojson_features:
                    change_geom = self.territory_geojson_features[0].get("geometry")
                elif self.drawn_features:
                    change_geom = self.drawn_features[0].get("geometry")

            # Indigenous lands tile URL
            il_tile_url = self.indigenous_lands_tile_url if self.show_indigenous_lands else None

            html = build_map(
                mapbiomas_years=self.mapbiomas_displayed_years or [],
                hansen_layers=self.hansen_displayed_layers or [],
                geometry_features=geom_features,
                change_mask_years=change_years,
                change_mask_geometry=change_geom,
                indigenous_lands_tile_url=il_tile_url,
                territory_names=self.available_territories if il_tile_url else None,
            )
            return html
        except Exception as e:
            logger.error(f"Error generating map HTML: {e}")
            import traceback
            traceback.print_exc()

            # Return basic map on error
            import folium
            m = folium.Map(location=[-10, -52], zoom_start=5, tiles="OpenStreetMap")
            folium.LayerControl().add_to(m)
            return m._repr_html_()
    
    @rx.var
    def selected_geometry_type(self) -> str:
        """Get the type of the selected geometry."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return ""
        
        feature = self.drawn_features[self.selected_geometry_idx]
        return feature.get('type', 'Unknown')
    
    @rx.var
    def selected_geometry_coords_preview(self) -> str:
        """Get a preview of the selected geometry's coordinates."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return ""
        
        feature = self.drawn_features[self.selected_geometry_idx]
        coords = feature.get('coordinates', [])
        
        # Return abbreviated preview
        if not coords:
            return "[No coordinates]"
        
        if isinstance(coords[0], (int, float)):
            # Single coordinate pair
            return f"[{coords[0]:.4f}, {coords[1]:.4f}]"
        else:
            # Multiple coordinate pairs
            return f"[{coords[0][0] if coords else 0:.4f}, ...] ({len(coords)} points)"
    
    # ========================================================================
    # Phase 4: Analysis Computed Properties (Charts & Summary)
    # ========================================================================

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_total_area(self) -> str:
        """Formatted total area from analysis results."""
        try:
            summary = self.analysis_results.get("summary", {})
            val = summary.get("total_area_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_classes(self) -> str:
        """Number of classes found."""
        try:
            return str(self.analysis_results.get("summary", {}).get("num_classes", 0))
        except Exception:
            return "0"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_summary_top_class(self) -> str:
        """Top class by area."""
        try:
            return self.analysis_results.get("summary", {}).get("top_class", "N/A")
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_cover(self) -> str:
        """Hansen total area analyzed."""
        try:
            summary = self.analysis_results.get("summary", {})
            # New format: total_area_ha
            val = summary.get("total_area_ha", 0)
            return f"{val:,.0f} ha" if val else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_loss(self) -> str:
        """Hansen number of classes found."""
        try:
            summary = self.analysis_results.get("summary", {})
            num = summary.get("num_classes", 0)
            return f"{num} classes" if num else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_summary_gain(self) -> str:
        """Hansen analysis year."""
        try:
            summary = self.analysis_results.get("summary", {})
            year = summary.get("year", "")
            return f"Year {year}" if year else "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_table_data(self) -> List[Dict[str, Any]]:
        """Analysis results as list of dicts for rx.data_table."""
        try:
            data = self.analysis_results.get("data", [])
            if not data:
                return []
            # Keep only display-friendly columns
            import pandas as pd
            df = pd.DataFrame(data)
            display_cols = [c for c in ['Class_Name', 'Class', 'Class_ID', 'Area_ha', 'Pixels', 'Percentage'] if c in df.columns]
            if not display_cols:
                display_cols = list(df.columns)[:6]
            return df[display_cols].to_dict('records')
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def analysis_table_columns(self) -> List[str]:
        """Column names for analysis data table."""
        try:
            data = self.analysis_results.get("data", [])
            if not data:
                return []
            import pandas as pd
            df = pd.DataFrame(data)
            display_cols = [c for c in ['Class_Name', 'Class', 'Class_ID', 'Area_ha', 'Pixels', 'Percentage'] if c in df.columns]
            if not display_cols:
                display_cols = list(df.columns)[:6]
            return display_cols
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def mapbiomas_bar_chart(self) -> Optional[Figure]:
        """Plotly bar chart figure for MapBiomas results."""
        try:
            from .utils.visualization import get_chart_for_analysis
            fig = get_chart_for_analysis(self.analysis_results, chart_type='bar')
            return fig if fig else None
        except Exception as e:
            logger.error(f"Error generating MapBiomas bar chart: {e}")
            return None

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def mapbiomas_pie_chart(self) -> Optional[Figure]:
        """Plotly pie chart figure for MapBiomas results."""
        try:
            from .utils.visualization import get_chart_for_analysis
            fig = get_chart_for_analysis(self.analysis_results, chart_type='pie')
            return fig if fig else None
        except Exception as e:
            logger.error(f"Error generating MapBiomas pie chart: {e}")
            return None

    @rx.var(auto_deps=False, deps=["analysis_results"])
    def hansen_balance_chart(self) -> Optional[Figure]:
        """Plotly area distribution chart for Hansen results."""
        try:
            from .utils.visualization import get_chart_for_analysis
            # Use 'bar' chart type for area distribution (not 'balance')
            fig = get_chart_for_analysis(self.analysis_results, chart_type='bar')
            return fig if fig else None
        except Exception as e:
            logger.error(f"Error generating Hansen chart: {e}")
            return None

    @rx.var(auto_deps=False, deps=["analysis_results", "selected_territory", "territory_analysis_year"])
    def analysis_info_text(self) -> str:
        """Display info about current analysis: territory name and year."""
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

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_available(self) -> bool:
        """Whether comparison data is available."""
        return self.mapbiomas_comparison_result is not None and bool(self.mapbiomas_comparison_result)

    @rx.var(auto_deps=False, deps=["result_keys_list"])
    def result_tab_labels(self) -> List[str]:
        """Display labels for each analysis result tab."""
        labels = []
        for key in self.result_keys_list:
            if "::" in key:
                prefix, name = key.split("::", 1)
                if prefix == "territory":
                    labels.append(name)
                else:
                    labels.append(f"Geom {name}")
            else:
                labels.append(key)
        return labels

    @rx.var(auto_deps=False, deps=["comparison_year1"])
    def comparison_year1_str(self) -> str:
        """Comparison year 1 as string for UI binding."""
        return str(self.comparison_year1)

    @rx.var(auto_deps=False, deps=["comparison_year2"])
    def comparison_year2_str(self) -> str:
        """Comparison year 2 as string for UI binding."""
        return str(self.comparison_year2)

    @rx.var(auto_deps=False, deps=["mapbiomas_current_year"])
    def mapbiomas_current_year_str(self) -> str:
        """MapBiomas current year as string for UI binding."""
        return str(self.mapbiomas_current_year) if self.mapbiomas_current_year > 0 else "2023"

    @rx.var(auto_deps=False, deps=["geometry_analysis_year"])
    def geometry_analysis_year_str(self) -> str:
        """Geometry analysis year as string for UI binding."""
        if isinstance(self.geometry_analysis_year, int):
            return str(self.geometry_analysis_year)
        else:
            return str(self.geometry_analysis_year) if self.geometry_analysis_year else "2023"

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_chart(self) -> Optional[Figure]:
        """Plotly comparison chart."""
        try:
            if not self.mapbiomas_comparison_result:
                return None
            from .utils.visualization import MapBiomasVisualizer
            import pandas as pd
            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if 'Area_Year1' in df.columns and 'Area_Year2' in df.columns:
                name_col = next((c for c in ['Class_Name', 'Class'] if c in df.columns), 'Class_ID')
                import plotly.graph_objects as go
                fig = go.Figure(data=[
                    go.Bar(name=str(year1), x=df[name_col], y=df['Area_Year1']),
                    go.Bar(name=str(year2), x=df[name_col], y=df['Area_Year2']),
                ])
                fig.update_layout(
                    title=f'Comparison: {year1} vs {year2}',
                    barmode='group', template='plotly_white', height=400,
                )
                return fig
            return None
        except Exception as e:
            logger.error(f"Comparison chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def gains_losses_chart(self) -> Optional[Figure]:
        """Plotly gains/losses chart from comparison."""
        try:
            if not self.mapbiomas_comparison_result:
                return None
            from .utils.visualization import create_gains_losses_chart
            import pandas as pd
            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if 'Change_km2' not in df.columns and 'Change_ha' in df.columns:
                df['Change_km2'] = df['Change_ha'] / 100
            if 'Abs_Change' not in df.columns:
                df['Abs_Change'] = df.get('Change_ha', df.get('Change_km2', 0)).abs()
            fig = create_gains_losses_chart(df, year1, year2)
            return fig if fig else None
        except Exception as e:
            logger.error(f"Gains/losses chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def change_pct_chart(self) -> Optional[Figure]:
        """Plotly percentage change chart."""
        try:
            if not self.mapbiomas_comparison_result:
                return None
            from .utils.visualization import create_change_percentage_chart
            import pandas as pd
            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return None
            df = pd.DataFrame(data)
            year1 = self.mapbiomas_comparison_result.get("year_start", 0)
            year2 = self.mapbiomas_comparison_result.get("year_end", 0)
            if 'Abs_Change' not in df.columns:
                df['Abs_Change'] = df.get('Change_ha', df.get('Change_km2', 0)).abs()
            fig = create_change_percentage_chart(df, year1, year2)
            return fig if fig else None
        except Exception as e:
            logger.error(f"Change pct chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_total_gains(self) -> str:
        """Total gains from comparison."""
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if 'Change_km2' in df.columns:
                val = df[df['Change_km2'] > 0]['Change_km2'].sum()
                return f"{val:,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_total_losses(self) -> str:
        """Total losses from comparison."""
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if 'Change_km2' in df.columns:
                val = abs(df[df['Change_km2'] < 0]['Change_km2'].sum())
                return f"{val:,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["mapbiomas_comparison_result"])
    def comparison_net_change(self) -> str:
        """Net change from comparison."""
        try:
            if not self.mapbiomas_comparison_result:
                return "N/A"
            import pandas as pd
            df = pd.DataFrame(self.mapbiomas_comparison_result.get("data", []))
            if 'Change_km2' in df.columns:
                val = df['Change_km2'].sum()
                return f"{val:+,.1f} km²"
            return "N/A"
        except Exception:
            return "N/A"

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def sankey_chart(self) -> Optional[Figure]:
        """Plotly Sankey diagram for land cover transitions."""
        try:
            transitions = self.territory_transitions
            if not transitions:
                # Try to derive from comparison result
                if not self.mapbiomas_comparison_result:
                    return None
                transitions = self.mapbiomas_comparison_result.get("transitions")
            if not transitions:
                return None
            year1 = self.comparison_year1
            year2 = self.comparison_year2
            if self.mapbiomas_comparison_result:
                year1 = self.mapbiomas_comparison_result.get("year_start", year1)
                year2 = self.mapbiomas_comparison_result.get("year_end", year2)
            from .utils.visualization import create_sankey_transitions
            fig = create_sankey_transitions(transitions, year1, year2)
            return fig if fig else None
        except Exception as e:
            logger.error(f"Sankey chart error: {e}")
            return None

    @rx.var(auto_deps=False, deps=["territory_transitions", "mapbiomas_comparison_result"])
    def transition_matrix_chart(self) -> Optional[Figure]:
        """Plotly heatmap showing transition matrix between two years."""
        try:
            transitions = self.territory_transitions
            if not transitions:
                if not self.mapbiomas_comparison_result:
                    return None
                transitions = self.mapbiomas_comparison_result.get("transitions")
            if not transitions:
                return None

            import plotly.graph_objects as pgo
            # Build matrix from transitions dict
            all_classes = set()
            for src, tgt_dict in transitions.items():
                if isinstance(tgt_dict, dict):
                    all_classes.add(str(src))
                    for tgt in tgt_dict:
                        all_classes.add(str(tgt))
            classes = sorted(all_classes)
            if not classes:
                return None

            # Try to get readable names
            try:
                from .utils.visualization import _get_mapbiomas_labels
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
                    src_dict = transitions.get(src, transitions.get(int(src) if src.isdigit() else src, {}))
                    if isinstance(src_dict, dict):
                        val = src_dict.get(tgt, src_dict.get(int(tgt) if tgt.isdigit() else tgt, 0))
                    else:
                        val = 0
                    row.append(float(val) if isinstance(val, (int, float)) else 0)
                matrix.append(row)

            year1 = self.comparison_year1
            year2 = self.comparison_year2
            if self.mapbiomas_comparison_result:
                year1 = self.mapbiomas_comparison_result.get("year_start", year1)
                year2 = self.mapbiomas_comparison_result.get("year_end", year2)

            fig = pgo.Figure(data=pgo.Heatmap(
                z=matrix,
                x=display_names,
                y=display_names,
                colorscale="YlOrRd",
                text=[[f"{v:,.0f}" for v in row] for row in matrix],
                texttemplate="%{text}",
                hovertemplate="From: %{y}<br>To: %{x}<br>Area: %{z:,.0f} ha<extra></extra>",
            ))
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

    # ========================================================================
    # Multi-result management
    # ========================================================================

    def _store_result(self, key: str, result: Dict[str, Any],
                      comparison: Dict[str, Any] = None,
                      geojson_feature: Dict[str, Any] = None):
        """Store an analysis result bundle under a key."""
        bundle = {
            "result": result,
            "comparison": comparison,
            "geojson": geojson_feature,
        }
        self.all_analysis_results[key] = bundle
        if key not in self.result_keys_list:
            self.result_keys_list = self.result_keys_list + [key]
        # Activate it
        self.active_result_key = key
        self.analysis_results = result
        if comparison:
            self.mapbiomas_comparison_result = comparison

    def switch_result(self, key: str):
        """Switch to a previously stored result by key."""
        if key not in self.all_analysis_results:
            return
        bundle = self.all_analysis_results[key]
        self.active_result_key = key
        self.analysis_results = bundle.get("result", {})
        self.mapbiomas_comparison_result = bundle.get("comparison")

        # Zoom to that result's geometry
        geojson = bundle.get("geojson")
        if geojson:
            geom = geojson.get("geometry", geojson)
            coords = geom.get("coordinates", [])
            if coords:
                all_pts = []
                def _flatten(c):
                    if isinstance(c, list) and len(c) > 0:
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
        """Remove a stored result."""
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

    # ========================================================================
    # Event Handlers for State Updates (no reruns, direct updates)
    # ========================================================================

    def set_selected_geometry(self, idx: int):
        """Set the selected geometry by index."""
        if 0 <= idx < len(self.drawn_features):
            self.selected_geometry_idx = idx
            logger.info(f"Selected geometry {idx}: {self.drawn_features[idx].get('type', 'Unknown')}")
    
    def add_drawn_feature(self, feature: Dict[str, Any]):
        """Add a drawn feature to the list."""
        feature["_idx"] = len(self.drawn_features)
        feature["_display_idx"] = len(self.drawn_features) + 1
        self.drawn_features.append(feature)
        self.geometry_version += 1
        logger.info(f"Added drawn feature: {feature.get('type', 'Unknown')}")
    
    def remove_geometry(self, idx: int):
        """Remove a geometry by index (_idx field)."""
        # Filter out the feature with matching _idx
        self.drawn_features = [
            f for f in self.drawn_features
            if f.get("_idx") != idx
        ]
        # Reset selected if it was the deleted one
        if self.selected_geometry_idx == idx:
            self.selected_geometry_idx = None
        self.geometry_version += 1
        logger.info(f"Removed geometry with _idx={idx}")
    
    def clear_geometries(self):
        """Clear all drawn geometries."""
        self.drawn_features = []
        self.selected_geometry_idx = None
        self.geometry_version += 1
        logger.info("Cleared all geometries")
    
    def toggle_indigenous_lands(self):
        """Toggle indigenous lands base layer."""
        self.show_indigenous_lands = not self.show_indigenous_lands
        self.geometry_version += 1

    def select_territory_from_map(self, territory_name: str):
        """Handle territory selection from map click (JS bridge callback)."""
        try:
            import time
            current_time = time.time()
            self._selection_call_count += 1
            call_num = self._selection_call_count
            time_since_last = current_time - self._selection_timestamp if self._selection_timestamp else 0
            self._selection_timestamp = current_time
            
            logger.info(f"[MAP_SELECTION #{call_num}] Call #{call_num}, {time_since_last:.3f}s since last call: {territory_name}")
            
            # Guard against empty/invalid names
            if not territory_name or territory_name == "null" or not isinstance(territory_name, str):
                logger.warning(f"[MAP_SELECTION #{call_num}] Invalid territory name: {territory_name}")
                return
            
            # Clean up the name (may have extra whitespace from JS)
            territory_name = territory_name.strip()
            if not territory_name:
                logger.warning(f"[MAP_SELECTION #{call_num}] Territory name is empty after strip()")
                return
            
            # Prevent immediate re-selection of the same territory (guards against double-fire)
            if self.selected_territory == territory_name:
                logger.info(f"[MAP_SELECTION #{call_num}] Territory already selected: {territory_name} - skipping duplicate")
                return
            
            # Guard against rapid successive calls (might indicate a polling issue)
            if time_since_last < 0.2 and call_num > 1:
                logger.warning(f"[MAP_SELECTION #{call_num}] Calls too rapid ({time_since_last:.3f}s apart), might be a loop")
                return
            
            # Find exact match or partial match
            matched_territory = None
            if territory_name in self.available_territories:
                matched_territory = territory_name
                logger.info(f"[MAP_SELECTION #{call_num}] Found exact match: {matched_territory}")
            else:
                # Try partial match
                for t in self.available_territories:
                    if territory_name in t or t in territory_name:
                        matched_territory = t
                        logger.info(f"[MAP_SELECTION #{call_num}] Found partial match: {t}")
                        break
            
            if matched_territory:
                logger.info(f"[MAP_SELECTION #{call_num}] Calling set_selected_territory with: {matched_territory}")
                self.set_selected_territory(matched_territory)
                logger.info(f"[MAP_SELECTION #{call_num}] Territory selection completed: {matched_territory}")
            else:
                self.error_message = f"Territory '{territory_name}' not found in available list"
                logger.warning(f"[MAP_SELECTION #{call_num}] Territory not found: {territory_name}")
        except Exception as e:
            logger.error(f"[MAP_SELECTION] Error in select_territory_from_map: {e}")
            import traceback
            traceback.print_exc()
            self.error_message = f"Error selecting territory from map: {e}"

    def toggle_geometries_on_map(self):
        """Toggle geometry overlay visibility on the map."""
        self.show_geometries_on_map = not self.show_geometries_on_map
        self.geometry_version += 1

    def toggle_change_mask(self):
        """Toggle the change mask layer on the map."""
        self.show_change_mask = not self.show_change_mask
        self.geometry_version += 1

    def set_change_mask_year1(self, year: str):
        """Set change mask start year."""
        self.change_mask_year1 = int(year)
        if self.show_change_mask:
            self.geometry_version += 1

    def set_change_mask_year2(self, year: str):
        """Set change mask end year."""
        self.change_mask_year2 = int(year)
        if self.show_change_mask:
            self.geometry_version += 1

    def add_geojson_feature(self):
        """Add a feature from GeoJSON input (placeholder - needs form integration)."""
        # TODO: Get GeoJSON from form input
        # For now, this is a placeholder
        logger.info("GeoJSON feature add requested (form integration needed)")
    
    def add_territory_geometry(self, territory_name: str):
        """Add a territory as a geometry (drawable feature for analysis)."""
        try:
            from .utils.ee_service_extended import get_ee_service
            ee_service = get_ee_service()
            
            # Get territory geometry
            territory_geom = ee_service.get_territory_geometry(territory_name)
            if territory_geom is None:
                logger.warning(f"Could not load geometry for territory: {territory_name}")
                self.error_message = f"Failed to load geometry for {territory_name}"
                return
            
            # Convert to dict for storage
            territory_feature = {
                "type": "Territory",
                "name": territory_name,
                "territory_name": territory_name,
                "coordinates": [],  # Will be fetched from EE on demand
                "_ee_geometry": territory_geom  # Store EE geometry object
            }
            
            self.drawn_features.append(territory_feature)
            self.geometry_version += 1
            logger.info(f"Added territory geometry: {territory_name}")
        except Exception as e:
            logger.error(f"Error adding territory geometry: {e}")
            self.error_message = f"Error loading territory: {str(e)}"
    
    def get_selected_geometry_ee(self) -> Optional[Any]:
        """Get Earth Engine geometry object for selected geometry."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            return None
        
        feature = self.drawn_features[self.selected_geometry_idx]
        
        # Check if it's a territory with cached EE geometry
        if feature.get("_ee_geometry"):
            return feature["_ee_geometry"]
        
        # Otherwise, try to convert coordinates to EE geometry
        if feature.get("coordinates"):
            try:
                coords = feature["coordinates"]
                if feature.get("type") == "Polygon":
                    return ee.Geometry.Polygon(coords)
                elif feature.get("type") == "LineString":
                    return ee.Geometry.LineString(coords)
                elif feature.get("type") == "Point":
                    return ee.Geometry.Point(coords)
            except Exception as e:
                logger.error(f"Error converting coordinates to EE geometry: {e}")
        
        return None
    
    def initialize_app(self):
        """Initialize application state on first load - auto-loads territories."""
        if self.ee_initialized:
            return  # Already initialized
        try:
            from .utils.ee_service_extended import get_ee_service
            ee_service = get_ee_service()

            # Load territories from Earth Engine
            success, territories = ee_service.load_territories()
            if success and territories:
                self.available_territories = list(territories)
            else:
                self.available_territories = [
                    "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                    "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná"
                ]

            # Cache indigenous lands tile URL for map display
            try:
                tile_url = ee_service.get_indigenous_lands_tile_url()
                if tile_url:
                    self.indigenous_lands_tile_url = tile_url
                    logger.info("Indigenous lands tile layer cached")
                self.territory_name_property = ee_service.get_name_property()
            except Exception as tile_err:
                logger.warning(f"Could not load indigenous lands tiles: {tile_err}")

            self.data_loaded = True
            self.ee_initialized = True
            self.geometry_version += 1  # Force map rebuild with new layer
            logger.info(f"App initialized with {len(self.available_territories)} territories")
        except Exception as e:
            self.error_message = f"Failed to initialize: {str(e)}"
            self.available_territories = []
            self.data_loaded = True
            self.ee_initialized = False
    
    def run_mapbiomas_analysis(self):
        """Run MapBiomas analysis for selected territory and year."""
        try:
            from .utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.mapbiomas_analysis_pending = True
            self.loading_message = f"Analyzing {self.selected_territory} for MapBiomas {self.mapbiomas_current_year}..."
            self.error_message = ""

            ee_service = get_ee_service()

            # Get territory geometry
            logger.info(f"Getting geometry for territory: {self.selected_territory}")
            territory_geom = ee_service.get_territory_geometry(self.selected_territory)
            if territory_geom is None:
                self.error_message = f"Could not find territory: {self.selected_territory}"
                logger.error(self.error_message)
                self.mapbiomas_analysis_pending = False
                self.loading_message = ""
                return

            logger.info(f"Running MapBiomas analysis for {self.selected_territory}, year {self.mapbiomas_current_year}")

            # Run analysis
            analysis_df = ee_service.analyze_mapbiomas(territory_geom, self.mapbiomas_current_year)

            if analysis_df.empty:
                self.error_message = f"No MapBiomas data found for {self.selected_territory} in {self.mapbiomas_current_year}"
                logger.warning(self.error_message)
            else:
                # Store results in both places
                result_dict = {
                    "type": "mapbiomas",
                    "summary": {
                        "total_area_ha": analysis_df['Area_ha'].sum(),
                        "classes": len(analysis_df)
                    },
                    "territory": self.selected_territory,
                    "year": self.mapbiomas_current_year,
                    "data": analysis_df.to_dict('records'),
                }
                self.analysis_results = result_dict  # Set as active result for display
                self.mapbiomas_analysis_result = result_dict  # Persist MapBiomas result
                self.territory_analysis_year = self.mapbiomas_current_year  # Track year used
                self.loading_message = f"✓ Analysis complete: {len(analysis_df)} classes found"
                logger.info(f"✓ MapBiomas analysis success: {len(analysis_df)} classes")

            self.mapbiomas_analysis_pending = False

        except Exception as e:
            logger.error(f"MapBiomas analysis error: {e}", exc_info=True)
            self.error_message = f"Analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            self.loading_message = ""
    
    def run_hansen_analysis(self):
        """Run Hansen analysis for selected territory and year."""
        try:
            from .utils.ee_service_extended import get_ee_service
            
            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return
            
            self.hansen_analysis_pending = True
            self.loading_message = f"Analyzing {self.selected_territory} for Hansen {self.hansen_current_year}..."
            
            ee_service = get_ee_service()
            
            # Get territory geometry and run analysis
            territory_geom = ee_service.get_territory_geometry(self.selected_territory)
            if territory_geom is None:
                self.error_message = f"Could not find territory: {self.selected_territory}"
                self.hansen_analysis_pending = False
                return
            
            # Run analysis
            analysis_df = ee_service.analyze_hansen(territory_geom, self.hansen_current_year)
            
            if analysis_df.empty:
                self.error_message = f"No data found for this territory"
            else:
                # Store results
                self.analysis_results = {
                    "type": "hansen",
                    "territory": self.selected_territory,
                    "year": self.hansen_current_year,
                    "data": analysis_df.to_dict(),
                }
                self.loading_message = ""
            
            self.hansen_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.hansen_analysis_pending = False
        
    def set_language(self, lang: str):
        """Change application language."""
        self.language = lang
    
    def set_country(self, country: str):
        """Change selected country/region."""
        self.selected_country = country
        
    def toggle_tutorial(self):
        """Toggle tutorial visibility."""
        self.show_tutorial = not self.show_tutorial

    def toggle_tutorial_step(self, step_index: int):
        """Toggle a tutorial step expansion."""
        if step_index in self.tutorial_expanded_steps:
            self.tutorial_expanded_steps = [s for s in self.tutorial_expanded_steps if s != step_index]
        else:
            self.tutorial_expanded_steps = self.tutorial_expanded_steps + [step_index]

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open
        
    def toggle_sidebar_section(self, section: str):
        """Toggle sidebar section expansion."""
        if section == "mapbiomas":
            self.sidebar_mapbiomas_expanded = not self.sidebar_mapbiomas_expanded
        elif section == "hansen":
            self.sidebar_hansen_expanded = not self.sidebar_hansen_expanded
        elif section == "territory":
            self.sidebar_territory_expanded = not self.sidebar_territory_expanded
        elif section == "geometry":
            self.sidebar_geometry_expanded = not self.sidebar_geometry_expanded
    
    def start_resize(self):
        """Start resizing the sidebar."""
        self.is_resizing_sidebar = True
    
    def end_resize(self):
        """Stop resizing the sidebar."""
        self.is_resizing_sidebar = False
    
    def update_sidebar_width(self, width: int):
        """Update sidebar width (called during resize)."""
        # Constrain width between 200px and 500px
        constrained_width = max(200, min(500, width))
        self.sidebar_width = constrained_width
        
    def set_active_tab(self, tab: str):
        """Switch to different tab."""
        self.active_tab = tab
        
    def set_map_center(self, lat: float, lng: float, zoom: int = None):
        """Update map center and optional zoom."""
        self.map_center = (lat, lng)
        if zoom is not None:
            self.map_zoom = zoom
            
    def toggle_mapbiomas_year(self, year: int):
        """Toggle MapBiomas layer for specific year."""
        self.mapbiomas_years_enabled[year] = not self.mapbiomas_years_enabled.get(year, False)
        
    def toggle_hansen_year(self, year: str):
        """Toggle Hansen layer for specific year."""
        self.hansen_years_enabled[year] = not self.hansen_years_enabled.get(year, False)
        
    def toggle_gfc_layer(self, layer_type: str):
        """Toggle Global Forest Change layers."""
        if layer_type == "tree_cover":
            self.show_hansen_gfc_tree_cover = not self.show_hansen_gfc_tree_cover
        elif layer_type == "tree_loss":
            self.show_hansen_gfc_tree_loss = not self.show_hansen_gfc_tree_loss
        elif layer_type == "tree_gain":
            self.show_hansen_gfc_tree_gain = not self.show_hansen_gfc_tree_gain
            
    def set_selected_territory(self, territory: str):
        """Select a territory for analysis and overlay its geometry on the map."""
        try:
            logger.info(f"[TERRITORY_SET] Starting set_selected_territory: {territory}")
            
            if not territory:
                logger.warning("[TERRITORY_SET] Territory is empty, returning")
                return

            logger.info(f"[TERRITORY_SET] Updating selected_territory state")
            self.selected_territory = territory
            self.pending_territory = None
            self.territory_name = territory
            logger.info(f"[TERRITORY_SET] State variables updated")

            # Load territory geometry, cache GeoJSON, and zoom to it
            # Wrap everything in try-except to prevent React rendering issues
            try:
                from .utils.ee_service_extended import get_ee_service
                ee_service = get_ee_service()
                logger.info(f"[TERRITORY_SET] Got EE service")

                # Handle territory names that might include IDs like "Balaio (5301)"
                # Extract base name and try to match against available territories
                territory_for_geometry = territory
                if "(" in territory and ")" in territory:
                    # Try to extract base name (everything before the ID)
                    base_name = territory.split("(")[0].strip()
                    logger.info(f"[TERRITORY_SET] Found ID in territory name, base name: {base_name}")
                    
                    # Try to find exact match in available territories
                    if base_name in self.available_territories:
                        territory_for_geometry = base_name
                        logger.info(f"[TERRITORY_SET] Using base name for geometry lookup: {base_name}")
                    else:
                        # Try to find partial match
                        for available_t in self.available_territories:
                            if base_name in available_t or available_t in base_name:
                                territory_for_geometry = available_t
                                logger.info(f"[TERRITORY_SET] Found partial match for geometry: {available_t}")
                                break

                logger.info(f"[TERRITORY_SET] Loading geometry for territory: {territory_for_geometry}")
                geom = ee_service.get_territory_geometry(territory_for_geometry)
                logger.info(f"[TERRITORY_SET] Geometry loaded")
                
                if not geom:
                    logger.warning(f"[TERRITORY_SET] No geometry found for territory: {territory_for_geometry}")
                    # Try with original territory name as fallback
                    if territory_for_geometry != territory:
                        logger.info(f"[TERRITORY_SET] Trying with original name: {territory}")
                        geom = ee_service.get_territory_geometry(territory)
                    
                    if not geom:
                        self.error_message = f"Could not load geometry for territory: {territory}"
                        return

                try:
                    logger.info(f"[TERRITORY_SET] Converting geometry to GeoJSON")
                    # Get GeoJSON for map overlay
                    # ee.Geometry.getInfo() returns bare geometry dict, possibly
                    # with EE-specific keys like 'geodesic', 'evenOdd'.
                    raw_geojson = geom.getInfo()
                    logger.info(f"[TERRITORY_SET] GeoJSON received from EE")
                    
                    # Strip EE-specific keys, keep only standard GeoJSON fields
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
                    
                    logger.info(f"[TERRITORY_SET] Updating territory_geojson_features")
                    # Replace any existing territory features (keep only current)
                    self.territory_geojson_features = [territory_feature]
                    logger.info(f"[TERRITORY_SET] Incrementing geometry_version")
                    self.geometry_version += 1
                    logger.info(f"[TERRITORY_SET] Territory GeoJSON cached: {clean_geom['type']} with {len(clean_geom.get('coordinates', []))} coord groups")
                except Exception as geojson_err:
                    logger.warning(f"[TERRITORY_SET] Could not convert territory geometry to GeoJSON: {geojson_err}")
                    import traceback
                    traceback.print_exc()
                    # Continue without GeoJSON overlay
                    self.territory_geojson_features = []

                try:
                    logger.info(f"[TERRITORY_SET] Computing bounds for zoom")
                    # Get bounds for zoom
                    bounds = geom.bounds().getInfo()
                    if bounds and "coordinates" in bounds:
                        coords = bounds["coordinates"][0]
                        if coords and len(coords) > 0:
                            min_lat = min(c[1] for c in coords)
                            max_lat = max(c[1] for c in coords)
                            min_lon = min(c[0] for c in coords)
                            max_lon = max(c[0] for c in coords)

                            self.map_zoom_bounds = {
                                "min_lat": min_lat,
                                "max_lat": max_lat,
                                "min_lon": min_lon,
                                "max_lon": max_lon,
                                "center_lat": (min_lat + max_lat) / 2,
                                "center_lon": (min_lon + max_lon) / 2,
                            }
                            self.territory_geometry_displayed = True
                            logger.info(f"[TERRITORY_SET] Territory bounds calculated for: {territory}")
                    else:
                        logger.warning(f"[TERRITORY_SET] No bounds found in geometry")
                except Exception as bounds_err:
                    logger.warning(f"[TERRITORY_SET] Could not calculate territory bounds: {bounds_err}")
                    import traceback
                    traceback.print_exc()
                    # Continue without zoom bounds
                    
            except Exception as e:
                logger.error(f"[TERRITORY_SET] Error loading territory geometry for {territory}: {e}")
                import traceback
                traceback.print_exc()
                self.error_message = f"Error loading territory: {e}"

            logger.info(f"[TERRITORY_SET] Territory selection completed successfully: {territory}")
        except Exception as outer_e:
            logger.error(f"[TERRITORY_SET] Unexpected error in set_selected_territory: {outer_e}")
            import traceback
            traceback.print_exc()
            self.error_message = f"Unexpected error setting territory: {outer_e}"
        
    def set_pending_territory(self, territory: Optional[str]):
        """Set pending territory (waiting for confirmation)."""
        self.pending_territory = territory
        
    def confirm_territory(self):
        """Confirm pending territory selection."""
        if self.pending_territory:
            self.selected_territory = self.pending_territory
            self.pending_territory = None
            
    def set_country(self, country: str):
        """Change selected country."""
        self.selected_country = country
        
    def set_territory_filter(self, state: Optional[str]):
        """Filter territories by state/region."""
        self.territory_filter_state = state
        
    def add_drawn_feature(self, feature: Dict[str, Any]):
        """Add a drawn feature to the list."""
        # Add index for tracking in the UI
        feature["_idx"] = len(self.drawn_features)
        self.drawn_features.append(feature)
        self.all_drawn_features.append(feature)
        
    def clear_drawn_features(self):
        """Clear all drawn features."""
        self.drawn_features = []
        self.geometry_version += 1
    
    def capture_drawn_features(self):
        """
        Capture drawn features from the Folium map.
        This method should be called after drawing on the map.
        Works by extracting GeoJSON from the Leaflet Draw layer via JavaScript.
        """
        # This method triggers JavaScript to extract drawn features
        # The JavaScript call happens via rx.call_script() in the component
        # and sends the GeoJSON back to this handler via load_geojson_from_browser()
        pass
    
    def load_geojson_from_browser(self, geojson_data: str):
        """
        Receive GeoJSON data captured from browser's Leaflet Draw layer.
        Called by rx.call_script() callback after extracting drawn features
        from the Folium iframe via the JS bridge injected in map_builder.py.

        Args:
            geojson_data: JSON string containing GeoJSON FeatureCollection or error
        """
        try:
            import json
            data = json.loads(geojson_data) if isinstance(geojson_data, str) else geojson_data

            # Check for JS bridge errors
            if "error" in data and "features" not in data:
                self.error_message = str(data["error"])
                logger.warning(f"JS bridge error: {data['error']}")
                return

            # Extract features from GeoJSON FeatureCollection
            features = data.get("features", [])

            if not features:
                self.error_message = "No drawn geometries found on the map. Draw a polygon or rectangle first."
                return

            # Append new features (don't clear existing ones from uploads etc.)
            new_count = 0
            for feature in features:
                try:
                    geom = feature.get("geometry", {})
                    geom_type = geom.get("type", "Unknown")

                    if not geom or not geom.get("coordinates"):
                        continue

                    idx = len(self.drawn_features)
                    feature_obj = {
                        "_idx": idx,
                        "_display_idx": idx + 1,
                        "type": geom_type,
                        "name": f"Drawing {idx + 1}",
                        "geometry": geom,
                        "properties": feature.get("properties", {}),
                        "coordinates": geom.get("coordinates", []),
                    }

                    self.drawn_features.append(feature_obj)
                    self.all_drawn_features.append(feature_obj)
                    new_count += 1
                except Exception as feature_err:
                    logger.warning(f"Error processing feature: {feature_err}")

            if new_count:
                self.error_message = f"Captured {new_count} drawing(s) from map ({len(self.drawn_features)} total)"
                self.geometry_version += 1
            else:
                self.error_message = "No valid geometries could be extracted"

        except json.JSONDecodeError as e:
            self.error_message = f"Error parsing GeoJSON: {str(e)}"
        except Exception as e:
            self.error_message = f"Error loading geometries: {str(e)}"
            logger.error(f"Error in load_geojson_from_browser: {e}")
    
    def add_test_geometry(self):
        """
        Add a test geometry to demonstrate the geometry selector UI.
        Useful for testing the interface without drawing on the map.
        In production, geometries would come from Leaflet Draw.
        """
        # Create a test polygon geometry (sample indigenous territory)
        idx = len(self.drawn_features)
        test_feature = {
            "_idx": idx,
            "_display_idx": idx + 1,
            "type": "Polygon",
            "name": "Test Territory",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-60.5, -3.0],
                    [-60.0, -3.0],
                    [-60.0, -2.5],
                    [-60.5, -2.5],
                    [-60.5, -3.0]
                ]]
            },
            "properties": {
                "name": "Test Territory",
                "description": "Sample geometry for testing the selector UI"
            },
            "coordinates": [[
                [-60.5, -3.0],
                [-60.0, -3.0],
                [-60.0, -2.5],
                [-60.5, -2.5],
                [-60.5, -3.0]
            ]],
        }
        
        self.drawn_features.append(test_feature)
        self.all_drawn_features.append(test_feature)
        self.geometry_version += 1
        self.error_message = "✓ Test geometry loaded. You can now test the analysis features."
    
    def show_geometry_info(self, geometry_idx: int):
        """Show geometry info popup for a specific geometry."""
        if 0 <= geometry_idx < len(self.drawn_features):
            feature = self.drawn_features[geometry_idx]
            self.geometry_popup_info = {
                "index": geometry_idx,
                "type": feature.get("type", "Unknown"),
                "area_km2": feature.get("area_km2", 0),
                "coordinates_count": self._count_coordinates(feature.get("geometry", {})),
                "created_at": feature.get("created_at", "Unknown"),
                "name": feature.get("name", f"Geometry {geometry_idx}"),
            }
            self.show_geometry_popup = True
    
    def hide_geometry_info(self):
        """Hide geometry info popup."""
        self.show_geometry_popup = False
        self.geometry_popup_info = {}
    
    def _count_coordinates(self, geometry: Dict[str, Any]) -> int:
        """Count total coordinates in a geometry."""
        if not geometry:
            return 0
        
        coords = geometry.get("coordinates", [])
        
        def count_coords(coords_obj):
            if isinstance(coords_obj, list):
                if len(coords_obj) > 0:
                    if isinstance(coords_obj[0], (int, float)):
                        # Single coordinate pair
                        return 1
                    else:
                        # Nested list of coordinates
                        total = 0
                        for item in coords_obj:
                            total += count_coords(item)
                        return total
            return 0
        
        return count_coords(coords)
        
    def add_buffer_geometry(self, name: str, geometry: Dict[str, Any], metadata: Dict[str, Any] = None):
        """Add a new buffer geometry for analysis."""
        import datetime
        buffer_obj = BufferGeometry(
            name=name,
            geometry=geometry,
            created_at=datetime.datetime.now().isoformat(),
            metadata=metadata or {}
        )
        self.buffer_geometries[name] = buffer_obj
        
    def delete_buffer_geometry(self, name: str):
        """Delete a buffer geometry."""
        if name in self.buffer_geometries:
            del self.buffer_geometries[name]
            if self.current_buffer_for_analysis == name:
                self.current_buffer_for_analysis = None
                
    def set_current_buffer(self, name: Optional[str]):
        """Set the current buffer for analysis."""
        self.current_buffer_for_analysis = name
        
    def toggle_buffer_compare_mode(self):
        """Toggle buffer comparison mode."""
        self.buffer_compare_mode = not self.buffer_compare_mode
        
    def set_analysis_results(self, results: Dict[str, Any]):
        """Store analysis results."""
        self.analysis_results = results
        
    def set_mapbiomas_year(self, year: int | str):
        """Change active MapBiomas year."""
        try:
            if isinstance(year, str):
                year = int(year)
            self.mapbiomas_current_year = year
        except (ValueError, TypeError):
            self.mapbiomas_current_year = 0
        
    def set_hansen_year(self, year: str):
        """Change active Hansen year."""
        self.hansen_current_year = year
        
    def set_country(self, country: str):
        """Change selected country."""
        self.selected_country = country
        
    def toggle_gfc_layer(self, layer_type: str):
        """Toggle Global Forest Change layer visibility."""
        if layer_type == "tree_cover":
            self.show_hansen_gfc_tree_cover = not self.show_hansen_gfc_tree_cover
        elif layer_type == "tree_loss":
            self.show_hansen_gfc_tree_loss = not self.show_hansen_gfc_tree_loss
        elif layer_type == "tree_gain":
            self.show_hansen_gfc_tree_gain = not self.show_hansen_gfc_tree_gain
    
    def add_mapbiomas_layer(self, year: Optional[int] = None):
        """Add MapBiomas year to map display."""
        if year is None:
            year = self.mapbiomas_current_year
        
        if year not in self.mapbiomas_displayed_years:
            self.mapbiomas_displayed_years.append(year)
            self.mapbiomas_displayed_years.sort()
            logger.info(f"Added MapBiomas {year} to display")
    
    def remove_mapbiomas_layer(self, year: int):
        """Remove MapBiomas year from map display."""
        if year in self.mapbiomas_displayed_years:
            self.mapbiomas_displayed_years.remove(year)
            logger.info(f"Removed MapBiomas {year} from display")
    
    def add_hansen_layer(self, layer_type: str = "loss"):
        """Add Hansen layer to map display."""
        if layer_type not in self.hansen_displayed_layers:
            self.hansen_displayed_layers.append(layer_type)
            logger.info(f"Added Hansen {layer_type} to display")
    
    def add_hansen_selected_year(self):
        """Add currently selected Hansen year to map display."""
        self.add_hansen_layer(self.hansen_current_year)
    
    def remove_hansen_layer(self, layer_type: str):
        """Remove Hansen layer from map display."""
        if layer_type in self.hansen_displayed_layers:
            self.hansen_displayed_layers.remove(layer_type)
            logger.info(f"Removed Hansen {layer_type} from display")
    
    def refresh_map(self):
        """Trigger map refresh (called when button is clicked)."""
        logger.info("Map refresh triggered")
    
    def clear_all_layers(self):
        """Clear all MapBiomas and Hansen layers from display."""
        self.mapbiomas_displayed_years = []
        self.hansen_displayed_layers = []
        logger.info("All layers cleared")
    
    def toggle_consolidated_classes(self):
        """Toggle between full and consolidated Hansen classes."""
        self.use_consolidated_classes = not self.use_consolidated_classes
        
    def set_error(self, message: str):
        """Set error message for display."""
        self.error_message = message
        
    def clear_error(self):
        """Clear error message."""
        self.error_message = ""
        
    def set_loading(self, message: str = ""):
        """Set loading state with optional message."""
        self.loading_message = message
        
    def clear_loading(self):
        """Clear loading state."""
        self.loading_message = ""
        
    def set_buffer_distance_input(self, value: str):
        """Update buffer distance input field."""
        self.buffer_distance_input = value
    
    def set_territory_search_query(self, query: str):
        """Update territory search query (filters filtered_territories)."""
        self.territory_search_query = query
        
    def mark_data_loaded(self):
        """Mark that core data has been loaded."""
        self.data_loaded = True
        self.ee_initialized = True
    
    # ========================================================================
    # Phase 4: CSV Download & Export
    # ========================================================================

    def download_analysis_csv(self):
        """Generate and trigger CSV download of current analysis results."""
        try:
            import pandas as pd
            data = self.analysis_results.get("data", [])
            if not data:
                self.error_message = "No analysis data to export"
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)

            a_type = self.analysis_results.get("type", "analysis")
            territory = self.analysis_results.get("geometry", "unknown")
            year = self.analysis_results.get("year", "")
            filename = f"{territory}_{a_type}_{year}.csv".replace(" ", "_")

            return rx.download(data=csv_content, filename=filename)
        except Exception as e:
            self.error_message = f"Export error: {str(e)}"

    def download_comparison_csv(self):
        """Generate CSV download of comparison results."""
        try:
            import pandas as pd
            if not self.mapbiomas_comparison_result:
                self.error_message = "No comparison data to export"
                return

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            year1 = self.mapbiomas_comparison_result.get("year_start", "")
            year2 = self.mapbiomas_comparison_result.get("year_end", "")
            filename = f"comparison_{year1}_vs_{year2}.csv"

            return rx.download(data=csv_content, filename=filename)
        except Exception as e:
            self.error_message = f"Export error: {str(e)}"

    # ========================================================================
    # Phase 5: Export Handlers
    # ========================================================================

    def export_analysis_zip(self):
        """Generate and download ZIP with all analysis data and figures."""
        try:
            from .utils.export_service import create_export_zip, collect_export_data_from_state

            self.export_pending = True
            self.loading_message = "Preparing export..."

            export_data = collect_export_data_from_state(self)
            zip_bytes = create_export_zip(**export_data)

            territory = self.territory_name or self.selected_territory or "analysis"
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"yvynation_{territory}_{ts}.zip".replace(" ", "_")

            self.export_pending = False
            self.loading_message = ""

            return rx.download(data=zip_bytes, filename=filename)

        except Exception as e:
            self.error_message = f"Export failed: {str(e)}"
            self.export_pending = False
            self.loading_message = ""
            logger.error(f"Export ZIP error: {e}")

    def export_pdf_maps(self):
        """Generate and download PDF maps for all active layers."""
        try:
            from .utils.map_export_service import create_map_set
            from .utils.export_service import _geojson_from_features
            import zipfile as zf_module

            self.map_export_pending = True
            self.loading_message = "Generating PDF maps..."

            # Get territory geometry if available
            territory_geojson = None
            ee_geometry = None
            if self.selected_territory:
                try:
                    from .utils.ee_service_extended import get_ee_service
                    ee_service = get_ee_service()
                    ee_geometry = ee_service.get_territory_geometry(self.selected_territory)
                    if ee_geometry:
                        territory_geojson = ee_geometry.getInfo()
                except Exception:
                    pass

            maps = create_map_set(
                drawn_features=self.drawn_features,
                territory_name=self.territory_name or self.selected_territory,
                active_mapbiomas_years=self.mapbiomas_displayed_years,
                active_hansen_layers=self.hansen_displayed_layers,
                ee_geometry=ee_geometry,
                territory_geojson=territory_geojson,
            )

            if not maps:
                self.error_message = "No maps generated. Add layers first."
                self.map_export_pending = False
                self.loading_message = ""
                return

            # If single map, download PDF directly
            if len(maps) == 1:
                name, pdf_bytes = next(iter(maps.items()))
                self.map_export_pending = False
                self.loading_message = ""
                return rx.download(data=pdf_bytes, filename=f"{name}.pdf")

            # Multiple maps -> ZIP
            import io
            buf = io.BytesIO()
            with zf_module.ZipFile(buf, 'w', zf_module.ZIP_DEFLATED) as zipf:
                for name, pdf_bytes in maps.items():
                    zipf.writestr(f"maps/{name}.pdf", pdf_bytes)
            buf.seek(0)

            territory = self.territory_name or self.selected_territory or "maps"
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"yvynation_maps_{territory}_{ts}.zip".replace(" ", "_")

            self.map_export_pending = False
            self.loading_message = ""

            return rx.download(data=buf.read(), filename=filename)

        except Exception as e:
            self.error_message = f"Map export failed: {str(e)}"
            self.map_export_pending = False
            self.loading_message = ""
            logger.error(f"PDF map export error: {e}")

    # ========================================================================
    # Geometry Upload & Buffer Methods (Phase 2)
    # ========================================================================

    def upload_geometry_from_geojson(self, geojson_data: Dict[str, Any], file_name: str = "Uploaded Geometry"):
        """
        Process an uploaded GeoJSON geometry.
        
        Args:
            geojson_data: Parsed GeoJSON (FeatureCollection or Feature)
            file_name: Name of the uploaded file for reference
        """
        try:
            from .utils.buffer_utils import convert_feature_collection_to_ee_geometry
            from .utils.geometry_handler import validate_geometry, get_bbox_from_geojson
            
            # Validate the GeoJSON
            is_valid, error_msg = validate_geometry(geojson_data)
            if not is_valid:
                self.error_message = f"Invalid geometry: {error_msg}"
                return False
            
            # Extract the feature name
            feature_name = file_name.rsplit('.', 1)[0] if file_name else "Uploaded Geometry"
            
            # Convert to Earth Engine geometry
            ee_geometry = convert_feature_collection_to_ee_geometry(geojson_data)
            if not ee_geometry:
                self.error_message = "Failed to convert geometry to Earth Engine format"
                return False
            
            # Add to drawn features
            feature = {
                'type': 'Feature',
                'properties': {
                    'name': feature_name,
                    'type': 'uploaded_geometry',
                    'source': 'upload'
                },
                'geometry': geojson_data.get('features', [{}])[0].get('geometry') if geojson_data.get('type') == 'FeatureCollection' else geojson_data.get('geometry')
            }
            
            self.add_drawn_feature(feature)
            self.selected_territory = feature_name
            
            self.error_message = ""
            return True
        
        except Exception as e:
            self.error_message = f"Error processing geometry: {str(e)}"
            return False
    
    def create_buffer_from_geometry(self, geometry_name: str, buffer_distance_km: float):
        """
        Create an external buffer from a drawn or territory geometry.

        Args:
            geometry_name: Name of the geometry to buffer
            buffer_distance_km: Buffer distance in kilometers
        """
        try:
            from .utils.buffer_utils import (
                create_external_buffer,
                create_buffer_geometry_dict,
                convert_geojson_to_ee_geometry
            )
            from .utils.ee_service_extended import get_ee_service
            import datetime

            ee_geom = None

            # First try: territory geometry from EE (most reliable)
            try:
                ee_service = get_ee_service()
                territory_geom = ee_service.get_territory_geometry(geometry_name)
                if territory_geom:
                    ee_geom = territory_geom
                    logger.info(f"Buffer: using EE geometry for territory '{geometry_name}'")
            except Exception:
                pass

            # Second try: search drawn features
            if not ee_geom:
                geom_feature = None
                for feat in self.all_drawn_features + self.drawn_features:
                    name = feat.get('name') or feat.get('properties', {}).get('name', '')
                    if name == geometry_name:
                        geom_feature = feat
                        break
                if geom_feature:
                    ee_geom = convert_geojson_to_ee_geometry(geom_feature)

            # Third try: territory geojson cache
            if not ee_geom:
                for feat in self.territory_geojson_features:
                    if feat.get('name') == geometry_name:
                        ee_geom = convert_geojson_to_ee_geometry(feat)
                        break

            if not ee_geom:
                self.error_message = f"Geometry '{geometry_name}' not found"
                return False
            
            # Create buffer
            buffer_geom = create_external_buffer(ee_geom, buffer_distance_km)
            if not buffer_geom:
                self.error_message = "Failed to create buffer"
                return False
            
            # Create buffer metadata
            buffer_name = f"Buffer {buffer_distance_km}km - {geometry_name}"
            buffer_dict = create_buffer_geometry_dict(
                name=buffer_name,
                ee_geometry=buffer_geom,
                buffer_size_km=buffer_distance_km,
                source_name=geometry_name,
                created_at=datetime.datetime.now().isoformat()
            )
            
            # Add to state
            self.add_buffer_geometry(buffer_name, buffer_dict)
            self.current_buffer_for_analysis = buffer_name
            
            self.error_message = ""
            return True
        
        except Exception as e:
            self.error_message = f"Error creating buffer: {str(e)}"
            return False
    
    async def handle_geometry_upload(self, files: list):
        """
        Handle file upload from the geometry upload widget.
        
        Args:
            files: List of uploaded files
        """
        try:
            from .utils.geometry_handler import parse_geojson, parse_kml, validate_geometry
            
            if not files:
                self.error_message = "No file selected"
                return
            
            # Get the first file (we only accept single file)
            upload_data = files[0] if files else None
            if not upload_data:
                self.error_message = "No file data"
                return
            
            # Extract file content and name
            # In Reflex, upload data comes as {"name": filename, "size": size}
            # We need to read the file content from the upload
            file_name = getattr(upload_data, 'name', 'unknown')
            
            # Read file content
            try:
                # Get the file content from the upload
                if hasattr(upload_data, 'read'):
                    file_content = await upload_data.read()
                else:
                    # Handle as bytes if already provided
                    file_content = upload_data
            except Exception as e:
                self.error_message = f"Could not read file: {str(e)}"
                return
            
            # Decode if bytes
            if isinstance(file_content, bytes):
                try:
                    file_content = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    self.error_message = "File must be UTF-8 encoded text"
                    return
            
            # Determine file type and parse
            file_ext = file_name.lower().split('.')[-1] if '.' in file_name else ''
            
            geojson_data = None
            if file_ext == 'json' or file_ext == 'geojson':
                geojson_data = parse_geojson(file_content, file_name)
            elif file_ext == 'kml':
                geojson_data = parse_kml(file_content, file_name)
            else:
                self.error_message = f"Unsupported file type: {file_ext}. Use .json or .kml"
                return
            
            if not geojson_data:
                self.error_message = "Failed to parse file. Check format and try again."
                return
            
            # Upload the geometry
            success = self.upload_geometry_from_geojson(geojson_data, file_name)
            if success:
                self.error_message = f"✅ Loaded {file_name}"
            
        except Exception as e:
            self.error_message = f"Upload error: {str(e)}"
    
    async def handle_create_buffer(self, buffer_distance: str):
        """
        Handle buffer creation from UI input.
        
        Args:
            buffer_distance: Distance in km as string
        """
        try:
            distance_km = float(buffer_distance)
            if distance_km <= 0:
                self.error_message = "Buffer distance must be greater than 0"
                return
            
            if not self.selected_territory:
                self.error_message = "Select a geometry first"
                return
            
            success = self.create_buffer_from_geometry(self.selected_territory, distance_km)
            if success:
                self.error_message = ""
        
        except ValueError:
            self.error_message = "Invalid buffer distance. Enter a number."
        except Exception as e:
            self.error_message = f"Buffer error: {str(e)}"
    
    # ========================================================================
    # MapBiomas Analysis Methods (Phase 3)
    # ========================================================================
    
    async def run_mapbiomas_analysis_on_geometry(self):
        """
        Run MapBiomas analysis on the selected drawn geometry.
        """
        try:
            from .utils.mapbiomas_analysis import get_mapbiomas_analyzer
            
            # Check if a geometry is selected
            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return
            
            # Get the EE geometry for the selected feature
            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return
            
            self.mapbiomas_analysis_pending = True
            self.loading_message = f"Analyzing MapBiomas {self.mapbiomas_current_year}..."
            
            # Run analysis
            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return
            
            # Analyze single year
            result_df = analyzer.analyze_single_year(
                ee_geom,
                self.mapbiomas_current_year,
                scale=30
            )
            
            if result_df.empty:
                self.error_message = "No MapBiomas data found for this area"
            else:
                geom_name = self.drawn_features[self.selected_geometry_idx].get('name', 'Selected Geometry')
                result_dict = {
                    "type": "mapbiomas",
                    "geometry": geom_name,
                    "year": self.mapbiomas_current_year,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "total_area_ha": result_df['Area_ha'].sum(),
                        "num_classes": len(result_df),
                        "top_class": result_df.iloc[0]['Class_Name'] if len(result_df) > 0 else 'Unknown',
                    }
                }
                key = f"geometry::{self.selected_geometry_idx}"
                feat = self.drawn_features[self.selected_geometry_idx]
                self._store_result(key, result_dict, geojson_feature=feat)
                self.set_active_tab("analysis")
                self.loading_message = ""

            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas analysis error: {e}")

    async def run_hansen_analysis_on_geometry(self):
        """
        Run Hansen area distribution analysis on selected drawn geometry.
        """
        try:
            from .utils.hansen_analysis import get_hansen_analyzer

            # Check if a geometry is selected
            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            # Get the EE geometry for the selected feature
            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return

            self.hansen_analysis_pending = True
            self.loading_message = f"Analyzing Hansen {self.hansen_current_year}..."

            # Run analysis
            analyzer = get_hansen_analyzer()
            if not analyzer.is_available():
                self.error_message = "Hansen dataset not available"
                self.hansen_analysis_pending = False
                return

            # Get area distribution for selected year
            result_df = analyzer.get_area_distribution(ee_geom, year=self.hansen_current_year, scale=30)

            if result_df is None or result_df.empty:
                self.error_message = "No Hansen data found for this area"
            else:
                geom_name = self.drawn_features[self.selected_geometry_idx].get('name', 'Selected Geometry')
                result_dict = {
                    "type": "hansen",
                    "geometry": geom_name,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "year": self.hansen_current_year,
                        "num_classes": len(result_df),
                        "total_area_ha": float(result_df['Area_ha'].sum()),
                    }
                }
                key = f"geometry::{self.selected_geometry_idx}"
                feat = self.drawn_features[self.selected_geometry_idx]
                self._store_result(key, result_dict, geojson_feature=feat)
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Hansen analysis complete: {len(result_df)} classes, {result_df['Area_ha'].sum():.0f} ha")

            self.hansen_analysis_pending = False

        except Exception as e:
            self.error_message = f"Hansen analysis failed: {str(e)}"
            self.hansen_analysis_pending = False
            logger.error(f"Hansen analysis error: {e}")

    async def run_full_analysis_on_geometry(self):
        """Run MapBiomas + comparison on selected drawn geometry (full pipeline like territory)."""
        try:
            from .utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from .utils.visualization import calculate_gains_losses

            if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
                self.error_message = "Please select a geometry first"
                return

            ee_geom = self.get_selected_geometry_ee()
            if not ee_geom:
                self.error_message = "Selected geometry is not valid for analysis"
                return

            self.mapbiomas_analysis_pending = True
            geom_name = self.drawn_features[self.selected_geometry_idx].get('name', f'Geometry {self.selected_geometry_idx + 1}')
            self.loading_message = f"Full analysis on {geom_name}..."

            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return

            y1, y2 = self.comparison_year1, self.comparison_year2

            # Run both years
            df1 = analyzer.analyze_single_year(ee_geom, y1, scale=30)
            df2 = analyzer.analyze_single_year(ee_geom, y2, scale=30)

            if df2.empty:
                self.error_message = f"No MapBiomas data for year {y2}"
                self.mapbiomas_analysis_pending = False
                return

            name_col = 'Class_Name' if 'Class_Name' in df2.columns else 'Class'
            result_dict = {
                "type": "mapbiomas",
                "geometry": geom_name,
                "year": y2,
                "data": df2.to_dict('records'),
                "summary": {
                    "total_area_ha": df2['Area_ha'].sum(),
                    "num_classes": len(df2),
                    "top_class": df2.iloc[0][name_col] if len(df2) > 0 else 'Unknown',
                }
            }

            # Comparison if both years have data
            comparison_dict = None
            if not df1.empty and not df2.empty:
                comparison_df = calculate_gains_losses(df1, df2)
                comparison_dict = {
                    "year_start": y1,
                    "year_end": y2,
                    "territory": geom_name,
                    "data": comparison_df.to_dict('records'),
                }

            key = f"geometry::{self.selected_geometry_idx}"
            feat = self.drawn_features[self.selected_geometry_idx]
            self._store_result(key, result_dict, comparison=comparison_dict, geojson_feature=feat)

            # Enable change mask for this geometry
            self.show_change_mask = True
            self.change_mask_year1 = y1
            self.change_mask_year2 = y2
            self.geometry_version += 1

            self.set_active_tab("analysis")
            self.loading_message = ""
            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Full analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"Full geometry analysis error: {e}")

    def set_geometry_analysis_type(self, analysis_type: str):
        """Set analysis type for drawn geometries (mapbiomas or hansen)."""
        if analysis_type in ["mapbiomas", "hansen"]:
            self.geometry_analysis_type = analysis_type

    def set_geometry_analysis_year(self, year: Any):
        """Set year for geometry analysis."""
        try:
            if self.geometry_analysis_type == "mapbiomas":
                self.geometry_analysis_year = int(year)
            else:
                self.geometry_analysis_year = str(year)
        except (ValueError, TypeError):
            pass

    async def run_geometry_analysis(self):
        """Run selected analysis on the selected drawn geometry."""
        if self.selected_geometry_idx is None or self.selected_geometry_idx >= len(self.drawn_features):
            self.error_message = "Please select a geometry first"
            return

        # Zoom to geometry bounds
        try:
            feature = self.drawn_features[self.selected_geometry_idx]
            if "bounds" in feature:
                bounds = feature["bounds"]
                self.map_zoom_bounds = {
                    "min_lat": bounds["min_lat"],
                    "max_lat": bounds["max_lat"],
                    "min_lon": bounds["min_lon"],
                    "max_lon": bounds["max_lon"],
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
        """Run MapBiomas analysis on selected drawn geometry."""
        try:
            from .utils.ee_service_extended import get_ee_service

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
                # Store results for this geometry
                result_dict = {
                    "type": "mapbiomas",
                    "year": self.geometry_analysis_year,
                    "num_classes": len(analysis_df),
                    "total_area_ha": float(analysis_df['Area_ha'].sum()),
                    "data": analysis_df.to_dict('records'),
                }
                self.geometry_analysis_results[self.selected_geometry_idx] = result_dict

                # Also set as active result for viewing
                self.analysis_results = {
                    "type": "mapbiomas",
                    "geometry": f"Custom Geometry #{self.selected_geometry_idx + 1}",
                    "year": self.geometry_analysis_year,
                    "data": analysis_df.to_dict('records'),
                    "summary": {
                        "total_area_ha": float(analysis_df['Area_ha'].sum()),
                        "classes": len(analysis_df)
                    }
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Geometry MapBiomas analysis complete: {len(analysis_df)} classes")

            self.geometry_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.geometry_analysis_pending = False
            logger.error(f"Geometry MapBiomas analysis error: {e}")

    async def run_geometry_hansen_analysis(self):
        """Run Hansen analysis on selected drawn geometry."""
        try:
            from .utils.hansen_analysis import get_hansen_analyzer

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

            result_df = analyzer.get_area_distribution(ee_geom, year=str(self.geometry_analysis_year), scale=30)

            if result_df is None or result_df.empty:
                self.error_message = f"No Hansen data found for year {self.geometry_analysis_year}"
            else:
                # Store results for this geometry
                result_dict = {
                    "type": "hansen",
                    "year": str(self.geometry_analysis_year),
                    "num_classes": len(result_df),
                    "total_area_ha": float(result_df['Area_ha'].sum()),
                    "data": result_df.to_dict('records'),
                }
                self.geometry_analysis_results[self.selected_geometry_idx] = result_dict

                # Also set as active result for viewing
                self.analysis_results = {
                    "type": "hansen",
                    "geometry": f"Custom Geometry #{self.selected_geometry_idx + 1}",
                    "year": str(self.geometry_analysis_year),
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "year": str(self.geometry_analysis_year),
                        "num_classes": len(result_df),
                        "total_area_ha": float(result_df['Area_ha'].sum()),
                    }
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Geometry Hansen analysis complete: {len(result_df)} classes")

            self.geometry_analysis_pending = False

        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.geometry_analysis_pending = False
            logger.error(f"Geometry Hansen analysis error: {e}")

    async def run_mapbiomas_comparison(self):
        """
        Compare MapBiomas data between two years.
        """
        try:
            from .utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from .utils.buffer_utils import convert_geojson_to_ee_geometry
            
            if not self.selected_territory:
                self.error_message = "Please select or upload a geometry first"
                return
            
            # Find the geometry
            geom_feature = None
            for feat in self.all_drawn_features:
                if feat.get('properties', {}).get('name') == self.selected_territory:
                    geom_feature = feat
                    break
            
            if not geom_feature:
                self.error_message = f"Geometry not found: {self.selected_territory}"
                return
            
            self.mapbiomas_analysis_pending = True
            year1 = self.mapbiomas_current_year - 5  # 5 years back
            self.loading_message = f"Comparing MapBiomas {year1} vs {self.mapbiomas_current_year}..."
            
            # Convert geometry
            ee_geom = convert_geojson_to_ee_geometry(geom_feature)
            if not ee_geom:
                self.error_message = "Failed to process geometry"
                self.mapbiomas_analysis_pending = False
                return
            
            # Run comparison
            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return
            
            comparison_df = analyzer.compare_years(
                ee_geom,
                year1,
                self.mapbiomas_current_year,
                scale=30
            )
            
            if comparison_df.empty:
                self.error_message = "Could not compare years"
            else:
                self.mapbiomas_comparison_result = {
                    "year_start": year1,
                    "year_end": self.mapbiomas_current_year,
                    "data": comparison_df.to_dict('records'),
                }
                self.loading_message = ""
            
            self.mapbiomas_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Comparison failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas comparison error: {e}")
    
    async def run_mapbiomas_analysis_on_territory(self):
        """
        Run MapBiomas analysis on selected territory.
        Uses territory geometry from Earth Engine.
        """
        try:
            from .utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from .utils.ee_service_extended import get_ee_service
            
            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return
            
            self.mapbiomas_analysis_pending = True
            self.loading_message = f"Analyzing {self.selected_territory} with MapBiomas {self.mapbiomas_current_year}..."
            
            # Get territory geometry from EE
            ee_service = get_ee_service()
            ee_geom = ee_service.get_territory_geometry(self.selected_territory)
            
            if not ee_geom:
                self.error_message = f"Territory geometry not found: {self.selected_territory}"
                self.mapbiomas_analysis_pending = False
                return
            
            # Run analysis
            analyzer = get_mapbiomas_analyzer()
            if not analyzer.is_available():
                self.error_message = "MapBiomas dataset not available"
                self.mapbiomas_analysis_pending = False
                return
            
            result_df = analyzer.analyze_single_year(
                ee_geom,
                self.mapbiomas_current_year,
                scale=30
            )
            
            if result_df.empty:
                self.error_message = f"No MapBiomas data found for {self.selected_territory}"
            else:
                # Store results
                result_dict = {
                    "type": "mapbiomas",
                    "geometry": self.selected_territory,
                    "year": self.mapbiomas_current_year,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "total_area_ha": result_df['Area_ha'].sum(),
                        "num_classes": len(result_df),
                        "top_class": result_df.iloc[0]['Class_Name'] if len(result_df) > 0 else 'Unknown',
                    }
                }
                # Store in multi-result system
                key = f"territory::{self.selected_territory}"
                geojson_feat = self.territory_geojson_features[0] if self.territory_geojson_features else None
                self._store_result(key, result_dict, geojson_feature=geojson_feat)
                self.set_active_tab("analysis")
                self.loading_message = ""

            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Territory analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas territory analysis error: {e}")

    async def run_hansen_analysis_on_territory(self):
        """
        Run Hansen area distribution analysis on selected territory.
        Uses territory geometry from Earth Engine.
        """
        try:
            from .utils.hansen_analysis import get_hansen_analyzer
            from .utils.ee_service_extended import get_ee_service

            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return

            self.hansen_analysis_pending = True
            self.loading_message = f"Analyzing Hansen {self.hansen_current_year} in {self.selected_territory}..."

            # Get territory geometry from EE
            ee_service = get_ee_service()
            ee_geom = ee_service.get_territory_geometry(self.selected_territory)

            if not ee_geom:
                self.error_message = f"Territory geometry not found: {self.selected_territory}"
                self.hansen_analysis_pending = False
                return

            # Run analysis
            analyzer = get_hansen_analyzer()
            if not analyzer.is_available():
                self.error_message = "Hansen dataset not available"
                self.hansen_analysis_pending = False
                return

            # Get area distribution for selected year
            result_df = analyzer.get_area_distribution(ee_geom, year=self.hansen_current_year, scale=30)

            # Handle DataFrame result
            if result_df is None or result_df.empty:
                self.error_message = f"No Hansen data found for {self.selected_territory} in {self.hansen_current_year}"
            else:
                # Store results in both places
                result_dict = {
                    "type": "hansen",
                    "geometry": self.selected_territory,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "year": self.hansen_current_year,
                        "num_classes": len(result_df),
                        "total_area_ha": float(result_df['Area_ha'].sum()),
                    }
                }
                # Store in multi-result system
                key = f"territory::{self.selected_territory}"
                geojson_feat = self.territory_geojson_features[0] if self.territory_geojson_features else None
                self._store_result(key, result_dict, geojson_feature=geojson_feat)
                self.hansen_analysis_result = result_dict
                self.territory_analysis_year = int(self.hansen_current_year)
                self.set_active_tab("analysis")
                self.loading_message = ""
                logger.info(f"Hansen analysis complete: {len(result_df)} classes, {result_df['Area_ha'].sum():.0f} ha")

            self.hansen_analysis_pending = False

        except Exception as e:
            self.error_message = f"Hansen analysis failed: {str(e)}"
            self.hansen_analysis_pending = False
            logger.error(f"Hansen territory analysis error: {e}")

    # ========================================================================
    # Phase 4: Comparison & Territory Comparison Handlers
    # ========================================================================

    def set_comparison_year1(self, year: str):
        """Set first comparison year."""
        try:
            self.comparison_year1 = int(year)
        except (ValueError, TypeError):
            pass

    def set_comparison_year2(self, year: str):
        """Set second comparison year."""
        try:
            self.comparison_year2 = int(year)
        except (ValueError, TypeError):
            pass

    async def run_territory_comparison(self):
        """
        Run MapBiomas comparison between two years for selected territory.
        Stores results in mapbiomas_comparison_result with gains/losses data.
        """
        try:
            from .utils.mapbiomas_analysis import get_mapbiomas_analyzer
            from .utils.ee_service_extended import get_ee_service
            from .utils.visualization import calculate_gains_losses

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

            # Calculate gains/losses
            comparison_df = calculate_gains_losses(df1, df2)

            # Store territory results as proper dict format (not list)
            self.territory_result = {
                "data": df1.to_dict('records'),
                "summary": {
                    "year": y1,
                    "num_classes": len(df1),
                    "total_area_ha": df1['Area_ha'].sum() if 'Area_ha' in df1.columns else 0,
                }
            }
            self.territory_result_year2 = {
                "data": df2.to_dict('records'),
                "summary": {
                    "year": y2,
                    "num_classes": len(df2),
                    "total_area_ha": df2['Area_ha'].sum() if 'Area_ha' in df2.columns else 0,
                }
            }
            self.territory_name = self.selected_territory
            self.territory_year = y1
            self.territory_year2 = y2
            self.territory_source = "MapBiomas"

            # Store comparison for charts
            comparison_dict = {
                "year_start": y1,
                "year_end": y2,
                "territory": self.selected_territory,
                "data": comparison_df.to_dict('records'),
            }
            self.mapbiomas_comparison_result = comparison_dict

            # Also update main analysis results with year2 data
            name_col = 'Class_Name' if 'Class_Name' in df2.columns else 'Class'
            result_dict = {
                "type": "mapbiomas",
                "geometry": self.selected_territory,
                "year": y2,
                "data": df2.to_dict('records'),
                "summary": {
                    "total_area_ha": df2['Area_ha'].sum(),
                    "num_classes": len(df2),
                    "top_class": df2.iloc[0][name_col] if len(df2) > 0 else 'Unknown',
                }
            }

            # Store in multi-result system with comparison
            key = f"territory::{self.selected_territory}"
            geojson_feat = self.territory_geojson_features[0] if self.territory_geojson_features else None
            self._store_result(key, result_dict, comparison=comparison_dict, geojson_feature=geojson_feat)

            self.loading_message = ""
            self.mapbiomas_analysis_pending = False

        except Exception as e:
            self.error_message = f"Comparison failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"Territory comparison error: {e}")
