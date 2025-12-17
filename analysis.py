'''
Analysis module for Yvynation.
Handles land cover analysis, change detection, and statistics.
'''

import ee
import pandas as pd
from config import MAPBIOMAS_LABELS


def clip_mapbiomas_to_geometry(mapbiomas, geometry, start_year, end_year):
    '''
    Clip MapBiomas data to specific geometry and year range.
    
    Args:
        mapbiomas (ee.Image): MapBiomas collection
        geometry (ee.Geometry): Area of interest
        start_year (int): Start year
        end_year (int): End year
    
    Returns:
        ee.Image: Clipped MapBiomas image
    '''
    bands = [f'classification_{year}' for year in range(start_year, end_year + 1)]
    clipped = mapbiomas.select(bands).clip(geometry)
    print(f"✓ Clipped MapBiomas data for {start_year}-{end_year}")
    return clipped


def calculate_area_by_class(image, geometry, year=None, scale=30):
    '''
    Calculate area for each land cover class in an image.
    
    Args:
        image (ee.Image): Classification image
        geometry (ee.Geometry): Area of interest
        year (int): Year to analyze (for MapBiomas band selection)
        scale (int): Analysis scale in meters
    
    Returns:
        pd.DataFrame: Area statistics by class
    '''
    band_names = image.bandNames().getInfo()
    
    # Determine which band to use
    if year is not None and f'classification_{year}' in band_names:
        classification_band = image.select(f'classification_{year}')
    elif len(band_names) == 1:
        classification_band = image.select(band_names[0])
    else:
        raise ValueError(f"Cannot determine classification band for year {year}")
    
    classification = classification_band.clip(geometry)
    
    # Calculate area by class
    area_image = ee.Image.pixelArea().divide(1e6)  # km²
    
    areas = area_image.addBands(classification).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName='class'),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    )
    
    try:
        result = areas.getInfo()['groups']
        df = pd.DataFrame(result)
        df.columns = ['Class_ID', 'Area_ha']
        df['Area_ha'] = df['Area_ha'] * 100  # Convert km² to hectares
        df['Class_Name'] = df['Class_ID'].map(MAPBIOMAS_LABELS)
        df['Year'] = year if year is not None else 'Classification'
        return df[['Year', 'Class_ID', 'Class_Name', 'Area_ha']].sort_values('Area_ha', ascending=False)
    except Exception as e:
        print(f"✗ Error calculating areas: {e}")
        return pd.DataFrame()


def calculate_land_cover_change(mapbiomas, geometry, start_year, end_year, scale=30):
    '''
    Calculate land cover change between two years.
    
    Args:
        mapbiomas (ee.Image): MapBiomas collection
        geometry (ee.Geometry): Area of interest
        start_year (int): Start year
        end_year (int): End year
        scale (int): Analysis scale
    
    Returns:
        dict: Change statistics and image
    '''
    start_band = f'classification_{start_year}'
    end_band = f'classification_{end_year}'
    
    start_class = mapbiomas.select(start_band).clip(geometry)
    end_class = mapbiomas.select(end_band).clip(geometry)
    
    # Binary change image
    change = start_class.neq(end_class)
    
    # Calculate total change area
    stats = change.multiply(ee.Image.pixelArea()).divide(1e6).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    )
    
    print(f"✓ Calculated change for {start_year}-{end_year}")
    return {
        'start_year': start_year,
        'end_year': end_year,
        'change_image': change,
        'change_area_km2': stats
    }


def get_class_specific_change(mapbiomas, geometry, start_year, end_year, class_id, scale=30):
    '''
    Calculate area change for a specific land cover class.
    
    Args:
        mapbiomas (ee.Image): MapBiomas collection
        geometry (ee.Geometry): Area of interest
        start_year (int): Start year
        end_year (int): End year
        class_id (int): MapBiomas class ID to track
        scale (int): Analysis scale
    
    Returns:
        dict: Class-specific change statistics
    '''
    start_band = f'classification_{start_year}'
    end_band = f'classification_{end_year}'
    
    start_class = mapbiomas.select(start_band).clip(geometry)
    end_class = mapbiomas.select(end_band).clip(geometry)
    
    # Areas with this class in start year
    start_presence = start_class.eq(class_id)
    end_presence = end_class.eq(class_id)
    
    # Loss and gain
    loss = start_presence.And(end_presence.Not())
    gain = end_presence.And(start_presence.Not())
    
    area_image = ee.Image.pixelArea().divide(1e6)
    
    loss_area = loss.multiply(area_image).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    ).getInfo()
    
    gain_area = gain.multiply(area_image).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    ).getInfo()
    
    class_name = MAPBIOMAS_LABELS.get(class_id, f'Class {class_id}')
    
    return {
        'class_id': class_id,
        'class_name': class_name,
        'loss_km2': loss_area.get('constant', 0),
        'gain_km2': gain_area.get('constant', 0),
        'loss_image': loss,
        'gain_image': gain
    }


def compare_areas(area_df1, area_df2):
    '''
    Compare land cover areas between two time periods.
    
    Args:
        area_df1 (pd.DataFrame): Area statistics from first period
        area_df2 (pd.DataFrame): Area statistics from second period
    
    Returns:
        pd.DataFrame: Comparison with changes
    '''
    comparison = area_df1[['Class_ID', 'Class_Name', 'Area_ha']].merge(
        area_df2[['Class_ID', 'Area_ha']],
        on='Class_ID',
        suffixes=('_start', '_end'),
        how='outer'
    ).fillna(0)
    
    comparison['Change_ha'] = comparison['Area_ha_end'] - comparison['Area_ha_start']
    comparison['Change_pct'] = (comparison['Change_ha'] / (comparison['Area_ha_start'] + 0.001)) * 100
    
    return comparison.sort_values('Change_ha', ascending=False)


def filter_territories_by_state(territories, state_code):
    '''
    Filter territories by Brazilian state code.
    
    Args:
        territories (ee.FeatureCollection): Territory features
        state_code (str): State code (e.g., 'MA', 'PA')
    
    Returns:
        ee.FeatureCollection: Filtered territories
    '''
    filtered = territories.filter(ee.Filter.eq('uf_sigla', state_code))
    count = filtered.size().getInfo()
    print(f"✓ Filtered to {count} territories in {state_code}")
    return filtered


def filter_territories_by_names(territories, names_list):
    '''
    Filter territories by name.
    
    Args:
        territories (ee.FeatureCollection): Territory features
        names_list (list): Territory names to filter
    
    Returns:
        ee.FeatureCollection: Filtered territories
    '''
    filters = [ee.Filter.eq('NAME', name) for name in names_list]
    combined_filter = ee.Filter.Or(*filters)
    filtered = territories.filter(combined_filter)
    count = filtered.size().getInfo()
    print(f"✓ Filtered to {count} territories")
    return filtered


def get_territory_info(territories):
    '''
    Get information about territories in a collection.
    
    Args:
        territories (ee.FeatureCollection): Territory features
    
    Returns:
        dict: Collection size and sample properties
    '''
    size = territories.size().getInfo()
    first_feature = territories.first().toDictionary().getInfo()
    
    return {
        'total_count': size,
        'sample_properties': first_feature
    }
