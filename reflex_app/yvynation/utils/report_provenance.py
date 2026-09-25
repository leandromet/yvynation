"""Methods rows for the report's ProvenanceTable (docs/PDF_REPORT.md §4).

Yvynation keeps no per-analysis ``Provenance`` records, so the rows are built
here from the configuration constants the analyses read
(``config/config.py``) and from the run context (years, buffer, quadrant
split, which analyses ran). They record what was used; nothing is recomputed.

Each row has the kit's keys: name, dataset_id, bands, scale_m, reducer,
degraded, computed_at, notes.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .report_text import km_label, s

HISTOGRAM = "frequencyHistogram"


def provenance_rows(ctx: Dict[str, Any], lang: str) -> List[Dict[str, Any]]:
    """``ctx`` keys (all optional): y1, y2, has_mapbiomas, has_transitions,
    has_gfc, has_glad, glad_year, has_mw, mw_years, has_timeline,
    timeline_years, buffer_km, n_parts, imagery (attribution string or None),
    computed_at (ISO string)."""
    from ..config.config import (HANSEN_DATASETS, HANSEN_GFC_DATASET,
                                 MAPBIOMAS_COLLECTIONS, MAPBIOMAS_DEFAULT_COLLECTION)

    mb_asset = MAPBIOMAS_COLLECTIONS.get(MAPBIOMAS_DEFAULT_COLLECTION, "")
    computed = str(ctx.get("computed_at") or "")
    y1, y2 = ctx.get("y1"), ctx.get("y2")
    n_parts = int(ctx.get("n_parts") or 1)
    common = [s("prov_note_area", lang)]
    if n_parts > 1:
        common.append(s("prov_note_quadrants", lang, n=n_parts))
    rows: List[Dict[str, Any]] = []

    def add(name, dataset, bands, reducer, notes=(), scale=30):
        # The shared area/quadrant notes are printed once, on the first row.
        notes = [n for n in notes if n not in common or not rows]
        rows.append({"name": name, "dataset_id": dataset, "bands": list(bands),
                     "scale_m": scale, "reducer": reducer, "degraded": False,
                     "computed_at": computed, "notes": list(notes)})

    if ctx.get("has_mapbiomas"):
        years = [y for y in (y1, y2) if y]
        add(s("prov_mapbiomas", lang), mb_asset,
            [f"classification_{y}" for y in dict.fromkeys(years)], HISTOGRAM, common)
    if ctx.get("has_transitions") and y1 and y2:
        add(s("prov_transitions", lang), mb_asset,
            [f"classification_{y1} × 1000 + classification_{y2}"], HISTOGRAM,
            [s("prov_note_transitions", lang)] + common)
    if ctx.get("has_gfc"):
        add(s("prov_gfc", lang), HANSEN_GFC_DATASET,
            ["treecover2000", "lossyear", "gain"], HISTOGRAM, common)
    if ctx.get("has_glad"):
        gy = str(ctx.get("glad_year") or "")
        add(s("prov_glad", lang), HANSEN_DATASETS.get(gy, HANSEN_DATASETS.get("2020", "")),
            ["b1"], HISTOGRAM, common)
    if ctx.get("has_mw"):
        years = list(ctx.get("mw_years") or [])
        bands = [f"classification_{y}" for y in years]
        add(s("prov_mw", lang), mb_asset, bands, HISTOGRAM, common)
    if ctx.get("has_timeline"):
        add(s("prov_timeline", lang), f"{HANSEN_GFC_DATASET}; MapBiomas",
            ["lossyear"], "sum per year", [s("prov_note_timeline", lang)])
    if ctx.get("buffer_km"):
        add(s("prov_buffer", lang), "—", [], "—",
            [s("prov_note_buffer", lang, km=km_label(ctx.get("buffer_km"), lang))], scale=None)
    if ctx.get("imagery"):
        add(s("prov_imagery", lang), str(ctx["imagery"]), [], "getThumbURL",
            [s("prov_note_imagery", lang)], scale=None)
    return rows
