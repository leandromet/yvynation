"""
Yvynation Earth Engine Application
Interactive Streamlit web app for MapBiomas and Indigenous Territories analysis
"""

import streamlit as st
import ee
import geemap
import folium
from folium.plugins import Draw, Fullscreen
import streamlit_folium
from streamlit_folium import st_folium
import pandas as pd
import json
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
)
from visualization import create_mapbiomas_legend

# Page config
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🌍",
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

# Sidebar
st.sidebar.title("🌍 Yvynation Configuration")

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

def create_ee_folium_map(center=[-45.3, -4.5], zoom=7):
    """Create a folium map with Earth Engine layers and drawing tools."""
    m = folium.Map(
        location=[center[1], center[0]],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    
    try:
        # Add MapBiomas 2023 layer
        mapbiomas = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')
        classification_2023 = mapbiomas.select('classification_2023')
        
        # MapBiomas color palette
        palette = [
            '#000000', '#228B22', '#00FF00', '#0000FF', '#FF0000',
            '#FFFF00', '#00FFFF', '#FF00FF', '#C0C0C0', '#808080',
            '#800000', '#008000', '#000080', '#808000', '#008080'
        ]
        
        vis_params = {
            'min': 0,
            'max': 62,
            'palette': palette
        }
        
        # Get map tile URL for MapBiomas - use tile_fetcher.url_format if available
        mapid = ee.Image(classification_2023).getMapId(vis_params)
        try:
            tile_url = mapid['tile_fetcher'].url_format
        except (KeyError, AttributeError):
            # Fallback to manual URL format if tile_fetcher not available
            tile_url = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
        
        folium.TileLayer(
            tiles=tile_url,
            attr='MapBiomas',
            name='MapBiomas 2023',
            overlay=True,
            control=True
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
    
    # Add fullscreen button
    Fullscreen().add_to(m)
    
    folium.LayerControl().add_to(m)
    return m

# Initialize EE
try:
    ee.Initialize(project=PROJECT_ID)
    st.sidebar.success("✅ Earth Engine initialized")
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
st.title("🌍 Yvynation: Indigenous Territories Analysis")
st.markdown(
    """
    Interactive analysis of land cover change in Brazilian Indigenous Territories
    using MapBiomas Collection 9 (1985-2023) and Indigenous Territories dataset.
    """
)

if not st.session_state.data_loaded:
    st.info("👈 Click 'Load Core Data' in the sidebar to begin")
    st.stop()

app = st.session_state.app

# Create two-column layout: Map on left, Analysis on right
map_col, analysis_col = st.columns([1.2, 1], gap="medium")

# LEFT COLUMN: Interactive Map (stays persistent)
with map_col:
    st.subheader("🗺️ Interactive Map with Drawing Tools")
    
    with st.expander("Map Controls", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.slider("Latitude", -33.0, 5.0, st.session_state.map_center_lat, key="lat")
            st.session_state.map_center_lat = center_lat
        with col2:
            center_lon = st.slider("Longitude", -75.0, -35.0, st.session_state.map_center_lon, key="lon")
            st.session_state.map_center_lon = center_lon
        
        zoom = st.slider("Zoom", 4, 13, st.session_state.map_zoom, key="zoom")
        st.session_state.map_zoom = zoom
    
    st.markdown("""
    **How to Use:**
    - Click the **Rectangle tool** (top-left) to draw your analysis area
    - Select layer visibility using layer control (top-right)
    - Use **Fullscreen** button for better view
    - Your drawn area will appear in the analysis tab
    """)
    
    try:
        # Only create map AFTER data is confirmed loaded
        if st.session_state.map_object is None and st.session_state.data_loaded:
            # Create fresh map with layers since data just loaded
            st.session_state.map_object = create_ee_folium_map(
                center=[st.session_state.map_center_lon, st.session_state.map_center_lat], 
                zoom=st.session_state.map_zoom
            )
            st.info("🗺️ Map created with MapBiomas and Indigenous Territories layers")
        
        if st.session_state.map_object is not None:
            m = st.session_state.map_object
            
            # Capture map with drawings - use key to prevent rerun issues
            map_data = st_folium(m, width=None, height=700, key="main_map")
            
            # Extract drawn geometry if available
            if map_data and map_data.get("last_active_drawing"):
                drawing = map_data["last_active_drawing"]
                if drawing:
                    st.session_state.drawn_geometry = drawing
                    st.success("✅ Drawing captured!")
        else:
            st.warning("⏳ Waiting for map to load...")
        
    except Exception as e:
        st.error(f"Map error: {e}")
        st.info("Make sure Earth Engine is properly initialized in the sidebar")

# RIGHT COLUMN: Analysis Tabs
with analysis_col:
    st.subheader("📊 Analysis Tools")
    
    # Tabs within the right column only
    tab1, tab2, tab3 = st.tabs(
        ["Area Analysis", "Change Detection", "About"]
    )
    
    # TAB 1: Area Analysis
    with tab1:
        st.subheader("Land Cover Area Distribution")
        
        # Option 1: Analyze drawn area
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### Option 1: Analyze Drawn Area")
        
        if st.session_state.drawn_geometry:
            st.success("✅ Drawing detected from map")
            
            try:
                drawing = st.session_state.drawn_geometry
                geom_type = drawing.get('geometry', {}).get('type')
                coords = drawing.get('geometry', {}).get('coordinates', [])
                
                if geom_type == 'Polygon' and coords:
                    # Create EE geometry from polygon
                    geom = ee.Geometry.Polygon(coords[0] if isinstance(coords[0][0], list) else coords)
                    
                    year = st.selectbox("Year", range(1985, 2024), index=38, key="year_drawn")
                    
                    if st.button("Analyze Drawn Area", key="btn_drawn"):
                        with st.spinner("Analyzing your drawn area..."):
                            try:
                                # Use mapbiomas_v9
                                mapbiomas = st.session_state.app.mapbiomas_v9
                                band = f'classification_{year}'
                                
                                area_df = calculate_area_by_class(
                                    mapbiomas.select(band),
                                    geom,
                                    year
                                )
                                
                                st.success(f"✅ Analysis complete for {year}")
                                
                                # Store geometry for map display
                                st.session_state.last_analyzed_geom = geom
                                st.session_state.last_analyzed_name = "Your Drawn Area"
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.dataframe(area_df.head(15), use_container_width=True)
                                
                                with col_b:
                                    fig = plot_area_distribution(area_df, year=year, top_n=10)
                                    if fig:
                                        st.pyplot(fig)
                                
                                st.success("✅ View the drawn area on the map on the left!")
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    
                elif geom_type == 'Rectangle' and coords:
                    st.info(f"Rectangle detected with {len(coords)} corners")
                    
            except Exception as e:
                st.warning(f"Could not parse drawn geometry: {e}")
        else:
            st.info("👈 Draw an area on the Map tab first")
        
        with col2:
            st.markdown("### Option 2: Quick Territory Search")
            st.info("Use the search below to find and analyze any territory")
            
            st.divider()
            
            # Quick search and analyze
            st.subheader("🔍 Quick Territory Search & Analyze")
            
            col_search1, col_search2 = st.columns([2, 1])
            
            with col_search1:
                if "app" not in st.session_state or st.session_state.app is None:
                    st.error("❌ Please click 'Load Core Data' in the sidebar first")
                else:
                    try:
                        territories_fc = st.session_state.app.territories
                        
                        # Debug: Check what properties are available
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
                                selected_territory = st.selectbox(
                                    "Search and select a territory (634 territories available)",
                                    territory_names,
                                    key="territory_search"
                                )
                                
                                if selected_territory:
                                    year = st.selectbox("Year", range(1985, 2024), index=38, key="year_territory")
                                    
                                    if st.button("Analyze Selected Territory", key="btn_analyze_territory"):
                                        with st.spinner(f"Analyzing {selected_territory}..."):
                                            try:
                                                # Filter to selected territory
                                                territory_geom = territories_fc.filter(
                                                    ee.Filter.eq(name_prop, selected_territory)
                                                ).first().geometry()
                                                
                                                # Analyze
                                                mapbiomas = st.session_state.app.mapbiomas_v9
                                                band = f'classification_{year}'
                                                
                                                area_df = calculate_area_by_class(
                                                    mapbiomas.select(band),
                                                    territory_geom,
                                                    year
                                                )
                                                
                                                # Store geometry for map display
                                                st.session_state.last_analyzed_geom = territory_geom
                                                st.session_state.last_analyzed_name = selected_territory
                                                
                                                st.success(f"✅ Analysis complete for {selected_territory} ({year})")
                                                
                                                col_a, col_b = st.columns(2)
                                                with col_a:
                                                    st.write(f"**Land Cover in {selected_territory} ({year})**")
                                                    st.dataframe(area_df.head(15), use_container_width=True)
                                                
                                                with col_b:
                                                    fig = plot_area_distribution(area_df, year=year, top_n=10)
                                                    if fig:
                                                        st.pyplot(fig)
                                                
                                                st.success(f"✅ View {selected_territory} on the map on the left - use the search box to highlight it!")
                                            
                                            except Exception as e:
                                                st.error(f"Analysis failed: {e}")
                    except Exception as e:
                        st.error(f"Error loading territories: {e}")

            st.divider()
            
            # Option 3: Default analysis for all territories
            st.markdown("### Option 3: Analyze All Territories")
            
            col1, col2 = st.columns(2)
            with col1:
                start_year = st.slider("Start Year", 1985, 2023, 1985, key="start_year_all")
            with col2:
                end_year = st.slider("End Year", 1985, 2023, 2023, key="end_year_all")
            
            if st.button("Analyze All Territories"):
                with st.spinner("Analyzing all territories..."):
                    try:
                        results = st.session_state.app.analyze_territories(
                            start_year=start_year,
                            end_year=end_year
                        )
                        st.session_state.results = results
                        
                        # Display area tables
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Area Distribution in {start_year}**")
                            st.dataframe(
                                results["area_start"].head(15),
                                use_container_width=True
                            )
                        
                        with col2:
                            st.write(f"**Area Distribution in {end_year}**")
                            st.dataframe(
                                results["area_end"].head(15),
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
            
            # Display charts if results exist
            if st.session_state.results:
                st.subheader("Visualizations")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        fig1 = plot_area_distribution(
                            st.session_state.results["area_start"],
                            year=start_year,
                            top_n=12
                        )
                        st.pyplot(fig1)
                    except Exception as e:
                        st.warning(f"Chart rendering issue: {e}")
                
                with col2:
                    try:
                        fig2 = plot_area_comparison(
                            st.session_state.results["area_start"],
                            st.session_state.results["area_end"],
                            start_year,
                            end_year,
                            top_n=12
                        )
                        st.pyplot(fig2)
                    except Exception as e:
                        st.warning(f"Chart rendering issue: {e}")
        
        # TAB 2: Change Detection
        with tab2:
            st.subheader("Land Cover Change Analysis")
            
            if st.session_state.results is None:
                st.info("Run analysis in the 'Area Analysis' tab first")
            else:
                results = st.session_state.results
                
                # Change table
                st.write("**Land Cover Changes (km²)**")
                comparison = results["comparison"].head(20)
                st.dataframe(comparison, use_container_width=True)
                
                # Change visualization
                try:
                    fig = plot_area_changes(comparison, start_year, end_year)
                    if fig:
                        st.pyplot(fig)
                    
                    fig2 = plot_temporal_trend(
                        [results["area_start"], results["area_end"]],
                        [start_year, end_year],
                        top_n=8
                    )
                    st.pyplot(fig2)
                except Exception as e:
                    st.warning(f"Visualization issue: {e}")

        # TAB 3: About
        with tab3:
            st.subheader("About Yvynation")
            
            st.markdown("""
            ### Project Overview
            
            **Yvynation** is an Earth Engine analysis application for studying land cover 
            change in Brazilian Indigenous Territories.
            
            ### Data Sources
            
            - **MapBiomas Collection 9**
              - Resolution: 30m
          - Period: 1985-2023 (annual)
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
        
        🔗 [Yvynation on Earth Engine](https://code.earthengine.google.com/?accept_repo=users/leandromet/yvynation)
        """)

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center'>
    <small>
    🌍 Yvynation | MapBiomas + Indigenous Territories Analysis
    <br/>
    Built with Earth Engine, geemap, and Streamlit
    </small>
    </div>
    """,
    unsafe_allow_html=True
)
