"""
Hansen/GLAD Analysis Module
Handles all Hansen/GLAD global land cover analysis
"""

import streamlit as st
import ee
import pandas as pd
import matplotlib.pyplot as plt
from config import HANSEN_DATASETS, HANSEN_PALETTE, HANSEN_COLOR_MAP


def get_hansen_color(class_id):
    """Get color for Hansen class ID from the palette"""
    if isinstance(class_id, (int, float)):
        class_id = int(class_id)
    
    # Map palette index to color
    if 0 <= class_id < len(HANSEN_PALETTE):
        return f"#{HANSEN_PALETTE[class_id]}"
    
    # Fallback for unknown classes - use gray
    return "#808080"


def hansen_histogram_to_dataframe(hist, year):
    """Convert Hansen frequency histogram to DataFrame"""
    if hist and 'b1' in hist:
        data = hist['b1']
        classes = {
            0: "No Data", 1: "Water", 2: "Evergreen Needleleaf", 
            3: "Evergreen Broadleaf", 4: "Deciduous Needleleaf", 5: "Deciduous Broadleaf",
            6: "Mixed Forest", 7: "Closed Shrublands", 8: "Open Shrublands", 
            9: "Woody Savannas", 10: "Savannas", 11: "Grasslands",
            12: "Permanent Wetlands", 13: "Croplands", 14: "Urban & Built-up",
            15: "Cropland/Natural", 16: "Snow & Ice", 17: "Barren"
        }
        records = []
        for class_id, count in data.items():
            records.append({
                "Class_ID": int(class_id),
                "Class": classes.get(int(class_id), f"Class {class_id}"),
                "Pixels": count,
                "Area_ha": count * 0.9  # 30m pixels ≈ 0.9 ha
            })
        return pd.DataFrame(records).sort_values("Area_ha", ascending=False)
    return pd.DataFrame()


def render_hansen_area_analysis():
    """Render Hansen drawn area analysis section"""
    
    if not st.session_state.hansen_drawn_areas:
        st.info("👈 Draw an area on the map to begin analysis")
        return
    
    st.success(f"✅ {len(st.session_state.hansen_drawn_areas)} drawing(s) captured")
    
    # Ensure selected area exists
    area_keys = list(st.session_state.hansen_drawn_areas.keys())
    if st.session_state.hansen_selected_drawn_area not in area_keys:
        st.session_state.hansen_selected_drawn_area = area_keys[0]
    
    # Select which drawn area to analyze
    col_select, col_delete = st.columns([3, 1])
    with col_select:
        selected_area = st.selectbox(
            "Select drawn area to analyze",
            area_keys,
            index=area_keys.index(st.session_state.hansen_selected_drawn_area),
            key="hansen_area_select",
            on_change=lambda: st.session_state.update({"hansen_selected_drawn_area": st.session_state.hansen_area_select})
        )
    
    with col_delete:
        if st.button("🗑️ Clear All", key="clear_drawn_hansen"):
            st.session_state.hansen_drawn_areas = {}
            st.session_state.hansen_drawn_area_count = 0
            st.session_state.hansen_selected_drawn_area = None
            st.rerun()
    
    try:
        geom_data = st.session_state.hansen_drawn_areas[st.session_state.hansen_selected_drawn_area]
        coords = geom_data.get('coordinates', [])
        
        if coords:
            # Create EE geometry from polygon
            geom = ee.Geometry.Polygon(coords[0] if isinstance(coords[0][0], list) else coords)
            
            col_year, col_btn = st.columns([2, 1])
            with col_year:
                hansen_year = st.selectbox(
                    "Select Year", 
                    ["2000", "2005", "2010", "2015", "2020"],
                    index=4,
                    key="year_hansen_drawn"
                )
            
            with col_btn:
                analyze_btn = st.button("📍 Analyze & Zoom", key="btn_hansen_drawn", use_container_width=True)
            
            if analyze_btn and st.session_state.hansen_selected_drawn_area:
                with st.spinner("Analyzing your drawn area with Hansen data..."):
                    try:
                        # Load Hansen data
                        hansen_image = ee.Image(HANSEN_DATASETS[hansen_year])
                        
                        # Get statistics from drawn area
                        stats = hansen_image.reduceRegion(
                            reducer=ee.Reducer.frequencyHistogram(),
                            geometry=geom,
                            scale=30,
                            maxPixels=1e9
                        ).getInfo()
                        
                        # Convert Hansen stats to DataFrame
                        df_hansen = hansen_histogram_to_dataframe(stats, hansen_year)
                        
                        # Store for visualization
                        st.session_state.hansen_area_result = df_hansen
                        st.session_state.hansen_area_year = hansen_year
                        st.session_state.last_analyzed_geom = geom
                        st.session_state.last_analyzed_name = "Your Drawn Area"
                                                # Store the polygon coordinates for drawing on map
                        st.session_state.hansen_drawn_polygon_coords = coords
                                                # Calculate bounds and set zoom flag
                        bounds = geom.bounds().getInfo()
                        st.session_state.hansen_zoom_bounds = bounds
                        st.session_state.hansen_should_zoom_to_feature = True
                        
                        st.success(f"✅ Hansen {hansen_year} data retrieved for your area")
                        
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")
        
        # Display Hansen area results if available
        if st.session_state.hansen_area_result is not None:
            st.divider()
            st.markdown(f"#### 📊 Hansen Land Cover Distribution ({st.session_state.hansen_area_year})")
            
            # Create visualization with class-specific colors
            fig, ax = plt.subplots(figsize=(10, 6))
            top_classes = st.session_state.hansen_area_result.head(15)
            
            # Get colors for each class
            colors = [get_hansen_color(class_id) for class_id in top_classes['Class_ID']]
            
            ax.barh(top_classes['Class'], top_classes['Area_ha'], color=colors)
            ax.set_xlabel('Area (hectares)')
            ax.set_ylabel('Land Cover Class')
            ax.set_title(f'Hansen {st.session_state.hansen_area_year} Land Cover Distribution')
            ax.invert_yaxis()
            plt.tight_layout()
            st.pyplot(fig)
            
            st.markdown("#### 📋 Detailed Statistics")
            st.dataframe(st.session_state.hansen_area_result, width="stretch")
            st.success("✅ View the drawn area on the map!")
            
    except Exception as e:
        st.error(f"Error: {e}")
            



def render_hansen_multiyear_analysis():
    """Render Hansen multi-year snapshot comparison"""
    
    if st.session_state.last_analyzed_geom is None:
        st.info("👈 First, analyze a drawn area above")
        return
    
    st.info(f"📍 Analyzing: **{st.session_state.last_analyzed_name}**")
    
    # Initialize year session state if needed
    if "hansen_start_year_current" not in st.session_state:
        st.session_state.hansen_start_year_current = 2000
    if "hansen_end_year_current" not in st.session_state:
        st.session_state.hansen_end_year_current = 2020
    
    years_list = [2000, 2005, 2010, 2015, 2020]
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.selectbox(
            "Start Year", 
            years_list, 
            index=years_list.index(st.session_state.hansen_start_year_current),
            key="hansen_start_year_current"
        )
    with col2:
        end_year = st.selectbox(
            "End Year", 
            years_list, 
            index=years_list.index(st.session_state.hansen_end_year_current),
            key="hansen_end_year_current"
        )
    
    if st.button("Compare Snapshots", width="stretch", key="btn_hansen_multiyear"):
        if start_year == end_year:
            st.warning("⚠️ Please select different start and end years")
            return
        with st.spinner(f"Comparing Hansen {start_year} and {end_year}..."):
            try:
                ee_module = st.session_state.ee_module
                geom = st.session_state.last_analyzed_geom
                
                # Get Hansen data for both years
                hansen_start_image = ee.Image(HANSEN_DATASETS[str(start_year)])
                hansen_end_image = ee.Image(HANSEN_DATASETS[str(end_year)])
                
                # Calculate frequency distribution for each year
                start_histogram = hansen_start_image.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geom,
                    scale=30,
                    maxPixels=1e13
                ).getInfo()
                
                end_histogram = hansen_end_image.reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geom,
                    scale=30,
                    maxPixels=1e13
                ).getInfo()
                
                # Convert to DataFrames
                area_start = hansen_histogram_to_dataframe(start_histogram, start_year)
                area_end = hansen_histogram_to_dataframe(end_histogram, end_year)
                
                # Store results
                st.session_state.multiyear_results = {
                    "area_start": area_start,
                    "area_end": area_end
                }
                st.session_state.multiyear_start_year = start_year
                st.session_state.multiyear_end_year = end_year
                
                st.success(f"✅ Comparison complete for {start_year}-{end_year}")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    
    # Display comparison results
    if st.session_state.multiyear_results:
        st.markdown(f"#### 🌍 Land Cover Distribution Comparison ({st.session_state.multiyear_start_year} vs {st.session_state.multiyear_end_year})")
        
        try:
            area_start = st.session_state.multiyear_results["area_start"]
            area_end = st.session_state.multiyear_results["area_end"]
            
            # Create comparison visualization with class-specific colors
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # Start year
            top_start = area_start.head(10)
            colors_start = [get_hansen_color(class_id) for class_id in top_start['Class_ID']]
            ax1.barh(top_start["Class"], top_start["Area_ha"], color=colors_start)
            ax1.set_xlabel("Area (hectares)")
            ax1.set_title(f"{st.session_state.multiyear_start_year}")
            ax1.invert_yaxis()
            
            # End year
            top_end = area_end.head(10)
            colors_end = [get_hansen_color(class_id) for class_id in top_end['Class_ID']]
            ax2.barh(top_end["Class"], top_end["Area_ha"], color=colors_end)
            ax2.set_xlabel("Area (hectares)")
            ax2.set_title(f"{st.session_state.multiyear_end_year}")
            ax2.invert_yaxis()
            
            plt.tight_layout()
            st.pyplot(fig)
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


def render_hansen_change_analysis():
    """Render Hansen change detection"""
    
    if st.session_state.multiyear_results is None:
        st.info("Run 'Compare Hansen Snapshots' first")
        return
    
    results = st.session_state.multiyear_results
    
    # Hansen class names mapping
    hansen_classes = {
        0: "No Data", 1: "Water", 2: "Evergreen Needleleaf", 
        3: "Evergreen Broadleaf", 4: "Deciduous Needleleaf", 5: "Deciduous Broadleaf",
        6: "Mixed Forest", 7: "Closed Shrublands", 8: "Open Shrublands", 
        9: "Woody Savannas", 10: "Savannas", 11: "Grasslands",
        12: "Permanent Wetlands", 13: "Croplands", 14: "Urban & Built-up",
        15: "Cropland/Natural", 16: "Snow & Ice", 17: "Barren"
    }
    
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
        
        # Change visualization with class-specific colors
        st.markdown("#### 📊 Largest Changes")
        top_changes = change_df.head(10)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        # Get class names and colors for visualization
        class_names = [hansen_classes.get(int(class_id), f"Class {class_id}") for class_id in top_changes.index]
        colors = [get_hansen_color(class_id) for class_id in top_changes.index]
        
        ax.barh(range(len(top_changes)), top_changes["Change (ha)"], color=colors)
        ax.set_yticks(range(len(top_changes)))
        ax.set_yticklabels(class_names)
        ax.set_xlabel("Change (hectares)")
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("Results format not recognized")
