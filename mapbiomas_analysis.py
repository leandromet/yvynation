"""
MapBiomas Analysis Module
Handles all MapBiomas (Brazil) land cover analysis
"""

import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt
from analysis import calculate_area_by_class, clip_mapbiomas_to_geometry
from plots import plot_area_distribution, plot_area_comparison, plot_temporal_trend, create_sankey_transitions


def render_mapbiomas_area_analysis():
    """Render MapBiomas drawn area analysis section"""
    st.markdown("### Analyze Drawn Area")
    
    if not st.session_state.drawn_areas:
        st.info("👈 Draw an area on the map to begin analysis")
        return
    
    st.success(f"✅ {len(st.session_state.drawn_areas)} drawing(s) captured")
    
    # Select which drawn area to analyze
    col_select, col_delete = st.columns([3, 1])
    with col_select:
        selected_area = st.selectbox(
            "Select drawn area to analyze",
            list(st.session_state.drawn_areas.keys()),
            index=list(st.session_state.drawn_areas.keys()).index(st.session_state.selected_drawn_area) 
                if st.session_state.selected_drawn_area in st.session_state.drawn_areas else 0
        )
        st.session_state.selected_drawn_area = selected_area
    
    with col_delete:
        if st.button("🗑️ Clear All", key="clear_drawn_mapbiomas"):
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
                year = st.selectbox("Year", range(1985, 2024), index=38, key="year_drawn_mapbiomas")
            
            with col_btn:
                analyze_btn = st.button("📍 Analyze & Zoom", key="btn_drawn_mapbiomas", width="stretch")
            
            if analyze_btn:
                with st.spinner("Analyzing your drawn area..."):
                    try:
                        mapbiomas = st.session_state.app.mapbiomas_v9
                        band = f'classification_{year}'
                        
                        area_df = calculate_area_by_class(
                            mapbiomas.select(band),
                            geom,
                            year
                        )
                        
                        # Store results
                        st.session_state.drawn_area_result = area_df
                        st.session_state.drawn_area_year = year
                        st.session_state.last_analyzed_geom = geom
                        st.session_state.last_analyzed_name = "Your Drawn Area"
                        
                        st.success(f"✅ Analysis complete for {year}")
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
        
        # Display results if available
        if st.session_state.drawn_area_result is not None:
            st.markdown(f"#### 📊 Land Cover Distribution Chart (Drawn Area - {st.session_state.drawn_area_year})")
            fig = plot_area_distribution(st.session_state.drawn_area_result, 
                                        year=st.session_state.drawn_area_year, top_n=15)
            if fig:
                st.pyplot(fig, width="stretch")
            
            st.markdown("#### 📋 Detailed Statistics")
            st.dataframe(st.session_state.drawn_area_result.head(20), width="stretch")
            st.success("✅ View the drawn area on the map!")
            
    except Exception as e:
        st.error(f"Error: {e}")


def render_mapbiomas_territory_analysis():
    """Render MapBiomas territory analysis section"""
    from analysis import filter_territories_by_state, filter_territories_by_names
    from plots import plot_area_distribution
    
    st.markdown("### Analyze Indigenous Territory")
    
    col_state, col_refresh = st.columns([3, 1])
    with col_state:
        state = st.selectbox(
            "State",
            ["Amazonas", "Rondônia", "Mato Grosso", "Pará", "Bahia", "Roraima", "Maranhão"],
            key="state_select"
        )
    
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_territories_mapbiomas"):
            st.rerun()
    
    try:
        territories_fc = filter_territories_by_state(state)
        
        if territories_fc is None:
            st.error(f"No territories found in {state}")
            return
        
        territory_names = [f["properties"]["TERR_NAME"] for f in territories_fc.getInfo()["features"]]
        
        col_terr, col_year = st.columns([2, 1])
        with col_terr:
            territory_name = st.selectbox("Territory", territory_names, key="territory_select")
        with col_year:
            territory_year = st.selectbox("Year", range(1985, 2024), index=38, key="territory_year")
        
        if st.button("📍 Analyze Territory", key="btn_territory", width="stretch"):
            with st.spinner(f"Analyzing {territory_name}..."):
                try:
                    mapbiomas = st.session_state.app.mapbiomas_v9
                    territories = filter_territories_by_names([territory_name])
                    
                    if territories:
                        geom = territories.first().geometry()
                        band = f'classification_{territory_year}'
                        
                        area_df = calculate_area_by_class(
                            mapbiomas.select(band),
                            geom,
                            territory_year
                        )
                        
                        st.session_state.territory_result = area_df
                        st.session_state.territory_name = territory_name
                        st.session_state.territory_year = territory_year
                        st.session_state.last_analyzed_geom = geom
                        st.session_state.last_analyzed_name = territory_name
                        
                        st.success(f"✅ Analysis complete for {territory_name}")
                        
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        
        # Display territory results if available
        if st.session_state.territory_result is not None:
            st.markdown(f"#### 📊 Land Cover Distribution in {st.session_state.territory_name}")
            fig = plot_area_distribution(st.session_state.territory_result, 
                                        year=st.session_state.territory_year, top_n=15)
            if fig:
                st.pyplot(fig, width="stretch")
            
            st.markdown("#### 📋 Detailed Statistics")
            st.dataframe(st.session_state.territory_result.head(20), width="stretch")
            st.success(f"✅ View {st.session_state.territory_name} on the map!")
            
    except Exception as e:
        st.error(f"Error loading territories: {e}")


def render_mapbiomas_multiyear_analysis():
    """Render MapBiomas multi-year territory analysis section"""
    st.markdown("### Multi-Year Territory Analysis")
    
    if "app" not in st.session_state or st.session_state.app is None:
        st.info("Load data first to enable multi-year analysis")
        return
    
    if st.session_state.last_analyzed_geom is None:
        st.info("👈 First, analyze a drawn area or select a territory above")
        return
    
    st.info(f"📍 Analyzing: **{st.session_state.last_analyzed_name}**")
    
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.slider("Start Year", 1985, 2023, 1985, key="start_year_current")
    with col2:
        end_year = st.slider("End Year", 1985, 2023, 2023, key="end_year_current")
    
    if st.button("Analyze Multi-Year Changes", width="stretch", key="btn_multiyear_mapbiomas"):
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
                
                # Store results
                st.session_state.multiyear_results = {
                    "area_start": area_start,
                    "area_end": area_end
                }
                st.session_state.multiyear_start_year = start_year
                st.session_state.multiyear_end_year = end_year
                
                st.success(f"✅ Analysis complete for {start_year}-{end_year}")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    
    # Display results if available
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


def render_mapbiomas_change_analysis():
    """Render MapBiomas change detection section"""
    st.markdown("### Change Between Years")
    
    if st.session_state.multiyear_results is None:
        st.info("Run analysis in the 'Multi-Year Territory Analysis' section first")
        return
    
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
        
        # Change visualization
        try:
            fig2 = plot_temporal_trend(
                [results["area_start"], results["area_end"]],
                [st.session_state.multiyear_start_year, st.session_state.multiyear_end_year]
            )
            st.pyplot(fig2)
        except Exception as e:
            st.warning(f"Visualization issue: {e}")
    else:
        st.warning("Results format not recognized")
