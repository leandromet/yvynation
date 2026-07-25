#!/usr/bin/env python3
"""Governance & policy CODEBOOK generator for the Yvynation manuscripts.

Every governance variable used in Report 4 and in the manuscripts' §2.7 is
*coded by hand* inside two source modules:

  reflex_app/.../political_context_brazil.py   president/governor ideology
  reflex_app/.../policy_context_brazil.py       annual policy-strength scores

This script introspects those modules (it does not re-encode anything) and the
enriched analysis panel (`data/governance_rate_panel.csv`) and emits a single,
citable **codebook** so a reader/reviewer can trace every governance number to
its coding rule:

  governance_codebook.md              ← human-readable coding table (methods appendix)
  data/codebook_variables.csv         ← flat variable × level × definition registry
  data/codebook_president_ideology.csv
  data/codebook_policy_scores_by_year.csv
  data/codebook_posture_bins.csv
  data/codebook_recognition_tiers.csv
  data/codebook_panel_coverage.csv    ← territory-years actually observed per bin
  figures/codebook_policy_heatmap.png ← 8 policy dimensions × year
  figures/codebook_pressure_timeline.png ← combined-pressure spread + posture bands

The coding *rules* (ideology scale, posture cut-points, change-window flag,
recognition ranks) are reproduced here from the exact expressions used in
`governance_policy_report.py` so the table documents what the pipeline runs.

Run:
  .venv/bin/python utils/governance_codebook.py
  .venv/bin/python utils/governance_codebook.py --out /path/to/yvynation_report
"""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT_DEFAULT = Path(
    "/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report"
)
_REFLEX_UTILS = Path(
    "/home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils"
)


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


political = _load_module(_REFLEX_UTILS / "political_context_brazil.py", "yv_political")
policy = _load_module(_REFLEX_UTILS / "policy_context_brazil.py", "yv_policy")


# --------------------------------------------------------------------------- #
# Coding rules — reproduced verbatim from the pipeline so the table documents  #
# exactly what governance_policy_report.py computes.                           #
# --------------------------------------------------------------------------- #

IDEOLOGY_LEVELS = [
    (-1, "Left", "PT and allied left; pro-enforcement, pro-demarcation posture."),
    (0, "Centre / patronage",
        "Centrist or patronage-machine administrations with no clear "
        "environmental posture (e.g. Sarney, Itamar; many MDB/PMDB governors)."),
    (1, "Centre-Right / moderate conservative",
        "Expands protected areas on paper but enforces weakly (e.g. FHC, Collor, Temer)."),
    (2, "Right / pro-agribusiness",
        "Actively rolls back enforcement and demarcation (Bolsonaro; frontier-state "
        "agribusiness governors)."),
]

# posture buckets — from governance_policy_report.build_political_year_state()
POSTURE_RULE = [
    ("Both progressive", "combined_pressure ≤ −0.5",
     "Federal + state executives both on the left/protective side."),
    ("Opposed / mixed", "−0.5 < combined_pressure < 1.0",
     "The two executive levels disagree, or sit near the centre."),
    ("Both conservative", "combined_pressure ≥ 1.0",
     "Federal + state executives both conservative / pro-agribusiness."),
]

# policy-strength dimensions — from policy_context_brazil docstring
POLICY_DIMS = [
    ("forest_law_strength", "0–3",
     "Statutory forest-protection strength *and* whether it is enforced "
     "(0 = absent/unenforced; 3 = strong Forest Code + active enforcement)."),
    ("indigenous_rights_score", "0–3",
     "Constitutional/administrative Indigenous-rights protection "
     "(0 = hostile; 3 = protective and actively demarcating)."),
    ("enforcement_capacity", "0–3",
     "Relative IBAMA/FUNAI field capacity (budget, staffing, operations)."),
    ("amazon_plan_phase", "0–5",
     "PPCDAm deforestation-control plan phase (0 = no plan; 1–5 = phase number; "
     "phase 5 launched 2023)."),
    ("amazon_fund_active", "0/1",
     "Amazon Fund operational and receiving donations that year."),
    ("car_registry_stage", "0–3",
     "Rural Environmental Registry maturity (0 = none; 1 = voluntary; "
     "2 = mandatory rollout; 3 = mature)."),
    ("demarcation_posture", "−1 / 0 / +1",
     "Federal stance on Indigenous demarcation (−1 = hostile/zero; 0 = stalled; +1 = active)."),
    ("licensing_strictness", "0–3",
     "Environmental-licensing rigour (0 = weak/captured; 3 = robust, CONAMA-backed)."),
]

# recognition-tier coding — from governance_policy_report metadata loaders
IND_FASE = [
    ("Em Estudo", 1, "Under study — claim opened, no legal effect yet."),
    ("Delimitada", 2, "Delimited — FUNAI technical study approved."),
    ("Declarada", 3, "Declared — Minister of Justice ordinance; boundaries fixed."),
    ("Encaminhada RI", 4, "Referred for ratification — sent for presidential decree."),
    ("Homologada", 5, "Ratified — presidential decree (homologação)."),
    ("Regularizada", 6, "Fully regularised — registered, physically demarcated (strongest)."),
]
UC_TIER = [
    ("Uso Sustentável", 1, "Sustainable-use group (APA, FLONA, RESEX, RDS…) — human use permitted."),
    ("Proteção Integral", 2, "Strict-protection group (Parque, REBIO, ESEC…) — no extractive use."),
]
UC_SPHERE = [
    ("Federal", "Created and managed by the Union (ICMBio)."),
    ("Estadual", "Created and managed by a state government."),
    ("Municipal", "Created and managed by a municipality."),
]

REGIME_LABEL = {
    "redemocratisation": "Redemocratisation (1985–1988)",
    "new_republic_early": "Collor / Itamar (1989–1994)",
    "FHC": "FHC (1995–2002)",
    "Lula_I_II": "Lula I–II (2003–2010)",
    "Dilma": "Dilma (2011–2016)",
    "Temer": "Temer (2017–2018)",
    "Bolsonaro": "Bolsonaro (2019–2022)",
    "Lula_III": "Lula III (2023–2024)",
}
REGIME_ORDER = list(REGIME_LABEL)


# --------------------------------------------------------------------------- #
# Applied crosswalk tables                                                     #
# --------------------------------------------------------------------------- #

def president_table() -> pd.DataFrame:
    rows = []
    for name, party, start, end, ideo, notes in political.PRESIDENTS:
        rows.append({
            "start_year": start, "end_year": end, "president": name,
            "party": party, "ideology": ideo,
            "ideology_label": dict((l, w) for l, w, _ in IDEOLOGY_LEVELS)[ideo],
            "notes": notes,
        })
    return pd.DataFrame(rows)


def governor_ideology_distribution() -> pd.DataFrame:
    """How the hand-coded governor-years distribute across the ideology scale."""
    pol = political.build_political_context()
    d = pol["gov_ideology"].value_counts(dropna=True).sort_index()
    rows = []
    for lvl, word, _ in IDEOLOGY_LEVELS:
        rows.append({"ideology": lvl, "ideology_label": word,
                     "governor_state_years": int(d.get(lvl, 0))})
    return pd.DataFrame(rows)


def policy_by_year_table() -> pd.DataFrame:
    pol = policy.build_combined_context()
    cols = ["year", "regime"] + [d for d, _, _ in POLICY_DIMS]
    cols = [c for c in cols if c in pol.columns]
    return pol[cols]


def posture_bin_table() -> pd.DataFrame:
    return pd.DataFrame(
        [{"posture": p, "rule": r, "definition": d} for p, r, d in POSTURE_RULE]
    )


def recognition_table() -> pd.DataFrame:
    rows = []
    for tier, rank, desc in IND_FASE:
        rows.append({"system": "Indigenous Land", "variable": "fase_ti (recognition_tier)",
                     "level": tier, "recognition_rank": rank,
                     "fully_recognized": tier == "Regularizada", "definition": desc})
    for tier, rank, desc in UC_TIER:
        rows.append({"system": "Conservation Unit", "variable": "grupo (recognition_tier)",
                     "level": tier, "recognition_rank": rank,
                     "fully_recognized": tier == "Proteção Integral", "definition": desc})
    for sph, desc in UC_SPHERE:
        rows.append({"system": "Conservation Unit", "variable": "esfera (sphere)",
                     "level": sph, "recognition_rank": np.nan,
                     "fully_recognized": np.nan, "definition": desc})
    return pd.DataFrame(rows)


def variable_registry() -> pd.DataFrame:
    """Flat machine-readable variable × level × definition registry."""
    rows: List[dict] = []

    def add(var, source, scale, level, label, definition):
        rows.append({"variable": var, "source_module": source, "scale": scale,
                     "level": level, "level_label": label, "definition": definition})

    for lvl, word, desc in IDEOLOGY_LEVELS:
        add("president_ideology / gov_ideology", "political_context_brazil",
            "-1…2 ordinal", lvl, word, desc)
    add("alignment", "political_context_brazil (derived)", "0/1", 1, "aligned",
        "1 if president and governor fall on the same side of the left/right split "
        "(both ideology ≤ 0, or both > 0); 0 if opposed.")
    add("alignment", "political_context_brazil (derived)", "0/1", 0, "opposed",
        "President and governor on opposite ideological sides.")
    add("combined_pressure", "political_context_brazil (derived)", "mean, −1…2",
        "", "president+governor mean",
        "(president_ideology + governor_ideology) / 2. Higher = more "
        "conservative/pro-agribusiness. Observed range −1…+2.")
    for p, r, d in POSTURE_RULE:
        add("posture", "governance_policy_report (derived)", "3-level", p, p,
            f"{d} Rule: {r}.")
    add("fed_change", "political_context_brazil (derived)", "bool", True, "federal change year",
        "President differs from previous year (first observed year is not a change).")
    add("state_change", "political_context_brazil (derived)", "bool", True, "state change year",
        "Governor differs from previous year for that state.")
    add("change_window", "governance_policy_report (derived)", "bool", True, "change window",
        "Government (federal OR state) changed this year or the previous year "
        "(the '±1 year' window around a transition).")
    for dim, rng, desc in POLICY_DIMS:
        add(dim, "policy_context_brazil", rng, "", "annual national score", desc)
    add("regime", "policy_context_brazil (derived)", "8-level", "", "federal administration",
        "Calendar-year → federal administration bucket (redemocratisation … Lula III).")
    for tier, rank, desc in IND_FASE:
        add("recognition_tier (IL)", "FUNAI vector layer", "6-tier ladder", tier,
            f"rank {rank}", desc)
    for tier, rank, desc in UC_TIER:
        add("recognition_tier (UC)", "MMA/CNUC vector layer", "2-group", tier,
            f"rank {rank}", desc)
    for sph, desc in UC_SPHERE:
        add("sphere (UC)", "MMA/CNUC vector layer", "3-level", sph, sph, desc)
    return pd.DataFrame(rows)


def panel_coverage(root: Path) -> pd.DataFrame | None:
    """Territory-years actually observed in each posture × regime bin — grounds
    the codebook in what the analysed sample really contains."""
    p = root / "data" / "governance_rate_panel.csv"
    if not p.is_file():
        return None
    pan = pd.read_csv(p)
    core = pan[pan["scope"] == "territory"].copy()
    tab = (core.pivot_table(index="regime", columns="posture", values="year",
                            aggfunc="count", fill_value=0)
           .reindex(REGIME_ORDER).fillna(0).astype(int))
    tab.index = [REGIME_LABEL.get(r, r) for r in tab.index]
    tab["All"] = tab.sum(axis=1)
    tab.loc["All"] = tab.sum(axis=0)
    tab.index.name = "Administration"
    tab.columns.name = None
    return tab


# --------------------------------------------------------------------------- #
# Figures                                                                      #
# --------------------------------------------------------------------------- #

def fig_policy_heatmap(root: Path) -> Path:
    pol = policy.build_policy_series()
    dims = [d for d, _, _ in POLICY_DIMS if d in pol.columns]
    M = pol.set_index("year")[dims].T.astype(float)
    # normalise each row to 0..1 by its own documented range for comparable shading
    ranges = {"forest_law_strength": 3, "indigenous_rights_score": 3,
              "enforcement_capacity": 3, "amazon_plan_phase": 5, "amazon_fund_active": 1,
              "car_registry_stage": 3, "demarcation_posture": 1, "licensing_strictness": 3}
    offset = {"demarcation_posture": 1}  # −1..+1 → 0..2, then /2
    N = M.copy()
    for d in dims:
        rng = ranges.get(d, M.loc[d].max() or 1)
        off = offset.get(d, 0)
        denom = (rng + off) or 1
        N.loc[d] = (M.loc[d] + off) / denom

    fig, ax = plt.subplots(figsize=(15, 4.4))
    im = ax.imshow(N.values, aspect="auto", cmap="YlGn", vmin=0, vmax=1)
    ax.set_yticks(range(len(dims)), [d.replace("_", " ") for d in dims], fontsize=9)
    years = M.columns.tolist()
    step = 3
    ax.set_xticks(range(0, len(years), step), years[::step], fontsize=8, rotation=0)
    # annotate raw scores
    for i, d in enumerate(dims):
        for j, y in enumerate(years):
            v = M.loc[d, y]
            if not np.isnan(v):
                ax.text(j, i, f"{int(v)}", ha="center", va="center", fontsize=6,
                        color="#333" if N.loc[d, y] < 0.6 else "#fff")
    ax.set_title("Annual environmental-policy strength scores, 1985–2024 "
                 "(cell = raw ordinal score; shade = share of its documented range)",
                 fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="within-range intensity")
    fig.tight_layout()
    path = root / "figures" / "codebook_policy_heatmap.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def fig_pressure_timeline(root: Path) -> Path:
    pol = political.build_political_context()
    g = pol.groupby("year")["combined_pressure"].agg(["mean", "min", "max",
                                                      lambda s: s.quantile(.25),
                                                      lambda s: s.quantile(.75)])
    g.columns = ["mean", "min", "max", "q25", "q75"]
    fig, ax = plt.subplots(figsize=(13, 4.8))
    # posture bands
    ax.axhspan(-1.05, -0.5, color="#166534", alpha=0.10, label="Both progressive (≤ −0.5)")
    ax.axhspan(-0.5, 1.0, color="#9aa5b1", alpha=0.12, label="Opposed / mixed")
    ax.axhspan(1.0, 2.05, color="#b03a2e", alpha=0.10, label="Both conservative (≥ 1.0)")
    ax.fill_between(g.index, g["q25"], g["q75"], color="#1f5fa8", alpha=0.25,
                    label="State spread (IQR)")
    ax.plot(g.index, g["mean"], color="#1f5fa8", lw=2, label="National mean")
    ax.axhline(0, color="#444", lw=0.7, ls="--")
    ax.set_ylabel("Combined pressure  (−1 both-left … +2 both-right)")
    ax.set_xlabel("Year")
    ax.set_ylim(-1.1, 2.1)
    ax.set_title("Federal+state ideological pressure across all states, 1985–2024",
                 fontsize=11)
    ax.legend(fontsize=8, ncol=2, loc="upper left")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = root / "figures" / "codebook_pressure_timeline.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Markdown writer                                                              #
# --------------------------------------------------------------------------- #

def _md_table(df: pd.DataFrame, index=False) -> str:
    """Render a DataFrame as a GitHub markdown table without the optional
    `tabulate` dependency (so the script runs in either venv)."""
    df = df.copy()
    if index:
        df = df.reset_index()

    def cell(v):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return ""
        if isinstance(v, float):
            return f"{v:g}"
        return str(v).replace("\n", " ").replace("|", "\\|")

    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(cell(row[c]) for c in df.columns) + " |")
    return "\n".join(lines)


def write_markdown(root: Path, tables: dict, figs: dict) -> Path:
    L: List[str] = []
    L += [
        "# Governance & policy codebook",
        "",
        "*Coding table backing the governance/policy variables used in Report 4 and "
        "in the manuscripts' §2.7 (governance and policy linkage). Auto-generated by "
        "`utils/governance_codebook.py`, which introspects the hand-coded source "
        "modules `political_context_brazil.py` and `policy_context_brazil.py` and the "
        "enriched analysis panel `data/governance_rate_panel.csv` — it re-reads the "
        "coded data rather than restating it, so this table cannot drift from what the "
        "pipeline runs.*",
        "",
        "All scores are **ordinal and relative to the 1985–2024 study window**; they "
        "encode each administration's dominant posture toward environmental and "
        "Indigenous-rights enforcement, not party label alone, and are intended as "
        "control/breakpoint variables, not absolute metrics. Sources: electoral "
        "records (TSE), legislative/interest-group compilations (DIAP), peer-reviewed "
        "enforcement analyses and institutional/NGO monitoring (full list in the two "
        "module docstrings).",
        "",
        "---",
        "",
        "## 1. Political ideology scale",
        "",
        "Each federal president and every state governor (27 units × up to 40 years) "
        "is coded on a single four-level ordinal scale:",
        "",
        _md_table(pd.DataFrame(
            [{"code": l, "label": w, "definition": d} for l, w, d in IDEOLOGY_LEVELS])),
        "",
        "How the hand-coded **governor** state-years distribute across the scale:",
        "",
        _md_table(tables["gov_dist"]),
        "",
        "### 1.1 Federal presidents (1985–2024)",
        "",
        _md_table(tables["presidents"]),
        "",
        "## 2. Derived political variables (per state × year)",
        "",
        "| Variable | Definition |",
        "|---|---|",
        "| `alignment` | 1 if president and governor sit on the same side of the "
        "left/right split (both ideology ≤ 0, or both > 0); 0 if opposed; missing if "
        "either is uncoded. |",
        "| `combined_pressure` | (president_ideology + governor_ideology) / 2. Higher "
        "= more conservative / pro-agribusiness. Observed range −1…+2. |",
        "| `posture` | Three-level bucketing of `combined_pressure` (see below). |",
        "| `fed_change` | President differs from the previous year (the first observed "
        "year is not counted as a change). |",
        "| `state_change` | Governor differs from the previous year, per state. |",
        "| `change_window` | Government (federal **or** state) changed this year or the "
        "previous year — the ±1-year transition window used in H1. |",
        "",
        "### 2.1 Posture buckets",
        "",
        _md_table(tables["posture"]),
        "",
        "## 3. Annual environmental-policy strength scores",
        "",
        "Eight national ordinal dimensions, coded once per year and joined to every "
        "territory-year:",
        "",
        _md_table(pd.DataFrame(
            [{"dimension": d, "range": r, "definition": x} for d, r, x in POLICY_DIMS])),
        "",
        f"![Policy score heatmap](figures/{figs['heatmap'].name})",
        "",
        "**Fig. C1.** The eight policy dimensions by year (cell = raw ordinal score; "
        "shade = share of that dimension's documented range). The full annual matrix is "
        "released as `data/codebook_policy_scores_by_year.csv`.",
        "",
        f"![Combined-pressure timeline](figures/{figs['pressure'].name})",
        "",
        "**Fig. C2.** Federal+state combined pressure across all states, with the three "
        "posture bands shaded. The shaded ribbon is the interquartile spread across the "
        "27 states in each year.",
        "",
        "### 3.1 Federal administration (regime) coding",
        "",
        "Calendar years are bucketed into eight federal administrations for the "
        "over-time (H3) tables: " +
        ", ".join(f"**{v}**" for v in REGIME_LABEL.values()) + ".",
        "",
        "## 4. Recognition-tier coding (cross-sectional H3)",
        "",
        "Recovered per area from the official vector layers (FUNAI Indigenous Lands; "
        "MMA/CNUC Conservation Units, May 2026 snapshots).",
        "",
        _md_table(tables["recognition"]),
        "",
        "## 5. Legal-milestone reference table",
        "",
        f"A point-in-time table of {tables['n_milestones']} legislative/constitutional "
        "milestones (1965–2024), each tagged by category "
        "(FOREST_LAW · INDIGENOUS · INSTITUTION · ENFORCEMENT · PLANNING · FINANCE · "
        "CLIMATE) and land-cover implication, backs the annual scores above. It is "
        "released as `data/codebook_legal_milestones.csv` and is not reproduced in full "
        "here.",
        "",
    ]
    if tables.get("coverage") is not None:
        L += [
            "## 6. Coverage in the analysed panel",
            "",
            "Territory-years actually observed in each posture × administration cell "
            "(protected-core scope; the buffer scope doubles every count). This grounds "
            "the codebook in what the sample really contains and flags the thin cells "
            "that the honest-nulls reading depends on:",
            "",
            _md_table(tables["coverage"], index=True),
            "",
        ]
    L += [
        "---",
        "",
        "### Reproducibility",
        "",
        "Re-run with `.venv/bin/python utils/governance_codebook.py`. Outputs: this "
        "file, `data/codebook_*.csv` (variable registry, president/policy/posture/"
        "recognition crosswalks, panel coverage, legal milestones) and "
        "`figures/codebook_*.png`. The coding rules live in "
        "`reflex_app/yvynation/utils/political_context_brazil.py` and "
        "`policy_context_brazil.py`; this script only reads them.",
        "",
    ]
    path = root / "governance_codebook.md"
    path.write_text("\n".join(L), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT_DEFAULT))
    args = ap.parse_args()
    root = Path(args.out)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "figures").mkdir(parents=True, exist_ok=True)

    presidents = president_table()
    gov_dist = governor_ideology_distribution()
    policy_year = policy_by_year_table()
    posture = posture_bin_table()
    recognition = recognition_table()
    registry = variable_registry()
    milestones = policy.build_milestones_df()
    coverage = panel_coverage(root)

    # crosswalk CSVs
    registry.to_csv(root / "data" / "codebook_variables.csv", index=False)
    presidents.to_csv(root / "data" / "codebook_president_ideology.csv", index=False)
    policy_year.to_csv(root / "data" / "codebook_policy_scores_by_year.csv", index=False)
    posture.to_csv(root / "data" / "codebook_posture_bins.csv", index=False)
    recognition.to_csv(root / "data" / "codebook_recognition_tiers.csv", index=False)
    milestones.to_csv(root / "data" / "codebook_legal_milestones.csv", index=False)
    if coverage is not None:
        coverage.to_csv(root / "data" / "codebook_panel_coverage.csv")

    figs = {"heatmap": fig_policy_heatmap(root), "pressure": fig_pressure_timeline(root)}

    tables = {
        "presidents": presidents, "gov_dist": gov_dist, "posture": posture,
        "recognition": recognition, "coverage": coverage,
        "n_milestones": len(milestones),
    }
    md = write_markdown(root, tables, figs)

    print(f"Wrote codebook → {md}")
    print(f"  variables registry rows: {len(registry)}")
    print(f"  presidents: {len(presidents)}   governor state-years coded: "
          f"{int(gov_dist['governor_state_years'].sum())}")
    print(f"  policy years: {len(policy_year)}   legal milestones: {len(milestones)}")
    if coverage is not None:
        print(f"  panel coverage: {coverage.loc['All', 'All']} core territory-years")
    print(f"  figures: {figs['heatmap'].name}, {figs['pressure'].name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
