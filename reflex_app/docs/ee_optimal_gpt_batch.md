
Plan: I'll list the full ordered processing sequence (when every option is ON), and for each step mark where it runs (Earth Engine vs Local / app process) and name the implementing functions/files so you can grep the code or Google improvements.

1) Initialize Earth Engine (idempotent)
- Where: Local process → initializes EE client library.
- Code: `run_batch_processing` → calls `initialize_earth_engine()` (utils/ee_service).
- Notes: client init only — no server computation.

Per territory (parallel workers, see ee_concurrency):

2) Load territory geometry from local GeoPackage and wrap as ee.Geometry
- Where: Local read (GeoPackage) → returns `ee.Geometry` (EE client object; lazy)
- Code: `_get_ee_geom()` in state/_batch.py → `territory_service.get_geojson_for_key` / `ee.Geometry(...)`

3) Create external buffer (if enabled)
- Where: Earth Engine server-side operations (buffer + difference are EE ops executed lazily by client)
- Code: `create_external_buffer` (utils/buffer_utils.py) invoked via run_in_executor

4) Decide split vs single region (quadrant split for large areas)
- Where: Area lookup uses local GeoPackage/shapely; quadrant creation uses EE geometry intersections (EE-side lazy)
- Code: `_get_area_and_shapely()` + `_make_quadrant_regions()` (state/_batch.py)

5) For each region (whole or nw/ne/sw/se) issue all EE analyses in parallel:
   - MapBiomas single-year y1
     - Where: Earth Engine server-side (`reduceRegion(frequencyHistogram)`) → result returned via `.getInfo()`
     - Code: `ExtendedEarthEngineService.analyze_mapbiomas` (utils/ee_service_extended.py) / or MapBiomasAnalyzer.analyze_single_year (utils/mapbiomas_analysis.py)
   - MapBiomas single-year y2
     - Same as above
   - MapBiomas comparison (y1→y2)
     - Where: EE (analyze_single_year twice → compute_transitions uses combined image → `reduceRegion(frequencyHistogram)`), then local pandas merges & gains/losses
     - Code: `mapbiomas_analysis.get_mapbiomas_analyzer().analyze_single_year`, `compute_transitions()` (utils/mapbiomas_analysis.py)
   - Multi-window transitions (if enabled) — pairwise transition reduceRegion calls per pair
     - Where: EE (`compute_transitions` repeated per pair)
     - Code: `_multi` → `get_mapbiomas_analyzer().compute_transitions` (state/_batch.py + utils/mapbiomas_analysis.py)
   - Hansen GLAD (area distribution)
     - Where: EE (`reduceRegion` frequencyHistogram) → DataFrame locally
     - Code: `get_hansen_analyzer().get_area_distribution` (utils/hansen_analysis.py)
   - Hansen GFC (treecover, lossyear, gain histograms)
     - Where: EE (`reduceRegion` frequencyHistogram called multiple times) → assembled locally
     - Code: `HansenAnalyzer.analyze_gfc` (utils/hansen_analysis.py)
   - Buffer versions of MapBiomas / Comparison / GLAD / GFC (if buffer enabled)
     - Where: EE calls identical to above but using buffer ee.Geometry
     - Code: `_buf_mb`, `_buf_cmp`, `_buf_glad`, `_buf_gfc` (state/_batch.py)

   Implementation notes:
   - All EE calls are dispatched concurrently via `_ee_with_retry` and the EE executor pool (utils/ee_concurrency).
   - Most server-side work uses `ee.Image.reduceRegion(...).getInfo()` or `ee.Image.getDownloadURL()` (see get_ee_layer_image).
   - Retry/backoff (`_ee_with_retry`) and concurrency budgeting (`effective_territory_concurrency`) are used.

6) Shape & validate results locally
- Where: Local (app process)
- Actions: parse EE histograms into pandas DataFrames, compute gains/losses, build transition dicts, mark skipped if None/empty
- Code: state/_batch.py shaping blocks, utils/analysis.py (`compare_areas` etc.), utils/mapbiomas_analysis.py

7) Collect per-region metadata for later maps/timeline
- Where: Local (accumulate `region_map_data` list in memory)
- Code: state/_batch.py

8) Build figures (Plotly) for MapBiomas / GLAD / GFC / transitions / treemap / sankey / sunburst
- Where: Local (CPU) — chart building with Plotly / matplotlib
- Code: `_build_territory_figures()` (state/_batch.py) + utils/visualization.py helpers
- Note: All figure rendering goes through `_render()` to a single-slot render pool (serialized) because kaleido / pyplot have global state.

9) Write per-region files (CSV/JSON + figures) into the live export folder
- Where: Local filesystem (DirExportWriter writes files to uploaded_files/exports/<run_name>/...)
- Code: `_write_region_to_zip()` → uses export_service helpers `_write_mapbiomas_section`, `_write_hansen_glad_section`, `_write_hansen_gfc_section`, `_write_multi_window_section`

10) After regions: write boundary.geojson (local file write)
- Where: Local
- Code: `_write_boundary()` in state/_batch.py

11) Create PDF / PNG maps (satellite + MapBiomas y1/y2 + Hansen + aux layers)
- Steps:
  - For each region, `create_map_set()` (utils/map_export_service.py) is called.
  - For each raster overlay, `get_ee_layer_image()` is invoked:
    - It builds an EE Image (e.g., MapBiomas band or aux asset), calls `.visualize()` and then `image.getDownloadURL(...)` (EE server-side tile/png rendering), then `requests.get(url)` to fetch the generated PNG (app does the HTTP download).
  - Basemap tiles (Google / ArcGIS) are fetched via HTTP requests (local).
  - Matplotlib composes layers and writes PDF/PNG (local).
- Where: EE server produces raster images via `getDownloadURL` (server-side); composition, basemap download, and final PDF/PNG rendering are local.
- Code: `create_map_set()` + `create_pdf_map()` + `get_ee_layer_image()` (utils/map_export_service.py)

12) Deforestation timeline (if enabled)
- Steps:
  - Collect series with `collect_timeline()` (utils/deforestation_timeline.py) — uses:
    - Hansen series built from gfc_result (local from earlier EE GFC)
    - MapBiomas aux series: stacked `reduceRegion` calls (via `_series_class_value`, `_series_nonzero`, `_series_year_value`) — EE server-side heavy but minimized (stacked reduceRegion to reduce round-trips)
  - Visualization of timelines & single-indicator charts (Plotly/matplotlib) — local
  - Write CSV + figures to export folder — local
- Where: EE for the stacked indicator reductions; local for charting & file writes.

13) Mark territory completed / error handling
- Where: Local (state updates, logs)
- Code: batch summary assembly in state/_batch.py

After all territories:

14) Write batch summary files (JSON + markdown)
- Where: Local file writes
- Code: `_write_summary` in state/_batch.py

15) Compress live export folder into final ZIP
- Where: Local (zip_directory writes ZIP on disk), then optionally remove folder. `save_export_to_upload_dir` used for non-bucket case.
- Code: `zip_directory`, `save_export_to_upload_dir` (utils/export_service.py)

16) Make download URL available (local / GCS sign if bucket configured)
- Where: Local (generate signed URL via GCS client if GCS_EXPORT_BUCKET is set)
- Code: `get_download_url` (utils/export_service.py)

Concurrency / reliability details
- EE calls are executed via an executor pool and wrapped with `_ee_with_retry()` which retries on transient EE errors (timeout, 5xx, rate limit).
- Rendering (kaleido/pyplot) is serialized via a separate single-worker render pool (`_render`) to avoid corruption.
- Quadrant splitting uses EE intersection (server-side lazy) so splitting itself is cheap; heavy work remains in the EE reduceRegion calls.
- Many EE calls use `.getInfo()` and `getDownloadURL()` — synchronous round-trips from Python client.

Which parts are EE-heavy vs local summary
- Mostly EE (server-side):
  - Buffer creation (buffer/difference)
  - MapBiomas per-year histograms (reduceRegion frequencyHistogram)
  - MapBiomas transitions (combined image → reduceRegion)
  - MapBiomas multi-window stacked transitions / per-year aux layers (stacked reduceRegion)
  - Hansen GLAD and GFC histograms (reduceRegion)
  - getDownloadURL for EE visualized images (EE server-side tile/png generation)
  - Quadrant intersection (ee.Geometry.intersection, lazy)
- Mostly Local (app process):
  - Reading GeoPackage geometries & attributes
  - Shaping results into pandas DataFrames
  - Gains/losses, merges, CSV creation
  - Plotly/matplotlib figure generation (via _render)
  - Basemap tile HTTP fetch and map composition
  - File writes, ZIP creation, signed URL generation
  - Control flow, concurrency, retries, and UI state

Quick recommendations to research (Google / Earth Engine docs) — places to possibly improve performance or robustness
- Replace frequent synchronous `.getInfo()` calls for large or many reduceRegion results with asynchronous/export workflows:
  - Use `ee.batch.Export.table.toCloudStorage` or `ee.batch.Export.table.toDrive` or `Export.image.toCloudStorage` for large histograms / tables, then read results from GCS. This avoids client `getInfo()` timeouts for large AOIs.
- For per-feature aggregations at scale, consider `ee.Image.reduceRegions()` on a feature collection and then `Export.table.*` rather than repeated `reduceRegion` calls per geometry.
- Use `tileScale` or `bestEffort=True` where reduceRegion fails on very large geometries; but prefer export tasks for deterministic results.
- For raster visualization downloads, `image.getDownloadURL()` is convenient but can be rate/size limited. Consider `Export.image.toCloudStorage` for large/hi-res map images and fetch from GCS.
- Use region-tiling + asynchronous exports for very large territories instead of client-side quadrant logic; EE Tasks can be queued and monitored.
- Minimize `getInfo()` round-trips by returning more aggregated results server-side (e.g., an EE `FeatureCollection` of results you `Export.table`), or compress multiple reducers into one stacked reduceRegion where possible (you already use stacked reduceRegion in timeline — good pattern).
- Consider using Earth Engine's `Image.reduceRegion(reducer=ee.Reducer.frequencyHistogram().forEach(...))` patterns or `ee.Reducer.histogram().group()` variants that produce table-ready outputs.
- If you expect many large batch runs, consider using Cloud-run / GCS pipeline: dispatch EE Export tasks and poll for completion, then assemble outputs from GCS — removes memory/time pressure on the web container.
- Look into newer Earth Engine best-practices and examples: `Export.table.toCloudStorage` for histograms, `reduceRegions` + `FeatureCollection` exports, and using `task.start()` + monitoring via `ee.batch` instead of synchronous getInfo for large jobs.

Compacted conversation

Updated todo list

I'll scan the codebase for Earth Engine API usages and reducers, then produce (1) a checklist mapping each EE call to the reducer used and file/line hints, and (2) a concise migration plan to move heavy reduceRegion/getInfo work to async Exports→GCS. I'll search the repo for EE patterns now.

Search complete: Find occurrences of Earth Engine API usage and reduceRegion/reducer patterns across the workspace

Searched codebase for "Earth Engine ee.Image reduceRegion getDownloadURL getInfo Export.image Export.table frequencyHistogram histogram reduceRegions", no results

Searched for regex `ee\.`, 915 results

Searched for regex `reduceRegion|reduceRegions`, 118 results

Searched for regex `frequencyHistogram|getDownloadURL|getInfo`, 317 results

Searched for regex `Export\.image|Export\.table`, 27 results

Searched for files matching `**/*ee*`, 184 matches

Searched for files matching `**/*.py`, 200 matches

Searched for text `getMapId`, 33 results

Now I'll run parallel text searches for the key EE patterns (reduceRegion, frequencyHistogram, getDownloadURL, Export, reduceRegions, getInfo) inside the Reflex app.

Searched for text `reduceRegion` (`**/reflex_app/**`), 80 results

Searched for text `frequencyHistogram` (`**/reflex_app/**`), 33 results

Searched for text `getDownloadURL` (`**/reflex_app/**`), 35 results

Searched for text `Export.image` (`**/reflex_app/**`), 62 results

Searched for text `Export.table` (`**/reflex_app/**`), 96 results

Searched for text `reduceRegions` (`**/reflex_app/**`), 18 results

Searched for text `getInfo(` (`**/reflex_app/**`), 107 results

I'll open the key util files to extract the exact EE calls and reducers used. I'll read the EE service, mapbiomas, hansen, timeline, map export, buffer, and batch orchestration files.

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/ee_service_extended.py)

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/mapbiomas_analysis.py#1-1), lines 1 to 400

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/mapbiomas_analysis.py#400-400), lines 400 to 441

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/analysis.py#1-1), lines 1 to 300

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/analysis.py#300-300), lines 300 to 348

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/hansen_analysis.py#1-1), lines 1 to 400

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/hansen_analysis.py#400-400), lines 400 to 501

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/deforestation_timeline.py#1-1), lines 1 to 300

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/deforestation_timeline.py#300-300), lines 300 to 623

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/map_export_service.py#1-1), lines 1 to 400

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/utils/buffer_utils.py)

Read [](file:///home/leandromb/google_eengine/yvynation/reflex_app/yvynation/state/_batch.py#1-1), lines 1 to 400

Now I'll collect exact line numbers for the key EE calls in the main utility files so I can include precise file+line links. I'll grep each target file for the reducer or call.

Searched for text `ee.Reducer.frequencyHistogram` (`**/reflex_app/yvynation/utils/**`), 10 results

Searched for text `reduceRegion(` (`**/reflex_app/yvynation/utils/**`), 22 results

Searched for text `getDownloadURL(` (`**/reflex_app/yvynation/**`), 1 result

Searched for text `create_external_buffer` (`**/reflex_app/yvynation/utils/**`), 1 result

Searched for text `_make_quadrant_regions` (`**/reflex_app/yvynation/state/_batch.py`), 2 results

Good — I did both. Below are (A) a compact checklist mapping each EE call in the repo to the exact reducer / API used (with file+line links you can click), and (B) a concise migration plan (steps + minimal code snippets) to move the heaviest `reduceRegion`/`.getInfo()` workloads to asynchronous Exports → Cloud Storage.

**A — Checklist: EE calls → reducer / API (file + line)**
- MapBiomas single-year histogram  
  - File: ee_service_extended.py — `image.reduceRegion(..., reducer=ee.Reducer.frequencyHistogram())` → `.getInfo()`
  - Caller: `ExtendedEarthEngineService.analyze_mapbiomas()` (`analyze_mapbiomas`)
- Hansen single-year histogram (Extended service)  
  - File: ee_service_extended.py — `hansen_image.reduceRegion(..., reducer=ee.Reducer.frequencyHistogram())` → `.getInfo()`
- MapBiomas transitions (band1*1000 + band2 → histogram)  
  - File: mapbiomas_analysis.py — `combined.reduceRegion(..., reducer=ee.Reducer.frequencyHistogram())` → `.getInfo()`
  - Caller: `MapBiomasAnalyzer.compute_transitions()`
- Area-by-class grouped sum (pixelArea + group reducer)  
  - File: analysis.py — `reduceRegion(reducer=ee.Reducer.sum().group(groupField=1, groupName='class'))` → `areas.getInfo()`
  - Caller: `calculate_area_by_class()`
- Change-area, class-specific loss/gain (sum reducer)  
  - File: analysis.py — `reduceRegion(reducer=ee.Reducer.sum())` → `.getInfo()` (change area)  
  - File: analysis.py — class loss/gain uses `ee.Reducer.sum()` → `.getInfo()`
- Hansen GFC: treecover / lossyear / gain (frequencyHistogram)  
  - File: hansen_analysis.py — `dataset.select(["treecover2000"]).reduceRegion(..., ee.Reducer.frequencyHistogram())` → `.getInfo()`  
  - File: hansen_analysis.py — `lossyear` histogram  
  - File: hansen_analysis.py — `gain` histogram
- Stacked yearly collectors (timeline) — stacked sum across per-year bands  
  - File: deforestation_timeline.py — `_reduce_stacked()` uses `stacked.reduceRegion(reducer=ee.Reducer.sum(), ..., bestEffort=True).getInfo()`  
  - Callers: `_series_year_value`, `_series_class_value`, `_series_nonzero` (timeline collectors)
- Quadrant splitting (geometry intersections — lazy EE ops)  
  - File: _batch.py — `_make_quadrant_regions()` uses `ee.Geometry.intersection()` and `ee.Geometry.Rectangle()` (GEOMETRY ops, no reducers)
- EE raster download / visualization (image → PNG)  
  - File: map_export_service.py — `image.visualize(...).getDownloadURL({...})` then `requests.get(url)` → local composition (used by `get_ee_layer_image()` / `create_pdf_map()`)
- Buffer creation (EE geometry ops)  
  - File: buffer_utils.py — `geometry.buffer(...).difference(geometry)` (EE geometry methods)
- Many call sites use `.getInfo()` to synchronously pull EE results into Python (see above lines). These are the primary time/timeout pressure points.

(If you want a full grep-able table I can produce a CSV mapping every `reduceRegion`/`getDownloadURL`/`.getInfo()` hit — say so and I’ll dump it.)

**B — Migration plan: move heavy `reduceRegion`/`.getInfo()` work to async Export → Cloud Storage**

Goal: avoid large synchronous `reduceRegion(...).getInfo()` calls for big geometries by using server-side exports (table/image) and fetching results from Cloud Storage reliably.

Plan (short, actionable):

1) Add configuration / infra
   - Provision a GCS bucket (or existing bucket) and set env `GCS_EXPORT_BUCKET`.
   - Ensure the service account used by EE has write access to that bucket if using server-side export from EE Tasks, or export to Drive/GCS as appropriate.

2) Identify heavy functions to convert (priority order)
   - `MapBiomasAnalyzer.analyze_single_year()` / `ExtendedEarthEngineService.analyze_mapbiomas()` — histogram per-territory (freqHistogram)  
   - `MapBiomasAnalyzer.compute_transitions()` — large frequencyHistogram on combined image  
   - `HansenAnalyzer.analyze_gfc()` — three frequencyHistogram calls  
   - `_reduce_stacked()` / timeline collectors in deforestation_timeline.py — stacked sum reduceRegion  
   - `get_ee_layer_image()` in map_export_service.py — replace `getDownloadURL()` for large images if necessary

3) Replace synchronous `reduceRegion(...).getInfo()` with asynchronous export of a small table:
   - Strategy A (preferred for histograms / tabular results): Build a FeatureCollection (one feature per region/quadrant) with geometry → call `image.reduceRegions(collection=fc, reducer=ee.Reducer.frequencyHistogram(), scale=30)` → the result is a FeatureCollection of features each with a histogram property. Then `ee.batch.Export.table.toCloudStorage(collection=results_fc, bucket=GCS_EXPORT_BUCKET, description=..., fileFormat='CSV' or 'GEOJSON')`. Start task and poll until completion, then read CSV from GCS.
   - Strategy B (for single-feature heavy AOI): create a FeatureCollection containing that single feature and use `reduceRegions` + Export.table (still async). Avoid `.getInfo()` on the client.

4) For `sum` reductions (area sums) and stacked sums:
   - Use `image.reduceRegions()` with `ee.Reducer.sum()` (one feature per region), then `Export.table.toCloudStorage(...)`.
   - Alternatively create an image where each band is already in hectares per pixel and `Export.table.toCloudStorage` on the result of `reduceRegions`.

5) For transition histograms (MapBiomas transitions):
   - Instead of `combined.reduceRegion(..., frequencyHistogram)`, create a FC with quadrants (or tile grid), call `combined.reduceRegions(fc, ee.Reducer.frequencyHistogram(), scale=30)`, export FC table, then post-process CSV grouped by feature id locally to reconstruct transition dict. This lets EE do the heavy histogram server-side asynchronously.

6) For raster visualizations / high-res maps:
   - Replace `image.getDownloadURL()` with `ee.batch.Export.image.toCloudStorage(image=vis_image, description=..., bucket=GCS_EXPORT_BUCKET, scale=..., region=..., fileFormat='PNG')`. Start tasks, poll, then fetch PNG from GCS and compose locally. Keeps EE to produce large images robustly.

7) Implement an EE Task manager (small helper)
   - Add `utils/ee_task_utils.py` with:
     - `start_export_task(task)` wrapper (`task.start()`), `poll_task(task, timeout=..., poll_interval=10)` → returns status and GCS URI.
     - Limit concurrent exported tasks per-run (configurable).
     - Exponential backoff while polling; handle `FAILED` by logging and falling back to smaller AOI/quadrant split.

8) Fallback policy & incremental rollout
   - For each function migrated, keep a toggle/env var (e.g., `USE_ASYNC_EXPORTS=True`) and a small code path that falls back to original `.getInfo()` for small geometries (area < threshold) to avoid extra task overhead.
   - For very large AOIs, prefer tiled/quad approach and produce multiple exports (one per tile) then aggregate.

9) Polling & ingestion example (minimal)
   - Export table example (histograms):
```python
# Build FC with one feature (or multiple quadrants) named 'fid'
fc = ee.FeatureCollection([ee.Feature(geometry, {'fid': 'territory_1'})])
# Server-side reduceRegions -> FeatureCollection with histogram property 'hist'
results = image.reduceRegions(collection=fc, reducer=ee.Reducer.frequencyHistogram(), scale=30)
task = ee.batch.Export.table.toCloudStorage(
    collection=results,
    description='mapbiomas_hist_territory_1',
    bucket=GCS_EXPORT_BUCKET,
    fileNamePrefix='exports/mapbiomas_hist_territory_1',
    fileFormat='CSV'
)
task.start()
# Poll:
while True:
    sts = task.status()
    if sts['state'] in ('COMPLETED', 'FAILED', 'CANCELLED'):
        break
    time.sleep(10)
# On COMPLETED -> fetch CSV(s) from gs://{GCS_EXPORT_BUCKET}/exports/mapbiomas_hist_territory_1-*.csv
```
   - Export image example:
```python
vis_image = image.visualize(**vis_params)
task = ee.batch.Export.image.toCloudStorage(
    image=vis_image,
    description='mapbiomas_vis_territory_1',
    bucket=GCS_EXPORT_BUCKET,
    fileNamePrefix='exports/mapbiomas_vis_territory_1',
    scale=30,
    region=region_coords,  # list of coords as in getDownloadURL
    fileFormat='PNG'
)
task.start()
# poll as above; once done download PNG from GCS
```

10) Post-export aggregation & local shaping
   - After CSVs are downloaded from GCS, parse them into the same pandas shapes used today (same columns), and reuse existing figure / export code paths unchanged (only the data ingestion is different).
   - For multi-part exports (per-quadrant), aggregate the per-quadrant CSVs by summing counts/areas before building visualizations/CSV outputs.

11) Operational notes & tuning
   - Use `task.status()` polling with reasonable intervals (10–30s) and a per-run concurrent-export cap (e.g., 4–8). Use your existing `ee_concurrency` patterns to gate these.
   - If you need faster server-side memory, use `tileScale` or reduce image complexity (e.g., drop unnecessary bands) — but prefer Export tasks.
   - Where histograms are huge (many unique values) consider pre-aggregating server-side (e.g., map classes into buckets first) to reduce payload size.
   - Keep `bestEffort=True` for stacked `reduceRegion` if you keep any synchronous calls, but asynchronous export is more deterministic.

Files/functions to change first (concrete):
- ee_service_extended.py — `analyze_mapbiomas()` → use `reduceRegions` + `Export.table.toCloudStorage` for large geometries. (ee_service_extended.py)
- mapbiomas_analysis.py — `compute_transitions()` → `reduceRegions` + export table, then post-process. (mapbiomas_analysis.py)
- hansen_analysis.py — `analyze_gfc()` → export histograms as table. (hansen_analysis.py)
- deforestation_timeline.py — `_reduce_stacked()` → optionally create a server-side image and `Export.table` or `Export.image` depending on use-case. (deforestation_timeline.py)
- map_export_service.py — `get_ee_layer_image()` → consider `Export.image.toCloudStorage()` for large/hi-res map tiles instead of `getDownloadURL()`. (map_export_service.py)
- _batch.py — replace synchronous calls with a queue that starts exports and awaits task completion; reuse `_ee_with_retry()` semantics for polling. (_batch.py)

Would you like me to:
- (1) produce a small patch that adds a helper `utils/ee_task_utils.py` (task start + poll) and wire one sample function (e.g., `HansenAnalyzer.get_area_distribution`) to use an async Export→GCS path as a proof-of-concept, or  
- (2) generate a CSV/JSON report of every `reduceRegion`/`.getInfo()` hit (file + line + short snippet) so you can plan the refactor offline?
