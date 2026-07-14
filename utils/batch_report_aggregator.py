#!/usr/bin/env python3
"""Aggregate and compare results from multiple yvynation batch-processing runs.

Reads the folder trees produced by the Reflex batch pipeline (either the
unzipped ZIP or the live run folder), collects the per-territory CSVs,
builds:

  data/     aggregated CSVs (summary, land cover long table, timelines)
  yvynation_comparison.xlsx  multi-sheet spreadsheet
  figures/  cross-territory comparison charts (PNG)
  images/   copied per-territory figure PNGs used by the reports
  report_<group>.md   side-by-side territory vs. buffer report per batch
  README.md           index + cross-group comparison

Usage:
  python batch_report_aggregator.py BATCH_DIR[:LABEL] [BATCH_DIR[:LABEL] ...] \
      --out /path/to/output

Each BATCH_DIR must contain territory/, buffer/ and batch_summary.json.
LABEL (optional, after a colon) names the group in outputs; defaults to the
folder basename.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------- constants

FOREST_CLASSES = {
    "Forest Formation",
    "Savanna Formation",
    "Mangrove",
    "Floodable Forest",
    "Wooded Sandbank Vegetation",
}
NATURAL_NONFOREST_CLASSES = {
    "Grassland",
    "Wetland",
    "Herbaceous Sandbank Vegetation",
    "Hypersaline Tidal Flat",
    "Rocky Outcrop",
    "Beach and Sand",
    "River Lake and Ocean",
}
ANTHROPIC_CLASSES = {
    "Pasture",
    "Mosaic of Uses",
    "Soybean",
    "Sugar Cane",
    "Rice",
    "Cotton",
    "Coffee",
    "Citrus",
    "Palm Oil",
    "Other Temporary Crops",
    "Other Perennial Crops",
    "Forest Plantation",
    "Urban Area",
    "Mining",
    "Aquaculture",
    "Other non Vegetated Areas",
}

TIMELINE_SERIES = ["hansen_loss", "mb_defor_primary", "mb_secondary_growth", "mb_fire_scar"]

# Figure pairs shown side-by-side in the per-territory report sections.
# (subdir under the area folder, filename suffix, caption)
PAIRED_FIGURES = [
    ("deforestation_timeline/figures", "raw", "Deforestation timeline (annual, raw)"),
    ("deforestation_timeline/figures", "ma5", "Deforestation timeline (5-yr moving average)"),
    ("mapbiomas/figures", "comparison_bars", "MapBiomas class areas — {y1} vs {y2}"),
    ("mapbiomas/figures", "sankey", "MapBiomas transitions {y1} → {y2} (Sankey)"),
    ("hansen_gfc/figures", "loss_by_year", "Hansen GFC forest loss by year"),
]

# Territory-only static maps (no buffer counterpart), shown as a grid.
REPORT_MAPS = [
    ("MapBiomas_{y1}", "MapBiomas {y1}"),
    ("MapBiomas_{y2}", "MapBiomas {y2}"),
    ("Satellite_Basemap", "Satellite basemap"),
    ("Deforestation___Secondary_Vegetation_{y2}", "Deforestation / secondary vegetation {y2}"),
    ("Fire_Frequency__1985_{y2}", "Fire frequency 1985–{y2}"),
    ("Year_of_Last_Fire", "Year of last fire"),
]

# ---------------------------------------------------------------- data model


@dataclass
class AreaBundle:
    """One analysed area (territory core or its buffer ring)."""

    name: str  # display name (from batch_summary when possible)
    slug: str  # folder name
    path: Path
    landcover: Dict[int, pd.DataFrame] = field(default_factory=dict)  # year -> df
    comparison: Optional[pd.DataFrame] = None
    timeline: Optional[pd.DataFrame] = None
    gfc_summary: Optional[pd.DataFrame] = None
    gfc_loss_by_year: Optional[pd.DataFrame] = None


@dataclass
class TerritoryResult:
    name: str
    slug: str
    group: str
    territory: AreaBundle
    buffer: Optional[AreaBundle]


@dataclass
class BatchRun:
    label: str
    path: Path
    year1: int
    year2: int
    buffer_km: float
    results: List[TerritoryResult] = field(default_factory=list)


# ---------------------------------------------------------------- loading


def _read_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.is_file():
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! failed to read {path.name}: {exc}", file=sys.stderr)
        return None


def _find_one(folder: Path, pattern: str) -> Optional[Path]:
    if not folder.is_dir():
        return None
    matches = sorted(folder.glob(pattern))
    return matches[0] if matches else None


def load_area(path: Path, name: str, year1: int, year2: int) -> AreaBundle:
    area = AreaBundle(name=name, slug=path.name, path=path)
    mb = path / "mapbiomas"
    for year in (year1, year2):
        p = _find_one(mb, f"*_mapbiomas_{year}_landcover*.csv")
        if p is not None:
            df = _read_csv(p)
            if df is not None:
                # Two header variants exist across batch versions:
                # Class_ID,Class,Pixels,Area_ha  and  Year,Class_ID,Class_Name,Area_ha,Area_km2
                if "Class" not in df.columns and "Class_Name" in df.columns:
                    df = df.rename(columns={"Class_Name": "Class"})
                area.landcover[year] = df
    p = _find_one(mb, f"*_mapbiomas_{year1}_vs_{year2}_comparison*.csv")
    area.comparison = _read_csv(p) if p else None
    p = _find_one(path / "deforestation_timeline", "*_deforestation_timeline_*.csv")
    area.timeline = _read_csv(p) if p else None
    gfc = path / "hansen_gfc"
    p = _find_one(gfc, "*_hansen_gfc_summary*.csv")
    area.gfc_summary = _read_csv(p) if p else None
    p = _find_one(gfc, "*_hansen_gfc_loss_by_year*.csv")
    area.gfc_loss_by_year = _read_csv(p) if p else None
    return area


def _display_names(summary: dict, territory_dirs: List[Path]) -> Dict[str, str]:
    """Map slug -> display name using batch_summary.json result order when sane."""

    def slugify(text: str) -> str:
        # Mirror of the batch export slug: strip accents, non-alnum -> _
        norm = unicodedata.normalize("NFD", text)
        ascii_txt = norm.encode("ascii", "ignore").decode()
        return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", ascii_txt)).strip("_")

    names: Dict[str, str] = {}
    for entry in summary.get("results", []):
        display = entry.get("territory", "")
        if display:
            names[slugify(display)] = display
    return names


def load_batch(path: Path, label: str) -> BatchRun:
    summary = json.loads((path / "batch_summary.json").read_text())
    year1 = int(summary.get("mapbiomas_year1", 1985))
    year2 = int(summary.get("mapbiomas_year2", 2024))
    buffer_km = float(summary.get("buffer_km", 10.0))
    run = BatchRun(label=label, path=path, year1=year1, year2=year2, buffer_km=buffer_km)

    territory_root = path / "territory"
    buffer_root = path / "buffer"
    territory_dirs = sorted(d for d in territory_root.iterdir() if d.is_dir())
    names = _display_names(summary, territory_dirs)

    for tdir in territory_dirs:
        display = names.get(tdir.name, tdir.name.replace("_", " "))
        terr = load_area(tdir, display, year1, year2)
        buf = None
        buf_matches = sorted(buffer_root.glob(f"{tdir.name}_Buffer_*")) if buffer_root.is_dir() else []
        if buf_matches:
            buf = load_area(buf_matches[0], f"{display} (buffer)", year1, year2)
        run.results.append(
            TerritoryResult(name=display, slug=tdir.name, group=label, territory=terr, buffer=buf)
        )
    return run


# ---------------------------------------------------------------- metrics


def _class_sum(df: Optional[pd.DataFrame], classes: set, col: str) -> float:
    if df is None or "Class" not in df.columns or col not in df.columns:
        return float("nan")
    return float(df.loc[df["Class"].isin(classes), col].sum())


def _gfc_metric(df: Optional[pd.DataFrame], metric: str) -> float:
    if df is None:
        return float("nan")
    row = df.loc[df["Metric"] == metric]
    if row.empty:
        return float("nan")
    return float(row["Area_ha"].iloc[0])


def area_metrics(area: Optional[AreaBundle], year1: int, year2: int) -> Dict[str, float]:
    m: Dict[str, float] = {}
    if area is None:
        return m
    cmp_df = area.comparison
    c1, c2 = f"Area_{year1}_ha", f"Area_{year2}_ha"
    total = _class_sum(cmp_df, set(cmp_df["Class"]) if cmp_df is not None else set(), c2)
    m["area_total_ha"] = total
    for label, classes in (
        ("forest", FOREST_CLASSES),
        ("natural_nonforest", NATURAL_NONFOREST_CLASSES),
        ("anthropic", ANTHROPIC_CLASSES),
    ):
        a1 = _class_sum(cmp_df, classes, c1)
        a2 = _class_sum(cmp_df, classes, c2)
        m[f"{label}_{year1}_ha"] = a1
        m[f"{label}_{year2}_ha"] = a2
        m[f"{label}_change_ha"] = a2 - a1
    if m.get(f"forest_{year1}_ha"):
        m["forest_change_pct"] = 100.0 * m["forest_change_ha"] / m[f"forest_{year1}_ha"]
    if total:
        m[f"forest_{year2}_pct_of_area"] = 100.0 * m[f"forest_{year2}_ha"] / total
        m[f"anthropic_{year2}_pct_of_area"] = 100.0 * m[f"anthropic_{year2}_ha"] / total

    m["gfc_tree_cover_2000_ha"] = _gfc_metric(area.gfc_summary, "Tree Cover 2000")
    m["gfc_loss_ha"] = _gfc_metric(area.gfc_summary, "Forest Loss")
    m["gfc_gain_ha"] = _gfc_metric(area.gfc_summary, "Forest Gain")
    if m.get("gfc_tree_cover_2000_ha"):
        m["gfc_loss_pct_of_2000_cover"] = 100.0 * m["gfc_loss_ha"] / m["gfc_tree_cover_2000_ha"]

    tl = area.timeline
    if tl is not None and "year" in tl.columns:
        for col in TIMELINE_SERIES:
            if col in tl.columns:
                m[f"{col}_total_ha"] = float(tl[col].sum())
        if "mb_defor_primary" in tl.columns and tl["mb_defor_primary"].max() > 0:
            m["peak_defor_year"] = int(tl.loc[tl["mb_defor_primary"].idxmax(), "year"])
    return m


def build_summary_table(runs: List[BatchRun]) -> pd.DataFrame:
    rows = []
    for run in runs:
        for res in run.results:
            row: Dict[str, object] = {"group": run.label, "territory": res.name, "slug": res.slug}
            for key, val in area_metrics(res.territory, run.year1, run.year2).items():
                row[f"t_{key}"] = val
            for key, val in area_metrics(res.buffer, run.year1, run.year2).items():
                row[f"b_{key}"] = val
            rows.append(row)
    return pd.DataFrame(rows)


def build_landcover_long(runs: List[BatchRun]) -> pd.DataFrame:
    rows = []
    for run in runs:
        for res in run.results:
            for scope, area in (("territory", res.territory), ("buffer", res.buffer)):
                if area is None:
                    continue
                for year, df in area.landcover.items():
                    for _, r in df.iterrows():
                        rows.append(
                            {
                                "group": run.label,
                                "territory": res.name,
                                "scope": scope,
                                "year": year,
                                "class": r["Class"],
                                "area_ha": r["Area_ha"],
                            }
                        )
    return pd.DataFrame(rows)


def build_timeline_long(runs: List[BatchRun]) -> pd.DataFrame:
    rows = []
    for run in runs:
        for res in run.results:
            for scope, area in (("territory", res.territory), ("buffer", res.buffer)):
                if area is None or area.timeline is None:
                    continue
                df = area.timeline
                for _, r in df.iterrows():
                    row = {
                        "group": run.label,
                        "territory": res.name,
                        "scope": scope,
                        "year": int(r["year"]),
                    }
                    for col in TIMELINE_SERIES:
                        if col in df.columns:
                            row[col] = r[col]
                    rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- spreadsheet


def write_spreadsheet(out: Path, summary: pd.DataFrame, lc: pd.DataFrame, tl: pd.DataFrame) -> Path:
    xlsx = out / "yvynation_comparison.xlsx"
    with pd.ExcelWriter(xlsx, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="summary", index=False)
        for scope in ("territory", "buffer"):
            sub = lc[lc["scope"] == scope]
            for year in sorted(sub["year"].unique()):
                pivot = (
                    sub[sub["year"] == year]
                    .pivot_table(index=["group", "territory"], columns="class", values="area_ha", aggfunc="sum")
                    .round(2)
                )
                pivot.to_excel(writer, sheet_name=f"lc{year}_{scope[:4]}")
        for series in ("mb_defor_primary", "hansen_loss", "mb_fire_scar"):
            if series not in tl.columns:
                continue
            for scope in ("territory", "buffer"):
                sub = tl[tl["scope"] == scope]
                pivot = sub.pivot_table(index="year", columns=["group", "territory"], values=series).round(2)
                sheet = f"{series.replace('mb_', '')[:22]}_{scope[:4]}"
                pivot.to_excel(writer, sheet_name=sheet)
    return xlsx


# ---------------------------------------------------------------- charts


def _slug(text: str) -> str:
    norm = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode()
    return re.sub(r"_+", "_", re.sub(r"[^A-Za-z0-9]+", "_", norm)).strip("_").lower()


def chart_forest_change_ranked(summary: pd.DataFrame, run: BatchRun, fig_dir: Path) -> Path:
    sub = summary[summary["group"] == run.label].dropna(subset=["t_forest_change_pct"])
    sub = sub.sort_values("t_forest_change_pct")
    n = len(sub)
    fig, ax = plt.subplots(figsize=(11, max(4, 0.32 * n + 1.5)))
    y = np.arange(n)
    ax.barh(y + 0.2, sub["t_forest_change_pct"], height=0.38, color="#166534", label="Territory")
    if "b_forest_change_pct" in sub:
        ax.barh(y - 0.2, sub["b_forest_change_pct"], height=0.38, color="#b45309", label=f"Buffer {run.buffer_km:.0f} km")
    ax.set_yticks(y, [_shorten(t) for t in sub["territory"]], fontsize=7)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel(f"Forest area change {run.year1}→{run.year2} (% of {run.year1} forest)")
    ax.set_title(f"Forest change ranking — {run.label} (n={n})")
    ax.legend(loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = fig_dir / f"forest_change_ranked_{_slug(run.label)}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def chart_inside_outside_scatter(summary: pd.DataFrame, runs: List[BatchRun], fig_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 8))
    colors = {run.label: c for run, c in zip(runs, ["#7c3aed", "#059669", "#b45309", "#2563eb"])}
    for run in runs:
        sub = summary[summary["group"] == run.label].dropna(
            subset=["t_gfc_loss_pct_of_2000_cover", "b_gfc_loss_pct_of_2000_cover"]
        )
        ax.scatter(
            sub["b_gfc_loss_pct_of_2000_cover"],
            sub["t_gfc_loss_pct_of_2000_cover"],
            s=30,
            alpha=0.75,
            color=colors[run.label],
            label=f"{run.label} (n={len(sub)})",
        )
    lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, lim], [0, lim], "k--", lw=1, label="inside = outside")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("Forest loss in 10 km buffer (% of 2000 tree cover, Hansen GFC)")
    ax.set_ylabel("Forest loss inside area (% of 2000 tree cover)")
    ax.set_title("Protection effect: forest loss inside vs. outside\n(points below the line lose less forest than their surroundings)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gfc_loss_inside_vs_outside.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def chart_group_timelines(tl: pd.DataFrame, runs: List[BatchRun], fig_dir: Path) -> Path:
    series_meta = [
        ("mb_defor_primary", "Primary-vegetation deforestation (MapBiomas)"),
        ("mb_fire_scar", "Fire scars (MapBiomas)"),
    ]
    fig, axes = plt.subplots(len(series_meta), len(runs), figsize=(7.5 * len(runs), 4.2 * len(series_meta)), squeeze=False)
    for j, run in enumerate(runs):
        for i, (series, title) in enumerate(series_meta):
            ax = axes[i][j]
            for scope, color in (("territory", "#166534"), ("buffer", "#b45309")):
                sub = tl[(tl["group"] == run.label) & (tl["scope"] == scope)]
                if sub.empty or series not in sub.columns:
                    continue
                agg = sub.groupby("year")[series].sum()
                ax.plot(agg.index, agg.values, color=color, lw=1.8,
                        label="Territories (sum)" if scope == "territory" else f"Buffers {run.buffer_km:.0f} km (sum)")
            ax.set_title(f"{title}\n{run.label}", fontsize=10)
            ax.set_ylabel("ha / year")
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
    fig.tight_layout()
    path = fig_dir / "group_annual_timelines.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def chart_landcover_composition(lc: pd.DataFrame, run: BatchRun, fig_dir: Path) -> Path:
    sub = lc[(lc["group"] == run.label) & (lc["scope"] == "territory") & (lc["year"] == run.year2)]
    pivot = sub.pivot_table(index="territory", columns="class", values="area_ha", aggfunc="sum").fillna(0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    top = pivot.sum().sort_values(ascending=False).head(9).index.tolist()
    other = [c for c in pct.columns if c not in top]
    plot_df = pct[top].copy()
    if other:
        plot_df["Other"] = pct[other].sum(axis=1)
    order = plot_df.get("Forest Formation", plot_df.iloc[:, 0]).sort_values(ascending=True).index
    plot_df = plot_df.loc[order]
    n = len(plot_df)
    fig, ax = plt.subplots(figsize=(12, max(4, 0.3 * n + 2)))
    left = np.zeros(n)
    cmap = plt.get_cmap("tab20")
    for k, col in enumerate(plot_df.columns):
        ax.barh(np.arange(n), plot_df[col], left=left, height=0.75, color=cmap(k % 20), label=col)
        left += plot_df[col].values
    ax.set_yticks(np.arange(n), [_shorten(t) for t in plot_df.index], fontsize=7)
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"% of area — MapBiomas {run.year2}")
    ax.set_title(f"Land-cover composition {run.year2} — {run.label}")
    ax.legend(fontsize=7, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    path = fig_dir / f"landcover_composition_{run.year2}_{_slug(run.label)}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _shorten(name: str, limit: int = 42) -> str:
    return name if len(name) <= limit else name[: limit - 1] + "…"


# ---------------------------------------------------------------- report


def _fmt(val: object, unit: str = "", decimals: int = 0) -> str:
    if val is None or (isinstance(val, float) and (np.isnan(val))):
        return "—"
    if isinstance(val, (int, float)):
        return f"{val:,.{decimals}f}{unit}"
    return str(val)


def _copy_image(src: Optional[Path], dest_dir: Path) -> Optional[str]:
    if src is None or not src.is_file():
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if not dest.exists():
        shutil.copy2(src, dest)
    return dest.name


def territory_section(res: TerritoryResult, run: BatchRun, out: Path, img_root: Path) -> str:
    y1, y2 = run.year1, run.year2
    tm = area_metrics(res.territory, y1, y2)
    bm = area_metrics(res.buffer, y1, y2)
    img_dir = img_root / _slug(run.label) / res.slug
    rel = lambda name: f"images/{_slug(run.label)}/{res.slug}/{name}"  # noqa: E731

    lines = [f"## {res.name}", ""]
    lines += [
        f"| Metric | Territory | Buffer {run.buffer_km:.0f} km |",
        "|---|---:|---:|",
        f"| Total area | {_fmt(tm.get('area_total_ha'), ' ha')} | {_fmt(bm.get('area_total_ha'), ' ha')} |",
        f"| Forest {y1} | {_fmt(tm.get(f'forest_{y1}_ha'), ' ha')} | {_fmt(bm.get(f'forest_{y1}_ha'), ' ha')} |",
        f"| Forest {y2} | {_fmt(tm.get(f'forest_{y2}_ha'), ' ha')} | {_fmt(bm.get(f'forest_{y2}_ha'), ' ha')} |",
        f"| Forest change {y1}→{y2} | {_fmt(tm.get('forest_change_pct'), ' %', 2)} | {_fmt(bm.get('forest_change_pct'), ' %', 2)} |",
        f"| Anthropic use {y2} (% of area) | {_fmt(tm.get(f'anthropic_{y2}_pct_of_area'), ' %', 1)} | {_fmt(bm.get(f'anthropic_{y2}_pct_of_area'), ' %', 1)} |",
        f"| Hansen GFC loss (% of 2000 cover) | {_fmt(tm.get('gfc_loss_pct_of_2000_cover'), ' %', 1)} | {_fmt(bm.get('gfc_loss_pct_of_2000_cover'), ' %', 1)} |",
        f"| Fire scars total (MapBiomas) | {_fmt(tm.get('mb_fire_scar_total_ha'), ' ha')} | {_fmt(bm.get('mb_fire_scar_total_ha'), ' ha')} |",
        f"| Peak deforestation year | {int(tm['peak_defor_year']) if tm.get('peak_defor_year') else '—'} | {int(bm['peak_defor_year']) if bm.get('peak_defor_year') else '—'} |",
        "",
    ]

    # Territory-only maps grid (2 per row)
    map_cells = []
    for suffix_t, caption_t in REPORT_MAPS:
        suffix = suffix_t.format(y1=y1, y2=y2)
        caption = caption_t.format(y1=y1, y2=y2)
        src = _find_one(res.territory.path / "maps", f"*_{suffix}.png")
        name = _copy_image(src, img_dir)
        if name:
            map_cells.append((caption, rel(name)))
    if map_cells:
        lines.append("### Maps (territory)\n")
        for i in range(0, len(map_cells), 2):
            chunk = map_cells[i : i + 2]
            lines.append("| " + " | ".join(c for c, _ in chunk) + " |")
            lines.append("|" + "---|" * len(chunk))
            lines.append("| " + " | ".join(f"![{c}]({p})" for c, p in chunk) + " |")
            lines.append("")

    # Side-by-side territory vs buffer figures
    lines.append(f"### Territory vs. buffer ({run.buffer_km:.0f} km ring)\n")
    for subdir, suffix, caption_t in PAIRED_FIGURES:
        caption = caption_t.format(y1=y1, y2=y2)
        t_src = _find_one(res.territory.path / subdir, f"*_{suffix}.png")
        b_src = None
        if res.buffer is not None:
            b_src = _find_one(res.buffer.path / subdir, f"*_{suffix}_Buffer_*.png")
        t_name = _copy_image(t_src, img_dir)
        b_name = _copy_image(b_src, img_dir)
        if not t_name and not b_name:
            continue
        lines.append(f"**{caption}**\n")
        lines.append("| Territory | Buffer |")
        lines.append("|---|---|")
        t_cell = f"![{caption} — territory]({rel(t_name)})" if t_name else "*(missing)*"
        b_cell = f"![{caption} — buffer]({rel(b_name)})" if b_name else "*(missing)*"
        lines.append(f"| {t_cell} | {b_cell} |")
        lines.append("")

    lines.append("---\n")
    return "\n".join(lines)


def write_group_report(run: BatchRun, summary: pd.DataFrame, out: Path, img_root: Path, charts: Dict[str, Path]) -> Path:
    sub = summary[summary["group"] == run.label]
    lines = [
        f"# Yvynation comparison report — {run.label}",
        "",
        f"- Source batch: `{run.path}`",
        f"- Areas: **{len(run.results)}** | MapBiomas years: **{run.year1} vs {run.year2}** | Buffer: **{run.buffer_km:.0f} km**",
        f"- Aggregate forest change {run.year1}→{run.year2}: territories "
        f"**{_fmt(sub['t_forest_change_ha'].sum(), ' ha')}**, buffers **{_fmt(sub['b_forest_change_ha'].sum(), ' ha')}**",
        "",
        "## Group overview",
        "",
    ]
    for key in ("forest_change_ranked", "landcover_composition"):
        p = charts.get(f"{key}_{_slug(run.label)}")
        if p:
            lines.append(f"![{key}](figures/{p.name})\n")
    lines += [
        "## Ranking table",
        "",
        f"| Territory | Area (ha) | Forest change % (T) | Forest change % (B) | GFC loss % (T) | GFC loss % (B) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    ranked = sub.sort_values("t_forest_change_pct")
    for _, r in ranked.iterrows():
        anchor = re.sub(r"[^a-z0-9\- ]", "", r["territory"].lower()).replace(" ", "-")
        lines.append(
            f"| [{r['territory']}](#{anchor}) | {_fmt(r.get('t_area_total_ha'))} | "
            f"{_fmt(r.get('t_forest_change_pct'), ' %', 2)} | {_fmt(r.get('b_forest_change_pct'), ' %', 2)} | "
            f"{_fmt(r.get('t_gfc_loss_pct_of_2000_cover'), ' %', 1)} | {_fmt(r.get('b_gfc_loss_pct_of_2000_cover'), ' %', 1)} |"
        )
    lines += ["", "---", ""]

    for res in run.results:
        lines.append(territory_section(res, run, out, img_root))

    path = out / f"report_{_slug(run.label)}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_index(runs: List[BatchRun], summary: pd.DataFrame, out: Path, charts: Dict[str, Path], xlsx: Path) -> Path:
    lines = [
        "# Yvynation multi-batch comparison",
        "",
        f"Generated: {pd.Timestamp.now().isoformat(timespec='seconds')}",
        "",
        "| Group | Areas | Years | Buffer | Report |",
        "|---|---:|---|---|---|",
    ]
    for run in runs:
        lines.append(
            f"| {run.label} | {len(run.results)} | {run.year1}–{run.year2} | {run.buffer_km:.0f} km | "
            f"[report_{_slug(run.label)}.md](report_{_slug(run.label)}.md) |"
        )
    lines += [
        "",
        f"Spreadsheet: [{xlsx.name}]({xlsx.name}) — sheets: summary, land cover pivots "
        "(per year, territory/buffer), annual timelines (deforestation, Hansen loss, fire).",
        "Raw aggregated tables in [data/](data/).",
        "",
        "## Cross-group comparisons",
        "",
    ]
    for key in ("gfc_loss_inside_vs_outside", "group_annual_timelines"):
        p = charts.get(key)
        if p:
            lines.append(f"![{key}](figures/{p.name})\n")

    # group aggregate stats
    lines += ["## Group aggregates", "", "| Group | Σ area (ha) | Σ forest change T (ha) | mean forest change T (%) | mean forest change B (%) | mean GFC loss T (%) | mean GFC loss B (%) |", "|---|---:|---:|---:|---:|---:|---:|"]
    for run in runs:
        sub = summary[summary["group"] == run.label]
        lines.append(
            f"| {run.label} | {_fmt(sub['t_area_total_ha'].sum())} | {_fmt(sub['t_forest_change_ha'].sum())} | "
            f"{_fmt(sub['t_forest_change_pct'].mean(), ' %', 2)} | {_fmt(sub['b_forest_change_pct'].mean(), ' %', 2)} | "
            f"{_fmt(sub['t_gfc_loss_pct_of_2000_cover'].mean(), ' %', 2)} | {_fmt(sub['b_gfc_loss_pct_of_2000_cover'].mean(), ' %', 2)} |"
        )
    path = out / "README.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batches", nargs="+", help="batch folder, optionally suffixed with :LABEL")
    ap.add_argument("--out", required=True, help="output directory for the aggregated report")
    args = ap.parse_args()

    out = Path(args.out)
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    img_root = out / "images"
    img_root.mkdir(exist_ok=True)

    runs: List[BatchRun] = []
    for spec in args.batches:
        if ":" in spec and not spec.startswith("/"):
            raise SystemExit(f"bad batch spec: {spec}")
        path_str, _, label = spec.rpartition(":") if (":" in spec[1:]) else ("", "", "")
        if path_str:
            path = Path(path_str)
        else:
            path, label = Path(spec), Path(spec).name
        if not (path / "batch_summary.json").is_file():
            raise SystemExit(f"not a batch folder (missing batch_summary.json): {path}")
        print(f"Loading {label}: {path}")
        runs.append(load_batch(path, label))
        print(f"  {len(runs[-1].results)} territories")

    print("Building aggregated tables …")
    summary = build_summary_table(runs)
    lc = build_landcover_long(runs)
    tl = build_timeline_long(runs)
    summary.to_csv(out / "data" / "summary_metrics.csv", index=False)
    lc.to_csv(out / "data" / "landcover_long.csv", index=False)
    tl.to_csv(out / "data" / "timeline_long.csv", index=False)

    print("Writing spreadsheet …")
    xlsx = write_spreadsheet(out, summary, lc, tl)

    print("Rendering comparison charts …")
    charts: Dict[str, Path] = {}
    charts["gfc_loss_inside_vs_outside"] = chart_inside_outside_scatter(summary, runs, out / "figures")
    charts["group_annual_timelines"] = chart_group_timelines(tl, runs, out / "figures")
    for run in runs:
        charts[f"forest_change_ranked_{_slug(run.label)}"] = chart_forest_change_ranked(summary, run, out / "figures")
        charts[f"landcover_composition_{_slug(run.label)}"] = chart_landcover_composition(lc, run, out / "figures")

    print("Writing markdown reports (copying figure PNGs) …")
    for run in runs:
        p = write_group_report(run, summary, out, img_root, charts)
        print(f"  {p}")
    idx = write_index(runs, summary, out, charts, xlsx)
    print(f"  {idx}")
    print(f"Done → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
