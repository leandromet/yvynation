"""
API routes for map generation with Earth Engine layers.
Generates complete Folium maps with selected MapBiomas and Hansen layers.
"""

from fastapi import APIRouter, HTTPException
from typing import List
import folium
from folium.plugins import Draw
import logging

logger = logging.getLogger(__name__)

# Import EE utilities
try:
    from ..utils.ee_layers import add_mapbiomas_layer, add_hansen_layer
    from ..utils.ee_service_extended import ExtendedEarthEngineService
    ee_service = ExtendedEarthEngineService()
except Exception as e:
    logger.error(f"Failed to import EE utilities: {e}")
    ee_service = None

router = APIRouter(prefix="/api/map", tags=["map"])


def create_base_map_with_layers(
    mapbiomas_years: List[int] = None,
    hansen_layers: List[str] = None,
) -> str:
    """
    Create a Folium map with basemaps and optional Earth Engine layers.
    
    Args:
        mapbiomas_years: List of years to display (e.g., [1985, 2023])
        hansen_layers: List of Hansen layer identifiers (e.g., ["2020", "2015"])
    
    Returns:
        HTML string of the map
    """
    try:
        m = folium.Map(
            location=[-5, -60],
            zoom_start=4,
            tiles="OpenStreetMap"
        )
        
        # Add alternative basemaps
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
        
        # Add MapBiomas layers from Earth Engine
        if mapbiomas_years and len(mapbiomas_years) > 0:
            try:
                if ee_service is None:
                    logger.warning("EE service not available for MapBiomas layers")
                else:
                    mapbiomas_coll = ee_service.get_mapbiomas()
                    for year in mapbiomas_years:
                        try:
                            result = add_mapbiomas_layer(
                                m, mapbiomas_coll, year,
                                opacity=0.8, shown=True
                            )
                            if result is not None:
                                m = result
                                logger.info(f"✓ Added MapBiomas {year}")
                            else:
                                logger.warning(f"Failed to add MapBiomas {year}")
                        except Exception as e:
                            logger.warning(f"Error adding MapBiomas {year}: {e}")
            except Exception as e:
                logger.error(f"Error with MapBiomas layers: {e}")
                import traceback
                traceback.print_exc()
        
        # Add Hansen layers from Earth Engine
        if hansen_layers and len(hansen_layers) > 0:
            try:
                for layer_str in hansen_layers:
                    try:
                        # Extract year from strings like "2020" or "Hansen 2020"
                        year_str = layer_str.split()[-1] if ' ' in layer_str else layer_str
                        result = add_hansen_layer(
                            m, year_str,
                            opacity=0.8, shown=True
                        )
                        if result is not None:
                            m = result
                            logger.info(f"✓ Added Hansen {year_str}")
                        else:
                            logger.warning(f"Failed to add Hansen {year_str}")
                    except Exception as e:
                        logger.warning(f"Error adding Hansen {layer_str}: {e}")
            except Exception as e:
                logger.error(f"Error with Hansen layers: {e}")
                import traceback
                traceback.print_exc()
        
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
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl(position='topright').add_to(m)
        
        return m._repr_html_()
        
    except Exception as e:
        logger.error(f"Critical error creating map: {e}")
        import traceback
        traceback.print_exc()
        
        # Return basic map on error
        m = folium.Map(location=[-5, -60], zoom_start=4, tiles="OpenStreetMap")
        folium.LayerControl().add_to(m)
        return m._repr_html_()


@router.post("/generate")
async def generate_map(
    mapbiomas_years: List[int] = None,
    hansen_layers: List[str] = None,
):
    """
    Generate a Folium map with selected Earth Engine layers.
    
    Query parameters:
    - mapbiomas_years: List of MapBiomas years (e.g., [1985, 2023])
    - hansen_layers: List of Hansen layer identifiers (e.g., ["2020"])
    
    Returns:
    - HTML string of the generated map
    """
    try:
        map_html = create_base_map_with_layers(
            mapbiomas_years=mapbiomas_years or [],
            hansen_layers=hansen_layers or [],
        )
        
        return {
            "map_html": map_html,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Error in generate_map endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test")
async def test_map():
    """Test endpoint - returns a basic map."""
    try:
        map_html = create_base_map_with_layers()
        return {"status": "ok", "map_html": map_html}
    except Exception as e:
        logger.error(f"Error in test_map: {e}")
        raise HTTPException(status_code=500, detail=str(e))
