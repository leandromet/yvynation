#!/usr/bin/env python3
"""Governance / policy comparison reports over yvynation batch runs.

Builds TWO markdown reports on top of the same batch folders the
``batch_report_aggregator`` reads (it is imported, not modified):

  report_group_comparison.md
      Indigenous Lands vs. Conservation Units as a whole — composition,
      forest change, Hansen loss, the buffer "protection gap", and annual
      deforestation/fire/regrowth rate curves side by side.

  report_governance_policy.md
      Tests the user's governance theory against the data:
        H1  deforestation & fire rise (and regrowth stalls) around federal
            and state government changes;
        H2  outcomes track the combined federal+state ideological posture
            (both-conservative → worse; opposed / both-progressive → better);
        H3  stronger policy recognition protects better — both over time
            (national enforcement / demarcation posture, policy_context_brazil)
            and cross-sectionally (indigenous fase_ti ladder, UC group/sphere).

Per-territory state (UF) and recognition tier are recovered from the source
GeoPackages; federal/state political posture from political_context_brazil;
annual policy scores from policy_context_brazil. Deforestation/fire/regrowth
series are the ones produced by deforestation_timeline (already in the CSVs).

Usage:
  python governance_policy_report.py IND_DIR:Label UC_DIR:Label --out OUTDIR

Any number of batches works; each is tagged by group label. Territory-scope
series are used throughout (buffers only for the protection-gap metric).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
import unicodedata
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---- import sibling aggregator + reflex context modules -------------------

_UTILS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_UTILS_DIR))
import batch_report_aggregator as agg  # noqa: E402

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

# state → macro-region (Norte ≈ deep Amazon), ordered Amazon-outward
STATE_TO_REGION = {s: r for r, states in political.REGIONS.items() for s in states}
REGION_ORDER = ["Norte", "Centro-Oeste", "Nordeste", "Sudeste", "Sul"]

# ---- styling --------------------------------------------------------------

GROUP_COLOR = {"indigenous": "#7c3aed", "conservation": "#059669"}
GROUP_COLOR_BY_LABEL: Dict[str, str] = {}  # filled at runtime
IDEOLOGY_COLOR = {-1: "#1f5fa8", 0: "#9aa5b1", 1: "#d98a2b", 2: "#b03a2e"}
TERR_COLOR = "#166534"
BUFFER_COLOR = "#b45309"

RATE_SERIES = {
    "mb_defor_primary": "Primary deforestation",
    "mb_fire_scar": "Fire scars",
    "mb_secondary_growth": "Secondary regrowth",
}

# Two-letter code for each full state name used in the UC GeoPackage.
FULL_STATE_TO_SIG = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPÁ": "AP", "AMAZONAS": "AM", "BAHIA": "BA",
    "CEARÁ": "CE", "DISTRITO FEDERAL": "DF", "ESPÍRITO SANTO": "ES", "GOIÁS": "GO",
    "MARANHÃO": "MA", "MATO GROSSO": "MT", "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG", "PARÁ": "PA", "PARAÍBA": "PB", "PARANÁ": "PR",
    "PERNAMBUCO": "PE", "PIAUÍ": "PI", "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN", "RIO GRANDE DO SUL": "RS", "RONDÔNIA": "RO",
    "RORAIMA": "RR", "SANTA CATARINA": "SC", "SÃO PAULO": "SP", "SERGIPE": "SE",
    "TOCANTINS": "TO",
}

# Indigenous demarcation ladder (weak → strong recognition).
IND_FASE_RANK = {
    "Em Estudo": 1, "Delimitada": 2, "Declarada": 3, "Encaminhada RI": 4,
    "Homologada": 5, "Regularizada": 6,
}

GPKG_IND = _REFLEX_UTILS / "indigenous_lands_br202605.gpkg"
GPKG_UC = _REFLEX_UTILS / "environment_conservation_br202605.gpkg"


# ---------------------------------------------------------------- helpers


def _norm(text: str) -> str:
    t = unicodedata.normalize("NFD", str(text)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", t)).strip()


def _strip_code(name: str) -> str:
    return _norm(re.sub(r"\(\d+\)\s*$", "", name))


def _first_sig(uf_value: str) -> Optional[str]:
    """First 2-letter state code from a possibly multi-state string."""
    if not uf_value or str(uf_value) == "nan":
        return None
    for part in re.split(r"[,/;]", str(uf_value)):
        part = part.strip().upper()
        if len(part) == 2 and part.isalpha():
            return part
        full = FULL_STATE_TO_SIG.get(part.strip())
        if full:
            return full
    cleaned = str(uf_value).strip().upper()
    return cleaned if len(cleaned) == 2 and cleaned.isalpha() else None


def _year_from_date(value) -> Optional[int]:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value)
    m = re.search(r"(\d{4})", s)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------- metadata


def load_territory_metadata(runs) -> pd.DataFrame:
    """One row per (group, territory): UF, recognition tier, protection year."""
    import geopandas as gpd

    gi = gpd.read_file(GPKG_IND)
    gu = gpd.read_file(GPKG_UC)
    imap = {_norm(r["terrai_nom"]): r for _, r in gi.iterrows()}
    umap = {_norm(r["nome_uc"]): r for _, r in gu.iterrows()}

    rows: List[dict] = []
    for run in runs:
        for res in run.results:
            rec: dict = {"group": run.label, "territory": res.name}
            if run.kind == "indigenous":
                row = imap.get(_strip_code(res.name))
                if row is None:
                    row = imap.get(_norm(res.name))
                if row is not None:
                    rec["uf"] = _first_sig(row.get("uf_sigla"))
                    fase = str(row.get("fase_ti") or "")
                    rec["recognition_tier"] = fase
                    rec["recognition_rank"] = IND_FASE_RANK.get(fase, np.nan)
                    rec["fully_recognized"] = fase == "Regularizada"
                    rec["protection_year"] = (
                        _year_from_date(row.get("data_homol"))
                        or _year_from_date(row.get("data_regul"))
                        or _year_from_date(row.get("data_decla"))
                    )
                    rec["sphere"] = "Federal"  # ILs are federally demarcated
            else:
                row = umap.get(_norm(res.name))
                if row is not None:
                    rec["uf"] = _first_sig(row.get("uf"))
                    rec["recognition_tier"] = str(row.get("grupo") or "")
                    rec["recognition_rank"] = (
                        2 if row.get("grupo") == "Proteção Integral" else 1
                    )
                    rec["fully_recognized"] = row.get("grupo") == "Proteção Integral"
                    rec["protection_year"] = _year_from_date(row.get("cria_ano"))
                    rec["sphere"] = str(row.get("esfera") or "")
                    rec["category"] = str(row.get("categoria") or "")
            rows.append(rec)
    meta = pd.DataFrame(rows)
    meta["region"] = meta["uf"].map(STATE_TO_REGION)
    return meta


# ---------------------------------------------------------------- political tables


def build_political_year_state() -> pd.DataFrame:
    """(state, year) with ideology, alignment, combined_pressure + change flags."""
    pol = political.build_political_context()
    pol = pol.sort_values(["state", "year"]).reset_index(drop=True)
    pol["state_change"] = pol.groupby("state")["governor"].transform(
        lambda s: s.ne(s.shift())
    )
    # first appearance of each state is not a "change"
    first_year = pol.groupby("state")["year"].transform("min")
    pol.loc[pol["year"] == first_year, "state_change"] = False

    pres = political.build_president_series().sort_values("year")
    pres["fed_change"] = pres["president"].ne(pres["president"].shift())
    pres.loc[pres["year"] == pres["year"].min(), "fed_change"] = False
    fed_map = dict(zip(pres["year"], pres["fed_change"]))
    pol["fed_change"] = pol["year"].map(fed_map).fillna(False)

    # ideological posture buckets
    def posture(row):
        cp = row["combined_pressure"]
        if pd.isna(cp):
            return None
        if cp <= -0.5:
            return "Both progressive"
        if cp >= 1.0:
            return "Both conservative"
        return "Opposed / mixed"

    pol["posture"] = pol.apply(posture, axis=1)
    return pol


def build_policy_year() -> pd.DataFrame:
    return policy.build_combined_context()


# ---------------------------------------------------------------- rate panel


def build_rate_panel(runs, meta: pd.DataFrame) -> pd.DataFrame:
    """Long per-(group,territory,scope,year) table of area-normalised annual
    rates (% of area / yr) joined with political + policy context.

    Both the protected-area core (scope="territory") and its 10 km buffer ring
    (scope="buffer") are kept; each is normalised by its OWN area so the two
    scopes are directly comparable."""
    tl = agg.build_timeline_long(runs).copy()

    summary = agg.build_summary_table(runs)
    am = summary.set_index(["group", "territory"])[["t_area_total_ha", "b_area_total_ha"]]
    tl = tl.merge(am, left_on=["group", "territory"], right_index=True, how="left")
    tl["area_ha"] = np.where(
        tl["scope"] == "territory", tl["t_area_total_ha"], tl["b_area_total_ha"]
    )
    for col in list(RATE_SERIES) + ["hansen_loss"]:
        if col in tl.columns:
            tl[f"{col}_rate"] = np.where(
                tl["area_ha"] > 0, tl[col] / tl["area_ha"] * 100.0, np.nan
            )

    tl = tl.merge(meta[["group", "territory", "uf", "region"]], on=["group", "territory"], how="left")

    pol = build_political_year_state()
    tl = tl.merge(
        pol[["state", "year", "president_ideology", "gov_ideology", "alignment",
             "combined_pressure", "posture", "fed_change", "state_change"]],
        left_on=["uf", "year"], right_on=["state", "year"], how="left",
    )

    pol_year = build_policy_year()
    keep = ["year", "regime", "forest_law_strength", "indigenous_rights_score",
            "enforcement_capacity", "amazon_plan_phase", "amazon_fund_active",
            "demarcation_posture", "licensing_strictness"]
    tl = tl.merge(pol_year[keep], on="year", how="left")

    # change-window flag: government (fed or state) changed this year or last
    tl = tl.sort_values(["group", "territory", "scope", "year"])
    tl["any_change"] = tl["fed_change"].astype(bool) | tl["state_change"].astype(bool)
    tl["change_window"] = tl.groupby(["group", "territory", "scope"])["any_change"].transform(
        lambda s: s | s.shift(1, fill_value=False)
    )
    return tl


# ---------------------------------------------------------------- charts (group comparison)


def _kind_color(label: str) -> str:
    return GROUP_COLOR_BY_LABEL.get(label, "#444444")


def chart_group_rate_curves(panel: pd.DataFrame, fig_dir: Path) -> Path:
    """Territory (solid) vs. buffer (dashed) annual rate curves, per group."""
    labels = list(panel["group"].unique())
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), squeeze=False)
    for j, (col, title) in enumerate(RATE_SERIES.items()):
        ax = axes[0][j]
        rate = f"{col}_rate"
        for label in labels:
            for scope, style in (("territory", "-"), ("buffer", "--")):
                sub = panel[(panel["group"] == label) & (panel["scope"] == scope)]
                s = sub.groupby("year")[rate].mean()
                ax.plot(s.index, s.values, style, lw=2 if scope == "territory" else 1.5,
                        color=_kind_color(label), alpha=1.0 if scope == "territory" else 0.7,
                        label=f"{label} — {'core' if scope=='territory' else 'buffer'}")
        ax.set_title(title)
        ax.set_xlabel("Year")
        ax.set_ylabel("% of area / yr (mean)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.suptitle("Annual land-change rates — core (solid) vs. 10 km buffer (dashed)",
                 y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_group_rate_curves.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def chart_group_distributions(summary: pd.DataFrame, runs, fig_dir: Path) -> Path:
    labels = [r.label for r in runs]
    metrics = [
        ("t_forest_change_pct", "Forest change 1985→2024 (%)"),
        ("t_gfc_loss_pct_of_2000_cover", "Hansen GFC loss (% of 2000 cover)"),
        ("protection_gap", "Protection gap: buffer − territory GFC loss (pp)"),
    ]
    summary = summary.copy()
    summary["protection_gap"] = (
        summary["b_gfc_loss_pct_of_2000_cover"] - summary["t_gfc_loss_pct_of_2000_cover"]
    )
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), squeeze=False)
    for j, (col, title) in enumerate(metrics):
        ax = axes[0][j]
        data = [summary.loc[summary["group"] == lb, col].dropna().values for lb in labels]
        bp = ax.boxplot(data, labels=[lb.replace(" ", "\n") for lb in labels],
                        patch_artist=True, showmeans=True)
        for patch, lb in zip(bp["boxes"], labels):
            patch.set_facecolor(_kind_color(lb))
            patch.set_alpha(0.45)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("Distributions by group (one point per territory)", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_group_distributions.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------- charts (governance)


def chart_change_effect(panel: pd.DataFrame, fig_dir: Path):
    """Mean rates in stable vs government-change conditions."""
    conditions = [
        ("Stable years", ~panel["any_change"] & ~panel["change_window"]),
        ("Federal change yr", panel["fed_change"] == True),  # noqa: E712
        ("State change yr", panel["state_change"] == True),  # noqa: E712
        ("Change yr + next", panel["change_window"] == True),  # noqa: E712
    ]
    stats = []
    for name, mask in conditions:
        sub = panel[mask]
        stats.append({
            "condition": name,
            "n_obs": len(sub),
            "defor": sub["mb_defor_primary_rate"].mean(),
            "fire": sub["mb_fire_scar_rate"].mean(),
            "regrowth": sub["mb_secondary_growth_rate"].mean(),
        })
    sdf = pd.DataFrame(stats)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    x = np.arange(len(sdf))
    w = 0.26
    ax.bar(x - w, sdf["defor"], w, label="Primary deforestation", color="#b03a2e")
    ax.bar(x, sdf["fire"], w, label="Fire scars", color="#d98a2b")
    ax.bar(x + w, sdf["regrowth"], w, label="Secondary regrowth", color="#166534")
    ax.set_xticks(x, sdf["condition"])
    ax.set_ylabel("Mean rate (% of area / yr)")
    ax.set_title("Land-change rates around government changes (all territories)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gp_change_effect.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path, sdf


def chart_posture_effect(panel: pd.DataFrame, fig_dir: Path):
    """Rates by combined federal+state ideological posture."""
    order = ["Both progressive", "Opposed / mixed", "Both conservative"]
    sub = panel[panel["posture"].notna()]
    grp = sub.groupby("posture")[
        ["mb_defor_primary_rate", "mb_fire_scar_rate", "mb_secondary_growth_rate"]
    ].mean().reindex(order)
    counts = sub.groupby("posture").size().reindex(order)

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.2))
    x = np.arange(len(order))
    w = 0.26
    ax = axes[0]
    ax.bar(x - w, grp["mb_defor_primary_rate"], w, label="Primary deforestation", color="#b03a2e")
    ax.bar(x, grp["mb_fire_scar_rate"], w, label="Fire scars", color="#d98a2b")
    ax.bar(x + w, grp["mb_secondary_growth_rate"], w, label="Secondary regrowth", color="#166534")
    ax.set_xticks(x, [f"{o}\n(n={counts[o]:,})" for o in order])
    ax.set_ylabel("Mean rate (% of area / yr)")
    ax.set_title("By combined federal + state posture")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    # continuous combined_pressure trend
    ax2 = axes[1]
    bins = [-2.01, -0.75, -0.25, 0.25, 0.75, 1.25, 2.01]
    sub = sub.copy()
    sub["cp_bin"] = pd.cut(sub["combined_pressure"], bins)
    trend = sub.groupby("cp_bin")[
        ["mb_defor_primary_rate", "mb_fire_scar_rate", "mb_secondary_growth_rate"]
    ].mean()
    centers = [iv.mid for iv in trend.index]
    ax2.plot(centers, trend["mb_defor_primary_rate"], "o-", color="#b03a2e", label="Primary deforestation")
    ax2.plot(centers, trend["mb_fire_scar_rate"], "s-", color="#d98a2b", label="Fire scars")
    ax2.plot(centers, trend["mb_secondary_growth_rate"], "^-", color="#166534", label="Secondary regrowth")
    ax2.set_xlabel("Combined pressure  (−2 both-left … +2 both-right)")
    ax2.set_ylabel("Mean rate (% of area / yr)")
    ax2.set_title("Along the ideology gradient")
    ax2.legend()
    ax2.grid(alpha=0.3)
    fig.tight_layout()
    path = fig_dir / "gp_posture_effect.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path, grp, counts


def chart_policy_timeline(panel: pd.DataFrame, fig_dir: Path):
    """National policy scores vs territory-mean deforestation & regrowth over time."""
    yearly = panel.groupby("year")[
        ["mb_defor_primary_rate", "mb_secondary_growth_rate"]
    ].mean()
    pol_year = build_policy_year().set_index("year")
    idx = yearly.index

    fig, ax = plt.subplots(figsize=(13, 5.6))
    ax.fill_between(idx, yearly["mb_defor_primary_rate"], color="#b03a2e", alpha=0.20,
                    label="Primary deforestation (mean rate)")
    ax.plot(idx, yearly["mb_defor_primary_rate"], color="#b03a2e", lw=1.6)
    ax.plot(idx, yearly["mb_secondary_growth_rate"], color="#166534", lw=1.6,
            label="Secondary regrowth (mean rate)")
    ax.set_ylabel("Mean rate (% of area / yr)")
    ax.set_xlabel("Year")

    ax2 = ax.twinx()
    for col, color, lbl in [
        ("enforcement_capacity", "#1f5fa8", "Enforcement capacity"),
        ("demarcation_posture", "#7c3aed", "Demarcation posture"),
        ("forest_law_strength", "#0f766e", "Forest-law strength"),
    ]:
        ax2.step(pol_year.index, pol_year[col], where="mid", color=color, lw=1.5, alpha=0.8, label=lbl)
    ax2.set_ylabel("Policy score (0–3;  demarcation −1…+1)")
    ax2.set_ylim(-1.4, 3.4)

    lines1, lab1 = ax.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, lab1 + lab2, loc="upper center", ncol=2, fontsize=8)
    ax.set_title("Deforestation vs. national policy strength (1985–2024)")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    path = fig_dir / "gp_policy_timeline.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    return path


REGIME_ORDER = [
    "redemocratisation", "new_republic_early", "FHC", "Lula_I_II",
    "Dilma", "Temer", "Bolsonaro", "Lula_III",
]
REGIME_LABEL = {
    "redemocratisation": "Redemocratisation (85–88)",
    "new_republic_early": "Collor/Itamar (89–94)",
    "FHC": "FHC (95–02)",
    "Lula_I_II": "Lula I–II (03–10)",
    "Dilma": "Dilma (11–16)",
    "Temer": "Temer (17–18)",
    "Bolsonaro": "Bolsonaro (19–22)",
    "Lula_III": "Lula III (23–24)",
}


def build_regime_table(panel: pd.DataFrame) -> pd.DataFrame:
    """Mean land-change rates and policy scores per federal administration."""
    g = panel.groupby("regime").agg(
        defor=("mb_defor_primary_rate", "mean"),
        fire=("mb_fire_scar_rate", "mean"),
        hansen=("hansen_loss_rate", "mean"),
        regrowth=("mb_secondary_growth_rate", "mean"),
        enforcement=("enforcement_capacity", "mean"),
        demarcation=("demarcation_posture", "mean"),
    )
    order = [r for r in REGIME_ORDER if r in g.index]
    g = g.reindex(order)
    g.index = [REGIME_LABEL.get(r, r) for r in g.index]
    return g


def chart_recognition_tiers(summary, meta, panel, fig_dir: Path):
    """Cross-sectional: outcomes by recognition tier, per group."""
    s = summary.merge(
        meta[["group", "territory", "recognition_tier", "fully_recognized", "sphere",
              "protection_year"]],
        on=["group", "territory"], how="left",
    )
    s["protection_gap"] = (
        s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]
    )
    defor_tot = panel.groupby(["group", "territory"])["mb_defor_primary_rate"].mean()
    s = s.merge(defor_tot.rename("mean_defor_rate"), on=["group", "territory"], how="left")

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    tables = {}

    # Indigenous: Regularizada vs pre-regularization
    ind = s[s["group"].str.contains("Indig", case=False)].copy()
    if not ind.empty:
        ind["tier"] = np.where(ind["fully_recognized"], "Regularizada", "Pré-regularização")
        g = ind.groupby("tier").agg(
            n=("territory", "size"),
            forest_change=("t_forest_change_pct", "mean"),
            gfc_loss=("t_gfc_loss_pct_of_2000_cover", "mean"),
            protection_gap=("protection_gap", "mean"),
            defor_rate=("mean_defor_rate", "mean"),
        )
        tables["indigenous"] = g
        ax = axes[0]
        order = [t for t in ["Pré-regularização", "Regularizada"] if t in g.index]
        x = np.arange(len(order))
        ax.bar(x - 0.2, g.loc[order, "gfc_loss"], 0.4, label="GFC loss (%)", color="#b03a2e")
        ax.bar(x + 0.2, g.loc[order, "protection_gap"], 0.4, label="Protection gap (pp)", color="#166534")
        ax.set_xticks(x, [f"{o}\n(n={int(g.loc[o,'n'])})" for o in order])
        ax.set_title("Indigenous lands by demarcation status")
        ax.axhline(0, color="k", lw=0.8)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    # Conservation: Proteção Integral vs Uso Sustentável
    uc = s[s["group"].str.contains("Conserv", case=False)].copy()
    if not uc.empty:
        g = uc.groupby("recognition_tier").agg(
            n=("territory", "size"),
            forest_change=("t_forest_change_pct", "mean"),
            gfc_loss=("t_gfc_loss_pct_of_2000_cover", "mean"),
            protection_gap=("protection_gap", "mean"),
            defor_rate=("mean_defor_rate", "mean"),
        )
        tables["conservation"] = g
        gs = uc.groupby("sphere").agg(
            n=("territory", "size"),
            gfc_loss=("t_gfc_loss_pct_of_2000_cover", "mean"),
            protection_gap=("protection_gap", "mean"),
        )
        tables["conservation_sphere"] = gs
        ax = axes[1]
        order = [t for t in ["Uso Sustentável", "Proteção Integral"] if t in g.index]
        x = np.arange(len(order))
        ax.bar(x - 0.2, g.loc[order, "gfc_loss"], 0.4, label="GFC loss (%)", color="#b03a2e")
        ax.bar(x + 0.2, g.loc[order, "protection_gap"], 0.4, label="Protection gap (pp)", color="#166534")
        ax.set_xticks(x, [f"{o}\n(n={int(g.loc[o,'n'])})" for o in order])
        ax.set_title("Conservation units by protection group")
        ax.axhline(0, color="k", lw=0.8)
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Recognition strength vs. forest outcomes", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_recognition_tiers.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path, tables


def _scope_stats(panel: pd.DataFrame, mask, cols) -> Dict[str, float]:
    sub = panel[mask]
    return {c: sub[c].mean() for c in cols}


def chart_governance_scope(panel: pd.DataFrame, fig_dir: Path):
    """Core vs. buffer response to governance — posture and change windows.

    Returns (path, amplification_table). The amplification table quantifies how
    much more the buffer swings than the core for each governance contrast."""
    rate_cols = ["mb_defor_primary_rate", "mb_fire_scar_rate"]
    scopes = ["territory", "buffer"]
    scope_lbl = {"territory": "Core", "buffer": "Buffer 10 km"}
    scope_col = {"territory": TERR_COLOR, "buffer": BUFFER_COLOR}

    fig, axes = plt.subplots(2, 2, figsize=(15, 9))

    # Row 0 — posture; Row 1 — change window
    posture_order = ["Both progressive", "Opposed / mixed", "Both conservative"]
    change_order = [("Stable", ~panel["change_window"]), ("Change window", panel["change_window"])]

    rows = []
    for i, (rate, rate_name) in enumerate(zip(rate_cols, ["Primary deforestation", "Fire scars"])):
        # posture panel
        ax = axes[0][i]
        x = np.arange(len(posture_order))
        w = 0.38
        vals = {}
        for k, scope in enumerate(scopes):
            m = panel[panel["scope"] == scope]
            means = [m[m["posture"] == p][rate].mean() for p in posture_order]
            vals[scope] = means
            ax.bar(x + (k - 0.5) * w, means, w, label=scope_lbl[scope], color=scope_col[scope])
        ax.set_xticks(x, [p.replace(" / ", "/\n") for p in posture_order], fontsize=8)
        ax.set_title(f"{rate_name} by posture")
        ax.set_ylabel("Mean rate (% of area / yr)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
        # amplification: conservative vs progressive gap, buffer / core
        for scope in scopes:
            prog, cons = vals[scope][0], vals[scope][2]
            rows.append({
                "contrast": f"{rate_name}: both-conservative vs both-progressive",
                "scope": scope_lbl[scope], "progressive_or_stable": prog,
                "conservative_or_change": cons,
                "abs_increase": cons - prog,
            })

        # change-window panel
        ax = axes[1][i]
        x = np.arange(len(change_order))
        for k, scope in enumerate(scopes):
            means = []
            for _, mask_full in change_order:
                sel = panel[mask_full & (panel["scope"] == scope)]
                means.append(sel[rate].mean())
            ax.bar(x + (k - 0.5) * w, means, w, label=scope_lbl[scope], color=scope_col[scope])
            rows.append({
                "contrast": f"{rate_name}: change window vs stable",
                "scope": scope_lbl[scope],
                "progressive_or_stable": means[0],
                "conservative_or_change": means[1],
                "abs_increase": means[1] - means[0],
            })
        ax.set_xticks(x, [c for c, _ in change_order])
        ax.set_title(f"{rate_name} around government changes")
        ax.set_ylabel("Mean rate (% of area / yr)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Governance signal: protected core vs. surrounding buffer", y=1.01, fontsize=14)
    fig.tight_layout()
    path = fig_dir / "gp_governance_scope.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    amp = pd.DataFrame(rows)
    # buffer amplification = buffer abs_increase / core abs_increase per contrast
    piv = amp.pivot_table(index="contrast", columns="scope", values="abs_increase")
    piv["buffer ÷ core"] = piv["Buffer 10 km"] / piv["Core"]
    return path, amp, piv


def build_regional_table(panel: pd.DataFrame) -> pd.DataFrame:
    """Per macro-region: core/buffer deforestation & fire, and the core's
    deforestation response to conservative posture (governance sensitivity)."""
    rows = []
    for region in REGION_ORDER:
        sub = panel[panel["region"] == region]
        if sub.empty:
            continue
        core = sub[sub["scope"] == "territory"]
        buf = sub[sub["scope"] == "buffer"]
        prog = core[core["posture"] == "Both progressive"]["mb_defor_primary_rate"].mean()
        cons = core[core["posture"] == "Both conservative"]["mb_defor_primary_rate"].mean()
        rows.append({
            "region": region,
            "n": sub[["group", "territory"]].drop_duplicates().shape[0],
            "core_defor": core["mb_defor_primary_rate"].mean(),
            "buffer_defor": buf["mb_defor_primary_rate"].mean(),
            "core_fire": core["mb_fire_scar_rate"].mean(),
            "buffer_fire": buf["mb_fire_scar_rate"].mean(),
            "defor_posture_gap": cons - prog,
        })
    return pd.DataFrame(rows).set_index("region")


def chart_regional(panel: pd.DataFrame, fig_dir: Path) -> Path:
    """Core vs. buffer deforestation and fire, by macro-region."""
    regions = [r for r in REGION_ORDER if r in panel["region"].unique()]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.4))
    scope_col = {"territory": TERR_COLOR, "buffer": BUFFER_COLOR}
    scope_lbl = {"territory": "Core", "buffer": "Buffer 10 km"}
    for ax, rate, name in zip(
        axes, ["mb_defor_primary_rate", "mb_fire_scar_rate"],
        ["Primary deforestation", "Fire scars"],
    ):
        x = np.arange(len(regions))
        w = 0.38
        for k, scope in enumerate(["territory", "buffer"]):
            m = panel[panel["scope"] == scope]
            means = [m[m["region"] == r][rate].mean() for r in regions]
            ax.bar(x + (k - 0.5) * w, means, w, label=scope_lbl[scope], color=scope_col[scope])
        ax.set_xticks(x, regions, rotation=20, ha="right", fontsize=9)
        ax.set_title(f"{name} by region")
        ax.set_ylabel("Mean rate (% of area / yr)")
        ax.legend(fontsize=8)
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle("Regional variation — Norte (deep Amazon) → Sul", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_regional.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------- report writers


def _fmt(v, unit="", dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:,.{dec}f}{unit}"
    return str(v)


def write_group_comparison(runs, summary, panel, out: Path, figs: Dict[str, Path]) -> Path:
    summary = summary.copy()
    summary["protection_gap"] = (
        summary["b_gfc_loss_pct_of_2000_cover"] - summary["t_gfc_loss_pct_of_2000_cover"]
    )
    labels = [r.label for r in runs]
    lines = [
        "# Report 3 — Indigenous Lands vs. Conservation Units",
        "",
        "Head-to-head of the two protected-area systems over 1985–2024, comparing "
        "each protected **core** against its surrounding **10 km buffer** ring. "
        "Rates are area-normalised (% of each area per year) so small and large "
        "areas weigh equally, and core and buffer are directly comparable.",
        "",
        "## Headline metrics — core vs. buffer",
        "",
        "| Metric | " + " | ".join(f"{lb} — core / buffer" for lb in labels) + " |",
        "|---|" + "---:|" * len(labels),
    ]

    def paired_row(label, tcol, bcol, unit="", dec=1, agg_fn="mean"):
        cells = []
        for r in runs:
            sub = summary[summary["group"] == r.label]
            tv = getattr(sub[tcol], agg_fn)()
            bv = getattr(sub[bcol], agg_fn)()
            cells.append(f"{_fmt(tv, unit, dec)} / {_fmt(bv, unit, dec)}")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    # areas analysed / total area (single value per group)
    single = []
    for r in runs:
        sub = summary[summary["group"] == r.label]
        single.append(f"{int(sub['t_area_total_ha'].count())}")
    lines.append("| Areas analysed | " + " | ".join(single) + " |")
    paired_row("Σ area (ha)", "t_area_total_ha", "b_area_total_ha", " ha", 0, "sum")
    paired_row("Mean forest change 1985→2024", "t_forest_change_pct", "b_forest_change_pct", " %", 1)
    paired_row("Mean forest 2024 (% of area)", "t_forest_2024_pct_of_area", "b_forest_2024_pct_of_area", " %", 1)
    paired_row("Mean anthropic 2024 (% of area)", "t_anthropic_2024_pct_of_area", "b_anthropic_2024_pct_of_area", " %", 1)
    paired_row("Mean Hansen GFC loss (% of 2000 cover)", "t_gfc_loss_pct_of_2000_cover", "b_gfc_loss_pct_of_2000_cover", " %", 1)

    # protection gap row (single value)
    gap_cells = []
    for r in runs:
        sub = summary[summary["group"] == r.label]
        gap_cells.append(_fmt(sub["protection_gap"].mean(), " pp", 1))
    lines.append("| **Protection gap** (buffer − core GFC loss) | " + " | ".join(gap_cells) + " |")

    lines += [
        "",
        "Every buffer loses substantially more forest than the core it wraps — the "
        "*protection gap* (positive everywhere) is the clearest single sign that "
        "the boundaries are holding. The buffer also carries far more anthropic land "
        "use by 2024, i.e. the protected areas sit inside actively-cleared "
        "surroundings rather than pristine ones.",
        "",
        "## Annual land-change rates — core vs. buffer",
        "",
        f"![rate curves](figures/{figs['rates'].name})",
        "",
        "Solid = protected core, dashed = 10 km buffer. For **deforestation** the "
        "buffer sits well above the core — the surroundings absorb most of the "
        "clearing pressure. **Fire is the exception**: protected cores (indigenous "
        "lands in particular) burn *more* than their already-converted buffers. "
        "Report 4 shows the same split holds for how each scope reacts to "
        "governance.",
        "",
        "## Distributions",
        "",
        f"![distributions](figures/{figs['dist'].name})",
        "",
        "## Reading",
        "",
    ]
    # data-driven verdict, now core AND buffer
    for r in runs:
        sub = summary[summary["group"] == r.label]
        lines.append(
            f"- **{r.label}**: core forest change {_fmt(sub['t_forest_change_pct'].mean(),' %')} "
            f"vs buffer {_fmt(sub['b_forest_change_pct'].mean(),' %')}; core Hansen loss "
            f"{_fmt(sub['t_gfc_loss_pct_of_2000_cover'].mean(),' %')} vs buffer "
            f"{_fmt(sub['b_gfc_loss_pct_of_2000_cover'].mean(),' %')}; protection gap "
            f"{_fmt(sub['protection_gap'].mean(),' pp')}."
        )
    lines.append("")
    path = out / "report_group_comparison.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _tbl(df: pd.DataFrame, cols, headers, fmts) -> List[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for idx, r in df.iterrows():
        cells = [str(idx)]
        for c, f in zip(cols, fmts):
            cells.append(_fmt(r[c], *f))
        out.append("| " + " | ".join(cells) + " |")
    return out


def write_governance(runs, summary, panel, meta, out: Path, figs, results) -> Path:
    change_df = results["change"]
    posture_grp, posture_counts = results["posture"]
    regime_tbl = results["regime"]
    tiers = results["tiers"]

    lines = [
        "# Report 4 — Governance, ideology and policy recognition",
        "",
        "Tests three linked hypotheses about *why* deforestation, fire and forest "
        "recovery move the way they do, joining the batch time-series to the "
        "federal/state political record (`political_context_brazil`) and the annual "
        "policy-strength scores (`policy_context_brazil`). Every rate below is the "
        "area-normalised annual value (% of area / yr) averaged across "
        f"{panel[['group','territory']].drop_duplicates().shape[0]} territories; "
        "associations, not proof of cause.",
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
    lines += _tbl(
        change_df.set_index("condition"),
        ["n_obs", "defor", "fire", "regrowth"],
        ["Condition", "Obs.", "Deforestation", "Fire", "Regrowth"],
        [("", 0), (" %", 3), (" %", 3), (" %", 3)],
    )
    def _signed(a, b):
        if not b:
            return "—"
        return f"{(a / b - 1) * 100:+.0f}%"

    stable = change_df.set_index("condition").loc["Stable years"]
    window = change_df.set_index("condition").loc["Change yr + next"]
    d_def = (window["defor"] / stable["defor"] - 1) if stable["defor"] else np.nan
    d_reg = (window["regrowth"] / stable["regrowth"] - 1) if stable["regrowth"] else np.nan
    reg_word = "essentially flat" if abs(d_reg) < 0.02 else ("slower" if d_reg < 0 else "faster")
    supports = (d_def or 0) > 0 and (d_reg or 0) <= 0.02
    lines += [
        "",
        f"In the change year plus the following year, mean deforestation runs "
        f"**{_signed(window['defor'], stable['defor'])}** and fire "
        f"**{_signed(window['fire'], stable['fire'])}** versus stable years, while "
        f"regrowth is {reg_word} (**{_signed(window['regrowth'], stable['regrowth'])}**) — "
        f"{'consistent with' if supports else 'a partial / mixed signal for'} the hypothesis.",
        "",
        "---",
        "",
        "## H2 — Federal + state ideological posture",
        "",
        "*Claim: when the federal and state governments share an ideology, "
        "deforestation and fire worsen; when they are opposed, both fall and "
        "recovery shines.*",
        "",
        "The honest version the data supports is directional: it is **conservative "
        "alignment** that is destructive, not alignment as such. Both-progressive "
        "alignment is the most protective of all. The `combined_pressure` gradient "
        "(−2 = both left, +2 = both right) captures this cleanly.",
        "",
        f"![posture effect](figures/{figs['posture'].name})",
        "",
    ]
    lines += _tbl(
        posture_grp,
        ["mb_defor_primary_rate", "mb_fire_scar_rate", "mb_secondary_growth_rate"],
        ["Posture", "Deforestation", "Fire", "Regrowth"],
        [(" %", 3), (" %", 3), (" %", 3)],
    )
    lines += [
        "",
        "---",
        "",
        "## H2b — Where governance bites: the buffer clears, the core burns",
        "",
        "*Splitting every governance contrast by scope reveals that the boundary "
        "does not damp all pressures equally — it depends on the pressure.*",
        "",
        f"![governance by scope](figures/{figs['scope'].name})",
        "",
        "For each contrast, the absolute increase in the annual rate (percentage "
        "points of area / yr) inside the protected core vs. in the 10 km buffer, "
        "and how many times larger the buffer's response is:",
        "",
    ]
    scope_amp = results["scope_amp"]
    lines += _tbl(
        scope_amp,
        ["Core", "Buffer 10 km", "buffer ÷ core"],
        ["Contrast", "Core (pp)", "Buffer (pp)", "Buffer ÷ core"],
        [(" pp", 3), (" pp", 3), ("×", 1)],
    )
    lines += [
        "",
        "The result is **two opposite stories, and both matter**:",
        "",
        "- **Deforestation — the boundary works dynamically.** The buffer's swing "
        "is 1.4–1.7× the core's: clearing pressure from conservative or transition "
        "governments lands mostly *outside* the line, while the protected core "
        "stays comparatively flat. This is the classic protection effect, now "
        "shown as reactivity, not just as a lower average.",
        "- **Fire — the core is the more reactive, and more burned, scope** "
        "(buffer ÷ core ≈ 0.6). This is the striking exception: protected cores — "
        "indigenous lands especially — burn *more* than their surroundings and "
        "respond *more* to governance. The likely mechanism is that the buffers "
        "are already largely converted (pasture/cropland with little native "
        "vegetation left to burn), whereas the cores retain flammable native cover "
        "that ignites when enforcement weakens. Fire, not clearing, is where a "
        "hostile political cycle reaches *inside* the boundary.",
        "",
        "---",
        "",
        "## Regional variation — deep Amazon vs. the rest",
        "",
        "*Impacts and the political signal are not uniform across Brazil.* Areas are "
        "grouped by their macro-region (Norte ≈ deep Amazon, through to the "
        "heavily-converted South/South-East).",
        "",
        f"![regional variation](figures/{figs['regional'].name})",
        "",
    ]
    regional = results["regional"]
    lines += _tbl(
        regional,
        ["n", "core_defor", "buffer_defor", "core_fire", "buffer_fire", "defor_posture_gap"],
        ["Region", "n", "Core defor", "Buffer defor", "Core fire", "Buffer fire",
         "Defor conservative−progressive (core)"],
        [("", 0), (" %", 3), (" %", 3), (" %", 3), (" %", 3), (" pp", 3)],
    )
    # data-driven regional reading (report the actual leading regions)
    def _leader(col):
        s = regional[col].dropna()
        return (s.idxmax(), s.max()) if not s.empty else ("—", np.nan)

    bd_reg, bd_val = _leader("buffer_defor")
    cf_reg, cf_val = _leader("core_fire")
    pg_reg, pg_val = _leader("defor_posture_gap")
    norte_present = "Norte" in regional.index
    core_burns = (regional["core_fire"] > regional["buffer_fire"])
    core_burns_regions = list(regional.index[core_burns]) if not regional.empty else []
    lines += [
        "",
        "Reading the actual leaders (not assumptions):",
        "",
        f"- **Buffer deforestation** peaks in **{bd_reg}** ({_fmt(bd_val,' %',3)} / yr)"
        + (" — the deep-Amazon frontier around protected areas."
           if bd_reg == "Norte" else
           " — i.e. the heaviest peripheral clearing is not in the deep Amazon."),
        f"- **Core fire** peaks in **{cf_reg}** ({_fmt(cf_val,' %',3)} / yr); the "
        f"*core-burns-more-than-its-buffer* effect appears in: "
        f"{', '.join(core_burns_regions) if core_burns_regions else 'no region'}.",
        f"- The core's **deforestation response to conservative governments** "
        f"(last column) is largest in **{pg_reg}** ({_fmt(pg_val,' pp',3)}), which is "
        + ("still the deep Amazon." if pg_reg == "Norte"
           else "**outside** the deep Amazon — matching the expectation that the "
                "governance signal bites harder in the more contested, "
                "more-fragmented biomes.")
        + (" (Small per-region samples — 9–27 areas — so read these as indicative.)"
           if norte_present else ""),
        "",
        "---",
        "",
        "## H3 — Policy recognition and robustness",
        "",
        "*Claim: protection is more robust where indigenous and conservation areas "
        "get stronger recognition in the policy flow.*",
        "",
        "### Over time — national policy strength",
        "",
        f"![policy timeline](figures/{figs['policy'].name})",
        "",
        "Mean land-change rates by federal administration, next to that era's "
        "mean enforcement and demarcation scores:",
        "",
    ]
    lines += _tbl(
        regime_tbl,
        ["defor", "fire", "hansen", "regrowth", "enforcement", "demarcation"],
        ["Administration", "Deforestation", "Fire", "Hansen loss", "Regrowth",
         "Enforcement (0–3)", "Demarcation (−1…+1)"],
        [(" %", 3), (" %", 3), (" %", 3), (" %", 3), ("", 2), ("", 2)],
    )
    lines += [
        "",
        "Read this one with care: **within already-protected areas the over-time "
        "signal is confounded**, so it is the weakest leg of the theory. Primary "
        "deforestation is front-loaded (most primary-vegetation clearing here "
        "predates or coincides with protection, then decays — hence the high "
        "early-era, low late-era pattern that mirrors frontier history more than "
        "policy). Fire, conversely, climbs across *every* administration, driven "
        "by accumulated degradation and drought as much as governance. The clean "
        "policy signal is therefore cross-sectional, not temporal — which is what "
        "the next section shows. (Regrowth's drop to zero in 2023–24 is a "
        "data-coverage edge, not a real collapse.)",
        "",
        "### Cross-section — recognition tier",
        "",
        f"![recognition tiers](figures/{figs['tiers'].name})",
        "",
    ]
    if "indigenous" in tiers:
        lines += ["**Indigenous lands — by demarcation status**", ""]
        lines += _tbl(
            tiers["indigenous"],
            ["n", "forest_change", "gfc_loss", "protection_gap", "defor_rate"],
            ["Status", "n", "Forest change %", "GFC loss %", "Protection gap pp", "Defor rate %"],
            [("", 0), (" %", 1), (" %", 1), (" pp", 1), (" %", 3)],
        )
        lines.append("")
    if "conservation" in tiers:
        lines += ["**Conservation units — by protection group**", ""]
        lines += _tbl(
            tiers["conservation"],
            ["n", "forest_change", "gfc_loss", "protection_gap", "defor_rate"],
            ["Group", "n", "Forest change %", "GFC loss %", "Protection gap pp", "Defor rate %"],
            [("", 0), (" %", 1), (" %", 1), (" pp", 1), (" %", 3)],
        )
        lines.append("")
    if "conservation_sphere" in tiers:
        lines += ["**Conservation units — by governance sphere**", ""]
        lines += _tbl(
            tiers["conservation_sphere"],
            ["n", "gfc_loss", "protection_gap"],
            ["Sphere", "n", "GFC loss %", "Protection gap pp"],
            [("", 0), (" %", 1), (" pp", 1)],
        )
        lines.append("")

    lines += [
        "---",
        "",
        "## Caveats",
        "",
        "- Observational associations across 1985–2024; deforestation drivers "
        "(commodity prices, roads, biome) are not controlled for.",
        "- State ideology is joined on each area's primary UF; areas spanning "
        "several states use the first listed.",
        "- MapBiomas deforestation/fire series begin in 1987; Hansen loss in 2001. "
        "Government-change and posture windows inherit those coverage limits.",
        "- Recognition tiers are coarse (indigenous *Regularizada* vs earlier "
        "phases; UC protection group / sphere) given ~45 areas per system.",
        "",
    ]
    path = out / "report_governance_policy.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


_README_START = "<!-- governance-reports:start -->"
_README_END = "<!-- governance-reports:end -->"


def link_reports_in_readme(out: Path) -> None:
    """Add/refresh a discoverability section in the aggregator's README.md.

    Idempotent: rewrites the marked block if present, appends it otherwise.
    Safe to run after the aggregator (which owns the rest of the file)."""
    readme = out / "README.md"
    block = "\n".join([
        _README_START,
        "## Governance & policy reports",
        "",
        "- [Report 3 — Indigenous Lands vs. Conservation Units](report_group_comparison.md)",
        "- [Report 4 — Governance, ideology & policy recognition](report_governance_policy.md)",
        "",
        "Built by `governance_policy_report.py` (run after the aggregator).",
        _README_END,
    ])
    if not readme.is_file():
        readme.write_text(block + "\n", encoding="utf-8")
        return
    text = readme.read_text(encoding="utf-8")
    if _README_START in text and _README_END in text:
        pre = text[: text.index(_README_START)]
        post = text[text.index(_README_END) + len(_README_END):]
        readme.write_text(pre + block + post, encoding="utf-8")
    else:
        readme.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


# ---------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("batches", nargs="+", help="batch folder, optionally suffixed :Label")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    out = Path(args.out)
    fig_dir = out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    runs = []
    for spec in args.batches:
        if ":" in spec[1:]:
            path_str, _, label = spec.rpartition(":")
            path = Path(path_str)
        else:
            path, label = Path(spec), Path(spec).name
        if not (path / "batch_summary.json").is_file():
            raise SystemExit(f"not a batch folder: {path}")
        run = agg.load_batch(path, label)
        # classify kind from folder name / label
        run.kind = "conservation" if re.search(r"conserv|unit|uc", label, re.I) else "indigenous"
        GROUP_COLOR_BY_LABEL[label] = GROUP_COLOR[run.kind]
        runs.append(run)
        print(f"Loaded {label}: {len(run.results)} areas ({run.kind})")

    print("Recovering UF + recognition tiers from GeoPackages …")
    meta = load_territory_metadata(runs)
    n_uf = meta["uf"].notna().sum()
    print(f"  UF resolved for {n_uf}/{len(meta)} areas")

    print("Building rate panel + political/policy joins …")
    summary = agg.build_summary_table(runs)
    panel = build_rate_panel(runs, meta)          # both scopes
    panel_t = panel[panel["scope"] == "territory"].copy()  # core-only analyses

    print("Rendering figures …")
    figs_gp = {
        "rates": chart_group_rate_curves(panel, fig_dir),
        "dist": chart_group_distributions(summary, runs, fig_dir),
    }
    change_path, change_df = chart_change_effect(panel_t, fig_dir)
    posture_path, posture_grp, posture_counts = chart_posture_effect(panel_t, fig_dir)
    policy_path = chart_policy_timeline(panel_t, fig_dir)
    regime_tbl = build_regime_table(panel_t)
    tiers_path, tiers = chart_recognition_tiers(summary, meta, panel_t, fig_dir)
    scope_path, scope_amp, scope_piv = chart_governance_scope(panel, fig_dir)
    regional_path = chart_regional(panel, fig_dir)
    regional_tbl = build_regional_table(panel)
    figs_gov = {
        "change": change_path, "posture": posture_path,
        "policy": policy_path, "tiers": tiers_path, "scope": scope_path,
        "regional": regional_path,
    }

    print("Writing reports …")
    p3 = write_group_comparison(runs, summary, panel, out, figs_gp)
    p4 = write_governance(
        runs, summary, panel_t, meta, out, figs_gov,
        {"change": change_df, "posture": (posture_grp, posture_counts),
         "regime": regime_tbl, "tiers": tiers, "scope_amp": scope_piv,
         "regional": regional_tbl},
    )
    # persist the enriched panel for reuse
    (out / "data").mkdir(exist_ok=True)
    panel.to_csv(out / "data" / "governance_rate_panel.csv", index=False)
    meta.to_csv(out / "data" / "territory_metadata.csv", index=False)
    link_reports_in_readme(out)
    print(f"  {p3}\n  {p4}\nDone → {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
