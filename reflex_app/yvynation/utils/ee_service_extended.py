"""
Extended Earth Engine service layer for Yvynation Reflex app.
Handles territory loading, analysis, and data processing.
"""

import ee
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional, Any

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
        """Load MapBiomas classification labels."""
        return {
            0: "Não classificado",
            1: "Floresta",
            3: "Floresta Plantada",
            4: "Savana",
            5: "Savana Plantada",
            6: "Hidrófila",
            7: "Herbácea",
            8: "Semente",
            9: "Cana-de-Açúcar",
            10: "Soja",
            11: "Milho",
            12: "Algodão",
            13: "Outras Lavouras",
            14: "Pastagem",
            15: "Infraestrutura Urbana",
            16: "Outras Áreas não Vegetadas",
            17: "Corpos d'Água",
            18: "Nuvens e Sombras",
            19: "Mineração",
            20: "Aquicultura",
            21: "Mangue",
            22: "Praia e Duna",
            23: "Afloramento rochoso",
            24: "Gleba não classificada",
            25: "Restinga",
            26: "Parque eólico",
            27: "Citrus",
            28: "Arrozal",
            29: "Coqueiro",
            30: "Datura",
            31: "Dendê",
            32: "Framboesa",
            33: "Fumo",
            34: "Guaraná",
            35: "Juta",
            36: "Malva",
            37: "Girassol",
        }
    
    @staticmethod
    def _load_hansen_labels() -> Dict[int, str]:
        """Load Hansen label mappings."""
        return {
            1: "Tree Cover",
            2: "Tree Loss",
            3: "Tree Gain",
            4: "Non-forest",
            5: "Non-forest to Forest",
            6: "Degradation",
            7: "Deforestation to Non-forest",
        }
    
    def load_territories(self) -> Tuple[bool, List[str]]:
        """
        Load indigenous territories from Earth Engine using config asset path.

        Returns:
            tuple: (success, territory_names)
        """
        try:
            from ..config.config import TERRITORY_COLLECTIONS

            # Use the exact asset path from config (like Streamlit app does)
            asset_path = TERRITORY_COLLECTIONS.get('indigenous')

            if not asset_path:
                logger.warning("No indigenous territory path in config")
                return False, []

            logger.info(f"Loading territories from: {asset_path}")
            self.territories_fc = ee.FeatureCollection(asset_path)

            # Test if it works and get the count
            count = self.territories_fc.size().getInfo()
            logger.info(f"✓ Loaded {count} indigenous territories")

            # Extract territory names
            self.territory_names = self._get_territory_names()

            if not self.territory_names:
                logger.warning("No territory names extracted, using fallback")
                return False, []

            logger.info(f"✓ Got {len(self.territory_names)} territory names")
            return True, sorted(self.territory_names)

        except Exception as e:
            logger.error(f"Failed to load territories: {e}")
            logger.warning("Using fallback territory data - connect to real EE dataset")
            # Return true with fallback list to avoid complete failure
            self.territory_names = [
                "Trincheira", "Kayapó", "Xingu", "Madeira", "Negro",
                "Solimões", "Tapajós", "Juruena", "Aripuanã", "Jiparaná",
                "Mato Grosso", "Pará", "Roraima", "Amazonas", "Acre",
            ]
            return False, sorted(self.territory_names)
    
    def _get_territory_names(self) -> List[str]:
        """Extract territory names from feature collection."""
        try:
            if not self.territories_fc:
                return []

            # Get first feature to inspect properties
            first = self.territories_fc.first().getInfo()
            props = first.get('properties', {})
            available_props = list(props.keys())

            logger.debug(f"Available properties in territories: {available_props}")

            # Try different property names (from Streamlit app)
            for prop in ['name', 'Nome', 'NAME', 'territorio_nome', 'territory_name', 'TERRITORY_NAME']:
                if prop in props:
                    logger.info(f"Using property '{prop}' for territory names")
                    names = self.territories_fc.aggregate_array(prop).getInfo()
                    if names:
                        return sorted([str(n) for n in names if n])

            # If no standard property found, log the available ones
            logger.warning(f"No standard name property found. Available: {available_props}")
            return []

        except Exception as e:
            logger.error(f"Error getting territory names: {e}")
            return []
    
    def get_territory_geometry(self, territory_name: str) -> Optional[ee.Geometry]:
        """Get geometry for a specific territory."""
        try:
            if not self.territories_fc:
                return None

            # Try different property names to find the territory
            for prop in ['name', 'Nome', 'NAME', 'territorio_nome', 'territory_name', 'TERRITORY_NAME']:
                try:
                    filtered = self.territories_fc.filter(ee.Filter.eq(prop, territory_name))
                    count = filtered.size().getInfo()
                    if count > 0:
                        geom = filtered.first().geometry()
                        logger.info(f"Found territory '{territory_name}' using property '{prop}'")
                        return geom
                except Exception:
                    continue

            logger.warning(f"Territory '{territory_name}' not found in any property")
            return None

        except Exception as e:
            logger.error(f"Error getting territory geometry for {territory_name}: {e}")
            return None
    
    def get_mapbiomas(self) -> ee.Image:
        """Get or load MapBiomas Image."""
        if self.mapbiomas is None:
            # MapBiomas v9 is an Image, not an ImageCollection
            self.mapbiomas = ee.Image('projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1')
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
            # MapBiomas v9 is an Image with bands like 'classification_2023', 'classification_2022', etc
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
                for class_id_str, count in hist[band_key].items():
                    try:
                        class_id = int(class_id_str)
                        class_name = self.mapbiomas_labels.get(class_id, f"Class {class_id}")
                        area_ha = count * 0.09  # 30m pixels = 0.09 ha

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
                for class_id_str, count in hist[band_key].items():
                    class_id = int(class_id_str)
                    class_name = self.hansen_labels.get(class_id, f"Class {class_id}")
                    area_ha = count * 0.9  # 30m pixels
                    
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
