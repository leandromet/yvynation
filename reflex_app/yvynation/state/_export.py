"""
Export event handlers: CSV download, ZIP archive, and PDF map generation.
"""
import logging

import reflex as rx

logger = logging.getLogger(__name__)


def _export_slug(name: str) -> str:
    """Quick filesystem-safe slug (mirrors export_service._slug without the import)."""
    import re, unicodedata
    norm = unicodedata.normalize("NFD", str(name))
    ascii_name = norm.encode("ascii", "ignore").decode("ascii")
    ascii_name = re.sub(r"[\s\(\)\[\]{}/\\:;,\-–—]+", "_", ascii_name)
    return re.sub(r"_+", "_", ascii_name).strip("_") or "unknown"


def _nest_zip_bytes(out_zip, inner_bytes: bytes, prefix: str):
    """Copy every entry of an in-memory ZIP into *out_zip* under *prefix*/."""
    import io, zipfile
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        for name in inner.namelist():
            try:
                out_zip.writestr(f"{prefix}/{name}", inner.read(name))
            except Exception as e:
                logger.warning(f"[DOWNLOAD-ALL] could not copy {name}: {e}")


def _build_area_maps(entry: dict, y1: int, y2: int, aux_keys):
    """Render the PNG map set for one registry area from its stored geometry."""
    try:
        from ..utils.map_export_service import create_map_set
        from ..utils.buffer_utils import convert_geojson_to_ee_geometry
        feat = entry.get("geojson")
        if not feat:
            return {}
        ee_geom = convert_geojson_to_ee_geometry(feat)
        geojson = feat.get("geometry") if feat.get("type") == "Feature" else feat
        buf = entry.get("buffer_geojson")
        buf_geojson = None
        if buf:
            bg = convert_geojson_to_ee_geometry(buf)
            if bg is not None:
                try:
                    buf_geojson = bg.getInfo()
                except Exception:
                    buf_geojson = buf.get("geometry") if buf.get("type") == "Feature" else buf
        mb_years = [y1] if y1 == y2 else sorted({y1, y2})
        aux_layers = [(k, y2) for k in aux_keys]
        return create_map_set(
            drawn_features=[],
            territory_name=entry.get("label"),
            active_mapbiomas_years=mb_years,
            active_hansen_layers=None,
            ee_geometry=ee_geom,
            territory_geojson=geojson,
            buffer_geojson=buf_geojson,
            image_format="png",
            active_aux_layers=aux_layers or None,
        )
    except Exception as e:
        logger.warning(f"[DOWNLOAD-ALL] map build error: {e}")
        return {}


class ExportMixin(rx.State, mixin=True):
    """Event handlers for data and map export."""

    # ---- CSV downloads --------------------------------------------------

    def download_analysis_csv(self):
        """Download the currently active analysis results as CSV."""
        try:
            import pandas as pd

            data = self.analysis_results.get("data", [])
            if not data:
                self.error_message = "No analysis data to export"
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            a_type = self.analysis_results.get("type", "analysis")
            territory = self.analysis_results.get("geometry", "unknown")
            year = self.analysis_results.get("year", "")
            slug = _export_slug(territory)
            filename = f"{slug}_{a_type}_{year}_data.csv"
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"Export error: {e}"

    def download_mapbiomas_csv(self):
        """Download MapBiomas land-cover analysis results as CSV."""
        try:
            import pandas as pd

            if not self.mapbiomas_analysis_result:
                self.error_message = "No MapBiomas analysis data to export"
                return

            data = self.mapbiomas_analysis_result.get("data", [])
            if not data:
                self.error_message = "No MapBiomas data to export"
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            territory = self.mapbiomas_analysis_result.get(
                "territory", self.selected_territory or "unknown"
            )
            year = self.mapbiomas_analysis_result.get("year", "")
            slug = _export_slug(territory)
            filename = f"{slug}_mapbiomas_{year}_landcover.csv"
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"MapBiomas export error: {e}"

    def download_hansen_csv(self):
        """Download Hansen GLAD distribution results as CSV."""
        try:
            import pandas as pd

            # Prefer geometry_glad_result (territory GLAD tab) over generic hansen_analysis_result
            result = self.geometry_glad_result or self.hansen_analysis_result
            if not result:
                self.error_message = "No Hansen analysis data to export"
                return

            data = result.get("data", [])
            if not data:
                self.error_message = "No Hansen data to export"
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            territory = (
                result.get("territory")
                or result.get("geometry_name")
                or self.selected_territory
                or "unknown"
            )
            year = result.get("year", "") or result.get("summary", {}).get("year", "")
            slug = _export_slug(territory)
            filename = f"{slug}_hansen_glad_{year}_distribution.csv"
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"Hansen export error: {e}"

    def download_gfc_csv(self):
        """Download Hansen GFC summary as CSV."""
        try:
            import pandas as pd, io, zipfile

            result = self.geometry_gfc_result
            if not result:
                self.error_message = "No Hansen GFC data to export"
                return

            territory = result.get("geometry_name", self.selected_territory or "unknown")
            slug = _export_slug(territory)

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                # Summary
                gfc_data = result.get("data", [])
                if gfc_data:
                    zf.writestr(
                        f"{slug}_hansen_gfc_summary.csv",
                        pd.DataFrame(gfc_data).to_csv(index=False),
                    )
                # Loss by year
                loss_rows = [r for r in result.get("tree_loss_data", []) if r.get("Year_Code", 0) > 0]
                if loss_rows:
                    zf.writestr(
                        f"{slug}_hansen_gfc_loss_by_year.csv",
                        pd.DataFrame(loss_rows).to_csv(index=False),
                    )
                # Gain
                gain_rows = result.get("tree_gain_data", [])
                if gain_rows:
                    zf.writestr(
                        f"{slug}_hansen_gfc_gain.csv",
                        pd.DataFrame(gain_rows).to_csv(index=False),
                    )
            buf.seek(0)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            return rx.download(data=buf.read(), filename=f"{slug}_hansen_gfc_{ts}.zip")

        except Exception as e:
            self.error_message = f"GFC export error: {e}"

    def download_comparison_csv(self):
        """Download MapBiomas year-comparison results as CSV (territory + buffer if available)."""
        try:
            import pandas as pd, io, zipfile

            if not self.mapbiomas_comparison_result:
                self.error_message = "No comparison data to export"
                return

            territory = (
                self.mapbiomas_comparison_result.get("territory")
                or self.territory_name
                or self.selected_territory
                or "unknown"
            )
            y1 = self.mapbiomas_comparison_result.get("year_start", "")
            y2 = self.mapbiomas_comparison_result.get("year_end", "")
            t_slug = _export_slug(territory)

            t_data = self.mapbiomas_comparison_result.get("data", [])
            buf_cmp = self.buffer_mapbiomas_comparison_result

            # Single territory, no buffer → plain CSV
            if not buf_cmp:
                if not t_data:
                    return
                csv_content = pd.DataFrame(t_data).to_csv(index=False)
                filename = f"{t_slug}_mapbiomas_{y1}_vs_{y2}_comparison.csv"
                return rx.download(data=csv_content, filename=filename)

            # Territory + buffer → ZIP with two CSVs
            buf_territory = (
                buf_cmp.get("territory")
                or self.current_buffer_for_analysis
                or f"{t_slug}_Buffer"
            )
            b_slug = _export_slug(buf_territory)

            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                if t_data:
                    zf.writestr(
                        f"{t_slug}_mapbiomas_{y1}_vs_{y2}_comparison.csv",
                        pd.DataFrame(t_data).to_csv(index=False),
                    )
                buf_data = buf_cmp.get("data", [])
                if buf_data:
                    zf.writestr(
                        f"{b_slug}_mapbiomas_{y1}_vs_{y2}_comparison.csv",
                        pd.DataFrame(buf_data).to_csv(index=False),
                    )
            zip_buf.seek(0)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"{t_slug}_mapbiomas_{y1}_vs_{y2}_comparison_{ts}.zip"
            return rx.download(data=zip_buf.read(), filename=filename)

        except Exception as e:
            self.error_message = f"Export error: {e}"

    # ---- ZIP export -----------------------------------------------------

    def export_analysis_zip(self):
        """Generate and download a ZIP archive with all analysis data and figures."""
        try:
            from ..utils.export_service import create_export_zip, collect_export_data_from_state
            from datetime import datetime

            self.export_pending = True
            self.loading_message = "Preparing export..."

            export_data = collect_export_data_from_state(self)
            zip_bytes = create_export_zip(**export_data)

            territory = self.territory_name or self.selected_territory or "analysis"
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"yvynation_{territory}_{ts}.zip".replace(" ", "_")

            # Serve from the exports dir over HTTP — reliable at any size
            # (a base64 data-URI over the websocket is not).
            from ..utils.export_service import save_export_to_upload_dir, get_download_url
            rel = save_export_to_upload_dir(zip_bytes, filename)

            self.export_pending = False
            self.loading_message = ""
            return rx.download(url=get_download_url(rel), filename=filename)

        except Exception as e:
            self.error_message = f"Export failed: {e}"
            self.export_pending = False
            self.loading_message = ""
            logger.error(f"Export ZIP error: {e}")

    # ---- PDF map export -------------------------------------------------

    def export_pdf_maps(self):
        """Generate and download PDF maps for all active layers."""
        try:
            from ..utils.map_export_service import create_map_set
            import zipfile as zf_module
            import io
            from datetime import datetime

            self.map_export_pending = True
            self.loading_message = "Generating PDF maps..."

            territory_geojson = None
            ee_geometry = None
            if self.selected_territory:
                try:
                    from ..utils.ee_service_extended import get_ee_service

                    ee_service = get_ee_service()
                    ee_geometry = ee_service.get_territory_geometry(self.selected_territory)
                    if ee_geometry:
                        territory_geojson = ee_geometry.getInfo()
                except Exception:
                    pass

            # Buffer overlay (external ring) when one is active — parity with
            # the batch PNG map set and the interactive Maps tab.
            buffer_geojson = None
            if self.buffer_geojson_features:
                try:
                    from ..utils.buffer_utils import convert_geojson_to_ee_geometry
                    bg = convert_geojson_to_ee_geometry(self.buffer_geojson_features[0])
                    if bg is not None:
                        buffer_geojson = bg.getInfo()
                except Exception:
                    pass

            # Auxiliary MapBiomas rasters selected on the Maps tab (rendered for
            # comparison year 2; fire_frequency is full-period).
            from ._advanced_viz import _AUX_KEY_MAP
            aux_layers = [
                (key, int(self.comparison_year2))
                for attr, key in _AUX_KEY_MAP if getattr(self, attr, False)
            ]

            maps = create_map_set(
                drawn_features=self.drawn_features,
                territory_name=self.territory_name or self.selected_territory,
                active_mapbiomas_years=self.mapbiomas_displayed_years,
                active_hansen_layers=self.hansen_displayed_layers,
                ee_geometry=ee_geometry,
                territory_geojson=territory_geojson,
                buffer_geojson=buffer_geojson,
                active_aux_layers=aux_layers or None,
            )

            if not maps:
                self.error_message = "No maps generated. Add layers first."
                self.map_export_pending = False
                self.loading_message = ""
                return

            self.map_export_pending = False
            self.loading_message = ""

            if len(maps) == 1:
                name, pdf_bytes = next(iter(maps.items()))
                return rx.download(data=pdf_bytes, filename=f"{name}.pdf")

            # Multiple maps → ZIP
            buf = io.BytesIO()
            with zf_module.ZipFile(buf, "w", zf_module.ZIP_DEFLATED) as zipf:
                for name, pdf_bytes in maps.items():
                    zipf.writestr(f"maps/{name}.pdf", pdf_bytes)
            buf.seek(0)

            territory = self.territory_name or self.selected_territory or "maps"
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"yvynation_maps_{territory}_{ts}.zip".replace(" ", "_")
            return rx.download(data=buf.read(), filename=filename)

        except Exception as e:
            self.error_message = f"Map export failed: {e}"
            self.map_export_pending = False
            self.loading_message = ""
            logger.error(f"PDF map export error: {e}")

    # ---- Combined download-all (data + viz + maps, every analyzed area) --

    @rx.event(background=True)
    async def download_all_results(self):
        """Bundle data + viz + maps for EVERY analyzed area into one ZIP.

        For each registered area with results: temporarily activates its result
        bundle to reuse the existing ``collect_export_data_from_state`` +
        ``create_export_zip`` machinery (data + figures), then renders its PNG
        map set from the stored geometry/buffer. Areas land in their own
        top-level folder. The originally-active result is restored at the end.

        The combined ZIP is written directly to ``uploaded_files/exports/``
        (memory stays flat regardless of area count) and downloaded over HTTP
        via the ``/_upload`` mount — a websocket data-URI would fail beyond a
        few tens of MB.
        """
        import asyncio
        import zipfile
        from datetime import datetime

        from ..utils.export_service import get_export_dir, prune_old_exports

        loop = asyncio.get_event_loop()
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        zip_filename = f"yvynation_all_results_{ts}.zip"
        zip_path = get_export_dir() / zip_filename
        try:
            async with self:
                entries = [
                    dict(e) for e in self.analysis_targets.values()
                    if e.get("has_results")
                ]
                original_key = self.active_result_key
                y1 = int(self.comparison_year1)
                y2 = int(self.comparison_year2)
                from ._advanced_viz import _AUX_KEY_MAP
                aux_keys = tuple(k for attr, k in _AUX_KEY_MAP if getattr(self, attr, False))
                self.export_pending = True
                self.loading_message = f"Bundling {len(entries)} area(s)…"

            if not entries:
                async with self:
                    self.export_pending = False
                    self.loading_message = ""
                    self.error_message = "No analyzed areas to download yet."
                return

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as out:
                for entry in entries:
                    rk = entry.get("result_key") or ""
                    label = entry.get("label") or rk or "area"
                    slug = _export_slug(label)

                    # 1) Data + figures (needs the area's result active in state)
                    data = None
                    try:
                        async with self:
                            if rk:
                                self.switch_result(rk)
                            self.loading_message = f"Collecting {label}…"
                            from ..utils.export_service import collect_export_data_from_state
                            data = collect_export_data_from_state(self)
                    except Exception as ce:
                        logger.warning(f"[DOWNLOAD-ALL] collect failed for {label}: {ce}")
                    if data is not None:
                        try:
                            from ..utils.export_service import create_export_zip
                            zbytes = await loop.run_in_executor(
                                None, lambda d=data: create_export_zip(**d)
                            )
                            _nest_zip_bytes(out, zbytes, f"{slug}/analysis")
                        except Exception as ze:
                            logger.warning(f"[DOWNLOAD-ALL] zip failed for {label}: {ze}")

                    # 2) PNG map set (generated fresh from stored geometry)
                    try:
                        async with self:
                            self.loading_message = f"Rendering maps for {label}…"
                        maps = await loop.run_in_executor(
                            None, _build_area_maps, entry, y1, y2, aux_keys
                        )
                        for nm, b in (maps or {}).items():
                            out.writestr(f"{slug}/maps/{slug}_{nm}.png", b)
                    except Exception as me:
                        logger.warning(f"[DOWNLOAD-ALL] maps failed for {label}: {me}")

                out.writestr(
                    "README.txt",
                    "Yvynation — combined results export\n"
                    f"Generated: {datetime.now().isoformat()}\n"
                    f"Areas: {len(entries)}\n"
                    f"MapBiomas years: {y1} / {y2}\n"
                    "Each area folder holds analysis/ (data + figures) and maps/.\n",
                )

            prune_old_exports()

            # Restore the user's original active result
            async with self:
                if original_key:
                    try:
                        self.switch_result(original_key)
                    except Exception:
                        pass
                self.export_pending = False
                self.loading_message = ""

            from ..utils.export_service import get_download_url
            download_url = await loop.run_in_executor(
                None, get_download_url, f"exports/{zip_filename}"
            )
            yield rx.download(url=download_url, filename=zip_filename)

        except Exception as e:
            logger.error(f"[DOWNLOAD-ALL] failed: {e}", exc_info=True)
            try:
                zip_path.unlink(missing_ok=True)
            except OSError:
                pass
            async with self:
                self.export_pending = False
                self.loading_message = ""
                self.error_message = f"Download-all failed: {e}"
