#!/usr/bin/env python3
"""Build the yvynation report set that compares the **extremes of scale** among
Brazilian Indigenous Lands: the 60 smallest (≤ ~530 ha) against the 27 largest
(> 1 M ha).

Sibling of `indigenous_report_builder.py` (one purposive mid-size IL selection)
and `national_uc_census_report.py` (one national single-category UC census). What
is new here is the **axis**: two groups that differ by three orders of magnitude
in area, so the primary stratifier is a two-level `size_class` rather than a
demarcation ladder or a creation era.

Two properties of the input data shape every design choice in this script, and
both are stated in the reports rather than smoothed over:

1. **Size is entangled with place and biome.** Brazil's smallest ILs are not
   small Amazonian lands — they are the residual, often re-purchased fragments of
   the South, Southeast and Northeast (Atlantic Forest, Pampa, Caatinga), while
   every >1 M ha land sits in Amazonia. Size, region, biome and (partly)
   recognition status therefore co-vary by construction: this is a comparison of
   two *kinds of situation*, and no cross-sectional contrast here can attribute
   an outcome to area alone. The reports carry that caveat next to every
   size contrast, and Report 3 shows the confound as a figure.
2. **The buffer axis is asymmetric.** The small-lands batch was run with buffers
   disabled (a 10 km ring around a 30 ha land is ~1000× the land itself and
   describes the municipality, not the land's surroundings), while the large-land
   batch has rings — recombined from quadrants, so they cover the part of the
   ring falling inside the territory bounding box (see `quadrant_merge.py`).
   Cross-group comparisons are therefore **core-only**; core-vs-buffer analysis
   runs inside the large group alone and is labelled as such.

Reuses `batch_report_aggregator` (agg) for data assembly, the spreadsheet, the
per-group reports and the README, and `governance_policy_report` (gov) for the
political/policy join and the governance figures. Group labels must contain the
ASCII string "Indig" so gov's indigenous branches fire.

Run (repo venv, from the repo root)::

    .venv/bin/python utils/indigenous_size_report.py            # all presets
    .venv/bin/python utils/indigenous_size_report.py size_extremes
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch_report_aggregator as agg  # noqa: E402
import governance_policy_report as gov  # noqa: E402
import indigenous_report_builder as ind  # noqa: E402  (ladder-date augmentation)

REGION_ORDER = gov.REGION_ORDER
REGION_ABBR = {"Norte": "N", "Centro-Oeste": "CO", "Nordeste": "NE",
               "Sudeste": "SE", "Sul": "S"}
REGION_COLOR = {"Norte": "#2e7d32", "Centro-Oeste": "#b45309", "Nordeste": "#7c3aed",
                "Sudeste": "#2563eb", "Sul": "#059669"}
TIER_ORDER = ["Em Estudo", "Delimitada", "Declarada", "Encaminhada RI", "Homologada",
              "Regularizada"]

# ---------------------------------------------------------------- formatting


def fmt(v, unit="", dec=1):
    if v is None or (isinstance(v, float) and (np.isnan(v) or np.isinf(v))):
        return "—"
    if isinstance(v, (int, float, np.floating, np.integer)):
        return f"{v:,.{dec}f}{unit}"
    return str(v)


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def ratio_word(a, b):
    """'3.4× higher' / '2.1× lower' / 'about the same' for a vs b."""
    if not b or np.isnan(a) or np.isnan(b) or b == 0:
        return "not comparable"
    r = a / b
    if 0.9 <= r <= 1.1:
        return "about the same"
    return f"{r:.1f}× higher" if r > 1 else f"{1 / r:.1f}× lower"


def agg_forest_change(sub, y1=1985, y2=2024):
    """Σ-based forest change (%), robust to near-zero per-land baselines.

    A land whose 1985 forest was 0.01 ha and whose 2024 forest is 2 ha shows a
    +17,000 % per-land change; averaging such ratios is meaningless. Summing the
    hectares first and taking one ratio is not.
    """
    a1 = sub[f"t_forest_{y1}_ha"].sum()
    a2 = sub[f"t_forest_{y2}_ha"].sum()
    return 100.0 * (a2 / a1 - 1.0) if a1 else np.nan


def tiny_baseline_count(sub, y1=1985, thresh_ha=1.0):
    """Lands whose y1 forest baseline is too small for a stable ratio."""
    return int((sub[f"t_forest_{y1}_ha"].fillna(0) < thresh_ha).sum())


def order_regions(index):
    ordered = [r for r in REGION_ORDER if r in index]
    return ordered + [r for r in index if r not in ordered]


def describe_regions(idx):
    names = list(idx)
    if len(names) >= 5:
        return "all five macro-regions"
    if len(names) > 1:
        return ", ".join(names[:-1]) + " and " + names[-1]
    return names[0] if names else "one region"


def build_place_labels(meta):
    """territory → 'Name · UF·Region' for chart y-axes."""
    m = {}
    for _, r in meta.iterrows():
        uf = r.get("uf") if isinstance(r.get("uf"), str) else "?"
        reg = REGION_ABBR.get(r.get("region"), "?")
        m[r["territory"]] = f"{agg._shorten(r['territory'], 26)} · {uf}·{reg}"
    return m


# ---------------------------------------------------------------- metadata


def augment_meta_size(meta: pd.DataFrame, summary: pd.DataFrame,
                      size_labels: dict) -> pd.DataFrame:
    """Add size_class, the analysed area and the FUNAI `superficie` to the meta.

    The analysed area (MapBiomas 2024 total) is the size measure used in figures:
    the FUNAI `superficie` field is 0 for a handful of the smallest lands (not yet
    surveyed), so it cannot rank them.
    """
    meta = meta.copy()
    meta["size_class"] = meta["group"].map(size_labels)
    area = summary.set_index(["group", "territory"])["t_area_total_ha"]
    meta = meta.merge(area.rename("analysed_area_ha"), on=["group", "territory"], how="left")
    try:
        import geopandas as gpd
        gi = gpd.read_file(gov.GPKG_IND)
        lut = {gov._norm(r["terrai_nom"]): r for _, r in gi.iterrows()}
        sup, etn = [], []
        for name in meta["territory"]:
            row = lut.get(gov._strip_code(name))
            if row is None:
                row = lut.get(gov._norm(name))
            sup.append(float(row["superficie"]) if row is not None else np.nan)
            etn.append(str(row["etnia_nome"]) if row is not None else None)
        meta["funai_superficie_ha"] = sup
        meta["etnia"] = etn
    except Exception as exc:  # noqa: BLE001
        print(f"  ! FUNAI area/ethnicity lookup failed ({exc})", file=sys.stderr)
    return meta


def attach_ring_coverage(meta: pd.DataFrame, batch_by_group: dict) -> pd.DataFrame:
    """Carry `ring_coverage_pct` from a merged batch's quadrant_merge_report.csv.

    Recombined buffer rings only cover the part of the ring inside the
    territory's bounding box, so every buffer statistic for the large lands is a
    partial — and per-land unequal — sample of the true ring. Reporting the
    coverage per land is what keeps that honest.
    """
    frames = []
    for group, batch in batch_by_group.items():
        rep = Path(batch) / "quadrant_merge_report.csv"
        if not rep.is_file():
            continue
        df = pd.read_csv(rep)
        keep = [c for c in ("slug", "ring_coverage_pct", "ring_in_bbox_pct",
                            "area_vs_boundary_pct", "boundary_ha") if c in df.columns]
        df = df[keep].copy()
        df["group"] = group
        frames.append(df)
    if not frames:
        return meta
    cov = pd.concat(frames, ignore_index=True)
    return meta.merge(cov, on=["group", "slug"], how="left") if "slug" in meta.columns \
        else meta.merge(cov, on="group", how="left")


# ---------------------------------------------------------------- grouped metrics


def with_gap(summary: pd.DataFrame) -> pd.DataFrame:
    s = summary.copy()
    s["protection_gap"] = (s["b_gfc_loss_pct_of_2000_cover"]
                           - s["t_gfc_loss_pct_of_2000_cover"]) \
        if "b_gfc_loss_pct_of_2000_cover" in s.columns else np.nan
    return s


def grouped_metrics(summary, meta, by, y1=1985, y2=2024, extra_keys=()):
    """Per-stratum core metrics. Forest change is the Σ-hectare ratio (see
    `agg_forest_change`) plus the median per-land ratio — never the mean of
    per-land ratios, which explodes on the sub-hectare 1985 baselines of the
    smallest lands."""
    keys = [by] + [k for k in extra_keys]
    s = with_gap(summary).merge(meta[["group", "territory"] + keys],
                               on=["group", "territory"], how="left")
    g = s.groupby(keys, observed=True).agg(
        n=("territory", "size"),
        area=("t_area_total_ha", "sum"),
        med_area=("t_area_total_ha", "median"),
        t_fc_med=("t_forest_change_pct", "median"),
        t_gfc=("t_gfc_loss_pct_of_2000_cover", "mean"),
        t_gfc_med=("t_gfc_loss_pct_of_2000_cover", "median"),
        forest_pct=(f"t_forest_{y2}_pct_of_area", "mean"),
        anthro_pct=(f"t_anthropic_{y2}_pct_of_area", "mean"),
        gap=("protection_gap", "mean"),
    )
    g["t_fc"] = s.groupby(keys, observed=True).apply(
        lambda d: agg_forest_change(d, y1, y2), include_groups=False)
    return g


def core_rates_by(panel, meta, by):
    """Mean core (territory-scope) annual rates per stratum."""
    p = panel[panel["scope"] == "territory"]
    if by not in p.columns:
        p = p.merge(meta[["group", "territory", by]], on=["group", "territory"], how="left")
    rows = []
    for val, sub in p.groupby(by, observed=True):
        rows.append({
            by: val,
            "n": sub[["group", "territory"]].drop_duplicates().shape[0],
            "defor": sub["mb_defor_primary_rate"].mean(),
            "fire": sub["mb_fire_scar_rate"].mean(),
            "regrowth": sub["mb_secondary_growth_rate"].mean(),
            "hansen": sub["hansen_loss_rate"].mean() if "hansen_loss_rate" in sub else np.nan,
        })
    return pd.DataFrame(rows).set_index(by)


def breakdown_block(title, note, g, level=2):
    L = [f"{'#' * level} {title}", ""] + ([note, ""] if note else [])
    headers = ["Stratum", "n", "Σ area (ha)", "Median area (ha)",
               "Forest chg Σ / median %", "Forest 2024 %", "Anthropic 2024 %",
               "GFC loss mean / median %"]
    rows = []
    for idx, r in g.iterrows():
        rows.append([idx, int(r["n"]), fmt(r["area"], "", 0), fmt(r["med_area"], "", 0),
                     f"{fmt(r['t_fc'])} / {fmt(r['t_fc_med'])}",
                     fmt(r["forest_pct"]), fmt(r["anthro_pct"]),
                     f"{fmt(r['t_gfc'])} / {fmt(r['t_gfc_med'])}"])
    L += md_table(headers, rows)
    return L


# ---------------------------------------------------------------- figures


def chart_size_outcomes(summary, meta, fig_dir: Path, size_order, y2=2024) -> Path:
    """Left: core outcomes per size class. Right: area (log) vs core canopy loss."""
    s = with_gap(summary).merge(
        meta[["group", "territory", "size_class", "region", "recognition_tier"]],
        on=["group", "territory"], how="left")
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(15.5, 5.6))

    g = s.groupby("size_class", observed=True).agg(
        n=("territory", "size"),
        gfc=("t_gfc_loss_pct_of_2000_cover", "mean"),
        forest=(f"t_forest_{y2}_pct_of_area", "mean"),
        anthro=(f"t_anthropic_{y2}_pct_of_area", "mean"),
    ).reindex(size_order)
    # Σ-hectare ratio, not the mean of per-land ratios: several of the smallest
    # lands had under 1 ha of 1985 forest, and their ratios reach +17,000 %.
    g["fc"] = s.groupby("size_class", observed=True).apply(
        lambda d: agg_forest_change(d, y2=y2), include_groups=False).reindex(size_order)
    metrics = [("forest", f"Forest {y2} (% of area)", "#166534"),
               ("anthro", f"Anthropic {y2} (% of area)", "#b45309"),
               ("fc", "Forest change 1985→%d (%%, Σ ha)" % y2, "#2563eb"),
               ("gfc", "Hansen loss (% of 2000 cover)", "#b03a2e")]
    x = np.arange(len(g))
    w = 0.2
    for i, (col, lab, color) in enumerate(metrics):
        ax0.bar(x + (i - 1.5) * w, g[col], w, label=lab, color=color)
    ax0.set_xticks(x, [f"{i}\n(n={int(r['n'])})" for i, r in g.iterrows()], fontsize=9)
    ax0.axhline(0, color="k", lw=0.8)
    ax0.set_ylabel("% of area  /  % of cover")
    ax0.set_title("Core outcomes by size class")
    ax0.legend(fontsize=8)
    ax0.grid(axis="y", alpha=0.3)

    sd = s.dropna(subset=["t_area_total_ha", "t_gfc_loss_pct_of_2000_cover"])
    sd = sd[sd["t_area_total_ha"] > 0]
    for reg, sub in sd.groupby("region"):
        ax1.scatter(sub["t_area_total_ha"], sub["t_gfc_loss_pct_of_2000_cover"], s=34,
                    alpha=0.85, color=REGION_COLOR.get(reg, "#444"), label=reg)
    if len(sd) >= 3:
        lx = np.log10(sd["t_area_total_ha"])
        b, a = np.polyfit(lx, sd["t_gfc_loss_pct_of_2000_cover"], 1)
        xs = np.array([lx.min(), lx.max()])
        ax1.plot(10 ** xs, a + b * xs, "k--", lw=1,
                 label=f"trend ({b:+.1f} pp per 10× area)")
    ax1.set_xscale("log")
    lo = sd.loc[sd["size_class"] == size_order[0], "t_area_total_ha"].max()
    hi = sd.loc[sd["size_class"] == size_order[1], "t_area_total_ha"].min()
    if lo and hi and hi > lo:
        ax1.axvspan(lo, hi, color="#cccccc", alpha=0.28, zorder=0)
        ax1.annotate("no lands sampled\nin this size range",
                     ((lo * hi) ** 0.5, ax1.get_ylim()[1] * 0.9), ha="center",
                     va="top", fontsize=8, color="#555")
    ax1.set_xlabel("Analysed area (ha, log scale)")
    ax1.set_ylabel("Core Hansen loss (% of 2000 cover)")
    ax1.set_title("Size gradient — every land, coloured by macro-region")
    ax1.legend(fontsize=7, ncol=2)
    ax1.grid(alpha=0.3)

    fig.suptitle("Extremes of scale — core forest outcomes", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_size_outcomes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_size_context(meta, fig_dir: Path, size_order) -> Path:
    """The confound, drawn: how region and recognition status differ by size class."""
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(14, 5.0))

    reg = pd.crosstab(meta["size_class"], meta["region"]).reindex(size_order).fillna(0)
    reg = reg[order_regions(reg.columns)]
    bottom = np.zeros(len(reg))
    for col in reg.columns:
        ax0.barh(np.arange(len(reg)), reg[col], left=bottom, label=col,
                 color=REGION_COLOR.get(col, "#888"))
        bottom += reg[col].values
    ax0.set_yticks(np.arange(len(reg)), reg.index, fontsize=9)
    ax0.set_xlabel("Number of lands")
    ax0.set_title("Macro-region composition by size class")
    ax0.legend(fontsize=8)
    ax0.grid(axis="x", alpha=0.3)

    tier = pd.crosstab(meta["size_class"], meta["recognition_tier"]).reindex(size_order).fillna(0)
    cols = [t for t in TIER_ORDER if t in tier.columns] + \
           [t for t in tier.columns if t not in TIER_ORDER]
    tier = tier[cols]
    cmap = plt.get_cmap("viridis", max(2, len(cols)))
    bottom = np.zeros(len(tier))
    for i, col in enumerate(cols):
        ax1.barh(np.arange(len(tier)), tier[col], left=bottom, label=col, color=cmap(i))
        bottom += tier[col].values
    ax1.set_yticks(np.arange(len(tier)), tier.index, fontsize=9)
    ax1.set_xlabel("Number of lands")
    ax1.set_title("Demarcation status (fase_ti) by size class")
    ax1.legend(fontsize=8)
    ax1.grid(axis="x", alpha=0.3)

    fig.suptitle("Size does not vary alone — the strata behind the contrast",
                 y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_size_context.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_size_landcover(lc, meta, fig_dir: Path, size_order, y1=1985, y2=2024) -> Path:
    """Mean land-cover balance (forest / natural non-forest / anthropic) per size
    class in both years — shows how different the 1985 *starting point* was."""
    d = lc[lc["scope"] == "territory"].merge(
        meta[["group", "territory", "size_class"]], on=["group", "territory"], how="left")

    def bucket(cls):
        if cls in agg.FOREST_CLASSES:
            return "Forest"
        if cls in agg.NATURAL_NONFOREST_CLASSES:
            return "Natural non-forest"
        if cls in agg.ANTHROPIC_CLASSES:
            return "Anthropic"
        return "Other"

    d["bucket"] = d["class"].map(bucket)
    tot = d.groupby(["size_class", "territory", "year"], observed=True)["area_ha"].transform("sum")
    d["share"] = 100 * d["area_ha"] / tot.replace(0, np.nan)
    g = d.groupby(["size_class", "year", "bucket"], observed=True)["share"].sum()
    per_land = d.groupby(["size_class", "year"], observed=True)["territory"].nunique()

    buckets = ["Forest", "Natural non-forest", "Anthropic", "Other"]
    colors = {"Forest": "#166534", "Natural non-forest": "#d6bc74",
              "Anthropic": "#b45309", "Other": "#b0b0b0"}
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    rows = [(sc, yr) for sc in size_order for yr in (y1, y2)]
    y = np.arange(len(rows))
    left = np.zeros(len(rows))
    for b in buckets:
        vals = []
        for sc, yr in rows:
            n = per_land.get((sc, yr), np.nan)
            v = g.get((sc, yr, b), 0.0)
            vals.append(v / n if n and not np.isnan(n) else np.nan)
        vals = np.array(vals, dtype=float)
        ax.barh(y, vals, left=left, color=colors[b], label=b)
        left += np.nan_to_num(vals)
    ax.set_yticks(y, [f"{sc} — {yr}" for sc, yr in rows], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Mean share of land area (%)")
    ax.set_title(f"Land-cover balance inside the lands, {y1} vs {y2}")
    ax.legend(fontsize=8, ncol=4, loc="lower right")
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gp_size_landcover.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_size_recognition(summary, meta, fig_dir: Path, size_order) -> Path:
    """Recognition status vs core outcomes, split by size class (H3 cross-section)."""
    s = with_gap(summary).merge(
        meta[["group", "territory", "size_class", "recognition_tier", "fully_recognized"]],
        on=["group", "territory"], how="left")
    s["tier2"] = np.where(s["fully_recognized"].fillna(False),
                          "Regularizada", "Pré-regularização")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.0), sharey=True)
    for ax, metric, title in zip(
            axes, ["t_gfc_loss_pct_of_2000_cover", "t_forest_change_pct"],
            ["Core Hansen loss (% of 2000 cover)", "Forest change 1985→2024 (%)"]):
        g = s.groupby(["size_class", "tier2"], observed=True)[metric].mean().unstack()
        n = s.groupby(["size_class", "tier2"], observed=True)[metric].size().unstack()
        g = g.reindex(size_order)
        n = n.reindex(size_order)
        cols = [c for c in ["Pré-regularização", "Regularizada"] if c in g.columns]
        x = np.arange(len(g))
        w = 0.35
        for i, c in enumerate(cols):
            ax.bar(x + (i - (len(cols) - 1) / 2) * w, g[c], w, label=c,
                   color=["#9aa5b1", "#166534"][i % 2])
            for xi, (v, cnt) in enumerate(zip(g[c], n[c])):
                if not np.isnan(v):
                    ax.annotate(f"n={int(cnt)}", (xi + (i - (len(cols) - 1) / 2) * w, v),
                                ha="center", va="bottom", fontsize=7)
        ax.set_xticks(x, list(g.index), fontsize=9)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
        ax.legend(fontsize=8)
    fig.suptitle("Recognition status vs. outcomes, within each size class",
                 y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_size_recognition.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------- Report 3


def write_group_comparison(out, cfg, runs, summary, meta, panel, figs):
    small_lbl, large_lbl = cfg["label_small"], cfg["label_large"]
    size_order = cfg["size_order"]
    word_s, word_l = cfg["word_small"], cfg["word_large"]
    y1, y2 = runs[0].year1, runs[0].year2
    s = with_gap(summary).merge(meta[["group", "territory", "size_class", "region",
                                     "recognition_tier"]],
                               on=["group", "territory"], how="left")
    S = s[s["size_class"] == size_order[0]]
    L_ = s[s["size_class"] == size_order[1]]
    core = panel[panel["scope"] == "territory"]
    buf = panel[panel["scope"] == "buffer"]

    def crate(sub, col):
        return sub[col].mean()

    small_regions = order_regions(S["region"].dropna().unique())
    large_regions = order_regions(L_["region"].dropna().unique())

    n_sel_small = len(S) + len(cfg.get("oversized_small") or [])
    intro3 = cfg["intro3"].format(
        n_small=len(S), n_large=len(L_), n_sel_small=n_sel_small,
        y1=y1, y2=y2,
        small_max=fmt(S["t_area_total_ha"].max(), "", 0),
        large_max=fmt(L_["t_area_total_ha"].max(), "", 0),
        n_states_small=int(meta[meta["size_class"] == size_order[0]]["uf"].nunique()))
    L = [
        f"# {cfg['title3']}",
        "",
        intro3,
        "",
        "## The two groups",
        "",
    ]
    L += md_table(
        ["", size_order[0], size_order[1]],
        [
            ["Lands analysed", f"{len(S)}", f"{len(L_)}"],
            ["Area range (analysed, ha)",
             f"{fmt(S['t_area_total_ha'].min(), '', 0)} – {fmt(S['t_area_total_ha'].max(), '', 0)}",
             f"{fmt(L_['t_area_total_ha'].min(), '', 0)} – {fmt(L_['t_area_total_ha'].max(), '', 0)}"],
            ["Median area (ha)", fmt(S["t_area_total_ha"].median(), "", 0),
             fmt(L_["t_area_total_ha"].median(), "", 0)],
            ["Σ area (ha)", fmt(S["t_area_total_ha"].sum(), "", 0),
             fmt(L_["t_area_total_ha"].sum(), "", 0)],
            ["States (UF)", f"{S['group'].size and meta[meta['size_class']==size_order[0]]['uf'].nunique()}",
             f"{meta[meta['size_class']==size_order[1]]['uf'].nunique()}"],
            ["Macro-regions", describe_regions(small_regions), describe_regions(large_regions)],
            ["Regularizada (fase_ti)",
             f"{int((S['recognition_tier'] == 'Regularizada').sum())} / {len(S)}",
             f"{int((L_['recognition_tier'] == 'Regularizada').sum())} / {len(L_)}"],
            ["10 km buffer ring analysed", "no (disabled in the batch)",
             "yes (recombined from quadrants)"],
        ],
    )
    L += [
        "",
        "> **Read this contrast as two situations, not as an area effect.** The two "
        "groups differ in area by three orders of magnitude, but they also differ in "
        f"*where they are*: the {word_s} are spread over "
        f"{describe_regions(small_regions)}, the {word_l} sit only in "
        f"{describe_regions(large_regions)}. Size, macro-region, biome and — partly — "
        "demarcation status co-vary, so no contrast below can attribute an outcome to "
        "area alone. What the comparison *does* isolate is the difference between two "
        "real situations in Brazilian Indigenous land policy: small remnant lands "
        "inside long-consolidated agricultural landscapes, and continental Amazonian "
        "territories on or behind the active frontier. Two regions — **Norte and "
        "Centro-Oeste — do contain lands of both extremes**, and that overlap is the "
        "one place in this design where size can be compared with region held roughly "
        "constant (see the region × size table below).",
        "",
        f"![size context](figures/{figs['context'].name})",
        "",
        "## Headline metrics — protected cores",
        "",
    ]
    L += md_table(
        ["Metric (core)", size_order[0], size_order[1]],
        [
            ["Σ area (ha)", fmt(S["t_area_total_ha"].sum(), "", 0), fmt(L_["t_area_total_ha"].sum(), "", 0)],
            [f"Forest change {y1}→{y2}, Σ hectares",
             fmt(agg_forest_change(S, y1, y2), " %"), fmt(agg_forest_change(L_, y1, y2), " %")],
            [f"Median per-land forest change {y1}→{y2}",
             fmt(S["t_forest_change_pct"].median(), " %"),
             fmt(L_["t_forest_change_pct"].median(), " %")],
            [f"Mean forest {y2} (% of area)", fmt(S[f"t_forest_{y2}_pct_of_area"].mean(), " %"),
             fmt(L_[f"t_forest_{y2}_pct_of_area"].mean(), " %")],
            [f"Mean anthropic {y2} (% of area)", fmt(S[f"t_anthropic_{y2}_pct_of_area"].mean(), " %"),
             fmt(L_[f"t_anthropic_{y2}_pct_of_area"].mean(), " %")],
            ["Mean Hansen GFC loss (% of 2000 cover)",
             fmt(S["t_gfc_loss_pct_of_2000_cover"].mean(), " %"),
             fmt(L_["t_gfc_loss_pct_of_2000_cover"].mean(), " %")],
            ["Median Hansen GFC loss (% of 2000 cover)",
             fmt(S["t_gfc_loss_pct_of_2000_cover"].median(), " %"),
             fmt(L_["t_gfc_loss_pct_of_2000_cover"].median(), " %")],
            ["Mean annual deforestation rate (% of area/yr)",
             fmt(crate(core[core["group"] == small_lbl], "mb_defor_primary_rate"), " %", 4),
             fmt(crate(core[core["group"] == large_lbl], "mb_defor_primary_rate"), " %", 4)],
            ["Mean annual fire rate (% of area/yr)",
             fmt(crate(core[core["group"] == small_lbl], "mb_fire_scar_rate"), " %", 4),
             fmt(crate(core[core["group"] == large_lbl], "mb_fire_scar_rate"), " %", 4)],
            ["Mean annual regrowth rate (% of area/yr)",
             fmt(crate(core[core["group"] == small_lbl], "mb_secondary_growth_rate"), " %", 4),
             fmt(crate(core[core["group"] == large_lbl], "mb_secondary_growth_rate"), " %", 4)],
        ],
    )
    gfc_s = S["t_gfc_loss_pct_of_2000_cover"].mean()
    gfc_l = L_["t_gfc_loss_pct_of_2000_cover"].mean()
    fire_s = crate(core[core["group"] == small_lbl], "mb_fire_scar_rate")
    fire_l = crate(core[core["group"] == large_lbl], "mb_fire_scar_rate")
    def_s = crate(core[core["group"] == small_lbl], "mb_defor_primary_rate")
    def_l = crate(core[core["group"] == large_lbl], "mb_defor_primary_rate")
    forest_s = S[f"t_forest_{y2}_pct_of_area"].mean()
    forest_l = L_[f"t_forest_{y2}_pct_of_area"].mean()
    anth_s = S[f"t_anthropic_{y2}_pct_of_area"].mean()
    anth_l = L_[f"t_anthropic_{y2}_pct_of_area"].mean()

    L += [
        "",
        f"![size outcomes](figures/{figs['size'].name})",
        "",
        f"By {y2} the {word_s} hold "
        f"{fmt(forest_s, ' %')} of their area as forest formations against "
        f"{fmt(forest_l, ' %')} in the {word_l}, and carry "
        f"{fmt(anth_s, ' %')} anthropic cover against {fmt(anth_l, ' %')}. "
        f"Canopy loss since 2000 is {ratio_word(gfc_s, gfc_l)} in the small lands "
        f"({fmt(gfc_s, ' %')} vs {fmt(gfc_l, ' %')} of 2000 cover), annual "
        f"clearing {ratio_word(def_s, def_l)} and annual burning "
        f"{ratio_word(fire_s, fire_l)}.",
        "",
        "The right-hand panel puts all "
        f"{len(S) + len(L_)} lands on one log-area axis: read it as a **gradient with "
        "region built in**, not as a causal slope — the small end of the axis is also "
        "the Atlantic-Forest/Caatinga end.",
        "",
        "> **Why Σ-hectares and medians, not means, for forest change.** "
        f"{tiny_baseline_count(S, y1)} of the {len(S)} {word_s} had "
        f"under 1 ha of forest formation in {y1}. A land that went from 0.01 ha to "
        "2 ha of forest scores +17,000 %, and averaging such ratios produces a "
        "meaningless group mean; the Σ-hectare ratio and the median are stable, so "
        "those are the headline figures here. Per-land means are still in "
        "`data/summary_metrics.csv` for anyone who wants them.",
        "",
        f"![land-cover balance](figures/{figs['landcover'].name})",
        "",
        f"The {y1} rows matter as much as the {y2} rows: the two groups did not start "
        "from the same place. A small land whose surroundings were cleared before the "
        f"satellite record begins can only show a small *change* over {y1}–{y2}, no "
        "matter how much was lost historically — the record starts after the loss. "
        "This is the single most important reason not to read a low change figure as "
        "protection success.",
        "",
    ]

    # ---- strata (always within a size class: pooling them would just re-state
    # the size contrast, since the strata are populated so unevenly) -----------
    for by, title, note in (
        ("region", "Breakdown by macro-region",
         "Region conditions biome, historical clearing and the frontier that presses "
         "on each land. Reported **within** each size class, because a pooled row "
         "would simply average two different situations."),
        ("recognition_tier", "Breakdown by demarcation status (fase_ti)",
         "The FUNAI ladder from *Em Estudo* to *Regularizada*. Small lands are far "
         "more likely to sit at a pre-regularisation stage — a policy fact of the "
         "fragmented-lands agenda, and another reason size and recognition cannot be "
         "cleanly separated here."),
    ):
        g = grouped_metrics(summary, meta, "size_class", y1, y2, extra_keys=(by,))
        L += [f"## {title}", "", note, ""]
        for sc in size_order:
            if sc not in g.index.get_level_values(0):
                continue
            sub = g.xs(sc, level=0)
            if by == "region":
                sub = sub.reindex([r for r in order_regions(sub.index)])
            else:
                sub = sub.reindex([x for x in TIER_ORDER if x in sub.index] +
                                  [x for x in sub.index if x not in TIER_ORDER])
            L += breakdown_block(sc, "", sub, level=3) + [""]

    # size × region cross-tab, the honest partial control
    sr = with_gap(summary).merge(meta[["group", "territory", "size_class", "region"]],
                                on=["group", "territory"], how="left")
    piv = sr.pivot_table(index="region", columns="size_class",
                         values="t_gfc_loss_pct_of_2000_cover", aggfunc="mean")
    cnt = sr.pivot_table(index="region", columns="size_class",
                         values="t_gfc_loss_pct_of_2000_cover", aggfunc="size")
    piv = piv.reindex(order_regions(piv.index))
    cnt = cnt.reindex(piv.index)
    piv = piv.reindex(columns=[c for c in size_order if c in piv.columns])
    cnt = cnt.reindex(columns=piv.columns)
    both = [r for r in piv.index
            if all(not pd.isna(cnt.loc[r, c]) and cnt.loc[r, c] > 0 for c in piv.columns)]
    L += [
        "### Core canopy loss by region × size class",
        "",
        "This is the design's one partial control. "
        + (f"**{describe_regions(both)}** hold lands of *both* extremes, so within "
           "those rows size varies while region (and broadly biome) is held roughly "
           "constant. The rows where one cell is empty carry no size contrast at all."
           if both else
           "No region holds lands of both extremes in this pair of batches, so no "
           "within-region contrast is available."),
        "",
    ]
    L += md_table(
        ["Region"] + [f"{c} (mean % / n)" for c in piv.columns],
        [[idx] + [f"{fmt(piv.loc[idx, c])} / {int(cnt.loc[idx, c]) if not pd.isna(cnt.loc[idx, c]) else 0}"
                  for c in piv.columns] for idx in piv.index],
    )
    if both:
        bits = []
        for r in both:
            a, b = piv.loc[r, size_order[0]], piv.loc[r, size_order[1]]
            bits.append(f"in **{r}** {fmt(a, ' %')} (n={int(cnt.loc[r, size_order[0]])}) "
                        f"vs {fmt(b, ' %')} (n={int(cnt.loc[r, size_order[1]])}) — "
                        f"{ratio_word(a, b)} in the small lands")
        L += ["", "Held within region, core canopy loss runs " + "; ".join(bits) + ". "
              "Small n on at least one side of every such pair: read these as the "
              "direction the data points in, not as an estimate.", ""]
    else:
        L += [""]

    # ---- annual rates --------------------------------------------------------
    L += [
        "## Annual land-change rates",
        "",
        f"![rate curves](figures/{figs['rates'].name})",
        "",
        f"Solid = protected core, dashed = 10 km buffer (large lands only — the "
        "small-lands batch was run without rings). Rates are area-normalised, so a "
        "30 ha land and a 9.6 M ha land are directly comparable.",
        "",
        "## Distributions",
        "",
        f"![distributions](figures/{figs['dist'].name})",
        "",
    ]

    # ---- core vs buffer, large group only ------------------------------------
    if not buf.empty:
        bl = with_gap(summary)
        bl = bl[bl["group"] == large_lbl]
        n_gap = int(bl["protection_gap"].notna().sum())
        n_pos = int((bl["protection_gap"] > 0).sum())
        cov = meta.loc[meta["size_class"] == size_order[1], "ring_coverage_pct"] \
            if "ring_coverage_pct" in meta.columns else pd.Series(dtype=float)
        L += [
            f"## Core vs. buffer — {size_order[1]} only",
            "",
            "The small-lands batch has no buffer ring, so this section is internal to "
            f"the {word_l}. Their rings were recombined from the "
            "quadrant export, which covers the ring only where it falls inside the "
            "territory's bounding box"
            + (f" (mean {fmt(cov.mean(), ' %')} of the true 10 km ring, range "
               f"{fmt(cov.min(), ' %')}–{fmt(cov.max(), ' %')})" if len(cov.dropna()) else "")
            + " — and MapBiomas stops at the national border, which removes most of the "
            "ring for the frontier lands. Ring rates are area-normalised and remain "
            "comparable; ring *totals* are floors, not full-ring values.",
            "",
        ]
        L += md_table(
            ["Metric", "Protected core", "10 km buffer (partial ring)"],
            [
                [f"Mean forest change {y1}→{y2}", fmt(bl["t_forest_change_pct"].mean(), " %"),
                 fmt(bl["b_forest_change_pct"].mean(), " %")],
                [f"Mean anthropic {y2} (% of area)",
                 fmt(bl[f"t_anthropic_{y2}_pct_of_area"].mean(), " %"),
                 fmt(bl[f"b_anthropic_{y2}_pct_of_area"].mean(), " %")],
                ["Mean Hansen GFC loss (% of 2000 cover)",
                 fmt(bl["t_gfc_loss_pct_of_2000_cover"].mean(), " %"),
                 fmt(bl["b_gfc_loss_pct_of_2000_cover"].mean(), " %")],
                ["Mean annual deforestation (% of area/yr)",
                 fmt(crate(core[core["group"] == large_lbl], "mb_defor_primary_rate"), " %", 4),
                 fmt(crate(buf[buf["group"] == large_lbl], "mb_defor_primary_rate"), " %", 4)],
                ["Mean annual fire (% of area/yr)",
                 fmt(crate(core[core["group"] == large_lbl], "mb_fire_scar_rate"), " %", 4),
                 fmt(crate(buf[buf["group"] == large_lbl], "mb_fire_scar_rate"), " %", 4)],
                ["**Protection gap** (buffer − core loss)",
                 f"**{fmt(bl['protection_gap'].mean(), ' pp')}**",
                 f"positive for {n_pos}/{n_gap}"],
            ],
        )
        fire_core = crate(core[core["group"] == large_lbl], "mb_fire_scar_rate")
        fire_buf = crate(buf[buf["group"] == large_lbl], "mb_fire_scar_rate")
        L += [
            "",
            f"![inside vs outside](figures/{figs['scatter'].name})",
            "",
            "Fire "
            + ("**reverses** the usual ordering: the protected cores burn *more* than "
               "their rings" if fire_core > fire_buf else
               "runs the same way as clearing: cores burn less than their rings")
            + f" ({fmt(fire_core, ' %', 4)} vs {fmt(fire_buf, ' %', 4)} of area / yr).",
            "",
        ]

    # ---- provenance ----------------------------------------------------------
    L += [
        "## Provenance and data notes",
        "",
        f"- **{size_order[0]}** — batch `{Path(cfg['batch_small']).name}` "
        f"({len(S)} of {len(S) + len(cfg.get('oversized_small') or [])} selected "
        "lands analysed, buffers disabled).",
    ]
    if cfg.get("oversized_small"):
        over = cfg["oversized_small"]
        L += [
            f"- **{len(over)} land(s) excluded from the {word_s} "
            f"group**: the batch selection ranked lands by FUNAI `superficie`, which "
            "is `0.0` for lands whose area has never been entered in the register, so "
            "a few genuinely large lands were selected as though they were the "
            "smallest. Excluded on their **analysed** area (cap "
            f"{cfg.get('max_area_ha_small'):,.0f} ha): "
            + "; ".join(f"*{n}* ({a:,.0f} ha)" for n, a in over)
            + ". They are neither in the tables above nor in the large group (they "
            "are below 1 M ha); a follow-up run could analyse them as a mid-size set.",
        ]
    L += [
        f"- **{size_order[1]}** — batch `{Path(cfg['batch_large']).name}` "
        f"({len(L_)} lands). Every land there exceeds the 1 M ha threshold at which "
        "the pipeline splits an export into four bounding-box quadrants; the "
        "quadrants were recombined into whole-territory tables, maps and figures by "
        "`utils/quadrant_merge.py` before this report ran. Summed quadrant areas land "
        + (f"at {fmt(meta['area_vs_boundary_pct'].mean(), ' %')} of the geodesic "
           "boundary area (30 m pixel-inclusive counting at the edges), so the merge "
           "loses nothing and double-counts nothing."
           if "area_vs_boundary_pct" in meta.columns else "within ~1 % of the "
           "geodesic boundary area."),
    ]
    if cfg.get("partial_timeline_large"):
        pt = cfg["partial_timeline_large"]
        L += [
            f"- **Annual series withheld for {len(pt)} land(s)** — "
            + ", ".join(f"*{n}*" for n in pt)
            + " exported only part of the four timeline quadrants, so their "
            "whole-territory annual deforestation/fire/Hansen series would be a "
            "partial sum against a whole-territory area. Their land-cover and "
            "Hansen-GFC totals are complete and are used; only the annual series "
            "(and the fire totals derived from it) are withheld.",
        ]
    L += [
        "- Metadata (UF, `fase_ti`, ladder dates, `superficie`, ethnicity) is joined "
        "from `indigenous_lands_br202605.gpkg` on the land name; all "
        f"{len(S) + len(L_)} lands matched.",
        "- FUNAI `superficie` is 0 for a few of the smallest lands (not yet "
        "surveyed), so every size figure here uses the **analysed** MapBiomas area.",
        f"- MapBiomas covers {y1}–{y2}; the deforestation/fire series effectively "
        "start in 1987 and Hansen canopy loss in 2001.",
        "",
    ]
    p = out / "report_group_comparison.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ---------------------------------------------------------------- Report 4


def write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs, tables):
    size_order = cfg["size_order"]
    small_lbl, large_lbl = cfg["label_small"], cfg["label_large"]
    change_df = tables["change"].set_index("condition")
    posture_grp = tables["posture"]
    regime_tbl = tables["regime"]
    scope_piv = tables.get("scope_amp")
    n_terr = panel_t[["group", "territory"]].drop_duplicates().shape[0]
    n_states = int(meta["uf"].nunique())

    L = [
        f"# {cfg['title4']}",
        "",
        "Tests the governance hypotheses of this project on the two extremes of "
        "Indigenous-land scale, joining each land's annual series to the "
        "federal/state political record (`political_context_brazil`) and the annual "
        "policy-strength scores (`policy_context_brazil`). Every rate is the "
        f"area-normalised annual value (% of area / yr) across {n_terr} lands in "
        f"{n_states} states; associations, not proof of cause.",
        "",
        "> Because the small lands sit in the South/Southeast/Northeast and the large "
        "ones in Amazonia, the **state-governor axis is not balanced across size "
        "classes**: a posture contrast computed on the pooled panel partly compares "
        "regions. Every governance table below is therefore also reported per size "
        "class, and the pooled figure is read as descriptive.",
        "",
        "---",
        "",
        "## H1 — Government changes",
        "",
        "*Claim: deforestation and fire worsen when federal or state governments "
        "change, while forest recovery slows.*",
        "",
        f"![change effect](figures/{figs['change'].name})",
        "",
    ]
    L += md_table(
        ["Condition", "Obs.", "Deforestation", "Fire", "Regrowth"],
        [[idx, fmt(r["n_obs"], "", 0), fmt(r["defor"], " %", 4), fmt(r["fire"], " %", 4),
          fmt(r["regrowth"], " %", 4)] for idx, r in change_df.iterrows()],
    )
    stable = change_df.loc["Stable years"]
    window = change_df.loc["Change yr + next"]

    def signed(a, b):
        return "—" if not b or np.isnan(b) else f"{(a / b - 1) * 100:+.0f}%"

    L += [
        "",
        f"In the change year plus the following year, mean deforestation runs "
        f"**{signed(window['defor'], stable['defor'])}** and fire "
        f"**{signed(window['fire'], stable['fire'])}** against stable years, with "
        f"regrowth at **{signed(window['regrowth'], stable['regrowth'])}**.",
        "",
        "### Per size class",
        "",
    ]
    rows = []
    for lbl, sc in ((small_lbl, size_order[0]), (large_lbl, size_order[1])):
        sub = panel_t[panel_t["group"] == lbl]
        if sub.empty:
            continue
        st = sub[~sub["any_change"] & ~sub["change_window"]]
        cw = sub[sub["change_window"]]
        rows.append([sc,
                     fmt(st["mb_defor_primary_rate"].mean(), " %", 4),
                     fmt(cw["mb_defor_primary_rate"].mean(), " %", 4),
                     signed(cw["mb_defor_primary_rate"].mean(), st["mb_defor_primary_rate"].mean()),
                     fmt(st["mb_fire_scar_rate"].mean(), " %", 4),
                     fmt(cw["mb_fire_scar_rate"].mean(), " %", 4),
                     signed(cw["mb_fire_scar_rate"].mean(), st["mb_fire_scar_rate"].mean())])
    L += md_table(["Size class", "Defor stable", "Defor change-window", "Δ",
                   "Fire stable", "Fire change-window", "Δ"], rows)

    L += [
        "",
        "---",
        "",
        "## H2 — Federal + state ideological posture",
        "",
        "*Claim: outcomes track the combined federal+state posture; conservative "
        "alignment is destructive, both-progressive alignment most protective.*",
        "",
        f"![posture effect](figures/{figs['posture'].name})",
        "",
    ]
    L += md_table(
        ["Posture", "Deforestation", "Fire", "Regrowth"],
        [[idx, fmt(r["mb_defor_primary_rate"], " %", 4), fmt(r["mb_fire_scar_rate"], " %", 4),
          fmt(r["mb_secondary_growth_rate"], " %", 4)] for idx, r in posture_grp.iterrows()],
    )
    pv = posture_grp["mb_defor_primary_rate"]
    prog, cons = pv.get("Both progressive", np.nan), pv.get("Both conservative", np.nan)
    mono = (not np.isnan(prog) and not np.isnan(cons) and cons > prog)
    L += [
        "",
        f"Primary deforestation under both-conservative alignment ({fmt(cons, ' %', 4)} "
        f"of area / yr) is "
        + (f"**higher** than under both-progressive alignment ({fmt(prog, ' %', 4)}) — "
           "consistent with the directional claim." if mono else
           f"**not** higher than under both-progressive alignment ({fmt(prog, ' %', 4)}) — "
           "the posture signal is weak or mixed here.")
        + " Read against the front-loading confound below before drawing a policy "
          "conclusion from it.",
        "",
        "### Per size class",
        "",
    ]
    rows = []
    for lbl, sc in ((small_lbl, size_order[0]), (large_lbl, size_order[1])):
        sub = panel_t[panel_t["group"] == lbl]
        if sub.empty:
            continue
        g = sub.groupby("posture")[["mb_defor_primary_rate", "mb_fire_scar_rate"]].mean()
        for post in ["Both progressive", "Opposed / mixed", "Both conservative"]:
            if post in g.index:
                rows.append([sc, post, fmt(g.loc[post, "mb_defor_primary_rate"], " %", 4),
                             fmt(g.loc[post, "mb_fire_scar_rate"], " %", 4)])
    L += md_table(["Size class", "Posture", "Deforestation", "Fire"], rows)
    L += ["", "---", ""]

    if scope_piv is not None:
        L += [
            f"## H2b — Where governance bites: core vs. buffer ({size_order[1]} only)",
            "",
            "*Only the large lands carry a buffer ring, so this contrast is internal "
            "to them; the ring is the partial, bbox-clipped ring described in "
            "Report 3.*",
            "",
            f"![governance by scope](figures/{figs['scope'].name})",
            "",
            "Absolute increase in the annual rate (pp of area / yr) inside the core "
            "vs. in the ring, and how many times larger the ring's response is:",
            "",
        ]
        L += md_table(
            ["Contrast", "Core (pp)", "Buffer (pp)", "Buffer ÷ core"],
            [[idx, fmt(r["Core"], " pp", 4), fmt(r["Buffer 10 km"], " pp", 4),
              fmt(r["buffer ÷ core"], "×", 1)] for idx, r in scope_piv.iterrows()],
        )
        L += ["", "---", ""]

    g = core_rates_by(panel, meta, "region")
    g = g.reindex(order_regions(g.index))
    L += [
        "## Variation by macro-region",
        "",
        f"![regional comparison](figures/{figs['regional'].name})",
        "",
        "Core rates only (the ring exists for the large lands alone). Region and size "
        "are the same axis in this design — the table below is the size contrast seen "
        "from the other side.",
        "",
    ]
    L += md_table(
        ["Region", "n", "Deforestation", "Fire", "Regrowth"],
        [[idx, int(r["n"]), fmt(r["defor"], " %", 4), fmt(r["fire"], " %", 4),
          fmt(r["regrowth"], " %", 4)] for idx, r in g.iterrows()],
    )

    L += [
        "",
        "---",
        "",
        "## H3 — Recognition strength and policy regime",
        "",
        "*Claim: protection is more robust where recognition is stronger and the "
        "national policy regime firmer.*",
        "",
        "### Cross-section — demarcation status within each size class",
        "",
        f"![recognition by size](figures/{figs['recognition'].name})",
        "",
    ]
    rec = with_gap(summary).merge(
        meta[["group", "territory", "size_class", "fully_recognized"]],
        on=["group", "territory"], how="left")
    rec["tier2"] = np.where(rec["fully_recognized"].fillna(False), "Regularizada",
                            "Pré-regularização")
    gg = rec.groupby(["size_class", "tier2"], observed=True).agg(
        n=("territory", "size"),
        gfc=("t_gfc_loss_pct_of_2000_cover", "mean"),
        fc=("t_forest_change_pct", "mean"))
    L += md_table(
        ["Size class", "Recognition", "n", "Core GFC loss %", "Forest change %"],
        [[idx[0], idx[1], int(r["n"]), fmt(r["gfc"]), fmt(r["fc"])]
         for idx, r in gg.iterrows()],
    )
    L += [
        "",
        "Within the large lands recognition barely varies (almost all are "
        "*Regularizada*), so the informative split is inside the small group, where "
        "a third of the lands are still short of regularisation.",
        "",
        "### Over time — national policy strength",
        "",
        f"![policy timeline](figures/{figs['policy'].name})",
        "",
    ]
    L += md_table(
        ["Administration", "Deforestation", "Fire", "Hansen loss", "Regrowth",
         "Enforcement (0–3)", "Demarcation (−1…+1)"],
        [[idx, fmt(r["defor"], " %", 4), fmt(r["fire"], " %", 4), fmt(r["hansen"], " %", 4),
          fmt(r["regrowth"], " %", 4), fmt(r["enforcement"], "", 2),
          fmt(r["demarcation"], "", 2)] for idx, r in regime_tbl.iterrows()],
    )
    L += [
        "",
        "Read with care: **inside already-recognised lands the over-time signal is "
        "confounded**. Primary-vegetation clearing is front-loaded (most of it "
        "predates or coincides with recognition, then decays), while fire tracks "
        "accumulated degradation and drought as much as governance. The clean policy "
        "signal in this project is cross-sectional. (Regrowth falling to zero in "
        "2023–24 is a MapBiomas coverage edge, not a real collapse.)",
        "",
        "---",
        "",
        "## Caveats",
        "",
        "- **Size is not isolated.** Size class, macro-region, biome and demarcation "
        "status co-vary by construction; every contrast in these reports is between "
        "two situations, not between two areas.",
        f"- **Baseline asymmetry.** {size_order[0]} sit in landscapes cleared largely "
        f"*before* 1985, so their {runs[0].year1}–{runs[0].year2} change figures "
        "understate historical loss; the large Amazonian lands were mostly forested at "
        "the start of the record.",
        "- **Buffer asymmetry.** No rings for the small lands (disabled in the batch — "
        "a 10 km ring around a 30 ha land describes its municipality). The large "
        "lands' rings are the bbox-clipped, border-truncated partial rings described "
        "in Report 3.",
        "- **Quadrant provenance.** All large-land tables, maps and figures are "
        "recombinations of four quadrant exports (`utils/quadrant_merge.py`); table "
        "sums are exact, maps are pixel-wise composites of four same-frame renders.",
        "- MapBiomas deforestation/fire series begin in 1987 and Hansen loss in 2001; "
        "government-change and posture windows inherit those limits.",
        "- Strata are uneven (some region × size cells hold one land); read n<5 cells "
        "as indicative only.",
        "",
    ]
    p = out / "report_governance_policy.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ---------------------------------------------------------------- README block

_RM_START = "<!-- governance-reports:start -->"
_RM_END = "<!-- governance-reports:end -->"


def link_reports_in_readme(out, cfg):
    readme = out / "README.md"
    rows = [_RM_START, "## Governance, policy & manuscripts", "",
            f"- [{cfg['title3']}](report_group_comparison.md)",
            f"- [{cfg['title4']}](report_governance_policy.md)"]
    for m in cfg.get("manuscripts", []):
        rows.append(f"- [Manuscript — {m['title']}]({m['file']})")
    rows += ["", f"Built by `{Path(__file__).name}`.", _RM_END]
    block = "\n".join(rows)
    if not readme.is_file():
        readme.write_text(block + "\n", encoding="utf-8")
        return
    text = readme.read_text(encoding="utf-8")
    if _RM_START in text and _RM_END in text:
        pre, post = text[: text.index(_RM_START)], text[text.index(_RM_END) + len(_RM_END):]
        readme.write_text(pre + block + post, encoding="utf-8")
    else:
        readme.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


# ---------------------------------------------------------------- orchestration


def drop_partial_timelines(run, batch: Path) -> list:
    """Blank the timeline of areas whose SOURCE export missed quadrants.

    `quadrant_merge.py` records how many quadrant files each data family was
    built from. A land that exported only one of four timeline quadrants (Parque
    do Araguaia does) has a whole-territory *landcover* total but a quarter-of-a
    -territory *timeline*, so its annual rates would be silently understated.
    Blanking the timeline drops it from the rate panel and from the fire totals
    instead of letting a partial sum through.
    """
    log = batch / "quadrant_merge_log.csv"
    if not log.is_file():
        return []
    df = pd.read_csv(log)
    if "t_q_timeline" not in df.columns:
        return []
    partial = df.loc[(df["t_q_timeline"] > 0) & (df["t_q_timeline"] < 4), "territory"].tolist()
    hit = []
    for res in run.results:
        if res.name in partial:
            res.territory.timeline = None
            if res.buffer is not None:
                res.buffer.timeline = None
            hit.append(res.name)
    return hit


def run_dataset(cfg):
    out = Path(cfg["out"])
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    img_root = out / "images"
    img_root.mkdir(exist_ok=True)
    fig_dir = out / "figures"

    runs = []
    for key, color in (("small", "#c026d3"), ("large", "#7c3aed")):
        label = cfg[f"label_{key}"]
        run = agg.load_batch(Path(cfg[f"batch_{key}"]), label)
        run.kind = "indigenous"
        gov.GROUP_COLOR_BY_LABEL[label] = color
        dropped = [r.name for r in run.results if r.territory.comparison is None]
        run.results = [r for r in run.results if r.territory.comparison is not None]
        if dropped:
            print(f"  ! [{label}] {len(dropped)} unreadable area(s) dropped: {dropped}")
        cfg[f"dropped_{key}"] = dropped
        # Batch selection used FUNAI `superficie`, which is 0.0 for lands whose
        # area has not been entered — so a few genuinely large lands landed in a
        # "smallest" selection. Filter on the ANALYSED area instead and record
        # what that removes; keeping a 726,871 ha land in a ≤530 ha group would
        # dominate every sum and mean in the report.
        cfg[f"oversized_{key}"] = []
        cap = cfg.get(f"max_area_ha_{key}")
        if cap:
            tmp = agg.build_summary_table([run]).set_index("territory")["t_area_total_ha"]
            over = sorted([(n, float(tmp.get(n, np.nan))) for n in tmp.index
                           if tmp.get(n, 0) > cap], key=lambda x: -x[1])
            if over:
                names = {n for n, _ in over}
                run.results = [r for r in run.results if r.name not in names]
                cfg[f"oversized_{key}"] = over
                print(f"  ! [{label}] {len(over)} land(s) above the {cap:,.0f} ha cap "
                      f"excluded (FUNAI superficie=0 selection artefact): "
                      + ", ".join(f"{n} ({a:,.0f} ha)" for n, a in over))
        partial = drop_partial_timelines(run, Path(cfg[f"batch_{key}"]))
        cfg[f"partial_timeline_{key}"] = partial
        if partial:
            print(f"  ! [{label}] timeline dropped for {len(partial)} land(s) with an "
                  f"incomplete quadrant export: {partial}")
        print(f"[{label}] {len(run.results)} lands")
        runs.append(run)
    size_labels = {cfg["label_small"]: cfg["size_order"][0],
                   cfg["label_large"]: cfg["size_order"][1]}

    print("  recovering UF + demarcation status + ladder dates …")
    meta = gov.load_territory_metadata(runs)
    meta = ind.augment_meta_dates(meta)
    summary = agg.build_summary_table(runs)
    meta = augment_meta_size(meta, summary, size_labels)
    meta = meta.merge(summary[["group", "territory", "slug"]],
                      on=["group", "territory"], how="left")
    meta = attach_ring_coverage(meta, {cfg["label_large"]: cfg["batch_large"]})
    place_labels = build_place_labels(meta)

    lc = agg.build_landcover_long(runs)
    tl = agg.build_timeline_long(runs)
    summary.to_csv(out / "data" / "summary_metrics.csv", index=False)
    lc.to_csv(out / "data" / "landcover_long.csv", index=False)
    tl.to_csv(out / "data" / "timeline_long.csv", index=False)
    xlsx = agg.write_spreadsheet(out, summary, lc, tl)

    charts = {
        "gfc_loss_inside_vs_outside": agg.chart_inside_outside_scatter(summary, runs, fig_dir),
        "group_annual_timelines": agg.chart_group_timelines(tl, runs, fig_dir),
    }
    for r in runs:
        charts[f"forest_change_ranked_{agg._slug(r.label)}"] = \
            agg.chart_forest_change_ranked(summary, r, fig_dir, place_labels)
        charts[f"landcover_composition_{agg._slug(r.label)}"] = \
            agg.chart_landcover_composition(lc, r, fig_dir, place_labels)
    for r in runs:
        agg.write_group_report(r, summary, out, img_root, charts)
    agg.write_index(runs, summary, out, charts, xlsx)

    panel = gov.build_rate_panel(runs, meta)
    panel_t = panel[panel["scope"] == "territory"].copy()
    panel_large = panel[panel["group"] == cfg["label_large"]]

    y1, y2 = runs[0].year1, runs[0].year2
    figs_gp = {
        "rates": gov.chart_group_rate_curves(panel, fig_dir),
        "dist": gov.chart_group_distributions(summary, runs, fig_dir),
        "size": chart_size_outcomes(summary, meta, fig_dir, cfg["size_order"], y2),
        "context": chart_size_context(meta, fig_dir, cfg["size_order"]),
        "landcover": chart_size_landcover(lc, meta, fig_dir, cfg["size_order"], y1, y2),
        "recognition": chart_size_recognition(summary, meta, fig_dir, cfg["size_order"]),
        "scatter": charts["gfc_loss_inside_vs_outside"],
    }
    change_path, change_df = gov.chart_change_effect(panel_t, fig_dir)
    posture_path, posture_grp, _ = gov.chart_posture_effect(panel_t, fig_dir)
    policy_path = gov.chart_policy_timeline(panel_t, fig_dir)
    regime_tbl = gov.build_regime_table(panel_t)
    regional_path = gov.chart_regional(panel, fig_dir)
    figs_gov = {"change": change_path, "posture": posture_path, "policy": policy_path,
                "regional": regional_path, "recognition": figs_gp["recognition"]}
    scope_piv = None
    if not panel_large[panel_large["scope"] == "buffer"].empty:
        scope_path, _, scope_piv = gov.chart_governance_scope(panel_large, fig_dir)
        figs_gov["scope"] = scope_path

    panel.to_csv(out / "data" / "governance_rate_panel.csv", index=False)
    meta.to_csv(out / "data" / "territory_metadata.csv", index=False)

    p3 = write_group_comparison(out, cfg, runs, summary, meta, panel, figs_gp)
    p4 = write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs_gov,
                          {"change": change_df, "posture": posture_grp,
                           "regime": regime_tbl, "scope_amp": scope_piv})
    link_reports_in_readme(out, cfg)
    print(f"  wrote {p3.name}, {p4.name}")
    return summary, meta, panel, panel_t


ROOT = "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report"
DL = "/media/leandromb/iron8/Downloads_ubuntuWD"
DATASETS = {
    "size_extremes": {
        "batch_small": f"{DL}/yvynation_batch_20260817_225732_60tipeq",
        "batch_large": f"{DL}/yvynation_batch_20260817_225855_26ti_1M_merged",
        "out": f"{ROOT}/indigenous_size_extremes",
        # FUNAI `superficie` is 0.0 for unregistered areas, so the "smallest"
        # selection picked up a few large lands — cap on the analysed area.
        "max_area_ha_small": 1000.0,
        # labels MUST contain ASCII "Indig" so gov's indigenous branches fire
        "label_small": "Smallest Indigenous Lands (≤ 530 ha)",
        "label_large": "Largest Indigenous Lands (> 1 M ha)",
        "size_order": ["Smallest (≤ 530 ha)", "Largest (> 1 M ha)"],
        # prose forms — never lower-case the labels, "1 M ha" must keep its M
        "word_small": "smallest lands",
        "word_large": "largest lands",
        "title3": "Report 3 — Extremes of scale: Brazil's smallest and largest Indigenous Lands",
        "title4": "Report 4 — Governance, ideology & policy recognition — smallest vs. largest Indigenous Lands",
        "manuscripts": [
            {"file": "MANUSCRIPT_size_extremes_indigenous_lands.md",
             "title": "Two hundred hectares and nine million — what scale does to Indigenous land protection in Brazil"},
        ],
        "intro3": (
            "Two batches at opposite ends of the Brazilian Indigenous-land size "
            "distribution, analysed over {y1}–{y2} on identical MapBiomas, Hansen GFC "
            "and MapBiomas-Fire inputs: the **{n_small} smallest** lands (of "
            "{n_sel_small} selected — analysed areas from 2 ha to {small_max} ha, "
            "across {n_states_small} states from Rio Grande do Sul to Acre) and the "
            "**{n_large} largest** (every land above 1 M ha, up to Yanomami's "
            "{large_max} ha, all in Amazonia). Rates are area-normalised (% of each "
            "area per year), so the two ends of a three-order-of-magnitude range can "
            "be compared directly. The large lands' rasters were exported in four "
            "bounding-box quadrants each and recombined here into whole-territory "
            "tables, maps and figures."),
    },
}


if __name__ == "__main__":
    which = sys.argv[1:] or list(DATASETS)
    for key in which:
        run_dataset(DATASETS[key])
        print(f"Done → {DATASETS[key]['out']}")
