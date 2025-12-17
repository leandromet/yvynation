'''
Core Earth Engine app for Yvynation.
Integrated workflows for maps, analysis, and visualization.
'''

import ee
from config import OUTPUT_BUCKET, OUTPUT_PREFIX, OUTPUT_SCALE, MAPBIOMAS_LABELS
from load_data import load_mapbiomas, load_territories
from analysis import (
    clip_mapbiomas_to_geometry,
    calculate_area_by_class,
    calculate_land_cover_change,
    compare_areas,
    filter_territories_by_state,
    filter_territories_by_names,
    get_territory_info,
)
from visualization import (
    create_map,
    add_mapbiomas_layer,
    add_territories_layer,
    add_change_layer,
    create_mapbiomas_legend,
    create_comparison_map,
    create_temporal_map,
)
from plots import (
    plot_area_distribution,
    plot_area_comparison,
    plot_area_changes,
    plot_temporal_trend,
)
from spot_module import check_spot_access, load_spot_data, classify_spot_ndvi


class YvynationApp:
    '''
    Main Yvynation application for Earth Engine geospatial analysis.
    Integrates MapBiomas, territories, and optional SPOT data.
    '''
    
    def __init__(self):
        '''Initialize the application.'''
        self.mapbiomas_v9 = None
        self.mapbiomas_v8 = None
        self.territories = None
        self.spot_available = False
        self.spot_analytic = None
        self.spot_visual = None
    
    def load_core_data(self):
        '''Load core MapBiomas and territory datasets.'''
        print("\n📦 Loading core datasets...\n")
        try:
            self.mapbiomas_v9 = load_mapbiomas('v9')
            self.mapbiomas_v8 = load_mapbiomas('v8')
            self.territories = load_territories('indigenous')
            print("✓ Core data loaded successfully\n")
            return True
        except Exception as e:
            print(f"✗ Failed to load core data: {e}")
            return False
    
    def load_spot_if_available(self):
        '''Load SPOT data if accessible (restricted).'''
        print("\n🛰️  Checking SPOT data access...\n")
        if check_spot_access():
            self.spot_analytic, self.spot_visual = load_spot_data()
            self.spot_available = True
        else:
            print("⚠️  SPOT data not available (restricted access)")
            self.spot_available = False
    
    def create_basic_map(self, center=None, zoom=8):
        '''
        Create a basic interactive map with MapBiomas and territories.
        
        Args:
            center (list): [lon, lat] center coordinates
            zoom (int): Initial zoom level
        
        Returns:
            geemap.Map: Interactive map
        '''
        if self.mapbiomas_v9 is None or self.territories is None:
            print("✗ Load data first with load_core_data()")
            return None
        
        Map = create_map(center=center, zoom=zoom)
        Map = add_mapbiomas_layer(Map, self.mapbiomas_v9, 2023, "MapBiomas 2023")
        Map = add_territories_layer(Map, self.territories)
        
        print("✓ Basic map created")
        return Map
    
    def analyze_territories(self, start_year=1985, end_year=2023):
        '''
        Perform comprehensive analysis on selected territories.
        
        Args:
            start_year (int): Analysis start year
            end_year (int): Analysis end year
        
        Returns:
            dict: Analysis results
        '''
        if self.territories is None:
            print("✗ Load data first with load_core_data()")
            return None
        
        print(f"\n🔍 Analyzing territories ({start_year}-{end_year})...\n")
        
        # Get territory info
        info = get_territory_info(self.territories)
        print(f"Processing {info['total_count']} territories")
        
        # Take first territory as example
        territory = ee.Feature(self.territories.first())
        geometry = territory.geometry()
        
        # Calculate areas for both years
        area_start = calculate_area_by_class(self.mapbiomas_v9, geometry, start_year)
        area_end = calculate_area_by_class(self.mapbiomas_v9, geometry, end_year)
        
        # Calculate change
        change_result = calculate_land_cover_change(self.mapbiomas_v9, geometry, start_year, end_year)
        comparison = compare_areas(area_start, area_end)
        
        results = {
            'area_start': area_start,
            'area_end': area_end,
            'comparison': comparison,
            'change_image': change_result['change_image'],
            'geometry': geometry
        }
        
        print("✓ Analysis complete\n")
        return results
    
    def create_comparison_visualization(self, analysis_results, year1=1985, year2=2023):
        '''
        Create side-by-side comparison visualization.
        
        Args:
            analysis_results (dict): Results from analyze_territories()
            year1 (int): First year
            year2 (int): Second year
        
        Returns:
            None (displays plots)
        '''
        print(f"\n📊 Creating comparison visualization ({year1} vs {year2})...\n")
        
        # Area distribution comparison
        plot_area_comparison(
            analysis_results['area_start'],
            analysis_results['area_end'],
            year1, year2,
            top_n=12
        )
        
        # Change visualization
        plot_area_changes(
            analysis_results['comparison'],
            year1, year2,
            top_n=12
        )
    
    def create_territory_map(self, state_code=None, territory_names=None, 
                            years_to_show=[1985, 2008, 2023], center=None, zoom=8):
        '''
        Create interactive map for specific territories.
        
        Args:
            state_code (str): Brazilian state code (e.g., 'MA')
            territory_names (list): Specific territory names
            years_to_show (list): Years to display as layers
            center (list): Map center
            zoom (int): Zoom level
        
        Returns:
            geemap.Map: Interactive territory map
        '''
        if self.territories is None:
            print("✗ Load data first")
            return None
        
        # Filter territories
        territories = self.territories
        if state_code:
            territories = filter_territories_by_state(territories, state_code)
        if territory_names:
            territories = filter_territories_by_names(territories, territory_names)
        
        # Create map with temporal layers
        Map = create_temporal_map(
            self.mapbiomas_v9,
            years_to_show,
            territories,
            center=center,
            zoom=zoom
        )
        
        print(f"✓ Territory map created ({len(years_to_show)} time periods)")
        return Map
    
    def export_results(self, image, name, description=""):
        '''
        Export analysis results to Cloud Storage.
        
        Args:
            image (ee.Image): Image to export
            name (str): Export task name
            description (str): Optional description
        
        Returns:
            ee.batch.Task: Export task
        '''
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


# ==============================================================================
# QUICK START EXAMPLE
# ==============================================================================

if __name__ == "__main__":
    # Initialize Earth Engine
    ee.Initialize()
    
    # Create app
    app = YvynationApp()
    
    # Load data
    app.load_core_data()
    app.load_spot_if_available()
    
    # Run analysis
    results = app.analyze_territories(start_year=1985, end_year=2023)
    
    # Create visualizations
    app.create_comparison_visualization(results, 1985, 2023)
    
    # Create interactive map
    territory_map = app.create_basic_map()
    
    print("\n✓ Yvynation app ready for analysis")
