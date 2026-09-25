"""The laid-out territory report — one builder for single-area and batch runs.

docs/PDF_REPORT.md §3–§6. Pipeline, in the order both callers run it:

1. **Snapshot** — a plain dict of one area's results (``snapshot_from_export``
   for the interactive app, ``merge_regions`` + ``snapshot_from_batch`` for a
   batch area, quadrants summed). No Reflex objects, no Earth Engine objects.
2. **Metadata** — ``lookup_meta`` (FUNAI / CNUC attributes; local GeoPackage).
3. **Maps** — ``fetch_report_maps``: Earth Engine thumbnails through
   ``report_kit.maps.fetch_thumbnail`` on the EE pool. Must run in an executor
   and BEFORE any render lane (docs/BATCH_CONCURRENCY.md §7).
4. **Charts** — ``render_pngs`` rasterises the figure dicts with the existing
   kaleido helper at report size (R3, R9). Runs on the kaleido lane. The HTML
   format skips it and embeds the figure JSON.
5. **Compose** — ``build_territory_report`` → ``report_kit.Report``, then
   ``render_pdf`` / ``render_html`` on the default executor (never on a render
   lane: reportlab would block other areas' charts).

The report never embeds ``create_map_set`` output (Google/Esri tiles, R5), and
its sentences only describe (``report_text``).
"""

from __future__ import annotations

import json
import logging
import numbers
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..report_kit import (Brand, Callout, Citation, ContentsItem, ContentsList,
                          Figure, KeyValues, LegendItem, LocatorMap, MapComposition,
                          MapFigure, Paragraph, ProvenanceTable, Report, ReportMeta,
                          Section, SideBySide, Table, VectorLayer)
from ..report_kit.text import fmt_ha, fmt_pct
from .report_provenance import provenance_rows
from .report_text import (buffer_gfc_reading, buffer_reading, gains_losses_reading,
                          gfc_reading, glad_reading, km_label, landcover_reading, s,
                          transitions_reading)

logger = logging.getLogger(__name__)

APP_NAME = "Yvynation"
APP_URL = os.getenv("YVY_PUBLIC_URL", "https://yvynation.umaterra.com.br")
BRAND = Brand(accent="#2f7d4f", app_line="umaterra · Yvynation")

#: MapBiomas natural forest classes (level-4 IDs of Collection 10.1): forest
#: formation, savanna formation, mangrove, floodable forest, wooded sandbank
#: vegetation. Used only for the territory-vs-buffer forest share.
FOREST_IDS = frozenset({3, 4, 5, 6, 49})

#: Section keys in §3 order. The ContentsList covers the analysis ones.
SECTION_ORDER = ("identification", "about", "maps", "landcover", "gains_losses",
                 "transitions", "gfc", "glad", "multi_window", "timeline", "buffer",
                 "methods", "citation", "appendix")
CONTENT_KEYS = ("maps", "landcover", "gains_losses", "transitions", "gfc", "glad",
                "multi_window", "timeline", "buffer", "appendix")

#: Every chart the report can hold: key → (slot, aspect). Keys prefixed
#: ``buffer:`` are the buffer's version of the same chart.
FIGURE_SPECS: Dict[str, Tuple[str, float]] = {
    "comparison_bar": ("full", 0.6),
    "gains_losses": ("full", 0.62),
    "sankey": ("full", 0.75),
    "gfc_loss": ("full", 0.45),
    "hansen_glad_bar": ("full", 0.56),
    "mw_sankey": ("full", 0.75),
    "timeline": ("full", 0.62),
    "change_pct": ("full", 0.62),
    "transition_matrix": ("full", 0.9),
    "buffer:comparison_bar": ("full", 0.6),
    "buffer:gains_losses": ("full", 0.62),
}
APPENDIX_FIGURES = ("change_pct", "transition_matrix", "buffer:comparison_bar",
                    "buffer:gains_losses")

#: ``_build_territory_figures`` (batch) key → report key.
BATCH_FIGURE_KEYS = {
    "comparison_bar_chart": "comparison_bar", "gains_losses_chart": "gains_losses",
    "change_pct_chart": "change_pct", "sankey_chart": "sankey",
    "transition_matrix_chart": "transition_matrix", "glad_bar": "hansen_glad_bar",
    "gfc_loss": "gfc_loss", "gfc_bar": "gfc_bar",
}

DEFAULT_OPTIONS = {"maps": True, "figures": True, "tables": True, "appendix": False,
                   "fmt": "pdf", "batch": False}


# --------------------------------------------------------------------------- #
# Plain data
# --------------------------------------------------------------------------- #

def plain(obj: Any) -> Any:
    """A deep copy made only of dict/list/str/int/float/bool/None.

    Unwraps Reflex's MutableProxy (isinstance sees through it) and numpy
    scalars, so the snapshot can leave the state lock safely and be pickled,
    JSON-dumped or handed to another thread."""
    if obj is None or isinstance(obj, (str, bool)):
        return obj
    if isinstance(obj, dict):
        if "bdata" in obj and "dtype" in obj:
            return _decode_typed_array(obj)
        return {(k if isinstance(k, (str, int, float)) else str(k)): plain(v)
                for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [plain(v) for v in obj]
    if isinstance(obj, numbers.Integral):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj)
    if hasattr(obj, "tolist"):
        return plain(obj.tolist())
    return obj


def _decode_typed_array(spec: dict) -> list:
    """Plotly ≥ 6 JSON encodes numeric arrays as ``{"dtype", "bdata"
    (base64), "shape"}``. Older plotly.js — the one bundled with kaleido 0.x —
    cannot read that and silently plots the indices instead, so figures are
    handed to every renderer as plain lists."""
    import base64

    import numpy as np
    arr = np.frombuffer(base64.b64decode(spec["bdata"]), dtype=np.dtype(spec["dtype"]))
    shape = spec.get("shape")
    if shape:
        dims = [int(x) for x in str(shape).split(",")] if isinstance(shape, str) else list(shape)
        arr = arr.reshape(dims)
    return arr.tolist()


def fig_to_json(fig: Any) -> Optional[dict]:
    """A Plotly figure (or dict) as a plain JSON-able dict of lists, or None
    when it has no traces — the app's empty-state charts are ``go.Figure()``
    placeholders. Never ``fig.to_json()``: see :func:`_decode_typed_array`."""
    if fig is None:
        return None
    try:
        if hasattr(fig, "to_plotly_json"):
            data = plain(fig.to_plotly_json())
        elif isinstance(fig, dict):
            data = plain(fig)
        else:
            return None
        json.dumps(data)   # must be JSON-able: it may be embedded in HTML
    except Exception as e:  # noqa: BLE001
        logger.warning(f"figure → JSON failed: {e}")
        return None
    return data if data.get("data") else None


# --------------------------------------------------------------------------- #
# Record helpers
# --------------------------------------------------------------------------- #

def _labels() -> Dict[int, str]:
    try:
        from ..config.config import MAPBIOMAS_LABELS
        return MAPBIOMAS_LABELS
    except Exception:  # noqa: BLE001
        return {}


def _colors() -> Dict[int, str]:
    try:
        from ..config.config import MAPBIOMAS_COLOR_MAP
        return MAPBIOMAS_COLOR_MAP
    except Exception:  # noqa: BLE001
        return {}


def _cid(value) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def class_areas(records: Optional[Iterable[dict]]) -> Dict[int, Tuple[str, float]]:
    """``{class_id: (name, area_ha)}`` summed over ``records`` (MapBiomas
    rows with ``Class_ID``, ``Class``/``Class_Name`` and ``Area_ha``)."""
    out: Dict[int, Tuple[str, float]] = {}
    labels = _labels()
    for r in records or []:
        cid = _cid(r.get("Class_ID"))
        if cid is None:
            continue
        area = float(r.get("Area_ha") or 0.0)
        name = r.get("Class_Name") or r.get("Class") or labels.get(cid, f"Class {cid}")
        prev = out.get(cid)
        out[cid] = (prev[0] if prev else str(name), (prev[1] if prev else 0.0) + area)
    return out


def _records_from_comparison(data: Optional[Iterable[dict]], col: str) -> List[dict]:
    """Per-year records from a gains/losses frame (``Area_Year1``/``Area_Year2``)."""
    rows = []
    for r in data or []:
        cid = _cid(r.get("Class_ID"))
        if cid is None or col not in r:
            continue
        rows.append({"Class_ID": cid, "Class": r.get("Class_Name") or r.get("Class"),
                     "Area_ha": float(r.get(col) or 0.0)})
    return rows


def forest_share(records) -> Optional[float]:
    areas = class_areas(records)
    total = sum(a for _, a in areas.values())
    if total <= 0:
        return None
    return sum(a for cid, (_, a) in areas.items() if cid in FOREST_IDS) / total * 100


def transition_pairs(transitions: Optional[dict]) -> List[Tuple[int, int, float]]:
    """(from id, to id, ha) for every changed pair, largest first."""
    pairs = []
    for src, tgts in (transitions or {}).items():
        if not isinstance(tgts, dict):
            continue
        a = _cid(src)
        for tgt, ha in tgts.items():
            b = _cid(tgt)
            if a is None or b is None or a == b:
                continue
            try:
                ha = float(ha)
            except (TypeError, ValueError):
                continue
            if ha > 0:
                pairs.append((a, b, ha))
    pairs.sort(key=lambda p: -p[2])
    return pairs


def gfc_numbers(gfc: Optional[dict]) -> Optional[Dict[str, Any]]:
    """Tree cover 2000, loss, gain and loss per year from a GFC result."""
    if not gfc or gfc.get("error"):
        return None
    cover = [r for r in gfc.get("tree_cover_data") or [] if (r.get("Percent_Cover") or 0) > 0]
    loss = [r for r in gfc.get("tree_loss_data") or [] if (_cid(r.get("Year_Code")) or 0) > 0]
    gain = [r for r in gfc.get("tree_gain_data") or [] if _cid(r.get("Gain_Code")) == 1]
    summ = gfc.get("summary") or {}
    cover_ha = sum(float(r.get("Area_ha") or 0) for r in cover) if cover else float(
        summ.get("tree_cover_2000_ha") or 0)
    loss_ha = sum(float(r.get("Area_ha") or 0) for r in loss) if loss else float(
        summ.get("forest_loss_ha") or 0)
    gain_ha = sum(float(r.get("Area_ha") or 0) for r in gain) if gain else float(
        summ.get("forest_gain_ha") or 0)
    by_year = sorted((2000 + int(_cid(r["Year_Code"])), float(r.get("Area_ha") or 0))
                     for r in loss)
    return {"cover_ha": cover_ha, "loss_ha": loss_ha, "gain_ha": gain_ha,
            "by_year": by_year,
            "loss_pct": (loss_ha / cover_ha * 100) if cover_ha > 0 else None}


def _outer_only(geojson: Optional[dict]) -> Optional[dict]:
    """The outer rings of every polygon in ``geojson`` — for a buffer ring,
    that is territory ∪ buffer."""
    if not geojson:
        return None
    from ..report_kit.maps import iter_rings
    polys = [[rings[0]] for kind, rings in iter_rings(geojson) if kind == "polygon" and rings]
    if not polys:
        return None
    return {"type": "MultiPolygon", "coordinates": polys}


def _geometry_of(obj: Optional[dict]) -> Optional[dict]:
    if not obj:
        return None
    if obj.get("type") == "Feature":
        return obj.get("geometry")
    if obj.get("type") == "FeatureCollection":
        feats = obj.get("features") or []
        return feats[0].get("geometry") if feats else None
    return obj


def _simplify(geojson: Optional[dict], tolerance_deg: float) -> Optional[dict]:
    """Drop vertices finer than a pixel — outlines of 100k-vertex territories
    would otherwise inflate every map and the locator."""
    if not geojson or tolerance_deg <= 0:
        return geojson
    try:
        from shapely.geometry import mapping, shape
        simple = shape(geojson).simplify(tolerance_deg, preserve_topology=True)
        if simple.is_empty:
            return geojson
        return json.loads(json.dumps(mapping(simple)))
    except Exception:  # noqa: BLE001
        return geojson


def parse_buffer_km(name: Optional[str]) -> Optional[float]:
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*km", str(name or ""), re.I)
    return float(m.group(1).replace(",", ".")) if m else None


# --------------------------------------------------------------------------- #
# Snapshots
# --------------------------------------------------------------------------- #

def _empty_snapshot() -> Dict[str, Any]:
    return {
        "name": "", "territory_type": "indigenous", "y1": None, "y2": None,
        "t_y1": None, "t_y2": None, "transitions": None, "glad": None, "gfc": None,
        "buffer_km": None, "b_y1": None, "b_y2": None, "b_transitions": None,
        "b_glad": None, "b_gfc": None, "geometry": None, "buffer_geometry": None,
        "mw": None, "timeline": None, "figures": {}, "n_parts": 1,
        "hansen_year": None, "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def snapshot_from_export(export: Dict[str, Any], *, territory_type: str,
                         geometry: Optional[dict], buffer_geometry: Optional[dict],
                         buffer_km: Optional[float],
                         figure_json: Optional[Dict[str, dict]] = None,
                         computed_at: Optional[str] = None) -> Dict[str, Any]:
    """The report snapshot from ``collect_export_data_from_state`` output
    (already passed through :func:`plain`). ``figure_json`` holds the
    on-screen charts as JSON dicts, under the report's figure keys."""
    snap = _empty_snapshot()
    cmp_ = export.get("comparison_result") or {}
    t_y1 = export.get("territory_result") or _records_from_comparison(
        cmp_.get("data"), "Area_Year1") or None
    t_y2 = export.get("territory_result_year2") or _records_from_comparison(
        cmp_.get("data"), "Area_Year2") or None
    bcmp = export.get("buffer_mapbiomas_comparison_result") or {}
    b_y1 = _records_from_comparison(bcmp.get("data"), "Area_Year1") or None
    b_y2 = _records_from_comparison(bcmp.get("data"), "Area_Year2") or None
    if b_y2 is None and (export.get("buffer_comparison_result") or {}).get("data"):
        b_y2 = export["buffer_comparison_result"]["data"]
    glad = export.get("glad_result")
    glad_year = None
    if glad:
        glad_year = glad.get("year") or (glad.get("summary") or {}).get("year")
    bglad = export.get("buffer_hansen_result")
    has_buffer_data = bool(b_y1 or b_y2 or export.get("buffer_gfc_result"))
    snap.update({
        "name": export.get("territory_name") or "",
        "territory_type": territory_type or "indigenous",
        "y1": cmp_.get("year_start") or export.get("territory_year"),
        "y2": cmp_.get("year_end") or export.get("territory_year2"),
        "t_y1": t_y1, "t_y2": t_y2,
        "transitions": export.get("territory_transitions") or cmp_.get("transitions") or None,
        "glad": {"year": glad_year, "data": glad.get("data") or []} if glad else None,
        "gfc": export.get("gfc_result") or None,
        "buffer_km": buffer_km if has_buffer_data else None,
        "b_y1": b_y1, "b_y2": b_y2,
        "b_transitions": export.get("buffer_territory_transitions") or bcmp.get("transitions"),
        "b_glad": {"year": bglad.get("year"), "data": bglad.get("data") or []} if bglad else None,
        "b_gfc": export.get("buffer_gfc_result") or None,
        "geometry": _geometry_of(geometry) or export.get("territory_geojson_cached"),
        "buffer_geometry": _geometry_of(buffer_geometry) if has_buffer_data else None,
        "mw": export.get("mw_result") or None,
        "timeline": export.get("timeline") or None,
        "figures": dict(figure_json or {}),
        "hansen_year": glad_year,
    })
    if computed_at:
        snap["computed_at"] = computed_at
    return snap


def _sum_records(record_lists: Sequence[Optional[List[dict]]]) -> Optional[List[dict]]:
    """Class records summed by Class_ID across parts; Percentage recomputed."""
    present = [r for r in record_lists if r]
    if not present:
        return None
    totals: Dict[int, Dict[str, Any]] = {}
    for recs in present:
        for r in recs:
            cid = _cid(r.get("Class_ID"))
            if cid is None:
                continue
            row = totals.setdefault(cid, {k: v for k, v in r.items()
                                          if k not in ("Area_ha", "Pixels", "Percentage")})
            row["Class_ID"] = cid
            row["Area_ha"] = row.get("Area_ha", 0.0) + float(r.get("Area_ha") or 0.0)
            if "Pixels" in r:
                row["Pixels"] = row.get("Pixels", 0) + int(r.get("Pixels") or 0)
    grand = sum(r["Area_ha"] for r in totals.values())
    out = sorted(totals.values(), key=lambda r: -r["Area_ha"])
    for r in out:
        r["Percentage"] = (r["Area_ha"] / grand * 100) if grand > 0 else 0.0
    return out


def _sum_transitions(dicts: Sequence[Optional[dict]]) -> Optional[dict]:
    present = [d for d in dicts if d]
    if not present:
        return None
    out: Dict[str, Dict[str, float]] = {}
    for d in present:
        for src, tgts in d.items():
            if not isinstance(tgts, dict):
                continue
            row = out.setdefault(str(src), {})
            for tgt, ha in tgts.items():
                try:
                    row[str(tgt)] = row.get(str(tgt), 0.0) + float(ha)
                except (TypeError, ValueError):
                    continue
    return out


def _sum_hist(rows_lists, key: str) -> List[dict]:
    acc: Dict[Any, Dict[str, Any]] = {}
    for rows in rows_lists:
        for r in rows or []:
            k = r.get(key)
            row = acc.setdefault(k, {kk: vv for kk, vv in r.items()
                                     if kk not in ("Pixels", "Area_ha")})
            row["Pixels"] = row.get("Pixels", 0) + int(r.get("Pixels") or 0)
            row["Area_ha"] = round(row.get("Area_ha", 0.0) + float(r.get("Area_ha") or 0.0), 2)
    return sorted(acc.values(), key=lambda r: (r.get(key) is None, r.get(key)))


def _sum_gfc(gfcs: Sequence[Optional[dict]]) -> Optional[dict]:
    """Quadrant GFC results summed histogram by histogram, then the summary
    rebuilt exactly as ``hansen_analysis.analyze_gfc`` builds it."""
    present = [g for g in gfcs if g and not g.get("error")]
    if not present:
        return None
    if len(present) == 1:
        return present[0]
    cover = _sum_hist([g.get("tree_cover_data") for g in present], "Percent_Cover")
    loss = _sum_hist([g.get("tree_loss_data") for g in present], "Year_Code")
    gain = _sum_hist([g.get("tree_gain_data") for g in present], "Gain_Code")
    merged = {"type": "hansen_gfc", "source": "Hansen GFC", "tree_cover_data": cover,
              "tree_loss_data": loss, "tree_gain_data": gain}
    nums = gfc_numbers(merged) or {}
    cover_ha, loss_ha, gain_ha = nums.get("cover_ha", 0), nums.get("loss_ha", 0), nums.get("gain_ha", 0)
    records = [
        {"Metric": "Tree Cover 2000", "Area_ha": round(cover_ha),
         "Percent": f"{(cover_ha / sum(r['Area_ha'] for r in cover) * 100) if cover else 0:.1f}%",
         "Description": "Baseline canopy cover (>0%)"},
        {"Metric": "Forest Loss", "Area_ha": round(loss_ha),
         "Percent": f"{(loss_ha / cover_ha * 100) if cover_ha else 0:.1f}%",
         "Description": "Forest loss 2001-2023"},
        {"Metric": "Forest Gain", "Area_ha": round(gain_ha),
         "Percent": f"{(gain_ha / cover_ha * 100) if cover_ha else 0:.1f}%",
         "Description": "Forest gain 2000-2012"},
    ]
    merged.update({"data": records, "table": records, "summary": {
        "tree_cover_2000_ha": round(cover_ha), "forest_loss_ha": round(loss_ha),
        "forest_gain_ha": round(gain_ha), "net_change_ha": round(gain_ha - loss_ha)}})
    return merged


def _sum_mw(mws: Sequence[Optional[dict]]) -> Optional[dict]:
    present = [m for m in mws if m and m.get("pairs")]
    if not present:
        return None
    if len(present) == 1:
        return present[0]
    pairs: Dict[Tuple[int, int], List[dict]] = {}
    for m in present:
        for p in m["pairs"]:
            pairs.setdefault((int(p["year_from"]), int(p["year_to"])), []).append(
                p.get("transitions") or {})
    return {"territory": present[0].get("territory"), "years": present[0].get("years"),
            "pairs": [{"year_from": a, "year_to": b, "transitions": _sum_transitions(ts) or {}}
                      for (a, b), ts in sorted(pairs.items())]}


def _single(result: Optional[dict], year) -> Optional[dict]:
    return {"type": "mapbiomas", "year": year, "data": result} if result else None


def merge_regions(regions: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge the batch's per-region dicts (one per quadrant, or a single one)
    into whole-territory results.

    Each region dict carries the batch's own result objects: ``mb1``/``mb2``
    (``{"data": records}``), ``cmp`` (``_raw_y1``, ``_raw_y2``,
    ``transitions``), ``glad`` (``{"year", "data"}``), ``gfc``, the same with a
    ``b`` prefix for the buffer, and ``mw``/``bmw``. Class areas, transitions,
    GFC histograms and GLAD classes are summed; percentages recomputed.
    """
    def recs(r, single, cmp_key, raw):
        if r.get(single) and r[single].get("data"):
            return r[single]["data"]
        c = r.get(cmp_key) or {}
        return c.get(raw)

    y1 = next((r["cmp"].get("year_start") for r in regions if r.get("cmp")), None)
    y2 = next((r["cmp"].get("year_end") for r in regions if r.get("cmp")), None)
    glad_year = next((r["glad"].get("year") for r in regions if r.get("glad")), None)
    t_y1 = _sum_records([recs(r, "mb1", "cmp", "_raw_y1") for r in regions])
    t_y2 = _sum_records([recs(r, "mb2", "cmp", "_raw_y2") for r in regions])
    b_y1 = _sum_records([recs(r, "bmb", "bcmp", "_raw_y1") for r in regions])
    b_y2 = _sum_records([(r.get("bcmp") or {}).get("_raw_y2") for r in regions])
    glad = _sum_records([(r.get("glad") or {}).get("data") for r in regions])
    bglad = _sum_records([(r.get("bglad") or {}).get("data") for r in regions])
    return {
        "y1": y1, "y2": y2, "n_parts": len(regions),
        "t_y1": t_y1, "t_y2": t_y2,
        "transitions": _sum_transitions([(r.get("cmp") or {}).get("transitions") for r in regions]),
        "glad": {"year": glad_year, "data": glad} if glad else None,
        "gfc": _sum_gfc([r.get("gfc") for r in regions]),
        "b_y1": b_y1, "b_y2": b_y2,
        "b_transitions": _sum_transitions([(r.get("bcmp") or {}).get("transitions")
                                           for r in regions]),
        "b_glad": {"year": glad_year, "data": bglad} if bglad else None,
        "b_gfc": _sum_gfc([r.get("bgfc") for r in regions]),
        "mw": _sum_mw([r.get("mw") for r in regions]),
    }


def sum_timeline_series(series_list: Sequence[Optional[dict]]) -> Optional[dict]:
    """``{indicator: {year: ha}}`` summed across parts."""
    present = [x for x in series_list if x]
    if not present:
        return None
    out: Dict[str, Dict[int, float]] = {}
    for ser in present:
        for ind, by_year in ser.items():
            if not isinstance(by_year, dict):
                continue
            row = out.setdefault(ind, {})
            for y, v in by_year.items():
                try:
                    row[int(y)] = row.get(int(y), 0.0) + float(v or 0.0)
                except (TypeError, ValueError):
                    continue
    return out


def snapshot_from_batch(merged: Dict[str, Any], *, name: str, territory_type: str,
                        geometry: dict, buffer_geometry: Optional[dict],
                        buffer_km: Optional[float], hansen_year, y1, y2,
                        timeline: Optional[dict] = None,
                        computed_at: Optional[str] = None) -> Dict[str, Any]:
    snap = _empty_snapshot()
    snap.update({k: merged.get(k) for k in (
        "t_y1", "t_y2", "transitions", "glad", "gfc", "b_y1", "b_y2", "b_transitions",
        "b_glad", "b_gfc", "mw")})
    has_buf = bool(merged.get("b_y1") or merged.get("b_y2") or merged.get("b_gfc"))
    snap.update({
        "name": name, "territory_type": territory_type,
        "y1": merged.get("y1") or y1, "y2": merged.get("y2") or y2,
        "n_parts": int(merged.get("n_parts") or 1),
        "geometry": _geometry_of(geometry),
        "buffer_geometry": _geometry_of(buffer_geometry) if has_buf else None,
        "buffer_km": buffer_km if has_buf else None,
        "hansen_year": hansen_year, "timeline": timeline,
    })
    if computed_at:
        snap["computed_at"] = computed_at
    return snap


# --------------------------------------------------------------------------- #
# Metadata
# --------------------------------------------------------------------------- #

def lookup_meta(name: str, territory_type: str = "indigenous") -> Dict[str, Any]:
    """FUNAI / CNUC attributes of ``name`` (attributes only, no geometry
    load). Tries the requested type first, then the other one."""
    order = ["conservation", "indigenous"] if territory_type == "conservation" \
        else ["indigenous", "conservation"]
    for kind in order:
        try:
            if kind == "conservation":
                from .conservation_service import get_conservation_unit_service
                svc = get_conservation_unit_service()
                info = svc.get_territory_info(name) or {}
                if info:
                    return {"type": kind, "info": info,
                            "creation": svc.get_creation_info(name) or {}}
            else:
                from .territory_service import get_territory_service
                svc = get_territory_service()
                info = svc.get_territory_info(name) or {}
                if info:
                    return {"type": kind, "info": info,
                            "demarcation": svc.get_demarcation_dates(name) or {}}
        except Exception as e:  # noqa: BLE001
            logger.warning(f"report metadata lookup ({kind}) for {name!r} failed: {e}")
    return {"type": territory_type, "info": {}}


# --------------------------------------------------------------------------- #
# Figures
# --------------------------------------------------------------------------- #

def extra_figures(snap: Dict[str, Any]) -> Dict[str, dict]:
    """Charts the snapshot does not carry but the report shows: the
    multi-window Sankey and the deforestation timeline — built with the same
    functions as the screen and the ZIP export."""
    out: Dict[str, dict] = {}
    mw = snap.get("mw")
    if mw and mw.get("pairs"):
        try:
            from .visualization import create_multi_stage_sankey
            stages = [(p["year_from"], p["year_to"], p.get("transitions") or {})
                      for p in mw["pairs"]]
            fig = fig_to_json(create_multi_stage_sankey(stages))
            if fig:
                out["mw_sankey"] = fig
        except Exception as e:  # noqa: BLE001
            logger.warning(f"report multi-window sankey failed: {e}")
    tl = snap.get("timeline")
    if tl and tl.get("series"):
        try:
            from .visualization import create_deforestation_timeline_chart
            y0, y1 = int(tl.get("year_start") or 0), int(tl.get("year_end") or 0)
            if y0 and y1:
                y0, y1 = min(y0, y1), max(y0, y1)
                series = {k: {int(y): v for y, v in (ser or {}).items()}
                          for k, ser in tl["series"].items() if isinstance(ser, dict)}
                fig = fig_to_json(create_deforestation_timeline_chart(
                    series, state_code=tl.get("state_code"), year_start=y0, year_end=y1,
                    variant="raw", territory_name=snap.get("name") or "",
                    territory_type=tl.get("territory_type") or snap.get("territory_type")))
                if fig:
                    out["timeline"] = fig
        except Exception as e:  # noqa: BLE001
            logger.warning(f"report timeline chart failed: {e}")
    return out


def canonical_batch_figures(figs: Dict[str, Any], prefix: str = "") -> Dict[str, dict]:
    """``_build_territory_figures`` output → report keys, as JSON dicts."""
    out = {}
    for src, dst in BATCH_FIGURE_KEYS.items():
        fj = fig_to_json(figs.get(src))
        if fj:
            out[prefix + dst] = fj
    return out


def figure_plan(snap: Dict[str, Any], options: Dict[str, Any]) -> List[str]:
    """The figure keys this report shows, given what ran and the options."""
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    if not opts["figures"]:
        return []
    has_cmp = bool(snap.get("t_y1") and snap.get("t_y2"))
    keys = []
    if has_cmp:
        keys += ["comparison_bar", "gains_losses"]
    if transition_pairs(snap.get("transitions")):
        keys.append("sankey")
    g = gfc_numbers(snap.get("gfc"))
    if g and g["by_year"]:
        keys.append("gfc_loss")
    if snap.get("glad") and snap["glad"].get("data"):
        keys.append("hansen_glad_bar")
    if snap.get("mw") and snap["mw"].get("pairs"):
        keys.append("mw_sankey")
    if snap.get("timeline") and snap["timeline"].get("series"):
        keys.append("timeline")
    if opts["appendix"] and not opts["batch"]:
        if has_cmp:
            keys.append("change_pct")
        if transition_pairs(snap.get("transitions")):
            keys.append("transition_matrix")
        if snap.get("b_y1") and snap.get("b_y2"):
            keys += ["buffer:comparison_bar", "buffer:gains_losses"]
    return keys


def render_pngs(figures: Dict[str, dict], keys: Sequence[str]) -> Dict[str, bytes]:
    """Rasterise ``figures[key]`` for each key at its report size (R9).

    Blocking kaleido work: call it on ``get_render_executor("kaleido")``.
    A figure that fails is simply missing from the result — the report then
    draws the kit's "figure unavailable" placeholder."""
    import plotly.graph_objects as go

    from ..report_kit.images import figure_opts, prepare_figure
    from .export_service import _plotly_to_png_bytes

    out: Dict[str, bytes] = {}
    for key in keys:
        fj = figures.get(key)
        if not fj:
            continue
        slot, aspect = FIGURE_SPECS.get(key, ("full", 0.56))
        try:
            prepared = prepare_figure(fj, slot, aspect)
            opts = figure_opts(prepared, slot)   # the size prepare_figure decided
            fig = go.Figure(prepared)
            png = _plotly_to_png_bytes(fig, width=opts["width"], height=opts["height"],
                                       scale=opts["scale"])
            if png:
                out[key] = png
        except Exception as e:  # noqa: BLE001
            logger.warning(f"report chart {key} failed: {e}")
    return out


# --------------------------------------------------------------------------- #
# Maps
# --------------------------------------------------------------------------- #

LOSS_BANDS = ((2001, 2008), (2009, 2016), (2017, 2025))


def _loss_color(year: int) -> str:
    """The screen's lossyear palette (yellow → red over codes 0..24)."""
    code = max(0, min(24, year - 2000))
    g = int(round(255 * (1 - code / 24)))
    return f"#ff{g:02x}00"


def _mb_legend(records, lang: str) -> List[LegendItem]:
    colors = _colors()
    areas = class_areas(records)
    items = []
    for cid, (name, ha) in sorted(areas.items(), key=lambda kv: -kv[1][1]):
        if ha > 0:
            items.append(LegendItem(colors.get(cid, "#808080"), str(name)))
    return items


def fetch_report_maps(snap: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """Every map composition the report shows, fetched from Earth Engine.

    Returns ``{"mb_y1", "mb_y2", "gfc", "imagery"}`` (MapComposition or None)
    plus ``"imagery_attr"``, ``"no_imagery"`` and ``"error"``. Blocking
    network work: run it in an executor, and in a batch BEFORE entering a
    render lane. The thumbnails are submitted to the shared EE pool, which is
    the global throttle on in-flight Earth Engine requests.
    """
    from ..report_kit import maps as kmaps
    from .ee_concurrency import get_ee_executor
    from .map_export_service import ee_layer_image

    out: Dict[str, Any] = {"mb_y1": None, "mb_y2": None, "gfc": None, "imagery": None,
                           "imagery_attr": None, "no_imagery": False, "error": ""}
    geom = snap.get("geometry")
    if not geom:
        out["error"] = "no boundary geometry"
        return out
    buf_outer = _outer_only(snap.get("buffer_geometry"))
    frame = [geom] + ([buf_outer] if buf_outer else [])
    view_full = kmaps.MapView.from_geojson(frame, slot="full")
    view_half = kmaps.MapView.from_geojson(frame, slot="half")
    w, s_, e, n = view_full.bbox_lonlat
    tol = (e - w) / max(1, view_full.px_w) / 1.5
    geom_s = _simplify(geom, tol)
    buf_s = _simplify(buf_outer, tol) if buf_outer else None
    clip = buf_s or geom_s
    km = snap.get("buffer_km")

    vectors = [VectorLayer(geojson=geom_s, stroke="#111111", width_pt=1.1)]
    lines = [LegendItem("#111111", s("legend_boundary", lang), "line")]
    if buf_s:
        vectors.append(VectorLayer(geojson=buf_s, stroke="#111111", width_pt=0.8,
                                   dash=(3, 2)))
        lines.append(LegendItem("#555555", s("legend_buffer", lang, km=km_label(km, lang)),
                                "line"))

    y1, y2 = snap.get("y1"), snap.get("y2")
    jobs: Dict[str, Any] = {}
    ex = get_ee_executor()

    def thumb(layer, year, view, key):
        img = ee_layer_image(layer, year)
        if img is None:
            raise RuntimeError(f"no image for {layer} {year}")
        return kmaps.fetch_thumbnail(img, view, "png", cache_key=key)

    def imagery(view, year):
        for yr in (year, year - 1):
            picked = kmaps.imagery_backdrop(view, yr)
            if picked is None:
                return None
            img, attr = picked
            try:
                return kmaps.fetch_thumbnail(img, view, "jpg", cache_key=f"img{yr}"), attr
            except Exception as e:  # noqa: BLE001
                logger.info(f"report imagery {yr} unavailable: {e}")
        return None

    if y1:
        jobs["mb_y1"] = ex.submit(thumb, "mapbiomas", int(y1), view_half, f"mb{y1}")
    if y2 and y2 != y1:
        jobs["mb_y2"] = ex.submit(thumb, "mapbiomas", int(y2), view_half, f"mb{y2}")
    jobs["gfc"] = ex.submit(thumb, "gfc_loss", None, view_full, "gfcloss")
    img_year = int(y2 or y1 or 2024)
    jobs["imagery"] = ex.submit(imagery, view_full, img_year)

    results: Dict[str, Any] = {}
    errors: List[str] = []
    for key, fut in jobs.items():
        try:
            results[key] = fut.result(timeout=180)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{key}: {e}")
            logger.warning(f"report map {key} failed: {e}")

    backdrop = None
    if results.get("imagery"):
        backdrop, out["imagery_attr"] = results["imagery"]
    elif view_full.longest_side_km > kmaps.IMAGERY_MAX_KM:
        out["no_imagery"] = True

    mb_attr = "MapBiomas Collection 10.1 (CC BY-SA 4.0)"
    for key, year, recs in (("mb_y1", y1, snap.get("t_y1")), ("mb_y2", y2, snap.get("t_y2"))):
        png = results.get(key)
        if key == "mb_y2" and y2 == y1:
            png = results.get("mb_y1")
        if png:
            out[key] = MapComposition(view=view_half, overlays=[png], vectors=vectors,
                                      clip_to=clip, legend=_mb_legend(recs, lang) + lines,
                                      attribution=mb_attr)
    if results.get("gfc"):
        legend = [LegendItem(_loss_color((a + b) // 2), s("legend_loss", lang, a=a, b=b))
                  for a, b in LOSS_BANDS] + lines
        attr = "Hansen/UMD/Google/USGS/NASA GFC v1.13 (CC BY 4.0)"
        if out["imagery_attr"]:
            attr += " · " + out["imagery_attr"]
        out["gfc"] = MapComposition(view=view_full, backdrop=backdrop,
                                    overlays=[results["gfc"]], vectors=vectors, clip_to=clip,
                                    legend=legend, attribution=attr)
    if backdrop:
        out["imagery"] = MapComposition(view=view_full, backdrop=backdrop, vectors=vectors,
                                        legend=list(lines), attribution=out["imagery_attr"])
    if errors and not any(out[k] for k in ("mb_y1", "mb_y2", "gfc", "imagery")):
        out["error"] = "; ".join(errors)[:300]
    return out


# --------------------------------------------------------------------------- #
# The report
# --------------------------------------------------------------------------- #

def _ufs(text: str) -> List[str]:
    return sorted(set(re.findall(r"\b[A-Z]{2}\b", str(text or ""))))


def _v(value) -> str:
    text = str(value or "").strip()
    return text if text and text.lower() not in ("nan", "none") else "—"


def _identification(snap, meta, lang) -> Tuple[List[Tuple[str, str]], str]:
    info = meta.get("info") or {}
    kind = meta.get("type") or snap.get("territory_type")
    y1, y2 = snap.get("y1"), snap.get("y2")
    computed = sum(a for _, a in class_areas(snap.get("t_y2") or snap.get("t_y1")).values())
    rows: List[Tuple[str, str]] = []
    if kind == "conservation":
        creation = meta.get("creation") or {}
        rows += [
            (s("id_name", lang), _v(info.get("nome_uc") or snap.get("name"))),
            (s("id_cnuc", lang), _v(info.get("cd_cnuc"))),
            (s("id_group", lang), _v(info.get("grupo") or creation.get("grupo"))),
            (s("id_category", lang), _v(info.get("categoria") or creation.get("categoria"))),
            (s("id_sphere", lang), _v(info.get("esfera") or creation.get("esfera"))),
            (s("id_uf", lang), _v(info.get("uf_sigla"))),
            (s("id_municipality", lang), _v(info.get("municipio"))),
            (s("id_creation_year", lang), _v(creation.get("creation_year"))),
        ]
        caption = s("id_caption_uc", lang)
    else:
        demar = meta.get("demarcation") or {}
        ladder = " › ".join(
            f"{s('stage_' + st, lang)} {demar[st]}"
            for st in ("em_estudo", "delimitada", "declarada", "homologada", "regularizada")
            if demar.get(st))
        rows += [
            (s("id_name", lang), _v(info.get("terrai_nom") or snap.get("name"))),
            (s("id_code", lang), _v(info.get("terrai_cod"))),
            (s("id_ethnicity", lang), _v(info.get("etnia"))),
            (s("id_phase", lang), _v(info.get("fase_ti"))),
            (s("id_modality", lang), _v(info.get("modalidade"))),
            (s("id_uf", lang), _v(info.get("uf_sigla"))),
            (s("id_municipality", lang), _v(info.get("municipio"))),
            (s("id_ladder", lang), ladder or "—"),
        ]
        caption = s("id_caption_ti", lang)
    official = info.get("superficie_ha")
    rows.append((s("id_area_official", lang), fmt_ha(official, 0, lang) if official else "—"))
    if computed > 0:
        rows.append((s("id_area_computed", lang, y=y2 or y1), fmt_ha(computed, 0, lang)))
    from ..config.config import HANSEN_GFC_DATASET, MAPBIOMAS_DEFAULT_COLLECTION
    if y1 and y2:
        rows.append((s("id_years", lang), f"{y1}–{y2}"))
    rows.append((s("id_mapbiomas", lang), MAPBIOMAS_DEFAULT_COLLECTION.replace("v", "").replace("_", ".")))
    rows.append((s("id_gfc", lang), HANSEN_GFC_DATASET.split("/")[-1] if snap.get("gfc")
                 else s("id_not_analysed", lang)))
    glad = snap.get("glad")
    rows.append((s("id_glad", lang), f"GLCLU2020 v2 · {glad.get('year')}" if glad
                 else s("id_not_analysed", lang)))
    km = snap.get("buffer_km")
    rows.append((s("id_buffer", lang), s("id_buffer_width", lang, km=km_label(km, lang))
                 if km else s("id_not_analysed", lang)))
    return rows, caption


def _figure(key: str, caption: str, snap, pngs, options, lang) -> Optional[Figure]:
    slot, aspect = FIGURE_SPECS.get(key, ("full", 0.56))
    if options["fmt"] == "html":
        fj = (snap.get("figures") or {}).get(key)
        if fj:
            return Figure(key=key, caption=caption, slot=slot, aspect=aspect, fig_json=fj)
    else:
        png = (pngs or {}).get(key)
        if png:
            return Figure(key=key, caption=caption, slot=slot, aspect=aspect, png=png)
    return Figure(key=key, caption=caption, slot=slot, aspect=aspect,
                  unavailable_reason=s("fig_render_failed", lang))


def _landcover_rows(snap) -> List[Tuple[int, str, float, float]]:
    a1 = class_areas(snap.get("t_y1"))
    a2 = class_areas(snap.get("t_y2"))
    rows = []
    for cid in set(a1) | set(a2):
        name = (a1.get(cid) or a2.get(cid))[0]
        rows.append((cid, name, a1.get(cid, ("", 0.0))[1], a2.get(cid, ("", 0.0))[1]))
    rows.sort(key=lambda r: -max(r[2], r[3]))
    return rows


def _name(cid: int) -> str:
    return _labels().get(cid, f"Class {cid}")


def build_territory_report(snapshot: Dict[str, Any], meta: Dict[str, Any],
                           pngs: Optional[Dict[str, bytes]], maps: Optional[Dict[str, Any]],
                           lang: str, options: Optional[Dict[str, Any]] = None) -> Report:
    """The whole report as a ``report_kit.Report`` (§3 outline).

    ``snapshot``: from ``snapshot_from_export`` / ``snapshot_from_batch``.
    ``meta``: from ``lookup_meta``. ``pngs``: ``{figure key: PNG}`` for the
    PDF (ignored for HTML, which embeds ``snapshot["figures"]``). ``maps``:
    from ``fetch_report_maps`` (None when maps are off or were not fetched).
    ``options``: maps / figures / tables / appendix (bools), fmt ("pdf" /
    "html"), batch (bool; forces the appendix off).
    """
    opts = {**DEFAULT_OPTIONS, **(options or {})}
    if opts["batch"]:
        opts["appendix"] = False
    lang = lang if lang in ("en", "pt", "es", "fr") else "en"
    snap = snapshot
    maps = maps or {}
    kind = meta.get("type") or snap.get("territory_type") or "indigenous"
    y1, y2 = snap.get("y1"), snap.get("y2")
    km = snap.get("buffer_km")
    name = (meta.get("info") or {}).get("terrai_nom") or (meta.get("info") or {}).get(
        "nome_uc") or snap.get("name") or "—"
    kind_label = s("kind_uc" if kind == "conservation" else "kind_ti", lang)
    from .. import __version__ as app_version
    report = Report(meta=ReportMeta(
        app=APP_NAME, app_url=APP_URL, app_version=app_version,
        title=s("report_title", lang), subject=f"{name} — {kind_label}", lang=lang,
        generated_at=datetime.now(timezone.utc), brand=BRAND))
    sections: Dict[str, Section] = {}

    def fig(key, caption):
        return _figure(key, caption, snap, pngs, opts, lang)

    # 1. Identification ----------------------------------------------------
    kv_rows, kv_caption = _identification(snap, meta, lang)
    info = meta.get("info") or {}
    geom = snap.get("geometry")
    ident_blocks: List[Any] = []
    kv = KeyValues(rows=kv_rows, caption=kv_caption)
    if geom:
        tol = 0.01
        ident_blocks.append(SideBySide(kv, LocatorMap(
            geometry=_simplify(geom, tol), label=s("locator_label", lang),
            highlight_ufs=tuple(_ufs(info.get("uf_sigla"))))))
    else:
        ident_blocks.append(kv)
    sections["identification"] = Section(s("sec_identification", lang), ident_blocks,
                                         "identification")

    # Which analyses exist -------------------------------------------------
    lc_rows = _landcover_rows(snap)
    has_cmp = bool(snap.get("t_y1") and snap.get("t_y2") and lc_rows)
    pairs = transition_pairs(snap.get("transitions"))
    gnum = gfc_numbers(snap.get("gfc"))
    glad = snap.get("glad") if snap.get("glad") and snap["glad"].get("data") else None
    mw = snap.get("mw") if snap.get("mw") and snap["mw"].get("pairs") else None
    tl = snap.get("timeline") if snap.get("timeline") and snap["timeline"].get("series") else None
    b_share1, b_share2 = forest_share(snap.get("b_y1")), forest_share(snap.get("b_y2"))
    b_gnum = gfc_numbers(snap.get("b_gfc"))
    has_buffer = bool(km and ((b_share1 is not None and b_share2 is not None) or b_gnum))
    map_keys = ("mb_y1", "mb_y2", "gfc", "imagery")
    have_maps = any(maps.get(k) for k in map_keys)

    # 3. Maps --------------------------------------------------------------
    maps_status, maps_reason = "included", ""
    if not opts["maps"]:
        maps_status, maps_reason = "excluded", s("reason_excluded", lang)
    elif not have_maps:
        maps_status, maps_reason = "unavailable", s("reason_maps_failed", lang)
        if maps.get("error"):
            sections["maps"] = Section(s("sec_maps", lang), [Callout(
                s("maps_failed", lang, err=maps["error"]), "warning")], "maps")
    else:
        # The intro follows the first map row: a heading plus a paragraph
        # alone at the foot of a page, with the maps overleaf, reads badly.
        blocks: List[Any] = []
        m1, m2 = maps.get("mb_y1"), maps.get("mb_y2")
        f1 = MapFigure(m1, s("map_mb_caption", lang, y=y1), "half") if m1 else None
        f2 = MapFigure(m2, s("map_mb_caption", lang, y=y2), "half") if m2 and y2 != y1 else None
        if f1 and f2:
            blocks.append(SideBySide(f1, f2))
        elif f1 or f2:
            blocks.append(f1 or f2)
        blocks.append(Paragraph(s("maps_intro", lang)))
        if maps.get("gfc"):
            blocks.append(MapFigure(maps["gfc"], s("map_gfc_caption", lang), "full"))
        if maps.get("imagery"):
            blocks.append(MapFigure(maps["imagery"], s("map_img_caption", lang), "full"))
        elif maps.get("no_imagery"):
            blocks.append(Callout(s("maps_no_imagery", lang), "note"))
        sections["maps"] = Section(s("sec_maps", lang), blocks, "maps")

    # 4. Land cover --------------------------------------------------------
    rows3 = [(r[1], r[2], r[3]) for r in lc_rows]
    if has_cmp:
        blocks = [Paragraph(s("lc_intro", lang))]
        if opts["figures"]:
            blocks.append(fig("comparison_bar", s("lc_fig_caption", lang, y1=y1, y2=y2)))
        if opts["tables"]:
            body = [[r[1], r[2], r[3], r[3] - r[2],
                     ((r[3] - r[2]) / r[2] * 100) if r[2] > 0 else None] for r in lc_rows]
            blocks.append(Table(
                columns=[s("col_class", lang), s("col_area_y", lang, y=y1),
                         s("col_area_y", lang, y=y2), s("col_delta_ha", lang),
                         s("col_delta_pct", lang)],
                rows=body, caption=s("lc_table_caption", lang, y1=y1, y2=y2),
                align=["l", "r", "r", "r", "r"], decimals=[None, 0, 0, 0, 1]))
        blocks.append(Paragraph(landcover_reading(rows3, y1, y2, lang)))
        sections["landcover"] = Section(s("sec_landcover", lang, y1=y1, y2=y2), blocks,
                                        "landcover")

        # 5. Gains and losses
        blocks = [Paragraph(s("gl_intro", lang, y1=y1, y2=y2))]
        if opts["figures"]:
            blocks.append(fig("gains_losses", s("gl_fig_caption", lang, y1=y1, y2=y2)))
        reading = gains_losses_reading(rows3, lang)
        if reading:
            blocks.append(Paragraph(reading))
        sections["gains_losses"] = Section(s("sec_gains_losses", lang), blocks, "gains_losses")

    # 6. Transitions -------------------------------------------------------
    if pairs:
        total = sum(p[2] for p in pairs)
        blocks = [Paragraph(s("tr_intro", lang, y1=y1, y2=y2))]
        if opts["figures"]:
            blocks.append(fig("sankey", s("tr_fig_caption", lang, y1=y1, y2=y2)))
        if opts["tables"]:
            blocks.append(Table(
                columns=[s("col_from", lang, y=y1), s("col_to", lang, y=y2),
                         s("col_area_ha", lang), s("col_share_changed", lang)],
                rows=[[_name(a), _name(b), ha, ha / total * 100] for a, b, ha in pairs[:10]],
                caption=s("tr_table_caption", lang, y1=y1, y2=y2),
                align=["l", "l", "r", "r"], decimals=[None, None, 0, 1]))
        blocks.append(Paragraph(transitions_reading(
            [(_name(a), _name(b), ha) for a, b, ha in pairs[:1]], total, lang)))
        sections["transitions"] = Section(s("sec_transitions", lang), blocks, "transitions")

    # 7. Hansen GFC --------------------------------------------------------
    if gnum:
        last = max([y for y, _ in gnum["by_year"]] or [2024])
        blocks = [Paragraph(s("gfc_intro", lang))]
        if opts["figures"] and gnum["by_year"]:
            blocks.append(fig("gfc_loss", s("gfc_fig_caption", lang)))
        if opts["tables"]:
            blocks.append(Table(
                columns=[s("col_metric", lang), s("col_value", lang)],
                rows=[[s("gfc_m_cover", lang), fmt_ha(gnum["cover_ha"], 0, lang)],
                      [s("gfc_m_loss", lang, last=last), fmt_ha(gnum["loss_ha"], 0, lang)],
                      [s("gfc_m_loss_pct", lang), fmt_pct(gnum["loss_pct"], 1, lang)],
                      [s("gfc_m_gain", lang), fmt_ha(gnum["gain_ha"], 0, lang)]],
                caption=s("gfc_table_caption", lang), align=["l", "r"]))
        blocks.append(Paragraph(gfc_reading(gnum["loss_ha"], gnum["cover_ha"],
                                            gnum["by_year"], lang)))
        sections["gfc"] = Section(s("sec_gfc", lang), blocks, "gfc")

    # 8. GLAD --------------------------------------------------------------
    if glad:
        gy = glad.get("year") or snap.get("hansen_year")
        grecs = sorted(glad["data"], key=lambda r: -float(r.get("Area_ha") or 0))
        gtotal = sum(float(r.get("Area_ha") or 0) for r in grecs)
        blocks = [Paragraph(s("glad_intro", lang))]
        if opts["figures"]:
            blocks.append(fig("hansen_glad_bar", s("glad_fig_caption", lang, year=gy)))
        if opts["tables"]:
            blocks.append(Table(
                columns=[s("col_class", lang), s("col_area_ha", lang), s("col_share", lang)],
                rows=[[str(r.get("Class") or r.get("Name") or r.get("Class_ID")),
                       float(r.get("Area_ha") or 0),
                       (float(r.get("Area_ha") or 0) / gtotal * 100) if gtotal else None]
                      for r in grecs[:5]],
                caption=s("glad_table_caption", lang, year=gy), align=["l", "r", "r"],
                decimals=[None, 0, 1]))
        if grecs:
            top = grecs[0]
            blocks.append(Paragraph(glad_reading(
                gy, str(top.get("Class") or top.get("Name") or top.get("Class_ID")),
                float(top.get("Area_ha") or 0), gtotal, lang)))
        sections["glad"] = Section(s("sec_glad", lang), blocks, "glad")

    # 9. Multi-window ------------------------------------------------------
    if mw:
        years = sorted({int(p["year_from"]) for p in mw["pairs"]}
                       | {int(p["year_to"]) for p in mw["pairs"]})
        blocks = [Paragraph(s("mw_intro", lang, years=", ".join(map(str, years))))]
        if opts["figures"]:
            blocks.append(fig("mw_sankey", s("mw_fig_caption", lang, n=len(mw["pairs"]),
                                             first=years[0], last=years[-1])))
        sections["multi_window"] = Section(s("sec_multi_window", lang), blocks, "multi_window")

    # 10. Timeline ---------------------------------------------------------
    if tl:
        t0, t1 = int(tl.get("year_start") or 0), int(tl.get("year_end") or 0)
        t0, t1 = min(t0, t1), max(t0, t1)
        blocks = [Paragraph(s("tl_intro", lang, y0=t0, y1=t1))]
        if opts["figures"]:
            blocks.append(fig("timeline", s("tl_fig_caption", lang, y0=t0, y1=t1)))
        blocks.append(Callout(s("tl_note", lang), "note"))
        sections["timeline"] = Section(s("sec_timeline", lang), blocks, "timeline")

    # 11. Territory vs buffer ---------------------------------------------
    if has_buffer:
        t1s, t2s = forest_share(snap.get("t_y1")), forest_share(snap.get("t_y2"))
        body = []
        if t1s is not None and b_share1 is not None:
            body.append([s("buf_m_forest_y", lang, y=y1), t1s, b_share1, b_share1 - t1s])
        if t2s is not None and b_share2 is not None:
            body.append([s("buf_m_forest_y", lang, y=y2), t2s, b_share2, b_share2 - t2s])
        t_pp = (t2s - t1s) if t1s is not None and t2s is not None else None
        b_pp = (b_share2 - b_share1) if b_share1 is not None and b_share2 is not None else None
        if t_pp is not None and b_pp is not None:
            body.append([s("buf_m_forest_change", lang, y1=y1, y2=y2), t_pp, b_pp, b_pp - t_pp])
        tg = gnum["loss_pct"] if gnum else None
        bg = b_gnum["loss_pct"] if b_gnum else None
        if tg is not None and bg is not None:
            body.append([s("buf_m_gfc", lang), tg, bg, bg - tg])
        blocks = [Paragraph(s("buf_intro", lang, km=km_label(km, lang)))]
        if opts["tables"] and body:
            blocks.append(Table(
                columns=[s("col_metric", lang), s("col_territory", lang), s("col_buffer", lang),
                         s("col_difference", lang)],
                rows=body, caption=s("buf_table_caption", lang), align=["l", "r", "r", "r"],
                decimals=[None, 1, 1, 1], note=s("buf_forest_note", lang)))
        for text in (buffer_reading(t_pp, b_pp, km, lang), buffer_gfc_reading(tg, bg, lang)):
            if text:
                blocks.append(Paragraph(text))
        sections["buffer"] = Section(s("sec_buffer", lang), blocks, "buffer")

    # 12. Methods ----------------------------------------------------------
    ctx = {"y1": y1, "y2": y2, "has_mapbiomas": has_cmp or bool(snap.get("t_y1")),
           "has_transitions": bool(pairs), "has_gfc": bool(gnum), "has_glad": bool(glad),
           "glad_year": (glad or {}).get("year"), "has_mw": bool(mw),
           "mw_years": sorted({int(p["year_from"]) for p in (mw or {}).get("pairs", [])}
                              | {int(p["year_to"]) for p in (mw or {}).get("pairs", [])}),
           "has_timeline": bool(tl), "buffer_km": km if has_buffer else None,
           "n_parts": snap.get("n_parts"), "computed_at": snap.get("computed_at"),
           "imagery": maps.get("imagery_attr") if opts["maps"] and have_maps else None}
    sections["methods"] = Section(s("sec_methods", lang), [
        Paragraph(s("methods_intro", lang)),
        ProvenanceTable(rows=provenance_rows(ctx, lang))], "methods")

    # 13. Citation ---------------------------------------------------------
    from .translations import t as tr
    attributions = [s("attr_mapbiomas", lang)]
    if gnum or (opts["maps"] and maps.get("gfc")):
        attributions.append(s("attr_hansen", lang))
    if glad:
        attributions.append(s("attr_glad", lang))
    if opts["maps"] and maps.get("imagery_attr"):
        attributions.append(maps["imagery_attr"])
    attributions.append(s("attr_uc" if kind == "conservation" else "attr_ti", lang))
    attributions.append(s("attr_ibge", lang))
    sections["citation"] = Section(s("sec_citation", lang), [
        Paragraph(tr("citation_acknowledgment_text", lang)),
        Citation(text=tr("citation_platform_text", lang),
                 sources=[tr("citation_ds_mapbiomas", lang), tr("citation_ds_hansen", lang),
                          tr("citation_ds_gee", lang)],
                 attributions=attributions)], "citation")

    # 14. Appendix ---------------------------------------------------------
    if opts["appendix"]:
        blocks = []
        if has_cmp and opts["tables"]:
            for year, idx in ((y1, 2), (y2, 3)):
                tot = sum(r[idx] for r in lc_rows) or 1.0
                blocks.append(Table(
                    columns=[s("col_class", lang), s("col_area_ha", lang), s("col_share", lang)],
                    rows=[[r[1], r[idx], r[idx] / tot * 100] for r in lc_rows if r[idx] > 0],
                    caption=s("app_classes_caption", lang, y=year), align=["l", "r", "r"],
                    decimals=[None, 0, 2], max_rows=200))
        if opts["figures"] and has_cmp:
            blocks.append(fig("change_pct", s("app_change_pct_caption", lang, y1=y1, y2=y2)))
        if opts["figures"] and pairs:
            blocks.append(fig("transition_matrix", s("app_matrix_caption", lang, y1=y1, y2=y2)))
        if opts["tables"] and pairs:
            total = sum(p[2] for p in pairs)
            blocks.append(Table(
                columns=[s("col_from", lang, y=y1), s("col_to", lang, y=y2),
                         s("col_area_ha", lang), s("col_share_changed", lang)],
                rows=[[_name(a), _name(b), ha, ha / total * 100] for a, b, ha in pairs],
                caption=s("app_transitions_caption", lang, y1=y1, y2=y2),
                align=["l", "l", "r", "r"], decimals=[None, None, 0, 2], max_rows=300))
        if snap.get("b_y1") and snap.get("b_y2"):
            if opts["figures"]:
                blocks.append(fig("buffer:comparison_bar",
                                  s("app_buffer_cmp_caption", lang, y1=y1, y2=y2)))
                blocks.append(fig("buffer:gains_losses",
                                  s("app_buffer_gl_caption", lang, y1=y1, y2=y2)))
            if opts["tables"]:
                b1, b2 = class_areas(snap["b_y1"]), class_areas(snap["b_y2"])
                brows = sorted(((b1.get(c) or b2.get(c))[0], b1.get(c, ("", 0.0))[1],
                                b2.get(c, ("", 0.0))[1]) for c in set(b1) | set(b2))
                brows.sort(key=lambda r: -max(r[1], r[2]))
                blocks.append(Table(
                    columns=[s("col_class", lang), s("col_area_y", lang, y=y1),
                             s("col_area_y", lang, y=y2), s("col_delta_ha", lang)],
                    rows=[[r[0], r[1], r[2], r[2] - r[1]] for r in brows],
                    caption=s("app_buffer_classes_caption", lang, y1=y1, y2=y2),
                    align=["l", "r", "r", "r"], decimals=[None, 0, 0, 0], max_rows=200))
        if blocks:
            sections["appendix"] = Section(s("sec_appendix", lang), blocks, "appendix")

    # 2. About (built last: it lists what the others contain) --------------
    def status(key: str) -> ContentsItem:
        titles = {"maps": s("sec_maps", lang), "landcover": s("sec_landcover", lang, y1=y1, y2=y2),
                  "gains_losses": s("sec_gains_losses", lang),
                  "transitions": s("sec_transitions", lang), "gfc": s("sec_gfc", lang),
                  "glad": s("sec_glad", lang), "multi_window": s("sec_multi_window", lang),
                  "timeline": s("sec_timeline", lang), "buffer": s("sec_buffer", lang),
                  "appendix": s("contents_appendix", lang)}
        title = titles[key]
        if key == "maps":
            return ContentsItem(title, maps_status, maps_reason)
        if key == "appendix":
            if opts["batch"]:
                return ContentsItem(title, "excluded", s("reason_appendix_batch", lang))
            if not opts["appendix"]:
                return ContentsItem(title, "excluded", s("reason_excluded", lang))
            return ContentsItem(title, "included" if "appendix" in sections else "not_run")
        if key in sections:
            return ContentsItem(title, "included")
        reason = s("reason_no_buffer", lang) if key == "buffer" else s("reason_not_run", lang)
        return ContentsItem(title, "not_run", reason)

    period = s("about_period", lang, y1=y1, y2=y2) if y1 and y2 else ""
    buffer = s("about_buffer", lang, km=km_label(km, lang)) if has_buffer else ""
    about: List[Any] = [ContentsList([status(k) for k in CONTENT_KEYS]),
                        Paragraph(s("about_para", lang, name=name, period=period, buffer=buffer))]
    if int(snap.get("n_parts") or 1) > 1:
        about.append(Paragraph(s("about_quadrants", lang, n=snap["n_parts"])))
    sections["about"] = Section(s("sec_about", lang), about, "about")

    report.sections = [sections[k] for k in SECTION_ORDER if k in sections]
    return report


def report_filename(name: str, fmt: str, when: Optional[datetime] = None) -> str:
    """``yvynation_<slug>_<YYYYMMDD-HHMM>.<fmt>`` (§2.9)."""
    from .export_service import _slug
    stamp = (when or datetime.now()).strftime("%Y%m%d-%H%M")
    return f"yvynation_{_slug(name)}_{stamp}.{'html' if fmt == 'html' else 'pdf'}"


def render(report: Report, fmt: str) -> bytes:
    """PDF or HTML bytes (reportlab / string work — the default executor)."""
    from ..report_kit import render_html, render_pdf
    return render_html(report) if fmt == "html" else render_pdf(report)
