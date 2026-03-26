"""
Configuration for Yvynation Reflex app.
Adapted from original Streamlit config.
"""

import os
from typing import Dict

# Google Cloud & Earth Engine
PROJECT_ID = os.getenv("GCP_PROJECT_ID", "your-project-id")
SERVICE_ACCOUNT_PATH = os.getenv("SERVICE_ACCOUNT_JSON", None)

# MapBiomas Configuration
MAPBIOMAS_LABELS = {
    0: "Non-observed",
    1: "Forest",
    2: "Natural Forest",
    3: "Forest Formation",
    4: "Savanna Formation",
    5: "Mangrove",
    6: "Herbaceous Vegetation",
    7: "Natural Grassland",
    8: "Pasture",
    9: "Corps",
    10: "Agriculture",
    11: "Sugarcane",
    12: "Bean",
    13: "Cassava",
    14: "Corn",
    15: "Cotton",
    16: "Fallow/Idle",
    17: "Perennial Crop",
    18: "Double Crop",
    19: "Rice",
    20: "Soy",
    21: "Temporary Crop",
    22: "Soybean",
    23: "Temporary Crops",
    24: "Beans",
    25: "Corn",
    26: "Wheat",
    27: "Cerrado",
    28: "Citrus",
    29: "Coffee",
    30: "Mature Forest",
    31: "Forest Plantation",
    32: "Herbaceous Grassland",
    33: "Non-forest Natural Formation",
    34: "Pasture",
    35: "Infrastructure Urbana",
    36: "Surface Water",
    37: "Herbaceous Water Vegetation",
    38: "Forest Water Vegetation",
    39: "Shrub",
    40: "Open Lichen and Moss",
    41: "Barren",
    42: "Rocks and Outcrops",
    43: "Herbaceous Vegetation",
    44: "Woody Savanna",
    45: "Restinga Vegetation",
    46: "Salt Flat",
    47: "Aquaculture",
    48: "Apiculture and Beekeeping",
    49: "Arboriculture",
    50: "Flooded Grassland",
    51: "Flooded-Pasture",
}

MAPBIOMAS_COLOR_MAP = {
    1: "#1f8d49",  # Forest - green
    6: "#e6cccc",  # Herbaceous Vegetation
    8: "#c59956",  # Pasture - brown
    9: "#c59956",  # Corps - brown
    10: "#ffd966",  # Agriculture - yellow
    20: "#f1e64c",  # Soy - light yellow
    41: "#cc0000",  # Barren - red
}

# Hansen Global Forest Change Configuration
HANSEN_DATASETS = {
    "2000": "UMD/hansen/global_forest_change_2023_v1_10",
    "2010": "UMD/hansen/global_forest_change_2023_v1_10",
    "2015": "UMD/hansen/global_forest_change_2023_v1_10",
    "2020": "UMD/hansen/global_forest_change_2023_v1_10",
}

HANSEN_OCEAN_MASK = "NOAA/NGDC/ETOPO1/dawson-keller-corrected/bedrock/1000"

HANSEN_CONSOLIDATED_MAPPING = {
    2000: "Year 2000",
    2001: "Year 2001",
    2002: "Year 2002",
    2003: "Year 2003",
    2004: "Year 2004",
    2005: "Year 2005",
    2006: "Year 2006",
    2007: "Year 2007",
    2008: "Year 2008",
    2009: "Year 2009",
    2010: "Year 2010",
}

HANSEN_CONSOLIDATED_COLORS = {
    2000: "#ffff00",
    2001: "#ffff00",
    2002: "#ffff00",
    # ... other years
}

# Mapbiomas years available
MAPBIOMAS_YEARS = list(range(1985, 2024))
HANSEN_YEARS = ["2000", "2010", "2015", "2020"]

# Application Settings
APP_NAME = "Yvynation"
APP_VERSION = "2.0.0"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Cloud Run settings
PORT = int(os.getenv("PORT", 3000))
HOST = os.getenv("HOST", "0.0.0.0")
