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
CPU-bound, and **must run one at a time per library**:

* `kaleido==0.2.1` drives one module-global headless renderer
  (`plotly.io._kaleido.scope`) over a single pipe. Concurrent `fig.to_image()`
  calls from different threads interleave on that pipe and deadlock or return
  truncated PNGs.
* `map_export_service` uses the `pyplot` state machine (global current
  figure/axes), which is likewise not thread-safe.

*Per library* is the operative part: those two globals are unrelated, so the
work divides into two independent **render lanes** that run concurrently with
each other while staying strictly serial inside (§3). Widening EE fetches does
not require widening rendering, and widening a single lane is not an option
without changing that dependency. The throughput win comes from **pipelining**:
while one territory renders, the others are waiting on Earth Engine — and a
second territory can render in the other lane meanwhile.

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
│     └─ RENDER ─ figures + section writers            ← kaleido lane (serial)
│
├─ map rasters: EE layer PNGs + basemap tiles, in parallel   ← NOT locked
├─ PNG maps (matplotlib compositing only)              ← matplotlib lane (serial)
└─ Deforestation timeline (plotly/kaleido)             ← kaleido lane (serial)

   the two lanes run CONCURRENTLY with each other
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
| `get_io_executor()` | `IO_CONCURRENCY` | Blocking work that is neither: GeoPackage reads, buffer construction, boundary/summary writes, map prefetch, the final ZIP |
| `get_render_executor("kaleido")` | `lane_width("kaleido")` — cores, capped at 8 | Plotly → PNG: charts, deforestation timeline. One `PlotlyScope` (and Chrome) per thread |
| `get_render_executor("matplotlib")` | `lane_width("matplotlib")` — cores, capped at 4 | Map composition (`map_export_service`), via `Figure` + `FigureCanvasAgg` |

### Render lanes: one per thread-unsafe library

The serialization requirement is **per library, not global**. kaleido's global is
`plotly.io._kaleido.scope`; pyplot's is its current-figure state machine; they
are unrelated. And the call sites divide cleanly — charts and the timeline are
pure Plotly→PNG, while map composition never touches Plotly (`map_export_service`
is the only pyplot user in the whole codebase).

A single shared render lock therefore made one territory's **maps block another
territory's charts for no reason at all**. Splitting it into one single-worker
pool per library means different territories *do* render simultaneously today,
as long as they are in different lanes — no library change, no process pool, no
pickling.

Route by **the library the work reaches**, never by which call site it is:
sending pyplot work into the kaleido lane would silently permit two concurrent
pyplot renders. An unknown lane name falls back to an existing pool rather than
minting a new one, so a typo cannot hand out a second worker for a library that
cannot take one.

Widening a *single* lane past 1 still needs that library fixed — see
[Future work](#9-future-work).

The I/O pool must stay **distinct from** the EE pool, not merely wide enough.
Map prefetch runs on it and submits its rasters to the EE pool, then blocks on
them; sharing one pool deadlocks as soon as enough territories are in flight.

Two things this replaced, both of which mattered:

* **`run_in_executor(None, …)`** — asyncio's default executor is sized
  `min(32, os.cpu_count() + 4)`, i.e. only **6 threads** on a 2-vCPU Cloud Run
  instance, and it is shared with every other blocking call in the app. Fanning
  out 11 requests onto it would have silently capped at 6 and starved everything
  else. `get_io_executor()` now covers the non-EE blocking calls too — with 8
  territory workers the default executor would have become the binding
  constraint, moving the queue from Earth Engine to GeoPackage reads rather than
  removing it. (`os.cpu_count()` also reports the *host's* cores inside a
  container rather than the cgroup limit, so the default size is not even
  reliably 6 — another reason to state the number.)
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

Profiles are **scaling rules, not fixed numbers.** Yvynation is open source and
runs on very different machines — Cloud Run at 2 vCPU / 8 GiB, or a 20-core
workstation. Hardcoding the container's numbers would leave most of a
workstation idle, so the width is derived from the CPU and memory actually
available:

```
territories = clamp(territories_per_cpu × cpus,
                    (memory_gib − 1) / 0.35,      ← memory bound
                    territories_max)
heavy       = territories × heavy_ratio
ee_requests = min(ee_per_territory × territories, ee_max)
io          = max(8, territories + 4)
```

| Profile | per CPU | cap | heavy ratio | EE per territory | EE cap |
|---|---|---|---|---|---|
| `partner` *(default)* | 4.0 | 16 | 0.75 | 3 | 64 |
| `contributor` | — | 1 | 1.0 | 4 | 4 |

Which lands as:

| Machine | Territories | …heavy | EE requests | I/O |
|---|---|---|---|---|
| Cloud Run 2 vCPU / 8 GiB | 8 | 6 | 24 | 12 |
| 4 cores / 16 GiB | 16 | 12 | 48 | 20 |
| 20 cores / 64 GiB | 16 | 12 | 48 | 20 |
| 20 cores / **2 GiB** | 2 | 2 | 6 | 8 |
| any, `contributor` | 1 | 1 | 4 | 8 |

**Detection is cgroup-aware.** `os.cpu_count()` reports the *host's* cores
inside a container — on Cloud Run it can read far higher than the 2 vCPU the
service is allowed — so `detect_cpus()` reads the cgroup v2 `cpu.max` (then v1
`cpu.cfs_quota_us`) and takes the lower. `detect_memory_gib()` does the same
with `memory.max`. Both fall back to the host figure when unconstrained. The
detected values are logged with the budget and recorded in `batch_summary.json`
under `concurrency.machine`, so a run's numbers are reproducible from its log.

**Why territories can exceed the core count.** These workers are waiting on the
network, not competing for CPU. Rendering is serialized, so at most *one*
territory holds figures and map PNGs at any moment; the others sit in
`getInfo()` holding only their fetched result dicts — class histograms, measured
in kilobytes. And on Cloud Run `uploaded_files/exports/` is a **GCS FUSE
volume** (`GCS_EXPORT_BUCKET`), so the bytes a run *writes* never enter the
container's memory budget at all. The final ZIP is likewise built with
`zip_directory()`, which streams file-by-file to disk rather than through a
`BytesIO` — archive size does not enter the memory budget either.

### Calibration, 2026-08-16 (previously a fixed 4 / 3 / 12)

A 31-territory production run on Cloud Run (2 vCPU / 8 GiB) at the old fixed
width measured:

| Resource | Observed | Available | Utilisation |
|---|---|---|---|
| Container memory | ~1.5 GiB | 8 GiB | < 20% |
| Container CPU | ~0.8 vCPU | 2 vCPU | < 40% |
| EE requests | 38/min avg, ~80 peak | 6000/min quota | < 1.5% |

Every dimension had a large multiple of headroom. `territories_per_cpu = 4.0` is
set so that container reproduces **8 / 6 / 24 / 12**, and everything else scales
from that anchor.

**Do not read the quota headroom as licence to keep raising this.** 6000/min
divided by 80 says 75×, but the run cannot use it. The same run came back
**render-bound at 80.1%**, and rendering is serialized — so the ceiling is
`100 / render_busy_pct` ≈ **1.2×** no matter how many territories are in
flight. Widening the fan-out is nearly free, but on its own it is nearly
worthless too. See §7.

**Why `contributor` keeps territory-level parallelism at 1:** with a narrow
request budget, running several territories at once only spreads the same
throughput over a longer wall time while multiplying peak memory. Step-level
fan-out (level 2) still applies — 4 concurrent requests sat comfortably inside
the free-tier budget in practice — so a contributor-tier run is still faster
than the fully serial pipeline this replaced.

### Per-run trimming

`effective_territory_concurrency(n, heavy)` narrows the width for *heavy* runs —
PNG maps, deforestation timeline, or buffer analysis enabled — since those hold
more live figures per territory and lengthen the render queue. It is a modest
trim (`heavy_ratio`, 0.75 → 8 becomes 6), not a hard clamp, for the reasons
above.

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
| `YVY_BATCH_IO_CONCURRENCY` | `max(8, territories + 4)` | Overrides the non-EE blocking pool. Raise alongside the territory width; it must stay ≥ it. |

Non-integer or `< 1` values are rejected with a warning and the default is used,
so a typo degrades to the safe setting rather than breaking the run.

Render concurrency is **not** exposed. One worker per lane is a correctness
constraint of kaleido 0.2.1 and pyplot, not a performance choice — a lane can
only widen once its library is fixed (§9).

The effective budget is logged in the batch log at the start of every run:

```
⚡ Concurrency: 6 territories in parallel · up to 24 Earth Engine requests in flight · 12 I/O slots · rendering serialized (tier=partner, 2 cores / 8 GiB detected)
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
   only up to about 1.6×. Past that a render lane has to be widened (see the render split).
```

Read it like this:

| Reading | Meaning | Action |
|---|---|---|
| **Any lane busy ≥ 80%** | Render-bound. Each lane is serialized, so occupancy is a hard ceiling: a stage owning R% of the wall clock caps the whole run at `100/R×`. | More territories will **not** help. Widen a lane (§9 #1); more cores only pay once one is widened. |
| **All lanes at once, low** | The lane split is not paying — one library owns nearly all the render time and the other lane idles. | Read the render split and widen the dominant lane; ignore the other. |
| **EE "all slots busy" ≥ 60%** | Territories are queueing for request slots; the tier budget is the constraint. | Raise `YVY_BATCH_EE_CONCURRENCY`. |
| **EE busy high, saturated low** | Latency-bound: slots are free but individual calls are slow. | Raise `YVY_BATCH_TERRITORY_CONCURRENCY` to keep more work in flight. |
| **Neither high** | Time is going elsewhere — geometry loading, file writes, final ZIP compression. | Profile those instead. |

Timing is taken *inside* the worker thread, so a slot counts as busy only while
the request is actually running, not while it waits in the queue behind others.

### Measured: 31 territories, Cloud Run 2 vCPU / 8 GiB, 2026-08-16

```
📊 Earth Engine pool: 612 calls · busy 9.8% · all 12 slots busy 0.1% · peak 12
📊 Render pool: 96 tasks · busy 80.1% of the run (serialized)
📊 Bottleneck: render-bound (80.1% of the run) — ceiling is 1.2×
🗜 Final ZIP: 644 MB, 10.6 minutes
```

Three things fall out of this, and they matter more than any knob:

1. **The Earth Engine pool is nearly idle** — 9.8% busy, all slots busy 0.1% of
   the run. `EE_REQUEST_CONCURRENCY` was never the constraint, and raising it
   buys nothing directly. (It is still raised, so that it is not the *next*
   constraint once rendering parallelises.)
2. **Rendering owns the run and cannot be widened**, so the total headroom from
   territory-level fan-out is `100/80.1` ≈ **1.2×**. Everything in §4 about
   scaling with the machine is real but capped here until rendering changes —
   on a 20-core workstation the run does **not** get 10× faster.
3. **The ZIP was 10.6 minutes** — ~1 MB/s for 644 MB. That is per-file latency
   on the GCS FUSE mount (~1500 small files, each a round trip to GCS), not
   compression. `zip_directory()` now overlaps those reads across
   `IO_CONCURRENCY` readers and stores already-compressed files (PNG/JPEG/PDF)
   instead of deflating them. Writes stay sequential, so archives are unchanged.

Note the meters are snapshotted **before** the ZIP, so the percentages describe
the analysis phase; the ZIP is timed separately in the completion line.

### First lever taken: split the render lock

That measurement was taken with **one** render lock covering both libraries. It
is now two lanes (§3), so a territory's charts and another territory's maps
overlap. The meter reports the overlap directly:

```
📊 Render lanes (2): 96 tasks · any lane busy 80.1% of the run · all lanes at once …%
```

* **"any lane busy"** is the ceiling driver — the run can be sped up at most
  `100 / that` by parallelism alone.
* **"all lanes at once"** says whether the split paid. High overlap means the
  two libraries genuinely interleave. Low overlap with high occupancy means one
  library dominates, the other lane is mostly idle, and widening *that* library
  is the whole game. The verdict line now says which of those it saw.

### Third lever taken: EE work out of the render lane

The `timeline` lane read 38.6% (803.5 s, **44.6 s per territory**) — but its ~6
charts render in about 1 s. The rest was `collect_timeline()` issuing
`reduceRegion(...).getInfo()` **from inside the render closure**: holding the
kaleido lane for every network round trip, and bypassing the EE pool entirely,
which is why the EE meter read 3.6% busy while the network sat near idle.

The series are now fetched by `_timeline_specs()` + `asyncio.gather` on the EE
pool *before* the lane is entered — same shape as `prefetch_map_inputs()`. Two
properties worth keeping:

* **One source of truth for the keys.** `_timeline_specs()` is what the prefetch
  walks; the writer builds `("t", rname)` / `("b", rname)` to match. The map
  prefetch drifted exactly this way before `_raster_specs` existed.
* **A miss is slow, never wrong.** If a key is absent — partial prefetch, EE
  outage — the writer fetches inline as before. Covered by a test that fails EE
  calls *only* on pool threads and asserts the charts still appear.

### FIFO pools: submit a territory's work in one batch

Observed on a 25-territory run: the first group of territories all sat at
"deforestation timeline" until the stragglers had run *their* MapBiomas and
Hansen, then finished in a burst — and the next group repeated it.

There is no barrier in the code. Workers pull from an `asyncio.Queue` with
`get_nowait()` and never await each other. The cause was **FIFO ordering in the
shared EE pool**: the timeline series were fetched in a *second* round, after
the per-region fan-out. By the time a nearly-finished territory submitted those
two calls, the queue already held every job of every territory that had started
since — so its last request waited behind newcomers' first ones.

The fix is ordering, not capacity: the timeline series now go out **in the same
`jobs` list** as MapBiomas and Hansen. This was possible because the dependency
was only apparent — `hansen_loss_series()` is pure reshaping of the `gfc` result
already fetched in that batch, so it is merged in locally afterwards and no EE
call has to wait for another.

**The general rule: a territory should submit everything it needs in one batch.**
Any dependent second round re-queues it behind work that started later, which is
what turns independent territories into a group that finishes together.

Note this is separate from fair-share interleaving, which is *not* a bug: N
territories sharing the pools each advance at ~1/N speed, so they naturally
arrive at stages together. `concurrency.stages.concurrent_fraction` in
`batch_summary.json` distinguishes them — near `territory_workers` means healthy
overlap; the per-stage seconds show where the time actually went.

### Which half of the render stage?

The two libraries behind the render lock are independent and need different
fixes, so the aggregate figure is not actionable — 80.1% does not say *what to
change*. Every `_render()` call is therefore labelled by call site, and the
split is reported at the end of a run (format only — **the shares below are
placeholders; the first run after this change supplies the real ones**):

```
📊 Render split: maps (pyplot) …% (n×, …s) · charts (kaleido) …% · timeline (kaleido) …%
```

Read it as a fork:

* **pyplot-dominated** → the fix is contained: `map_export_service` can move off
  the `pyplot` state machine to explicit `Figure` + `FigureCanvasAgg` objects,
  which *are* thread-safe, and the map path alone can then be widened.
* **kaleido-dominated** → threads cannot help at all; it needs a process pool or
  a kaleido upgrade ([Future work](#9-future-work) #1).

### Is it worth moving to 4 vCPU?

Only together with a widened render lane. Extra cores on their own change
nothing: each lane is one worker because of kaleido and pyplot global state, not
because of the core count, so a 4-core container would run the same two render
threads. The lane split (§3) is what makes those two overlap; going past two
needs §9 #1. This is also why the machine-scaling in §4 is not a
substitute — a bigger box widens the fan-out that the meter says is already
idle. Read the render split first, then spend.

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
| Widen concurrency now that Partner Tier applies | Done, and widened again on 2026-08-16 to 8 territories / 24 requests after measuring the container — still nowhere near the 80–100 Gemini suggests (see below). |
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
  `YVY_BATCH_EE_CONCURRENCY`. The 2026-08-16 widening to 8/24 came from
  measuring the container, and it is the same reasoning that stops there: the
  quota alone would justify far more, and the quota alone is not the limit.
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

### Done in response to that measurement

1. **Basemap tiles are cached** per `(provider, zoom, x, y)` in a bounded LRU
   (`YVY_TILE_CACHE_TILES`, default 1024). All of a territory's maps share one
   footprint, so the repeat fetches are gone — and the cache is keyed by tile,
   not by map, so it also pays off across neighbouring territories.
2. **Tiles are fetched concurrently** on a dedicated pool
   (`YVY_TILE_FETCH_WORKERS`, default 8). Measured 5.2× on a 12-tile grid.
3. **Raster fetching happens before the render lock is taken.**
   `prefetch_map_inputs()` downloads every EE layer PNG (on the shared EE pool,
   so it stays inside the tier budget and shows up in the metering) and the
   basemap composite, concurrently. `create_map_set(prefetched=…)` then does
   pure compositing. The batch pipeline runs the prefetch on the *default*
   executor — never the EE pool, since it submits to that pool and blocks on
   the results, and a task that waits on its own pool deadlocks once enough of
   them run at once.

`create_map_set()` still works with no prefetch (fetching inline, as before),
so nothing else that calls it had to change.

### Second measurement — now it really is the render stage

The 31-territory run above (§7) re-ran the same meters after those three fixes:
render fell from **98.5% → 80.1%**, and the EE pool went from 1.7% to 9.8% busy
over 612 calls. The remaining 80% is no longer hidden network I/O — the tiles
and rasters are fetched before the lock now — so this time it *is* CPU, and it
is the thing to fix next. Two things follow:

* Widening territories or EE requests is nearly exhausted as a lever (1.2×).
  §4's machine-scaling is still worth having — it is free, and it stops the EE
  pool becoming the next wall — but it is not what makes runs faster from here.
* The render split (§7) decides between the two fixes below, and it is cheap to
  read: it lands in the next run's log and in `batch_summary.json`.

### Still ordered by expected value

0. **Split the render lock per library** — *done*, see §3. Free, and it already
   lets different territories render concurrently in different lanes.

0b. **Hoist Earth Engine work out of the render lanes** — *done* for the
   timeline (§7). Worth re-checking whenever a writer grows a new data
   dependency: anything issuing `getInfo()` under a render lane serializes the
   whole batch behind one network round trip *and* hides from the EE meter.

0c. **Figure export is now run-scoped** (`export_service.figure_export()`).
   Batch runs can skip PNGs entirely or drop to scale 0.6; the interactive
   geometry/territory exports pin `png_enabled=True` and keep print quality.
   PNGs were 449 MB of a 503 MB archive but only ~4% of its run time — this is a
   **space** lever, not a speed one. Measured: complex charts at 1600x1000 take
   38-82 ms each in kaleido 0.2.1, so 1494 of them are ~90 s of a 2028 s run.
   Upgrading kaleido is capped by that same ~4%.

1. **Widen the lanes past one worker** — *done for both*. Neither needed a
   process pool; in both cases the fix was to stop using a module-global.
   * **kaleido** — `fig.to_image()` uses the global `plotly.io._kaleido.scope`.
     A `PlotlyScope` *instance* owns its own Chrome, so `export_service` keeps
     one per thread (`threading.local`) and the shared state disappears. Output
     is byte-identical; the Python thread waits on its pipe with the GIL
     released while Chrome works in a separate process, so N threads use N
     cores. Measured 3.4x on 4 threads. Guarded by `scoped_kaleido_available()`
     — if per-thread scopes fail, the lane drops back to one worker rather than
     letting concurrent callers onto the shared global.
   * **matplotlib** — `map_export_service` had only *three* pyplot calls
     (`subplots`, `tight_layout`, `close`). Replacing them with `Figure` +
     `FigureCanvasAgg` removes the current-figure global entirely. Verified
     byte-identical to serial composition, with no cross-thread mixing. Narrower
     than kaleido because this is real in-process CPU under the GIL.

   The lanes made this incremental: each was widened without disturbing the
   other, and neither needed the territory workers to change.
2. **Upgrade kaleido to 1.x**, which is not built around a global scope — but it
   delegates to an external Chrome install, which is why it is pinned at 0.2.1
   today (see `requirements.txt`).
3. **Parallelise quadrants** — only worth doing after (1), and only pays off for
   a single large territory running alone.
4. **The high-volume EE endpoint** (`earthengine-highvolume.googleapis.com`) is
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
* render work is serialized *within* a lane — peak 1, one named lane thread
* the lanes themselves: distinct pools, one worker each, an unknown lane falls
  back instead of minting a pool, no two same-lane renders overlap, and the two
  lanes **do** overlap (the property that lets territories render in parallel)
* `batch_stop` drains the queue, lets in-flight territories finish, and still
  produces a downloadable ZIP (the width is pinned for that check — with a pool
  wider than the selection, every territory is already "current" when the flag
  flips, so the assertion would be vacuous on a big machine)
* measured speedup vs. the serial call count
* the budget plan across machine shapes: the Cloud Run anchor (8/6/24/12), a
  20-core box scaling up but staying under the cap, a small box scaling down,
  memory bounding it when cores are plentiful, and `contributor` pinned at 1
* render time is attributed to labelled call sites and the shares sum to 100%

`zip_directory()` has its own harness that fakes FUSE latency with a sleep and
asserts the reads overlap while the archive stays byte-identical, sorted,
traversal-free, mtime-preserving, and valid to a plain reader — plus that a read
failure propagates rather than silently truncating the archive.

Not covered by the harness: the PNG-map (matplotlib) and deforestation-timeline
paths. Both route through the same `_render` helper as the section writers that
*are* covered, so their serialization follows from the same single-worker pool —
but their EE-side behaviour under load has not been exercised in a test.
