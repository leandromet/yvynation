"""
UI Components Module
Shared UI components and utilities
"""

import streamlit as st


def render_map_controls():
    """Render map controls for MapBiomas"""
    with st.expander("Map Controls", expanded=False):
        st.subheader("🇧🇷 MapBiomas (Brazil) Layers")
        st.info("Data: MapBiomas Collection 9 - Brazilian land cover classification")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.slider("Latitude", -33.0, 5.0, st.session_state.mapbiomas_map_center_lat, key="lat_mapbiomas")
            st.session_state.mapbiomas_map_center_lat = center_lat
        with col2:
            center_lon = st.slider("Longitude", -75.0, -35.0, st.session_state.mapbiomas_map_center_lon, key="lon_mapbiomas")
            st.session_state.mapbiomas_map_center_lon = center_lon
        
        zoom = st.slider("Zoom", 4, 13, st.session_state.mapbiomas_map_zoom, key="zoom_mapbiomas")
        st.session_state.mapbiomas_map_zoom = zoom
        
        st.divider()
        
        # Compare Mode
        if st.checkbox("🔀 Compare Layers", value=st.session_state.split_compare_mode, key="compare_layers_mapbiomas"):
            st.session_state.split_compare_mode = True
            
            col_left, col_right = st.columns(2)
            with col_left:
                st.session_state.split_left_year = st.selectbox(
                    "Layer 1 Year",
                    range(1985, 2024),
                    index=38,
                    key="split_left"
                )
            with col_right:
                st.session_state.split_right_year = st.selectbox(
                    "Layer 2 Year",
                    range(1985, 2024),
                    index=0,
                    key="split_right"
                )
            
            # Opacity sliders
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


def render_hansen_map_controls():
    """Render map controls for Hansen"""
    with st.expander("Map Controls", expanded=False):
        st.subheader("🌍 Hansen/GLAD (Global) Layers")
        st.info("Data: Global Land Analysis and Discovery (GLAD) Lab, University of Maryland")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.slider("Latitude", -33.0, 5.0, st.session_state.hansen_map_center_lat, key="lat_hansen")
            st.session_state.hansen_map_center_lat = center_lat
        with col2:
            center_lon = st.slider("Longitude", -75.0, -35.0, st.session_state.hansen_map_center_lon, key="lon_hansen")
            st.session_state.hansen_map_center_lon = center_lon
        
        zoom = st.slider("Zoom", 4, 13, st.session_state.hansen_map_zoom, key="zoom_hansen")
        st.session_state.hansen_map_zoom = zoom
        
        st.divider()
        
        hansen_year = st.selectbox(
            "Select Year",
            ["2000", "2005", "2010", "2015", "2020", "2000-2020 Change"],
            help="Available years from Hansen dataset",
            key="hansen_year_controls"
        )
        st.session_state.hansen_year = hansen_year
        
        st.markdown("**About Hansen/GLAD Data:**")
        st.caption("- Global coverage (2000-2020)           - 30-meter resolution")
        st.caption("- Land cover & land use classification  - Learn more: [glad.umd.edu](https://glad.umd.edu/dataset/GLCLUC2020)")



def render_map_instructions():
    """Render drawing instructions"""
    st.markdown('''
    **How to Use:**
    - Click the **Rectangle tool** (top-left) to draw your analysis area
    - Select layer visibility using layer control (top-right)
    - Use **Fullscreen** button for better view
    - Your drawn area will appear in the analysis tab
    ''')


def render_load_button(col):
    """Render the Load Core Data button"""
    with col:
        if st.button("Load Core Data", key="btn_load_core_data", use_container_width=True):
            with st.spinner("Loading Earth Engine data..."):
                try:
                    from streamlit_app import init_earth_engine
                    ee, app = init_earth_engine()
                    st.session_state.app = app
                    st.session_state.data_loaded = True
                    st.session_state.ee_module = ee
                    st.success("✅ Data loaded successfully!")
                except Exception as e:
                    st.error(f"Failed to load data: {e}")


def render_about_section():
    """Render about section"""
    with st.expander("ℹ️ About Yvynation", expanded=False):
        st.markdown(
            '''
            **Yvynation** - Indigenous Land Monitoring Platform
            
            Analyze land cover change in indigenous territories and custom areas using:
            - **MapBiomas**: Detailed Brazilian land cover classification (1985-2023)
            - **Hansen/GLAD**: Global land cover snapshots (2000-2020)
            
            ### Features
            - 🗺️ Interactive map with drawing tools
            - 📊 Area analysis and statistics
            - 📈 Multi-year change detection
            - 🌍 Global and regional coverage
            
            ### Data Sources
            - MapBiomas Collection 9
            - Hansen/GLAD GLCLUC 2020
            - Google Earth Engine
            
            ### Disclaimer
            This tool is for research and monitoring purposes.
            '''
        )


def render_mapbiomas_legend():
    """Render MapBiomas land cover legend"""
    from config import MAPBIOMAS_COLOR_MAP, MAPBIOMAS_LABELS
    
    st.subheader("🎨 Land Cover Legend")
    
    # Main MapBiomas classes to display
    main_classes = [
        1, 3, 4, 5, 9, 11, 12, 15, 18, 20, 24, 26, 30, 33
    ]
    
    with st.container():
        for class_id in main_classes:
            if class_id in MAPBIOMAS_LABELS and class_id in MAPBIOMAS_COLOR_MAP:
                color = MAPBIOMAS_COLOR_MAP[class_id]
                label = MAPBIOMAS_LABELS[class_id]
                
                col_color, col_label = st.columns([0.12, 0.88])
                with col_color:
                    st.markdown(
                        f'<div style="background-color: {color}; width: 30px; height: 20px; '
                        f'border: 1px solid #999; border-radius: 2px;"></div>',
                        unsafe_allow_html=True
                    )
                with col_label:
                    st.markdown(f"<small style='word-wrap: break-word; overflow-wrap: break-word;'>{label}</small>", unsafe_allow_html=True)


def render_hansen_legend():
    """Render Hansen/GLAD land cover legend"""
    from config import HANSEN_COLOR_MAP
    
    st.subheader("🎨 Land Cover Legend")
    
    # Hansen classes and their descriptions
    hansen_classes = {
        0: "No Data",
        1: "Water",
        2: "Evergreen Needleleaf",
        3: "Evergreen Broadleaf",
        4: "Deciduous Needleleaf",
        5: "Deciduous Broadleaf",
        6: "Mixed Forest",
        7: "Closed Shrublands",
        8: "Open Shrublands",
        9: "Woody Savannas",
        10: "Savannas",
        11: "Grasslands",
        12: "Permanent Wetlands",
        13: "Croplands",
        14: "Urban & Built-up",
        15: "Cropland/Natural",
        16: "Snow & Ice",
        17: "Barren"
    }
    
    with st.container():
        for class_id, label in hansen_classes.items():
            if class_id in HANSEN_COLOR_MAP:
                color = HANSEN_COLOR_MAP[class_id]
                
                col_color, col_label = st.columns([0.12, 0.88])
                with col_color:
                    st.markdown(
                        f'<div style="background-color: {color}; width: 30px; height: 20px; '
                        f'border: 1px solid #999; border-radius: 2px;"></div>',
                        unsafe_allow_html=True
                    )
                with col_label:
                    st.markdown(f"<small style='word-wrap: break-word; overflow-wrap: break-word;'>{label}</small>", unsafe_allow_html=True)
