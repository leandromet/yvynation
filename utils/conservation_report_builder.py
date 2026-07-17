#!/usr/bin/env python3
"""Build a full yvynation report set (aggregator + governance) for ONE batch
folder of Brazilian *conservation units*, with dataset-aware, data-driven prose.

Reuses batch_report_aggregator (agg) and governance_policy_report (gov) for all
data assembly and figures; only the two headline markdown reports
(report_group_comparison.md, report_governance_policy.md) are re-written here so
their titles and interpretation fit a single-system, single-state UC dataset
(the stock writers hardcode an Indigenous-vs-Conservation, all-Brazil narrative).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/leandromb/google_eengine/yvynation/utils")
import batch_report_aggregator as agg  # noqa: E402
import governance_policy_report as gov  # noqa: E402


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
    p = panel.merge(meta[["group", "territory", by]], on=["group", "territory"], how="left")
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


def breakdown_block(title, note, g):
    """Markdown for a grouped_metrics table (core/buffer + gap)."""
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
        ["Metric", "Protected core", f"10 km buffer"],
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
        f"**{n_pos} of {n}** areas — the clearest single sign that the boundaries are "
        f"holding. Buffers also carry markedly more anthropic land use by 2024 "
        f"({fmt(s['b_anthropic_2024_pct_of_area'].mean(), ' %')} vs "
        f"{fmt(s['t_anthropic_2024_pct_of_area'].mean(), ' %')} inside), i.e. these "
        f"units sit inside actively-cleared surroundings rather than pristine ones.",
        "",
    ]

    # breakdowns by protection group (grupo), governance sphere, and SNUC category
    grp = grouped_metrics(summary, meta, "recognition_tier")
    if len(grp) > 1:
        L += breakdown_block(
            "Breakdown by protection group (SNUC)",
            "Uso Sustentável (multiple-use, e.g. Florestas Nacionais) vs. Proteção "
            "Integral (strict protection, e.g. Parques, Reservas Biológicas, "
            "Estações Ecológicas). The protection gap is what each core saves "
            "relative to its own buffer.",
            grp,
        ) + [""]
    sph = grouped_metrics(summary, meta, "sphere")
    if len(sph) > 1:
        L += breakdown_block(
            "Breakdown by governance sphere",
            "Who administers the unit — federal (ICMBio), state (Ideflor-Bio), or "
            "municipal. Sphere shapes *both* scopes: municipal units cluster near "
            "cities where the surrounding buffer is far more converted, so their "
            "buffers clear faster even where the core holds.",
            sph,
        ) + [""]
    cat = grouped_metrics(summary, meta, "category")
    if len(cat) > 1:
        L += breakdown_block(
            "Breakdown by SNUC category",
            "The management category (Parque, Reserva Biológica, Estação "
            "Ecológica, Monumento Natural, Refúgio de Vida Silvestre, Floresta). "
            "Category encodes both the permitted uses inside the core and, "
            "indirectly, the kind of landscape each unit sits in — so it "
            "conditions core and buffer trajectories together.",
            cat.sort_values("gap", ascending=False),
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
            "aggregate metrics (the loader reads only single-tile exports). "
            + ("This unit is analysed in full in the National Forests report set."
               if "JAMANXIM" in " ".join(cfg["excluded"]).upper() else ""),
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

    L = [
        f"# {cfg['title4']}",
        "",
        "Tests three linked hypotheses about *why* deforestation, fire and forest "
        "recovery move the way they do, joining the batch time-series to the "
        "federal/state political record (`political_context_brazil`) and the annual "
        "policy-strength scores (`policy_context_brazil`). Every rate below is the "
        f"area-normalised annual value (% of area / yr) averaged across {n_terr} "
        "areas; associations, not proof of cause.",
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
    # data-driven posture verdict
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
        + " (Within a single state the political panel varies mostly through the "
          "federal cycle, so read posture cautiously.)",
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
    # data-driven scope reading — use the change-window contrast (cleaner than the
    # posture contrast in a single-state panel) and only cite a ratio when both the
    # core and buffer swings are positive, so signs don't produce nonsense ratios.
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
        "## Variation by sphere and SNUC category",
        "",
        "*These areas share one state and biome, so macro-regional variation is not "
        "informative; the meaningful axes are the governance sphere and the SNUC "
        "category. Both the protected **core** and its 10 km **buffer** are shown, "
        "because sphere and category condition the surrounding landscape as much as "
        "the interior.*",
        "",
    ]
    for by, label in (("sphere", "Sphere"), ("category", "SNUC category"),
                      ("recognition_tier", "Protection group")):
        g = rates_by_attr(panel, meta, by)
        if len(g) <= 1:
            continue
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
        "*Claim: protection is more robust where areas hold stronger recognition.*",
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
        "Read with care: **within already-protected areas the over-time signal is "
        "confounded**. Primary-vegetation clearing is front-loaded (most of it "
        "predates or coincides with protection, then decays), while fire is driven "
        "by accumulated degradation and drought as much as by governance. The clean "
        "policy signal is cross-sectional, not temporal. (Regrowth's drop to zero in "
        "2023–24 is a data-coverage edge, not a real collapse.)",
        "",
        "### Cross-section — recognition tier",
        "",
        f"![recognition tiers](figures/{figs['tiers'].name})",
        "",
    ]
    if "conservation" in tiers and not tiers["conservation"].empty:
        L += ["**By protection group**", ""]
        L += md_table(
            ["Group", "n", "Forest change %", "GFC loss %", "Protection gap pp", "Defor rate %"],
            [[idx, int(r["n"]), fmt(r["forest_change"], " %"), fmt(r["gfc_loss"], " %"),
              fmt(r["protection_gap"], " pp"), fmt(r["defor_rate"], " %", 3)]
             for idx, r in tiers["conservation"].iterrows()],
        )
        L.append("")
    if "conservation_sphere" in tiers and len(tiers["conservation_sphere"]) > 1:
        L += ["**By governance sphere**", ""]
        L += md_table(
            ["Sphere", "n", "GFC loss %", "Protection gap pp"],
            [[idx, int(r["n"]), fmt(r["gfc_loss"], " %"), fmt(r["protection_gap"], " pp")]
             for idx, r in tiers["conservation_sphere"].iterrows()],
        )
        L.append("")

    L += [
        "---",
        "",
        "## Caveats",
        "",
        "- Observational associations across 1985–2024; deforestation drivers "
        "(commodity prices, roads, biome) are not controlled for.",
        "- All areas fall in one state, so the state-ideology panel varies chiefly "
        "through the federal cycle; posture and change-window effects are dominated "
        "by federal transitions.",
        "- MapBiomas deforestation/fire series begin in 1987; Hansen loss in 2001. "
        "Government-change and posture windows inherit those coverage limits.",
        "- Recognition tiers are coarse and some strata are small (n < 5); read them "
        "as indicative.",
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
    """Refresh the discoverability block in the aggregator's README with the
    correct dataset-specific titles and a link to the manuscript. Idempotent."""
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
    rows += ["", "Built by `conservation_report_builder.py`.", _RM_END]
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
    run.kind = "conservation"
    gov.GROUP_COLOR_BY_LABEL[cfg["label"]] = gov.GROUP_COLOR["conservation"]
    # Drop areas with no loadable core land-cover — large polygons (>~1M ha)
    # are exported in four quadrant subfolders the aggregator loader cannot read.
    excluded = [r.name for r in run.results if r.territory.comparison is None]
    run.results = [r for r in run.results if r.territory.comparison is not None]
    cfg["excluded"] = excluded
    runs = [run]
    print(f"[{cfg['label']}] {len(run.results)} areas"
          + (f"  (excluded quadrant-split: {excluded})" if excluded else ""))

    # ---- aggregator layer (detailed per-area report + README + xlsx) --------
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
        charts[f"forest_change_ranked_{agg._slug(r.label)}"] = agg.chart_forest_change_ranked(summary, r, fig_dir)
        charts[f"landcover_composition_{agg._slug(r.label)}"] = agg.chart_landcover_composition(lc, r, fig_dir)
    for r in runs:
        agg.write_group_report(r, summary, out, img_root, charts)
    agg.write_index(runs, summary, out, charts, xlsx)

    # ---- governance layer ---------------------------------------------------
    print("  recovering UF + recognition tiers …")
    meta = gov.load_territory_metadata(runs)
    panel = gov.build_rate_panel(runs, meta)
    panel_t = panel[panel["scope"] == "territory"].copy()

    figs_gp = {
        "rates": gov.chart_group_rate_curves(panel, fig_dir),
        "dist": gov.chart_group_distributions(summary, runs, fig_dir),
    }
    change_path, change_df = gov.chart_change_effect(panel_t, fig_dir)
    posture_path, posture_grp, posture_counts = gov.chart_posture_effect(panel_t, fig_dir)
    policy_path = gov.chart_policy_timeline(panel_t, fig_dir)
    regime_tbl = gov.build_regime_table(panel_t)
    tiers_path, tiers = gov.chart_recognition_tiers(summary, meta, panel_t, fig_dir)
    scope_path, scope_amp, scope_piv = gov.chart_governance_scope(panel, fig_dir)
    figs_gov = {"change": change_path, "posture": posture_path, "policy": policy_path,
                "tiers": tiers_path, "scope": scope_path}

    panel.to_csv(out / "data" / "governance_rate_panel.csv", index=False)
    meta.to_csv(out / "data" / "territory_metadata.csv", index=False)

    p3 = write_group_comparison(out, cfg, runs, summary, meta, panel, figs_gp)
    p4 = write_governance(out, cfg, runs, summary, meta, panel, panel_t, figs_gov,
                          {"change": change_df, "posture": posture_grp, "regime": regime_tbl,
                           "tiers": tiers, "scope_amp": scope_piv})
    link_reports_in_readme(out, cfg)
    print(f"  wrote {p3.name}, {p4.name}")
    return summary, meta, panel, panel_t


DATASETS = {
    "national_forests": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260716_164417",
        "out": "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report/national_forests",
        "label": "Florestas e Parques Nacionais (Conservação federal, PA)",
        "title3": "Report 3 — Federal National Forests & Parks of Pará: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Federal conservation units of Pará",
        "manuscript": "MANUSCRIPT_land_use_policy_national_forests.md",
        "manuscript_title": "Sustainable-use vs strict protection on the same frontier",
        "intro3": (
            "The 17 **federal** conservation units of the Tapajós–Xingu–Carajás arc "
            "of Pará (13 Florestas Nacionais, *Uso Sustentável*; 4 Parques "
            "Nacionais, *Proteção Integral*) over 1985–2024, each protected **core** "
            "referenced against its surrounding **10 km buffer** ring. Rates are "
            "area-normalised (% of each area per year) so small and large units "
            "weigh equally and core and buffer are directly comparable."),
    },
    "para_state": {
        "batch": "/media/leandromb/iron8/Downloads_ubuntuWD/yvynation_batch_20260716_151954",
        "out": "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report/para_state",
        "label": "Unidades de Conservação do Pará (Conservação federal/estadual/municipal)",
        "title3": "Report 3 — Pará's protected-area mosaic: core vs. buffer",
        "title4": "Report 4 — Governance, ideology & policy recognition — Pará conservation units",
        "manuscript": "MANUSCRIPT_land_use_policy_para_conservation.md",
        "manuscript_title": "Who administers the boundary matters — sphere, category & the protection gap",
        "intro3": (
            "A selection of **26 conservation units in the state of Pará** spanning "
            "federal, state and municipal spheres and several SNUC categories "
            "(Parques, Reservas Biológicas, Estações Ecológicas, Monumentos "
            "Naturais, Refúgios de Vida Silvestre, one Floresta Nacional), over "
            "1985–2024, each protected **core** referenced against its surrounding "
            "**10 km buffer** ring. Rates are area-normalised (% of each area per "
            "year) so small and large units weigh equally and core and buffer are "
            "directly comparable."),
    },
}


if __name__ == "__main__":
    which = sys.argv[1:] or list(DATASETS)
    for key in which:
        run_dataset(DATASETS[key])
        print(f"Done → {DATASETS[key]['out']}")
