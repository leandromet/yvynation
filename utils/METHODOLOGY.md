# Methodology — Yvynation land-change analysis and the batch comparison reports

*Companion to the offline reporting tools in `utils/` (`batch_report_aggregator.py`,
`governance_policy_report.py`) and the basis for the methods section of the
Yvynation paper. It documents, in reproducible detail, how the satellite data are
produced by the Yvynation Reflex application, how the sample of protected areas
was selected, and how the two report scripts turn per-territory exports into the
cross-territory, governance and policy findings used in the four case studies
(`reflex_app/docs/LeandroBiondo_case_studies`).*

---

## 1. Purpose and scope

The analysis has one guiding question: **does formal protection of a territory
change what happens to its land cover, and can that change be read against the
policy and political record that is supposed to drive it?** The answer is built
in three layers, each corresponding to a piece of software:

1. **Yvynation Reflex** (the web application) computes, for any polygon, a
   consistent battery of land-cover, deforestation, fire and forest-loss
   statistics from public Earth-observation archives, plus the same statistics
   for a surrounding buffer ring. It exports one self-contained folder per area.
2. **`batch_report_aggregator.py`** reads many such export folders, normalises
   them into tidy tables, and produces per-group side-by-side reports, a
   multi-sheet spreadsheet, and cross-territory comparison charts.
3. **`governance_policy_report.py`** joins those tables to an encoded record of
   Brazilian federal/state politics (1985–2024) and of annual environmental
   policy strength, then tests three hypotheses about the drivers of land change.

The design is deliberately **layered and file-based**: every intermediate is a
plain CSV or PNG, so a reviewer can inspect or re-derive any number without
re-running Earth Engine. The reports carry their own data-driven prose (verdicts
are computed from the tables, not hard-coded), which keeps the narrative honest
as the underlying collections are updated.

---

## 2. Data sources and provenance

All raster statistics come from three public archives, accessed through Google
Earth Engine inside the Reflex application (`reflex_app/yvynation/utils/`):

| Signal | Source asset | Role in the analysis |
|---|---|---|
| Land-cover class areas | **MapBiomas Collection 10** (`1985–2024`) annual land-use/land-cover | Composition, transition (Sankey) matrices, forest/anthropic split |
| Annual canopy loss | **Hansen Global Forest Change** (`UMD/hansen/global_forest_change`, v1.11–v1.13; year-code `2000 + code`) | Independent, sensor-based forest-loss cross-check, 2001 onward |
| Primary deforestation / secondary regrowth | **MapBiomas Deforestation & Secondary Vegetation** (Coll. 10.1; class 100 = deforestation, 200 = regrowth) | Annual primary-clearing and regrowth series |
| Fire scars | **MapBiomas Fire Collection 4** annual burned area | Annual fire series |

Ancillary vector data used for stratification and recognition tiers:

- `indigenous_lands_br202605.gpkg` — FUNAI Indigenous Lands (name, UF, `fase_ti`
  demarcation phase, homologation/regularisation/declaration dates).
- `environment_conservation_br202605.gpkg` — Conservation Units (name, UF,
  `grupo` = *Proteção Integral* / *Uso Sustentável*, `esfera` = governance
  sphere, `categoria`, creation year).

**Data-version discipline.** Because the collections are re-released on a yearly
cadence, every export records the exact asset version in its
`metadata.json`/`batch_summary.json`. The chapters were first written against
MapBiomas Collection 9 (1985–2023) + Hansen to 2024, then refreshed with the
Collection 10 batch run (1985–2024) + Hansen to 2025; a further revision is
planned for MapBiomas Collection 11 (expected August 2026). Reporting *both*
collections where they disagree is treated as part of the validation story, not
an inconsistency to be hidden (see §7, the Kayapó 2024 loss anomaly).

### 2.1 Two independent forest-loss measures, on purpose

MapBiomas (thematic classification) and Hansen GFC (canopy-cover change
detection) are produced by different teams with different methods. The framework
reports both for every area and never collapses them into one number. Systematic
disagreement is diagnostic: e.g. for Kayapó, MapBiomas shows a ~1.9 % Forest
Formation decline over 1985–2023 while Hansen shows a 14.2 % canopy-loss
footprint concentrated in a single 2024 wildfire event — a gap that flags a real
disturbance rather than a bug.

---

## 3. Study design and sampling

### 3.1 The two protected-area systems

The comparison is a **matched, cross-sectional design over two populations of
protected areas**:

- **Indigenous Lands (ILs)** — federally demarcated; internal recognition ladder
  from *Em Estudo* → *Delimitada* → *Declarada* → *Encaminhada RI* →
  *Homologada* → *Regularizada* (encoded as `IND_FASE_RANK`, weak → strong).
- **Conservation Units (UCs)** — split by protection group (*Proteção Integral*
  vs *Uso Sustentável*) and by governance sphere (federal/state/municipal).

Test batches used to develop the tooling: **46 Indigenous Lands** and **45
Conservation Units** (≈45–46 areas per system), a sample size chosen so that the
recognition tiers still hold enough areas to compare while keeping Earth Engine
processing tractable.

### 3.2 How the areas were selected (sampling frame)

The areas were **selected manually rather than drawn at random**, under three
explicit criteria that define the sampling frame and must be stated as such in
the paper because they shape external validity:

1. **Comparable size.** Areas of broadly similar extent were chosen so that a
   single 10 km buffer ring is a meaningful counterfactual for each core and so
   that no single very large polygon dominates the group aggregates. (Where a
   polygon exceeds ~1 million ha it is processed in quadrants — §4.3 — so the
   Kayapó block enters the analysis as four comparable sub-areas rather than one
   outlier.)
2. **National coverage across all states.** The sample spans the 26 states +
   Distrito Federal, so that every macro-region (Norte ≈ deep Amazon,
   Nordeste, Centro-Oeste, Sudeste, Sul) and every major biome is represented.
   This is what makes the *regional* analysis (§6.4) possible.
3. **Spatial separation between protected areas.** Areas were spaced at a
   reasonable distance from one another so that their 10 km buffers do not
   overlap and so that neighbouring protected areas are not double-counted as
   each other's "unprotected surroundings."

These criteria yield a **purposive, spatially-stratified sample**, not a
probability sample. The consequence for inference is stated plainly in the
caveats (§8): the results describe *this* set of comparable, well-separated
areas spanning Brazil, and associations are not adjusted for confounders such as
commodity prices, road access or biome. The four intensively-studied case
territories (Krenak / Krenak de Sete Salões, Bacurizinho 4901 & 4902 expansion,
Kayapó, Betânia) sit inside this frame and were chosen to span the full
biome/degradation gradient from coastal Atlantic Forest to deep western Amazon.

### 3.3 The core–buffer natural experiment

For every area the analysis computes statistics **twice**: once for the
protected **core** (the polygon itself) and once for a **10 km buffer ring**
around it. The buffer is the local counterfactual — the same neighbourhood,
climate and commodity frontier, differing chiefly in protection status. The
difference between the two (the *protection gap*, §5.4) is the paper's central
quasi-experimental estimand. Where an exclusive buffer was not available, a
nested-polygon substitute is used: Bacurizinho **4901** (homologated 1983) vs
**4902** (declared 2008 expansion) are nested in the same biome and pressure
profile and yield a 1.75–1.91× loss differential that brackets the Pfaff &
Robalino (2017) protection-effect literature.

---

## 4. Per-territory processing (Yvynation Reflex)

### 4.1 Outputs per area

Each analysed area produces a self-contained folder containing:

- `mapbiomas/` — per-year land-cover CSVs and a `{y1}_vs_{y2}_comparison` CSV;
  Sankey transition diagrams and comparison-bar figures (HTML/PNG).
- `deforestation_timeline/` — the annual series CSV
  (`hansen_loss`, `mb_defor_primary`, `mb_secondary_growth`, `mb_fire_scar`) plus
  raw and 5-year-moving-average figures.
- `hansen_gfc/` — a summary CSV (Tree Cover 2000, Forest Loss, Forest Gain) and a
  loss-by-year CSV/figure.
- `maps/` — static reference maps (MapBiomas y1/y2, satellite basemap,
  deforestation/secondary-vegetation, fire frequency 1985–y2, year of last fire).
- `metadata.json` / `README.txt` and the boundary GeoJSON.

### 4.2 Timeline indicators (definitions)

All timeline indicators are **areas in hectares per calendar year**, each
computed with a single stacked-band `reduceRegion` call to keep Earth Engine
round-trips low:

- `hansen_loss` — Hansen `lossyear` band, per-year area (year = `2000 + code`;
  code 0 = no loss).
- `mb_defor_primary` — MapBiomas deforestation class (100); auto-detects
  "year-value" vs "per-year class band" semantics.
- `mb_secondary_growth` — MapBiomas regrowth class (200).
- `mb_fire_scar` — MapBiomas Fire annual burned area (any non-zero per-year band).

### 4.3 Large-area handling

Polygons larger than ~1 million ha are clipped into four quadrants and processed
separately (to avoid Earth Engine timeouts), each written to its own sub-folder.
This is why Kayapó appears as NE / NW / SE / SW quadrants in the batch tables.

---

## 5. Aggregation and comparison (`batch_report_aggregator.py`)

The aggregator ingests any number of batch folders (`BATCH_DIR:LABEL …`) and
emits `data/` CSVs, a multi-sheet `yvynation_comparison.xlsx`, cross-territory
`figures/`, one `report_<group>.md` per batch, and a `README.md` index.

### 5.1 Land-cover class groupings

Every MapBiomas class is assigned to one of three interpretive groups so that
heterogeneous class lists are comparable across areas and biomes:

- **Forest** — Forest Formation, Savanna Formation, Mangrove, Floodable Forest,
  Wooded Sandbank Vegetation.
- **Natural non-forest** — Grassland, Wetland, Herbaceous Sandbank Vegetation,
  Hypersaline Tidal Flat, Rocky Outcrop, Beach and Sand, River/Lake/Ocean.
- **Anthropic** — Pasture, Mosaic of Uses, and all croplands (Soybean, Sugar
  Cane, Rice, Cotton, Coffee, Citrus, Palm Oil, temporary/perennial crops),
  Forest Plantation, Urban Area, Mining, Aquaculture, other non-vegetated.

A robustness detail baked into the loader: MapBiomas CSVs ship in two header
variants across collection versions (`Class_ID,Class,Pixels,Area_ha` vs
`Year,Class_ID,Class_Name,Area_ha,Area_km2`); the loader normalises
`Class_Name → Class` so both parse identically.

### 5.2 Per-area metrics

For each area (core and buffer) the aggregator computes:

- Total area (ha); forest / natural-non-forest / anthropic area in y1 and y2 and
  their change; **forest change %** (`100 × Δforest / forest_y1`); forest and
  anthropic share of area in y2.
- Hansen: Tree Cover 2000, Forest Loss, Forest Gain, and
  **GFC loss % of 2000 cover** (`100 × loss / tree_cover_2000`) — the version-
  independent loss rate used throughout.
- Timeline totals per series and the **peak deforestation year** (argmax of
  `mb_defor_primary`).

### 5.3 Cross-territory figures

- **Forest-change ranking** — horizontal bars, core vs buffer, per group.
- **Land-cover composition** — 100 % stacked bars of y2 class shares per area.
- **Inside-vs-outside scatter** — core GFC-loss % against buffer GFC-loss %,
  with the 45° line; points below the line lose less forest than their
  surroundings (the protection signal, area by area).
- **Group annual timelines** — summed deforestation and fire, core vs buffer.

### 5.4 The protection gap

The single headline estimand:

```
protection_gap = GFC_loss%(buffer) − GFC_loss%(core)      [percentage points]
```

A positive gap means the boundary is holding — the ring is losing more forest
than the protected interior. It is positive across essentially every area in the
sample, which is the clearest single sign the boundaries matter.

---

## 6. Governance and policy analysis (`governance_policy_report.py`)

This script imports the aggregator (for loaders and tidy tables — it does not
modify it), recovers each area's state and recognition tier from the two
GeoPackages, and joins the annual series to two encoded context datasets. It
writes **Report 3** (ILs vs UCs head-to-head) and **Report 4** (the governance
hypotheses), and persists an enriched panel (`governance_rate_panel.csv`) for
reuse.

### 6.1 Rate normalisation

All governance analysis uses **area-normalised annual rates** so small and large
areas weigh equally and core and buffer are directly comparable:

```
rate(series, scope, year) = 100 × area_ha(series) / area_ha(scope)   [% of area / yr]
```

computed for `mb_defor_primary`, `mb_fire_scar`, `mb_secondary_growth` and
`hansen_loss`, with each scope normalised by *its own* area.

### 6.2 Political and policy context (the join tables)

- **`political_context_brazil.py`** — federal presidents (1985–2025) and all 26
  states + DF governors, each hand-coded on an ideology scale
  (−1 = Left, 0 = Centre/patronage, 1 = Centre-Right, 2 = Right/pro-agribusiness),
  reflecting the administration's environmental/indigenous-enforcement posture
  rather than party label. Derived per (state, year): `alignment`,
  `combined_pressure` (= president + governor ideology, −2…+2), and change flags
  (`fed_change`, `state_change`, and a two-year `change_window`). Sources: TSE,
  Wikipedia, DIAP, news archives.
- **`policy_context_brazil.py`** — annual ordinal scores (1985–2024) for
  `forest_law_strength` (0–3), `indigenous_rights_score` (0–3),
  `enforcement_capacity` (0–3), `amazon_plan_phase` (PPCDAm 0–4),
  `amazon_fund_active` (0/1), `car_registry_stage` (0–3),
  `demarcation_posture` (−1/0/+1), `licensing_strictness` (0–3), plus a
  point-in-time `LEGAL_MILESTONES` table (the simplified forest-law timeline).
  Sources include Nature Sci. Rep. doi:10.1038/s41598-024-52180-7, HRW, CPI/PUC-
  Rio, Mongabay, Amazon Watch/APIB.

The **ideological posture** buckets used in Report 4 are derived from
`combined_pressure`: ≤ −0.5 → *Both progressive*; ≥ +1.0 → *Both conservative*;
otherwise *Opposed / mixed*.

### 6.3 The three hypotheses (Report 4)

- **H1 — Government changes.** Compares mean deforestation, fire and regrowth
  rates in *stable* years vs *federal-change*, *state-change* and
  *change-window* (change year + next) conditions.
- **H2 — Ideological posture.** Rates by combined federal+state posture and along
  the continuous `combined_pressure` gradient. The data support a *directional*
  reading: conservative alignment is destructive; both-progressive alignment is
  the most protective — alignment *per se* is not the driver.
- **H2b — Where governance bites (scope split).** Each contrast is split into
  core vs buffer and the buffer-÷-core amplification is tabulated. The recurring
  finding: **deforestation** is absorbed by the buffer (buffer swings
  1.4–1.7× the core — the boundary works dynamically), while **fire** is the
  exception — the protected core burns *more* and is the more governance-reactive
  scope (buffer ÷ core ≈ 0.6), because buffers are already converted and retain
  little native fuel.
- **H3 — Policy recognition & robustness.** Two readings: *over time* (national
  enforcement/demarcation scores by federal administration) and
  *cross-sectionally* (recognition tier — IL *Regularizada* vs pre-
  regularisation; UC *Proteção Integral* vs *Uso Sustentável* and by sphere).
  The temporal signal within already-protected areas is **confounded** (primary
  clearing is front-loaded / legacy-frontier), so the **clean policy signal is
  cross-sectional**, not temporal — this is stated explicitly in the report.

### 6.4 Regional stratification

Each area is mapped to a macro-region via its primary UF (`REGIONS`, Norte ≈ deep
Amazon → Sul). The regional table reports core/buffer deforestation and fire per
region and the core's deforestation response to conservative posture
(`conservative − progressive`, the governance-sensitivity gap). The report reads
the *actual* leaders from the data rather than assuming the deep Amazon leads —
and finds peripheral clearing and governance sensitivity peak **outside** the
deep Amazon (Cerrado/frontier and Nordeste).

---

## 7. Cross-checks and known data artifacts

- **Rasterisation overflow** (~0.4 pp) at polygon boundaries can push a fully-
  forested area above 100 % (documented in MapBiomas technical notes); it does
  not affect class-*difference* statistics, which is what the chapters report.
- **`mb_secondary_growth` = 0 in 2023–24** is a coverage edge of the MapBiomas
  regrowth product, not a real collapse — flagged wherever regrowth is discussed.
- **MapBiomas vs Hansen disagreement** is reported, not reconciled (§2.1).
- **Front-loaded primary deforestation** confounds any temporal policy
  correlation *inside* protected areas; the analysis leans on the cross-sectional
  recognition signal instead.

---

## 8. Reproducibility and caveats

**Run order** (same `--out` for both):

```bash
# 1) aggregate the raw batch export folders
python utils/batch_report_aggregator.py \
    /path/IND_BATCH:"Indigenous Lands" \
    /path/UC_BATCH:"Conservation Units" \
    --out /path/report

# 2) governance/policy layer (imports the aggregator; refreshes its README)
python utils/governance_policy_report.py \
    /path/IND_BATCH:"Indigenous Lands" \
    /path/UC_BATCH:"Conservation Units" \
    --out /path/report
```

Run with the repository virtualenv
(`/home/leandromb/google_eengine/yvynation/.venv/bin/python`). The governance
script additionally needs `geopandas` and the two GeoPackages, and loads the
reflex-app context modules by file path.

**Caveats to carry into the paper:**

- Observational associations across 1985–2024; deforestation drivers (commodity
  prices, roads, biome) are **not** controlled for — the buffer is the only
  counterfactual.
- The sample is **purposive** (comparable size, national coverage, spatially
  separated — §3.2), not a probability sample; inference is to this frame.
- State ideology is joined on each area's **primary** UF; multi-state areas use
  the first listed.
- MapBiomas deforestation/fire series begin ~1987; Hansen loss in 2001. Change-
  and posture-windows inherit those coverage limits.
- Recognition tiers are coarse given ~45 areas per system; per-region samples
  (9–27 areas) are indicative, not conclusive.

---

## 9. Relationship to the case studies

The batch tooling and the four intensive case studies are two views of the same
pipeline. The case studies (Krenak, Bacurizinho, Kayapó, Betânia — spanning the
coastal Atlantic Forest → deep western Amazon gradient) narrate the
policy-to-pixel signature area by area, anchoring specific Hansen loss spikes and
MapBiomas transitions to dated legal and non-policy events (e.g. the 2012 Forest
Code revision, the Fundão dam collapse, Belo Monte, the 2025 "Devastation Bill",
the 2026 STF mining ruling) via the master instrument/event index. The batch
reports generalise those single-area findings across ~90 protected areas, and the
protection gap, the deforestation/fire scope split, and the cross-sectional
recognition signal are the quantitative backbone the synthesis chapter
(Ch. 11) rests on.
