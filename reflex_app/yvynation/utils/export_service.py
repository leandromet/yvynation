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
  │       ├── hansen_gfc/
  │       │   ├── {slug}_hansen_gfc_summary.csv
  │       │   ├── {slug}_hansen_gfc_loss_by_year.csv
  │       │   ├── {slug}_hansen_gfc_gain.csv
  │       │   └── figures/
  │       │       ├── {slug}_hansen_gfc_summary.png + .html
  │       │       └── {slug}_hansen_gfc_loss_by_year.png + .html
  │       └── mapbiomas_multi_window/     (when the multi-window analysis ran)
  │           ├── {slug}_mapbiomas_multi_window_{years}_transitions.csv
  │           └── figures/
  │               ├── {slug}_mapbiomas_multi_window_{years}_sankey.png + .html
  │               └── {slug}_mapbiomas_{y1}_vs_{y2}_sunburst.png + .html  (per pair)
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
# Export delivery via the upload dir (HTTP download instead of data-URI)
# ---------------------------------------------------------------------------
#
# ``rx.download(data=...)`` ships the whole archive as a base64 data-URI over
# the websocket — unreliable beyond a few tens of MB and ~3× the RAM.  Large
# exports are therefore written under ``uploaded_files/exports/``:
#
#     rel = save_export_to_upload_dir(zip_bytes, filename)
#     return rx.download(url=get_download_url(rel), filename=filename)
#
# Use get_download_url(), not rx.get_upload_url(), for anything that might
# exceed ~32 MiB. Locally/small files it's the same /_upload static mount;
# on Cloud Run (GCS_EXPORT_BUCKET set) exports/ is a GCS FUSE volume and
# Cloud Run's proxy caps fixed-Content-Length responses at ~32 MiB, so
# get_download_url() hands back a signed GCS URL instead — the browser
# downloads straight from GCS, bypassing that cap entirely.
#
# For very large archives, build the ZIP directly on disk instead of BytesIO:
#
#     path = get_export_dir() / filename
#     with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf: ...
#     prune_old_exports()

#: Trailing "_YYYYMMDD_HHMM…zip" — stripped to group exports by kind
_EXPORT_TS_RE = re.compile(r"_\d{8}_\d{4}.*\.zip$")


class DirExportWriter:
    """``zipfile.ZipFile``-compatible ``writestr()`` that writes straight to a
    folder instead of an archive.

    Used by the batch pipeline so every CSV/PNG/HTML becomes visible on disk
    (and downloadable via the ``/_upload`` mount) the moment it is produced,
    instead of being locked inside a growing, unreadable ZIP. No compression
    happens during the run — the folder is deflated once at the end with
    :func:`zip_directory`.
    """

    def __init__(self, root):
        from pathlib import Path

        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def writestr(self, arcname: str, data) -> None:
        path = self.root / arcname
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        path.write_bytes(data)

    # Context-manager protocol so it can replace ``with zipfile.ZipFile(...)``
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def zip_directory(src_dir, zip_path) -> int:
    """Deflate *src_dir* recursively into *zip_path*; returns the ZIP size."""
    from pathlib import Path

    src_dir = Path(src_dir)
    zip_path = Path(zip_path)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(src_dir).as_posix())
    return zip_path.stat().st_size


def get_export_dir():
    """Return (and create) ``uploaded_files/exports/`` as a ``Path``."""
    import reflex as rx

    export_dir = rx.get_upload_dir() / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def prune_old_exports(keep_per_prefix: int = 2) -> None:
    """Delete older export ZIPs and leftover run folders.

    ZIPs: keeps the newest *keep_per_prefix* of each kind (kind = name with
    the trailing ``_YYYYMMDD_HHMM`` stripped), so interactive exports never
    evict a freshly built batch archive.

    Folders: deleted ONLY when their completed marker — a same-name ``.zip``
    — exists (the batch normally removes its own folder after compressing;
    this just sweeps leftovers). A folder without a matching ZIP is NEVER
    touched: it is either a run still in progress (deleting it mid-run would
    silently empty that run's final archive — mtime is no indicator, a run
    folder's root mtime never updates while files land in subfolders) or a
    crashed run kept for manual salvage.
    """
    import shutil

    try:
        export_dir = get_export_dir()
        zip_groups: Dict[str, list] = {}
        completed_dirs: list = []
        for p in export_dir.iterdir():
            if p.is_file() and p.suffix == ".zip":
                zip_groups.setdefault(_EXPORT_TS_RE.sub("", p.name), []).append(p)
            elif p.is_dir() and (export_dir / f"{p.name}.zip").exists():
                completed_dirs.append(p)
        for d in completed_dirs:
            shutil.rmtree(d, ignore_errors=True)
        for files in zip_groups.values():
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            for old in files[keep_per_prefix:]:
                try:
                    old.unlink()
                except OSError:
                    pass
    except Exception as e:
        logger.warning(f"export prune failed: {e}")


def save_export_to_upload_dir(zip_bytes: bytes, filename: str) -> str:
    """Write *zip_bytes* to the export dir and return the upload-relative path
    (``exports/<filename>``) for ``rx.get_upload_url``."""
    path = get_export_dir() / filename
    path.write_bytes(zip_bytes)
    prune_old_exports()
    logger.info(f"Export saved: {path} ({len(zip_bytes) // 1024} KB)")
    return f"exports/{filename}"


def get_download_url(relpath: str) -> str:
    """URL for downloading an ``exports/``-relative path.

    Locally (no ``GCS_EXPORT_BUCKET`` env var) this is the app's own
    ``/_upload`` static mount. On Cloud Run, ``uploaded_files/exports/`` is
    a GCS FUSE volume, but Cloud Run's own proxy caps fixed-Content-Length
    responses at ~32 MiB — Starlette's static-file serving sets
    Content-Length, so any export past that size 500s when served through
    the app (see the batch-processing memory/persistence fix notes).
    Anything bucket-backed is therefore handed to the browser as a signed
    GCS URL instead, bypassing the app entirely for the actual transfer.

    Requires ``roles/iam.serviceAccountTokenCreator`` granted to the
    Cloud Run service account on itself (no private key on the instance,
    so signing goes through the IAM Credentials API's signBlob).
    """
    import os
    bucket_name = os.environ.get("GCS_EXPORT_BUCKET", "")
    if not bucket_name:
        import reflex as rx
        return rx.get_upload_url(relpath)

    blob_name = relpath[len("exports/"):] if relpath.startswith("exports/") else relpath

    import datetime
    import google.auth
    from google.auth.transport import requests as g_requests
    from google.cloud import storage

    credentials, project = google.auth.default()
    credentials.refresh(g_requests.Request())

    client = storage.Client(credentials=credentials, project=project)
    blob = client.bucket(bucket_name).blob(blob_name)
    return blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=6),
        method="GET",
        service_account_email=credentials.service_account_email,
        access_token=credentials.token,
    )


# ---------------------------------------------------------------------------
# Previous Runs — browse/recover what's sitting in the exports dir
#
# Backs the "Previous Runs" page. A folder without a matching ZIP is either
# a run still in progress or one that never finished (crashed / OOM-killed
# mid-batch) — see prune_old_exports(), which deliberately never touches
# such folders. list_export_runs() surfaces both kinds so a user coming back
# after a crash can still find and recover what was written before it died.
# ---------------------------------------------------------------------------

def _dir_size_and_count(path) -> Tuple[int, int]:
    size = 0
    count = 0
    for f in path.rglob("*"):
        if f.is_file():
            size += f.stat().st_size
            count += 1
    return size, count


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def list_export_runs() -> List[Dict[str, Any]]:
    """List every finished export ZIP and every leftover run folder.

    Returns dicts with: name, kind ("zip"|"partial"), relpath (upload-
    relative path, only for "zip"), size_label, file_count (only for
    "partial"), time_label — newest first.
    """
    export_dir = get_export_dir()
    zip_stems = set()
    runs: List[Dict[str, Any]] = []

    entries = list(export_dir.iterdir())
    for p in entries:
        if p.is_file() and p.suffix == ".zip":
            zip_stems.add(p.stem)
            st = p.stat()
            runs.append({
                "name": p.stem,
                "kind": "zip",
                "relpath": f"exports/{p.name}",
                "size_label": _format_size(st.st_size),
                "file_count": 0,
                "time_label": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "mtime": st.st_mtime,
            })
    for p in entries:
        if p.is_dir() and p.name not in zip_stems:
            size, count = _dir_size_and_count(p)
            runs.append({
                "name": p.name,
                "kind": "partial",
                "relpath": "",
                "size_label": _format_size(size),
                "file_count": count,
                "time_label": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "mtime": p.stat().st_mtime,
            })

    runs.sort(key=lambda r: r["mtime"], reverse=True)
    for r in runs:
        del r["mtime"]
    return runs


def zip_partial_run(run_name: str) -> Optional[str]:
    """Compress a still-present run folder (in-progress or crashed) into a
    downloadable ZIP. Returns the upload-relative path, or ``None`` if the
    folder is gone or empty."""
    export_dir = get_export_dir()
    work_dir = (export_dir / run_name).resolve()
    if export_dir.resolve() not in work_dir.parents or not work_dir.is_dir():
        return None

    zip_path = export_dir / f"{run_name}.zip"
    size = zip_directory(work_dir, zip_path)
    if size <= 0:
        zip_path.unlink(missing_ok=True)
        return None

    import shutil
    shutil.rmtree(work_dir, ignore_errors=True)
    logger.info(f"Salvaged partial run '{run_name}' → {zip_path.name} ({size // 1024} KB)")
    return f"exports/{zip_path.name}"


def delete_export_run(name: str, kind: str) -> bool:
    """Delete a finished ZIP (``kind="zip"``) or a leftover folder
    (``kind="partial"``) from the exports dir. Returns whether it existed."""
    export_dir = get_export_dir()
    target = (export_dir / (f"{name}.zip" if kind == "zip" else name)).resolve()
    if export_dir.resolve() not in target.parents:
        return False
    if kind == "zip" and target.is_file():
        target.unlink()
        return True
    if kind == "partial" and target.is_dir():
        import shutil
        shutil.rmtree(target, ignore_errors=True)
        return True
    return False


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


def _plotly_to_png_bytes(
    fig,
    width: Optional[int] = None,
    height: Optional[int] = None,
    scale: float = 1.0,
) -> Optional[bytes]:
    """Convert Plotly figure to PNG bytes (requires kaleido).

    When *width*/*height* are omitted, kaleido uses the figure's own layout
    dimensions (or its default 700×450 if none are set).  Pass ``scale`` > 1
    for high-DPI export (scale=2 → @2× / print quality).
    """
    try:
        kwargs: dict = {"format": "png", "scale": scale}
        if width is not None:
            kwargs["width"] = width
        if height is not None:
            kwargs["height"] = height
        return fig.to_image(**kwargs)
    except Exception as e:
        logger.warning(f"Plotly → PNG failed (install kaleido): {e}")
        return None


def _write_fig(
    zf: zipfile.ZipFile,
    base_path: str,
    fig,
    png_width: Optional[int] = None,
    png_height: Optional[int] = None,
    png_scale: float = 1.0,
) -> None:
    """Write both .html and (if kaleido available) .png versions of a figure.

    For ordinary charts the default 1:1 scale is fine.  Pass
    ``png_scale=2.0`` (and leave *png_width*/*png_height* unset) for the
    deforestation-timeline chart so kaleido uses the figure's own layout
    dimensions at @2× pixel density — print-ready quality.
    """
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
        png = _plotly_to_png_bytes(fig, width=png_width, height=png_height, scale=png_scale)
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
    single_year_result_extra: Optional[Dict] = None,
    comparison_result: Optional[Dict] = None,
    territory_result_y1: Optional[List[Dict]] = None,
    territory_result_y2: Optional[List[Dict]] = None,
    transitions: Optional[Dict] = None,
    bar_chart=None,
    pie_chart=None,
    bar_chart_extra=None,
    pie_chart_extra=None,
    comparison_bar_chart=None,
    gains_losses_chart=None,
    change_pct_chart=None,
    sankey_chart=None,
    sunburst_chart=None,
    treemap_chart=None,
    transition_matrix_chart=None,
    name_suffix: str = "",
) -> None:
    """Write MapBiomas CSVs + figures into base_dir/mapbiomas/.

    ``name_suffix`` is appended to every base filename right before the
    extension — used to tag buffer outputs (e.g. ``_Buffer_10km``).

    ``single_year_result_extra`` (plus matching ``bar_chart_extra`` /
    ``pie_chart_extra``) writes a second single-year landcover CSV +
    distribution/pie figures — so a comparison run produces parallel y1
    and y2 outputs for both territory and buffer.
    """
    mb_dir = f"{base_dir}/mapbiomas"
    sfx = name_suffix

    # --- Single-year land-cover CSVs (primary + optional extra) ---
    single_pairs = [
        (single_year_result, bar_chart, pie_chart),
        (single_year_result_extra, bar_chart_extra, pie_chart_extra),
    ]
    seen_single_years = set()
    for syr, _bc, _pc in single_pairs:
        if not syr:
            continue
        data = syr.get("data", [])
        year = syr.get("year", "")
        if data and year not in seen_single_years:
            df = pd.DataFrame(data)
            zf.writestr(
                f"{mb_dir}/{slug}_mapbiomas_{year}_landcover{sfx}.csv",
                _df_to_csv_bytes(df),
            )
            seen_single_years.add(year)

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
    y1 = (comparison_result or {}).get("year_start", "")
    y2 = (comparison_result or {}).get("year_end", "")

    # Single-year distribution + pie for each provided result (skip duplicates)
    seen_fig_years = set()
    for syr, bc, pc in single_pairs:
        if not syr:
            continue
        year = syr.get("year", "")
        if not year or year in seen_fig_years:
            continue
        if bc is not None:
            _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{year}_distribution{sfx}", bc)
        if pc is not None:
            _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{year}_composition_pie{sfx}", pc)
        seen_fig_years.add(year)

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
    if treemap_chart is not None and y1 and y2:
        _write_fig(zf, f"{fig_dir}/{slug}_mapbiomas_{y1}_vs_{y2}_class_transitions_treemap{sfx}", treemap_chart)
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
# Multi-window MapBiomas section
# ---------------------------------------------------------------------------

def _write_multi_window_section(
    zf: zipfile.ZipFile,
    base_dir: str,
    slug: str,
    *,
    mw_result: Optional[Dict] = None,
    name_suffix: str = "",
    include_treemaps: bool = True,
) -> None:
    """Write the multi-time-window MapBiomas outputs.

    ``mw_result`` must have the shape::

        {
            "years": [1985, 1993, 2001, ..., 2024],
            "pairs": [
                {"year_from": 1985, "year_to": 1993, "transitions": {...}},
                ...
            ],
        }

    Produces (inside ``base_dir/mapbiomas_multi_window/``):
      * one combined long-format CSV with columns
        ``year_from, year_to, class_from, class_to, area_ha``
      * one combined multi-stage Sankey (PNG + HTML)
      * one Sunburst per consecutive pair (PNG + HTML)
    """
    if not mw_result:
        return
    pairs = mw_result.get("pairs") or []
    years = mw_result.get("years") or []
    if not pairs or len(years) < 2:
        return

    mw_dir = f"{base_dir}/mapbiomas_multi_window"
    fig_dir = f"{mw_dir}/figures"
    sfx = name_suffix
    years_tag = "_".join(str(y) for y in years)
    base_name = f"{slug}_mapbiomas_multi_window_{years_tag}"

    # ---- Combined long-format CSV ---------------------------------------
    rows: List[Dict[str, Any]] = []
    for pair in pairs:
        y_from = pair.get("year_from")
        y_to = pair.get("year_to")
        for src_id, tgt_dict in (pair.get("transitions") or {}).items():
            if not isinstance(tgt_dict, dict):
                continue
            for tgt_id, area in tgt_dict.items():
                if not isinstance(area, (int, float)) or area <= 0:
                    continue
                rows.append({
                    "year_from": y_from,
                    "year_to": y_to,
                    "class_from": src_id,
                    "class_to": tgt_id,
                    "area_ha": float(area),
                })
    if rows:
        df = pd.DataFrame(rows)
        zf.writestr(
            f"{mw_dir}/{base_name}_transitions{sfx}.csv",
            _df_to_csv_bytes(df),
        )

    # ---- Figures (Sankey + per-pair sunbursts + per-pair treemaps) ------
    try:
        from .visualization import (
            create_multi_stage_sankey, create_sunburst_transitions,
            create_class_transition_treemaps,
        )
    except Exception as e:
        logger.warning(f"Could not import visualization helpers for multi-window: {e}")
        return

    try:
        stages = [
            (p["year_from"], p["year_to"], p.get("transitions") or {})
            for p in pairs
        ]
        sankey_fig = create_multi_stage_sankey(stages)
        if sankey_fig is not None:
            _write_fig(zf, f"{fig_dir}/{base_name}_sankey{sfx}", sankey_fig)
    except Exception as e:
        logger.warning(f"multi-window sankey build failed: {e}")

    for pair in pairs:
        y_from = pair.get("year_from")
        y_to = pair.get("year_to")
        tdict = pair.get("transitions") or {}
        if not tdict:
            continue
        try:
            sun_fig = create_sunburst_transitions(tdict, year_start=y_from, year_end=y_to)
            if sun_fig is not None:
                _write_fig(
                    zf,
                    f"{fig_dir}/{slug}_mapbiomas_{y_from}_vs_{y_to}_sunburst{sfx}",
                    sun_fig,
                )
        except Exception as e:
            logger.warning(f"multi-window sunburst {y_from}->{y_to} failed: {e}")
        if include_treemaps:
            try:
                tree_fig = create_class_transition_treemaps(tdict, y_from, y_to)
                if tree_fig is not None:
                    _write_fig(
                        zf,
                        f"{fig_dir}/{slug}_mapbiomas_{y_from}_vs_{y_to}_class_transitions_treemap{sfx}",
                        tree_fig,
                    )
            except Exception as e:
                logger.warning(f"multi-window treemap {y_from}->{y_to} failed: {e}")


# ---------------------------------------------------------------------------
# Deforestation timeline section
# ---------------------------------------------------------------------------

def _write_timeline_section(
    zf: zipfile.ZipFile,
    base_dir: str,
    slug: str,
    *,
    series: Optional[Dict[str, Dict]] = None,
    year_start: int = 0,
    year_end: int = 0,
    state_code: Optional[str] = None,
    territory_name: str = "",
    territory_type: str = "indigenous",
    title_extra: str = "",
    name_suffix: str = "",
) -> None:
    """Write the deforestation-timeline CSV + 3 chart variants.

    Mirrors the batch pipeline naming so interactive and batch exports merge
    cleanly::

        deforestation_timeline/{slug}_deforestation_timeline_{y1}_{y2}{sfx}.csv
        deforestation_timeline/figures/
            {slug}_deforestation_timeline_{y1}_{y2}_{raw|ma5|derivatives}{sfx}.png/.html

    ``series`` is ``{indicator: {year: ha}}`` from
    ``deforestation_timeline.collect_timeline``. Figures are rebuilt here (not
    taken from state) so the export always carries the full context chart —
    political stripes, ENSO strip, and policy rows included.
    """
    if not series or not year_start or not year_end:
        return
    y1, y2 = int(year_start), int(year_end)
    if y2 < y1:
        y1, y2 = y2, y1
    tl_dir = f"{base_dir}/deforestation_timeline"
    sfx = name_suffix

    # Wide CSV: one row per year, one column per indicator (int or str year keys)
    years = list(range(y1, y2 + 1))
    rows: List[Dict[str, Any]] = []
    for y in years:
        row: Dict[str, Any] = {"year": y}
        for k, ser in series.items():
            try:
                val = (ser or {}).get(y, (ser or {}).get(str(y), 0.0))
                row[k] = float(val or 0.0)
            except Exception:
                row[k] = 0.0
        rows.append(row)
    zf.writestr(
        f"{tl_dir}/{slug}_deforestation_timeline_{y1}_{y2}{sfx}.csv",
        _df_to_csv_bytes(pd.DataFrame(rows)),
    )

    try:
        from .visualization import create_deforestation_timeline_chart
    except Exception as e:
        logger.warning(f"timeline visualization import failed: {e}")
        return

    fig_dir = f"{tl_dir}/figures"
    for variant, suffix in (
        ("raw", "raw"),
        ("moving_avg", "ma5"),
        ("derivatives", "derivatives"),
    ):
        try:
            fig = create_deforestation_timeline_chart(
                series,
                state_code=state_code,
                year_start=y1,
                year_end=y2,
                variant=variant,
                moving_window=5,
                title_suffix=f"{territory_name}{title_extra}",
                territory_name=territory_name,
                territory_type=territory_type,
            )
            if fig is not None:
                _write_fig(
                    zf,
                    f"{fig_dir}/{slug}_deforestation_timeline_{y1}_{y2}_{suffix}{sfx}",
                    fig,
                    png_width=1400, png_scale=2.0,
                )
        except Exception as e:
            logger.warning(f"timeline figure ({variant}) failed: {e}")


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
    # Advanced viz: multi-window transitions + deforestation timeline
    mw_result: Optional[Dict[str, Any]] = None,
    buffer_mw_result: Optional[Dict[str, Any]] = None,
    #: {"series", "buffer_series", "state_code", "year_start", "year_end",
    #:  "territory_type"} — from the interactive timeline run
    timeline: Optional[Dict[str, Any]] = None,
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
            "has_multi_window": bool((mw_result or {}).get("pairs")),
            "has_timeline": bool((timeline or {}).get("series")),
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
            "  mapbiomas/                ← land-cover CSVs + figures",
            "  hansen_glad/              ← forest-cover snapshot CSVs + figures",
            "  hansen_gfc/               ← annual loss/gain CSVs + figures",
            "  mapbiomas_multi_window/   ← multi-year Sankey/Sunburst transitions (when run)",
            "  deforestation_timeline/   ← annual indicators + political/ENSO context (when run)",
            "  boundary.geojson          ← territory polygon",
            "buffer/{slug}/              ← same sub-structure for the buffer ring",
            "geometries.geojson          ← any manually drawn features",
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
            treemap_chart=territory_figures.get("treemap"),
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

        # ── Territory multi-window MapBiomas transitions ─────────────────────
        _write_multi_window_section(
            zf, terr_base, t_slug,
            mw_result=mw_result,
        )

        # ── Territory deforestation timeline ─────────────────────────────────
        if timeline and timeline.get("series"):
            _write_timeline_section(
                zf, terr_base, t_slug,
                series=timeline.get("series"),
                year_start=timeline.get("year_start") or 0,
                year_end=timeline.get("year_end") or 0,
                state_code=timeline.get("state_code") or None,
                territory_name=territory_name,
                territory_type=timeline.get("territory_type") or "indigenous",
            )

        # ── Buffer sections (only when buffer data exists) ───────────────────
        if any([
            buffer_mapbiomas_result,
            buffer_mapbiomas_comparison_result,
            buffer_hansen_result,
            buffer_gfc_result,
            buffer_mw_result,
            (timeline or {}).get("buffer_series"),
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
                treemap_chart=buffer_figures.get("treemap"),
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

            # Buffer multi-window MapBiomas transitions
            _write_multi_window_section(
                zf, buf_base, t_slug,
                mw_result=buffer_mw_result,
                name_suffix=buf_suffix,
            )

            # Buffer deforestation timeline
            if timeline and timeline.get("buffer_series"):
                _write_timeline_section(
                    zf, buf_base, t_slug,
                    series=timeline.get("buffer_series"),
                    year_start=timeline.get("year_start") or 0,
                    year_end=timeline.get("year_end") or 0,
                    state_code=timeline.get("state_code") or None,
                    territory_name=territory_name,
                    territory_type=timeline.get("territory_type") or "indigenous",
                    title_extra=f" — {buffer_name}" if buffer_name else " — Buffer",
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
        if state.treemap_transitions_chart:
            terr_figs["treemap"] = state.treemap_transitions_chart
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
        if state.buffer_treemap_chart:
            buf_figs["treemap"] = state.buffer_treemap_chart
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

    # ── Advanced viz: multi-window + deforestation timeline ─────────────────
    mw_result = None
    buffer_mw_result = None
    timeline = None
    try:
        if (state.mw_result or {}).get("pairs"):
            mw_result = state.mw_result
        if (state.buffer_mw_result or {}).get("pairs"):
            buffer_mw_result = state.buffer_mw_result
        if state.timeline_series:
            timeline = {
                "series": state.timeline_series,
                "buffer_series": state.buffer_timeline_series or None,
                "state_code": state.timeline_state_code or None,
                "year_start": state.timeline_year_start,
                "year_end": state.timeline_year_end,
                "territory_type": state.timeline_territory_type or "indigenous",
            }
    except Exception as e:
        logger.warning(f"Error collecting advanced-viz results: {e}")

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
        # Advanced viz
        "mw_result": mw_result,
        "buffer_mw_result": buffer_mw_result,
        "timeline": timeline,
    }
