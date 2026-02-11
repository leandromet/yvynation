"""
Map Export Components
Handles exporting interactive maps with different layers and overlays
"""

import streamlit as st
import folium
from folium.plugins import Draw, MeasureControl, MousePosition
from streamlit_folium import st_folium
from translations import t
import ee
import os
import json
from datetime import datetime

def create_map_with_layer(
    base_map,
    layer_type,
    year=None,
    mapbiomas_year_1=None,
    mapbiomas_year_2=None,
    hansen_year_1=None,
    hansen_year_2=None,
    drawn_features=None,
    territories_geojson=None,
    territory_style=None
):
    """
    Create a folium map with specific layer for export
    
    Args:
        base_map: folium.Map object (will be copied)
        layer_type: 'mapbiomas', 'hansen', 'mapbiomas_comparison', 'hansen_comparison', 'satellite', 'maps'
        year: Single year for mapbiomas or hansen (if not comparison)
        mapbiomas_year_1, mapbiomas_year_2: Years for mapbiomas comparison
        hansen_year_1, hansen_year_2: Years for hansen comparison
        drawn_features: List of drawn feature dictionaries
        territories_geojson: GeoJSON of territories
        territory_style: Style function for territories
    
    Returns:
        folium.Map object
    """
    from ee_layers import add_mapbiomas_layer, add_hansen_layer
    from map_manager import add_territories_layer
    
    # Create a fresh map with same bounds and center
    center = base_map.location
    zoom = base_map.zoom_start
    
    export_map = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    
    # Add basemap based on layer type
    if layer_type == 'satellite':
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri',
            name='Google Satellite',
            overlay=False
        ).add_to(export_map)
    elif layer_type == 'maps':
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google Maps',
            name='Google Maps',
            overlay=False
        ).add_to(export_map)
    else:
        export_map.add_child(folium.TileLayer('OpenStreetMap', name='OpenStreetMap'))
    
    # Add territories layer if provided
    if territories_geojson and territory_style:
        folium.GeoJson(
            data=territories_geojson,
            style_function=territory_style,
            name='Indigenous Territories',
            overlay=True
        ).add_to(export_map)
    
    # Add the specific data layer
    if layer_type == 'mapbiomas' and year:
        add_mapbiomas_layer(export_map, year, opacity=0.7, name=f'MapBiomas {year}')
    
    elif layer_type == 'hansen' and year:
        add_hansen_layer(export_map, year, opacity=0.7, name=f'Hansen {year}')
    
    elif layer_type == 'mapbiomas_comparison' and mapbiomas_year_1 and mapbiomas_year_2:
        add_mapbiomas_layer(export_map, mapbiomas_year_1, opacity=0.6, name=f'MapBiomas {mapbiomas_year_1}')
        add_mapbiomas_layer(export_map, mapbiomas_year_2, opacity=0.6, name=f'MapBiomas {mapbiomas_year_2}')
    
    elif layer_type == 'hansen_comparison' and hansen_year_1 and hansen_year_2:
        add_hansen_layer(export_map, hansen_year_1, opacity=0.6, name=f'Hansen {hansen_year_1}')
        add_hansen_layer(export_map, hansen_year_2, opacity=0.6, name=f'Hansen {hansen_year_2}')
    
    # Add drawn polygons
    if drawn_features:
        for idx, feature in enumerate(drawn_features):
            try:
                geom = feature.get('geometry', {})
                props = feature.get('properties', {})
                
                color = props.get('color', '#0033FF')
                
                folium.GeoJson(
                    data=feature,
                    style_function=lambda x, col=color: {
                        'fillColor': col,
                        'color': col,
                        'weight': 2,
                        'opacity': 0.7,
                        'fillOpacity': 0.3
                    },
                    name=f'Polygon {idx + 1}',
                    overlay=True
                ).add_to(export_map)
                
                # Add popup with polygon info
                geom_type = geom.get('type', 'Unknown')
                popup_text = f"<b>Polygon {idx + 1}</b><br>Type: {geom_type}"
                
                if geom_type == 'Polygon' and geom.get('coordinates'):
                    coords = geom['coordinates'][0]  # Exterior ring
                    if coords:
                        center_lat = sum(c[1] for c in coords) / len(coords)
                        center_lon = sum(c[0] for c in coords) / len(coords)
                        
                        folium.Marker(
                            location=[center_lat, center_lon],
                            popup=folium.Popup(popup_text, max_width=250),
                            icon=folium.Icon(color='blue', icon='info-sign'),
                        ).add_to(export_map)
            except Exception as e:
                st.warning(t("export_maps_polygon_error", idx=idx + 1, error=str(e)))
    
    # Add scale bar and measure control
    MeasureControl(primary_length_unit='kilometers').add_to(export_map)
    
    # Add layer control
    folium.LayerControl(position='topright', collapsed=False).add_to(export_map)
    
    return export_map


def export_map_with_polygons(
    base_map,
    layer_name,
    layer_type,
    year=None,
    mapbiomas_year_1=None,
    mapbiomas_year_2=None,
    hansen_year_1=None,
    hansen_year_2=None
):
    """
    Create and export a map with specific layer and current polygons
    
    Args:
        base_map: Reference map to get bounds and polygons
        layer_name: Name for the exported map file
        layer_type: Type of layer to show
        year: Year for single-year layers
        mapbiomas_year_1, mapbiomas_year_2: Years for comparison
        hansen_year_1, hansen_year_2: Years for comparison
    
    Returns:
        folium.Map object for export
    """
    # Extract drawn features from session state
    drawn_features = st.session_state.get('all_drawn_features', [])
    
    # Get territories if available
    territories_geojson = st.session_state.get('territories_geojson', None)
    territory_style = st.session_state.get('territory_style', None)
    
    # Create export map
    export_map = create_map_with_layer(
        base_map=base_map,
        layer_type=layer_type,
        year=year,
        mapbiomas_year_1=mapbiomas_year_1,
        mapbiomas_year_2=mapbiomas_year_2,
        hansen_year_1=hansen_year_1,
        hansen_year_2=hansen_year_2,
        drawn_features=drawn_features,
        territories_geojson=territories_geojson,
        territory_style=territory_style
    )
    
    return export_map


def create_export_map_set(base_map):
    """
    Create a set of maps for all active layers with polygon overlays
    
    Returns:
        Dictionary of {map_name: folium.Map}
    """
    export_maps = {}
    drawn_features = st.session_state.get('all_drawn_features', [])
    
    if not drawn_features:
        st.warning(t("export_maps_no_polygons_warn"))
        return export_maps
    
    # Get territories
    territories_geojson = st.session_state.get('territories_geojson', None)
    territory_style = st.session_state.get('territory_style', None)
    
    # Get active layers from session state
    active_mapbiomas = [y for y, v in st.session_state.get('mapbiomas_layers', {}).items() if v]
    active_hansen = [y for y, v in st.session_state.get('hansen_layers', {}).items() if v]
    
    # Create maps for each active MapBiomas year
    for year in active_mapbiomas:
        map_name = f"MapBiomas_{year}"
        export_maps[map_name] = create_map_with_layer(
            base_map=base_map,
            layer_type='mapbiomas',
            year=year,
            drawn_features=drawn_features,
            territories_geojson=territories_geojson,
            territory_style=territory_style
        )
    
    # Create maps for each active Hansen year
    for year in active_hansen:
        map_name = f"Hansen_{year}"
        export_maps[map_name] = create_map_with_layer(
            base_map=base_map,
            layer_type='hansen',
            year=year,
            drawn_features=drawn_features,
            territories_geojson=territories_geojson,
            territory_style=territory_style
        )
    
    # Create satellite basemap version
    export_maps['Satellite_Basemap'] = create_map_with_layer(
        base_map=base_map,
        layer_type='satellite',
        drawn_features=drawn_features,
        territories_geojson=territories_geojson,
        territory_style=territory_style
    )
    
    # Create Google Maps basemap version
    export_maps['GoogleMaps_Basemap'] = create_map_with_layer(
        base_map=base_map,
        layer_type='maps',
        drawn_features=drawn_features,
        territories_geojson=territories_geojson,
        territory_style=territory_style
    )
    
    return export_maps


def render_map_export_section():
    """
    Render UI section for exporting maps with polygon overlays
    Shows options to export maps with different layers
    """
    st.divider()
    st.subheader(t("export_maps_intro"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption(t("export_maps_description"))
    
    with col2:
        if st.session_state.get('all_drawn_features'):
            st.success(t("export_maps_ready", count=len(st.session_state.get('all_drawn_features', []))))
        else:
            st.warning(t("export_maps_warning"))
    
    # Export button
    export_button_col, info_col = st.columns([1, 2])
    
    with export_button_col:
        if st.button(t("export_maps_button"), key="prepare_maps_export", width="stretch"):
            if not st.session_state.get('all_drawn_features'):
                st.error(t("export_maps_no_polygons"))
            elif not st.session_state.get('map_object'):
                st.error(t("export_maps_no_object"))
            else:
                with st.spinner(t("export_maps_preparing")):
                    try:
                        # Actually create the maps now
                        export_maps = create_export_map_set(st.session_state.get('map_object'))
                        
                        # Convert to HTML and store in session state
                        map_exports = {}
                        for map_name, folium_map in export_maps.items():
                            try:
                                html_content = folium_map._repr_html_()
                                if html_content:
                                    map_exports[map_name] = html_content
                            except Exception as e:
                                st.warning(t("export_maps_convert_error", name=map_name, error=str(e)))
                        
                        # Store in session state for export
                        st.session_state.prepared_map_exports = map_exports
                        st.session_state.export_maps_ready = True
                        
                        if map_exports:
                            st.success(t("export_maps_success", count=len(map_exports)))
                        else:
                            st.warning(t("export_maps_no_created"))
                    except Exception as e:
                        st.error(t("export_maps_error", error=str(e)))
                        import traceback
                        traceback.print_exc()
    
    with info_col:
        st.caption(t("export_maps_caption"))


def get_map_export_figures():
    """
    Get all prepared maps as HTML strings for export
    
    Returns:
        Dictionary of {map_name: html_string}
    """
    map_figures = {}
    
    if not st.session_state.get('export_maps_ready'):
        return map_figures
    
    if 'all_drawn_features' not in st.session_state or not st.session_state.all_drawn_features:
        return map_figures
    
    try:
        # Create export maps
        export_maps = create_export_map_set(st.session_state.get('map_object'))
        
        # Convert to HTML strings
        for map_name, folium_map in export_maps.items():
            try:
                html_string = folium_map._repr_html_()
                map_figures[map_name] = html_string
            except Exception as e:
                st.warning(t("export_maps_export_error", name=map_name, error=str(e)))
    
    except Exception as e:
        st.warning(t("export_maps_create_error", error=str(e)))
    
    return map_figures
