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
from config import PROJECT_ID, MAPBIOMAS_LABELS, MAPBIOMAS_COLOR_MAP, HANSEN_CONSOLIDATED_MAPPING, HANSEN_CONSOLIDATED_COLORS
from ee_auth import initialize_earth_engine
from map_manager import create_base_map, add_territories_layer
from ee_layers import add_mapbiomas_layer, add_hansen_layer
from app_file import YvynationApp
from mapbiomas_analysis import calculate_area_by_class as mapbiomas_area_analysis
from hansen_analysis import hansen_histogram_to_dataframe
from hansen_consolidated_utils import (
    get_consolidated_class,
    get_consolidated_color,
    aggregate_to_consolidated,
    create_comparison_dataframe,
    summarize_consolidated_stats
)
from territory_analysis import (
    get_territory_names,
    get_territory_geometry,
    analyze_territory_mapbiomas,
    analyze_territory_hansen,
    initialize_territory_session_state
)
from plotting_utils import (
    plot_area_distribution,
    plot_area_comparison,
    get_hansen_color,
    display_summary_metrics
)

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
if "use_consolidated_classes" not in st.session_state:
    st.session_state.use_consolidated_classes = True

# Initialize territory analysis session state
initialize_territory_session_state()

# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("📊 Yvynation")
st.sidebar.markdown("Indigenous Land Monitoring Platform")
st.sidebar.divider()

# Layer management section
with st.sidebar.expander("🎛️ Map Controls", expanded=True):
    st.markdown("**Layer Control:** Look for the ⌗ icon in the top-right corner of the map to toggle layers on/off")
    st.markdown("**Basemaps:** 4 basemap options available (OpenStreetMap, Google Satellite, ArcGIS Street, ArcGIS Terrain)")
    st.info("Tip: Overlay multiple basemaps and data layers to compare different views", icon="💡")

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

# Indigenous territories analysis
if st.session_state.data_loaded:
    with st.sidebar.expander("🏛️ Indigenous Territories Analysis", expanded=False):
        st.write("Analyze land cover in indigenous territories:")
        
        try:
            territories_fc = st.session_state.app.territories
            if territories_fc is None:
                st.error("❌ Territories data not loaded.")
            else:
                # Get territory names from Earth Engine
                territory_names, name_prop = get_territory_names(territories_fc)
                
                if not territory_names or not name_prop:
                    st.error("❌ Could not load territory names")
                else:
                    selected_territory = st.selectbox(
                        "Select a territory",
                        territory_names,
                        key="territory_select"
                    )
                    
                    # Data source selection
                    data_source = st.radio(
                        "Data Source",
                        ["MapBiomas", "Hansen/GLAD"],
                        horizontal=True,
                        key="territory_source_radio"
                    )
                    st.session_state.territory_source = data_source
                    
                    # Year selection
                    col1, col2 = st.columns(2)
                    with col1:
                        if data_source == "MapBiomas":
                            territory_year = st.selectbox(
                                "Year 1",
                                range(1985, 2024),
                                index=38,
                                key="year_territory_1"
                            )
                        else:
                            hansen_years = ["2000", "2005", "2010", "2015", "2020"]
                            territory_year = st.selectbox(
                                "Year 1",
                                hansen_years,
                                index=4,
                                key="year_territory_h1"
                            )
                    
                    with col2:
                        compare_mode = st.checkbox("Compare Years", value=False, key="territory_compare")
                        if compare_mode:
                            if data_source == "MapBiomas":
                                territory_year2 = st.selectbox(
                                    "Year 2",
                                    range(1985, 2024),
                                    index=30,
                                    key="year_territory_2"
                                )
                            else:
                                hansen_years = ["2000", "2005", "2010", "2015", "2020"]
                                territory_year2 = st.selectbox(
                                    "Year 2",
                                    hansen_years,
                                    index=0,
                                    key="year_territory_h2"
                                )
                        else:
                            territory_year2 = None
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        analyze_btn = st.button("📊 Analyze", key="btn_analyze_territory", use_container_width=True)
                    with col_btn2:
                        add_layer_btn = st.button("➕ Add to Map", key="btn_add_territory_layer", use_container_width=True)
                    
                    if add_layer_btn:
                        try:
                            # Filter to selected territory and store geometry
                            territory_geom = territories_fc.filter(
                                ee.Filter.eq(name_prop, selected_territory)
                            ).first().geometry()
                            
                            # Store geometry and flag for map display
                            st.session_state.territory_geom = territory_geom
                            st.session_state.add_territory_layer_to_map = True
                            st.session_state.territory_layer_name = selected_territory
                            
                            st.success(f"✅ Territory '{selected_territory}' added to map - scroll down to see map")
                        
                        except Exception as e:
                            st.error(f"❌ Failed to add territory layer: {e}")
                            import traceback
                            traceback.print_exc()

                    
                    if analyze_btn:
                        with st.spinner(f"Analyzing {selected_territory}..."):
                            try:
                                # Get territory geometry
                                territory_geom = get_territory_geometry(territories_fc, selected_territory, name_prop)
                                if not territory_geom:
                                    st.error("❌ Could not get territory geometry")
                                else:
                                    # Store geometry
                                    st.session_state.territory_geom = territory_geom
                                    st.session_state.territory_name = selected_territory
                                    st.session_state.territory_source = data_source
                                    st.session_state.add_analysis_layer_to_map = False
                                    
                                    if data_source == "MapBiomas":
                                        # Analyze MapBiomas
                                        mapbiomas = st.session_state.app.mapbiomas_v9
                                        band = f'classification_{territory_year}'
                                        area_df = analyze_territory_mapbiomas(mapbiomas, territory_geom, territory_year)
                                        
                                        st.session_state.territory_result = area_df
                                        st.session_state.territory_year = territory_year
                                        st.session_state.territory_result_year2 = None
                                        # Store the image for visualization
                                        st.session_state.territory_analysis_image = mapbiomas.select(band)
                                        st.session_state.territory_analysis_image_year2 = None
                                        
                                        # Comparison year
                                        if compare_mode and territory_year2:
                                            band2 = f'classification_{territory_year2}'
                                            area_df2 = analyze_territory_mapbiomas(mapbiomas, territory_geom, territory_year2)
                                            st.session_state.territory_result_year2 = area_df2
                                            st.session_state.territory_year2 = territory_year2
                                            st.session_state.territory_analysis_image_year2 = mapbiomas.select(band2)
                                    
                                    else:  # Hansen
                                        # Analyze Hansen
                                        try:
                                            area_df, hansen_image = analyze_territory_hansen(
                                                st.session_state.ee_module,
                                                territory_geom,
                                                territory_year,
                                                st.session_state.use_consolidated_classes
                                            )
                                            
                                            st.session_state.territory_result = area_df
                                            st.session_state.territory_year = str(territory_year)
                                            st.session_state.territory_result_year2 = None
                                            st.session_state.territory_analysis_image = hansen_image
                                            st.session_state.territory_analysis_image_year2 = None
                                            
                                            # Comparison year
                                            if compare_mode and territory_year2 and territory_year2 != territory_year:
                                                area_df2, hansen_image2 = analyze_territory_hansen(
                                                    st.session_state.ee_module,
                                                    territory_geom,
                                                    territory_year2,
                                                    st.session_state.use_consolidated_classes
                                                )
                                                st.session_state.territory_result_year2 = area_df2
                                                st.session_state.territory_year2 = str(territory_year2)
                                                st.session_state.territory_analysis_image_year2 = hansen_image2
                                        except Exception as hansen_error:
                                            st.error(f"❌ Hansen analysis failed: {hansen_error}")
                                            raise
                                    
                                    st.session_state.add_analysis_layer_to_map = True
                                    st.success(f"✅ Analysis complete for {selected_territory}")

                            
                            except Exception as e:
                                st.error(f"❌ Analysis failed: {e}")
                                import traceback
                                traceback.print_exc()
        
        except Exception as e:
            st.error(f"❌ Territory analysis error: {e}")

st.sidebar.divider()

# View options
with st.sidebar.expander("🎨 View Options", expanded=True):
    use_consolidated = st.checkbox(
        "Show Consolidated Classes",
        value=st.session_state.use_consolidated_classes,
        help="Group Hansen 256 classes into 12 consolidated categories for cleaner visualization"
    )
    st.session_state.use_consolidated_classes = use_consolidated
    
    if use_consolidated:
        st.caption("📊 Consolidated view: 256 classes → 12 categories")
    else:
        st.caption("📊 Detailed view: All 256 original classes")

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

# Display current layer configuration
if st.session_state.data_loaded:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Base Layer", "OpenStreetMap", help="Switch in map controls (top-right)")
        
    with col2:
        mapbiomas_count = len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
        st.metric("MapBiomas Layers", mapbiomas_count, help="Brazil land cover (1985-2023)")
        
    with col3:
        hansen_count = len([y for y, v in st.session_state.hansen_layers.items() if v])
        st.metric("Hansen Layers", hansen_count, help="Global forest change (2000-2020)")
    
    # Show active layers
    st.divider()
    st.subheader("📋 Active Layers")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.mapbiomas_layers:
            years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            if years:
                st.write("**MapBiomas Years:**")
                st.write(", ".join(map(str, years)))
            else:
                st.caption("No MapBiomas layers selected")
        else:
            st.caption("No MapBiomas layers added")
    
    with col2:
        if st.session_state.hansen_layers:
            years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
            if years:
                st.write("**Hansen Years:**")
                st.write(", ".join(map(str, years)))
            else:
                st.caption("No Hansen layers selected")
        else:
            st.caption("No Hansen layers added")

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

# Add territory boundary layer if requested
if st.session_state.add_territory_layer_to_map and st.session_state.territory_geom and st.session_state.territory_layer_name:
    try:
        territory_geom = st.session_state.territory_geom
        territory_name = st.session_state.territory_layer_name
        
        # Get territory GeoJSON directly
        territory_geojson = territory_geom.getInfo()
        
        # Create a GeoJSON layer with strong styling
        folium.GeoJson(
            data=territory_geojson,
            name=f"Territory: {territory_name}",
            style_function=lambda x: {
                'fillColor': '#FF0000',
                'color': '#FF0000',
                'weight': 3,
                'opacity': 0.9,
                'fillOpacity': 0.2
            },
            overlay=True,
            control=True,
            highlight_function=lambda x: {
                'fillColor': '#FF6B6B',
                'color': '#FF6B6B',
                'weight': 4,
                'opacity': 1.0,
                'fillOpacity': 0.3
            }
        ).add_to(display_map)
        
        # Zoom to territory bounds
        bounds_info = territory_geom.bounds().getInfo()
        if bounds_info and bounds_info.get('coordinates'):
            coords = bounds_info['coordinates'][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            sw = [min(lats), min(lons)]
            ne = [max(lats), max(lons)]
            display_map.fit_bounds([sw, ne])
            print(f"✓ Territory {territory_name} added to map with bounds: {sw} to {ne}")
    
    except Exception as e:
        print(f"❌ Error adding territory layer: {e}")
        import traceback
        traceback.print_exc()

# Add analyzed data layer if available
if st.session_state.add_analysis_layer_to_map and st.session_state.territory_analysis_image and st.session_state.territory_geom:
    try:
        analysis_image = st.session_state.territory_analysis_image
        territory_geom = st.session_state.territory_geom
        
        # Get visualization parameters based on data source
        if st.session_state.territory_source == "MapBiomas":
            from config import MAPBIOMAS_PALETTE
            vis_params = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
            layer_name = f"MapBiomas Analysis ({st.session_state.territory_year})"
        else:  # Hansen
            from config import HANSEN_PALETTE
            vis_params = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
            layer_name = f"Hansen Analysis ({st.session_state.territory_year})"
        
        # Add the analyzed layer as a map tile
        map_id = analysis_image.getMapId(vis_params)
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr=f'{st.session_state.territory_source} Analysis',
            name=layer_name,
            overlay=True,
            control=True,
            opacity=0.7
        ).add_to(display_map)
        
        print(f"✓ Analysis layer added to map: {layer_name}")
        
        # Add second year analysis if available
        if st.session_state.territory_analysis_image_year2:
            try:
                analysis_image_year2 = st.session_state.territory_analysis_image_year2
                
                map_id2 = analysis_image_year2.getMapId(vis_params)
                layer_name2 = f"{st.session_state.territory_source} Analysis ({st.session_state.territory_year2})"
                folium.TileLayer(
                    tiles=map_id2['tile_fetcher'].url_format,
                    attr=f'{st.session_state.territory_source} Analysis',
                    name=layer_name2,
                    overlay=True,
                    control=True,
                    opacity=0.7
                ).add_to(display_map)
                
                print(f"✓ Comparison layer added to map: {layer_name2}")
            except Exception as year2_error:
                print(f"⚠️ Could not add second year analysis: {year2_error}")
    
    except Exception as e:
        print(f"❌ Error adding analysis layer: {e}")
        import traceback
        traceback.print_exc()

# Add layer control with enhanced styling
layer_control = folium.LayerControl(position='topright', collapsed=False)
layer_control.add_to(display_map)

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

# Show layer legend
col1, col2 = st.columns([3, 1])
with col1:
    st.caption("🎨 Draw polygons on the map to analyze land cover. Use the layer control (⌗ top-right) to toggle layers.")
with col2:
    # Quick layer summary
    active_layers = 0
    if st.session_state.data_loaded:
        active_layers = 1  # Basemap
        active_layers += len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
        active_layers += len([y for y, v in st.session_state.hansen_layers.items() if v])
    st.metric("Active Layers", active_layers)

try:
    map_data = st_folium(display_map, use_container_width=True, height=600)
    
    # Capture drawn features from the map
    if map_data and "all_drawings" in map_data and map_data["all_drawings"]:
        st.session_state.last_drawn_feature = map_data["all_drawings"][-1]  # Get the last drawn feature
        st.info(f"✓ Captured {len(map_data['all_drawings'])} drawn feature(s)")
    elif map_data and "last_active_drawing" in map_data:
        st.session_state.last_drawn_feature = map_data["last_active_drawing"]
    
except Exception as e:
    st.warning(f"Map display error: {e}")
    print(f"Error displaying map: {e}")

# Display layer reference guide
st.divider()
with st.expander("📚 Layer Reference Guide", expanded=False):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Basemaps**")
        st.caption("""
        - 🗺️ OpenStreetMap (default)
        - 🛰️ Google Satellite
        - 🛣️ ArcGIS Street
        - ⛰️ ArcGIS Terrain
        """)
    
    with col2:
        st.markdown("**Data Layers**")
        st.caption("""
        - 🌱 MapBiomas: Brazilian land cover (1985-2023)
        - 🌍 Hansen: Global forest change (2000-2020)
        - 📍 Indigenous Territories
        """)
    
    with col3:
        st.markdown("**Controls**")
        st.caption("""
        - ⌗ Layer Control: top-right corner
        - ✏️ Drawing Tools: top-left corner
        - 🎨 Opacity: Adjust in sidebar
        """)

# ============================================================================
# ANALYSIS SECTION
# ============================================================================

# Display territory analysis results if available
if st.session_state.data_loaded and st.session_state.territory_result is not None:
    st.divider()
    
    # Check if comparing years
    if st.session_state.territory_result_year2 is not None:
        st.subheader(f"🏛️ Territory Comparison - {st.session_state.territory_name}")
        
        # Comparison tabs
        comp_tab1, comp_tab2, comp_tab3 = st.tabs(
            ["📊 Side-by-Side Comparison", "📋 Data Tables", "ℹ️ Territory Info"]
        )
        
        with comp_tab1:
            st.markdown(f"### Land Cover Distribution Comparison in {st.session_state.territory_name}")
            fig = plot_area_comparison(
                st.session_state.territory_result,
                st.session_state.territory_result_year2,
                st.session_state.territory_year,
                st.session_state.territory_year2,
                top_n=15
            )
            st.pyplot(fig, use_container_width=True)
        
        with comp_tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"### Year {st.session_state.territory_year}")
                display_cols = ['Name', 'Class_ID', 'Pixels', 'Area_ha'] if 'Name' in st.session_state.territory_result.columns else ['Class', 'Class_ID', 'Pixels', 'Area_ha']
                st.dataframe(st.session_state.territory_result[display_cols], use_container_width=True)
                csv1 = st.session_state.territory_result.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv1,
                    file_name=f"{st.session_state.territory_name}_{st.session_state.territory_year}.csv",
                    mime="text/csv",
                    key="download_comp_1"
                )
            
            with col2:
                st.markdown(f"### Year {st.session_state.territory_year2}")
                display_cols = ['Name', 'Class_ID', 'Pixels', 'Area_ha'] if 'Name' in st.session_state.territory_result_year2.columns else ['Class', 'Class_ID', 'Pixels', 'Area_ha']
                st.dataframe(st.session_state.territory_result_year2[display_cols], use_container_width=True)
                csv2 = st.session_state.territory_result_year2.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv2,
                    file_name=f"{st.session_state.territory_name}_{st.session_state.territory_year2}.csv",
                    mime="text/csv",
                    key="download_comp_2"
                )
        
        with comp_tab3:
            st.markdown(f"### Territory Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Year {st.session_state.territory_year}**")
                total_area1 = st.session_state.territory_result['Area_ha'].sum()
                num_classes1 = len(st.session_state.territory_result)
                largest_class1 = st.session_state.territory_result.loc[st.session_state.territory_result['Area_ha'].idxmax()]
                
                st.metric("Total Area", f"{total_area1:,.0f} ha")
                st.metric("Classes", num_classes1)
                st.metric("Largest Class", largest_class1['Class'])
            
            with col2:
                st.markdown(f"**Year {st.session_state.territory_year2}**")
                total_area2 = st.session_state.territory_result_year2['Area_ha'].sum()
                num_classes2 = len(st.session_state.territory_result_year2)
                largest_class2 = st.session_state.territory_result_year2.loc[st.session_state.territory_result_year2['Area_ha'].idxmax()]
                
                st.metric("Total Area", f"{total_area2:,.0f} ha")
                st.metric("Classes", num_classes2)
                st.metric("Largest Class", largest_class2['Class'])
            
            st.divider()
            st.info(f"Territory: **{st.session_state.territory_name}**")
            st.info(f"Data Source: **{st.session_state.territory_source}**")
    
    else:
        # Single year analysis
        st.subheader(f"🏛️ Territory Analysis - {st.session_state.territory_name}")
        
        # Show territory results in tabs
        terr_tab1, terr_tab2, terr_tab3 = st.tabs(
            ["📊 Land Cover Distribution", "📋 Data Table", "ℹ️ Territory Info"]
        )
        
        with terr_tab1:
            st.markdown(f"### Land Cover Distribution in {st.session_state.territory_name} ({st.session_state.territory_year})")
            fig = plot_area_distribution(st.session_state.territory_result, year=st.session_state.territory_year, top_n=15)
            st.pyplot(fig, use_container_width=True)
        
        with terr_tab2:
            st.markdown(f"### Raw Data - {st.session_state.territory_name} ({st.session_state.territory_year})")
            # Display with Name column if available
            display_cols = ['Name', 'Class_ID', 'Pixels', 'Area_ha'] if 'Name' in st.session_state.territory_result.columns else ['Class', 'Class_ID', 'Pixels', 'Area_ha']
            st.dataframe(st.session_state.territory_result[display_cols], use_container_width=True)
            
            # Download CSV option
            csv = st.session_state.territory_result.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"{st.session_state.territory_name}_{st.session_state.territory_year}.csv",
                mime="text/csv"
            )
        
        with terr_tab3:
            st.markdown(f"### Territory Information")
            
            # Calculate summary statistics
            total_area = st.session_state.territory_result['Area_ha'].sum()
            num_classes = len(st.session_state.territory_result)
            largest_class = st.session_state.territory_result.loc[st.session_state.territory_result['Area_ha'].idxmax()]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Area", f"{total_area:,.0f} ha", help="Total area analyzed")
            with col2:
                st.metric("Classes", num_classes, help="Number of land cover classes detected")
            with col3:
                st.metric("Largest Class", largest_class['Class'], help=f"{largest_class['Area_ha']:,.0f} ha")
            
            st.info(f"Territory: **{st.session_state.territory_name}**")
            st.info(f"Year: **{st.session_state.territory_year}**")
            st.info(f"Data Source: **{st.session_state.territory_source}**")

if st.session_state.data_loaded and st.session_state.app:
    st.divider()
    st.subheader("📊 Analysis & Statistics")
    
    # Check if a feature was drawn
    if st.session_state.last_drawn_feature:
        try:
            feature_data = st.session_state.last_drawn_feature
            geometry = None
            
            # Extract geometry from drawn feature GeoJSON
            if isinstance(feature_data, dict):
                if 'geometry' in feature_data:
                    # Feature format: {"geometry": {...}, "properties": {...}}
                    geometry = ee.Geometry(feature_data['geometry'])
                elif 'type' in feature_data and feature_data['type'] == 'Polygon':
                    # Direct Polygon GeoJSON
                    geometry = ee.Geometry.Polygon(feature_data['coordinates'])
                elif 'type' in feature_data and feature_data['type'] == 'LineString':
                    # LineString (from drawing)
                    geometry = ee.Geometry.LineString(feature_data['coordinates'])
            
            if not geometry:
                st.warning("⚠️ Could not extract geometry from drawn feature")
            else:
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
                                        
                                        # Get bounds of the geometry for validation
                                        geom_bounds = geometry.bounds().getInfo()
                                        st.caption(f"Bounds: {geom_bounds.get('coordinates', 'unknown')}")
                                        
                                        with st.spinner(f"Analyzing {year}..."):
                                            stats = image.reduceRegion(
                                                reducer=ee.Reducer.frequencyHistogram(),
                                                geometry=geometry,
                                                scale=30,
                                                maxPixels=1e9
                                            ).getInfo()
                                        
                                        if stats:
                                            from config import MAPBIOMAS_LABELS
                                            # MapBiomas returns data with band name as key, not 'b1'
                                            band_key = f'classification_{year}' if f'classification_{year}' in stats else list(stats.keys())[0]
                                            histogram_data = stats.get(band_key, {})
                                            
                                            if histogram_data:
                                                records = []
                                                for class_id, count in histogram_data.items():
                                                    class_id = int(class_id)
                                                    class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                                                    area_ha = count * 0.09
                                                    records.append({
                                                        "Class_ID": class_id,
                                                        "Class": class_name,
                                                        "Pixels": int(count),
                                                        "Area_ha": round(area_ha, 2)
                                                    })
                                                df = pd.DataFrame(records).sort_values("Area_ha", ascending=False)
                                                
                                                # Show data table
                                                st.dataframe(df[['Class', 'Pixels', 'Area_ha']], use_container_width=True)
                                                
                                                # Show plot
                                                fig = plot_area_distribution(df, year=year, top_n=15)
                                                st.pyplot(fig, use_container_width=True)
                                                st.success(f"✓ {year}: {len(records)} classes found")
                                            else:
                                                st.warning(f"Empty histogram for {year}")
                                        else:
                                            st.warning(f"No stats returned for {year}")
                                    except Exception as e:
                                        st.error(f"Error analyzing {year}: {str(e)[:200]}")
                                        print(f"Full error: {e}")
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
                                                # Consolidate if toggled
                                                if st.session_state.use_consolidated_classes:
                                                    df_display = aggregate_to_consolidated(df)
                                                    st.markdown("**Consolidated View (12 classes)**")
                                                else:
                                                    df_display = df
                                                    st.markdown("**Detailed View (256 classes)**")
                                                
                                                # Prepare columns for display
                                                if 'Name' in df_display.columns:
                                                    display_cols = ['Name', 'Class_ID', 'Pixels', 'Area_ha']
                                                elif 'Consolidated_Class' in df_display.columns:
                                                    display_cols = ['Consolidated_Class', 'Class_ID', 'Pixels', 'Area_ha']
                                                else:
                                                    display_cols = ['Class', 'Class_ID', 'Pixels', 'Area_ha']
                                                st.dataframe(df_display[display_cols], use_container_width=True)
                                                
                                                # Show plot with consolidation
                                                fig = plot_area_distribution(df_display, year=year, top_n=15)
                                                st.pyplot(fig, use_container_width=True)
                                                
                                                # Show consolidated summary
                                                if st.session_state.use_consolidated_classes:
                                                    with st.expander("📊 Summary Statistics"):
                                                        summary = summarize_consolidated_stats(df_display, year=year)
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.metric("Total Area", f"{summary.get('total_area_ha', 0):,.0f} ha")
                                                        with col2:
                                                            st.metric("Classes", summary.get('num_classes', 0))
                                                        with col3:
                                                            st.metric("Largest Class", summary.get('largest_class', 'N/A'))
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
                    
                    # MapBiomas comparison
                    if st.session_state.mapbiomas_layers and st.session_state.app.mapbiomas_v9:
                        mapbiomas_years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
                        if len(mapbiomas_years) >= 2:
                            st.subheader("📊 MapBiomas Change Analysis")
                            col1, col2 = st.columns(2)
                            with col1:
                                year1 = st.selectbox(
                                    "Year 1 (baseline)",
                                    options=mapbiomas_years,
                                    key="mapbiomas_comp_year1"
                                )
                            with col2:
                                year2 = st.selectbox(
                                    "Year 2 (comparison)",
                                    options=mapbiomas_years,
                                    index=len(mapbiomas_years)-1,
                                    key="mapbiomas_comp_year2"
                                )
                            
                            if st.button("🔄 Compare MapBiomas Years", use_container_width=True, key="mapbiomas_compare"):
                                try:
                                    from config import MAPBIOMAS_LABELS
                                    
                                    with st.spinner(f"Comparing MapBiomas {year1} vs {year2}..."):
                                        # Get data for year 1
                                        band1 = f'classification_{year1}'
                                        image1 = st.session_state.app.mapbiomas_v9.select(band1)
                                        stats1 = image1.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        # Get data for year 2
                                        band2 = f'classification_{year2}'
                                        image2 = st.session_state.app.mapbiomas_v9.select(band2)
                                        stats2 = image2.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        # Process both histograms
                                        hist1 = stats1.get(band1, {})
                                        hist2 = stats2.get(band2, {})
                                        
                                        if hist1 and hist2:
                                            # Create comparison dataframe
                                            all_classes = set(hist1.keys()) | set(hist2.keys())
                                            records = []
                                            
                                            for class_id in sorted(map(int, all_classes)):
                                                class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                                                area1_ha = hist1.get(str(class_id), 0) * 0.09
                                                area2_ha = hist2.get(str(class_id), 0) * 0.09
                                                change_ha = area2_ha - area1_ha
                                                change_pct = (change_ha / area1_ha * 100) if area1_ha > 0 else 0
                                                
                                                records.append({
                                                    "Class": class_name,
                                                    f"{year1} (ha)": round(area1_ha, 2),
                                                    f"{year2} (ha)": round(area2_ha, 2),
                                                    "Change (ha)": round(change_ha, 2),
                                                    "Change %": round(change_pct, 1)
                                                })
                                            
                                            df = pd.DataFrame(records).sort_values("Change (ha)", ascending=False)
                                            st.dataframe(df, use_container_width=True)
                                            
                                            # Create comparison plot
                                            df_year1 = pd.DataFrame({
                                                'Class_ID': [int(cid) for cid in all_classes],
                                                'Area_ha': [hist1.get(str(int(cid)), 0) * 0.09 for cid in all_classes],
                                                'Class': [MAPBIOMAS_LABELS.get(int(cid), f"Class {cid}") for cid in all_classes]
                                            }).sort_values('Area_ha', ascending=False)
                                            
                                            df_year2 = pd.DataFrame({
                                                'Class_ID': [int(cid) for cid in all_classes],
                                                'Area_ha': [hist2.get(str(int(cid)), 0) * 0.09 for cid in all_classes],
                                                'Class': [MAPBIOMAS_LABELS.get(int(cid), f"Class {cid}") for cid in all_classes]
                                            }).sort_values('Area_ha', ascending=False)
                                            
                                            fig = plot_area_comparison(df_year1, df_year2, year1, year2, top_n=15)
                                            st.pyplot(fig, use_container_width=True)
                                            
                                            # Summary statistics
                                            total_change = df["Change (ha)"].sum()
                                            loss = df[df["Change (ha)"] < 0]["Change (ha)"].sum()
                                            gain = df[df["Change (ha)"] > 0]["Change (ha)"].sum()
                                            
                                            col1, col2, col3 = st.columns(3)
                                            with col1:
                                                st.metric("Total Change", f"{total_change:.0f} ha")
                                            with col2:
                                                st.metric("Loss", f"{loss:.0f} ha", delta=f"{loss:.0f}")
                                            with col3:
                                                st.metric("Gain", f"{gain:.0f} ha", delta=f"{gain:.0f}")
                                        else:
                                            st.error("Could not retrieve data for one or both years")
                                except Exception as e:
                                    st.error(f"Comparison error: {e}")
                        else:
                            st.info("Add 2 or more MapBiomas years to compare changes")
                    
                    # Hansen comparison
                    if st.session_state.hansen_layers:
                        hansen_years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
                        if len(hansen_years) >= 2:
                            st.subheader("📊 Hansen Change Analysis")
                            col1, col2 = st.columns(2)
                            with col1:
                                h_year1 = st.selectbox(
                                    "Year 1 (baseline)",
                                    options=hansen_years,
                                    key="hansen_comp_year1"
                                )
                            with col2:
                                h_year2 = st.selectbox(
                                    "Year 2 (comparison)",
                                    options=hansen_years,
                                    index=len(hansen_years)-1,
                                    key="hansen_comp_year2"
                                )
                            
                            if st.button("🔄 Compare Hansen Years", use_container_width=True, key="hansen_compare"):
                                try:
                                    from config import HANSEN_DATASETS, HANSEN_OCEAN_MASK
                                    
                                    with st.spinner(f"Comparing Hansen {h_year1} vs {h_year2}..."):
                                        landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
                                        
                                        # Get data for year 1
                                        hansen1 = ee.Image(HANSEN_DATASETS[str(h_year1)]).updateMask(landmask)
                                        stats1 = hansen1.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        # Get data for year 2
                                        hansen2 = ee.Image(HANSEN_DATASETS[str(h_year2)]).updateMask(landmask)
                                        stats2 = hansen2.reduceRegion(
                                            reducer=ee.Reducer.frequencyHistogram(),
                                            geometry=geometry,
                                            scale=30,
                                            maxPixels=1e9
                                        ).getInfo()
                                        
                                        if stats1 and stats2:
                                            df1 = hansen_histogram_to_dataframe(stats1, h_year1)
                                            df2 = hansen_histogram_to_dataframe(stats2, h_year2)
                                            
                                            if not df1.empty and not df2.empty:
                                                # Consolidate if toggled
                                                if st.session_state.use_consolidated_classes:
                                                    df1_disp = aggregate_to_consolidated(df1)
                                                    df2_disp = aggregate_to_consolidated(df2)
                                                else:
                                                    df1_disp = df1
                                                    df2_disp = df2
                                                
                                                # Merge on class
                                                merge_col = 'Consolidated_Class' if st.session_state.use_consolidated_classes else 'Class'
                                                df1_merge = df1_disp.rename(columns={"Area_ha": f"{h_year1}_ha"})[[merge_col, f"{h_year1}_ha"]]
                                                df2_merge = df2_disp.rename(columns={"Area_ha": f"{h_year2}_ha"})[[merge_col, f"{h_year2}_ha"]]
                                                
                                                df_comp = df1_merge.merge(df2_merge, on=merge_col, how="outer").fillna(0)
                                                df_comp["Change (ha)"] = df_comp[f"{h_year2}_ha"] - df_comp[f"{h_year1}_ha"]
                                                df_comp = df_comp.sort_values("Change (ha)", ascending=False, key=abs)
                                                
                                                st.markdown(f"**{'Consolidated' if st.session_state.use_consolidated_classes else 'Detailed'} View**")
                                                st.dataframe(df_comp, use_container_width=True)
                                                
                                                # Create comparison plot
                                                fig = plot_area_comparison(df1_disp, df2_disp, h_year1, h_year2, top_n=12)
                                                st.pyplot(fig, use_container_width=True)
                                                
                                                # Summary statistics
                                                total_change = df_comp["Change (ha)"].sum()
                                                loss = df_comp[df_comp["Change (ha)"] < 0]["Change (ha)"].sum()
                                                gain = df_comp[df_comp["Change (ha)"] > 0]["Change (ha)"].sum()
                                                
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("Total Change", f"{total_change:.0f} ha")
                                                with col2:
                                                    st.metric("Loss", f"{loss:.0f} ha", delta=f"{loss:.0f}")
                                                with col3:
                                                    st.metric("Gain", f"{gain:.0f} ha", delta=f"{gain:.0f}")
                                        else:
                                            st.error("Could not retrieve data for one or both years")
                                except Exception as e:
                                    st.error(f"Comparison error: {e}")
                        else:
                            st.info("Add 2 or more Hansen years to compare changes")
                    
                    if not (st.session_state.mapbiomas_layers or st.session_state.hansen_layers):
                        st.info("Add layers from the sidebar to enable comparisons")
                
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
