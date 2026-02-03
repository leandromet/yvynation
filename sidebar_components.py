"""
Sidebar components for Yvynation app.
Handles all sidebar UI including layer controls, territory analysis, and settings.
"""

import streamlit as st
import ee
import traceback
from territory_analysis import (
    get_territory_names,
    get_territory_geometry,
    analyze_territory_mapbiomas,
    analyze_territory_hansen
)


def render_sidebar_header():
    """Render the sidebar title and description."""
    st.sidebar.title("🌎🌍🌏🏞️ Yvynation 🛰️🗺️🌳🌲")
    st.sidebar.markdown("Indigenous Land Monitoring Platform")
    st.sidebar.markdown("Leandro M. Biondo - PhD Candidate - IGS/UBCO")
    st.sidebar.divider()


def render_map_controls():
    """Render map controls help section."""
    with st.sidebar.expander("🎛️ Map Controls", expanded=False):
        st.markdown("**Layer Control:** Look for the ⌗ icon in the top-right corner of the map to toggle layers on/off")
        st.markdown("**Basemaps:** 6 basemap options available (OpenStreetMap, Google Maps, Google Satellite, ArcGIS Street, ArcGIS Satellite, ArcGIS Terrain) - Google Maps is selected by default")
        st.info("Tip: Overlay multiple basemaps and data layers to compare different views", icon="💡")


def render_layer_selection():
    """Render map layer selection controls (MapBiomas and Hansen)."""
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


def render_territory_analysis():
    """Render territory analysis controls."""
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
                            add_layer_btn = st.button("➕ Zoom to Territory", key="btn_add_territory_layer", use_container_width=True)
                        
                        if add_layer_btn:
                            try:
                                # Filter to selected territory and store geometry
                                territory_geom = territories_fc.filter(
                                    ee.Filter.eq(name_prop, selected_territory)
                                ).first().geometry()
                                
                                # Store geometry and flag for map display
                                st.session_state.territory_geom = territory_geom
                                st.session_state.territory_geometry_for_analysis = territory_geom
                                st.session_state.add_territory_layer_to_map = True
                                st.session_state.territory_layer_name = selected_territory
                                
                                st.success(f"✅ Territory '{selected_territory}' added to map - scroll down to see map")
                            
                            except Exception as e:
                                st.error(f"❌ Failed to add territory layer: {e}")
                                traceback.print_exc()
                        
                        if analyze_btn:
                            with st.spinner(f"Analyzing {selected_territory}..."):
                                try:
                                    # Get territory geometry
                                    territory_geom = get_territory_geometry(territories_fc, selected_territory, name_prop)
                                    if not territory_geom:
                                        st.error("❌ Could not get territory geometry")
                                    else:
                                        # Store geometry with distinct key for analysis
                                        st.session_state.territory_geom = territory_geom
                                        st.session_state.territory_geometry_for_analysis = territory_geom
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
                                            st.session_state.territory_analysis_source = "MapBiomas"
                                            st.session_state.territory_analysis_image_year2 = None
                                            
                                            # Comparison year
                                            if compare_mode and territory_year2:
                                                band2 = f'classification_{territory_year2}'
                                                area_df2 = analyze_territory_mapbiomas(mapbiomas, territory_geom, territory_year2)
                                                st.session_state.territory_result_year2 = area_df2
                                                st.session_state.territory_year2 = territory_year2
                                                st.session_state.territory_analysis_image_year2 = mapbiomas.select(band2)
                                                st.session_state.territory_analysis_source_year2 = "MapBiomas"
                                        
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
                                                st.session_state.territory_analysis_source = "Hansen/GLAD"
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
                                                    st.session_state.territory_analysis_source_year2 = "Hansen/GLAD"
                                            except Exception as hansen_error:
                                                st.error(f"❌ Hansen analysis failed: {hansen_error}")
                                                raise
                                        
                                        st.session_state.add_analysis_layer_to_map = True
                                        st.success(f"✅ Analysis complete for {selected_territory}")
                                
                                except Exception as e:
                                    st.error(f"❌ Analysis failed: {e}")
                                    traceback.print_exc()
            
            except Exception as e:
                st.error(f"❌ Territory analysis error: {e}")


def render_view_options():
    """Render view options (consolidated classes toggle)."""
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


def render_about_section():
    """Render the about/info section."""
    with st.sidebar.expander("ℹ️ About", expanded=False):
        st.sidebar.markdown("""
        ### Project Overview

        This land use and land cover analysis tool is part of a research project studying 
        environmental changes in Brazilian Indigenous Territories using Google Earth Engine 
        and MapBiomas data. This data is compared with policy changes and deforestation trends 
        to understand the impacts on these critical lands.

        **Leandro Meneguelli Biondo** - PhD Candidate in Sustainability - IGS/UBCO
        Supervisor: Dr. Jon Corbett

        **Yvynation** is a name for this app, as it is not the full project content.

        "Yvy" (Tupi–Guarani) means land, earth, or territory — emphasizing the ground we walk 
        on and our sacred connection to nature. It often relates to the concept of 
        "Yvy marãe'ỹ" (Land without evil).

        "Nation" refers to a self-governing community or people with shared culture, 
        history, language, and land. It signifies self-determination and governance.

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

        ✅ Interactive mapping with real-time data  
        ✅ Area calculations and change detection  
        ✅ Territory filtering by state or name  
        ✅ Statistical visualizations  
        ✅ Data export capabilities

        ### Technologies

        - Python 3.8+
        - Google Earth Engine API
        - geemap (interactive mapping)
        - Streamlit (web interface)
        - pandas, matplotlib, seaborn (analysis & visualization)
        """)


def render_complete_sidebar():
    """Render the entire sidebar with all components."""
    render_sidebar_header()
    render_map_controls()
    st.sidebar.divider()
    render_layer_selection()
    st.sidebar.divider()
    render_territory_analysis()
    st.sidebar.divider()
    render_view_options()
    st.sidebar.divider()
    render_about_section()
