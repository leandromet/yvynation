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
*and* must run one at a time regardless of how many cores we have:

* ``kaleido==0.2.1`` drives a single module-global headless renderer
  (``plotly.io._kaleido.scope``) over one pipe — concurrent ``fig.to_image()``
  calls from different threads interleave on that pipe and deadlock or return
  truncated PNGs.
* ``map_export_service`` uses the ``pyplot`` state machine (global current
  figure / axes), which is likewise not thread-safe.

So :data:`RENDER_CONCURRENCY` is pinned to 1 and is **not** a tuning knob. The
throughput win comes from *pipelining*: while one territory renders, the others
are fetching from Earth Engine.

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
#: An extra in-flight territory is much cheaper than it looks. Rendering is
#: serialized, so at most one territory holds figures and map PNGs at any
#: moment; the others are parked in ``getInfo()`` holding only their fetched
#: result dicts (class histograms — kilobytes, not megabytes). And on Cloud Run
#: ``uploaded_files/exports/`` is a GCS FUSE volume, so the bytes a run *writes*
#: never enter the container's memory budget at all. Hence ``territories`` well
#: above the core count: these workers are waiting on the network, not competing
#: for CPU.
#:
#: The contributor numbers are the pre-uplift behaviour plus a little headroom:
#: one territory at a time, but still fanning its independent analyses out — 4
#: concurrent requests sat comfortably inside the free-tier budget in practice.
#: ``territories: 1`` there is deliberate: with a narrow request budget, running
#: several territories at once only spreads the same throughput over a longer
#: wall time.
_PROFILES = {
    "partner": {"territories": 4, "heavy": 3, "ee_requests": 12},
    "contributor": {"territories": 1, "heavy": 1, "ee_requests": 4},
}

_DEFAULT_TIER = "partner"


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
_profile = _PROFILES[TIER]

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

#: Pinned to 1 — kaleido 0.2.1 and pyplot are not thread-safe. Not tunable.
RENDER_CONCURRENCY = 1


# ---------------------------------------------------------------------------
# Executors — created lazily, shared for the process lifetime
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_ee_executor: Optional[ThreadPoolExecutor] = None
_render_executor: Optional[ThreadPoolExecutor] = None


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


def get_render_executor() -> ThreadPoolExecutor:
    """Single-worker pool that serializes all chart/map rendering.

    One worker is a correctness requirement, not a performance choice — see the
    module docstring. Because it is a dedicated pool, render work also never
    queues behind Earth Engine fetches (or vice versa).
    """
    global _render_executor
    if _render_executor is None:
        with _lock:
            if _render_executor is None:
                _render_executor = ThreadPoolExecutor(
                    max_workers=RENDER_CONCURRENCY,
                    thread_name_prefix="render",
                )
    return _render_executor


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
        f"rendering serialized (tier={TIER})"
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


def reset_meters() -> None:
    """Zero both meters — call at the start of each batch run."""
    ee_meter.reset()
    render_meter.reset()


def meter_report() -> dict:
    """Both snapshots plus a plain-language verdict on what to change next."""
    ee = ee_meter.snapshot()
    render = render_meter.snapshot()

    # Rendering is serialized, so its occupancy is a hard ceiling on any
    # speedup from more parallelism: a stage that owns R% of the wall clock
    # and cannot be widened caps the whole run at 100/R×, no matter how many
    # territories are in flight.
    render_pct = render["busy_pct"]
    ceiling = (100.0 / render_pct) if render_pct > 0 else float("inf")

    if render_pct >= 80:
        verdict = (
            f"render-bound ({render_pct}% of the run) — rendering is "
            f"serialized, so more territories cannot help; the ceiling is "
            f"{ceiling:.1f}×. Needs more cores + a multiprocess render pool."
        )
    elif ee["saturated_pct"] >= 60:
        verdict = (
            f"EE-pool-bound — all {ee['capacity']} request slots were busy "
            f"{ee['saturated_pct']}% of the run. Raise YVY_BATCH_EE_CONCURRENCY."
        )
    elif render_pct >= 50:
        verdict = (
            f"partly render-bound ({render_pct}%) — more territories still "
            f"help, but only up to about {ceiling:.1f}×. Past that it takes "
            f"more cores + a multiprocess render pool."
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
    return {"earth_engine": ee, "render": render, "verdict": verdict}


def describe_meters() -> List[str]:
    """Log lines summarising the meters at the end of a run."""
    r = meter_report()
    ee, render = r["earth_engine"], r["render"]
    return [
        f"📊 Earth Engine pool: {ee['calls']} calls · busy {ee['busy_pct']}% · "
        f"all {ee['capacity']} slots busy {ee['saturated_pct']}% · "
        f"peak {ee['peak_inflight']}",
        f"📊 Render pool: {render['calls']} tasks · busy {render['busy_pct']}% "
        f"of the run (serialized)",
        f"📊 Bottleneck: {r['verdict']}",
    ]
