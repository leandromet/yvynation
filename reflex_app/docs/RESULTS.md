# Results — reading the April 2026 run, territory by territory

This note walks through the six polygons of the four case studies as they appear
in the **April 2026 run outputs** (MapBiomas Collection 9, 1985–2023; Hansen GFC
to 2024), archived under
`~/Documents/2026_ubc/four_indigenous_territories/data/yvynation_reflex_results/`.
Numbers are taken from the exported `comparison_1985_vs_2023.csv`,
`hansen_gfc_summary.csv`, and `hansen_gfc_loss_by_year.csv` in each folder, and
cross-referenced to the chapter tables. See [METHODOLOGY.md](METHODOLOGY.md) for
how these were produced and [SYNTHESIS.md](SYNTHESIS.md) for the cross-case
argument.

The four cases are ordered **coast → west**, which is also **old → recent** in
the timing of their critical juncture. Read that way, the sequence is a single
argument: *the later the protective policy arrived relative to the frontier, the
more forest it was able to keep.*

| Folder | Polygon | Extent | Headline 1985→2023 story |
|---|---|---:|---|
| `Krenak_23401_…1504` | Krenak | 4,282 ha | Forest **+141%** on former pasture — recovery |
| `Krenak_de_Sete_Saloes_23402_…1512` | Krenak Sete Salões | 16,596 ha | Pasture −24%, Forest +6% — quiet mosaic shift |
| `Bacurizinho_4901_…1148` | Bacurizinho (1983 demarcated) | 82,515 ha | Forest −3.6%, new pasture/soy/cane at edges |
| `Bacurizinho_4902_…1424` | Bacurizinho (2008 declared) | 133,984 ha | Forest −6.3%, +12,694 ha pasture — tenure gap |
| `Kayapo_23001_…1455` | Kayapó | 3,283,191 ha | Mining +1,352%, Pasture +1,352% — extractive lockstep |
| `Betania_6201_…1444` | Betânia | 122,347 ha | Floodable Forest −5.3%, Wetland +223% — hydrology |

> A 7th folder (`Bacurizinho_4901_…1147`) is a duplicate 4901 run kept for
> completeness. `metadata.json` mojibake (`Kayap�`) is a UTF-8 export bug in
> the territory-name field only; it does not affect any numeric output.

---

## Krenak (23401) — coastal Atlantic Forest, the recovery case

**Critical juncture 1808 (the "Just War" decree); title restored 1997 (STF).**

The headline is *forest recovery on former pasture*. Forest Formation more than
doubles, 354 ha (8.3%) → 856 ha (20.0%), **+141%**; Pasture falls 2,879 → 2,189 ha
(−24%); Mosaic of Uses gains +220 ha.

Hansen adds the crucial caveat: the satellite era did **not** begin with intact
forest. Tree-cover 2000 was already only 56.4% (2,414 ha), and 2001–2023 loss was
189 ha (7.8% of that baseline), concentrated in **2014 (63 ha), 2017 (39 ha),
2015 (32 ha)** — fire-driven pasture stress years in Minas Gerais. Hansen "gain"
(a 2000–2012 mask) is near zero, so the 502 ha MapBiomas recovery must be
**secondary regrowth** the Hansen gain mask cannot see.

**What this refines in the chapter:** the "89% deforestation" figure is a *1985
baseline*, not a present trajectory. Post-1988 the direction is slow recovery,
concentrated on land that used to be pasture — consistent with leased-land
returns after 1980 and judicial restitution in 1997. The 2015 Fundão dam
collapse does **not** register as canopy loss here; its only pixel trace is the
River class shrinking 30 → 7 ha. Krenak's lesson: *policy recognition is
necessary but insufficient once path dependence has already exhausted the
resource* — the forest was gone before the satellite record began.

## Krenak de Sete Salões (23402) — same direction, larger scale

Same story, bigger polygon: Pasture −1,145 ha (−24%), Mosaic +656 ha (+18%),
Forest +436 ha (+6%); marginal new uses appear (Coffee +39 ha, Forest Plantation
+27.5 ha). Hansen: tree cover 2000 = 78.4%, 2001–2023 loss ≈ **0 ha**. For
practical purposes Sete Salões lost *no* canopy over the satellite era — its
dynamic is internal mosaic reorganisation (pasture → mosaic → secondary forest),
reflecting its status as first a state park and later an Indigenous reserve.

---

## Bacurizinho — the boundary-effect natural experiment

**Refuge after the 1901 Alto Alegre rebellion; original block homologated 1983
(4901); expansion declared 2008 (4902); TRF1 finalisation order 2025.**

Running the 1983-homologated block and the 2008-declared expansion together is
the methodological payoff: two polygons in the *same* biome and pressure profile
that differ only in the **legal age of the boundary**.

### 4901 (original, 82,515 ha) — demarcated and holding

Forest falls modestly 82,865 → 79,881 ha (−3.6%); Savanna −40%. The telling
signal is what *appears* from zero: Pasture (690 ha), Sugar Cane (583 ha),
Soybean (341 ha) — the leakage the 1983 demarcation could not fully prevent.
Hansen: tree cover 2000 = 99.8%, 2001–2023 loss 5,908 ha (**7.1%**), peaking in
the Maranhão fire years 2017 (1,722 ha) and 2014 (1,542 ha).

### 4902 (expansion, 133,984 ha) — the tenure gap

Same direction, much higher amplitude. Forest −7,041 ha (−6.3%, over twice the
absolute loss of 4901); Savanna −43%. **Pasture appears at 12,696 ha** (vs 690 ha
in 4901); "Other non-Vegetated Areas" (mining/quarry scars, bare degraded land)
jumps 4 → 183 ha (33×). Hansen: tree cover 2000 = 92.3%, 2001–2023 loss 17,062 ha
(**13.6%**).

### The boundary effect

| Indicator | 4901 (1983) | 4902 (2008) | Differential |
|---|---:|---:|---:|
| Forest Δ 1985–2023 | −3.6% | −6.3% | **1.75×** |
| Pasture 2023 | 690 ha | 12,696 ha | 18.4× |
| Hansen loss 2001–2023 | 7.1% | 13.6% | **1.91×** |
| Hansen 2014+2017 loss | 3,264 ha | 6,043 ha | 1.85× |

Three independent metrics agree on a **1.75–1.91× differential** — a clean
internal cross-check, and a range that brackets the Pfaff & Robalino (2017)
Amazon protection-effect literature. Bacurizinho's lesson: *the same legal
category produces different pixel outcomes when tenure clarity differs.* Legal
declaration is necessary but not sufficient; what matters is whether demarcation
was physically executed and overlapping private (CAR) claims resolved. The 2025
TRF1 order therefore has a quantifiable expected effect: closing the gap would
save ≈9,000 ha of Hansen canopy over a 23-year horizon.

---

## Kayapó (23001) — the mining–pasture lockstep

**1970s BR-163 contact disaster; Altamira Gathering 1989; ratified 1991.**

At 3.28 M ha this is the largest polygon in the thesis, processed in four
quadrants (§Methodology 6). Two effects only appear at this scale.

**The lockstep.** Between 1985 and 2023, Pasture and Mining grow at the *same*
relative rate inside the demarcated polygon — both **+1,352.6%**:

| Class | 1985 (ha) | 2023 (ha) | Δ ha | Δ % |
|---|---:|---:|---:|---:|
| Forest Formation | 2,875,570 | 2,821,132 | −54,438 | −1.9% |
| Pasture | 2,105 | 30,597 | +28,492 | +1,352.6% |
| Mining | 951 | 13,825 | +12,874 | +1,352.6% |
| Floodable Forest | 170,632 | 161,178 | −9,454 | −5.5% |
| Wetland | 3,647 | 2,049 | −1,598 | −43.8% |

The equal percentage is a numeric coincidence, but the story is real: the two
extractive land uses expand **together, not sequentially**, inside a mostly
intact forest. The 57 new mining-process filings of 2026 (§9.6) are the next
chapter of a process the satellite record can already see.

**The Hansen warning.** MapBiomas shows Forest Formation −1.9%; Hansen shows a
14.2% canopy-loss footprint over 2001–2023 — because Hansen captures
degradation, thinning, and burn-area hits that MapBiomas' persistence logic
re-absorbs as the same class. The annual series is post-2017 heavy: **2017
(73,644 ha)**, 2020 (32,074 ha). The **2024 row (305,250 ha)** is a wildfire
scar, not canopy removal — the caveat that drove the Collection 10/11 upgrade.

**The hydrological footprint.** A quieter signal: Wetland collapses 44%
(3,647 → 2,049 ha) and River/Lake shrinks 6%, alongside −5.5% Floodable Forest.
This coincides with Belo Monte's 2011 licensing and 2016 commercial start even
though the dam sits ~900 km downstream — the framework registered a water-regime
signal the forest-class series alone would have missed.

Kayapó's lesson: *strong institutional capacity plus international visibility
produces the cleanest demonstration of policy effectiveness in the dataset* —
but the protective effect now depends on holding back the mining pipeline, and
even that strength is not autonomous from national political cycles (the 2019
rollback shows as a 2020 loss uptick).

---

## Betânia (6201) — the hydrological re-classification case

**Missionary land purchase in the 1960s; delimited 1985, declared 1991,
homologated 1995.**

The lowest-deforestation case — but the dominant dynamic is *not* agricultural.
Forest Formation barely moves (−0.5%, −341 ha) and Floodable Forest declines only
5.3% (−2,496 ha); meanwhile **Wetland triples (+223%, +2,297 ha)** and Grassland
grows ten-fold (+932%, +698 ha):

| Class | 1985 (ha) | 2023 (ha) | Δ ha | Δ % |
|---|---:|---:|---:|---:|
| Forest Formation | 63,304 | 62,963 | −341 | −0.5% |
| Floodable Forest | 47,318 | 44,822 | −2,496 | −5.3% |
| River, Lake, Ocean | 10,106 | 9,607 | −500 | −4.9% |
| Wetland | 1,030 | 3,327 | +2,297 | +222.8% |
| Grassland | 74 | 772 | +698 | +932.0% |

This is a **hydrological footprint, not an agricultural one**: Floodable Forest
converting to open Wetland and Grassland, paired with River-class shrinkage, is
consistent with the Solimões várzea flood-regime change documented for
2010–2020 (extreme low-water years). Hansen: tree cover 2000 = 92.2%, 2001–2023
loss 4,254 ha (**3.7%** — the lowest in the set), with the only >500 ha year
being **2023 (789 ha)**, coinciding with the declared health emergency.

**What this refines in the chapter:** the "COVID/health emergencies are
non-deforestation shocks" framing is *half* confirmed — 2020 is quiet (281 ha,
at the multi-year median), but **2023 is a real +180% pressure spike**. And the
"minimal deforestation (<3%)" claim is slightly out of date (Hansen puts it at
3.7%). Betânia's lesson: *where path dependence runs cleanly through Indigenous
stewardship and recent recognition, the satellite record shows what an effective
policy regime looks like* — and the absence of a pixel transition (COVID) is
itself a meaningful finding when the hypothesis predicts stability.

---

## How to open the outputs

Each folder's `figures/*.html` are interactive Plotly charts; the
`exports/png_flat/` and `exports/png/` trees hold 2800×1800 PNGs with identical
filenames per territory (so `*__transitions_sankey.png` lines up across cases).
The single best figure per case study is `transitions_sankey.html` (the 1985→2023
flow) paired with `hansen_gfc_loss_by_year.html` (the policy-lag series). The
raw numbers above all come from `territory/<name>/comparison_1985_vs_2023.csv`
and the two `hansen_gfc_*.csv` files.
