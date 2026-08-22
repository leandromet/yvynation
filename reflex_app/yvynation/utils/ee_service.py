"""
Earth Engine service wrapper for Reflex app.
Handles initialization, authentication, and data operations.
"""

import os
import ee
import pandas as pd
from typing import Optional, Dict, Any, Tuple
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

# Global initialization flag
_EE_INITIALIZED = False


def initialize_earth_engine() -> bool:
    """
    Initialize Earth Engine with multiple authentication methods.
    
    Priority:
    1. Cloud Run: EE_PRIVATE_KEY + EE_SERVICE_ACCOUNT_EMAIL
    2. Google Cloud: Application Default Credentials
    3. Local: Service account JSON file
    
    Returns:
        bool: True if successful
    """
    global _EE_INITIALIZED
    
    if _EE_INITIALIZED:
        logger.debug("EE already initialized")
        return True
    
    project_id = os.environ.get('GCP_PROJECT_ID', 'ee-leandromet')
    
    # Method 1: Environment variables (Cloud Run)
    private_key = os.environ.get('EE_PRIVATE_KEY')
    service_account_email = os.environ.get('EE_SERVICE_ACCOUNT_EMAIL')
    
    if private_key and service_account_email:
        try:
            logger.info("Initializing EE with environment variables")
            credentials_dict = {
                'type': 'service_account',
                'project_id': project_id,
                'private_key_id': os.environ.get('EE_PRIVATE_KEY_ID', ''),
                'private_key': private_key,
                'client_email': service_account_email,
                'client_id': os.environ.get('EE_CLIENT_ID', ''),
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            }
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_dict,
                scopes=[
                    'https://www.googleapis.com/auth/earthengine',
                    'https://www.googleapis.com/auth/cloud-platform'
                ]
            )
            ee.Initialize(credentials, project=project_id)
            _EE_INITIALIZED = True
            logger.info("✓ Earth Engine initialized with env credentials")
            return True
        except Exception as e:
            logger.warning(f"Failed with env vars: {e}")
    
    # Method 2: Application Default Credentials
    try:
        logger.info("Attempting EE initialization with ADC")
        ee.Initialize(project=project_id)
        _EE_INITIALIZED = True
        logger.info("✓ Earth Engine initialized with ADC")
        return True
    except Exception as e:
        logger.warning(f"Failed with ADC: {e}")
    
    # Method 3: JSON service account file
    sa_json = os.environ.get('EE_SERVICE_ACCOUNT_JSON')
    if sa_json and os.path.exists(sa_json):
        try:
            logger.info(f"Attempting EE init with JSON: {sa_json}")
            credentials = service_account.Credentials.from_service_account_file(
                sa_json,
                scopes=[
                    'https://www.googleapis.com/auth/earthengine',
                    'https://www.googleapis.com/auth/cloud-platform'
                ]
            )
            ee.Initialize(credentials, project=project_id)
            _EE_INITIALIZED = True
            logger.info("✓ Earth Engine initialized with JSON file")
            return True
        except Exception as e:
            logger.warning(f"Failed with JSON: {e}")
    
    error = "Failed to initialize EE. Check environment variables."
    logger.error(error)
    raise RuntimeError(error)


def is_ee_initialized() -> bool:
    """Check if EE is initialized."""
    return _EE_INITIALIZED


def get_ee() -> ee.Image.__class__:
    """Get EE module (ensures initialization)."""
    if not _EE_INITIALIZED:
        initialize_earth_engine()
    return ee


def mean_pixel_area_ha(geometry: "ee.Geometry", scale: int = 30, max_pixels: float = 1e9) -> float:
    """True mean pixel area (ha) inside ``geometry``, in place of a flat 0.09 ha/pixel
    (30 m) assumption that drifts with latitude — Earth Engine pixels are only exactly
    ``scale``x``scale`` metres at the equator.

    Pair with a ``frequencyHistogram`` reduceRegion on the same geometry/scale and
    convert counts with ``count * mean_pixel_area_ha(...)`` instead of ``count * 0.09``.
    Falls back to the nominal 0.09 ha (900 m² at 30 m) if the call fails, so callers
    never need their own except-branch for this.
    """
    try:
        stats = (
            ee.Image.pixelArea()
            .reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=scale,
                maxPixels=max_pixels,
            )
            .getInfo()
        )
        mean_m2 = (stats or {}).get("area")
        if mean_m2:
            return float(mean_m2) / 10_000.0
    except Exception as e:  # noqa: BLE001
        logger.warning(f"mean_pixel_area_ha failed, falling back to nominal {scale}m: {e}")
    return (scale * scale) / 10_000.0


class EarthEngineService:
    """Service for Earth Engine operations."""
    
    _initialized: bool = False
    _mapbiomas_v10_1: Optional[ee.Image] = None
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
    def load_mapbiomas(cls, version: str = None) -> Optional[ee.Image]:
        """Load MapBiomas dataset.

        ``version`` defaults to ``MAPBIOMAS_DEFAULT_COLLECTION`` (currently 'v10_1').
        Pass 'v9' or 'v8' explicitly for older collections.
        """
        if not cls._initialized:
            logger.error("Earth Engine not initialized")
            return None

        from ..config.config import MAPBIOMAS_COLLECTIONS, MAPBIOMAS_DEFAULT_COLLECTION
        if version is None:
            version = MAPBIOMAS_DEFAULT_COLLECTION

        try:
            if version == 'v10_1':
                if cls._mapbiomas_v10_1 is None:
                    cls._mapbiomas_v10_1 = ee.Image(MAPBIOMAS_COLLECTIONS['v10_1'])
                return cls._mapbiomas_v10_1
            elif version == 'v9':
                if cls._mapbiomas_v9 is None:
                    cls._mapbiomas_v9 = ee.Image(MAPBIOMAS_COLLECTIONS['v9'])
                return cls._mapbiomas_v9
            elif version == 'v8':
                if cls._mapbiomas_v8 is None:
                    cls._mapbiomas_v8 = ee.Image(MAPBIOMAS_COLLECTIONS['v8'])
                return cls._mapbiomas_v8
            else:
                # Arbitrary version key passed — look it up in config
                asset = MAPBIOMAS_COLLECTIONS.get(version)
                if asset:
                    return ee.Image(asset)
                logger.warning(f"Unknown MapBiomas version '{version}', falling back to default")
                return cls.load_mapbiomas(MAPBIOMAS_DEFAULT_COLLECTION)
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
            
            mapbiomas = cls.load_mapbiomas()  # uses MAPBIOMAS_DEFAULT_COLLECTION
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
                    area_per_px_ha = mean_pixel_area_ha(ee_geometry, scale=30)
                    records = []
                    for class_id, count in histogram_data.items():
                        class_id = int(class_id)
                        class_name = MAPBIOMAS_LABELS.get(class_id, f"Class {class_id}")
                        area_ha = count * area_per_px_ha
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
                area_per_px_ha = mean_pixel_area_ha(ee_geometry, scale=30)
                records = []
                for class_id_str, count in histogram.items():
                    class_id = int(class_id_str)
                    count = int(count)
                    area_ha = count * area_per_px_ha
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
