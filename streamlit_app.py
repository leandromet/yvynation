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

# Sidebar
st.sidebar.title("🌍 Yvynation Configuration")

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
        
        # Get map tile URL for MapBiomas
        mapid = ee.Image(classification_2023).getMapId(vis_params)
        ee_tile_url = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
        folium.TileLayer(
            tiles=ee_tile_url,
            attr='MapBiomas',
            name='MapBiomas 2023',
            overlay=True,
            control=True
        ).add_to(m)
        
        # Add Indigenous Territories layer
        territories = ee.FeatureCollection('projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES')
        
        # Create simple style for territories (red boundary, no fill)
        styled_territories = territories.map(lambda f: f.set({'style': {
            'color': '#FF0000',
            'fillColor': '#FF0000',
            'weight': 2,
            'opacity': 0.6,
            'fillOpacity': 0.1
        }}))
        
        ee_image_object = ee.Image().paint(territories, 0, 2)
        mapid_territories = ee_image_object.getMapId({'min': 0, 'max': 1, 'palette': ['red']})
        
        ee_tile_url_territories = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{mapid_territories["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
        folium.TileLayer(
            tiles=ee_tile_url_territories,
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

# App initialization
if st.sidebar.button("Load Core Data"):
    with st.spinner("Loading MapBiomas and territories..."):
        try:
            st.session_state.app = YvynationApp()
            st.session_state.app.load_core_data()
            st.session_state.data_loaded = True
            st.sidebar.success("✅ Data loaded successfully!")
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
else:
    app = st.session_state.app

    # Tabs - skip interactive maps for now, focus on working analysis
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🗺️ Map", "📊 Area Analysis", "📈 Change Detection", "ℹ️ About"]
    )

    # TAB 1: Map
    with tab1:
        st.subheader("Interactive Map with Drawing Tools")
        
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
        ### Map Layers & Instructions
        
        **Available Layers:**
        - 🌍 **MapBiomas 2023** - Land cover classification (62 classes)
        - 🏘️ **Indigenous Territories** - Official boundaries (red)
        
        **How to Use:**
        1. Click the **Rectangle tool** (top-left) to draw your analysis area
        2. Select layer visibility using layer control (top-right)
        3. Use **Fullscreen** button for better view
        4. Your drawn area will automatically appear in the "Area Analysis" tab
        """)
        
        try:
            # Create map once and keep it fresh
            m = create_ee_folium_map(center=[center_lon, center_lat], zoom=zoom)
            
            # Capture map with drawings - use key to prevent rerun issues
            map_data = st_folium(m, width=1400, height=700, key="main_map")
            
            # Extract drawn geometry if available
            if map_data and map_data.get("last_active_drawing"):
                drawing = map_data["last_active_drawing"]
                if drawing:
                    st.session_state.drawn_geometry = drawing
                    st.success("✅ Drawing captured! Go to 'Area Analysis' tab to analyze.")
                    
                    # Show drawing info
                    with st.expander("📍 Drawing Details"):
                        st.json(drawing)
            
        except Exception as e:
            st.error(f"Map error: {e}")
            st.info("Make sure Earth Engine is properly initialized in the sidebar")
    
    # TAB 2: Area Analysis
    with tab2:
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
                                    
                                    # Display drawn area on map
                                    with st.expander("🗺️ View Your Drawn Area on Map", expanded=True):
                                        try:
                                            # Get center point using centroid
                                            geom_centroid = geom.centroid().getInfo()
                                            center_lon = geom_centroid['coordinates'][0]
                                            center_lat = geom_centroid['coordinates'][1]
                                            zoom = 10
                                            
                                            # Create map
                                            m = folium.Map(
                                                location=[center_lat, center_lon],
                                                zoom_start=zoom,
                                                tiles='OpenStreetMap'
                                            )
                                            
                                            # Add MapBiomas layer
                                            mapbiomas_map = st.session_state.app.mapbiomas_v9.select(band)
                                            map_id = mapbiomas_map.getMapId()
                                            ee_tile_url = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{map_id["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
                                            folium.TileLayer(
                                                tiles=ee_tile_url,
                                                attr='MapBiomas',
                                                name='MapBiomas Collection 9',
                                                overlay=True
                                            ).add_to(m)
                                            
                                            # Add drawn area boundary in red
                                            drawn_geojson = geom.getInfo()
                                            folium.GeoJson(
                                                drawn_geojson,
                                                style_function=lambda x: {
                                                    'color': 'red',
                                                    'weight': 3,
                                                    'opacity': 0.8,
                                                    'fillOpacity': 0.1
                                                },
                                                name="Your Drawn Area"
                                            ).add_to(m)
                                            
                                            folium.LayerControl().add_to(m)
                                            st_folium(m, width=1200, height=500)
                                        except Exception as map_e:
                                            st.error(f"Could not display map: {map_e}")
                                    
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
            try:
                # Check if app is loaded
                if "app" not in st.session_state or st.session_state.app is None:
                    st.error("❌ Please click 'Load Core Data' in the sidebar first")
                else:
                    territories_fc = st.session_state.app.territories
                    
                    # Debug: Check what properties are available
                    try:
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
                                                
                                                # Display territory on map
                                                with st.expander("🗺️ View Territory on Map", expanded=True):
                                                    try:
                                                        # Get center point using centroid
                                                        geom_centroid = territory_geom.centroid().getInfo()
                                                        center_lon = geom_centroid['coordinates'][0]
                                                        center_lat = geom_centroid['coordinates'][1]
                                                        zoom = 10
                                                        
                                                        # Create map
                                                        m = folium.Map(
                                                            location=[center_lat, center_lon],
                                                            zoom_start=zoom,
                                                            tiles='OpenStreetMap'
                                                        )
                                                        
                                                        # Add MapBiomas layer
                                                        mapbiomas_map = st.session_state.app.mapbiomas_v9.select(band)
                                                        map_id = mapbiomas_map.getMapId()
                                                        ee_tile_url = f'https://earthengine.googleapis.com/v1alpha/projects/earthengine-public/maps/{map_id["mapid"]}/tiles/{{z}}/{{x}}/{{y}}'
                                                        folium.TileLayer(
                                                            tiles=ee_tile_url,
                                                            attr='MapBiomas',
                                                            name='MapBiomas Collection 9',
                                                            overlay=True
                                                        ).add_to(m)
                                                        
                                                        # Add territory boundary in red
                                                        territory_geojson = territory_geom.getInfo()
                                                        folium.GeoJson(
                                                            territory_geojson,
                                                            style_function=lambda x: {
                                                                'color': 'red',
                                                                'weight': 3,
                                                                'opacity': 0.8,
                                                                'fillOpacity': 0.1
                                                            },
                                                            name=selected_territory
                                                        ).add_to(m)
                                                        
                                                        folium.LayerControl().add_to(m)
                                                        st_folium(m, width=1200, height=500)
                                                    except Exception as map_e:
                                                        st.error(f"Could not display map: {map_e}")
                                            
                                            except Exception as e:
                                                st.error(f"Analysis failed: {e}")
                            
                            else:
                                st.warning("No territories found in the collection")
                    
                    except Exception as e:
                        st.error(f"Territory search initialization error: {e}")
                        st.info("This may occur if the territories dataset is not properly loaded.")
            
            except Exception as e:
                st.warning(f"Territory search error: {e}")
        
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

    # TAB 3: Change Detection
    with tab3:
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
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = plot_area_changes(comparison, start_year, end_year)
                    if fig:
                        st.pyplot(fig)
                
                with col2:
                    fig2 = plot_temporal_trend(
                        [results["area_start"], results["area_end"]],
                        [start_year, end_year],
                        top_n=8
                    )
                    st.pyplot(fig2)
            except Exception as e:
                st.warning(f"Visualization issue: {e}")

    # TAB 4: About
    with tab4:
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
