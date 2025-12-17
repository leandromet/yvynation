"""
Main entry point for the Yvynation Earth Engine application.
"""

import ee
from config import PROJECT_ID, REGION_OF_INTEREST

def initialize_ee():
    """Initialize Earth Engine."""
    try:
        ee.Initialize(project=PROJECT_ID)
        print(f"✓ Earth Engine initialized with project: {PROJECT_ID}")
    except Exception as e:
        print(f"✗ Failed to initialize Earth Engine: {e}")
        raise

def main():
    """Main application logic."""
    initialize_ee()
    
    # Example: Load and process a dataset
    # roi = ee.Geometry.Rectangle(REGION_OF_INTEREST)
    # dataset = ee.ImageCollection('COPERNICUS/S2').filterBounds(roi)
    # print(f"✓ Loaded {dataset.size().getInfo()} Sentinel-2 images")
    
    print("✓ Yvynation Earth Engine app initialized successfully")

if __name__ == "__main__":
    main()
