# Batch Processing Concurrency

How the batch pipeline parallelises Earth Engine work, why the limits are what
they are, and **how to roll back to the Contributor Tier budget** when the
Partner Tier uplift expires.

| | |
|---|---|
| **Tier** | Earth Engine **Partner Tier** (uplift granted 2026-08-15) |
| **Expires** | **2027-02-15** — see [Rollback](#rollback-to-contributor-tier) |
| **Target runtime** | Cloud Run, 2 vCPU / 8 GiB |
| **Config** | [`yvynation/utils/ee_concurrency.py`](../yvynation/utils/ee_concurrency.py) |
| **Pipeline** | [`yvynation/state/_batch.py`](../yvynation/state/_batch.py) — `run_batch_processing` |

---

## 1. The shape of the problem

A batch run interleaves two kinds of work with opposite scaling behaviour.

**Earth Engine fetches** — `analyze_mapbiomas`, `get_area_distribution`,
`analyze_gfc`, `compute_transitions`. Each blocks in `getInfo()` waiting on
EE's compute backend, with the GIL released. They consume almost no local CPU,
so dozens can be in flight on a 2-core container. This is the work the Partner
Tier uplift lets us widen, and it dominates wall time in a typical run.

**Rendering** — Plotly figures → PNG via kaleido, Matplotlib map composition.
CPU-bound, and **must run one at a time**:

* `kaleido==0.2.1` drives one module-global headless renderer
  (`plotly.io._kaleido.scope`) over a single pipe. Concurrent `fig.to_image()`
  calls from different threads interleave on that pipe and deadlock or return
  truncated PNGs.
* `map_export_service` uses the `pyplot` state machine (global current
  figure/axes), which is likewise not thread-safe.

Widening EE fetches therefore does **not** require widening rendering, and
widening rendering is not an option at all without changing those dependencies.
The throughput win comes from **pipelining**: while one territory renders, the
others are waiting on Earth Engine.

---

## 2. Three levels of parallelism

```
run_batch_processing
│
├─ N territory workers ── pull from a shared queue (N = TERRITORY_CONCURRENCY)
│  │
│  └─ per territory: regions loop (1 region, or 4 quadrants if > 1 M ha)  ← SERIAL
│     │
│     ├─ FETCH  ─ all independent EE analyses issued together via asyncio.gather
│     │           (MapBiomas y1 · y2 · comparison · GLAD · GFC ·
│     │            the same five for the buffer ring · multi-window ×2)
│     │           → up to 11 concurrent requests per region
│     │
│     └─ RENDER ─ figures + section writers            ← serialized globally
│
├─ PNG maps (matplotlib)                               ← serialized globally
└─ Deforestation timeline (plotly/kaleido)             ← serialized globally
```

### Level 1 — territories in parallel

Workers pull from an `asyncio.Queue` rather than taking a pre-sliced chunk.
Territory sizes vary by more than an order of magnitude, so chunking would
strand a worker behind one 2 M ha quadrant-split territory while others idle.

### Level 2 — all EE analyses of a region at once

Every analysis in a region reads the same geometry and writes its own result
slot; none consumes another's output. They are issued in one `asyncio.gather`,
collapsing the region's wall time from the *sum* of the calls to the *slowest
single one*.

One subtlety: the comparison step used to be gated on both MapBiomas years
returning non-empty data, which cannot be known before they return. The gate is
now re-applied **after** the gather (the result is discarded if either year came
back empty), so the output is byte-identical to the serial version.

### Level 3 — quadrants: deliberately still serial

Quadrant-split territories process their four regions one after another. This is
*intentional*, not an oversight: with 3–4 territories in flight the EE pool is
already saturated (4 × 11 = 44 requests contending for 12 slots), so
parallelising quadrants would add scheduling complexity and peak memory while
delivering no extra throughput. It would only help a single huge territory
running alone at the tail of a queue. See [Future work](#9-future-work).

---

## 3. How the limits are enforced

Bounding uses **sized `ThreadPoolExecutor`s, not asyncio semaphores**. An
executor with N workers already queues everything past the Nth submission, and
unlike a semaphore it has no event-loop affinity — the same pool survives across
Reflex background tasks.

| Pool | Size | Purpose |
|---|---|---|
| `get_ee_executor()` | `EE_REQUEST_CONCURRENCY` | Every Earth Engine call, via `_ee_with_retry` |
| `get_render_executor()` | **1 (fixed)** | Every kaleido/pyplot path, via `_render` |

Two things this replaced, both of which mattered:

* **`run_in_executor(None, …)`** — asyncio's default executor is sized
  `min(32, cpu_count + 4)`, i.e. only **6 threads** on a 2-vCPU Cloud Run
  instance, and it is shared with every other blocking call in the app. Fanning
  out 11 requests onto it would have silently capped at 6 and starved everything
  else.
* **EE's HTTP connection pool** — `ee.data` issues all Cloud API calls through a
  single shared `requests.Session` carrying urllib3's stock adapter, capped at
  **10 connections per host**. Past the cap urllib3 does not block: it opens a
  throwaway connection, pays a fresh TLS handshake, discards it, and logs
  `Connection pool is full` for every call. `tune_ee_connection_pool()` mounts a
  wider adapter (`EE_REQUEST_CONCURRENCY + 4`) right after EE init. It reaches
  into `ee.data` internals, so every failure path is non-fatal — the run just
  falls back to the default pool with more handshakes.

Retry backoff (`_ee_with_retry`) sleeps **outside** the executor, so a retrying
call never holds a worker slot.

---

## 4. Tier profiles

Defined in `ee_concurrency.py`:

| Profile | Territories in parallel | …for *heavy* runs | Max in-flight EE requests |
|---|---|---|---|
| `partner` *(current default)* | 4 | 3 | 12 |
| `contributor` | 1 | 1 | 4 |

**Why territories can exceed the core count.** These workers are waiting on the
network, not competing for CPU. Rendering is serialized, so at most *one*
territory holds figures and map PNGs at any moment; the others sit in
`getInfo()` holding only their fetched result dicts — class histograms, measured
in kilobytes. And on Cloud Run `uploaded_files/exports/` is a **GCS FUSE
volume** (`GCS_EXPORT_BUCKET`), so the bytes a run *writes* never enter the
container's memory budget at all. A 2 vCPU container comfortably carries 4
in-flight territories.

**Why `contributor` keeps territory-level parallelism at 1:** with a narrow
request budget, running several territories at once only spreads the same
throughput over a longer wall time while multiplying peak memory. Step-level
fan-out (level 2) still applies — 4 concurrent requests sat comfortably inside
the free-tier budget in practice — so a contributor-tier run is still faster
than the fully serial pipeline this replaced.

### Per-run trimming

`effective_territory_concurrency(n, heavy)` narrows the width by one for *heavy*
runs — PNG maps, deforestation timeline, or buffer analysis enabled — since
those hold more live figures per territory and lengthen the render queue. It is
a modest trim, not a hard clamp, for the reasons above.

Setting `YVY_BATCH_TERRITORY_CONCURRENCY` explicitly **disables the trim**: if
someone pinned the width to benchmark it, silently halving it would make the
benchmark meaningless.

The width is also clamped to the number of selected territories, so a 1-item run
never spawns idle workers.

---

## 5. Tuning

All knobs are environment variables — **no code change and no redeploy of new
code is needed**, only a service update.

| Variable | Default | Effect |
|---|---|---|
| `YVY_EE_TIER` | `partner` | Selects a profile (`partner` \| `contributor`). Unknown values warn and fall back to `partner`. |
| `YVY_BATCH_TERRITORY_CONCURRENCY` | from profile | Overrides territories-in-parallel. Wins over the profile. |
| `YVY_BATCH_EE_CONCURRENCY` | from profile | Overrides max in-flight EE requests. Wins over the profile. |

Non-integer or `< 1` values are rejected with a warning and the default is used,
so a typo degrades to the safe setting rather than breaking the run.

Render concurrency is **not** exposed. It is a correctness constraint of
kaleido 0.2.1 and pyplot, not a performance choice.

The effective budget is logged in the batch log at the start of every run:

```
⚡ Concurrency: 3 territories in parallel · up to 12 Earth Engine requests in flight · rendering serialized (tier=partner)
```

---

## 6. Rollback to Contributor Tier

**When the uplift expires on 2027-02-15**, one command restores the pre-uplift
budget:

```bash
gcloud run services update yvynation \
  --region <REGION> \
  --set-env-vars YVY_EE_TIER=contributor
```

Verify by starting any batch run and reading the first lines of the batch log —
it should say `1 territories in parallel · up to 4 Earth Engine requests in
flight (tier=contributor)`.

To roll back further, to the fully serial pre-concurrency behaviour:

```bash
--set-env-vars YVY_EE_TIER=contributor,YVY_BATCH_EE_CONCURRENCY=1,YVY_BATCH_TERRITORY_CONCURRENCY=1
```

That reduces both pools to a single worker; the `asyncio.gather` still runs but
resolves one call at a time, so behaviour matches the original serial pipeline.

### Symptoms that mean you are over budget

Trim `YVY_BATCH_EE_CONCURRENCY` first — it is the knob that maps to EE quota.
Watch for:

* `Too many concurrent aggregations` / `User memory limit exceeded` from EE
* HTTP **429** or `quota` in the batch log's `⚠ skipped` lines
* Many `⚠ … transient error … retrying` warnings that were not there before

Trim `YVY_BATCH_TERRITORY_CONCURRENCY` instead for **container** problems —
Cloud Run OOM kills, or the instance being evicted mid-run.

---

## 7. Sizing from measurement, not guesswork

Every run meters both pools and reports where the time went — in the batch log,
and under `concurrency` in `batch_summary.json`:

```
📊 Earth Engine pool: 418 calls · busy 71.2% · all 12 slots busy 44.8% · peak 12
📊 Render pool: 96 tasks · busy 63.5% of the run (serialized)
📊 Bottleneck: partly render-bound (63.5%) — more territories still help, but
   only up to about 1.6×. Past that it takes more cores + a multiprocess render pool.
```

Read it like this:

| Reading | Meaning | Action |
|---|---|---|
| **Render busy ≥ 80%** | Render-bound. Rendering is serialized, so its occupancy is a hard ceiling: a stage owning R% of the wall clock caps the whole run at `100/R×`. | More territories will **not** help. Needs more cores **and** a multiprocess render pool — one without the other does nothing. |
| **EE "all slots busy" ≥ 60%** | Territories are queueing for request slots; the tier budget is the constraint. | Raise `YVY_BATCH_EE_CONCURRENCY`. |
| **EE busy high, saturated low** | Latency-bound: slots are free but individual calls are slow. | Raise `YVY_BATCH_TERRITORY_CONCURRENCY` to keep more work in flight. |
| **Neither high** | Time is going elsewhere — geometry loading, file writes, final ZIP compression. | Profile those instead. |

Timing is taken *inside* the worker thread, so a slot counts as busy only while
the request is actually running, not while it waits in the queue behind others.

### Is it worth moving to 4 vCPU?

Only if runs come back **render-bound**, and only together with a multiprocess
render pool ([Future work](#9-future-work) #1). Extra cores on their own change
nothing: `RENDER_CONCURRENCY` is 1 because of kaleido and pyplot global state,
not because of the core count, so a 4-core container would run the exact same
single render thread. The meter tells you which of the two problems you have
before spending anything.

To benchmark widths, pin the value — pinning also disables the *heavy* trim, so
you measure the width you asked for:

```bash
YVY_BATCH_TERRITORY_CONCURRENCY=6 YVY_BATCH_EE_CONCURRENCY=20 <run>
```

Compare `wall_s` and the verdict line across runs on the *same* territory
selection; sizes vary enough that a different selection is not a comparison.

---

## 8. Assessment of the external review notes

`ee_optimal_gpt_batch.md` and `ee_optimal_gemini_batch.md` are LLM-generated
reviews of this pipeline. Their recommendations, checked against the code:

### Adopted

| Recommendation | Notes |
|---|---|
| Fan out independent EE calls per region | Already implemented — see §2 level 2. |
| Serialize kaleido/pyplot | Already implemented — and it is a correctness requirement, not tuning. |
| Widen concurrency now that Partner Tier applies | Done, but to 4 territories / 12 requests, **not** the 80–100 Gemini suggests (see below). |
| Measure before resizing | Implemented as the pool meters, §6. |

### Already true — no change needed

* **"Declare `scale=30` explicitly on GFC/GLAD reductions."** Verified: every
  `reduceRegion` call in `hansen_analysis.py`, `mapbiomas_analysis.py` and
  `ee_service_extended.py` already passes `scale` and `maxPixels` explicitly.
* **"Use stacked reduceRegion in the timeline."** Already the pattern in
  `deforestation_timeline._reduce_stacked`; GPT's own notes acknowledge this.

### Rejected

* **"Scale `effective_territory_concurrency` to 80–100 concurrent slots"**
  (Gemini). This confuses the EE quota with the container. The constraint here
  is 2 vCPU and a serialized render stage — 100 in-flight territories would
  queue 100 render jobs behind one thread and multiply peak RSS for zero
  throughput. The tier uplift widens the *request* budget, which is
  `YVY_BATCH_EE_CONCURRENCY`, and even that is only worth raising when the meter
  reports the pool saturated.
* **"Move to Xee + Dask"** (Gemini). A large new dependency and a rewrite of
  every analysis function, to solve a problem — blocking threads — that a thread
  pool already solves at this scale.
* **"Combine all reducers into one stacked `reduceRegion` per region"** (both).
  Genuinely appealing for EE tile-cache reuse, but it works *against* the
  current design: it trades 11 parallel requests for 1 serial one, and merges 11
  independently retryable calls into a single failure domain where one
  `User memory limit exceeded` loses the whole region. Worth *measuring* if runs
  come back EE-pool-bound; not worth adopting blind.

### Deferred — real, but not free

* **`Export.table.toCloudStorage` instead of `getInfo`** (both, at length). The
  underlying concern is real: `getInfo` has a hard server-side timeout, and very
  large territories can hit it. But that case is already handled by quadrant
  splitting plus `_ee_with_retry`, and async export tasks bring task-queue
  polling, GCS round-trips and a much longer tail latency for every *ordinary*
  territory. Revisit only if large territories start failing after retries.
* **Local Shapely quadrant splitting instead of `ee.Geometry.intersection`**
  (both). The payload argument is sound — complex boundaries are re-uploaded on
  every request. Contained, but not trivial: shapely intersection of a fractured
  boundary with a bbox can yield `MultiPolygon`/`GeometryCollection` needing
  careful handling, and the buffer ring only exists server-side, so buffer
  quadrants would still need EE intersection. Worth doing as its own change.
* **Ingest the GeoPackage as an EE `FeatureCollection` asset** (Gemini). Would
  remove per-request geometry upload entirely — the biggest payload win
  available. Cost is an asset build/sync pipeline and the risk of the asset
  drifting from the local GeoPackage that drives the UI.
* **Skip raster downloads when the statistics came back empty** (Gemini). Small,
  low-risk saving; the maps stage already runs after the fetch stage, so the
  information needed is on hand.

## 9. Future work

### First measurement — the "render" stage is mostly network

A 3-territory run of small conservation units (2026-08-16) reported:

```
📊 Earth Engine pool: 33 calls · busy 1.7% · all 12 slots busy 1.0% · peak 12
📊 Render pool: 9 tasks · busy 98.5% of the run (serialized)
```

The EE pool is essentially idle and the render pool is pegged. But that 98.5%
is **not** CPU — it is sequential HTTP, serialized behind a lock that exists
only for matplotlib. In `map_export_service`:

* `get_basemap_image()` walks the tile grid with a nested loop doing one
  blocking `requests.get(url, timeout=10)` per tile. A 6×6 grid is 36
  round-trips, one after another.
* **Nothing is cached.** `create_map_set()` calls `create_pdf_map()` once per
  layer (satellite, MapBiomas y1, MapBiomas y2, Hansen, each aux layer) and
  every one of them re-fetches the *same* basemap tiles for the *same* bounds.
  Four maps over a 6×6 grid is ~144 sequential tile requests per territory.
* `get_ee_layer_image()` adds `region.getInfo()` plus
  `image.getDownloadURL()` plus a `requests.get(…, timeout=60)`, also under the
  lock.

So the fix order below is driven by that measurement, not by the theory that
rendering is CPU-bound. **More cores would have bought almost nothing.**

### Ordered by expected value

1. **Cache basemap tiles per (bounds, zoom).** All of a territory's maps share
   one footprint, so this alone removes most of the redundant fetches. Smallest
   change, largest win.
2. **Fetch tiles concurrently.** The nested loop is pure I/O with no shared
   state — a thread pool over the grid turns 36 sequential round-trips into a
   handful of batches. Safe: no matplotlib involved.
3. **Move raster fetching out of the render lock.** Prefetch the EE layer PNGs
   and basemap composites on the EE pool, then hand finished images to the
   serialized matplotlib step. Only the compositing genuinely needs the lock.
4. **Render in a process pool.** Worth revisiting only *after* 1–3, once the
   render stage is actually CPU-bound. Two worker processes would each get their
   own kaleido scope and pyplot state. Plotly figures are picklable; the
   matplotlib map path is not (it holds live `ee.Geometry` objects), so this
   works for charts before maps. **This is also the point at which 4 vCPU starts
   to pay** — not before.
5. **Upgrade kaleido to 1.x**, which is not built around a global scope — but it
   delegates to an external Chrome install, which is why it is pinned at 0.2.1
   today (see `requirements.txt`).
6. **Parallelise quadrants** — only worth doing after (4), and only pays off for
   a single large territory running alone.
7. **The high-volume EE endpoint** (`earthengine-highvolume.googleapis.com`) is
   built for many small parallel requests. It is *not* a drop-in win here: it
   applies tighter per-request compute limits, and this pipeline's heavy
   `reduceRegion` calls over million-hectare territories are exactly what it
   handles worse. Would need per-call routing (small territories → high-volume,
   large → standard) to be worth it.

---

## 10. Verification

`_batch.py` orchestration is covered by a harness that fakes Earth Engine, the
geometry services, and the chart writers, then asserts on real instrumented
thread behaviour:

* every selected territory processed exactly once, no duplicates
* EE fan-out actually occurs, and peak concurrency never exceeds the tier budget
* render work is strictly serialized — peak 1, single thread
* `batch_stop` drains the queue, lets in-flight territories finish, and still
  produces a downloadable ZIP
* measured speedup vs. the serial call count

Not covered by the harness: the PNG-map (matplotlib) and deforestation-timeline
paths. Both route through the same `_render` helper as the section writers that
*are* covered, so their serialization follows from the same single-worker pool —
but their EE-side behaviour under load has not been exercised in a test.
