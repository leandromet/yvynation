"""
Batch processing event handlers.

Iterates over a user-selected list of territories, runs the full analysis
suite (MapBiomas, comparison, Hansen GLAD, Hansen GFC, buffer) for each one,
and packs everything into a single download-ready ZIP archive.

The ZIP uses the same structure as export_service.create_export_zip but
collects data from *all* selected territories into one file:

  batch_{timestamp}.zip/
    territory/{slug}/
      boundary.geojson
      mapbiomas/  …
      mapbiomas_multi_window/  ← optional Sankey/Sunburst across N years
      hansen_glad/  …
      hansen_gfc/  …
      maps/        ← PNG maps (satellite, MapBiomas y1/y2, Hansen)
      deforestation_timeline/  ← optional: yearly Hansen + MapBiomas defor +
                                  secondary regrowth + fire scar CSV, plus
                                  three chart variants (raw, MA5, derivatives)
                                  with political/policy context bars.
    buffer/{buffer_slug}/
      …
    batch_summary.json
    batch_report.md
"""

import asyncio
import gc
import io
import json
import logging
import time
import zipfile
from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Optional

import reflex as rx

logger = logging.getLogger(__name__)

# NOTE: the batch ZIP used to be held here as a module-level bytes blob and
# shipped through rx.download(data=...). It is now written straight to
# ``uploaded_files/exports/`` and downloaded over HTTP (see download_batch_zip).

# ---------------------------------------------------------------------------
# Quadrant splitting
#
# EE's compute backend times out on territories larger than ~2 M ha (Parque do
# Xingu, Kayapó, etc.) when combined with a buffer ring.  We split such
# territories into four bounding-box quadrants and run the full analysis
# pipeline on each, writing results to sub-folders nw/, ne/, sw/, se/ inside
# the territory and buffer ZIP folders.
# ---------------------------------------------------------------------------

SPLIT_THRESHOLD_HA = 1_000_000  # split territories larger than this


def _compute_quadrant_bboxes(minx, miny, maxx, maxy):
    """Return ``[(name, bbox), ...]`` for the 4 cardinal quadrants of a bbox."""
    midx = (minx + maxx) / 2
    midy = (miny + maxy) / 2
    return [
        ("nw", (minx, midy, midx, maxy)),
        ("ne", (midx, midy, maxx, maxy)),
        ("sw", (minx, miny, midx, midy)),
        ("se", (midx, miny, maxx, midy)),
    ]


def _make_quadrant_regions(ee_geom, buf_ee_geom, shapely_geom):
    """Build a list of ``(region_name, region_ee_geom, region_buf_ee_geom)``.

    Quadrant splitting happens entirely server-side in EE (``intersection``
    is a lazy op — no ``getInfo`` round-trip), so this is essentially free.
    The shared midpoint comes from the territory's local bounds so the four
    quadrants tile the buffer ring consistently.
    """
    import ee
    minx, miny, maxx, maxy = shapely_geom.bounds
    regions = []
    for qname, qbbox in _compute_quadrant_bboxes(minx, miny, maxx, maxy):
        qbox = ee.Geometry.Rectangle(list(qbbox))
        q_terr = ee_geom.intersection(qbox, maxError=1)
        q_buf = buf_ee_geom.intersection(qbox, maxError=1) if buf_ee_geom else None
        regions.append((qname, q_terr, q_buf))
    return regions


# ---------------------------------------------------------------------------
# EE call helper — retry-with-backoff for "Computation timed out" etc.
# ---------------------------------------------------------------------------

_TRANSIENT_PATTERNS = ("timed out", "timeout", "deadline", "internal error",
                       "503", "502", "504", "rate limit", "quota")


def _is_transient_error(exc: Exception) -> bool:
    """Heuristic: is this EE error worth retrying?"""
    msg = str(exc).lower()
    return any(p in msg for p in _TRANSIENT_PATTERNS)


async def _ee_with_retry(loop, fn, label: str, retries: int = 3, base_delay: float = 4.0):
    """
    Run *fn* on the Earth Engine pool with up to *retries* attempts on transient
    EE errors.

    Returns the result on success, ``None`` on persistent failure.  Logs
    progress between attempts so the batch task can keep going.

    The pool (``utils/ee_concurrency``) is the single global throttle on
    in-flight EE requests: callers can fan out as widely as the analysis graph
    allows and the pool queues whatever exceeds the tier budget.  Backoff waits
    happen *outside* the executor, so a retrying call never occupies a worker.
    """
    from ..utils.ee_concurrency import ee_meter, get_ee_executor

    executor = get_ee_executor()

    def _metered(_fn=fn):
        # Metered inside the worker thread, so the timing covers the actual
        # request rather than the queue wait ahead of it — a slot only counts
        # as busy once it really is.
        ee_meter.enter()
        try:
            return _fn()
        finally:
            ee_meter.exit()

    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return await loop.run_in_executor(executor, _metered)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            transient = _is_transient_error(exc)
            if attempt < retries and transient:
                wait = base_delay * (2 ** (attempt - 1))  # 4s, 8s, 16s
                logger.warning(
                    f"⚠ {label}: transient error '{exc}' on attempt "
                    f"{attempt}/{retries} — retrying in {wait:.0f}s"
                )
                await asyncio.sleep(wait)
                continue
            break
    logger.error(f"❌ {label}: gave up after {attempt} attempts — {last_exc}")
    return None


async def _render(loop, fn, label: str, lane: str):
    """Run chart/map rendering on the single-slot pool for *lane*'s library.

    Everything that touches kaleido (Plotly → PNG) or pyplot (the map exporter)
    must go through here — both keep module-global state that concurrent threads
    corrupt. Within a lane the work is strictly one-at-a-time while Earth Engine
    fetches overlap.

    **Across** lanes it runs concurrently, and that is the point: the two
    libraries share no global state, so one territory's maps and another's
    charts have no reason to block each other. Pick the lane by the library the
    work actually reaches, never by which call site it is — routing pyplot work
    into the kaleido lane would silently allow two concurrent pyplot renders.

    *label* attributes time to a call site within a lane; the libraries need
    different fixes, so the aggregate render share does not say where to spend
    effort — the split does.
    """
    import time as _time

    from ..utils.ee_concurrency import (
        get_render_executor, record_render, render_meter,
    )

    def _metered():
        render_meter.enter()
        t0 = _time.monotonic()
        try:
            return fn()
        finally:
            # Keyed by lane too — the split's job is to name the library to
            # fix, and two call sites can share a lane.
            record_render(f"{label} ({lane})", _time.monotonic() - t0)
            render_meter.exit()

    return await loop.run_in_executor(get_render_executor(lane), _metered)


# ---------------------------------------------------------------------------
# Figure builders — pure CPU, run inside the export thread
# ---------------------------------------------------------------------------

def _ensure_class_name(df):
    """Make sure the DataFrame has a ``Class_Name`` column for chart functions.

    ``ee_service.analyze_mapbiomas`` returns ``Class``; ``analyzer.analyze_single_year``
    returns ``Class_Name``.  When the batch task mixes both sources, the chart
    builders (which look for one or the other) can fail.  Normalising up-front
    makes downstream code resilient regardless of which analyzer produced the DF.
    """
    if df is None or df.empty:
        return df
    if "Class_Name" in df.columns:
        return df
    if "Class" in df.columns:
        return df.assign(Class_Name=df["Class"])
    if "Class_ID" in df.columns:
        return df.assign(Class_Name=df["Class_ID"].astype(str))
    return df

def _build_transition_matrix_fig(transitions, year1, year2):
    """Heatmap of land-cover transitions (replicates AppState.transition_matrix_chart)."""
    import plotly.graph_objects as pgo
    try:
        if not transitions:
            return pgo.Figure()

        from ..utils.visualization import _get_mapbiomas_labels
        try:
            labels = _get_mapbiomas_labels()
        except Exception:
            labels = {}

        all_classes = set()
        for src, tgt_dict in transitions.items():
            if isinstance(tgt_dict, dict):
                all_classes.add(str(src))
                all_classes.update(str(t) for t in tgt_dict)
        classes = sorted(all_classes)
        if not classes:
            return pgo.Figure()

        display_names = []
        for c in classes:
            try:
                display_names.append(labels.get(int(c), c))
            except (ValueError, TypeError):
                display_names.append(labels.get(c, c))

        matrix = []
        for src in classes:
            row = []
            for tgt in classes:
                src_dict = transitions.get(
                    src, transitions.get(int(src) if src.isdigit() else src, {})
                )
                if isinstance(src_dict, dict):
                    val = src_dict.get(tgt, src_dict.get(int(tgt) if tgt.isdigit() else tgt, 0))
                else:
                    val = 0
                row.append(float(val) if isinstance(val, (int, float)) else 0)
            matrix.append(row)

        fig = pgo.Figure(
            data=pgo.Heatmap(
                z=matrix, x=display_names, y=display_names,
                colorscale="YlOrRd", hoverongaps=False,
                hovertemplate=f"<b>%{{y}} → %{{x}}</b><br>{year1}→{year2}: %{{z:,.1f}} ha<extra></extra>",
            )
        )
        fig.update_layout(
            title=f"Land-Cover Transition Matrix ({year1} → {year2})",
            xaxis_title=f"To class ({year2})", yaxis_title=f"From class ({year1})",
            template="plotly_white", height=700, margin=dict(l=200, b=180),
        )
        return fig
    except Exception:
        logger.warning("transition matrix build failed", exc_info=True)
        return pgo.Figure()


def _build_territory_figures(
    mb_y1_records,
    mb_y2_records,
    transitions,
    glad_records,
    gfc_dict,
    y1, y2, hansen_year,
    run_treemap=True,
):
    """Build every plotly figure needed for the export ZIP (territory or buffer)."""
    import pandas as pd
    figs = {}
    try:
        from ..utils.visualization import (
            MapBiomasVisualizer, HansenVisualizer,
            calculate_gains_losses,
            create_gains_losses_chart, create_change_percentage_chart,
            create_sankey_transitions, create_sunburst_transitions,
            create_class_transition_treemaps,
            _create_gfc_summary_chart,
        )
    except Exception as e:
        logger.warning(f"Could not import visualization helpers: {e}")
        return figs

    df1 = pd.DataFrame(mb_y1_records) if mb_y1_records else pd.DataFrame()
    df2 = pd.DataFrame(mb_y2_records) if mb_y2_records else pd.DataFrame()
    df1 = _ensure_class_name(df1)
    df2 = _ensure_class_name(df2)

    # Single-year distribution + pie — build for both years when both have
    # data, so the export ends up with parallel y1 and y2 files for both
    # the territory and its buffer.
    def _build_single_year(df, year, suffix):
        if df.empty:
            return
        try:
            figs[f"bar_chart_{suffix}"] = MapBiomasVisualizer.create_area_bar_chart(df, year=year)
        except Exception as e:
            logger.warning(f"bar_chart_{suffix} build failed: {e}")
        try:
            figs[f"pie_chart_{suffix}"] = MapBiomasVisualizer.create_pie_chart(df)
        except Exception as e:
            logger.warning(f"pie_chart_{suffix} build failed: {e}")

    _build_single_year(df1, y1, "y1")
    _build_single_year(df2, y2, "y2")
    # Back-compat aliases (still used by older non-batch call sites).
    figs["bar_chart"] = figs.get("bar_chart_y2") or figs.get("bar_chart_y1")
    figs["pie_chart"] = figs.get("pie_chart_y2") or figs.get("pie_chart_y1")

    # Year-over-year comparison
    if not df1.empty and not df2.empty:
        try:
            figs["comparison_bar_chart"] = MapBiomasVisualizer.create_comparison_chart(
                df1, df2, y1, y2
            )
        except Exception as e:
            logger.warning(f"comparison_bar_chart build failed: {e}")
        try:
            comp_df = calculate_gains_losses(df1, df2)
            if comp_df is not None and not comp_df.empty:
                figs["gains_losses_chart"] = create_gains_losses_chart(comp_df, y1, y2)
                figs["change_pct_chart"] = create_change_percentage_chart(comp_df, y1, y2)
        except Exception as e:
            logger.warning(f"gains_losses/change_pct build failed: {e}")

    # Transition-based charts
    if transitions:
        try:
            figs["sankey_chart"] = create_sankey_transitions(transitions, y1, y2)
        except Exception as e:
            logger.warning(f"sankey build failed: {e}")
        try:
            figs["sunburst_chart"] = create_sunburst_transitions(transitions, y1, y2)
        except Exception as e:
            logger.warning(f"sunburst build failed: {e}")
        if run_treemap:
            try:
                # Year-start area per class so the treemap persistence % is
                # measured against each class's original area (correct for
                # change-only dicts).
                class_totals = {}
                for row in (mb_y1_records or []):
                    cid, area = row.get("Class_ID"), row.get("Area_ha")
                    if cid is not None and isinstance(area, (int, float)):
                        class_totals[cid] = float(area)
                figs["treemap_chart"] = create_class_transition_treemaps(
                    transitions, y1, y2, class_totals=class_totals or None
                )
            except Exception as e:
                logger.warning(f"treemap build failed: {e}")
        try:
            figs["transition_matrix_chart"] = _build_transition_matrix_fig(transitions, y1, y2)
        except Exception as e:
            logger.warning(f"matrix build failed: {e}")

    # Hansen GLAD bar chart
    if glad_records:
        try:
            glad_df = pd.DataFrame(glad_records)
            figs["glad_bar"] = HansenVisualizer.create_area_distribution_chart(
                glad_df, year=hansen_year
            )
        except Exception as e:
            logger.warning(f"glad_bar build failed: {e}")

    # Hansen GFC charts
    if gfc_dict:
        try:
            summary_data = gfc_dict.get("data")
            if summary_data:
                figs["gfc_bar"] = _create_gfc_summary_chart(pd.DataFrame(summary_data))
        except Exception as e:
            logger.warning(f"gfc_bar build failed: {e}")
        try:
            loss_rows = [r for r in gfc_dict.get("tree_loss_data", [])
                         if r.get("Year_Code", 0) > 0]
            if loss_rows:
                loss_df = pd.DataFrame(loss_rows)
                if "Year" not in loss_df.columns and "Year_Code" in loss_df.columns:
                    loss_df["Year"] = 2000 + loss_df["Year_Code"].astype(int)
                if "Loss_ha" not in loss_df.columns and "Area_ha" in loss_df.columns:
                    loss_df["Loss_ha"] = loss_df["Area_ha"]
                figs["gfc_loss"] = HansenVisualizer.create_loss_timeline_chart(loss_df)
        except Exception as e:
            logger.warning(f"gfc_loss build failed: {e}")

    return figs


# ---------------------------------------------------------------------------
# Steps reported to the UI
# ---------------------------------------------------------------------------
STEPS = {
    "geometry":     "📐 Loading geometry…",
    "fetch":        "⚡ {n} Earth Engine analyses in parallel…",
    "mb_y1":        "🌿 MapBiomas {year1} analysis…",
    "mb_y2":        "🌿 MapBiomas {year2} analysis…",
    "comparison":   "📊 Land-cover comparison {year1} → {year2}…",
    "glad":         "🌲 Hansen GLAD {hansen_year} analysis…",
    "gfc":          "🪓 Hansen GFC (tree cover / loss / gain)…",
    "buf_mb":       "🔵 Buffer MapBiomas {year1}…",
    "buf_cmp":      "🔵 Buffer comparison {year1} → {year2}…",
    "buf_glad":     "🔵 Buffer Hansen GLAD…",
    "buf_gfc":      "🔵 Buffer Hansen GFC…",
    "multi_window": "🌀 Multi-window MapBiomas transitions…",
    "buf_multi":    "🔵 Multi-window MapBiomas transitions (buffer)…",
    "maps_fetch":   "🛰 Downloading map rasters…",
    "maps":         "🗺️  Rendering PNG maps…",
    "export":       "📦 Packaging data…",
    "done":         "✅ Done",
}

# ---------------------------------------------------------------------------
# Large-run guardrail — soft warning only, run is never blocked.
#
# Above these counts a single run risks the container's memory ceiling (see
# CLOUD_RUN_DEPLOYMENT.md: exports are written under uploaded_files/, which on
# Cloud Run draws from the same memory budget as everything else). The lower,
# "heavy" threshold applies when PNG maps and/or the buffer analysis are on,
# since both multiply the per-territory output.
# ---------------------------------------------------------------------------
BATCH_WARN_THRESHOLD = 40
BATCH_WARN_THRESHOLD_HEAVY = 25

# ---------------------------------------------------------------------------
# Hard cap on total selection (both types combined). Enforced at every point
# a territory can be added (checkbox toggle, "select all filtered", paste
# list) — not just a UI hint, since "select all" on an unfiltered 3,247-unit
# conservation list would otherwise queue a run large enough to risk real EE
# usage cost and container memory, however the batch loop performs.
# ---------------------------------------------------------------------------
BATCH_MAX_SELECTION = 100

# How many territory rows the selector actually draws. Unrelated to the cap
# above: this one is about DOM cost, not run size. `rx.foreach` builds a row
# per entry, and the unfiltered conservation list is 3,247 of them — enough
# to make the selector visibly slow to open, worst on the phones that can
# least afford it. Search and the attribute filters are how you reach past
# it; every handler still operates on the full filtered list.
BATCH_LIST_RENDER_CAP = 300

# ---------------------------------------------------------------------------
# Attribute-filter dropdown vocabularies — hardcoded rather than scanned from
# the GeoPackage. These come from fixed government classification schemes
# (SNUC for conservation units, FUNAI process stages for indigenous
# demarcation) and don't change at runtime. Scanning ~3,247 conservation
# rows per field (via get_territory_info) to discover "what values exist"
# was measured at ~1.5s each — six of those on every type-toggle click was
# most of a reported ~10s stall. Values below match the current GeoPackage
# exactly (verified 2026-08-16); update here if the source data changes.
# ---------------------------------------------------------------------------
_UF_OPTIONS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG",
    "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO",
]
_FASE_OPTIONS = ["Declarada", "Delimitada", "Em Estudo", "Encaminhada RI", "Homologada", "Regularizada"]
_MODALIDADE_OPTIONS: List[str] = []  # column is unpopulated in the current GeoPackage
_CATEGORIA_OPTIONS = [
    "Estação Ecológica", "Floresta", "Monumento Natural", "Parque",
    "Refúgio de Vida Silvestre", "Reserva Biológica", "Reserva Extrativista",
    "Reserva Particular do Patrimônio Natural", "Reserva de Desenvolvimento Sustentável",
    "Reserva de Fauna", "Área de Proteção Ambiental", "Área de Relevante Interesse Ecológico",
]
_ESFERA_OPTIONS = ["Estadual", "Federal", "Municipal"]
_GRUPO_OPTIONS = ["Proteção Integral", "Uso Sustentável"]


class BatchMixin(rx.State, mixin=True):
    """Event handlers and helpers for the batch-processing page."""

    # ---- Configuration -------------------------------------------------------
    batch_selected_territories: List[str] = []
    # Stored as strings so they bind cleanly to ``rx.select(value=...)``.
    # ``int_var.to(str)`` does not reactively update the displayed dropdown
    # value in Reflex 0.8.27 — use a direct string var instead.
    batch_year: str = "1985"      # single-year MapBiomas
    batch_year2: str = "2024"     # comparison year
    batch_hansen_year: str = "2020"
    batch_buffer_km: str = "10"
    batch_buffer_enabled: bool = True
    batch_run_mapbiomas: bool = True
    batch_run_comparison: bool = True
    batch_run_treemap: bool = True   # class-transition treemaps (compare + multi-window)
    batch_run_glad: bool = True
    batch_run_gfc: bool = True
    batch_run_pdf_maps: bool = True
    # ── MapBiomas auxiliary raster layers (each rendered as one PNG when on) ──
    # Per-year layers use the configured batch year2; full-period layers
    # (fire_frequency) render one image regardless of year selection.
    batch_run_aux_deforestation: bool = False
    batch_run_aux_fire_scar: bool = False
    batch_run_aux_fire_frequency: bool = False
    batch_run_aux_fire_year_last: bool = False
    batch_run_aux_mining_substances: bool = False
    batch_run_aux_agriculture_cycles: bool = False
    # ── Annual deforestation / regrowth / fire timeline with political &
    # policy context bars (per-territory, full year range from batch_year to
    # batch_year2). One CSV + three chart variants per region.
    batch_run_deforestation_timeline: bool = False
    # Timeline context bands. Each is independent; turning one off also gives
    # back the vertical space it reserved, so the chart gets shorter.
    batch_timeline_political: bool = True    # president / governor stripes
    batch_timeline_policy: bool = True       # policy heat-rows + milestone key
    batch_timeline_enso: bool = True         # Oceanic Niño Index strip
    # ── Figure export (PNG) ───────────────────────────────────────────────
    # PNGs are ~90% of an archive's bytes (449 MB of 503 MB in a measured
    # 18-territory run); HTML is always written either way, so a no-PNG run is
    # still complete. Batch only — the interactive geometry/territory exports
    # keep print quality regardless.
    batch_export_png: bool = True
    # False → scale 1.2 (default). True → 2.0 ("high res"). See
    # batch_png_scale — both tiers now render sharper than the interactive
    # exports' scale=1.0, since the plain default read too soft.
    batch_png_high_res: bool = False
    # ── Multiple time-window MapBiomas (off by default) ───────────────────
    batch_run_multi_window: bool = False
    # "constant" → step list from 1985, force-end on 2024
    # "custom"   → user-supplied comma-separated year list
    batch_multi_window_mode: str = "constant"
    # Step in years for the constant mode (one of 1, 2, 4, 5, 8).
    batch_multi_window_step: str = "8"
    # Custom mode: 3 to 10 user-selected years, comma-separated.
    batch_multi_window_custom_years: str = "1985, 1994, 2004, 2014, 2024"
    batch_territory_search: str = ""
    # Which GeoPackage backs the territory list view — always exactly one
    # entry ("indigenous" or "conservation"; kept as a list so the existing
    # ``_batch_active_services``/filter code, written for either-or-both,
    # needs no branching). The *selection* can still span both types across
    # view switches — see ``batch_set_territory_type``.
    batch_territory_types: List[str] = ["indigenous"]
    # Hectare range filter (empty string = no bound on that side). Kept as
    # strings so they bind cleanly to on_change number inputs.
    batch_min_area_ha: str = ""
    batch_max_area_ha: str = ""
    # ---- Attribute filters (multi-select; empty list = no restriction) -------
    batch_selected_ufs: List[str] = []
    # Indigenous-only fields (empty/no-op while only conservation is active)
    batch_selected_fase: List[str] = []
    batch_selected_modalidade: List[str] = []
    # Conservation-only fields (empty/no-op while only indigenous is active)
    batch_selected_categoria: List[str] = []
    batch_selected_esfera: List[str] = []
    batch_selected_grupo: List[str] = []
    # "name_asc" | "name_desc" | "area_asc" | "area_desc"
    batch_sort_by: str = "name_asc"
    # Selected-territories review panel (see review_selection_modal)
    batch_show_review: bool = False

    # ---- Stage flow (pages/batch_processing.py) ------------------------------
    #: Which of the three stages the page is on: "select" | "configure" | "run".
    #: Read through `batch_stage_effective` below, never directly — a run in
    #: flight overrides it.
    batch_stage: str = "select"
    #: Which groups of the configuration accordion are open
    #: (components/batch_config_panel.py). Its own list rather than the
    #: analysis sidebar's `open_groups`: the two panels have nothing to do
    #: with each other and sharing one list would have opening a batch group
    #: silently change the map page's sidebar.
    batch_config_groups: List[str] = ["years", "analyses"]
    # ---- Paste/upload a name list to auto-select areas ------------------------
    batch_paste_text: str = ""
    batch_paste_feedback: str = ""
    batch_paste_unmatched: List[str] = []

    # ---- Runtime status ------------------------------------------------------
    batch_running: bool = False
    batch_done: bool = False
    #: Set the instant a run is dispatched, cleared once `batch_running` takes
    #: over (or the run bails out early).
    #:
    #: `run_batch_processing` is a background task that does not reach
    #: `batch_running = True` for several seconds: it first snapshots the
    #: configuration, then awaits two abuse-control checks in the executor.
    #: The Start button is gated on `batch_running`, so for that whole window
    #: it stayed live — and a second click launched a second, concurrent run
    #: over the same selection. Reported from a real session: two ZIPs, same
    #: contents, a few seconds apart. This flag closes the window, and unlike
    #: `batch_running` it is set synchronously in the click handler itself,
    #: before any await, so the second event cannot slip past it.
    batch_starting: bool = False
    #: Friction step in front of run_batch_processing — see request_batch_run.
    #: Server-side enforcement is abuse_control.py, not this flag; this only
    #: deters an accidental/reflexive click.
    batch_confirm_pending: bool = False
    batch_zip_ready: bool = False
    #: Upload-relative path of the finished ZIP (e.g. "exports/yvynation_batch_….zip")
    batch_zip_relpath: str = ""
    batch_current_territory: str = ""
    batch_current_step: str = ""
    #: territory → step label, one entry per territory currently in flight.
    #: With territories processed in parallel there is no single "current"
    #: step, so the status panel lists these; ``batch_current_territory`` /
    #: ``batch_current_step`` are kept as a summary of the same data.
    batch_active_steps: Dict[str, str] = {}
    batch_completed: List[str] = []      # successfully processed
    batch_failed: List[str] = []         # territories that errored
    batch_errors: Dict[str, str] = {}    # territory → error message
    batch_total: int = 0
    batch_log: List[str] = []           # live log lines (most recent last)

    # ---- Computed ------------------------------------------------------------

    def _batch_active_services(self) -> List[tuple]:
        """[(type_name, service_singleton), ...] for the active territory types."""
        services: List[tuple] = []
        if "indigenous" in self.batch_territory_types:
            from ..utils.territory_service import get_territory_service
            services.append(("indigenous", get_territory_service()))
        if "conservation" in self.batch_territory_types:
            from ..utils.conservation_service import get_conservation_unit_service
            services.append(("conservation", get_conservation_unit_service()))
        return services

    def _batch_parse_ha(self, raw: str) -> Optional[float]:
        try:
            v = float(raw)
            return v if v >= 0 else None
        except (ValueError, TypeError):
            return None

    def _batch_field_dict(self, field: str, only_type: Optional[str] = None) -> Dict[str, str]:
        """display_key → stripped string value of ``field`` from get_territory_info().

        ``field`` is a type-specific attribute (e.g. "fase_ti", "categoria"),
        so callers usually pass ``only_type`` to avoid the other source's
        ``get_territory_info`` doing a lookup for a key it won't recognise.
        """
        out: Dict[str, str] = {}
        for type_name, svc in self._batch_active_services():
            if only_type and type_name != only_type:
                continue
            for key in svc.get_all_display_keys():
                info = svc.get_territory_info(key) or {}
                v = str(info.get(field) or "").strip()
                if v:
                    out[key] = v
        return out

    def _batch_toggle_filter_value(self, attr_name: str, value: str):
        """Add/remove ``value`` from the list-valued filter state var named ``attr_name``."""
        current = list(getattr(self, attr_name))
        if value in current:
            current.remove(value)
        else:
            current.append(value)
        setattr(self, attr_name, current)

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_available_territories(self) -> List[str]:
        """Full territory list from all active sources (indigenous and/or conservation).

        auto_deps=False: the relative imports inside ``_batch_active_services``
        make Reflex's static dependency scan bail out silently (logged as a
        "Failed to automatically determine dependencies" warning), which
        left this var never recomputing when ``batch_territory_types``
        changed — the territory list stayed on indigenous lands after
        toggling to conservation even though the filter dropdowns (which
        already declared deps explicitly) updated correctly.
        """
        try:
            keys: List[str] = []
            for _type, svc in self._batch_active_services():
                keys.extend(svc.get_all_display_keys())
            return sorted(set(keys))
        except Exception:
            return []

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_area_ha(self) -> Dict[str, float]:
        """display_key → superficie_ha from the owning GeoPackage.

        Backs the min/max hectare range filter — reuses the same cheap
        static attribute already shown in ``batch_territory_meta``.
        """
        try:
            out: Dict[str, float] = {}
            for _type, svc in self._batch_active_services():
                for key in svc.get_all_display_keys():
                    info = svc.get_territory_info(key) or {}
                    out[key] = float(info.get("superficie_ha") or 0)
            return out
        except Exception:
            return {}

    # ---- Attribute filter data (values per key + dropdown options) -----------
    # Indigenous-only fields
    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_fase(self) -> Dict[str, str]:
        """display_key → fase_ti (demarcation stage), indigenous lands only."""
        return self._batch_field_dict("fase_ti", only_type="indigenous")

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_modalidade(self) -> Dict[str, str]:
        """display_key → modalidade (land tenure type), indigenous lands only."""
        return self._batch_field_dict("modalidade", only_type="indigenous")

    # Conservation-only fields
    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_categoria(self) -> Dict[str, str]:
        """display_key → categoria (unit category), conservation units only."""
        return self._batch_field_dict("categoria", only_type="conservation")

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_esfera(self) -> Dict[str, str]:
        """display_key → esfera (federal/state/municipal), conservation units only."""
        return self._batch_field_dict("esfera", only_type="conservation")

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_grupo(self) -> Dict[str, str]:
        """display_key → grupo (full/sustainable protection), conservation units only."""
        return self._batch_field_dict("grupo", only_type="conservation")

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_uf_options(self) -> List[str]:
        """The 27 Brazilian federative units — fixed, so listed directly rather
        than scanned from the data (see the vocabulary block above ``BatchMixin``)."""
        return _UF_OPTIONS

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_fase_options(self) -> List[str]:
        return _FASE_OPTIONS if "indigenous" in self.batch_territory_types else []

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_modalidade_options(self) -> List[str]:
        return _MODALIDADE_OPTIONS if "indigenous" in self.batch_territory_types else []

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_categoria_options(self) -> List[str]:
        return _CATEGORIA_OPTIONS if "conservation" in self.batch_territory_types else []

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_esfera_options(self) -> List[str]:
        return _ESFERA_OPTIONS if "conservation" in self.batch_territory_types else []

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_grupo_options(self) -> List[str]:
        return _GRUPO_OPTIONS if "conservation" in self.batch_territory_types else []

    def _batch_apply_uf_filter(self, items: List[str]) -> List[str]:
        if not self.batch_selected_ufs:
            return items
        sel = set(self.batch_selected_ufs)
        uf_map = self.batch_territory_uf
        out = []
        for t in items:
            parts = {p.strip() for p in uf_map.get(t, "").split(",") if p.strip()}
            if sel & parts:
                out.append(t)
        return out

    def _batch_apply_value_filter(self, items: List[str], selected: List[str], value_map: Dict[str, str]) -> List[str]:
        if not selected:
            return items
        sel = set(selected)
        return [t for t in items if value_map.get(t, "") in sel]

    @rx.var(auto_deps=False, deps=[
        "batch_available_territories", "batch_territory_search",
        "batch_min_area_ha", "batch_max_area_ha", "batch_territory_area_ha",
        "batch_selected_ufs", "batch_territory_uf",
        "batch_selected_fase", "batch_territory_fase",
        "batch_selected_modalidade", "batch_territory_modalidade",
        "batch_selected_categoria", "batch_territory_categoria",
        "batch_selected_esfera", "batch_territory_esfera",
        "batch_selected_grupo", "batch_territory_grupo",
        "batch_sort_by",
    ])
    def batch_filtered_territories(self) -> List[str]:
        """Territory list filtered by search text, hectare range, UF, and attribute filters.

        auto_deps=False: most of the filtering happens inside plain helper
        methods (``_batch_apply_uf_filter`` etc.), one call frame away from
        this function's body, which Reflex's static dependency scan doesn't
        see — so every var actually read (directly or through those
        helpers) is declared explicitly rather than relying on detection.
        """
        out = self.batch_available_territories
        q = self.batch_territory_search.lower()
        if q:
            out = [t for t in out if q in t.lower()]
        areas = self.batch_territory_area_ha
        min_ha = self._batch_parse_ha(self.batch_min_area_ha)
        max_ha = self._batch_parse_ha(self.batch_max_area_ha)
        if min_ha is not None:
            out = [t for t in out if areas.get(t, 0) >= min_ha]
        if max_ha is not None:
            out = [t for t in out if areas.get(t, 0) <= max_ha]
        out = self._batch_apply_uf_filter(out)
        out = self._batch_apply_value_filter(out, self.batch_selected_fase, self.batch_territory_fase)
        out = self._batch_apply_value_filter(out, self.batch_selected_modalidade, self.batch_territory_modalidade)
        out = self._batch_apply_value_filter(out, self.batch_selected_categoria, self.batch_territory_categoria)
        out = self._batch_apply_value_filter(out, self.batch_selected_esfera, self.batch_territory_esfera)
        out = self._batch_apply_value_filter(out, self.batch_selected_grupo, self.batch_territory_grupo)
        if self.batch_sort_by == "name_desc":
            out = sorted(out, reverse=True)
        elif self.batch_sort_by == "area_asc":
            out = sorted(out, key=lambda t: areas.get(t, 0))
        elif self.batch_sort_by == "area_desc":
            out = sorted(out, key=lambda t: areas.get(t, 0), reverse=True)
        # "name_asc" (default): already alphabetical — batch_available_territories
        # is built from sorted(set(keys)) and no filter above reorders it.
        return out

    @rx.var(auto_deps=False, deps=["batch_active_steps"])
    def batch_active_rows(self) -> List[Dict[str, str]]:
        """Territories currently being processed, with the step each is on.

        Sorted by name so the list doesn't reshuffle every time one worker
        advances a step — with several running in parallel, dict order would
        otherwise jump around on every update.
        """
        return [
            {"territory": name, "step": step}
            for name, step in sorted(self.batch_active_steps.items())
        ]

    @rx.var
    def batch_progress_pct(self) -> int:
        """0–100 overall progress percentage."""
        done = len(self.batch_completed) + len(self.batch_failed)
        if not self.batch_total:
            return 0
        return min(100, int(done / self.batch_total * 100))

    @rx.var
    def batch_selected_count(self) -> int:
        return len(self.batch_selected_territories)

    # ---- Stage flow ---------------------------------------------------------

    @rx.var
    def batch_stage_effective(self) -> str:
        """Which stage the page actually shows.

        Forced to "run" from the moment a job is dispatched — `batch_starting`,
        not just `batch_running` — so the several seconds of configuration
        snapshot and abuse-control checks before the progress bar exists are
        spent looking at the Run stage saying so, rather than at a Start button
        that appears not to have done anything. `batch_reset()` clears all
        three flags, which drops the user back to whatever stage they were on.
        """
        if self.batch_starting or self.batch_running or self.batch_done:
            return "run"
        return self.batch_stage

    @rx.var
    def batch_busy(self) -> bool:
        """Dispatched but not yet finished — the window in which no second
        run may be started, and the Start button must not look clickable."""
        return self.batch_starting or self.batch_running

    def set_batch_stage(self, name: str):
        """Move to a stage. Ignores anything unrecognised rather than
        rendering an empty body."""
        if name in ("select", "configure", "run"):
            self.batch_stage = name

    def set_batch_config_groups(self, value):
        """The configuration accordion's own `on_value_change`.

        Typed loosely for the same reason as `state/_ui.py::set_open_groups`:
        Reflex's accordion event spec is shared with `type="single"`, which
        reports a bare string, so the signature has to accept both to pass
        its type check even though this accordion is always
        `type="multiple"`.
        """
        self.batch_config_groups = [value] if isinstance(value, str) else list(value)

    @rx.var
    def batch_capped_territories(self) -> List[str]:
        """The territory rows actually rendered.

        Purely presentational: unfiltered, the conservation list is 3,247
        entries and `rx.foreach` builds a DOM row for every one of them,
        which is most of what makes the selector slow to open on a phone.
        Every handler — `batch_select_all_filtered` above all — still works
        off the full `batch_filtered_territories`, so selecting "all
        filtered" selects all of them, not the visible 300.
        """
        return self.batch_filtered_territories[:BATCH_LIST_RENDER_CAP]

    @rx.var
    def batch_list_is_capped(self) -> bool:
        return len(self.batch_filtered_territories) > BATCH_LIST_RENDER_CAP

    # Explicit deps: the deferred `get_translations` import below defeats
    # Reflex's automatic dependency detection (it walks the source and cannot
    # resolve a relative import made inside the body), and an undetected
    # dependency means a stale note.
    @rx.var(auto_deps=False,
            deps=["language", "batch_filtered_territories"])
    def batch_list_capped_note(self) -> str:
        """"Showing the first 300 of 3,247 — refine your filters…".

        Built here rather than concatenated in the component: `AppState.tr[…]`
        is a Var, and a Var has no `.format`, so assembling it in the UI would
        mean splicing prefix/suffix keys around the numbers and pinning every
        language to English word order.
        """
        from ..utils.translations import get_translations

        total = len(self.batch_filtered_territories)
        if total <= BATCH_LIST_RENDER_CAP:
            return ""
        return get_translations(self.language)["batch_list_capped"].format(
            shown=BATCH_LIST_RENDER_CAP, total=total
        )

    @rx.var
    def batch_has_active_filters(self) -> bool:
        """True when any list-narrowing filter (not just the type toggle) is set."""
        return bool(
            self.batch_territory_search
            or self.batch_min_area_ha
            or self.batch_max_area_ha
            or self.batch_selected_ufs
            or self.batch_selected_fase
            or self.batch_selected_modalidade
            or self.batch_selected_categoria
            or self.batch_selected_esfera
            or self.batch_selected_grupo
        )

    @rx.var
    def batch_max_selection(self) -> int:
        """Exposes BATCH_MAX_SELECTION to the UI so the cap is never hardcoded twice."""
        return BATCH_MAX_SELECTION

    @rx.var(auto_deps=False, deps=["batch_selected_territories"])
    def batch_selected_territories_detail(self) -> List[Dict[str, str]]:
        """Per-selected-territory display info for the review panel.

        Resolved independently of which type is currently toggled in the
        list view — the selection can span both types, so each item's
        source is looked up on its own via ``_batch_resolve_territory_type``
        rather than assumed from the active view.
        """
        out: List[Dict[str, str]] = []
        for t in self.batch_selected_territories:
            ttype = self._batch_resolve_territory_type(t)
            if ttype == "conservation":
                from ..utils.conservation_service import get_conservation_unit_service
                svc = get_conservation_unit_service()
            else:
                from ..utils.territory_service import get_territory_service
                svc = get_territory_service()
            info = svc.get_territory_info(t) or {}
            ha = info.get("superficie_ha") or 0
            out.append({
                "name": t,
                "type": ttype,
                "uf": info.get("uf_sigla", "") or "",
                "ha": f"{ha:,.0f}" if ha else "",
            })
        return out

    @rx.var
    def batch_is_large_run(self) -> bool:
        """True when the current selection is large enough to risk exhausting
        the container's memory in one run (see BATCH_WARN_THRESHOLD).

        Heavier per-territory output (PNG maps, buffer analyses) lowers the
        safe threshold since each territory produces more files/figures.
        """
        threshold = BATCH_WARN_THRESHOLD
        if self.batch_run_pdf_maps or self.batch_buffer_enabled:
            threshold = BATCH_WARN_THRESHOLD_HEAVY
        return self.batch_selected_count > threshold

    @rx.var
    def batch_confirm_message(self) -> str:
        """Message shown by the friction step in front of run_batch_processing."""
        return (
            f"{self.tr['batch_confirm_prefix']} {self.batch_selected_count} "
            f"{self.tr['territories_word']}{self.tr['batch_confirm_suffix']}"
        )

    @rx.var
    def batch_is_territory_selected(self) -> Dict[str, bool]:
        """Lookup map for checkbox state (display key → bool)."""
        return {t: True for t in self.batch_selected_territories}

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_uf(self) -> Dict[str, str]:
        """display_key → normalised UF sigla string (e.g. "PA", "MT, PA").

        Returns ``""`` for keys with no data so the UI can render unconditionally.
        Siglas are comma+space separated regardless of how they are stored.
        """
        try:
            out: Dict[str, str] = {}
            for _type, svc in self._batch_active_services():
                for key in svc.get_all_display_keys():
                    info = svc.get_territory_info(key) or {}
                    raw = (info.get("uf_sigla") or "").strip()
                    # Normalise separators: "RR,AM,PA" → "RR, AM, PA"
                    if raw:
                        out[key] = ", ".join(p.strip() for p in raw.split(",") if p.strip())
            return out
        except Exception:
            return {}

    @rx.var(auto_deps=False, deps=["batch_territory_types"])
    def batch_territory_meta(self) -> Dict[str, str]:
        """display_key → one-line metadata string from the owning GeoPackage.

        Indigenous format: ``🪶 {etnia}   🏛 {fase}   📐 {area} ha``
        Conservation format: ``🌿 {categoria}   🏛 {esfera}   📐 {area} ha``
        Parts are omitted when missing; returns ``""`` for unknown keys.

        auto_deps=False: Reflex's dep introspection trips on relative imports,
        so we declare deps explicitly to react when the territory list or
        active types change.
        """
        try:
            out: Dict[str, str] = {}
            for type_name, svc in self._batch_active_services():
                is_conservation = type_name == "conservation"
                for key in svc.get_all_display_keys():
                    info = svc.get_territory_info(key) or {}
                    parts = []
                    if is_conservation:
                        cat = (info.get("categoria") or "").strip()
                        if cat:
                            parts.append(f"🌿 {cat}")
                        esfera = (info.get("esfera") or "").strip()
                        if esfera:
                            parts.append(f"🏛 {esfera}")
                    else:
                        etn = (info.get("etnia") or "").strip()
                        if etn:
                            parts.append(f"🪶 {etn}")
                        fase = (info.get("fase_ti") or "").strip()
                        if fase:
                            parts.append(f"🏛 {fase}")
                    ha = info.get("superficie_ha") or 0
                    if ha and ha > 0:
                        parts.append(f"📐 {ha:,.0f} ha")
                    out[key] = "   ".join(parts)
            return out
        except Exception:
            return {}

    def _batch_resolve_territory_type(self, key: str) -> str:
        """Which GeoPackage a selected display key actually belongs to.

        Selection can outlive the type-filter toggles (mixed indigenous +
        conservation runs), so this checks both services directly instead of
        trusting the current UI filter state.
        """
        from ..utils.territory_service import get_territory_service
        if get_territory_service().get_territory_info(key):
            return "indigenous"
        from ..utils.conservation_service import get_conservation_unit_service
        if get_conservation_unit_service().get_territory_info(key):
            return "conservation"
        return "indigenous"

    # ---- Selection helpers ---------------------------------------------------

    def batch_set_territory_search(self, q: str):
        self.batch_territory_search = q

    def batch_set_min_area_ha(self, v: str):
        self.batch_min_area_ha = v

    def batch_set_max_area_ha(self, v: str):
        self.batch_max_area_ha = v

    def batch_clear_area_filter(self):
        self.batch_min_area_ha = ""
        self.batch_max_area_ha = ""

    def batch_toggle_uf(self, uf: str):
        self._batch_toggle_filter_value("batch_selected_ufs", uf)

    def batch_toggle_fase(self, v: str):
        self._batch_toggle_filter_value("batch_selected_fase", v)

    def batch_toggle_modalidade(self, v: str):
        self._batch_toggle_filter_value("batch_selected_modalidade", v)

    def batch_toggle_categoria(self, v: str):
        self._batch_toggle_filter_value("batch_selected_categoria", v)

    def batch_toggle_esfera(self, v: str):
        self._batch_toggle_filter_value("batch_selected_esfera", v)

    def batch_toggle_grupo(self, v: str):
        self._batch_toggle_filter_value("batch_selected_grupo", v)

    def batch_set_sort_by(self, v: str):
        if v in ("name_asc", "name_desc", "area_asc", "area_desc"):
            self.batch_sort_by = v

    def batch_clear_all_filters(self):
        """Reset every territory-list filter (not the type toggle) to its default."""
        self.batch_territory_search = ""
        self.batch_min_area_ha = ""
        self.batch_max_area_ha = ""
        self.batch_selected_ufs = []
        self.batch_selected_fase = []
        self.batch_selected_modalidade = []
        self.batch_selected_categoria = []
        self.batch_selected_esfera = []
        self.batch_selected_grupo = []

    def batch_set_territory_type(self, t: str):
        """Switch which single GeoPackage backs the territory list view.

        Exclusive — exactly one of "indigenous"/"conservation" is active at
        a time, so the two toggle buttons are never both highlighted. The
        *selection* (checked territories) is NOT cleared on switch, so you
        can check some indigenous territories, switch the view to
        conservation, check some there too, and both end up in the same
        batch run — each one's actual source is resolved independently at
        run time (``_batch_resolve_territory_type``), not from this toggle.
        Filters reset since a search/attribute filter from one source
        rarely means anything for the other.
        """
        if t not in ("indigenous", "conservation") or self.batch_territory_types == [t]:
            return
        self.batch_territory_types = [t]
        self.batch_clear_all_filters()

    # ---- Paste/upload list → auto-select -------------------------------------

    def batch_set_paste_text(self, txt: str):
        self.batch_paste_text = txt

    def batch_clear_paste(self):
        self.batch_paste_text = ""
        self.batch_paste_feedback = ""
        self.batch_paste_unmatched = []

    def batch_select_from_list(self):
        """Match the pasted name list against the active source and select hits.

        Matching is accent-stripped and case-insensitive (so "Apinaye" finds
        "Apinayé", and conservation-unit names match regardless of casing).
        A name that equals the base of duplicate display keys — e.g.
        "{nome} (cod)" pairs — selects every key sharing that base name.
        Matches are ADDED to the current selection; misses are listed.
        """
        self.batch_confirm_pending = False
        import re
        import unicodedata

        def _norm(s: str) -> str:
            s = unicodedata.normalize("NFD", str(s)).encode("ascii", "ignore").decode("ascii")
            return re.sub(r"\s+", " ", s).strip().lower()

        names = [
            p.strip()
            for chunk in self.batch_paste_text.replace(";", "\n").splitlines()
            for p in [chunk]
            if p.strip()
        ]
        if not names:
            self.batch_paste_feedback = "Paste one name per line first."
            self.batch_paste_unmatched = []
            return

        keys = list(self.batch_available_territories)
        exact = {_norm(k): k for k in keys}
        base_map: Dict[str, List[str]] = {}
        for k in keys:
            base = re.sub(r"\s*\([^)]*\)\s*$", "", k)
            base_map.setdefault(_norm(base), []).append(k)

        current = set(self.batch_selected_territories)
        matched = 0
        capped = 0
        unmatched: List[str] = []
        for name in names:
            n = _norm(name)
            if n in exact:
                hit_keys = [exact[n]]
            elif n in base_map:
                hit_keys = base_map[n]
            else:
                unmatched.append(name)
                continue
            matched += 1
            for k in hit_keys:
                if k in current:
                    continue
                if len(current) >= BATCH_MAX_SELECTION:
                    capped += 1
                    continue
                current.add(k)

        self.batch_selected_territories = sorted(current)
        self.batch_paste_unmatched = unmatched
        src = " + ".join(
            "conservation units" if t == "conservation" else "indigenous lands"
            for t in self.batch_territory_types
        )
        cap_note = (
            f" ⚠ {capped} not added — {BATCH_MAX_SELECTION} max reached." if capped else ""
        )
        self.batch_paste_feedback = (
            f"✓ Matched {matched} of {len(names)} names against {src} — "
            f"{len(self.batch_selected_territories)} selected total.{cap_note}"
        )

    async def batch_upload_territory_list(self, files: List[rx.UploadFile]):
        """Read an uploaded .txt/.csv name list into the paste box and select."""
        try:
            if not files:
                return
            data = await files[0].read()
            text = data.decode("utf-8", errors="replace")
            # CSV convenience: keep only the first column
            lines = []
            for ln in text.splitlines():
                lines.append(ln.split(",")[0] if "," in ln else ln)
            self.batch_paste_text = "\n".join(lines)
            self.batch_select_from_list()
        except Exception as e:
            logger.error(f"[BATCH] list upload failed: {e}", exc_info=True)
            self.error_message = f"List upload failed: {e}"

    def batch_toggle_territory(self, territory: str):
        """Add or remove a territory from the batch selection (capped at BATCH_MAX_SELECTION)."""
        self.batch_confirm_pending = False
        if territory in self.batch_selected_territories:
            self.batch_selected_territories = [
                t for t in self.batch_selected_territories if t != territory
            ]
            return
        if len(self.batch_selected_territories) >= BATCH_MAX_SELECTION:
            self.error_message = (
                f"Selection limit reached ({BATCH_MAX_SELECTION} territories max) — "
                f"remove one before adding another."
            )
            return
        self.batch_selected_territories = self.batch_selected_territories + [territory]

    def batch_select_all_filtered(self):
        """Add currently-filtered territories to the selection, up to BATCH_MAX_SELECTION total."""
        self.batch_confirm_pending = False
        current = set(self.batch_selected_territories)
        room = BATCH_MAX_SELECTION - len(current)
        added = 0
        capped = 0
        for t in self.batch_filtered_territories:
            if t in current:
                continue
            if added >= room:
                capped += 1
                continue
            current.add(t)
            added += 1
        self.batch_selected_territories = sorted(current)
        if capped > 0:
            self.error_message = (
                f"Added {added} — selection capped at {BATCH_MAX_SELECTION} total "
                f"({capped} more matched but weren't added; narrow your filters or "
                f"remove some first)."
            )

    def batch_clear_selection(self):
        self.batch_selected_territories = []
        self.batch_confirm_pending = False

    def batch_toggle_review(self):
        """Toggle the selected-territories review panel."""
        self.batch_show_review = not self.batch_show_review

    def batch_set_year(self, year: str):
        try:
            int(year)  # validation
            self.batch_year = year
        except (ValueError, TypeError):
            pass

    def batch_set_year2(self, year: str):
        try:
            int(year)
            self.batch_year2 = year
        except (ValueError, TypeError):
            pass

    def batch_set_hansen_year(self, year: str):
        self.batch_hansen_year = year

    def batch_set_buffer_km(self, km: str):
        if km in ("1", "2", "5", "10", "20"):
            self.batch_buffer_km = km

    def batch_toggle_run_mapbiomas(self, val: bool):
        self.batch_run_mapbiomas = val

    def batch_toggle_run_comparison(self, val: bool):
        self.batch_run_comparison = val

    def batch_toggle_run_treemap(self, val: bool):
        self.batch_run_treemap = val

    def batch_toggle_run_glad(self, val: bool):
        self.batch_run_glad = val

    def batch_toggle_run_gfc(self, val: bool):
        self.batch_run_gfc = val

    def batch_toggle_run_pdf_maps(self, val: bool):
        self.batch_run_pdf_maps = val

    # ── Figure export / timeline-band toggles ────────────────────────────
    def batch_toggle_export_png(self, val: bool):
        self.batch_export_png = val

    def batch_toggle_png_high_res(self, val: bool):
        self.batch_png_high_res = val

    def batch_toggle_timeline_political(self, val: bool):
        self.batch_timeline_political = val

    def batch_toggle_timeline_policy(self, val: bool):
        self.batch_timeline_policy = val

    def batch_toggle_timeline_enso(self, val: bool):
        self.batch_timeline_enso = val

    @rx.var
    def batch_png_scale(self) -> float:
        """Kaleido scale for this run's figures.

        0.6 read too soft at the default tier — doubled both tiers so "high
        res" stays a meaningful step above the default rather than becoming
        redundant with it.
        """
        return 2.0 if self.batch_png_high_res else 1.2

    # ── Auxiliary-layer toggles ──────────────────────────────────────────
    def batch_toggle_aux_deforestation(self, val: bool):
        self.batch_run_aux_deforestation = val

    def batch_toggle_aux_fire_scar(self, val: bool):
        self.batch_run_aux_fire_scar = val

    def batch_toggle_aux_fire_frequency(self, val: bool):
        self.batch_run_aux_fire_frequency = val

    def batch_toggle_aux_fire_year_last(self, val: bool):
        self.batch_run_aux_fire_year_last = val

    def batch_toggle_aux_mining_substances(self, val: bool):
        self.batch_run_aux_mining_substances = val

    def batch_toggle_aux_agriculture_cycles(self, val: bool):
        self.batch_run_aux_agriculture_cycles = val

    def batch_toggle_run_deforestation_timeline(self, val: bool):
        self.batch_run_deforestation_timeline = val

    # ── Multi-window MapBiomas setters ────────────────────────────────────
    def batch_toggle_run_multi_window(self, val: bool):
        self.batch_run_multi_window = val

    def batch_set_multi_window_mode(self, mode: str):
        if mode in ("constant", "custom"):
            self.batch_multi_window_mode = mode

    def batch_set_multi_window_step(self, step: str):
        if step in ("1", "2", "4", "5", "8"):
            self.batch_multi_window_step = step

    def batch_set_multi_window_custom_years(self, txt: str):
        self.batch_multi_window_custom_years = txt

    @rx.var
    def batch_multi_window_resolved_years(self) -> List[int]:
        """Compute the active year list for the multi-window analysis.

        Constant mode: start at 1985, take steps of ``batch_multi_window_step``
        years, always include 2024 as the final year. Custom mode: parse the
        comma-separated text and keep 3 to 10 valid years between 1985 and 2024.
        Returns an empty list when the input is invalid.
        """
        START, END = 1985, 2024
        try:
            if self.batch_multi_window_mode == "custom":
                raw = [p.strip() for p in self.batch_multi_window_custom_years.split(",") if p.strip()]
                years: List[int] = []
                for p in raw:
                    try:
                        y = int(p)
                    except ValueError:
                        continue
                    if START <= y <= END and y not in years:
                        years.append(y)
                years.sort()
                if 3 <= len(years) <= 10:
                    return years
                return []
            # constant mode
            step = int(self.batch_multi_window_step)
            if step <= 0:
                return []
            years = list(range(START, END + 1, step))
            if years[-1] != END:
                years.append(END)
            return years
        except Exception:
            return []

    def batch_toggle_buffer_enabled(self, val: bool):
        self.batch_buffer_enabled = val

    def request_batch_run(self):
        """Friction step in front of run_batch_processing (see abuse_control.py
        for the actual server-side enforcement — this only deters a reflexive
        click, since a script can call run_batch_processing directly).

        Also the double-dispatch guard. This handler is synchronous, so two
        clicks arrive as two events processed in order against the same state:
        setting `batch_starting` here, before returning, is enough for the
        second one to find the door shut. Doing it in `run_batch_processing`
        instead would be too late — it is a background task, and it does not
        set `batch_running` until after two awaited abuse-control checks.
        """
        if not self.batch_selected_territories:
            return None
        if self.batch_starting or self.batch_running:
            return None
        if self.batch_confirm_pending:
            self.batch_confirm_pending = False
            self.batch_starting = True
            return type(self).run_batch_processing()
        self.batch_confirm_pending = True
        return None

    def cancel_batch_run(self):
        self.batch_confirm_pending = False
        self.batch_starting = False

    def batch_stop(self):
        """Signal the running batch to stop after the current territory."""
        self.batch_running = False
        self.batch_starting = False
        self.batch_confirm_pending = False
        self._batch_append_log("⏹ Stop requested — will halt after current territory")

    def _batch_append_log(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.batch_log = self.batch_log + [f"[{ts}] {line}"]
        # Keep the last 200 lines to avoid unbounded growth
        if len(self.batch_log) > 200:
            self.batch_log = self.batch_log[-200:]

    # ---- Download -----------------------------------------------------------

    def download_batch_zip(self):
        """Download the completed batch ZIP (signed GCS URL in production —
        see export_service.get_download_url — since Cloud Run's own proxy
        caps app-proxied responses around 32 MiB, well under batch ZIP size)."""
        if not self.batch_zip_relpath:
            self.error_message = "Batch ZIP not ready yet"
            return
        from ..utils.export_service import get_download_url
        return rx.download(
            url=get_download_url(self.batch_zip_relpath),
            filename=self.batch_zip_relpath.rsplit("/", 1)[-1],
        )

    def batch_reset(self):
        """Reset batch state for a new run."""
        self.batch_zip_relpath = ""
        self.batch_running = False
        self.batch_starting = False
        self.batch_done = False
        self.batch_confirm_pending = False
        self.batch_zip_ready = False
        self.batch_current_territory = ""
        self.batch_current_step = ""
        self.batch_active_steps = {}
        self.batch_completed = []
        self.batch_failed = []
        self.batch_errors = {}
        self.batch_total = 0
        self.batch_log = []

    # ---- Main background task -----------------------------------------------

    @rx.event(background=True)
    async def run_batch_processing(self):
        """
        Background task: iterate territories, run analysis, build ZIP.

        All EE calls are dispatched via ``run_in_executor`` to avoid blocking
        the async event loop.  State is mutated only inside ``async with self``
        blocks so Reflex can push WebSocket deltas to the frontend.
        """
        # ── Snapshot configuration ──────────────────────────────────────────
        async with self:
            territories = list(self.batch_selected_territories)
            try:
                year1 = int(self.batch_year)
                year2 = int(self.batch_year2)
            except (ValueError, TypeError):
                self.error_message = "Invalid year selection."
                self.batch_starting = False
                return
            hansen_year = str(self.batch_hansen_year)
            buf_km = float(self.batch_buffer_km)
            buf_enabled = bool(self.batch_buffer_enabled)
            run_mb = bool(self.batch_run_mapbiomas)
            run_cmp = bool(self.batch_run_comparison)
            run_treemap = bool(self.batch_run_treemap)
            run_glad = bool(self.batch_run_glad)
            run_gfc = bool(self.batch_run_gfc)
            run_maps = bool(self.batch_run_pdf_maps)
            run_multi = bool(self.batch_run_multi_window)
            aux_layer_keys: List[str] = []
            if self.batch_run_aux_deforestation:    aux_layer_keys.append("deforestation_secondary")
            if self.batch_run_aux_fire_scar:        aux_layer_keys.append("fire_scar_size")
            if self.batch_run_aux_fire_frequency:   aux_layer_keys.append("fire_frequency")
            if self.batch_run_aux_fire_year_last:   aux_layer_keys.append("fire_year_last")
            if self.batch_run_aux_mining_substances:aux_layer_keys.append("mining_substances")
            if self.batch_run_aux_agriculture_cycles:aux_layer_keys.append("agriculture_cycles")
            run_timeline = bool(self.batch_run_deforestation_timeline)
            # Resolved per-territory (not a single global value) so a run can
            # mix indigenous lands and conservation units in one selection.
            territory_type_map: Dict[str, str] = {
                t: self._batch_resolve_territory_type(t) for t in self.batch_selected_territories
            }
            multi_years: List[int] = list(self.batch_multi_window_resolved_years) if run_multi else []
            if run_multi and len(multi_years) < 2:
                # Invalid input — disable for this run to avoid wasted EE calls.
                run_multi = False
                multi_years = []

            if not territories:
                self.error_message = "No territories selected for batch processing."
                self.batch_starting = False
                return
            if len(territories) > BATCH_MAX_SELECTION:
                # Defense in depth — every UI path that adds to the selection
                # already enforces this, but never run past the cap even if
                # it's somehow bypassed.
                self.error_message = (
                    f"Selection exceeds the {BATCH_MAX_SELECTION}-territory "
                    f"limit ({len(territories)} selected) — remove some before running."
                )
                self.batch_starting = False
                return

            # Captured now (inside the state lock) for the abuse-control check
            # right below — router.session is only reachable through self.
            client_ip = self.router.session.client_ip
            client_token = self.router.session.client_token
            session_id = self.router.session.session_id

        # ── Abuse control ────────────────────────────────────────────────────
        # Enforcement, not the friction step (request_batch_run) — checked here
        # regardless of how run_batch_processing was reached, since a script
        # calling it directly over the WebSocket skips the UI confirm entirely.
        # See utils/abuse_control.py and docs/ABUSE_CONTROL.md.
        from ..utils import abuse_control
        loop = asyncio.get_event_loop()
        # Wrapped because these are the last awaits before `batch_running`
        # takes over the double-dispatch guard: an exception escaping here
        # would leave `batch_starting` set with no run behind it, and the UI
        # would sit on "Starting…" forever with Start refusing every click.
        # The Stop button stays mounted through `batch_busy` as a second
        # line of defence, but a stall the user has to notice and clear by
        # hand is not a resting state worth shipping.
        try:
            ok, reason = await loop.run_in_executor(
                None, abuse_control.check_session_cooldown, client_token
            )
            if ok:
                ok, reason = await loop.run_in_executor(
                    None, abuse_control.check_ip_rate_limit, client_ip
                )
            abuse_control.log_event(
                ip=client_ip, client_token=client_token, session_id=session_id,
                action="batch_run", outcome="allowed" if ok else "refused",
                detail={"n_territories": len(territories)},
            )
        except Exception as guard_err:
            logger.error("Abuse-control check failed: %s", guard_err, exc_info=True)
            async with self:
                self.error_message = (
                    "Could not start the run — the rate-limit check failed. "
                    "Try again in a moment."
                )
                self.batch_starting = False
            return
        if not ok:
            async with self:
                self.error_message = reason
                self.batch_starting = False
            return

        async with self:
            # `batch_running` takes over the guard from here; every early
            # return above clears `batch_starting` itself, since none of them
            # ever reach this line.
            self.batch_starting = False
            self.batch_running = True
            self.batch_done = False
            self.batch_zip_ready = False
            self.batch_zip_relpath = ""
            self.batch_total = len(territories)
            self.batch_completed = []
            self.batch_failed = []
            self.batch_errors = {}
            self.batch_log = []
            self.batch_current_territory = ""
            self.batch_current_step = ""
            self.batch_active_steps = {}
            self._batch_append_log(
                f"Starting batch: {len(territories)} territories, "
                f"MapBiomas {year1}/{year2}, Hansen GLAD {hansen_year}, "
                f"buffer={'%.0f km' % buf_km if buf_enabled else 'off'}"
            )

        # loop already bound above, ahead of the abuse-control check.

        # Every blocking non-EE, non-render call below goes to this pool rather
        # than to ``run_in_executor(None, …)``. asyncio's default executor is
        # sized off the core count (6 threads on 2 vCPU) and would cap the run
        # well below the territory width — see get_io_executor().
        from ..utils.ee_concurrency import get_io_executor
        io_pool = get_io_executor()

        # ── Ensure Earth Engine is initialised before the first EE call ───────
        # The batch entry-point can be reached directly from the portal without
        # ever touching the territory-analysis page that lazily initialises EE
        # via ``get_ee()``. On Cloud Run that means the very first
        # ``ee.Geometry(...)`` blows up with "client library not initialized".
        # ``initialize_earth_engine()`` is idempotent (guarded by a module-level
        # flag), so calling it here is free when EE is already set up locally.
        try:
            def _ee_init():
                from ..utils.ee_service import initialize_earth_engine
                return initialize_earth_engine()
            await loop.run_in_executor(io_pool, _ee_init)
            # Only possible once the session exists (i.e. after ee.Initialize).
            from ..utils.ee_concurrency import tune_ee_connection_pool
            await loop.run_in_executor(io_pool, tune_ee_connection_pool)
        except Exception as ee_err:
            async with self:
                self._batch_append_log(f"❌ Earth Engine init failed: {ee_err}")
                self.error_message = (
                    "Earth Engine init failed — check EE_PRIVATE_KEY / "
                    "EE_SERVICE_ACCOUNT_EMAIL env vars on the Cloud Run service, "
                    "or grant the runtime service account access to Earth Engine."
                )
                self.batch_starting = False
                self.batch_running = False
                self.batch_done = True
            logger.error(f"EE init failed in batch: {ee_err}", exc_info=True)
            return

        # Results are written as plain files into a live run folder under
        # uploaded_files/exports/ — visible (and downloadable via /_upload) the
        # moment each one is produced, with no inline compression slowing the
        # per-territory loop. The folder is deflated into the final ZIP once,
        # at the end of the run. Memory stays flat at any archive size.
        from ..utils.export_service import (
            DirExportWriter, get_export_dir, prune_old_exports, zip_directory,
        )
        # Seconds in the name: concurrent runs (e.g. two browsers) must never
        # share a folder
        run_name = f"yvynation_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        zip_filename = f"{run_name}.zip"
        zip_path = get_export_dir() / zip_filename
        work_dir = get_export_dir() / run_name
        batch_summary: List[Dict] = []

        # ── Concurrency budget for this run ─────────────────────────────────
        # Territories run in parallel; within each one every independent Earth
        # Engine analysis is issued at once.  Rendering (kaleido / pyplot) is
        # serialized on its own single-worker pool, so the win here is
        # pipelining: while one territory renders its charts and maps, the
        # others are waiting on Earth Engine.
        from ..utils.ee_concurrency import (
            IO_CONCURRENCY, TIER, describe_budget, describe_meters,
            effective_territory_concurrency, meter_report, reset_meters,
        )
        reset_meters()
        n_workers = effective_territory_concurrency(
            len(territories),
            heavy=(run_maps or run_timeline or buf_enabled),
        )
        async with self:
            self._batch_append_log(
                f"📂 Files appear live in uploaded_files/exports/{run_name}/"
            )
            self._batch_append_log(describe_budget(n_workers))

        # Per-territory stage timing. ``_stage_open`` holds the step a territory
        # is currently in; ``_stage_totals`` accumulates seconds per step. Both
        # are only touched from the event loop, so no lock is needed.
        _stage_open: Dict[str, Any] = {}
        _stage_totals: Dict[str, Dict[str, float]] = {}
        _territory_span: Dict[str, Any] = {}

        def _stage_report() -> Dict[str, Any]:
            """Where each territory's wall time went, and how much overlapped.

            ``concurrent_fraction`` is (sum of per-territory spans) / (wall time
            of the whole territory phase). At 1.0 nothing overlapped; near
            *n_workers* every worker was busy the whole time. A high value with
            slow individual territories means fair-share interleaving — each
            territory is getting 1/N of the pools — not a synchronisation
            barrier. Lowering the territory width trades total throughput for
            territories that *complete* sooner, one after another.
            """
            spans = [(a, b) for a, b in _territory_span.values() if b]
            if not spans:
                return {}
            wall = max(b for _, b in spans) - min(a for a, _ in spans)
            busy = sum(b - a for a, b in spans)
            per_stage: Dict[str, float] = {}
            for acc in _stage_totals.values():
                for label, secs in acc.items():
                    per_stage[label] = per_stage.get(label, 0.0) + secs
            slowest = sorted(
                (((b - a), t) for t, (a, b) in _territory_span.items() if b),
                reverse=True,
            )[:5]
            return {
                "stages": {
                    "phase_wall_s": round(wall, 1),
                    "territory_time_total_s": round(busy, 1),
                    "concurrent_fraction": round(busy / wall, 2) if wall else 0,
                    "seconds_by_stage": {
                        k: round(v, 1) for k, v in
                        sorted(per_stage.items(), key=lambda kv: -kv[1])
                    },
                    "slowest_territories": [
                        {"territory": t, "seconds": round(d, 1)} for d, t in slowest
                    ],
                }
            }

        async def _set_step(terr: str, text: str):
            """Publish *terr*'s current step to the UI.

            With several territories in flight there is no single current step,
            so each worker updates its own slot; the scalar vars mirror the most
            recent update for the parts of the UI that still read them.
            """
            # Close out the previous step's timing before switching. This is
            # what distinguishes "this stage is slow" from "this territory was
            # queued behind eleven others" — with N territories sharing the
            # pools, every one of them advances at ~1/N speed and they arrive at
            # each stage together, which looks like a barrier but is not one.
            now = time.monotonic()
            prev = _stage_open.get(terr)
            if prev is not None:
                label, started = prev
                acc = _stage_totals.setdefault(terr, {})
                acc[label] = acc.get(label, 0.0) + (now - started)
            _stage_open[terr] = (text, now)

            async with self:
                self.batch_active_steps = {**self.batch_active_steps, terr: text}
                self.batch_current_territory = terr
                self.batch_current_step = text

        # Run-scoped PNG policy for every section writer, however deeply nested.
        # Read from state once here rather than per figure: all render lanes
        # share the value, so it must not change mid-run.
        from ..utils.export_service import figure_export
        async with self:
            _png_on, _png_scale = self.batch_export_png, self.batch_png_scale
            self._batch_append_log(
                f"🖼 Figures: HTML always · PNG "
                + (f"on (scale {_png_scale:g})" if _png_on
                   else "off — saves ~90% of archive size")
            )

        with figure_export(png=_png_on, scale=_png_scale), \
                DirExportWriter(work_dir) as master_zf:

            async def _process_territory(territory: str):
                t_result: Dict[str, Any] = {"territory": territory, "status": "error"}

                try:
                    # ─── Step 1: EE geometry (instant, local GeoPackage) ────
                    def _get_ee_geom(terr=territory, ttype=territory_type_map[territory]):
                        if ttype == "conservation":
                            from ..utils.conservation_service import get_conservation_unit_service
                            svc = get_conservation_unit_service()
                        else:
                            from ..utils.territory_service import get_territory_service
                            svc = get_territory_service()
                        geojson = svc.get_geojson_for_key(terr)
                        if geojson is None:
                            raise ValueError(f"Territory not found in GeoPackage: {terr}")
                        from ..utils.buffer_utils import convert_geojson_to_ee_geometry
                        ee_geom = convert_geojson_to_ee_geometry(geojson, terr)
                        if ee_geom is None:
                            raise ValueError(f"Unusable geometry for territory: {terr}")
                        return ee_geom, geojson

                    ee_geom, raw_geojson = await loop.run_in_executor(io_pool, _get_ee_geom)

                    # ─── Buffer EE geometry ─────────────────────────────────
                    buf_ee_geom = None
                    if buf_enabled:
                        def _make_buffer(geom=ee_geom, km=buf_km):
                            from ..utils.buffer_utils import create_external_buffer
                            return create_external_buffer(geom, km)
                        try:
                            buf_ee_geom = await loop.run_in_executor(io_pool, _make_buffer)
                        except Exception as be:
                            logger.warning(f"Buffer creation failed (non-fatal): {be}")

                    # ─── Decide regions: 1 region or 4 quadrants ─────────────
                    # Large territories (>2 M ha) time out in EE when buffered
                    # — split them into four bounding-box quadrants and run
                    # the whole pipeline on each.  Each quadrant becomes its
                    # own sub-folder in the ZIP (nw/, ne/, sw/, se/).
                    def _get_area_and_shapely(terr=territory, ttype=territory_type_map[territory]):
                        if ttype == "conservation":
                            from ..utils.conservation_service import get_conservation_unit_service
                            svc = get_conservation_unit_service()
                        else:
                            from ..utils.territory_service import get_territory_service
                            svc = get_territory_service()
                        info = svc.get_territory_info(terr)
                        row = svc._get_geom_row(terr)
                        return info.get("superficie_ha", 0), (row.geometry if row is not None else None)

                    try:
                        area_ha, shapely_geom = await loop.run_in_executor(
                            io_pool, _get_area_and_shapely
                        )
                    except Exception:
                        area_ha, shapely_geom = 0, None

                    if area_ha > SPLIT_THRESHOLD_HA and shapely_geom is not None:
                        regions = _make_quadrant_regions(ee_geom, buf_ee_geom, shapely_geom)
                        async with self:
                            self._batch_append_log(
                                f"  ⚙ Large territory ({area_ha:,.0f} ha) — splitting into "
                                f"{len(regions)} quadrants: {', '.join(r[0].upper() for r in regions)}"
                            )
                    else:
                        regions = [("", ee_geom, buf_ee_geom)]

                    # Accumulate (region_name, ee_geom, gfc_result) for maps +
                    # timeline tasks that run after the regions loop.
                    region_map_data: List[tuple] = []

                    # Timeline series, filled by the per-region fan-out below.
                    # Deliberately NOT a second round of requests after the
                    # regions loop: the EE pool is FIFO, so work submitted late
                    # queues behind every job of every territory that started
                    # since — a nearly-finished territory would wait for
                    # newcomers' MapBiomas and Hansen before its last two calls
                    # ran. Submitting everything a territory needs in one batch
                    # is what lets it finish and release its worker.
                    tl_series: Dict[Any, Any] = {}
                    tl_y0, tl_y1 = int(year1), int(year2)
                    if tl_y1 < tl_y0:
                        tl_y0, tl_y1 = tl_y1, tl_y0

                    for region_name, region_ee_geom, region_buf_geom in regions:
                        rlabel = f" [{region_name.upper()}]" if region_name else ""
                        rsuffix = f" ({region_name.upper()})" if region_name else ""

                        # Per-region result containers
                        mb_y1_result = mb_y2_result = cmp_result = None
                        glad_result = gfc_result = None
                        buf_mb_result = buf_cmp_result = None
                        buf_glad_result = buf_gfc_result = None
                        multi_window_result = None      # territory multi-window
                        buf_multi_window_result = None  # buffer multi-window

                        if region_name:
                            async with self:
                                self._batch_append_log(f"  ▸ Quadrant {region_name.upper()}…")

                        # ─── Steps 2-10: every Earth Engine analysis, at once ──
                        # These all read the same region geometry and write
                        # separate result slots — none consumes another's
                        # output — so they are issued together and the region's
                        # wall time collapses from the sum of the calls to the
                        # slowest single one.  Total in-flight requests stay
                        # bounded by the shared EE pool (utils/ee_concurrency),
                        # so widening this never exceeds the tier budget no
                        # matter how many territories/quadrants are running.
                        def _mb_y1(geom=region_ee_geom, yr=year1):
                            from ..utils.ee_service_extended import get_ee_service
                            svc = get_ee_service()
                            return svc.analyze_mapbiomas(geom, yr)

                        def _mb_y2(geom=region_ee_geom, yr=year2):
                            from ..utils.ee_service_extended import get_ee_service
                            svc = get_ee_service()
                            return svc.analyze_mapbiomas(geom, yr)

                        def _cmp(geom=region_ee_geom, y1=year1, y2=year2):
                            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                            from ..utils.visualization import calculate_gains_losses
                            analyzer = get_mapbiomas_analyzer()
                            df_y1 = analyzer.analyze_single_year(geom, y1, scale=30)
                            df_y2 = analyzer.analyze_single_year(geom, y2, scale=30)
                            comp_df = calculate_gains_losses(df_y1, df_y2)
                            if comp_df is not None and not comp_df.empty:
                                gains_ha = float(comp_df.loc[comp_df["Change_ha"] > 0, "Change_ha"].sum())
                                losses_ha = float(comp_df.loc[comp_df["Change_ha"] < 0, "Change_ha"].sum())
                                net_ha = gains_ha + losses_ha
                            else:
                                gains_ha = losses_ha = net_ha = 0.0
                            transitions = {}
                            try:
                                raw_trans = analyzer.compute_transitions(geom, y1, y2, 30)
                                if raw_trans:
                                    transitions = {str(k): v for k, v in raw_trans.items()}
                            except Exception:
                                pass
                            rows = []
                            name_col = "Class_Name" if "Class_Name" in df_y2.columns else "Class"
                            for _, row in df_y2.iterrows():
                                cls = row[name_col]
                                a1 = float(
                                    df_y1.loc[df_y1[name_col] == cls, "Area_ha"].sum()
                                ) if not df_y1.empty else 0
                                a2 = float(row["Area_ha"])
                                rows.append({
                                    "Class": cls, f"Area_{y1}_ha": a1,
                                    f"Area_{y2}_ha": a2, "Change_ha": a2 - a1,
                                })
                            return {
                                "territory": territory,
                                "year_start": y1, "year_end": y2,
                                "data": rows,
                                "gains_ha": gains_ha,
                                "losses_ha": losses_ha,
                                "net_ha": net_ha,
                                "transitions": transitions,
                                "_raw_y1": df_y1.to_dict("records"),
                                "_raw_y2": df_y2.to_dict("records"),
                            }

                        def _glad(geom=region_ee_geom, yr=hansen_year):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            return analyzer.get_area_distribution(geom, year=int(yr), scale=30)

                        def _gfc(geom=region_ee_geom):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            return analyzer.analyze_gfc(geom)

                        # region_buf_geom is the FULL territory's buffer ring
                        # clipped to this quadrant's bounding box — built BEFORE
                        # the regions loop so the buffer is geometrically correct
                        # (not separate per-quadrant buffers).
                        def _buf_mb(geom=region_buf_geom, yr=year1):
                            from ..utils.ee_service_extended import get_ee_service
                            svc = get_ee_service()
                            return svc.analyze_mapbiomas(geom, yr)

                        def _buf_cmp(geom=region_buf_geom, y1=year1, y2=year2):
                            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                            from ..utils.visualization import calculate_gains_losses
                            analyzer = get_mapbiomas_analyzer()
                            df1b = analyzer.analyze_single_year(geom, y1, scale=30)
                            df2b = analyzer.analyze_single_year(geom, y2, scale=30)
                            comp_df = calculate_gains_losses(df1b, df2b)
                            if comp_df is not None and not comp_df.empty:
                                gains_ha = float(comp_df.loc[comp_df["Change_ha"] > 0, "Change_ha"].sum())
                                losses_ha = float(comp_df.loc[comp_df["Change_ha"] < 0, "Change_ha"].sum())
                                net_ha = gains_ha + losses_ha
                            else:
                                gains_ha = losses_ha = net_ha = 0.0
                            transitions = {}
                            try:
                                raw_trans = analyzer.compute_transitions(geom, y1, y2, 30)
                                if raw_trans:
                                    transitions = {str(k): v for k, v in raw_trans.items()}
                            except Exception:
                                pass
                            rows = []
                            nc = "Class_Name" if "Class_Name" in df2b.columns else "Class"
                            for _, row in df2b.iterrows():
                                cls = row[nc]
                                a1 = float(df1b.loc[df1b[nc] == cls, "Area_ha"].sum()) if not df1b.empty else 0
                                a2 = float(row["Area_ha"])
                                rows.append({"Class": cls, f"Area_{y1}_ha": a1,
                                             f"Area_{y2}_ha": a2, "Change_ha": a2 - a1})
                            return {
                                "territory": f"{territory} - Buffer {buf_km:g}km",
                                "year_start": y1, "year_end": y2,
                                "data": rows,
                                "gains_ha": gains_ha,
                                "losses_ha": losses_ha,
                                "net_ha": net_ha,
                                "transitions": transitions,
                                "_raw_y1": df1b.to_dict("records"),
                                "_raw_y2": df2b.to_dict("records"),
                            }

                        def _buf_glad(geom=region_buf_geom, yr=hansen_year):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            return analyzer.get_area_distribution(geom, year=int(yr), scale=30)

                        def _buf_gfc(geom=region_buf_geom):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            r = analyzer.analyze_gfc(geom)
                            return r if r and "error" not in r else None

                        def _multi(geom=region_ee_geom, years=tuple(multi_years)):
                            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                            analyzer = get_mapbiomas_analyzer()
                            pairs = []
                            for ya, yb in zip(years[:-1], years[1:]):
                                try:
                                    tr = analyzer.compute_transitions(
                                        geom, ya, yb, 30,
                                        include_unchanged=True,
                                    )
                                except Exception:
                                    tr = {}
                                pairs.append({
                                    "year_from": int(ya),
                                    "year_to": int(yb),
                                    "transitions": {str(k): v for k, v in (tr or {}).items()},
                                })
                            return pairs

                        def _buf_multi(geom=region_buf_geom, years=tuple(multi_years)):
                            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                            analyzer = get_mapbiomas_analyzer()
                            pairs = []
                            for ya, yb in zip(years[:-1], years[1:]):
                                try:
                                    tr = analyzer.compute_transitions(
                                        geom, ya, yb, 30,
                                        include_unchanged=True,
                                    )
                                except Exception:
                                    tr = {}
                                pairs.append({
                                    "year_from": int(ya),
                                    "year_to": int(yb),
                                    "transitions": {str(k): v for k, v in (tr or {}).items()},
                                })
                            return pairs

                        # ── Assemble the job list ────────────────────────────
                        has_buf = buf_enabled and region_buf_geom is not None
                        do_multi = run_multi and len(multi_years) >= 2

                        jobs: List[tuple] = []
                        if run_mb:
                            jobs.append(("mb_y1", _mb_y1, f"MapBiomas {year1}{rsuffix}"))
                        if run_mb or run_cmp:
                            jobs.append(("mb_y2", _mb_y2, f"MapBiomas {year2}{rsuffix}"))
                        # The comparison used to be gated on both MapBiomas
                        # results being non-empty, which it cannot be until they
                        # return.  That gate is re-applied after the gather
                        # instead; `run_mb` is required here because mb_y1 only
                        # runs when it is on, so the gate could never pass
                        # otherwise — the semantics are unchanged.
                        if run_cmp and run_mb:
                            jobs.append(("cmp", _cmp, f"Comparison {year1}→{year2}{rsuffix}"))
                        if run_glad:
                            jobs.append(("glad", _glad, f"Hansen GLAD {hansen_year}{rsuffix}"))
                        if run_gfc:
                            jobs.append(("gfc", _gfc, f"Hansen GFC{rsuffix}"))
                        if has_buf and run_mb:
                            jobs.append(("buf_mb", _buf_mb, f"Buffer MapBiomas {year1}{rsuffix}"))
                        if has_buf and run_cmp:
                            jobs.append(("buf_cmp", _buf_cmp,
                                         f"Buffer comparison {year1}→{year2}{rsuffix}"))
                        if has_buf and run_glad:
                            jobs.append(("buf_glad", _buf_glad, f"Buffer Hansen GLAD{rsuffix}"))
                        if has_buf and run_gfc:
                            jobs.append(("buf_gfc", _buf_gfc, f"Buffer Hansen GFC{rsuffix}"))
                        if do_multi:
                            jobs.append(("multi", _multi, f"Multi-window transitions{rsuffix}"))
                        if do_multi and has_buf:
                            jobs.append(("buf_multi", _buf_multi,
                                         f"Buffer multi-window transitions{rsuffix}"))

                        # Deforestation-timeline series. Only the MapBiomas and
                        # fire indicators need Earth Engine; the Hansen loss
                        # series is pure reshaping of the `gfc` result above, so
                        # it is merged in locally after the gather rather than
                        # forcing a dependent second round.
                        if run_timeline:
                            def _tl(geom=region_ee_geom):
                                from ..utils.deforestation_timeline import collect_timeline
                                return collect_timeline(
                                    geom, tl_y0, tl_y1, include_hansen=False
                                )
                            jobs.append(("tl", _tl, f"Timeline series{rsuffix}"))
                            if has_buf:
                                def _tl_buf(geom=region_buf_geom):
                                    from ..utils.deforestation_timeline import collect_timeline
                                    return collect_timeline(
                                        geom, tl_y0, tl_y1, include_hansen=False
                                    )
                                jobs.append(("tl_buf", _tl_buf,
                                             f"Buffer timeline series{rsuffix}"))

                        res: Dict[str, Any] = {}
                        if jobs:
                            await _set_step(
                                territory,
                                STEPS["fetch"].format(n=len(jobs)) + rlabel,
                            )
                            gathered = await asyncio.gather(*[
                                _ee_with_retry(loop, fn, f"{lbl} ({territory})")
                                for _, fn, lbl in jobs
                            ])
                            res = {key: value for (key, _, _), value in zip(jobs, gathered)}

                        # ── Shape the results (identical to the serial version;
                        #    a missing key means the analysis was switched off,
                        #    a None value means it failed every retry) ─────────
                        skipped: List[str] = []

                        if "mb_y1" in res:
                            df1 = res["mb_y1"]
                            if df1 is None:
                                skipped.append(f"MapBiomas {year1}")
                            elif not df1.empty:
                                mb_y1_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year1, "data": df1.to_dict("records"),
                                }

                        if "mb_y2" in res:
                            df2 = res["mb_y2"]
                            if df2 is None:
                                skipped.append(f"MapBiomas {year2}")
                            elif not df2.empty:
                                mb_y2_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year2, "data": df2.to_dict("records"),
                                }

                        if "cmp" in res:
                            cmp_result = res["cmp"]
                            if cmp_result is None:
                                skipped.append("comparison")
                            elif not (mb_y1_result and mb_y2_result):
                                # Both MapBiomas years must have produced data.
                                cmp_result = None

                        if "glad" in res:
                            glad_df = res["glad"]
                            if glad_df is None:
                                skipped.append("Hansen GLAD")
                            elif not glad_df.empty:
                                glad_result = {
                                    "type": "hansen_glad",
                                    "territory": territory,
                                    "year": hansen_year,
                                    "data": glad_df.to_dict("records"),
                                    "summary": {
                                        "year": int(hansen_year),
                                        "total_area_ha": float(glad_df["Area_ha"].sum()),
                                    },
                                }

                        if "gfc" in res:
                            gfc_result = res["gfc"]
                            if gfc_result and "error" in gfc_result:
                                gfc_result = None
                            if gfc_result:
                                gfc_result["territory"] = territory
                            else:
                                skipped.append("Hansen GFC")

                        if "buf_mb" in res:
                            bdf = res["buf_mb"]
                            if bdf is None:
                                skipped.append(f"buffer MapBiomas {year1}")
                            elif not bdf.empty:
                                buf_mb_result = {
                                    "type": "mapbiomas",
                                    "territory": f"{territory} - Buffer {buf_km:g}km",
                                    "year": year1,
                                    "data": bdf.to_dict("records"),
                                }

                        if "buf_cmp" in res:
                            buf_cmp_result = res["buf_cmp"]
                            if buf_cmp_result is None:
                                skipped.append("buffer comparison")

                        if "buf_glad" in res:
                            bgdf = res["buf_glad"]
                            if bgdf is None:
                                skipped.append("buffer Hansen GLAD")
                            elif not bgdf.empty:
                                buf_glad_result = {
                                    "type": "hansen_glad",
                                    "territory": f"{territory} - Buffer {buf_km:g}km",
                                    "year": hansen_year,
                                    "data": bgdf.to_dict("records"),
                                }

                        if "buf_gfc" in res:
                            buf_gfc_result = res["buf_gfc"]
                            if buf_gfc_result:
                                buf_gfc_result["territory"] = f"{territory} - Buffer {buf_km:g}km"
                            else:
                                skipped.append("buffer Hansen GFC")

                        if "multi" in res:
                            multi_pairs = res["multi"]
                            if multi_pairs:
                                multi_window_result = {
                                    "territory": territory,
                                    "years": list(multi_years),
                                    "pairs": multi_pairs,
                                }
                            else:
                                skipped.append("multi-window")

                        if "buf_multi" in res:
                            buf_multi_pairs = res["buf_multi"]
                            if buf_multi_pairs:
                                buf_multi_window_result = {
                                    "territory": f"{territory} - Buffer {buf_km:g}km",
                                    "years": list(multi_years),
                                    "pairs": buf_multi_pairs,
                                }
                            else:
                                skipped.append("buffer multi-window")

                        if skipped:
                            async with self:
                                self._batch_append_log(
                                    f"  ⚠ {territory}{rsuffix}: skipped "
                                    + ", ".join(skipped)
                                )

                        # Capture region data for per-quadrant maps + timeline.
                        # 4-tuple: (region_name, territory_geom, gfc_result, buffer_geom)
                        # buffer_geom is the quadrant-clipped buffer (or full buffer for
                        # non-split territories); None when buffer is not enabled.
                        region_map_data.append((region_name, region_ee_geom, gfc_result, region_buf_geom))

                        # Merge the timeline series for this region. The Hansen
                        # loss series is derived locally from `gfc_result` — it
                        # is a reshaping of data already fetched above, so it
                        # costs no request and needs no ordering.
                        if run_timeline:
                            from ..utils.deforestation_timeline import hansen_loss_series
                            for _slot, _key, _gfc in (
                                ("tl", ("t", region_name), gfc_result),
                                ("tl_buf", ("b", region_name), None),
                            ):
                                _series = res.get(_slot)
                                if not _series:
                                    continue
                                _series = dict(_series)
                                _series["hansen_loss"] = hansen_loss_series(
                                    _gfc, tl_y0, tl_y1
                                )
                                tl_series[_key] = _series

                        # ─── Step 11: Write THIS region to master ZIP ───────
                        await _set_step(territory, STEPS["export"] + rlabel)

                        def _write_region_to_zip(
                            zf=master_zf,
                            terr=territory,
                            rname=region_name,
                            y1=year1, y2=year2, hy=hansen_year,
                            bkm=buf_km, ben=buf_enabled,
                            mb1=mb_y1_result, mb2=mb_y2_result, cmp=cmp_result,
                            glad=glad_result, gfc=gfc_result,
                            bmb=buf_mb_result, bcmp=buf_cmp_result,
                            bglad=buf_glad_result, bgfc=buf_gfc_result,
                            mw=multi_window_result, bmw=buf_multi_window_result,
                            run_treemap=run_treemap,
                        ):
                            from ..utils.export_service import (
                                _slug, _write_mapbiomas_section,
                                _write_hansen_glad_section, _write_hansen_gfc_section,
                                _write_multi_window_section,
                            )

                            t_slug = _slug(terr)
                            # Region suffix: territory/<slug>/<rname>/... when split,
                            # else just territory/<slug>/...
                            rsub = f"/{rname}" if rname else ""
                            t_dir = f"territory/{t_slug}{rsub}"
                            # Quadrant tag appended to every filename (just
                            # before the extension, or just before the buffer
                            # tag for buffer files) so flat-listed files can
                            # still be traced back to their quadrant.
                            q_tag = f"_{rname.upper()}" if rname else ""

                            # MapBiomas section + figures
                            t_y1_records = mb1.get("data") if mb1 else (cmp.get("_raw_y1") if cmp else None)
                            t_y2_records = mb2.get("data") if mb2 else (cmp.get("_raw_y2") if cmp else None)
                            t_transitions = cmp.get("transitions") if cmp else None
                            t_glad_records = glad.get("data") if glad else None
                            t_figs = _build_territory_figures(
                                mb_y1_records=t_y1_records,
                                mb_y2_records=t_y2_records,
                                transitions=t_transitions,
                                glad_records=t_glad_records,
                                gfc_dict=gfc,
                                y1=y1, y2=y2, hansen_year=hy,
                                run_treemap=run_treemap,
                            )

                            # Synthesize single-year results from comparison
                            # raw rows when the dedicated mb step was skipped,
                            # so we always emit both y1 and y2 distribution +
                            # pie when comparison data is available.
                            t_y1_single = mb1
                            if t_y1_single is None and cmp and cmp.get("_raw_y1"):
                                t_y1_single = {"type": "mapbiomas", "year": y1, "data": cmp["_raw_y1"]}
                            t_y2_single = mb2
                            if t_y2_single is None and cmp and cmp.get("_raw_y2"):
                                t_y2_single = {"type": "mapbiomas", "year": y2, "data": cmp["_raw_y2"]}

                            _write_mapbiomas_section(
                                zf, t_dir, t_slug,
                                single_year_result=t_y2_single,
                                single_year_result_extra=t_y1_single,
                                comparison_result=cmp,
                                territory_result_y1=cmp.get("_raw_y1") if cmp else None,
                                territory_result_y2=cmp.get("_raw_y2") if cmp else None,
                                transitions=t_transitions,
                                bar_chart=t_figs.get("bar_chart_y2"),
                                pie_chart=t_figs.get("pie_chart_y2"),
                                bar_chart_extra=t_figs.get("bar_chart_y1"),
                                pie_chart_extra=t_figs.get("pie_chart_y1"),
                                comparison_bar_chart=t_figs.get("comparison_bar_chart"),
                                gains_losses_chart=t_figs.get("gains_losses_chart"),
                                change_pct_chart=t_figs.get("change_pct_chart"),
                                sankey_chart=t_figs.get("sankey_chart"),
                                sunburst_chart=t_figs.get("sunburst_chart"),
                                treemap_chart=t_figs.get("treemap_chart"),
                                transition_matrix_chart=t_figs.get("transition_matrix_chart"),
                                name_suffix=q_tag,
                            )
                            if glad:
                                _write_hansen_glad_section(
                                    zf, t_dir, t_slug,
                                    glad_result=glad,
                                    bar_chart=t_figs.get("glad_bar"),
                                    name_suffix=q_tag,
                                )
                            if gfc:
                                _write_hansen_gfc_section(
                                    zf, t_dir, t_slug,
                                    gfc_result=gfc,
                                    bar_chart=t_figs.get("gfc_bar"),
                                    loss_chart=t_figs.get("gfc_loss"),
                                    name_suffix=q_tag,
                                )

                            # Buffer section for this region — folder keeps
                            # the buffer slug, but filenames use the territory
                            # slug with `_Buffer_{km}km` appended after the
                            # dataset (so they sort next to territory files).
                            if ben:
                                b_slug = _slug(f"{terr}_Buffer_{bkm:g}km")
                                b_dir = f"buffer/{b_slug}{rsub}"
                                # Quadrant tag goes *before* the buffer tag so
                                # the buffer marker stays last (just before
                                # the extension), preserving file grouping.
                                b_suffix = f"{q_tag}_Buffer_{bkm:g}km"

                                b_y1_records = bmb.get("data") if bmb else (bcmp.get("_raw_y1") if bcmp else None)
                                b_y2_records = bcmp.get("_raw_y2") if bcmp else None
                                b_transitions = bcmp.get("transitions") if bcmp else None
                                b_glad_records = bglad.get("data") if bglad else None
                                b_figs = _build_territory_figures(
                                    mb_y1_records=b_y1_records,
                                    mb_y2_records=b_y2_records,
                                    transitions=b_transitions,
                                    glad_records=b_glad_records,
                                    gfc_dict=bgfc,
                                    y1=y1, y2=y2, hansen_year=hy,
                                    run_treemap=run_treemap,
                                )
                                if bmb or bcmp:
                                    # buf year1 single = bmb (run_mb path);
                                    # buf year2 single is synthesized from
                                    # bcmp._raw_y2 since the dedicated buffer
                                    # mb step only analyses year1.
                                    b_y1_single = bmb
                                    if b_y1_single is None and bcmp and bcmp.get("_raw_y1"):
                                        b_y1_single = {"type": "mapbiomas", "year": y1, "data": bcmp["_raw_y1"]}
                                    b_y2_single = None
                                    if bcmp and bcmp.get("_raw_y2"):
                                        b_y2_single = {"type": "mapbiomas", "year": y2, "data": bcmp["_raw_y2"]}

                                    _write_mapbiomas_section(
                                        zf, b_dir, t_slug,
                                        single_year_result=b_y2_single or b_y1_single,
                                        single_year_result_extra=b_y1_single if b_y2_single else None,
                                        comparison_result=bcmp,
                                        territory_result_y1=bcmp.get("_raw_y1") if bcmp else None,
                                        territory_result_y2=bcmp.get("_raw_y2") if bcmp else None,
                                        transitions=b_transitions,
                                        bar_chart=b_figs.get("bar_chart_y2") or b_figs.get("bar_chart_y1"),
                                        pie_chart=b_figs.get("pie_chart_y2") or b_figs.get("pie_chart_y1"),
                                        bar_chart_extra=b_figs.get("bar_chart_y1") if b_figs.get("bar_chart_y2") else None,
                                        pie_chart_extra=b_figs.get("pie_chart_y1") if b_figs.get("pie_chart_y2") else None,
                                        comparison_bar_chart=b_figs.get("comparison_bar_chart"),
                                        gains_losses_chart=b_figs.get("gains_losses_chart"),
                                        change_pct_chart=b_figs.get("change_pct_chart"),
                                        sankey_chart=b_figs.get("sankey_chart"),
                                        sunburst_chart=b_figs.get("sunburst_chart"),
                                        treemap_chart=b_figs.get("treemap_chart"),
                                        transition_matrix_chart=b_figs.get("transition_matrix_chart"),
                                        name_suffix=b_suffix,
                                    )
                                if bglad:
                                    _write_hansen_glad_section(
                                        zf, b_dir, t_slug,
                                        glad_result=bglad,
                                        bar_chart=b_figs.get("glad_bar"),
                                        name_suffix=b_suffix,
                                    )
                                if bgfc:
                                    _write_hansen_gfc_section(
                                        zf, b_dir, t_slug,
                                        gfc_result=bgfc,
                                        bar_chart=b_figs.get("gfc_bar"),
                                        loss_chart=b_figs.get("gfc_loss"),
                                        name_suffix=b_suffix,
                                    )

                                # ── Multi-window MapBiomas (buffer) ───
                                if bmw:
                                    _write_multi_window_section(
                                        zf, b_dir, t_slug,
                                        mw_result=bmw,
                                        name_suffix=b_suffix,
                                        include_treemaps=run_treemap,
                                    )

                            # ── Multi-window MapBiomas (territory) ────
                            if mw:
                                _write_multi_window_section(
                                    zf, t_dir, t_slug,
                                    mw_result=mw,
                                    name_suffix=q_tag,
                                    include_treemaps=run_treemap,
                                )

                        await _render(loop, _write_region_to_zip, "charts", "kaleido")

                    # ─── End of regions loop ────────────────────────────────
                    # Write the full territory boundary ONCE at the top level
                    # (same boundary regardless of quadrant splitting).
                    def _write_boundary(zf=master_zf, terr=territory, geojson=raw_geojson):
                        from ..utils.export_service import _slug
                        t_slug = _slug(terr)
                        zf.writestr(
                            f"territory/{t_slug}/boundary.geojson",
                            json.dumps({"type": "Feature", "geometry": geojson,
                                        "properties": {"name": terr}}).encode(),
                        )
                    await loop.run_in_executor(io_pool, _write_boundary)

                    # ─── PDF maps (satellite + MapBiomas y1/y2, per territory) ──
                    if run_maps:
                        await _set_step(territory, STEPS["maps_fetch"])

                        # Download every raster this territory's maps need
                        # BEFORE taking the render lock. These are EE
                        # getDownloadURL round-trips and basemap tile grids —
                        # pure network, no matplotlib — and holding the single
                        # render slot through them was measured at ~98% of a
                        # run's wall clock. Prefetched concurrently here, the
                        # lock below covers only the compositing.
                        #
                        # Runs on the default executor on purpose:
                        # prefetch_map_inputs submits to the EE pool and blocks
                        # on the results, so it must not occupy an EE worker
                        # itself.
                        def _prefetch_maps(
                            geojson=raw_geojson,
                            all_regions=region_map_data,
                            buf_ee=buf_ee_geom,
                            y1=year1, y2=year2, hy=hansen_year,
                            do_mb=(run_mb or run_cmp),
                            do_glad=run_glad,
                            aux_keys=tuple(aux_layer_keys),
                        ):
                            from ..utils.map_export_service import prefetch_map_inputs
                            buf_gj = None
                            if buf_ee is not None:
                                try:
                                    buf_gj = buf_ee.getInfo()
                                except Exception as be:
                                    logger.warning(f"buffer geojson for {territory} failed: {be}")
                            mb_years = ([int(y1)] if y1 == y2 else [int(y1), int(y2)]) if do_mb else []
                            glad_layers = [str(hy)] if do_glad else None
                            aux_layers = [(k, int(y2)) for k in aux_keys]
                            per_region = {}
                            for rname, region_geom, *_ in all_regions:
                                try:
                                    per_region[rname] = prefetch_map_inputs(
                                        drawn_features=[],
                                        active_mapbiomas_years=mb_years,
                                        active_hansen_layers=glad_layers,
                                        ee_geometry=region_geom,
                                        territory_geojson=geojson,
                                        buffer_geojson=buf_gj,
                                        active_aux_layers=aux_layers,
                                    )
                                except Exception as pe:
                                    # Non-fatal: create_map_set falls back to
                                    # fetching inline for anything missing.
                                    logger.warning(
                                        f"map prefetch {rname or 'full'} for {territory}: {pe}"
                                    )
                                    per_region[rname] = None
                            return buf_gj, per_region

                        try:
                            buf_gj_pre, map_prefetch = await loop.run_in_executor(
                                io_pool, _prefetch_maps
                            )
                        except Exception as pe:
                            logger.warning(f"map prefetch for {territory} failed: {pe}")
                            buf_gj_pre, map_prefetch = None, {}

                        await _set_step(territory, STEPS["maps"])

                        def _write_pdf_maps(
                            zf=master_zf,
                            terr=territory,
                            geojson=raw_geojson,
                            all_regions=region_map_data,
                            buf_ee=buf_ee_geom,
                            y1=year1, y2=year2, hy=hansen_year,
                            do_mb=(run_mb or run_cmp),
                            do_glad=run_glad,
                            aux_keys=tuple(aux_layer_keys),
                            buf_gj=buf_gj_pre,
                            prefetch=map_prefetch,
                        ):
                            try:
                                from ..utils.export_service import _slug
                                from ..utils.map_export_service import create_map_set
                                t_slug = _slug(terr)

                                mb_years: List[int] = []
                                if do_mb:
                                    mb_years = [int(y1)] if y1 == y2 else [int(y1), int(y2)]
                                glad_layers = [str(hy)] if do_glad else None
                                aux_layers = [(k, int(y2)) for k in aux_keys]
                                multi = any(rname for rname, *_ in all_regions)

                                for rname, region_geom, *_ in all_regions:
                                    q_label = rname.upper() if rname else ""
                                    map_title = f"{terr} [{q_label}]" if q_label else terr
                                    fname_pre = f"{q_label}_" if q_label else ""
                                    try:
                                        maps = create_map_set(
                                            drawn_features=[],
                                            territory_name=map_title,
                                            active_mapbiomas_years=mb_years,
                                            active_hansen_layers=glad_layers,
                                            ee_geometry=region_geom,
                                            territory_geojson=geojson,
                                            buffer_geojson=buf_gj,
                                            image_format="png",
                                            active_aux_layers=aux_layers,
                                            # Downloaded before the render lock
                                            # was taken; None here just means
                                            # "fetch inline", as before.
                                            prefetched=prefetch.get(rname),
                                        )
                                        for name, img_bytes in (maps or {}).items():
                                            zf.writestr(
                                                f"territory/{t_slug}/maps/{t_slug}_{fname_pre}{name}.png",
                                                img_bytes,
                                            )
                                    except Exception as me:
                                        logger.warning(
                                            f"PDF maps {q_label or 'full'} for {terr}: {me}",
                                        )
                            except Exception as me:
                                logger.warning(
                                    f"PDF maps for {terr} failed (non-fatal): {me}",
                                    exc_info=True,
                                )

                        try:
                            await _render(loop, _write_pdf_maps, "maps", "matplotlib")
                        except Exception as me:
                            async with self:
                                self._batch_append_log(f"  ⚠ PDF maps skipped: {me}")

                    # ── Deforestation timeline (per-territory + buffer) ─────
                    # The series were fetched in the per-region fan-out above,
                    # in the same batch as MapBiomas and Hansen. Nothing is
                    # requested here: a second round would be submitted to the
                    # back of a FIFO pool already holding every job of every
                    # territory that started in the meantime.
                    if run_timeline:
                        await _set_step(territory, "📈 Deforestation timeline…")

                        def _write_timeline(
                            zf=master_zf,
                            terr=territory,
                            all_regions=region_map_data,
                            buf_ee=buf_ee_geom,
                            ben=buf_enabled,
                            bkm=buf_km,
                            y_start=int(year1),
                            y_end=int(year2),
                            ttype=territory_type_map[territory],
                            tl_pol=self.batch_timeline_political,
                            tl_pcy=self.batch_timeline_policy,
                            tl_enso=self.batch_timeline_enso,
                            # Keys mirror how the region loop stored them:
                            # ("t", region_name) / ("b", region_name). A
                            # mismatch degrades to an inline fetch on the render
                            # thread — slower, never a missing chart.
                            prefetched=tl_series,
                        ):
                            try:
                                from ..utils.export_service import _slug, _write_fig
                                from ..utils.deforestation_timeline import (
                                    collect_timeline, first_state_code,
                                )
                                from ..utils.visualization import (
                                    create_deforestation_timeline_chart,
                                )
                                from ..utils.territory_service import get_territory_service
                                import pandas as pd

                                t_slug = _slug(terr)
                                if y_end < y_start:
                                    y_start, y_end = y_end, y_start

                                # State code for the political bar
                                try:
                                    if ttype == "conservation":
                                        from ..utils.conservation_service import get_conservation_unit_service
                                        _svc = get_conservation_unit_service()
                                    else:
                                        _svc = get_territory_service()
                                    info = _svc.get_territory_info(terr) or {}
                                    state_code = first_state_code(info.get("uf_sigla"))
                                except Exception:
                                    state_code = None

                                def _write_region(label_suffix, sub_dir, region_geom,
                                                  gfc_for_region, title_extra,
                                                  key=None):
                                    """Build CSV + 3 chart variants for one region (territory or buffer)."""
                                    logger.info(
                                        f"_write_region({label_suffix}): gfc_for_region={'present' if gfc_for_region else 'None'}, "
                                        f"tree_loss_data={'present' if (gfc_for_region and gfc_for_region.get('tree_loss_data')) else 'missing/None'}"
                                    )
                                    # Prefetched on the EE pool before this lane
                                    # was entered. Falling back to an inline
                                    # fetch keeps a partial prefetch working —
                                    # slower, but never a missing chart.
                                    series = prefetched.get(key) if key else None
                                    if not series:
                                        if key:
                                            logger.info(
                                                f"_write_region({label_suffix}): no prefetched "
                                                f"series for {key} — fetching inline"
                                            )
                                        series = collect_timeline(
                                            region_geom, y_start, y_end,
                                            gfc_result=gfc_for_region,
                                        )
                                    if not series:
                                        logger.warning(f"_write_region({label_suffix}): no series returned")
                                        return
                                    # Wide CSV: one row per year, one column per indicator
                                    years = list(range(y_start, y_end + 1))
                                    rows = []
                                    for y in years:
                                        row = {"year": y}
                                        for k, ser in series.items():
                                            row[k] = float(ser.get(y, 0.0) or 0.0)
                                        rows.append(row)
                                    df = pd.DataFrame(rows)
                                    csv_path = (f"{sub_dir}/{t_slug}_deforestation_timeline_"
                                                f"{y_start}_{y_end}{label_suffix}.csv")
                                    zf.writestr(csv_path,
                                                df.to_csv(index=False).encode("utf-8"))

                                    # Three chart variants
                                    fig_dir = f"{sub_dir}/figures"
                                    for variant, suffix in (
                                        ("raw", "raw"),
                                        ("moving_avg", "ma5"),
                                        ("derivatives", "derivatives"),
                                    ):
                                        fig = create_deforestation_timeline_chart(
                                            series,
                                            state_code=state_code,
                                            year_start=y_start,
                                            year_end=y_end,
                                            variant=variant,
                                            moving_window=5,
                                            title_suffix=f"{terr}{title_extra}",
                                            territory_name=terr,
                                            territory_type=ttype,
                                            include_political=tl_pol,
                                            include_policy=tl_pcy,
                                            include_enso=tl_enso,
                                        )
                                        if fig is not None:
                                            base = (f"{fig_dir}/{t_slug}_deforestation_timeline_"
                                                    f"{y_start}_{y_end}_{suffix}{label_suffix}")
                                            # png_width=1400 overrides kaleido's 700px
                                            # default; the scale comes from the run's
                                            # figure_export() policy so a batch can trade
                                            # resolution for archive size.
                                            _write_fig(zf, base, fig, png_width=1400)

                                    # Also emit single-indicator raw plots (one line each)
                                    for ik, ival in series.items():
                                        try:
                                            single = {ik: ival}
                                            fig_single = create_deforestation_timeline_chart(
                                                single,
                                                state_code=state_code,
                                                year_start=y_start,
                                                year_end=y_end,
                                                variant="raw",
                                                moving_window=5,
                                                title_suffix=f"{terr}{title_extra}",
                                                territory_name=terr,
                                                territory_type=ttype,
                                                include_political=tl_pol,
                                                include_policy=tl_pcy,
                                                include_enso=tl_enso,
                                            )
                                            if fig_single is not None:
                                                base_single = (
                                                    f"{fig_dir}/{t_slug}_deforestation_timeline_"
                                                    f"{y_start}_{y_end}_{ik}{label_suffix}"
                                                )
                                                _write_fig(zf, base_single, fig_single,
                                                           png_width=1400)
                                        except Exception:
                                            logger.debug(f"failed to write single-indicator plot for {ik}")

                                # Territory — one pass per region/quadrant
                                t_dir = f"territory/{t_slug}/deforestation_timeline"
                                for rname, region_geom, region_gfc, region_buf_geom in all_regions:
                                    q_label = rname.upper() if rname else ""
                                    _write_region(
                                        f"_{q_label}" if q_label else "",
                                        t_dir,
                                        region_geom,
                                        region_gfc,
                                        title_extra=f" [{q_label}]" if q_label else "",
                                        key=("t", rname),
                                    )

                                # Buffer — per quadrant when quadrant splitting was used,
                                # one whole-buffer timeline otherwise.  Buffer geometry comes
                                # from each entry's 4th element (quadrant-clipped or full).
                                if ben:
                                    b_slug = _slug(f"{terr}_Buffer_{bkm:g}km")
                                    b_dir = f"buffer/{b_slug}/deforestation_timeline"
                                    for rname, _, __, region_buf_geom in all_regions:
                                        if region_buf_geom is None:
                                            continue
                                        q_label = rname.upper() if rname else ""
                                        _write_region(
                                            f"_Buffer_{bkm:g}km{'_' + q_label if q_label else ''}",
                                            b_dir,
                                            region_buf_geom,
                                            None,
                                            title_extra=(
                                                f" — Buffer {bkm:g} km [{q_label}]"
                                                if q_label else
                                                f" — Buffer {bkm:g} km"
                                            ),
                                            key=("b", rname),
                                        )

                            except Exception as te:
                                logger.warning(
                                    f"Deforestation timeline for {terr} failed: {te}",
                                    exc_info=True,
                                )

                        try:
                            await _render(loop, _write_timeline, "timeline", "kaleido")
                        except Exception as te:
                            async with self:
                                self._batch_append_log(f"  ⚠ Timeline skipped: {te}")

                    # ── Mark as completed ────────────────────────────────────
                    total_area = (
                        mb_y2_result["data"][0].get("Area_ha", 0)
                        if mb_y2_result and mb_y2_result.get("data")
                        else 0
                    )
                    t_result = {
                        "territory": territory,
                        "status": "ok",
                        "mb_year1": year1 if mb_y1_result else None,
                        "mb_year2": year2 if mb_y2_result else None,
                        "glad_year": hansen_year if glad_result else None,
                        "gfc": gfc_result is not None,
                        "buffer": buf_enabled and buf_ee_geom is not None,
                    }
                    async with self:
                        self.batch_completed = self.batch_completed + [territory]
                        self._batch_append_log(f"  ✅ {territory} — complete")

                except Exception as exc:
                    t_result = {"territory": territory, "status": "error",
                                "error": str(exc)}
                    async with self:
                        self.batch_failed = self.batch_failed + [territory]
                        err_msg = str(exc)[:120]
                        self.batch_errors = {**self.batch_errors, territory: err_msg}
                        self._batch_append_log(f"  ❌ {territory} — error: {err_msg}")
                    logger.error(f"Batch error for {territory}: {exc}", exc_info=True)

                batch_summary.append(t_result)

                # Pandas/numpy objects routinely form reference cycles that
                # refcounting alone won't reclaim (DataFrame internals, EE
                # client objects). Force a collection between territories so
                # peak RSS doesn't ratchet up over a long batch run.
                gc.collect()

            # ── Worker pool ────────────────────────────────────────────────
            # Territories are pulled off a shared queue rather than sliced into
            # per-worker chunks, so a worker that draws a fast territory
            # immediately picks up the next one instead of idling — sizes vary
            # by more than an order of magnitude, and a 2 M ha quadrant-split
            # territory would otherwise stall a whole chunk behind it.
            pending: "asyncio.Queue[str]" = asyncio.Queue()
            for _t in territories:
                pending.put_nowait(_t)

            async def _worker():
                while True:
                    try:
                        territory = pending.get_nowait()
                    except asyncio.QueueEmpty:
                        return

                    # Stop is cooperative: it drains the queue so nothing new
                    # starts, while territories already in flight finish and
                    # keep their results.
                    async with self:
                        if not self.batch_running:
                            return
                        self.batch_active_steps = {
                            **self.batch_active_steps,
                            territory: STEPS["geometry"],
                        }
                        self.batch_current_territory = territory
                        self.batch_current_step = STEPS["geometry"]
                        self._batch_append_log(f"▶ Processing: {territory}")

                    _territory_span[territory] = [time.monotonic(), None]
                    try:
                        await _process_territory(territory)
                    finally:
                        _territory_span[territory][1] = time.monotonic()
                        last = _stage_open.pop(territory, None)
                        if last is not None:
                            _lbl, _t0 = last
                            _acc = _stage_totals.setdefault(territory, {})
                            _acc[_lbl] = _acc.get(_lbl, 0.0) + (time.monotonic() - _t0)
                        async with self:
                            remaining = dict(self.batch_active_steps)
                            remaining.pop(territory, None)
                            self.batch_active_steps = remaining

            await asyncio.gather(*[_worker() for _ in range(n_workers)])

            async with self:
                if not self.batch_running:
                    self._batch_append_log("⏹ Batch stopped by user.")

            # ── Finalize ZIP: add summary files ────────────────────────────
            async with self:
                self.batch_current_step = "📋 Writing summary files…"
                self.batch_active_steps = {}

            def _write_summary(
                zf=master_zf,
                summary=batch_summary,
                territories=territories,
                n_workers=n_workers,
                meter_report=meter_report,
                y1=year1, y2=year2, hy=hansen_year,
                bkm=buf_km, ben=buf_enabled,
            ):
                ts = datetime.now().isoformat()
                meta = {
                    "generated": ts,
                    # Where the run's time actually went — see
                    # docs/BATCH_CONCURRENCY.md §"Sizing from measurement".
                    "concurrency": {
                        "territory_workers": n_workers,
                        "io_slots": IO_CONCURRENCY,
                        "tier": TIER,
                        **run_meters,
                        # Per-territory stage timing, plus the number that
                        # distinguishes a real barrier from fair-share
                        # interleaving: with N territories sharing the pools each
                        # advances at ~1/N speed, so they finish together and
                        # `concurrent_fraction` approaches 1. A genuine barrier
                        # would show idle stages instead.
                        **_stage_report(),
                    },
                    "territories_requested": len(territories),
                    "territories_completed": sum(1 for r in summary if r["status"] == "ok"),
                    "territories_failed": sum(1 for r in summary if r["status"] == "error"),
                    "mapbiomas_year1": y1,
                    "mapbiomas_year2": y2,
                    "hansen_glad_year": hy,
                    "buffer_km": bkm if ben else None,
                    "results": summary,
                }
                zf.writestr("batch_summary.json", json.dumps(meta, indent=2).encode())

                ok = [r["territory"] for r in summary if r["status"] == "ok"]
                fail = [f"{r['territory']}: {r.get('error','?')}"
                        for r in summary if r["status"] == "error"]
                report_lines = [
                    "# Yvynation Batch Analysis Report",
                    f"Generated: {ts}",
                    f"Territories processed: {len(ok)}/{len(territories)}",
                    f"MapBiomas: {y1} vs {y2}",
                    f"Hansen GLAD: {hy}",
                    f"Buffer: {bkm} km" if ben else "Buffer: disabled",
                    "",
                    "## Completed territories",
                ] + [f"- {t}" for t in ok] + [
                    "",
                    "## Failed territories",
                ] + ([f"- {f}" for f in fail] if fail else ["None"])
                zf.writestr("batch_report.md", "\n".join(report_lines).encode())

            # Snapshot the pools *before* the final ZIP. Compression uses
            # neither pool, so letting it run first would dilute both
            # percentages and make the verdict describe the wrong phase.
            run_meters = meter_report()
            await loop.run_in_executor(io_pool, _write_summary)

        # Deflate the live folder into the final ZIP (single compression pass).
        # Runs on the stop-after-current path too, so a partial run still
        # yields a downloadable archive; the folder itself stays browsable
        # until the next batch run prunes it.
        #
        # Not a cheap tail step: on Cloud Run the folder is a GCS FUSE mount, so
        # this reads ~1500 small files back over the network. A 31-territory run
        # spent 10.6 min here. zip_directory() overlaps those reads — hence the
        # explicit reader count.
        zip_t0 = time.monotonic()
        async with self:
            self.batch_current_step = "🗜 Compressing final ZIP…"
            self._batch_append_log("🗜 Compressing results into the final ZIP…")
        zip_size = 0
        try:
            zip_size = await loop.run_in_executor(
                io_pool, partial(
                    zip_directory, work_dir, zip_path, workers=IO_CONCURRENCY,
                )
            )
            # Archive built — the live folder is now redundant; remove it so
            # exports/ holds only ZIPs (crashed runs keep theirs for salvage).
            import shutil
            await loop.run_in_executor(
                io_pool, lambda: shutil.rmtree(work_dir, ignore_errors=True)
            )
        except Exception as ze:
            logger.error(f"[BATCH] final ZIP compression failed: {ze}", exc_info=True)
            async with self:
                self._batch_append_log(
                    f"❌ Final ZIP failed ({ze}) — files remain in "
                    f"uploaded_files/exports/{run_name}/"
                )
        prune_old_exports()

        async with self:
            self.batch_running = False
            self.batch_done = True
            self.batch_zip_ready = zip_size > 0
            self.batch_zip_relpath = f"exports/{zip_filename}" if zip_size > 0 else ""
            self.batch_current_territory = ""
            self.batch_current_step = STEPS["done"]
            n_ok = len(self.batch_completed)
            n_fail = len(self.batch_failed)
            self._batch_append_log(
                f"🏁 Batch complete: {n_ok} OK, {n_fail} failed — "
                f"ZIP size {zip_size // 1024} KB in {time.monotonic() - zip_t0:.0f}s"
            )
            for line in describe_meters():
                self._batch_append_log(line)
            logger.info(f"Batch processing complete: {n_ok}/{len(territories)} territories")
