'''
Configuration and constants for the Yvynation Earth Engine application.
'''

import ee

# ==============================================================================
# EARTH ENGINE PROJECT CONFIGURATION
# ==============================================================================
PROJECT_ID = "ee-leandromet"

# Region of interest (Brazil)
# Format: [min_longitude, min_latitude, max_longitude, max_latitude]
REGION_OF_INTEREST = [-73.0, -33.0, -35.0, 5.0]

# ==============================================================================
# OUTPUT CONFIGURATION
# ==============================================================================
OUTPUT_BUCKET = "gs://yvynation-bucket"
OUTPUT_PREFIX = "yvynation"
OUTPUT_SCALE = 30  # Export resolution in meters

# ==============================================================================
# MAPBIOMAS CONFIGURATION
# ==============================================================================
MAPBIOMAS_COLLECTIONS = {
    'v9': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1',
    'v8': 'projects/mapbiomas-public/assets/brazil/lulc/collection8/mapbiomas_collection80_integration_v1'
}

TERRITORY_COLLECTIONS = {
    'indigenous': 'projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES',
    'biomes': 'projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/BIOMES'
}

# ==============================================================================
# SATELLITE IMAGERY COLLECTIONS
# ==============================================================================
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
LANDSAT_COLLECTION = "LANDSAT/LC09/C02/T1_L2"
SPOT_VISUAL_ASSET = 'projects/google/brazil_forest_code/spot_bfc_rgb_mosaic_metadata_v03'
SPOT_ANALYTIC_ASSET = 'projects/google/brazil_forest_code/spot_bfc_ms_mosaic_v02'

# ==============================================================================
# PROCESSING PARAMETERS
# ==============================================================================
CLOUD_FILTER = 20  # Maximum cloud cover percentage
FOREST_NDVI_THRESHOLD = 0.5
URBAN_NDVI_THRESHOLD = 0.2

# ==============================================================================
# LAND COVER CLASSIFICATION LABELS & COLORS (MapBiomas Collection 9)
# ==============================================================================
MAPBIOMAS_LABELS = {
    0: "No data",
    1: "Forest", 2: "Natural Forest", 3: "Forest Formation", 4: "Savanna Formation", 5: "Mangrove",
    6: "Floodable Forest", 7: "Flooded Forest", 8: "Wooded Restinga", 9: "Forest Plantation",
    10: "Herbaceous", 11: "Wetland", 12: "Grassland", 13: "Other Natural Formation", 14: "Farming",
    15: "Pasture", 16: "Agriculture", 17: "Perennial Crop", 18: "Agri", 19: "Temporary Crop",
    20: "Sugar Cane", 21: "Mosaic of Uses", 22: "Non vegetated", 23: "Beach and Sand", 24: "Urban Area",
    25: "Other non Vegetated Areas", 26: "Water", 27: "Not Observed", 28: "Rocky Outcrop", 29: "Rocky Outcrop",
    30: "Mining", 31: "Aquaculture", 32: "Hypersaline Tidal Flat", 33: "River Lake and Ocean", 34: "Reservoir",
    35: "Palm Oil", 36: "Perennial Crop", 37: "Semi-Perennial Crop", 38: "Annual Crop", 39: "Soybean",
    40: "Rice", 41: "Other Temporary Crops", 42: "Other Annual Crop", 43: "Other Semi-Perennial Crop",
    44: "Other Perennial Crop", 45: "Coffee", 46: "Coffee", 47: "Citrus", 48: "Other Perennial Crops",
    49: "Wooded Sandbank Vegetation", 50: "Herbaceous Sandbank Vegetation", 51: "Salt Flat",
    52: "Apicuns and Salines", 62: "Cotton", 146: "Other Land Use", 435: "Other Transition",
    466: "Other Classification"
}

MAPBIOMAS_COLOR_MAP = {
    0: "#ffffff", 1: "#1f8d49", 2: "#1f8d49", 3: "#1f8d49", 4: "#7dc975", 5: "#04381d", 6: "#007785",
    7: "#005544", 8: "#33a02c", 9: "#7a5900", 10: "#d6bc74", 11: "#519799", 12: "#d6bc74", 13: "#ffffff",
    14: "#ffefc3", 15: "#edde8e", 16: "#e974ed", 17: "#d082de", 18: "#e974ed", 19: "#c27ba0", 20: "#db7093",
    21: "#ffefc3", 22: "#d4271e", 23: "#ffa07a", 24: "#d4271e", 25: "#db4d4f", 26: "#2532e4", 27: "#ffffff",
    28: "#ffaa5f", 29: "#ffaa5f", 30: "#9c0027", 31: "#091077", 32: "#fc8114", 33: "#259fe4", 34: "#259fe4",
    35: "#9065d0", 36: "#d082de", 37: "#d082de", 38: "#c27ba0", 39: "#f5b3c8", 40: "#c71585", 41: "#f54ca9",
    42: "#f54ca9", 43: "#d082de", 44: "#d082de", 45: "#d68fe2", 46: "#d68fe2", 47: "#9932cc", 48: "#e6ccff",
    49: "#02d659", 50: "#ad5100", 51: "#fc8114", 52: "#fc8114", 62: "#ff69b4", 146: "#ffefc3", 435: "#cccccc",
    466: "#999999"
}

# Create visualization palette from color map
MAPBIOMAS_PALETTE = [MAPBIOMAS_COLOR_MAP[k] for k in sorted(MAPBIOMAS_COLOR_MAP.keys())]
