"""
Generic analysis utilities for Yvynation Reflex app.
Handles common Earth Engine operations for land cover analysis.
Ported from original analysis.py, adapted for Reflex (no Streamlit deps).
"""

import ee
import pandas as pd
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def clip_classification_to_geometry(
    classification_image: ee.Image, 
    geometry: ee.Geometry, 
    start_year: int = None,
    end_year: int = None
) -> ee.Image:
    """
    Clip classification image to specific geometry and year range.
    
    Args:
        classification_image: EE classification image
        geometry: Area of interest
        start_year: Start year (for band selection)
        end_year: End year (for band selection)
    
    Returns:
        Clipped EE image
    """
    try:
        if start_year and end_year:
            # Select bands for year range
            bands = [f'classification_{year}' for year in range(start_year, end_year + 1)]
            clipped = classification_image.select(bands).clip(geometry)
        else:
            # Just clip without band selection
            clipped = classification_image.clip(geometry)
        
        logger.info(f"Clipped classification for {start_year}-{end_year if start_year and end_year else 'all years'}")
        return clipped
    
    except Exception as e:
        logger.error(f"Error clipping classification: {e}")
        return None


def calculate_area_by_class(
    image: ee.Image,
    geometry: ee.Geometry,
    year: Optional[int] = None,
    scale: int = 30,
    class_labels: Dict[int, str] = None
) -> pd.DataFrame:
    """
    Calculate area for each land cover class in an image.
    
    Args:
        image: Classification image
        geometry: Area of interest
        year: Year to analyze (for band selection)
        scale: Analysis scale in meters
        class_labels: Dictionary mapping class IDs to names
    
    Returns:
        DataFrame with area statistics by class
    """
    try:
        # Select band if year specified
        band_names = image.bandNames().getInfo()
        
        if year is not None and f'classification_{year}' in band_names:
            classification_band = image.select(f'classification_{year}')
        elif len(band_names) == 1:
            classification_band = image.select(band_names[0])
        elif len(band_names) > 1:
            # Use first band if year not found
            classification_band = image.select(band_names[0])
        else:
            logger.error(f"No suitable band found for year {year}")
            return pd.DataFrame()
        
        # Clip to geometry
        classification = classification_band.clip(geometry)
        
        # Calculate area by class using pixelArea
        area_image = ee.Image.pixelArea().divide(1e6)  # Convert to km²
        
        # Reduce region to get area by class
        areas = area_image.addBands(classification).reduceRegion(
            reducer=ee.Reducer.sum().group(groupField=1, groupName='class'),
            geometry=geometry,
            scale=scale,
            maxPixels=1e13
        )
        
        result = areas.getInfo()
        
        # Handle empty results
        if not result or 'groups' not in result:
            logger.warning(f"No classification data found for year {year}")
            return pd.DataFrame()
        
        # Parse results into DataFrame
        groups = result.get('groups', [])
        if not groups:
            return pd.DataFrame()
        
        records = []
        for group in groups:
            class_id = int(group['group'])
            area_km2 = group.get('sum', 0)
            area_ha = area_km2 * 100  # Convert km² to hectares
            
            class_name = class_labels.get(class_id, f'Class {class_id}') if class_labels else f'Class {class_id}'
            
            records.append({
                'Year': year if year else 'All',
                'Class_ID': class_id,
                'Class_Name': class_name,
                'Area_ha': area_ha,
                'Area_km2': area_km2,
            })
        
        df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
        logger.info(f"Calculated areas for {len(df)} classes")
        return df
    
    except Exception as e:
        logger.error(f"Error calculating areas: {e}")
        return pd.DataFrame()


def calculate_change_area(
    image_start: ee.Image,
    image_end: ee.Image,
    geometry: ee.Geometry,
    scale: int = 30
) -> Dict[str, Any]:
    """
    Calculate total area of change between two classification images.
    
    Args:
        image_start: Start year classification
        image_end: End year classification
        geometry: Area of interest
        scale: Analysis scale
    
    Returns:
        Dictionary with change statistics
    """
    try:
        # Clip both images
        start = image_start.clip(geometry)
        end = image_end.clip(geometry)
        
        # Create binary change image (1 where classes differ, 0 where same)
        change = start.neq(end).cast({'type': 'uint8'})
        
        # Calculate change area
        area_image = ee.Image.pixelArea().divide(1e6)  # km²
        change_area_result = change.multiply(area_image).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e13
        ).getInfo()
        
        change_area_km2 = change_area_result.get('constant', 0) if change_area_result else 0
        change_area_ha = change_area_km2 * 100
        
        logger.info(f"Calculated change area: {change_area_km2:.2f} km²")
        
        return {
            'change_area_km2': change_area_km2,
            'change_area_ha': change_area_ha,
            'change_image': change,
        }
    
    except Exception as e:
        logger.error(f"Error calculating change: {e}")
        return {'change_area_km2': 0, 'change_area_ha': 0, 'change_image': None}


def calculate_class_specific_change(
    image_start: ee.Image,
    image_end: ee.Image,
    geometry: ee.Geometry,
    class_id: int,
    scale: int = 30,
    class_labels: Dict[int, str] = None
) -> Dict[str, Any]:
    """
    Calculate loss and gain for a specific class between two years.
    
    Args:
        image_start: Start classification
        image_end: End classification
        geometry: Area of interest
        class_id: Class ID to track
        scale: Analysis scale
        class_labels: Dictionary mapping class IDs to names
    
    Returns:
        Dictionary with loss/gain statistics
    """
    try:
        # Clip both images
        start = image_start.clip(geometry)
        end = image_end.clip(geometry)
        
        # Binary images for class presence
        start_presence = start.eq(class_id)
        end_presence = end.eq(class_id)
        
        # Loss and gain
        loss = start_presence.And(end_presence.Not())
        gain = end_presence.And(start_presence.Not())
        
        # Calculate areas
        area_image = ee.Image.pixelArea().divide(1e6)  # km²
        
        loss_area_km2 = loss.multiply(area_image).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e13
        ).getInfo().get('constant', 0)
        
        gain_area_km2 = gain.multiply(area_image).reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=geometry,
            scale=scale,
            maxPixels=1e13
        ).getInfo().get('constant', 0)
        
        class_name = class_labels.get(class_id, f'Class {class_id}') if class_labels else f'Class {class_id}'
        
        logger.info(f"Class {class_id} ({class_name}): Loss={loss_area_km2:.2f} km², Gain={gain_area_km2:.2f} km²")
        
        return {
            'class_id': class_id,
            'class_name': class_name,
            'loss_km2': loss_area_km2,
            'loss_ha': loss_area_km2 * 100,
            'gain_km2': gain_area_km2,
            'gain_ha': gain_area_km2 * 100,
            'loss_image': loss,
            'gain_image': gain,
        }
    
    except Exception as e:
        logger.error(f"Error calculating class-specific change: {e}")
        return {
            'class_id': class_id,
            'class_name': 'Unknown',
            'loss_km2': 0,
            'loss_ha': 0,
            'gain_km2': 0,
            'gain_ha': 0,
            'loss_image': None,
            'gain_image': None,
        }


def compare_areas(
    df_start: pd.DataFrame,
    df_end: pd.DataFrame,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None
) -> pd.DataFrame:
    """
    Compare land cover areas between two time periods.
    
    Args:
        df_start: Area statistics from start year
        df_end: Area statistics from end year
        year_start: Start year label
        year_end: End year label
    
    Returns:
        DataFrame with comparison and change metrics
    """
    try:
        if df_start.empty or df_end.empty:
            logger.warning("Cannot compare empty DataFrames")
            return pd.DataFrame()
        
        # Merge on Class_ID
        comparison = df_start[['Class_ID', 'Class_Name', 'Area_ha']].merge(
            df_end[['Class_ID', 'Area_ha']],
            on='Class_ID',
            suffixes=('_start', '_end'),
            how='outer'
        ).fillna(0)
        
        # Calculate change
        comparison['Change_ha'] = comparison['Area_ha_end'] - comparison['Area_ha_start']
        comparison['Change_pct'] = (comparison['Change_ha'] / (comparison['Area_ha_start'] + 1)) * 100
        
        # Add years
        if year_start:
            comparison['Year_Start'] = year_start
        if year_end:
            comparison['Year_End'] = year_end
        
        logger.info(f"Compared areas across {comparison.shape[0]} classes")
        return comparison.sort_values('Change_ha', ascending=False)
    
    except Exception as e:
        logger.error(f"Error comparing areas: {e}")
        return pd.DataFrame()


def get_geometry_bounds(geometry: ee.Geometry) -> Optional[Dict[str, float]]:
    """
    Get bounding box of an Earth Engine geometry.
    
    Args:
        geometry: EE geometry
    
    Returns:
        Dict with 'min_lon', 'min_lat', 'max_lon', 'max_lat'
    """
    try:
        bounds = geometry.bounds().getInfo()
        
        if bounds and bounds.get('type') == 'Polygon':
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
