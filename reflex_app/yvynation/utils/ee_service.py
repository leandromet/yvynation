"""
Earth Engine service wrapper for async/background processing.
Handles initialization and data analysis operations.
"""

import ee
import pandas as pd
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class EarthEngineService:
    """Service for Earth Engine operations."""
    
    _initialized: bool = False
    _mapbiomas_v9: Optional[ee.Image] = None
    _mapbiomas_v8: Optional[ee.Image] = None
    _territories: Optional[ee.FeatureCollection] = None
    
    @classmethod
    def initialize(cls, use_service_account: bool = False, credentials_path: Optional[str] = None):
        """
        Initialize Earth Engine connection.
        
        Args:
            use_service_account: Whether to use service account credentials
            credentials_path: Path to service account JSON file
        """
        if cls._initialized:
            return True
            
        try:
            if use_service_account and credentials_path:
                ee.Authenticate(credentials_path)
            ee.Initialize()
            cls._initialized = True
            logger.info("✓ Earth Engine initialized")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to initialize Earth Engine: {e}")
            return False
    
    @classmethod
    def load_mapbiomas(cls, version: str = 'v9') -> Optional[ee.Image]:
        """Load MapBiomas dataset."""
        if not cls._initialized:
            logger.error("Earth Engine not initialized")
            return None
            
        try:
            if version == 'v9':
                if cls._mapbiomas_v9 is None:
                    cls._mapbiomas_v9 = ee.Image('projects/mapbiomas-workspace/public/collection9/mapbiomas_collection90_integration_v1')
                return cls._mapbiomas_v9
            elif version == 'v8':
                if cls._mapbiomas_v8 is None:
                    cls._mapbiomas_v8 = ee.Image('projects/mapbiomas-workspace/public/collection8/mapbiomas_collection80_integration_v1')
                return cls._mapbiomas_v8
        except Exception as e:
            logger.error(f"Error loading MapBiomas {version}: {e}")
        return None
    
    @classmethod
    def load_territories(cls, territory_type: str = 'indigenous') -> Optional[ee.FeatureCollection]:
        """Load territory datasets."""
        if not cls._initialized:
            logger.error("Earth Engine not initialized")
            return None
            
        try:
            if territory_type == 'indigenous':
                if cls._territories is None:
                    # FUNAI Indigenous Territories
                    cls._territories = ee.FeatureCollection('projects/mapbiomas-workspace/AUXILIAR/territories/indigenous_territories_funai')
                return cls._territories
        except Exception as e:
            logger.error(f"Error loading territories: {e}")
        return None
    
    @classmethod
    def analyze_mapbiomas_geometry(
        cls,
        geometry: Dict[str, Any],
        year: int,
        area_name: str = "Area"
    ) -> Optional[pd.DataFrame]:
        """
        Analyze MapBiomas data for a given geometry and year.
        
        Returns:
            pd.DataFrame: Analysis results or None if error
        """
        try:
            from ..config import MAPBIOMAS_LABELS
            
            mapbiomas = cls.load_mapbiomas('v9')
            if mapbiomas is None:
                return None
            
            band = f'classification_{year}'
            image = mapbiomas.select(band)
            
            # Convert geometry dict to EE geometry
            ee_geometry = ee.Geometry(geometry)
            
            stats = image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=ee_geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            if stats:
                band_key = f'classification_{year}' if f'classification_{year}' in stats else list(stats.keys())[0]
                histogram_data = stats.get(band_key, {})
                
                if histogram_data:
                    records = []
                    for class_id, count in histogram_data.items():
                        class_id = int(class_id)
                        class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                        area_ha = count * 0.09
                        records.append({
                            "Class_ID": class_id,
                            "Class": class_name,
                            "Pixels": int(count),
                            "Area_ha": round(area_ha, 2)
                        })
                    df = pd.DataFrame(records).sort_values("Area_ha", ascending=False)
                    return df
        except Exception as e:
            logger.error(f"Error analyzing MapBiomas for {area_name}: {e}")
        return None
    
    @classmethod
    def analyze_hansen_geometry(
        cls,
        geometry: Dict[str, Any],
        year: int,
        area_name: str = "Area"
    ) -> Optional[pd.DataFrame]:
        """
        Analyze Hansen Global Forest Change data.
        
        Returns:
            pd.DataFrame: Analysis results or None if error
        """
        try:
            from ..config import HANSEN_DATASETS, HANSEN_OCEAN_MASK
            
            if not cls._initialized:
                return None
            
            landmask = ee.Image(HANSEN_OCEAN_MASK).lte(1)
            hansen_image = ee.Image(HANSEN_DATASETS[str(year)]).updateMask(landmask)
            
            # Convert geometry dict to EE geometry
            ee_geometry = ee.Geometry(geometry)
            
            stats = hansen_image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=ee_geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            if stats:
                # Process histogram into dataframe
                histogram = stats.get('classification', {}) if 'classification' in stats else stats
                records = []
                for class_id_str, count in histogram.items():
                    class_id = int(class_id_str)
                    count = int(count)
                    area_ha = count * 0.09
                    records.append({
                        "Class_ID": class_id,
                        "Pixels": count,
                        "Area_ha": round(area_ha, 2)
                    })
                df = pd.DataFrame(records).sort_values("Area_ha", ascending=False)
                return df
        except Exception as e:
            logger.error(f"Error analyzing Hansen for {area_name}: {e}")
        return None
