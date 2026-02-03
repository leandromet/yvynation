"""
Map components for Yvynation app.
Handles map creation, layer management, and display.
"""

import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from map_manager import create_base_map, add_territories_layer
from ee_layers import add_mapbiomas_layer, add_hansen_layer
from config import MAPBIOMAS_PALETTE, HANSEN_PALETTE
import ee


def build_and_display_map():
    """
    Build the interactive map with all current layers and return map data.
    
    Returns:
    --------
    map_data : dict
        Data from st_folium containing drawn features
    """
    
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
                    opacity=0.8,
                    use_consolidated=st.session_state.use_consolidated_classes
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

    # Add analyzed data layer if available
    if st.session_state.add_analysis_layer_to_map and st.session_state.territory_analysis_image and st.session_state.territory_geom:
        try:
            analysis_image = st.session_state.territory_analysis_image
            territory_geom = st.session_state.territory_geom
            
            # Get visualization parameters based on the SOURCE that created this image
            source_for_image = st.session_state.get('territory_analysis_source', st.session_state.territory_source)
            if source_for_image == "MapBiomas":
                vis_params = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
                layer_name = f"MapBiomas Analysis ({int(st.session_state.territory_year)})"
            else:  # Hansen/GLAD or any other source
                vis_params = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
                layer_name = f"Hansen Analysis ({int(st.session_state.territory_year)})"
            
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
                    
                    # Get visualization parameters for year2 based on ITS source
                    source_for_image_year2 = st.session_state.get('territory_analysis_source_year2', st.session_state.territory_source)
                    if source_for_image_year2 == "MapBiomas":
                        vis_params_year2 = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
                    else:  # Hansen/GLAD
                        vis_params_year2 = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
                    
                    map_id2 = analysis_image_year2.getMapId(vis_params_year2)
                    layer_name2 = f"{source_for_image_year2} Analysis ({int(st.session_state.territory_year2)})"
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

    # Display the map and capture drawing data
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
        return map_data
    
    except Exception as e:
        st.warning(f"Map display error: {e}")
        print(f"Error displaying map: {e}")
        return None


def process_drawn_features(map_data):
    """
    Process drawn features from map and update session state.
    
    Parameters:
    -----------
    map_data : dict
        Data from st_folium
    """
    if map_data:
        # Capture drawn features from the map
        if "all_drawings" in map_data and map_data["all_drawings"]:
            # Store all captured drawings
            st.session_state.all_drawn_features = map_data["all_drawings"]
            st.session_state.last_drawn_feature = map_data["all_drawings"][-1]
            
            # Show success message with count
            st.success(f"✓ Captured {len(map_data['all_drawings'])} polygon(s). Select one below to analyze.")
        elif "last_active_drawing" in map_data and map_data["last_active_drawing"]:
            if map_data["last_active_drawing"] not in st.session_state.all_drawn_features:
                st.session_state.all_drawn_features.append(map_data["last_active_drawing"])
            st.session_state.last_drawn_feature = map_data["last_active_drawing"]
            st.success("✓ Polygon captured. Scroll down to analyze.")


def render_polygon_selector():
    """Render the polygon selector UI if multiple drawings exist."""
    if st.session_state.all_drawn_features:
        st.divider()
        st.subheader("🎨 Select Polygon to Analyze")
        
        # Create labels for each polygon
        polygon_labels = []
        for idx, feature in enumerate(st.session_state.all_drawn_features):
            try:
                geom = feature.get('geometry', {})
                geom_type = geom.get('type', 'Unknown')
                coords = geom.get('coordinates', [[]])
                if geom_type == 'Polygon' and coords:
                    # Get bounding box
                    all_lons = [c[0] for ring in coords for c in ring]
                    all_lats = [c[1] for ring in coords for c in ring]
                    if all_lons and all_lats:
                        bbox = f"[{min(all_lats):.2f}, {min(all_lons):.2f}, {max(all_lats):.2f}, {max(all_lons):.2f}]"
                    else:
                        bbox = "N/A"
                    polygon_labels.append(f"Polygon {idx+1} - {geom_type} - Bounds: {bbox}")
                else:
                    polygon_labels.append(f"Polygon {idx+1} - {geom_type}")
            except:
                polygon_labels.append(f"Polygon {idx+1}")
        
        selected_idx = st.selectbox(
            "Choose a polygon to analyze:",
            options=range(len(st.session_state.all_drawn_features)),
            format_func=lambda i: polygon_labels[i],
            key="polygon_selector"
        )
        
        if selected_idx is not None:
            st.session_state.selected_feature_index = selected_idx
            st.session_state.last_drawn_feature = st.session_state.all_drawn_features[selected_idx]
            st.info(f"✓ Selected Polygon {selected_idx + 1} for analysis")


def render_layer_reference_guide():
    """Render the layer reference guide with legends."""
    st.divider()
    with st.expander("📚 Layer Reference Guide - legends", expanded=False):

         # Indigenous Territories Legend
        st.markdown("### 📍 Indigenous Lands & Territories")
        st.markdown(
            "<div style='display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px;'>"
            "<span><span style='color: #4B0082; font-size: 16px;'>■</span> Indigenous Territories</span>"
            "<span><span style='color: #FF0000; font-size: 16px;'>■</span> Selected Territory</span>"
            "<span><span style='color: #0033FF; font-size: 16px;'>■</span> Drawn Polygon</span>"
            "</div>",
            unsafe_allow_html=True
        )
        # MapBiomas Legend
        st.markdown("### 🌱 MapBiomas Land Cover Classes")
        mapbiomas_legend_html = "<div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>"
        mapbiomas_legend_data = [
            ("Forest", "#1f8d49"),
            ("Savanna", "#7dc975"),
            ("Mangrove", "#04381d"),
            ("Wetland", "#519799"),
            ("Grassland", "#d6bc74"),
            ("Pasture", "#edde8e"),
            ("Agriculture", "#e974ed"),
            ("Sugarcane", "#db7093"),
            ("Urban", "#d4271e"),
            ("Water", "#2532e4"),
        ]
        for label, color in mapbiomas_legend_data:
            mapbiomas_legend_html += f"<span><span style='color: {color}; font-size: 16px;'>■</span> {label}</span>"
        mapbiomas_legend_html += "</div>"
        st.markdown(mapbiomas_legend_html, unsafe_allow_html=True)
        
        # Hansen Consolidated Legend
        st.markdown("### 🌍 Hansen Global Forest Change Classes")
        hansen_legend_html = "<div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>"
        hansen_legend_data = [
            ("Dense Tree Cover", "#1F8040"),
            ("Open Tree Cover", "#90C090"),
            ("Dense Short Vegetation", "#B8D4A8"),
            ("Unvegetated", "#D4D4A8"),
            ("Tree Gain", "#4CAF50"),
            ("Tree Loss", "#E53935"),
            ("Cropland", "#FFD700"),
            ("Built-up", "#FF6B35"),
            ("Water", "#2196F3"),
        ]
        for label, color in hansen_legend_data:
            hansen_legend_html += f"<span><span style='color: {color}; font-size: 16px;'>■</span> {label}</span>"
        hansen_legend_html += "</div>"
        st.markdown(hansen_legend_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Basemaps**")
            st.caption("""
            - 🗺️ OpenStreetMap
            - 🛰️ Google Maps (default)
            - 🛰️ Google Satellite
            - 🛣️ ArcGIS Street
            - 🛰️ ArcGIS Satellite
            - ⛰️ ArcGIS Terrain
            """)
            
            st.markdown("**Controls**")
            st.caption("""
            - ⌗ Layer Control: top-right corner
            - ✏️ Drawing Tools: top-left corner
            - 🎨 Opacity: Adjust in sidebar
            """)
        
        with col2:
            st.markdown("**Data Layers Overview**")
            st.caption("""
            - 🌱 MapBiomas: Brazilian land cover (1985-2023)
            - 🌍 Hansen: Global forest change (2000-2020)
            - 📍 Indigenous Territories
            """)
