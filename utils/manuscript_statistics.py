#!/usr/bin/env python3
"""Per-manuscript statistical analysis (ANOVA + econometrics) for the Yvynation
buffer-referenced protection reports.

For each of the four manuscripts we build a territory-level analysis table from
the already-aggregated `data/summary_metrics.csv` + `data/territory_metadata.csv`
and run a documented battery of tests, writing a *step-by-step* registry so every
number in the manuscript can be traced to the exact test that produced it:

  statistics/STATISTICS_REPORT.md   ← human-readable, step by step, with prose
  statistics/results.json           ← every statistic, machine-readable
  statistics/tables/*.csv           ← descriptives, ANOVA, post-hoc, OLS coefs
  statistics/figures/*.png          ← boxplots + residual QQ diagnostics

Design of the battery (adapts to each dataset's factor structure):
  1. Analysis variables (core vs buffer GFC loss, protection gap, fire, forest Δ)
  2. Paired core-vs-buffer test (the buffer-absorption / fire-reversal claim)
  3. Primary-factor group comparison
       - 2 levels  -> Welch t, Mann-Whitney U, Hedges g
       - 3+ levels -> one-way ANOVA (+ Levene, Shapiro, Kruskal-Wallis, Tukey HSD)
  4. Secondary one-way ANOVAs on the remaining categorical factors
  5. Two-way ANOVA (only where a second balanced factor exists, e.g. group x region)
  6. Cross-sectional OLS with heteroskedasticity-robust (HC3) SE
  7. Panel econometric model: cluster-robust OLS on the territory x year x scope
     governance panel (scope + governance posture), SE clustered by territory

Run:
  .venv_stats/bin/python utils/manuscript_statistics.py            # all four
  .venv_stats/bin/python utils/manuscript_statistics.py root para_state
"""
from __future__ import annotations

import json
import sys
import textwrap
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import scipy.stats as st
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

ROOT = Path("/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report")

# --------------------------------------------------------------------------- #
# Dataset configuration                                                        #
# --------------------------------------------------------------------------- #

@dataclass
class DS:
    key: str
    d: Path
    label: str
    manuscript: str
    primary_factor: str          # main grouping variable
    anova_factors: list          # categorical factors to test one-way
    twoway: tuple | None         # (f1, f2) for a two-way ANOVA, else None
    ols_formula: str             # cross-sectional OLS spec (on `gap`)
    trend_var: str | None = None # continuous timing var to headline (else None)
    notes: str = ""

DATASETS = {
    "root": DS(
        key="root", d=ROOT,
        label="Indigenous Lands vs Conservation Units (91 protected areas)",
        manuscript="MANUSCRIPT_land_use_policy.md",
        primary_factor="group",
        anova_factors=["group", "region", "recognition_tier"],
        twoway=("group", "region"),
        ols_formula="gap ~ C(group) + C(region) + log_area + protection_year_c",
        notes="Indigenous (n=46) vs Conservation (n=45); recognition_tier spans "
              "both systems (singleton tiers dropped).",
    ),
    "indigenous_selection": DS(
        key="indigenous_selection", d=ROOT / "indigenous_selection",
        label="Regularizada Indigenous Lands (50-300k ha, off-border)",
        manuscript="MANUSCRIPT_land_use_policy_indigenous_selection.md",
        primary_factor="region",
        anova_factors=["region"],
        twoway=None,
        ols_formula="gap ~ protection_year_c + C(region) + log_area",
        trend_var="protection_year",
        notes="Single system/sphere; protection_year is the regularization year "
              "(marco-temporal timing test).",
    ),
    "national_forests": DS(
        key="national_forests", d=ROOT / "national_forests",
        label="National Forests & Parks (federal conservation, PA/AM)",
        manuscript="MANUSCRIPT_land_use_policy_national_forests.md",
        primary_factor="category",
        anova_factors=["category"],
        twoway=None,
        ols_formula="gap ~ C(category) + log_area",
        notes="Small n=16; Floresta (sustainable use, 12) vs Parque (strict, 4). "
              "Non-parametric robustness emphasised.",
    ),
    "para_state": DS(
        key="para_state", d=ROOT / "para_state",
        label="Para State Conservation Units (federal/state/municipal)",
        manuscript="MANUSCRIPT_land_use_policy_para_conservation.md",
        primary_factor="sphere",
        anova_factors=["sphere", "category_bin"],
        twoway=None,
        ols_formula="gap ~ C(sphere) + log_area",
        notes="Single region (Norte); governance sphere (federal/state/municipal) "
              "is the factor of interest.",
    ),
}

OUTCOMES = {
    "core_loss": "Core GFC forest loss (% of 2000 tree cover)",
    "buffer_loss": "Buffer GFC forest loss (% of 2000 tree cover)",
    "gap": "Protection gap = buffer loss - core loss (pp)",
    "core_forest_change_pct": "Core MapBiomas forest change 1985-2024 (%)",
    "core_fire_pct": "Core cumulative fire scar (% of core area)",
    "buffer_fire_pct": "Buffer cumulative fire scar (% of buffer area)",
}

# --------------------------------------------------------------------------- #
# Reporter                                                                     #
# --------------------------------------------------------------------------- #

class Reporter:
    def __init__(self, ds: DS):
        self.ds = ds
        self.lines: list[str] = []
        self.results: dict = {"dataset": ds.key, "label": ds.label, "steps": {}}
        self._step = 0
        self.pvals: list[dict] = []  # pre-specified test p-values for FDR

    def register_p(self, family, label, p, test="", primary=True):
        """Record a p-value so the multiplicity step can FDR-adjust the family."""
        if p is None or (isinstance(p, float) and np.isnan(p)):
            return
        self.pvals.append({"family": family, "label": label, "test": test,
                           "p": float(p), "primary": bool(primary)})

    def h(self, text, level=2):
        self.lines.append(f"\n{'#'*level} {text}\n")

    def p(self, text):
        self.lines.append(textwrap.dedent(text).strip() + "\n")

    def code(self, text):
        self.lines.append(f"```\n{text.strip()}\n```\n")

    def table(self, df: pd.DataFrame, floatfmt=3):
        self.lines.append(df.round(floatfmt).to_markdown() + "\n")

    def step(self, key, title):
        self._step += 1
        self.h(f"Step {self._step}. {title}")
        self.results["steps"][key] = {}
        return self.results["steps"][key]

    def save(self, out: Path):
        (out / "STATISTICS_REPORT.md").write_text("\n".join(self.lines))
        (out / "results.json").write_text(json.dumps(self.results, indent=2, default=_json_default))


def _json_default(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.ndarray,)):
        return o.tolist()
    return str(o)


# --------------------------------------------------------------------------- #
# Statistics helpers                                                           #
# --------------------------------------------------------------------------- #

def _fmt_p(p):
    if p is None or (isinstance(p, float) and np.isnan(p)):
        return "n/a"
    return "<0.001" if p < 1e-3 else f"{p:.3f}"


def _fmt_ci(lo, hi, dec=2):
    if lo is None or np.isnan(lo) or np.isnan(hi):
        return "n/a"
    return f"[{lo:.{dec}f}, {hi:.{dec}f}]"


def benjamini_hochberg(pvals):
    """Benjamini–Hochberg FDR-adjusted p-values (q-values), monotone, clipped."""
    p = np.asarray(pvals, float)
    n = len(p)
    if n == 0:
        return p
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / np.arange(1, n + 1)
    q = np.minimum.accumulate(q[::-1])[::-1]  # enforce monotonicity
    out = np.empty(n)
    out[order] = np.clip(q, 0, 1)
    return out


def boot_ci(stat_fn, *samples, B=2000, alpha=0.05, seed=42, paired=False):
    """Percentile bootstrap CI for an effect size.

    paired=True resamples one shared index across all arrays (matched pairs);
    otherwise each sample is resampled independently."""
    rng = np.random.default_rng(seed)
    samples = [np.asarray(s, float) for s in samples]
    vals = []
    for _ in range(B):
        if paired:
            idx = rng.integers(0, len(samples[0]), len(samples[0]))
            rs = [s[idx] for s in samples]
        else:
            rs = [s[rng.integers(0, len(s), len(s))] for s in samples]
        try:
            vals.append(float(stat_fn(*rs)))
        except Exception:  # noqa: BLE001
            vals.append(np.nan)
    vals = np.asarray(vals, float)
    vals = vals[np.isfinite(vals)]
    if len(vals) < 2:
        return (np.nan, np.nan)
    lo, hi = np.percentile(vals, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(lo), float(hi)


def hedges_g(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    n1, n2 = len(a), len(b)
    sp = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    d = (a.mean() - b.mean()) / sp if sp else np.nan
    J = 1 - 3 / (4 * (n1 + n2) - 9)
    return d * J


def eta_omega(aov: pd.DataFrame, factor: str):
    """eta^2 and omega^2 from a statsmodels anova_lm type-II table."""
    ss = aov["sum_sq"]
    ss_total = ss.sum()
    ss_eff = ss.get(factor, np.nan)
    df_eff = aov["df"].get(factor, np.nan)
    ms_err = aov.loc["Residual", "sum_sq"] / aov.loc["Residual", "df"]
    eta = ss_eff / ss_total
    omega = (ss_eff - df_eff * ms_err) / (ss_total + ms_err)
    return float(eta), float(omega)


def _eta_boot_ci(sub, outcome, factor, B=1000, seed=42):
    """Percentile bootstrap CI for eta^2 (resample rows, refit one-way ANOVA)."""
    rng = np.random.default_rng(seed)
    sub = sub[[outcome, factor]].dropna().reset_index(drop=True)
    n = len(sub)
    vals = []
    for _ in range(B):
        rs = sub.iloc[rng.integers(0, n, n)]
        if rs[factor].nunique() < 2 or (rs.groupby(factor).size() < 2).any():
            continue
        try:
            m = smf.ols(f"Q('{outcome}') ~ C(Q('{factor}'))", data=rs).fit()
            av = anova_lm(m, typ=2)
            ss = av["sum_sq"]
            vals.append(float(ss.iloc[0] / ss.sum()))
        except Exception:  # noqa: BLE001
            continue
    if len(vals) < 2:
        return (np.nan, np.nan)
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def two_group(rep, sub, res, outcome, factor):
    levels = sub[factor].dropna().unique().tolist()
    a = sub.loc[sub[factor] == levels[0], outcome].dropna()
    b = sub.loc[sub[factor] == levels[1], outcome].dropna()
    t, pt = st.ttest_ind(a, b, equal_var=False)          # Welch
    u, pu = st.mannwhitneyu(a, b, alternative="two-sided")
    g = hedges_g(a, b)
    g_lo, g_hi = boot_ci(hedges_g, a.values, b.values)
    rep.p(f"**{OUTCOMES.get(outcome, outcome)}** — {factor}: "
          f"*{levels[0]}* (n={len(a)}, mean={a.mean():.2f}) vs "
          f"*{levels[1]}* (n={len(b)}, mean={b.mean():.2f}).")
    rep.code(
        f"Welch t-test:      t = {t:.3f}, p = {_fmt_p(pt)}\n"
        f"Mann-Whitney U:    U = {u:.1f}, p = {_fmt_p(pu)}  (non-parametric)\n"
        f"Hedges g:          g = {g:.3f}  95% CI {_fmt_ci(g_lo, g_hi)}  "
        f"({_g_word(g)} effect)")
    res[outcome] = dict(test="welch_t+mwu", levels=levels,
                        mean=[a.mean(), b.mean()], n=[len(a), len(b)],
                        t=t, p_welch=pt, U=u, p_mwu=pu,
                        hedges_g=g, hedges_g_ci=[g_lo, g_hi])
    rep.register_p("group_comparison", f"{outcome} ~ {factor} (Welch t)", pt,
                   test="welch_t")


def _g_word(g):
    ag = abs(g)
    return "negligible" if ag < .2 else "small" if ag < .5 else "medium" if ag < .8 else "large"


def oneway(rep, sub, res, outcome, factor):
    sub = sub[[outcome, factor]].dropna()
    counts = sub[factor].value_counts()
    keep = counts[counts >= 3].index
    sub = sub[sub[factor].isin(keep)]
    if sub[factor].nunique() < 2:
        rep.p(f"*{factor}*: fewer than two levels with n>=3 — skipped.")
        return
    groups = [g[outcome].values for _, g in sub.groupby(factor)]
    model = smf.ols(f"Q('{outcome}') ~ C(Q('{factor}'))", data=sub).fit()
    aov = anova_lm(model, typ=2)
    fac_row = [i for i in aov.index if i != "Residual"][0]
    F = aov.loc[fac_row, "F"]; p = aov.loc[fac_row, "PR(>F)"]
    df1 = aov.loc[fac_row, "df"]; df2 = aov.loc["Residual", "df"]
    eta, omega = eta_omega(aov.rename(index={fac_row: factor}), factor)
    eta_lo, eta_hi = _eta_boot_ci(sub, outcome, factor)
    lev = st.levene(*groups, center="median")
    sh = st.shapiro(model.resid)
    kw = st.kruskal(*groups)
    means = sub.groupby(factor)[outcome].agg(["count", "mean", "std"])
    rep.p(f"**{OUTCOMES.get(outcome, outcome)}** by *{factor}* "
          f"({sub[factor].nunique()} levels, N={len(sub)}):")
    rep.table(means)
    rep.code(
        f"One-way ANOVA:     F({df1:.0f},{df2:.0f}) = {F:.3f}, p = {_fmt_p(p)}\n"
        f"  eta^2 = {eta:.3f} 95% CI {_fmt_ci(eta_lo, eta_hi, 3)}   "
        f"omega^2 = {omega:.3f}   ({_eta_word(eta)})\n"
        f"Levene (var eq.):  W = {lev.statistic:.3f}, p = {_fmt_p(lev.pvalue)}  "
        f"{'(homogeneous)' if lev.pvalue>=.05 else '(HETEROGENEOUS -> read Kruskal)'}\n"
        f"Shapiro (resid.):  W = {sh.statistic:.3f}, p = {_fmt_p(sh.pvalue)}  "
        f"{'(normal)' if sh.pvalue>=.05 else '(non-normal -> read Kruskal)'}\n"
        f"Kruskal-Wallis:    H = {kw.statistic:.3f}, p = {_fmt_p(kw.pvalue)}  (non-parametric)")
    res[outcome] = dict(test="oneway_anova", F=F, df=[df1, df2], p=p,
                        eta_sq=eta, eta_sq_ci=[eta_lo, eta_hi], omega_sq=omega,
                        levene_p=lev.pvalue, shapiro_p=sh.pvalue,
                        kruskal_H=kw.statistic, kruskal_p=kw.pvalue,
                        means=means.reset_index().to_dict("records"))
    # register the more conservative of the parametric/non-parametric omnibus p
    rep.register_p("anova", f"{outcome} ~ {factor} (one-way ANOVA)", max(p, kw.pvalue),
                   test="anova_or_kruskal")
    # Tukey post-hoc when omnibus (ANOVA or KW) is significant
    if min(p, kw.pvalue) < 0.05 and sub[factor].nunique() > 2:
        tuk = pairwise_tukeyhsd(sub[outcome], sub[factor])
        td = pd.DataFrame(tuk.summary().data[1:], columns=tuk.summary().data[0])
        rep.p("Tukey HSD post-hoc (family-wise 0.05):")
        rep.table(td.set_index(["group1", "group2"]))
        res[outcome]["tukey"] = td.to_dict("records")


def _eta_word(e):
    return "small" if e < .06 else "medium" if e < .14 else "large"


def paired_core_buffer(rep, res, df):
    rep.p("Within each territory the buffer and the protected core are a *matched "
          "pair* observed under the same regional pressure, so we test them paired.")
    for a_col, b_col, name in [
        ("core_loss", "buffer_loss", "GFC forest loss (%)"),
        ("core_fire_pct", "buffer_fire_pct", "cumulative fire scar (% of area)"),
    ]:
        d = df[[a_col, b_col]].dropna()
        diff = d[b_col] - d[a_col]
        tt = st.ttest_rel(d[b_col], d[a_col])
        w = st.wilcoxon(d[b_col], d[a_col])
        _dz = lambda x: x.mean() / x.std(ddof=1) if x.std(ddof=1) else np.nan
        dz = _dz(diff.values)
        dz_lo, dz_hi = boot_ci(_dz, diff.values, paired=True)
        rep.p(f"**{name}** — buffer mean {d[b_col].mean():.2f} vs core mean "
              f"{d[a_col].mean():.2f} (mean paired diff {diff.mean():+.2f}, n={len(d)}):")
        rep.code(
            f"Paired t-test:     t = {tt.statistic:.3f}, p = {_fmt_p(tt.pvalue)}\n"
            f"Wilcoxon signed:   W = {w.statistic:.1f}, p = {_fmt_p(w.pvalue)}\n"
            f"Cohen dz:          dz = {dz:.3f}  95% CI {_fmt_ci(dz_lo, dz_hi)}")
        res[name] = dict(buffer_mean=d[b_col].mean(), core_mean=d[a_col].mean(),
                         mean_diff=diff.mean(), t=tt.statistic, p_t=tt.pvalue,
                         wilcoxon_p=w.pvalue, cohen_dz=dz, cohen_dz_ci=[dz_lo, dz_hi],
                         n=len(d))
        rep.register_p("paired_core_buffer", f"{name} (paired t)", tt.pvalue,
                       test="paired_t")


def two_way(rep, res, df, f1, f2, outcome="gap"):
    sub = df[[outcome, f1, f2]].dropna()
    for f in (f1, f2):
        counts = sub[f].value_counts()
        sub = sub[sub[f].isin(counts[counts >= 3].index)]
    if sub[f1].nunique() < 2 or sub[f2].nunique() < 2:
        rep.p("Two-way ANOVA skipped (a factor collapsed below two usable levels).")
        return
    model = smf.ols(f"Q('{outcome}') ~ C(Q('{f1}')) * C(Q('{f2}'))", data=sub).fit()
    aov = anova_lm(model, typ=2)
    idx = {i: i.replace(f"C(Q('{f1}'))", f1).replace(f"C(Q('{f2}'))", f2) for i in aov.index}
    aov2 = aov.rename(index=idx)
    rep.p(f"**Two-way ANOVA** — {OUTCOMES.get(outcome, outcome)} ~ {f1} * {f2} "
          f"(N={len(sub)}):")
    rep.table(aov2[["sum_sq", "df", "F", "PR(>F)"]])
    res["anova_table"] = aov2[["sum_sq", "df", "F", "PR(>F)"]].reset_index().to_dict("records")
    for term in aov2.index:
        if term == "Residual":
            continue
        eta, omega = eta_omega(aov2, term)
        res.setdefault("effects", {})[term] = dict(
            F=aov2.loc[term, "F"], p=aov2.loc[term, "PR(>F)"], eta_sq=eta, omega_sq=omega)
        rep.register_p("two_way", f"{outcome} ~ {term} (two-way ANOVA)",
                       aov2.loc[term, "PR(>F)"], test="two_way_anova")


def ols_robust(rep, res, df, formula):
    sub = df.dropna(subset=_formula_vars(formula, df))
    model = smf.ols(formula, data=sub).fit(cov_type="HC3")
    rep.p(f"Cross-sectional OLS (HC3 heteroskedasticity-robust SE), N={int(model.nobs)}:")
    rep.code(f"{formula}\nR^2 = {model.rsquared:.3f}   adj R^2 = {model.rsquared_adj:.3f}   "
             f"F p = {_fmt_p(model.f_pvalue)}")
    ct = pd.DataFrame({"coef": model.params, "robust_se": model.bse,
                       "t": model.tvalues, "p": model.pvalues,
                       "ci_low": model.conf_int()[0], "ci_high": model.conf_int()[1]})
    rep.table(ct)
    res["ols"] = dict(formula=formula, n=int(model.nobs), r2=model.rsquared,
                      adj_r2=model.rsquared_adj, f_pvalue=model.f_pvalue,
                      coef=ct.reset_index().rename(columns={"index": "term"}).to_dict("records"))
    return ct


def _formula_vars(formula, df):
    lhs = formula.split("~")[0].strip()
    cols = [lhs]
    for c in df.columns:
        if c in formula:
            cols.append(c)
    return list(dict.fromkeys(cols))


def _cluster_ols(formula, data, groups, drop_dummies=True):
    """Fit an OLS with territory-clustered SE; return (model, coef_table).

    With absorbed fixed effects the cluster-robust vcov is rank-deficient on the
    (dropped) dummy rows, which statsmodels flags with a sqrt-of-negative warning;
    the coefficients of interest are unaffected, so we silence just that noise."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        model = smf.ols(formula, data=data).fit(
            cov_type="cluster", cov_kwds={"groups": groups})
        # force the lazy sqrt(vcov) here, inside the warning guard
        ct = pd.DataFrame({"coef": model.params, "cluster_se": model.bse,
                           "z": model.tvalues, "p": model.pvalues})
    if drop_dummies:  # hide the many territory/year fixed-effect rows from the report
        ct = ct[~ct.index.str.startswith(("C(territory)", "C(year)"))]
    return model, ct


def panel_model(rep, res, ds: DS):
    p = ds.d / "data" / "governance_rate_panel.csv"
    if not p.is_file():
        return
    pan = pd.read_csv(p)
    pan = pan.dropna(subset=["hansen_loss_rate"])
    multi_region = pan["region"].nunique() > 1
    n_clusters = int(pan["territory"].nunique())
    res["panel"] = {}

    # --- Model A: baseline pooled panel (scope + posture [+ region]) ---------
    rhsA = "C(scope) + C(posture)" + (" + C(region)" if multi_region else "")
    try:
        mA, ctA = _cluster_ols(f"hansen_loss_rate ~ {rhsA}", pan, pan["territory"])
    except Exception as e:  # noqa: BLE001
        rep.p(f"Panel model skipped ({type(e).__name__}: {e}).")
        return
    rep.p(f"**Model A — pooled governance panel.** Territory × year × scope panel "
          f"(N={int(mA.nobs)} obs, SE clustered by territory, {n_clusters} clusters). "
          f"Outcome = annual Hansen loss rate (% of area). This is the descriptive "
          f"baseline and it *reproduces the front-loading confound* — hostile "
          f"'Opposed/mixed' posture appears with lower annual loss because most "
          f"legacy clearing predates the satellite window.")
    rep.code(f"hansen_loss_rate ~ {rhsA}   [cluster-robust]\nR^2 = {mA.rsquared:.3f}")
    rep.table(ctA)
    res["panel"]["model_A"] = dict(
        formula=f"hansen_loss_rate ~ {rhsA}", n=int(mA.nobs), n_clusters=n_clusters,
        r2=mA.rsquared, coef=ctA.reset_index().rename(columns={"index": "term"}).to_dict("records"))

    # --- Model B: two-way (territory + year) fixed effects -------------------
    # Year FE absorb the national front-loading trend; territory FE absorb every
    # time-invariant area trait, so scope + posture are identified *within* area
    # and year. This is the confound-robust upgrade of Model A.
    rhsB = "C(scope) + C(posture) + C(year) + C(territory)"
    try:
        mB, ctB = _cluster_ols(f"hansen_loss_rate ~ {rhsB}", pan, pan["territory"])
        rep.p(f"**Model B — two-way fixed effects (territory + year).** Same panel, "
              f"now netting out every time-invariant area trait *and* the common "
              f"annual trend, so the scope and posture coefficients are identified "
              f"from *within-area, within-year* variation only (fixed-effect dummy "
              f"rows suppressed for readability).")
        rep.code(f"hansen_loss_rate ~ {rhsB}   [cluster-robust]\n"
                 f"within R^2 = {mB.rsquared:.3f}   N = {int(mB.nobs)}")
        rep.table(ctB)
        for term in ctB.index:
            if term.startswith("C(posture)") or term.startswith("C(scope)"):
                rep.register_p("panel", f"[FE panel] {term}", ctB.loc[term, "p"],
                               test="twoway_fe_ols")
        res["panel"]["model_B"] = dict(
            formula=f"hansen_loss_rate ~ {rhsB}", n=int(mB.nobs), n_clusters=n_clusters,
            r2=mB.rsquared,
            coef=ctB.reset_index().rename(columns={"index": "term"}).to_dict("records"))
    except Exception as e:  # noqa: BLE001
        rep.p(f"Model B (two-way FE) skipped ({type(e).__name__}: {e}).")

    # --- Model C: rates on continuous pressure + change window ---------------
    # Explicit panel-level H1/H2 test, on the MapBiomas rate series (which start
    # ~1987 and are less front-loaded than Hansen), one model per rate.
    rep.p("**Model C — explicit H1/H2 panel test.** Annual MapBiomas rates on the "
          "continuous `combined_pressure` (H2) and the `change_window` flag (H1), "
          "with scope and year FE and territory-clustered SE. Coefficients are pp of "
          "area/yr per +1 pressure unit / per change window.")
    res["panel"]["model_C"] = {}
    for rate, name in [("mb_defor_primary_rate", "Primary deforestation"),
                       ("mb_fire_scar_rate", "Fire scars")]:
        sub = pan.dropna(subset=[rate, "combined_pressure", "change_window"])
        if sub.empty:
            continue
        try:
            mC, ctC = _cluster_ols(
                f"{rate} ~ combined_pressure + C(change_window) + C(scope) + C(year)",
                sub, sub["territory"])
            rep.p(f"*{name}* (N={int(mC.nobs)}):")
            rep.table(ctC)
            for term in ctC.index:
                if term.startswith(("combined_pressure", "C(change_window)")):
                    rep.register_p("panel", f"[{name}] {term}", ctC.loc[term, "p"],
                                   test="rate_panel_ols")
            res["panel"]["model_C"][rate] = dict(
                n=int(mC.nobs), r2=mC.rsquared,
                coef=ctC.reset_index().rename(columns={"index": "term"}).to_dict("records"))
        except Exception as e:  # noqa: BLE001
            rep.p(f"Model C ({name}) skipped ({type(e).__name__}: {e}).")


def multiplicity(rep, res, out: Path):
    """Benjamini–Hochberg FDR across the pre-specified primary tests."""
    prim = [r for r in rep.pvals if r["primary"]]
    if not prim:
        rep.p("No pre-specified p-values were registered — nothing to adjust.")
        return
    df = pd.DataFrame(prim)
    df["q_bh"] = benjamini_hochberg(df["p"].values)
    df["sig_raw"] = df["p"] < 0.05
    df["sig_fdr"] = df["q_bh"] < 0.05
    df = df.sort_values("p").reset_index(drop=True)
    n_raw, n_fdr = int(df["sig_raw"].sum()), int(df["sig_fdr"].sum())
    rep.p(f"""
        The battery above evaluates {len(df)} pre-specified primary hypothesis tests
        (paired core–buffer contrasts, primary- and secondary-factor comparisons,
        any two-way and timing tests, and the fixed-effect panel coefficients).
        Because they are few and pre-specified rather than screened, the main text
        reports uncorrected p-values; here we additionally control the false-discovery
        rate (Benjamini–Hochberg). **{n_raw}** tests are significant at raw α = 0.05 and
        **{n_fdr}** survive FDR control at q < 0.05 — the gap between the two is the
        honest multiplicity exposure of this dataset.
    """)
    show = df[["family", "label", "test", "p", "q_bh", "sig_fdr"]].copy()
    rep.table(show.set_index(["family", "label"]))
    show.to_csv(out / "tables" / "fdr_correction.csv", index=False)
    res.update(n_tests=len(df), n_sig_raw=n_raw, n_sig_fdr=n_fdr,
               table=df.to_dict("records"))


# --------------------------------------------------------------------------- #
# Data prep                                                                    #
# --------------------------------------------------------------------------- #

def build_frame(ds: DS) -> pd.DataFrame:
    s = pd.read_csv(ds.d / "data" / "summary_metrics.csv")
    m = pd.read_csv(ds.d / "data" / "territory_metadata.csv")
    df = s.merge(m, on=["group", "territory"], how="left")
    df["core_loss"] = df["t_gfc_loss_pct_of_2000_cover"]
    df["buffer_loss"] = df["b_gfc_loss_pct_of_2000_cover"]
    df["gap"] = df["buffer_loss"] - df["core_loss"]
    df["core_forest_change_pct"] = df["t_forest_change_pct"]
    df["core_fire_pct"] = df["t_mb_fire_scar_total_ha"] / df["t_area_total_ha"] * 100
    df["buffer_fire_pct"] = df["b_mb_fire_scar_total_ha"] / df["b_area_total_ha"] * 100
    df["log_area"] = np.log(df["t_area_total_ha"])
    if "protection_year" in df.columns:
        df["protection_year_c"] = df["protection_year"] - df["protection_year"].mean()
    if "category" in df.columns:
        df["category_bin"] = np.where(df["category"] == "Parque", "Parque", "Outras")
    # Drop quadrant-split / unreadable areas (NaN core & buffer loss)
    before = len(df)
    df = df.dropna(subset=["core_loss", "buffer_loss"])
    df.attrs["dropped"] = before - len(df)
    return df


# --------------------------------------------------------------------------- #
# Diagnostic figures                                                           #
# --------------------------------------------------------------------------- #

CB = ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"]


def fig_boxplot(df, outcome, factor, out: Path, title):
    sub = df[[outcome, factor]].dropna()
    counts = sub[factor].value_counts()
    order = counts[counts >= 2].index.tolist()
    data = [sub.loc[sub[factor] == g, outcome].values for g in order]
    if len(order) < 2:
        return None
    fig, ax = plt.subplots(figsize=(1.6 * len(order) + 2, 4.5))
    bp = ax.boxplot(data, patch_artist=True, widths=0.6, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="black", markeredgecolor="black", markersize=5))
    for i, box in enumerate(bp["boxes"]):
        box.set(facecolor=CB[i % len(CB)], alpha=0.65, edgecolor="#333")
    for i, g in enumerate(order):
        y = sub.loc[sub[factor] == g, outcome].values
        ax.scatter(np.full_like(y, i + 1, dtype=float) + np.random.uniform(-.08, .08, len(y)),
                   y, s=14, color="#222", alpha=.5, zorder=3)
    ax.set_xticks(range(1, len(order) + 1), [f"{g}\n(n={counts[g]})" for g in order], fontsize=8)
    ax.set_ylabel(OUTCOMES.get(outcome, outcome), fontsize=9)
    ax.set_title(title, fontsize=10)
    ax.axhline(0, color="#888", lw=.8, ls="--")
    ax.grid(axis="y", alpha=.25)
    fig.tight_layout()
    path = out / f"box_{outcome}_by_{factor}.png"
    fig.savefig(path, dpi=150); plt.close(fig)
    return path


def fig_qq(resid, out: Path, name):
    fig, ax = plt.subplots(figsize=(4.5, 4.5))
    st.probplot(resid, dist="norm", plot=ax)
    ax.get_lines()[0].set(marker="o", markerfacecolor=CB[0], markeredgecolor="#333", markersize=5, alpha=.7)
    ax.get_lines()[1].set(color=CB[1], lw=1.5)
    ax.set_title(f"Normal Q-Q — residuals ({name})", fontsize=10)
    fig.tight_layout()
    path = out / f"qq_{name}.png"
    fig.savefig(path, dpi=150); plt.close(fig)
    return path


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(ds: DS):
    out = ds.d / "statistics"
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    df = build_frame(ds)
    rep = Reporter(ds)

    rep.h(f"Statistical analysis — {ds.label}", level=1)
    rep.p(f"""
        *Auto-generated by `utils/manuscript_statistics.py` — a re-runnable, step-by-step
        registry backing the statistics in `{ds.manuscript}`.*
        Environment: Python {sys.version.split()[0]}, scipy {__import__('scipy').__version__},
        statsmodels {__import__('statsmodels').__version__}. Analysis unit = protected area (territory);
        N = {len(df)} usable areas ({df.attrs['dropped']} dropped as quadrant-split / unreadable).
        {ds.notes}
    """)
    rep.p("Outcome variables (all derived from the buffer-referenced pipeline):")
    rep.table(pd.DataFrame({"variable": list(OUTCOMES), "definition": list(OUTCOMES.values())}).set_index("variable"), floatfmt=0)

    # Step 1 — descriptives
    s = rep.step("descriptives", "Descriptive statistics")
    desc = df[list(OUTCOMES)].describe().T
    rep.table(desc)
    desc.to_csv(out / "tables" / "descriptives.csv")
    s["table"] = desc.reset_index().to_dict("records")

    # Step 2 — paired core vs buffer
    s = rep.step("paired_core_buffer", "Paired core-vs-buffer contrast")
    paired_core_buffer(rep, s, df)

    # Step 3 — primary factor
    pf = ds.primary_factor
    s = rep.step("primary_factor", f"Primary comparison by {pf}")
    sub = df.copy()
    n_levels = sub[pf].dropna().nunique()
    for outcome in ["gap", "core_loss", "buffer_loss", "core_fire_pct"]:
        if n_levels == 2:
            two_group(rep, sub.dropna(subset=[outcome, pf]), s, outcome, pf)
        else:
            oneway(rep, sub, s, outcome, pf)
    fbox = fig_boxplot(df, "gap", pf, out / "figures", f"Protection gap by {pf}")

    # Step 4 — secondary one-way ANOVAs
    s = rep.step("secondary_anova", "Secondary one-way ANOVAs")
    for fac in ds.anova_factors:
        if fac == pf or fac not in df.columns:
            continue
        oneway(rep, df, s, "gap", fac)
        oneway(rep, df, s, "core_loss", fac)

    # Step 5 — two-way
    if ds.twoway:
        s = rep.step("two_way", f"Two-way ANOVA ({ds.twoway[0]} x {ds.twoway[1]})")
        two_way(rep, s, df, *ds.twoway, outcome="gap")

    # Step 6 — timing trend (indigenous)
    if ds.trend_var and ds.trend_var in df.columns:
        s = rep.step("timing_trend", f"Timing trend ({ds.trend_var} vs gap)")
        d = df[[ds.trend_var, "gap"]].dropna()
        r, pr = st.pearsonr(d[ds.trend_var], d["gap"])
        rho, prho = st.spearmanr(d[ds.trend_var], d["gap"])
        slope, intc, rv, pv, se = st.linregress(d[ds.trend_var], d["gap"])
        rep.p(f"Does the protection gap depend on *when* the area reached its "
              f"current status? (marco-temporal test, n={len(d)})")
        rep.code(
            f"Pearson r  = {r:.3f}, p = {_fmt_p(pr)}\n"
            f"Spearman rho = {rho:.3f}, p = {_fmt_p(prho)}\n"
            f"OLS slope  = {slope:.3f} pp/yr (SE {se:.3f}), p = {_fmt_p(pv)}")
        s.update(dict(pearson_r=r, pearson_p=pr, spearman_rho=rho, spearman_p=prho,
                      slope=slope, slope_p=pv, n=len(d)))
        rep.register_p("timing_trend", f"{ds.trend_var} vs gap (OLS slope)", pv,
                       test="linregress")

    # Step 7 — OLS
    s = rep.step("ols", "Cross-sectional OLS (robust SE)")
    try:
        ct = ols_robust(rep, s, df, ds.ols_formula)
        model = smf.ols(ds.ols_formula, data=df.dropna(subset=_formula_vars(ds.ols_formula, df))).fit()
        fig_qq(model.resid, out / "figures", "ols_gap")
    except Exception as e:  # noqa: BLE001
        rep.p(f"OLS skipped ({type(e).__name__}: {e}).")

    # Step 8 — panel econometrics
    s = rep.step("panel", "Panel econometric model (cluster-robust)")
    panel_model(rep, s, ds)

    # Step 9 — multiplicity correction across the pre-specified family
    s = rep.step("multiplicity", "Multiplicity correction (Benjamini–Hochberg FDR)")
    multiplicity(rep, s, out)

    rep.h("Reproducibility", level=2)
    rep.p(f"""
        Re-run with `.venv_stats/bin/python utils/manuscript_statistics.py {ds.key}`.
        Inputs: `data/summary_metrics.csv`, `data/territory_metadata.csv`,
        `data/governance_rate_panel.csv`. Outputs in `statistics/`
        (`STATISTICS_REPORT.md`, `results.json`, `tables/`, `figures/`).
        Significance threshold alpha = 0.05 throughout; effect-size conventions:
        Hedges g / Cohen dz (0.2/0.5/0.8), eta^2 (0.01/0.06/0.14). Effect sizes carry
        percentile bootstrap 95% CIs (2,000 resamples for g/dz, 1,000 for eta^2;
        seed 42). The panel step fits three specifications — (A) pooled scope+posture,
        (B) two-way territory+year fixed effects, (C) MapBiomas rates on continuous
        combined_pressure + change_window — all with territory-clustered SE. A final
        Benjamini-Hochberg step FDR-adjusts the pre-specified primary tests
        (`tables/fdr_correction.csv`).
    """)

    rep.save(out)
    print(f"[{ds.key}] wrote {out}/STATISTICS_REPORT.md  (N={len(df)})")
    return rep.results


if __name__ == "__main__":
    keys = sys.argv[1:] or list(DATASETS)
    np.random.seed(42)
    for k in keys:
        run(DATASETS[k])
