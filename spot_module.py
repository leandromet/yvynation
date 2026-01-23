'''
SPOT Module for Yvynation.
Handles SPOT 2008 satellite data and classification.

⚠️  RESTRICTED ACCESS WARNING
SPOT data requires special permissions. This module is separated from the main app
to handle access restrictions gracefully. Check access before using.
'''

import ee
from config import SPOT_ANALYTIC_ASSET, SPOT_VISUAL_ASSET, FOREST_NDVI_THRESHOLD, URBAN_NDVI_THRESHOLD


# ==============================================================================
# SPOT DATA LOADING (RESTRICTED ACCESS)
# ==============================================================================

def check_spot_access():
    '''
    Check if SPOT data is accessible.
    
    Returns:
        bool: True if accessible, False otherwise
    '''
    try:
        test_image = ee.Image(SPOT_ANALYTIC_ASSET)
        test_image.bandNames().getInfo()
        print("✓ SPOT data access confirmed")
        return True
    except Exception as e:
        print(f"✗ SPOT data access denied: {e}")
        print("  This dataset requires special permissions from Google Earth Engine.")
        return False


def load_spot_analytic():
    '''
    Load SPOT 2008 analytic (multispectral) data.
    
    Returns:
        ee.Image: SPOT image or None if access denied
    '''
    try:
        image = ee.Image(SPOT_ANALYTIC_ASSET)
        print(f"✓ Loaded SPOT analytic image")
        return image
    except Exception as e:
        print(f"✗ Cannot load SPOT analytic: {e}")
        return None


def load_spot_visual():
    '''
    Load SPOT 2008 visual (RGB) basemap.
    
    Returns:
        ee.Image: SPOT RGB image or None if access denied
    '''
    try:
        image = ee.Image(SPOT_VISUAL_ASSET)
        print(f"✓ Loaded SPOT visual basemap")
        return image
    except Exception as e:
        print(f"✗ Cannot load SPOT visual: {e}")
        return None


def load_spot_data():
    '''
    Load both SPOT analytic and visual datasets.
    
    Returns:
        tuple: (analytic_image, visual_image) - either may be None if access denied
    '''
    analytic = load_spot_analytic()
    visual = load_spot_visual()
    return analytic, visual


# ==============================================================================
# SPOT CLASSIFICATION (NDVI-based)
# ==============================================================================

def classify_spot_ndvi(spot_image):
    '''
    Create land cover classification from SPOT data using NDVI.
    Uses MapBiomas class IDs for compatibility.
    
    Args:
        spot_image (ee.Image): SPOT multispectral image with N (NIR) and R (Red) bands
    
    Returns:
        ee.Image: Classification image with MapBiomas classes:
                 - 3: Forest (NDVI > forest_threshold)
                 - 15: Pasture (between thresholds)
                 - 24: Urban (NDVI < urban_threshold)
                 - 0: No data/background
    '''
    if spot_image is None:
        print("✗ Cannot classify: SPOT image is None")
        return ee.Image.constant(0).rename('spot_classification')
    
    band_names = spot_image.bandNames().getInfo()
    
    if 'N' not in band_names or 'R' not in band_names:
        print(f"✗ SPOT missing required bands (N, R). Available: {band_names}")
        return ee.Image.constant(0).rename('spot_classification')
    
    # Calculate NDVI
    ndvi = spot_image.normalizedDifference(['N', 'R']).rename('ndvi')
    
    # Initialize as no data
    classification = ee.Image(0)
    
    # Apply MapBiomas class assignments
    classification = classification.where(
        ndvi.gt(FOREST_NDVI_THRESHOLD), 
        3  # Forest Formation
    )
    classification = classification.where(
        ndvi.lt(URBAN_NDVI_THRESHOLD), 
        24  # Urban Area
    )
    classification = classification.where(
        ndvi.gte(URBAN_NDVI_THRESHOLD).And(ndvi.lte(FOREST_NDVI_THRESHOLD)),
        15  # Pasture
    )
    
    print("✓ SPOT classification complete (NDVI-based)")
    return classification.rename('spot_classification')


def get_spot_visualization_params(use_analytic=True):
    '''
    Get visualization parameters for SPOT data.
    
    Args:
        use_analytic (bool): If True, return params for analytic (false color).
                            If False, return params for visual (true color).
    
    Returns:
        dict: Visualization parameters
    '''
    if use_analytic:
        return {
            'bands': ['N', 'R', 'G'],  # False color: NIR, Red, Green
            'min': 0,
            'max': 3000,
            'gamma': 1.4
        }
    else:
        return {
            'bands': ['B', 'G', 'R'],  # True color: Blue, Green, Red
            'min': 0,
            'max': 255,
            'gamma': 1.0
        }


# ==============================================================================
# SPOT UTILITIES
# ==============================================================================

def validate_spot_bands(spot_image, required_bands=['N', 'R', 'G']):
    '''
    Validate that SPOT image has required bands.
    
    Args:
        spot_image (ee.Image): SPOT image to validate
        required_bands (list): Bands that must be present
    
    Returns:
        bool: True if all required bands present
    '''
    if spot_image is None:
        return False
    
    try:
        band_names = spot_image.bandNames().getInfo()
        has_all = all(b in band_names for b in required_bands)
        if not has_all:
            missing = [b for b in required_bands if b not in band_names]
            print(f"✗ Missing bands: {missing}")
        return has_all
    except Exception as e:
        print(f"✗ Error validating bands: {e}")
        return False


def clip_spot_to_geometry(spot_image, geometry):
    '''
    Clip SPOT image to a specific geometry.
    
    Args:
        spot_image (ee.Image): SPOT image
        geometry (ee.Geometry): Area to clip to
    
    Returns:
        ee.Image: Clipped SPOT image
    '''
    if spot_image is None:
        return None
    return spot_image.clip(geometry)


# ==============================================================================
# ACCESS INFORMATION
# ==============================================================================

SPOT_INFO = '''
🛰️  SPOT 2008 Data Information

Asset ID: projects/google/brazil_forest_code/spot_bfc_ms_mosaic_v02

Bands Available:
- N: Near Infrared (NIR)
- R: Red
- G: Green
- B: Blue
- Pan: Panchromatic

Access Requirements:
- This dataset has restricted access
- Only available to authorized Earth Engine projects
- Requires special permission from Google Earth Engine
- Check https://code.earthengine.google.com for access status

Usage:
- Use with caution in production workflows
- Separate module allows graceful degradation if access denied
- NDVI-based classification available when accessible
- Visualization parameters optimized for false-color composite (N, R, G)
'''


def print_spot_info():
    '''Print SPOT dataset information.'''
    print(SPOT_INFO)
