#!/usr/bin/env python3
"""Build a full yvynation report set (aggregator + governance) for ONE batch
folder of Brazilian *Indigenous Lands*, with dataset-aware, data-driven prose.

Sibling of `conservation_report_builder.py`; the difference is the recovered
metadata. Indigenous lands carry a demarcation ladder (fase_ti) instead of an
SNUC group/category, are all federally demarcated (no sphere axis), and a
purposive Amazon-wide selection typically spans several states — so the
meaningful stratifiers here are **demarcation status** and **macro-region**, and
the report keeps the macro-regional analysis that the single-state UC sets drop.

Reuses batch_report_aggregator (agg) and governance_policy_report (gov) for all
data assembly and figures; only report_group_comparison.md and
report_governance_policy.md are re-written here with correct titles and
interpretation. The group label must contain "Indig" (ASCII) so
gov.chart_recognition_tiers fires its indigenous branch.
"""
from __future__ import annotations

import re
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

REGION_ORDER = gov.REGION_ORDER  # Norte, Centro-Oeste, Nordeste, Sudeste, Sul

# FUNAI demarcation ladder date fields → stage label (weak → strong recognition).
LADDER_STAGES = [
    ("data_em_es", "Em Estudo", "#9aa5b1"),
    ("data_delim", "Delimitada", "#5b8fd6"),
    ("data_decla", "Declarada", "#d98a2b"),
    ("data_homol", "Homologada", "#7c3aed"),
    ("data_regul", "Regularizada", "#166534"),
]
REGUL_ERA_BINS = [0, 2000, 2010, 2020, 3000]
REGUL_ERA_LABELS = ["≤2000", "2001–2010", "2011–2020", "≥2021"]
MARCO_TEMPORAL_YEAR = 1988  # 1988-10-05 Constitution — timeframe-doctrine reference


def _yr(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return np.nan
    m = re.search(r"(\d{4})", str(v))
    if not m:
        return np.nan
    y = int(m.group(1))
    return float(y) if 1970 <= y <= 2026 else np.nan  # guard stray typos (e.g. 1926)


def augment_meta_dates(meta):
    """Add FUNAI ladder-stage years + regularisation era to the metadata frame."""
    import geopandas as gpd
    gi = gpd.read_file(gov.GPKG_IND)
    imap = {gov._norm(r["terrai_nom"]): r for _, r in gi.iterrows()}
    recs = []
    for terr in meta["territory"]:
        row = imap.get(gov._strip_code(terr))
        if row is None:
            row = imap.get(gov._norm(terr))
        rec = {"territory": terr}
        for col, label, _ in LADDER_STAGES:
            rec[f"y_{col[5:]}"] = _yr(row.get(col)) if row is not None else np.nan
        recs.append(rec)
    dates = pd.DataFrame(recs)
    meta = meta.merge(dates, on="territory", how="left")
    meta["regul_era"] = pd.cut(meta["y_regul"], REGUL_ERA_BINS, labels=REGUL_ERA_LABELS)
    firsts = meta[["y_em_es", "y_delim", "y_decla"]].min(axis=1)
    meta["yrs_to_regul"] = (meta["y_regul"] - firsts).where(lambda s: s >= 0)
    meta["declared_pre_1988"] = np.where(
        meta["y_decla"].notna(), meta["y_decla"] <= MARCO_TEMPORAL_YEAR, np.nan)
    return meta


# ---------------------------------------------------------------- formatting

def fmt(v, unit="", dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:,.{dec}f}{unit}"
    return str(v)


def signed_pct(a, b):
    if not b or (isinstance(b, float) and np.isnan(b)):
        return "—"
    return f"{(a / b - 1) * 100:+.0f}%"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def _order_regions(index):
    ordered = [r for r in REGION_ORDER if r in index]
    return ordered + [r for r in index if r not in ordered]


REGION_ABBR = {"Norte": "N", "Centro-Oeste": "CO", "Nordeste": "NE",
               "Sudeste": "SE", "Sul": "S"}


def build_place_labels(meta):
    """territory → 'Name · UF·Region' for chart y-axes, so similar cases (same
    state/region) are visible next to each other in ranked/timeline order."""
    m = {}
    for _, r in meta.iterrows():
        uf = r.get("uf") if isinstance(r.get("uf"), str) else "?"
        reg = REGION_ABBR.get(r.get("region"), "?")
        m[r["territory"]] = f"{agg._shorten(r['territory'], 24)} · {uf}·{reg}"
    return m


# ---------------------------------------------------------------- grouped metrics

def grouped_metrics(summary, meta, by):
    """Mean core/buffer metrics + protection gap, grouped by a meta attribute."""
    s = summary.merge(meta[["group", "territory", by]], on=["group", "territory"], how="left")
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]
    g = s.groupby(by).agg(
        n=("territory", "size"),
        area=("t_area_total_ha", "sum"),
        t_fc=("t_forest_change_pct", "mean"),
        b_fc=("b_forest_change_pct", "mean"),
        t_gfc=("t_gfc_loss_pct_of_2000_cover", "mean"),
        b_gfc=("b_gfc_loss_pct_of_2000_cover", "mean"),
        gap=("protection_gap", "mean"),
    )
    return g


def rates_by_attr(panel, meta, by):
    """Mean core AND buffer annual rates, grouped by a meta attribute."""
    # `region`/`uf` are already on the panel; only join attributes it lacks.
    p = panel if by in panel.columns else panel.merge(
        meta[["group", "territory", by]], on=["group", "territory"], how="left")
    rows = []
    for val, sub in p.groupby(by):
        core = sub[sub["scope"] == "territory"]
        buf = sub[sub["scope"] == "buffer"]
        rows.append({
            by: val,
            "n": sub[["group", "territory"]].drop_duplicates().shape[0],
            "core_defor": core["mb_defor_primary_rate"].mean(),
            "buf_defor": buf["mb_defor_primary_rate"].mean(),
            "core_fire": core["mb_fire_scar_rate"].mean(),
            "buf_fire": buf["mb_fire_scar_rate"].mean(),
        })
    return pd.DataFrame(rows).set_index(by)


def chart_demarcation_timeline(meta, fig_dir: Path, label_map=None) -> Path:
    """Per-land path through the FUNAI demarcation ladder (stage year markers),
    one row per land sorted by regularisation year."""
    d = meta.dropna(subset=["y_regul"]).sort_values("y_regul")
    n = len(d)
    fig, ax = plt.subplots(figsize=(11, max(4, 0.30 * n + 1.5)))
    y = np.arange(n)
    stage_cols = [f"y_{c[5:]}" for c, _, _ in LADDER_STAGES]
    # connecting line from first to last known stage per land
    for i, (_, r) in enumerate(d.iterrows()):
        yrs = [r[c] for c in stage_cols if not np.isnan(r[c])]
        if yrs:
            ax.plot([min(yrs), max(yrs)], [i, i], color="#cccccc", lw=1.2, zorder=1)
    for col, label, color in LADDER_STAGES:
        c = f"y_{col[5:]}"
        ax.scatter(d[c], y, s=26, color=color, label=label, zorder=2, edgecolor="white", linewidth=0.3)
    ax.axvline(MARCO_TEMPORAL_YEAR, color="#b03a2e", ls="--", lw=1.2)
    ax.text(MARCO_TEMPORAL_YEAR, n + 0.5, " 1988 Constitution", color="#b03a2e", fontsize=8, va="bottom")
    ax.set_yticks(y, [agg._disp(t, label_map) for t in d["territory"]], fontsize=6.5)
    ax.set_ylim(-1, n + 1)
    ax.set_xlabel("Year")
    ax.set_title(f"Path through the demarcation ladder ({n} lands, sorted by regularisation year)")
    ax.legend(fontsize=8, loc="lower right", ncol=2)
    ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gp_demarcation_timeline.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def chart_regularization_outcomes(summary, meta, fig_dir: Path) -> Path:
    """How outcomes relate to WHEN each land was regularised: era bars (left) and
    regularisation-year vs protection-gap scatter by region (right)."""
    s = summary.merge(
        meta[["group", "territory", "regul_era", "y_regul", "region"]],
        on=["group", "territory"], how="left")
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(15, 5.4))

    g = s.groupby("regul_era", observed=True).agg(
        n=("territory", "size"),
        gap=("protection_gap", "mean"),
        core_loss=("t_gfc_loss_pct_of_2000_cover", "mean"),
    ).reindex(REGUL_ERA_LABELS)
    x = np.arange(len(g))
    w = 0.4
    ax0.bar(x - w / 2, g["gap"], w, label="Protection gap (pp)", color="#166534")
    ax0.bar(x + w / 2, g["core_loss"], w, label="Core GFC loss (%)", color="#b03a2e")
    ax0.set_xticks(x, [f"{e}\n(n={int(v) if not np.isnan(v) else 0})" for e, v in zip(g.index, g["n"])])
    ax0.set_title("Outcomes by regularisation era")
    ax0.set_ylabel("pp  /  % of 2000 cover")
    ax0.legend(fontsize=8)
    ax0.grid(axis="y", alpha=0.3)

    region_color = {"Norte": "#2e7d32", "Centro-Oeste": "#b45309", "Nordeste": "#7c3aed",
                    "Sudeste": "#2563eb", "Sul": "#059669"}
    for reg, sub in s.dropna(subset=["y_regul"]).groupby("region"):
        ax1.scatter(sub["y_regul"], sub["protection_gap"], s=34, alpha=0.8,
                    color=region_color.get(reg, "#444444"), label=reg)
    sd = s.dropna(subset=["y_regul", "protection_gap"])
    if len(sd) >= 3:
        b, a = np.polyfit(sd["y_regul"], sd["protection_gap"], 1)
        xs = np.array([sd["y_regul"].min(), sd["y_regul"].max()])
        ax1.plot(xs, a + b * xs, "k--", lw=1, label=f"trend ({b:+.2f} pp/yr)")
    ax1.axvline(MARCO_TEMPORAL_YEAR, color="#b03a2e", ls="--", lw=1)
    ax1.set_xlabel("Year of regularisation")
    ax1.set_ylabel("Protection gap (pp)")
    ax1.set_title("Regularisation year vs protection gap")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)

    fig.suptitle("Path to regularisation and forest outcomes", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_regularization_outcomes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def breakdown_block(title, note, g):
    L = [f"## {title}", "", note, ""]
    L += md_table(
        ["Stratum", "n", "Σ area (ha)", "Forest chg core/buf %", "GFC loss core/buf %", "Protection gap pp"],
        [[idx, int(r["n"]), fmt(r["area"], "", 0),
          f"{fmt(r['t_fc'])} / {fmt(r['b_fc'])}", f"{fmt(r['t_gfc'])} / {fmt(r['b_gfc'])}",
          fmt(r["gap"], "", 1)] for idx, r in g.iterrows()],
    )
    return L


# ---------------------------------------------------------------- Report 3

def write_group_comparison(out, cfg, runs, summary, meta, panel, figs):
    run = runs[0]
    s = summary.copy()
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]
    n = len(s)
    n_pos = int((s["protection_gap"] > 0).sum())
    core_fire = panel[panel["scope"] == "territory"]["mb_fire_scar_rate"].mean()
    buf_fire = panel[panel["scope"] == "buffer"]["mb_fire_scar_rate"].mean()
    core_def = panel[panel["scope"] == "territory"]["mb_defor_primary_rate"].mean()
    buf_def = panel[panel["scope"] == "buffer"]["mb_defor_primary_rate"].mean()
    fire_core_more = core_fire > buf_fire

    L = [
        f"# {cfg['title3']}",
        "",
        cfg["intro3"],
        "",
        "## Headline metrics — core vs. buffer",
        "",
    ]
    L += md_table(
        ["Metric", "Protected core", "10 km buffer"],
        [
            ["Areas analysed", f"{n}", "—"],
            ["Σ area (ha)", fmt(s["t_area_total_ha"].sum(), "", 0), fmt(s["b_area_total_ha"].sum(), "", 0)],
            ["Mean forest change 1985→2024", fmt(s["t_forest_change_pct"].mean(), " %"), fmt(s["b_forest_change_pct"].mean(), " %")],
            ["Mean forest 2024 (% of area)", fmt(s["t_forest_2024_pct_of_area"].mean(), " %"), fmt(s["b_forest_2024_pct_of_area"].mean(), " %")],
            ["Mean anthropic 2024 (% of area)", fmt(s["t_anthropic_2024_pct_of_area"].mean(), " %"), fmt(s["b_anthropic_2024_pct_of_area"].mean(), " %")],
            ["Mean Hansen GFC loss (% of 2000 cover)", fmt(s["t_gfc_loss_pct_of_2000_cover"].mean(), " %"), fmt(s["b_gfc_loss_pct_of_2000_cover"].mean(), " %")],
            ["**Protection gap** (buffer − core loss)", f"**{fmt(s['protection_gap'].mean(), ' pp')}**", ""],
        ],
    )
    L += [
        "",
        f"The **protection gap** (buffer minus core canopy loss) is positive for "
        f"**{n_pos} of {n}** lands — the clearest single sign that the boundaries are "
        f"holding. Buffers also carry markedly more anthropic land use by 2024 "
        f"({fmt(s['b_anthropic_2024_pct_of_area'].mean(), ' %')} vs "
        f"{fmt(s['t_anthropic_2024_pct_of_area'].mean(), ' %')} inside), i.e. these "
        f"lands sit inside actively-cleared surroundings rather than pristine ones.",
        "",
    ]

    # Breakdown by demarcation status (fase_ti) — most are Regularizada
    grp = grouped_metrics(summary, meta, "recognition_tier")
    if len(grp) > 1:
        L += breakdown_block(
            "Breakdown by demarcation status",
            "Position on the FUNAI demarcation ladder (*Em Estudo → Delimitada → "
            "Declarada → Homologada → Regularizada*). The selection targeted "
            "*Regularizada* lands; a few read an earlier phase in the current "
            "snapshot. The protection gap is what each core saves relative to its "
            "own buffer.",
            grp,
        ) + [""]

    # Breakdown by macro-region — the selection spans several states
    if meta["region"].nunique(dropna=True) > 1:
        reg = grouped_metrics(summary, meta, "region")
        reg = reg.reindex(_order_regions(reg.index))
        L += breakdown_block(
            "Breakdown by macro-region",
            "Grouped by macro-region (Norte ≈ deep Amazon, then Centro-Oeste ≈ "
            "Cerrado/MT frontier, Nordeste). Region conditions both the protected "
            "core and the frontier pressing on its buffer.",
            reg,
        ) + [""]

    # Path to regularisation — timing of the demarcation ladder
    if meta["y_regul"].notna().any():
        med = int(meta["y_regul"].median())
        L += [
            "",
            "## Path to regularisation (demarcation timing)",
            "",
            "Every land here is *Regularizada*, but they reached that status across "
            f"four decades (median **{med}**). The FUNAI ladder dates "
            "(*Em Estudo → Delimitada → Declarada → Homologada → Regularizada*) show "
            "each land's path; the dashed line marks the 1988 Constitution, the "
            "reference date of the *marco temporal* (time-frame) debate.",
            "",
            f"![demarcation timeline](figures/{figs['timeline'].name})",
            "",
            "Do earlier-regularised lands protect better? Outcomes by regularisation "
            "era, and regularisation year against the protection gap:",
            "",
            f"![regularisation outcomes](figures/{figs['reg_outcomes'].name})",
            "",
        ]
        era = grouped_metrics(summary, meta, "regul_era")
        era = era.reindex([e for e in REGUL_ERA_LABELS if e in era.index])
        if len(era) > 1:
            L += breakdown_block(
                "Breakdown by regularisation era",
                "Grouped by the year the land became *Regularizada*. Earlier "
                "regularisation means more of the 1985–2024 series is post-"
                "recognition; later regularisation means the land was consolidating "
                "for much of the record.",
                era,
            ) + [""]

    L += [
        "",
        "## Annual land-change rates — core vs. buffer",
        "",
        f"![rate curves](figures/{figs['rates'].name})",
        "",
        f"Solid = protected core, dashed = 10 km buffer. For **deforestation** the "
        f"buffer runs above the core ({fmt(buf_def, ' %', 3)} vs {fmt(core_def, ' %', 3)} "
        f"of area / yr on average) — the surroundings absorb most of the clearing "
        f"pressure. For **fire** the ordering "
        + ("**reverses**: the protected cores burn *more* than their already-converted "
           if fire_core_more else "runs the same way: cores burn *less* than ")
        + f"buffers ({fmt(core_fire, ' %', 3)} vs {fmt(buf_fire, ' %', 3)} of area / yr). "
        + ("Report 4 shows the same split holds for how each scope reacts to governance."
           if fire_core_more else "Report 4 examines how each scope reacts to governance."),
        "",
        "## Distributions",
        "",
        f"![distributions](figures/{figs['dist'].name})",
        "",
        "## Reading",
        "",
        f"- **{run.label}**: core forest change {fmt(s['t_forest_change_pct'].mean(), ' %')} "
        f"vs buffer {fmt(s['b_forest_change_pct'].mean(), ' %')}; core Hansen loss "
        f"{fmt(s['t_gfc_loss_pct_of_2000_cover'].mean(), ' %')} vs buffer "
        f"{fmt(s['b_gfc_loss_pct_of_2000_cover'].mean(), ' %')}; protection gap "
        f"{fmt(s['protection_gap'].mean(), ' pp')} (positive for {n_pos}/{n}).",
        "",
    ]
    if cfg.get("excluded"):
        L += [
            f"> **Note.** {len(cfg['excluded'])} large polygon(s) exported in four "
            f"quadrants — {', '.join(cfg['excluded'])} — are omitted from the "
            "aggregate metrics (the loader reads only single-tile exports).",
            "",
        ]
    p = out / "report_group_comparison.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ---------------------------------------------------------------- Report 4

def write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs, tables):
    change_df = tables["change"].set_index("condition")
    posture_grp = tables["posture"]
    regime_tbl = tables["regime"]
    tiers = tables["tiers"]
    scope_piv = tables["scope_amp"]
    n_terr = panel_t[["group", "territory"]].drop_duplicates().shape[0]
    multi_state = meta["uf"].nunique(dropna=True) > 1

    L = [
        f"# {cfg['title4']}",
        "",
        "Tests three linked hypotheses about *why* deforestation, fire and forest "
        "recovery move the way they do, joining the batch time-series to the "
        "federal/state political record (`political_context_brazil`) and the annual "
        "policy-strength scores (`policy_context_brazil`). Every rate below is the "
        f"area-normalised annual value (% of area / yr) averaged across {n_terr} "
        "lands; associations, not proof of cause.",
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
        [[idx, fmt(r["n_obs"], "", 0), fmt(r["defor"], " %", 3), fmt(r["fire"], " %", 3), fmt(r["regrowth"], " %", 3)]
         for idx, r in change_df.iterrows()],
    )
    stable = change_df.loc["Stable years"]
    window = change_df.loc["Change yr + next"]
    d_reg = (window["regrowth"] / stable["regrowth"] - 1) if stable["regrowth"] else np.nan
    reg_word = "essentially flat" if abs(d_reg) < 0.02 else ("slower" if d_reg < 0 else "faster")
    L += [
        "",
        f"In the change year plus the following year, mean deforestation runs "
        f"**{signed_pct(window['defor'], stable['defor'])}** and fire "
        f"**{signed_pct(window['fire'], stable['fire'])}** versus stable years, while "
        f"regrowth is {reg_word} (**{signed_pct(window['regrowth'], stable['regrowth'])}**).",
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
        [[idx, fmt(r["mb_defor_primary_rate"], " %", 3), fmt(r["mb_fire_scar_rate"], " %", 3), fmt(r["mb_secondary_growth_rate"], " %", 3)]
         for idx, r in posture_grp.iterrows()],
    )
    pv = posture_grp["mb_defor_primary_rate"]
    prog = pv.get("Both progressive", np.nan)
    cons = pv.get("Both conservative", np.nan)
    mono = (not np.isnan(prog) and not np.isnan(cons) and cons > prog)
    L += [
        "",
        f"Primary deforestation under both-conservative alignment "
        f"({fmt(cons, ' %', 3)} of area / yr) is "
        + (f"**higher** than under both-progressive alignment ({fmt(prog, ' %', 3)}) — "
           "consistent with the directional claim." if mono else
           f"**not** higher than under both-progressive alignment ({fmt(prog, ' %', 3)}) — "
           "the posture signal is weak or mixed here.")
        + (" Because these lands span several states, the state-governor axis carries "
           "real cross-sectional variation (not just the federal cycle)." if multi_state
           else ""),
        "",
        "---",
        "",
        "## H2b — Where governance bites: core vs. buffer",
        "",
        "*Splitting every governance contrast by scope shows the boundary does not "
        "damp all pressures equally.*",
        "",
        f"![governance by scope](figures/{figs['scope'].name})",
        "",
        "Absolute increase in the annual rate (pp of area / yr) inside the core vs. "
        "in the 10 km buffer, and how many times larger the buffer's response is:",
        "",
    ]
    L += md_table(
        ["Contrast", "Core (pp)", "Buffer (pp)", "Buffer ÷ core"],
        [[idx, fmt(r["Core"], " pp", 3), fmt(r["Buffer 10 km"], " pp", 3), fmt(r["buffer ÷ core"], "×", 1)]
         for idx, r in scope_piv.iterrows()],
    )

    def _cw_row(keyword):
        m = [i for i in scope_piv.index
             if keyword in i.lower() and "change window" in i.lower()]
        if not m:
            return None, None
        r = scope_piv.loc[m[0]]
        return r["Core"], r["Buffer 10 km"]

    def_c, def_b = _cw_row("deforestation")
    fire_c, fire_b = _cw_row("fire")

    def _defor_bullet(c, b):
        if c is None:
            return "no change-window contrast available."
        if c > 0 and b > 0:
            if b > c:
                return (f"around government changes the buffer's clearing swing is "
                        f"**{b / c:.1f}×** the core's — pressure lands mostly *outside* "
                        "the line while the core stays comparatively flat, the classic "
                        "protection effect shown as reactivity.")
            return ("the core's clearing swing around government changes is as large as "
                    "or larger than the buffer's — the boundary does not deflect "
                    "clearing outward in this set.")
        if c <= 0 < b:
            return ("around government changes clearing *eases* inside the core but "
                    "*rises* in the buffer — pressure is displaced outward.")
        return ("neither scope shows a clear rise in clearing around government "
                "changes in this set.")

    def _fire_bullet(c, b):
        if c is None:
            return "no change-window contrast available."
        if c > 0 and b > 0:
            if c > b:
                return (f"the core is the more reactive scope — its change-window fire "
                        f"swing is **{c / b:.1f}×** the buffer's. Protected cores burn "
                        "*more* and respond *more* to governance, likely because "
                        "buffers are already largely converted (little native fuel "
                        "left) while cores keep flammable native cover that ignites "
                        "when enforcement weakens. Fire is where a hostile political "
                        "cycle reaches *inside* the boundary.")
            return ("fire rises more in the buffer than in the core around government "
                    "changes — here fire does not preferentially penetrate the core.")
        if b <= 0 < c:
            return ("fire rises inside the core around government changes while the "
                    "buffer does not — fire penetrates the boundary.")
        return ("neither scope shows a clear fire rise around government changes in "
                "this set.")

    L += [
        "",
        "- **Deforestation** — " + _defor_bullet(def_c, def_b),
        "- **Fire** — " + _fire_bullet(fire_c, fire_b),
        "",
        "---",
        "",
        "## Variation by macro-region and demarcation status",
        "",
        "*The selection spans several states and biomes, so macro-region is a "
        "meaningful axis (Norte ≈ deep Amazon → Centro-Oeste ≈ Cerrado/MT frontier → "
        "Nordeste). Both the protected **core** and its 10 km **buffer** are shown.*",
        "",
    ]
    for by, label, order in (("region", "Macro-region", True),
                             ("recognition_tier", "Demarcation status", False)):
        if meta[by].nunique(dropna=True) <= 1:
            continue
        g = rates_by_attr(panel, meta, by)
        if order:
            g = g.reindex(_order_regions(g.index))
        L += [f"**By {label.lower()}** — annual rates, core / buffer:", ""]
        L += md_table(
            [label, "n", "Defor core/buf %", "Fire core/buf %"],
            [[idx, int(r["n"]),
              f"{fmt(r['core_defor'], '', 3)} / {fmt(r['buf_defor'], '', 3)}",
              f"{fmt(r['core_fire'], '', 3)} / {fmt(r['buf_fire'], '', 3)}"]
             for idx, r in g.iterrows()],
        )
        L.append("")

    L += [
        "---",
        "",
        "## H3 — Policy recognition and robustness",
        "",
        "*Claim: protection is more robust where lands hold stronger recognition.*",
        "",
        "### Over time — national policy strength",
        "",
        f"![policy timeline](figures/{figs['policy'].name})",
        "",
        "Mean land-change rates by federal administration, next to that era's mean "
        "enforcement and demarcation scores:",
        "",
    ]
    L += md_table(
        ["Administration", "Deforestation", "Fire", "Hansen loss", "Regrowth", "Enforcement (0–3)", "Demarcation (−1…+1)"],
        [[idx, fmt(r["defor"], " %", 3), fmt(r["fire"], " %", 3), fmt(r["hansen"], " %", 3),
          fmt(r["regrowth"], " %", 3), fmt(r["enforcement"], "", 2), fmt(r["demarcation"], "", 2)]
         for idx, r in regime_tbl.iterrows()],
    )
    L += [
        "",
        "Read with care: **within already-demarcated lands the over-time signal is "
        "confounded**. Primary-vegetation clearing is front-loaded (most of it "
        "predates or coincides with regularisation, then decays), while fire is "
        "driven by accumulated degradation and drought as much as by governance. The "
        "clean policy signal is cross-sectional, not temporal. (Regrowth's drop to "
        "zero in 2023–24 is a data-coverage edge, not a real collapse.)",
        "",
        "### Cross-section — recognition tier",
        "",
        f"![recognition tiers](figures/{figs['tiers'].name})",
        "",
    ]
    if "indigenous" in tiers and not tiers["indigenous"].empty:
        L += ["**By demarcation status**", ""]
        L += md_table(
            ["Status", "n", "Forest change %", "GFC loss %", "Protection gap pp", "Defor rate %"],
            [[idx, int(r["n"]), fmt(r["forest_change"], " %"), fmt(r["gfc_loss"], " %"),
              fmt(r["protection_gap"], " pp"), fmt(r["defor_rate"], " %", 3)]
             for idx, r in tiers["indigenous"].iterrows()],
        )
        L.append("")

    L += [
        "---",
        "",
        "## Caveats",
        "",
        "- Observational associations across 1985–2024; deforestation drivers "
        "(commodity prices, roads, biome) are not controlled for.",
    ]
    if multi_state:
        L.append(
            "- Lands span several states; state ideology is joined on each area's "
            "primary UF (multi-state lands use the first listed).")
    else:
        L.append(
            "- All lands fall in one state, so the state-ideology panel varies "
            "chiefly through the federal cycle.")
    L += [
        "- MapBiomas deforestation/fire series begin in 1987; Hansen loss in 2001. "
        "Government-change and posture windows inherit those coverage limits.",
        "- The selection is purposive (Regularizada, 50,000–300,000 ha, off the "
        "border strip); some strata are small — read them as indicative.",
    ]
    if cfg.get("excluded"):
        L.append(
            f"- {len(cfg['excluded'])} large polygon(s) exported in quadrants "
            f"({', '.join(cfg['excluded'])}) are omitted from all rates here.")
    L.append("")
    p = out / "report_governance_policy.md"
    p.write_text("\n".join(L), encoding="utf-8")
    return p


# ---------------------------------------------------------------- README block

_RM_START = "<!-- governance-reports:start -->"
_RM_END = "<!-- governance-reports:end -->"


def link_reports_in_readme(out, cfg):
    readme = out / "README.md"
    rows = [
        _RM_START,
        "## Governance, policy & manuscript",
        "",
        f"- [{cfg['title3']}](report_group_comparison.md)",
        f"- [{cfg['title4']}](report_governance_policy.md)",
    ]
    if cfg.get("manuscript"):
        rows.append(f"- [Manuscript — {cfg.get('manuscript_title', 'draft')}]({cfg['manuscript']})")
    rows += ["", "Built by `indigenous_report_builder.py`.", _RM_END]
    block = "\n".join(rows)
    if not readme.is_file():
        readme.write_text(block + "\n", encoding="utf-8")
        return
    text = readme.read_text(encoding="utf-8")
    if _RM_START in text and _RM_END in text:
        pre = text[: text.index(_RM_START)]
        post = text[text.index(_RM_END) + len(_RM_END):]
        readme.write_text(pre + block + post, encoding="utf-8")
    else:
        readme.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


# ---------------------------------------------------------------- orchestration

def run_dataset(cfg):
    out = Path(cfg["out"])
    (out / "data").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    img_root = out / "images"
    img_root.mkdir(exist_ok=True)
    fig_dir = out / "figures"

    run = agg.load_batch(Path(cfg["batch"]), cfg["label"])
    run.kind = "indigenous"
    gov.GROUP_COLOR_BY_LABEL[cfg["label"]] = gov.GROUP_COLOR["indigenous"]
    excluded = [r.name for r in run.results if r.territory.comparison is None]
    run.results = [r for r in run.results if r.territory.comparison is not None]
    cfg["excluded"] = excluded
    runs = [run]
    print(f"[{cfg['label']}] {len(run.results)} lands"
          + (f"  (excluded quadrant-split: {excluded})" if excluded else ""))

    # ---- metadata first, so charts can label by state/region ----------------
    print("  recovering UF + demarcation tiers + ladder dates …")
    meta = gov.load_territory_metadata(runs)
    meta = augment_meta_dates(meta)
    place_labels = build_place_labels(meta)

    # ---- aggregator layer ---------------------------------------------------
    summary = agg.build_summary_table(runs)
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
        charts[f"forest_change_ranked_{agg._slug(r.label)}"] = agg.chart_forest_change_ranked(summary, r, fig_dir, place_labels)
        charts[f"landcover_composition_{agg._slug(r.label)}"] = agg.chart_landcover_composition(lc, r, fig_dir, place_labels)
    for r in runs:
        agg.write_group_report(r, summary, out, img_root, charts)
    agg.write_index(runs, summary, out, charts, xlsx)

    # ---- governance layer ---------------------------------------------------
    panel = gov.build_rate_panel(runs, meta)
    panel_t = panel[panel["scope"] == "territory"].copy()

    figs_gp = {
        "rates": gov.chart_group_rate_curves(panel, fig_dir),
        "dist": gov.chart_group_distributions(summary, runs, fig_dir),
        "timeline": chart_demarcation_timeline(meta, fig_dir, place_labels),
        "reg_outcomes": chart_regularization_outcomes(summary, meta, fig_dir),
    }
    change_path, change_df = gov.chart_change_effect(panel_t, fig_dir)
    posture_path, posture_grp, posture_counts = gov.chart_posture_effect(panel_t, fig_dir)
    policy_path = gov.chart_policy_timeline(panel_t, fig_dir)
    regime_tbl = gov.build_regime_table(panel_t)
    tiers_path, tiers = gov.chart_recognition_tiers(summary, meta, panel_t, fig_dir)
    scope_path, scope_amp, scope_piv = gov.chart_governance_scope(panel, fig_dir)
    regional_path = gov.chart_regional(panel, fig_dir)  # macro-region bars (multi-state set)
    figs_gov = {"change": change_path, "posture": posture_path, "policy": policy_path,
                "tiers": tiers_path, "scope": scope_path, "regional": regional_path}

    panel.to_csv(out / "data" / "governance_rate_panel.csv", index=False)
    meta.to_csv(out / "data" / "territory_metadata.csv", index=False)

    p3 = write_group_comparison(out, cfg, runs, summary, meta, panel, figs_gp)
    p4 = write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs_gov,
                          {"change": change_df, "posture": posture_grp, "regime": regime_tbl,
                           "tiers": tiers, "scope_amp": scope_piv})
    link_reports_in_readme(out, cfg)
    print(f"  wrote {p3.name}, {p4.name}")
    return summary, meta, panel, panel_t


ROOT = "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report"
DATASETS = {
    "indigenous_selection": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260716_220322",
        "out": f"{ROOT}/indigenous_selection",
        # label MUST contain ASCII "Indig" so gov.chart_recognition_tiers fires.
        "label": "Indigenous Lands (Regularizada, 50–300k ha, off-border)",
        "title3": "Report 3 — Regularised mid-sized Indigenous Lands: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Regularised mid-sized Indigenous Lands",
        "manuscript": "MANUSCRIPT_land_use_policy_indigenous_selection.md",
        "manuscript_title": "Do regularised Indigenous boundaries hold across the frontier?",
        "intro3": (
            "A purposive sample of **Indigenous Lands** selected as *fully "
            "regularised* (fase_ti = Regularizada), of mid size (superfície "
            "50,000–300,000 ha) and **off the international border strip** "
            "(faixa_fronteira = Não), analysed over 1985–2024. Each protected "
            "**core** is referenced against its surrounding **10 km buffer** ring; "
            "rates are area-normalised (% of each area per year) so small and large "
            "lands weigh equally and core and buffer are directly comparable. The "
            "selection holds recognition strength roughly constant and spans several "
            "Amazon and Cerrado states."),
    },
}


if __name__ == "__main__":
    which = sys.argv[1:] or list(DATASETS)
    for key in which:
        run_dataset(DATASETS[key])
        print(f"Done → {DATASETS[key]['out']}")
