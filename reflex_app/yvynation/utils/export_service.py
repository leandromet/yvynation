"""
Phase 5: Export service for generating ZIP bundles with analysis data.
Ports Streamlit's export_utils.py to work with Reflex AppState.

Generates organized ZIP with:
  - metadata.json
  - geometries.geojson
  - polygons/polygon_N/{analysis}_data.csv
  - territory/{name}/{analysis}.csv, transitions.json, figures/
  - figures/{name}.png, {name}.html
  - maps/{name}.pdf
"""

import io
import json
import zipfile
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def _fig_to_png_bytes(fig, dpi: int = 150) -> Optional[bytes]:
    """Convert a matplotlib Figure to PNG bytes."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.warning(f"Could not convert figure to PNG: {e}")
        return None


def _plotly_to_html_bytes(fig) -> Optional[bytes]:
    """Convert a Plotly figure to interactive HTML bytes."""
    try:
        html_str = fig.to_html(include_plotlyjs='cdn', full_html=True)
        return html_str.encode('utf-8')
    except Exception as e:
        logger.warning(f"Could not convert Plotly figure to HTML: {e}")
        return None


def _plotly_to_png_bytes(fig, width: int = 1200, height: int = 600) -> Optional[bytes]:
    """Convert Plotly figure to PNG bytes (requires kaleido)."""
    try:
        return fig.to_image(format='png', width=width, height=height)
    except Exception as e:
        logger.warning(f"Plotly PNG export failed (install kaleido?): {e}")
        return None


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes."""
    return df.to_csv(index=False).encode('utf-8')


def _geojson_from_features(features: List[Dict]) -> Dict:
    """Build a GeoJSON FeatureCollection from drawn features."""
    fc = {"type": "FeatureCollection", "features": []}
    for feat in features:
        geom = feat.get("geometry")
        if not geom and "coordinates" in feat:
            geom = {"type": feat.get("type", "Polygon"), "coordinates": feat["coordinates"]}
        if geom:
            fc["features"].append({
                "type": "Feature",
                "geometry": geom,
                "properties": feat.get("properties", {"name": feat.get("name", "Unknown")}),
            })
    return fc


def _territory_geojson(territory_name: str) -> Optional[Dict]:
    """Try to get territory GeoJSON from Earth Engine."""
    try:
        from .ee_service_extended import get_ee_service
        ee_service = get_ee_service()
        ee_geom = ee_service.get_territory_geometry(territory_name)
        if ee_geom:
            return ee_geom.getInfo()
    except Exception as e:
        logger.warning(f"Could not get territory GeoJSON: {e}")
    return None


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def create_export_zip(
    analysis_results: Dict[str, Any],
    comparison_result: Optional[Dict[str, Any]] = None,
    territory_name: str = "",
    territory_year: int = 0,
    territory_year2: Optional[int] = None,
    territory_source: str = "MapBiomas",
    drawn_features: Optional[List[Dict]] = None,
    plotly_figures: Optional[Dict[str, Any]] = None,
    transitions: Optional[Dict] = None,
    territory_result: Optional[List[Dict]] = None,
    territory_result_year2: Optional[List[Dict]] = None,
) -> bytes:
    """
    Create a ZIP file containing all analysis data, figures, and metadata.

    Args:
        analysis_results: Current analysis results dict from AppState
        comparison_result: Year comparison data (if available)
        territory_name: Name of analyzed territory
        territory_year: Primary analysis year
        territory_year2: Comparison year (if any)
        territory_source: Data source (MapBiomas, Hansen)
        drawn_features: List of drawn geometry features
        plotly_figures: Dict of {name: plotly_figure_json} for export
        transitions: Transition matrix data (for Sankey)
        territory_result: Territory analysis data for year 1
        territory_result_year2: Territory analysis data for year 2

    Returns:
        bytes: ZIP file content
    """
    buf = io.BytesIO()

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        timestamp = datetime.now().isoformat()

        # === 1. Metadata ===
        metadata = {
            "app": "Yvynation - Indigenous Land Monitoring",
            "export_timestamp": timestamp,
            "territory": territory_name or "N/A",
            "year": territory_year,
            "year2": territory_year2,
            "source": territory_source,
            "analysis_type": analysis_results.get("type", "N/A"),
            "has_comparison": comparison_result is not None,
            "num_polygons": len(drawn_features) if drawn_features else 0,
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2, default=str))

        # === 2. Geometries GeoJSON ===
        if drawn_features:
            geojson = _geojson_from_features(drawn_features)
            zf.writestr("geometries.geojson", json.dumps(geojson, indent=2, default=str))

        # Try to add territory boundary
        if territory_name:
            terr_geojson = _territory_geojson(territory_name)
            if terr_geojson:
                zf.writestr(
                    f"territory/{territory_name}/boundary.geojson",
                    json.dumps(terr_geojson, indent=2, default=str),
                )

        # === 3. Analysis results CSV ===
        a_data = analysis_results.get("data", [])
        if a_data:
            df = pd.DataFrame(a_data)
            a_type = analysis_results.get("type", "analysis")
            year = analysis_results.get("year", "")

            if territory_name:
                path = f"territory/{territory_name}/{a_type}_{year}_data.csv"
            else:
                path = f"analysis/{a_type}_{year}_data.csv"
            zf.writestr(path, _df_to_csv_bytes(df))

        # === 4. Territory year 1 & year 2 results ===
        if territory_result and territory_name:
            df1 = pd.DataFrame(territory_result)
            zf.writestr(
                f"territory/{territory_name}/{territory_source}_{territory_year}_data.csv",
                _df_to_csv_bytes(df1),
            )

        if territory_result_year2 and territory_name and territory_year2:
            df2 = pd.DataFrame(territory_result_year2)
            zf.writestr(
                f"territory/{territory_name}/{territory_source}_{territory_year2}_data.csv",
                _df_to_csv_bytes(df2),
            )

        # === 5. Comparison data ===
        if comparison_result:
            comp_data = comparison_result.get("data", [])
            if comp_data:
                df_comp = pd.DataFrame(comp_data)
                y1 = comparison_result.get("year_start", "")
                y2 = comparison_result.get("year_end", "")

                if territory_name:
                    path = f"territory/{territory_name}/comparison_{y1}_vs_{y2}.csv"
                else:
                    path = f"analysis/comparison_{y1}_vs_{y2}.csv"
                zf.writestr(path, _df_to_csv_bytes(df_comp))

        # === 6. Transitions JSON ===
        if transitions:
            if territory_name:
                path = f"territory/{territory_name}/transitions.json"
            else:
                path = "analysis/transitions.json"
            zf.writestr(path, json.dumps(transitions, indent=2, default=str))

        # === 7. Plotly figures (HTML + PNG) ===
        if plotly_figures:
            import plotly.graph_objects as go
            for name, fig_data in plotly_figures.items():
                try:
                    if isinstance(fig_data, dict):
                        fig = go.Figure(fig_data)
                    else:
                        fig = fig_data

                    # HTML (always works)
                    html_bytes = _plotly_to_html_bytes(fig)
                    if html_bytes:
                        zf.writestr(f"figures/{name}.html", html_bytes)

                    # PNG (may require kaleido)
                    png_bytes = _plotly_to_png_bytes(fig)
                    if png_bytes:
                        zf.writestr(f"figures/{name}.png", png_bytes)
                except Exception as e:
                    logger.warning(f"Failed to export figure '{name}': {e}")

        # === 8. Summary text ===
        summary_lines = [
            f"Yvynation Analysis Export",
            f"========================",
            f"Generated: {timestamp}",
            f"Territory: {territory_name or 'N/A'}",
            f"Source: {territory_source}",
            f"Year: {territory_year}",
        ]
        if territory_year2:
            summary_lines.append(f"Comparison Year: {territory_year2}")
        if comparison_result:
            summary_lines.append(f"Comparison: {comparison_result.get('year_start')} vs {comparison_result.get('year_end')}")

        summary = analysis_results.get("summary", {})
        if summary:
            summary_lines.append(f"\nAnalysis Summary:")
            for k, v in summary.items():
                summary_lines.append(f"  {k}: {v}")

        zf.writestr("README.txt", "\n".join(summary_lines))

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Convenience: collect export data from AppState fields
# ---------------------------------------------------------------------------

def collect_export_data_from_state(state) -> Dict[str, Any]:
    """
    Collect all exportable data from an AppState instance.

    Returns dict with keys matching create_export_zip() parameters.
    """
    # Collect Plotly figure JSONs from computed properties
    plotly_figs = {}
    try:
        if state.analysis_results.get("type") == "mapbiomas":
            if state.mapbiomas_bar_chart:
                plotly_figs["mapbiomas_distribution"] = state.mapbiomas_bar_chart
            if state.mapbiomas_pie_chart:
                plotly_figs["mapbiomas_composition"] = state.mapbiomas_pie_chart
        elif state.analysis_results.get("type") == "hansen":
            if state.hansen_balance_chart:
                plotly_figs["hansen_balance"] = state.hansen_balance_chart

        if state.comparison_available:
            if state.gains_losses_chart:
                plotly_figs["gains_losses"] = state.gains_losses_chart
            if state.change_pct_chart:
                plotly_figs["change_percentage"] = state.change_pct_chart
    except Exception as e:
        logger.warning(f"Error collecting plotly figures: {e}")

    return {
        "analysis_results": state.analysis_results,
        "comparison_result": state.mapbiomas_comparison_result,
        "territory_name": state.territory_name or state.selected_territory or "",
        "territory_year": state.territory_year or state.mapbiomas_current_year,
        "territory_year2": state.territory_year2,
        "territory_source": state.territory_source,
        "drawn_features": state.drawn_features,
        "plotly_figures": plotly_figs if plotly_figs else None,
        "transitions": state.territory_transitions,
        "territory_result": state.territory_result,
        "territory_result_year2": state.territory_result_year2,
    }
