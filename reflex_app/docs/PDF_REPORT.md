# PDF report — laid-out territory reports (single area and batch)

A **laid-out report** for one analysed Indigenous Land (TI) or Conservation Unit (UC), with its
buffer when one was analysed. It contains identification and metadata first, then maps,
charts and tables, each with a short explanatory paragraph. It is offered as **PDF** and
**HTML** from a new *Report* tab of the export panel. In a batch run it is written as **one
PDF per area** into the run folder.

Planned on **2026-09-24**. It is planned together with the same feature in Naturametrics
(`/server/naturametrics/doc/14-pdf-report.md`, the **canonical copy** of the shared kit) and
Camposcope (`/server/camposcope/doc/13-pdf-report.md`). The three reports share one layout,
one kit and one set of image rules (§2). Related:
[EXPORT_DOWNLOADS.md](EXPORT_DOWNLOADS.md) (the download route) and
[BATCH_CONCURRENCY.md](BATCH_CONCURRENCY.md) (render lanes).

---

## 1. Purpose and scope

The export panel (`yvynation/components/export_panel.py`, mounted in
`pages/index.py:907`) offers two tabs today:

- **"Data & Figures"**, a ZIP (`state/_export.py::export_analysis_zip`, L260).
- **"PDF Maps"**, matplotlib maps (`export_pdf_maps`, L293).

Both are hard-coded in English. Neither is a document someone can read from front to back.
The CSVs and figures in the ZIP are for reprocessing, and the map PDFs are single images built
on Google/Esri basemap tiles (`utils/map_export_service.py:36-230`). **Those tile images can't
be redistributed, so the report never uses them** (R5).

**Scope of the first release:**

| Case | v1 |
| --- | --- |
| **Single area**: the active result (`active_result_key`), a TI or a UC (`territory_type`), with its buffer if analysed | ✅ PDF and HTML |
| **Batch**: one `territory/{slug}/{slug}_report.pdf` per area, including quadrant-split areas over 1 M ha (`SPLIT_THRESHOLD_HA`, `state/_batch.py:58`) | ✅ PDF only |
| Drawn polygons (`drawn_features`) | ⏸ No metadata record to open the report with |
| A run-level summary PDF (index of all areas) | ⏸ |

**Languages:** en, pt, es, fr, following the interface (`AppState.tr`, English as reference
and fallback). A batch uses the interface language at the moment the batch starts.

**Existing pitfalls this work must handle first:**

1. **Stale per-area results.** `switch_result` (`state/_analysis.py:66-121`) restores only the
   main result, comparison, timeline, multi-window and zoom. It does not restore:
   - GLAD, GFC and the buffer results;
   - `territory_result*`, `territory_name` and `territory_geojson_features`.

   After switching areas, those still belong to the last area analysed, so a report would mix
   two areas. `download_all_results` (`_export.py:436-441`) already does.

   **Fixed at the root (2026-09-24).**
   - `state/_analysis.py::AREA_RESULT_FIELDS` lists the per-area flat fields: MapBiomas, the
     territory years 1 and 2 and their transitions, GLAD, GFC, and every `buffer_*` result.
     `AREA_LABEL_FIELDS` lists the name, years and source.
   - Each handler that writes them calls `_save_area_fields(key)` right afterwards, with the key
     of the area it analysed (`territory::{selected_territory}` or `geometry::{idx}`). This saves
     a deep copy into that area's bundle.
   - `switch_result` restores them, or gives `None` for anything that area never ran.
   - `set_selected_territory` now clears all of them (`_clear_area_fields`), not just
     `territory_result*`.
   - The territory comparison used to *replace* its bundle, which also discarded timeline and
     multi-window payloads. It now merges, like `_store_result` does.

   This also fixes *Download all*, which loops over `switch_result`, and the report needs no
   owner-key guard. Tests: `tests/test_area_switch.py`.
2. **Don't copy `export_analysis_zip`'s shape.** It renders synchronously on the event loop
   (`_export.py:260-289`). The report handler is a **background** event.
3. **Kaleido drift.** The local `.venv` has kaleido 0.2.1, while `requirements.txt` pins 1.3.0.
   The v0 dispatch in `export_service.py` still works, but sync the venv before verifying
   (see the kaleido notes in `export_service.py` L671-803).

---

## 2. The shared report kit (same text in all three apps)

> **This section is copied word for word** into Naturametrics `doc/14-pdf-report.md`,
> Camposcope `doc/13-pdf-report.md` and Yvynation `reflex_app/docs/PDF_REPORT.md`. Edit it in
> Naturametrics only, then copy it again. Everything outside §2 is specific to each app.

### 2.1 What the kit is, and why it is copied into each app

Naturametrics, Camposcope and Yvynation are three umaterra apps, and all three need the same
kind of document. That is a readable report with metadata first, then maps, charts and
tables, joined by short paragraphs. If each app built its own, they would drift apart within a
month. So the page model, the renderers, the map framing and the image rules live in one
package, **`report_kit`**, which knows nothing about any app.

| Copy | Path |
| --- | --- |
| **Canonical** | `/server/naturametrics/naturametrics/report_kit/` |
| Vendored | `/server/camposcope/camposcope/report_kit/` |
| Vendored | `/home/leandromb/google_eengine/yvynation/reflex_app/yvynation/report_kit/` |

`scripts/sync_report_kit.py` in Naturametrics copies the canonical tree into the other two
apps and rewrites `report_kit/MANIFEST`, which holds the sha256 of every file.
`tests/test_report_kit_manifest.py` in each app recomputes the hashes and fails on any
difference. **A fix made in a vendored copy would be lost at the next sync, so kit fixes go into
the canonical copy only.** This is the same copy-with-provenance pattern already used for
`ods.py`, `provenance.py` and `tiles.py`. A shared pip package was rejected: it would add a
private package source to three Cloud Build pipelines for about 1 500 lines of code.

**Rules for kit code:**

- Relative imports only.
- Never import the host app or `reflex`, and never import `ee` at module level. `ee` is
  imported lazily inside `maps.fetch_thumbnail`.
- Must run on **Python 3.11** (Yvynation's image). No nested same-quote f-strings and no
  `type X = …` aliases.
- Dependencies: `reportlab>=4.2,<5` and `pillow>=10`. pandas is imported lazily, only by
  `Table.from_frame`.

### 2.2 Decisions shared by the three apps (agreed 2026-09-24)

| # | Decision | Chosen | Rejected, and why |
| --- | --- | --- | --- |
| R1 | PDF engine | **reportlab**: a pure wheel with no system packages, and native tables that split across pages | Chromium printing: Naturametrics and Camposcope deliberately carry no Chromium. WeasyPrint: needs pango/cairo in the image and cannot run Plotly. matplotlib `PdfPages`: poor text layout |
| R2 | Chart images, Naturametrics and Camposcope | **Rendered by the browser**: `Plotly.toImage` of figure JSON sent by the server (§2.7) | kaleido + Chromium: about 300 MB of image, the most fragile part of Yvynation's deploy, and it reverses Naturametrics `doc/11-exports.md` §4. matplotlib re-draws: duplicate chart code, and the charts would no longer match the screen |
| R3 | Chart images, Yvynation | **Its existing server-side kaleido path** (`export_service._plotly_to_png_bytes`) | Browser capture: batch runs have no browser |
| R4 | HTML and PDF | **One content model, two renderers** (`render_pdf`, `render_html`), so the two formats cannot disagree | Two independent generators, as today, would drift |
| R5 | Map backdrop | **Earth Engine only**, via `getThumbURL`, using the same palettes as the screen | Google or Esri tiles: redistributing them inside a PDF is a terms-of-service problem |
| R6 | Explanatory text | **Deterministic templates for each language**, fed from the frames the charts already use | An LLM: not reproducible, and it could produce claims the data does not support |
| R7 | Sharing the code | **Vendored copies checked against a manifest** (§2.1) | A private pip package |
| R9 | Image resolution | **Screen quality, sized to the page: 150 dpi at the slot's size** (§2.5) | 300 dpi print: files 4× larger for a document read on screen |

(R8 is specific to Naturametrics' scope and is in its own doc.)

### 2.3 Content model: `report_kit/model.py`

Each app builds a `Report`, and the kit renders it. The model uses plain dataclasses and
contains no Reflex or Earth Engine objects.

```python
Slot = Literal["full", "half"]            # 170 mm or 82 mm wide (style.py)

@dataclass
class Brand:        accent: str; app_line: str        # e.g. "#2f7d4f", "umaterra · Camposcope"
@dataclass
class ReportMeta:   app: str; app_url: str; app_version: str; title: str; subject: str
                    lang: str                          # "pt" | "en" | "es" | "fr"
                    generated_at: datetime             # tz-aware UTC
                    brand: Brand
@dataclass
class Report:       meta: ReportMeta; sections: list[Section]
@dataclass
class Section:      title: str; blocks: list[Block]; key: str = ""   # key feeds ContentsList

# Blocks
Paragraph(text: str, lead: bool = False)             # **bold** / *italic* only; the kit escapes all else
KeyValues(rows: list[tuple[str, str]], caption: str = "")
Figure(key: str, caption: str, slot: Slot = "full", aspect: float = 0.56,
       fig_json: dict | None = None,                 # HTML: interactive Plotly
       png: bytes | None = None,                      # PDF: the rasterised chart
       unavailable_reason: str = "")                  # neither → a "figure unavailable" placeholder
MapFigure(composition: MapComposition, caption: str, slot: Slot = "full")
LocatorMap(geometry: dict, label: str, slot: Slot = "half")   # GeoJSON of the object
Table(columns: list[str], rows: list[list], caption: str,
      align: list[str] | None = None,                 # "l" / "r" per column
      max_rows: int = 40, note: str = "",             # overflow → "n more rows in the appendix/ODS"
      decimals: list[int | None] | None = None)       # numeric cells are locale-formatted by the kit
Table.from_frame(df, headers: dict[str, str], caption, **kw)
Callout(text: str, kind: Literal["disclosure", "note", "warning"] = "note", title: str = "")
ContentsList(items: list[ContentsItem])
ContentsItem(title: str, status: Literal["included", "not_run", "unavailable", "excluded"],
             reason: str = "")
ProvenanceTable(rows: list[dict])                     # each app's Provenance.to_dict()
Citation(text: str, sources: list[str], attributions: list[str])
SideBySide(left: Block, right: Block)                 # two half-slot blocks on one row
PageBreak()
```

Figures, maps and locators share one "Figure n" counter, and tables have their own. Captions
are prefixed by the kit ("Figura 3 —", "Table 2 —"). `ProvenanceTable` shows `name`,
`dataset_id`, `bands`, `scale_m`, `reducer`, `degraded` and `computed_at`, with `notes`
underneath. A degraded row is always shown, never hidden.

### 2.4 The same outline in every report

1. **Title block.** App line, report title, subject, the time it was generated (UTC and local
   time of the requested language), app version and URL.
2. *(Camposcope only)* **Disclosure callout.**
3. **Identification.** `KeyValues` of the object's metadata, `SideBySide` with the `LocatorMap`.
4. **About this report.** A `ContentsList`: every section the app can produce, marked included,
   not run, unavailable or excluded (by a checkbox), with the reason. Then one paragraph giving
   the period, the zones or buffers, and how to read the document: *data, not a verdict*.
5. **Maps.**
6. **Analysis sections**, one per dataset, in each app's on-screen order. Each has a one-sentence
   intro (what the dataset is), the figure, a summary table, and a *reading* paragraph built
   from the numbers.
7. **Methods and provenance.** `ProvenanceTable`.
8. **Sources, citation and attributions.** In the report's language, including "Contains
   modified Copernicus Sentinel data {year}" and "Landsat: USGS/NASA" whenever those backdrops
   appear.
9. **Appendix** (optional). Full tables. Always off in batch runs.

**Page, `style.py`.**

- A4 portrait, margins 20 mm on both sides and 18 mm at top and bottom, text width **170 mm**.
- Noto Sans (OFL, in `report_kit/fonts/`): body 9.5 pt on 13.5 pt leading, H1 16 pt, H2 12.5 pt,
  captions 8.5 pt.
- The header band on pages 2 onwards carries the app line in the accent colour, with the subject
  on the right.
- Footer: `umaterra · <App> · <url> — página x de y — gerado em <date>`, in the report's
  language.
- Tables: `LongTable(repeatRows=1)`, zebra rows, numbers right-aligned and formatted for the
  locale.

Noto Sans covers Guarani and Portuguese diacritics (ỹ, g̃). reportlab does no text shaping, so
combining marks can sit slightly off. This is accepted.

The system Noto Sans has **no − (U+2212), →, ≥, ≤ or ↳**, and reportlab drops a missing glyph
silently: "−3,2" printed as "3,2". Since kit v0.1.1, `fonts/NotoSansMath-Subset.ttf` (35 KB,
arrows, math operators and the true minus) is registered as a fallback. `pdf._glyph_fallback`
wraps any character the main font lacks in that font, and canvas strings (header, footer, scale
bar) get ASCII stand-ins. Apps may use these characters freely.

### 2.5 Images: screen quality, sized to the page (R9)

The reports are read on screens. Every raster is produced **for the slot it fills, at 150 dpi**,
never at print resolution and never larger than its slot.

| Slot | Width | Pixels at 150 dpi | Chart layout in CSS px (96 dpi) | Plotly/kaleido `scale` |
| --- | --- | --- | --- | --- |
| `full` | 170 mm | ≈ 1004 | 643 × (643·aspect) | 150/96 = **1.5625** |
| `half` | 82 mm | ≈ 484 | 310 × (310·aspect) | 1.5625 |
| full map | 170 × 110 mm | ≈ 1004 × 650 | — | — |

- **Charts are laid out at their true on-page CSS size and rasterised at `scale = 150/96`.**
  Plotly's pixel font sizes then print at about their nominal point size next to the 9.5 pt body
  text. A chart laid out 1000 px wide and shrunk to 170 mm would print its 12 px labels at about
  6 pt.
- `images.chart_opts(slot, aspect) -> {"width", "height", "scale"}` gives the numbers above to
  both chart paths (browser and kaleido).
- `images.prepare_figure(fig_json, slot, aspect) -> dict` works on a copy of the figure dict and
  needs no plotly import. It:
  - sets width and height;
  - sets a white paper and plot background (on-screen charts are transparent);
  - raises fonts to at least 10 px;
  - moves legends with more than six entries below the plot;
  - removes `updatemenus` and `sliders`.
- `images.fit_image(data, slot_mm, kind)`:
  - reads the PNG IHDR or JPEG SOF header **before** decoding, and refuses anything over 40 MP;
  - downsamples to the slot's size at 150 dpi;
  - re-encodes imagery (`kind="photo"`) as **JPEG q≈80**, and class rasters and charts
    (`kind="flat"`) as **PNG**, palette-quantised when there are 256 colours or fewer.
  - Both renderers call it, so an oversized input can never inflate the file.
- **Budget:** a synthetic report with 8 figures and 4 maps must stay **at or under 3 MB**, and a
  kit test asserts it.

### 2.6 Maps: `report_kit/maps.py` and `locator.py`

- **`MapView.from_geojson(geoms, slot, margin=0.08)`.** Computes the bounding box in EPSG:3857,
  padded and stretched to the slot's aspect ratio, so the fetched raster fills the frame exactly.
  It exposes `bbox_lonlat`, `bbox_3857`, `px` and `metres_per_px`.
- **`fetch_thumbnail(image, view, fmt, *, cache_key)`** is the kit's **only network call**. It
  calls `image.getThumbURL({"region": ee.Geometry.Rectangle(view.bbox_lonlat, None, False),
  "dimensions": f"{view.px_w}x{view.px_h}", "crs": "EPSG:3857", "format": fmt})` and makes an
  HTTP GET (`urllib`, 60 s timeout). Both dimensions are passed, so the raster is exactly the
  view's size. Results are cached in the process by `(cache_key, bbox rounded to 1e-5, px, fmt)`.
  - The caller must have initialised Earth Engine (its own `get_ee()`).
  - The caller must run it in an executor, never on the event loop.
  - In Yvynation it runs **before** entering a render lane.
- **`imagery_backdrop(view, year) -> ee.Image | None`** picks the backdrop by map extent:

| Longest side of the view | Backdrop | Visualisation |
| --- | --- | --- |
| ≤ 50 km (property, rings, buffers) | `COPERNICUS/S2_SR_HARMONIZED` masked with `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED` `cs ≥ 0.60`, median of the dry season (Jun–Sep) of `year`, falling back to the full year | B4/B3/B2, 0–3000, JPEG |
| 50–300 km (territories) | `LANDSAT/COMPOSITES/C02/T1_L2_ANNUAL`, image for `year` | red/green/blue, 0–0.3, gamma 1.2, JPEG |
| > 300 km | none: class layers and the locator only | — |

- **Class layers** (MapBiomas, Hansen, change masks and so on) are **provided by the app** as an
  already-visualised `ee.Image`, built by the *same* `<layer>_image()` function its tile layer
  uses (see §6 of each app doc). The PDF and the screen then share their pixels and palettes.
  They are fetched as PNG with transparency.
- **`MapComposition`** contains:
  - `view`;
  - `backdrop` (JPEG bytes or `None`);
  - `overlays` (PNG bytes, bottom to top);
  - `vectors`: `VectorLayer(geojson, stroke, width_pt, dash=None, fill=None, label="")`;
  - `clip_to` (GeoJSON that masks the overlays to the object's shape, or `None`);
  - `legend`: `LegendItem(color, label, kind="fill"|"line")`;
  - `attribution`.

  **Outlines and rings are drawn as vectors by the renderer, not painted in Earth Engine.** They
  stay sharp at any zoom, no geometry is sent to Earth Engine, and the thumbnail cache works per
  bounding box.
- **Frame furniture**, drawn by both renderers:
  - a thin frame;
  - a scale bar with a round length of about ⅕ of the width, corrected by cos(latitude);
  - a north arrow;
  - the legend **below** the map, never on top of it;
  - the attribution in 7 pt.

  The PDF renderer uses a reportlab `Drawing`. The HTML renderer uses the `<img>` layers plus
  inline SVG.
- **`LocatorMap`.** Draws Brazil's states from the kit's `data/br_uf.simplified.geojson`
  (copied from Camposcope `data/uf_boundaries.simplified.geojson`, 99 KB) as vectors. It
  highlights the object's state or states and marks the object (a point, or its bounding box
  when larger than 2 % of the map).

### 2.7 Chart capture in the browser (Naturametrics and Camposcope)

The kit provides the JavaScript and the job store. Each app writes the three handlers. The
flow was verified against Reflex 0.8.27: `state.js` L354–379 awaits a Promise returned by
`call_script`, and `reflex/utils/format.py:588` `format_queue_events` builds callbacks.

```text
[PDF button] ─► start_report("pdf")                 (normal, non-background handler: snapshot + job)
                 ├─ figs = {key: prepare_figure(fig_json, slot, aspect)}   ← same charts.* builders as the screen
                 ├─ job = JobStore.create(client_token, expected=figs.keys())
                 └─ return [rx.call_script(build_capture_script(figs, callbacks, opts)),   # no callback
                            State.build_report(job.id, "pdf")]                          # background
browser:  await window.Plotly (≤ 8 s) → for each key: try { d = await Plotly.toImage(fig, opts) }
          catch { d = "" }; if d.length > 900 000 retry at scale 1; cb[key](d)   ← one socket event per chart
          ─► receive_report_chart(job_id, key, data)  → JobStore.put(...)   (validates, stores bytes)
build_report(job_id, fmt)  [background]
   ├─ starts the EE thumbnails in an executor immediately (they overlap the browser's rendering)
   ├─ polls JobStore every 250 ms until every key is resolved or 15 s + 2 s × n_figures elapse
   ├─ a missing or failed key → Figure(png=None, unavailable_reason=…)   (never hangs)
   └─ builds the Report → render_pdf → rx.download(data=…, filename=…, mime_type="application/pdf")
```

- **Callbacks** are created in the app, because the kit cannot import Reflex. For each key:
  `str(format_queue_events(State.receive_report_chart(job_id, key), args_spec=lambda d: [d]))`.
  They are passed to `build_capture_script(figs, callbacks, opts)` as a `{key: js_source}`
  mapping.
- **One script, not N `call_script`s.** Each `call_script` holds the page's event queue while its
  Promise is pending, and a rejected Promise never fires its callback. One script with
  per-chart callbacks avoids both problems.
- **`JobStore`** (`browser_capture.STORE`) is a module-level dict with a lock and a 10-minute
  TTL, pruned on every access. Its API is `create(token, keys) -> job_id`,
  `put(job_id, key, data_url, token) -> bool`, `progress(job_id) -> (got, expected)`, `done()`,
  and `take(job_id) -> ({key: png | None}, {key: error})`. `wait_deadline_s(n)` gives the build
  task's timeout.
  It holds images outside Reflex state, because even `_backend` vars are pickled on every event.
  `put()` rejects:
  - a client token that differs from the job's;
  - data without the `data:image/png;base64,` prefix;
  - anything over 3 MB decoded;
  - a PNG whose IHDR exceeds 4000 × 4000.

  An empty string means the browser failed, and is recorded as such.
- **Incoming socket limit.** Reflex caps incoming messages at `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE`
  (default 1 000 000 bytes). Beyond it, engine.io drops the connection *silently*. R9-sized charts
  are 50–200 KB, and the Dockerfile sets `REFLEX_SOCKET_MAX_HTTP_BUFFER_SIZE=4000000` as headroom.
- **`window.Plotly`** exists only after the first `rx.plotly` has mounted, because its bundle loads
  lazily. The report block mounts a hidden 1×1 `rx.plotly` so that the bundle is present, and the
  8 s wait plus the placeholder cover everything else.
- **The HTML format needs no capture.** It embeds `fig_json` directly, so `start_report("html")`
  goes straight to `build_report`.
- **Background-handler rules still apply:** no `type(self)` in background tasks, and every state
  write inside `async with self`. Wrap the snapshot in the app's `plain()`.

### 2.8 Explanatory text

- Each app has `services/report_text.py`: pure functions `(frames…, lang) -> str` returning
  one to three sentences. They are held as one template dict per language, with the app's
  reference language as fallback. `report_kit/text.py` formats numbers, areas, percentages
  and dates for pt, en, es and fr. The kit's own fixed strings are in those four languages too.
- **Describe, never judge.**
  - The sentences state quantities, changes over the period, and comparisons with the rings or
    the buffer.
  - No causal claims ("because of…").
  - No legal, compliance or valuation vocabulary.
  - Camposcope enforces this with a test (its doc, §9). The other two follow it by review.
- Every number in a sentence comes from the same frame the chart or table in that section was
  drawn from. **Nothing is recomputed at export.**

### 2.9 The export UI block: same anatomy in the three apps

```text
┌ Relatório  ·  Report ───────────────────────────────────────────┐
│ A laid-out document: identification, maps, charts and tables    │
│ with short explanations. Language = the interface's.            │
│ [✓] Mapas   [✓] Gráficos   [✓] Tabelas-resumo   [ ] Apêndice    │
│ [ ] GBIF  (where the app has it)                                │
│ ( PDF )  primary          ( HTML )  secondary                   │
│ Gráficos 3/7 · Mapas 2/3 · Montando PDF…      ← stage line      │
│ ⓘ reason when disabled (no result yet / wrong mode / running)   │
└──────────────────────────────────────────────────────────────────┘
```

**Common names:**

- State vars: `exp_report_maps`, `exp_report_figures`, `exp_report_tables`,
  `exp_report_appendix` (Naturametrics and Camposcope already have the figures and tables
  ones), plus `report_busy`, `report_stage` and `report_error`.
- Handlers: `toggle_exp_report_*` and `start_report(fmt: str)`, where `fmt` is a string because
  of the Reflex arg-type rule.
- Translation keys use the prefix `report_`.

**File names:**

- `<app>_<object-slug>_<YYYYMMDD-HHMM>.pdf` (or `.html`), for example
  `camposcope_MT-5108501-CBE0F5_20260924-1530.pdf`.
- Batch runs: `territory/{slug}/{slug}_report.pdf`.

### 2.10 Kit tests (canonical, run through each vendored copy)

**Status (2026-09-24): kit v0.1.0 is built** in the canonical location. The tests below pass
(`tests/test_report_kit.py`, 23 tests, plus `tests/test_report_kit_manifest.py`), and a report
also renders under a real CPython 3.11.15. A synthetic 7-page report with every block type,
6 charts, a 4000 px backdrop and a 120-row table is 0.37 MB and renders in 0.4 s.
`scripts/sync_report_kit.py --check` verifies all copies. Both repositories' `.gitignore`
ignored any file named `MANIFEST`; `!**/report_kit/MANIFEST` now overrides that.

- A synthetic `Report` using **every block type** produces bytes starting with `%PDF` and one
  self-contained HTML file with no external URLs.
- A 4000 px input image is embedded at the slot's pixel size or smaller, and a JPEG backdrop
  stays JPEG.
- 8 figures + 4 maps + 3 tables produce a file of **3 MB or less**.
- A 120-row `Table` spans pages and repeats its header row.
- `fmt_num(1234.5)` gives `1.234,5` in pt, es and fr style and `1,234.5` in en. The kit strings
  exist in all four languages.
- `Figure(png=None)` renders the placeholder and does not raise.
- `JobStore` rejects wrong tokens, prefixes and sizes, and an oversized IHDR; a job times out
  into "unavailable" entries.
- `MapView` aspect and scale-bar arithmetic are checked at the equator and at 30°S.
- The suite runs under Python 3.12 (Naturametrics, Camposcope) **and 3.11** (the Yvynation
  venv).

---

## 3. Report outline (Yvynation)

This fills in the common outline of §2.4. y1 and y2 are the comparison years
(`comparison_year1` / `comparison_year2`).

| # | Section | Blocks |
| --- | --- | --- |
| 1 | Identification | **TI:** `terrai_nom`, `terrai_cod`, `etnia`, `fase_ti`, `modalidade`, UF, município, official area (`superficie_ha`) vs computed area, and the demarcation ladder years (em estudo → delimitada → declarada → homologada → regularizada). **UC:** `nome_uc`, `cd_cnuc`, `grupo`, `categoria`, `esfera`, UF, município, official vs computed area, creation year. **Analysis:** y1, y2, MapBiomas collection (`MAPBIOMAS_DEFAULT_COLLECTION = v10_1`), Hansen GFC (`UMD/hansen/global_forest_change_2025_v1_13`), GLAD GLCLU2020 v2, buffer width. `SideBySide` with the `LocatorMap` |
| 2 | About this report | `ContentsList`: land cover y1/y2, gains/losses, transitions, Hansen GFC, GLAD, multi-window, deforestation timeline, territory vs buffer. Each is *included*, *not run*, *unavailable (belongs to another area)* or *excluded* |
| 3 | Maps | `SideBySide`: MapBiomas y1 and y2 (half slots), each with the boundary and the buffer outline as vectors. Then GFC loss year with outlines (full). Then the imagery backdrop with outlines (full): Landsat annual composite above 50 km, Sentinel-2 below |
| 4 | Land cover y1 vs y2 | Figure `comparison_bar`; table of class, y1 ha, y2 ha, Δ ha and Δ %; reading paragraph |
| 5 | Gains and losses | Figure `gains_losses` (plus `change_pct` in the appendix) |
| 6 | Transitions | Figure `sankey`; table of the top 10 transitions from `territory_transitions` |
| 7 | Hansen GFC | Figure `gfc_loss` (loss by year); summary table: tree cover in 2000, total loss, % of the 2000 cover, gain (2000–2012, undated) |
| 8 | GLAD | Figure `hansen_glad_bar`, if run |
| 9 | Multi-window | The multi-window figures, if run |
| 10 | Deforestation timeline | The timeline series chart, if run, with a one-line note on the political/policy context layers shown |
| 11 | **Territory vs buffer** | Table of metric, territory, buffer and difference: forest % in y1 and y2, change in pp, GFC loss as % of 2000 cover. Paragraph on the gap between buffer and core loss. Buffer figures (`buffer_*`) go in the appendix |
| 12 | Methods and data | `ProvenanceTable` built from config (§4) |
| 13 | Sources and citation | `citation_*` translations, plus the acknowledgement that processing runs on Earth Engine project *ProtectedLandsYvynation-EE* (noncommercial research) |
| 14 | Appendix *(optional; always off in batch)* | Full class tables for y1 and y2, buffer figures, `change_pct`, the transition matrix |

### 3a. Explanatory text: examples (`utils/report_text.py`, en reference, pt/es/fr, fallback to en)

| Section | en | pt |
| --- | --- | --- |
| Land cover | "Between 1985 and 2024, forest formation inside the territory went from 912,400 ha (93.1%) to 881,020 ha (89.9%), a decrease of 31,380 ha. Pasture grew by 24,110 ha." | "Entre 1985 e 2024, a formação florestal dentro do território passou de 912.400 ha (93,1 %) para 881.020 ha (89,9 %), uma redução de 31.380 ha. A pastagem cresceu 24.110 ha." |
| GFC | "Hansen records 18,740 ha of tree-cover loss from 2001 to 2024, 2.0% of the 2000 tree cover; the largest single year was 2019 (2,310 ha)." | "O Hansen registra 18.740 ha de perda de cobertura arbórea entre 2001 e 2024, 2,0 % da cobertura de 2000; o maior ano foi 2019 (2.310 ha)." |
| Territory vs buffer | "Over the same period, forest fell 3.2 pp inside the territory and 14.8 pp in its 10 km buffer, a gap of 11.6 pp." | "No mesmo período, a floresta caiu 3,2 p.p. dentro do território e 14,8 p.p. no buffer de 10 km, uma diferença de 11,6 p.p." |

The text states differences and never attributes them to protection, governance or any cause
(§2.8). The causal reading belongs to the offline governance reports in `utils/`, not to a
per-area export.

---

## 4. Where each block comes from

| Block | Source in the code |
| --- | --- |
| Snapshot | `utils/export_service.py::collect_export_data_from_state` (L1661), called inside `async with self`. It returns `territory_figures` (the `terr_figs` dict: `comparison_bar`, `gains_losses`, `change_pct`, `sankey`, `sunburst`, `treemap`, `transition_matrix`, `hansen_glad_bar`, `gfc_bar`, `gfc_loss`), `buffer_figures`, results, transitions, `glad_result`, `gfc_result`, buffer results and `territory_geojson_cached` |
| TI metadata | `utils/territory_service.py` `get_territory_info` (L230) and `get_demarcation_dates` (L248) |
| UC metadata | `utils/conservation_service.py` L239 (fields) and `get_creation_info` (L266) |
| Years and datasets | `comparison_year1/2`, `territory_year`, `territory_source`, `hansen_current_year`, `auto_buffer_km` (`state/__init__.py`); `config/config.py` L50-78 |
| Methods table | **New `utils/report_provenance.py`.** Yvynation has no `Provenance` records, so this builds kit `ProvenanceTable` rows (`name`, `dataset_id`, `bands`, `scale_m`, `reducer`, `computed_at`, `notes`) per section from the config constants and the run context. It records what was used and does not recompute anything |
| Map image builders | `utils/map_export_service.py` `_raster_specs` (L677) and `get_ee_layer_image` (L233): split the ee.Image and vis construction into `ee_layer_image(layer_type, year, geometry)`, which is used both by `get_ee_layer_image` and by the kit's `fetch_thumbnail` |
| Citation | `citation_*` keys (`utils/translations/en.py:498-513`) |

---

## 5. Chart path: server side, kaleido (R3)

Figures are rasterised with the existing helper,
`export_service._plotly_to_png_bytes(fig, width, height, scale)` (L803). The explicit
arguments come from `report_kit.images.chart_opts(slot, aspect)`, so R9 sizes apply and the
batch-wide `FIGURE_EXPORT` policy is bypassed. `_kaleido_v1_render` (L783) already takes a
format. The figure dict first goes through `prepare_figure` (white background, fixed size).

**Single area, a background handler `build_report(fmt)`:**

1. Take the snapshot and the metadata lookup inside `async with self`.
2. Fetch the Earth Engine thumbnails in the I/O pool.
3. Rasterise the charts on `get_render_executor("kaleido")` (`utils/ee_concurrency.py:461`).
4. Compose with reportlab on the default executor. reportlab is thread-safe per document once
   fonts are registered at import.
5. Save with `save_export_to_upload_dir` and deliver with
   `rx.download(url=get_download_url(rel))`.

The HTML format skips steps 3–4 and embeds `fig_json`.

**Batch, per area** (`state/_batch.py`):

- **Capture.** Next to `region_map_data.append(...)` (L2264), append the per-region dicts
  already in memory to `region_report_data`: `mb1`, `mb2`, `cmp`, `glad`, `gfc`, `bmb`, `bcmp`,
  `bglad`, `bgfc`. This adds no Earth Engine calls.
- **Hook at about L2820**, before the completion bookkeeping:
  1. **I/O pool:** merge the quadrants: sum `Area_ha` per class, the transitions, GFC loss per
     year and GLAD, then recompute the percentages. A single region passes through unchanged.
     Fetch the maps for the whole territory and the buffer box. The buffer shape is already
     fetched by `_prefetch_maps` (L2503-2539) when maps are on; otherwise fetch it here.
  2. **Kaleido lane:** `_build_territory_figures` (L274) on the merged data, rasterised at
     report size: 5–7 figures at about 25–70 ms each. They are rendered again rather than
     reusing the ZIP's PNGs, which are per quadrant, use the batch scale of 1.2 or 2.0 (L1342),
     and do not exist when PNG export is off (L1794).
  3. **Default executor:** compose and write `territory/{slug}/{slug}_report.pdf` through the
     run's `DirExportWriter`.
- **Rules:**
  - Fetch everything from Earth Engine *before* entering a lane (`utils/ee_concurrency.py:45`; BATCH_CONCURRENCY.md §7).
  - Never run reportlab on the kaleido or matplotlib lanes; it would block other areas'
    renders.
  - Don't reuse `total_area` (L2821): it reads only the last quadrant.
- A failed report is logged into the area's status and **never fails the area**. The ZIP and
  CSVs are the primary output.

---

## 6. Maps

| Map | Image builder | View |
| --- | --- | --- |
| MapBiomas y1, y2 | `ee_layer_image("mapbiomas", year, geom)` (split, §4) | territory + buffer + margin |
| GFC loss year | `ee_layer_image("hansen", …)` (the `"hansen"` layer type of `_raster_specs`) | same |
| Imagery | `report_kit.maps.imagery_backdrop(view, y2)`: Landsat annual composite above 50 km, Sentinel-2 below | same |

- The boundary and buffer come from the cached territory GeoJSON and are drawn as vectors.
- The big Flonas (above 1 M ha) are a single view of the whole territory. Thumbnails are
  resampled by EE at about 600 m/px, so no quadrant stitching is needed.
- Legends show only the classes present, with the MapBiomas 10.1 palette.

---

## 7. UI

**Single area.** A third tab, **"Report"**, in `export_panel.py`, holding the shared block
(§2.9):

- **Checkboxes:** `exp_report_maps`, `exp_report_figures`, `exp_report_tables` and
  `exp_report_appendix`.
- **Buttons:** PDF and HTML, calling `start_report(fmt)`.
- **Stage line:** "Charts 3/7 · Maps 2/3 · Composing".
- **Disabled** without an active result or while busy.

The three tab labels move to `tr` keys (`export_tab_data`, `export_tab_maps`, `export_tab_report`)
in en, pt, es and fr. The rest of the English-only panel may follow, but is not required.

**Batch.** A `batch_run_report_pdf` checkbox in `_figures_group()`
(`components/batch_config_panel.py:129`), with its handler `batch_toggle_report_pdf` in
`state/_batch.py` next to L1307-1424. It is on by default, with the hint "One readable PDF per
area, in the interface language". `batch_summary.json` and `batch_report.md` list each area's
report path.

Translation coverage is checked with `python -m yvynation.utils.translations`.

---

## 8. Delivery

| Case | Delivery |
| --- | --- |
| Single area | Written to the root of `uploaded_files/exports/` as `yvynation_<slug>_<YYYYMMDD-HHMM>.pdf` through `save_export_to_upload_dir` (`export_service.py:255`). Downloaded by `rx.download(url=get_download_url(rel))` through `/download/exports/{filename}`, which accepts plain file names only. Kept for 10 per prefix by `prune_old_exports`, and expires with the bucket lifecycle (about a day) |
| Batch | Inside the run folder, so it is included in the final ZIP |

---

## 9. Guardrails

- **Licences (R5).** EE thumbnails only. The report never embeds `create_map_set` output, which
  contains Google/Esri tiles. Attributions include MapBiomas (CC BY-SA 4.0), Hansen/UMD/Google/
  USGS/NASA (CC BY 4.0), "Contains modified Copernicus Sentinel data {yr}" or "Landsat:
  USGS/NASA", and the FUNAI/CNUC boundary sources.
- **Noncommercial EE registration.** The footer or citation always carries the
  *ProtectedLandsYvynation-EE* acknowledgement.
- **Descriptive text only (§2.8).** No causal or governance claims in per-area reports.
- **No mixing of areas** (§1, pitfall 1).

---

## 10. Files to add or change

| File | Change |
| --- | --- |
| `yvynation/report_kit/**` | **Vendored** from Naturametrics by its `scripts/sync_report_kit.py`. Never edited here. Must pass its tests under this venv's Python 3.11 |
| `yvynation/utils/report_builder.py` | New: `build_territory_report(snapshot, meta, pngs, maps, lang, options) -> Report`, shared by the single-area and batch paths |
| `yvynation/utils/report_text.py` | New: explanatory templates (en/pt/es/fr) |
| `yvynation/utils/report_provenance.py` | New: methods rows from config and run context (§4) |
| `yvynation/utils/map_export_service.py` | Split `ee_layer_image` out of `get_ee_layer_image` |
| `yvynation/state/_export.py` | New vars (§2.9); `start_report` and the background `build_report` |
| `yvynation/state/_analysis.py`, `_territory.py` | ✅ done: per-area save and restore of results (§1, pitfall 1) |
| `yvynation/state/_batch.py` | `batch_run_report_pdf` and its toggle; `region_report_data` capture; the hook at about L2820; quadrant merge |
| `yvynation/components/export_panel.py` | "Report" tab; tab labels via `tr` |
| `yvynation/components/batch_config_panel.py` | Checkbox in the figures group |
| `yvynation/utils/translations/{en,pt,es,fr}.py` | `report_*`, `export_tab_*`, `batch_chk_report_pdf` keys |
| `requirements.txt` | `reportlab>=4.2,<5` (Pillow is already pinned) |
| `Dockerfile` | Extend the build-time smoke test to render a one-page kit report |
| `tests/test_report_builder.py`, `tests/test_report_quadrant_merge.py`, `tests/test_report_kit_manifest.py` | New |
| `docs/EXPORT_DOWNLOADS.md`, `docs/BATCH_CONCURRENCY.md` | Links to this doc |

---

## 11. Tests and the done test

**Offline** (`pytest`):

- `build_territory_report` on synthetic TI and UC snapshots: sections come in the §3 order, and
  missing analyses are `not_run`.
- Switching areas restores each area's own GLAD/GFC/buffer results, never a mix
  (`tests/test_area_switch.py`, ✅ passing).
- Quadrant merge: four synthetic quadrants sum to the expected class areas, and the percentages
  add up to 100 ± 0.01.
- es and fr reports contain no English template text, except the fallback keys listed by the
  translation coverage check.
- The kit tests pass under **Python 3.11** here, and the manifest test passes.

`tests/test_export_service.py` is stale (it expects `README.txt` and `metadata["year"]`). It is
out of scope: don't use it as the gate.

**Live** (run locally):

1. One small TI: PDF and HTML, in en and pt.
2. A batch of 3: the small TI, one UC, and one area above 1 M ha (quadrant split).

For each, check the per-area PDFs in the run folder and in the final ZIP.

**Done test.**

- **Single area:** a user analyses a TI with a 10 km buffer, opens *Export → Report* and
  presses PDF. They get a file of 3 MB or less. Page 1 names the land, its ethnic group, stage
  and state, and lists what the report contains. The maps have legend, scale bar and
  attribution, and use no Google or Esri imagery. The charts match the screen. The territory vs
  buffer table matches the ZIP's CSVs.
- **Batch:** a 3-area batch with *PDF report per area* ticked writes three such PDFs. The one
  above 1 M ha reports whole-territory totals, not the SE quadrant's.


**Implementation status (2026-09-24).** Built: `utils/report_builder.py`, `utils/report_text.py`,
`utils/report_provenance.py`, `map_export_service.ee_layer_image` (adds a `gfc_loss` layer type),
the *Report* tab (`start_report` / background `build_report` in `state/_export.py`), and the batch
hook (`_build_area_report` in `state/_batch.py`, reports listed in `batch_summary.json` and
`batch_report.md`). Tests: `tests/test_report_builder.py`, `tests/test_report_quadrant_merge.py`.
A live smoke run (Chão Preto, en and pt, real EE maps and kaleido 0.2.1 charts) gave a 12-page,
0.88 MB PDF. Not yet verified: clicking through the UI in a browser, and a real batch run.
Notes:
- Figure JSON is passed as plain lists, never `fig.to_json()`. Plotly 6 base64 `bdata` arrays
  are read as indices by the plotly.js bundled with kaleido 0.x.
- The kit's Noto Sans subset has no `→`, `−` (U+2212) or `↳`. The app avoids them, but the kit's
  own `fmt_signed` and the provenance-note arrow print blanks. This needs a fix upstream.
- The HTML format inlines plotly.js (about 5 MB), so the 3 MB budget applies to the PDF only.

---

## 12. Deliberately deferred

- A run-level summary PDF.
- Reports for drawn polygons.
- Translating the rest of the export panel.
- Replacing the Google/Esri basemaps in the existing *PDF Maps* export. That licensing question
  predates this work and is only noted here.
