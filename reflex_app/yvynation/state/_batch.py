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
    "export":       "📦 Packaging data…",
    "done":         "✅ Done",
}


class BatchMixin(rx.State, mixin=True):
    """Event handlers and helpers for the batch-processing page."""

    # ---- Configuration -------------------------------------------------------
    batch_selected_territories: List[str] = []
    batch_year: int = 2024        # single-year MapBiomas
    batch_year2: int = 2019       # comparison year
    batch_hansen_year: str = "2020"
    batch_buffer_km: float = 10.0
    batch_buffer_enabled: bool = True
    batch_run_mapbiomas: bool = True
    batch_run_comparison: bool = True
    batch_run_glad: bool = True
    batch_run_gfc: bool = True
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
            self.batch_year = int(year)
        except (ValueError, TypeError):
            pass

    def batch_set_year2(self, year: str):
        try:
            self.batch_year2 = int(year)
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
            year1 = int(self.batch_year)
            year2 = int(self.batch_year2)
            hansen_year = str(self.batch_hansen_year)
            buf_km = float(self.batch_buffer_km)
            buf_enabled = bool(self.batch_buffer_enabled)
            run_mb = bool(self.batch_run_mapbiomas)
            run_cmp = bool(self.batch_run_comparison)
            run_glad = bool(self.batch_run_glad)
            run_gfc = bool(self.batch_run_gfc)

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

                    # Build all result containers
                    mb_y1_result = mb_y2_result = cmp_result = None
                    glad_result = gfc_result = None
                    buf_mb_result = buf_cmp_result = None
                    buf_glad_result = buf_gfc_result = None

                    # ─── Step 2: MapBiomas year1 ────────────────────────────
                    if run_mb:
                        async with self:
                            self.batch_current_step = STEPS["mb_y1"].format(year1=year1)
                        def _mb_y1(geom=ee_geom, yr=year1):
                            from ..utils.ee_service_extended import get_ee_service
                            svc = get_ee_service()
                            df = svc.analyze_mapbiomas(geom, yr)
                            return df
                        try:
                            df1 = await loop.run_in_executor(None, _mb_y1)
                            if df1 is not None and not df1.empty:
                                mb_y1_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year1, "data": df1.to_dict("records"),
                                }
                        except Exception as e:
                            logger.warning(f"MapBiomas {year1} failed for {territory}: {e}")

                    # ─── Step 3: MapBiomas year2 ────────────────────────────
                    if run_mb or run_cmp:
                        async with self:
                            self.batch_current_step = STEPS["mb_y2"].format(year2=year2)
                        def _mb_y2(geom=ee_geom, yr=year2):
                            from ..utils.ee_service_extended import get_ee_service
                            svc = get_ee_service()
                            return svc.analyze_mapbiomas(geom, yr)
                        try:
                            df2 = await loop.run_in_executor(None, _mb_y2)
                            if df2 is not None and not df2.empty:
                                mb_y2_result = {
                                    "type": "mapbiomas", "territory": territory,
                                    "year": year2, "data": df2.to_dict("records"),
                                }
                        except Exception as e:
                            logger.warning(f"MapBiomas {year2} failed for {territory}: {e}")

                    # ─── Step 4: Comparison ─────────────────────────────────
                    if run_cmp and mb_y1_result and mb_y2_result:
                        async with self:
                            self.batch_current_step = STEPS["comparison"].format(
                                year1=year1, year2=year2
                            )
                        def _cmp(geom=ee_geom, y1=year1, y2=year2):
                            from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                            from ..utils.visualization import calculate_gains_losses
                            import pandas as pd
                            analyzer = get_mapbiomas_analyzer()
                            df_y1 = analyzer.analyze_single_year(geom, y1, scale=30)
                            df_y2 = analyzer.analyze_single_year(geom, y2, scale=30)
                            gains, losses, net = calculate_gains_losses(df_y1, df_y2)
                            transitions = {}
                            try:
                                raw_trans = analyzer.compute_transitions(geom, y1, y2, 30)
                                if raw_trans:
                                    transitions = {str(k): v for k, v in raw_trans.items()}
                            except Exception:
                                pass
                            rows = []
                            name_col = "Class_Name" if "Class_Name" in df_y2.columns else "Class"
                            area_col = "Area_ha"
                            for _, row in df_y2.iterrows():
                                cls = row[name_col]
                                a1 = float(
                                    df_y1.loc[df_y1[name_col] == cls, area_col].sum()
                                ) if not df_y1.empty else 0
                                a2 = float(row[area_col])
                                rows.append({
                                    "Class": cls, f"Area_{y1}_ha": a1,
                                    f"Area_{y2}_ha": a2, "Change_ha": a2 - a1,
                                })
                            return {
                                "territory": territory,
                                "year_start": y1, "year_end": y2,
                                "data": rows,
                                "gains_ha": float(gains),
                                "losses_ha": float(losses),
                                "net_ha": float(net),
                                "transitions": transitions,
                            }, df_y1.to_dict("records"), df_y2.to_dict("records")
                        try:
                            cmp_result, raw_y1, raw_y2 = await loop.run_in_executor(None, _cmp)
                        except Exception as e:
                            logger.warning(f"Comparison failed for {territory}: {e}")

                    # ─── Step 5: Hansen GLAD ────────────────────────────────
                    if run_glad:
                        async with self:
                            self.batch_current_step = STEPS["glad"].format(
                                hansen_year=hansen_year
                            )
                        def _glad(geom=ee_geom, yr=hansen_year):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            df = analyzer.get_area_distribution(geom, year=int(yr), scale=30)
                            return df
                        try:
                            glad_df = await loop.run_in_executor(None, _glad)
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
                        except Exception as e:
                            logger.warning(f"Hansen GLAD failed for {territory}: {e}")

                    # ─── Step 6: Hansen GFC ─────────────────────────────────
                    if run_gfc:
                        async with self:
                            self.batch_current_step = STEPS["gfc"]
                        def _gfc(geom=ee_geom):
                            from ..utils.hansen_analysis import get_hansen_analyzer
                            analyzer = get_hansen_analyzer()
                            return analyzer.analyze_gfc(geom)
                        try:
                            gfc_result = await loop.run_in_executor(None, _gfc)
                            if gfc_result and "error" in gfc_result:
                                gfc_result = None
                            if gfc_result:
                                gfc_result["territory"] = territory
                        except Exception as e:
                            logger.warning(f"Hansen GFC failed for {territory}: {e}")

                    # ─── Steps 7–10: Buffer analyses ────────────────────────
                    if buf_enabled and buf_ee_geom is not None:
                        if run_mb:
                            async with self:
                                self.batch_current_step = STEPS["buf_mb"].format(year1=year1)
                            def _buf_mb(geom=buf_ee_geom, yr=year1):
                                from ..utils.ee_service_extended import get_ee_service
                                svc = get_ee_service()
                                return svc.analyze_mapbiomas(geom, yr)
                            try:
                                bdf = await loop.run_in_executor(None, _buf_mb)
                                if bdf is not None and not bdf.empty:
                                    buf_mb_result = {
                                        "type": "mapbiomas",
                                        "territory": f"Buffer {buf_km}km - {territory}",
                                        "year": year1,
                                        "data": bdf.to_dict("records"),
                                    }
                            except Exception as e:
                                logger.warning(f"Buffer MapBiomas failed for {territory}: {e}")

                        if run_cmp:
                            async with self:
                                self.batch_current_step = STEPS["buf_cmp"].format(
                                    year1=year1, year2=year2
                                )
                            def _buf_cmp(geom=buf_ee_geom, y1=year1, y2=year2):
                                from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                                from ..utils.visualization import calculate_gains_losses
                                analyzer = get_mapbiomas_analyzer()
                                df1b = analyzer.analyze_single_year(geom, y1, scale=30)
                                df2b = analyzer.analyze_single_year(geom, y2, scale=30)
                                gains, losses, net = calculate_gains_losses(df1b, df2b)
                                rows = []
                                nc = "Class_Name" if "Class_Name" in df2b.columns else "Class"
                                ac = "Area_ha"
                                for _, row in df2b.iterrows():
                                    cls = row[nc]
                                    a1 = float(df1b.loc[df1b[nc] == cls, ac].sum()) if not df1b.empty else 0
                                    a2 = float(row[ac])
                                    rows.append({"Class": cls, f"Area_{y1}_ha": a1,
                                                 f"Area_{y2}_ha": a2, "Change_ha": a2 - a1})
                                return {
                                    "territory": f"Buffer {buf_km}km - {territory}",
                                    "year_start": y1, "year_end": y2,
                                    "data": rows,
                                    "gains_ha": float(gains),
                                    "losses_ha": float(losses),
                                    "net_ha": float(net),
                                }
                            try:
                                buf_cmp_result = await loop.run_in_executor(None, _buf_cmp)
                            except Exception as e:
                                logger.warning(f"Buffer comparison failed for {territory}: {e}")

                        if run_glad:
                            async with self:
                                self.batch_current_step = STEPS["buf_glad"]
                            def _buf_glad(geom=buf_ee_geom, yr=hansen_year):
                                from ..utils.hansen_analysis import get_hansen_analyzer
                                analyzer = get_hansen_analyzer()
                                return analyzer.get_area_distribution(geom, year=int(yr), scale=30)
                            try:
                                bgdf = await loop.run_in_executor(None, _buf_glad)
                                if bgdf is not None and not bgdf.empty:
                                    buf_glad_result = {
                                        "type": "hansen_glad",
                                        "territory": f"Buffer {buf_km}km - {territory}",
                                        "year": hansen_year,
                                        "data": bgdf.to_dict("records"),
                                    }
                            except Exception as e:
                                logger.warning(f"Buffer GLAD failed for {territory}: {e}")

                        if run_gfc:
                            async with self:
                                self.batch_current_step = STEPS["buf_gfc"]
                            def _buf_gfc(geom=buf_ee_geom):
                                from ..utils.hansen_analysis import get_hansen_analyzer
                                analyzer = get_hansen_analyzer()
                                r = analyzer.analyze_gfc(geom)
                                return r if r and "error" not in r else None
                            try:
                                buf_gfc_result = await loop.run_in_executor(None, _buf_gfc)
                                if buf_gfc_result:
                                    buf_gfc_result["territory"] = f"Buffer {buf_km}km - {territory}"
                            except Exception as e:
                                logger.warning(f"Buffer GFC failed for {territory}: {e}")

                    # ─── Step 11: Write to master ZIP ───────────────────────
                    async with self:
                        self.batch_current_step = STEPS["export"]

                    def _write_territory_to_zip(
                        zf=master_zf,
                        terr=territory,
                        geojson=raw_geojson,
                        y1=year1, y2=year2, hy=hansen_year,
                        bkm=buf_km, ben=buf_enabled,
                        mb1=mb_y1_result, mb2=mb_y2_result, cmp=cmp_result,
                        glad=glad_result, gfc=gfc_result,
                        bmb=buf_mb_result, bcmp=buf_cmp_result,
                        bglad=buf_glad_result, bgfc=buf_gfc_result,
                    ):
                        from ..utils.export_service import _slug, _write_mapbiomas_section
                        from ..utils.export_service import _write_hansen_glad_section
                        from ..utils.export_service import _write_hansen_gfc_section
                        import pandas as pd

                        t_slug = _slug(terr)
                        t_dir = f"territory/{t_slug}"

                        # boundary
                        zf.writestr(
                            f"{t_dir}/boundary.geojson",
                            json.dumps({"type": "Feature", "geometry": geojson,
                                        "properties": {"name": terr}}).encode(),
                        )

                        # MapBiomas section
                        _write_mapbiomas_section(
                            zf, t_dir, t_slug,
                            single_year_result=mb1,
                            comparison_result=cmp,
                            territory_result_y1=cmp.get("_raw_y1") if cmp else None,
                            territory_result_y2=cmp.get("_raw_y2") if cmp else None,
                            transitions=cmp.get("transitions") if cmp else None,
                        )

                        # Hansen GLAD
                        if glad:
                            _write_hansen_glad_section(zf, t_dir, t_slug, result=glad)

                        # Hansen GFC
                        if gfc:
                            _write_hansen_gfc_section(zf, t_dir, t_slug, result=gfc)

                        # Buffer
                        if ben:
                            b_slug = _slug(f"Buffer_{bkm}km_{terr}")
                            b_dir = f"buffer/{b_slug}"
                            if bmb or bcmp:
                                _write_mapbiomas_section(
                                    zf, b_dir, b_slug,
                                    single_year_result=bmb,
                                    comparison_result=bcmp,
                                    transitions=bcmp.get("transitions") if bcmp else None,
                                )
                            if bglad:
                                _write_hansen_glad_section(zf, b_dir, b_slug, result=bglad)
                            if bgfc:
                                _write_hansen_gfc_section(zf, b_dir, b_slug, result=bgfc)

                    await loop.run_in_executor(None, _write_territory_to_zip)

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
