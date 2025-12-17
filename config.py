"""
Configuration and constants for the Yvynation application.
"""

# Earth Engine project ID
PROJECT_ID = "leandromet"

# Region of interest (example: Brazil)
# Format: [min_longitude, min_latitude, max_longitude, max_latitude]
REGION_OF_INTEREST = [-73.0, -33.0, -35.0, 5.0]

# Output settings
OUTPUT_BUCKET = "gs://your-bucket-name"
OUTPUT_PREFIX = "yvynation"

# Dataset configurations
SENTINEL2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
LANDSAT_COLLECTION = "LANDSAT/LC09/C02/T1_L2"

# Processing parameters
CLOUD_FILTER = 20  # Maximum cloud cover percentage
