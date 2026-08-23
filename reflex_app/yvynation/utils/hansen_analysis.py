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
from ..config.config import HANSEN_CONSOLIDATED_MAPPING, HANSEN_GFC_DATASET
from .ee_service import mean_pixel_area_ha

logger = logging.getLogger(__name__)


class HansenAnalyzer:
    """
    Analyzer for Hansen Global Forest Change data.
    Tracks global forest loss and gain detection.
    """

    # Hansen Global Forest Change dataset - use latest from config
    HANSEN_DATASET = HANSEN_GFC_DATASET

    def __init__(self):
        """Initialize analyzer."""
        self.hansen_dataset = None
        self._load_dataset()

    def _load_dataset(self):
        """Load Hansen dataset from Earth Engine."""
        try:
            logger.info(f"Loading Hansen GFC from: {self.HANSEN_DATASET}")
            self.hansen_dataset = ee.Image(self.HANSEN_DATASET)
            logger.info("✓ Loaded Hansen Global Forest Change dataset")
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
    
    def analyze_gfc(
        self,
        geometry: ee.Geometry,
        scale: int = 30
    ) -> Dict[str, Any]:
        """
        Hansen GFC analysis using frequencyHistogram (3 EE calls).
        Bands: treecover2000 (0-100%), lossyear (0=no loss, 1-24=year offset),
        gain (0=no gain, 1=gain 2000-2012).
        Ported from the working streamlit gfc_analysis.py approach.
        """
        try:
            from ..config.config import HANSEN_GFC_DATASET
            dataset = ee.Image(HANSEN_GFC_DATASET)

            # Shared across all three histograms below — same geometry/scale.
            area_per_px_ha = mean_pixel_area_ha(geometry, scale=scale)

            # ---- Tree Cover 2000 (band: treecover2000) --------------------
            cover_histogram: dict = {}
            try:
                stats = dataset.select(["treecover2000"]).reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=scale,
                    maxPixels=int(1e9),
                ).getInfo()
                cover_histogram = stats.get("treecover2000") or {}
                logger.info(f"GFC cover histogram: {len(cover_histogram)} buckets")
            except Exception as e:
                logger.error(f"GFC cover histogram failed: {e}")

            cover_records = []
            for pct_str, cnt in cover_histogram.items():
                pct = int(pct_str)
                cover_records.append({
                    "Percent_Cover": pct,
                    "Pixels": int(cnt),
                    "Area_ha": round(int(cnt) * area_per_px_ha, 2),
                })
            df_cover = pd.DataFrame(cover_records).sort_values("Percent_Cover") if cover_records else pd.DataFrame()

            # ---- Tree Loss Year (band: lossyear) --------------------------
            loss_histogram: dict = {}
            try:
                stats = dataset.select(["lossyear"]).reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=scale,
                    maxPixels=int(1e9),
                ).getInfo()
                loss_histogram = stats.get("lossyear") or {}
                logger.info(f"GFC loss histogram: {len(loss_histogram)} buckets")
            except Exception as e:
                logger.error(f"GFC loss histogram failed: {e}")

            loss_records = []
            for code_str, cnt in loss_histogram.items():
                code = int(code_str)
                loss_records.append({
                    "Year_Code": code,
                    "Year": "No Loss" if code == 0 else str(2000 + code),
                    "Pixels": int(cnt),
                    "Area_ha": round(int(cnt) * area_per_px_ha, 2),
                })
            df_loss = pd.DataFrame(loss_records).sort_values("Year_Code") if loss_records else pd.DataFrame()

            # ---- Tree Gain (band: gain) ------------------------------------
            gain_histogram: dict = {}
            try:
                stats = dataset.select(["gain"]).reduceRegion(
                    reducer=ee.Reducer.frequencyHistogram(),
                    geometry=geometry,
                    scale=scale,
                    maxPixels=int(1e9),
                ).getInfo()
                gain_histogram = stats.get("gain") or {}
                logger.info(f"GFC gain histogram: {len(gain_histogram)} buckets")
            except Exception as e:
                logger.error(f"GFC gain histogram failed: {e}")

            gain_records = []
            for code_str, cnt in gain_histogram.items():
                code = int(code_str)
                gain_records.append({
                    "Gain_Code": code,
                    "Status": "Gain (2000-2012)" if code == 1 else "No Gain",
                    "Pixels": int(cnt),
                    "Area_ha": round(int(cnt) * area_per_px_ha, 2),
                })
            df_gain = pd.DataFrame(gain_records).sort_values("Gain_Code") if gain_records else pd.DataFrame()

            if df_cover.empty and df_loss.empty and df_gain.empty:
                return {"error": "No GFC data found in this area", "type": "hansen_gfc", "table": [], "summary": {}, "data": []}

            # ---- Derive summary metrics ------------------------------------
            total_area_ha = df_cover["Area_ha"].sum() if not df_cover.empty else 0
            tree_cover_ha = df_cover[df_cover["Percent_Cover"] > 0]["Area_ha"].sum() if not df_cover.empty else 0
            loss_ha = df_loss[df_loss["Year_Code"] > 0]["Area_ha"].sum() if not df_loss.empty else 0
            gain_ha = df_gain[df_gain["Gain_Code"] == 1]["Area_ha"].sum() if not df_gain.empty else 0
            net_ha = gain_ha - loss_ha

            cover_pct = (tree_cover_ha / total_area_ha * 100) if total_area_ha > 0 else 0
            loss_pct = (loss_ha / tree_cover_ha * 100) if tree_cover_ha > 0 else 0
            gain_pct = (gain_ha / tree_cover_ha * 100) if tree_cover_ha > 0 else 0

            gfc_records = [
                {"Metric": "Tree Cover 2000", "Area_ha": round(tree_cover_ha),
                 "Percent": f"{cover_pct:.1f}%", "Description": "Baseline canopy cover (>0%)"},
                {"Metric": "Forest Loss",     "Area_ha": round(loss_ha),
                 "Percent": f"{loss_pct:.1f}%", "Description": "Forest loss 2001-2023"},
                {"Metric": "Forest Gain",     "Area_ha": round(gain_ha),
                 "Percent": f"{gain_pct:.1f}%", "Description": "Forest gain 2000-2012"},
            ]

            logger.info(
                f"GFC complete: cover={tree_cover_ha:.0f}ha ({cover_pct:.1f}%), "
                f"loss={loss_ha:.0f}ha, gain={gain_ha:.0f}ha, net={net_ha:.0f}ha"
            )

            return {
                "type": "hansen_gfc",
                "source": "Hansen GFC",
                "data": gfc_records,
                "table": gfc_records,
                "summary": {
                    "tree_cover_2000_ha": round(tree_cover_ha),
                    "forest_loss_ha":     round(loss_ha),
                    "forest_gain_ha":     round(gain_ha),
                    "net_change_ha":      round(net_ha),
                },
                # Detailed distributions for richer UI
                "tree_cover_data": df_cover.to_dict("records") if not df_cover.empty else [],
                "tree_loss_data":  df_loss.to_dict("records")  if not df_loss.empty  else [],
                "tree_gain_data":  df_gain.to_dict("records")  if not df_gain.empty  else [],
            }

        except Exception as e:
            logger.error(f"GFC analysis failed: {e}", exc_info=True)
            return {"error": str(e), "type": "hansen_gfc", "table": [], "summary": {}, "data": []}
    
    def get_area_distribution(
        self,
        geometry: ee.Geometry,
        year: str = '2020',
        scale: int = 30
    ) -> Optional[pd.DataFrame]:
        """
        Get area distribution by Hansen class for a given geometry.

        Args:
            geometry: Area of interest
            year: Year as string (e.g., '2020')
            scale: Analysis scale

        Returns:
            DataFrame with Class_ID, Class, Pixels, Area_ha columns
        """
        try:
            if not self.is_available():
                logger.error("Hansen dataset not available")
                return None

            # Get the Hansen image (using GLAD LCLUC - unified landcover data)
            try:
                from ..config.config import HANSEN_DATASETS, HANSEN_LABELS
            except ImportError:
                logger.error("Cannot import HANSEN_DATASETS or HANSEN_LABELS from config")
                return None

            # Load GLAD LCLUC data if available, otherwise use Hansen GFC
            if str(year) in HANSEN_DATASETS:
                hansen_image = ee.Image(HANSEN_DATASETS[str(year)])
            else:
                # Fallback to Hansen GFC
                hansen_image = self.hansen_dataset

            # Calculate frequency histogram
            histogram = hansen_image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=scale,
                maxPixels=int(1e13)
            ).getInfo()

            if not histogram:
                logger.warning(f"No Hansen histogram data for year {year}")
                return None

            # Discover the band key — try known names then fall back to first dict value
            histogram_data: dict = {}
            for candidate in ("b1", "classification", "VV", "lossyear", "treecover2000"):
                if candidate in histogram and isinstance(histogram[candidate], dict):
                    histogram_data = histogram[candidate]
                    break
            if not histogram_data:
                for v in histogram.values():
                    if isinstance(v, dict) and v:
                        histogram_data = v
                        break
            if not histogram_data:
                logger.warning(f"Hansen {year}: histogram exists but no band data found; keys={list(histogram.keys())}")
                return None

            # Convert histogram to DataFrame
            data = histogram_data
            if not data:
                return None

            records = []
            area_per_px_ha = mean_pixel_area_ha(geometry, scale=scale)
            for class_id_str, count in data.items():
                try:
                    class_id = int(class_id_str)
                    class_name = HANSEN_LABELS.get(class_id, f"Class {class_id}")
                    area_ha = count * area_per_px_ha

                    records.append({
                        'Class_ID': class_id,
                        'Class': class_name,
                        'Pixels': int(count),
                        'Area_ha': round(area_ha, 2),
                        'Area_km2': round(area_ha / 100, 2),
                    })
                except (ValueError, TypeError):
                    continue

            if not records:
                return None

            df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
            df['Year'] = str(year)

            logger.info(f"Hansen {year} area distribution: {len(df)} classes found")
            return df

        except Exception as e:
            logger.error(f"Error getting Hansen area distribution for {year}: {e}")
            return None




# Singleton instance
_hansen_analyzer = None


def get_hansen_analyzer() -> HansenAnalyzer:
    """Get or create Hansen analyzer instance."""
    global _hansen_analyzer
    if _hansen_analyzer is None:
        _hansen_analyzer = HansenAnalyzer()
    return _hansen_analyzer
