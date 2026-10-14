"""Build the Canadian protected-areas GeoPackage from CPCAD.

    python -m yvynation.utils.build_ca_protected_areas      (from reflex_app/)

Source: the Canadian Protected and Conserved Areas Database (CPCAD),
Environment and Climate Change Canada, via its public ArcGIS REST service —
Open Government Licence – Canada, which permits redistribution with
attribution (unlike WDPA, whose terms forbid redistributing the data).

What the build does, in order:

1. **Land only** (``BIOME = 'T'``). Every dataset Yvynation analyses —
   MapBiomas, Hansen, AAFC — is a land product; a marine area would return an
   empty chart that looks like a failure.
2. **OCAP exclusion, at build time.** A protected area is dropped *before
   anything is written* when any of its zones is an Indigenous Protected and
   Conserved Area (``IPCA = 1``), is governed by Indigenous peoples
   (``GOV_TYPE = 10``) or is Indigenous-owned (``OWNER_TYPE = 4``). Under the
   First Nations principles of Ownership, Control, Access and Possession,
   publication in a national register is not consent to third-party analysis;
   not holding the data at all is the only posture that needs no further
   argument. Co-governed areas (collaborative/joint governance — many national
   parks) are kept, with their governance shown verbatim, because the
   governing Crown partner published them for exactly this kind of use.
   Revisiting that line is a conversation with the partners, not a flag flip.
3. **One row per protected area.** CPCAD stores management zones as separate
   records sharing a ``PARENT_ID``; they are dissolved into one polygon.
4. **The conservation service's own schema** (``nome_uc``, ``cd_cnuc``,
   ``ha_total``, ``uf``, ``grupo``, ``categoria``, ``esfera``, ``cria_ano`` …)
   so ``ConservationUnitService`` reads it unchanged, plus CPCAD's own columns
   carried verbatim (``name_fr``, ``name_ind``, ``iucn_cat``, …).

Output goes to ``utils/protected_areas_ca/``: one zipped GeoPackage per
province or territory (``BC.gpkg.zip`` …) — the app loads BC on start and
adds a province only when the user goes there — plus ``provinces.geojson.gz``
(StatCan outlines, for click-to-province lookup). ``meta.json`` records the
source, fetch date, licence, the
exclusion rule and how many areas it removed.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List

import requests

logger = logging.getLogger(__name__)

SERVICE = "https://maps-cartes.ec.gc.ca/arcgis/rest/services/CWS_SCF/CPCAD/MapServer/0"
LICENCE = "Open Government Licence – Canada (https://open.canada.ca/en/open-government-licence-canada)"
ATTRIBUTION = ("Contains information licensed under the Open Government Licence – "
               "Canada. Canadian Protected and Conserved Areas Database (CPCAD), "
               "Environment and Climate Change Canada.")

FIELDS = ["OBJECTID", "NAME_E", "NAME_F", "NAME_IND", "PA_OECM_DF", "IPCA",
          "IUCN_CAT", "STATUS", "ESTYEAR", "LOC", "O_AREA_HA", "PARENT_ID",
          "ZONE_ID", "TYPE_E", "MECH_E", "OWNER_TYPE", "OWNER_E", "GOV_TYPE",
          "MGMT_E", "PROVIDER"]

#: OCAP exclusion (see module docstring §2).
EXCLUDE_IPCA = {1}
EXCLUDE_GOV_TYPE = {10}       # Indigenous peoples
EXCLUDE_OWNER_TYPE = {4}      # Indigenous

PROVINCE_ABBR = {
    1: "AB", 2: "BC", 3: "MB", 4: "NB", 5: "NL", 6: "NT", 7: "NS", 8: "NU",
    9: "ON", 10: "PE", 11: "QC", 12: "SK", 13: "YT",
}

#: Server-side generalisation (degrees, ~50 m). Matches what a 30 m land-cover
#: analysis can resolve and keeps the file near the Brazilian GeoPackages' size.
MAX_OFFSET_DEG = 0.0005
PAGE = 1000

OUT_DIR = os.path.join(os.path.dirname(__file__), "protected_areas_ca")

PROVINCES_SERVICE = ("https://geo.statcan.gc.ca/geo_wa/rest/services/2021/"
                     "Cartographic_boundary_files/MapServer/0")
PRUID_ABBR = {"10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC",
              "35": "ON", "46": "MB", "47": "SK", "48": "AB", "59": "BC",
              "60": "YT", "61": "NT", "62": "NU"}


def _get(url: str, params: Dict[str, Any], tries: int = 4) -> Dict[str, Any]:
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180,
                             headers={"User-Agent": "yvynation-build/1.0 (leandromet@gmail.com)"})
            r.raise_for_status()
            return r.json()
        except (requests.RequestException, ValueError) as exc:
            if attempt == tries - 1:
                raise
            logger.warning("retrying after %s", exc)
            time.sleep(3 * (attempt + 1))
    return {}


def _domains() -> Dict[str, Dict[Any, str]]:
    meta = _get(SERVICE, {"f": "pjson"})
    out: Dict[str, Dict[Any, str]] = {}
    for f in meta.get("fields", []):
        dom = f.get("domain") or {}
        if dom.get("codedValues"):
            out[f["name"]] = {c["code"]: c["name"] for c in dom["codedValues"]}
    return out


def _fetch_all() -> List[Dict[str, Any]]:
    total = _get(f"{SERVICE}/query", {"where": "BIOME='T'", "returnCountOnly": "true",
                                      "f": "json"})["count"]
    feats: List[Dict[str, Any]] = []
    offset = 0
    while offset < total:
        page = _get(f"{SERVICE}/query", {
            "where": "BIOME='T'", "outFields": ",".join(FIELDS), "outSR": 4326,
            "maxAllowableOffset": MAX_OFFSET_DEG, "orderByFields": "OBJECTID",
            "resultOffset": offset, "resultRecordCount": PAGE, "f": "geojson",
        })
        got = page.get("features") or []
        if not got:
            break
        feats.extend(got)
        offset += len(got)
        print(f"  fetched {offset}/{total}", file=sys.stderr)
    return feats


def _polygonal(geom):
    """A valid (Multi)Polygon, or ``None``.

    A few CPCAD records come back from the generalised query as geometries
    that GEOS's ``make_valid`` refuses outright ("Overlay input is
    mixed-dimension"); ``buffer(0)`` repairs most of those. Whatever survives
    may be a GeometryCollection with stray lines or points — only the polygon
    parts are an area anyone can analyse.
    """
    from shapely.geometry import MultiPolygon, Polygon
    from shapely.validation import make_valid

    if geom is None or geom.is_empty:
        return None
    for fix in (lambda g: g if g.is_valid else make_valid(g), lambda g: g.buffer(0)):
        try:
            g = fix(geom)
        except Exception:
            continue
        if isinstance(g, (Polygon, MultiPolygon)):
            return g if not g.is_empty else None
        parts = [p for p in getattr(g, "geoms", []) if isinstance(p, (Polygon, MultiPolygon))]
        polys = [q for p in parts for q in (p.geoms if isinstance(p, MultiPolygon) else [p])]
        if polys:
            return MultiPolygon(polys)
    return None


def build(month: str | None = None) -> str:
    import geopandas as gpd
    import pandas as pd

    month = month or _dt.date.today().strftime("%Y%m")
    domains = _domains()
    # The raw download is cached beside nothing that ships: set CPCAD_CACHE to
    # a scratch path to re-run the processing without re-fetching ~20k records.
    cache = os.environ.get("CPCAD_CACHE")
    if cache and os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            feats = json.load(fh)
    else:
        feats = _fetch_all()
        if cache:
            with open(cache, "w", encoding="utf-8") as fh:
                json.dump(feats, fh)
    gdf = gpd.GeoDataFrame.from_features(feats, crs="EPSG:4326")
    n_records = len(gdf)
    gdf["geometry"] = gdf.geometry.apply(_polygonal)
    unusable = int(gdf.geometry.isna().sum())
    gdf = gdf[gdf.geometry.notna()].copy()

    # --- OCAP exclusion, by protected area (any zone flags the whole area) ---
    flag = (gdf["IPCA"].isin(EXCLUDE_IPCA) | gdf["GOV_TYPE"].isin(EXCLUDE_GOV_TYPE)
            | gdf["OWNER_TYPE"].isin(EXCLUDE_OWNER_TYPE))
    excluded_parents = set(gdf.loc[flag, "PARENT_ID"])
    kept = gdf[~gdf["PARENT_ID"].isin(excluded_parents)].copy()

    # --- dissolve zones into one row per protected area ---------------------
    rows = []
    for pid, grp in kept.groupby("PARENT_ID"):
        main = grp[grp["ZONE_ID"] == pid]
        head = (main if len(main) else grp.sort_values("O_AREA_HA", ascending=False)).iloc[0]
        geom = grp.geometry.union_all() if len(grp) > 1 else grp.geometry.iloc[0]
        area = float(grp["O_AREA_HA"].fillna(0).sum())
        dec = lambda f: domains.get(f, {}).get(head.get(f), "") if pd.notna(head.get(f)) else ""
        year = int(head["ESTYEAR"]) if pd.notna(head.get("ESTYEAR")) and head["ESTYEAR"] else None
        name = (head.get("NAME_E") or head.get("NAME_F") or f"Protected area {pid}").strip()
        rows.append({
            # ConservationUnitService's schema ----------------------------------
            "cd_cnuc": str(int(pid)),
            "nome_uc": name,
            "cria_ano": f"01-01-{year}" if year else "",
            "ha_total": f"{area:.1f}",
            "esfera": dec("GOV_TYPE"),
            "uf": PROVINCE_ABBR.get(int(head["LOC"]), "") if pd.notna(head.get("LOC")) else "",
            "municipio": "",
            "org_gestor": str(head.get("MGMT_E") or ""),
            "grupo": dec("PA_OECM_DF"),
            "categoria": str(head.get("TYPE_E") or ""),
            # CPCAD, verbatim -------------------------------------------------
            "name_fr": str(head.get("NAME_F") or ""),
            "name_ind": str(head.get("NAME_IND") or ""),
            "iucn_cat": dec("IUCN_CAT"),
            "status": dec("STATUS"),
            "est_year": year or 0,
            "owner_type": dec("OWNER_TYPE"),
            "owner": str(head.get("OWNER_E") or ""),
            "mechanism": str(head.get("MECH_E") or ""),
            "provider": dec("PROVIDER"),
            "zones": len(grp),
            "geometry": geom,
        })
    out = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")

    # Display keys are fixed NATIONALLY, here, not by whichever provinces a
    # running server happens to have loaded: a name shared by two areas
    # anywhere in Canada gets "(PROV, id)" in every file, so loading Alberta
    # later can never rename a BC area a session is already holding.
    dup = out["nome_uc"].duplicated(keep=False)
    out["display_key"] = out["nome_uc"]
    out.loc[dup, "display_key"] = (out.loc[dup, "nome_uc"] + " (" + out.loc[dup, "uf"]
                                   + ", " + out.loc[dup, "cd_cnuc"] + ")")

    # One zipped GeoPackage per province/territory: the app loads BC on start
    # and only adds another province when the user goes there.
    os.makedirs(OUT_DIR, exist_ok=True)
    import zipfile
    per_province = {}
    for prov, part in out.groupby("uf"):
        if not prov:
            continue
        name = f"{prov}.gpkg"
        tmp = os.path.join(OUT_DIR, name)
        if os.path.exists(tmp):
            os.remove(tmp)
        part.to_file(tmp, layer="cpcad", driver="GPKG")
        with zipfile.ZipFile(tmp + ".zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(tmp, arcname=name)
        os.remove(tmp)
        _write_overview(part, os.path.join(OUT_DIR, f"{prov}.overview.geojson.gz"))
        per_province[prov] = int(len(part))

    provinces_path = _write_provinces()

    meta = {
        "source": "Canadian Protected and Conserved Areas Database (CPCAD), ECCC",
        "service": SERVICE,
        "fetched": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "release_month": month,
        "licence": LICENCE,
        "attribution": ATTRIBUTION,
        "filter": "BIOME = 'T' (terrestrial / freshwater)",
        "generalisation_deg": MAX_OFFSET_DEG,
        "records_fetched": n_records,
        "records_without_usable_polygon": unusable,
        "ocap_rule": ("a protected area is excluded when any of its zones has "
                      "IPCA = Yes, GOV_TYPE = Indigenous peoples or OWNER_TYPE = Indigenous"),
        "ocap_excluded_areas": len(excluded_parents),
        "protected_areas_written": int(len(out)),
        "per_province": per_province,
        "provinces_file": os.path.basename(provinces_path),
        "provinces_source": PROVINCES_SERVICE,
    }
    with open(os.path.join(OUT_DIR, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, ensure_ascii=False)
    print(json.dumps(meta, indent=2, ensure_ascii=False))
    return OUT_DIR


#: The map overview (every area of a province drawn at once) is precomputed
#: here rather than at run time: building BC's on demand took ~20 s and 7 MB.
OVERVIEW_TOLERANCE_DEG = 0.005      # what the Brazilian CNUC overview uses
OVERVIEW_DECIMALS = 4            # ~10 m — invisible at overview zooms


def _write_overview(part, path: str) -> None:
    import gzip
    from shapely.geometry import mapping

    def _round(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            return [round(c[0], OVERVIEW_DECIMALS), round(c[1], OVERVIEW_DECIMALS)]
        return [_round(x) for x in c]

    feats = []
    for _, row in part.iterrows():
        g = row.geometry.simplify(OVERVIEW_TOLERANCE_DEG, preserve_topology=True)
        if g.is_empty:
            continue
        m = mapping(g)
        feats.append({
            "type": "Feature",
            "geometry": {"type": m["type"], "coordinates": _round(m["coordinates"])},
            "properties": {
                "display_key": row["display_key"], "nome_uc": row["nome_uc"],
                "cd_cnuc": row["cd_cnuc"], "uf": row["uf"], "grupo": row["grupo"],
                "categoria": row["categoria"], "superficie": float(row["ha_total"]),
            },
        })
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh,
                  separators=(",", ":"))


def _write_provinces() -> str:
    """Province/territory outlines for "which province is this click in?" —
    Statistics Canada's 2021 cartographic boundary file (Open Government
    Licence – Canada), generalised to lookup grade (~2 km, islands under
    10 km² dropped): a few hundred KB instead of the service's 13 MB."""
    import gzip
    import geopandas as gpd
    from shapely.geometry import MultiPolygon

    data = _get(f"{PROVINCES_SERVICE}/query", {
        "where": "1=1", "outFields": "PRUID,PRENAME", "outSR": 4326,
        "maxAllowableOffset": 0.02, "f": "geojson"})
    gdf = gpd.GeoDataFrame.from_features(data["features"], crs="EPSG:4326")
    feats = []
    for _, row in gdf.iterrows():
        geom = _polygonal(row.geometry.simplify(0.02, preserve_topology=True))
        parts = [p for p in getattr(geom, "geoms", [geom]) if p.area > 0.001]
        geom = MultiPolygon(parts) if parts else geom
        feats.append({"type": "Feature",
                      "properties": {"code": PRUID_ABBR[str(row["PRUID"])],
                                     "name": row["PRENAME"]},
                      "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]})
    path = os.path.join(OUT_DIR, "provinces.geojson.gz")
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": feats}, fh)
    return path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build(sys.argv[1] if len(sys.argv) > 1 else None)
