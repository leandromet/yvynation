"""
Extended Earth Engine service layer for Yvynation Reflex app.
Handles territory loading, analysis, and data processing.
"""

import ee
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any

from .ee_service import mean_pixel_area_ha

logger = logging.getLogger(__name__)


class ExtendedEarthEngineService:
    """Extended EE service with territory and analysis functions."""
    
    def __init__(self):
        """Initialize the extended EE service."""
        self.territories_fc = None
        self.territory_names = []
        self.mapbiomas = None
        self.hansen_datasets = {
            '2000': 'projects/glad/GLCLU2020/v2/LCLUC_2000',
            '2005': 'projects/glad/GLCLU2020/v2/LCLUC_2005',
            '2010': 'projects/glad/GLCLU2020/v2/LCLUC_2010',
            '2015': 'projects/glad/GLCLU2020/v2/LCLUC_2015',
            '2020': 'projects/glad/GLCLU2020/v2/LCLUC_2020',
        }
        self.mapbiomas_labels = self._load_mapbiomas_labels()
        self.hansen_labels = self._load_hansen_labels()
    
    @staticmethod
    def _load_mapbiomas_labels() -> Dict[int, str]:
        """Load MapBiomas classification labels (English, from central config)."""
        from ..config.config import MAPBIOMAS_LABELS
        return MAPBIOMAS_LABELS

    @staticmethod
    def _load_hansen_labels() -> Dict[int, str]:
        """Load Hansen GLCLU label mappings (English, from central config)."""
        from ..config.config import HANSEN_LABELS
        return HANSEN_LABELS
    
    def load_territories(self) -> Tuple[bool, List[str]]:
        """
        Load indigenous territory display-keys from the local GeoPackage.

        No EE round-trip: delegates to :mod:`territory_service`.

        Returns:
            tuple: (success, territory_display_keys)
        """
        try:
            from .territory_service import get_territory_service
            svc = get_territory_service()
            if not svc.is_ready():
                logger.warning("TerritoryService not ready, returning empty list")
                return False, []
            keys = svc.get_all_display_keys()
            self.territory_names = keys
            logger.info(f"✓ Loaded {len(keys)} territory keys from local GeoPackage")
            return True, keys
        except Exception as e:
            logger.error(f"Failed to load territories from GeoPackage: {e}")
            return False, []
    
    def _get_territory_names(self) -> List[str]:
        """Extract territory display keys (delegates to local GeoPackage service)."""
        try:
            from .territory_service import get_territory_service
            return get_territory_service().get_all_display_keys()
        except Exception as e:
            logger.error(f"Error getting territory names: {e}")
            return []

    def debug_all_territories(self) -> List[Dict]:
        """Return detailed info about all territories for debugging."""
        try:
            if not self.territories_fc:
                return []

            # Get all features
            features = self.territories_fc.getInfo()['features']
            result = []

            for feat in features:
                props = feat.get('properties', {})
                result.append({
                    'all_properties': props,
                    'geometry_type': feat.get('geometry', {}).get('type'),
                })

            return result
        except Exception as e:
            logger.error(f"Error in debug_all_territories: {e}")
            return []
    
    def get_territory_geometry(self, display_key: str) -> Optional[ee.Geometry]:
        """Return an ``ee.Geometry`` for *display_key* built from local GeoPackage data.

        No EE network call — the geometry dict is pulled from the local file
        and wrapped in ``ee.Geometry()``.
        """
        try:
            from .territory_service import get_territory_service
            svc = get_territory_service()
            ee_geom = svc.get_ee_geometry(display_key)
            if ee_geom is not None:
                logger.info(f"Built EE geometry for '{display_key}' from local GeoPackage")
                return ee_geom
            # Fallback: try stripping the " (cod)" suffix for legacy callers
            if "(" in display_key and ")" in display_key:
                base_name = display_key.rsplit("(", 1)[0].strip()
                ee_geom = svc.get_ee_geometry(base_name)
                if ee_geom is not None:
                    logger.info(f"Built EE geometry for '{display_key}' via base-name fallback")
                    return ee_geom
            logger.warning(f"Territory '{display_key}' not found in local GeoPackage")
            return None
        except Exception as e:
            logger.error(f"Error getting territory geometry for {display_key}: {e}")
            return None
    
    def get_name_property(self) -> str:
        """Return the property key used for territory display names (local GeoPackage)."""
        return "display_key"

    def get_indigenous_lands_tile_url(self) -> Optional[str]:
        """Deprecated — territory boundaries now come from the local GeoPackage.

        Returns ``None`` so callers fall through to the local GeoJSON path.
        The interactive Folium layer is built directly from
        :func:`territory_service.get_all_geojson_fc` in ``map_builder.py``.
        """
        return None

    def get_mapbiomas(self) -> ee.Image:
        """Get or load MapBiomas Image (default: Collection 10.1)."""
        if self.mapbiomas is None:
            from ..config.config import MAPBIOMAS_COLLECTIONS, MAPBIOMAS_DEFAULT_COLLECTION
            asset = MAPBIOMAS_COLLECTIONS.get(
                MAPBIOMAS_DEFAULT_COLLECTION,
                MAPBIOMAS_COLLECTIONS['v10_1'],
            )
            self.mapbiomas = ee.Image(asset)
        return self.mapbiomas
    
    def analyze_mapbiomas(self, geometry: ee.Geometry, year: int) -> pd.DataFrame:
        """
        Analyze MapBiomas land cover for a geometry.

        Args:
            geometry: EE geometry to analyze
            year: Year to analyze (e.g., 2023)

        Returns:
            DataFrame with land cover breakdown
        """
        try:
            # MapBiomas Collection 10.1 is a single multi-band Image with bands like 'classification_2024', 'classification_2023', etc
            mapbiomas = self.get_mapbiomas()

            # Select the specific year band
            band = f'classification_{year}'
            image = mapbiomas.select(band)

            # Get histogram
            hist = image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=int(1e9)
            ).getInfo()

            if not hist:
                logger.warning(f"No mapbiomas data for year {year}")
                return pd.DataFrame()

            # Process histogram
            records = []
            band_key = band  # Should be the band we selected

            if band_key in hist and hist[band_key]:
                area_per_px_ha = mean_pixel_area_ha(geometry, scale=30)
                for class_id_str, count in hist[band_key].items():
                    try:
                        class_id = int(class_id_str)
                        class_name = self.mapbiomas_labels.get(class_id, f"Class {class_id}")
                        area_ha = count * area_per_px_ha

                        records.append({
                            'Class_ID': class_id,
                            'Class': class_name,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    except (ValueError, TypeError):
                        continue

            if not records:
                logger.warning(f"No valid class data for MapBiomas {year}")
                return pd.DataFrame()

            df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
            logger.info(f"✓ Analyzed MapBiomas {year}: {len(df)} classes")
            return df

        except Exception as e:
            logger.error(f"Error analyzing MapBiomas {year}: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def analyze_hansen(self, geometry: ee.Geometry, year: str) -> pd.DataFrame:
        """
        Analyze Hansen/GLAD forest change for a geometry.
        
        Args:
            geometry: EE geometry to analyze
            year: Year to analyze (str like '2020')
        
        Returns:
            DataFrame with forest change breakdown
        """
        try:
            year_key = str(year)
            
            if year_key not in self.hansen_datasets:
                return pd.DataFrame()
            
            hansen_image = ee.Image(self.hansen_datasets[year_key])
            
            # Get histogram
            hist = hansen_image.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            # Process histogram
            records = []
            band_key = list(hist.keys())[0] if hist else None
            
            if band_key and hist[band_key]:
                area_per_px_ha = mean_pixel_area_ha(geometry, scale=30)
                for class_id_str, count in hist[band_key].items():
                    class_id = int(class_id_str)
                    class_name = self.hansen_labels.get(class_id, f"Class {class_id}")
                    area_ha = count * area_per_px_ha
                    
                    records.append({
                        'Class_ID': class_id,
                        'Class': class_name,
                        'Pixels': count,
                        'Area_ha': round(area_ha, 2)
                    })
            
            df = pd.DataFrame(records).sort_values('Area_ha', ascending=False)
            return df
        
        except Exception as e:
            logger.error(f"Error analyzing Hansen: {e}")
            return pd.DataFrame()


# Global instance
_ee_service = None


def get_ee_service() -> ExtendedEarthEngineService:
    """Get or create the global EE service instance."""
    global _ee_service
    if _ee_service is None:
        _ee_service = ExtendedEarthEngineService()
    return _ee_service
