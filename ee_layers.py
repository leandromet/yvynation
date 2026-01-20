"""
Earth Engine layer utilities for Yvynation.
Handles adding MapBiomas, Hansen/GLAD, and other EE layers to maps.
"""

import folium
import ee
from config import MAPBIOMAS_PALETTE, HANSEN_DATASETS, HANSEN_OCEAN_MASK, HANSEN_PALETTE


def add_mapbiomas_layer(m, mapbiomas, year, opacity=1.0, shown=True):
    """
    Add MapBiomas layer to map for a specific year.
    
    Args:
        m (folium.Map): Map object to add layer to
        mapbiomas (ee.ImageCollection): MapBiomas image collection
        year (int): Year to display
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        print(f"Adding MapBiomas {year} layer...")
        band = f'classification_{year}'
        image = mapbiomas.select(band)
        
        vis_params = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
        map_id = image.getMapId(vis_params)
        
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr='Map data: MapBiomas',
            name=f"MapBiomas {year}",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ MapBiomas {year} added")
        return m
    except Exception as e:
        print(f"❌ Error adding MapBiomas {year}: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_hansen_layer(m, year, opacity=1.0, shown=True):
    """
    Add Hansen/GLAD global forest change layer to map.
    
    Args:
        m (folium.Map): Map object to add layer to
        year (int or str): Year to display
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        year_key = str(year) if year else "2020"
        print(f"Adding Hansen {year_key} layer...")
        
        # Apply ocean mask
        landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
        hansen_image = ee.Image(HANSEN_DATASETS[year_key]).updateMask(landmask)
        
        vis_params = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
        map_id = hansen_image.getMapId(vis_params)
        
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr='Map data: Hansen/GLAD',
            name=f"Hansen {year_key}",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ Hansen {year_key} added")
        return m
    except Exception as e:
        print(f"❌ Error adding Hansen {year_key}: {e}")
        import traceback
        traceback.print_exc()
        return None


def remove_layer(m, layer_name):
    """
    Remove a layer from the map by name.
    
    Args:
        m (folium.Map): Map object
        layer_name (str): Name of layer to remove
    
    Returns:
        folium.Map: Updated map object
    """
    try:
        # Find and remove the layer
        for child_id, child in list(m._children.items()):
            if hasattr(child, 'name') and child.name == layer_name:
                m._children.pop(child_id)
                print(f"✓ Removed {layer_name}")
                break
        return m
    except Exception as e:
        print(f"❌ Error removing {layer_name}: {e}")
        return m
