"""
EE tile layer management for Folium map visualization.
Converts Earth Engine images to map tiles and displays them.
"""

import ee
import logging
from typing import Dict, Tuple, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class EETileManager:
    """Manage Earth Engine tile layer URLs for Folium display."""
    
    def __init__(self):
        """Initialize tile cache."""
        self._tile_cache: Dict[str, Tuple[str, str]] = {}
    
    def get_mapbiomas_tile(self, year: int) -> Optional[Tuple[str, str]]:
        """
        Get tile URL for MapBiomas data for a specific year.
        Returns: (tile_url, attribution) or None if error
        """
        try:
            cache_key = f"mapbiomas_{year}"

            if cache_key in self._tile_cache:
                return self._tile_cache[cache_key]

            # Load MapBiomas v9 (it's an Image, not ImageCollection)
            from ..config.config import MAPBIOMAS_COLLECTIONS, MAPBIOMAS_PALETTE

            mapbiomas_asset = MAPBIOMAS_COLLECTIONS.get('v9',
                'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')

            image = ee.Image(mapbiomas_asset)

            # Select the year band
            band = f'classification_{year}'
            year_image = image.select(band)

            if year_image is None:
                logger.warning(f"No MapBiomas data for year {year}")
                return None

            # Get map ID (tile URL)
            map_id = year_image.getMapId({'min': 0, 'max': 49, 'palette': MAPBIOMAS_PALETTE[:50]})

            tile_url = map_id['tile_fetcher'].url_format
            attribution = f"MapBiomas {year}"

            self._tile_cache[cache_key] = (tile_url, attribution)
            logger.info(f"Generated MapBiomas {year} tile URL")

            return (tile_url, attribution)

        except Exception as e:
            logger.error(f"Failed to get MapBiomas tile for {year}: {e}")
            return None
    
    def get_hansen_tile(self, layer_type: str = "loss") -> Optional[Tuple[str, str]]:
        """
        Get tile URL for Hansen forest change data.
        
        Args:
            layer_type: 'loss', 'gain', or 'cover'
        
        Returns:
            (tile_url, attribution) or None if error
        """
        try:
            cache_key = f"hansen_{layer_type}"
            
            if cache_key in self._tile_cache:
                return self._tile_cache[cache_key]
            
            # Load Hansen dataset
            dataset = ee.Image("UMD/hansen/global_forest_change_2023_v1_10")
            
            # Select appropriate band
            if layer_type == "loss":
                image = dataset.select(['loss'])
                viz_params = {'min': 0, 'max': 1, 'palette': ['green', 'red']}
                attribution = "Hansen Loss"
            elif layer_type == "gain":
                image = dataset.select(['gain'])
                viz_params = {'min': 0, 'max': 1, 'palette': ['red', 'green']}
                attribution = "Hansen Gain"
            else:  # cover
                image = dataset.select(['treecover2000'])
                viz_params = {'min': 0, 'max': 100, 'palette': ['white', 'green']}
                attribution = "Hansen Tree Cover 2000"
            
            # Get map ID
            map_id = image.getMapId(viz_params)
            tile_url = map_id['tile_fetcher'].url_format
            
            self._tile_cache[cache_key] = (tile_url, attribution)
            logger.info(f"Generated Hansen {layer_type} tile URL")
            
            return (tile_url, attribution)
            
        except Exception as e:
            logger.error(f"Failed to get Hansen tile for {layer_type}: {e}")
            return None
    
    @staticmethod
    def _get_mapbiomas_palette() -> str:
        """Get MapBiomas color palette for visualization."""
        # Simplified palette for major classes
        palette = [
            '#FFE4C2',  # 0 - Non-classified
            '#1f8d49',  # 3 - Forest Formation
            '#B3CC33',  # 4 - Savanna Formation
            '#B7DC58',  # 5 - Grassland
            '#E1C69F',  # 9 - Forest Plantation
            '#E1C69F',  # 10 - Pasture
            '#000000',  # 11 - Urban Area
            '#E2BEFF',  # 12 - Non-vegetated Area
            '#D0D0D0',  # 13 - Water
            '#A5F57F',  # 14 - Perennial Crop
            '#D3AF37',  # 15 - Semi-perennial Crop
            '#FF6B6B',  # 16 - Temporary Crop
            '#8B4513',  # 17 - Fallow
        ]
        return ','.join(palette)
    
    def clear_cache(self):
        """Clear tile URL cache."""
        self._tile_cache.clear()
        logger.info("Tile cache cleared")


# Singleton instance
_tile_manager: Optional[EETileManager] = None

def get_tile_manager() -> EETileManager:
    """Get singleton tile manager instance."""
    global _tile_manager
    if _tile_manager is None:
        _tile_manager = EETileManager()
    return _tile_manager
