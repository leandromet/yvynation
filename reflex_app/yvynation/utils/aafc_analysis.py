"""
AAFC (Annual Crop Inventory) Analysis for Canadian territories.
Handles forest and crop inventory analysis using Earth Engine AAFC dataset.
"""

import ee
import pandas as pd
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AAFCAnalyzer:
    """Singleton analyzer for AAFC Annual Crop Inventory data (Canada)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize AAFC analyzer."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._dataset_cache = {}

    def get_aafc_data(self, year: int) -> Optional[ee.Image]:
        """
        Get AAFC image for a specific year.

        Args:
            year: Year (e.g., 2023)

        Returns:
            Earth Engine Image or None
        """
        try:
            from ..config.config import AAFC_ACI_DATASET

            aafc_collection = ee.ImageCollection(AAFC_ACI_DATASET)
            filtered = aafc_collection.filter(
                ee.Filter.date(f'{year}-01-01', f'{year}-12-31')
            ).first()

            return filtered
        except Exception as e:
            logger.error(f"Error getting AAFC data for {year}: {e}")
            return None

    def analyze_single_year(self, geometry: ee.Geometry, year: int) -> Optional[pd.DataFrame]:
        """
        Analyze AAFC land cover for a single year.

        Args:
            geometry: Earth Engine geometry (AOI)
            year: Year to analyze (e.g., 2023)

        Returns:
            DataFrame with class, pixels, and area_ha columns
        """
        try:
            from ..config.config import AAFC_LABELS

            aafc_image = self.get_aafc_data(year)
            if aafc_image is None:
                logger.warning(f"No AAFC data available for year {year}")
                return None

            # Select landcover band and compute histogram
            landcover = aafc_image.select(['landcover'])

            stats = landcover.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=int(1e9)
            ).getInfo()

            if not stats or 'landcover' not in stats:
                logger.warning(f"No valid AAFC stats for {year}")
                return None

            histogram = stats.get('landcover', {})
            if not histogram:
                return None

            # Convert histogram to DataFrame
            records = []
            for value_str, count in histogram.items():
                try:
                    value = int(value_str)
                    class_name = AAFC_LABELS.get(value, f"Class {value}")
                    area_ha = count * 0.09  # 30m pixel = 0.09 ha

                    records.append({
                        'Class_ID': value,
                        'Class_Name': class_name,
                        'Pixels': int(count),
                        'Area_ha': round(area_ha, 2),
                        'Area_km2': round(area_ha / 100, 2),
                    })
                except ValueError:
                    continue

            if not records:
                return None

            df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
            df['Year'] = year

            return df

        except Exception as e:
            logger.error(f"Error analyzing AAFC for {year}: {e}")
            return None

    def analyze_year_range(self, geometry: ee.Geometry,
                          year_start: int, year_end: int) -> Optional[pd.DataFrame]:
        """
        Analyze AAFC data for multiple years.

        Args:
            geometry: Earth Engine geometry
            year_start: Start year
            year_end: End year (inclusive)

        Returns:
            Combined DataFrame for all years
        """
        try:
            dfs = []
            for year in range(year_start, year_end + 1):
                df = self.analyze_single_year(geometry, year)
                if df is not None:
                    dfs.append(df)

            if not dfs:
                return None

            return pd.concat(dfs, ignore_index=True)

        except Exception as e:
            logger.error(f"Error analyzing AAFC year range: {e}")
            return None

    def compare_years(self, geometry: ee.Geometry,
                      year1: int, year2: int) -> Optional[Dict[str, Any]]:
        """
        Compare AAFC data between two years.

        Args:
            geometry: Earth Engine geometry
            year1: First year
            year2: Second year

        Returns:
            Dictionary with comparison results
        """
        try:
            df1 = self.analyze_single_year(geometry, year1)
            df2 = self.analyze_single_year(geometry, year2)

            if df1 is None or df2 is None:
                return None

            # Merge on class
            merged = pd.merge(
                df1[['Class_ID', 'Class_Name', 'Area_ha']].rename(columns={'Area_ha': 'Area_ha_Y1'}),
                df2[['Class_ID', 'Class_Name', 'Area_ha']].rename(columns={'Area_ha': 'Area_ha_Y2'}),
                on=['Class_ID', 'Class_Name'],
                how='outer'
            ).fillna(0)

            merged['Change_ha'] = merged['Area_ha_Y2'] - merged['Area_ha_Y1']
            merged['Change_Pct'] = (merged['Change_ha'] / (merged['Area_ha_Y1'] + 1)) * 100

            return {
                'data': merged.to_dict('records'),
                'year_start': year1,
                'year_end': year2,
                'summary': {
                    'total_area_y1': df1['Area_ha'].sum(),
                    'total_area_y2': df2['Area_ha'].sum(),
                }
            }

        except Exception as e:
            logger.error(f"Error comparing AAFC years: {e}")
            return None

    def get_class_timeline(self, geometry: ee.Geometry, class_id: int,
                           year_start: int, year_end: int) -> Optional[pd.DataFrame]:
        """
        Get time series of a specific class over years.

        Args:
            geometry: Earth Engine geometry
            class_id: AAFC class ID
            year_start: Start year
            year_end: End year

        Returns:
            DataFrame with year and area columns
        """
        try:
            from ..config.config import AAFC_LABELS

            df = self.analyze_year_range(geometry, year_start, year_end)
            if df is None:
                return None

            class_name = AAFC_LABELS.get(class_id, f"Class {class_id}")
            class_df = df[df['Class_ID'] == class_id][['Year', 'Area_ha']].copy()

            if class_df.empty:
                return None

            class_df['Class_Name'] = class_name
            return class_df.sort_values('Year')

        except Exception as e:
            logger.error(f"Error getting AAFC class timeline: {e}")
            return None


# Singleton instance
def get_aafc_analyzer() -> AAFCAnalyzer:
    """Get or create AAFC analyzer instance."""
    return AAFCAnalyzer()
