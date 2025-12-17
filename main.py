"""
Main entry point for Yvynation Earth Engine application.
"""

import ee
from config import PROJECT_ID
from load_data import load_mapbiomas, load_territories, load_spot_analytic, classify_spot_ndvi


def initialize_ee():
    """Initialize Earth Engine with project credentials."""
    try:
        ee.Initialize(project=PROJECT_ID)
        print(f"✓ Earth Engine initialized")
        return True
    except Exception as e:
        print(f"✗ EE initialization failed: {e}")
        return False


def main():
    """Main application workflow."""
    if not initialize_ee():
        return
    
    print("\n=== Yvynation Earth Engine Application ===\n")
    
    # Load datasets
    try:
        mapbiomas = load_mapbiomas('v9')
        territories = load_territories('indigenous')
        spot_image = load_spot_analytic()
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return
    
    # Example: Classify SPOT data
    if spot_image:
        classification = classify_spot_ndvi(spot_image)
        print(f"✓ Classification bands: {classification.bandNames().getInfo()}")
    
    print("\n✓ Application ready for analysis")


if __name__ == "__main__":
    main()
