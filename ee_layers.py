"""
Earth Engine layer utilities for Yvynation.
Handles adding MapBiomas, Hansen/GLAD, and other EE layers to maps.
"""

import folium
import ee
from config import (
    MAPBIOMAS_PALETTE, HANSEN_DATASETS, HANSEN_OCEAN_MASK, HANSEN_PALETTE
)
from hansen_reference_mapping import (
    HANSEN_CLASS_TO_STRATUM, HANSEN_STRATUM_COLORS, HANSEN_STRATUM_NAMES
)


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


def add_hansen_layer(m, year, opacity=1.0, shown=True, use_consolidated=False):
    """
    Add Hansen/GLAD global forest change layer to map.
    
    Args:
        m (folium.Map): Map object to add layer to
        year (int or str): Year to display
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
        use_consolidated (bool): If True, remap to 11 strata; if False, show all 256 classes
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        year_key = str(year) if year else "2020"
        print(f"Adding Hansen {year_key} layer{'(strata)' if use_consolidated else ''}...")
        
        # Apply ocean mask
        landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
        hansen_image = ee.Image(HANSEN_DATASETS[year_key]).updateMask(landmask)
        
        if use_consolidated:
            # Remap 256 classes to 11 strata using reference mapping
            from_vals = list(HANSEN_CLASS_TO_STRATUM.keys())
            to_vals = list(HANSEN_CLASS_TO_STRATUM.values())
            
            # Create the remap expression
            hansen_strata = hansen_image.remap(from_vals, to_vals, 0)  # Default to 0 for unmapped
            
            # Create strata color palette (11 colors + 1 for unmapped)
            strata_palette = [
                "#CCCCCC",  # 0: unmapped/no data
                HANSEN_STRATUM_COLORS.get(1, "#D4D4A8").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(2, "#F4D584").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(3, "#A8D4A8").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(4, "#70C070").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(5, "#1F8040").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(6, "#C0B0A8").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(7, "#4A90E2").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(8, "#E0E0E0").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(9, "#FFD700").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(10, "#FF6B35").lstrip('#'),
                HANSEN_STRATUM_COLORS.get(11, "#90EE90").lstrip('#'),
            ]
            
            vis_params = {'min': 0, 'max': 11, 'palette': strata_palette}
            map_id = hansen_strata.getMapId(vis_params)
            layer_name = f"Hansen {year_key} (Strata)"
        else:
            # Use original 256-class palette
            vis_params = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
            map_id = hansen_image.getMapId(vis_params)
            layer_name = f"Hansen {year_key}"
        
        folium.TileLayer(
            tiles=map_id['tile_fetcher'].url_format,
            attr='Map data: Hansen/GLAD',
            name=layer_name,
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ {layer_name} added")
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
