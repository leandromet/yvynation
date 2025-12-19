"""
MapBiomas Analysis Module
Handles all MapBiomas (Brazil) land cover analysis
"""

import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt


# Helper function for area analysis
def calculate_area_by_class(image, geometry, year):
    """Calculate area by land cover class"""
    try:
        stats = image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        if stats and 'b1' in stats:
            data = stats['b1']
            from config import MAPBIOMAS_LABELS
            
            records = []
            for class_id, count in data.items():
                class_id = int(class_id)
                class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                records.append({
                    "Class_ID": class_id,
                    "Class": class_name,
                    "Pixels": count,
                    "Area_ha": count * 0.09  # 30m pixels ≈ 0.09 ha
                })
            return pd.DataFrame(records).sort_values("Area_ha", ascending=False)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error calculating area: {e}")
        return pd.DataFrame()


# Helper function for plotting
def plot_area_distribution(df, year=None, top_n=15):
    """Plot land cover area distribution"""
    try:
        from config import MAPBIOMAS_COLOR_MAP
        
        top_df = df.head(top_n)
        colors = [MAPBIOMAS_COLOR_MAP.get(class_id, "#808080") for class_id in top_df['Class_ID']]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(top_df['Class'], top_df['Area_ha'], color=colors)
        ax.set_xlabel('Area (hectares)')
        ax.set_ylabel('Land Cover Class')
        if year:
            ax.set_title(f'Land Cover Distribution ({year})')
        ax.invert_yaxis()
        plt.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Error plotting: {e}")
        return None


def plot_area_comparison(df_start, df_end, year_start=None, year_end=None):
    """Plot comparison of two years"""
    try:
        from config import MAPBIOMAS_COLOR_MAP
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        top_start = df_start.head(10)
        colors_start = [MAPBIOMAS_COLOR_MAP.get(class_id, "#808080") for class_id in top_start['Class_ID']]
        ax1.barh(top_start["Class"], top_start["Area_ha"], color=colors_start)
        ax1.set_xlabel("Area (hectares)")
        ax1.set_title(f"{year_start}")
        ax1.invert_yaxis()
        
        top_end = df_end.head(10)
        colors_end = [MAPBIOMAS_COLOR_MAP.get(class_id, "#808080") for class_id in top_end['Class_ID']]
        ax2.barh(top_end["Class"], top_end["Area_ha"], color=colors_end)
        ax2.set_xlabel("Area (hectares)")
        ax2.set_title(f"{year_end}")
        ax2.invert_yaxis()
        
        plt.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Error plotting comparison: {e}")
        return None


def plot_temporal_trend(df, years=None):
    """Plot temporal trend"""
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        if df is not None and not df.empty:
            ax.plot(range(len(df)), df.values)
            ax.set_xlabel('Year')
            ax.set_ylabel('Area (hectares)')
            ax.set_title('Land Cover Temporal Trend')
            plt.tight_layout()
        return fig
    except Exception as e:
        st.error(f"Error plotting trend: {e}")
        return None


def render_mapbiomas_area_analysis():
    """Render MapBiomas drawn area analysis section"""
    
    if not st.session_state.mapbiomas_drawn_areas:
        st.info("👈 Draw an area on the map to begin analysis")
        return
    
    st.success(f"✅ {len(st.session_state.mapbiomas_drawn_areas)} drawing(s) captured")
    
    # Ensure selected area exists
    area_keys = list(st.session_state.mapbiomas_drawn_areas.keys())
    if st.session_state.mapbiomas_selected_drawn_area not in area_keys:
        st.session_state.mapbiomas_selected_drawn_area = area_keys[0]
    
    # Select which drawn area to analyze
    col_select, col_delete = st.columns([3, 1])
    with col_select:
        selected_area = st.selectbox(
            "Select drawn area to analyze",
            area_keys,
            index=area_keys.index(st.session_state.mapbiomas_selected_drawn_area),
            key="mapbiomas_area_select",
            on_change=lambda: st.session_state.update({"mapbiomas_selected_drawn_area": st.session_state.mapbiomas_area_select})
        )
    
    with col_delete:
        if st.button("🗑️ Clear All", key="clear_drawn_mapbiomas"):
            st.session_state.mapbiomas_drawn_areas = {}
            st.session_state.mapbiomas_drawn_area_count = 0
            st.session_state.mapbiomas_selected_drawn_area = None
            st.rerun()
    
    try:
        geom_data = st.session_state.mapbiomas_drawn_areas[st.session_state.mapbiomas_selected_drawn_area]
        coords = geom_data.get('coordinates', [])
        
        if coords:
            # Create EE geometry from polygon
            geom = ee.Geometry.Polygon(coords[0] if isinstance(coords[0][0], list) else coords)
            
            col_year, col_btn = st.columns([2, 1])
            with col_year:
                year = st.selectbox("Year", range(1985, 2024), index=38, key="year_mapbiomas_drawn")
            
            with col_btn:
                analyze_btn = st.button("📍 Analyze & Zoom", key="btn_mapbiomas_drawn", width="stretch")
            
            if analyze_btn and st.session_state.mapbiomas_selected_drawn_area:
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
                        
                        # Store the polygon coordinates for drawing on map
                        st.session_state.mapbiomas_drawn_polygon_coords = coords
                        
                        # Calculate bounds and set zoom flag
                        bounds = geom.bounds().getInfo()
                        st.session_state.mapbiomas_zoom_bounds = bounds
                        st.session_state.mapbiomas_should_zoom_to_feature = True
                        
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


def filter_territories_by_names(territories, names):
    """Filter territories by name"""
    if not names:
        return territories
    try:
        return territories.filterMetadata('territory_name', 'in_list', names)
    except:
        return territories


def render_mapbiomas_territory_analysis():
    """Render MapBiomas territory analysis section"""
    
    col_search, col_refresh = st.columns([3, 1])
    with col_search:
        st.caption("Search and select a territory from all available indigenous territories")
    
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_territories_mapbiomas"):
            st.rerun()
    
    try:
        territories = st.session_state.app.territories
        if territories is None:
            st.error("Territories not loaded. Please click 'Load Core Data' first.")
            return
        
        # Get all territories (no state filtering since uf_sigla is empty)
        territories_fc = territories
        
        # Get features to extract territory names
        features = territories_fc.getInfo()["features"]
        if not features:
            st.error("No territory features found")
            return
        
        # Detect the correct property name for territory names
        first_props = features[0]["properties"]
        name_prop = None
        for prop in ['NAME', 'name', 'TERR_NAME', 'territorio_nome', 'territory_name', 'TERRITORY_NAME', 'NOME']:
            if prop in first_props:
                name_prop = prop
                break
        
        if name_prop is None:
            st.error(f"Could not find territory name property. Available: {list(first_props.keys())}")
            return
        
        # Extract and clean territory names (remove outer brackets like "[Name (ID)]" -> "Name (ID)")
        territory_names_raw = [f["properties"][name_prop] for f in features]
        territory_names = []
        clean_to_raw = {}  # Map clean names back to raw names for filtering
        for name in territory_names_raw:
            # Clean format: [Name (ID)] -> Name (ID)
            clean_name = name.strip('[]') if '[' in name else name
            if clean_name not in clean_to_raw:  # Keep first occurrence
                clean_to_raw[clean_name] = name
            territory_names.append(clean_name)
        
        territory_names = sorted(list(set(territory_names)))  # Remove duplicates and sort
        
        col_terr, col_year = st.columns([2, 1])
        with col_terr:
            territory_name = st.selectbox(
                f"Territory ({len(territory_names)} available)",
                territory_names,
                key="territory_select"
            )
        with col_year:
            territory_year = st.selectbox("Year", range(1985, 2024), index=38, key="territory_year")
        
        if st.button("📍 Analyze Territory", key="btn_territory", width="stretch"):
            with st.spinner(f"Analyzing {territory_name}..."):
                try:
                    mapbiomas = st.session_state.app.mapbiomas_v9
                    territories_app = st.session_state.app.territories
                    # Use the raw name from the mapping for filtering
                    raw_name = clean_to_raw.get(territory_name, territory_name)
                    filtered_territories = filter_territories_by_names(territories_app, [raw_name], name_prop)
                    
                    if filtered_territories:
                        geom = filtered_territories.first().geometry()
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
