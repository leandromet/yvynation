"""
Map management utilities for Yvynation.
Handles base map creation, layer management, and map operations.
Reflex version - no Streamlit dependencies.
"""

import folium
import ee
from ..config import MAPBIOMAS_PALETTE


def create_base_map(country="Brazil", center_lat=None, center_lon=None, zoom=None):
    """
    Create a base Folium map with standard basemap options.
    
    Args:
        country (str): Country to center map on ("Brazil" or "Canada")
        center_lat (float): Override center latitude (default based on country)
        center_lon (float): Override center longitude (default based on country)
        zoom (int): Override initial zoom level (default based on country)
    
    Returns:
        folium.Map: Base map object
    """
    # Set coordinates based on country if not manually overridden
    country_coordinates = {
        "Brazil": {"lat": -15, "lon": -50, "zoom": 4},
        "Canada": {"lat": 56, "lon": -95, "zoom": 3}
    }
    
    coords = country_coordinates.get(country, country_coordinates["Brazil"])
    if center_lat is None:
        center_lat = coords["lat"]
    if center_lon is None:
        center_lon = coords["lon"]
    if zoom is None:
        zoom = coords["zoom"]
    # Create map with OpenStreetMap initially, then switch to Google Maps as default
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="OpenStreetMap"
    )
    
    # Add basemap options - Google Maps first so it becomes the visible default

    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Street',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
        attr='Tiles &copy; Esri',
        name='ArcGIS Terrain',
        overlay=False,
        control=True
    ).add_to(m)

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}',
        attr='Google',
        name='Google Maps',
        overlay=False,
        control=True,
        show=True
    ).add_to(m)
    
    return m


def add_territories_layer(m, territories, name='Indigenous Territories', opacity=0.7):
    """
    Add interactive indigenous territories layer to map with hover labels and click capability.
    
    Args:
        m (folium.Map): Map object to add layer to
        territories (ee.FeatureCollection): EE territories feature collection
        name (str): Layer name
        opacity (float): Layer opacity (0-1)
    
    Returns:
        folium.Map: Updated map object
    """
    if territories is None:
        return m
    
    try:
        import streamlit as st

        # Use cached GeoJSON to avoid repeated EE API calls on every rerun
        if 'territories_clean_geojson' not in st.session_state or st.session_state.territories_clean_geojson is None:
            print(f"Adding {name} layer (fetching from EE)...")
            territories_geojson = territories.getInfo()

            valid_features = []
            if territories_geojson.get('type') == 'FeatureCollection':
                features = territories_geojson.get('features', [])
                for feature in features:
                    try:
                        geometry = feature.get('geometry', {})
                        if geometry and geometry.get('type') and geometry.get('coordinates'):
                            valid_features.append(feature)
                    except Exception as e:
                        print(f"[Warning] Skipping invalid feature: {e}")
                        continue
                print(f"[Info] Filtered to {len(valid_features)} valid territories from {len(features)} total")

            clean_features = []
            for f in valid_features:
                name_val = f.get('properties', {}).get('NAME', 'Unknown')
                clean_features.append({
                    'type': 'Feature',
                    'geometry': f['geometry'],
                    'properties': {'NAME': name_val}
                })

            st.session_state.territories_clean_geojson = {'type': 'FeatureCollection', 'features': clean_features}
            # Also store the raw geojson for export use
            st.session_state.territories_geojson = territories_geojson
        else:
            print(f"Adding {name} layer (from cache)...")

        clean_geojson = st.session_state.territories_clean_geojson
        
        # Add as a SINGLE GeoJson layer - this is key for streamlit_folium click detection
        folium.GeoJson(
            data=clean_geojson,
            name=name,
            style_function=lambda x: {
                'fillColor': '#4B0082',
                'color': '#4B0082',
                'weight': 2,
                'opacity': 0.7,
                'fillOpacity': 0.3
            },
            highlight_function=lambda x: {
                'fillColor': '#8B00FF',
                'color': '#FF1493',
                'weight': 3,
                'opacity': 1.0,
                'fillOpacity': 0.5
            },
            tooltip=folium.features.GeoJsonTooltip(
                fields=['NAME'],
                aliases=['Territory:'],
                sticky=True,
                labels=True
            ),
            popup=folium.features.GeoJsonPopup(
                fields=['NAME'],
                aliases=['Territory:'],
                labels=True
            )
        ).add_to(m)
        
        print(f"✓ {name} added with hover labels and popups")
        return m
    except Exception as e:
        print(f"❌ Error adding interactive territories layer: {e}")
        import traceback
        traceback.print_exc()
        return m


def add_layer_control(m):
    """Add layer control to map."""
    folium.LayerControl().add_to(m)
    return m
