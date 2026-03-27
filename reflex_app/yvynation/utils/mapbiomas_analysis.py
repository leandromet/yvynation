"""
MapBiomas-specific analysis for Yvynation Reflex app.
Handles Brazil land cover analysis 1985-2023.
Ported from mapbiomas_analysis.py, adapted for Reflex.
"""

import ee
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from .analysis import (
    clip_classification_to_geometry,
    calculate_area_by_class,
    calculate_change_area,
    calculate_class_specific_change,
    compare_areas,
)
from ..config import MAPBIOMAS_LABELS, MAPBIOMAS_YEARS
from ..utils.ee_service import get_ee

logger = logging.getLogger(__name__)


class MapBiomasAnalyzer:
    """
    Analyzer for MapBiomas Brazil land cover data.
    Handles multi-year analysis and comparisons.
    """
    
    # MapBiomas dataset collection ID (Brazil dataset)
    MAPBIOMAS_COLLECTION_ID = "users/mapbiomas/aqueousv3/mapbiomas_v802_2023"
    
    def __init__(self):
        """Initialize analyzer."""
        self.ee = get_ee()
        self.mapbiomas_dataset = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load MapBiomas dataset from Earth Engine."""
        try:
            self.mapbiomas_dataset = ee.Image(self.MAPBIOMAS_COLLECTION_ID)
            logger.info("Loaded MapBiomas dataset")
        except Exception as e:
            logger.error(f"Error loading MapBiomas dataset: {e}")
            self.mapbiomas_dataset = None
    
    def is_available(self) -> bool:
        """Check if MapBiomas dataset is available."""
        return self.mapbiomas_dataset is not None
    
    def analyze_single_year(
        self,
        geometry: ee.Geometry,
        year: int,
        scale: int = 30
    ) -> pd.DataFrame:
        """
        Analyze land cover for a single year.
        
        Args:
            geometry: Area of interest
            year: Year to analyze (1985-2023)
            scale: Analysis scale in meters
        
        Returns:
            DataFrame with area by class
        """
        try:
            if not self.is_available():
                logger.error("MapBiomas dataset not available")
                return pd.DataFrame()
            
            if year < 1985 or year > 2023:
                logger.error(f"Year {year} out of range (1985-2023)")
                return pd.DataFrame()
            
            # Extract band for year
            band_name = f'classification_{year}'
            year_image = self.mapbiomas_dataset.select(band_name)
            
            # Calculate areas
            df = calculate_area_by_class(
                year_image,
                geometry,
                year=year,
                scale=scale,
                class_labels=MAPBIOMAS_LABELS
            )
            
            logger.info(f"Analyzed MapBiomas {year}: {len(df)} classes")
            return df
        
        except Exception as e:
            logger.error(f"Error analyzing single year {year}: {e}")
            return pd.DataFrame()
    
    def analyze_year_range(
        self,
        geometry: ee.Geometry,
        start_year: int,
        end_year: int,
        scale: int = 30,
        step: int = 1
    ) -> Dict[int, pd.DataFrame]:
        """
        Analyze multiple years in a range.
        
        Args:
            geometry: Area of interest
            start_year: Start year
            end_year: End year
            scale: Analysis scale
            step: Year step (1 = every year, 5 = every 5 years)
        
        Returns:
            Dictionary mapping year -> DataFrame
        """
        try:
            years_to_analyze = range(start_year, end_year + 1, step)
            results = {}
            
            for year in years_to_analyze:
                df = self.analyze_single_year(geometry, year, scale)
                if not df.empty:
                    results[year] = df
            
            logger.info(f"Analyzed {len(results)} years")
            return results
        
        except Exception as e:
            logger.error(f"Error analyzing year range {start_year}-{end_year}: {e}")
            return {}
    
    def compare_years(
        self,
        geometry: ee.Geometry,
        year_start: int,
        year_end: int,
        scale: int = 30
    ) -> pd.DataFrame:
        """
        Compare land cover between two years.
        
        Args:
            geometry: Area of interest
            year_start: Start year
            year_end: End year
            scale: Analysis scale
        
        Returns:
            Comparison DataFrame with change metrics
        """
        try:
            # Analyze both years
            df_start = self.analyze_single_year(geometry, year_start, scale)
            df_end = self.analyze_single_year(geometry, year_end, scale)
            
            if df_start.empty or df_end.empty:
                logger.error(f"Could not analyze years {year_start} or {year_end}")
                return pd.DataFrame()
            
            # Compare
            comparison = compare_areas(
                df_start,
                df_end,
                year_start=year_start,
                year_end=year_end
            )
            
            logger.info(f"Compared {year_start} vs {year_end}")
            return comparison
        
        except Exception as e:
            logger.error(f"Error comparing years {year_start}-{year_end}: {e}")
            return pd.DataFrame()
    
    def get_change_timeline(
        self,
        geometry: ee.Geometry,
        start_year: int,
        end_year: int,
        class_id: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Create a timeline of land cover change for a class.
        
        Args:
            geometry: Area of interest
            start_year: Start year
            end_year: End year
            class_id: Specific class to track (None = all classes)
        
        Returns:
            DataFrame with area over time
        """
        try:
            year_data = self.analyze_year_range(
                geometry,
                start_year,
                end_year,
                step=1
            )
            
            if not year_data:
                return pd.DataFrame()
            
            # Build timeline
            if class_id:
                # Single class timeline
                records = []
                for year, df in sorted(year_data.items()):
                    class_row = df[df['Class_ID'] == class_id]
                    if not class_row.empty:
                        records.append({
                            'Year': year,
                            'Class_ID': class_id,
                            'Class_Name': class_row.iloc[0]['Class_Name'],
                            'Area_ha': class_row.iloc[0]['Area_ha'],
                        })
                
                return pd.DataFrame(records)
            
            else:
                # All classes timeline
                records = []
                for year, df in sorted(year_data.items()):
                    for _, row in df.iterrows():
                        records.append({
                            'Year': year,
                            'Class_ID': row['Class_ID'],
                            'Class_Name': row['Class_Name'],
                            'Area_ha': row['Area_ha'],
                        })
                
                return pd.DataFrame(records)
        
        except Exception as e:
            logger.error(f"Error creating timeline {start_year}-{end_year}: {e}")
            return pd.DataFrame()
    
    def identify_forest_change(
        self,
        geometry: ee.Geometry,
        year_start: int,
        year_end: int,
        scale: int = 30
    ) -> Dict[str, Any]:
        """
        Identify forest loss and gain between years.
        
        Uses class IDs for natural forest (from MapBiomas labels).
        Classes 3-4, 9, 10, 12 represent natural vegetation.
        
        Args:
            geometry: Area of interest
            year_start: Start year
            year_end: End year
            scale: Analysis scale
        
        Returns:
            Dict with forest loss/gain metrics
        """
        try:
            # Forest class IDs in MapBiomas (natural vegetation)
            forest_classes = [3, 4, 9, 10, 12]
            
            # Get year images
            start_img = self.mapbiomas_dataset.select(f'classification_{year_start}')
            end_img = self.mapbiomas_dataset.select(f'classification_{year_end}')
            
            # Identify forest pixels at each time
            forest_start = None
            for class_id in forest_classes:
                class_mask = start_img.eq(class_id)
                forest_start = class_mask if forest_start is None else forest_start.Or(class_mask)
            
            forest_end = None
            for class_id in forest_classes:
                class_mask = end_img.eq(class_id)
                forest_end = class_mask if forest_end is None else forest_end.Or(class_mask)
            
            # Calculate loss and gain
            forest_loss = forest_start.And(forest_end.Not())
            forest_gain = forest_end.And(forest_start.Not())
            
            area_image = ee.Image.pixelArea().divide(1e6)  # km²
            
            loss_area = forest_loss.multiply(area_image).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=scale,
                maxPixels=1e13
            ).getInfo().get('constant', 0)
            
            gain_area = forest_gain.multiply(area_image).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=scale,
                maxPixels=1e13
            ).getInfo().get('constant', 0)
            
            logger.info(f"Forest change {year_start}-{year_end}: Loss={loss_area:.2f} km², Gain={gain_area:.2f} km²")
            
            return {
                'year_start': year_start,
                'year_end': year_end,
                'forest_loss_km2': loss_area,
                'forest_loss_ha': loss_area * 100,
                'forest_gain_km2': gain_area,
                'forest_gain_ha': gain_area * 100,
                'net_forest_change_km2': gain_area - loss_area,
                'net_forest_change_ha': (gain_area - loss_area) * 100,
            }
        
        except Exception as e:
            logger.error(f"Error identifying forest change: {e}")
            return {
                'year_start': year_start,
                'year_end': year_end,
                'forest_loss_km2': 0,
                'forest_loss_ha': 0,
                'forest_gain_km2': 0,
                'forest_gain_ha': 0,
                'net_forest_change_km2': 0,
                'net_forest_change_ha': 0,
            }


# Singleton instance
_analyzer = None


def get_mapbiomas_analyzer() -> MapBiomasAnalyzer:
    """Get or create MapBiomas analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = MapBiomasAnalyzer()
    return _analyzer
