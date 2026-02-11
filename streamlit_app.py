'''
Yvynation - Indigenous Land Monitoring Platform
Interactive analysis tool for land cover changes in indigenous territories
'''

import streamlit as st

# Import translation helper
from translations import t, get_translation

# Page configuration
st.set_page_config(
    page_title=t("page_title"),
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
from tutorial_component import render_getting_started_tutorial
from analysis_tabs_component import render_analysis_tabs
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


def analyze_hansen_gfc_geometry(geometry, area_name="Area"):
    """
    Analyze Hansen Global Forest Change data for a given geometry.
    Analyzes tree cover 2000, tree loss years, and tree gain.
    
    Returns:
        dict: Dictionary with 'tree_cover', 'tree_loss', 'tree_gain' DataFrames
    """
    try:
        from config import HANSEN_GFC_DATASET
        dataset = ee.Image(HANSEN_GFC_DATASET)
        
        results = {}
        
        with st.spinner(f"🌲 Analyzing Hansen GFC data for {area_name} (3 layers)..."):
            print(f"[GFC Analysis] Starting analysis for {area_name}")
            
            # Analyze Tree Cover 2000 (0-100% canopy cover)
            try:
                print("[GFC Analysis] Processing tree cover 2000...")
                tree_cover = dataset.select(['treecover2000'])
                cover_stats = tree_cover.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                if cover_stats and 'treecover2000' in cover_stats:
                    histogram = cover_stats['treecover2000']
                    records = []
                    for percent_str, count in histogram.items():
                        percent = int(percent_str)
                        area_ha = count * 0.09
                        records.append({
                            'Percent_Cover': percent,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    results['tree_cover'] = pd.DataFrame(records).sort_values('Percent_Cover')
                    print(f"[GFC Analysis] Tree cover: {len(records)} data points")
            except Exception as cover_err:
                print(f"[GFC Analysis] Warning - tree cover analysis failed: {cover_err}")
                st.warning(f"Tree cover analysis partial: {str(cover_err)[:100]}")
            
            # Analyze Tree Loss Year (0=no loss, 1-24=year 2001-2024)
            try:
                print("[GFC Analysis] Processing tree loss...")
                tree_loss = dataset.select(['lossyear'])
                loss_stats = tree_loss.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                if loss_stats and 'lossyear' in loss_stats:
                    histogram = loss_stats['lossyear']
                    records = []
                    for year_code_str, count in histogram.items():
                        year_code = int(year_code_str)
                        if year_code == 0:
                            year_label = 'No Loss'
                        else:
                            year_label = f'{2000 + year_code}'
                        area_ha = count * 0.09
                        records.append({
                            'Year_Code': year_code,
                            'Year': year_label,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    results['tree_loss'] = pd.DataFrame(records).sort_values('Year_Code')
                    print(f"[GFC Analysis] Tree loss: {len(records)} data points")
            except Exception as loss_err:
                print(f"[GFC Analysis] Warning - tree loss analysis failed: {loss_err}")
                st.warning(f"Tree loss analysis partial: {str(loss_err)[:100]}")
            
            # Analyze Tree Gain (0=no gain, 1=gain 2000-2012)
            try:
                print("[GFC Analysis] Processing tree gain...")
                tree_gain = dataset.select(['gain'])
                gain_stats = tree_gain.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                if gain_stats and 'gain' in gain_stats:
                    histogram = gain_stats['gain']
                    records = []
                    for gain_code_str, count in histogram.items():
                        gain_code = int(gain_code_str)
                        gain_label = 'Gain (2000-2012)' if gain_code == 1 else 'No Gain'
                        area_ha = count * 0.09
                        records.append({
                            'Gain_Code': gain_code,
                            'Status': gain_label,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    results['tree_gain'] = pd.DataFrame(records).sort_values('Gain_Code')
                    print(f"[GFC Analysis] Tree gain: {len(records)} data points")
            except Exception as gain_err:
                print(f"[GFC Analysis] Warning - tree gain analysis failed: {gain_err}")
                st.warning(f"Tree gain analysis partial: {str(gain_err)[:100]}")
        
        if results:
            print(f"[GFC Analysis] Completed with {len(results)} datasets: {list(results.keys())}")
            st.success(f"✓ Analysis complete! Found data for: {', '.join(results.keys())}")
            return results
        else:
            print("[GFC Analysis] No data returned from analysis")
            st.warning("No Hansen GFC data found in this area")
            return None
        
    except Exception as e:
        import traceback
        error_msg = str(e)[:300]
        print(f"[GFC Analysis] CRITICAL ERROR: {e}")
        traceback.print_exc()
        st.error(f"Error analyzing Hansen GFC for {area_name}: {error_msg}")
    return None


def analyze_aafc_geometry(geometry, year, area_name="Area"):
    """
    Analyze AAFC Annual Crop Inventory data for a given geometry and year (Canada).
    
    Returns:
        pd.DataFrame: Analysis results or None if error
    """
    try:
        from config import AAFC_ACI_DATASET, AAFC_LABELS
        
        with st.spinner(f"Analyzing AAFC {year} for {area_name}..."):
            # Filter image collection to specific year
            aafc_image = ee.ImageCollection(AAFC_ACI_DATASET).filter(
                ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
            ).first()
            
            if aafc_image is None:
                st.warning(f"No AAFC data found for year {year}")
                return None
            
            # Get the landcover band
            landcover = aafc_image.select(['landcover'])
            
            stats = landcover.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            if stats:
                histogram = stats.get('landcover', {})
                if histogram:
                    records = []
                    for value_str, count in histogram.items():
                        value = int(value_str)
                        crop_name = AAFC_LABELS.get(value, f"Class {value}")
                        area_ha = count * 0.09
                        records.append({
                            'Class_ID': value,
                            'Class': crop_name,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
                    return df
    except Exception as e:
        st.error(f"Error analyzing AAFC for {area_name}: {str(e)[:200]}")
        print(f"Full error: {e}")
    return None



# ============================================================================
# INITIALIZATION
# ============================================================================

print("\n🚀 Yvynation App Starting...")

# Initialize Earth Engine
try:
    st.session_state.ee_module = initialize_earth_engine()
    print("✓ Earth Engine initialized")
except Exception as e:
    st.error(t("ee_init_error", error=str(e)))
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
if "selected_country" not in st.session_state:
    st.session_state.selected_country = "Brazil"
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
if "current_mapbiomas_year" not in st.session_state:
    st.session_state.current_mapbiomas_year = 2023
if "current_hansen_year" not in st.session_state:
    st.session_state.current_hansen_year = "2020"
if "current_aafc_year" not in st.session_state:
    st.session_state.current_aafc_year = 2023
if "mapbiomas_layers" not in st.session_state:
    st.session_state.mapbiomas_layers = {}  # {year: True/False}
if "hansen_layers" not in st.session_state:
    st.session_state.hansen_layers = {}  # {year: True/False}
if "aafc_layers" not in st.session_state:
    st.session_state.aafc_layers = {}  # {year: True/False}
if "hansen_gfc_tree_cover" not in st.session_state:
    st.session_state.hansen_gfc_tree_cover = False
if "hansen_gfc_tree_loss" not in st.session_state:
    st.session_state.hansen_gfc_tree_loss = False
if "hansen_gfc_tree_gain" not in st.session_state:
    st.session_state.hansen_gfc_tree_gain = False
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

# Helper to get current language
def get_lang():
    return st.session_state.get('language', 'en')

st.title(t("main_page_title"))

# Render bilingual tutorial component
render_getting_started_tutorial()

# Display current layer configuration
if st.session_state.data_loaded:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(t("base_layer"), "OpenStreetMap", help=t("base_layer_hint"))
        
    with col2:
        mapbiomas_count = len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
        st.metric(t("mapbiomas_layers_label"), mapbiomas_count, help=t("mapbiomas_layers_hint"))
        
    with col3:
        hansen_count = len([y for y, v in st.session_state.hansen_layers.items() if v])
        st.metric(t("hansen_layers_label"), hansen_count, help=t("hansen_layers_hint"))
    
    with col4:
        hansen_gfc_count = sum([
            st.session_state.get('hansen_gfc_tree_cover', False),
            st.session_state.get('hansen_gfc_tree_loss', False),
            st.session_state.get('hansen_gfc_tree_gain', False)
        ])
        st.metric(t("hansen_gfc_layers_label"), hansen_gfc_count, help=t("hansen_gfc_layers_hint"))
    
    # Show active layers
    st.divider()
    st.subheader(t("active_layers"))
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.mapbiomas_layers:
            years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            if years:
                st.write(f"**{t('mapbiomas_years')}**")
                st.write(", ".join(map(str, years)))
            else:
                st.caption(t("no_mapbiomas_selected"))
        else:
            st.caption(t("no_mapbiomas_added"))
    
    with col2:
        if st.session_state.hansen_layers:
            years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
            if years:
                st.write(f"**{t('hansen_years')}**")
                st.write(", ".join(map(str, years)))
            else:
                st.caption(t("no_hansen_selected"))
        else:
            st.caption(t("no_hansen_added"))
    
    with col3:
        hansen_gfc_layers = []
        if st.session_state.get('hansen_gfc_tree_cover', False):
            hansen_gfc_layers.append(t("tree_cover_2000"))
        if st.session_state.get('hansen_gfc_tree_loss', False):
            hansen_gfc_layers.append(t("tree_loss_period"))
        if st.session_state.get('hansen_gfc_tree_gain', False):
            hansen_gfc_layers.append(t("tree_gain_period"))
        
        if hansen_gfc_layers:
            st.write(f"**{t('hansen_gfc_label')}**")
            for layer in hansen_gfc_layers:
                st.caption(f"• {layer}")
        else:
            st.caption(t("no_hansen_gfc_added"))


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
        with st.expander(t("side_by_side_comparison"), expanded=True):
            st.markdown(f"{t('land_cover_distribution')} {t('comparison')}")
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
        with st.expander(t("gains_losses"), expanded=True):
            st.markdown(f"{t('class_gains_losses')} ({year1} {t('to')} {year2})")
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
                    st.metric(t("gains"), f"{total_gains:,.1f} km²")
                with col2:
                    st.metric(t("losses"), f"{total_losses:,.1f} km²")
                with col3:
                    st.metric(t("net"), f"{net_change:+,.1f} km²")
            else:
                st.info(t("no_comparison_data_available"))
    
    # Data tables and change analysis
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander(t("data_tables"), expanded=False):
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
        with st.expander(t("change_analysis"), expanded=False):
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
    with st.expander(t("land_cover_transitions"), expanded=False):
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
    st.subheader(t("export_analysis"))
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
    st.subheader(t("polygon_analysis_header"))
    
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
                    st.info(t("analyzing_polygon", name=buffer_name))
            
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
                        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                            ["📍 MapBiomas Analysis", "🌲 Hansen GFC Analysis", "🌍 Hansen/GLAD Analysis", "🚜 AAFC Analysis", "📈 Comparison", "ℹ️ About"]
                        )
                        
                        # Use existing analysis code for original geometry
                        render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, tab5, tab6, area_prefix="original")
                    
                    # ===== BUFFER ZONE TAB =====
                    with main_tab2:
                        buffer_tab1, buffer_tab2, buffer_tab3, buffer_tab4, buffer_tab5, buffer_tab6 = st.tabs(
                            ["📍 MapBiomas Analysis", "🌲 Hansen GFC Analysis", "🌍 Hansen/GLAD Analysis", "🚜 AAFC Analysis", "📈 Comparison", "ℹ️ About"]
                        )
                        
                        # Use same analysis code for buffer geometry
                        render_analysis_tabs(buffer_geom, buffer_tab1, buffer_tab2, buffer_tab3, buffer_tab4, buffer_tab5, buffer_tab6,
                                           area_prefix="buffer", buffer_name=st.session_state.current_buffer_for_analysis,
                                           buffer_size=buffer_meta['buffer_size_km'])
                else:
                    # Standard tabs without buffer comparison
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                        ["📍 MapBiomas Analysis", "🌲 Hansen GFC Analysis", "🌍 Hansen/GLAD Analysis", "🚜 AAFC Analysis", "📈 Comparison", "ℹ️ About"]
                    )
                    
                    # Render standard analysis
                    render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, tab5, tab6, area_prefix="original")
        except Exception as e:
            st.error(f"Error processing drawn feature: {e}")
            print(f"Analysis error: {e}")
    else:
        st.info("🎨 Draw a polygon on the map to start analyzing land cover in that area. Use the drawing tools in the top-left of the map.")


print("\n✓ Yvynation App Loaded Successfully")
