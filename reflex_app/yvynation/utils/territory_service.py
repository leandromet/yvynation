"""
Singleton service for Brazilian indigenous territories from the local GeoPackage.

Replaces EE round-trips for territory list, geometry, and map overlay.
All 657 FUNAI territories are loaded once from ``indigenous_lands_br202605.gpkg``
(EPSG:4326, MultiPolygon, ~20 MB) and cached in memory.

Display-key rules
-----------------
* Unique ``terrai_nom``  → display key is ``terrai_nom``
* Duplicate ``terrai_nom`` → display key is ``"{terrai_nom} ({terrai_cod})"``
  (11 such pairs exist in the 2026-05 dataset)

Primary key: ``terrai_cod`` (integer, always unique, 657 distinct values).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_GPKG_PATH = os.path.join(os.path.dirname(__file__), "indigenous_lands_br202605.gpkg")


class TerritoryService:
    """GeoPackage-backed territory service.  Instantiate once via :func:`get_territory_service`."""

    def __init__(self):
        self._gdf = None                          # geopandas.GeoDataFrame
        self._key_to_cod: Dict[str, int] = {}     # display_key → terrai_cod
        self._cod_to_key: Dict[int, str] = {}     # terrai_cod → display_key
        self._display_keys: List[str] = []        # sorted list of display keys
        self._geojson_fc_cache: Optional[Dict] = None  # full FeatureCollection, built once
        self._load()

    # ------------------------------------------------------------------
    # Load & index
    # ------------------------------------------------------------------

    def _load(self):
        """Load the GeoPackage and build lookup indices."""
        try:
            import geopandas as gpd

            if not os.path.exists(_GPKG_PATH):
                logger.error(f"GeoPackage not found: {_GPKG_PATH}")
                return

            self._gdf = gpd.read_file(_GPKG_PATH)
            # Normalise CRS (should already be EPSG:4326)
            if self._gdf.crs and self._gdf.crs.to_epsg() != 4326:
                self._gdf = self._gdf.to_crs(epsg=4326)
            logger.info(f"Loaded {len(self._gdf)} territories from GeoPackage")
            self._build_indices()
        except Exception as exc:
            logger.error(f"Failed to load GeoPackage: {exc}", exc_info=True)
            self._gdf = None

    def _build_indices(self):
        """Build display-key ↔ terrai_cod mappings."""
        if self._gdf is None or self._gdf.empty:
            return

        # Find names that appear more than once
        nom_counts = self._gdf["terrai_nom"].value_counts()
        duplicates = set(nom_counts[nom_counts > 1].index)

        key_to_cod: Dict[str, int] = {}
        cod_to_key: Dict[int, str] = {}

        for _, row in self._gdf.iterrows():
            cod = int(row["terrai_cod"])
            nom = str(row["terrai_nom"])
            key = f"{nom} ({cod})" if nom in duplicates else nom
            key_to_cod[key] = cod
            cod_to_key[cod] = key

        self._key_to_cod = key_to_cod
        self._cod_to_key = cod_to_key
        self._display_keys = sorted(key_to_cod.keys())
        logger.info(
            f"Territory index ready: {len(self._display_keys)} display keys, "
            f"{len(duplicates)} duplicate-name pairs resolved with (terrai_cod) suffix"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """True if the GeoPackage was loaded successfully."""
        return self._gdf is not None and len(self._gdf) > 0

    def get_all_display_keys(self) -> List[str]:
        """Sorted list of display names for the territory selector UI."""
        return self._display_keys

    def get_terrai_cod(self, display_key: str) -> Optional[int]:
        """Return ``terrai_cod`` for a display key, or None if not found."""
        return self._key_to_cod.get(display_key)

    def get_display_key_for_cod(self, terrai_cod: int) -> Optional[str]:
        """Return the display key for a given ``terrai_cod``."""
        return self._cod_to_key.get(int(terrai_cod))

    def _get_row(self, display_key: str):
        """Return the GeoDataFrame row for *display_key* (or None)."""
        if self._gdf is None:
            return None
        cod = self._key_to_cod.get(display_key)
        if cod is None:
            return None
        rows = self._gdf[self._gdf["terrai_cod"] == cod]
        return rows.iloc[0] if len(rows) > 0 else None

    def _get_row_fuzzy(self, display_key: str):
        """Like _get_row but falls back to accent-stripped, case-insensitive matching."""
        import unicodedata

        row = self._get_row(display_key)
        if row is not None or self._gdf is None:
            return row

        def _norm(s: str) -> str:
            return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii").lower().strip()

        target = _norm(display_key)
        for _, candidate in self._gdf.iterrows():
            if _norm(str(candidate.get("terrai_nom", ""))) == target:
                return candidate
        return None

    def get_geojson_for_key(self, display_key: str) -> Optional[Dict]:
        """Return the geometry as a plain GeoJSON dict for *display_key*."""
        row = self._get_row(display_key)
        if row is None:
            return None
        try:
            # Use shapely's mapping() for reliable GeoJSON conversion
            from shapely.geometry import mapping
            return json.loads(json.dumps(mapping(row.geometry)))
        except Exception as exc:
            logger.error(f"Error converting geometry for {display_key}: {exc}")
            return None

    def get_bounds_for_key(self, display_key: str) -> Optional[Dict[str, float]]:
        """Return ``{min_lat, max_lat, min_lon, max_lon, center_lat, center_lon}``."""
        row = self._get_row(display_key)
        if row is None:
            return None
        try:
            minx, miny, maxx, maxy = row.geometry.bounds  # (minx, miny, maxx, maxy)
            return {
                "min_lat": float(miny),
                "max_lat": float(maxy),
                "min_lon": float(minx),
                "max_lon": float(maxx),
                "center_lat": float((miny + maxy) / 2),
                "center_lon": float((minx + maxx) / 2),
            }
        except Exception as exc:
            logger.error(f"Error computing bounds for {display_key}: {exc}")
            return None

    def get_territory_info(self, display_key: str) -> Dict[str, Any]:
        """Return a dict of territory metadata for *display_key*."""
        row = self._get_row(display_key)
        if row is None:
            return {}
        return {
            "terrai_cod": int(row["terrai_cod"]),
            "terrai_nom": str(row["terrai_nom"]),
            "display_key": display_key,
            "uf_sigla": str(row.get("uf_sigla", "") or ""),
            "municipio": str(row.get("municipio_", "") or ""),
            "etnia": str(row.get("etnia_nome", "") or ""),
            "fase_ti": str(row.get("fase_ti", "") or ""),
            "modalidade": str(row.get("modalidade", "") or ""),
            "superficie_ha": float(row.get("superficie", 0) or 0),
        }

    def get_demarcation_dates(self, display_key: str) -> Dict[str, Optional[int]]:
        """Return demarcation stage years for *display_key*.

        Keys: ``em_estudo``, ``delimitada``, ``declarada``, ``homologada``,
        ``regularizada``.  Values are integer years or ``None`` when the stage
        has not been reached / date is missing.
        """
        import pandas as pd

        row = self._get_row_fuzzy(display_key)
        if row is None:
            return {}
        result: Dict[str, Optional[int]] = {}
        for col, stage in [
            ("data_em_es", "em_estudo"),
            ("data_delim", "delimitada"),
            ("data_decla", "declarada"),
            ("data_homol", "homologada"),
            ("data_regul", "regularizada"),
        ]:
            val = row.get(col)
            try:
                result[stage] = int(pd.Timestamp(val).year) if val is not None and not pd.isnull(val) else None
            except Exception:
                result[stage] = None
        return result

    def get_ethnicity(self, display_key: str) -> str:
        """Return the ``etnia_nome`` value for *display_key*, or empty string.

        Values are kept exactly as stored (comma-separated Portuguese names).
        """
        row = self._get_row_fuzzy(display_key)
        if row is None:
            return ""
        return str(row.get("etnia_nome", "") or "")

    def get_ee_geometry(self, display_key: str):
        """Return an ``ee.Geometry`` built from local data — no EE round-trip."""
        geojson = self.get_geojson_for_key(display_key)
        if geojson is None:
            return None
        try:
            import ee
            return ee.Geometry(geojson)
        except Exception as exc:
            logger.error(f"Error creating EE geometry for {display_key}: {exc}")
            return None

    # Simplification tolerance in degrees for the map overview layer.
    # At zoom ~5 over Brazil (≈5 km/pixel), 0.005° ≈ 500 m — imperceptible.
    # Reduces the FeatureCollection from ~59 MB to < 3 MB, keeping WebSocket
    # deltas small when the map is rebuilt.
    _SIMPLIFY_TOLERANCE = 0.005

    def get_all_geojson_fc(self) -> Dict:
        """GeoJSON FeatureCollection for all territories — simplified for map overview.

        Geometries are simplified with a 0.005° tolerance (≈ 500 m, invisible at
        country-wide zoom) so the payload is < 3 MB instead of ~59 MB.  The cache
        is populated on first call and reused thereafter.

        Features include ``display_key``, ``terrai_nom``, ``terrai_cod``,
        ``fase_ti`` and ``superficie`` for use in map popups.
        """
        if self._geojson_fc_cache is not None:
            return self._geojson_fc_cache

        features = []
        if self._gdf is None:
            self._geojson_fc_cache = {"type": "FeatureCollection", "features": []}
            return self._geojson_fc_cache

        from shapely.geometry import mapping

        tol = self._SIMPLIFY_TOLERANCE
        skipped = 0
        for _, row in self._gdf.iterrows():
            cod = int(row["terrai_cod"])
            key = self._cod_to_key.get(cod, str(row["terrai_nom"]))
            try:
                # Simplify at map-overview resolution; preserve_topology keeps the
                # polygon valid (no ring crossings).
                simplified = row.geometry.simplify(tol, preserve_topology=True)
                if simplified.is_empty:
                    skipped += 1
                    continue
                geom_dict = json.loads(json.dumps(mapping(simplified)))
            except Exception:
                skipped += 1
                continue
            features.append({
                "type": "Feature",
                "geometry": geom_dict,
                "properties": {
                    "display_key": key,
                    "terrai_nom": str(row["terrai_nom"]),
                    "terrai_cod": cod,
                    "uf_sigla": str(row.get("uf_sigla", "") or ""),
                    "fase_ti": str(row.get("fase_ti", "") or ""),
                    "superficie": float(row.get("superficie", 0) or 0),
                },
            })

        self._geojson_fc_cache = {"type": "FeatureCollection", "features": features}
        logger.info(
            f"Built simplified GeoJSON FeatureCollection: "
            f"{len(features)} features, {skipped} skipped (tolerance={tol}°)"
        )
        return self._geojson_fc_cache


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_service: Optional[TerritoryService] = None


def get_territory_service() -> TerritoryService:
    """Return the module-level singleton :class:`TerritoryService`.

    The GeoPackage is loaded on the first call; subsequent calls return the
    cached instance instantly.
    """
    global _service
    if _service is None:
        _service = TerritoryService()
    return _service
