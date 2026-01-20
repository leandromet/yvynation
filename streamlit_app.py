'''
Yvynation - Indigenous Land Monitoring Platform
Refactored version with improved map handling and modular structure
'''

import streamlit as st
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded"
)

import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import pandas as pd

# Import custom modules
from config import PROJECT_ID
from ee_auth import initialize_earth_engine
from map_manager import create_base_map, add_territories_layer
from ee_layers import add_mapbiomas_layer, add_hansen_layer
from app_file import YvynationApp
from mapbiomas_analysis import calculate_area_by_class as mapbiomas_area_analysis
from hansen_analysis import hansen_histogram_to_dataframe

# ============================================================================
# INITIALIZATION
# ============================================================================

print("\n🚀 Yvynation App Starting...")

# Initialize Earth Engine
try:
    st.session_state.ee_module = initialize_earth_engine()
    print("✓ Earth Engine initialized")
except Exception as e:
    st.error(f"❌ Failed to initialize Earth Engine: {e}")
    st.stop()

# Auto-load core data
@st.cache_resource
def load_core_data():
    """Load MapBiomas and territories data once and cache it."""
    print("Loading core datasets...")
    try:
        app = YvynationApp()
        success = app.load_core_data()
        if success:
            print("✓ Core data loaded and cached")
            return app
        else:
            print("❌ Failed to load core data")
            return None
    except Exception as e:
        print(f"❌ Error loading core data: {e}")
        return None

# Load data automatically
if "app" not in st.session_state:
    st.session_state.app = load_core_data()
    if st.session_state.app:
        st.session_state.data_loaded = True

# Initialize session state
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "current_mapbiomas_year" not in st.session_state:
    st.session_state.current_mapbiomas_year = 2023
if "current_hansen_year" not in st.session_state:
    st.session_state.current_hansen_year = "2020"
if "mapbiomas_layers" not in st.session_state:
    st.session_state.mapbiomas_layers = {}  # {year: True/False}
if "hansen_layers" not in st.session_state:
    st.session_state.hansen_layers = {}  # {year: True/False}
if "last_drawn_feature" not in st.session_state:
    st.session_state.last_drawn_feature = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("📊 Yvynation")
st.sidebar.markdown("Indigenous Land Monitoring Platform")
st.sidebar.divider()

# Layer controls
if st.session_state.data_loaded:
    st.sidebar.subheader("🗺️ Add Map Layers")
    
    # MapBiomas section
    with st.sidebar.expander("MapBiomas (Brazil)", expanded=True):
        st.write("Select a year and add to map:")
        mapbiomas_year = st.select_slider(
            "Year",
            options=list(range(1985, 2024)),
            value=st.session_state.current_mapbiomas_year,
            key="mb_year_slider"
        )
        if st.button("➕ Add MapBiomas Layer", use_container_width=True, key="add_mapbiomas"):
            st.session_state.mapbiomas_layers[mapbiomas_year] = True
            st.session_state.current_mapbiomas_year = mapbiomas_year
            st.success(f"✓ Added MapBiomas {mapbiomas_year}")
    
    # Hansen section
    with st.sidebar.expander("Hansen/GLAD (Global)", expanded=False):
        st.write("Select a year and add to map:")
        hansen_years = ["2000", "2005", "2010", "2015", "2020"]
        hansen_year = st.selectbox(
            "Year",
            options=hansen_years,
            index=hansen_years.index(st.session_state.current_hansen_year),
            key="hansen_year_select"
        )
        if st.button("➕ Add Hansen Layer", use_container_width=True, key="add_hansen"):
            st.session_state.hansen_layers[hansen_year] = True
            st.session_state.current_hansen_year = hansen_year
            st.success(f"✓ Added Hansen {hansen_year}")

st.sidebar.divider()

# About section
with st.sidebar.expander("ℹ️ About", expanded=False):
    st.sidebar.markdown("""
    **Yvynation** is an interactive platform for analyzing land cover changes
    across indigenous territories using:
    
    - **MapBiomas**: Brazilian land cover classification (1985-2023)
    - **Hansen/GLAD**: Global forest change detection
    - **Earth Engine**: Real-time geospatial analysis
    
    Draw areas on the map to get detailed statistics.
    """)

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("🌎 Yvynation - Land Cover Analysis")

# Build map fresh each time with current layers
display_map = create_base_map()

# Add territories
if st.session_state.data_loaded and st.session_state.app:
    display_map = add_territories_layer(
        display_map,
        st.session_state.app.territories,
        opacity=0.7
    )

# Add stored MapBiomas layers
if st.session_state.data_loaded and st.session_state.app:
    for year in st.session_state.mapbiomas_layers:
        if st.session_state.mapbiomas_layers[year]:
            display_map = add_mapbiomas_layer(
                display_map,
                st.session_state.app.mapbiomas_v9,
                year,
                opacity=0.8
            )

# Add stored Hansen layers
if st.session_state.data_loaded and st.session_state.app:
    for year in st.session_state.hansen_layers:
        if st.session_state.hansen_layers[year]:
            display_map = add_hansen_layer(
                display_map,
                year,
                opacity=0.8
            )

# Add layer control
folium.LayerControl(position='topright', collapsed=False).add_to(display_map)

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
draw.add_to(display_map)

# Display the map
st.subheader("🗺️ Interactive Map")
st.caption("🎨 Draw polygons on the map to analyze land cover. Use sidebar controls to add data layers.")

try:
    map_data = st_folium(display_map, width=1200, height=600)
    if map_data and 'last_active_drawing' in map_data:
        st.session_state.last_drawn_feature = map_data['last_active_drawing']
except Exception as e:
    st.warning(f"Map display error: {e}")
    print(f"Error displaying map: {e}")

# ============================================================================
# ANALYSIS SECTION
# ============================================================================

if st.session_state.data_loaded and st.session_state.app:
    st.divider()
    st.subheader("📊 Analysis & Statistics")
    
    # Check if a feature was drawn
    if st.session_state.last_drawn_feature:
        try:
            feature_data = st.session_state.last_drawn_feature
            
            # Extract geometry from drawn feature
            if feature_data and 'geometry' in feature_data:
                geometry = ee.Geometry(feature_data['geometry'])
                
                # Create tabs for different analyses
                tab1, tab2, tab3, tab4 = st.tabs(
                    ["📍 MapBiomas Analysis", "🌍 Hansen Analysis", "📈 Comparison", "ℹ️ About"]
                )
                
                with tab1:
                    st.markdown("### MapBiomas Land Cover Analysis")
                    if st.session_state.mapbiomas_layers and st.session_state.app.mapbiomas_v9:
                        years_to_analyze = [y for y, enabled in st.session_state.mapbiomas_layers.items() if enabled]
                        if years_to_analyze:
                            st.write(f"Analyzing {len(years_to_analyze)} year(s) of data...")
                            for year in sorted(years_to_analyze):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.markdown(f"**Year {year}**")
                                    try:
                                        band = f'classification_{year}'
                                        image = st.session_state.app.mapbiomas_v9.select(band)
                                        stats = image.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        if stats and 'b1' in stats:
                                            from config import MAPBIOMAS_LABELS
                                            records = []
                                            for class_id, count in stats['b1'].items():
                                                class_id = int(class_id)
                                                class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                                                area_ha = count * 0.09
                                                records.append({
                                                    "Class": class_name,
                                                    "Pixels": count,
                                                    "Area (ha)": round(area_ha, 2)
                                                })
                                            df = pd.DataFrame(records).sort_values("Area (ha)", ascending=False)
                                            st.dataframe(df, use_container_width=True)
                                        else:
                                            st.info("No data in selected area for this year")
                                    except Exception as e:
                                        st.error(f"Error analyzing {year}: {e}")
                        else:
                            st.info("Add a MapBiomas layer from the sidebar to analyze")
                    else:
                        st.info("Load data and add a MapBiomas layer to begin analysis")
                
                with tab2:
                    st.markdown("### Hansen/GLAD Forest Change Analysis")
                    if st.session_state.hansen_layers and st.session_state.app:
                        years_to_analyze = [y for y, enabled in st.session_state.hansen_layers.items() if enabled]
                        if years_to_analyze:
                            st.write(f"Analyzing {len(years_to_analyze)} year(s) of data...")
                            for year in sorted(years_to_analyze):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.markdown(f"**Year {year}**")
                                    try:
                                        from config import HANSEN_DATASETS, HANSEN_OCEAN_MASK
                                        landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
                                        hansen_image = ee.Image(HANSEN_DATASETS[str(year)]).updateMask(landmask)
                                        
                                        stats = hansen_image.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        if stats:
                                            df = hansen_histogram_to_dataframe(stats, year)
                                            if not df.empty:
                                                st.dataframe(df, use_container_width=True)
                                            else:
                                                st.info("No data in selected area for this year")
                                        else:
                                            st.info("No data in selected area for this year")
                                    except Exception as e:
                                        st.error(f"Error analyzing {year}: {e}")
                        else:
                            st.info("Add a Hansen layer from the sidebar to analyze")
                    else:
                        st.info("Load data and add a Hansen layer to begin analysis")
                
                with tab3:
                    st.markdown("### Multi-Year Comparison")
                    if st.session_state.mapbiomas_layers or st.session_state.hansen_layers:
                        st.info("Select years from different datasets in tabs 1-2 to compare changes over time")
                    else:
                        st.info("Add layers from the sidebar to compare")
                
                with tab4:
                    col1, col2 = st.columns(2)
                    with col1:
                        with st.expander("📍 MapBiomas Info"):
                            st.markdown("""
                            **MapBiomas** is a Brazilian initiative that provides detailed land cover mapping:
                            - Annual classification since 1985
                            - 30-meter resolution
                            - 25+ land cover classes
                            - Covers all of Brazil
                            """)
                    with col2:
                        with st.expander("🌍 Hansen/GLAD Info"):
                            st.markdown("""
                            **Hansen/GLAD** detects global forest changes:
                            - Global coverage (all continents)
                            - 30-meter resolution
                            - Forest loss and gain tracking
                            - Available 2000-2020+
                            """)
        except Exception as e:
            st.error(f"Error processing drawn feature: {e}")
            print(f"Analysis error: {e}")
    else:
        st.info("🎨 Draw a polygon on the map to start analyzing land cover in that area. Use the drawing tools in the top-left of the map.")

print("\n✓ Yvynation App Loaded Successfully")
