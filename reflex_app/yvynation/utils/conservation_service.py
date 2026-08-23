"""
Singleton service for Brazilian conservation units from the local GeoPackage.

All 3,247 CNUC conservation units are loaded once from
``environment_conservation_br202605.gpkg`` (EPSG:4326, MultiPolygon) and
cached in memory.  The public API mirrors :class:`TerritoryService` so the
batch pipeline can use either service interchangeably.

Loading is split in two, same as TerritoryService: attributes load eagerly
and cheaply at construction (everything the batch/interactive list and its
filters touch); geometry loads lazily on first call to a geometry-needing
method, since browsing/filtering thousands of units never needs a polygon.

Display-key rules
-----------------
* Unique ``nome_uc``  → display key is ``nome_uc``
* Duplicate ``nome_uc`` → display key is ``"{nome_uc} ({cd_cnuc})"``
  (34 such pairs in the 2026-05 dataset)

Primary key: ``cd_cnuc`` (string, always unique, e.g. ``"0000.00.0011"``).
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_GPKG_PATH = os.path.join(os.path.dirname(__file__), "environment_conservation_br202605.gpkg")
_LAYER_NAME = "cnuc"

# Full Brazilian state names → 2-letter sigla.
# The CNUC GeoPackage ``uf`` column stores full names (possibly comma-separated
# for multi-state units), not the abbreviations used by the indigenous-lands data.
_UF_NAME_TO_SIGLA: Dict[str, str] = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPÁ": "AP", "AMAZONAS": "AM",
    "BAHIA": "BA", "CEARÁ": "CE", "DISTRITO FEDERAL": "DF",
    "ESPÍRITO SANTO": "ES", "GOIÁS": "GO", "MARANHÃO": "MA",
    "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG",
    "PARÁ": "PA", "PARAÍBA": "PB", "PARANÁ": "PR", "PERNAMBUCO": "PE",
    "PIAUÍ": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDÔNIA": "RO", "RORAIMA": "RR",
    "SANTA CATARINA": "SC", "SÃO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}


def _safe_ha(raw: Any) -> float:
    """Parse the GeoPackage's ``ha_total`` (TEXT, comma-decimal) into a finite float.

    A handful of rows carry a literal NaN, and ``float("nan")`` doesn't
    raise — it silently returns NaN, which then breaks any ``>=``/``<=``
    comparison (area filter, sort) since NaN comparisons are always False.
    """
    try:
        v = float(str(raw or 0).replace(",", "."))
        return v if v == v else 0.0  # NaN != NaN
    except (ValueError, TypeError):
        return 0.0


def _uf_full_to_siglas(uf_str: str) -> str:
    """Convert comma-separated full state names to 2-letter siglas.

    E.g. "MINAS GERAIS, RIO DE JANEIRO, SÃO PAULO" → "MG, RJ, SP".
    Parts that are already 2-letter codes are passed through unchanged.
    """
    if not uf_str:
        return ""
    result = []
    for part in uf_str.split(","):
        name = part.strip().upper()
        if len(name) == 2 and name.isalpha():
            result.append(name)
        else:
            sig = _UF_NAME_TO_SIGLA.get(name)
            if sig:
                result.append(sig)
    return ", ".join(result)


class ConservationUnitService:
    """GeoPackage-backed conservation unit service.

    Instantiate once via :func:`get_conservation_unit_service`.
    """

    def __init__(self):
        self._attrs_df = None                   # attributes-only DataFrame (no geometry), loaded eagerly
        self._gdf = None                         # full GeoDataFrame with geometry, loaded lazily
        self._geometry_loaded = False
        self._key_to_cod: Dict[str, str] = {}   # display_key → cd_cnuc
        self._cod_to_key: Dict[str, str] = {}   # cd_cnuc → display_key
        self._cod_to_attrs: Dict[str, Any] = {} # cd_cnuc → attrs-only row (O(1), no geometry)
        self._cod_to_row: Dict[str, Any] = {}   # cd_cnuc → full row w/ geometry (populated lazily)
        self._display_keys: List[str] = []
        self._geojson_fc_cache: Optional[Dict] = None
        self._load_attributes()

    # ------------------------------------------------------------------
    # Load & index
    # ------------------------------------------------------------------

    def _load_attributes(self):
        """Load conservation-unit attributes (no geometry) and build lookup indices."""
        try:
            import geopandas as gpd

            if not os.path.exists(_GPKG_PATH):
                logger.error(f"Conservation GeoPackage not found: {_GPKG_PATH}")
                return

            self._attrs_df = gpd.read_file(_GPKG_PATH, layer=_LAYER_NAME, ignore_geometry=True)
            logger.info(f"Loaded {len(self._attrs_df)} conservation unit attribute rows (geometry deferred)")
            self._build_indices()
        except Exception as exc:
            logger.error(f"Failed to load conservation GeoPackage attributes: {exc}", exc_info=True)
            self._attrs_df = None

    def _build_indices(self):
        if self._attrs_df is None or self._attrs_df.empty:
            return

        nom_counts = self._attrs_df["nome_uc"].value_counts()
        duplicates = set(nom_counts[nom_counts > 1].index)

        key_to_cod: Dict[str, str] = {}
        cod_to_key: Dict[str, str] = {}
        cod_to_attrs: Dict[str, Any] = {}

        for _, row in self._attrs_df.iterrows():
            cod = str(row["cd_cnuc"])
            nom = str(row["nome_uc"])
            key = f"{nom} ({cod})" if nom in duplicates else nom
            key_to_cod[key] = cod
            cod_to_key[cod] = key
            cod_to_attrs[cod] = row

        self._key_to_cod = key_to_cod
        self._cod_to_key = cod_to_key
        self._cod_to_attrs = cod_to_attrs
        self._display_keys = sorted(key_to_cod.keys())
        logger.info(
            f"Conservation unit index ready: {len(self._display_keys)} display keys, "
            f"{len(duplicates)} duplicate-name pairs resolved with (cd_cnuc) suffix"
        )

    def _ensure_geometry(self) -> bool:
        """Lazily load the full geometry-bearing GeoDataFrame on first need.

        Every geometry-touching method funnels through here — attribute-only
        access (display keys, ``get_territory_info``, filters, batch listing)
        never calls this, so browsing/filtering never parses a polygon.
        """
        if self._geometry_loaded:
            return self._gdf is not None
        try:
            import geopandas as gpd

            gdf = gpd.read_file(_GPKG_PATH, layer=_LAYER_NAME)
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            cod_to_row: Dict[str, Any] = {}
            for _, row in gdf.iterrows():
                cod_to_row[str(row["cd_cnuc"])] = row
            self._gdf = gdf
            self._cod_to_row = cod_to_row
            self._geometry_loaded = True
            logger.info(f"Loaded {len(gdf)} conservation unit geometries (lazy, first use)")
            return True
        except Exception as exc:
            logger.error(f"Failed to load conservation unit geometries: {exc}", exc_info=True)
            self._geometry_loaded = True  # don't retry on every subsequent call after a hard failure
            return False

    # ------------------------------------------------------------------
    # Public API (mirrors TerritoryService)
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        return self._attrs_df is not None and len(self._attrs_df) > 0

    def get_all_display_keys(self) -> List[str]:
        """Sorted list of display names for the territory selector UI."""
        return self._display_keys

    def get_cd_cnuc(self, display_key: str) -> Optional[str]:
        """Return ``cd_cnuc`` for a display key, or None if not found."""
        return self._key_to_cod.get(display_key)

    def _get_row(self, display_key: str):
        """Return the attributes-only row for *display_key* (or None). O(1), no geometry."""
        cod = self._key_to_cod.get(display_key)
        if cod is None:
            return None
        return self._cod_to_attrs.get(cod)

    def _get_geom_row(self, display_key: str):
        """Return the full row (incl. geometry) for *display_key*. Triggers lazy geometry load."""
        if not self._ensure_geometry():
            return None
        cod = self._key_to_cod.get(display_key)
        if cod is None:
            return None
        return self._cod_to_row.get(cod)

    def get_geojson_for_key(self, display_key: str) -> Optional[Dict]:
        """Return the geometry as a plain GeoJSON dict for *display_key*."""
        row = self._get_geom_row(display_key)
        if row is None:
            return None
        try:
            from shapely.geometry import mapping
            return json.loads(json.dumps(mapping(row.geometry)))
        except Exception as exc:
            logger.error(f"Error converting geometry for {display_key}: {exc}")
            return None

    def get_bounds_for_key(self, display_key: str) -> Optional[Dict[str, float]]:
        """Return ``{min_lat, max_lat, min_lon, max_lon, center_lat, center_lon}``."""
        row = self._get_geom_row(display_key)
        if row is None:
            return None
        try:
            minx, miny, maxx, maxy = row.geometry.bounds
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
        """Return a dict of unit metadata for *display_key*. Attributes-only, no geometry load.

        Keys match the TerritoryService contract so shared code can call
        ``info.get("superficie_ha")`` and ``info.get("uf_sigla")`` without
        branching.  ``uf_sigla`` maps to the raw ``uf`` column (full state
        name, possibly multi-state); ``first_state_code`` handles parsing.
        """
        row = self._get_row(display_key)
        if row is None:
            return {}
        superficie_ha = _safe_ha(row.get("ha_total", 0))
        return {
            "cd_cnuc": str(row["cd_cnuc"]),
            "nome_uc": str(row["nome_uc"]),
            "display_key": display_key,
            # uf_sigla: convert full state names to 2-letter siglas so shared
            # code (first_state_code, batch metadata) works identically to the
            # indigenous-lands service.
            "uf_sigla": _uf_full_to_siglas(str(row.get("uf", "") or "")),
            "municipio": str(row.get("municipio", "") or ""),
            "grupo": str(row.get("grupo", "") or ""),
            "categoria": str(row.get("categoria", "") or ""),
            "esfera": str(row.get("esfera", "") or ""),
            "superficie_ha": superficie_ha,
        }

    def get_creation_info(self, display_key: str) -> Optional[Dict[str, Any]]:
        """Return creation metadata for a conservation unit. Attributes-only, no geometry load.

        Falls back to accent-stripped, case-insensitive matching when the exact
        display key is not found (handles names derived from filenames / batch slugs).

        Returned keys:
          ``creation_year`` (int or None), ``esfera``, ``grupo``, ``categoria``,
          ``nome_uc``.
        """
        import unicodedata

        def _norm(s: str) -> str:
            return unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii").lower().strip()

        row = self._get_row(display_key)
        if row is None and self._attrs_df is not None:
            target = _norm(display_key)
            for _, candidate in self._attrs_df.iterrows():
                if _norm(str(candidate.get("nome_uc", ""))) == target:
                    row = candidate
                    break
        if row is None:
            return None

        creation_year: Optional[int] = None
        cria_ano = str(row.get("cria_ano", "") or "")
        if cria_ano:
            try:
                # Format stored as DD-MM-YYYY
                parts = cria_ano.split("-")
                if len(parts) == 3 and len(parts[2]) == 4:
                    creation_year = int(parts[2])
            except Exception:
                pass

        return {
            "creation_year": creation_year,
            "esfera":   str(row.get("esfera",   "") or ""),
            "grupo":    str(row.get("grupo",    "") or ""),
            "categoria": str(row.get("categoria", "") or ""),
            "nome_uc":  str(row.get("nome_uc",  "") or ""),
        }

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

    _SIMPLIFY_TOLERANCE = 0.005

    def get_all_geojson_fc(self) -> Dict:
        """GeoJSON FeatureCollection for all units — simplified for map overview.

        Triggers the lazy geometry load — this is a whole-dataset map
        overview, so it legitimately needs every polygon, unlike the
        list/filter paths.
        """
        if self._geojson_fc_cache is not None:
            return self._geojson_fc_cache

        features = []
        if not self._ensure_geometry() or self._gdf is None:
            self._geojson_fc_cache = {"type": "FeatureCollection", "features": []}
            return self._geojson_fc_cache

        from shapely.geometry import mapping

        tol = self._SIMPLIFY_TOLERANCE
        skipped = 0
        for _, row in self._gdf.iterrows():
            cod = str(row["cd_cnuc"])
            key = self._cod_to_key.get(cod, str(row["nome_uc"]))
            try:
                simplified = row.geometry.simplify(tol, preserve_topology=True)
                if simplified.is_empty:
                    skipped += 1
                    continue
                geom_dict = json.loads(json.dumps(mapping(simplified)))
            except Exception:
                skipped += 1
                continue
            ha = _safe_ha(row.get("ha_total", 0))
            features.append({
                "type": "Feature",
                "geometry": geom_dict,
                "properties": {
                    "display_key": key,
                    "nome_uc": str(row["nome_uc"]),
                    "cd_cnuc": cod,
                    "uf": str(row.get("uf", "") or ""),
                    "grupo": str(row.get("grupo", "") or ""),
                    "categoria": str(row.get("categoria", "") or ""),
                    "superficie": ha,
                },
            })

        self._geojson_fc_cache = {"type": "FeatureCollection", "features": features}
        logger.info(
            f"Built simplified conservation units GeoJSON: "
            f"{len(features)} features, {skipped} skipped (tolerance={tol}°)"
        )
        return self._geojson_fc_cache


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_service: Optional[ConservationUnitService] = None


def get_conservation_unit_service() -> ConservationUnitService:
    """Return the module-level singleton :class:`ConservationUnitService`.

    Attributes load on the first call; subsequent calls return the cached
    instance instantly. Geometry loads lazily, on first actual need.
    """
    global _service
    if _service is None:
        _service = ConservationUnitService()
    return _service
