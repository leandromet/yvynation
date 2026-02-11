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
from buffer_utils import add_buffer_to_session_state, add_buffer_to_polygon_list
from translations import t


def render_sidebar_header():
    """Render the sidebar title and description."""
    st.sidebar.markdown(f"### {t('app_title')}")
    st.sidebar.caption(f"{t('app_subtitle')} · {t('author')}")


def render_language_selection():
    """Render language selection controls."""
    st.sidebar.markdown("**" + t("language") + "**")
    
    # Initialize language if not present
    if "language" not in st.session_state:
        st.session_state.language = "en"
    
    # Use render ID to make keys unique across multiple renders
    render_id = st.session_state.get('_current_render_id', '')
    
    # Language selection
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🇬🇧 EN",
                    use_container_width=True,
                    key=f"lang_en_{render_id}",
                    type="primary" if st.session_state.language == "en" else "secondary"):
            st.session_state.language = "en"
            st.rerun()
    
    with col2:
        if st.button("🇧🇷 PT",
                    use_container_width=True,
                    key=f"lang_pt_{render_id}",
                    type="primary" if st.session_state.language == "pt-br" else "secondary"):
            st.session_state.language = "pt-br"
            st.rerun()


def render_country_selection():
    """Render country selection controls."""
    st.sidebar.markdown("**" + t("select_region") + "**")
    
    # Initialize country selection if not present
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = "Brazil"
    
    # Use render ID to make keys unique across multiple renders
    render_id = st.session_state.get('_current_render_id', '')
    
    # Country selection with flags
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🇧🇷 BR",
                    use_container_width=True,
                    key=f"region_br_{render_id}",
                    type="primary" if st.session_state.selected_country == "Brazil" else "secondary"):
            st.session_state.selected_country = "Brazil"
            st.rerun()
    
    with col2:
        if st.button("🇨🇦 CA",
                    use_container_width=True,
                    key=f"region_ca_{render_id}",
                    type="primary" if st.session_state.selected_country == "Canada" else "secondary"):
            st.session_state.selected_country = "Canada"
            st.rerun()


def render_map_controls():
    """Render map controls help section."""
    with st.sidebar.expander("🗺️ " + t("map_controls"), expanded=False):
        st.caption(f"**{t('layer_control')}:** {t('layer_control_hint')}")
        st.caption(f"**{t('basemaps_section')}:** {t('basemaps_info')}")
        st.caption(f"💡 {t('overlay_tip')}")


def render_layer_selection():
    """Render map layer selection controls (MapBiomas and Hansen)."""
    if st.session_state.data_loaded:
        st.sidebar.markdown("**🗺️ " + t("add_layer_to_analyze").split("{")[0].strip() + "**")
        
        # Use render ID to make keys unique across multiple renders
        render_id = st.session_state.get('_current_render_id', '')
        
        # MapBiomas section - Only show for Brazil
        if st.session_state.selected_country == "Brazil":
            with st.sidebar.expander(t("mapbiomas_layer"), expanded=False):
                st.write(t("year") + ":")
                mapbiomas_year = st.select_slider(
                    t("year"),
                    options=list(range(1985, 2024)),
                    value=st.session_state.current_mapbiomas_year,
                    key="mb_year_slider"
                )
                if st.button(t("add_layer"), width="stretch", key=f"add_mapbiomas_{render_id}"):
                    st.session_state.mapbiomas_layers[mapbiomas_year] = True
                    st.session_state.current_mapbiomas_year = mapbiomas_year
                    st.success(f"✓ {t('mapbiomas_layer')} {mapbiomas_year}")
        else:
            st.info(f"🇧🇷 {t('mapbiomas_layer')} " + t("territory_info").split("Select")[0].strip() + " " + t("brazil"), icon="ℹ️")
        
         # AAFC Annual Crop Inventory section - Only show for Canada
        if st.session_state.selected_country == "Canada":
            with st.sidebar.expander(t("aafc_layer"), expanded=False):
                st.write(t("analyze_territory") + ":")
                st.caption(t("aafc_subtitle"))
                
                aafc_years = list(range(2009, 2025))
                aafc_year = st.select_slider(
                    t("year"),
                    options=aafc_years,
                    value=st.session_state.get('current_aafc_year', 2023),
                    key="aafc_year_slider"
                )
                if st.button(t("add_layer"), width="stretch", key=f"add_aafc_{render_id}"):
                    st.session_state.aafc_layers[aafc_year] = True
                    st.session_state.current_aafc_year = aafc_year
                    st.success(f"✓ {t('aafc_layer')} {aafc_year}")
                
                st.info(t("aafc_info"), icon="ℹ️")
        else:
            if st.session_state.selected_country == "Brazil":
                st.info(f"🚜 {t('aafc_layer')} " + t("territory_info").split("Select")[0].strip() + " " + t("canada"), icon="ℹ️")

        # Hansen section
        with st.sidebar.expander(t("hansen_layer"), expanded=False):
            st.write("Select a year:")
            hansen_years = ["2000", "2005", "2010", "2015", "2020"]
            hansen_year = st.selectbox(
                t("year"),
                options=hansen_years,
                index=hansen_years.index(st.session_state.current_hansen_year),
                key="hansen_year_select"
            )
            if st.button(t("add_layer"), width="stretch", key=f"add_hansen_{render_id}"):
                st.session_state.hansen_layers[hansen_year] = True
                st.session_state.current_hansen_year = hansen_year
                st.success(f"✓ {t('hansen_layer')} {hansen_year}")
        
        # Hansen Global Forest Change section
        with st.sidebar.expander(t("hansen_gfc_layer"), expanded=False):
            st.write(t("tree_gain_desc") + ":")
            st.caption(t("gfc_info"))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(t("tree_cover"), key=f"add_hansen_gfc_cover_{render_id}", use_container_width=True):
                    st.session_state.hansen_gfc_tree_cover = True
                    st.success(f"✓ {t('tree_cover')}")
                    
                if st.button(t("tree_gain"), key=f"add_hansen_gfc_gain_{render_id}", use_container_width=True):
                    st.session_state.hansen_gfc_tree_gain = True
                    st.success(f"✓ {t('tree_gain')}")
            
            with col2:
                if st.button(t("tree_loss"), key=f"add_hansen_gfc_loss_{render_id}", use_container_width=True):
                    st.session_state.hansen_gfc_tree_loss = True
                    st.success(f"✓ {t('tree_loss')}")
            
            st.info(t("tree_loss_desc"), icon="ℹ️")


def render_territory_analysis():
    """Render territory analysis controls."""
    if st.session_state.data_loaded:
        # Use render ID to make keys unique across multiple renders
        render_id = st.session_state.get('_current_render_id', '')
        
        with st.sidebar.expander(t("territory_analysis_title"), expanded=False):
            st.write(t("analyze_territory_intro"))
            
            try:
                territories_fc = st.session_state.app.territories
                if territories_fc is None:
                    st.error(t("territories_not_loaded"))
                else:
                    # Get territory names from Earth Engine
                    territory_names, name_prop = get_territory_names(territories_fc)
                    
                    if not territory_names or not name_prop:
                        st.error(t("territory_names_error"))
                    else:
                        selected_territory = st.selectbox(
                            t("select_a_territory"),
                            territory_names,
                            key="territory_select"
                        )
                        
                        # Data source selection
                        data_source = st.radio(
                            t("data_source_label"),
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
                                    t("year_1"),
                                    range(1985, 2024),
                                    index=38,
                                    key="year_territory_1"
                                )
                            else:
                                hansen_years = ["2000", "2005", "2010", "2015", "2020"]
                                territory_year = st.selectbox(
                                    t("year_1"),
                                    hansen_years,
                                    index=4,
                                    key="year_territory_h1"
                                )
                        
                        with col2:
                            compare_mode = st.checkbox(t("compare_years_label"), value=False, key="territory_compare")
                            if compare_mode:
                                if data_source == "MapBiomas":
                                    territory_year2 = st.selectbox(
                                        t("year_2"),
                                        range(1985, 2024),
                                        index=30,
                                        key="year_territory_2"
                                    )
                                else:
                                    hansen_years = ["2000", "2005", "2010", "2015", "2020"]
                                    territory_year2 = st.selectbox(
                                        t("year_2"),
                                        hansen_years,
                                        index=0,
                                        key="year_territory_h2"
                                    )
                            else:
                                territory_year2 = None
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            analyze_btn = st.button(t("btn_analyze"), key=f"btn_analyze_territory_{render_id}", width="stretch")
                        with col_btn2:
                            add_layer_btn = st.button(t("btn_zoom_territory"), key=f"btn_add_territory_layer_{render_id}", width="stretch")
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
                                    
                                    st.success(t("territory_added", territory=selected_territory))
                                
                                except Exception as e:
                                    st.error(t("territory_add_failed", error=str(e)))
                                    traceback.print_exc()
                            
                        if analyze_btn:
                                with st.spinner(t("analyzing_territory", territory=selected_territory)):
                                    try:
                                        # Save compare mode and year2 to session state for use in buffer analysis
                                        st.session_state.territory_compare_mode = compare_mode
                                        st.session_state.territory_year2_for_analysis = territory_year2 if compare_mode else None
                                        
                                        # Get territory geometry
                                        territory_geom = get_territory_geometry(territories_fc, selected_territory, name_prop)
                                        if not territory_geom:
                                            st.error(t("territory_geometry_error"))
                                        else:
                                            # Store geometry with distinct key for analysis
                                            st.session_state.territory_geom = territory_geom
                                            st.session_state.territory_geometry_for_analysis = territory_geom
                                            st.session_state.territory_name = selected_territory
                                            st.session_state.territory_source = data_source
                                            st.session_state.add_analysis_layer_to_map = False
                                            st.session_state.add_territory_layer_to_map = True
                                            st.session_state.territory_layer_name = selected_territory
                                            
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
                                            st.success(t("analysis_complete", territory=selected_territory))
                                    
                                    except Exception as e:
                                        st.error(t("analysis_failed", error=str(e)))
                                        traceback.print_exc()

                    # Add buffer zone option
                    with st.sidebar.expander(t("buffer_zone_title"), expanded=False):
                            st.markdown(f"**{t('buffer_zone_desc')}**")
                            st.caption(t("buffer_zone_hint"))
                            
                            # Buffer compare mode toggle
                            buffer_compare = st.checkbox(
                                t("compare_buffer"),
                                value=st.session_state.buffer_compare_mode,
                                help=t("compare_buffer_help"),
                                key="territory_buffer_compare_toggle"
                            )
                            st.session_state.buffer_compare_mode = buffer_compare
                            
                            col_dist, col_create = st.columns([2, 1])
                            with col_dist:
                                buffer_distance = st.selectbox(
                                    t("buffer_distance_label"),
                                    options=[1, 2, 5, 10],
                                    format_func=lambda x: t("km_format", distance=x),
                                    key="territory_buffer_distance"
                                )
                            with col_create:
                                create_buffer_btn = st.button(t("btn_create_buffer"), key=f"btn_create_territory_buffer_{render_id}", width="stretch")
                            
                            if create_buffer_btn:
                                try:
                                    # Get territory geometry
                                    territory_geom = territories_fc.filter(
                                        ee.Filter.eq(name_prop, selected_territory)
                                    ).first().geometry()
                                    
                                    # Create and store the buffer
                                    buffer_name = add_buffer_to_session_state(
                                        territory_geom,
                                        buffer_distance,
                                        selected_territory
                                    )
                                    
                                    # Add to polygon list
                                    add_buffer_to_polygon_list(buffer_name)
                                    
                                    # If compare mode, set this buffer for comparison
                                    if st.session_state.buffer_compare_mode:
                                        st.session_state.current_buffer_for_analysis = buffer_name
                                        st.success(t("buffer_created", distance=buffer_distance))
                                        st.info(t("buffer_compare_info"), icon="📊")
                                    else:
                                        st.session_state.current_buffer_for_analysis = buffer_name
                                        st.success(t("buffer_created_compare", distance=buffer_distance, territory=selected_territory))
                                        st.info(t("buffer_analyze_info"), icon="🔽")
                                    
                                except Exception as e:
                                    st.error(t("buffer_create_failed", error=str(e)))
                                    traceback.print_exc()
                            
                            # Show Analyze Buffer button if buffer exists
                            if st.session_state.current_buffer_for_analysis and st.session_state.current_buffer_for_analysis in st.session_state.buffer_geometries:
                                st.markdown(f"**{t('buffer_zone_analysis')}**")
                                buffer_meta = st.session_state.buffer_metadata[st.session_state.current_buffer_for_analysis]
                                st.caption(t("buffer_analysis_hint", distance=buffer_meta['buffer_size_km'], territory=buffer_meta['source_name']))
                                
                                col_buffer_analyze, col_buffer_zoom = st.columns(2)
                                with col_buffer_analyze:
                                    analyze_buffer_btn = st.button(t("btn_analyze_buffer"), key=f"btn_analyze_territory_buffer_{unique_suffix}", width="stretch")
                                with col_buffer_zoom:
                                    zoom_buffer_btn = st.button(t("btn_zoom_buffer"), key=f"btn_zoom_territory_buffer_{unique_suffix}", width="stretch")
                                
                                if zoom_buffer_btn:
                                    try:
                                        # Get buffer geometry
                                        buffer_name = st.session_state.current_buffer_for_analysis
                                        buffer_geom = st.session_state.buffer_geometries[buffer_name]
                                        
                                        # Store geometry and flag for map display
                                        st.session_state.buffer_geom_for_display = buffer_geom
                                        st.session_state.add_buffer_layer_to_map = True
                                        st.session_state.buffer_layer_name = buffer_name
                                        
                                        st.success(t("buffer_added", distance=buffer_meta['buffer_size_km']))
                                    
                                    except Exception as e:
                                        st.error(t("buffer_added_error", error=str(e)))
                                        traceback.print_exc()
                                
                                if analyze_buffer_btn:
                                    with st.spinner(t("buffer_analyzing")):
                                        try:
                                            # Get buffer geometry and metadata
                                            buffer_name = st.session_state.current_buffer_for_analysis
                                            buffer_geom = st.session_state.buffer_geometries[buffer_name]
                                            buffer_meta = st.session_state.buffer_metadata[buffer_name]
                                            
                                            print(f"DEBUG: Buffer analysis - name={buffer_name}, geom_type={type(buffer_geom)}")
                                            
                                            # Store buffer info (keep territory_geom separate for reference)
                                            # Don't overwrite territory_geom - keep original territory reference
                                            st.session_state.territory_geometry_for_analysis = buffer_geom
                                            st.session_state.territory_name = f"{buffer_meta['source_name']} Buffer ({buffer_meta['buffer_size_km']}km)"
                                            st.session_state.territory_source = data_source
                                            
                                            if data_source == "MapBiomas":
                                                # Analyze MapBiomas for buffer
                                                mapbiomas = st.session_state.app.mapbiomas_v9
                                                print(f"DEBUG: mapbiomas type = {type(mapbiomas)}, buffer_geom type = {type(buffer_geom)}")
                                                band = f'classification_{territory_year}'
                                                area_df = analyze_territory_mapbiomas(mapbiomas, buffer_geom, territory_year)
                                                
                                                # Store buffer results in dedicated session state variables
                                                st.session_state.buffer_result_mapbiomas = area_df
                                                st.session_state.buffer_result_mapbiomas_y2 = None
                                                
                                                # Check if we need a second year analysis
                                                # Get compare mode and year from session state since local variables may not be in scope
                                                territory_compare_from_state = st.session_state.get('territory_compare_mode', False)
                                                territory_year2_from_state = st.session_state.get('territory_year2_for_analysis', None)
                                                
                                                if territory_compare_from_state and territory_year2_from_state:
                                                    band2 = f'classification_{territory_year2_from_state}'
                                                    area_df2 = analyze_territory_mapbiomas(mapbiomas, buffer_geom, territory_year2_from_state)
                                                    st.session_state.buffer_result_mapbiomas_y2 = area_df2
                                            
                                            else:  # Hansen
                                                # Analyze Hansen for buffer
                                                area_df, hansen_image = analyze_territory_hansen(
                                                    st.session_state.ee_module,
                                                    buffer_geom,
                                                    territory_year,
                                                    st.session_state.use_consolidated_classes
                                                )
                                                
                                                # Store buffer results in dedicated session state variables
                                                st.session_state.buffer_result_hansen = area_df
                                                st.session_state.buffer_result_hansen_y2 = None
                                                
                                                # Check if we need a second year analysis
                                                territory_compare_from_state = st.session_state.get('territory_compare_mode', False)
                                                territory_year2_from_state = st.session_state.get('territory_year2_for_analysis', None)
                                                
                                                if territory_compare_from_state and territory_year2_from_state:
                                                    area_df2, hansen_image2 = analyze_territory_hansen(
                                                        st.session_state.ee_module,
                                                        buffer_geom,
                                                        territory_year2_from_state,
                                                        st.session_state.use_consolidated_classes
                                                    )
                                                    st.session_state.buffer_result_hansen_y2 = area_df2
                                            
                                            st.success(t("buffer_analysis_complete"))
                                            st.info(t("buffer_analysis_info"), icon="📊")
                                        
                                        except Exception as e:
                                            st.error(t("buffer_analysis_failed", error=str(e)))
                                            import traceback
                                            st.error(f"Full error: {traceback.format_exc()}")
                                            traceback.print_exc()
                            
                           
            
            except Exception as e:
                st.error(t("territory_error", error=str(e)))


def render_view_options():
    """Render view options (consolidated classes toggle)."""
    with st.sidebar.expander(t("view_options"), expanded=False):
        use_consolidated = st.checkbox(
            t("show_consolidated"),
            value=st.session_state.use_consolidated_classes,
            help=t("consolidated_help")
        )
        st.session_state.use_consolidated_classes = use_consolidated
        
        if use_consolidated:
            st.caption(t("consolidated_view"))
        else:
            st.caption(t("detailed_view"))


def render_about_section():
    """Render the about/info section."""
    with st.sidebar.expander(t("about_title"), expanded=False):
        st.sidebar.markdown(f"""
        ### {t("about_overview")}

        {t("about_desc")}

        **{t("about_author")}** - {t("about_role")} - {t("about_university")}
        {t("about_supervisor")}

        **{t("about_app_name")}** {t("about_app_note")}

        {t("yvynation_meaning")}

        {t("nation_meaning")}

        ### {t("data_sources_title")}
        - **{t("mapbiomas_title")}**
          - {t("mapbiomas_resolution")}
          - {t("mapbiomas_period")}
          - {t("mapbiomas_classes")}
          - {t("mapbiomas_license")}

        - **{t("territories_title")}**
          - {t("territories_desc")}

        ### {t("features_title")}

        ✅ {t("feature_mapping")}  
        ✅ {t("feature_calculation")}  
        ✅ {t("feature_filtering")}  
        ✅ {t("feature_visualization")}  
        ✅ {t("feature_export")}

        ### {t("tech_title")}

        - {t("tech_python")}
        - {t("tech_gee")}
        - {t("tech_geemap")}
        - {t("tech_streamlit")}
        - {t("tech_science")}
        """)


def render_complete_sidebar():
    """Render the entire sidebar with all components."""
    render_sidebar_header()
    render_language_selection()
    render_country_selection()
    render_map_controls()
    render_layer_selection()
    st.sidebar.divider()
    render_territory_analysis()
    render_view_options()
    st.sidebar.divider()
    render_about_section()
