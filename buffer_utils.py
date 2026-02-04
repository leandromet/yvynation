"""
Buffer utility functions for creating external buffer zones around territories and polygons.
Creates donut-shaped buffers (buffer minus original geometry) for analysis.
"""

import streamlit as st
import ee


def create_external_buffer(geometry, distance_km):
    """
    Create an external buffer zone around a geometry (donut/ring shape).
    
    The buffer excludes the original geometry, creating a ring around it.
    This is useful for analyzing areas immediately adjacent to territories or polygons.
    
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
    # Convert km to meters for Earth Engine
    distance_meters = distance_km * 1000
    
    # Create the full buffer
    buffered = geometry.buffer(distance_meters)
    
    # Subtract the original geometry to create the external ring (donut shape)
    external_buffer = buffered.difference(geometry)
    
    return external_buffer


def add_buffer_to_session_state(geometry, buffer_size_km, source_name):
    """
    Create a buffer and add it to session state for analysis.
    
    Parameters:
    -----------
    geometry : ee.Geometry
        The source geometry to buffer
    buffer_size_km : float
        Buffer distance in kilometers
    source_name : str
        Name of the source (territory name or "Polygon N")
    
    Returns:
    --------
    str
        Name of the created buffer for reference
    """
    # Initialize buffer storage in session state if not exists
    if 'buffer_geometries' not in st.session_state:
        st.session_state.buffer_geometries = {}
    if 'buffer_metadata' not in st.session_state:
        st.session_state.buffer_metadata = {}
    
    # Create the buffer
    buffer_geom = create_external_buffer(geometry, buffer_size_km)
    
    # Create a unique name for this buffer
    buffer_name = f"External Buffer {buffer_size_km}km - {source_name}"
    
    # Store in session state
    st.session_state.buffer_geometries[buffer_name] = buffer_geom
    st.session_state.buffer_metadata[buffer_name] = {
        'source_name': source_name,
        'buffer_size_km': buffer_size_km,
        'source_geometry': geometry,
        'type': 'external_buffer'
    }
    
    return buffer_name


def get_buffer_as_feature(buffer_name):
    """
    Convert a stored buffer to a GeoJSON-like feature for adding to all_drawn_features.
    
    Parameters:
    -----------
    buffer_name : str
        Name of the buffer in session state
    
    Returns:
    --------
    dict
        GeoJSON-like feature dictionary compatible with all_drawn_features
    """
    if buffer_name not in st.session_state.buffer_geometries:
        return None
    
    buffer_geom = st.session_state.buffer_geometries[buffer_name]
    
    # Get the GeoJSON representation from Earth Engine
    buffer_geojson = buffer_geom.getInfo()
    
    # Create feature structure compatible with drawn features
    feature = {
        'type': 'Feature',
        'geometry': buffer_geojson,
        'properties': {
            'name': buffer_name,
            'type': 'external_buffer',
            'metadata': st.session_state.buffer_metadata.get(buffer_name, {})
        }
    }
    
    return feature


def add_buffer_to_polygon_list(buffer_name):
    """
    Add a buffer to the all_drawn_features list so it appears in the polygon selector.
    
    Parameters:
    -----------
    buffer_name : str
        Name of the buffer to add
    """
    # Initialize if needed
    if 'all_drawn_features' not in st.session_state:
        st.session_state.all_drawn_features = []
    
    # Get the feature representation
    buffer_feature = get_buffer_as_feature(buffer_name)
    
    if buffer_feature:
        # Check if this buffer is already in the list
        existing_names = [
            f.get('properties', {}).get('name', '')
            for f in st.session_state.all_drawn_features
        ]
        
        if buffer_name not in existing_names:
            st.session_state.all_drawn_features.append(buffer_feature)
            return True
    
    return False


def get_buffer_info(buffer_name):
    """
    Get metadata information about a buffer.
    
    Parameters:
    -----------
    buffer_name : str
        Name of the buffer
    
    Returns:
    --------
    dict or None
        Buffer metadata if exists
    """
    return st.session_state.buffer_metadata.get(buffer_name)


def remove_buffer(buffer_name):
    """
    Remove a buffer from session state.
    
    Parameters:
    -----------
    buffer_name : str
        Name of the buffer to remove
    """
    # Remove from geometries
    if buffer_name in st.session_state.buffer_geometries:
        del st.session_state.buffer_geometries[buffer_name]
    
    # Remove from metadata
    if buffer_name in st.session_state.buffer_metadata:
        del st.session_state.buffer_metadata[buffer_name]
    
    # Remove from all_drawn_features
    if 'all_drawn_features' in st.session_state:
        st.session_state.all_drawn_features = [
            f for f in st.session_state.all_drawn_features
            if f.get('properties', {}).get('name', '') != buffer_name
        ]


def list_all_buffers():
    """
    Get a list of all buffer names currently in session state.
    
    Returns:
    --------
    list
        List of buffer names
    """
    if 'buffer_geometries' not in st.session_state:
        return []
    
    return list(st.session_state.buffer_geometries.keys())
