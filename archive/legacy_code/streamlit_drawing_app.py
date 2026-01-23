'''
Advanced Streamlit app with interactive drawing and area analysis.
Uses streamlit-folium with drawing tools for custom area selection.
'''

import streamlit as st
import ee
import folium
from folium.plugins import Draw, Fullscreen
import streamlit_folium
import pandas as pd
import json
from config import PROJECT_ID
from app_file import YvynationApp
from analysis import clip_mapbiomas_to_geometry, calculate_area_by_class
from plots import plot_area_distribution, plot_area_comparison

# Page config
st.set_page_config(
    page_title="Yvynation - Drawing Analysis",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state
if "app" not in st.session_state:
    st.session_state.app = None
if "drawn_geometry" not in st.session_state:
    st.session_state.drawn_geometry = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

st.title("🌍 Yvynation - Interactive Area Drawing & Analysis")

# Sidebar
with st.sidebar:
    st.title("Configuration")
    
    # Initialize EE
    try:
        ee.Initialize(project=PROJECT_ID)
        st.success("✅ Earth Engine initialized")
    except Exception as e:
        st.error(f"❌ EE init failed: {e}")
    
    # Load app
    if st.button("Load Core Data"):
        with st.spinner("Loading MapBiomas and territories..."):
            try:
                st.session_state.app = YvynationApp()
                st.session_state.app.load_core_data()
                st.success("✅ Data loaded")
            except Exception as e:
                st.error(f"❌ Load failed: {e}")

# Main content
if not st.session_state.app:
    st.info("👈 Click 'Load Core Data' in the sidebar to begin")
else:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Draw Your Analysis Area")
        
        st.markdown('''
        ### Instructions:
        1. Use the **Rectangle tool** (top-left) to draw your analysis area
        2. You can draw **multiple rectangles** or **polygons**
        3. Select/deselect layers with the **layer control** (top-right)
        4. **Click "Analyze Drawn Area"** to get results
        
        ### Visible Layers:
        - 🌍 **MapBiomas 2023** - Land cover classification
        - 🏘️ **Indigenous Territories** - Official boundaries
        ''')
        
        # Create map
        m = folium.Map(
            location=[-4.5, -45.3],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        try:
            # Add MapBiomas
            mapbiomas = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')
            classification_2023 = mapbiomas.select('classification_2023')
            
            vis_params = {'min': 0, 'max': 62, 'palette': ['#000000', '#228B22', '#00FF00', '#0000FF', '#FF0000']}
            mapid = ee.Image(classification_2023).getMapId(vis_params)
            
            folium.TileLayer(
                tiles=mapid['tile_fetcher'].url_format,
                attr='MapBiomas',
                name='MapBiomas 2023',
                overlay=True,
                control=True
            ).add_to(m)
            
            # Add territories
            territories = ee.FeatureCollection('projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES')
            ee_image = ee.Image().paint(territories, 0, 2)
            mapid_territories = ee_image.getMapId({'min': 0, 'max': 1, 'palette': ['red']})
            
            folium.TileLayer(
                tiles=mapid_territories['tile_fetcher'].url_format,
                attr='Indigenous Territories',
                name='Indigenous Territories',
                overlay=True,
                control=True
            ).add_to(m)
            
        except Exception as e:
            st.warning(f"Layer loading: {e}")
        
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
        
        Fullscreen().add_to(m)
        folium.LayerControl().add_to(m)
        
        # Display map
        map_data = streamlit_folium.folium_static(m, width=1400, height=700)
    
    with col2:
        st.subheader("Actions")
        
        if st.button("📊 Analyze Drawn Area", use_container_width=True):
            st.info("⚠️ Note: Drawing exports work best in full-screen mode")
            st.info('''
            **To analyze a drawn area:**
            1. Draw a rectangle/polygon on the map
            2. Click the export button (⬇️ icon in toolbar)
            3. Save the GeoJSON file
            4. Upload it below
            ''')
        
        st.divider()
        
        # File uploader for GeoJSON
        uploaded_file = st.file_uploader("Upload GeoJSON from map export", type=['geojson', 'json'])
        
        if uploaded_file:
            try:
                geojson_data = json.load(uploaded_file)
                st.success("✅ GeoJSON loaded")
                
                # Parse geometry
                if 'features' in geojson_data:
                    features = geojson_data['features']
                    st.write(f"Found {len(features)} features")
                    
                    if st.button("Run Analysis on Geometry"):
                        with st.spinner("Analyzing..."):
                            try:
                                # Get first feature's geometry
                                first_feature = features[0]
                                coords = first_feature['geometry']['coordinates']
                                
                                # Create ee.Geometry from coordinates
                                if first_feature['geometry']['type'] == 'Polygon':
                                    geom = ee.Geometry.Polygon(coords[0])
                                elif first_feature['geometry']['type'] == 'Rectangle':
                                    geom = ee.Geometry.Rectangle(coords)
                                else:
                                    geom = ee.Geometry(first_feature['geometry'])
                                
                                # Clip and analyze
                                mapbiomas = st.session_state.app.mapbiomas['v9']
                                clipped = clip_mapbiomas_to_geometry(
                                    mapbiomas.select('classification_2023'),
                                    geom,
                                    30
                                )
                                
                                area_df = calculate_area_by_class(clipped, geom, 2023)
                                
                                st.session_state.analysis_results = area_df
                                st.success("✅ Analysis complete!")
                                
                                # Show results
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.dataframe(area_df.head(15), use_container_width=True)
                                with col_b:
                                    fig = plot_area_distribution(area_df, year=2023, top_n=10)
                                    st.pyplot(fig)
                                
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                                st.info(str(e))
                
            except Exception as e:
                st.error(f"GeoJSON parsing failed: {e}")
