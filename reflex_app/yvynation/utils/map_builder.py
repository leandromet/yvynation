"""
Map builder module - generates Folium maps with Earth Engine layers.
Replicates the Streamlit pattern: iterate through selected layers and add them to the map.
"""

import folium
from folium.plugins import Draw
from typing import List, Optional
import logging
import ee

logger = logging.getLogger(__name__)


def _ensure_ee_initialized():
    """Ensure Earth Engine is initialized."""
    try:
        # Test if EE is already initialized
        ee.Image('USGS/SRTM90_V4').getInfo()
        logger.info("✓ Earth Engine already initialized")
        return True
    except Exception as e:
        try:
            logger.info("Initializing Earth Engine...")
            ee.Initialize()
            logger.info("✓ Earth Engine initialized")
            return True
        except Exception as init_error:
            logger.error(f"Failed to initialize Earth Engine: {init_error}")
            return False


def build_map(mapbiomas_years: List[int] = None, hansen_layers: List[str] = None) -> str:
    """
    Build a complete Folium map with Earth Engine layers.
    This replicates the Streamlit approach: iterate through selections and add layers.
    
    Args:
        mapbiomas_years: List of years to display (e.g., [1985, 2023])
        hansen_layers: List of Hansen layer identifiers (e.g., ["2020"])
    
    Returns:
        HTML string of the complete map
    """
    try:
        # Ensure EE is initialized
        if not _ensure_ee_initialized():
            logger.warning("Earth Engine not initialized - layers may not work")
        
        # Create base map
        display_map = folium.Map(
            location=[-5, -60],
            zoom_start=4,
            tiles="OpenStreetMap"
        )
        
        logger.info(f"Base map created. MapBiomas years: {mapbiomas_years}, Hansen: {hansen_layers}")
        
        # Add alternative basemaps
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
        
        # ADD MAPBIOMAS LAYERS - following Streamlit pattern
        layers_added = 0
        if mapbiomas_years and len(mapbiomas_years) > 0:
            try:
                from .ee_service_extended import ExtendedEarthEngineService
                from .ee_layers import add_mapbiomas_layer
                
                ee_service = ExtendedEarthEngineService()
                mapbiomas_coll = ee_service.get_mapbiomas()
                logger.info(f"MapBiomas collection loaded")
                
                # Iterate through selected years (same as Streamlit)
                for year in mapbiomas_years:
                    try:
                        logger.info(f"Adding MapBiomas {year}...")
                        result = add_mapbiomas_layer(
                            display_map,
                            mapbiomas_coll,
                            year,
                            opacity=0.8,
                            shown=True
                        )
                        if result is not None:
                            display_map = result
                            # Check if layer was actually added
                            layer_count = len(display_map._children)
                            logger.info(f"✓ Added MapBiomas {year} - map now has {layer_count} children")
                            layers_added += 1
                        else:
                            logger.warning(f"Failed to add MapBiomas {year} - function returned None")
                    except Exception as e:
                        logger.error(f"Error adding MapBiomas {year}: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                logger.error(f"Error setting up MapBiomas layers: {e}")
                import traceback
                traceback.print_exc()
        
        # ADD HANSEN LAYERS - following Streamlit pattern
        if hansen_layers and len(hansen_layers) > 0:
            try:
                from .ee_layers import (
                    add_hansen_layer, 
                    add_hansen_gfc_tree_cover,
                    add_hansen_gfc_tree_loss,
                    add_hansen_gfc_tree_gain
                )
                
                # Iterate through selected layers (same as Streamlit)
                for layer_str in hansen_layers:
                    try:
                        # Check if it's a GFC layer type (cover, loss, gain) or a year
                        if layer_str in ['cover', 'loss', 'gain']:
                            # Route to GFC functions
                            logger.info(f"Adding Hansen {layer_str} layer (GFC)...")
                            if layer_str == 'cover':
                                result = add_hansen_gfc_tree_cover(display_map, opacity=0.8, shown=True)
                            elif layer_str == 'loss':
                                result = add_hansen_gfc_tree_loss(display_map, opacity=0.8, shown=True)
                            elif layer_str == 'gain':
                                result = add_hansen_gfc_tree_gain(display_map, opacity=0.8, shown=True)
                        else:
                            # Extract year from strings like "2020" or "Hansen 2020"
                            year_str = layer_str.split()[-1] if ' ' in layer_str else layer_str
                            logger.info(f"Adding Hansen {year_str}...")
                            
                            result = add_hansen_layer(
                                display_map,
                                year_str,
                                opacity=0.8,
                                shown=True,
                                use_consolidated=False
                            )
                        
                        if result is not None:
                            display_map = result
                            layer_count = len(display_map._children)
                            logger.info(f"✓ Added Hansen {layer_str} - map now has {layer_count} children")
                            layers_added += 1
                        else:
                            logger.warning(f"Failed to add Hansen {layer_str} - function returned None")
                    except Exception as e:
                        logger.error(f"Error adding Hansen {layer_str}: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                logger.error(f"Error setting up Hansen layers: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Layers added: {layers_added}")
        
        # Add Leaflet Draw tool
        Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': True,
                'polygon': True,
                'rectangle': True,
                'circle': False,
                'circlemarker': False,
                'marker': True,
            }
        ).add_to(display_map)
        
        # Add layer control - IMPORTANT: this must be added AFTER all layers
        layer_control = folium.LayerControl(position='topright', collapsed=False)
        display_map.add_child(layer_control)
        logger.info(f"Layer control added")
        
        # Get the map HTML
        map_html = display_map._repr_html_()
        logger.info(f"Map HTML generated - length: {len(map_html)}")
        
        return map_html
        
    except Exception as e:
        logger.error(f"Critical error in build_map: {e}")
        import traceback
        traceback.print_exc()
        
        # Return basic map on error
        m = folium.Map(location=[-5, -60], zoom_start=4, tiles="OpenStreetMap")
        folium.LayerControl().add_to(m)
        return m._repr_html_()
