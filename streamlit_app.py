"""
Yvynation Earth Engine Application
Interactive Streamlit web app for MapBiomas and Indigenous Territories analysis
"""

import streamlit as st
import ee
import geemap
import folium
import streamlit_folium
import pandas as pd
from config import PROJECT_ID
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
if "results" not in st.session_state:
    st.session_state.results = None

# Sidebar
st.sidebar.title("🌍 Yvynation Configuration")

def create_ee_folium_map(center=[-45.3, -4.5], zoom=7):
    """Create a folium map with Earth Engine layers."""
    m = folium.Map(
        location=[center[1], center[0]],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    
    try:
        # Add MapBiomas 2023 layer
        mapbiomas = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')
        classification_2023 = mapbiomas.select('classification_2023')
        
        # Create a simple visualization
        vis_params = {
            'min': 0,
            'max': 62,
            'palette': ['#000000', '#228B22', '#00FF00', '#0000FF', '#FF0000']
        }
        
        # Get map tile URL
        mapid = ee.Image(classification_2023).getMapId(vis_params)
        folium.TileLayer(
            tiles=mapid['tile_fetcher'].url_format,
            attr='MapBiomas',
            name='MapBiomas 2023',
            overlay=True,
            control=True
        ).add_to(m)
        
    except Exception as e:
        st.warning(f"Could not load MapBiomas layer: {e}")
    
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
        st.subheader("MapBiomas 2023 with Earth Engine Tiles")
        
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.slider("Latitude", -33.0, 5.0, -4.5, key="lat")
        with col2:
            center_lon = st.slider("Longitude", -75.0, -35.0, -45.3, key="lon")
        
        zoom = st.slider("Zoom", 4, 13, 7, key="zoom")
        
        st.info("🗺️ Displaying MapBiomas Collection 9 - 2023 Land Cover Classification")
        
        try:
            m = create_ee_folium_map(center=[center_lon, center_lat], zoom=zoom)
            streamlit_folium.folium_static(m, width=1400, height=600)
        except Exception as e:
            st.error(f"Map error: {e}")
            st.info("Make sure Earth Engine is properly initialized in the sidebar")
    
    # TAB 2: Area Analysis
        st.subheader("Land Cover Area Distribution")
        
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.slider("Start Year", 1985, 2023, 1985)
        with col2:
            end_year = st.slider("End Year", 1985, 2023, 2023)
        
        if st.button("Analyze Territories"):
            with st.spinner("Analyzing land cover..."):
                try:
                    results = app.analyze_territories(
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
