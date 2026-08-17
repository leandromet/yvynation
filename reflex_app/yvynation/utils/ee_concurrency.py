"""
Concurrency budget for the batch pipeline.

The batch run has two very different kinds of work and they must be scheduled
differently:

**Earth Engine fetches** (``analyze_mapbiomas``, ``get_area_distribution``,
``analyze_gfc``, ``compute_transitions``…) are network-bound. The thread sits
in ``getInfo()`` waiting on EE's compute backend with the GIL released, so many
can be in flight at once without touching the container's CPU. This is the work
the Partner Tier uplift lets us widen.

**Rendering** (Plotly → PNG via kaleido, Matplotlib map composition) is CPU-bound
and constrained by *module-global* state in both libraries — but the two globals
are unrelated, so rendering is split into one **lane** per library
(:data:`RENDER_POOLS`), which run concurrently with each other:

* **kaleido** — ``fig.to_image()`` drives one module-global ``PlotlyScope``
  (``plotly.io._kaleido.scope``) over a single pipe, so concurrent calls
  interleave and deadlock or truncate. ``export_service`` instead gives each
  thread its **own** ``PlotlyScope`` (hence its own Chrome), which removes the
  shared state entirely — so this lane runs several workers wide. Guarded by
  ``scoped_kaleido_available()``: if per-thread scopes are unavailable the
  fallback uses the shared global, and the lane drops back to one worker.
* **matplotlib** — ``map_export_service`` builds ``Figure`` +
  ``FigureCanvasAgg`` objects directly instead of going through ``pyplot``, so
  there is no current-figure global either, and this lane also runs several
  wide. It is narrower than kaleido because the drawing is real in-process CPU
  under the GIL, where kaleido's work happens in a separate Chrome process.

Lane widths come from :func:`lane_width`; :func:`render_capacity` is their sum,
and is what the render meter measures "saturated" against. The remaining win
comes from *pipelining*: while one territory renders, the others fetch from
Earth Engine.

Anything that reaches Earth Engine must be fetched **before** a render lane is
entered. A ``getInfo()`` under a render lane holds that lane for a whole network
round trip and never appears in the EE meter — see ``prefetch_map_inputs()`` and
the timeline prefetch in ``_batch.py``.

Bounding is done with sized ``ThreadPoolExecutor``s rather than asyncio
semaphores — an executor with N workers already queues everything past the Nth
submission, and unlike a semaphore it carries no event-loop affinity, so the
same pool is reusable across Reflex's background tasks.


Tier profiles
-------------

Sized for the Earth Engine **Partner Tier** uplift (granted 2026-08-15, expires
**2027-02-15**) on Cloud Run with 2 vCPU / 8 GiB.

To roll back to the pre-uplift budget when the uplift expires, set one env var
on the Cloud Run service — no code change::

    gcloud run services update yvynation --set-env-vars YVY_EE_TIER=contributor

Individual knobs can also be overridden directly
(``YVY_BATCH_TERRITORY_CONCURRENCY``, ``YVY_BATCH_EE_CONCURRENCY``); they win
over the tier profile. See ``docs/BATCH_CONCURRENCY.md`` for the full rationale,
the measurement procedure, and the rollback checklist.
"""

import logging
import os
import threading
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier profiles
# ---------------------------------------------------------------------------

#: ``territories``  — how many territories are processed at the same time.
#: ``heavy``        — the same, for runs with PNG maps / timeline / buffer on.
#: ``ee_requests``  — ceiling on simultaneous in-flight Earth Engine calls,
#:                    summed across every territory and quadrant in flight.
#:
#: Profiles are **scaling rules, not fixed numbers**. Yvynation is open source
#: and runs on very different machines: Cloud Run at 2 vCPU / 8 GiB, and
#: workstations with 20 cores and plenty of RAM. Hardcoding the container's
#: numbers would leave most of a workstation idle, so the width is derived from
#: the CPU and memory actually available (see :func:`detect_cpus` /
#: :func:`detect_memory_gib` — both cgroup-aware, so a container gets its own
#: limit rather than the host's).
#:
#: ``territories_per_cpu``  — in-flight territories per available core.
#: ``territories_max``      — cap; past this, extra workers only lengthen queues.
#: ``heavy_ratio``          — multiplier for runs with PNG maps / timeline / buffer.
#: ``ee_per_territory``     — request slots to keep each worker fed.
#: ``ee_max``               — tier ceiling on simultaneous requests.
#:
#: **Why territories can exceed the core count:** these workers wait on the
#: network, not on CPU. Only the few territories currently in a render lane hold
#: figures; the rest sit in ``getInfo()`` holding kilobyte-sized result dicts. On
#: Cloud Run ``uploaded_files/exports/`` is a GCS FUSE volume, so written output
#: never enters the memory budget either.
#:
#: **Calibration (2026-08-16)** — a 31-territory production run on Cloud Run
#: (2 vCPU / 8 GiB) at the previous fixed 4/3/12 measured memory < 20% of 8 GiB,
#: CPU < 40% of 2 vCPU, and Earth Engine at 38 req/min average (~80 peak)
#: against a **6000/min** quota — under 1.5%. Every dimension had a large
#: multiple of headroom. ``territories_per_cpu = 4`` reproduces 8/6/24 on that
#: container and scales from there.
#:
#: Do **not** read the quota headroom as licence to keep raising these. The same
#: run came back *render-bound*: once rendering dominates, the ceiling is
#: ``100 / render_busy_pct`` no matter how wide the territory fan-out — widening
#: a render lane is the lever there, not this profile. Size from a meter reading
#: (§6 of ``docs/BATCH_CONCURRENCY.md``), not from quota.
#:
#: ``contributor`` pins territories to 1 regardless of the machine: with a narrow
#: request budget, running several at once only spreads the same throughput over
#: a longer wall time. Step-level fan-out still applies.
_PROFILES = {
    "partner": {
        "territories_per_cpu": 4.0,
        "territories_max": 16,
        "heavy_ratio": 0.75,
        "ee_per_territory": 3,
        "ee_max": 64,
    },
    "contributor": {
        "territories_per_cpu": 0.0,   # → clamps to 1
        "territories_max": 1,
        "heavy_ratio": 1.0,
        "ee_per_territory": 4,
        "ee_max": 4,
    },
}

#: Rough peak RSS per in-flight territory, plus a base for the app itself.
#: Mostly just the fetched result dicts per territory, so this is deliberately
#: generous. (Kaleido lane workers carry their own Chrome; that is budgeted
#: separately in :func:`_kaleido_lane_width`.)
_GIB_PER_TERRITORY = 0.35
_GIB_BASE = 1.0

_DEFAULT_TIER = "partner"


# ---------------------------------------------------------------------------
# Resource detection — cgroup-aware, so a container sees its own limit
# ---------------------------------------------------------------------------

def _read_first(*paths) -> Optional[str]:
    for p in paths:
        try:
            with open(p) as fh:
                return fh.read().strip()
        except (OSError, ValueError):
            continue
    return None


def _cgroup_cpu_limit() -> Optional[float]:
    """CPU quota in cores from cgroup v2 then v1, or None if unlimited."""
    raw = _read_first("/sys/fs/cgroup/cpu.max")          # v2: "<quota> <period>"
    if raw:
        parts = raw.split()
        if len(parts) == 2 and parts[0] != "max":
            try:
                return int(parts[0]) / int(parts[1])
            except (ValueError, ZeroDivisionError):
                pass
    quota = _read_first("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")   # v1
    period = _read_first("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    try:
        if quota and period and int(quota) > 0:
            return int(quota) / int(period)
    except (ValueError, ZeroDivisionError):
        pass
    return None


def detect_cpus() -> float:
    """Cores actually usable here.

    ``os.cpu_count()`` reports the **host's** cores inside a container, so on
    Cloud Run it can read far higher than the 2 vCPU the service is allowed.
    The cgroup quota is the truth when present.
    """
    host = float(os.cpu_count() or 1)
    limit = _cgroup_cpu_limit()
    return max(1.0, min(limit, host) if limit else host)


def _cgroup_memory_limit() -> Optional[int]:
    raw = _read_first(
        "/sys/fs/cgroup/memory.max",                      # v2
        "/sys/fs/cgroup/memory/memory.limit_in_bytes",    # v1
    )
    if not raw or raw == "max":
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    # v1 reports an enormous sentinel rather than "max" when unlimited.
    return value if 0 < value < (1 << 62) else None


def detect_memory_gib() -> float:
    """Memory actually usable here, in GiB (cgroup limit, else physical)."""
    value = _cgroup_memory_limit()
    if value is None:
        try:
            value = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
        except (OSError, ValueError, AttributeError):
            return 8.0   # unknown platform — assume the Cloud Run shape
    return max(1.0, value / (1024 ** 3))


def _plan(profile: dict, cpus: float, gib: float) -> dict:
    """Derive the concurrency width for one tier on this machine."""
    by_cpu = round(profile["territories_per_cpu"] * cpus)
    by_memory = int((gib - _GIB_BASE) / _GIB_PER_TERRITORY)
    territories = max(1, min(by_cpu, by_memory, profile["territories_max"]))
    heavy = max(1, round(territories * profile["heavy_ratio"]))
    ee = max(
        profile["ee_per_territory"],
        min(profile["ee_per_territory"] * territories, profile["ee_max"]),
    )
    return {
        "territories": territories,
        "heavy": heavy,
        "ee_requests": ee,
        "io": max(8, territories + 4),
    }


def _resolve_tier() -> str:
    tier = os.environ.get("YVY_EE_TIER", _DEFAULT_TIER).strip().lower()
    if tier not in _PROFILES:
        logger.warning(
            f"Unknown YVY_EE_TIER={tier!r} — falling back to {_DEFAULT_TIER!r}. "
            f"Valid values: {', '.join(sorted(_PROFILES))}"
        )
        return _DEFAULT_TIER
    return tier


def _int_env(name: str, default: int) -> int:
    """Positive-int env override, ignoring blanks and garbage."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning(f"{name}={raw!r} is not an integer — using {default}")
        return default
    if value < 1:
        logger.warning(f"{name}={value} must be >= 1 — using {default}")
        return default
    return value


TIER = _resolve_tier()

#: What this machine actually offers. Logged with the budget so a run's numbers
#: can be reproduced from its log alone.
DETECTED_CPUS = detect_cpus()
DETECTED_MEMORY_GIB = detect_memory_gib()

_profile = _plan(_PROFILES[TIER], DETECTED_CPUS, DETECTED_MEMORY_GIB)

#: Territories processed concurrently. See :func:`effective_territory_concurrency`
#: for the per-run value.
TERRITORY_CONCURRENCY = _int_env(
    "YVY_BATCH_TERRITORY_CONCURRENCY", _profile["territories"]
)

#: Width used for output-heavy runs (PNG maps / timeline / buffer). Ignored when
#: ``YVY_BATCH_TERRITORY_CONCURRENCY`` is set explicitly — an operator asking for
#: a specific width should get it rather than being silently trimmed.
HEAVY_TERRITORY_CONCURRENCY = _profile["heavy"]

#: True when the operator pinned the width by hand.
TERRITORY_CONCURRENCY_PINNED = bool(
    os.environ.get("YVY_BATCH_TERRITORY_CONCURRENCY", "").strip()
)

#: Hard ceiling on simultaneous Earth Engine requests (the EE thread pool size).
EE_REQUEST_CONCURRENCY = _int_env(
    "YVY_BATCH_EE_CONCURRENCY", _profile["ee_requests"]
)

#: Rendering is split into one **lane per thread-unsafe library**, each a
#: single-worker pool.
#:
#: The serialization requirement is per-library, not global: kaleido's global is
#: ``plotly.io._kaleido.scope``, pyplot's is its current-figure state machine,
#: and they are unrelated. The batch pipeline's render call sites divide cleanly
#: between them — charts and the deforestation timeline are pure Plotly→PNG,
#: while map composition (``map_export_service``, the only pyplot user in the
#: codebase) never touches Plotly. Sharing one lock therefore made a territory's
#: maps block another territory's charts for no reason at all.
#:
#: So different territories *can* render at the same time today, as long as they
#: are in different lanes. Widening a single lane still needs the library fixed
#: — see ``docs/BATCH_CONCURRENCY.md`` §9.
RENDER_POOLS = ("kaleido", "matplotlib")


def _kaleido_lane_width() -> int:
    """Workers for the kaleido lane.

    ``export_service`` gives each thread its own ``PlotlyScope`` (hence its own
    Chrome), so concurrent chart rendering is safe — there is no shared global
    left. Each worker costs one Chrome process (~150 MB), so the width is capped
    rather than tracking the core count all the way up.

    **Guarded by the probe**: if per-thread scopes are unavailable, rendering
    falls back to plotly's shared global scope, which cannot take concurrent
    callers — so the lane must stay at one worker.
    """
    override = _int_env("YVY_RENDER_KALEIDO_WORKERS", 0)
    try:
        from .export_service import scoped_kaleido_available
        if not scoped_kaleido_available():
            return 1
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"kaleido probe failed ({exc}) — lane pinned to 1 worker")
        return 1
    if override:
        return override
    by_cpu = max(2, int(DETECTED_CPUS))
    by_memory = max(1, int((DETECTED_MEMORY_GIB - _GIB_BASE) / 0.2))
    return max(1, min(by_cpu, by_memory, 8))


def _matplotlib_lane_width() -> int:
    """Workers for the map-composition lane.

    ``map_export_service`` builds ``Figure`` + ``FigureCanvasAgg`` objects
    directly rather than going through ``pyplot``, so there is no current-figure
    global to corrupt and maps can compose concurrently. Unlike kaleido this is
    real in-process CPU under the GIL — Agg releases it for the raster work, but
    the Python-level drawing does not — so scaling is sublinear and the width is
    modest.
    """
    override = _int_env("YVY_RENDER_MATPLOTLIB_WORKERS", 0)
    if override:
        return override
    return max(1, min(int(DETECTED_CPUS), 4))


#: Workers per lane, populated lazily on first use so the kaleido probe (which
#: starts a Chrome) does not run at import time.
_LANE_WIDTHS: dict = {}

_LANE_SIZERS = {
    "kaleido": _kaleido_lane_width,
    "matplotlib": _matplotlib_lane_width,
}


def lane_width(kind: str) -> int:
    if kind not in _LANE_WIDTHS:
        sizer = _LANE_SIZERS.get(kind)
        _LANE_WIDTHS[kind] = sizer() if sizer else 1
    return _LANE_WIDTHS[kind]


def render_capacity() -> int:
    """Total render slots across every lane."""
    return sum(lane_width(k) for k in RENDER_POOLS)


#: Conservative capacity for the meter created at import time; corrected to the
#: real total by :func:`reset_meters` once the lanes are known.
RENDER_CONCURRENCY = len(RENDER_POOLS)

#: Blocking work that is neither an Earth Engine call nor a render: GeoPackage
#: reads, buffer construction, boundary/summary writes, basemap tile fetches,
#: the final ZIP. Must be at least the territory width — every worker holds one
#: of these slots at several points in its territory — plus room for the tail
#: tasks that run outside the workers.
IO_CONCURRENCY = _int_env("YVY_BATCH_IO_CONCURRENCY", _profile["io"])


# ---------------------------------------------------------------------------
# Executors — created lazily, shared for the process lifetime
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_ee_executor: Optional[ThreadPoolExecutor] = None
_render_executors: dict = {}
_io_executor: Optional[ThreadPoolExecutor] = None


def get_ee_executor() -> ThreadPoolExecutor:
    """Thread pool for Earth Engine calls.

    Sized to :data:`EE_REQUEST_CONCURRENCY`, which *is* the concurrency limit:
    submissions past the Nth queue up rather than opening more sockets. Use this
    instead of ``run_in_executor(None, …)`` — asyncio's default executor is
    sized ``min(32, cpu_count + 4)``, i.e. only 6 threads on a 2-vCPU Cloud Run
    instance, and it is shared with every other blocking call in the app.
    """
    global _ee_executor
    if _ee_executor is None:
        with _lock:
            if _ee_executor is None:
                _ee_executor = ThreadPoolExecutor(
                    max_workers=EE_REQUEST_CONCURRENCY,
                    thread_name_prefix="ee",
                )
                logger.info(
                    f"Earth Engine pool: {EE_REQUEST_CONCURRENCY} workers "
                    f"(tier={TIER})"
                )
    return _ee_executor


def get_io_executor() -> ThreadPoolExecutor:
    """Thread pool for blocking work that is neither Earth Engine nor rendering.

    Replaces ``run_in_executor(None, …)`` in the batch pipeline. asyncio's
    default executor is sized ``min(32, os.cpu_count() + 4)``, so on a 2-vCPU
    Cloud Run instance it is **6 threads** — narrower than the territory width,
    and shared with every other blocking call in the app. Left on the default,
    widening the territory count just moves the queue: workers would stall on
    GeoPackage reads and map prefetch instead of on Earth Engine.

    (``os.cpu_count()`` reports the *host's* cores inside a container, not the
    cgroup limit, so the default size is not even reliably 6 — another reason to
    state the number rather than inherit it.)

    Deliberately a **different** pool from :func:`get_ee_executor`. Map prefetch
    runs here and submits its rasters to the EE pool, then blocks on them; on a
    single shared pool that is a deadlock once enough territories are in flight.
    """
    global _io_executor
    if _io_executor is None:
        with _lock:
            if _io_executor is None:
                _io_executor = ThreadPoolExecutor(
                    max_workers=IO_CONCURRENCY,
                    thread_name_prefix="io",
                )
                logger.info(f"Batch I/O pool: {IO_CONCURRENCY} workers")
    return _io_executor


def get_render_executor(kind: str = "kaleido") -> ThreadPoolExecutor:
    """Single-worker pool serializing one library's rendering.

    *kind* selects the lane — see :data:`RENDER_POOLS`. One worker **per lane**
    is a correctness requirement, not a performance choice; separate lanes are
    safe because the libraries share no global state. Because these are
    dedicated pools, render work also never queues behind Earth Engine fetches
    (or vice versa).

    An unknown *kind* falls back to the first lane rather than silently minting
    a new pool: a typo must not hand out a second concurrent worker for a
    library that cannot take one.
    """
    if kind not in RENDER_POOLS:
        logger.warning(
            f"Unknown render lane {kind!r} — using {RENDER_POOLS[0]!r}. "
            f"Valid lanes: {', '.join(RENDER_POOLS)}"
        )
        kind = RENDER_POOLS[0]
    pool = _render_executors.get(kind)
    if pool is None:
        with _lock:
            pool = _render_executors.get(kind)
            if pool is None:
                width = lane_width(kind)
                pool = ThreadPoolExecutor(
                    max_workers=width, thread_name_prefix=f"render-{kind}"
                )
                _render_executors[kind] = pool
                logger.info(f"Render lane {kind!r}: {width} worker(s)")
    return pool


# ---------------------------------------------------------------------------
# Per-run sizing
# ---------------------------------------------------------------------------

def effective_territory_concurrency(n_territories: int, heavy: bool) -> int:
    """Territories to run at once for *this* run.

    *heavy* (PNG maps, deforestation timeline, or buffer analysis enabled) means
    more live figures and map PNGs per territory and a longer render queue, so
    the width is trimmed a little. It is a modest trim, not a hard clamp: the
    written output lives on a GCS FUSE volume rather than in RAM, and rendering
    is serialized, so the extra in-flight territories cost far less memory than
    the file sizes suggest.

    An explicit ``YVY_BATCH_TERRITORY_CONCURRENCY`` disables the trim entirely —
    if someone pinned the width to benchmark it, silently halving it would make
    the benchmark meaningless.
    """
    width = TERRITORY_CONCURRENCY
    if heavy and not TERRITORY_CONCURRENCY_PINNED:
        width = min(width, HEAVY_TERRITORY_CONCURRENCY)
    return max(1, min(width, n_territories))


def tune_ee_connection_pool() -> bool:
    """Widen Earth Engine's HTTP connection pool to match the request budget.

    ``ee.data`` issues every Cloud API call through one shared
    ``requests.Session`` (``build_cloud_resource`` wraps it as the transport for
    the discovery ``Resource``). That session carries urllib3's stock adapter,
    which caps the pool at 10 connections per host — below
    :data:`EE_REQUEST_CONCURRENCY`. Past the cap urllib3 does not block: it
    opens a throwaway connection, pays a fresh TLS handshake, discards it, and
    logs "Connection pool is full" for every call. Correct, but it turns the
    extra parallelism into handshake overhead and log noise.

    Call once after ``initialize_earth_engine()`` — the session only exists
    after ``ee.Initialize``. Safe to call repeatedly.

    Returns True when the pool was resized. Reaches into ``ee.data`` internals,
    so every failure mode is non-fatal: the batch still runs correctly on the
    default pool, just with more handshakes.
    """
    try:
        from ee import data as ee_data
        from requests.adapters import HTTPAdapter

        session = getattr(ee_data._get_state(), "requests_session", None)
        if session is None:
            logger.debug("EE session not available yet — pool left at default")
            return False

        # Headroom over the worker count: redirects and token refreshes can
        # briefly hold a second connection while a call is in flight.
        size = EE_REQUEST_CONCURRENCY + 4
        # max_retries=0 — retries/backoff are handled by _ee_with_retry, which
        # can log and give up gracefully instead of silently blocking a worker.
        adapter = HTTPAdapter(
            pool_connections=size, pool_maxsize=size, max_retries=0
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        logger.info(f"Earth Engine HTTP pool resized to {size} connections")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            f"Could not resize the Earth Engine HTTP pool ({exc}) — "
            f"continuing with the default 10-connection pool"
        )
        return False


def describe_budget(n_workers: int) -> str:
    """One-line summary for the batch log."""
    return (
        f"⚡ Concurrency: {n_workers} territories in parallel · "
        f"up to {EE_REQUEST_CONCURRENCY} Earth Engine requests in flight · "
        f"{IO_CONCURRENCY} I/O slots · render "
        + " + ".join(f"{lane_width(k)}x {k}" for k in RENDER_POOLS) + " "
        f"(tier={TIER}, {DETECTED_CPUS:g} cores / {DETECTED_MEMORY_GIB:.0f} GiB detected)"
    )


# ---------------------------------------------------------------------------
# Pool metering
#
# Answers the only two questions that matter when deciding whether to widen the
# pipeline or buy more cores:
#
#   * Is the Earth Engine pool saturated?  → raise YVY_BATCH_EE_CONCURRENCY.
#     All slots busy most of the run means territories are queueing for request
#     slots, and the tier budget is what's holding throughput back.
#
#   * Is the render pool saturated?  → more territories will NOT help, because
#     rendering is serialized. That is the case for more cores plus a
#     multiprocess render pool; until then, extra parallelism just grows the
#     render queue.
#
# If neither is saturated the bottleneck is latency in individual EE calls, and
# the fix is more in-flight work (more territories), not a bigger container.
# ---------------------------------------------------------------------------

class PoolMeter:
    """Cumulative busy/saturated time for one pool.

    "Saturated" means every slot was occupied — measured as elapsed time, not a
    sample count, so a pool that is briefly full many times does not read the
    same as one that is full throughout.
    """

    def __init__(self, name: str, capacity: int):
        self.name = name
        self.capacity = capacity
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._inflight = 0
            self._since = time.monotonic()   # last time _inflight changed
            self.calls = 0
            self.busy_s = 0.0            # Σ time at least one slot was in use
            self.saturated_s = 0.0       # Σ time every slot was in use
            self.peak_inflight = 0
            self._t0 = time.monotonic()

    def _advance(self, now: float) -> None:
        """Credit the interval since the last change to the right buckets."""
        delta = now - self._since
        if self._inflight > 0:
            self.busy_s += delta
        if self._inflight >= self.capacity:
            self.saturated_s += delta
        self._since = now

    def enter(self) -> None:
        with self._lock:
            self._advance(time.monotonic())
            self._inflight += 1
            self.calls += 1
            self.peak_inflight = max(self.peak_inflight, self._inflight)

    def exit(self) -> None:
        with self._lock:
            self._advance(time.monotonic())
            self._inflight -= 1

    @contextmanager
    def track(self):
        """Meter a synchronous call: ``with ee_meter.track(): ...``.

        For work that reaches Earth Engine without going through
        ``_ee_with_retry`` — map raster downloads, say — which would otherwise
        leave the pool looking idle while it was busy.
        """
        self.enter()
        try:
            yield
        finally:
            self.exit()

    def snapshot(self) -> dict:
        with self._lock:
            self._advance(time.monotonic())
            wall = max(time.monotonic() - self._t0, 1e-9)
            return {
                "pool": self.name,
                "capacity": self.capacity,
                "calls": self.calls,
                "wall_s": round(wall, 1),
                "busy_s": round(self.busy_s, 1),
                "saturated_s": round(self.saturated_s, 1),
                "busy_pct": round(100 * self.busy_s / wall, 1),
                "saturated_pct": round(100 * self.saturated_s / wall, 1),
                "peak_inflight": self.peak_inflight,
            }


ee_meter = PoolMeter("earth_engine", EE_REQUEST_CONCURRENCY)
render_meter = PoolMeter("render", RENDER_CONCURRENCY)

# Render work splits across two mutually independent thread-unsafe libraries —
# kaleido (Plotly charts) and pyplot (map composition). They would need
# different fixes, so knowing the *total* render share is not actionable on its
# own: it does not say which one to spend effort on. This breaks the serialized
# stage down by call site.
_render_breakdown: dict = {}
_breakdown_lock = threading.Lock()


def record_render(label: str, seconds: float) -> None:
    with _breakdown_lock:
        calls, total = _render_breakdown.get(label, (0, 0.0))
        _render_breakdown[label] = (calls + 1, total + seconds)


def render_breakdown() -> dict:
    """``{label: {calls, seconds, pct_of_render}}``, heaviest first."""
    with _breakdown_lock:
        items = dict(_render_breakdown)
    total = sum(s for _, s in items.values()) or 1e-9
    return {
        label: {
            "calls": calls,
            "seconds": round(secs, 1),
            "pct_of_render": round(100 * secs / total, 1),
        }
        for label, (calls, secs) in sorted(
            items.items(), key=lambda kv: -kv[1][1]
        )
    }


def reset_meters() -> None:
    """Zero both meters — call at the start of each batch run.

    Also fixes the render meter's capacity to the real total across lanes. The
    lane widths are resolved lazily (the kaleido probe launches a Chrome, which
    must not happen at import), so the import-time value is a placeholder.
    """
    render_meter.capacity = render_capacity()
    ee_meter.reset()
    render_meter.reset()
    with _breakdown_lock:
        _render_breakdown.clear()


def meter_report() -> dict:
    """Both snapshots plus a plain-language verdict on what to change next."""
    ee = ee_meter.snapshot()
    render = render_meter.snapshot()

    # Each render lane is serialized, so the time when *any* lane is busy is a
    # hard ceiling on any speedup from more parallelism: a stage that owns R% of
    # the wall clock and cannot be widened caps the whole run at 100/R×, no
    # matter how many territories are in flight.
    render_pct = render["busy_pct"]
    ceiling = (100.0 / render_pct) if render_pct > 0 else float("inf")

    # "Saturated" = every lane busy at once, i.e. the lane split is actually
    # paying off. Low overlap with high occupancy means one library dominates
    # and the other lane is mostly idle — so widening *that* library is the
    # whole game, and the split bought little.
    overlap = render["saturated_pct"]

    if render_pct >= 80:
        if overlap >= 0.4 * render_pct:
            lane_note = (
                f"lanes overlap {overlap}% of the run, so the split is already "
                f"paying; going further needs a lane widened"
            )
        else:
            lane_note = (
                f"lanes overlap only {overlap}% of the run — one library "
                f"dominates, so widen that lane (see the render split)"
            )
        verdict = (
            f"render-bound ({render_pct}% of the run) — each lane is "
            f"serialized, so more territories cannot help; the ceiling is "
            f"{ceiling:.1f}×. {lane_note}."
        )
    elif ee["saturated_pct"] >= 60:
        verdict = (
            f"EE-pool-bound — all {ee['capacity']} request slots were busy "
            f"{ee['saturated_pct']}% of the run. Raise YVY_BATCH_EE_CONCURRENCY."
        )
    elif render_pct >= 50:
        verdict = (
            f"partly render-bound ({render_pct}%) — more territories still "
            f"help, but only up to about {ceiling:.1f}×. Past that a render "
            f"lane has to be widened (see the render split)."
        )
    elif ee["busy_pct"] >= 60:
        verdict = (
            "latency-bound — the EE pool has spare slots but calls are slow. "
            "Raise YVY_BATCH_TERRITORY_CONCURRENCY to keep more work in flight."
        )
    else:
        verdict = (
            "not bound by either pool — the time is going somewhere else "
            "(geometry loading, file writes, ZIP compression)."
        )
    return {
        "earth_engine": ee,
        "render": render,
        "render_breakdown": render_breakdown(),
        "machine": {
            "cpus": DETECTED_CPUS,
            "memory_gib": round(DETECTED_MEMORY_GIB, 1),
        },
        "verdict": verdict,
    }


def describe_meters(report: Optional[dict] = None) -> List[str]:
    """Log lines summarising the meters at the end of a run.

    Pass a *report* captured earlier to describe a specific phase. The batch
    pipeline does this: it snapshots before the final ZIP, so the percentages
    describe the analysis phase rather than being diluted by a compression step
    that neither pool participates in — and so the log agrees with the
    ``concurrency`` block written into ``batch_summary.json``.
    """
    r = report if report is not None else meter_report()
    ee, render = r["earth_engine"], r["render"]
    lines = [
        f"📊 Earth Engine pool: {ee['calls']} calls · busy {ee['busy_pct']}% · "
        f"all {ee['capacity']} slots busy {ee['saturated_pct']}% · "
        f"peak {ee['peak_inflight']}",
        f"📊 Render ({render['capacity']} slots across "
        f"{len(RENDER_POOLS)} lanes): {render['calls']} tasks · "
        f"any slot busy {render['busy_pct']}% of the run · "
        f"all slots busy {render['saturated_pct']}% · "
        f"peak {render['peak_inflight']}",
    ]
    breakdown = r.get("render_breakdown") or {}
    if breakdown:
        lines.append(
            "📊 Render split: " + " · ".join(
                f"{label} {v['pct_of_render']}% ({v['calls']}×, {v['seconds']}s)"
                for label, v in breakdown.items()
            )
        )
    lines.append(f"📊 Bottleneck: {r['verdict']}")
    return lines
