"""
Visualization module for Yvynation.
Handles interactive maps, layers, and legends using geemap.
"""

import ee
import geemap
from IPython.display import HTML
from config import MAPBIOMAS_COLOR_MAP, MAPBIOMAS_LABELS, MAPBIOMAS_PALETTE


def create_map(center=None, zoom=8):
    """
    Create an interactive geemap Map.
    
    Args:
        center (list): [lon, lat] coordinates
        zoom (int): Zoom level
    
    Returns:
        geemap.Map: Interactive map
    """
    default_center = center or [-55.5, -15.8]
    Map = geemap.Map(center=default_center, zoom=zoom)
    return Map


def add_mapbiomas_layer(Map, mapbiomas, year, name=None, visible=True):
    """
    Add MapBiomas classification layer to map.
    
    Args:
        Map (geemap.Map): Map object
        mapbiomas (ee.Image): MapBiomas image
        year (int): Year to display
        name (str): Layer name
        visible (bool): Whether layer is visible by default
    
    Returns:
        geemap.Map: Updated map
    """
    band = f'classification_{year}'
    vis_params = {
        'min': 0,
        'max': 62,
        'palette': MAPBIOMAS_PALETTE
    }
    layer_name = name or f'MapBiomas {year}'
    Map.addLayer(mapbiomas.select(band), vis_params, layer_name, visible)
    return Map


def add_territories_layer(Map, territories, name='Indigenous Territories', color='red'):
    """
    Add territories as vector layer to map.
    
    Args:
        Map (geemap.Map): Map object
        territories (ee.FeatureCollection): Territory features
        name (str): Layer name
        color (str): Border color
    
    Returns:
        geemap.Map: Updated map
    """
    style = {
        'color': color,
        'fillColor': 'rgba(255,0,0,0.1)',
        'width': 2
    }
    Map.addLayer(territories, style, name, True)
    return Map


def add_change_layer(Map, change_image, name='Land Cover Change', visible=False):
    """
    Add change detection layer to map.
    
    Args:
        Map (geemap.Map): Map object
        change_image (ee.Image): Binary change image
        name (str): Layer name
        visible (bool): Whether layer is visible
    
    Returns:
        geemap.Map: Updated map
    """
    vis_params = {
        'min': 0,
        'max': 1,
        'palette': ['white', 'red']
    }
    Map.addLayer(change_image, vis_params, name, visible)
    return Map


def add_classification_layer(Map, classification, name='Classification', visible=True):
    """
    Add generic classification layer to map.
    
    Args:
        Map (geemap.Map): Map object
        classification (ee.Image): Classification image
        name (str): Layer name
        visible (bool): Whether visible by default
    
    Returns:
        geemap.Map: Updated map
    """
    vis_params = {
        'min': 0,
        'max': 33,
        'palette': MAPBIOMAS_PALETTE
    }
    Map.addLayer(classification, vis_params, name, visible)
    return Map


def create_mapbiomas_legend():
    """
    Create HTML legend for main MapBiomas classes.
    
    Returns:
        HTML: Interactive legend
    """
    legend_html = '<div style="background:white; padding:12px; border-radius:5px; border: 2px solid #ccc;">'
    legend_html += '<h4 style="margin-top:0;">MapBiomas Land Cover Classes</h4>'
    
    # Main classes to display
    main_classes = [1, 3, 4, 9, 15, 18, 20, 24, 26, 33]
    
    for class_id in main_classes:
        if class_id in MAPBIOMAS_LABELS and class_id in MAPBIOMAS_COLOR_MAP:
            color = MAPBIOMAS_COLOR_MAP[class_id]
            label = MAPBIOMAS_LABELS[class_id]
            legend_html += f'<div style="margin: 4px 0;"><span style="background:{color}; width:20px; height:20px; display:inline-block; border: 1px solid #999;"></span> {label}</div>'
    
    legend_html += '</div>'
    return HTML(legend_html)


def create_comparison_map(mapbiomas, year1, year2, territories, center=None, zoom=8):
    """
    Create a map with layers for comparing two years.
    
    Args:
        mapbiomas (ee.Image): MapBiomas image
        year1 (int): First year
        year2 (int): Second year
        territories (ee.FeatureCollection): Territory features
        center (list): Map center
        zoom (int): Zoom level
    
    Returns:
        geemap.Map: Comparison map
    """
    Map = create_map(center=center, zoom=zoom)
    Map = add_mapbiomas_layer(Map, mapbiomas, year1, f'MapBiomas {year1}', visible=True)
    Map = add_mapbiomas_layer(Map, mapbiomas, year2, f'MapBiomas {year2}', visible=False)
    Map = add_territories_layer(Map, territories)
    return Map


def create_temporal_map(mapbiomas, years, territories, center=None, zoom=8):
    """
    Create a map with multiple years for temporal analysis.
    
    Args:
        mapbiomas (ee.Image): MapBiomas image
        years (list): List of years to add
        territories (ee.FeatureCollection): Territory features
        center (list): Map center
        zoom (int): Zoom level
    
    Returns:
        geemap.Map: Temporal map
    """
    Map = create_map(center=center, zoom=zoom)
    
    for year in years:
        visible = (year == years[0])  # First year visible by default
        Map = add_mapbiomas_layer(Map, mapbiomas, year, f'MapBiomas {year}', visible=visible)
    
    Map = add_territories_layer(Map, territories)
    return Map
