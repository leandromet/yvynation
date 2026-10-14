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

#: Canadian protected and conserved areas (CPCAD), written in this service's
#: own schema by ``utils/build_ca_protected_areas.py``: one zipped GeoPackage
#: per province/territory, read in place through GDAL's /vsizip/.
_CA_DIR = os.path.join(os.path.dirname(__file__), "protected_areas_ca")
_CA_LAYER = "cpcad"
#: Albers equal-area — preserves area exactly, wherever its parameters centre it.
_EQUAL_AREA = ("+proj=aea +lat_1=50 +lat_2=70 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 "
               "+ellps=GRS80 +units=m +no_defs")
#: The province loaded on start — the suite's focus. Others load on demand.
CA_DEFAULT_PROVINCES = ("BC",)

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

    def __init__(self, gpkg_path: str = _GPKG_PATH, layer: str = _LAYER_NAME,
                 exists_path: Optional[str] = None,
                 overview_min_ha: float = 0.0,
                 simplify_tolerance: float = 0.005):
        #: ``exists_path`` is what to stat when ``gpkg_path`` is a GDAL virtual
        #: path (/vsizip/…) that os.path cannot see.
        self._gpkg_path = gpkg_path
        self._layer = layer
        self._exists_path = exists_path or gpkg_path
        #: The whole-dataset map overlay skips units smaller than this. 0 for
        #: Brazil's 3,247 units; Canada's 17,792 include ~9,000 small private
        #: conservation lots that would bloat the Folium document past what a
        #: browser parses comfortably — they stay searchable and selectable,
        #: only the overview omits them.
        self._overview_min_ha = overview_min_ha
        self._SIMPLIFY_TOLERANCE = simplify_tolerance
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

            if not os.path.exists(self._exists_path):
                logger.error(f"Conservation GeoPackage not found: {self._exists_path}")
                return

            self._attrs_df = gpd.read_file(self._gpkg_path, layer=self._layer, ignore_geometry=True)
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
        # A file may carry its own display keys (the Canadian build fixes them
        # nationally, so loading another province never renames one).
        has_keys = "display_key" in self._attrs_df.columns

        for _, row in self._attrs_df.iterrows():
            cod = str(row["cd_cnuc"])
            nom = str(row["nome_uc"])
            if has_keys and row.get("display_key"):
                key = str(row["display_key"])
            else:
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

            gdf = gpd.read_file(self._gpkg_path, layer=self._layer)
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

    # ------------------------------------------------------------------
    # Parts — one record, many separate polygons
    # ------------------------------------------------------------------
    #
    # A protected area is often a MultiPolygon of unconnected pieces
    # (Muskwa-Kechika Special Wildland Areas: 39; BC's "Old Growth Management
    # Areas (Mapped Legal)": 20,287 spread across the province). Analysing all
    # of them as one area is rarely the question, so the parts are exposed
    # individually. A part's identity is its position in the stored geometry
    # (stable: the file is static); its displayed *rank* is by area, largest 1.

    def _parts(self, display_key: str) -> List[Any]:
        row = self._get_geom_row(display_key)
        if row is None or row.geometry is None:
            return []
        geom = row.geometry
        return list(getattr(geom, "geoms", [geom]))

    def get_parts(self, display_key: str) -> List[Dict[str, Any]]:
        """Every part, largest first: ``{id, rank, ha, bounds}`` where ``id``
        is the part's stable index (string) and ``bounds`` is
        ``[[s, w], [n, e]]``. Area is measured in an Albers equal-area
        projection — the same kind ``canada/_shared/zones.py`` uses for the
        zone figures, so a part's hectares and the zone card agree. (An
        earlier version used EPSG:3978; that is Lambert *conformal*, which
        distorts area — about 5% off at 58°N.)"""
        cache = self.__dict__.setdefault("_parts_cache", {})
        if display_key in cache:
            return cache[display_key]
        parts = self._parts(display_key)
        if not parts:
            return []
        import geopandas as gpd
        ha = gpd.GeoSeries(parts, crs="EPSG:4326").to_crs(_EQUAL_AREA).area / 1e4
        order = sorted(range(len(parts)), key=lambda i: -float(ha.iloc[i]))
        out = []
        for rank, i in enumerate(order, start=1):
            minx, miny, maxx, maxy = parts[i].bounds
            out.append({"id": str(i), "rank": rank, "ha": round(float(ha.iloc[i]), 1),
                        "bounds": [[miny, minx], [maxy, maxx]]})
        cache[display_key] = out
        return out

    def get_parts_geojson(self, display_key: str, ids) -> Optional[Dict]:
        """GeoJSON (Multi)Polygon of the chosen parts only."""
        from shapely.geometry import MultiPolygon, mapping
        parts = self._parts(display_key)
        chosen = [parts[int(i)] for i in ids if str(i).isdigit() and int(i) < len(parts)]
        if not chosen:
            return None
        polys = [q for p in chosen for q in getattr(p, "geoms", [p])]
        geom = polys[0] if len(polys) == 1 else MultiPolygon(polys)
        return json.loads(json.dumps(mapping(geom)))

    def part_at(self, display_key: str, lat: float, lon: float) -> Optional[str]:
        """The id of the part containing (lat, lon), or None."""
        from shapely.geometry import Point
        pt = Point(lon, lat)
        for i, p in enumerate(self._parts(display_key)):
            if p.contains(pt):
                return str(i)
        return None

    def get_ee_geometry(self, display_key: str):
        """Return an ``ee.Geometry`` built from local data — no EE round-trip."""
        geojson = self.get_geojson_for_key(display_key)
        if geojson is None:
            return None
        try:
            import ee
            from .geometry_handler import sanitize_geometry
            clean = sanitize_geometry(geojson, display_key)
            if clean is None:
                return None
            return ee.Geometry(clean)
        except Exception as exc:
            logger.error(f"Error creating EE geometry for {display_key}: {exc}")
            return None

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
            if self._overview_min_ha and _safe_ha(row.get("ha_total", 0)) < self._overview_min_ha:
                continue
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


class ProvincialProtectedAreaService(ConservationUnitService):
    """Canada's protected and conserved areas, one province file at a time.

    The same service as Brazil's CNUC (same schema, same API), over a set of
    per-province GeoPackages of which only the loaded ones are read. Loading
    is **process-wide** — this is a module singleton shared by every session —
    so *which provinces a session shows* is passed in by the caller
    (``provinces=``) rather than held here; otherwise one user clicking into
    Alberta would put Alberta on everyone's map.

    Indigenous-governed and Indigenous-owned areas are not in these files at
    all (OCAP — see ``build_ca_protected_areas.py``).
    """

    def __init__(self, directory: str = _CA_DIR,
                 default_provinces=CA_DEFAULT_PROVINCES):
        import threading
        self._dir = directory
        self._lock = threading.RLock()
        self._loaded: List[str] = [p for p in default_provinces if self._has(p)]
        self._fc_by_set: Dict[tuple, Dict] = {}
        self._provinces_fc = None
        super().__init__(gpkg_path="", layer=_CA_LAYER, exists_path=directory,
                         simplify_tolerance=0.005)

    # --- files ---------------------------------------------------------------
    def _zip(self, prov: str) -> str:
        return os.path.join(self._dir, f"{prov}.gpkg.zip")

    def _has(self, prov: str) -> bool:
        return os.path.exists(self._zip(prov))

    def available_provinces(self) -> List[str]:
        try:
            return sorted(f.split(".")[0] for f in os.listdir(self._dir)
                          if f.endswith(".gpkg.zip"))
        except OSError:
            return []

    def loaded_provinces(self) -> List[str]:
        return list(self._loaded)

    def _read(self, ignore_geometry: bool):
        import geopandas as gpd
        import pandas as pd
        frames = [gpd.read_file(f"/vsizip/{self._zip(p)}/{p}.gpkg", layer=_CA_LAYER,
                                ignore_geometry=ignore_geometry)
                  for p in self._loaded]
        if not frames:
            return None
        df = pd.concat(frames, ignore_index=True)
        return df if ignore_geometry else gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    def _load_attributes(self):
        try:
            self._attrs_df = self._read(ignore_geometry=True)
            if self._attrs_df is not None:
                logger.info(f"CPCAD attributes loaded for {self._loaded}: {len(self._attrs_df)} areas")
                self._build_indices()
        except Exception as exc:
            logger.error(f"Failed to load CPCAD attributes: {exc}", exc_info=True)
            self._attrs_df = None

    def _ensure_geometry(self) -> bool:
        with self._lock:
            if self._geometry_loaded:
                return self._gdf is not None
            try:
                gdf = self._read(ignore_geometry=False)
                self._gdf = gdf
                self._cod_to_row = ({str(r["cd_cnuc"]): r for _, r in gdf.iterrows()}
                                    if gdf is not None else {})
            except Exception as exc:
                logger.error(f"Failed to load CPCAD geometries: {exc}", exc_info=True)
                self._gdf = None
            self._geometry_loaded = True
            return self._gdf is not None

    def ensure_provinces(self, provinces) -> List[str]:
        """Make sure every province in ``provinces`` is loaded; returns the
        ones that were newly loaded (empty when nothing changed)."""
        with self._lock:
            new = [p for p in provinces if p not in self._loaded and self._has(p)]
            if not new:
                return []
            self._loaded.extend(new)
            self._load_attributes()
            # Geometry and overview caches are rebuilt on next need.
            self._geometry_loaded = False
            self._gdf = None
            self._cod_to_row = {}
            self._fc_by_set = {}
            self._geojson_fc_cache = None
            return new

    # --- per-session views -----------------------------------------------------
    def get_all_display_keys(self, provinces=None) -> List[str]:
        if provinces is None or self._attrs_df is None:
            return self._display_keys
        wanted = set(provinces)
        return sorted(self._cod_to_key[str(r["cd_cnuc"])]
                      for _, r in self._attrs_df.iterrows() if r.get("uf") in wanted)

    def get_all_geojson_fc(self, provinces=None) -> Dict:
        """The map overview for ``provinces`` — read from the per-province
        overview files the build precomputes (simplified, ~10 m coordinates),
        so it costs a gzip read, not a pass over every polygon."""
        import gzip
        key = tuple(sorted(provinces or self._loaded))
        with self._lock:
            if key in self._fc_by_set:
                return self._fc_by_set[key]
            feats: List[Dict] = []
            for prov in key:
                path = os.path.join(self._dir, f"{prov}.overview.geojson.gz")
                try:
                    with gzip.open(path, "rt", encoding="utf-8") as fh:
                        feats.extend(json.load(fh)["features"])
                except OSError:
                    logger.warning(f"No CPCAD overview for {prov}")
            fc = {"type": "FeatureCollection", "features": feats}
            self._fc_by_set[key] = fc
            return fc

    def areas_at(self, lat: float, lon: float, provinces=None) -> List[str]:
        """Display keys of every loaded area containing (lat, lon), smallest
        first — protected areas nest (a park inside a wider wildland
        designation), and "what did this click land in" means the most local
        unit. Restricted to ``provinces`` (the session's view) when given."""
        if not self._ensure_geometry() or self._gdf is None:
            return []
        from shapely.geometry import Point
        pt = Point(lon, lat)
        gdf = self._gdf
        idx = list(gdf.sindex.query(pt, predicate="intersects"))
        hits = []
        wanted = set(provinces) if provinces else None
        for i in idx:
            row = gdf.iloc[i]
            if wanted and row.get("uf") not in wanted:
                continue
            if row.geometry is not None and row.geometry.contains(pt):
                hits.append((_safe_ha(row.get("ha_total", 0)),
                             self._cod_to_key.get(str(row["cd_cnuc"]))))
        return [k for _, k in sorted(hits) if k]

    # --- where is a point? -------------------------------------------------------
    def province_at(self, lat: float, lon: float) -> Optional[str]:
        """The province/territory code containing (lat, lon), or None —
        StatCan's outlines (``provinces.geojson.gz``), lookup-grade."""
        if self._provinces_fc is None:
            import gzip
            from shapely.geometry import shape
            from shapely.prepared import prep
            try:
                with gzip.open(os.path.join(self._dir, "provinces.geojson.gz"), "rt",
                               encoding="utf-8") as fh:
                    data = json.load(fh)
                self._provinces_fc = [(f["properties"]["code"], prep(shape(f["geometry"])))
                                      for f in data["features"]]
            except Exception as exc:
                logger.error(f"Province outlines unavailable: {exc}")
                self._provinces_fc = []
        from shapely.geometry import Point
        pt = Point(lon, lat)
        for code, geom in self._provinces_fc:
            if geom.contains(pt):
                return code
        return None


_ca_service: Optional[ProvincialProtectedAreaService] = None


def get_ca_protected_area_service() -> ProvincialProtectedAreaService:
    """Singleton for Canada's protected and conserved areas (CPCAD)."""
    global _ca_service
    if _ca_service is None:
        _ca_service = ProvincialProtectedAreaService()
    return _ca_service


def get_conservation_unit_service() -> ConservationUnitService:
    """Return the module-level singleton :class:`ConservationUnitService`.

    Attributes load on the first call; subsequent calls return the cached
    instance instantly. Geometry loads lazily, on first actual need.
    """
    global _service
    if _service is None:
        _service = ConservationUnitService()
    return _service
