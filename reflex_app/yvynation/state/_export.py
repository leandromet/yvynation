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

            self.export_pending = False
            self.loading_message = ""
            return rx.download(data=zip_bytes, filename=filename)

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

            maps = create_map_set(
                drawn_features=self.drawn_features,
                territory_name=self.territory_name or self.selected_territory,
                active_mapbiomas_years=self.mapbiomas_displayed_years,
                active_hansen_layers=self.hansen_displayed_layers,
                ee_geometry=ee_geometry,
                territory_geojson=territory_geojson,
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
