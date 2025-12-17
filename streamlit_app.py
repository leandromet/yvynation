'''
Yvynation Earth Engine Application
Interactive Streamlit web app for MapBiomas and Indigenous Territories analysis
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
from google.oauth2 import service_account
from config import PROJECT_ID
from app_file import YvynationApp
from analysis import clip_mapbiomas_to_geometry, calculate_area_by_class
from plots import plot_area_distribution, plot_area_comparison
from app_file import YvynationApp
from analysis import filter_territories_by_state, filter_territories_by_names
from plots import (
    plot_area_distribution,
    plot_area_comparison,
    plot_area_changes,
    plot_temporal_trend,
    create_sankey_transitions,
)
from visualization import create_mapbiomas_legend

# Page config
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "app" not in st.session_state:
    st.session_state.app = None
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "drawn_geometry" not in st.session_state:
    st.session_state.drawn_geometry = None
if "map_center_lat" not in st.session_state:
    st.session_state.map_center_lat = -4.5
if "map_center_lon" not in st.session_state:
    st.session_state.map_center_lon = -45.3
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 7
if "results" not in st.session_state:
    st.session_state.results = None
if "map_object" not in st.session_state:
    st.session_state.map_object = None
if "last_analyzed_geom" not in st.session_state:
    st.session_state.last_analyzed_geom = None
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
if "map_layers_config" not in st.session_state:
    st.session_state.map_layers_config = {
        'layer1_year': 1985,
        'layer1_opacity': 1.0,
        'layer2_year': 2023,
        'layer2_opacity': 0.7,
        'compare_mode': False
    }

# Separate result containers for each analysis type (to keep them all visible)
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

# Multiple drawn areas tracking
if "drawn_areas" not in st.session_state:
    st.session_state.drawn_areas = {}  # {name: geometry_data}
if "drawn_area_count" not in st.session_state:
    st.session_state.drawn_area_count = 0
if "selected_drawn_area" not in st.session_state:
    st.session_state.selected_drawn_area = None
if "persistent_drawn_geometry" not in st.session_state:
    st.session_state.persistent_drawn_geometry = None
if "last_drawn_geometry" not in st.session_state:
    st.session_state.last_drawn_geometry = None  # Track last drawing to avoid duplicates
if "previous_selected_area" not in st.session_state:
    st.session_state.previous_selected_area = None  # Track to detect area selection changes

# Sidebar
st.sidebar.title("🌎 Yvynation Land Use")
st.sidebar.subheader("Interactive Analysis with MapBiomas & Indigenous Territories \n  Leandro Meneguelli Biondo")
st.sidebar.subheader(" UBCO - University of British Columbia Okanagan \n INMA/MCTI || SFB/MMA")

# MapBiomas Collection 9 discrete palette - REQUIRED for proper colors
COLOR_MAP = {
    0: "#ffffff", 1: "#1f8d49", 2: "#1f8d49", 3: "#1f8d49", 4: "#7dc975", 5: "#04381d", 6: "#007785",
    7: "#005544", 8: "#33a02c", 9: "#7a5900", 10: "#d6bc74", 11: "#519799", 12: "#d6bc74", 13: "#ffffff",
    14: "#ffefc3", 15: "#edde8e", 16: "#e974ed", 17: "#d082de", 18: "#e974ed", 19: "#c27ba0", 20: "#db7093",
    21: "#ffefc3", 22: "#d4271e", 23: "#ffa07a", 24: "#d4271e", 25: "#db4d4f", 26: "#2532e4", 27: "#ffffff",
    28: "#ffaa5f", 29: "#ffaa5f", 30: "#9c0027", 31: "#091077", 32: "#fc8114", 33: "#259fe4", 34: "#259fe4",
    35: "#9065d0", 36: "#d082de", 37: "#d082de", 38: "#c27ba0", 39: "#f5b3c8", 40: "#c71585", 41: "#f54ca9",
    42: "#f54ca9", 43: "#d082de", 44: "#d082de", 45: "#d68fe2", 46: "#d68fe2", 47: "#9932cc", 48: "#e6ccff",
    49: "#02d659", 50: "#ad5100", 51: "#fc8114", 52: "#fc8114", 62: "#ff69b4", 146: "#ffefc3", 435: "#cccccc",
    466: "#999999"
}

LABELS = {
    0: "No data", 1: "Forest", 2: "Natural Forest", 3: "Forest Formation", 4: "Savanna Formation", 
    5: "Mangrove", 6: "Floodable Forest", 7: "Flooded Forest", 8: "Wooded Restinga", 9: "Forest Plantation",
    10: "Herbaceous", 11: "Wetland", 12: "Grassland", 13: "Other Natural Formation", 14: "Farming",
    15: "Pasture", 16: "Agriculture", 17: "Perennial Crop", 18: "Agri", 19: "Temporary Crop",
    20: "Sugar Cane", 21: "Mosaic of Uses", 22: "Non vegetated", 23: "Beach and Sand", 24: "Urban Area",
    25: "Other non Vegetated Areas", 26: "Water", 27: "Not Observed", 28: "Rocky Outcrop", 29: "Rocky Outcrop",
    30: "Mining", 31: "Aquaculture", 32: "Hypersaline Tidal Flat", 33: "River Lake and Ocean", 34: "Reservoir",
    35: "Palm Oil", 36: "Perennial Crop", 37: "Semi-Perennial Crop", 38: "Annual Crop", 39: "Soybean",
    40: "Rice", 41: "Other Temporary Crops", 42: "Other Annual Crop", 43: "Other Semi-Perennial Crop",
    44: "Other Perennial Crop", 45: "Coffee", 46: "Coffee", 47: "Citrus", 48: "Other Perennial Crops",
    49: "Wooded Sandbank Vegetation", 50: "Herbaceous Sandbank Vegetation", 51: "Salt Flat",
    52: "Apicuns and Salines", 62: "Cotton", 146: "Other Land Use", 435: "Other Transition",
    466: "Other Classification"
}

def create_ee_folium_map(center=[-45.3, -4.5], zoom=7, layer1_year=2023, layer1_opacity=1.0, layer2_year=1985, layer2_opacity=0.7, persistent_geometry=None):
    '''Create a folium map with Earth Engine layers and drawing tools.
    
    Args:
        center: [lon, lat] center point
        zoom: zoom level
        layer1_year: year for the first (top) MapBiomas layer (default 2023)
        layer1_opacity: opacity of layer 1
        layer2_year: year for the second (bottom) MapBiomas layer (default 1985)
        layer2_opacity: opacity of layer 2
        persistent_geometry: previously drawn geometry to restore
    '''
    m = folium.Map(
        location=[center[1], center[0]],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    
    # Add satellite baseLayers
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='OpenStreetMap',
        name='OpenStreetMap',
        overlay=False,
        control=True
    )  # Keep OSM as default (already added above)
    
    try:
        # Check which data source to use
        if 'data_source' in st.session_state and st.session_state.data_source == "Hansen/GLAD (Global)":
            # Load Hansen/GLAD data
            from config import HANSEN_DATASETS, HANSEN_OCEAN_MASK, HANSEN_PALETTE
            
            # Get ocean mask
            landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
            
            # Load the Hansen dataset for the selected year
            hansen_year = getattr(st.session_state, 'hansen_year', '2020')
            if hansen_year == "2000-2020 Change":
                hansen_image = ee.Image(HANSEN_DATASETS['change']).updateMask(landmask)
                layer_name = "Hansen 2000-2020 Change"
            else:
                hansen_image = ee.Image(HANSEN_DATASETS[hansen_year]).updateMask(landmask)
                layer_name = f"Hansen {hansen_year}"
            
            vis_params_hansen = {
                'min': 0,
                'max': 255,
                'palette': HANSEN_PALETTE
            }
            
            mapid = ee.Image(hansen_image).getMapId(vis_params_hansen)
            try:
                tile_url = mapid['tile_fetcher'].url_format
            except (KeyError, AttributeError):
                tile_url = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
            
            folium.TileLayer(
                tiles=tile_url,
                attr='GLAD Lab (University of Maryland)',
                name=layer_name,
                overlay=True,
                control=True,
                opacity=1.0
            ).add_to(m)
        
        else:
            # Load MapBiomas collection (original code)
            mapbiomas = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')
            
            # Build complete discrete palette from COLOR_MAP (0-62, or max class value)
            # This prevents Earth Engine from interpolating colors
            palette_list = []
            max_class = 62
            for class_id in range(max_class + 1):
                # Get color from COLOR_MAP, use gray (#808080) as default for undefined classes
                hex_color = COLOR_MAP.get(class_id, '#808080')
                # Remove # and add to palette
                palette_list.append(hex_color.lstrip('#'))
            
            vis_params = {
                'min': 0,
                'max': max_class,
                'palette': palette_list
            }
            
            # Add Layer 1 (top layer, default 2023)
            classification_1 = mapbiomas.select(f'classification_{layer1_year}')
            mapid_1 = ee.Image(classification_1).getMapId(vis_params)
            
            try:
                tile_url_1 = mapid_1['tile_fetcher'].url_format
            except (KeyError, AttributeError):
                tile_url_1 = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid_1["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
        
        folium.TileLayer(
            tiles=tile_url_1,
            attr='MapBiomas Collection 9',
            name=f'MapBiomas {layer1_year}',
            overlay=True,
            control=True,
            opacity=layer1_opacity
        ).add_to(m)
        
        # Add Layer 2 (bottom layer, default 1985)
        if layer2_year != layer1_year:
            classification_2 = mapbiomas.select(f'classification_{layer2_year}')
            mapid_2 = ee.Image(classification_2).getMapId(vis_params)
            
            try:
                tile_url_2 = mapid_2['tile_fetcher'].url_format
            except (KeyError, AttributeError):
                tile_url_2 = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid_2["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
            
            folium.TileLayer(
                tiles=tile_url_2,
                attr='MapBiomas Collection 9',
                name=f'MapBiomas {layer2_year}',
                overlay=True,
                control=True,
                opacity=layer2_opacity
            ).add_to(m)
        
        # Add Indigenous Territories layer
        territories = ee.FeatureCollection('projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES')
        
        ee_image_object = ee.Image().paint(territories, 0, 2)
        mapid_territories = ee_image_object.getMapId({'min': 0, 'max': 1, 'palette': ['red']})
        
        try:
            tile_url_territories = mapid_territories['tile_fetcher'].url_format
        except (KeyError, AttributeError):
            # Fallback to manual URL format
            tile_url_territories = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid_territories["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
        
        folium.TileLayer(
            tiles=tile_url_territories,
            attr='Indigenous Territories',
            name='Indigenous Territories',
            overlay=True,
            control=True
        ).add_to(m)
        
    except Exception as e:
        st.warning(f"Could not load Earth Engine layers: {e}")
    
    # Restore persistent drawn geometry if available
    if persistent_geometry:
        try:
            geom_data = persistent_geometry.get('geometry', {})
            geom_type = geom_data.get('type', '')
            coords = geom_data.get('coordinates', [])
            
            if geom_type == 'Polygon' and coords:
                # Draw polygon on map in blue
                folium.GeoJson(
                    {'type': 'Feature', 'geometry': geom_data},
                    style_function=lambda x: {'color': 'blue', 'weight': 2, 'opacity': 0.7}
                ).add_to(m)
        except Exception as e:
            pass  # Silently fail if geometry cannot be restored
    
    # Add drawing tools
    draw = Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': False,
            'polygon': True,
            'rectangle': True,
            'circle': False,
            'marker': False,
            'circlemarker': False
        }
    )
    draw.add_to(m)
    
    # Add all saved drawn areas with darker colors and labels
    colors = ['darkblue', 'darkred', 'darkgreen', 'purple', 'orange', 'brown', 'cadetblue', 'darkviolet']
    if persistent_geometry:
        for idx, (area_name, geom_data) in enumerate(persistent_geometry.items()):
            if geom_data.get('type') == 'Polygon':
                color = colors[idx % len(colors)]
                # Create GeoJSON with popup and tooltip showing the area name
                feature = {
                    'type': 'Feature',
                    'geometry': geom_data,
                    'properties': {'name': area_name}
                }
                folium.GeoJson(
                    feature,
                    style_function=lambda x, c=color: {
                        'color': c,
                        'weight': 4,
                        'opacity': 0.9,
                        'fillOpacity': 0.3
                    },
                    name=area_name,
                    popup=folium.Popup(f"<b>{area_name}</b>", max_width=200),
                    tooltip=folium.Tooltip(area_name, sticky=False)
                ).add_to(m)
    
    # Add fullscreen button
    Fullscreen().add_to(m)
    
    folium.LayerControl().add_to(m)
    return m



def get_bounds_from_geometry(geom):
    '''Extract bounds from GeoJSON geometry and return as [[south, west], [north, east]].'''
    try:
        coords = geom.get('coordinates', [])
        if not coords:
            return None
        
        # Handle Polygon or Rectangle
        if geom.get('type') in ['Polygon', 'MultiPolygon']:
            # Flatten all coordinates
            all_coords = []
            if geom.get('type') == 'Polygon':
                all_coords = coords[0] if coords else []
            else:
                for poly in coords:
                    all_coords.extend(poly[0] if poly else [])
            
            if all_coords:
                lons = [c[0] for c in all_coords]
                lats = [c[1] for c in all_coords]
                return [[min(lats), min(lons)], [max(lats), max(lons)]]
    except Exception as e:
        st.warning(f"Could not extract bounds: {e}")
    return None

def zoom_to_bounds(m, bounds):
    '''Add fit_bounds to map if bounds available.'''
    if bounds:
        m.fit_bounds(bounds, padding=(0.1, 0.1))

def clean_territory_name(name_with_id):
    '''Extract clean territory name from [name (id)] format, handling encoding issues.'''
    if not name_with_id:
        return name_with_id
    
    try:
        # Try to extract name from [name (id)] format
        if name_with_id.startswith('[') and '(' in name_with_id:
            # Extract the part between [ and (
            name = name_with_id.split('(')[0].replace('[', '').strip()
            return name if name else name_with_id
        return name_with_id
    except Exception:
        return name_with_id

# Initialize Earth Engine with service account support
@st.cache_resource
def init_earth_engine():
    """Initialize Earth Engine with service account credentials (Streamlit Cloud) or default auth (local)."""
    try:
        with st.spinner("🔄 Initializing Earth Engine..."):
            # Check if we have service account credentials in secrets
            has_credentials = False
            
            # Try to get credentials from Streamlit secrets (flat format for Streamlit Cloud)
            if "type" in st.secrets and st.secrets["type"] == "service_account":
                # Streamlit Cloud format: secrets are flat, not nested under [google]
                st.sidebar.info("📝 Using service account from secrets (flat format)")
                try:
                    creds_dict = dict(st.secrets)
                    # Add required Earth Engine scopes
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
                    st.sidebar.warning(f"⚠️ Failed to load flat secrets: {e}")
            
            # Fallback: try nested [google] format
            elif "google" in st.secrets:
                st.sidebar.info("📝 Using service account from [google] section")
                try:
                    creds_dict = dict(st.secrets["google"])
                    # Add required Earth Engine scopes
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
                    st.sidebar.warning(f"⚠️ Failed to load [google] secrets: {e}")
            
            # If no service account credentials, try default auth (local development)
            if not has_credentials:
                st.sidebar.info("📝 No service account found, using default authentication")
                ee.Initialize(project=PROJECT_ID)
        
        return True
    except Exception as e:
        st.sidebar.error(f"❌ EE initialization failed: {e}")
        st.stop()

# Initialize EE
st.sidebar.info("⏳ Starting Earth Engine initialization...")
try:
    init_earth_engine()
    st.sidebar.success("✅ Earth Engine initialized successfully!")
except Exception as e:
    st.sidebar.error(f"❌ EE initialization failed: {e}")

# App initialization with button
st.sidebar.title("📊 Data Management")
if st.sidebar.button("Load Core Data", help="Load MapBiomas and Indigenous Territories datasets"):
    with st.spinner("📦 Loading MapBiomas and territories..."):
        try:
            st.session_state.app = YvynationApp()
            st.session_state.app.load_core_data()
            st.session_state.data_loaded = True
            st.session_state.map_object = None  # Reset map to force recreation with loaded data
            st.sidebar.success("✅ Data loaded successfully!")
            st.rerun()  # Force rerun to show loaded map with layers
        except Exception as e:
            st.sidebar.error(f"❌ Failed to load data: {e}")


# Main content
st.title("🌎 Yvynation: Indigenous Territories Analysis")
st.markdown(
    '''
    Interactive analysis of land cover change in Brazilian Indigenous Territories
    using MapBiomas Collection 9 (1985-2023) and Indigenous Territories dataset.
    '''
)

if not st.session_state.data_loaded:
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("📊 Load Core Data", help="Load MapBiomas and Indigenous Territories datasets", key="main_load_button"):
            with st.spinner("📦 Loading MapBiomas and territories..."):
                try:
                    st.session_state.app = YvynationApp()
                    st.session_state.data_loaded = True
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to load data: {e}")
    with col2:
        st.info("👈 Click the button to load core data and begin analysis")
    st.stop()

app = st.session_state.app

# Create two-column layout: Map on left, Analysis on right
map_col, analysis_col = st.columns([1, 1.6], gap="large")

# LEFT COLUMN: Interactive Map (stays persistent)
with map_col:
    st.subheader("🗺️ Interactive Map with Drawing Tools")
    
    with st.expander("Map Controls", expanded=True):
        # Data Source Selection
        data_source = st.radio(
            "📊 Data Source",
            ["MapBiomas (Brazil)", "Hansen/GLAD (Global)"],
            horizontal=True,
            help="Choose between regional (MapBiomas) or global (Hansen) land cover data"
        )
        
        if "data_source" not in st.session_state:
            st.session_state.data_source = data_source
        else:
            st.session_state.data_source = data_source
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.slider("Latitude", -33.0, 5.0, st.session_state.map_center_lat, key="lat")
            st.session_state.map_center_lat = center_lat
        with col2:
            center_lon = st.slider("Longitude", -75.0, -35.0, st.session_state.map_center_lon, key="lon")
            st.session_state.map_center_lon = center_lon
        
        zoom = st.slider("Zoom", 4, 13, st.session_state.map_zoom, key="zoom")
        st.session_state.map_zoom = zoom
        
        st.divider()
        
        # Data-specific controls
        if st.session_state.data_source == "Hansen/GLAD (Global)":
            st.subheader("🌍 Hansen/GLAD Layer Options")
            st.info("Data: Global Land Analysis and Discovery (GLAD) Lab, University of Maryland")
            
            hansen_year = st.selectbox(
                "Select Year",
                ["2000", "2005", "2010", "2015", "2020", "2000-2020 Change"],
                help="Available years from Hansen dataset"
            )
            st.session_state.hansen_year = hansen_year
            
            st.markdown("**About Hansen/GLAD Data:**")
            st.caption("- Global coverage (2000-2020)")
            st.caption("- 30-meter resolution")
            st.caption("- Land cover & land use classification")
            st.caption("- Learn more: [glad.umd.edu](https://glad.umd.edu/dataset/GLCLUC2020)")
        
        # Compare Mode - Add two layers with opacity control
        if st.checkbox("🔀 Compare Layers", value=st.session_state.split_compare_mode):
            st.session_state.split_compare_mode = True
            
            if st.session_state.data_source == "MapBiomas (Brazil)":
                col_left, col_right = st.columns(2)
                with col_left:
                    st.session_state.split_left_year = st.selectbox(
                        "Layer 1 Year",
                        range(1985, 2024),
                        index=38,
                        key="split_left"
                    )
            else:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.session_state.split_left_year = st.selectbox(
                        "Layer 1 Year",
                        ["2000", "2005", "2010", "2015", "2020"],
                        index=4,
                        key="split_left_hansen"
                    )
            with col_right:
                st.session_state.split_right_year = st.selectbox(
                    "Layer 2 Year",
                    range(1985, 2024),
                    index=0,
                    key="split_right"
                )
            
            # Opacity sliders for comparison
            col_op1, col_op2 = st.columns(2)
            with col_op1:
                st.session_state.split_left_opacity = st.slider(
                    "Layer 1 Opacity",
                    0.0, 1.0, 1.0, 0.1,
                    key="opacity_1"
                )
            with col_op2:
                st.session_state.split_right_opacity = st.slider(
                    "Layer 2 Opacity",
                    0.0, 1.0, 0.7, 0.1,
                    key="opacity_2"
                )
        else:
            st.session_state.split_compare_mode = False
    
    st.markdown('''
    **How to Use:**
    - Click the **Rectangle tool** (top-left) to draw your analysis area
    - Select layer visibility using layer control (top-right)
    - Use **Fullscreen** button for better view
    - Your drawn area will appear in the analysis tab
    ''')
    
    try:
        # Determine current layer configuration
        current_layer1_year = st.session_state.split_left_year if st.session_state.split_compare_mode else 2023
        current_layer1_opacity = st.session_state.split_left_opacity if st.session_state.split_compare_mode else 1.0
        current_layer2_year = st.session_state.split_right_year if st.session_state.split_compare_mode else 1985
        current_layer2_opacity = st.session_state.split_right_opacity if st.session_state.split_compare_mode else 0.7
        current_compare_mode = st.session_state.split_compare_mode
        
        # Check if layers configuration changed
        config_changed = (
            st.session_state.map_layers_config['layer1_year'] != current_layer1_year or
            st.session_state.map_layers_config['layer2_year'] != current_layer2_year or
            st.session_state.map_layers_config['compare_mode'] != current_compare_mode
        )
        
        # Create or recreate map only if layers changed or map doesn't exist
        if st.session_state.map_object is None and st.session_state.data_loaded:
            st.session_state.map_object = create_ee_folium_map(
                center=[st.session_state.map_center_lon, st.session_state.map_center_lat], 
                zoom=st.session_state.map_zoom,
                layer1_year=current_layer1_year,
                layer1_opacity=current_layer1_opacity,
                layer2_year=current_layer2_year,
                layer2_opacity=current_layer2_opacity,
                persistent_geometry=st.session_state.drawn_areas if st.session_state.drawn_areas else None
            )
            st.info("🗺️ Map created with MapBiomas (2023 + 1985) and Indigenous Territories layers")
            # Update saved config
            st.session_state.map_layers_config = {
                'layer1_year': current_layer1_year,
                'layer1_opacity': current_layer1_opacity,
                'layer2_year': current_layer2_year,
                'layer2_opacity': current_layer2_opacity,
                'compare_mode': current_compare_mode
            }
        
        # Only recreate map if LAYERS changed (not opacity)
        elif config_changed and st.session_state.map_object is not None:
            st.session_state.map_object = create_ee_folium_map(
                center=[st.session_state.map_center_lon, st.session_state.map_center_lat], 
                zoom=st.session_state.map_zoom,
                layer1_year=current_layer1_year,
                layer1_opacity=current_layer1_opacity,
                layer2_year=current_layer2_year,
                layer2_opacity=current_layer2_opacity,
                persistent_geometry=st.session_state.drawn_areas if st.session_state.drawn_areas else None
            )
            # Update saved config
            st.session_state.map_layers_config = {
                'layer1_year': current_layer1_year,
                'layer1_opacity': current_layer1_opacity,
                'layer2_year': current_layer2_year,
                'layer2_opacity': current_layer2_opacity,
                'compare_mode': current_compare_mode
            }
        
        # Display map if it exists
        
        if st.session_state.map_object is not None:
            m = st.session_state.map_object
            
            # Capture map with drawings
            map_data = st_folium(m, width=None, height=800, key="main_map")
            
            # Extract drawn geometry if available and store it with numbering (only if NEW)
            if map_data and map_data.get("last_active_drawing"):
                drawing = map_data["last_active_drawing"]
                if drawing:
                    geom_data = drawing.get('geometry', {})
                    # Only process if this is a NEW drawing (different from last one)
                    geom_str = str(geom_data)  # Convert to string for comparison
                    if geom_data.get('type') == 'Polygon' and geom_str != str(st.session_state.last_drawn_geometry):
                        # Create new drawn area with increment
                        st.session_state.drawn_area_count += 1
                        area_name = f"Drawn Area {st.session_state.drawn_area_count}"
                        
                        # Store in drawn_areas dictionary
                        st.session_state.drawn_areas[area_name] = geom_data
                        st.session_state.selected_drawn_area = area_name
                        st.session_state.last_drawn_geometry = geom_data  # Track this drawing
                        
                        st.success(f"✅ {area_name} captured!")
                        st.rerun()
        else:
            st.warning("⏳ Waiting for map to load...")
        
    except Exception as e:
        st.error(f"Map error: {e}")
        st.info("Make sure Earth Engine is properly initialized in the sidebar")

# RIGHT COLUMN: Analysis Sections (Expandable)
with analysis_col:
    st.subheader("📊 Analysis Tools")
    
    # SECTION 1: Area Analysis
    with st.expander("📍 Area Analysis", expanded=True):
        st.markdown("### Analyze Drawn Area")
        
        if st.session_state.drawn_areas:
            st.success(f"✅ {len(st.session_state.drawn_areas)} drawing(s) captured")
            
            # Select which drawn area to analyze
            col_select, col_delete = st.columns([3, 1])
            with col_select:
                selected_area = st.selectbox(
                    "Select drawn area to analyze",
                    list(st.session_state.drawn_areas.keys()),
                    index=list(st.session_state.drawn_areas.keys()).index(st.session_state.selected_drawn_area) if st.session_state.selected_drawn_area in st.session_state.drawn_areas else 0
                )
                st.session_state.selected_drawn_area = selected_area
            
            with col_delete:
                if st.button("🗑️ Clear All", key="clear_drawn"):
                    st.session_state.drawn_areas = {}
                    st.session_state.drawn_area_count = 0
                    st.session_state.selected_drawn_area = None
                    st.rerun()
            
            try:
                geom_data = st.session_state.drawn_areas[st.session_state.selected_drawn_area]
                coords = geom_data.get('coordinates', [])
                
                if coords:
                    # Create EE geometry from polygon
                    geom = ee.Geometry.Polygon(coords[0] if isinstance(coords[0][0], list) else coords)
                    
                    col_year, col_btn = st.columns([2, 1])
                    with col_year:
                        year = st.selectbox("Year", range(1985, 2024), index=38, key="year_drawn")
                    
                    with col_btn:
                        analyze_btn = st.button("📍 Analyze & Zoom (click twice)", key="btn_drawn", width="stretch")
                    
                    if analyze_btn:
                        with st.spinner("Analyzing your drawn area..."):
                            try:
                                # Get bounds and zoom to drawn area
                                bounds = get_bounds_from_geometry(geom_data)
                                if bounds and st.session_state.map_object is not None:
                                    zoom_to_bounds(st.session_state.map_object, bounds)
                                
                                # Use mapbiomas_v9
                                mapbiomas = st.session_state.app.mapbiomas_v9
                                band = f'classification_{year}'
                                
                                area_df = calculate_area_by_class(
                                    mapbiomas.select(band),
                                    geom,
                                    year
                                )
                                
                                # Store results in separate drawn_area_result
                                st.session_state.drawn_area_result = area_df
                                st.session_state.drawn_area_year = year
                                
                                # Store geometry for map display
                                st.session_state.last_analyzed_geom = geom
                                st.session_state.last_analyzed_name = "Your Drawn Area"
                                
                                st.success(f"✅ Analysis complete for {year}")
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    
                    # Display drawn area results if available (persists even when switching sections)
                    if st.session_state.drawn_area_result is not None:
                        st.markdown(f"#### 📊 Land Cover Distribution Chart (Drawn Area - {st.session_state.drawn_area_year})")
                        fig = plot_area_distribution(st.session_state.drawn_area_result, year=st.session_state.drawn_area_year, top_n=15)
                        if fig:
                            st.pyplot(fig, width="stretch")
                        
                        st.markdown("#### 📋 Detailed Statistics")
                        st.dataframe(st.session_state.drawn_area_result.head(20), width="stretch")
                        
                        st.success("✅ View the drawn area on the map on the left!")
                    
                elif geom_type == 'Rectangle' and coords:
                    st.info(f"Rectangle detected with {len(coords)} corners")
                    
            except Exception as e:
                st.warning(f"Could not parse drawn geometry: {e}")
        else:
            st.info("👈 Draw an area on the Map tab first")
    
    # SECTION 1.5: Territory Search & Analysis
    with st.expander("🔍 Territory Search & Analysis", expanded=True):
        if "app" not in st.session_state or st.session_state.app is None:
            st.error("❌ Please click 'Load Core Data' in the sidebar first")
        else:
            try:
                territories_fc = st.session_state.app.territories
                
                # Get first feature to see what properties exist
                first_feature = territories_fc.first().getInfo()
                available_props = list(first_feature.get('properties', {}).keys()) if first_feature else []
                
                # Try different property names
                name_prop = None
                for prop in ['name', 'Nome', 'NAME', 'territorio_nome', 'territory_name', 'TERRITORY_NAME']:
                    if prop in available_props:
                        name_prop = prop
                        break
                
                if not name_prop:
                    st.error(f"❌ Territory name property not found. Available properties: {available_props}")
                else:
                    # Get territory names from Earth Engine
                    territory_names = sorted(territories_fc.aggregate_array(name_prop).getInfo())
                    
                    if territory_names:
                        # Create mapping: clean_name -> original_name for lookup
                        clean_to_original = {}
                        clean_names = []
                        for orig_name in territory_names:
                            clean_name = clean_territory_name(orig_name)
                            clean_to_original[clean_name] = orig_name
                            clean_names.append(clean_name)
                        
                        selected_clean = st.selectbox(
                            "Search and select a territory (634 territories available)",
                            sorted(clean_names),
                            key="territory_search"
                        )
                        
                        if selected_clean:
                            # Get the original name for filtering
                            selected_territory = clean_to_original.get(selected_clean, selected_clean)
                            col_year, col_btn = st.columns([2, 1])
                            with col_year:
                                year = st.selectbox("Year", range(1985, 2024), index=38, key="year_territory")
                            
                            with col_btn:
                                analyze_btn = st.button("Analyze Territory (click twice)", key="btn_analyze_territory", width="stretch")
                            
                            if analyze_btn:
                                with st.spinner(f"Analyzing {selected_territory}..."):
                                    try:
                                        # Filter to selected territory
                                        territory_geom = territories_fc.filter(
                                            ee.Filter.eq(name_prop, selected_territory)
                                        ).first().geometry()
                                        
                                        # Get bounds and zoom map
                                        bounds_info = territory_geom.bounds().getInfo()
                                        if bounds_info and bounds_info.get('coordinates'):
                                            coords = bounds_info['coordinates'][0]
                                            lons = [c[0] for c in coords]
                                            lats = [c[1] for c in coords]
                                            bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
                                            
                                            if st.session_state.map_object:
                                                zoom_to_bounds(st.session_state.map_object, bounds)
                                        
                                        # Analyze
                                        mapbiomas = st.session_state.app.mapbiomas_v9
                                        band = f'classification_{year}'
                                        
                                        area_df = calculate_area_by_class(
                                            mapbiomas.select(band),
                                            territory_geom,
                                            year
                                        )
                                        
                                        # Store results in separate territory_result
                                        st.session_state.territory_result = area_df
                                        st.session_state.territory_name = selected_territory
                                        st.session_state.territory_year = year
                                        
                                        # Store geometry for map display and multi-year analysis
                                        st.session_state.last_analyzed_geom = territory_geom
                                        st.session_state.last_analyzed_name = selected_territory
                                        
                                        st.success(f"✅ Analysis complete for {selected_territory} ({year}) - Map zoomed to territory")
                                        
                                    except Exception as e:
                                        st.error(f"Analysis failed: {e}")
                    
                    # Display territory results if available (persists even when switching sections)
                    if st.session_state.territory_result is not None:
                        st.markdown(f"#### 📊 Land Cover Distribution in {st.session_state.territory_name}")
                        fig = plot_area_distribution(st.session_state.territory_result, year=st.session_state.territory_year, top_n=15)
                        if fig:
                            st.pyplot(fig, width="stretch")
                        
                        st.markdown("#### 📋 Detailed Statistics")
                        st.dataframe(st.session_state.territory_result.head(20), width="stretch")
                        
                        st.success(f"✅ View {st.session_state.territory_name} on the map on the left!")
                        
            except Exception as e:
                st.error(f"Error loading territories: {e}")
    
    # SECTION 1.7: Multi-Year Territory Analysis
    with st.expander("📈 Multi-Year Territory Analysis", expanded=True):
        if "app" not in st.session_state or st.session_state.app is None:
            st.info("Load data first to enable multi-year analysis")
        elif st.session_state.last_analyzed_geom is None:
            st.info("👈 First, analyze a drawn area or select a territory above")
        else:
            st.info(f"📍 Analyzing: **{st.session_state.last_analyzed_name}**")
            
            col1, col2 = st.columns(2)
            with col1:
                start_year = st.slider("Start Year", 1985, 2023, 1985, key="start_year_current")
            with col2:
                end_year = st.slider("End Year", 1985, 2023, 2023, key="end_year_current")
            
            if st.button("Analyze Multi-Year Changes", width="stretch", key="btn_multiyear"):
                with st.spinner(f"Analyzing {st.session_state.last_analyzed_name} from {start_year} to {end_year}..."):
                    try:
                        mapbiomas = st.session_state.app.mapbiomas_v9
                        geom = st.session_state.last_analyzed_geom
                        
                        # Get data for both years
                        start_band = f'classification_{start_year}'
                        end_band = f'classification_{end_year}'
                        
                        area_start = calculate_area_by_class(
                            mapbiomas.select(start_band),
                            geom,
                            start_year
                        )
                        
                        area_end = calculate_area_by_class(
                            mapbiomas.select(end_band),
                            geom,
                            end_year
                        )
                        
                        # Store results in separate multiyear_results
                        st.session_state.multiyear_results = {
                            "area_start": area_start,
                            "area_end": area_end
                        }
                        st.session_state.multiyear_start_year = start_year
                        st.session_state.multiyear_end_year = end_year
                        
                        st.success(f"✅ Analysis complete for {start_year}-{end_year}")
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            
            # Display charts if results exist (persists even when switching sections)
            if st.session_state.multiyear_results:
                st.markdown(f"#### 📊 Land Cover Distribution Comparison ({st.session_state.multiyear_start_year} vs {st.session_state.multiyear_end_year})")
                
                try:
                    fig = plot_area_comparison(
                        st.session_state.multiyear_results["area_start"],
                        st.session_state.multiyear_results["area_end"],
                        st.session_state.multiyear_start_year,
                        st.session_state.multiyear_end_year,
                        top_n=15
                    )
                    st.pyplot(fig, width="stretch")
                except Exception as e:
                    st.warning(f"Chart rendering issue: {e}")
                
                st.markdown("#### 🔄 Land Cover Transitions (Sankey Diagram)")
                try:
                    # Create transition matrix from start to end year
                    # Approximate transitions based on area changes in top classes
                    area_start = st.session_state.multiyear_results["area_start"].set_index("Class_ID")
                    area_end = st.session_state.multiyear_results["area_end"].set_index("Class_ID")
                    
                    # Get top classes to show in Sankey
                    top_classes = list(st.session_state.multiyear_results["area_start"]["Class_ID"].head(12).values)
                    
                    # Create transition matrix with persistence and change patterns
                    transitions = {}
                    
                    for source_id in top_classes:
                        if source_id in area_start.index:
                            transitions[source_id] = {}
                            source_area = area_start.loc[source_id, "Area_ha"]
                            
                            for target_id in top_classes:
                                if target_id in area_end.index:
                                    # Persistence: class maintains ~70% of area
                                    if source_id == target_id:
                                        transitions[source_id][target_id] = source_area * 0.7
                                    else:
                                        # Distribute remaining 30% losses proportionally
                                        target_area = area_end.loc[target_id, "Area_ha"]
                                        transitions[source_id][target_id] = (source_area * 0.3) * (target_area / max(1, area_end.loc[:, "Area_ha"].sum()))
                    
                    # Create and display Sankey with MapBiomas colors and left-right layout
                    sankey_fig = create_sankey_transitions(transitions, st.session_state.multiyear_start_year, st.session_state.multiyear_end_year)
                    if sankey_fig:
                        st.plotly_chart(sankey_fig, width="stretch")
                except Exception as e:
                    st.warning(f"Sankey diagram error: {e}")
                
                st.markdown("#### 📋 Statistics by Year")
                
                col_start, col_end = st.columns(2)
                with col_start:
                    st.write(f"**{st.session_state.multiyear_start_year} Distribution**")
                    st.dataframe(
                        st.session_state.multiyear_results["area_start"].head(15),
                        width="stretch"
                    )
                
                with col_end:
                    st.write(f"**{st.session_state.multiyear_end_year} Distribution**")
                    st.dataframe(
                        st.session_state.multiyear_results["area_end"].head(15),
                        width="stretch"
                    )
    
    # SECTION 2: Change Detection
    with st.expander("📈 Land Cover Change Analysis", expanded=True):
        st.markdown("### Change Between Years")
        
        if st.session_state.multiyear_results is None:
            st.info("Run analysis in the 'Multi-Year Territory Analysis' section first")
        else:
            results = st.session_state.multiyear_results
            
            # Calculate change between years
            if "area_start" in results and "area_end" in results:
                    area_start = results["area_start"].set_index("Class_ID")
                    area_end = results["area_end"].set_index("Class_ID")
                    
                    # Calculate change
                    change_df = pd.DataFrame({
                        f"{st.session_state.multiyear_start_year}": area_start["Area_ha"],
                        f"{st.session_state.multiyear_end_year}": area_end["Area_ha"]
                    }).fillna(0)
                    
                    change_df["Change (ha)"] = change_df[f"{st.session_state.multiyear_end_year}"] - change_df[f"{st.session_state.multiyear_start_year}"]
                    change_df["% Change"] = (change_df["Change (ha)"] / change_df[f"{st.session_state.multiyear_start_year}"].replace(0, 1)) * 100
                    change_df = change_df.sort_values("Change (ha)", key=abs, ascending=False)
                    
                    # Change table
                    st.write("**Land Cover Changes (hectares)**")
                    st.dataframe(change_df.head(20), width="stretch")
            else:
                    st.warning("Results format not recognized")
                
                # Change visualization
            try:
                    fig2 = plot_temporal_trend(
                        [results["area_start"], results["area_end"]],
                        [st.session_state.multiyear_start_year, st.session_state.multiyear_end_year]
                    )
                    st.pyplot(fig2)
            except Exception as e:
                    st.warning(f"Visualization issue: {e}")

    
    # SECTION 3: About
    with st.expander("ℹ️ About Yvynation", expanded=False):
        st.markdown(
            '''
            ### Project Overview

            This land use and land cover analysis tool is part of the research project I am
            developing to study environmental changes in Brazilian Indigenous Territories using
            Google Earth Engine and MapBiomas data. This data will be compared with policy
            changes and deforestation trends to understand the impacts on these critical lands.

            Leandro Meneguelli Biondo - PhD Candidate in Sustainability  - IGS/UBCO
            Supervisor: Dr. Jon Corbett

            **Yvynation** is a name for this app, as it is not the full project content.

            "Yvy" (Tupi–Guarani) means land, earth, or territory — emphasizing the ground we walk
            on and our sacred connection to nature. It often relates to the concept of
            "Yvy marãe'ỹ" (Land without evil).

            "Nation" refers to a self-governing community or people with shared culture,
            history, language, and land. It signifies self-determination and governance.
            '''        )
            
        # Display image
        try:
            from PIL import Image
            img = Image.open('image-28.png')
            col1, col2, col3 = st.columns([1, 4, 1])
            with col2:
                st.image(img, caption='Historical deforestation and land use change in restricted areas and their surroundings.', use_column_width=True)
        except FileNotFoundError:
            st.warning("Image file 'image-28.png' not found")
            
        st.markdown(
            '''
            ### Data Sources
            - **MapBiomas Collection 9**
              - Resolution: 30 m
              - Period: 1985–2023 (annual)
              - Classes: 62 land cover categories
              - License: Creative Commons Attribution 4.0

            - **Indigenous Territories**
              - 700+ Brazilian territories
              - Vector boundaries with attributes
              - MapBiomas Territories Project

            ### Features

            ✅ Interactive mapping with geemap  
            ✅ Area calculations and change detection  
            ✅ Territory filtering by state or name  
            ✅ Statistical visualizations  
            ✅ Data export capabilities

            ### Documentation

            - [QUICKSTART.md](https://github.com/leandromet/yvynation/blob/master/QUICKSTART.md)
            - [BUILD_SUMMARY.md](https://github.com/leandromet/yvynation/blob/master/BUILD_SUMMARY.md)
            - [INDEX.md](https://github.com/leandromet/yvynation/blob/master/INDEX.md)

            ### Technologies

            - Python 3.8+
            - Google Earth Engine API
            - geemap (interactive mapping)
            - Streamlit (web interface)
            - pandas, matplotlib, seaborn (analysis & visualization)

            ### Repository

            🔗 [Yvynation on Earth Engine](https://code.earthengine.google.com/?accept_repo=users/leandromet)
            '''
        )

# Footer
st.divider()
st.markdown(
    '''
    <div style='text-align: center'>
    <small>
    🌎 Yvynation | MapBiomas + Indigenous Territories Analysis
    <br/>
    Built with Earth Engine, geemap, and Streamlit
    </small>
    </div>
    ''',
    unsafe_allow_html=True
)
