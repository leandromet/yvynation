'''
Yvynation - Indigenous Land Monitoring Platform
Interactive analysis tool for land cover changes in indigenous territories
'''

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Yvynation - Earth Engine Analysis",
    page_icon="🏞️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Standard imports
import ee
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
import pandas as pd

# Import core configuration and modules
from config import (
    PROJECT_ID, MAPBIOMAS_LABELS, MAPBIOMAS_COLOR_MAP, 
    HANSEN_CONSOLIDATED_MAPPING, HANSEN_CONSOLIDATED_COLORS, 
    HANSEN_DATASETS, HANSEN_OCEAN_MASK
)

# Import utility modules
from ee_auth import initialize_earth_engine
from app_file import YvynationApp
from mapbiomas_analysis import calculate_area_by_class as mapbiomas_area_analysis
from hansen_analysis import hansen_histogram_to_dataframe
from hansen_consolidated_utils import (
    get_consolidated_class,
    get_consolidated_color,
    aggregate_to_consolidated,
    create_comparison_dataframe,
    summarize_consolidated_stats,
    HANSEN_CONSOLIDATED_MAPPING
)

# Import mapping and visualization modules
from map_manager import create_base_map, add_territories_layer
from export_utils import generate_export_button
from ee_layers import add_mapbiomas_layer, add_hansen_layer
from plotting_utils import (
    plot_area_distribution,
    plot_area_comparison,
    get_hansen_color,
    display_summary_metrics
)

# Import analysis modules
from territory_analysis import (
    get_territory_names,
    get_territory_geometry,
    analyze_territory_mapbiomas,
    analyze_territory_hansen,
    initialize_territory_session_state
)
from main import create_sankey_transitions, plot_gains_losses, plot_area_changes, plot_change_percentage

# Import modular components
from components import (
    initialize_earth_engine_and_data,
    render_sidebar,
    render_tutorial,
    render_main_content,
)
from components.main_content import render_layer_metrics, render_footer

# Import refactored sidebar and map components
from sidebar_components import render_complete_sidebar
from map_components import (
    build_and_display_map,
    process_drawn_features,
    render_polygon_selector,
    render_layer_reference_guide
)
from map_pdf_export import render_map_export_section

# ============================================================================
# HELPER FUNCTIONS FOR BUFFER COMPARISON
# ============================================================================

def analyze_mapbiomas_geometry(geometry, year, area_name="Area"):
    """
    Analyze MapBiomas data for a given geometry and year.
    
    Returns:
        pd.DataFrame: Analysis results or None if error
    """
    try:
        band = f'classification_{year}'
        image = st.session_state.app.mapbiomas_v9.select(band)
        
        with st.spinner(f"Analyzing {area_name} for {year}..."):
            stats = image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
        
        if stats:
            from config import MAPBIOMAS_LABELS
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
                return df
    except Exception as e:
        st.error(f"Error analyzing {area_name}: {str(e)[:200]}")
        print(f"Full error: {e}")
    return None


def analyze_hansen_geometry(geometry, year, area_name="Area"):
    """
    Analyze Hansen data for a given geometry and year.
    
    Returns:
        pd.DataFrame: Analysis results or None if error
    """
    try:
        from config import HANSEN_DATASETS, HANSEN_OCEAN_MASK
        landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
        hansen_image = ee.Image(HANSEN_DATASETS[str(year)]).updateMask(landmask)
        
        with st.spinner(f"Analyzing {area_name} for {year}..."):
            stats = hansen_image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
        
        if stats:
            df = hansen_histogram_to_dataframe(stats, year)
            if not df.empty:
                return df
    except Exception as e:
        st.error(f"Error analyzing {area_name}: {e}")
    return None


def render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, area_prefix="original", buffer_name=None, buffer_size=None):
    """
    Render the complete analysis tab structure for a given geometry.
    Can be used for both original area and buffer zone.
    
    Parameters:
    -----------
    geometry : ee.Geometry
        The geometry to analyze
    tab1, tab2, tab3, tab4 : streamlit tabs
        The tab objects to render into
    area_prefix : str
        Prefix for file exports ("original" or "buffer")
    buffer_name : str, optional
        Name of buffer for storage
    buffer_size : int, optional
        Buffer size in km for display
    """
    
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
                                    st.dataframe(df[['Class', 'Pixels', 'Area_ha']], width="stretch")
                                    
                                    # Show plot
                                    fig = plot_area_distribution(df, year=year, top_n=15)
                                    st.pyplot(fig, width="stretch")
                                    st.success(f"✓ {year}: {len(records)} classes found")
                                    
                                    # Store results for export
                                    if buffer_name:
                                        if 'buffer_analysis_results' not in st.session_state:
                                            st.session_state.buffer_analysis_results = {}
                                        if buffer_name not in st.session_state.buffer_analysis_results:
                                            st.session_state.buffer_analysis_results[buffer_name] = {}
                                        st.session_state.buffer_analysis_results[buffer_name][f'mapbiomas_{year}'] = df
                                    
                                    # Download CSV with prefix
                                    csv = df.to_csv(index=False)
                                    filename = f"{area_prefix}_mapbiomas_{year}.csv"
                                    st.download_button(
                                        label=f"📥 Download CSV ({year})",
                                        data=csv,
                                        file_name=filename,
                                        mime="text/csv",
                                        key=f"dl_{area_prefix}_mb_{year}_{id(geometry)}"
                                    )
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
                                        display_cols = ['Consolidated_Class', 'Pixels', 'Area_ha']
                                    elif 'Class' in df_display.columns:
                                        display_cols = ['Class', 'Pixels', 'Area_ha']
                                    else:
                                        display_cols = [col for col in df_display.columns if col in ['Pixels', 'Area_ha']]
                                    
                                    # Only show columns that exist
                                    display_cols = [col for col in display_cols if col in df_display.columns]
                                    if display_cols:
                                        st.dataframe(df_display[display_cols], width="stretch")
                                    else:
                                        st.dataframe(df_display, width="stretch")
                                    
                                    # Show plot with consolidation
                                    fig = plot_area_distribution(df_display, year=year, top_n=15)
                                    st.pyplot(fig, width="stretch")
                                    
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
                                    
                                    # Store results for export
                                    if buffer_name:
                                        if buffer_name not in st.session_state.buffer_analysis_results:
                                            st.session_state.buffer_analysis_results[buffer_name] = {}
                                        st.session_state.buffer_analysis_results[buffer_name][f'hansen_{year}'] = df
                                    
                                    # Download CSV with prefix
                                    csv = df.to_csv(index=False)
                                    filename = f"{area_prefix}_hansen_{year}.csv"
                                    st.download_button(
                                        label=f"📥 Download CSV ({year})",
                                        data=csv,
                                        file_name=filename,
                                        mime="text/csv",
                                        key=f"dl_{area_prefix}_hansen_{year}_{id(geometry)}"
                                    )
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
                            
                            if st.button("🔄 Compare MapBiomas Years", width="stretch", key="mapbiomas_compare"):
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
                                            
                                            # Create dataframes for each year
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
                                            
                                            # Compute transitions for Sankey
                                            transitions = {}
                                            band1 = f'classification_{year1}'
                                            band2 = f'classification_{year2}'
                                            try:
                                                combined = st.session_state.app.mapbiomas_v9.select(band1).multiply(1000).add(
                                                    st.session_state.app.mapbiomas_v9.select(band2)
                                                )
                                                transition_hist = combined.reduceRegion(
                                                    reducer=ee.Reducer.frequencyHistogram(),
                                                    geometry=geometry,
                                                    scale=30,
                                                    maxPixels=1e9
                                                ).getInfo()
                                                
                                                if transition_hist:
                                                    trans_key = list(transition_hist.keys())[0] if transition_hist else None
                                                    if trans_key and transition_hist[trans_key]:
                                                        for combined_val_str, count in transition_hist[trans_key].items():
                                                            combined_val = int(combined_val_str)
                                                            source_class = combined_val // 1000
                                                            target_class = combined_val % 1000
                                                            area_ha = count * 0.09
                                                            if source_class > 0 and target_class > 0 and area_ha > 0:
                                                                if source_class not in transitions:
                                                                    transitions[source_class] = {}
                                                                transitions[source_class][target_class] = area_ha
                                            except:
                                                pass
                                            
                                            # Store comparison results in session state
                                            st.session_state.mapbiomas_comparison_result = {
                                                'year1': year1,
                                                'year2': year2,
                                                'df': df,
                                                'df_year1': df_year1,
                                                'df_year2': df_year2,
                                                'hist1': hist1,
                                                'hist2': hist2,
                                                'all_classes': all_classes,
                                                'geometry': geometry,
                                                'transitions': transitions
                                            }
                                            
                                            st.success(f"✓ MapBiomas Comparison ({year1} vs {year2}) completed")
                                        else:
                                            st.error("Could not retrieve data for one or both years")
                                except Exception as e:
                                    st.error(f"MapBiomas Comparison error: {e}")
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
                            
                            if st.button("🔄 Compare Hansen Years", width="stretch", key="hansen_compare"):
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
                                                
                                                # Compute transitions for Sankey
                                                transitions = {}
                                                try:
                                                    combined = hansen1.multiply(1000).add(hansen2)
                                                    transition_hist = combined.reduceRegion(
                                                        reducer=ee.Reducer.frequencyHistogram(),
                                                        geometry=geometry,
                                                        scale=30,
                                                        maxPixels=1e9
                                                    ).getInfo()
                                                    
                                                    if transition_hist:
                                                        trans_key = list(transition_hist.keys())[0] if transition_hist else None
                                                        if trans_key and transition_hist[trans_key]:
                                                            for combined_val_str, count in transition_hist[trans_key].items():
                                                                combined_val = int(combined_val_str)
                                                                source_class = combined_val // 1000
                                                                target_class = combined_val % 1000
                                                                area_ha = count * 0.09
                                                                
                                                                if source_class > 0 and target_class > 0 and area_ha > 0:
                                                                    if st.session_state.use_consolidated_classes:
                                                                        source_consolidated = get_consolidated_class(source_class)
                                                                        target_consolidated = get_consolidated_class(target_class)
                                                                        if source_consolidated not in transitions:
                                                                            transitions[source_consolidated] = {'_source_id': source_class}
                                                                        if target_consolidated not in transitions[source_consolidated]:
                                                                            transitions[source_consolidated][target_consolidated] = 0
                                                                        transitions[source_consolidated][target_consolidated] += area_ha
                                                                    else:
                                                                        if source_class not in transitions:
                                                                            transitions[source_class] = {}
                                                                        transitions[source_class][target_class] = area_ha
                                                except:
                                                    pass
                                                
                                                # Store comparison results in session state
                                                st.session_state.hansen_comparison_result = {
                                                    'year1': h_year1,
                                                    'year2': h_year2,
                                                    'df_comp': df_comp,
                                                    'df1_disp': df1_disp,
                                                    'df2_disp': df2_disp,
                                                    'hansen1': hansen1,
                                                    'hansen2': hansen2,
                                                    'geometry': geometry,
                                                    'use_consolidated': st.session_state.use_consolidated_classes,
                                                    'transitions': transitions
                                                }
                                                
                                                st.success(f"✓ Hansen Comparison ({h_year1} vs {h_year2}) completed")
                                        else:
                                            st.error("Could not retrieve data for one or both years")
                                except Exception as e:
                                    st.error(f"Hansen Comparison error: {e}")
                        else:
                            st.info("Add 2 or more Hansen years to compare changes")
                    
                    # Display stored comparison results side-by-side
                    st.divider()
                    st.markdown("### 📊 Comparison Results Summary")
                    
                    col_mb, col_hansen = st.columns(2)
                    
                    # MapBiomas comparison results
                    with col_mb:
                        if st.session_state.mapbiomas_comparison_result:
                            result = st.session_state.mapbiomas_comparison_result
                            st.markdown(f"#### 🌱 MapBiomas ({result['year1']} vs {result['year2']})")
                            
                            with st.expander("📋 Data Table"):
                                st.dataframe(result['df'], width="stretch")
                            
                            with st.expander("📊 Side-by-side Charts"):
                                col_left, col_right = st.columns(2)
                                with col_left:
                                    fig = plot_area_distribution(result['df_year1'], year=result['year1'], top_n=10)
                                    st.pyplot(fig, width="stretch")
                                    # Store for export (use 1-based indexing for consistency with folder names)
                                    polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                    if 'analysis_figures' not in st.session_state:
                                        st.session_state.analysis_figures = {}
                                    st.session_state.analysis_figures[f'polygon_{polygon_idx}_mapbiomas_year1'] = fig
                                with col_right:
                                    fig = plot_area_distribution(result['df_year2'], year=result['year2'], top_n=10)
                                    st.pyplot(fig, width="stretch")
                                    # Store for export (use 1-based indexing for consistency with folder names)
                                    polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                    if 'analysis_figures' not in st.session_state:
                                        st.session_state.analysis_figures = {}
                                    st.session_state.analysis_figures[f'polygon_{polygon_idx}_mapbiomas_year2'] = fig
                            
                            with st.expander("🎯 Gains & Losses (km²)"):
                                from plotting_utils import calculate_gains_losses
                                try:
                                    comparison_df = calculate_gains_losses(
                                        result['df_year1'],
                                        result['df_year2'],
                                        class_col='Class_ID',
                                        area_col='Area_ha'
                                    )
                                    if len(comparison_df) > 0:
                                        fig = plot_gains_losses(
                                            comparison_df,
                                            result['year1'],
                                            result['year2'],
                                            top_n=12
                                        )
                                        st.pyplot(fig, width="stretch")
                                        # Store for export (use 1-based indexing for consistency with folder names)
                                        polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                        if 'analysis_figures' not in st.session_state:
                                            st.session_state.analysis_figures = {}
                                        st.session_state.analysis_figures[f'polygon_{polygon_idx}_mapbiomas_gains_losses'] = fig
                                        # Store comparison CSV for export
                                        st.session_state.mapbiomas_comparison_csv = comparison_df
                                    else:
                                        st.info("No comparison data available")
                                except Exception as e:
                                    st.warning(f"Could not generate gains/losses chart: {str(e)[:100]}")
                            
                            with st.expander("🔄 Land Cover Transitions (Sankey)"):
                                if result.get('transitions'):
                                    try:
                                        sankey_fig = create_sankey_transitions(result['transitions'], result['year1'], result['year2'])
                                        if sankey_fig:
                                            st.plotly_chart(sankey_fig, width="stretch")
                                            # Store Sankey for export (use 1-based indexing)
                                            polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                            if 'analysis_figures' not in st.session_state:
                                                st.session_state.analysis_figures = {}
                                            st.session_state.analysis_figures[f'polygon_{polygon_idx}_mapbiomas_sankey'] = sankey_fig
                                            # Store transitions data for export
                                            st.session_state.mapbiomas_transitions = result.get('transitions')
                                    except Exception as e:
                                        st.warning(f"Could not display Sankey: {str(e)[:50]}")
                                else:
                                    st.info("No transition data available")
                            
                            # Display summary metrics
                            total_change = result['df']["Change (ha)"].sum()
                            loss = result['df'][result['df']["Change (ha)"] < 0]["Change (ha)"].sum()
                            gain = result['df'][result['df']["Change (ha)"] > 0]["Change (ha)"].sum()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Change", f"{total_change:.0f} ha")
                            with col2:
                                st.metric("Loss", f"{loss:.0f} ha")
                            with col3:
                                st.metric("Gain", f"{gain:.0f} ha")
                        else:
                            st.caption("No MapBiomas comparison yet. Click 'Compare MapBiomas Years' to run comparison.")
                    
                    # Hansen comparison results
                    with col_hansen:
                        if st.session_state.hansen_comparison_result:
                            result = st.session_state.hansen_comparison_result
                            st.markdown(f"#### 🌍 Hansen ({result['year1']} vs {result['year2']})")
                            
                            with st.expander("📋 Data Table"):
                                st.dataframe(result['df_comp'], width="stretch")
                            
                            with st.expander("📊 Side-by-side Charts"):
                                col_left, col_right = st.columns(2)
                                with col_left:
                                    fig = plot_area_distribution(result['df1_disp'], year=result['year1'], top_n=10)
                                    st.pyplot(fig, width="stretch")
                                    # Store for export (use 1-based indexing for consistency with folder names)
                                    polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                    if 'analysis_figures' not in st.session_state:
                                        st.session_state.analysis_figures = {}
                                    st.session_state.analysis_figures[f'polygon_{polygon_idx}_hansen_year1'] = fig
                                with col_right:
                                    fig = plot_area_distribution(result['df2_disp'], year=result['year2'], top_n=10)
                                    st.pyplot(fig, width="stretch")
                                    # Store for export (use 1-based indexing for consistency with folder names)
                                    polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                    if 'analysis_figures' not in st.session_state:
                                        st.session_state.analysis_figures = {}
                                    st.session_state.analysis_figures[f'polygon_{polygon_idx}_hansen_year2'] = fig
                            
                            with st.expander("🎯 Gains & Losses (km²)"):
                                from plotting_utils import calculate_gains_losses
                                try:
                                    # Detect which class column to use
                                    class_col = 'Class_ID'
                                    if 'Class_ID' not in result['df1_disp'].columns:
                                        if 'Consolidated_Class' in result['df1_disp'].columns:
                                            class_col = 'Consolidated_Class'
                                        elif 'Class' in result['df1_disp'].columns:
                                            class_col = 'Class'
                                    
                                    comparison_df = calculate_gains_losses(
                                        result['df1_disp'],
                                        result['df2_disp'],
                                        class_col=class_col,
                                        area_col='Area_ha'
                                    )
                                    if len(comparison_df) > 0:
                                        fig = plot_gains_losses(
                                            comparison_df,
                                            result['year1'],
                                            result['year2'],
                                            top_n=12
                                        )
                                        st.pyplot(fig, width="stretch")
                                        # Store for export (use 1-based indexing for consistency with folder names)
                                        polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                        if 'analysis_figures' not in st.session_state:
                                            st.session_state.analysis_figures = {}
                                        st.session_state.analysis_figures[f'polygon_{polygon_idx}_hansen_gains_losses'] = fig
                                        # Store comparison CSV for export
                                        st.session_state.hansen_comparison_csv = comparison_df
                                    else:
                                        st.info("No comparison data available")
                                except Exception as e:
                                    st.warning(f"Could not generate gains/losses chart: {str(e)[:100]}")
                            
                            with st.expander("🔄 Land Cover Transitions (Sankey)"):
                                if result.get('transitions'):
                                    try:
                                        sankey_fig = create_sankey_transitions(result['transitions'], result['year1'], result['year2'])
                                        if sankey_fig:
                                            st.plotly_chart(sankey_fig, width="stretch")
                                            # Store Sankey for export (use 1-based indexing)
                                            polygon_idx = st.session_state.get('selected_feature_index', 0) + 1
                                            if 'analysis_figures' not in st.session_state:
                                                st.session_state.analysis_figures = {}
                                            st.session_state.analysis_figures[f'polygon_{polygon_idx}_hansen_sankey'] = sankey_fig
                                            # Store transitions data for export
                                            st.session_state.hansen_transitions = result.get('transitions')
                                    except Exception as e:
                                        st.warning(f"Could not display Sankey: {str(e)[:50]}")
                                else:
                                    st.info("No transition data available")
                            
                            # Display summary metrics
                            total_change = result['df_comp']["Change (ha)"].sum()
                            loss = result['df_comp'][result['df_comp']["Change (ha)"] < 0]["Change (ha)"].sum()
                            gain = result['df_comp'][result['df_comp']["Change (ha)"] > 0]["Change (ha)"].sum()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Change", f"{total_change:.0f} ha")
                            with col2:
                                st.metric("Loss", f"{loss:.0f} ha")
                            with col3:
                                st.metric("Gain", f"{gain:.0f} ha")
                        else:
                            st.caption("No Hansen comparison yet. Click 'Compare Hansen Years' to run comparison.")
                    
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
if "all_drawn_features" not in st.session_state:
    st.session_state.all_drawn_features = []  # List of all captured polygons
if "selected_feature_index" not in st.session_state:
    st.session_state.selected_feature_index = None
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "mapbiomas_comparison_result" not in st.session_state:
    st.session_state.mapbiomas_comparison_result = None
if "hansen_comparison_result" not in st.session_state:
    st.session_state.hansen_comparison_result = None
if "use_consolidated_classes" not in st.session_state:
    st.session_state.use_consolidated_classes = True
if "analysis_figures" not in st.session_state:
    st.session_state.analysis_figures = {}  # Store matplotlib figures for export

# Initialize buffer storage
if "buffer_geometries" not in st.session_state:
    st.session_state.buffer_geometries = {}  # {buffer_name: ee.Geometry}
if "buffer_metadata" not in st.session_state:
    st.session_state.buffer_metadata = {}  # {buffer_name: metadata_dict}
if "buffer_compare_mode" not in st.session_state:
    st.session_state.buffer_compare_mode = False  # Whether to compare original vs buffer
if "buffer_analysis_results" not in st.session_state:
    st.session_state.buffer_analysis_results = {}  # {buffer_name: {year: dataframe}}
if "current_buffer_for_analysis" not in st.session_state:
    st.session_state.current_buffer_for_analysis = None  # Active buffer for comparison

# Initialize territory analysis session state
initialize_territory_session_state()

# ============================================================================
# SIDEBAR
# ============================================================================


# ============================================================================
# SIDEBAR RENDERING
# ============================================================================

render_complete_sidebar()

# ============================================================================
# MAIN CONTENT
# ============================================================================

st.title("🌎 Yvynation - Land Cover Analysis 🏞️")

# Tutorial section - main location
with st.expander("📚 How to Use This Platform", expanded=False):
    st.markdown("### 🎯 Getting Started\n\nThis platform enables comprehensive land cover analysis for Brazil and global forest monitoring. You can analyze custom areas, indigenous territories, and external buffer zones.")
    
    with st.expander("1️⃣ **Analyze a Custom Polygon**", expanded=False):
        st.markdown("""
        **Draw and analyze any area on the map:**
        
        1. **Drawing Tools** (top-left corner of map):
           - Click the **Rectangle** tool (⬜) for quick rectangular selections
           - Click the **Polygon** tool (🔷) for custom shapes with multiple points
           - Double-click or click the first point again to complete a polygon
        
        2. **Select Data Layers** (left sidebar):
           - **MapBiomas**: Brazilian land cover (1985-2023, 62 classes, 30m resolution)
           - **Hansen/GLAD**: Global forest change (2000-2020, 256 classes, 30m resolution)
           - Toggle multiple years to enable comparisons
        
        3. **Analysis Results**:
           - Land cover distribution by class
           - Area statistics (hectares and percentages)
           - Visual charts and data tables
           - Downloadable CSV files with "original_" prefix
        
        4. **Buffer Zone Analysis** (NEW):
           - After drawing, click "🔵 Add Buffer Zone"
           - Choose buffer distance: **2km**, **5km**, or **10km**
           - Creates a ring-shaped zone around your polygon
           - Enable "📊 Compare Polygon vs Buffer" to analyze both areas side-by-side
           - CSV files will have "buffer_" prefix for buffer zone data
        
        💡 **Tips**:
        - Delete unwanted polygons by clicking the trash icon (🗑️) in drawing tools
        - Draw multiple small areas to compare different locations
        - Use buffer zones to understand edge effects and surrounding land use
        """)
    
    with st.expander("2️⃣ **Analyze an Indigenous Territory**", expanded=False):
        st.markdown("""
        **Pre-defined indigenous territory boundaries with historical analysis:**
        
        1. **Select Territory** (📊 Territory Analysis tab in sidebar):
           - Filter by **State** or browse all territories
           - Choose from 400+ officially recognized indigenous lands
           - View territory metadata: area, location, recognition status
        
        2. **Territory Analysis Features**:
           - Historical land cover changes (1985-2023)
           - Area changes by land cover class
           - Deforestation and regeneration trends
           - Transition diagrams (Sankey charts) showing conversions between classes
           - Export all data and visualizations
        
        3. **Buffer Zone Analysis for Territories**:
           - Create **external buffer zones** (2km/5km/10km) around the entire territory
           - Compare land use **inside vs outside** the protected boundary
           - Identify pressure zones and encroachment patterns
           - Enable "📊 Compare Territory vs Buffer" checkbox
           - Results appear in separate tabs: **"📍 Original Area"** and **"🔵 Buffer Zone Xkm"**
        
        💡 **Tips**:
        - Compare multiple territories in the same state to identify regional patterns
        - Use buffer analysis to assess external threats and boundary integrity
        - Long-term comparisons (1985 vs 2023) reveal protection effectiveness
        - Export data for integration with GIS software or reports
        """)
    
    with st.expander("3️⃣ **Multi-Year Comparison**", expanded=False):
        st.markdown("""
        **Compare land cover changes between any two years:**
        
        1. **Setup Comparison** (📈 Comparison tab):
           - First select **2+ years** in the layer controls (sidebar)
           - Draw a polygon or select a territory
           - Navigate to the **📈 Comparison** tab
           - Choose **Year 1** (baseline) and **Year 2** (comparison)
        
        2. **Click Comparison Buttons**:
           - **🔄 Compare MapBiomas Years**: Brazilian land cover changes
           - **🔄 Compare Hansen Years**: Global forest changes
        
        3. **View Results**:
           - **Data Table**: Side-by-side area values with change calculations
           - **Side-by-side Charts**: Visual distribution for each year
           - **Gains & Losses**: Horizontal bar chart showing increases/decreases
           - **Sankey Diagram**: Flow chart showing land cover transitions
           - **Summary Metrics**: Total change, loss, and gain values
        
        4. **Buffer Comparison Mode**:
           - When buffer compare is enabled, perform comparisons on both areas
           - Results appear in separate tabs for original and buffer zones
           - Download separate CSV files for each area
        
        💡 **Tips**:
        - **Long-term trends**: Compare 1985 vs 2023 for 38 years of change
        - **Recent changes**: Compare consecutive years (2022 vs 2023) for current activity
        - **Policy impact**: Compare years before/after policy implementation
        - **Deforestation events**: Use 5-year intervals to identify major changes
        """)
    
    with st.expander("4️⃣ **Export and Download Results**", expanded=False):
        st.markdown("""
        **Save your analysis results for reports and further analysis:**
        
        - **CSV Downloads**: Click "📥 Download CSV" buttons in each analysis tab
          - Individual year data: `original_mapbiomas_2023.csv`
          - Buffer zone data: `buffer_mapbiomas_2023.csv`
          - Comparison tables with change calculations
        
        - **PNG Exports**: High-resolution images from Earth Engine
          - Export analysis regions as georeferenced images
          - Suitable for GIS software and publications
        
        - **PDF Reports** (future): Comprehensive analysis summaries
        
        💡 **Tip**: All downloads use consistent naming conventions for easy organization
        """)
    
    with st.expander("🗺️ **Map Controls & Navigation**", expanded=False):
            st.markdown("""
            **Basic Navigation:**
            - **Zoom In/Out**: 
              - Mouse scroll wheel
              - **+/−** buttons (top-left corner)
              - Double-click to zoom in
            - **Pan**: Click and drag anywhere on the map
            - **Fullscreen**: Click fullscreen button (top-left area) for larger view
            
            **Drawing Tools** (top-left corner):
            - **✏️ Edit Layers**: Modify existing polygons
            - **🗑️ Delete Layers**: Remove unwanted polygons
            - **⬜ Draw Rectangle**: Quick rectangular areas
            - **🔷 Draw Polygon**: Custom multi-point shapes
            - **Finish Drawing**: Double-click or click first point to complete
            
            **Layer Controls** (top-right corner):
            - **Base Layers**: Switch between OpenStreetMap, Satellite, Terrain views
            - **Overlays**: Toggle MapBiomas and Hansen layers on/off
            - **Transparency**: Some layers support transparency adjustment
            - **Territory Boundaries**: Show/hide indigenous territory outlines
            
            **Map Features:**
            - **Sky-blue rings**: External buffer zones (when created)
            - **Colored polygons**: Your drawn analysis areas
            - **Territory boundaries**: Pre-loaded indigenous land boundaries
            - **Scale bar**: Bottom-left shows map scale
            - **Coordinates**: Hover to see latitude/longitude (if enabled)
            
            💡 **Navigation Tip**: Click the home button to reset the map to initial Brazil view
            """)
        
    with st.expander("📊 **Understanding the Data & Results**", expanded=False):
            st.markdown("""
            **Data Sources:**
            
            **MapBiomas Collection 9** (Brazil):
            - **Coverage**: All of Brazil, 1985-2023
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 62 land cover types including:
              - Natural vegetation (forest, savanna, grassland, wetland)
              - Agriculture (crops, pasture, plantations)
              - Urban areas, water bodies, mining
            - **Update frequency**: Annual releases
            - **Accuracy**: ~90% overall (varies by class and region)
            
            **Hansen/GLAD Global Forest Change**:
            - **Coverage**: Global (all continents)
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 256 land use classes combining:
              - Forest cover presence/absence
              - Forest loss year (2000-2020)
              - Forest gain (2000-2012)
              - Land use categories
            - **Best for**: Forest change detection and monitoring
            - **Consolidation**: Toggle "Use consolidated classes" for simplified 12-class view
            
            **Result Interpretation:**
            - **Area (ha)**: Hectares = 10,000 m² (about 2.5 acres)
            - **Pixels**: Each pixel = 900 m² (30m × 30m)
            - **Percentages**: Calculated from total analyzed area
            - **Change values**: Positive = increase, Negative = decrease
            - **Transitions**: Flow from one land cover class to another
            
            **Charts & Visualizations:**
            - **Bar charts**: Top 15 classes by area (customizable)
            - **Sankey diagrams**: Flow of land cover transitions between years
            - **Gains & Losses**: Horizontal bars showing increases (right) and decreases (left)
            - **Summary metrics**: Key statistics at a glance
            
            💡 **Accuracy Note**: Results depend on source data quality. Cross-reference with both datasets for validation.
            """)

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

# ============================================================================
# MAP DISPLAY
# ============================================================================

# Build and display the interactive map
map_data = build_and_display_map()

# Process drawn features from the map
process_drawn_features(map_data)

# Polygon selector
render_polygon_selector()

# Layer reference guide
render_layer_reference_guide()
    
    

# ============================================================================
# HELPER FUNCTIONS FOR TERRITORY ANALYSIS
# ============================================================================

def render_territory_comparison_content(result_y1, result_y2, year1, year2, area_name, source, geometry, area_prefix="territory"):
    """Render the comparison charts and data tables for territory or buffer analysis"""
    
    from plotting_utils import calculate_gains_losses
    comparison_df = calculate_gains_losses(
        result_y1,
        result_y2,
        class_col='Class_ID',
        area_col='Area_ha'
    )
    
    # Side-by-side comparison with gains/losses
    col_left, col_right = st.columns(2)
    
    with col_left:
        with st.expander("📊 Side-by-Side Comparison", expanded=True):
            st.markdown(f"Land Cover Distribution Comparison")
            fig = plot_area_comparison(
                result_y1,
                result_y2,
                year1,
                year2,
                top_n=12
            )
            st.pyplot(fig, width="stretch")
            st.session_state.analysis_figures[f'{area_prefix}_comparison'] = fig
    
    with col_right:
        with st.expander("🎯 Gains & Losses (km²)", expanded=True):
            st.markdown(f"Class Gains and Losses ({year1} to {year2})")
            if len(comparison_df) > 0:
                fig = plot_gains_losses(
                    comparison_df,
                    year1,
                    year2,
                    top_n=12
                )
                st.pyplot(fig, width="stretch")
                st.session_state.analysis_figures[f'{area_prefix}_gains_losses'] = fig
                
                # Summary stats
                total_gains = comparison_df[comparison_df['Change_km2'] > 0]['Change_km2'].sum()
                total_losses = abs(comparison_df[comparison_df['Change_km2'] < 0]['Change_km2'].sum())
                net_change = total_gains - total_losses
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Gains", f"{total_gains:,.1f} km²")
                with col2:
                    st.metric("Losses", f"{total_losses:,.1f} km²")
                with col3:
                    st.metric("Net", f"{net_change:+,.1f} km²")
            else:
                st.info("No comparison data available")
    
    # Data tables and change analysis
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("📋 Data Tables", expanded=False):
            tab_y1, tab_y2 = st.tabs([f"Year {year1}", f"Year {year2}"])
            
            with tab_y1:
                display_cols = ['Class', 'Class_ID', 'Pixels', 'Area_ha'] if 'Class' in result_y1.columns else ['Class_ID', 'Pixels', 'Area_ha']
                st.dataframe(result_y1[display_cols], width="stretch")
                csv1 = result_y1.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv1,
                    file_name=f"{area_name}_{year1}.csv",
                    mime="text/csv",
                    key=f"download_{area_prefix}_y1"
                )
            
            with tab_y2:
                display_cols = ['Class', 'Class_ID', 'Pixels', 'Area_ha'] if 'Class' in result_y2.columns else ['Class_ID', 'Pixels', 'Area_ha']
                st.dataframe(result_y2[display_cols], width="stretch")
                csv2 = result_y2.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv2,
                    file_name=f"{area_name}_{year2}.csv",
                    mime="text/csv",
                    key=f"download_{area_prefix}_y2"
                )
    
    with col2:
        with st.expander("📈 Change Analysis", expanded=False):
            st.markdown(f"Percentage Change Analysis")
            if len(comparison_df) > 0:
                fig = plot_change_percentage(
                    comparison_df,
                    year1,
                    year2,
                    top_n=12
                )
                st.pyplot(fig, width="stretch")
                st.session_state.analysis_figures[f'{area_prefix}_change_percentage'] = fig
                
                # Top gainers and losers
                tcol1, tcol2 = st.columns(2)
                with tcol1:
                    st.markdown("**Top Gainers**")
                    top_gainers = comparison_df[comparison_df['Change_km2'] > 0].nlargest(5, 'Change_km2')
                    if len(top_gainers) > 0:
                        st.dataframe(top_gainers[['Class', 'Change_km2', 'Change_pct']], width="stretch")
                
                with tcol2:
                    st.markdown("**Top Losers**")
                    top_losers = comparison_df[comparison_df['Change_km2'] < 0].nsmallest(5, 'Change_km2')
                    if len(top_losers) > 0:
                        st.dataframe(top_losers[['Class', 'Change_km2', 'Change_pct']], width="stretch")
    
    # Add Sankey diagram with pixel-level transitions
    with st.expander("🔄 Land Cover Transitions (Sankey)", expanded=False):
        st.markdown(f"Pixel-level transitions from {year1} to {year2}")
        try:
            if geometry is not None:
                # Compute pixel-level transitions using Earth Engine
                transitions = {}
                
                # Determine which dataset we're using
                if source == 'MapBiomas':
                    band1 = f'classification_{year1}'
                    band2 = f'classification_{year2}'
                    dataset = st.session_state.app.mapbiomas_v9
                    class_labels = MAPBIOMAS_LABELS
                else:  # Hansen
                    # Load Hansen datasets from Earth Engine
                    year1_str = str(year1)
                    year2_str = str(year2)
                    
                    # Get Hansen asset IDs
                    if year1_str not in HANSEN_DATASETS or year2_str not in HANSEN_DATASETS:
                        st.error(f"Hansen data not available for years {year1_str} and {year2_str}")
                        return
                    
                    # Load Hansen images and apply ocean mask
                    landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
                    hansen1 = ee.Image(HANSEN_DATASETS[year1_str]).updateMask(landmask)
                    hansen2 = ee.Image(HANSEN_DATASETS[year2_str]).updateMask(landmask)
                    
                    # Don't remap on EE side - get raw classes and consolidate in Python
                    dataset = hansen1.rename('band1').addBands(hansen2.rename('band2'))
                    band1 = 'band1'
                    band2 = 'band2'
                    class_labels = {}
                
                # Calculate transitions using frequencyHistogram
                combined = dataset.select(band1).multiply(1000).add(
                    dataset.select(band2)
                )
                transition_hist = combined.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                if transition_hist:
                    trans_key = list(transition_hist.keys())[0] if transition_hist else None
                    if trans_key and transition_hist[trans_key]:
                        for combined_val_str, count in transition_hist[trans_key].items():
                            combined_val = int(combined_val_str)
                            source_class = combined_val // 1000
                            target_class = combined_val % 1000
                            area_ha = count * 0.09
                            
                            if source_class > 0 and target_class > 0 and area_ha > 0:
                                # For Hansen, use stratum names; for MapBiomas, use numeric IDs
                                if 'Hansen' in source:
                                    from hansen_reference_mapping import get_stratum_name
                                    source_key = get_stratum_name(source_class)
                                    target_key = get_stratum_name(target_class)
                                else:
                                    source_key = source_class
                                    target_key = target_class
                                
                                if source_key not in transitions:
                                    transitions[source_key] = {}
                                # Aggregate transitions
                                if target_key not in transitions[source_key]:
                                    transitions[source_key][target_key] = area_ha
                                else:
                                    transitions[source_key][target_key] += area_ha
                
                if transitions:
                    # For Hansen, use stratum colors; for MapBiomas, use class colors
                    if 'Hansen' in source:
                        from hansen_reference_mapping import HANSEN_STRATUM_COLORS, HANSEN_STRATUM_NAMES
                        
                        class_colors = {}
                        class_names = {}
                        
                        for source_name in transitions.keys():
                            if source_name not in class_colors:
                                stratum_num = None
                                for num, name in HANSEN_STRATUM_NAMES.items():
                                    if name == source_name:
                                        stratum_num = num
                                        break
                                
                                if stratum_num and stratum_num in HANSEN_STRATUM_COLORS:
                                    class_colors[source_name] = HANSEN_STRATUM_COLORS[stratum_num]
                                else:
                                    class_colors[source_name] = '#cccccc'
                                class_names[source_name] = source_name
                            
                            for target_name in transitions[source_name].keys():
                                if target_name not in class_colors:
                                    stratum_num = None
                                    for num, name in HANSEN_STRATUM_NAMES.items():
                                        if name == target_name:
                                            stratum_num = num
                                            break
                                    
                                    if stratum_num and stratum_num in HANSEN_STRATUM_COLORS:
                                        class_colors[target_name] = HANSEN_STRATUM_COLORS[stratum_num]
                                    else:
                                        class_colors[target_name] = '#cccccc'
                                    class_names[target_name] = target_name
                    else:
                        class_colors = MAPBIOMAS_COLOR_MAP
                        class_names = MAPBIOMAS_LABELS
                    
                    sankey_fig = create_sankey_transitions(
                        transitions,
                        year1,
                        year2,
                        class_colors=class_colors,
                        class_names=class_names
                    )
                    if sankey_fig:
                        st.plotly_chart(sankey_fig, width="stretch")
                        # Store Sankey for export
                        if 'analysis_figures' not in st.session_state:
                            st.session_state.analysis_figures = {}
                        st.session_state.analysis_figures[f'{area_prefix}_sankey'] = sankey_fig
                        # Store transitions data for export
                        if area_prefix == "territory":
                            st.session_state.territory_transitions = transitions
                    else:
                        st.info("Could not generate Sankey diagram")
                else:
                    st.info("No transition data available")
            else:
                st.warning("Geometry not available. Run analysis first.")
        except Exception as e:
            st.warning(f"Could not display Sankey diagram: {str(e)[:100]}")


# ============================================================================
# ANALYSIS SECTION
# ============================================================================

# Map export section
render_map_export_section()

# Export all button at the top
st.divider()
with st.container():
    st.subheader("💾 Export Analysis")
    generate_export_button(st.session_state)

st.divider()

# Display territory analysis results if available
if st.session_state.data_loaded and st.session_state.territory_result is not None:
    st.divider()
    
    # Check if comparing years
    if st.session_state.territory_result_year2 is not None:
        st.subheader(f"🏛️ Territory Comparison - {st.session_state.territory_name}")
        
        # Debug info - show buffer status
        if st.session_state.buffer_compare_mode:
            buffer_status_cols = st.columns([1, 1, 1])
            with buffer_status_cols[0]:
                if st.session_state.buffer_compare_mode:
                    st.success("✓ Buffer Compare Mode: ON")
                else:
                    st.info("Buffer Compare Mode: OFF")
            with buffer_status_cols[1]:
                if st.session_state.current_buffer_for_analysis:
                    st.success(f"✓ Buffer: {st.session_state.current_buffer_for_analysis}")
                else:
                    st.warning("⚠ No Buffer Created")
            with buffer_status_cols[2]:
                if st.session_state.current_buffer_for_analysis and st.session_state.current_buffer_for_analysis in st.session_state.buffer_geometries:
                    st.success("✓ Geometry: Available")
                else:
                    st.warning("⚠ Geometry: Not Found")
        
        # Check if buffer compare mode is active for territory
        territory_geom = st.session_state.get('territory_geometry_for_analysis')
        
        # Check if buffer has been created and analyzed
        buffer_exists = (
            st.session_state.buffer_compare_mode and 
            st.session_state.current_buffer_for_analysis and
            st.session_state.current_buffer_for_analysis in st.session_state.buffer_geometries
        )
        
        # Check if we have buffer analysis results
        has_buffer_results = (
            'buffer_result_mapbiomas' in st.session_state or 
            'buffer_result_hansen' in st.session_state
        )
        
        # Show buffer status hint if buffer mode is on but buffer not ready
        if st.session_state.buffer_compare_mode and not buffer_exists:
            if not st.session_state.current_buffer_for_analysis:
                st.info("💡 **How to enable buffer comparison:** Go to the sidebar → Territory Analysis section → Enable '📊 Compare Territory vs Buffer' → Select distance → Click '🔵 Create Buffer' → Click 'Analyze Buffer Zone'")
            elif st.session_state.current_buffer_for_analysis not in st.session_state.buffer_geometries:
                st.warning("⚠️ Buffer geometry not found. Please create the buffer again in the sidebar.")
        
        # Always show tabs if buffer compare mode is on
        if st.session_state.buffer_compare_mode and buffer_exists:
            # Get buffer geometry and metadata
            buffer_geom = st.session_state.buffer_geometries[st.session_state.current_buffer_for_analysis]
            buffer_meta = st.session_state.buffer_metadata[st.session_state.current_buffer_for_analysis]
            
            if has_buffer_results:
                st.info(f"📊 Compare Mode: Switch between Territory and Buffer Zone ({buffer_meta['buffer_size_km']}km) tabs below")
            else:
                st.info(f"📊 Buffer Mode: Use 'Analyze Buffer Zone' button in sidebar to populate buffer tab data")
            
            # Create outer tabs for Territory vs Buffer - ALWAYS SHOW BOTH TABS
            territory_main_tab, buffer_main_tab = st.tabs([
                f"🏛️ {st.session_state.territory_name}",
                f"🔵 Buffer Zone ({buffer_meta['buffer_size_km']}km)"
            ])
            
            # ===== TERRITORY TAB =====
            with territory_main_tab:
                render_territory_comparison_content(
                    st.session_state.territory_result,
                    st.session_state.territory_result_year2,
                    st.session_state.territory_year,
                    st.session_state.territory_year2,
                    st.session_state.territory_name,
                    st.session_state.territory_source,
                    territory_geom,
                    area_prefix="territory"
                )
            
            # ===== BUFFER ZONE TAB =====
            with buffer_main_tab:
                # Check if buffer analysis has been done
                if 'buffer_result_mapbiomas' in st.session_state or 'buffer_result_hansen' in st.session_state:
                    # Display stored buffer results
                    if st.session_state.territory_source == 'MapBiomas':
                        buffer_result_y1 = st.session_state.get('buffer_result_mapbiomas')
                        buffer_result_y2 = st.session_state.get('buffer_result_mapbiomas_y2')
                    else:
                        buffer_result_y1 = st.session_state.get('buffer_result_hansen')
                        buffer_result_y2 = st.session_state.get('buffer_result_hansen_y2')
                    
                    if buffer_result_y1 is not None:
                        render_territory_comparison_content(
                            buffer_result_y1,
                            buffer_result_y2 if buffer_result_y2 is not None else None,
                            st.session_state.territory_year,
                            st.session_state.get('territory_year2'),
                            f"Buffer Zone ({buffer_meta['buffer_size_km']}km)",
                            st.session_state.territory_source,
                            buffer_geom,
                            area_prefix="buffer"
                        )
                    else:
                        st.info(f"📊 No buffer analysis data yet. Click 'Analyze Buffer Zone' in the sidebar to generate buffer comparison data.")
                else:
                    st.info(f"📊 No buffer analysis data. Click 'Analyze Buffer Zone' in the sidebar to generate buffer comparison data.")
        else:
            # Standard comparison without buffer
            render_territory_comparison_content(
                st.session_state.territory_result,
                st.session_state.territory_result_year2,
                st.session_state.territory_year,
                st.session_state.territory_year2,
                st.session_state.territory_name,
                st.session_state.territory_source,
                territory_geom,
                area_prefix="territory"
            )
    
    else:
        # Single year analysis - keep existing code
        st.subheader(f"🏛️ Territory Analysis - {st.session_state.territory_name}")
        
        # Show territory results in tabs
        terr_tab1, terr_tab2, terr_tab3 = st.tabs(
            ["📊 Land Cover Distribution", "📋 Data Table", "ℹ️ Territory Info"]
        )
        
        with terr_tab1:
            st.markdown(f"### Land Cover Distribution in {st.session_state.territory_name} ({st.session_state.territory_year})")
            fig = plot_area_distribution(st.session_state.territory_result, year=st.session_state.territory_year, top_n=15)
            st.pyplot(fig, width="stretch")
            st.session_state.analysis_figures['territory_distribution'] = fig
        
        with terr_tab2:
            st.markdown(f"### Raw Data - {st.session_state.territory_name} ({st.session_state.territory_year})")
            # Display with Name column if available
            display_cols = ['Name', 'Class_ID', 'Pixels', 'Area_ha'] if 'Name' in st.session_state.territory_result.columns else ['Class', 'Class_ID', 'Pixels', 'Area_ha']
            st.dataframe(st.session_state.territory_result[display_cols], width="stretch")
            
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
    st.subheader("📊 Polygon Analysis & Statistics")
    
    # Check if a feature was drawn
    if st.session_state.last_drawn_feature:
        try:
            feature_data = st.session_state.last_drawn_feature
            geometry = None
            is_buffer = False
            buffer_name = None
            
            # Check if this is a buffer feature
            if isinstance(feature_data, dict) and 'properties' in feature_data:
                props = feature_data.get('properties', {})
                if props.get('type') == 'external_buffer':
                    is_buffer = True
                    buffer_name = props.get('name', 'External Buffer')
                    st.info(f"🔵 Analyzing: {buffer_name}")
            
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
                # Check if buffer compare mode is active and buffer exists
                compare_with_buffer = (
                    st.session_state.buffer_compare_mode and 
                    st.session_state.current_buffer_for_analysis and
                    st.session_state.current_buffer_for_analysis in st.session_state.buffer_geometries
                )
                
                if compare_with_buffer:
                    # Get buffer geometry
                    buffer_geom = st.session_state.buffer_geometries[st.session_state.current_buffer_for_analysis]
                    buffer_meta = st.session_state.buffer_metadata[st.session_state.current_buffer_for_analysis]
                    
                    st.info(f"📊 Compare Mode: Switch between Original Area and Buffer Zone ({buffer_meta['buffer_size_km']}km) tabs below")
                    
                    # Create outer tabs for Original vs Buffer
                    main_tab1, main_tab2 = st.tabs(["📍 Original Area", f"🔵 Buffer Zone ({buffer_meta['buffer_size_km']}km)"])
                    
                    # ===== ORIGINAL AREA TAB =====
                    with main_tab1:
                        tab1, tab2, tab3, tab4 = st.tabs(
                            ["📍 MapBiomas Analysis", "🌍 Hansen Analysis", "📈 Comparison", "ℹ️ About"]
                        )
                        
                        # Use existing analysis code for original geometry
                        render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, area_prefix="original")
                    
                    # ===== BUFFER ZONE TAB =====
                    with main_tab2:
                        buffer_tab1, buffer_tab2, buffer_tab3, buffer_tab4 = st.tabs(
                            ["📍 MapBiomas Analysis", "🌍 Hansen Analysis", "📈 Comparison", "ℹ️ About"]
                        )
                        
                        # Use same analysis code for buffer geometry
                        render_analysis_tabs(buffer_geom, buffer_tab1, buffer_tab2, buffer_tab3, buffer_tab4, 
                                           area_prefix="buffer", buffer_name=st.session_state.current_buffer_for_analysis,
                                           buffer_size=buffer_meta['buffer_size_km'])
                else:
                    # Standard tabs without buffer comparison
                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["📍 MapBiomas Analysis", "🌍 Hansen Analysis", "📈 Comparison", "ℹ️ About"]
                    )
                    
                    # Render standard analysis
                    render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, area_prefix="original")
        except Exception as e:
            st.error(f"Error processing drawn feature: {e}")
            print(f"Analysis error: {e}")
    else:
        st.info("🎨 Draw a polygon on the map to start analyzing land cover in that area. Use the drawing tools in the top-left of the map.")


print("\n✓ Yvynation App Loaded Successfully")
