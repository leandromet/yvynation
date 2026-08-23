# Methodology — the Yvynation batch pipeline and analytical framework

This note delineates *how* the four-territory results were produced, so the
chapter narratives can be read against a reproducible method. Everything here is
driven by the batch module `yvynation/pages/batch_processing.py` and its backend
handlers in `state/`, running against Google Earth Engine (EE).

---

## 1. What the framework is trying to measure

The core empirical claim is not simply *"forest cover is higher inside an
Indigenous Territory (TI) than outside"* — that could be self-selection, since
remote lands were often demarcated *because* they were remote. The claim is
that the **rate of land-cover change inside the boundary differs systematically
from the rate in an adjacent, unprotected strip** that shares the same biome,
road network, commodity market, and climate. The 10 km exclusive buffer is
constructed to be that counterfactual (see §5).

A second claim is about **policy lag**: the sharpest inflection in a land-cover
trend does not coincide with the year of the policy event that (hypothetically)
caused it. The framework treats that lag as finite, measurable, and causally
informative — and, as it turns out, of three distinct kinds (see
[SYNTHESIS.md](SYNTHESIS.md) §3).

---

## 2. Data sources

| Source | Product | Role |
|---|---|---|
| **MapBiomas** | Collection 9 (1985–2023) for the April run; Collection 10 (1985–2024) for the May run | Annual land-cover *class* areas and class-to-class transitions |
| **Hansen GFC** | Global Forest Change (v1.11 for April; v1.12 / `2024_v1_12` for May) | Tree-cover 2000 baseline, annual canopy **loss** (2001–), gain (2000–2012) |
| **Hansen / GLAD** | GLCLU 2020 | A second, independent per-class forest-cover snapshot |
| **FUNAI** | Indigenous Lands boundaries (657 territories) | Territory geometry source |
| **CNUC** | Conservation Units (3,247 units) | Alternative geometry source (same pipeline) |

Using **two independent forest measures** (MapBiomas class change vs Hansen
canopy loss) is deliberate: the gap between them is part of the validation
story, not noise. The clearest example is Kayapó, where MapBiomas reports −1.9%
Forest Formation over 1985–2023 but Hansen reports a 14.2% canopy-loss footprint
(§9.12.2) — the divergence flags fire/degradation that MapBiomas' persistence
logic re-absorbs into the same class.

---

## 3. The pipeline (what a batch run does)

A run is configured entirely in the left/right panels of `batch_processing.py`
and then executed unattended by `AppState.run_batch_processing`. For each
selected territory (and, optionally, its buffer) the following analyses can be
switched on:

| Analysis toggle | Output |
|---|---|
| 🌿 MapBiomas single-year | Class composition + distribution for one year |
| 📊 Year-over-year comparison | Δha / Δ% / gains–losses between `year` and `year2` |
| 🟦 Class-transition treemaps | Faceted treemap per class (small classes → "Others") |
| 🌲 Hansen GLAD forest cover | GLCLU 2020 per-class breakdown |
| 🪓 Hansen GFC (loss / gain) | Tree-cover 2000, annual loss series, gain |
| 🗺️ PNG maps & charts | Satellite + MapBiomas y1/y2 raster PNGs |
| 🌀 Multiple time-window | Sankey + Sunburst + treemaps across N stages |
| 📈 Deforestation timeline | Hansen + MapBiomas + fire, with policy/political context bands |

Extra MapBiomas auxiliary rasters (rendered for `year2`) can be added on top of
the PNG maps: **deforestation & secondary vegetation**, **annual burned area**,
**fire frequency (full 1985–2024 period)**, **year of last fire**, **mining
substances**, and **agriculture cycles**. These are what produced the fire-scar
and mining overlays discussed in the Kayapó chapter (§9.6, §9.12).

The multi-time-window mode mimics the original offline Python code: either a
**constant step** (1, 2, 4, 5 or 8 years, with 1985→2024 forced as endpoints) or
a **custom** list of 3–4 comma-separated years (e.g. `1985, 2004, 2012, 2023` to
align stages with policy events). Each stage gets its own Sankey/Sunburst so a
single figure can carry the whole 40-year trajectory.

Expected cost is **2–10 minutes per territory** depending on toggles; the tab
runs in the background and can be stopped after the current territory.

---

## 4. Output artefacts (what a run produces)

Everything is packaged into one self-describing ZIP. Per territory the folder
contains:

```
metadata.json          territory id, source, year pair, run timestamp, analysis_type
README.txt             human-readable analysis summary
figures/               11 interactive HTML figures (Plotly)
territory/<name>/       per-class CSVs + boundary.geojson + transitions.json
```

The **11 figures** (identical filenames across territories, so cross-case
comparison is trivial):

```
mapbiomas_composition.html      class composition, latest year
mapbiomas_distribution.html     class-area bar chart, latest year
change_percentage.html          class-by-class % change y1→y2
gains_losses.html               diverging bar of net gains/losses
transitions_matrix.html         source-class × target-class heatmap
transitions_sankey.html         flow diagram of the same transitions   ★ headline figure
transitions_sunburst.html       hierarchical transition view
hansen_glad_distribution.html   GLAD GLCLU 2020 per-class breakdown
hansen_gfc_summary.html         Tree Cover 2000 + Loss + Gain panel
hansen_gfc_loss_by_year.html    annual canopy-loss series             ★ policy-lag figure
hansen_balance.html             net forest balance
```

The **CSVs** are the ground truth the chapters quote. Example, the Kayapó
`comparison_1985_vs_2023.csv` carries one row per class:

```
Class_ID, Area_Year1, Class_Name, Area_Year2, Change_ha, Change_km2, Change_pct, Abs_Change
3,  2,875,570, Forest Formation, 2,821,132, −54,438, ..., −1.89%, ...
15,    2,105,  Pasture,             30,597, +28,492, ..., +1352.58%, ...
30,      951,  Mining,              13,825, +12,874, ..., +1352.56%, ...
```

`hansen_gfc_summary.csv` gives the three headline Hansen numbers (Tree Cover
2000, Forest Loss %, Forest Gain %); `hansen_gfc_loss_by_year.csv` gives the
annual series; `transitions.json` gives the normalised class→class flow weights
behind the Sankey.

A post-processing step (`_build_bundle.py`, `_export_pngs.py` in the results
folder) renders all HTML figures to a paginated PDF and to 2800×1800 PNGs, both
flat and per-territory, for dropping into the thesis document.

---

## 5. The buffer as counterfactual

When the buffer toggle is on, the same analysis runs on an **external ring**
(default 10 km) around each territory, written to
`buffer/{territory}_Buffer_{km}km/`. The ring is *not* clipped to remove other
protected areas inside it, so the comparison is deliberately
territory-vs-whatever-is-actually-there (unprotected land *and* adjacent
protected land).

The logic: where the same highway runs along the boundary, interior and buffer
pixels face the same accessibility; where the same soy frontier expands, both
face the same commodity price; where the same drought reduces fire resistance,
both face the same climate shock. The **only systematic difference is legal
status** and the institutional response it triggers. Buffer results are
summarised in [`multi_window.md`](multi_window.md) and discussed in
[SYNTHESIS.md](SYNTHESIS.md) §4.

---

## 6. Quadrant clipping for very large areas

Kayapó (~3.3 M ha reported extent, part of an 11 M ha contiguous block) cannot
be processed as one EE call without timing out. The batch clips any geometry
larger than **1 million hectares into four quadrants** (NW, NE, SE, SW),
processed and stored separately. This was a computational necessity that turned
into an analytical asset: the quadrants isolate pressure fronts — the **eastern**
quadrants border rural properties (pasture, agriculture, mining), while the
**western** quadrants adjoin other protected areas and harder-to-reach zones.
The NE quadrant is the mining hot-spot; the SW is nearly stationary (see
`multi_window.md` and RESULTS §Kayapó).

---

## 7. The two data epochs (why numbers differ)

| Run | MapBiomas | Hansen | End year | Where reported |
|---|---|---|---|---|
| **April 2026** (per-territory folders) | Collection 9 | GFC to 2024 | 2023 | `RESULTS.md`, chapters §7.10–§10.10 |
| **May 2026** (batch + buffer + multi-window) | Collection 10 | GFC to 2025 | 2024 | `multi_window.md`, report batch section |

The report is explicit (§11.1) that Table 11.1 and the chapter figures use
slightly different inputs. The gap is *informative*: it isolates which findings
depend on the choice of headline metric (MapBiomas class change vs Hansen canopy
loss) and which survive both. Collection 11 (1985–2025, expected August 2026)
will trigger a reconciliation pass.

### The Hansen-2024 caveat

The April Kayapó export reported **305,250 ha of 2024 loss** — roughly two-thirds
of the entire 2001–2023 cumulative loss in a single year (see
`hansen_gfc_loss_by_year.csv`). This is implausible as canopy *removal* and
reflects a **2024 wildfire scar** captured by the `2024_v1_12` asset; MapBiomas
Collection 10 independently reports >300,000 ha of post-wildfire canopy loss in
the same window. The figure is reported as-is but flagged, and it is the main
reason the project moved to Collection 10 and will move to Collection 11.

---

## 8. Reproducing any of this

Every chart and table in the report can be regenerated from the app for **any**
FUNAI territory or (with minor changes) CNUC conservation unit:

1. Open the batch page, pick source type, search and tick territories.
2. Set MapBiomas `year`/`year2` and the Hansen GLAD reference year.
3. Enable the analyses you want (+ auxiliary rasters, + multi-window, + timeline).
4. Optionally enable the 10 km buffer.
5. Start, wait, download the ZIP.

The individual-territory module offers the same analysis with an interactive
map; the batch module is the reproducible, headless path for a known set of
areas.
