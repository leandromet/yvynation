'''
Yvynation - Indigenous Land Monitoring Platform
Interactive Streamlit web app for MapBiomas and Hansen/GLAD analysis
'''

import streamlit as st

# Performance optimization - prevent unnecessary reruns
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    render_mapbiomas_legend,
    render_hansen_legend,
)
from visualization import create_mapbiomas_legend

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

# Map state - MapBiomas
if "mapbiomas_map_center_lat" not in st.session_state:
    st.session_state.mapbiomas_map_center_lat = -4.5
if "mapbiomas_map_center_lon" not in st.session_state:
    st.session_state.mapbiomas_map_center_lon = -45.3
if "mapbiomas_map_zoom" not in st.session_state:
    st.session_state.mapbiomas_map_zoom = 7
if "mapbiomas_map_object" not in st.session_state:
    st.session_state.mapbiomas_map_object = None

# Map state - Hansen
if "hansen_map_center_lat" not in st.session_state:
    st.session_state.hansen_map_center_lat = -4.5
if "hansen_map_center_lon" not in st.session_state:
    st.session_state.hansen_map_center_lon = -45.3
if "hansen_map_zoom" not in st.session_state:
    st.session_state.hansen_map_zoom = 7
if "hansen_map_object" not in st.session_state:
    st.session_state.hansen_map_object = None

# Drawn areas - MapBiomas
if "mapbiomas_drawn_areas" not in st.session_state:
    st.session_state.mapbiomas_drawn_areas = {}
if "mapbiomas_drawn_area_count" not in st.session_state:
    st.session_state.mapbiomas_drawn_area_count = 0
if "mapbiomas_selected_drawn_area" not in st.session_state:
    st.session_state.mapbiomas_selected_drawn_area = None
if "mapbiomas_drawn_geometry_hashes" not in st.session_state:
    st.session_state.mapbiomas_drawn_geometry_hashes = set()
if "mapbiomas_should_zoom_to_feature" not in st.session_state:
    st.session_state.mapbiomas_should_zoom_to_feature = False
if "mapbiomas_zoom_bounds" not in st.session_state:
    st.session_state.mapbiomas_zoom_bounds = None

# Drawn areas - Hansen
if "hansen_drawn_areas" not in st.session_state:
    st.session_state.hansen_drawn_areas = {}
if "hansen_drawn_area_count" not in st.session_state:
    st.session_state.hansen_drawn_area_count = 0
if "hansen_selected_drawn_area" not in st.session_state:
    st.session_state.hansen_selected_drawn_area = None
if "hansen_drawn_geometry_hashes" not in st.session_state:
    st.session_state.hansen_drawn_geometry_hashes = set()
if "hansen_should_zoom_to_feature" not in st.session_state:
    st.session_state.hansen_should_zoom_to_feature = False
if "hansen_zoom_bounds" not in st.session_state:
    st.session_state.hansen_zoom_bounds = None

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
    st.session_state.territory_year = None
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
if "last_hansen_year" not in st.session_state:
    st.session_state.last_hansen_year = None
if "last_data_source" not in st.session_state:
    st.session_state.last_data_source = None

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

# Load data button
if st.sidebar.button("Load Core Data", use_container_width=True):
    with st.spinner("📦 Loading MapBiomas and territories..."):
        try:
            app = YvynationApp()
            # Load core data (MapBiomas, territories)
            success = app.load_core_data()
            if success:
                st.session_state.app = app
                st.session_state.data_loaded = True
                st.sidebar.success("✅ Data loaded successfully!")
            else:
                st.sidebar.error("❌ Failed to load MapBiomas or territories")
        except Exception as e:
            st.sidebar.error(f"❌ Failed to load data: {e}")

if not st.session_state.data_loaded:
    st.sidebar.warning("⚠️ Click 'Load Core Data' to begin")

st.sidebar.divider()

# ============================================================================
# MAP CREATION FUNCTION (MUST BE DEFINED BEFORE TABS)
# ============================================================================

def create_ee_folium_map(center, zoom, layer1_year, layer1_opacity=1.0, 
                         layer2_year=None, layer2_opacity=0.7, compare_mode=False, data_source="MapBiomas"):
    """Create a folium map with Earth Engine layers"""
    try:
        # Check if app data is loaded
        if not st.session_state.data_loaded or st.session_state.app is None:
            st.error("❌ Data not loaded. Click 'Load Core Data' in the sidebar first.")
            return None
        
        # Create folium map
        m = folium.Map(
            location=[center[1], center[0]],
            zoom_start=zoom,
            tiles="OpenStreetMap"
        )
        
        if data_source == "MapBiomas":
            # MapBiomas layers
            mapbiomas = st.session_state.app.mapbiomas_v9
            if mapbiomas is None:
                st.error("❌ MapBiomas data not loaded. Please click 'Load Core Data' again.")
                return None
            
            # Layer 1 (default: 2023)
            if isinstance(layer1_year, int):
                layer1_band = f'classification_{layer1_year}'
                layer1_image = mapbiomas.select(layer1_band)
                
                # Get tile URL from EE image
                map_id = layer1_image.getMapId({'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE})
                folium.TileLayer(
                    tiles=map_id['tile_fetcher'].url_format,
                    attr='Map data: MapBiomas',
                    name=f"MapBiomas {layer1_year}",
                    overlay=True,
                    control=True,
                    opacity=layer1_opacity
                ).add_to(m)
            
            # Layer 2 (comparison mode, default: 1985)
            if compare_mode and layer2_year:
                layer2_band = f'classification_{layer2_year}'
                layer2_image = mapbiomas.select(layer2_band)
                
                map_id2 = layer2_image.getMapId({'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE})
                folium.TileLayer(
                    tiles=map_id2['tile_fetcher'].url_format,
                    attr='Map data: MapBiomas',
                    name=f"MapBiomas {layer2_year}",
                    overlay=True,
                    control=True,
                    opacity=layer2_opacity
                ).add_to(m)
            
            # Add indigenous territories layer on top (dark purple)
            territories = st.session_state.app.territories
            if territories is not None:
                try:
                    territories_image = ee.Image().paint(territories, 1, 2)
                    map_id_terr = territories_image.getMapId({'min': 0, 'max': 1, 'palette': ['00000000', '4B0082']})
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
                    territories_image = ee.Image().paint(territories, 1, 2)
                    map_id_terr = territories_image.getMapId({'min': 0, 'max': 1, 'palette': ['00000000', '4B0082']})
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
        
        # Add drawing tools
        Draw(export=True).add_to(m)
        Fullscreen().add_to(m)
        folium.LayerControl().add_to(m)
        
        return m
    
    except Exception as e:
        st.error(f"Map creation error: {e}")
        return None

# ============================================================================
# MAIN CONTENT - TABS
# ============================================================================

st.title("🌎 Yvynation - Land Cover Analysis")

# Create tabs for MapBiomas and Hansen
tab_mapbiomas, tab_hansen = st.tabs(["🇧🇷 MapBiomas (Brazil)", "🌍 Hansen/GLAD (Global)"])

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
        
        # Create MapBiomas map
        if st.session_state.data_loaded:
            try:
                current_layer1_year = st.session_state.split_left_year if st.session_state.split_compare_mode else 2023
                current_layer1_opacity = st.session_state.split_left_opacity if st.session_state.split_compare_mode else 1.0
                current_layer2_year = st.session_state.split_right_year if st.session_state.split_compare_mode else 1985
                current_layer2_opacity = st.session_state.split_right_opacity if st.session_state.split_compare_mode else 0.7
                
                # Recreate map if layers or compare mode changed
                if (st.session_state.mapbiomas_map_object is None or 
                    st.session_state.get('mapbiomas_last_layer1_year') != current_layer1_year or
                    st.session_state.get('mapbiomas_last_layer2_year') != current_layer2_year or
                    st.session_state.get('mapbiomas_last_compare_mode') != st.session_state.split_compare_mode or
                    st.session_state.get('mapbiomas_last_layer1_opacity') != current_layer1_opacity or
                    st.session_state.get('mapbiomas_last_layer2_opacity') != current_layer2_opacity):
                    
                    st.session_state.mapbiomas_map_object = create_ee_folium_map(
                        center=[st.session_state.mapbiomas_map_center_lon, st.session_state.mapbiomas_map_center_lat],
                        zoom=st.session_state.mapbiomas_map_zoom,
                        layer1_year=current_layer1_year,
                        layer1_opacity=current_layer1_opacity,
                        layer2_year=current_layer2_year,
                        layer2_opacity=current_layer2_opacity,
                        compare_mode=st.session_state.split_compare_mode,
                        data_source="MapBiomas"
                    )
                    
                    # Remember current settings
                    st.session_state.mapbiomas_last_layer1_year = current_layer1_year
                    st.session_state.mapbiomas_last_layer2_year = current_layer2_year
                    st.session_state.mapbiomas_last_compare_mode = st.session_state.split_compare_mode
                    st.session_state.mapbiomas_last_layer1_opacity = current_layer1_opacity
                    st.session_state.mapbiomas_last_layer2_opacity = current_layer2_opacity
                
                # Apply zoom to feature if needed
                if st.session_state.mapbiomas_should_zoom_to_feature and st.session_state.mapbiomas_zoom_bounds:
                    bounds = st.session_state.mapbiomas_zoom_bounds
                    coords = bounds.get('coordinates')
                    if coords and len(coords) > 0:
                        try:
                            # Extract all coordinate pairs from the polygon ring
                            coord_list = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
                            lons = [c[0] for c in coord_list]
                            lats = [c[1] for c in coord_list]
                            min_lon, max_lon = min(lons), max(lons)
                            min_lat, max_lat = min(lats), max(lats)
                            
                            # Update map center and zoom to fit bounds
                            center_lon = (min_lon + max_lon) / 2
                            center_lat = (min_lat + max_lat) / 2
                            st.session_state.mapbiomas_map_center_lon = center_lon
                            st.session_state.mapbiomas_map_center_lat = center_lat
                            # Calculate appropriate zoom level (rough approximation)
                            import math
                            lon_diff = max_lon - min_lon
                            lat_diff = max_lat - min_lat
                            max_diff = max(lon_diff, lat_diff)
                            if max_diff > 0:
                                zoom = int(12 - math.log2(max_diff * 110))  # 110 km per degree approx
                                zoom = max(4, min(zoom, 13))  # Clamp between 4 and 13
                                st.session_state.mapbiomas_map_zoom = zoom
                        except (IndexError, TypeError, ValueError) as e:
                            st.warning(f"Could not parse bounds: {e}")
                    st.session_state.mapbiomas_should_zoom_to_feature = False
                    st.session_state.mapbiomas_zoom_bounds = None
                    # Recreate map with new center/zoom
                    st.session_state.mapbiomas_map_object = create_ee_folium_map(
                        center=[st.session_state.mapbiomas_map_center_lon, st.session_state.mapbiomas_map_center_lat],
                        zoom=st.session_state.mapbiomas_map_zoom,
                        layer1_year=current_layer1_year,
                        layer1_opacity=current_layer1_opacity,
                        layer2_year=current_layer2_year,
                        layer2_opacity=current_layer2_opacity,
                        compare_mode=st.session_state.split_compare_mode,
                        data_source="MapBiomas"
                    )
                
                # Display map and capture drawn areas
                map_data = st_folium(st.session_state.mapbiomas_map_object, width=700, height=600)
                
                if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
                    import hashlib
                    import json
                    
                    for idx, drawing in enumerate(map_data["all_drawings"]):
                        geom_data = drawing["geometry"]
                        geom_type = geom_data.get("type", "Unknown")
                        
                        # Create a hash of the geometry to prevent duplicates
                        geom_hash = hashlib.md5(json.dumps(geom_data, sort_keys=True).encode()).hexdigest()
                        
                        # Only add if this geometry hasn't been added before
                        if geom_hash not in st.session_state.mapbiomas_drawn_geometry_hashes:
                            st.session_state.mapbiomas_drawn_area_count += 1
                            area_name = f"Area {st.session_state.mapbiomas_drawn_area_count} ({geom_type})"
                            st.session_state.mapbiomas_drawn_areas[area_name] = geom_data
                            st.session_state.mapbiomas_drawn_geometry_hashes.add(geom_hash)
                            st.session_state.mapbiomas_selected_drawn_area = area_name
                
                # Display legend below map
                st.divider()
                render_mapbiomas_legend()
                
            except Exception as e:
                st.warning(f"⏳ Map loading... {str(e)[:50]}")
        else:
            st.info("Click 'Load Core Data' in the sidebar to enable the map")
    
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
        
        # Create Hansen map
        if st.session_state.data_loaded:
            try:
                # Check if need to recreate map
                if (st.session_state.hansen_map_object is None or
                    st.session_state.get('hansen_last_hansen_year') != st.session_state.hansen_year or
                    st.session_state.get('hansen_last_data_source') != 'Hansen'):
                    
                    st.session_state.hansen_map_object = create_ee_folium_map(
                        center=[st.session_state.hansen_map_center_lon, st.session_state.hansen_map_center_lat],
                        zoom=st.session_state.hansen_map_zoom,
                        layer1_year=st.session_state.hansen_year,
                        data_source="Hansen"
                    )
                    st.session_state.hansen_last_hansen_year = st.session_state.hansen_year
                    st.session_state.hansen_last_data_source = 'Hansen'
                
                # Apply zoom to feature if needed
                if st.session_state.hansen_should_zoom_to_feature and st.session_state.hansen_zoom_bounds:
                    bounds = st.session_state.hansen_zoom_bounds
                    coords = bounds.get('coordinates')
                    if coords and len(coords) > 0:
                        try:
                            # Extract all coordinate pairs from the polygon ring
                            coord_list = coords[0] if isinstance(coords[0][0], (list, tuple)) else coords
                            lons = [c[0] for c in coord_list]
                            lats = [c[1] for c in coord_list]
                            min_lon, max_lon = min(lons), max(lons)
                            min_lat, max_lat = min(lats), max(lats)
                            
                            center_lon = (min_lon + max_lon) / 2
                            center_lat = (min_lat + max_lat) / 2
                            st.session_state.hansen_map_center_lon = center_lon
                            st.session_state.hansen_map_center_lat = center_lat
                            import math
                            lon_diff = max_lon - min_lon
                            lat_diff = max_lat - min_lat
                            max_diff = max(lon_diff, lat_diff)
                            if max_diff > 0:
                                zoom = int(12 - math.log2(max_diff * 110))
                                zoom = max(4, min(zoom, 13))
                                st.session_state.hansen_map_zoom = zoom
                        except (IndexError, TypeError, ValueError) as e:
                            st.warning(f"Could not parse bounds: {e}")
                    st.session_state.hansen_should_zoom_to_feature = False
                    st.session_state.hansen_zoom_bounds = None
                    st.session_state.hansen_map_object = create_ee_folium_map(
                        center=[st.session_state.hansen_map_center_lon, st.session_state.hansen_map_center_lat],
                        zoom=st.session_state.hansen_map_zoom,
                        layer1_year=st.session_state.hansen_year,
                        data_source="Hansen"
                    )
                
                # Display map and capture drawn areas
                map_data = st_folium(st.session_state.hansen_map_object, width=700, height=600)
                
                if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
                    import hashlib
                    import json
                    
                    for idx, drawing in enumerate(map_data["all_drawings"]):
                        geom_data = drawing["geometry"]
                        geom_type = geom_data.get("type", "Unknown")
                        
                        # Create a hash of the geometry to prevent duplicates
                        geom_hash = hashlib.md5(json.dumps(geom_data, sort_keys=True).encode()).hexdigest()
                        
                        # Only add if this geometry hasn't been added before
                        if geom_hash not in st.session_state.hansen_drawn_geometry_hashes:
                            st.session_state.hansen_drawn_area_count += 1
                            area_name = f"Area {st.session_state.hansen_drawn_area_count} ({geom_type})"
                            st.session_state.hansen_drawn_areas[area_name] = geom_data
                            st.session_state.hansen_drawn_geometry_hashes.add(geom_hash)
                            st.session_state.hansen_selected_drawn_area = area_name
                
                # Display legend below map
                st.divider()
                render_hansen_legend()
                
            except Exception as e:
                st.warning(f"⏳ Map loading... {str(e)[:50]}")
        else:
            st.info("Click 'Load Core Data' in the sidebar to enable the map")
    
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

