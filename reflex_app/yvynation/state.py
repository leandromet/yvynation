"""
Global state management for Yvynation Reflex app.
Reactive state eliminates Streamlit reruns for better performance.
"""

import reflex as rx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import ee
import logging

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
    
    # Geometry Info Popup
    show_geometry_popup: bool = False  # Show/hide geometry info popup
    geometry_popup_info: Dict[str, Any] = {}  # Info to display in popup
    
    # Analysis Results
    analysis_results: Dict[str, Any] = {}  # Empty dict when no analysis is active
    mapbiomas_comparison_result: Optional[Dict[str, Any]] = None
    hansen_comparison_result: Optional[Dict[str, Any]] = None
    analysis_figures: Dict[str, Any] = {}
    
    # Analysis pending/computed flags  
    mapbiomas_analysis_pending: bool = False
    hansen_analysis_pending: bool = False
    
    # UI State
    active_tab: str = "map"  # "map", "analysis", "tutorial", "about"
    sidebar_open: bool = True
    sidebar_width: int = 300  # Sidebar width in pixels
    is_resizing_sidebar: bool = False  # Whether currently resizing
    show_tutorial: bool = True
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
    @rx.var(auto_deps=False, deps=["mapbiomas_displayed_years", "hansen_displayed_layers"])
    def map_html(self) -> str:
        """
        Generate map HTML based on current layer selections.
        Only rebuilds when mapbiomas_displayed_years or hansen_displayed_layers actually change.
        """
        try:
            from .utils.map_builder import build_map
            
            # Call the map builder with current selections
            html = build_map(
                mapbiomas_years=self.mapbiomas_displayed_years or [],
                hansen_layers=self.hansen_displayed_layers or []
            )
            return html
        except Exception as e:
            logger.error(f"Error generating map HTML: {e}")
            import traceback
            traceback.print_exc()
            
            # Return basic map on error
            import folium
            m = folium.Map(location=[-5, -60], zoom_start=4, tiles="OpenStreetMap")
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
        logger.info(f"Removed geometry with _idx={idx}")
    
    def clear_geometries(self):
        """Clear all drawn geometries."""
        self.drawn_features = []
        self.selected_geometry_idx = None
        logger.info("Cleared all geometries")
    
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
        """Initialize application state on first load."""
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
            
            self.data_loaded = True
            self.ee_initialized = True
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
            
            ee_service = get_ee_service()
            
            # Get territory geometry and run analysis
            territory_geom = ee_service.get_territory_geometry(self.selected_territory)
            if territory_geom is None:
                self.error_message = f"Could not find territory: {self.selected_territory}"
                self.mapbiomas_analysis_pending = False
                return
            
            # Run analysis
            analysis_df = ee_service.analyze_mapbiomas(territory_geom, self.mapbiomas_current_year)
            
            if analysis_df.empty:
                self.error_message = f"No data found for this territory"
            else:
                # Store results
                self.analysis_results = {
                    "type": "mapbiomas",
                    "territory": self.selected_territory,
                    "year": self.mapbiomas_current_year,
                    "data": analysis_df.to_dict(),
                }
                self.loading_message = ""
            
            self.mapbiomas_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
    
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
        """Select a territory for analysis."""
        self.selected_territory = territory
        self.pending_territory = None
        
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
        Called by JavaScript after extracting drawn features.
        
        Args:
            geojson_data: JSON string containing GeoJSON features
        """
        try:
            import json
            data = json.loads(geojson_data) if isinstance(geojson_data, str) else geojson_data
            
            # Extract features from GeoJSON FeatureCollection
            features = data.get("features", [])
            
            # Clear existing and load new features
            self.drawn_features = []
            
            for idx, feature in enumerate(features):
                try:
                    geom = feature.get("geometry", {})
                    geom_type = geom.get("type", "Unknown")
                    
                    # Create a displayable feature object
                    feature_obj = {
                        "_idx": idx,
                        "_display_idx": idx + 1,
                        "type": geom_type,
                        "name": f"Geometry {idx + 1}",
                        "geometry": geom,
                        "properties": feature.get("properties", {}),
                        "coordinates": geom.get("coordinates", []),
                    }
                    
                    self.drawn_features.append(feature_obj)
                    self.all_drawn_features.append(feature_obj)
                except Exception as feature_err:
                    logger.warning(f"Error processing feature {idx}: {feature_err}")
            
            # Notify user
            if self.drawn_features:
                self.error_message = f"✓ Loaded {len(self.drawn_features)} geometry/ies"
            else:
                self.error_message = "No geometries found in the map"
                
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
        Create an external buffer from a drawn geometry.
        
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
            import datetime
            
            # Find the geometry
            geom_feature = None
            for feat in self.all_drawn_features:
                if feat.get('properties', {}).get('name') == geometry_name:
                    geom_feature = feat
                    break
            
            if not geom_feature:
                self.error_message = f"Geometry '{geometry_name}' not found"
                return False
            
            # Convert to EE geometry
            ee_geom = convert_geojson_to_ee_geometry(geom_feature)
            if not ee_geom:
                self.error_message = "Failed to convert geometry for buffering"
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
                # Store results
                geom_name = self.drawn_features[self.selected_geometry_idx].get('name', 'Selected Geometry')
                self.analysis_results = {
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
                self.set_active_tab("analysis")
                self.loading_message = ""
            
            self.mapbiomas_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas analysis error: {e}")
    
    async def run_hansen_analysis_on_geometry(self):
        """
        Run Hansen forest change analysis on selected drawn geometry.
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
            self.loading_message = "Analyzing forest change with Hansen..."
            
            # Run analysis
            analyzer = get_hansen_analyzer()
            if not analyzer.is_available():
                self.error_message = "Hansen dataset not available"
                self.hansen_analysis_pending = False
                return
            
            # Analyze forest dynamics
            result_df = analyzer.analyze_forest_dynamics(ee_geom, scale=30)
            
            if result_df.empty:
                self.error_message = "No Hansen data found for this area"
            else:
                # Store results
                geom_name = self.drawn_features[self.selected_geometry_idx].get('name', 'Selected Geometry')
                self.analysis_results = {
                    "type": "hansen",
                    "geometry": geom_name,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "total_tree_cover_2000_ha": result_df['Tree_Cover_2000_ha'].iloc[0] if len(result_df) > 0 else 0,
                        "total_loss_ha": result_df['Loss_ha'].sum(),
                        "total_gain_ha": result_df['Gain_ha'].sum(),
                    }
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
            
            self.hansen_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Hansen analysis failed: {str(e)}"
            self.hansen_analysis_pending = False
            logger.error(f"Hansen analysis error: {e}")
    
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
                self.analysis_results = {
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
                self.set_active_tab("analysis")
                self.loading_message = ""
            
            self.mapbiomas_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Territory analysis failed: {str(e)}"
            self.mapbiomas_analysis_pending = False
            logger.error(f"MapBiomas territory analysis error: {e}")
    
    async def run_hansen_analysis_on_territory(self):
        """
        Run Hansen forest change analysis on selected territory.
        Uses territory geometry from Earth Engine.
        """
        try:
            from .utils.hansen_analysis import get_hansen_analyzer
            from .utils.ee_service_extended import get_ee_service
            
            if not self.selected_territory:
                self.error_message = "Please select a territory first"
                return
            
            self.hansen_analysis_pending = True
            self.loading_message = f"Analyzing forest change in {self.selected_territory}..."
            
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
            
            result_df = analyzer.analyze_forest_dynamics(ee_geom, scale=30)
            
            if result_df.empty:
                self.error_message = f"No Hansen data found for {self.selected_territory}"
            else:
                # Store results
                self.analysis_results = {
                    "type": "hansen",
                    "geometry": self.selected_territory,
                    "data": result_df.to_dict('records'),
                    "summary": {
                        "total_tree_cover_2000_ha": result_df.iloc[0]['Tree_Cover_2000_ha'] if len(result_df) > 0 else 0,
                        "total_loss_ha": result_df['Loss_ha'].sum(),
                        "total_gain_ha": result_df['Gain_ha'].sum(),
                    }
                }
                self.set_active_tab("analysis")
                self.loading_message = ""
            
            self.hansen_analysis_pending = False
        
        except Exception as e:
            self.error_message = f"Hansen analysis failed: {str(e)}"
            self.hansen_analysis_pending = False
            logger.error(f"Hansen territory analysis error: {e}")
