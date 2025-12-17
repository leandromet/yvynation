'''
Data loading and Earth Engine asset management for Yvynation.
Provides functions to load MapBiomas, SPOT, and satellite imagery.
'''

import ee
import pandas as pd
from config import (
    MAPBIOMAS_COLLECTIONS,
    TERRITORY_COLLECTIONS,
    SPOT_VISUAL_ASSET,
    SPOT_ANALYTIC_ASSET,
    FOREST_NDVI_THRESHOLD,
    URBAN_NDVI_THRESHOLD,
    MAPBIOMAS_LABELS,
)


# ==============================================================================
# MAPBIOMAS LOADING
# ==============================================================================

def load_mapbiomas(version='v9'):
    '''Load MapBiomas Brazil Collection.'''
    if version not in MAPBIOMAS_COLLECTIONS:
        raise ValueError(f"Unsupported version: {version}")
    
    asset_path = MAPBIOMAS_COLLECTIONS[version]
    try:
        mapbiomas = ee.Image(asset_path)
        print(f"✓ Loaded MapBiomas Collection {version}")
        return mapbiomas
    except Exception as e:
        print(f"✗ Error loading MapBiomas {version}: {e}")
        raise


def load_territories(territory_type='indigenous'):
    '''Load MapBiomas official territories.'''
    if territory_type not in TERRITORY_COLLECTIONS:
        raise ValueError(f"Unsupported type: {territory_type}")
    
    asset_path = TERRITORY_COLLECTIONS[territory_type]
    try:
        territories = ee.FeatureCollection(asset_path)
        count = territories.size().getInfo()
        print(f"✓ Loaded {count} {territory_type} territories")
        return territories
    except Exception as e:
        print(f"✗ Error loading territories: {e}")
        raise


# ==============================================================================
# SATELLITE DATA LOADING
# ==============================================================================

def load_sentinel2(roi, start_date, end_date, cloud_filter=20):
    '''Load Sentinel-2 imagery.'''
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', cloud_filter))
    )
    count = collection.size().getInfo()
    print(f"✓ Loaded {count} Sentinel-2 images")
    return collection


def load_spot_visual():
    '''Load SPOT visual (RGB) basemap.'''
    try:
        image = ee.Image(SPOT_VISUAL_ASSET)
        print(f"✓ Loaded SPOT visual basemap")
        return image
    except Exception as e:
        print(f"✗ Error loading SPOT visual: {e}")
        return None


def load_spot_analytic():
    '''Load SPOT analytic (multispectral) data.'''
    try:
        image = ee.Image(SPOT_ANALYTIC_ASSET)
        print(f"✓ Loaded SPOT analytic image")
        return image
    except Exception as e:
        print(f"✗ Error loading SPOT analytic: {e}")
        return None


# ==============================================================================
# CLASSIFICATION FUNCTIONS
# ==============================================================================

def classify_spot_ndvi(spot_image):
    '''Create land cover classification from SPOT using NDVI.'''
    if spot_image is None:
        print("✗ Cannot classify: SPOT image is None")
        return ee.Image.constant(0).rename('classification')

    band_names = spot_image.bandNames().getInfo()
    
    if 'N' not in band_names or 'R' not in band_names:
        print(f"✗ Missing NIR ('N') or Red ('R') bands")
        return ee.Image.constant(0).rename('classification')

    ndvi = spot_image.normalizedDifference(['N', 'R']).rename('ndvi')
    classification = ee.Image(0)
    classification = classification.where(ndvi.gt(FOREST_NDVI_THRESHOLD), 3)
    classification = classification.where(ndvi.lt(URBAN_NDVI_THRESHOLD), 24)
    classification = classification.where(
        ndvi.gte(URBAN_NDVI_THRESHOLD).And(ndvi.lte(FOREST_NDVI_THRESHOLD)), 15
    )
    print("✓ SPOT classification complete")
    return classification.rename('spot_classification')


# ==============================================================================
# AREA ANALYSIS
# ==============================================================================

def calculate_area_by_class(image, geometry, year=None, scale=30):
    '''Calculate area for each land cover class.'''
    area_image = ee.Image.pixelArea().divide(1e6)
    classified = image.clip(geometry)

    areas = area_image.addBands(classified).reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName='class'),
        geometry=geometry,
        scale=scale,
        maxPixels=1e13
    )

    try:
        result = areas.getInfo()['groups']
        df = pd.DataFrame(result)
        df.columns = ['Class_ID', 'Area_km2']
        df['Class_Name'] = df['Class_ID'].map(MAPBIOMAS_LABELS)
        if year:
            df['Year'] = year
        return df.sort_values('Area_km2', ascending=False)
    except Exception as e:
        print(f"✗ Error: {e}")
        return pd.DataFrame()


def get_deforestation(mapbiomas_v9, mapbiomas_v8, roi, forest_class=3, scale=30):
    '''Calculate deforestation between MapBiomas versions.'''
    forest_v9 = mapbiomas_v9.eq(forest_class).clip(roi)
    forest_v8 = mapbiomas_v8.eq(forest_class).clip(roi)
    deforestation = forest_v8.And(forest_v9.Not())
    
    area_m2 = deforestation.multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi,
        scale=scale,
        maxPixels=1e13
    )
    
    area_hectares = ee.Number(area_m2.get('constant')).divide(10000).getInfo()
    print(f"✓ Deforestation: {area_hectares:.0f} hectares")
    return {
        'deforestation_hectares': area_hectares,
        'deforestation_image': deforestation
    }


def filter_territories_by_state(territories, state_code):
    '''Filter territories by Brazilian state code.'''
    filtered = territories.filter(ee.Filter.eq('uf_sigla', state_code))
    count = filtered.size().getInfo()
    print(f"✓ Filtered to {count} territories in {state_code}")
    return filtered
