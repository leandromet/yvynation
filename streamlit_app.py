'''
Yvynation - Indigenous Land Monitoring Platform
Interactive Streamlit web app for MapBiomas and Hansen/GLAD analysis
'''

import streamlit as st
import ee
import geemap
import folium
from folium.plugins import Draw, Fullscreen
import streamlit_folium
from streamlit_folium import st_folium
import pandas as pd
import json
import matplotlib.pyplot as plt
from google.oauth2 import service_account

# Import modules
from config import PROJECT_ID, MAPBIOMAS_PALETTE
from app_file import YvynationApp
from mapbiomas_analysis import (
    render_mapbiomas_area_analysis,
    render_mapbiomas_territory_analysis,
    render_mapbiomas_multiyear_analysis,
    render_mapbiomas_change_analysis,
)
from hansen_analysis import (
    render_hansen_area_analysis,
    render_hansen_multiyear_analysis,
    render_hansen_change_analysis,
)
from ui_components import (
    render_map_controls,
    render_hansen_map_controls,
    render_map_instructions,
    render_load_button,
    render_about_section,
)
from visualization import create_mapbiomas_legend

# Page config
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

# Core app state
if "app" not in st.session_state:
    st.session_state.app = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "ee_module" not in st.session_state:
    st.session_state.ee_module = None

# Map state - MapBiomas (Brazil)
if "mapbiomas_center_lat" not in st.session_state:
    st.session_state.mapbiomas_center_lat = -14.2
if "mapbiomas_center_lon" not in st.session_state:
    st.session_state.mapbiomas_center_lon = -51.9
if "mapbiomas_zoom" not in st.session_state:
    st.session_state.mapbiomas_zoom = 4
if "map_object" not in st.session_state:
    st.session_state.map_object = None

# Map state - Hansen (Americas)
if "hansen_center_lat" not in st.session_state:
    st.session_state.hansen_center_lat = 10.0
if "hansen_center_lon" not in st.session_state:
    st.session_state.hansen_center_lon = -80.0
if "hansen_zoom" not in st.session_state:
    st.session_state.hansen_zoom = 3

# Drawn areas
if "drawn_areas" not in st.session_state:
    st.session_state.drawn_areas = {}
if "drawn_area_count" not in st.session_state:
    st.session_state.drawn_area_count = 0
if "selected_drawn_area" not in st.session_state:
    st.session_state.selected_drawn_area = None

# Analysis results - MapBiomas
if "drawn_area_result" not in st.session_state:
    st.session_state.drawn_area_result = None
if "drawn_area_year" not in st.session_state:
    st.session_state.drawn_area_year = None
if "territory_result" not in st.session_state:
    st.session_state.territory_result = None
if "territory_name" not in st.session_state:
    st.session_state.territory_name = None
if "territory_year" not in st.session_state:
    st.session_state.territory_year = 2023
if "multiyear_results" not in st.session_state:
    st.session_state.multiyear_results = None
if "multiyear_start_year" not in st.session_state:
    st.session_state.multiyear_start_year = None
if "multiyear_end_year" not in st.session_state:
    st.session_state.multiyear_end_year = None
if "last_analyzed_geom" not in st.session_state:
    st.session_state.last_analyzed_geom = None
if "last_analyzed_name" not in st.session_state:
    st.session_state.last_analyzed_name = None

# Analysis results - Hansen
if "hansen_area_result" not in st.session_state:
    st.session_state.hansen_area_result = None
if "hansen_area_year" not in st.session_state:
    st.session_state.hansen_area_year = None

# Layer controls
if "split_compare_mode" not in st.session_state:
    st.session_state.split_compare_mode = False
if "split_left_year" not in st.session_state:
    st.session_state.split_left_year = 2023
if "split_right_year" not in st.session_state:
    st.session_state.split_right_year = 1985
if "split_left_opacity" not in st.session_state:
    st.session_state.split_left_opacity = 1.0
if "split_right_opacity" not in st.session_state:
    st.session_state.split_right_opacity = 0.7
if "hansen_year" not in st.session_state:
    st.session_state.hansen_year = "2020"

# ============================================================================
# EARTH ENGINE INITIALIZATION
# ============================================================================

@st.cache_resource
def init_earth_engine():
    """Initialize Earth Engine with service account credentials"""
    try:
        with st.spinner("🔄 Initializing Earth Engine..."):
            has_credentials = False
            
            # Try flat format (Streamlit Cloud)
            if "type" in st.secrets and st.secrets["type"] == "service_account":
                try:
                    creds_dict = dict(st.secrets)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            'https://www.googleapis.com/auth/earthengine',
                            'https://www.googleapis.com/auth/cloud-platform'
                        ]
                    )
                    ee.Initialize(credentials, project=st.secrets.get("ee_project_id", PROJECT_ID))
                    has_credentials = True
                except Exception as e:
                    pass
            
            # Try nested [google] format
            elif "google" in st.secrets:
                try:
                    creds_dict = dict(st.secrets["google"])
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_dict,
                        scopes=[
                            'https://www.googleapis.com/auth/earthengine',
                            'https://www.googleapis.com/auth/cloud-platform'
                        ]
                    )
                    ee.Initialize(credentials, project=st.secrets.get("ee_project_id", PROJECT_ID))
                    has_credentials = True
                except Exception as e:
                    pass
            
            # Fallback to default auth
            if not has_credentials:
                ee.Initialize(project=PROJECT_ID)
        
        return ee
    except Exception as e:
        st.error(f"❌ Earth Engine initialization failed: {e}")
        st.stop()


# Initialize EE
st.session_state.ee_module = init_earth_engine()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("📊 Yvynation")
st.sidebar.markdown("Indigenous Land Monitoring Platform")
st.sidebar.divider()

# Auto-load data on first run
if not st.session_state.data_loaded:
    try:
        app = YvynationApp()
        success = app.load_core_data()
        if success:
            st.session_state.app = app
            st.session_state.data_loaded = True
            st.sidebar.success("✅ Data loaded!")
        else:
            st.sidebar.error("❌ Failed to load data")
    except Exception as e:
        st.sidebar.error(f"❌ Error: {e}")

st.sidebar.divider()

# ============================================================================
# MAP CREATION FUNCTION (MUST BE DEFINED BEFORE TABS)
# ============================================================================

def create_base_folium_map(center, zoom):
    """Create a base folium map with just base layers"""
    from folium.plugins import Draw, Fullscreen
    
    m = folium.Map(
        location=[center[1], center[0]],
        zoom_start=zoom,
        tiles="OpenStreetMap"
    )
    
    # Add drawing tools
    Draw(export=True).add_to(m)
    Fullscreen().add_to(m)
    
    # Add layer control
    folium.LayerControl(position="topleft").add_to(m)
    
    return m

def add_ee_layers_to_map(m, center, zoom, layer1_year, layer1_opacity=1.0, 
                         layer2_year=None, layer2_opacity=0.7, compare_mode=False, data_source="MapBiomas"):
    """Add Earth Engine data layers to an existing folium map"""
    try:
        # Check if app data is loaded
        if not st.session_state.data_loaded or st.session_state.app is None:
            return m
        
        if data_source == "MapBiomas":
            from config import MAPBIOMAS_PALETTE
            
            # Layer 1
            if layer1_year:
                mapbiomas = st.session_state.app.mapbiomas_v9
                if mapbiomas is not None:
                    try:
                        # MapBiomas has bands named 'classification_YEAR'
                        band_name = f'classification_{int(layer1_year)}'
                        classification = mapbiomas.select(band_name)
                        
                        vis_params = {
                            'min': 0,
                            'max': 60,
                            'palette': MAPBIOMAS_PALETTE
                        }
                        map_id = classification.getMapId(vis_params)
                        folium.TileLayer(
                            tiles=map_id['tile_fetcher'].url_format,
                            attr='Map data: MapBiomas',
                            name=f"MapBiomas {layer1_year}",
                            overlay=True,
                            control=True,
                            opacity=layer1_opacity
                        ).add_to(m)
                    except Exception as e:
                        st.warning(f"Could not load MapBiomas layer {layer1_year}: {e}")
            
            # Layer 2 (comparison mode)
            if compare_mode and layer2_year:
                mapbiomas = st.session_state.app.mapbiomas_v9
                if mapbiomas is not None:
                    try:
                        # MapBiomas has bands named 'classification_YEAR'
                        band_name = f'classification_{int(layer2_year)}'
                        classification = mapbiomas.select(band_name)
                        
                        vis_params = {
                            'min': 0,
                            'max': 60,
                            'palette': MAPBIOMAS_PALETTE
                        }
                        map_id = classification.getMapId(vis_params)
                        folium.TileLayer(
                            tiles=map_id['tile_fetcher'].url_format,
                            attr='Map data: MapBiomas',
                            name=f"MapBiomas {layer2_year}",
                            overlay=True,
                            control=True,
                            opacity=layer2_opacity
                        ).add_to(m)
                    except Exception as e:
                        st.warning(f"Could not load MapBiomas layer {layer2_year}: {e}")
            
            # Add indigenous territories layer
            territories = st.session_state.app.territories
            if territories is not None:
                try:
                    map_id_terr = territories.getMapId({'color': '9400D3', 'opacity': 0.7})
                    folium.TileLayer(
                        tiles=map_id_terr['tile_fetcher'].url_format,
                        attr='Map data: Indigenous Territories',
                        name='Indigenous Territories',
                        overlay=True,
                        control=True,
                        opacity=0.7
                    ).add_to(m)
                except Exception as e:
                    st.warning(f"Could not load territories layer: {e}")
        
        elif data_source == "Hansen":
            # Hansen/GLAD layers with ocean mask and proper palette
            from config import HANSEN_DATASETS, HANSEN_OCEAN_MASK, HANSEN_PALETTE
            
            # Ensure year is a string for HANSEN_DATASETS
            year_key = str(layer1_year) if layer1_year else "2020"
            
            # Apply ocean mask to the Hansen image
            landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
            hansen_image = ee.Image(HANSEN_DATASETS[year_key]).updateMask(landmask)
            
            # Use proper HANSEN_PALETTE (256 colors)
            vis_params = {
                'min': 0,
                'max': 255,
                'palette': HANSEN_PALETTE
            }
            map_id = hansen_image.getMapId(vis_params)
            folium.TileLayer(
                tiles=map_id['tile_fetcher'].url_format,
                attr='Map data: Hansen/GLAD',
                name=f"Hansen {year_key}",
                overlay=True,
                control=True,
                opacity=layer1_opacity
            ).add_to(m)
            
            # Add indigenous territories layer on top (dark purple)
            territories = st.session_state.app.territories
            if territories is not None:
                try:
                    map_id_terr = territories.getMapId({'color': '9400D3', 'opacity': 0.7})
                    folium.TileLayer(
                        tiles=map_id_terr['tile_fetcher'].url_format,
                        attr='Map data: Indigenous Territories',
                        name='Indigenous Territories',
                        overlay=True,
                        control=True,
                        opacity=0.7
                    ).add_to(m)
                except Exception as e:
                    st.warning(f"Could not load territories layer: {e}")
        
        return m
        
    except Exception as e:
        st.error(f"Map layer error: {e}")
        return m

def create_ee_folium_map(center, zoom, layer1_year, layer1_opacity=1.0, 
                         layer2_year=None, layer2_opacity=0.7, compare_mode=False, data_source="MapBiomas"):
    """Create a folium map with Earth Engine layers (legacy function for compatibility)"""
    m = create_base_folium_map(center, zoom)
    return add_ee_layers_to_map(m, center, zoom, layer1_year, layer1_opacity, layer2_year, layer2_opacity, compare_mode, data_source)

# ============================================================================
# MAIN CONTENT - TABS
# ============================================================================

st.title("🌎 Yvynation - Land Cover Analysis")

# Create tabs for MapBiomas and Hansen
tab_hansen, tab_mapbiomas = st.tabs(["🌍 Hansen/GLAD (Global)", "🇧🇷 MapBiomas (Brazil)"])

# ============================================================================
# TAB 1: MAPBIOMAS
# ============================================================================

with tab_mapbiomas:
    st.markdown("## MapBiomas Analysis")
    st.info("Analyze Brazilian land cover using MapBiomas Collection 9 data (1985-2023)")
    
    # Split layout: Map on left, Analysis on right
    map_col, analysis_col = st.columns([1, 1.6], gap="large")
    
    # Map column
    with map_col:
        st.subheader("🗺️ Interactive Map")
        
        render_map_controls()
        render_map_instructions()
        
        # Initialize map if not exists
        if st.session_state.map_object is None:
            st.session_state.map_object = create_base_folium_map(
                center=[st.session_state.mapbiomas_center_lon, st.session_state.mapbiomas_center_lat],
                zoom=st.session_state.mapbiomas_zoom
            )
            st.session_state.map_has_data_layers = False
        
        # Add data layers if data is loaded and layers haven't been added
        if st.session_state.data_loaded and not st.session_state.get('map_has_data_layers', False):
            current_layer1_year = st.session_state.split_left_year if st.session_state.split_compare_mode else 2023
            current_layer1_opacity = st.session_state.split_left_opacity if st.session_state.split_compare_mode else 1.0
            current_layer2_year = st.session_state.split_right_year if st.session_state.split_compare_mode else 1985
            current_layer2_opacity = st.session_state.split_right_opacity if st.session_state.split_compare_mode else 0.7
            
            st.session_state.map_object = add_ee_layers_to_map(
                st.session_state.map_object,
                center=[st.session_state.mapbiomas_center_lon, st.session_state.mapbiomas_center_lat],
                zoom=st.session_state.mapbiomas_zoom,
                layer1_year=current_layer1_year,
                layer1_opacity=current_layer1_opacity,
                layer2_year=current_layer2_year,
                layer2_opacity=current_layer2_opacity,
                compare_mode=st.session_state.split_compare_mode,
                data_source="MapBiomas"
            )
            st.session_state.map_has_data_layers = True
        
        # Update layers if settings changed
        elif st.session_state.data_loaded and st.session_state.get('map_has_data_layers', False):
            current_layer1_year = st.session_state.split_left_year if st.session_state.split_compare_mode else 2023
            current_layer1_opacity = st.session_state.split_left_opacity if st.session_state.split_compare_mode else 1.0
            current_layer2_year = st.session_state.split_right_year if st.session_state.split_compare_mode else 1985
            current_layer2_opacity = st.session_state.split_right_opacity if st.session_state.split_compare_mode else 0.7
            
            # Check if we need to recreate the map with new layers
            if (st.session_state.get('last_layer1_year') != current_layer1_year or
                st.session_state.get('last_layer2_year') != current_layer2_year or
                st.session_state.get('last_compare_mode') != st.session_state.split_compare_mode or
                st.session_state.get('last_layer1_opacity') != current_layer1_opacity or
                st.session_state.get('last_layer2_opacity') != current_layer2_opacity):
                
                # Recreate base map and add new layers
                st.session_state.map_object = create_base_folium_map(
                    center=[st.session_state.mapbiomas_center_lon, st.session_state.mapbiomas_center_lat],
                    zoom=st.session_state.mapbiomas_zoom
                )
                st.session_state.map_object = add_ee_layers_to_map(
                    st.session_state.map_object,
                    center=[st.session_state.mapbiomas_center_lon, st.session_state.mapbiomas_center_lat],
                    zoom=st.session_state.mapbiomas_zoom,
                    layer1_year=current_layer1_year,
                    layer1_opacity=current_layer1_opacity,
                    layer2_year=current_layer2_year,
                    layer2_opacity=current_layer2_opacity,
                    compare_mode=st.session_state.split_compare_mode,
                    data_source="MapBiomas"
                )
                
                # Remember current settings
                st.session_state.last_layer1_year = current_layer1_year
                st.session_state.last_layer2_year = current_layer2_year
                st.session_state.last_compare_mode = st.session_state.split_compare_mode
                st.session_state.last_layer1_opacity = current_layer1_opacity
                st.session_state.last_layer2_opacity = current_layer2_opacity
        
        # Display map and capture drawn areas
        if st.session_state.map_object:
            try:
                map_data = st_folium(st.session_state.map_object, width=700, height=600)
                
                if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
                    for idx, drawing in enumerate(map_data["all_drawings"]):
                        geom_data = drawing["geometry"]
                        geom_type = geom_data.get("type", "Unknown")
                        area_name = f"Area {st.session_state.drawn_area_count + idx + 1} ({geom_type})"
                        
                        if area_name not in st.session_state.drawn_areas:
                            st.session_state.drawn_areas[area_name] = geom_data
                            st.session_state.drawn_area_count += 1
                            st.session_state.selected_drawn_area = area_name
                        else:
                            st.session_state.drawn_areas[area_name] = geom_data
            except Exception as e:
                st.warning(f"⏳ Map loading... {str(e)[:50]}")
    
    # Analysis column
    with analysis_col:
        st.subheader("📊 Analysis Tools")
        
        # Area analysis
        with st.expander("📍 Analyze Drawn Area", expanded=True):
            render_mapbiomas_area_analysis()
        
        # Territory analysis
        with st.expander("🏘️ Analyze Indigenous Territory"):
            render_mapbiomas_territory_analysis()
        
        # Multi-year analysis
        with st.expander("📈 Multi-Year Analysis"):
            render_mapbiomas_multiyear_analysis()
        
        # Change detection
        with st.expander("📊 Land Cover Change"):
            render_mapbiomas_change_analysis()

# ============================================================================
# TAB 2: HANSEN
# ============================================================================

with tab_hansen:
    st.markdown("## Hansen/GLAD Global Analysis")
    st.info("Analyze global land cover using Hansen/GLAD data (2000-2020, 30m resolution)")
    
    # Split layout: Map on left, Analysis on right
    map_col_h, analysis_col_h = st.columns([1, 1.6], gap="large")
    
    # Map column
    with map_col_h:
        st.subheader("🗺️ Interactive Map")
        
        render_hansen_map_controls()
        render_map_instructions()
        
        # Initialize map if not exists
        if st.session_state.get('hansen_map_object') is None:
            st.session_state.hansen_map_object = create_base_folium_map(
                center=[st.session_state.hansen_center_lon, st.session_state.hansen_center_lat],
                zoom=st.session_state.hansen_zoom
            )
            st.session_state.hansen_map_has_data_layers = False
        
        # Add data layers if data is loaded and layers haven't been added
        if st.session_state.data_loaded and not st.session_state.get('hansen_map_has_data_layers', False):
            st.session_state.hansen_map_object = add_ee_layers_to_map(
                st.session_state.hansen_map_object,
                center=[st.session_state.hansen_center_lon, st.session_state.hansen_center_lat],
                zoom=st.session_state.hansen_zoom,
                layer1_year=st.session_state.hansen_year,
                data_source="Hansen"
            )
            st.session_state.hansen_map_has_data_layers = True
        
        # Update layers if year changed
        elif st.session_state.data_loaded and st.session_state.get('hansen_map_has_data_layers', False):
            if st.session_state.get('last_hansen_year') != st.session_state.hansen_year:
                # Recreate base map and add new layers
                st.session_state.hansen_map_object = create_base_folium_map(
                    center=[st.session_state.hansen_center_lon, st.session_state.hansen_center_lat],
                    zoom=st.session_state.hansen_zoom
                )
                st.session_state.hansen_map_object = add_ee_layers_to_map(
                    st.session_state.hansen_map_object,
                    center=[st.session_state.hansen_center_lon, st.session_state.hansen_center_lat],
                    zoom=st.session_state.hansen_zoom,
                    layer1_year=st.session_state.hansen_year,
                    data_source="Hansen"
                )
                st.session_state.last_hansen_year = st.session_state.hansen_year
        
        # Display map and capture drawn areas
        if st.session_state.get('hansen_map_object'):
            try:
                map_data = st_folium(st.session_state.hansen_map_object, width=700, height=600)
                
                if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
                    for idx, drawing in enumerate(map_data["all_drawings"]):
                        geom_data = drawing["geometry"]
                        geom_type = geom_data.get("type", "Unknown")
                        area_name = f"Hansen Area {idx + 1} ({geom_type})"
                        
                        if area_name not in st.session_state.drawn_areas:
                            st.session_state.drawn_areas[area_name] = geom_data
                            st.session_state.selected_drawn_area = area_name
                        else:
                            st.session_state.drawn_areas[area_name] = geom_data
            except Exception as e:
                st.warning(f"⏳ Map loading... {str(e)[:50]}")
    
    # Analysis column
    with analysis_col_h:
        st.subheader("📊 Analysis Tools")
        
        # Area analysis
        with st.expander("📍 Analyze Drawn Area", expanded=True):
            render_hansen_area_analysis()
        
        # Multi-year comparison
        with st.expander("📈 Compare Snapshots"):
            render_hansen_multiyear_analysis()
        
        # Change detection
        with st.expander("📊 Change Analysis"):
            render_hansen_change_analysis()

