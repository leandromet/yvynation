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

# ==============================================================================
# HANSEN/GLAD GLOBAL LAND COVER CONFIGURATION
# ==============================================================================
# Global Land Analysis and Discovery (GLAD) Lab - University of Maryland
# Available globally (not just Brazil)
HANSEN_DATASETS = {
    '2000': 'projects/glad/GLCLU2020/v2/LCLUC_2000',
    '2005': 'projects/glad/GLCLU2020/v2/LCLUC_2005',
    '2010': 'projects/glad/GLCLU2020/v2/LCLUC_2010',
    '2015': 'projects/glad/GLCLU2020/v2/LCLUC_2015',
    '2020': 'projects/glad/GLCLU2020/v2/LCLUC_2020',
    'change': 'projects/glad/GLCLU2020/v2/LCLUC'  # 2000-2020 change
}

HANSEN_OCEAN_MASK = 'projects/glad/OceanMask'

HANSEN_PALETTE = [
    "FEFECC","FAFAC3","F7F7BB","F4F4B3","F1F1AB","EDEDA2","EAEA9A","E7E792","E4E48A",
    "E0E081","DDDD79","DADA71","D7D769","D3D360","D0D058","CDCD50","CACA48","C6C63F","C3C337","C0C02F","BDBD27","B9B91E","B6B616",
    "B3B30E","B0B006","609C60","5C985C","589558","549254","508E50","4C8B4C","488848","448544","408140","3C7E3C","387B38","347834",
    "317431","2D712D","296E29","256B25","216721","1D641D","196119","155E15","115A11","0D570D","095409","065106","643700","643a00",
    "643d00","644000","644300","644600","644900","654c00","654f00","655200","655500","655800","655a00","655d00","655000","656300",
    "666600","666900","666c00","666f00","667200","667500","667800","667b00","ff99ff","FC92FC","F98BF9","F685F6","F37EF3","F077F0",
    "ED71ED","EA6AEA","E763E7","E45DE4","E156E1","DE4FDE","DB49DB","D842D8","D53BD5","D235D2","CF2ECF","CC27CC","C921C9","C61AC6",
    "C313C3","C00DC0","BD06BD","bb00bb","000003","000004","000005","BFC0C0","B7BDC2","AFBBC4","A8B8C6","A0B6C9","99B3CB","91B1CD",
    "89AFD0","82ACD2","7AAAD4","73A7D6","6BA5D9","64A3DB","5CA0DD","549EE0","4D9BE2","4599E4","3E96E6","3694E9","2E92EB","278FED",
    "1F8DF0","188AF2","1088F4","0986F7","55A5A5","53A1A2","519E9F","4F9B9C","4D989A","4B9597","499294","478F91","458B8F","43888C",
    "418589","3F8286","3D7F84","3B7C81","39797E","37767B","357279","336F76","316C73","2F6970","2D666E","2B636B","296068","285D66",
    "bb93b0","B78FAC","B48CA9","B189A6","AE85A2","AA829F","A77F9C","A47B99","A17895","9E7592","9A718F","976E8C","946B88","916885",
    "8D6482","8A617F","875E7B","845A78","815775","7D5472","7A506E","774D6B","744A68","714765","de7cbb","DA77B7","D772B3","D46EAF",
    "D169AB","CE64A8","CB60A4","C85BA0","C4579C","C15298","BE4D95","BB4991","B8448D","B54089","B23B86","AF3682","AB327E","A82D7A",
    "A52976","A22473","9F1F6F","9C1B6B","991667","961264","000000","000000","000000",
    "1964EB","1555E4","1147DD","0E39D6","0A2ACF","071CC8","030EC1","0000BA",
    "0000BA","040464","0000FF","3051cf","000000","000000","000000","000000",
    "000000","000000","000000","000000","000000","000000","000000","000000",
    "000000","000000","000000","000000","000000","000000","000000","000000",
    "547FC4","4D77BA","466FB1","4067A7","395F9E","335895","335896","335897","ff2828","ffffff","d0ffff","ffe0d0","ff7d00","fac800","c86400",
    "fff000","afcd96","afcd96","64dcdc","00ffff","00ffff","00ffff","111133","000000"
]

# Hansen/GLAD discrete color map for 18 land cover classes
HANSEN_COLOR_MAP = {
    0: "#FFFFFF",      # No Data - White
    1: "#2E8BC0",      # Water - Blue
    2: "#1F4F2F",      # Evergreen Needleleaf - Dark Green
    3: "#2D5016",      # Evergreen Broadleaf - Dark Green
    4: "#3D5C2F",      # Deciduous Needleleaf - Green
    5: "#4A7C3E",      # Deciduous Broadleaf - Light Green
    6: "#3D6B3F",      # Mixed Forest - Green
    7: "#8B7355",      # Closed Shrublands - Brown
    8: "#A0826D",      # Open Shrublands - Tan
    9: "#C4B585",      # Woody Savannas - Khaki
    10: "#D4C869",     # Savannas - Gold
    11: "#E8D957",     # Grasslands - Yellow
    12: "#4A6FA0",     # Permanent Wetlands - Blue-Green
    13: "#FFD700",     # Croplands - Golden Yellow
    14: "#FF6B35",     # Urban & Built-up - Orange-Red
    15: "#FFA500",     # Cropland/Natural - Orange
    16: "#F0F8FF",     # Snow & Ice - Alice Blue (light)
    17: "#8B8680",     # Barren - Gray-Brown
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

# Create visualization palette from color map (0-62 range)
MAPBIOMAS_PALETTE = []
for i in range(63):
    if i in MAPBIOMAS_COLOR_MAP:
        MAPBIOMAS_PALETTE.append(MAPBIOMAS_COLOR_MAP[i].lstrip('#'))
    else:
        MAPBIOMAS_PALETTE.append('808080')  # Gray for undefined classes
