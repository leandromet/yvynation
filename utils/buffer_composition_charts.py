#!/usr/bin/env python3
"""Render land-cover composition charts for the 10 km BUFFER scope, one per
dataset, with rows ordered exactly like the existing core (territory) chart so
each area lines up between the two figures for a core-vs-buffer read.

Reuses the MapBiomas palette and helpers from batch_report_aggregator. Reads the
already-aggregated data/landcover_long.csv in each report dir and writes
figures/landcover_composition_<year2>_<slug>_buffer.png next to the core chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, "/home/leandromb/google_eengine/yvynation/utils")
import batch_report_aggregator as agg  # noqa: E402

YEAR2 = 2024


def _pct_pivot(lc, label, scope):
    sub = lc[(lc["group"] == label) & (lc["scope"] == scope) & (lc["year"] == YEAR2)]
    pivot = sub.pivot_table(index="territory", columns="class", values="area_ha", aggfunc="sum").fillna(0)
    pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    return pivot, pct


REGION_ABBR = {"Norte": "N", "Centro-Oeste": "CO", "Nordeste": "NE",
               "Sudeste": "SE", "Sul": "S"}


def place_labels_from_meta(data_dir: Path):
    """Build territory → 'Name · UF·Region' from a saved territory_metadata.csv,
    if it has usable uf/region columns (else return None → plain names)."""
    p = data_dir / "data" / "territory_metadata.csv"
    if not p.is_file():
        return None
    m = pd.read_csv(p)
    if "uf" not in m.columns or "region" not in m.columns:
        return None
    if m["uf"].nunique(dropna=True) <= 1 and m["region"].nunique(dropna=True) <= 1:
        return None  # single-state set — place tag adds nothing
    out = {}
    for _, r in m.iterrows():
        uf = r["uf"] if isinstance(r.get("uf"), str) else "?"
        reg = REGION_ABBR.get(r.get("region"), "?")
        out[r["territory"]] = f"{agg._shorten(str(r['territory']), 24)} · {uf}·{reg}"
    return out


def chart_buffer_composition(lc, label, fig_dir: Path, label_map=None) -> Path:
    # Row order = core (territory) forest-formation order, so both charts align.
    _, tpct = _pct_pivot(lc, label, "territory")
    core_order = tpct.get("Forest Formation", tpct.iloc[:, 0]).sort_values(ascending=True).index.tolist()

    # Buffer composition: pick the buffer's own top-9 classes (its story is the
    # conversion the core avoids); colours are class-name keyed so they still match.
    bpivot, bpct = _pct_pivot(lc, label, "buffer")
    top = bpivot.sum().sort_values(ascending=False).head(9).index.tolist()
    other = [c for c in bpct.columns if c not in top]
    plot_df = bpct[top].copy()
    if other:
        plot_df["Other"] = bpct[other].sum(axis=1)

    order = [t for t in core_order if t in plot_df.index]
    plot_df = plot_df.loc[order]
    n = len(plot_df)

    fig, ax = plt.subplots(figsize=(12, max(4, 0.3 * n + 2)))
    left = np.zeros(n)
    for col in plot_df.columns:
        color = agg.MAPBIOMAS_NAME_COLOR.get(col, agg._MB_FALLBACK_COLOR)
        ax.barh(np.arange(n), plot_df[col], left=left, height=0.75, color=color,
                edgecolor="white", linewidth=0.3, label=col)
        left += plot_df[col].values
    ax.set_yticks(np.arange(n), [agg._disp(t, label_map) for t in plot_df.index], fontsize=7)
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"% of area — MapBiomas {YEAR2}")
    ax.set_title(f"Land-cover composition {YEAR2} — {label} (10 km buffer)")
    ax.legend(fontsize=7, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    path = fig_dir / f"landcover_composition_{YEAR2}_{agg._slug(label)}_buffer.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


ROOT = Path("/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report")
DATASETS = [
    # (data_dir, figures_dir, label)
    (ROOT, ROOT / "figures", "Indigenous Lands"),
    (ROOT, ROOT / "figures", "Conservation Units"),
    (ROOT / "national_forests", ROOT / "national_forests" / "figures",
     "Florestas e Parques Nacionais (Conservação federal, PA)"),
    (ROOT / "para_state", ROOT / "para_state" / "figures",
     "Unidades de Conservação do Pará (Conservação federal/estadual/municipal)"),
    (ROOT / "indigenous_selection", ROOT / "indigenous_selection" / "figures",
     "Indigenous Lands (Regularizada, 50–300k ha, off-border)"),
]


if __name__ == "__main__":
    for data_dir, fig_dir, label in DATASETS:
        lc = pd.read_csv(data_dir / "data" / "landcover_long.csv")
        labels = place_labels_from_meta(data_dir)  # None for single-state sets
        p = chart_buffer_composition(lc, label, fig_dir, labels)
        print("wrote", p)
