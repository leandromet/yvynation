"""
Earth Engine layer utilities for Yvynation.
Handles adding MapBiomas, Hansen/GLAD, and other EE layers to maps.
Tile URLs from getMapId() are cached in st.session_state._tile_cache
to avoid redundant EE API calls on every Streamlit rerun.
"""

import folium
import ee
import streamlit as st
from config import (
    MAPBIOMAS_PALETTE, HANSEN_DATASETS, HANSEN_OCEAN_MASK, HANSEN_PALETTE,
    HANSEN_GFC_DATASET, HANSEN_GFC_TREE_COVER_VIS, HANSEN_GFC_TREE_LOSS_VIS,
    HANSEN_GFC_TREE_GAIN_VIS
)
from hansen_reference_mapping import (
    HANSEN_CLASS_TO_STRATUM, HANSEN_STRATUM_COLORS, HANSEN_STRATUM_NAMES
)


def _get_tile_cache():
    """Return (and lazily initialise) the session-state tile URL cache."""
    if '_tile_cache' not in st.session_state:
        st.session_state._tile_cache = {}
    return st.session_state._tile_cache


def _cached_get_map_id(cache_key, image_fn, vis_params):
    """
    Return a cached tile URL string for the given cache_key.
    If not cached yet, call image_fn() to get the ee.Image, then getMapId().
    """
    cache = _get_tile_cache()
    if cache_key in cache:
        return cache[cache_key]
    image = image_fn() if callable(image_fn) else image_fn
    map_id = image.getMapId(vis_params)
    tile_url = map_id['tile_fetcher'].url_format
    cache[cache_key] = tile_url
    return tile_url


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
        
        vis_params = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
        tile_url = _cached_get_map_id(
            f'mapbiomas_{year}',
            lambda: mapbiomas.select(band),
            vis_params
        )
        
        folium.TileLayer(
            tiles=tile_url,
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
            
            strata_palette = [
                "#CCCCCC",
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
            tile_url = _cached_get_map_id(
                f'hansen_{year_key}_strata',
                lambda: hansen_image.remap(from_vals, to_vals, 0),
                vis_params
            )
            layer_name = f"Hansen {year_key} (Strata)"
        else:
            vis_params = {'min': 0, 'max': 255, 'palette': HANSEN_PALETTE}
            tile_url = _cached_get_map_id(
                f'hansen_{year_key}_raw',
                lambda: hansen_image,
                vis_params
            )
            layer_name = f"Hansen {year_key}"
        
        folium.TileLayer(
            tiles=tile_url,
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


def add_hansen_gfc_tree_cover(m, opacity=1.0, shown=True):
    """
    Add Hansen Global Forest Change tree cover 2000 layer to map.
    
    Args:
        m (folium.Map): Map object to add layer to
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        print(f"Adding Hansen GFC Tree Cover 2000 layer...")
        
        vis_params = HANSEN_GFC_TREE_COVER_VIS
        tile_url = _cached_get_map_id(
            'hansen_gfc_treecover2000',
            lambda: ee.Image(HANSEN_GFC_DATASET).select(['treecover2000']),
            vis_params
        )
        
        folium.TileLayer(
            tiles=tile_url,
            attr='Map data: Hansen/UMD Global Forest Change',
            name=f"Hansen GFC - Tree Cover 2000",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ Hansen GFC Tree Cover 2000 added")
        return m
    except Exception as e:
        print(f"❌ Error adding Hansen GFC Tree Cover: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_hansen_gfc_tree_loss(m, opacity=1.0, shown=True):
    """
    Add Hansen Global Forest Change tree loss by year layer to map.
    Shows forest loss from 2001-2024 (coded as 1-24).
    
    Args:
        m (folium.Map): Map object to add layer to
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        print(f"Adding Hansen GFC Tree Loss Year layer...")
        
        vis_params = HANSEN_GFC_TREE_LOSS_VIS
        tile_url = _cached_get_map_id(
            'hansen_gfc_lossyear',
            lambda: ee.Image(HANSEN_GFC_DATASET).select(['lossyear']),
            vis_params
        )
        
        folium.TileLayer(
            tiles=tile_url,
            attr='Map data: Hansen/UMD Global Forest Change',
            name=f"Hansen GFC - Tree Loss Year (2001-2024)",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ Hansen GFC Tree Loss Year added")
        return m
    except Exception as e:
        print(f"❌ Error adding Hansen GFC Tree Loss: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_hansen_gfc_tree_gain(m, opacity=1.0, shown=True):
    """
    Add Hansen Global Forest Change tree gain layer to map.
    Shows areas with tree cover gain from 2000-2012.
    
    Args:
        m (folium.Map): Map object to add layer to
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        print(f"Adding Hansen GFC Tree Gain layer...")
        
        vis_params = {
            'min': 0,
            'max': 1,
            'palette': ['#00FF00']
        }
        tile_url = _cached_get_map_id(
            'hansen_gfc_gain',
            lambda: ee.Image(HANSEN_GFC_DATASET).select(['gain']).eq(1).selfMask(),
            vis_params
        )
        
        folium.TileLayer(
            tiles=tile_url,
            attr='Map data: Hansen/UMD Global Forest Change',
            name=f"Hansen GFC - Tree Gain (2000-2012)",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ Hansen GFC Tree Gain added")
        return m
    except Exception as e:
        print(f"❌ Error adding Hansen GFC Tree Gain: {e}")
        import traceback
        traceback.print_exc()
        return None


def add_aafc_layer(m, year, opacity=1.0, shown=True):
    """
    Add AAFC Annual Crop Inventory layer to map for a specific year (Canada only).
    
    Args:
        m (folium.Map): Map object to add layer to
        year (int): Year to display (2009-2024)
        opacity (float): Layer opacity (0-1)
        shown (bool): Whether layer is visible by default
    
    Returns:
        folium.Map: Updated map object or None if error
    """
    try:
        from config import AAFC_ACI_DATASET, AAFC_PALETTE
        
        print(f"Adding AAFC Annual Crop Inventory {year} layer...")
        
        # Filter image collection to specific year
        aafc_image = ee.ImageCollection(AAFC_ACI_DATASET).filter(
            ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
        ).first()
        
        if aafc_image is None:
            print(f"❌ No AAFC data found for year {year}")
            return None
        
        # Get the landcover band
        landcover = aafc_image.select(['landcover'])
        
        vis_params = {
            'min': 0,
            'max': 255,
            'palette': AAFC_PALETTE
        }
        
        tile_url = _cached_get_map_id(
            f'aafc_{year}',
            lambda: landcover,
            vis_params
        )
        
        folium.TileLayer(
            tiles=tile_url,
            attr='Map data: AAFC Annual Crop Inventory',
            name=f"AAFC Crop Inventory {year}",
            overlay=True,
            control=True,
            opacity=opacity,
            show=shown
        ).add_to(m)
        
        print(f"✓ AAFC {year} added")
        return m
    except Exception as e:
        print(f"❌ Error adding AAFC layer: {e}")
        import traceback
        traceback.print_exc()
        return None
