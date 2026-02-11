"""
Analysis Tabs Component for Yvynation Platform
Displays comprehensive analysis results for MapBiomas, Hansen, Hansen GFC, AAFC layers
"""

import streamlit as st
import pandas as pd
import ee
from translations import t
from plotting_utils import plot_area_distribution
from main import plot_gains_losses, create_sankey_transitions
from config import MAPBIOMAS_LABELS, HANSEN_DATASETS, HANSEN_OCEAN_MASK


def hansen_histogram_to_dataframe(stats, year):
    """Convert Hansen histogram stats to DataFrame"""
    from config import HANSEN_CONSOLIDATED_MAPPING
    
    # Try different band names for Hansen data
    histogram_data = {}
    for key in ['b1', 'classification', 'VV']:
        if key in stats and isinstance(stats[key], dict):
            histogram_data = stats[key]
            break
    
    # If still empty, try first available key that contains histogram data
    if not histogram_data:
        for key, value in stats.items():
            if isinstance(value, dict) and len(value) > 0:
                histogram_data = value
                break
    
    if not histogram_data:
        print(f"[DEBUG] Hansen {year}: stats keys = {list(stats.keys())}, no histogram data found")
        return pd.DataFrame()
    
    records = []
    
    for class_id_str, count in histogram_data.items():
        try:
            class_id = int(float(class_id_str))
            area_ha = count * 0.09
            
            # Get the class name/description from mapping if available
            class_name = f"Class {class_id}"
            
            records.append({
                "Class_ID": class_id,
                "Class": class_name,
                "Pixels": int(count),
                "Area_ha": round(area_ha, 2)
            })
        except (ValueError, TypeError):
            continue
    
    if records:
        df = pd.DataFrame(records).sort_values("Area_ha", ascending=False)
        return df
    else:
        print(f"[DEBUG] Hansen {year}: histogram_data exists but no valid records")
        return pd.DataFrame()



def aggregate_to_consolidated(df):
    """Consolidate Hansen 256 classes to 12 main classes"""
    from config import HANSEN_CONSOLIDATED_MAPPING
    
    df_copy = df.copy()
    df_copy['Consolidated_Class'] = df_copy['Class_ID'].apply(
        lambda x: HANSEN_CONSOLIDATED_MAPPING.get(x, f"Class {x}")
    )
    
    df_consolidated = df_copy.groupby('Consolidated_Class').agg({
        'Pixels': 'sum',
        'Area_ha': 'sum'
    }).reset_index().sort_values('Area_ha', ascending=False)
    
    return df_consolidated


def get_consolidated_class(class_id):
    """Get consolidated class name for a given Hansen class ID"""
    from config import HANSEN_CONSOLIDATED_MAPPING
    return HANSEN_CONSOLIDATED_MAPPING.get(class_id, f"Class {class_id}")


def summarize_consolidated_stats(df, year=None):
    """Summarize consolidated Hansen statistics"""
    return {
        'total_area_ha': df['Area_ha'].sum(),
        'num_classes': len(df),
        'largest_class': df.iloc[0]['Consolidated_Class'] if len(df) > 0 else "N/A"
    }


def analyze_aafc_geometry(geometry, year, area_name="Area"):
    """Analyze AAFC data for given geometry"""
    try:
        from config import AAFC_LABELS
        
        aafc_collection = ee.ImageCollection("AAFC/ACI")
        image = aafc_collection.filterDate(f"{year}-01-01", f"{year}-12-31").first()
        
        if image is None:
            return None
        
        stats = image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        if not stats:
            return None
        
        # AAFC can have different band names, try to find the histogram data
        histogram_data = {}
        
        # Try common band names
        for key in ['b1', 'classification', 'cropland', 'asters_classification_1']:
            if key in stats and isinstance(stats[key], dict):
                histogram_data = stats[key]
                break
        
        # If still empty, try first available key that contains histogram data
        if not histogram_data:
            for key, value in stats.items():
                if isinstance(value, dict) and len(value) > 0:
                    histogram_data = value
                    break
        
        if not histogram_data:
            print(f"[DEBUG] AAFC {year}: stats keys = {list(stats.keys())}, no histogram data found")
            return None
        
        records = []
        
        for class_id_str, count in histogram_data.items():
            try:
                class_id = int(float(class_id_str))
                class_name = AAFC_LABELS.get(class_id, f"Class {class_id}")
                area_ha = count * 0.09
                
                records.append({
                    "Class_ID": class_id,
                    "Class": class_name,
                    "Pixels": int(count),
                    "Area_ha": round(area_ha, 2)
                })
            except (ValueError, TypeError):
                continue
        
        # Only sort if we have records
        if records:
            df = pd.DataFrame(records).sort_values("Area_ha", ascending=False)
            return df
        else:
            print(f"[DEBUG] AAFC {year}: histogram_data has keys but no valid records. Keys: {list(histogram_data.keys())[:5]}")
            return None
    except Exception as e:
        print(f"AAFC analysis error ({year}): {str(e)[:100]}")
        import traceback
        traceback.print_exc()
        return None


def render_analysis_tabs(geometry, tab1, tab2, tab3, tab4, tab5, tab6, area_prefix="original", buffer_name=None, buffer_size=None):
    """
    Render the complete analysis tab structure for a given geometry.
    Can be used for both original area and buffer zone.
    
    Parameters:
    -----------
    geometry : ee.Geometry
        The geometry to analyze
    tab1, tab2, tab3, tab4, tab5, tab6 : streamlit tabs
        The tab objects to render into
    area_prefix : str
        Prefix for file exports ("original" or "buffer")
    buffer_name : str, optional
        Name of buffer for storage
    buffer_size : int, optional
        Buffer size in km for display
    """
    
    with tab1:
        st.markdown(f"### {t('mapbiomas_header')}")
        if st.session_state.mapbiomas_layers and st.session_state.app.mapbiomas_v9:
            years_to_analyze = [y for y, enabled in st.session_state.mapbiomas_layers.items() if enabled]
            if years_to_analyze:
                st.write(t("analyzing_years", count=len(years_to_analyze)))
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
                                    st.success(t("year_classes_found", year=year, count=len(records)))
                                    
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
                                    st.warning(t("empty_histogram", year=year))
                            else:
                                st.warning(t("no_stats_returned", year=year))
                        except Exception as e:
                            st.error(t("error_analyzing_year", year=year, error=str(e)[:200]))
                            print(f"Full error: {e}")
            else:
                st.info(t("no_mapbiomas_layer"))
        else:
            st.info(t("load_data_mapbiomas"))
    
    with tab2:
        st.markdown(f"### {t('hansen_header')}")
        if st.session_state.hansen_layers and st.session_state.app:
            years_to_analyze = [y for y, enabled in st.session_state.hansen_layers.items() if enabled]
            if years_to_analyze:
                st.write(f"Analyzing {len(years_to_analyze)} year(s) of data...")
                for year in sorted(years_to_analyze):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"**Year {year}**")
                        try:
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
                                    st.info(t("no_data_area"))
                            else:
                                st.info(t("no_data_area"))
                        except Exception as e:
                            st.error(t("error_analyzing_year", year=year, error=str(e)))
            else:
                st.info(t("no_hansen_layer"))
        else:
            st.info(t("load_data_hansen"))
    
    with tab3:
        st.markdown(f"### {t('hansen_gfc_header')}")
        st.caption("Analyze tree cover, loss, and gain from 2000-2024")
        
        # Check if Hansen GFC layers are enabled
        has_gfc_layers = any([
            st.session_state.get('hansen_gfc_tree_cover', False),
            st.session_state.get('hansen_gfc_tree_loss', False),
            st.session_state.get('hansen_gfc_tree_gain', False)
        ])
        
        if not has_gfc_layers:
            st.info(t('add_gfc_layers'))
            st.markdown(f"""
            **{t('gfc_available_layers')}**
            - {t('gfc_layer_tree_cover')}
            - {t('gfc_layer_tree_loss')}
            - {t('gfc_layer_tree_gain')}
            
            {t('gfc_add_from_sidebar')}
            """)
        else:
            # Simple analysis button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Analyzing area: {area_prefix}**")
            with col2:
                if st.button("🔄 Analyze GFC", key=f"gfc_analyze_{area_prefix}"):
                    st.session_state[f'gfc_force_rerun_{area_prefix}'] = True
            
            # Run analysis if button clicked or first time
            session_key = f'hansen_gfc_results_{area_prefix}'
            attempt_key = f'hansen_gfc_analysis_attempted_{area_prefix}'
            
            should_analyze = (
                st.session_state.get(f'gfc_force_rerun_{area_prefix}', False) or
                (attempt_key not in st.session_state)
            )
            
            if should_analyze and attempt_key not in st.session_state:
                st.session_state[attempt_key] = True
                st.session_state[f'gfc_force_rerun_{area_prefix}'] = False
                
                try:
                    from gfc_analysis import analyze_hansen_gfc_geometry
                    gfc_results = analyze_hansen_gfc_geometry(geometry, area_name=f"{area_prefix} area")
                    st.session_state[session_key] = gfc_results if gfc_results else None
                except Exception as e:
                    print(f"[Error] Hansen GFC analysis failed: {e}")
                    import traceback
                    traceback.print_exc()
                    st.session_state[session_key] = None
            
            # Display cached results
            gfc_results = st.session_state.get(session_key)
            
            if gfc_results and isinstance(gfc_results, dict) and len(gfc_results) > 0:
                st.success("✓ Analysis complete!")
                
                # Simple expanders instead of nested tabs
                if 'tree_cover' in gfc_results:
                    with st.expander("🌳 Tree Cover 2000", expanded=True):
                        df_cover = gfc_results['tree_cover']
                        st.markdown(f"#### {t('tree_cover_header')}")
                        st.caption("Percent of canopy cover (0-100%)")
                        
                        total_area = df_cover['Area_ha'].sum()
                        df_cover['Category'] = df_cover['Percent_Cover'].apply(lambda x: 
                            'No Tree Cover (0%)' if x == 0 else
                            'Low Cover (1-25%)' if x <= 25 else
                            'Medium Cover (26-50%)' if x <= 50 else
                            'High Cover (51-75%)' if x <= 75 else
                            'Very High Cover (76-100%)'
                        )
                        
                        df_grouped = df_cover.groupby('Category').agg({
                            'Pixels': 'sum',
                            'Area_ha': 'sum'
                        }).reset_index()
                        df_grouped['Percentage'] = (df_grouped['Area_ha'] / total_area * 100).round(2)
                        
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.dataframe(df_grouped[['Category', 'Area_ha', 'Percentage']], use_container_width=True)
                        with col2:
                            st.metric("Total Area", f"{total_area:,.0f} ha")
                            avg_cover = (df_cover['Percent_Cover'] * df_cover['Area_ha']).sum() / total_area
                            st.metric("Average Cover", f"{avg_cover:.1f}%")
                        
                        csv = df_cover.to_csv(index=False)
                        st.download_button(
                            "📥 Download Tree Cover Data",
                            csv,
                            f"{area_prefix}_tree_cover_2000.csv",
                            "text/csv",
                            key=f"dl_gfc_cover_{area_prefix}_{id(geometry)}"
                        )
                
                if 'tree_loss' in gfc_results:
                    with st.expander("🔥 Tree Loss"):
                        df_loss = gfc_results['tree_loss']
                        st.markdown(f"#### {t('tree_loss_header')}")
                        st.caption("Areas where tree cover was lost (2001-2024)")
                        
                        df_with_loss = df_loss[df_loss['Year_Code'] > 0]
                        
                        if not df_with_loss.empty:
                            total_loss_area = df_with_loss['Area_ha'].sum()
                            total_area = df_loss['Area_ha'].sum()
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Loss", f"{total_loss_area:,.0f} ha")
                            with col2:
                                loss_pct = (total_loss_area / total_area * 100)
                                st.metric("% of Area", f"{loss_pct:.2f}%")
                            with col3:
                                st.metric("Years with Loss", len(df_with_loss))
                            
                            st.markdown("**Loss by Year:**")
                            st.dataframe(df_with_loss[['Year', 'Area_ha', 'Pixels']], use_container_width=True)
                            
                            csv = df_loss.to_csv(index=False)
                            st.download_button(
                                "📥 Download Loss Data",
                                csv,
                                f"{area_prefix}_tree_loss.csv",
                                "text/csv",
                                key=f"dl_gfc_loss_{area_prefix}_{id(geometry)}"
                            )
                        else:
                            st.success(t("no_forest_loss"))
                
                if 'tree_gain' in gfc_results:
                    with st.expander("🌲 Tree Gain"):
                        df_gain = gfc_results['tree_gain']
                        st.markdown(f"#### {t('tree_gain_header')}")
                        st.caption("Areas with forest regrowth or afforestation (2000-2012)")
                        
                        df_with_gain = df_gain[df_gain['Gain_Code'] == 1]
                        total_area = df_gain['Area_ha'].sum()
                        
                        if not df_with_gain.empty:
                            gain_area = df_with_gain['Area_ha'].sum()
                            gain_pct = (gain_area / total_area * 100)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric(t("area_with_gain"), f"{gain_area:,.0f} ha")
                            with col2:
                                st.metric("% of Analyzed Area", f"{gain_pct:.2f}%")
                            
                            st.dataframe(df_gain[['Status', 'Area_ha', 'Pixels']], use_container_width=True)
                            
                            csv = df_gain.to_csv(index=False)
                            st.download_button(
                                "📥 Download Gain Data",
                                csv,
                                f"{area_prefix}_tree_gain.csv",
                                "text/csv",
                                key=f"dl_gfc_gain_{area_prefix}_{id(geometry)}"
                            )
                        else:
                            st.info(t('no_gain_detected'))
            elif gfc_results is None and attempt_key in st.session_state:
                st.warning("No Hansen GFC data found in this area")
            else:
                st.info("Click 'Analyze GFC' button to start analysis")
    
    with tab4:
        st.markdown(f"### {t('aafc_header')}")
        st.caption("Analyze crop and land cover classifications from Canada's Agricultural and Agri-Food dataset")
        
        selected_country = st.session_state.get('selected_country', 'Brazil')
        
        if selected_country == "Canada":
            if st.session_state.get('aafc_layers'):
                years_to_analyze = [y for y, enabled in st.session_state.aafc_layers.items() if enabled]
                if years_to_analyze:
                    st.write(t("aafc_analyzing_years", count=len(years_to_analyze)))
                    for year in sorted(years_to_analyze):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            st.markdown(f"**{t('aafc_year_label', year=year)}**")
                            try:
                                df = analyze_aafc_geometry(geometry, year, area_name=f"{area_prefix} area")
                                
                                if df is not None and not df.empty:
                                    total_area = df['Area_ha'].sum()
                                    num_classes = len(df)
                                    largest_class = df.iloc[0]['Class'] if len(df) > 0 else "N/A"
                                    largest_area = df.iloc[0]['Area_ha'] if len(df) > 0 else 0
                                    
                                    col_a, col_b, col_c = st.columns(3)
                                    with col_a:
                                        st.metric(t("aafc_total_area"), f"{total_area:,.0f} ha")
                                    with col_b:
                                        st.metric(t("aafc_classes_detected"), num_classes)
                                    with col_c:
                                        st.metric(t("aafc_largest_class"), largest_class)
                                    
                                    st.dataframe(df[['Class', 'Pixels', 'Area_ha']], use_container_width=True)
                                    
                                    fig = plot_area_distribution(df, year=year, top_n=15)
                                    st.pyplot(fig, use_container_width=True)
                                    
                                    if buffer_name:
                                        if 'buffer_analysis_results' not in st.session_state:
                                            st.session_state.buffer_analysis_results = {}
                                        if buffer_name not in st.session_state.buffer_analysis_results:
                                            st.session_state.buffer_analysis_results[buffer_name] = {}
                                        st.session_state.buffer_analysis_results[buffer_name][f'aafc_{year}'] = df
                                    
                                    csv = df.to_csv(index=False)
                                    filename = f"{area_prefix}_aafc_{year}.csv"
                                    st.download_button(
                                        label=t("aafc_download_csv", year=year),
                                        data=csv,
                                        file_name=filename,
                                        mime="text/csv",
                                        key=f"dl_{area_prefix}_aafc_{year}_{id(geometry)}"
                                    )
                                    st.success(t("aafc_analysis_complete", year=year))
                                else:
                                    st.warning(t("aafc_no_data_year", year=year))
                            except Exception as e:
                                st.error(t("aafc_analysis_error", year=year, error=str(e)[:200]))
                                print(f"Full AAFC error: {e}")
                else:
                    st.info("Add an AAFC layer from the sidebar to analyze")
            else:
                st.info("Add an AAFC layer from the sidebar to analyze")
        else:
            st.info("🍁 AAFC data is only available for Canada. Select Canada from the country selector to analyze crop inventory.")
    
    with tab5:
        st.markdown("### Multi-Year Comparison")
        
        if st.session_state.mapbiomas_layers and st.session_state.app.mapbiomas_v9:
            mapbiomas_years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            if len(mapbiomas_years) >= 2:
                st.subheader("📊 MapBiomas Change Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    year1 = st.selectbox(
                        "Year 1 (baseline)",
                        options=mapbiomas_years,
                        key=f"mapbiomas_comp_year1_{area_prefix}"
                    )
                with col2:
                    year2 = st.selectbox(
                        "Year 2 (comparison)",
                        options=mapbiomas_years,
                        index=len(mapbiomas_years)-1,
                        key=f"mapbiomas_comp_year2_{area_prefix}"
                    )
                
                if st.button("🔄 Compare MapBiomas Years", width="stretch", key=f"mapbiomas_compare_{area_prefix}"):
                    try:
                        with st.spinner(f"Comparing MapBiomas {year1} vs {year2}..."):
                            band1 = f'classification_{year1}'
                            image1 = st.session_state.app.mapbiomas_v9.select(band1)
                            stats1 = image1.reduceRegion(
                                reducer=ee.Reducer.frequencyHistogram(),
                                geometry=geometry,
                                scale=30,
                                maxPixels=1e9
                            ).getInfo()
                            
                            band2 = f'classification_{year2}'
                            image2 = st.session_state.app.mapbiomas_v9.select(band2)
                            stats2 = image2.reduceRegion(
                                reducer=ee.Reducer.frequencyHistogram(),
                                geometry=geometry,
                                scale=30,
                                maxPixels=1e9
                            ).getInfo()
                            
                            hist1 = stats1.get(band1, {})
                            hist2 = stats2.get(band2, {})
                            
                            if hist1 and hist2:
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
                                
                                transitions = {}
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
        
        if st.session_state.hansen_layers:
            hansen_years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
            if len(hansen_years) >= 2:
                st.subheader("📊 Hansen Change Analysis")
                col1, col2 = st.columns(2)
                with col1:
                    h_year1 = st.selectbox(
                        "Year 1 (baseline)",
                        options=hansen_years,
                        key=f"hansen_comp_year1_{area_prefix}"
                    )
                with col2:
                    h_year2 = st.selectbox(
                        "Year 2 (comparison)",
                        options=hansen_years,
                        index=len(hansen_years)-1,
                        key=f"hansen_comp_year2_{area_prefix}"
                    )
                
                if st.button("🔄 Compare Hansen Years", width="stretch", key=f"hansen_compare_{area_prefix}"):
                    try:
                        with st.spinner(f"Comparing Hansen {h_year1} vs {h_year2}..."):
                            landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
                            
                            hansen1 = ee.Image(HANSEN_DATASETS[str(h_year1)]).updateMask(landmask)
                            stats1 = hansen1.reduceRegion(
                                reducer=ee.Reducer.frequencyHistogram(),
                                geometry=geometry,
                                scale=30,
                                maxPixels=1e9
                            ).getInfo()
                            
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
                                    if st.session_state.use_consolidated_classes:
                                        df1_disp = aggregate_to_consolidated(df1)
                                        df2_disp = aggregate_to_consolidated(df2)
                                    else:
                                        df1_disp = df1
                                        df2_disp = df2
                                    
                                    merge_col = 'Consolidated_Class' if st.session_state.use_consolidated_classes else 'Class'
                                    df1_merge = df1_disp.rename(columns={"Area_ha": f"{h_year1}_ha"})[[merge_col, f"{h_year1}_ha"]]
                                    df2_merge = df2_disp.rename(columns={"Area_ha": f"{h_year2}_ha"})[[merge_col, f"{h_year2}_ha"]]
                                    
                                    df_comp = df1_merge.merge(df2_merge, on=merge_col, how="outer").fillna(0)
                                    df_comp["Change (ha)"] = df_comp[f"{h_year2}_ha"] - df_comp[f"{h_year1}_ha"]
                                    df_comp = df_comp.sort_values("Change (ha)", ascending=False, key=abs)
                                    
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
        
        st.divider()
        st.markdown("### 📊 Comparison Results Summary")
        
        col_mb, col_hansen = st.columns(2)
        
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
                    with col_right:
                        fig = plot_area_distribution(result['df_year2'], year=result['year2'], top_n=10)
                        st.pyplot(fig, width="stretch")
                
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
                                st.session_state.mapbiomas_transitions = result.get('transitions')
                        except Exception as e:
                            st.warning(f"Could not display Sankey: {str(e)[:50]}")
                    else:
                        st.info("No transition data available")
                
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
                    with col_right:
                        fig = plot_area_distribution(result['df2_disp'], year=result['year2'], top_n=10)
                        st.pyplot(fig, width="stretch")
                
                with st.expander("🎯 Gains & Losses (km²)"):
                    from plotting_utils import calculate_gains_losses
                    try:
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
                                st.session_state.hansen_transitions = result.get('transitions')
                        except Exception as e:
                            st.warning(f"Could not display Sankey: {str(e)[:50]}")
                    else:
                        st.info("No transition data available")
                
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
    
    with tab6:
        st.markdown("### 📚 About These Datasets")
        
        with st.expander("🌱 MapBiomas Collection 9 Info"):
            st.markdown("""
            **MapBiomas** is Brazil's primary land cover classification:
            - **Coverage**: All of Brazil (1985-2023)
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 62 land cover types
            - **Accuracy**: ~90% (varies by region and class)
            - Includes: Forests, grasslands, agriculture, urban areas
            - Annual updates
            
            [Learn more](https://mapbiomas.org/)
            """)
        
        with st.expander("🌍 Hansen/GLAD Forest Change Info"):
            st.markdown("""
            **Hansen Global Forest Change** tracks deforestation worldwide:
            - **Coverage**: Global (all land areas)
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 256 categories combining multiple dimensions:
              - Tree canopy presence/absence
              - Forest loss year (2000-2020)
              - Forest gain (2000-2012)
              - Land use type
            - **Best for**: Forest change detection and monitoring
            - Consolidation: Can view as 12 simplified classes
            
            [Learn more](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2024_v1_12)
            """)
        
        with st.expander("🚜 Hansen GFC Advanced Info"):
            st.markdown("""
            **Hansen Global Forest Change** provides detailed forest metrics:
            - **Tree Cover 2000**: Tree canopy density for year 2000 (0-100%)
            - **Tree Loss**: Annual forest loss detection from 2001-2024
            - **Tree Gain**: Forest regrowth identification from 2000-2012
            - **Global Coverage**: Available for all land areas worldwide
            - **30-meter Resolution**: Detailed spatial analysis
            - **Source**: University of Maryland, based on Landsat imagery
            
            [Learn more](https://developers.google.com/earth-engine/datasets/catalog/UMD_hansen_global_forest_change_2024_v1_12)
            """)
        
        with st.expander("🚜 AAFC Annual Crop Inventory Info"):
            st.markdown("""
            **AAFC** is Canada's agricultural land cover dataset:
            - Annual crop and land cover classification
            - Coverage: 2009-2024
            - Resolution: 30 meters
            - 75+ crop and land cover classes
            - Includes: Grains, oilseeds, pulses, vegetables, fruits, grassland, forest, water
            - Updated annually by Agriculture and Agri-Food Canada
            
            [Learn more](https://developers.google.com/earth-engine/datasets/catalog/AAFC_ACI)
            """)
