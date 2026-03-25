"""
Geometry file upload and parsing utilities.
Handles KML, GeoJSON, and other geometry format uploads.
"""

import json
import streamlit as st
from typing import Optional, List, Dict, Any
import xml.etree.ElementTree as ET


def parse_geojson(file_content: str, file_name: str = "") -> Optional[Dict]:
    """
    Parse a GeoJSON file.
    
    Args:
        file_content: String content of the GeoJSON file
        file_name: Optional file name for default feature naming
        
    Returns:
        Parsed GeoJSON object or None if parsing fails
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
                # Raw geometry
                feature_name = file_name.rsplit('.', 1)[0] if file_name else "Uploaded Geometry"
                return {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"name": feature_name},
                        "geometry": data
                    }]
                }
        
        st.error("Invalid GeoJSON format")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON: {str(e)[:100]}")
        return None
    except Exception as e:
        st.error(f"Error parsing GeoJSON: {str(e)[:100]}")
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
            st.error("No placemarks found in KML file")
            return None
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    except ET.ParseError as e:
        st.error(f"Invalid KML format: {str(e)[:100]}")
        return None
    except Exception as e:
        st.error(f"Error parsing KML: {str(e)[:100]}")
        return None


def _placemark_to_geojson(placemark, ns, base_name: str = "Feature", feature_idx: int = 0) -> Optional[Dict]:
    """
    Convert a KML Placemark to GeoJSON Feature.
    
    Args:
        placemark: XML Placemark element
        ns: Namespace dictionary
        base_name: Base name for features (e.g., "territories")
        feature_idx: Index of this feature (used for numbering)
    """
    try:
        # Extract name and description
        name_elem = placemark.find('kml:name', ns)
        desc_elem = placemark.find('kml:description', ns)
        
        # Use file name based name if no name in KML, otherwise use KML name
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
        print(f"Error converting placemark: {e}")
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
        print(f"Error parsing coordinates: {e}")
        return None


def render_geometry_uploader():
    """
    Render a file uploader for geometry files (KML, GeoJSON).
    Returns tuple of (uploaded_features, file_names) or (None, None).
    """
    st.markdown("### 📤 Upload Geometry Files")
    st.caption("Upload KML or GeoJSON files instead of drawing. Multiple files are supported.")
    
    uploaded_files = st.file_uploader(
        "Choose geometry files",
        type=['geojson', 'json', 'kml'],
        accept_multiple_files=True,
        key="geometry_file_uploader"
    )
    
    if not uploaded_files:
        return None, None
    
    all_features = []
    file_names = []
    
    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        
        try:
            # Read file content
            content = uploaded_file.read().decode('utf-8')
            
            geojson_data = None
            
            # Determine file type and parse
            if file_name.lower().endswith('.kml'):
                geojson_data = parse_kml(content, file_name)
            elif file_name.lower().endswith(('.geojson', '.json')):
                geojson_data = parse_geojson(content, file_name)
            else:
                st.warning(f"Unknown file type: {file_name}")
                continue
            
            if geojson_data and 'features' in geojson_data:
                st.success(f"✓ {file_name}: {len(geojson_data['features'])} feature(s) loaded")
                all_features.extend(geojson_data['features'])
                # Store file name for each feature from this file
                file_names.extend([file_name] * len(geojson_data['features']))
        
        except Exception as e:
            st.error(f"Error reading {file_name}: {str(e)[:100]}")
    
    return (all_features, file_names) if all_features else (None, None)


def add_uploaded_features_to_session(features: List[Dict], file_names: List[str] = None):
    """
    Add uploaded features to session state.
    Combines with drawn features and marks them as uploaded.
    
    Args:
        features: List of GeoJSON Feature objects
        file_names: List of file names corresponding to features (for naming)
    """
    if not features:
        return
    
    if not file_names:
        file_names = [f"Feature"] * len(features)
    
    # Initialize if needed
    if 'all_drawn_features' not in st.session_state:
        st.session_state.all_drawn_features = []
    
    if 'uploaded_features_metadata' not in st.session_state:
        st.session_state.uploaded_features_metadata = {}
    
    # Add each feature
    for i, feature in enumerate(features):
        # Mark as uploaded
        feature['properties'] = feature.get('properties', {})
        feature['properties']['source'] = 'uploaded'
        
        # Get file name without extension
        file_display_name = file_names[i].rsplit('.', 1)[0] if i < len(file_names) else f"Feature {i + 1}"
        
        # Use existing name if present, otherwise use file name
        feature_name = feature['properties'].get('name', file_display_name)
        
        # Store metadata
        feature_idx = len(st.session_state.all_drawn_features)
        st.session_state.uploaded_features_metadata[feature_idx] = {
            'name': feature_name,
            'description': feature['properties'].get('description', ''),
            'source': 'file',
            'file_name': file_names[i] if i < len(file_names) else 'unknown'
        }
        
        # Add to session
        st.session_state.all_drawn_features.append(feature)
    
    st.success(f"✅ {len(features)} feature(s) added to map. Select one to analyze.")
    st.rerun()
