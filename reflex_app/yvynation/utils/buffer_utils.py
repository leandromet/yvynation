"""
Buffer utility functions for Yvynation Reflex app.
Creates external buffer zones (donut shapes) around geometries for analysis.
Ported from Streamlit version adapted for Reflex.
"""

import ee
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def create_external_buffer(geometry: ee.Geometry, distance_km: float) -> ee.Geometry:
    """
    Create an external buffer zone around a geometry (donut/ring shape).
    
    The buffer excludes the original geometry, creating a ring around it.
    This is useful for analyzing areas immediately adjacent to territories.
    
    Parameters:
    -----------
    geometry : ee.Geometry
        The input geometry to buffer
    distance_km : float
        Buffer distance in kilometers (e.g., 2, 5, 10)
    
    Returns:
    --------
    ee.Geometry
        External buffer geometry (donut shape)
    """
    try:
        # Convert km to meters for Earth Engine
        distance_meters = distance_km * 1000
        
        # Create the full buffer
        buffered = geometry.buffer(distance_meters)
        
        # Subtract the original geometry to create the external ring
        external_buffer = buffered.difference(geometry)
        
        return external_buffer
    
    except Exception as e:
        logger.error(f"Error creating buffer: {e}")
        return None


def create_buffer_geometry_dict(
    name: str,
    ee_geometry: ee.Geometry,
    buffer_size_km: float,
    source_name: str,
    created_at: str
) -> Dict[str, Any]:
    """
    Create a buffer geometry dictionary for storage in AppState.
    
    Parameters:
    -----------
    name : str
        Name for the buffer
    ee_geometry : ee.Geometry
        The Earth Engine geometry object
    buffer_size_km : float
        Buffer distance in kilometers
    source_name : str
        Name of the source (territory or uploaded file)
    created_at : str
        ISO timestamp of creation
    
    Returns:
    --------
    dict
        Buffer metadata and geometry info
    """
    return {
        'name': name,
        'source_name': source_name,
        'buffer_size_km': buffer_size_km,
        'geometry_type': 'external_buffer',
        'created_at': created_at,
        'ee_geometry': ee_geometry,  # Store the actual ee.Geometry object
    }


def convert_ee_geometry_to_geojson(ee_geometry: ee.Geometry) -> Optional[Dict[str, Any]]:
    """
    Convert an Earth Engine Geometry to GeoJSON.
    
    Parameters:
    -----------
    ee_geometry : ee.Geometry
        Earth Engine geometry object
    
    Returns:
    --------
    dict or None
        GeoJSON geometry dict, or None if conversion fails
    """
    try:
        # Call getInfo() to retrieve geometry from Earth Engine
        geojson = ee_geometry.getInfo()
        return geojson
    
    except Exception as e:
        logger.error(f"Error converting EE geometry to GeoJSON: {e}")
        return None


def convert_geojson_to_ee_geometry(geojson: Dict) -> Optional[ee.Geometry]:
    """
    Convert a GeoJSON dict to an Earth Engine Geometry.
    
    Parameters:
    -----------
    geojson : dict
        GeoJSON geometry or Feature
    
    Returns:
    --------
    ee.Geometry or None
        Earth Engine geometry, or None if conversion fails
    """
    try:
        # Extract geometry from Feature if needed
        if geojson.get('type') == 'Feature':
            geometry = geojson.get('geometry')
        else:
            geometry = geojson
        
        if not geometry:
            return None
        
        # Create ee.Geometry from GeoJSON
        ee_geometry = ee.Geometry(geometry)
        return ee_geometry
    
    except Exception as e:
        logger.error(f"Error converting GeoJSON to EE geometry: {e}")
        return None


def convert_feature_collection_to_ee_geometry(geojson_fc: Dict) -> Optional[ee.Geometry]:
    """
    Convert a GeoJSON FeatureCollection to an Earth Engine Geometry.
    
    Merges all features into a single geometry.
    
    Parameters:
    -----------
    geojson_fc : dict
        GeoJSON FeatureCollection
    
    Returns:
    --------
    ee.Geometry or None
        Merged geometry from all features
    """
    try:
        if geojson_fc.get('type') != 'FeatureCollection':
            return None
        
        features = geojson_fc.get('features', [])
        if not features:
            return None
        
        # Convert each feature to ee.Geometry
        geometries = []
        for feature in features:
            geom = convert_geojson_to_ee_geometry(feature)
            if geom:
                geometries.append(geom)
        
        if not geometries:
            return None
        
        # Merge all geometries
        if len(geometries) == 1:
            return geometries[0]
        
        merged = geometries[0]
        for geom in geometries[1:]:
            merged = merged.union(geom)
        
        return merged
    
    except Exception as e:
        logger.error(f"Error converting FeatureCollection to EE geometry: {e}")
        return None


def get_geometry_bounds(ee_geometry: ee.Geometry) -> Optional[Dict[str, float]]:
    """
    Get the bounds of an Earth Engine Geometry.
    
    Parameters:
    -----------
    ee_geometry : ee.Geometry
        Earth Engine geometry
    
    Returns:
    --------
    dict or None
        Dict with 'min_lon', 'min_lat', 'max_lon', 'max_lat', or None if fails
    """
    try:
        bounds = ee_geometry.bounds().getInfo()
        
        if bounds and 'type' == 'Polygon':
            coords = bounds.get('coordinates', [[]])[0]
            if coords:
                lons = [c[0] for c in coords]
                lats = [c[1] for c in coords]
                
                return {
                    'min_lon': min(lons),
                    'min_lat': min(lats),
                    'max_lon': max(lons),
                    'max_lat': max(lats),
                }
        
        return None
    
    except Exception as e:
        logger.error(f"Error getting geometry bounds: {e}")
        return None
