"""
Territory Analysis Module for Yvynation.
Handles indigenous territory data analysis, visualization, and comparison.
"""

import streamlit as st
import ee
import pandas as pd


def get_territory_names(territories_fc):
    """
    Extract territory names from Earth Engine feature collection.
    
    Args:
        territories_fc (ee.FeatureCollection): Indigenous territories collection
    
    Returns:
        tuple: (sorted_names, name_property) or (None, None) if error
    """
    try:
        first_feature = territories_fc.first().getInfo()
        available_props = list(first_feature.get('properties', {}).keys()) if first_feature else []
        
        # Try different property names
        name_prop = None
        for prop in ['name', 'Nome', 'NAME', 'territorio_nome', 'territory_name', 'TERRITORY_NAME']:
            if prop in available_props:
                name_prop = prop
                break
        
        if not name_prop:
            return None, None
        
        # Get sorted territory names
        territory_names = sorted(territories_fc.aggregate_array(name_prop).getInfo())
        return territory_names, name_prop
    
    except Exception as e:
        print(f"❌ Error getting territory names: {e}")
        return None, None


def get_territory_geometry(territories_fc, territory_name, name_prop):
    """
    Extract geometry for a specific territory.
    
    Args:
        territories_fc (ee.FeatureCollection): Indigenous territories collection
        territory_name (str): Name of territory to extract
        name_prop (str): Property name containing territory names
    
    Returns:
        ee.Geometry: Territory geometry or None if error
    """
    try:
        territory_geom = territories_fc.filter(
            ee.Filter.eq(name_prop, territory_name)
        ).first().geometry()
        return territory_geom
    except Exception as e:
        print(f"❌ Error getting territory geometry: {e}")
        return None


def analyze_territory_mapbiomas(mapbiomas, territory_geom, year):
    """
    Analyze MapBiomas land cover in a territory.
    
    Args:
        mapbiomas (ee.ImageCollection): MapBiomas collection
        territory_geom (ee.Geometry): Territory geometry
        year (int): Year to analyze
    
    Returns:
        pd.DataFrame: Land cover area by class
    """
    try:
        from mapbiomas_analysis import calculate_area_by_class as mapbiomas_area_analysis
        
        band = f'classification_{year}'
        area_df = mapbiomas_area_analysis(
            mapbiomas.select(band),
            territory_geom,
            year
        )
        return area_df
    except Exception as e:
        print(f"❌ Error analyzing MapBiomas: {e}")
        raise


def analyze_territory_hansen(ee_module, territory_geom, year, use_consolidated=False):
    """
    Analyze Hansen/GLAD forest change in a territory.
    
    Args:
        ee_module: Earth Engine module
        territory_geom (ee.Geometry): Territory geometry
        year (str): Year to analyze
        use_consolidated (bool): Use consolidated classes
    
    Returns:
        pd.DataFrame: Land cover area by class
    """
    try:
        from hansen_analysis import hansen_histogram_to_dataframe
        
        hansen_year_key = str(year)
        region_hist = ee_module.Image(
            "UMD/Hansen/global_forest_change_2020_v1_8"
        ).reduceRegion(
            reducer=ee_module.Reducer.frequencyHistogram(),
            geometry=territory_geom,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        area_df = hansen_histogram_to_dataframe(
            region_hist,
            hansen_year_key,
            use_consolidated
        )
        return area_df
    except Exception as e:
        print(f"❌ Error analyzing Hansen: {e}")
        raise


def initialize_territory_session_state():
    """Initialize all territory-related session state variables."""
    if "territory_result" not in st.session_state:
        st.session_state.territory_result = None
    if "territory_result_year2" not in st.session_state:
        st.session_state.territory_result_year2 = None
    if "territory_name" not in st.session_state:
        st.session_state.territory_name = None
    if "territory_year" not in st.session_state:
        st.session_state.territory_year = None
    if "territory_year2" not in st.session_state:
        st.session_state.territory_year2 = None
    if "territory_geom" not in st.session_state:
        st.session_state.territory_geom = None
    if "territory_source" not in st.session_state:
        st.session_state.territory_source = "MapBiomas"
    if "add_territory_layer_to_map" not in st.session_state:
        st.session_state.add_territory_layer_to_map = False
    if "territory_layer_name" not in st.session_state:
        st.session_state.territory_layer_name = None
