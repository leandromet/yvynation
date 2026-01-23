"""
Map management utilities for Yvynation.
Handles base map creation, layer management, and map operations.
"""

import folium
import ee
from config import MAPBIOMAS_PALETTE


def create_base_map(center_lat=-15, center_lon=-50, zoom=4):
    """
    Create a base Folium map with standard basemap options.
    
    Args:
        center_lat (float): Center latitude
        center_lon (float): Center longitude
        zoom (int): Initial zoom level
    
    Returns:
        folium.Map: Base map object
    """
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
    Add indigenous territories layer to map.
    
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
        print(f"Adding {name} layer...")
        territories_image = ee.Image().paint(territories, 1, 2)
        vis_params = {'min': 0, 'max': 1, 'palette': ['00000000', '4B0082']}
        
        map_id = territories_image.getMapId(vis_params)
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr='Map data: Indigenous Territories',
            name=name,
            overlay=True,
            control=True,
            opacity=opacity
        ).add_to(m)
        print(f"✓ {name} added")
        return m
    except Exception as e:
        print(f"❌ Error adding territories layer: {e}")
        import traceback
        traceback.print_exc()
        return m


def add_layer_control(m):
    """Add layer control to map."""
    folium.LayerControl().add_to(m)
    return m
