"""
Map components for Yvynation app.
Handles map creation, layer management, and display.
"""

import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from map_manager import create_base_map, add_territories_layer
from ee_layers import (
    add_mapbiomas_layer, 
    add_hansen_layer, 
    add_hansen_gfc_tree_cover,
    add_hansen_gfc_tree_loss,
    add_hansen_gfc_tree_gain,
    add_aafc_layer
)
from config import MAPBIOMAS_PALETTE, HANSEN_PALETTE
from buffer_utils import add_buffer_to_session_state, add_buffer_to_polygon_list
from translations import t
import ee
import traceback


def build_and_display_map():
    """
    Build the interactive map with all current layers and return map data.
    Uses a single global map that pans/zooms - no separate Brazil/Canada maps.
    Preserves user's current map view (center, zoom).
    
    Returns:
    --------
    map_data : dict
        Data from st_folium containing drawn features
    """
    
    # Get last known map view state or use default
    last_view = st.session_state.get('last_map_view', None)
    if last_view and 'center' in last_view:
        center_lat, center_lon = last_view['center']
        zoom_level = last_view.get('zoom', 3)
    else:
        center_lat, center_lon = 0, 0
        zoom_level = 3
    
    # Always build map from scratch but preserve user's view
    display_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_level,
        tiles="OpenStreetMap"
    )
    
    # Add basemap options
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(display_map)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Street',
        overlay=False,
        control=True
    ).add_to(display_map)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Satellite',
        overlay=False,
        control=True
    ).add_to(display_map)

    # Add territories
    if st.session_state.data_loaded and st.session_state.app:
        result = add_territories_layer(
            display_map,
            st.session_state.app.territories,
            opacity=0.7
        )
        if result is not None:
            display_map = result

    # Add stored MapBiomas layers
    if st.session_state.data_loaded and st.session_state.app:
        for year in st.session_state.mapbiomas_layers:
            if st.session_state.mapbiomas_layers[year]:
                result = add_mapbiomas_layer(
                    display_map,
                    st.session_state.app.mapbiomas_v9,
                    year,
                    opacity=0.8
                )
                if result is not None:
                    display_map = result

    # Add stored Hansen layers
    if st.session_state.data_loaded and st.session_state.app:
        for year in st.session_state.hansen_layers:
            if st.session_state.hansen_layers[year]:
                result = add_hansen_layer(
                    display_map,
                    year,
                    opacity=0.8,
                    use_consolidated=st.session_state.use_consolidated_classes
                )
                if result is not None:
                    display_map = result
    
    # Add Hansen Global Forest Change layers
    if st.session_state.get('hansen_gfc_tree_cover', False):
        result = add_hansen_gfc_tree_cover(display_map, opacity=0.8, shown=True)
        if result is not None:
            display_map = result
    
    if st.session_state.get('hansen_gfc_tree_loss', False):
        result = add_hansen_gfc_tree_loss(display_map, opacity=0.8, shown=True)
        if result is not None:
            display_map = result
    
    if st.session_state.get('hansen_gfc_tree_gain', False):
        result = add_hansen_gfc_tree_gain(display_map, opacity=0.8, shown=True)
        if result is not None:
            display_map = result

    # Add AAFC Annual Crop Inventory layers (Canada)
    if st.session_state.get('aafc_layers'):
        for year in st.session_state.aafc_layers:
            if st.session_state.aafc_layers[year]:
                result = add_aafc_layer(display_map, year=year, opacity=0.8, shown=True)
                if result is not None:
                    display_map = result

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
                name=t("territory_layer", territory_name=territory_name),
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
                print(f"[Map] Territory layer added: {territory_name}")
        
        except Exception as e:
            print(f"[Error] Adding territory layer failed: {e}")

    # Add buffer boundary layer if requested
    if st.session_state.add_buffer_layer_to_map and st.session_state.buffer_geom_for_display and st.session_state.buffer_layer_name:
        try:
            buffer_geom = st.session_state.buffer_geom_for_display
            buffer_name = st.session_state.buffer_layer_name
            
            # Get buffer GeoJSON directly
            buffer_geojson = buffer_geom.getInfo()
            
            # Create a GeoJSON layer with distinct styling (blue for buffer)
            folium.GeoJson(
                data=buffer_geojson,
                name=t("buffer_geojson", buffer_name=buffer_name),
                style_function=lambda x: {
                    'fillColor': '#0000FF',
                    'color': '#0000FF',
                    'weight': 2,
                    'opacity': 0.7,
                    'fillOpacity': 0.15
                },
                overlay=True,
                control=True,
                highlight_function=lambda x: {
                    'fillColor': '#6B6BFF',
                    'color': '#6B6BFF',
                    'weight': 3,
                    'opacity': 1.0,
                    'fillOpacity': 0.2
                }
            ).add_to(display_map)
            
            # Zoom to buffer bounds
            bounds_info = buffer_geom.bounds().getInfo()
            if bounds_info and bounds_info.get('coordinates'):
                coords = bounds_info['coordinates'][0]
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                sw = [min(lats), min(lons)]
                ne = [max(lats), max(lons)]
                display_map.fit_bounds([sw, ne])
                print(f"[Map] Buffer layer added: {buffer_name}")
        
        except Exception as e:
            print(f"[Error] Adding buffer layer failed: {e}")

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

    # Add buffer zones as visible layers
    if 'buffer_geometries' in st.session_state and st.session_state.buffer_geometries:
        for buffer_name, buffer_geom in st.session_state.buffer_geometries.items():
            try:
                # Get buffer GeoJSON - safely convert ee.Geometry to GeoJSON
                if buffer_geom is not None:
                    try:
                        buffer_geojson = buffer_geom.getInfo()
                    except Exception as geom_error:
                        print(f"[Warning] Could not convert buffer {buffer_name} to GeoJSON: {geom_error}")
                        continue
                    
                    # Add buffer as GeoJSON layer with distinct styling
                    folium.GeoJson(
                        data=buffer_geojson,
                        name=f"Buffer: {buffer_name}",
                        style_function=lambda x: {
                            'fillColor': '#00BFFF',
                            'color': '#0080FF',
                            'weight': 2,
                            'opacity': 0.8,
                            'fillOpacity': 0.15
                        },
                        overlay=True,
                        control=True,
                        highlight_function=lambda x: {
                            'fillColor': '#87CEEB',
                            'color': '#4169E1',
                            'weight': 3,
                            'opacity': 1.0,
                            'fillOpacity': 0.25
                        }
                    ).add_to(display_map)
                    
                    print(f"[Map] Buffer layer added: {buffer_name}")
            except Exception as e:
                print(f"[Error] Adding buffer layer failed for {buffer_name}: {e}")
                import traceback
                traceback.print_exc()

    # Add layer control with enhanced styling
    layer_control = folium.LayerControl(position='topright', collapsed=False)
    layer_control.add_to(display_map)

    # Re-add previously drawn features as GeoJSON layers
    if st.session_state.all_drawn_features:
        for idx, feature in enumerate(st.session_state.all_drawn_features):
            try:
                props = feature.get('properties', {})
                is_buffer = props.get('type') == 'external_buffer'
                
                # Define styling before using in lambda
                if is_buffer:
                    # Buffer zone - light blue ring
                    color = '#00BFFF'
                    fill_color = '#00BFFF'
                    layer_name = props.get('name', f"Buffer {idx+1}")
                    highlight_color = '#87CEEB'
                    highlight_border = '#4169E1'
                else:
                    # Regular polygon - blue
                    color = '#0033FF'
                    fill_color = '#0033FF'
                    layer_name = f"Polygon {idx+1}"
                    highlight_color = '#FF6B6B'
                    highlight_border = '#FF0000'
                
                # Create style function with closure
                def make_style_fn(col, fcol):
                    return lambda x: {
                        'fillColor': fcol,
                        'color': col,
                        'weight': 2,
                        'opacity': 0.8,
                        'fillOpacity': 0.25
                    }
                
                def make_highlight_fn(hcol, hborder):
                    return lambda x: {
                        'fillColor': hcol,
                        'color': hborder,
                        'weight': 3,
                        'opacity': 1.0,
                        'fillOpacity': 0.4
                    }
                
                folium.GeoJson(
                    data=feature,
                    name=layer_name,
                    style_function=make_style_fn(color, fill_color),
                    overlay=True,
                    control=True,
                    highlight_function=make_highlight_fn(highlight_color, highlight_border)
                ).add_to(display_map)
            except Exception as e:
                print(f"[Warning] Could not re-add drawn feature {idx}: {e}")
        
        # Fit map bounds to show drawn features
        try:
            first_feature = st.session_state.all_drawn_features[0]
            geom = first_feature.get('geometry', {})
            if geom.get('type') == 'Polygon' and geom.get('coordinates'):
                coords = geom['coordinates'][0]
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                if lons and lats:
                    sw = [min(lats), min(lons)]
                    ne = [max(lats), max(lons)]
                    display_map.fit_bounds([sw, ne])
        except Exception as e:
            print(f"[Warning] Could not fit bounds to drawn features: {e}")

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
    st.subheader(t("interactive_map"))

    # Show layer legend
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(t("draw_instruction"))
    with col2:
        # Quick layer summary
        active_layers = 0
        if st.session_state.data_loaded:
            active_layers = 1  # Basemap
            active_layers += len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            active_layers += len([y for y, v in st.session_state.hansen_layers.items() if v])
            active_layers += len([y for y, v in st.session_state.get('aafc_layers', {}).items() if v])
        st.metric(t("active_layers"), active_layers)

    try:
        # Store map object and territories for export functionality
        st.session_state.map_object = display_map
        if st.session_state.data_loaded and st.session_state.app:
            st.session_state.territories_geojson = st.session_state.app.territories.getInfo()
            st.session_state.territory_style = lambda x: {
                'fillColor': '#4B0082',
                'color': '#4B0082',
                'weight': 1,
                'opacity': 0.6,
                'fillOpacity': 0.1
            }
        
        # Display map and capture data
        map_data = st_folium(display_map, width="stretch", height=600)
        
        # Store current map view state for persistence across reruns
        if map_data:
            try:
                if 'center' in map_data:
                    center = map_data.get('center')
                    zoom = map_data.get('zoom', 3)
                    st.session_state.last_map_view = {
                        'center': (center.get('lat', 0), center.get('lng', 0)),
                        'zoom': zoom
                    }
            except Exception as view_error:
                print(f"[Debug] Could not capture map view: {view_error}")
        
        return map_data
    
    except Exception as e:
        st.warning(t("map_display_error", error=str(e)[:200]))
        print(f"Error displaying map: {e}")
        import traceback
        traceback.print_exc()
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
            st.success(t("captured_polygons", count=len(map_data['all_drawings'])))
        elif "last_active_drawing" in map_data and map_data["last_active_drawing"]:
            if map_data["last_active_drawing"] not in st.session_state.all_drawn_features:
                st.session_state.all_drawn_features.append(map_data["last_active_drawing"])
            st.session_state.last_drawn_feature = map_data["last_active_drawing"]
            st.success(t("polygon_captured"))


def render_polygon_selector():
    """Render the polygon selector UI if multiple drawings exist."""
    if st.session_state.all_drawn_features:
        st.divider()
        st.subheader(t("select_polygon"))
        
        # Create labels for each polygon
        polygon_labels = []
        for idx, feature in enumerate(st.session_state.all_drawn_features):
            try:
                # Check if this is a buffer
                props = feature.get('properties', {})
                if props.get('type') == 'external_buffer':
                    # This is a buffer - use its name directly
                    buffer_name = props.get('name', t("buffer_label", number=idx+1))
                    polygon_labels.append(f"🔵 {buffer_name}")
                    continue
                
                # Regular polygon - create label from geometry
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
                    polygon_labels.append(t("polygon_bounds", number=idx+1, type=geom_type, bounds=bbox))
                else:
                    polygon_labels.append(t("polygon_bounds", number=idx+1, type=geom_type, bounds="N/A"))
            except:
                polygon_labels.append(t("buffer_label", number=idx+1))
        
        selected_idx = st.selectbox(
            t("choose_polygon"),
            options=range(len(st.session_state.all_drawn_features)),
            format_func=lambda i: polygon_labels[i],
            key=f"polygon_selector_{st.session_state.get('_current_render_id', '')}"
        )
        
        if selected_idx is not None:
            st.session_state.selected_feature_index = selected_idx
            st.session_state.last_drawn_feature = st.session_state.all_drawn_features[selected_idx]
            
            # Check if selected is a buffer
            selected_feature = st.session_state.all_drawn_features[selected_idx]
            is_buffer = selected_feature.get('properties', {}).get('type') == 'external_buffer'
            
            if is_buffer:
                buffer_name = selected_feature.get('properties', {}).get('name', '')
                st.info(t("selected_buffer", buffer_name=buffer_name))
            else:
                st.info(t("selected_polygon", number=selected_idx + 1))
                
                # Add buffer creation UI for non-buffer polygons
                st.divider()
                st.markdown("**" + t("buffer_zone_desc") + "**")
                st.caption(t("buffer_ring_help"))
                
                # Buffer compare mode toggle
                render_id = st.session_state.get('_current_render_id', '')
                buffer_compare = st.checkbox(
                    t("buffer_comparison"),
                    value=st.session_state.buffer_compare_mode,
                    help=t("compare_help"),
                    key=f"polygon_buffer_compare_toggle_{render_id}"
                )
                st.session_state.buffer_compare_mode = buffer_compare
                
                col_dist, col_create = st.columns([2, 1])
                with col_dist:
                    buffer_distance = st.selectbox(
                        t("buffer_distance"),
                        options=[2, 5, 10],
                        format_func=lambda x: f"{x} km",
                        key="polygon_buffer_distance"
                    )
                with col_create:
                    create_buffer_btn = st.button(t("create_buffer"), key="btn_create_polygon_buffer", width="stretch")
                
                if create_buffer_btn:
                    try:
                        # Extract geometry from selected feature
                        feature_geom = selected_feature.get('geometry', {})
                        
                        # Convert to ee.Geometry
                        if feature_geom.get('type') == 'Polygon':
                            coords = feature_geom.get('coordinates', [[]])
                            ee_geom = ee.Geometry.Polygon(coords)
                        else:
                            st.error(t("polygon_only_error"))
                            return
                        
                        # Create and store the buffer
                        polygon_name = f"Polygon {selected_idx + 1}"
                        buffer_name = add_buffer_to_session_state(
                            ee_geom,
                            buffer_distance,
                            polygon_name
                        )
                        
                        # Add to polygon list
                        add_buffer_to_polygon_list(buffer_name)
                        
                        # If compare mode, set this buffer for comparison
                        if st.session_state.buffer_compare_mode:
                            st.session_state.current_buffer_for_analysis = buffer_name
                            st.success(t("buffer_created_compare", distance=buffer_distance))
                            st.info(t("analysis_compare_info"))
                        else:
                            st.success(t("buffer_created", distance=buffer_distance, name=polygon_name))
                            st.info(t("buffer_added_info"))
                        st.rerun()
                        
                    except Exception as e:
                        st.error(t("buffer_creation_error", error=str(e)))
                        traceback.print_exc()


def render_layer_reference_guide():
    """Render the layer reference guide with legends."""
    st.divider()
    with st.expander(t("layer_reference_full"), expanded=False):

         # Indigenous Territories Legend
        st.markdown("### " + t("indigenous_territories_legend"))
        st.markdown(
            "<div style='display: flex; gap: 20px; flex-wrap: wrap; font-size: 13px;'>"
            "<span><span style='color: #4B0082; font-size: 16px;'>■</span> " + t("indigenous_territories_label") + "</span>"
            "<span><span style='color: #FF0000; font-size: 16px;'>■</span> " + t("selected_territory_label") + "</span>"
            "<span><span style='color: #0033FF; font-size: 16px;'>■</span> " + t("drawn_polygon_label") + "</span>"
            "<span><span style='color: #00BFFF; font-size: 16px;'>■</span> " + t("buffer_zone_label") + "</span>"
            "</div>",
            unsafe_allow_html=True
        )
        # MapBiomas Legend
        st.markdown("### " + t("mapbiomas_legend"))
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
        st.markdown("### " + t("hansen_legend"))
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
        
        # Hansen Global Forest Change Legend
        st.markdown("### " + t("gfc_legend"))
        st.caption(t("gfc_legend_desc"))
        hansen_gfc_legend_html = "<div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>"
        hansen_gfc_legend_data = [
            ("Tree Cover 2000", "black → green", "0-100% tree canopy cover"),
            ("Tree Loss Year", "yellow → red", "Forest loss 2001-2024"),
            ("Tree Gain", "green", "Forest gain 2000-2012"),
        ]
        for label, color, desc in hansen_gfc_legend_data:
            hansen_gfc_legend_html += f"<div style='margin: 5px 0;'><strong>{label}:</strong> <span style='color: gray;'>{color}</span> - {desc}</div>"
        hansen_gfc_legend_html += "</div>"
        st.markdown(hansen_gfc_legend_html, unsafe_allow_html=True)
        
        # AAFC Legend
        st.markdown("### " + t("aafc_legend"))
        st.caption(t("aafc_legend_desc"))
        aafc_legend_html = "<div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>"
        aafc_legend_data = [
            ("Agriculture (undifferentiated)", "#cc6600"),
            ("Cropland", "#ff9933"),
            ("Pasture and Forages", "#ffcc33"),
            ("Cereals", "#660000"),
            ("Wheat", "#a7b34d"),
            ("Canola and Rapeseed", "#d6ff70"),
            ("Corn for Grain", "#ffff99"),
            ("Soybeans", "#cc9933"),
            ("Grassland", "#cccc00"),
            ("Forest", "#009900"),
            ("Water", "#3333ff"),
            ("Urban and Developed", "#cc6699"),
        ]
        for label, color in aafc_legend_data:
            aafc_legend_html += f"<span><span style='color: {color}; font-size: 16px;'>■</span> {label}</span>"
        aafc_legend_html += "</div>"
        st.markdown(aafc_legend_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**" + t("basemaps") + "**")
            st.caption("""
            - 🗺️ OpenStreetMap
            - 🛰️ Google Maps (default)
            - 🛰️ Google Satellite
            - 🛣️ ArcGIS Street
            - 🛰️ ArcGIS Satellite
            - ⛰️ ArcGIS Terrain
            """)
            
            st.markdown("**" + t("legend_controls") + "**")
            st.caption(f"""
            - ⌗ {t("legend_layer_control")}
            - ✏️ {t("legend_drawing_tools")}
            - 🎨 {t("legend_opacity")}
            """)
        
        with col2:
            st.markdown("**" + t("legend_data_overview") + "**")
            st.caption(f"""
            - {t("legend_data_brazilian")}
            - {t("legend_data_global")}
            - {t("legend_data_agriculture")}
            - {t("legend_data_territories")}
            """)
