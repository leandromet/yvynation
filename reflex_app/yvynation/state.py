"""
Global state management for Yvynation Reflex app.
Reactive state eliminates Streamlit reruns for better performance.
"""

import reflex as rx
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import ee


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
    data_loaded: bool = False
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
    
    hansen_years_enabled: Dict[str, bool] = {}
    hansen_current_year: str = "2020"
    
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
    
    # Drawn Features & Buffers
    drawn_features: List[Dict[str, Any]] = []
    all_drawn_features: List[Dict[str, Any]] = []
    buffer_geometries: Dict[str, BufferGeometry] = {}
    current_buffer_for_analysis: Optional[str] = None
    buffer_compare_mode: bool = False
    
    # Analysis Results
    analysis_results: Optional[Dict[str, Any]] = None
    mapbiomas_comparison_result: Optional[Dict[str, Any]] = None
    hansen_comparison_result: Optional[Dict[str, Any]] = None
    analysis_figures: Dict[str, Any] = {}
    
    # UI State
    active_tab: str = "map"  # "map", "analysis", "tutorial", "about"
    sidebar_open: bool = True
    show_tutorial: bool = True
    use_consolidated_classes: bool = True
    
    # Pending confirmations (for territory selection)
    pending_territory: Optional[str] = None
    
    # ========================================================================
    # Event Handlers for State Updates (no reruns, direct updates)
    # ========================================================================
    
    def set_language(self, lang: str):
        """Change application language."""
        self.language = lang
        
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open
        
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
        self.drawn_features.append(feature)
        self.all_drawn_features.append(feature)
        
    def clear_drawn_features(self):
        """Clear all drawn features."""
        self.drawn_features = []
        
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
        
    def mark_data_loaded(self):
        """Mark that core data has been loaded."""
        self.data_loaded = True
        self.ee_initialized = True
