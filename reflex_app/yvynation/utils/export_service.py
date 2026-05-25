"""
Yvynation – Export service.

Generates a ZIP archive with a predictable, self-describing folder/file
structure so that exports from multiple territories can be merged into a
single directory without name collisions:

  yvynation_{territory_slug}_{YYYYMMDD_HHMM}.zip
  │
  ├── README.md               ← human-readable summary
  ├── metadata.json           ← machine-readable metadata
  │
  ├── territory/
  │   └── {slug}/
  │       ├── boundary.geojson
  │       ├── mapbiomas/
  │       │   ├── {slug}_mapbiomas_{year}_landcover.csv
  │       │   ├── {slug}_mapbiomas_{y1}_vs_{y2}_comparison.csv
  │       │   ├── {slug}_mapbiomas_{y1}_vs_{y2}_transitions.json
  │       │   └── figures/
  │       │       ├── {slug}_mapbiomas_{year}_distribution.png + .html
  │       │       ├── {slug}_mapbiomas_{year}_composition_pie.png + .html
  │       │       ├── {slug}_mapbiomas_{y1}_vs_{y2}_comparison_bars.png + .html
  │       │       ├── {slug}_mapbiomas_{y1}_vs_{y2}_gains_losses.png + .html
  │       │       ├── {slug}_mapbiomas_{y1}_vs_{y2}_change_pct.png + .html
  │       │       ├── {slug}_mapbiomas_{y1}_vs_{y2}_sankey.png + .html
  │       │       ├── {slug}_mapbiomas_{y1}_vs_{y2}_sunburst.png + .html
  │       │       └── {slug}_mapbiomas_{y1}_vs_{y2}_transition_matrix.png + .html
  │       ├── hansen_glad/
  │       │   ├── {slug}_hansen_glad_{year}_distribution.csv
  │       │   └── figures/
  │       │       └── {slug}_hansen_glad_{year}_distribution.png + .html
  │       └── hansen_gfc/
  │           ├── {slug}_hansen_gfc_summary.csv
  │           ├── {slug}_hansen_gfc_loss_by_year.csv
  │           ├── {slug}_hansen_gfc_gain.csv
  │           └── figures/
  │               ├── {slug}_hansen_gfc_summary.png + .html
  │               └── {slug}_hansen_gfc_loss_by_year.png + .html
  │
  └── buffer/
      └── {buffer_slug}/      (e.g. {territory_slug}_Buffer_10km)
          └── [same sub-structure as territory/]
"""

import io
import json
import re
import zipfile
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slug(name: str) -> str:
    """Turn an arbitrary territory / buffer name into a safe filesystem slug.

    Examples:
        "Terra Indígena Xingu (PA)"  → "Terra_Indigena_Xingu_PA"
        "Xingu - Buffer 10km"        → "Xingu_Buffer_10km"
    """
    import unicodedata
    # Normalize unicode (remove accents)
    norm = unicodedata.normalize("NFD", str(name))
    ascii_name = norm.encode("ascii", "ignore").decode("ascii")
    # Replace common separators / brackets with underscores
    ascii_name = re.sub(r"[\s\(\)\[\]{}/\\:;,\-–—]+", "_", ascii_name)
    # Strip leading/trailing underscores, collapse multiples
    ascii_name = re.sub(r"_+", "_", ascii_name).strip("_")
    return ascii_name or "unknown"


def _df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _plotly_to_html_bytes(fig) -> Optional[bytes]:
    try:
        return fig.to_html(include_plotlyjs="cdn", full_html=True).encode("utf-8")
    except Exception as e:
        logger.warning(f"Plotly → HTML failed: {e}")
        return None


def _plotly_to_png_bytes(fig, width: int = 1400, height: int = 700) -> Optional[bytes]:
    """Convert Plotly figure to PNG bytes (requires kaleido)."""
    try:
        return fig.to_image(format="png", width=width, height=height)
    except Exception as e:
        logger.warning(f"Plotly → PNG failed (install kaleido): {e}")
        return None


def _write_fig(zf: zipfile.ZipFile, base_path: str, fig) -> None:
    """Write both .html and (if kaleido available) .png versions of a figure."""
    if fig is None:
        return
    try:
        import plotly.graph_objects as go
        if isinstance(fig, dict):
            fig = go.Figure(fig)
        # Always try HTML first (no extra deps)
        html = _plotly_to_html_bytes(fig)
        if html:
            zf.writestr(base_path + ".html", html)
        # PNG is optional
        png = _plotly_to_png_bytes(fig)
        if png:
            zf.writestr(base_path + ".png", png)
    except Exception as e:
        logger.warning(f"Could not write figure '{base_path}': {e}")


def _geojson_from_features(features: List[Dict]) -> Dict:
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


# ---------------------------------------------------------------------------
# Section writers  (territory or buffer, same logic)
# ---------------------------------------------------------------------------

def _write_mapbiomas_section(
    zf: zipfile.ZipFile,
    base_dir: str,
    slug: str,
    *,
    single_year_result: Optional[Dict] = None,
    comparison_result: Optional[Dict] = None,
    territory_result_y1: Optional[List[Dict]] = None,
    territory_result_y2: Optional[List[Dict]] = None,
    transitions: Optional[Dict] = None,
    bar_chart=None,
    pie_chart=None,
    comparison_bar_chart=None,
    gains_losses_chart=None,
    change_pct_chart=None,
    sankey_chart=None,
    sunburst_chart=None,
    transition_matrix_chart=None,
    name_suffix: str = "",
) -> None:
    """Write MapBiomas CSVs + figures into base_dir/mapbiomas/.

    ``name_suffix`` is appended to every base filename right before the
    extension — used to tag buffer outputs (e.g. ``_Buffer_10km``).
    """
    mb_dir = f"{base_dir}/mapbiomas"
    sfx = name_suffix

    # --- Single-year land-cover CSV ---
    if single_year_result:
        data = single_year_result.get("data", [])
        year = single_year_result.get("year", "")
        if data:
            df = pd.DataFrame(data)
            zf.writestr(
                f"{mb_dir}/{slug}_mapbiomas_{year}_landcover{sfx}.csv",
                _df_to_csv_bytes(df),
            )

    # --- Raw year1 / year2 data rows (from territory_result / territory_result_year2) ---
    if territory_result_y1 and comparison_result:
        y1 = comparison_result.get("year_start", "")
        df = pd.DataFrame(territory_result_y1)
        zf.writestr(
            f"{mb_dir}/{slug}_mapbiomas_{y1}_raw_classes{sfx}.csv",
            _df_to_csv_bytes(df),
        )
    if territory_result_y2 and comparison_result:
        y2 = comparison_result.get("year_end", "")
        df = pd.DataFrame(territory_result_y2)
        zf.writestr(
            f"{mb_dir}/{slug}_mapbiomas_{y2}_raw_classes{sfx}.csv",
            _df_to_csv_bytes(df),
        )

    # --- Comparison gains/losses CSV ---
    if comparison_result:
        data = comparison_result.get("data", [])
        y1 = comparison_result.get("year_start", "")
        y2 = comparison_result.get("year_end", "")
        if data:
            df = pd.DataFrame(data)
            zf.writestr(
                f"{mb_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_comparison{sfx}.csv",
                _df_to_csv_bytes(df),
            )

    # --- Transitions JSON ---
    if transitions:
        y1 = (comparison_result or {}).get("year_start", "")
        y2 = (comparison_result or {}).get("year_end", "")
        label = f"_{y1}_vs_{y2}" if y1 and y2 else ""
        zf.writestr(
            f"{mb_dir}/{slug}_mapbiomas{label}_transitions{sfx}.json",
            json.dumps(transitions, indent=2, default=str),
        )

    # --- Figures ---
    fig_dir = f"{mb_dir}/figures"
    year = (single_year_result or {}).get("year", "")
    y1 = (comparison_result or {}).get("year_start", "")
    y2 = (comparison_result or {}).get("year_end", "")

    if bar_chart is not None and year:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{year}_distribution{sfx}", bar_chart)
    if pie_chart is not None and year:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{year}_composition_pie{sfx}", pie_chart)
    if comparison_bar_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_comparison_bars{sfx}", comparison_bar_chart)
    if gains_losses_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_gains_losses{sfx}", gains_losses_chart)
    if change_pct_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_change_pct{sfx}", change_pct_chart)
    if sankey_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_sankey{sfx}", sankey_chart)
    if sunburst_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_sunburst{sfx}", sunburst_chart)
    if transition_matrix_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_transition_matrix{sfx}", transition_matrix_chart)


def _write_hansen_glad_section(
    zf: zipfile.ZipFile,
    base_dir: str,
    slug: str,
    *,
    glad_result: Optional[Dict] = None,
    bar_chart=None,
    name_suffix: str = "",
) -> None:
    """Write Hansen GLAD CSV + figure into base_dir/hansen_glad/."""
    if not glad_result:
        return
    gl_dir = f"{base_dir}/hansen_glad"
    sfx = name_suffix
    data = glad_result.get("data", [])
    year = glad_result.get("summary", {}).get("year", "")
    if data:
        df = pd.DataFrame(data)
        zf.writestr(
            f"{gl_dir}/{slug}_hansen_glad_{year}_distribution{sfx}.csv",
            _df_to_csv_bytes(df),
        )
    if bar_chart is not None and year:
        _write_fig(
            zf,
            f"{gl_dir}/figures/{slug}_hansen_glad_{year}_distribution{sfx}",
            bar_chart,
        )


def _write_hansen_gfc_section(
    zf: zipfile.ZipFile,
    base_dir: str,
    slug: str,
    *,
    gfc_result: Optional[Dict] = None,
    bar_chart=None,
    loss_chart=None,
    name_suffix: str = "",
) -> None:
    """Write Hansen GFC CSVs + figures into base_dir/hansen_gfc/."""
    if not gfc_result:
        return
    gfc_dir = f"{base_dir}/hansen_gfc"
    sfx = name_suffix

    # Summary metrics
    data = gfc_result.get("data", [])
    if data:
        df = pd.DataFrame(data)
        zf.writestr(
            f"{gfc_dir}/{slug}_hansen_gfc_summary{sfx}.csv",
            _df_to_csv_bytes(df),
        )

    # Loss by year (Year_Code > 0)
    loss_data = [r for r in gfc_result.get("tree_loss_data", []) if r.get("Year_Code", 0) > 0]
    if loss_data:
        df_loss = pd.DataFrame(loss_data)
        zf.writestr(
            f"{gfc_dir}/{slug}_hansen_gfc_loss_by_year{sfx}.csv",
            _df_to_csv_bytes(df_loss),
        )

    # Gain summary
    gain_data = gfc_result.get("tree_gain_data", [])
    if gain_data:
        df_gain = pd.DataFrame(gain_data)
        zf.writestr(
            f"{gfc_dir}/{slug}_hansen_gfc_gain{sfx}.csv",
            _df_to_csv_bytes(df_gain),
        )

    # Tree cover categories
    cover_data = gfc_result.get("tree_cover_data", [])
    if cover_data:
        df_cover = pd.DataFrame(cover_data)
        zf.writestr(
            f"{gfc_dir}/{slug}_hansen_gfc_tree_cover_2000{sfx}.csv",
            _df_to_csv_bytes(df_cover),
        )

    fig_dir = f"{gfc_dir}/figures"
    if bar_chart is not None:
        _write_fig(zf, f"{fig_dir}/{slug}_hansen_gfc_summary{sfx}", bar_chart)
    if loss_chart is not None and loss_data:
        _write_fig(zf, f"{fig_dir}/{slug}_hansen_gfc_loss_by_year{sfx}", loss_chart)


# ---------------------------------------------------------------------------
# Main export function
# ---------------------------------------------------------------------------

def create_export_zip(
    # Territory identity
    territory_name: str = "",
    territory_year: int = 0,
    territory_year2: Optional[int] = None,
    territory_source: str = "MapBiomas",
    # Territory analysis data
    analysis_results: Optional[Dict[str, Any]] = None,
    mapbiomas_analysis_result: Optional[Dict[str, Any]] = None,
    comparison_result: Optional[Dict[str, Any]] = None,
    territory_result: Optional[List[Dict]] = None,
    territory_result_year2: Optional[List[Dict]] = None,
    territory_transitions: Optional[Dict] = None,
    glad_result: Optional[Dict[str, Any]] = None,
    gfc_result: Optional[Dict[str, Any]] = None,
    territory_geojson_cached: Optional[Dict] = None,
    drawn_features: Optional[List[Dict]] = None,
    # Territory figures
    territory_figures: Optional[Dict[str, Any]] = None,
    # Buffer identity + data
    buffer_name: str = "",
    buffer_mapbiomas_result: Optional[Dict[str, Any]] = None,
    buffer_comparison_result: Optional[Dict[str, Any]] = None,   # year2 single-year
    buffer_mapbiomas_comparison_result: Optional[Dict[str, Any]] = None,
    buffer_territory_transitions: Optional[Dict] = None,
    buffer_hansen_result: Optional[Dict[str, Any]] = None,
    buffer_gfc_result: Optional[Dict[str, Any]] = None,
    # Buffer figures
    buffer_figures: Optional[Dict[str, Any]] = None,
    # Legacy parameter (ignored, kept for backwards compat)
    plotly_figures: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Build and return a well-structured ZIP archive for download."""
    buf = io.BytesIO()
    analysis_results = analysis_results or {}
    territory_figures = territory_figures or {}
    buffer_figures = buffer_figures or {}

    t_slug = _slug(territory_name) if territory_name else "territory"
    b_slug = _slug(buffer_name) if buffer_name else (f"{t_slug}_buffer" if t_slug else "buffer")
    timestamp = datetime.now().isoformat()

    y1 = (comparison_result or {}).get("year_start", territory_year or "")
    y2 = (comparison_result or {}).get("year_end", territory_year2 or "")

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        # ── metadata.json ────────────────────────────────────────────────────
        metadata = {
            "app": "Yvynation – Indigenous Land Monitoring",
            "export_timestamp": timestamp,
            "territory": territory_name or "N/A",
            "territory_slug": t_slug,
            "year_primary": territory_year,
            "year_comparison": territory_year2,
            "source": territory_source,
            "has_comparison": comparison_result is not None,
            "has_buffer": bool(buffer_name),
            "buffer_name": buffer_name or None,
            "buffer_slug": b_slug if buffer_name else None,
            "num_drawn_polygons": len(drawn_features) if drawn_features else 0,
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2, default=str))

        # ── README.md ────────────────────────────────────────────────────────
        readme_lines = [
            "# Yvynation Analysis Export",
            "",
            f"**Generated:** {timestamp}",
            f"**Territory:** {territory_name or 'N/A'}",
            f"**Source:** {territory_source}",
        ]
        if territory_year:
            readme_lines.append(f"**Primary year:** {territory_year}")
        if territory_year2:
            readme_lines.append(f"**Comparison year:** {territory_year2}")
        if buffer_name:
            readme_lines.append(f"**Buffer zone:** {buffer_name}")
        readme_lines += [
            "",
            "## Folder structure",
            "",
            "```",
            "territory/{slug}/",
            "  mapbiomas/          ← land-cover CSVs + figures",
            "  hansen_glad/        ← forest-cover snapshot CSVs + figures",
            "  hansen_gfc/         ← annual loss/gain CSVs + figures",
            "  boundary.geojson    ← territory polygon",
            "buffer/{slug}/        ← same sub-structure for the buffer ring",
            "geometries.geojson    ← any manually drawn features",
            "```",
            "",
            "## File naming convention",
            "",
            "Every file is prefixed with the territory slug so that exports",
            "from multiple territories can be merged into one flat folder",
            "without name collisions. Buffer outputs append a `_Buffer_{km}km`",
            "suffix at the end (just before the extension) so they sort",
            "directly after the matching territory file.",
            "",
            "Pattern: `{territory_slug}_{dataset}_{year(s)}_{chart_type}[_Buffer_{km}km].ext`",
            "",
            "Examples:",
            f"  `{t_slug}_mapbiomas_{territory_year}_landcover.csv`",
            f"  `{t_slug}_mapbiomas_{y1}_vs_{y2}_gains_losses.png`",
            f"  `{t_slug}_hansen_gfc_loss_by_year_Buffer_10km.csv`",
        ]
        zf.writestr("README.md", "\n".join(readme_lines))

        # ── Drawn features ───────────────────────────────────────────────────
        if drawn_features:
            fc = _geojson_from_features(drawn_features)
            zf.writestr("geometries.geojson", json.dumps(fc, indent=2, default=str))

        # ── Territory boundary ───────────────────────────────────────────────
        terr_base = f"territory/{t_slug}"
        if territory_geojson_cached:
            zf.writestr(
                f"{terr_base}/boundary.geojson",
                json.dumps(territory_geojson_cached, indent=2, default=str),
            )

        # ── Territory MapBiomas ──────────────────────────────────────────────
        _write_mapbiomas_section(
            zf, terr_base, t_slug,
            single_year_result=mapbiomas_analysis_result or (
                analysis_results if analysis_results.get("type") == "mapbiomas" else None
            ),
            comparison_result=comparison_result,
            territory_result_y1=territory_result,
            territory_result_y2=territory_result_year2,
            transitions=territory_transitions,
            bar_chart=territory_figures.get("mapbiomas_bar"),
            pie_chart=territory_figures.get("mapbiomas_pie"),
            comparison_bar_chart=territory_figures.get("comparison_bar"),
            gains_losses_chart=territory_figures.get("gains_losses"),
            change_pct_chart=territory_figures.get("change_pct"),
            sankey_chart=territory_figures.get("sankey"),
            sunburst_chart=territory_figures.get("sunburst"),
            transition_matrix_chart=territory_figures.get("transition_matrix"),
        )

        # ── Territory Hansen GLAD ────────────────────────────────────────────
        _write_hansen_glad_section(
            zf, terr_base, t_slug,
            glad_result=glad_result,
            bar_chart=territory_figures.get("hansen_glad_bar"),
        )

        # ── Territory Hansen GFC ─────────────────────────────────────────────
        _write_hansen_gfc_section(
            zf, terr_base, t_slug,
            gfc_result=gfc_result,
            bar_chart=territory_figures.get("gfc_bar"),
            loss_chart=territory_figures.get("gfc_loss"),
        )

        # ── Buffer sections (only when buffer data exists) ───────────────────
        if any([
            buffer_mapbiomas_result,
            buffer_mapbiomas_comparison_result,
            buffer_hansen_result,
            buffer_gfc_result,
        ]):
            buf_base = f"buffer/{b_slug}"

            # File-name slug stays as the territory slug; the buffer marker
            # (e.g. "_Buffer_10km") is appended *after* the dataset/year so
            # files like {terr}_hansen_gfc_summary_Buffer_10km.png group with
            # their territory counterparts when listed alphabetically.
            if b_slug.startswith(t_slug):
                buf_suffix = b_slug[len(t_slug):]
                if buf_suffix and not buf_suffix.startswith("_"):
                    buf_suffix = "_" + buf_suffix
            else:
                buf_suffix = "_" + b_slug

            # Buffer MapBiomas — single year comes from buffer_mapbiomas_result (year1)
            # or buffer_comparison_result (year2); comparison from buffer_mapbiomas_comparison_result
            _write_mapbiomas_section(
                zf, buf_base, t_slug,
                single_year_result=buffer_mapbiomas_result,
                comparison_result=buffer_mapbiomas_comparison_result,
                transitions=buffer_territory_transitions,
                bar_chart=buffer_figures.get("mapbiomas_bar"),
                comparison_bar_chart=buffer_figures.get("comparison_bar"),
                gains_losses_chart=buffer_figures.get("gains_losses"),
                change_pct_chart=buffer_figures.get("change_pct"),
                sankey_chart=buffer_figures.get("sankey"),
                sunburst_chart=buffer_figures.get("sunburst"),
                transition_matrix_chart=buffer_figures.get("transition_matrix"),
                name_suffix=buf_suffix,
            )

            # Buffer Hansen GLAD
            _write_hansen_glad_section(
                zf, buf_base, t_slug,
                glad_result=buffer_hansen_result,
                bar_chart=buffer_figures.get("hansen_glad_bar"),
                name_suffix=buf_suffix,
            )

            # Buffer Hansen GFC
            _write_hansen_gfc_section(
                zf, buf_base, t_slug,
                gfc_result=buffer_gfc_result,
                bar_chart=buffer_figures.get("gfc_bar"),
                loss_chart=buffer_figures.get("gfc_loss"),
                name_suffix=buf_suffix,
            )

    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Convenience: collect export data from AppState
# ---------------------------------------------------------------------------

def collect_export_data_from_state(state) -> Dict[str, Any]:
    """Collect all exportable data from an AppState instance."""

    # ── Territory figures ────────────────────────────────────────────────────
    terr_figs: Dict[str, Any] = {}
    try:
        if state.mapbiomas_bar_chart:
            terr_figs["mapbiomas_bar"] = state.mapbiomas_bar_chart
        if state.mapbiomas_pie_chart:
            terr_figs["mapbiomas_pie"] = state.mapbiomas_pie_chart
        if state.comparison_chart:
            terr_figs["comparison_bar"] = state.comparison_chart
        if state.gains_losses_chart:
            terr_figs["gains_losses"] = state.gains_losses_chart
        if state.change_pct_chart:
            terr_figs["change_pct"] = state.change_pct_chart
        if state.sankey_chart:
            terr_figs["sankey"] = state.sankey_chart
        if state.sunburst_transitions_chart:
            terr_figs["sunburst"] = state.sunburst_transitions_chart
        if state.transition_matrix_chart:
            terr_figs["transition_matrix"] = state.transition_matrix_chart
        if state.glad_bar_chart:
            terr_figs["hansen_glad_bar"] = state.glad_bar_chart
        elif state.hansen_balance_chart:
            terr_figs["hansen_glad_bar"] = state.hansen_balance_chart
        if state.gfc_bar_chart:
            terr_figs["gfc_bar"] = state.gfc_bar_chart
        if state.gfc_loss_chart:
            terr_figs["gfc_loss"] = state.gfc_loss_chart
    except Exception as e:
        logger.warning(f"Error collecting territory figures: {e}")

    # ── Buffer figures ───────────────────────────────────────────────────────
    buf_figs: Dict[str, Any] = {}
    try:
        if state.buffer_mapbiomas_bar_chart:
            buf_figs["mapbiomas_bar"] = state.buffer_mapbiomas_bar_chart
        if state.buffer_comparison_chart:
            buf_figs["comparison_bar"] = state.buffer_comparison_chart
        if state.buffer_compare_gains_losses_chart:
            buf_figs["gains_losses"] = state.buffer_compare_gains_losses_chart
        if state.buffer_compare_change_pct_chart:
            buf_figs["change_pct"] = state.buffer_compare_change_pct_chart
        if state.buffer_sankey_chart:
            buf_figs["sankey"] = state.buffer_sankey_chart
        if state.buffer_sunburst_chart:
            buf_figs["sunburst"] = state.buffer_sunburst_chart
        if state.buffer_transition_matrix_chart:
            buf_figs["transition_matrix"] = state.buffer_transition_matrix_chart
        if state.buffer_hansen_bar_chart:
            buf_figs["hansen_glad_bar"] = state.buffer_hansen_bar_chart
        if state.buffer_gfc_bar_chart:
            buf_figs["gfc_bar"] = state.buffer_gfc_bar_chart
        if state.buffer_gfc_loss_chart:
            buf_figs["gfc_loss"] = state.buffer_gfc_loss_chart
    except Exception as e:
        logger.warning(f"Error collecting buffer figures: {e}")

    # ── Territory result data ────────────────────────────────────────────────
    t_result = state.territory_result
    t_result_y2 = state.territory_result_year2
    t_data = t_result.get("data", []) if isinstance(t_result, dict) else (t_result or [])
    t_data_y2 = t_result_y2.get("data", []) if isinstance(t_result_y2, dict) else (t_result_y2 or [])

    # ── Cached territory GeoJSON ─────────────────────────────────────────────
    cached_geojson = None
    try:
        feats = state.territory_geojson_features
        if feats:
            cached_geojson = feats[0].get("geometry")
    except Exception:
        pass

    # ── Buffer name ─────────────────────────────────────────────────────────
    buffer_name = ""
    try:
        buffer_name = state.current_buffer_for_analysis or ""
        if not buffer_name and state.buffer_mapbiomas_result:
            buffer_name = state.buffer_mapbiomas_result.get("territory", "")
        if not buffer_name and state.buffer_mapbiomas_comparison_result:
            buffer_name = state.buffer_mapbiomas_comparison_result.get("territory", "")
        if not buffer_name and any([
            state.buffer_mapbiomas_result,
            state.buffer_gfc_result,
            state.buffer_hansen_result,
        ]):
            t = state.territory_name or state.selected_territory or ""
            buffer_name = f"{t} - Buffer {state.auto_buffer_km:g}km" if t else "Buffer"
    except Exception:
        pass

    return {
        "territory_name": state.territory_name or state.selected_territory or "",
        "territory_year": state.territory_year or state.mapbiomas_current_year,
        "territory_year2": state.territory_year2,
        "territory_source": state.territory_source,
        "analysis_results": state.analysis_results,
        "mapbiomas_analysis_result": state.mapbiomas_analysis_result,
        "comparison_result": state.mapbiomas_comparison_result,
        "territory_result": t_data or None,
        "territory_result_year2": t_data_y2 or None,
        "territory_transitions": state.territory_transitions,
        "glad_result": state.geometry_glad_result or None,
        "gfc_result": state.geometry_gfc_result or None,
        "territory_geojson_cached": cached_geojson,
        "drawn_features": state.drawn_features,
        "territory_figures": terr_figs or None,
        # Buffer
        "buffer_name": buffer_name,
        "buffer_mapbiomas_result": state.buffer_mapbiomas_result,
        "buffer_comparison_result": state.buffer_compare_result,
        "buffer_mapbiomas_comparison_result": state.buffer_mapbiomas_comparison_result,
        "buffer_territory_transitions": state.buffer_territory_transitions,
        "buffer_hansen_result": state.buffer_hansen_result,
        "buffer_gfc_result": state.buffer_gfc_result,
        "buffer_figures": buf_figs or None,
    }
