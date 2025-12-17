"""
Core Earth Engine processing module for Yvynation.
Handles geospatial analysis, classification, and exports.
"""

import ee
from config import OUTPUT_BUCKET, OUTPUT_PREFIX, OUTPUT_SCALE, MAPBIOMAS_LABELS, MAPBIOMAS_COLOR_MAP
from load_data import (
    load_mapbiomas,
    load_territories,
    classify_spot_ndvi,
    calculate_area_by_class,
)


class YvynationAnalyzer:
    """Main Earth Engine analyzer for Yvynation."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.mapbiomas_v9 = None
        self.mapbiomas_v8 = None
        self.territories = None
    
    def load_data(self):
        """Load all required data assets."""
        print("\n📦 Loading data assets...\n")
        
        try:
            self.mapbiomas_v9 = load_mapbiomas('v9')
            self.mapbiomas_v8 = load_mapbiomas('v8')
            self.territories = load_territories('indigenous')
            print("✓ All data loaded successfully\n")
        except Exception as e:
            print(f"✗ Failed to load data: {e}")
            raise
    
    def analyze_territory(self, territory_index=0):
        """
        Analyze land cover in a specific territory.
        
        Args:
            territory_index (int): Index of territory in collection
        """
        if self.territories is None:
            print("✗ Territories not loaded. Call load_data() first.")
            return
        
        territory = ee.Feature(self.territories.first())
        roi = territory.geometry()
        
        print(f"\n🔍 Analyzing territory...\n")
        
        # Calculate areas
        areas_df = calculate_area_by_class(self.mapbiomas_v9, roi)
        
        if not areas_df.empty:
            print(areas_df.to_string())
        
        return areas_df
    
    def export_classification(self, image, name, description=""):
        """
        Export classification image to Google Cloud Storage.
        
        Args:
            image (ee.Image): Image to export
            name (str): Export task name
            description (str): Optional description
        """
        task = ee.batch.Export.image.toCloudStorage(
            image=image,
            description=description or name,
            bucket=OUTPUT_BUCKET,
            fileNamePrefix=f"{OUTPUT_PREFIX}/{name}",
            scale=OUTPUT_SCALE,
            maxPixels=1e13
        )
        
        task.start()
        print(f"✓ Export started: {name}")
        return task
    
    def get_vis_params(self):
        """Get visualization parameters for MapBiomas."""
        colors = [MAPBIOMAS_COLOR_MAP[k] for k in sorted(MAPBIOMAS_COLOR_MAP.keys())]
        return {
            'min': 0,
            'max': 466,
            'palette': colors
        }


# Example usage
if __name__ == "__main__":
    # Initialize EE
    ee.Initialize()
    
    # Create analyzer
    analyzer = YvynationAnalyzer()
    analyzer.load_data()
    
    # Analyze first territory
    results = analyzer.analyze_territory(0)
    
    # Export example
    # analyzer.export_classification(
    #     image=analyzer.mapbiomas_v9,
    #     name="mapbiomas_v9_export",
    #     description="MapBiomas Collection 9 export"
    # )
