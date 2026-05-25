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
      hansen_glad/  …
      hansen_gfc/  …
      maps/        ← PNG maps (satellite, MapBiomas y1/y2, Hansen)
    buffer/{buffer_slug}/
      …
    batch_summary.json
    batch_report.md
"""

import asyncio
import io
import json
import logging
import zipfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import reflex as rx

logger = logging.getLogger(__name__)

# Module-level storage for the batch ZIP bytes (too large to keep in Reflex state)
_batch_zip_bytes: Optional[bytes] = None

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
    Run *fn* in an executor with up to *retries* attempts on transient EE errors.

    Returns the result on success, ``None`` on persistent failure.  Logs
    progress between attempts so the batch task can keep going.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            return await loop.run_in_executor(None, fn)
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
    "mb_y1":        "🌿 MapBiomas {year1} analysis…",
    "mb_y2":        "🌿 MapBiomas {year2} analysis…",
    "comparison":   "📊 Land-cover comparison {year1} → {year2}…",
    "glad":         "🌲 Hansen GLAD {hansen_year} analysis…",
    "gfc":          "🪓 Hansen GFC (tree cover / loss / gain)…",
    "buf_mb":       "🔵 Buffer MapBiomas {year1}…",
    "buf_cmp":      "🔵 Buffer comparison {year1} → {year2}…",
    "buf_glad":     "🔵 Buffer Hansen GLAD…",
    "buf_gfc":      "🔵 Buffer Hansen GFC…",
    "maps":         "🗺️  Rendering PNG maps…",
    "export":       "📦 Packaging data…",
    "done":         "✅ Done",
}


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
    batch_buffer_km: float = 10.0
    batch_buffer_enabled: bool = True
    batch_run_mapbiomas: bool = True
    batch_run_comparison: bool = True
    batch_run_glad: bool = True
    batch_run_gfc: bool = True
    batch_run_pdf_maps: bool = True
    batch_territory_search: str = ""

    # ---- Runtime status ------------------------------------------------------
    batch_running: bool = False
    batch_done: bool = False
    batch_zip_ready: bool = False
    batch_current_territory: str = ""
    batch_current_step: str = ""
    batch_completed: List[str] = []      # successfully processed
    batch_failed: List[str] = []         # territories that errored
    batch_errors: Dict[str, str] = {}    # territory → error message
    batch_total: int = 0
    batch_log: List[str] = []           # live log lines (most recent last)

    # ---- Computed ------------------------------------------------------------

    @rx.var
    def batch_filtered_territories(self) -> List[str]:
        """Territory list filtered by the search query."""
        q = self.batch_territory_search.lower()
        if not q:
            return self.available_territories
        return [t for t in self.available_territories if q in t.lower()]

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

    @rx.var
    def batch_is_territory_selected(self) -> Dict[str, bool]:
        """Lookup map for checkbox state (display key → bool)."""
        return {t: True for t in self.batch_selected_territories}

    # ---- Selection helpers ---------------------------------------------------

    def batch_set_territory_search(self, q: str):
        self.batch_territory_search = q

    def batch_toggle_territory(self, territory: str):
        """Add or remove a territory from the batch selection."""
        if territory in self.batch_selected_territories:
            self.batch_selected_territories = [
                t for t in self.batch_selected_territories if t != territory
            ]
        else:
            self.batch_selected_territories = self.batch_selected_territories + [territory]

    def batch_select_all_filtered(self):
        """Add all currently-filtered territories to the selection."""
        current = set(self.batch_selected_territories)
        for t in self.batch_filtered_territories:
            current.add(t)
        self.batch_selected_territories = sorted(current)

    def batch_clear_selection(self):
        self.batch_selected_territories = []

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
        try:
            v = float(km)
            if v > 0:
                self.batch_buffer_km = v
        except (ValueError, TypeError):
            pass

    def batch_toggle_run_mapbiomas(self, val: bool):
        self.batch_run_mapbiomas = val

    def batch_toggle_run_comparison(self, val: bool):
        self.batch_run_comparison = val

    def batch_toggle_run_glad(self, val: bool):
        self.batch_run_glad = val

    def batch_toggle_run_gfc(self, val: bool):
        self.batch_run_gfc = val

    def batch_toggle_run_pdf_maps(self, val: bool):
        self.batch_run_pdf_maps = val

    def batch_toggle_buffer_enabled(self, val: bool):
        self.batch_buffer_enabled = val

    def batch_stop(self):
        """Signal the running batch to stop after the current territory."""
        self.batch_running = False
        self._batch_append_log("⏹ Stop requested — will halt after current territory")

    def _batch_append_log(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.batch_log = self.batch_log + [f"[{ts}] {line}"]
        # Keep the last 200 lines to avoid unbounded growth
        if len(self.batch_log) > 200:
            self.batch_log = self.batch_log[-200:]

    # ---- Download -----------------------------------------------------------

    def download_batch_zip(self):
        """Download the completed batch ZIP."""
        global _batch_zip_bytes
        if not _batch_zip_bytes:
            self.error_message = "Batch ZIP not ready yet"
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        return rx.download(data=_batch_zip_bytes, filename=f"yvynation_batch_{ts}.zip")

    def batch_reset(self):
        """Reset batch state for a new run."""
        global _batch_zip_bytes
        _batch_zip_bytes = None
        self.batch_running = False
        self.batch_done = False
        self.batch_zip_ready = False
        self.batch_current_territory = ""
        self.batch_current_step = ""
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
        global _batch_zip_bytes

        # ── Snapshot configuration ──────────────────────────────────────────
        async with self:
            territories = list(self.batch_selected_territories)
            try:
                year1 = int(self.batch_year)
                year2 = int(self.batch_year2)
            except (ValueError, TypeError):
                self.error_message = "Invalid year selection."
                return
            hansen_year = str(self.batch_hansen_year)
            buf_km = float(self.batch_buffer_km)
            buf_enabled = bool(self.batch_buffer_enabled)
            run_mb = bool(self.batch_run_mapbiomas)
            run_cmp = bool(self.batch_run_comparison)
            run_glad = bool(self.batch_run_glad)
            run_gfc = bool(self.batch_run_gfc)
            run_maps = bool(self.batch_run_pdf_maps)

            if not territories:
                self.error_message = "No territories selected for batch processing."
                return

            self.batch_running = True
            self.batch_done = False
            self.batch_zip_ready = False
            self.batch_total = len(territories)
            self.batch_completed = []
            self.batch_failed = []
            self.batch_errors = {}
            self.batch_log = []
            self.batch_current_territory = ""
            self.batch_current_step = ""
            self._batch_append_log(
                f"Starting batch: {len(territories)} territories, "
                f"MapBiomas {year1}/{year2}, Hansen GLAD {hansen_year}, "
                f"buffer={'%.0f km' % buf_km if buf_enabled else 'off'}"
            )

        loop = asyncio.get_event_loop()

        # Master ZIP buffer
        master_buf = io.BytesIO()
        batch_summary: List[Dict] = []

        with zipfile.ZipFile(master_buf, "w", zipfile.ZIP_DEFLATED) as master_zf:
            for territory in territories:
                # ── Check stop flag ────────────────────────────────────────────
                async with self:
                    if not self.batch_running:
                        self._batch_append_log("⏹ Batch stopped by user.")
                        break

                    self.batch_current_territory = territory
                    self.batch_current_step = STEPS["geometry"]
                    self._batch_append_log(f"▶ Processing: {territory}")

                t_result: Dict[str, Any] = {"territory": territory, "status": "error"}

                try:
                    # ─── Step 1: EE geometry (instant, local GeoPackage) ────
                    def _get_ee_geom(terr=territory):
                        from ..utils.territory_service import get_territory_service
                        svc = get_territory_service()
                        geojson = svc.get_geojson_for_key(terr)
                        if geojson is None:
                            raise ValueError(f"Territory not found in GeoPackage: {terr}")
                        import ee
                        return ee.Geometry(geojson), geojson

                    ee_geom, raw_geojson = await loop.run_in_executor(None, _get_ee_geom)

                    # ─── Buffer EE geometry ─────────────────────────────────
                    buf_ee_geom = None
                    if buf_enabled:
                        def _make_buffer(geom=ee_geom, km=buf_km):
                            from ..utils.buffer_utils import create_external_buffer
                            return create_external_buffer(geom, km)
                        try:
                            buf_ee_geom = await loop.run_in_executor(None, _make_buffer)
                        except Exception as be:
                            logger.warning(f"Buffer creation failed (non-fatal): {be}")

                    # ─── Decide regions: 1 region or 4 quadrants ─────────────
                    # Large territories (>2 M ha) time out in EE when buffered
                    # — split them into four bounding-box quadrants and run
                    # the whole pipeline on each.  Each quadrant becomes its
                    # own sub-folder in the ZIP (nw/, ne/, sw/, se/).
                    def _get_area_and_shapely(terr=territory):
                        from ..utils.territory_service import get_territory_service
                        svc = get_territory_service()
                        info = svc.get_territory_info(terr)
                        row = svc._get_row(terr)
                        return info.get("superficie_ha", 0), (row.geometry if row is not None else None)

                    try:
                        area_ha, shapely_geom = await loop.run_in_executor(
                            None, _get_area_and_shapely
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

                    # Per-region result containers (region_name → result dict)
                    per_region: Dict[str, Dict[str, Any]] = {}

                    for region_name, region_ee_geom, region_buf_geom in regions:
                        rlabel = f" [{region_name.upper()}]" if region_name else ""
                        rsuffix = f" ({region_name.upper()})" if region_name else ""

                        # Per-region result containers
                        mb_y1_result = mb_y2_result = cmp_result = None
                        glad_result = gfc_result = None
                        buf_mb_result = buf_cmp_result = None
                        buf_glad_result = buf_gfc_result = None

                        if region_name:
                            async with self:
                                self._batch_append_log(f"  ▸ Quadrant {region_name.upper()}…")

                        # ─── Step 2: MapBiomas year1 ────────────────────────
                        if run_mb:
                            async with self:
                                self.batch_current_step = STEPS["mb_y1"].format(year1=year1) + rlabel
                            def _mb_y1(geom=region_ee_geom, yr=year1):
                                from ..utils.ee_service_extended import get_ee_service
                                svc = get_ee_service()
                                return svc.analyze_mapbiomas(geom, yr)
                            df1 = await _ee_with_retry(loop, _mb_y1,
                                                       f"MapBiomas {year1}{rsuffix} ({territory})")
                            if df1 is not None and not df1.empty:
                                mb_y1_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year1, "data": df1.to_dict("records"),
                                }
                            elif df1 is None:
                                async with self:
                                    self._batch_append_log(f"  ⚠ skipped MapBiomas {year1}{rsuffix}")

                        # ─── Step 3: MapBiomas year2 ────────────────────────
                        if run_mb or run_cmp:
                            async with self:
                                self.batch_current_step = STEPS["mb_y2"].format(year2=year2) + rlabel
                            def _mb_y2(geom=region_ee_geom, yr=year2):
                                from ..utils.ee_service_extended import get_ee_service
                                svc = get_ee_service()
                                return svc.analyze_mapbiomas(geom, yr)
                            df2 = await _ee_with_retry(loop, _mb_y2,
                                                       f"MapBiomas {year2}{rsuffix} ({territory})")
                            if df2 is not None and not df2.empty:
                                mb_y2_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year2, "data": df2.to_dict("records"),
                                }
                            elif df2 is None:
                                async with self:
                                    self._batch_append_log(f"  ⚠ skipped MapBiomas {year2}{rsuffix}")

                        # ─── Step 4: Comparison ─────────────────────────────
                        if run_cmp and mb_y1_result and mb_y2_result:
                            async with self:
                                self.batch_current_step = STEPS["comparison"].format(
                                    year1=year1, year2=year2
                                ) + rlabel
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
                            cmp_result = await _ee_with_retry(
                                loop, _cmp, f"Comparison {year1}→{year2}{rsuffix} ({territory})"
                            )
                            if cmp_result is None:
                                async with self:
                                    self._batch_append_log(f"  ⚠ skipped comparison{rsuffix}")

                        # ─── Step 5: Hansen GLAD ─────────────────────────────
                        if run_glad:
                            async with self:
                                self.batch_current_step = STEPS["glad"].format(
                                    hansen_year=hansen_year
                                ) + rlabel
                            def _glad(geom=region_ee_geom, yr=hansen_year):
                                from ..utils.hansen_analysis import get_hansen_analyzer
                                analyzer = get_hansen_analyzer()
                                return analyzer.get_area_distribution(geom, year=int(yr), scale=30)
                            glad_df = await _ee_with_retry(
                                loop, _glad, f"Hansen GLAD {hansen_year}{rsuffix} ({territory})"
                            )
                            if glad_df is not None and not glad_df.empty:
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
                            elif glad_df is None:
                                async with self:
                                    self._batch_append_log(f"  ⚠ skipped Hansen GLAD{rsuffix}")

                        # ─── Step 6: Hansen GFC ──────────────────────────────
                        if run_gfc:
                            async with self:
                                self.batch_current_step = STEPS["gfc"] + rlabel
                            def _gfc(geom=region_ee_geom):
                                from ..utils.hansen_analysis import get_hansen_analyzer
                                analyzer = get_hansen_analyzer()
                                return analyzer.analyze_gfc(geom)
                            gfc_result = await _ee_with_retry(
                                loop, _gfc, f"Hansen GFC{rsuffix} ({territory})"
                            )
                            if gfc_result and "error" in gfc_result:
                                gfc_result = None
                            if gfc_result:
                                gfc_result["territory"] = territory
                            else:
                                async with self:
                                    self._batch_append_log(f"  ⚠ skipped Hansen GFC{rsuffix}")

                        # ─── Steps 7-10: Buffer analyses (region slice) ─────
                        # region_buf_geom is the FULL territory's buffer ring
                        # clipped to this quadrant's bounding box — built BEFORE
                        # the regions loop so the buffer is geometrically correct
                        # (not separate per-quadrant buffers).
                        if buf_enabled and region_buf_geom is not None:
                            if run_mb:
                                async with self:
                                    self.batch_current_step = STEPS["buf_mb"].format(year1=year1) + rlabel
                                def _buf_mb(geom=region_buf_geom, yr=year1):
                                    from ..utils.ee_service_extended import get_ee_service
                                    svc = get_ee_service()
                                    return svc.analyze_mapbiomas(geom, yr)
                                bdf = await _ee_with_retry(
                                    loop, _buf_mb, f"Buffer MapBiomas {year1}{rsuffix} ({territory})"
                                )
                                if bdf is not None and not bdf.empty:
                                    buf_mb_result = {
                                        "type": "mapbiomas",
                                        "territory": f"{territory} - Buffer {buf_km:g}km",
                                        "year": year1,
                                        "data": bdf.to_dict("records"),
                                    }
                                elif bdf is None:
                                    async with self:
                                        self._batch_append_log(f"  ⚠ skipped buffer MapBiomas {year1}{rsuffix}")

                            if run_cmp:
                                async with self:
                                    self.batch_current_step = STEPS["buf_cmp"].format(
                                        year1=year1, year2=year2
                                    ) + rlabel
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
                                buf_cmp_result = await _ee_with_retry(
                                    loop, _buf_cmp,
                                    f"Buffer comparison {year1}→{year2}{rsuffix} ({territory})"
                                )
                                if buf_cmp_result is None:
                                    async with self:
                                        self._batch_append_log(f"  ⚠ skipped buffer comparison{rsuffix}")

                            if run_glad:
                                async with self:
                                    self.batch_current_step = STEPS["buf_glad"] + rlabel
                                def _buf_glad(geom=region_buf_geom, yr=hansen_year):
                                    from ..utils.hansen_analysis import get_hansen_analyzer
                                    analyzer = get_hansen_analyzer()
                                    return analyzer.get_area_distribution(geom, year=int(yr), scale=30)
                                bgdf = await _ee_with_retry(
                                    loop, _buf_glad, f"Buffer Hansen GLAD{rsuffix} ({territory})"
                                )
                                if bgdf is not None and not bgdf.empty:
                                    buf_glad_result = {
                                        "type": "hansen_glad",
                                        "territory": f"{territory} - Buffer {buf_km:g}km",
                                        "year": hansen_year,
                                        "data": bgdf.to_dict("records"),
                                    }
                                elif bgdf is None:
                                    async with self:
                                        self._batch_append_log(f"  ⚠ skipped buffer Hansen GLAD{rsuffix}")

                            if run_gfc:
                                async with self:
                                    self.batch_current_step = STEPS["buf_gfc"] + rlabel
                                def _buf_gfc(geom=region_buf_geom):
                                    from ..utils.hansen_analysis import get_hansen_analyzer
                                    analyzer = get_hansen_analyzer()
                                    r = analyzer.analyze_gfc(geom)
                                    return r if r and "error" not in r else None
                                buf_gfc_result = await _ee_with_retry(
                                    loop, _buf_gfc, f"Buffer Hansen GFC{rsuffix} ({territory})"
                                )
                                if buf_gfc_result:
                                    buf_gfc_result["territory"] = f"{territory} - Buffer {buf_km:g}km"
                                else:
                                    async with self:
                                        self._batch_append_log(f"  ⚠ skipped buffer Hansen GFC{rsuffix}")

                        # Track accumulated success across regions
                        if mb_y1_result: had_mb_y1 = True
                        if mb_y2_result: had_mb_y2 = True
                        if cmp_result: had_cmp = True
                        if glad_result: had_glad = True
                        if gfc_result: had_gfc = True
                        if any([buf_mb_result, buf_cmp_result, buf_glad_result, buf_gfc_result]):
                            had_buffer = True

                        # ─── Step 11: Write THIS region to master ZIP ───────
                        async with self:
                            self.batch_current_step = STEPS["export"] + rlabel

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
                        ):
                            from ..utils.export_service import (
                                _slug, _write_mapbiomas_section,
                                _write_hansen_glad_section, _write_hansen_gfc_section,
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

                        await loop.run_in_executor(None, _write_region_to_zip)

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
                    await loop.run_in_executor(None, _write_boundary)

                    # ─── PDF maps (satellite + MapBiomas y1/y2, per territory) ──
                    if run_maps:
                        async with self:
                            self.batch_current_step = STEPS["maps"]

                        def _write_pdf_maps(
                            zf=master_zf,
                            terr=territory,
                            geojson=raw_geojson,
                            ee_g=ee_geom,
                            buf_ee=buf_ee_geom,
                            y1=year1, y2=year2, hy=hansen_year,
                            do_mb=(run_mb or run_cmp),
                            do_glad=run_glad,
                        ):
                            try:
                                from ..utils.export_service import _slug
                                from ..utils.map_export_service import create_map_set
                                t_slug = _slug(terr)
                                # Buffer outline (single EE round-trip if available)
                                buf_gj = None
                                if buf_ee is not None:
                                    try:
                                        buf_gj = buf_ee.getInfo()
                                    except Exception as be:
                                        logger.warning(f"buffer geojson for {terr} failed: {be}")

                                mb_years: List[int] = []
                                if do_mb:
                                    if y1 == y2:
                                        mb_years = [int(y1)]
                                    else:
                                        mb_years = [int(y1), int(y2)]
                                glad_layers = [str(hy)] if do_glad else None

                                maps = create_map_set(
                                    drawn_features=[],
                                    territory_name=terr,
                                    active_mapbiomas_years=mb_years,
                                    active_hansen_layers=glad_layers,
                                    ee_geometry=ee_g,
                                    territory_geojson=geojson,
                                    buffer_geojson=buf_gj,
                                    image_format="png",
                                )
                                for name, img_bytes in (maps or {}).items():
                                    zf.writestr(
                                        f"territory/{t_slug}/maps/{t_slug}_{name}.png",
                                        img_bytes,
                                    )
                            except Exception as me:
                                logger.warning(
                                    f"PDF maps for {terr} failed (non-fatal): {me}",
                                    exc_info=True,
                                )

                        try:
                            await loop.run_in_executor(None, _write_pdf_maps)
                        except Exception as me:
                            async with self:
                                self._batch_append_log(f"  ⚠ PDF maps skipped: {me}")

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

            # ── Finalize ZIP: add summary files ────────────────────────────
            async with self:
                self.batch_current_step = "📋 Writing summary files…"

            def _write_summary(
                zf=master_zf,
                summary=batch_summary,
                territories=territories,
                y1=year1, y2=year2, hy=hansen_year,
                bkm=buf_km, ben=buf_enabled,
            ):
                ts = datetime.now().isoformat()
                meta = {
                    "generated": ts,
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

            await loop.run_in_executor(None, _write_summary)

        # Store bytes in module-level variable
        zip_bytes = master_buf.getvalue()
        _batch_zip_bytes = zip_bytes

        async with self:
            self.batch_running = False
            self.batch_done = True
            self.batch_zip_ready = bool(zip_bytes)
            self.batch_current_territory = ""
            self.batch_current_step = STEPS["done"]
            n_ok = len(self.batch_completed)
            n_fail = len(self.batch_failed)
            self._batch_append_log(
                f"🏁 Batch complete: {n_ok} OK, {n_fail} failed — "
                f"ZIP size {len(zip_bytes)//1024} KB"
            )
            logger.info(f"Batch processing complete: {n_ok}/{len(territories)} territories")
