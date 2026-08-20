#!/usr/bin/env python3
"""Build a full yvynation report set (aggregator + governance) for nationwide,
single-SNUC-category conservation-unit censuses (Florestas Nacionais, Reservas
Extrativistas, Reservas Biológicas, ...), with dataset-aware, data-driven
prose.

Sibling of `conservation_report_builder.py` / `indigenous_report_builder.py`.
Unlike the single-state UC sets, each selection here is ALL units of one SNUC
category returned by the national CNUC query: SNUC category and protection
group are therefore UNIFORM within a dataset — there is no category/group
axis to test. What DOES vary, because each set spans the whole country, is
macro-region, the year each unit was gazetted (`cria_ano`), and — for
categories that exist at more than one level of government (e.g. Reservas
Extrativistas, Reservas Biológicas) — the governance **sphere** (Federal /
Estadual / Municipal). Those axes replace the demarcation ladder used for
Indigenous Lands and the category/sphere axis used for the single-state UC
sets; the sphere axis is only exercised when a dataset actually mixes
spheres (see `cfg["sphere_axis"]`, auto-detected from the data if unset).

Reuses batch_report_aggregator (agg) and governance_policy_report (gov) for all
data assembly and figures; only report_group_comparison.md and
report_governance_policy.md are re-written here. Group label must contain
"Conserv" so gov.chart_recognition_tiers fires its conservation branch.
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

REGION_ORDER = gov.REGION_ORDER  # Norte, Centro-Oeste, Nordeste, Sudeste, Sul
REGION_ABBR = {"Norte": "N", "Centro-Oeste": "CO", "Nordeste": "NE",
               "Sudeste": "SE", "Sul": "S"}

# Default creation-year (cria_ano) eras, aligned to Brazilian forest-policy
# milestones: 1965 Forest Code, 1988 Constitution, 2000 SNUC, 2004 PPCDAm,
# 2012 Forest Code. Datasets whose creation years don't span this range
# (e.g. Reservas Extrativistas, which start in 1990) pass their own
# `era_bins`/`era_labels`/`milestones` via cfg.
ERA_BINS = [0, 1965, 1988, 1999, 2004, 2012, 3000]
ERA_LABELS = ["≤1965", "1966–1988", "1989–1999", "2000–2004", "2005–2012", "2013–2024"]
MILESTONES = [(1965, "1965 Code"), (1988, "1988 Const."), (2000, "2000 SNUC"),
              (2004, "2004 PPCDAm"), (2012, "2012 Code")]


def augment_meta_era(meta: pd.DataFrame, era_bins=None, era_labels=None) -> pd.DataFrame:
    meta = meta.copy()
    meta["creation_era"] = pd.cut(
        meta["protection_year"], era_bins or ERA_BINS, labels=era_labels or ERA_LABELS)
    return meta


def describe_regions(reg_index) -> str:
    names = list(reg_index)
    if len(names) >= 5:
        return "all five macro-regions"
    if len(names) > 1:
        return ", ".join(names[:-1]) + " and " + names[-1]
    return names[0] if names else "one region"


def describe_creation_pulses(meta: pd.DataFrame, min_count: int = 4, top: int = 3) -> str:
    vc = meta["protection_year"].dropna().astype(int).value_counts()
    vc = vc[vc >= min_count].sort_values(ascending=False)
    if vc.empty:
        return "Creation dates are spread across the record without a single dominant pulse year."
    parts = [f"**{int(c)} units** gazetted together in **{int(y)}**" for y, c in vc.head(top).items()]
    return "Notable creation pulses: " + "; ".join(parts) + "."


def describe_spheres(meta: pd.DataFrame) -> str:
    vc = meta["sphere"].value_counts()
    return ", ".join(f"{int(c)} {s}" for s, c in vc.items() if s)


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


# Long SNUC category prefixes, replaced by their common acronym before
# truncation so ranked/composition chart labels keep the distinguishing part
# of each name instead of "RESERVA EXTRATIVISTA C…" for every RESEX.
CATEGORY_ABBR = {
    "RESERVA EXTRATIVISTA": "RESEX",
    "RESERVA BIOLÓGICA (REBIO)": "REBIO",  # a few territories already embed "(REBIO)"
    "RESERVA BIOLÓGICA": "REBIO",
    "FLORESTA NACIONAL": "FLONA",
}


def _abbreviate_category(name: str) -> str:
    upper = name.upper()
    for prefix, abbr in CATEGORY_ABBR.items():
        if upper.startswith(prefix):
            return abbr + name[len(prefix):]
    return name


def build_place_labels(meta):
    """territory → 'Name · UF·Region' for chart y-axes."""
    m = {}
    for _, r in meta.iterrows():
        uf = r.get("uf") if isinstance(r.get("uf"), str) else "?"
        reg = REGION_ABBR.get(r.get("region"), "?")
        short_name = agg._shorten(_abbreviate_category(r["territory"]), 24)
        m[r["territory"]] = f"{short_name} · {uf}·{reg}"
    return m


# ---------------------------------------------------------------- grouped metrics

def grouped_metrics(summary, meta, by):
    s = summary.merge(meta[["group", "territory", by]], on=["group", "territory"], how="left")
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]
    g = s.groupby(by, observed=True).agg(
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
    p = panel if by in panel.columns else panel.merge(
        meta[["group", "territory", by]], on=["group", "territory"], how="left")
    rows = []
    for val, sub in p.groupby(by, observed=True):
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


def breakdown_block(title, note, g):
    L = [f"## {title}", "", note, ""]
    L += md_table(
        ["Stratum", "n", "Σ area (ha)", "Forest chg core/buf %", "GFC loss core/buf %", "Protection gap pp"],
        [[idx, int(r["n"]), fmt(r["area"], "", 0),
          f"{fmt(r['t_fc'])} / {fmt(r['b_fc'])}", f"{fmt(r['t_gfc'])} / {fmt(r['b_gfc'])}",
          fmt(r["gap"], "", 1)] for idx, r in g.iterrows()],
    )
    return L


# ---------------------------------------------------------------- creation-era figure

def chart_creation_outcomes(summary, meta, fig_dir: Path, era_labels=None, milestones=None,
                            unit_word="forest") -> Path:
    """How outcomes relate to WHEN each unit was gazetted: era bars (left) and
    creation-year vs protection-gap scatter by region (right)."""
    era_labels = era_labels or ERA_LABELS
    milestones = MILESTONES if milestones is None else milestones
    s = summary.merge(
        meta[["group", "territory", "creation_era", "protection_year", "region"]],
        on=["group", "territory"], how="left")
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(15, 5.4))

    g = s.groupby("creation_era", observed=True).agg(
        n=("territory", "size"),
        gap=("protection_gap", "mean"),
        core_loss=("t_gfc_loss_pct_of_2000_cover", "mean"),
    ).reindex(era_labels)
    x = np.arange(len(g))
    w = 0.4
    ax0.bar(x - w / 2, g["gap"], w, label="Protection gap (pp)", color="#166534")
    ax0.bar(x + w / 2, g["core_loss"], w, label="Core GFC loss (%)", color="#b03a2e")
    ax0.set_xticks(x, [f"{e}\n(n={int(v) if not np.isnan(v) else 0})" for e, v in zip(g.index, g["n"])],
                    fontsize=8)
    ax0.set_title("Outcomes by creation era (policy period)")
    ax0.set_ylabel("pp  /  % of 2000 cover")
    ax0.axhline(0, color="#888", lw=.8)
    ax0.legend(fontsize=8)
    ax0.grid(axis="y", alpha=0.3)

    region_color = {"Norte": "#2e7d32", "Centro-Oeste": "#b45309", "Nordeste": "#7c3aed",
                    "Sudeste": "#2563eb", "Sul": "#059669"}
    for reg, sub in s.dropna(subset=["protection_year"]).groupby("region"):
        ax1.scatter(sub["protection_year"], sub["protection_gap"], s=34, alpha=0.8,
                    color=region_color.get(reg, "#444444"), label=reg)
    sd = s.dropna(subset=["protection_year", "protection_gap"])
    if len(sd) >= 3:
        b, a = np.polyfit(sd["protection_year"], sd["protection_gap"], 1)
        xs = np.array([sd["protection_year"].min(), sd["protection_year"].max()])
        ax1.plot(xs, a + b * xs, "k--", lw=1, label=f"trend ({b:+.2f} pp/yr)")
    for yr, lbl in milestones:
        ax1.axvline(yr, color="#999", ls=":", lw=0.8)
    ax1.set_xlabel("Year of creation (decree)")
    ax1.set_ylabel("Protection gap (pp)")
    ax1.set_title("Creation year vs protection gap")
    ax1.legend(fontsize=7, ncol=2)
    ax1.grid(alpha=0.3)

    fig.suptitle(f"When a {unit_word} was created and how it has fared", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_creation_era_outcomes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_sphere_outcomes(sphere_tbl: pd.DataFrame, fig_dir: Path) -> Path:
    """Bar chart of protection gap / core GFC loss by governance sphere
    (Federal / Estadual / Municipal) — only meaningful when a dataset mixes
    spheres (RESEX, REBIO); Flona is all-Federal so this axis is skipped there."""
    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    x = np.arange(len(sphere_tbl))
    w = 0.35
    ax.bar(x - w / 2, sphere_tbl["gap"], w, label="Protection gap (pp)", color="#166534")
    ax.bar(x + w / 2, sphere_tbl["t_gfc"], w, label="Core GFC loss (%)", color="#b03a2e")
    ax.set_xticks(x, [f"{i}\n(n={int(r['n'])})" for i, r in sphere_tbl.iterrows()], fontsize=9)
    ax.set_title("Outcomes by governance sphere")
    ax.set_ylabel("pp  /  % of 2000 cover")
    ax.axhline(0, color="#888", lw=.8)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gp_sphere_outcomes.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


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

    n_states = int(meta["uf"].nunique())
    yr_min = int(meta["protection_year"].min())
    yr_max = int(meta["protection_year"].max())
    sphere_n0 = int(meta["sphere"].nunique())
    n_regions = int(meta["region"].nunique())
    n_missing_terr = len(cfg.get("missing_territory") or [])
    n_total = cfg.get("n_requested") or (n + len(cfg.get("excluded") or []) + n_missing_terr)
    unit_word0 = cfg.get("unit_word", "unit")
    intro3 = cfg["intro3"]
    if intro3 == "__AUTOFILL__":
        excl_bits = []
        if cfg.get("excluded"):
            excl_bits.append(f"{len(cfg['excluded'])} large polygon(s) excluded (quadrant exports)")
        if n_missing_terr:
            excl_bits.append(f"{n_missing_terr} excluded for a missing core-territory export, see note below")
        excl_note = f" ({n} analysable; {'; '.join(excl_bits)})" if excl_bits else ""
        sphere_clause = (f"across {sphere_n0} governance spheres ({describe_spheres(meta)})"
                          if sphere_n0 > 1 else "under a single governance sphere")
        intro3 = (
            f"All **{n_total} {cfg.get('category_label', run.label)} {unit_word0}s**{excl_note}, "
            f"spanning **{n_states} states and {describe_regions(_order_regions(meta['region'].dropna().unique()))}**, "
            f"{sphere_clause}, gazetted between **{yr_min} and {yr_max}**, analysed over "
            "1985–2024. Each protected **core** is referenced against its surrounding "
            "**10 km buffer** ring; rates are area-normalised (% of each area per year) "
            "so small and large units weigh equally and core and buffer are directly "
            f"comparable. Every unit shares the same SNUC category ({cfg.get('category_label','')}) "
            f"and protection group ({cfg.get('group_label','')}) — this is a national, "
            "single-category census of the estate.")

    L = [
        f"# {cfg['title3']}",
        "",
        intro3,
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
    sphere_n = sphere_n0
    unit_word = unit_word0
    category_label = cfg.get("category_label", run.label)
    group_label = cfg.get("group_label", "")

    L += [
        "",
        f"The **protection gap** (buffer minus core canopy loss) is positive for "
        f"**{n_pos} of {n}** {unit_word}s. Buffers also carry markedly more anthropic "
        f"land use by 2024 ({fmt(s['b_anthropic_2024_pct_of_area'].mean(), ' %')} vs "
        f"{fmt(s['t_anthropic_2024_pct_of_area'].mean(), ' %')} inside): these units sit "
        f"inside actively-cleared surroundings, not pristine ones.",
        "",
    ]
    if sphere_n <= 1:
        sphere_name = meta["sphere"].dropna().iloc[0] if meta["sphere"].notna().any() else "—"
        L += [
            f"All {n} analysable units share the same SNUC category ({category_label}, "
            f"{group_label}) and governance sphere ({sphere_name}) — the axes that "
            "distinguished the single-state Pará report do not vary here. What varies "
            "instead is **where** each unit sits and **when** it was created (§ below).",
            "",
        ]
    else:
        L += [
            f"All {n} analysable units share the same SNUC category ({category_label}, "
            f"{group_label}), but unlike the Florestas Nacionais (all-Federal), this "
            f"category exists at more than one level of government: {describe_spheres(meta)}. "
            "Governance sphere joins region and creation year as a real cross-sectional "
            "axis here (§ below).",
            "",
        ]

    reg = grouped_metrics(summary, meta, "region")
    if len(reg) > 1:
        reg = reg.reindex(_order_regions(reg.index))
        L += breakdown_block(
            "Breakdown by macro-region",
            f"The selection spans {describe_regions(reg.index)}. Region conditions both "
            "the protected core (biome, historical clearing) and the frontier pressing on "
            "its buffer.",
            reg,
        ) + [""]

    if sphere_n > 1:
        sph = grouped_metrics(summary, meta, "sphere")
        sph_order = [s for s in ["Federal", "Estadual", "Municipal"] if s in sph.index]
        sph = sph.reindex(sph_order + [s for s in sph.index if s not in sph_order])
        L += breakdown_block(
            "Breakdown by governance sphere",
            "Federal, state and municipal units answer to different agencies "
            "(ICMBio vs. state/municipal environment secretariats) with different "
            "staffing and enforcement capacity.",
            sph,
        ) + ["", f"![sphere outcomes](figures/{figs['sphere'].name})", ""]

    L += [
        "",
        f"## When the {unit_word}s were created (creation era)",
        "",
        f"Gazettement years run from **{yr_min} to {yr_max}**, spanning "
        f"{cfg.get('policy_span_note', 'the relevant forest/conservation-policy milestones')}. "
        f"{describe_creation_pulses(meta)}",
        "",
        f"![creation era outcomes](figures/{figs['creation'].name})",
        "",
    ]
    era_labels = cfg.get("era_labels", ERA_LABELS)
    era = grouped_metrics(summary, meta, "creation_era")
    era = era.reindex([e for e in era_labels if e in era.index])
    if len(era) > 1:
        L += breakdown_block(
            "Breakdown by creation era",
            f"Grouped by the decree year of each {unit_word}, bucketed to the policy "
            "eras above. Earlier creation means more of the 1985–2024 satellite record "
            "is post-protection; later creation means the unit was still consolidating "
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
        + f"buffers ({fmt(core_fire, ' %', 3)} vs {fmt(buf_fire, ' %', 3)} of area / yr).",
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
    missing_terr = cfg.get("missing_territory") or []
    if missing_terr:
        L += [
            f"> **Note — coverage gap.** {len(missing_terr)} of {cfg.get('n_requested', '?')} "
            f"{unit_word0}s have a 10 km **buffer** export in this batch but no "
            "**core-territory** export (the source batch reports them as processed, but "
            "the territory-side raster is missing on disk); they cannot be scored for a "
            "protection gap and are excluded entirely from this report, not just from "
            "the aggregate metrics. This is a data-completeness gap in the source batch, "
            "not a modelling choice — treat every figure below as describing the "
            f"**{n}-{unit_word0} subset with a core export**, not the full national "
            f"population. Missing: {', '.join(missing_terr)}.",
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
    scope_piv = tables["scope_amp"]
    n_terr = panel_t[["group", "territory"]].drop_duplicates().shape[0]
    unit_word = cfg.get("unit_word", "unit")
    n_states = int(meta["uf"].nunique())
    sphere_n = int(meta["sphere"].nunique())

    L = [
        f"# {cfg['title4']}",
        "",
        "Tests three linked hypotheses about *why* deforestation, fire and forest "
        "recovery move the way they do, joining the batch time-series to the "
        "federal/state political record (`political_context_brazil`) and the annual "
        "policy-strength scores (`policy_context_brazil`). Every rate below is the "
        f"area-normalised annual value (% of area / yr) averaged across {n_terr} "
        f"{unit_word}s; associations, not proof of cause.",
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
        f"regrowth is {reg_word} (**{signed_pct(window['regrowth'], stable['regrowth'])}**). "
        f"Because these {unit_word}s span {n_states} states, both the federal AND "
        "state-governor axes carry real cross-sectional variation, unlike a "
        "single-state selection.",
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
           "the posture signal is weak or mixed here."),
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
                        "the line while the core stays comparatively flat.")
            return ("the core's clearing swing around government changes is as large as "
                    "or larger than the buffer's — the boundary does not clearly deflect "
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
                        "left) while cores keep flammable native cover.")
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
        "## Variation by macro-region",
        "",
        f"*The selection spans {describe_regions(_order_regions(meta['region'].dropna().unique()))} "
        "and several biomes, so region is a meaningful axis — unlike a single-state "
        "set, where category/sphere alone would carry the variation.*",
        "",
    ]
    g = rates_by_attr(panel, meta, "region")
    g = g.reindex(_order_regions(g.index))
    L += [f"![regional comparison](figures/{figs['regional'].name})", ""]
    L += md_table(
        ["Region", "n", "Defor core/buf %", "Fire core/buf %"],
        [[idx, int(r["n"]),
          f"{fmt(r['core_defor'], '', 3)} / {fmt(r['buf_defor'], '', 3)}",
          f"{fmt(r['core_fire'], '', 3)} / {fmt(r['buf_fire'], '', 3)}"]
         for idx, r in g.iterrows()],
    )
    L.append("")

    if sphere_n > 1:
        gs = rates_by_attr(panel, meta, "sphere")
        sph_order = [s for s in ["Federal", "Estadual", "Municipal"] if s in gs.index]
        gs = gs.reindex(sph_order + [s for s in gs.index if s not in sph_order])
        L += [
            "---",
            "",
            "## Variation by governance sphere",
            "",
            f"*{describe_spheres(meta)} — different agencies, different enforcement "
            "capacity, same protection category.*",
            "",
            f"![sphere outcomes](figures/{figs['sphere'].name})",
            "",
        ]
        L += md_table(
            ["Sphere", "n", "Defor core/buf %", "Fire core/buf %"],
            [[idx, int(r["n"]),
              f"{fmt(r['core_defor'], '', 3)} / {fmt(r['buf_defor'], '', 3)}",
              f"{fmt(r['core_fire'], '', 3)} / {fmt(r['buf_fire'], '', 3)}"]
             for idx, r in gs.iterrows()],
        )
        L.append("")

    L += [
        "---",
        "",
        "## H3 — Policy strength over time and by creation era" + (" / sphere" if sphere_n > 1 else ""),
        "",
        "*Claim: protection is more robust where the national policy regime is "
        "stronger; here, every unit shares the same protection category, so the "
        "cross-sectional recognition test becomes a cross-sectional* creation-era"
        + (" / governance-sphere" if sphere_n > 1 else "") + " *test instead.*",
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
        f"Read with care: **within already-protected {unit_word}s the over-time signal "
        "is confounded**. Primary-vegetation clearing is front-loaded (most of it "
        "predates or coincides with creation, then decays), while fire is driven by "
        "accumulated degradation and drought as much as by governance. The clean "
        "policy signal is cross-sectional — here, by *when* the unit was created"
        + (" or under which sphere it sits" if sphere_n > 1 else "") +
        " — not temporal. (Regrowth's drop to zero in 2023–24 is a data-coverage edge, "
        "not a real collapse.)",
        "",
        "### Cross-section — creation era",
        "",
        f"![creation era outcomes](figures/{figs['creation'].name})",
        "",
        f"See Report 3 for the era-by-era table (Breakdown by creation era). Every "
        f"{unit_word} here is a {cfg.get('category_label', runs[0].label)} under "
        f"{cfg.get('group_label', '')} — the protection-*category* cross-section that "
        "distinguishes ILs vs UCs, or strict vs sustainable-use units elsewhere in "
        "this project, is not available in a single-category selection; creation era"
        + (", and governance sphere," if sphere_n > 1 else "") +
        " is the closest analogue for a policy-recognition test.",
        "",
        "---",
        "",
        "## Caveats",
        "",
        "- Observational associations across 1985–2024; deforestation drivers "
        "(commodity prices, roads, biome) are not controlled for.",
    ]
    if sphere_n <= 1:
        sphere_name = meta["sphere"].dropna().iloc[0] if meta["sphere"].notna().any() else "—"
        L.append(
            f"- Every analysable unit shares SNUC category ({cfg.get('category_label', '')}), "
            f"protection group ({cfg.get('group_label', '')}) and governance sphere "
            f"({sphere_name}); no category/sphere contrast is possible in this dataset "
            "(see the single-state companion reports for that axis).")
    else:
        L.append(
            f"- Every analysable unit shares SNUC category ({cfg.get('category_label', '')}) "
            f"and protection group ({cfg.get('group_label', '')}); no category/group "
            f"contrast is possible, but governance sphere varies ({describe_spheres(meta)}) "
            "and is tested above.")
    L += [
        f"- {unit_word.capitalize()}s span {n_states} states across "
        f"{meta['region'].nunique()} macro-regions and several biomes; state "
        "ideology is joined on each unit's own UF, so the state-governor axis carries "
        "real cross-sectional variation here (unlike a single-state selection).",
        "- MapBiomas deforestation/fire series begin in 1987; Hansen loss in 2001. "
        "Government-change and posture windows inherit those coverage limits.",
        "- Creation-era and, where applicable, sphere strata are uneven in size; read "
        "small strata (n<5) as indicative only.",
    ]
    if cfg.get("excluded"):
        L.append(
            f"- {len(cfg['excluded'])} large polygon(s) exported in quadrants "
            f"({', '.join(cfg['excluded'])}) are omitted from all rates here.")
    if cfg.get("missing_territory"):
        L.append(
            f"- **Coverage gap**: {len(cfg['missing_territory'])} of "
            f"{cfg.get('n_requested', '?')} {unit_word}s in the source batch have no "
            "core-territory export (buffer-only) and are excluded from this report "
            f"entirely; see Report 3 for the full list. All rates below describe the "
            f"{n_terr}-{unit_word} subset with a usable core export, not the full "
            "national population of this category.")
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
        "## Governance, policy & manuscripts",
        "",
        f"- [{cfg['title3']}](report_group_comparison.md)",
        f"- [{cfg['title4']}](report_governance_policy.md)",
    ]
    for m in cfg.get("manuscripts", []):
        rows.append(f"- [Manuscript — {m['title']}]({m['file']})")
    rows += ["", f"Built by `{Path(__file__).name}`.", _RM_END]
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

    # Detect a silent export gap: batches where the buffer ring exported for
    # more units than the protected core did (territory/ dir short of buffer/).
    batch_path = Path(cfg["batch"])
    buf_names = sorted({p.name.split("_Buffer_")[0] for p in (batch_path / "buffer").glob("*")}) \
        if (batch_path / "buffer").is_dir() else []
    terr_names = sorted(d.name for d in (batch_path / "territory").iterdir() if d.is_dir()) \
        if (batch_path / "territory").is_dir() else []
    missing_territory = sorted(set(buf_names) - set(terr_names))
    cfg["missing_territory"] = missing_territory
    cfg["n_requested"] = len(set(buf_names) | set(terr_names))
    if missing_territory:
        print(f"  WARNING: {len(missing_territory)} unit(s) have a buffer export "
              f"but no core-territory export — excluded upstream of the loader: "
              f"{missing_territory[:5]}{'...' if len(missing_territory) > 5 else ''}")

    run = agg.load_batch(batch_path, cfg["label"])
    run.kind = "conservation"
    gov.GROUP_COLOR_BY_LABEL[cfg["label"]] = gov.GROUP_COLOR["conservation"]
    excluded = [r.name for r in run.results if r.territory.comparison is None]
    run.results = [r for r in run.results if r.territory.comparison is not None]
    cfg["excluded"] = excluded
    runs = [run]
    print(f"[{cfg['label']}] {len(run.results)} forests"
          + (f"  (excluded quadrant-split: {excluded})" if excluded else ""))

    print("  recovering UF + creation year …")
    meta = gov.load_territory_metadata(runs)
    meta = augment_meta_era(meta, cfg.get("era_bins"), cfg.get("era_labels"))
    place_labels = build_place_labels(meta)
    sphere_n = int(meta["sphere"].nunique())

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

    panel = gov.build_rate_panel(runs, meta)
    panel_t = panel[panel["scope"] == "territory"].copy()

    figs_gp = {
        "rates": gov.chart_group_rate_curves(panel, fig_dir),
        "dist": gov.chart_group_distributions(summary, runs, fig_dir),
        "creation": chart_creation_outcomes(
            summary, meta, fig_dir, cfg.get("era_labels"), cfg.get("milestones"),
            cfg.get("unit_word", "unit")),
    }
    if sphere_n > 1:
        sph_tbl = grouped_metrics(summary, meta, "sphere")
        figs_gp["sphere"] = chart_sphere_outcomes(sph_tbl, fig_dir)
    change_path, change_df = gov.chart_change_effect(panel_t, fig_dir)
    posture_path, posture_grp, posture_counts = gov.chart_posture_effect(panel_t, fig_dir)
    policy_path = gov.chart_policy_timeline(panel_t, fig_dir)
    regime_tbl = gov.build_regime_table(panel_t)
    scope_path, scope_amp, scope_piv = gov.chart_governance_scope(panel, fig_dir)
    regional_path = gov.chart_regional(panel, fig_dir)
    figs_gov = {"change": change_path, "posture": posture_path, "policy": policy_path,
                "scope": scope_path, "regional": regional_path, "creation": figs_gp["creation"]}
    if "sphere" in figs_gp:
        figs_gov["sphere"] = figs_gp["sphere"]

    panel.to_csv(out / "data" / "governance_rate_panel.csv", index=False)
    meta.to_csv(out / "data" / "territory_metadata.csv", index=False)

    p3 = write_group_comparison(out, cfg, runs, summary, meta, panel, figs_gp)
    p4 = write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs_gov,
                          {"change": change_df, "posture": posture_grp, "regime": regime_tbl,
                           "scope_amp": scope_piv})
    link_reports_in_readme(out, cfg)
    print(f"  wrote {p3.name}, {p4.name}")
    return summary, meta, panel, panel_t


ROOT = "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report"
DATASETS = {
    "national_forests_brasil": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260814_231734",
        "out": f"{ROOT}/national_forests_brasil",
        # label MUST contain "Conserv" so gov.chart_recognition_tiers fires its
        # conservation branch.
        "label": "Florestas Nacionais do Brasil (Conservação federal, Uso Sustentável)",
        "unit_word": "forest",
        "category_label": "*Floresta Nacional*",
        "group_label": "*Uso Sustentável*",
        "policy_span_note": ("every major forest-law milestone (1965 Forest Code, "
                              "1988 Constitution, 2000 SNUC, 2004 PPCDAm, 2012 Forest Code)"),
        "title3": "Report 3 — Federal National Forests of Brazil: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Federal National Forests of Brazil",
        "manuscripts": [
            {"file": "MANUSCRIPT_core_buffer_national_forests_brasil.md",
             "title": "The boundary holds nationwide — core vs. buffer across 64 Brazilian National Forests"},
            {"file": "MANUSCRIPT_governance_policy_national_forests_brasil.md",
             "title": "Six decades of Florestas Nacionais — governance, legislation and political cycles"},
        ],
        "intro3": (
            "All **68 federal Florestas Nacionais** returned by the national CNUC "
            "query (64 analysable as single-tile exports; 4 large polygons excluded, "
            "see note below), spanning **22 states and all five macro-regions**, "
            "gazetted between **1934 and 2023**, analysed over 1985–2024. Each "
            "protected **core** is referenced against its surrounding **10 km "
            "buffer** ring; rates are area-normalised (% of each area per year) so "
            "small and large units weigh equally and core and buffer are directly "
            "comparable. Unlike the companion Pará-only report, every unit here "
            "shares the same SNUC category and sphere — this is a national, "
            "single-instrument census of the *Floresta Nacional* estate."),
    },
    "extractive_reserves_brasil": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260815_055037",
        "out": f"{ROOT}/extractive_reserves_brasil",
        "label": "Reservas Extrativistas do Brasil (Conservação, Uso Sustentável)",
        "unit_word": "reserve",
        "category_label": "*Reserva Extrativista*",
        "group_label": "*Uso Sustentável*",
        # RESEX is a post-1990 instrument (Decreto 98.897/1990, traditional/extractive
        # peoples); its creation years don't reach back to the 1965/1988 milestones.
        "era_bins": [0, 1994, 1999, 2004, 2012, 3000],
        "era_labels": ["1990–1994", "1995–1999", "2000–2004", "2005–2012", "2013–2024"],
        "milestones": [(1990, "1990 RESEX decree"), (2000, "2000 SNUC"),
                       (2004, "2004 PPCDAm"), (2012, "2012 Code")],
        "policy_span_note": ("the RESEX instrument's own history (1990 founding decree, "
                              "2000 SNUC, 2004 PPCDAm, 2012 Forest Code)"),
        "title3": "Report 3 — Extractive Reserves of Brazil: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Extractive Reserves of Brazil",
        "manuscripts": [
            {"file": "MANUSCRIPT_core_buffer_extractive_reserves_brasil.md",
             "title": "Core vs. buffer across Brazil's Extractive Reserves"},
            {"file": "MANUSCRIPT_governance_policy_extractive_reserves_brasil.md",
             "title": "Governance, legislation and political cycles across Brazil's Extractive Reserves"},
        ],
        "intro3": "__AUTOFILL__",
    },
    "biological_reserves_brasil": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260815_065810",
        "out": f"{ROOT}/biological_reserves_brasil",
        "label": "Reservas Biológicas do Brasil (Conservação, Proteção Integral)",
        "unit_word": "reserve",
        "category_label": "*Reserva Biológica*",
        "group_label": "*Proteção Integral*",
        "policy_span_note": ("every major forest-law milestone (1965 Forest Code, "
                              "1988 Constitution, 2000 SNUC, 2004 PPCDAm, 2012 Forest Code)"),
        "title3": "Report 3 — Biological Reserves of Brazil: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Biological Reserves of Brazil",
        "manuscripts": [
            {"file": "MANUSCRIPT_core_buffer_biological_reserves_brasil.md",
             "title": "Core vs. buffer across Brazil's Biological Reserves"},
            {"file": "MANUSCRIPT_governance_policy_biological_reserves_brasil.md",
             "title": "Governance, legislation and political cycles across Brazil's Biological Reserves"},
        ],
        "intro3": "__AUTOFILL__",
    },
}


if __name__ == "__main__":
    which = sys.argv[1:] or list(DATASETS)
    for key in which:
        run_dataset(DATASETS[key])
        print(f"Done → {DATASETS[key]['out']}")
