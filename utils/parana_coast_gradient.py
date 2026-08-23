#!/usr/bin/env python3
"""Add a coast-to-interior (east-west) breakdown to the already-built
parana_parques report set.

Parana runs from the Atlantic coast (~-48.5 deg longitude) to the Paraguay/
Argentina border (~-54.5 deg) -- a gradient the stock sphere/creation-era/
macro-region axes in national_uc_census_report.py cannot see (macro-region is
"Sul" for all but one unit). This script reuses the already-written
data/*.csv from a prior run_dataset() pass (no batch/EE reload), joins each
unit's centroid longitude from the UC gpkg, buckets into longitude tertiles
(Litoral / Planalto / Oeste), and inserts an idempotent markdown block (EN +
pt-br) into both headline reports plus a two-panel figure.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import governance_policy_report as gov  # noqa: E402

OUT = Path("/media/leandromb/a659eae9-58a3-42ca-b03e-47a9f716e89a/yvynation_report/parana_parques")
ZONE_LABELS = ["Oeste (fronteira Paraguai)", "Planalto (interior)", "Litoral (costa atlântica)"]
ZONE_LABELS_EN = ["West (Paraguay border)", "Interior plateau", "Coast (Atlantic)"]


def load_longitudes(names: list[str]) -> pd.Series:
    gu = gpd.read_file(gov.GPKG_UC)
    gu["_norm"] = gu["nome_uc"].map(gov._norm)
    gu["_lon"] = gu.geometry.centroid.x
    lut = dict(zip(gu["_norm"], gu["_lon"]))
    out = {}
    for n in names:
        v = lut.get(gov._norm(n))
        if v is None:
            v = lut.get(gov._strip_code(n)) if hasattr(gov, "_strip_code") else None
        out[n] = v
    return pd.Series(out, name="longitude")


def build_zone_tables():
    meta = pd.read_csv(OUT / "data" / "territory_metadata.csv")
    summary = pd.read_csv(OUT / "data" / "summary_metrics.csv")
    panel = pd.read_csv(OUT / "data" / "governance_rate_panel.csv")

    lon = load_longitudes(meta["territory"].tolist())
    meta = meta.merge(lon.rename("longitude"), left_on="territory", right_index=True, how="left")
    missing = meta[meta["longitude"].isna()]["territory"].tolist()
    if missing:
        print(f"  WARNING: no longitude match for {missing}")
    meta = meta.dropna(subset=["longitude"]).copy()

    meta["zone_en"] = pd.qcut(meta["longitude"], 3, labels=ZONE_LABELS_EN)
    meta["zone_pt"] = pd.qcut(meta["longitude"], 3, labels=ZONE_LABELS)

    s = summary.merge(meta[["group", "territory", "longitude", "zone_en", "zone_pt", "sphere"]],
                       on=["group", "territory"], how="inner")
    s["protection_gap"] = s["b_gfc_loss_pct_of_2000_cover"] - s["t_gfc_loss_pct_of_2000_cover"]

    def _grp(by):
        g = s.groupby(by, observed=True).agg(
            n=("territory", "size"),
            area=("t_area_total_ha", "sum"),
            lon_min=("longitude", "min"),
            lon_max=("longitude", "max"),
            t_fc=("t_forest_change_pct", "mean"),
            b_fc=("b_forest_change_pct", "mean"),
            t_gfc=("t_gfc_loss_pct_of_2000_cover", "mean"),
            b_gfc=("b_gfc_loss_pct_of_2000_cover", "mean"),
            gap=("protection_gap", "mean"),
        )
        return g.reindex(ZONE_LABELS_EN if by == "zone_en" else ZONE_LABELS)

    g_en = _grp("zone_en")
    g_pt = _grp("zone_pt")

    p = panel.merge(meta[["group", "territory", "zone_en"]], on=["group", "territory"], how="inner")
    rows = []
    for val, sub in p.groupby("zone_en", observed=True):
        core = sub[sub["scope"] == "territory"]
        buf = sub[sub["scope"] == "buffer"]
        rows.append({
            "zone_en": val, "n": sub[["group", "territory"]].drop_duplicates().shape[0],
            "core_defor": core["mb_defor_primary_rate"].mean(),
            "buf_defor": buf["mb_defor_primary_rate"].mean(),
            "core_fire": core["mb_fire_scar_rate"].mean(),
            "buf_fire": buf["mb_fire_scar_rate"].mean(),
        })
    rates = pd.DataFrame(rows).set_index("zone_en").reindex(ZONE_LABELS_EN)

    return meta, s, g_en, g_pt, rates


def chart_coast_gradient(meta, s, g_en, fig_dir: Path) -> Path:
    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(13, 5))

    x = np.arange(len(g_en))
    w = 0.35
    ax0.bar(x - w / 2, g_en["gap"], w, label="Protection gap (pp)", color="#166534")
    ax0.bar(x + w / 2, g_en["t_gfc"], w, label="Core GFC loss (%)", color="#b03a2e")
    ax0.set_xticks(x, [f"{lbl}\n(n={int(r['n'])})" for lbl, r in g_en.iterrows()], fontsize=8)
    ax0.set_title("Outcomes by coast-to-interior zone")
    ax0.set_ylabel("pp  /  % of 2000 cover")
    ax0.axhline(0, color="#888", lw=.8)
    ax0.legend(fontsize=8)
    ax0.grid(axis="y", alpha=0.3)

    sphere_color = {"Federal": "#2563eb", "Estadual": "#059669", "Municipal": "#b45309"}
    for sph, sub in s.dropna(subset=["longitude"]).groupby("sphere"):
        ax1.scatter(sub["longitude"], sub["protection_gap"], s=36, alpha=0.85,
                    color=sphere_color.get(sph, "#444"), label=sph)
    sd = s.dropna(subset=["longitude", "protection_gap"])
    if len(sd) >= 3:
        b, a = np.polyfit(sd["longitude"], sd["protection_gap"], 1)
        xs = np.array([sd["longitude"].min(), sd["longitude"].max()])
        ax1.plot(xs, a + b * xs, "k--", lw=1, label=f"trend ({b:+.2f} pp/deg)")
    ax1.set_xlabel("Longitude (border → coast, west to east, left to right)")
    ax1.set_ylabel("Protection gap (pp)")
    ax1.set_title("Longitude vs protection gap, by sphere")
    ax1.legend(fontsize=8)
    ax1.grid(alpha=0.3)

    fig.suptitle("Coast-to-interior gradient across Paraná's parks", y=1.02, fontsize=13)
    fig.tight_layout()
    path = fig_dir / "gp_coast_gradient.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def fmt(v, unit="", dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:,.{dec}f}{unit}"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


START, END = "<!-- coast-gradient:start -->", "<!-- coast-gradient:end -->"


def block_en(g_en, rates, fig_name) -> str:
    L = [START, "## Coast-to-interior gradient (Atlantic → Paraguay border)", "",
         "*Paraná runs from the Atlantic coast to the Paraguay/Argentina border — a "
         "west-east gradient the sphere/creation-era/macro-region axes above cannot "
         "see (macro-region is \"Sul\" for 41 of 42 units). Units are split into "
         "longitude tertiles (14 each).*", "",
         f"![coast gradient](figures/{fig_name})", ""]
    L += md_table(
        ["Zone", "n", "Lon. range", "Σ area (ha)", "Forest chg core/buf %",
         "GFC loss core/buf %", "Protection gap pp"],
        [[idx, int(r["n"]), f"{r['lon_min']:.2f}° to {r['lon_max']:.2f}°",
          fmt(r["area"], "", 0), f"{fmt(r['t_fc'])} / {fmt(r['b_fc'])}",
          f"{fmt(r['t_gfc'])} / {fmt(r['b_gfc'])}", fmt(r["gap"], "", 1)]
         for idx, r in g_en.iterrows()],
    )
    L += ["", "Annual land-change rates, core / buffer, by zone:", ""]
    L += md_table(
        ["Zone", "n", "Defor core/buf %", "Fire core/buf %"],
        [[idx, int(r["n"]), f"{fmt(r['core_defor'], '', 3)} / {fmt(r['buf_defor'], '', 3)}",
          f"{fmt(r['core_fire'], '', 3)} / {fmt(r['buf_fire'], '', 3)}"]
         for idx, r in rates.iterrows()],
    )
    coast_gap = g_en.loc[ZONE_LABELS_EN[2], "gap"]
    west_gap = g_en.loc[ZONE_LABELS_EN[0], "gap"]
    coast_fire = rates.loc[ZONE_LABELS_EN[2], "core_fire"]
    west_fire = rates.loc[ZONE_LABELS_EN[0], "core_fire"]
    direction = "widens" if coast_gap > west_gap else "narrows"
    fire_dir = "higher" if coast_fire > west_fire else "lower"
    L += ["",
          f"Moving from the western border toward the coast, the protection gap "
          f"**{direction}** ({fmt(west_gap, ' pp')} west → {fmt(coast_gap, ' pp')} "
          f"coast), and core fire runs **{fire_dir}** at the coast "
          f"({fmt(west_fire, ' %', 3)} west vs {fmt(coast_fire, ' %', 3)} coast, "
          "% of area/yr). Read directionally, not causally — zone correlates with "
          "biome (Mata Atlântica coast/escarpment vs Cerrado/mixed-forest interior), "
          "unit age and sphere, none of which are held constant here.",
          "", END]
    return "\n".join(L)


def block_pt(g_pt, fig_name) -> str:
    L = [START, "## Gradiente costa-interior (Atlântico → fronteira com o Paraguai)", "",
         "*O Paraná vai da costa atlântica até a fronteira com Paraguai/Argentina — um "
         "gradiente leste-oeste que os eixos de esfera/época de criação/macrorregião "
         "acima não conseguem captar (a macrorregião é \"Sul\" para 41 das 42 "
         "unidades). As unidades são divididas em tercis de longitude (14 cada).*", "",
         f"![coast gradient](figures/{fig_name})", ""]
    L += md_table(
        ["Zona", "n", "Faixa de longitude", "Σ área (ha)", "Var. floresta núcleo/entorno %",
         "Perda GFC núcleo/entorno %", "Gap de proteção pp"],
        [[idx, int(r["n"]), f"{r['lon_min']:.2f}° a {r['lon_max']:.2f}°".replace(".", ","),
          fmt(r["area"], "", 0).replace(",", "."),
          f"{fmt(r['t_fc']).replace('.', ',')} / {fmt(r['b_fc']).replace('.', ',')}",
          f"{fmt(r['t_gfc']).replace('.', ',')} / {fmt(r['b_gfc']).replace('.', ',')}",
          fmt(r["gap"], "", 1).replace(".", ",")]
         for idx, r in g_pt.iterrows()],
    )
    coast_gap = g_pt.loc[ZONE_LABELS[2], "gap"]
    west_gap = g_pt.loc[ZONE_LABELS[0], "gap"]
    direction = "aumenta" if coast_gap > west_gap else "diminui"
    L += ["",
          f"Da fronteira oeste em direção ao litoral, o gap de proteção "
          f"**{direction}** ({fmt(west_gap, ' pp').replace('.', ',')} no oeste → "
          f"{fmt(coast_gap, ' pp').replace('.', ',')} no litoral). Leia isso como uma "
          "correlação direcional, não causal — a zona está correlacionada com o bioma "
          "(Mata Atlântica no litoral/escarpa vs. Cerrado/floresta mista no interior), "
          "com a idade da unidade e com a esfera de governança, nenhuma das quais é "
          "controlada aqui.",
          "", END]
    return "\n".join(L)


def _insert(path: Path, block: str, after_heading: str):
    text = path.read_text(encoding="utf-8")
    if START in text and END in text:
        pre = text[: text.index(START)]
        post = text[text.index(END) + len(END):]
        path.write_text(pre + block + post, encoding="utf-8")
        return
    marker = "\n" + after_heading
    if marker in text:
        i = text.index(marker) + len(marker)
        # insert right before the next "## " after this heading's content ends;
        # simplest robust option: append right after the heading's own paragraph
        # by inserting before the NEXT "\n## " occurrence.
        j = text.find("\n## ", i)
        if j == -1:
            path.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
        else:
            path.write_text(text[:j] + "\n\n" + block + "\n" + text[j:], encoding="utf-8")
    else:
        path.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")


def main():
    fig_dir = OUT / "figures"
    meta, s, g_en, g_pt, rates = build_zone_tables()
    fig_path = chart_coast_gradient(meta, s, g_en, fig_dir)
    en_block = block_en(g_en, rates, fig_path.name)
    pt_block = block_pt(g_pt, fig_path.name)

    _insert(OUT / "report_group_comparison.md", en_block, "## Breakdown by governance sphere")
    _insert(OUT / "report_group_comparison.pt-br.md", pt_block, "## Distribuição por esfera de governança")
    _insert(OUT / "report_governance_policy.md", en_block, "## Variation by governance sphere")
    _insert(OUT / "report_governance_policy.pt-br.md", pt_block, "## Variação por esfera de governança")
    meta.to_csv(OUT / "data" / "territory_metadata_with_zone.csv", index=False)
    print(f"Inserted coast-gradient section + wrote {fig_path}")


if __name__ == "__main__":
    main()
