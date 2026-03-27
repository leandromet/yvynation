"""
Hansen Global Forest Change analysis for Yvynation Reflex app.
Handles global forest loss/gain detection 2000-2023.
Ported from hansen_analysis.py, adapted for Reflex.
"""

import ee
import pandas as pd
import logging
from typing import Dict, List, Optional, Any
from .analysis import (
    calculate_change_area,
    calculate_class_specific_change,
    get_geometry_bounds,
)
from ..config import HANSEN_CONSOLIDATED_MAPPING

logger = logging.getLogger(__name__)


class HansenAnalyzer:
    """
    Analyzer for Hansen Global Forest Change data.
    Tracks global forest loss and gain detection.
    """
    
    # Hansen Global Forest Change dataset
    HANSEN_DATASET = 'UMD/hansen/global_forest_change_2023_v1_10'
    
    def __init__(self):
        """Initialize analyzer."""
        self.hansen_dataset = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load Hansen dataset from Earth Engine."""
        try:
            self.hansen_dataset = ee.Image(self.HANSEN_DATASET)
            logger.info("Loaded Hansen Global Forest Change dataset")
        except Exception as e:
            logger.error(f"Error loading Hansen dataset: {e}")
            self.hansen_dataset = None
    
    def is_available(self) -> bool:
        """Check if Hansen dataset is available."""
        return self.hansen_dataset is not None
    
    def get_tree_cover_2000(
        self,
        geometry: ee.Geometry,
        scale: int = 30,
        coverage_threshold: int = 10
    ) -> Dict[str, Any]:
        """
        Get tree cover in year 2000.
        
        Args:
            geometry: Area of interest
            scale: Analysis scale
            coverage_threshold: Minimum percent cover (0-100)
        
        Returns:
            Dictionary with tree cover statistics
        """
        try:
            if not self.is_available():
                logger.error("Hansen dataset not available")
                return {'coverage_2000': 0, 'area_ha': 0}
            
            # Extract tree cover 2000 band
            tree_cover_2000 = self.hansen_dataset.select('first_b30')
            
            # Threshold to coverage percentage
            tree_cover_binary = tree_cover_2000.gte(coverage_threshold)
            
            # Calculate area
            area_km2 = tree_cover_binary.multiply(
                ee.Image.pixelArea().divide(1e6)
            ).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=scale,
                maxPixels=1e13
            ).getInfo().get('constant', 0)
            
            area_ha = area_km2 * 100
            percent_cover = (tree_cover_binary.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=scale,
                maxPixels=1e13
            ).getInfo().get('constant', 0)) * 100
            
            logger.info(f"Tree cover 2000: {area_ha:.0f} ha ({percent_cover:.1f}%)")
            
            return {
                'year': 2000,
                'tree_cover_area_ha': area_ha,
                'tree_cover_percent': percent_cover,
            }
        
        except Exception as e:
            logger.error(f"Error calculating tree cover 2000: {e}")
            return {'year': 2000, 'tree_cover_area_ha': 0, 'tree_cover_percent': 0}
    
    def get_forest_loss(
        self,
        geometry: ee.Geometry,
        start_year: int = 2000,
        end_year: int = 2023,
        scale: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate forest loss in a period.
        
        Args:
            geometry: Area of interest
            start_year: Period start (2000-2023)
            end_year: Period end
            scale: Analysis scale
        
        Returns:
            Dictionary with loss statistics by year
        """
        try:
            if not self.is_available():
                logger.error("Hansen dataset not available")
                return {}
            
            # Extract loss year band (0-23 = 2000-2023)
            loss_year = self.hansen_dataset.select('lossyear')
            
            # Filter to year range
            loss_in_period = loss_year.gte(start_year - 2000).And(
                loss_year.lte(end_year - 2000)
            )
            
            # Calculate annual loss
            results = {}
            for year in range(start_year, end_year + 1):
                year_loss = loss_year.eq(year - 2000)
                
                loss_area_km2 = year_loss.multiply(
                    ee.Image.pixelArea().divide(1e6)
                ).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=geometry,
                    scale=scale,
                    maxPixels=1e13
                ).getInfo().get('constant', 0)
                
                results[year] = {
                    'year': year,
                    'loss_area_ha': loss_area_km2 * 100,
                    'loss_area_km2': loss_area_km2,
                }
            
            logger.info(f"Calculated forest loss {start_year}-{end_year}")
            return results
        
        except Exception as e:
            logger.error(f"Error calculating forest loss: {e}")
            return {}
    
    def get_forest_gain(
        self,
        geometry: ee.Geometry,
        period: str = '12'  # Default to 2000-2012
    ) -> Dict[str, Any]:
        """
        Calculate forest gain.
        
        Note: Hansen GFC tracks gain for specific periods (e.g., 2000-2012).
        
        Args:
            geometry: Area of interest
            period: Period code ('12' = 2000-2012)
        
        Returns:
            Dictionary with gain statistics
        """
        try:
            if not self.is_available():
                logger.error("Hansen dataset not available")
                return {'gain_area_ha': 0}
            
            # Extract gain band
            gain = self.hansen_dataset.select('gain')
            
            # Calculate total gain
            gain_area_km2 = gain.multiply(
                ee.Image.pixelArea().divide(1e6)
            ).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=geometry,
                scale=30,
                maxPixels=1e13
            ).getInfo().get('constant', 0)
            
            gain_area_ha = gain_area_km2 * 100
            
            logger.info(f"Forest gain (2000-2012): {gain_area_ha:.0f} ha")
            
            return {
                'period': f'2000-20{period}',
                'gain_area_ha': gain_area_ha,
                'gain_area_km2': gain_area_km2,
            }
        
        except Exception as e:
            logger.error(f"Error calculating forest gain: {e}")
            return {'gain_area_ha': 0}
    
    def create_loss_timeline(
        self,
        geometry: ee.Geometry,
        start_year: int = 2000,
        end_year: int = 2023
    ) -> pd.DataFrame:
        """
        Create annual forest loss timeline.
        
        Args:
            geometry: Area of interest
            start_year: Period start
            end_year: Period end
        
        Returns:
            DataFrame with annual loss
        """
        try:
            loss_dict = self.get_forest_loss(geometry, start_year, end_year)
            
            if not loss_dict:
                return pd.DataFrame()
            
            records = []
            for year, data in sorted(loss_dict.items()):
                records.append({
                    'Year': year,
                    'Loss_ha': data['loss_area_ha'],
                    'Loss_km2': data['loss_area_km2'],
                })
            
            return pd.DataFrame(records)
        
        except Exception as e:
            logger.error(f"Error creating loss timeline: {e}")
            return pd.DataFrame()
    
    def analyze_forest_dynamics(
        self,
        geometry: ee.Geometry,
        start_year: int = 2000,
        end_year: int = 2023,
        scale: int = 30
    ) -> Dict[str, Any]:
        """
        Comprehensive forest dynamics analysis.
        
        Args:
            geometry: Area of interest
            start_year: Analysis start year
            end_year: Analysis end year
            scale: Analysis scale
        
        Returns:
            Dictionary with complete forest statistics
        """
        try:
            if not self.is_available():
                logger.error("Hansen dataset not available")
                return {}
            
            # Get baselines
            cover_2000 = self.get_tree_cover_2000(geometry, scale)
            
            # Get loss
            loss_dict = self.get_forest_loss(geometry, start_year, end_year, scale)
            total_loss_ha = sum(d['loss_area_ha'] for d in loss_dict.values())
            
            # Get gain
            gain = self.get_forest_gain(geometry)
            
            # Calculate net change
            net_change_ha = gain.get('gain_area_ha', 0) - total_loss_ha
            
            logger.info(f"Forest dynamics: Loss={total_loss_ha:.0f} ha, Gain={gain.get('gain_area_ha', 0):.0f} ha, Net={net_change_ha:.0f} ha")
            
            return {
                'tree_cover_2000_ha': cover_2000.get('tree_cover_area_ha', 0),
                'tree_cover_2000_percent': cover_2000.get('tree_cover_percent', 0),
                'forest_loss_total_ha': total_loss_ha,
                'forest_loss_annual_avg_ha': total_loss_ha / (end_year - start_year + 1) if (end_year - start_year + 1) > 0 else 0,
                'forest_gain_ha': gain.get('gain_area_ha', 0),
                'net_forest_change_ha': net_change_ha,
                'net_forest_change_percent': (net_change_ha / (cover_2000.get('tree_cover_area_ha', 1))) * 100 if cover_2000.get('tree_cover_area_ha', 0) > 0 else 0,
                'analysis_period': f'{start_year}-{end_year}',
            }
        
        except Exception as e:
            logger.error(f"Error in forest dynamics analysis: {e}")
            return {}


# Singleton instance
_hansen_analyzer = None


def get_hansen_analyzer() -> HansenAnalyzer:
    """Get or create Hansen analyzer instance."""
    global _hansen_analyzer
    if _hansen_analyzer is None:
        _hansen_analyzer = HansenAnalyzer()
    return _hansen_analyzer
