"""
Geometry file parsing utilities for Yvynation Reflex app.
Handles KML, GeoJSON, and Shapefile format parsing and validation.
Ported from Streamlit version without st.* references.
"""

import json
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def parse_geojson(file_content: str, file_name: str = "") -> Optional[Dict]:
    """
    Parse a GeoJSON file.
    
    Args:
        file_content: String content of the GeoJSON file
        file_name: Optional file name for default feature naming
        
    Returns:
        Parsed GeoJSON FeatureCollection or None if parsing fails
    """
    try:
        data = json.loads(file_content)
        
        # Validate it's valid GeoJSON
        if 'type' in data:
            if data['type'] == 'FeatureCollection' and 'features' in data:
                return data
            elif data['type'] == 'Feature' and 'geometry' in data:
                return {"type": "FeatureCollection", "features": [data]}
            elif data['type'] in ['Point', 'LineString', 'Polygon', 'MultiPolygon', 'MultiLineString', 'MultiPoint']:
                # Raw geometry - wrap in Feature
                feature_name = file_name.rsplit('.', 1)[0] if file_name else "Uploaded Geometry"
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"name": feature_name},
                        "geometry": data
                    }]
                }
        
        logger.error(f"Invalid GeoJSON format in {file_name}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_name}: {str(e)[:100]}")
        return None
    except Exception as e:
        logger.error(f"Error parsing GeoJSON {file_name}: {str(e)[:100]}")
        return None


def parse_kml(file_content: str, file_name: str = "") -> Optional[Dict]:
    """
    Parse a KML file and convert to GeoJSON.
    
    Args:
        file_content: String content of the KML file
        file_name: Optional file name for default feature naming
        
    Returns:
        GeoJSON FeatureCollection or None if parsing fails
    """
    try:
        root = ET.fromstring(file_content)
        
        # Handle KML namespace
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        features = []
        base_name = file_name.rsplit('.', 1)[0] if file_name else "KML Feature"
        
        # Extract Placemarks (features)
        for idx, placemark in enumerate(root.findall('.//kml:Placemark', ns)):
            feature = _placemark_to_geojson(placemark, ns, base_name, idx)
            if feature:
                features.append(feature)
        
        if not features:
            logger.error(f"No placemarks found in KML file {file_name}")
            return None
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    except ET.ParseError as e:
        logger.error(f"Invalid KML format in {file_name}: {str(e)[:100]}")
        return None
    except Exception as e:
        logger.error(f"Error parsing KML {file_name}: {str(e)[:100]}")
        return None


def _placemark_to_geojson(placemark, ns, base_name: str = "Feature", feature_idx: int = 0) -> Optional[Dict]:
    """
    Convert a KML Placemark to GeoJSON Feature.
    
    Args:
        placemark: XML Placemark element
        ns: Namespace dictionary
        base_name: Base name for features
        feature_idx: Index of this feature for numbering
    """
    try:
        # Extract name and description
        name_elem = placemark.find('kml:name', ns)
        desc_elem = placemark.find('kml:description', ns)
        
        default_name = name_elem.text if name_elem is not None and name_elem.text else f"{base_name} (Feature {feature_idx + 1})"
        
        properties = {
            'name': default_name,
            'description': desc_elem.text if desc_elem is not None else ''
        }
        
        # Extract geometry
        geometry = None
        
        # Point
        point = placemark.find('.//kml:Point/kml:coordinates', ns)
        if point is not None and point.text:
            coords = point.text.strip().split(',')
            if len(coords) >= 2:
                geometry = {
                    "type": "Point",
                    "coordinates": [float(coords[0]), float(coords[1])]
                }
        
        # LineString
        if geometry is None:
            linestring = placemark.find('.//kml:LineString/kml:coordinates', ns)
            if linestring is not None and linestring.text:
                coords = _parse_kml_coordinates(linestring.text)
                if coords:
                    geometry = {
                        "type": "LineString",
                        "coordinates": coords
                    }
        
        # Polygon
        if geometry is None:
            polygon = placemark.find('.//kml:Polygon', ns)
            if polygon is not None:
                outer = polygon.find('kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', ns)
                if outer is not None and outer.text:
                    outer_coords = _parse_kml_coordinates(outer.text)
                    if outer_coords:
                        coordinates = [outer_coords]
                        
                        # Inner boundaries (holes)
                        for inner in polygon.findall('kml:innerBoundaryIs/kml:LinearRing/kml:coordinates', ns):
                            if inner.text:
                                inner_coords = _parse_kml_coordinates(inner.text)
                                if inner_coords:
                                    coordinates.append(inner_coords)
                        
                        geometry = {
                            "type": "Polygon",
                            "coordinates": coordinates
                        }
        
        if geometry:
            return {
                "type": "Feature",
                "properties": properties,
                "geometry": geometry
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Error converting placemark: {e}")
        return None


def _parse_kml_coordinates(coord_str: str) -> Optional[List]:
    """
    Parse KML coordinates string (lon,lat,alt lon,lat,alt ...).
    Returns list of [lon, lat] arrays.
    """
    try:
        coords = []
        for coord_tuple in coord_str.strip().split():
            parts = coord_tuple.split(',')
            if len(parts) >= 2:
                coords.append([float(parts[0]), float(parts[1])])
        return coords if coords else None
    except Exception as e:
        logger.error(f"Error parsing coordinates: {e}")
        return None


def validate_geometry(geojson_data: Dict) -> tuple[bool, str]:
    """
    Validate a GeoJSON structure and bounds.
    
    Args:
        geojson_data: GeoJSON FeatureCollection or Feature
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not isinstance(geojson_data, dict):
            return False, "GeoJSON must be a dictionary"
        
        # Check if it's a FeatureCollection
        if geojson_data.get('type') == 'FeatureCollection':
            if 'features' not in geojson_data:
                return False, "FeatureCollection must have 'features' property"
            
            if not geojson_data['features']:
                return False, "FeatureCollection has no features"
            
            # Validate each feature
            for idx, feature in enumerate(geojson_data['features']):
                valid, msg = _validate_feature(feature)
                if not valid:
                    return False, f"Feature {idx}: {msg}"
        
        elif geojson_data.get('type') == 'Feature':
            valid, msg = _validate_feature(geojson_data)
            if not valid:
                return False, msg
        else:
            return False, "GeoJSON must be a Feature or FeatureCollection"
        
        return True, ""
    
    except Exception as e:
        return False, f"Validation error: {str(e)[:100]}"


def _validate_feature(feature: Dict) -> tuple[bool, str]:
    """Validate a single GeoJSON Feature."""
    try:
        if not isinstance(feature, dict):
            return False, "Feature must be a dictionary"
        
        if feature.get('type') != 'Feature':
            return False, "Must be type 'Feature'"
        
        if 'geometry' not in feature:
            return False, "Missing 'geometry' property"
        
        geometry = feature['geometry']
        if not geometry or 'type' not in geometry:
            return False, "Invalid geometry structure"
        
        geom_type = geometry['type']
        valid_types = ['Point', 'LineString', 'Polygon', 'MultiPoint', 'MultiLineString', 'MultiPolygon']
        
        if geom_type not in valid_types:
            return False, f"Invalid geometry type: {geom_type}"
        
        if 'coordinates' not in geometry:
            return False, "Geometry missing 'coordinates' property"
        
        return True, ""
    
    except Exception as e:
        return False, f"Feature validation error: {str(e)[:100]}"


def get_bbox_from_geojson(geojson_data: Dict) -> Optional[List[float]]:
    """
    Calculate bounding box from GeoJSON.
    
    Args:
        geojson_data: GeoJSON FeatureCollection or Feature
        
    Returns:
        Bounding box [min_lon, min_lat, max_lon, max_lat] or None
    """
    try:
        lons = []
        lats = []
        
        features = geojson_data.get('features', [geojson_data]) if geojson_data.get('type') == 'FeatureCollection' else [geojson_data]
        
        for feature in features:
            if feature.get('type') == 'Feature':
                coords = _extract_all_coords(feature.get('geometry', {}))
                for lon, lat in coords:
                    lons.append(lon)
                    lats.append(lat)
        
        if lons and lats:
            return [min(lons), min(lats), max(lons), max(lats)]
        
        return None
    
    except Exception as e:
        logger.error(f"Error calculating bbox: {e}")
        return None


def _extract_all_coords(geometry: Dict) -> List[tuple]:
    """Extract all [lon, lat] tuples from a geometry."""
    coords = []
    
    if not geometry:
        return coords
    
    geom_type = geometry.get('type')
    geom_coords = geometry.get('coordinates', [])
    
    if geom_type == 'Point':
        coords.append(tuple(geom_coords[:2]))
    elif geom_type == 'LineString':
        coords.extend([tuple(c[:2]) for c in geom_coords])
    elif geom_type == 'Polygon':
        for ring in geom_coords:
            coords.extend([tuple(c[:2]) for c in ring])
    elif geom_type == 'MultiPoint':
        coords.extend([tuple(c[:2]) for c in geom_coords])
    elif geom_type == 'MultiLineString':
        for line in geom_coords:
            coords.extend([tuple(c[:2]) for c in line])
    elif geom_type == 'MultiPolygon':
        for polygon in geom_coords:
            for ring in polygon:
                coords.extend([tuple(c[:2]) for c in ring])
    
    return coords
