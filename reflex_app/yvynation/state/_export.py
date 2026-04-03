"""
Export event handlers: CSV download, ZIP archive, and PDF map generation.
"""
import logging

import reflex as rx

logger = logging.getLogger(__name__)


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
            filename = f"{territory}_{a_type}_{year}.csv".replace(" ", "_")
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"Export error: {e}"

    def download_mapbiomas_csv(self):
        """Download MapBiomas analysis results as CSV."""
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
            territory = self.mapbiomas_analysis_result.get("territory", "unknown")
            year = self.mapbiomas_analysis_result.get("year", "")
            filename = f"{territory}_MapBiomas_{year}.csv".replace(" ", "_")
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"MapBiomas export error: {e}"

    def download_hansen_csv(self):
        """Download Hansen analysis results as CSV."""
        try:
            import pandas as pd

            if not self.hansen_analysis_result:
                self.error_message = "No Hansen analysis data to export"
                return

            data = self.hansen_analysis_result.get("data", [])
            if not data:
                self.error_message = "No Hansen data to export"
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            territory = self.hansen_analysis_result.get("territory", "unknown")
            year = self.hansen_analysis_result.get("year", "")
            filename = f"{territory}_Hansen_{year}.csv".replace(" ", "_")
            return rx.download(data=csv_content, filename=filename)

        except Exception as e:
            self.error_message = f"Hansen export error: {e}"

    def download_comparison_csv(self):
        """Download MapBiomas comparison results as CSV."""
        try:
            import pandas as pd

            if not self.mapbiomas_comparison_result:
                self.error_message = "No comparison data to export"
                return

            data = self.mapbiomas_comparison_result.get("data", [])
            if not data:
                return

            df = pd.DataFrame(data)
            csv_content = df.to_csv(index=False)
            year1 = self.mapbiomas_comparison_result.get("year_start", "")
            year2 = self.mapbiomas_comparison_result.get("year_end", "")
            filename = f"comparison_{year1}_vs_{year2}.csv"
            return rx.download(data=csv_content, filename=filename)

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
