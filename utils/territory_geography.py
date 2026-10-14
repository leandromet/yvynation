#!/usr/bin/env python3
"""Distance to the ocean and latitude for every analysed protected area (RQ2).

For each (group, territory) in a report's ``data/summary_metrics.csv`` this
matches the official polygon (FUNAI Indigenous Lands / MMA-CNUC Conservation
Units, May 2026 snapshots, the same layers ``governance_policy_report.py``
uses for recognition tiers) and computes, in the Brazil Polyconic projection
(EPSG:5880):

  dist_coast_km      distance from the polygon centroid to the nearest Atlantic
                     coastline (Natural Earth 1:10m coastline)
  dist_coast_min_km  distance from the nearest point of the polygon to that
                     coastline (0 when the area touches the coast)
  lat, lon           centroid latitude / longitude (decimal degrees, SIRGAS 2000)
  match_area_ratio   polygon area / pipeline core area, a check on the name match

"Atlantic coastline" = Natural Earth coastline segments between 70°W and the
mainland's easternmost point (34.7°W), 36°S–12°N. That keeps Brazil plus the
neighbouring Atlantic coasts (Uruguay, the Guianas, eastern Venezuela) and
drops the Pacific and the oceanic islands (Fernando de Noronha, Atol das Rocas,
Trindade, São Pedro e São Paulo), which would otherwise pull the distances of
north-eastern areas toward points 350–1,100 km offshore.

Writes ``<report>/data/territory_geography.csv``.

Run (needs geopandas, i.e. the app venv, not .venv_stats):
  /home/leandromb/google_eengine/yvynation/.venv/bin/python utils/territory_geography.py [REPORT_DIR]
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

# dev-tree copy: the GeoPackages live in the app's utils folder, the report
# (and the Natural Earth coastline under data/external/) on the report drive
_REFLEX_UTILS = Path(__file__).resolve().parent.parent / "reflex_app" / "yvynation" / "utils"
ROOT = Path("/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report")
GPKG_IND = _REFLEX_UTILS / "indigenous_lands_br202605.gpkg"
GPKG_UC = _REFLEX_UTILS / "environment_conservation_br202605.gpkg"
COAST = ROOT / "data" / "external" / "ne_10m_coastline" / "ne_10m_coastline.shp"
METRIC = "EPSG:5880"            # SIRGAS 2000 / Brazil Polyconic (metres)
ATLANTIC_BOX = (-70.0, -36.0, -34.7, 12.0)


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _code(name: str):
    m = re.search(r"\((\d+)\)\s*$", str(name))
    return m.group(1) if m else None


def atlantic_coast():
    coast = gpd.read_file(COAST).to_crs("EPSG:4674")
    coast = coast.clip(box(*ATLANTIC_BOX))
    coast = coast[~coast.geometry.is_empty]
    return coast.to_crs(METRIC).geometry.union_all()


def _pick(cands: gpd.GeoDataFrame, area_ha: float, uf: str | None, uf_col: str):
    """Several polygons share a name: prefer the state match, then the closest area."""
    if len(cands) > 1 and uf:
        same = cands[cands[uf_col].astype(str).str.upper().str.contains(uf, na=False)]
        if len(same):
            cands = same
    if len(cands) > 1 and np.isfinite(area_ha):
        cands = cands.assign(_d=(cands.geometry.area / 1e4 - area_ha).abs()).sort_values("_d")
    return cands.iloc[0]


def main(report_dir: Path = ROOT):
    s = pd.read_csv(report_dir / "data" / "summary_metrics.csv")[["group", "territory", "t_area_total_ha"]]
    meta = pd.read_csv(report_dir / "data" / "territory_metadata.csv")[["group", "territory", "uf"]]
    s = s.merge(meta, on=["group", "territory"], how="left")

    gi = gpd.read_file(GPKG_IND).to_crs(METRIC)
    gu = gpd.read_file(GPKG_UC).to_crs(METRIC)
    gi["_n"] = gi["terrai_nom"].map(_norm)
    gi["_c"] = gi["terrai_cod"].astype(str).str.replace(r"\.0$", "", regex=True)
    gu["_n"] = gu["nome_uc"].map(_norm)
    coast = atlantic_coast()

    rows = []
    for _, r in s.iterrows():
        name, area = r["territory"], r["t_area_total_ha"]
        uf = r["uf"] if isinstance(r["uf"], str) else None
        if r["group"].startswith("Indigenous"):
            code = _code(name)
            cands = gi[gi["_c"] == code] if code else gi.iloc[0:0]
            if cands.empty:
                cands = gi[gi["_n"] == _norm(re.sub(r"\(\d+\)\s*$", "", name))]
            uf_col = "uf_sigla"
        else:
            cands = gu[gu["_n"] == _norm(name)]
            uf_col = "uf"
        rec = {"group": r["group"], "territory": name, "uf": uf, "n_candidates": len(cands)}
        if len(cands):
            poly = _pick(cands, area, uf, uf_col)
            geom = poly.geometry
            cen = geom.centroid
            cen_ll = gpd.GeoSeries([cen], crs=METRIC).to_crs("EPSG:4674").iloc[0]
            rec.update(
                dist_coast_km=cen.distance(coast) / 1000,
                dist_coast_min_km=geom.distance(coast) / 1000,
                lat=cen_ll.y, lon=cen_ll.x,
                match_area_ratio=(geom.area / 1e4) / area if area else np.nan,
            )
        rows.append(rec)

    out = pd.DataFrame(rows)
    path = report_dir / "data" / "territory_geography.csv"
    out.to_csv(path, index=False)
    miss = out["dist_coast_km"].isna().sum()
    print(f"wrote {path}: {len(out)} areas, {miss} unmatched")
    if miss:
        print(out.loc[out["dist_coast_km"].isna(), ["group", "territory"]].to_string())
    odd = out[(out["match_area_ratio"] < 0.8) | (out["match_area_ratio"] > 1.25)]
    if len(odd):
        print("area ratio outside [0.8, 1.25] (check the name match):")
        print(odd[["group", "territory", "match_area_ratio", "n_candidates"]].to_string())


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT)
