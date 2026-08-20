#!/usr/bin/env python3
"""Recombine a quadrant-split yvynation batch into a flat, aggregator-ready batch.

Territories larger than ``SPLIT_THRESHOLD_HA`` (1 M ha) are exported by the
Reflex batch pipeline as four bounding-box quadrants (``nw/ ne/ sw/ se/``
sub-folders, every filename tagged ``_NW`` … ``_SE``) because Earth Engine times
out on a whole mega-territory plus its buffer ring.  Nothing downstream can read
that layout: ``batch_report_aggregator.load_area`` globs one CSV per family, so a
split area silently loads a single quadrant — which is why the report builders
drop them (``res.territory.comparison is None``).

This tool rebuilds one flat area folder per territory (and per buffer ring) that
is byte-compatible with a normal batch export:

* **tables** — every quadrant CSV/JSON family is summed on its key columns
  (class, metric, year, transition), so ``Area_ha`` totals become
  whole-territory totals.  The quadrants tile the territory's bounding box and
  are cut server-side with ``ee_geom.intersection(quadrant_box)``, so they are
  disjoint and the sums are exact (validated at ~101 % of the geodesic boundary
  area — the excess is 30 m pixel-inclusive counting at the edges).
* **maps** — the four quadrant PNGs share one frame, extent and scale, each
  drawing raster only inside its own quadrant.  They are recombined pixel-wise
  (the odd-one-out of four is the quadrant that carries data) into a single
  full-territory map, with the ``[NW]`` tag cut from the title.
* **figures** — the timeline and Hansen-GFC PNG/HTML figures are re-rendered
  from the merged tables with the app's own chart functions, so the merged area
  carries the same figure set (and the same look) as an unsplit one.

Buffer caveat, reported per area in ``quadrant_merge_report.csv``: the quadrant
boxes tile the **territory** bbox, and the buffer ring is clipped to them, so the
part of the ring lying outside that bbox is absent from the export and cannot be
recovered here (mean ~81 % of the ring is retained across the 27 >1 M ha
Indigenous Lands; frontier lands lose more, and MapBiomas coverage additionally
stops at the national border).  Ring rates stay comparable because they are
area-normalised, but the ring is a partial sample of the real ring.

Usage::

    python quadrant_merge.py SRC_BATCH [--out DEST] [--kind indigenous]
                             [--jobs 4] [--no-figures] [--no-maps] [--no-validate]

Idempotent: re-running overwrites the destination area folders in place.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

QUADS = ("nw", "ne", "sw", "se")
QUAD_TAGS = ("NW", "NE", "SW", "SE")

# Quadrant tag inside a filename: "_NW." or "_NW_" (the pipeline puts the
# quadrant tag before the "_Buffer_10km" tag on territory-scope files and after
# it on the parent-level timeline files, so match either position).
_TAG_RE = re.compile(r"_(NW|NE|SW|SE)(?=[._])")

# ---------------------------------------------------------------------------
# Table merge specs: filename fragment -> (key columns, columns to sum)
# Keys are matched as substrings of the file stem, longest first.  "*" in the
# sum list means "every remaining numeric column".
# ---------------------------------------------------------------------------
MERGE_SPECS: List[Tuple[str, Sequence[str], Sequence[str]]] = [
    ("_mapbiomas_multi_window_", ("year_from", "year_to", "class_from", "class_to"), ("area_ha",)),
    ("_landcover", ("Class_ID", "Class"), ("Pixels", "Area_ha")),
    ("_raw_classes", ("Year", "Class_ID", "Class_Name"), ("Area_ha", "Area_km2")),
    ("_comparison", ("Class",), ("*",)),
    ("_hansen_gfc_summary", ("Metric", "Description"), ("Area_ha",)),
    ("_hansen_gfc_loss_by_year", ("Year_Code", "Year"), ("Pixels", "Area_ha")),
    ("_hansen_gfc_gain", ("Gain_Code", "Status"), ("Pixels", "Area_ha")),
    ("_hansen_gfc_tree_cover_2000", ("Percent_Cover",), ("Pixels", "Area_ha")),
    ("_hansen_glad", ("Class_ID", "Class", "Year"), ("Pixels", "Area_ha", "Area_km2")),
    ("_deforestation_timeline_", ("year",), ("*",)),
]

# Map-name -> title template for the recombined full-territory map. Only used
# when the "[NW]" tag cannot be cut from the original title band.
MAP_TITLE_FALLBACK = "{map_name} | {territory}"


def _slugify(text: str) -> str:
    norm = unicodedata.normalize("NFD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", norm)).strip("_")


def _strip_tag(name: str) -> str:
    """`X_hansen_gfc_summary_NW.csv` -> `X_hansen_gfc_summary.csv`."""
    return _TAG_RE.sub("", name)


def _spec_for(stem: str) -> Optional[Tuple[Sequence[str], Sequence[str]]]:
    for frag, keys, sums in MERGE_SPECS:
        if frag in stem:
            return keys, sums
    return None


# ---------------------------------------------------------------------------
# table merging
# ---------------------------------------------------------------------------


def merge_tables(dfs: Sequence[pd.DataFrame], keys: Sequence[str],
                 sums: Sequence[str]) -> pd.DataFrame:
    """Concatenate quadrant frames and sum the value columns per key tuple."""
    df = pd.concat(dfs, ignore_index=True)
    keys = [k for k in keys if k in df.columns]
    if "*" in sums:
        value_cols = [c for c in df.columns
                      if c not in keys and pd.api.types.is_numeric_dtype(df[c])]
    else:
        value_cols = [c for c in sums if c in df.columns]
    if not keys:  # single-row families without a usable key: sum everything
        return df[value_cols].sum().to_frame().T
    other = [c for c in df.columns if c not in keys and c not in value_cols]
    out = df.groupby(keys, dropna=False, sort=False)[value_cols].sum().reset_index()
    for col in other:  # carry non-numeric extras (e.g. Description) from the 1st
        first = df.groupby(keys, dropna=False, sort=False)[col].first().reset_index()
        out = out.merge(first, on=keys, how="left")
    return out[[c for c in df.columns if c in out.columns]]


def _fix_gfc_percent(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute the GFC summary's Percent column against the merged baseline."""
    if "Metric" not in df.columns or "Percent" not in df.columns:
        return df
    base = df.loc[df["Metric"] == "Tree Cover 2000", "Area_ha"]
    if base.empty or not float(base.iloc[0]):
        return df
    total = float(base.iloc[0])
    df = df.copy()
    df["Percent"] = [f"{100.0 * float(a) / total:.1f}%" for a in df["Area_ha"]]
    return df


def _merge_transitions_json(paths: Sequence[Path]) -> Optional[dict]:
    """Sum the `{"from->to": area_ha}`-style transition dicts of 4 quadrants."""
    merged: Dict[str, float] = {}
    nested = False
    for p in paths:
        try:
            data = json.loads(p.read_text())
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for key, val in data.items():
            if isinstance(val, dict):  # {from: {to: ha}}
                nested = True
                sub = merged.setdefault(key, {})
                for k2, v2 in val.items():
                    try:
                        sub[k2] = float(sub.get(k2, 0.0)) + float(v2)
                    except (TypeError, ValueError):
                        sub[k2] = v2
            else:
                try:
                    merged[key] = float(merged.get(key, 0.0)) + float(val)
                except (TypeError, ValueError):
                    merged[key] = val
    if not merged:
        return None
    return merged if nested else merged


def merge_area_tables(src: Path, dst: Path,
                      counts: Optional[Dict[str, int]] = None) -> Dict[str, Path]:
    """Merge every quadrant table of one area folder into *dst*.

    Returns ``{stem-fragment: written path}`` for the families the figure step
    needs (timeline, gfc summary, gfc loss-by-year). When *counts* is given it is
    filled with the number of quadrant files each of those families was built
    from — a family with fewer than 4 means the source export is incomplete for
    that area (it happens: Parque do Araguaia only exported one quadrant's
    timeline), and a whole-territory total built from it is a partial sum.
    """
    written: Dict[str, Path] = {}
    # (a) tables inside the quadrant sub-folders
    families: Dict[Tuple[str, str], List[Path]] = {}
    for q in QUADS:
        qdir = src / q
        if not qdir.is_dir():
            continue
        for path in sorted(qdir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in (".csv", ".json"):
                continue
            rel_parent = path.parent.relative_to(qdir).as_posix()
            families.setdefault((rel_parent, _strip_tag(path.name)), []).append(path)
    # (b) parent-level tables that are themselves quadrant-tagged (timelines)
    for path in sorted(src.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".csv", ".json"):
            continue
        if path.parts[len(src.parts)] in QUADS:
            continue
        if not _TAG_RE.search(path.name):
            continue
        rel_parent = path.parent.relative_to(src).as_posix()
        families.setdefault((rel_parent, _strip_tag(path.name)), []).append(path)

    for (rel_parent, out_name), paths in sorted(families.items()):
        out_dir = dst / rel_parent if rel_parent != "." else dst
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / out_name
        stem = Path(out_name).stem
        if out_path.suffix.lower() == ".json":
            merged = _merge_transitions_json(paths)
            if merged is not None:
                out_path.write_text(json.dumps(merged), encoding="utf-8")
            continue
        spec = _spec_for(stem)
        if spec is None:
            shutil.copy2(paths[0], out_path)  # unknown family: keep 1st quadrant
            continue
        frames = []
        for p in paths:
            try:
                frames.append(pd.read_csv(p))
            except Exception as exc:  # noqa: BLE001
                print(f"  ! {p.name}: {exc}", file=sys.stderr)
        if not frames:
            continue
        merged = merge_tables(frames, *spec)
        if "_hansen_gfc_summary" in stem:
            merged = _fix_gfc_percent(merged)
        if 0 < len(paths) < len(QUADS):
            # The source export is missing quadrants for this family, so the sum
            # covers only part of the territory. Publishing it under the normal
            # name would let every downstream reader treat a partial sum as a
            # whole-territory total; quarantine it in partial/ instead, where the
            # aggregator's (non-recursive) globs cannot pick it up but the data
            # is still on disk.
            out_path = out_dir / "partial" / out_name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            merged.to_csv(out_path, index=False)
            if counts is not None:
                for tag in ("_deforestation_timeline_", "_hansen_gfc_summary",
                            "_hansen_gfc_loss_by_year", "_landcover"):
                    if tag in stem:
                        counts[tag] = min(counts.get(tag, 99), len(paths))
            continue
        merged.to_csv(out_path, index=False)
        for tag in ("_deforestation_timeline_", "_hansen_gfc_summary",
                    "_hansen_gfc_loss_by_year", "_landcover"):
            if tag in stem:
                written[tag] = out_path
                if counts is not None:
                    counts[tag] = min(counts.get(tag, 99), len(paths))
    return written


# ---------------------------------------------------------------------------
# map recombination
# ---------------------------------------------------------------------------


def _title_band(img) -> int:
    """Row index where the axes frame starts (bottom of the title band)."""
    gray = np.asarray(img.convert("L"))
    dark_rows = np.where((gray < 120).sum(axis=1) > 0.5 * gray.shape[1])[0]
    return int(dark_rows[0]) if len(dark_rows) else int(0.06 * gray.shape[0])


def _retitle(img, fallback_title: Optional[str] = None):
    """Cut the `[NW]` quadrant tag from the title and re-centre what remains.

    Re-uses the original rendered pixels (same font, same weight) rather than
    redrawing text; falls back to drawing *fallback_title* if the tag cannot be
    located.
    """
    from PIL import Image, ImageDraw, ImageFont

    y0 = max(6, _title_band(img) - 3)
    band = img.crop((0, 0, img.width, y0))
    dark = np.asarray(band.convert("L")) < 120
    cols = np.where(dark.any(axis=0))[0]
    out = img.copy()
    d = ImageDraw.Draw(out)
    if len(cols):
        x_left, x_right = int(cols[0]), int(cols[-1])
        # word gaps = runs of blank columns inside the text span
        blank = ~dark[:, x_left:x_right + 1].any(axis=0)
        gaps = []
        start = None
        for i, b in enumerate(blank):
            if b and start is None:
                start = i
            elif not b and start is not None:
                gaps.append((start, i))
                start = None
        min_gap = max(6, int(0.012 * (x_right - x_left)))
        wide = [g for g in gaps if g[1] - g[0] >= min_gap]
        tag_start = None
        if wide:
            last = wide[-1]
            tail_w = (x_right - x_left) - last[1]
            if 0 < tail_w < 0.18 * (x_right - x_left):  # looks like "[NW]"
                tag_start = x_left + last[0]
        if tag_start is not None:
            text = band.crop((x_left, 0, tag_start, y0))
            d.rectangle([0, 0, out.width, y0], fill=(255, 255, 255, 255))
            out.paste(text, (int((out.width - text.width) / 2), 0))
            return out
    if fallback_title:
        d.rectangle([0, 0, out.width, y0], fill=(255, 255, 255, 255))
        import matplotlib
        fp = Path(matplotlib.get_data_path()) / "fonts/ttf/DejaVuSans-Bold.ttf"
        font = ImageFont.truetype(str(fp), max(12, int(y0 * 0.42)))
        bb = d.textbbox((0, 0), fallback_title, font=font)
        d.text(((out.width - (bb[2] - bb[0])) / 2,
                max(2, (y0 - (bb[3] - bb[1])) / 2 - bb[1])),
               fallback_title, font=font, fill=(20, 20, 20, 255))
    return out


def composite_quadrant_map(paths: Sequence[Path], out_path: Path,
                           fallback_title: Optional[str] = None) -> bool:
    """Recombine 4 same-frame quadrant map PNGs into one full-extent map.

    All four renders share the figure frame, extent and scale; each draws raster
    only inside its own quadrant and the flat territory fill everywhere else.
    So for any pixel three images agree (background) and at most one differs
    (its quadrant's data) — the per-pixel odd-one-out is the data pixel.
    """
    from PIL import Image

    ims = [Image.open(p).convert("RGBA") for p in paths]
    if len({im.size for im in ims}) != 1:
        shutil.copy2(paths[0], out_path)  # cannot align — keep one quadrant
        return False
    stack = np.stack([np.asarray(im, dtype=np.int16) for im in ims])
    bg = np.median(stack, axis=0)
    pick = np.abs(stack - bg).sum(axis=-1).argmax(axis=0)
    arr = np.take_along_axis(stack, pick[None, ..., None], axis=0)[0].astype(np.uint8)
    img = _retitle(Image.fromarray(arr, "RGBA"), fallback_title)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return True


def merge_area_maps(src: Path, dst: Path, territory: str) -> int:
    """Recombine every `<slug>_<Q>_<MapName>.png` family in `src/maps`."""
    maps_dir = src / "maps"
    if not maps_dir.is_dir():
        return 0
    families: Dict[str, Dict[str, Path]] = {}
    for path in sorted(maps_dir.glob("*.png")):
        m = re.search(r"_(NW|NE|SW|SE)_", path.name)
        if not m:
            families.setdefault(path.name, {})["-"] = path
            continue
        families.setdefault(_strip_tag(path.name.replace(f"_{m.group(1)}_", "_", 1)),
                            {})[m.group(1)] = path
    n = 0
    for out_name, quad_paths in sorted(families.items()):
        out_path = dst / "maps" / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if set(quad_paths) == {"-"}:
            shutil.copy2(quad_paths["-"], out_path)
            n += 1
            continue
        ordered = [quad_paths[t] for t in QUAD_TAGS if t in quad_paths]
        if len(ordered) < 2:
            shutil.copy2(ordered[0], out_path)
        else:
            map_name = Path(out_name).stem.split("_", 1)[-1].replace("_", " ").strip()
            composite_quadrant_map(
                ordered, out_path,
                MAP_TITLE_FALLBACK.format(map_name=map_name, territory=territory))
        n += 1
    return n


# ---------------------------------------------------------------------------
# figure regeneration (app chart functions, so the look matches an unsplit run)
# ---------------------------------------------------------------------------

_APP_READY = None


def _ensure_app_on_path() -> bool:
    """Put reflex_app on sys.path so the app's chart functions are importable."""
    global _APP_READY
    if _APP_READY is not None:
        return _APP_READY
    app_root = Path(__file__).resolve().parent.parent / "reflex_app"
    if app_root.is_dir() and str(app_root) not in sys.path:
        sys.path.insert(0, str(app_root))
    try:
        import yvynation.utils.visualization  # noqa: F401
        _APP_READY = True
    except Exception as exc:  # noqa: BLE001
        print(f"  ! app chart functions unavailable ({exc}) — skipping figures",
              file=sys.stderr)
        _APP_READY = False
    return _APP_READY


TIMELINE_SERIES = ("mb_defor_primary", "mb_secondary_growth", "mb_fire_scar", "hansen_loss")


def _write_fig(fig, base: Path) -> None:
    from yvynation.utils.export_service import _plotly_to_html_bytes, _plotly_to_png_bytes

    base.parent.mkdir(parents=True, exist_ok=True)
    try:
        html = _plotly_to_html_bytes(fig)
        if html:
            base.with_suffix(".html").write_bytes(html)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! html {base.name}: {exc}", file=sys.stderr)
    try:
        png = _plotly_to_png_bytes(fig, width=1400, height=None, scale=2.0)
        if png:
            base.with_suffix(".png").write_bytes(png)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! png {base.name}: {exc}", file=sys.stderr)


_BUF_TAG_RE = re.compile(r"_(Buffer_[0-9.]+km)$")


def _fig_stem(csv_stem: str, variant: str) -> str:
    """Figure stem for a timeline variant, keeping the pipeline's tag order.

    The batch pipeline writes ``..._1985_2024_raw_Buffer_10km.png`` — variant
    first, buffer tag last — and `batch_report_aggregator` globs buffer figures
    as ``*_{variant}_Buffer_*.png``. Appending the variant to a stem that already
    ends in the buffer tag would produce ``..._Buffer_10km_raw.png``, which that
    glob never matches (the buffer column then renders as "(missing)").
    """
    m = _BUF_TAG_RE.search(csv_stem)
    if m:
        return f"{csv_stem[:m.start()]}_{variant}_{m.group(1)}"
    return f"{csv_stem}_{variant}"


def regen_timeline_figures(csv_path: Path, territory: str, state_code: Optional[str],
                           title_extra: str = "") -> int:
    """Re-render raw / ma5 / derivatives + one chart per series from a CSV."""
    if not _ensure_app_on_path():
        return 0
    from yvynation.utils.visualization import create_deforestation_timeline_chart

    df = pd.read_csv(csv_path)
    if "year" not in df.columns or df.empty:
        return 0
    # A quadrant CSV can carry a blank year row; groupby(dropna=False) keeps it,
    # and a NaN year (or value) blows up the chart's int() conversions.
    df = df[np.isfinite(pd.to_numeric(df["year"], errors="coerce"))].copy()
    df["year"] = df["year"].astype(int)
    if df.empty:
        return 0
    y1, y2 = int(df["year"].min()), int(df["year"].max())
    series = {}
    for c in df.columns:
        if c == "year":
            continue
        vals = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
        series[c] = {int(y): float(v) for y, v in zip(df["year"], vals)}
    fig_dir = csv_path.parent / "figures"
    stem = csv_path.stem
    variants = [("raw", "raw", series), ("moving_avg", "ma5", series),
                ("derivatives", "derivatives", series)]
    variants += [("raw", key, {key: series[key]}) for key in TIMELINE_SERIES
                 if key in series]
    n = 0
    for variant, suffix, data in variants:
        fig = None
        # The app's governor stripe calls int() on the ideology score, so a state
        # with a gap in the political table (Tocantins has no governor before its
        # 1988 creation) raises "cannot convert float NaN to integer". Retry
        # without the state so the chart still renders, minus that stripe.
        for sc in (state_code, None) if state_code else (None,):
            try:
                fig = create_deforestation_timeline_chart(
                    data, state_code=sc, year_start=y1, year_end=y2,
                    variant=variant, moving_window=5,
                    title_suffix=f"{territory}{title_extra}", territory_name=territory,
                    territory_type="indigenous")
                break
            except Exception as exc:  # noqa: BLE001
                print(f"  ! timeline {suffix} (state={sc}): {exc}", file=sys.stderr)
        if fig is not None:
            _write_fig(fig, fig_dir / _fig_stem(stem, suffix))
            n += 1
    return n


def regen_gfc_figures(summary_csv: Optional[Path], loss_csv: Optional[Path]) -> int:
    """Re-render the Hansen-GFC summary bar + annual-loss bar from merged CSVs."""
    if not _ensure_app_on_path():
        return 0
    import plotly.graph_objects as pgo
    from yvynation.utils.visualization import get_chart_for_analysis

    n = 0
    if summary_csv is not None and summary_csv.is_file():
        df = pd.read_csv(summary_csv)
        fig = get_chart_for_analysis(
            {"type": "hansen_gfc", "data": df.to_dict("records")}, chart_type="bar")
        if fig is not None:
            _write_fig(fig, summary_csv.parent / "figures" / summary_csv.stem)
            n += 1
    if loss_csv is not None and loss_csv.is_file():
        df = pd.read_csv(loss_csv).sort_values("Year")
        years = df["Year"].tolist()
        areas = df["Area_ha"].tolist()
        fig = pgo.Figure(data=[pgo.Bar(
            x=years, y=areas, marker_color="#e74c3c",
            text=[f"{a:,.0f} ha" for a in areas], textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>")])
        fig.update_layout(
            title=f"Annual Tree Loss ({int(min(years))}–{int(max(years))})",
            xaxis_title="Year", yaxis_title="Loss Area (ha)",
            template="plotly_white", height=350, showlegend=False)
        _write_fig(fig, loss_csv.parent / "figures" / loss_csv.stem)
        n += 1
    return n


# ---------------------------------------------------------------------------
# per-area driver
# ---------------------------------------------------------------------------


def is_split(area: Path) -> bool:
    return any((area / q).is_dir() for q in QUADS)


def merge_area(src: Path, dst: Path, territory: str, *, state_code=None,
               do_maps=True, do_figures=True, title_extra="") -> dict:
    """Merge one area folder (territory core or buffer ring)."""
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for path in sorted(src.iterdir()):  # untagged parent files (boundary.geojson…)
        if path.is_file() and not _TAG_RE.search(path.name):
            shutil.copy2(path, dst / path.name)
    counts: Dict[str, int] = {}
    written = merge_area_tables(src, dst, counts)
    n_maps = merge_area_maps(src, dst, territory) if do_maps else 0
    n_figs = 0
    if do_figures:
        tl = written.get("_deforestation_timeline_")
        if tl is not None:
            n_figs += regen_timeline_figures(tl, territory, state_code, title_extra)
        n_figs += regen_gfc_figures(written.get("_hansen_gfc_summary"),
                                    written.get("_hansen_gfc_loss_by_year"))
    return {"maps": n_maps, "figures": n_figs, "tables": len(list(dst.rglob("*.csv"))),
            "q_timeline": counts.get("_deforestation_timeline_", 0),
            "q_landcover": counts.get("_landcover", 0),
            "q_gfc": counts.get("_hansen_gfc_summary", 0)}


def _partial_note(res: dict) -> str:
    """Flag areas whose SOURCE export is missing quadrants for a data family."""
    bits = []
    for key, label in (("q_timeline", "timeline"), ("q_landcover", "landcover"),
                       ("q_gfc", "gfc")):
        for scope in ("t", "b"):
            n = res.get(f"{scope}_{key}")
            if n is not None and 0 < n < 4:
                bits.append(f"{scope}:{label}={n}/4")
    return f"   ⚠ partial source export ({', '.join(bits)})" if bits else ""


def _merge_one_territory(args: tuple) -> dict:
    """ProcessPool worker: merge a territory core and its buffer ring."""
    (src_batch, dst_batch, tname, display, state_code, do_maps, do_figures) = args
    src_batch, dst_batch = Path(src_batch), Path(dst_batch)
    src_t = src_batch / "territory" / tname
    res = {"territory": display, "slug": tname, "split": is_split(src_t)}
    if not res["split"]:
        dst_t = dst_batch / "territory" / tname
        if dst_t.exists():
            shutil.rmtree(dst_t)
        shutil.copytree(src_t, dst_t)
        res["note"] = "copied (not split)"
    else:
        res.update({f"t_{k}": v for k, v in merge_area(
            src_t, dst_batch / "territory" / tname, display,
            state_code=state_code, do_maps=do_maps, do_figures=do_figures).items()})
    for src_b in sorted((src_batch / "buffer").glob(f"{tname}_Buffer_*")):
        dst_b = dst_batch / "buffer" / src_b.name
        if not is_split(src_b):
            if dst_b.exists():
                shutil.rmtree(dst_b)
            shutil.copytree(src_b, dst_b)
            continue
        km = re.search(r"Buffer_(\d+)km", src_b.name)
        res.update({f"b_{k}": v for k, v in merge_area(
            src_b, dst_b, display, state_code=state_code, do_maps=do_maps,
            do_figures=do_figures,
            title_extra=f" — {km.group(1)} km buffer" if km else " — buffer").items()})
    return res


# ---------------------------------------------------------------------------
# validation
# ---------------------------------------------------------------------------


def _sum_landcover(area: Path, year: int) -> float:
    tot = 0.0
    for p in (area / "mapbiomas").glob(f"*_mapbiomas_{year}_landcover*.csv"):
        try:
            tot += float(pd.read_csv(p)["Area_ha"].sum())
        except Exception:  # noqa: BLE001
            pass
    return tot


def validate(src_batch: Path, dst_batch: Path, year2: int, buffer_km: float) -> pd.DataFrame:
    """Merged totals vs. geodesic boundary area, and how much ring survives.

    The quadrant boxes tile the *territory* bbox, so the buffer ring is only
    exported where it falls inside that bbox — ``ring_in_bbox_pct`` is the
    ceiling on ring coverage and ``ring_coverage_pct`` what the merged tables
    actually hold (lower again where the ring leaves Brazil, since MapBiomas
    stops at the border).
    """
    import geopandas as gpd
    from shapely.geometry import box, shape

    EA = 6933  # EASE-Grid 2.0 global, equal-area
    rows = []
    for dst_t in sorted((dst_batch / "territory").iterdir()):
        if not dst_t.is_dir():
            continue
        rec = {"slug": dst_t.name, "merged_area_ha": _sum_landcover(dst_t, year2)}
        gj_path = dst_t / "boundary.geojson"
        if gj_path.is_file():
            gj = json.loads(gj_path.read_text())
            geom = shape(gj["geometry"] if "geometry" in gj else
                         gj["features"][0]["geometry"])
            g = gpd.GeoSeries([geom], crs=4326).to_crs(EA).iloc[0]
            rec["boundary_ha"] = g.area / 1e4
            minx, miny, maxx, maxy = geom.bounds
            bbox = gpd.GeoSeries([box(minx, miny, maxx, maxy)], crs=4326).to_crs(EA).iloc[0]
            ring = g.buffer(buffer_km * 1000).difference(g)
            rec["ring_ha"] = ring.area / 1e4
            rec["ring_in_bbox_ha"] = ring.intersection(bbox).area / 1e4
        bufs = list((dst_batch / "buffer").glob(f"{dst_t.name}_Buffer_*"))
        rec["merged_buffer_ha"] = _sum_landcover(bufs[0], year2) if bufs else np.nan
        rows.append(rec)
    df = pd.DataFrame(rows)
    if "boundary_ha" in df:
        df["area_vs_boundary_pct"] = 100 * df["merged_area_ha"] / df["boundary_ha"]
        df["ring_in_bbox_pct"] = 100 * df["ring_in_bbox_ha"] / df["ring_ha"]
        df["ring_coverage_pct"] = 100 * df["merged_buffer_ha"] / df["ring_ha"]
    return df


# ---------------------------------------------------------------------------
# state-code lookup (for the governor stripe on the timeline charts)
# ---------------------------------------------------------------------------


def load_state_codes(names: Sequence[str], kind: str) -> Dict[str, Optional[str]]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import governance_policy_report as gov
        import geopandas as gpd
    except Exception as exc:  # noqa: BLE001
        print(f"  ! state lookup unavailable ({exc})", file=sys.stderr)
        return {n: None for n in names}
    gpkg = gov.GPKG_IND if kind == "indigenous" else gov.GPKG_UC
    name_col = "terrai_nom" if kind == "indigenous" else "nome_uc"
    uf_col = "uf_sigla" if kind == "indigenous" else "uf"
    gdf = gpd.read_file(gpkg)
    lut = {gov._norm(r[name_col]): r for _, r in gdf.iterrows()}
    out: Dict[str, Optional[str]] = {}
    for n in names:
        row = lut.get(gov._strip_code(n))
        if row is None:  # NB a matched row is a Series — never use `or` here
            row = lut.get(gov._norm(n))
        out[n] = gov._first_sig(row[uf_col]) if row is not None else None
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def merge_batch(src: Path, dst: Path, *, kind="indigenous", jobs=4, do_maps=True,
                do_figures=True, do_validate=True) -> Path:
    summary = json.loads((src / "batch_summary.json").read_text())
    year2 = int(summary.get("mapbiomas_year2", 2024))
    buffer_km = float(summary.get("buffer_km", 10.0) or 0.0)
    dst.mkdir(parents=True, exist_ok=True)
    for fname in ("batch_summary.json", "batch_report.md"):
        if (src / fname).is_file():
            shutil.copy2(src / fname, dst / fname)

    display_by_slug = {_slugify(e.get("territory", "")): e.get("territory", "")
                       for e in summary.get("results", [])}
    tdirs = sorted(d for d in (src / "territory").iterdir() if d.is_dir())
    names = [display_by_slug.get(d.name, d.name.replace("_", " ")) for d in tdirs]
    states = load_state_codes(names, kind) if do_figures else {n: None for n in names}

    tasks = [(str(src), str(dst), d.name, display_by_slug.get(d.name, d.name.replace("_", " ")),
              states.get(display_by_slug.get(d.name, d.name.replace("_", " "))),
              do_maps, do_figures) for d in tdirs]
    print(f"merging {len(tasks)} territories  src={src.name}  →  {dst}")
    results = []
    if jobs > 1:
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futs = {pool.submit(_merge_one_territory, t): t[3] for t in tasks}
            for fut in as_completed(futs):
                res = fut.result()
                results.append(res)
                print(f"  ✓ {res['territory']}  "
                      f"tables={res.get('t_tables', '—')} maps={res.get('t_maps', '—')} "
                      f"figs={res.get('t_figures', '—')}  [{len(results)}/{len(tasks)}]"
                      + _partial_note(res))
    else:
        for t in tasks:
            res = _merge_one_territory(t)
            results.append(res)
            print(f"  ✓ {res['territory']}  tables={res.get('t_tables', '—')} "
                  f"maps={res.get('t_maps', '—')} figs={res.get('t_figures', '—')}"
                  + _partial_note(res))
    pd.DataFrame(results).to_csv(dst / "quadrant_merge_log.csv", index=False)

    if do_validate:
        print("validating merged totals …")
        val = validate(src, dst, year2, buffer_km)
        val.to_csv(dst / "quadrant_merge_report.csv", index=False)
        cols = [c for c in ("area_vs_boundary_pct", "ring_in_bbox_pct", "ring_coverage_pct")
                if c in val.columns]
        if cols:
            print(val[["slug"] + cols].round(1).to_string(index=False))
            print("\nmeans:", val[cols].mean().round(1).to_dict())
    return dst


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="quadrant-split batch folder")
    ap.add_argument("--out", default=None, help="destination (default: <src>_merged)")
    ap.add_argument("--kind", default="indigenous", choices=("indigenous", "conservation"))
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-maps", action="store_true")
    ap.add_argument("--no-figures", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    args = ap.parse_args(argv)
    src = Path(args.src).resolve()
    dst = Path(args.out).resolve() if args.out else src.with_name(src.name + "_merged")
    merge_batch(src, dst, kind=args.kind, jobs=args.jobs, do_maps=not args.no_maps,
                do_figures=not args.no_figures, do_validate=not args.no_validate)
    print(f"Done → {dst}")


if __name__ == "__main__":
    main()
