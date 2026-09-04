"""
Phase 5: PDF map export service.
Ports Streamlit's map_pdf_export.py to work with Reflex.

Generates publication-quality PDF maps with:
  - Basemap tiles (Google/ArcGIS satellite)
  - Earth Engine raster overlays (MapBiomas, Hansen)
  - Polygon overlays with labels
  - Scale bar, grid, legend, title
"""

import io
import math
import logging
import os
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, Tuple

import matplotlib
matplotlib.use('Agg')
# NOT pyplot. ``plt`` is a global state machine (current figure / current axes)
# shared by every thread, which forced map composition onto a single render
# worker. ``Figure`` + ``FigureCanvasAgg`` own all their state, so composing
# maps is thread-safe and the matplotlib render lane can run several wide.
# See utils/ee_concurrency.py — the lane width is derived from this.
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.patches as mpatches
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import numpy as np

logger = logging.getLogger(__name__)

# Tile URL templates
TILE_URLS = {
    'google': 'https://mt0.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    'google_satellite': 'https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    'arcgis_satellite': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}

MAX_TILES = 40


# ---------------------------------------------------------------------------
# Basemap tile cache + parallel fetch
#
# Tiles used to be fetched one at a time in a nested loop, and nothing was
# cached — so every map in a set re-downloaded the same tiles for the same
# footprint, all of it sequential and (worse) all of it holding the serialized
# render lock. A 40-tile grid across four maps was ~160 blocking round-trips
# per territory. Measured at 98.5% of one batch run's wall clock.
#
# The cache is keyed by tile identity, not by map, so it also pays off across
# maps of neighbouring territories.
# ---------------------------------------------------------------------------

def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning(f"{name}={raw!r} is not an integer — using {default}")
        return default
    return value if value >= 1 else default


#: Tiles kept in memory. 256×256 satellite JPEG/PNG runs ~20–50 KB, so the
#: default sits around 20–50 MB — negligible against an 8 GiB container.
TILE_CACHE_MAX = _int_env("YVY_TILE_CACHE_TILES", 1024)

#: Concurrent tile downloads. Pure network I/O against a CDN.
TILE_FETCH_WORKERS = _int_env("YVY_TILE_FETCH_WORKERS", 8)

_TILE_CACHE: "OrderedDict[Tuple[str, int, int, int], bytes]" = OrderedDict()
_TILE_CACHE_LOCK = threading.Lock()
_tile_pool: Optional[ThreadPoolExecutor] = None
_tile_pool_lock = threading.Lock()


def _get_tile_pool() -> ThreadPoolExecutor:
    global _tile_pool
    if _tile_pool is None:
        with _tile_pool_lock:
            if _tile_pool is None:
                _tile_pool = ThreadPoolExecutor(
                    max_workers=TILE_FETCH_WORKERS, thread_name_prefix="tile"
                )
    return _tile_pool


def _tile_cache_get(key) -> Optional[bytes]:
    with _TILE_CACHE_LOCK:
        data = _TILE_CACHE.get(key)
        if data is not None:
            _TILE_CACHE.move_to_end(key)   # LRU touch
        return data


def _tile_cache_put(key, data: bytes) -> None:
    with _TILE_CACHE_LOCK:
        _TILE_CACHE[key] = data
        _TILE_CACHE.move_to_end(key)
        while len(_TILE_CACHE) > TILE_CACHE_MAX:
            _TILE_CACHE.popitem(last=False)


def clear_tile_cache() -> None:
    """Drop every cached tile (tests, or to reclaim memory)."""
    with _TILE_CACHE_LOCK:
        _TILE_CACHE.clear()


def _fetch_tile(provider: str, zoom: int, xi: int, yi: int):
    """Return ``(key, png_bytes_or_None, was_cache_hit)``.

    Never raises: a tile that will not load leaves its square blank, which is
    how this has always degraded.
    """
    import requests

    key = (provider, zoom, xi, yi)
    cached = _tile_cache_get(key)
    if cached is not None:
        return key, cached, True

    url_template = TILE_URLS.get(provider, TILE_URLS['google_satellite'])
    try:
        resp = requests.get(url_template.format(x=xi, y=yi, z=zoom), timeout=10)
        if resp.status_code == 200:
            _tile_cache_put(key, resp.content)
            return key, resp.content, False
    except Exception:
        pass
    return key, None, False


def _lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    """Convert lat/lon to tile coordinates."""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def _tile_to_lat_lon(x: int, y: int, zoom: int) -> Tuple[float, float]:
    """Convert tile coordinates back to lat/lon (top-left corner)."""
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1.0 - 2.0 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def _optimal_zoom(bounds: Tuple[float, float, float, float],
                  max_tiles: int = MAX_TILES) -> int:
    """Calculate optimal zoom level to keep tile count under limit."""
    min_lon, min_lat, max_lon, max_lat = bounds
    for z in range(15, 5, -1):
        x1, y1 = _lat_lon_to_tile(max_lat, min_lon, z)
        x2, y2 = _lat_lon_to_tile(min_lat, max_lon, z)
        n_tiles = (abs(x2 - x1) + 1) * (abs(y2 - y1) + 1)
        if n_tiles <= max_tiles:
            return z
    return 6


def get_basemap_image(bounds: Tuple[float, float, float, float],
                      tile_provider: str = 'google_satellite'):
    """
    Download and stitch basemap tiles for the given bounds.

    Returns (PIL.Image, actual_bounds) or (None, None).
    """
    try:
        from PIL import Image
        import requests
    except ImportError as e:
        logger.error(f"Missing dependency for basemap: {e}")
        return None, None

    min_lon, min_lat, max_lon, max_lat = bounds
    zoom = _optimal_zoom(bounds)

    x1, y1 = _lat_lon_to_tile(max_lat, min_lon, zoom)
    x2, y2 = _lat_lon_to_tile(min_lat, max_lon, zoom)

    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    cols = x2 - x1 + 1
    rows = y2 - y1 + 1

    composite = Image.new('RGB', (cols * 256, rows * 256), (255, 255, 255))

    # Fetch the whole grid at once (cache hits resolve without a request), then
    # paste. Decoding stays here on the calling thread — PIL decode is cheap
    # next to a round-trip, and it keeps the workers purely I/O-bound.
    coords = [(xi, yi) for xi in range(x1, x2 + 1) for yi in range(y1, y2 + 1)]
    results = list(_get_tile_pool().map(
        lambda c: _fetch_tile(tile_provider, zoom, c[0], c[1]), coords
    ))

    hits = sum(1 for _, _, hit in results if hit)
    misses = len(results) - hits
    for (_, _, xi, yi), data, _hit in results:
        if not data:
            continue
        try:
            tile = Image.open(io.BytesIO(data))
            composite.paste(tile, ((xi - x1) * 256, (yi - y1) * 256))
        except Exception:
            pass  # Leave white tile on failure
    logger.debug(
        f"basemap {tile_provider} z{zoom}: {len(results)} tiles "
        f"({hits} cached, {misses} fetched)"
    )

    # Calculate actual bounds of the tile grid
    top_lat, left_lon = _tile_to_lat_lon(x1, y1, zoom)
    bot_lat, right_lon = _tile_to_lat_lon(x2 + 1, y2 + 1, zoom)
    actual_bounds = (left_lon, bot_lat, right_lon, top_lat)

    return composite, actual_bounds


def get_ee_layer_image(bounds: Tuple[float, float, float, float],
                       ee_geometry,
                       layer_type: str = 'mapbiomas',
                       year: int = 2023,
                       vis_params: Optional[Dict] = None):
    """
    Download Earth Engine raster layer as PIL Image.

    Returns (PIL.Image, bounds) or (None, None).
    """
    try:
        import ee
        from PIL import Image
        import requests
    except ImportError as e:
        logger.error(f"Missing dependency for EE layer: {e}")
        return None, None

    try:
        min_lon, min_lat, max_lon, max_lat = bounds
        lon_span = max_lon - min_lon
        max_px_width = 1024
        scale = max(10, int(lon_span * 111000 / max_px_width))

        if layer_type == 'mapbiomas':
            from ..config.config import MAPBIOMAS_COLLECTIONS, MAPBIOMAS_DEFAULT_COLLECTION, MAPBIOMAS_PALETTE
            asset = MAPBIOMAS_COLLECTIONS.get(MAPBIOMAS_DEFAULT_COLLECTION, MAPBIOMAS_COLLECTIONS['v10_1'])
            image = ee.Image(asset).select(f'classification_{year}')
            if vis_params is None:
                vis_params = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
        elif layer_type == 'hansen':
            from ..config.config import HANSEN_DATASETS
            year_str = str(year)
            if year_str in HANSEN_DATASETS:
                image = ee.Image(HANSEN_DATASETS[year_str])
            else:
                return None, None
            if vis_params is None:
                vis_params = {'min': 0, 'max': 255}
        elif isinstance(layer_type, str) and layer_type.startswith('aux:'):
            # MapBiomas auxiliary rasters (deforestation, fire, mining,
            # agriculture-cycles). Spec comes from MAPBIOMAS_AUX_DATASETS so
            # palettes/bands can be tuned in config without touching this
            # renderer. We probe the asset's actual band names and try each
            # candidate in order — handles the common case where different
            # MapBiomas collections use slightly different band naming.
            from ..config.config import MAPBIOMAS_AUX_DATASETS, resolve_aux_band
            aux_key = layer_type.split(':', 1)[1]
            spec = MAPBIOMAS_AUX_DATASETS.get(aux_key)
            if spec is None:
                logger.warning(f"Unknown aux layer key: {aux_key}")
                return None, None
            asset_id = spec["asset"]
            candidates = spec.get("band_candidates") or []
            
            # Per-year layers: respect year range constraints, fall back
            # within the valid range if needed
            band = None
            year_used = year
            if spec.get("per_year") and year is not None:
                year_start = spec.get("year_start", 1985)
                year_end = spec.get("year_end", 2024)
                
                # If requested year is outside range, clamp to range
                if year < year_start:
                    logger.info(
                        f"aux layer {aux_key}: requested year {year} < "
                        f"available range start {year_start}, using {year_start}"
                    )
                    year_used = year_start
                elif year > year_end:
                    logger.info(
                        f"aux layer {aux_key}: requested year {year} > "
                        f"available range end {year_end}, using {year_end}"
                    )
                    year_used = year_end
                
                # Try clamped year and nearby years
                for y_try in (year_used, year_used + 1, year_used - 1):
                    if year_start <= y_try <= year_end:
                        band = resolve_aux_band(asset_id, candidates, year=y_try)
                        if band:
                            year_used = y_try
                            break
            else:
                # Pass the year even for non-per_year layers: some of these
                # assets (e.g. fire "year of last fire") still store per-year
                # bands, and resolve_aux_band skips {year} templates when it
                # gets no year to substitute.
                band = resolve_aux_band(asset_id, candidates, year=year)
            
            if band is None:
                logger.warning(
                    f"aux layer {aux_key}: no candidate band found in "
                    f"{asset_id}. Tried: {candidates}"
                )
                return None, None
            try:
                image = ee.Image(asset_id).select(band)
            except Exception as ee_err:
                logger.warning(
                    f"aux layer {aux_key}: select('{band}') failed on "
                    f"{asset_id} — {ee_err}"
                )
                return None, None
            if vis_params is None:
                vis_params = dict(spec.get("vis") or {})
            logger.info(
                f"aux layer {aux_key}: using band '{band}'"
                + (f" (year {year} → {year_used})"
                   if year_used != year else "")
            )
        else:
            return None, None

        # Clip and visualize
        image = image.clip(ee_geometry).visualize(**vis_params)

        # Download
        region = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
        url = image.getDownloadURL({
            'region': region.getInfo()['coordinates'],
            'scale': scale,
            'format': 'png',
        })

        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            img = Image.open(io.BytesIO(resp.content)).convert('RGBA')
            return img, bounds

    except Exception as e:
        logger.error(f"EE layer download failed: {e}")

    return None, None


def add_scale_bar(ax, min_lon: float, min_lat: float,
                  max_lon: float, max_lat: float):
    """Add a scale bar to the matplotlib axis."""
    mid_lat = (min_lat + max_lat) / 2
    map_width_km = (max_lon - min_lon) * 111 * math.cos(math.radians(mid_lat))

    # Choose appropriate scale
    if map_width_km > 200:
        scale_km = 50
    elif map_width_km > 100:
        scale_km = 25
    elif map_width_km > 50:
        scale_km = 10
    else:
        scale_km = 5

    scale_deg = scale_km / (111 * math.cos(math.radians(mid_lat)))
    x_start = min_lon + (max_lon - min_lon) * 0.05
    y_pos = min_lat + (max_lat - min_lat) * 0.05

    ax.plot([x_start, x_start + scale_deg], [y_pos, y_pos],
            color='black', linewidth=3, solid_capstyle='butt')
    ax.plot([x_start, x_start], [y_pos - 0.001, y_pos + 0.001],
            color='black', linewidth=2)
    ax.plot([x_start + scale_deg, x_start + scale_deg],
            [y_pos - 0.001, y_pos + 0.001], color='black', linewidth=2)
    ax.text(x_start + scale_deg / 2, y_pos + (max_lat - min_lat) * 0.015,
            f'{scale_km} km', ha='center', fontsize=8, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))


def get_geometry_bounds(features: List[Dict],
                        territory_geojson: Optional[Dict] = None,
                        buffer_geojson: Optional[Dict] = None,
                        padding: float = 0.1) -> Tuple[float, float, float, float]:
    """
    Get bounding box from features and/or territory + buffer GeoJSON.
    Returns (min_lon, min_lat, max_lon, max_lat) with padding.
    """
    all_lons, all_lats = [], []

    def _extract_coords(coords):
        if not coords:
            return
        if isinstance(coords[0], (int, float)):
            all_lons.append(coords[0])
            all_lats.append(coords[1])
        else:
            for c in coords:
                _extract_coords(c)

    def _from_geojson(gj):
        if not gj:
            return
        coords = gj.get('coordinates', [])
        if not coords and 'features' in gj:
            for f in gj['features']:
                _extract_coords(f.get('geometry', {}).get('coordinates', []))
        else:
            _extract_coords(coords)

    # Territory + buffer bounds (so the external ring isn't clipped off)
    _from_geojson(territory_geojson)
    _from_geojson(buffer_geojson)

    # Drawn features
    for feat in (features or []):
        geom = feat.get('geometry', feat)
        _extract_coords(geom.get('coordinates', []))

    if not all_lons or not all_lats:
        return (-75.0, -35.0, -35.0, 5.0)  # Default: Brazil

    min_lon, max_lon = min(all_lons), max(all_lons)
    min_lat, max_lat = min(all_lats), max(all_lats)

    # Add padding
    lon_pad = (max_lon - min_lon) * padding
    lat_pad = (max_lat - min_lat) * padding
    return (min_lon - lon_pad, min_lat - lat_pad,
            max_lon + lon_pad, max_lat + lat_pad)


def create_pdf_map(
    bounds: Tuple[float, float, float, float],
    layer_type: str = 'satellite',
    year: Optional[int] = None,
    drawn_features: Optional[List[Dict]] = None,
    territory_geojson: Optional[Dict] = None,
    buffer_geojson: Optional[Dict] = None,
    title: Optional[str] = None,
    ee_geometry=None,
    figsize: Tuple[int, int] = (12, 10),
    image_format: str = "pdf",
    prefetched: Optional[Dict[str, Any]] = None,
) -> Optional[bytes]:
    """
    Create a publication-quality map image.

    Args:
        bounds: (min_lon, min_lat, max_lon, max_lat)
        layer_type: 'satellite', 'mapbiomas', 'hansen', 'roadmap'
        year: Year for MapBiomas/Hansen layers
        drawn_features: Drawn polygon features to overlay
        territory_geojson: Territory boundary GeoJSON
        buffer_geojson: Buffer zone GeoJSON
        title: Map title
        ee_geometry: Earth Engine geometry for raster layer
        figsize: Figure size in inches
        image_format: 'pdf' (default), 'png', or any other matplotlib backend
            that ``Figure.savefig`` accepts.
        prefetched: optional ``{"raster": (img, bounds), "basemap": (img, bounds)}``
            from :func:`prefetch_map_inputs`. A present key means "already
            fetched, do not download" — including when its value is
            ``(None, None)``, which records a fetch that was attempted and
            failed, so the fallback path still runs without a retry.

    Returns:
        bytes: rendered image bytes, or None on error
    """
    try:
        min_lon, min_lat, max_lon, max_lat = bounds
        fig = Figure(figsize=figsize)
        FigureCanvasAgg(fig)          # attach a renderer; no global registry
        ax = fig.add_subplot(1, 1, 1)

        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        ax.set_aspect('equal')

        pf = prefetched or {}

        def _basemap():
            """Prefetched satellite basemap if we have one, else fetch now."""
            if "basemap" in pf and pf["basemap"] is not None:
                return pf["basemap"]
            return get_basemap_image(bounds, 'google_satellite')

        # 1. Basemap
        if layer_type in ('satellite', 'google_satellite', 'arcgis_satellite'):
            basemap, bm_bounds = _basemap()
            if basemap:
                ax.imshow(basemap, extent=[bm_bounds[0], bm_bounds[2], bm_bounds[1], bm_bounds[3]],
                          aspect='auto', zorder=0)
        elif layer_type == 'roadmap':
            basemap, bm_bounds = get_basemap_image(bounds, 'google')
            if basemap:
                ax.imshow(basemap, extent=[bm_bounds[0], bm_bounds[2], bm_bounds[1], bm_bounds[3]],
                          aspect='auto', zorder=0)
        elif (
            layer_type in ('mapbiomas', 'hansen')
            or (isinstance(layer_type, str) and layer_type.startswith('aux:'))
        ) and ee_geometry:
            # EE raster overlay (year is required for per-year layers; aux
            # layers with per_year=False ignore it).
            if "raster" in pf:
                ee_img, ee_bounds = pf["raster"]
            else:
                ee_img, ee_bounds = get_ee_layer_image(
                    bounds, ee_geometry, layer_type, year
                )
            if ee_img:
                ax.imshow(ee_img, extent=[ee_bounds[0], ee_bounds[2], ee_bounds[1], ee_bounds[3]],
                          aspect='auto', zorder=1, alpha=0.85)
            else:
                # Fallback to satellite basemap so the territory + buffer
                # outlines still have a meaningful background.
                basemap, bm_bounds = _basemap()
                if basemap:
                    ax.imshow(basemap, extent=[bm_bounds[0], bm_bounds[2], bm_bounds[1], bm_bounds[3]],
                              aspect='auto', zorder=0)

        # 2. Territory boundary
        if territory_geojson:
            _plot_geojson(ax, territory_geojson, color='purple', linewidth=2,
                          fill_alpha=0.1, label='Territory', zorder=5)

        # 3. Buffer zone
        if buffer_geojson:
            _plot_geojson(ax, buffer_geojson, color='blue', linewidth=1.5,
                          linestyle='--', fill_alpha=0.05, label='Buffer', zorder=4)

        # 4. Drawn polygons
        if drawn_features:
            for i, feat in enumerate(drawn_features):
                geom = feat.get('geometry', feat)
                _plot_geojson(ax, geom, color='#2196F3', linewidth=1.5,
                              fill_alpha=0.15, zorder=6)
                # Add number label at centroid
                centroid = _geojson_centroid(geom)
                if centroid:
                    ax.annotate(str(i + 1), xy=centroid, fontsize=9,
                                fontweight='bold', color='white', ha='center', va='center',
                                bbox=dict(boxstyle='circle,pad=0.3', facecolor='#2196F3', alpha=0.9),
                                zorder=7)

        # 5. Scale bar
        add_scale_bar(ax, min_lon, min_lat, max_lon, max_lat)

        # 6. Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.set_xlabel('Longitude', fontsize=10)
        ax.set_ylabel('Latitude', fontsize=10)

        # 7. Title
        if title:
            ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
        else:
            default_title = f'{layer_type.title()} Map'
            if year:
                default_title += f' ({year})'
            ax.set_title(default_title, fontsize=14, fontweight='bold', pad=15)

        # 8. Legend
        legend_handles = []
        if territory_geojson:
            legend_handles.append(mpatches.Patch(facecolor='purple', alpha=0.3, label='Territory'))
        if buffer_geojson:
            legend_handles.append(mpatches.Patch(facecolor='blue', alpha=0.2,
                                                  linestyle='--', label='Buffer Zone'))
        if drawn_features:
            legend_handles.append(mpatches.Patch(facecolor='#2196F3', alpha=0.3,
                                                  label=f'Polygons ({len(drawn_features)})'))
        if legend_handles:
            ax.legend(handles=legend_handles, loc='upper right', fontsize=8)

        # 9. Timestamp
        ax.text(0.01, 0.01, f'Yvynation | {year or ""} | Generated {__import__("datetime").datetime.now().strftime("%Y-%m-%d")}',
                transform=ax.transAxes, fontsize=7, color='gray', alpha=0.7)

        fig.tight_layout()

        # Export to bytes in the requested format
        buf = io.BytesIO()
        fig.savefig(buf, format=image_format, dpi=150, bbox_inches='tight')
        # No plt.close() — nothing registered the figure globally, so it is
        # freed with its last reference.
        buf.seek(0)
        return buf.read()

    except Exception as e:
        logger.error(f"Map image creation failed ({image_format}): {e}")
        return None


def _plot_geojson(ax, geojson: Dict, color: str = 'blue',
                  linewidth: float = 1.5, linestyle: str = '-',
                  fill_alpha: float = 0.1, label: str = '',
                  zorder: int = 5):
    """Plot a GeoJSON geometry on matplotlib axis."""
    from matplotlib.patches import Polygon as MplPolygon
    from matplotlib.collections import PatchCollection

    geom_type = geojson.get('type', '')
    coords = geojson.get('coordinates', [])

    if not coords and 'features' in geojson:
        for f in geojson['features']:
            _plot_geojson(ax, f.get('geometry', {}), color=color,
                          linewidth=linewidth, linestyle=linestyle,
                          fill_alpha=fill_alpha, zorder=zorder)
        return

    if geom_type == 'Polygon':
        for ring in coords:
            if ring:
                xs = [c[0] for c in ring]
                ys = [c[1] for c in ring]
                ax.fill(xs, ys, alpha=fill_alpha, color=color, zorder=zorder)
                ax.plot(xs, ys, color=color, linewidth=linewidth,
                        linestyle=linestyle, zorder=zorder + 1)
    elif geom_type == 'MultiPolygon':
        for polygon in coords:
            for ring in polygon:
                if ring:
                    xs = [c[0] for c in ring]
                    ys = [c[1] for c in ring]
                    ax.fill(xs, ys, alpha=fill_alpha, color=color, zorder=zorder)
                    ax.plot(xs, ys, color=color, linewidth=linewidth,
                            linestyle=linestyle, zorder=zorder + 1)


def _geojson_centroid(geojson: Dict) -> Optional[Tuple[float, float]]:
    """Calculate approximate centroid of a GeoJSON geometry."""
    coords = geojson.get('coordinates', [])
    if not coords:
        return None

    all_pts = []

    def _flatten(c):
        if isinstance(c[0], (int, float)):
            all_pts.append(c)
        else:
            for sub in c:
                _flatten(sub)

    _flatten(coords)

    if not all_pts:
        return None

    avg_x = sum(p[0] for p in all_pts) / len(all_pts)
    avg_y = sum(p[1] for p in all_pts) / len(all_pts)
    return (avg_x, avg_y)


def _raster_specs(
    active_mapbiomas_years: Optional[List[int]],
    active_hansen_layers: Optional[List[str]],
    active_aux_layers: Optional[List[Tuple[str, Optional[int]]]],
) -> List[Dict[str, Any]]:
    """Describe every raster-backed map in a set.

    The single source of truth for map identity: the prefetch pass and the
    compose pass both walk this list, so a raster fetched under one key can
    never be looked up under another.
    """
    specs: List[Dict[str, Any]] = []

    for year in (active_mapbiomas_years or []):
        specs.append({
            "key": f"mapbiomas:{year}",
            "layer_type": "mapbiomas",
            "year": year,
            "map_name": f"MapBiomas_{year}",
            "title": f"MapBiomas Land Cover - {year}",
        })

    for layer in (active_hansen_layers or []):
        try:
            year = int(layer)
        except (ValueError, TypeError):
            continue
        specs.append({
            "key": f"hansen:{year}",
            "layer_type": "hansen",
            "year": year,
            "map_name": f"Hansen_{year}",
            "title": f"Hansen/GLAD - {year}",
        })

    if active_aux_layers:
        try:
            from ..config.config import MAPBIOMAS_AUX_DATASETS
        except Exception:
            MAPBIOMAS_AUX_DATASETS = {}
        for aux_key, year in active_aux_layers:
            spec = MAPBIOMAS_AUX_DATASETS.get(aux_key)
            if spec is None:
                logger.warning(f"aux layer '{aux_key}' not in MAPBIOMAS_AUX_DATASETS")
                continue
            label = spec.get("label", aux_key)
            per_year = bool(spec.get("per_year", False))
            year_for_call = year if per_year else None
            name_year = f"_{year}" if per_year and year else ""
            # PNG-safe filename slug for the layer
            safe_label = "".join(
                c if c.isalnum() else "_"
                for c in label.replace(" ", "_")
            ).strip("_") or aux_key
            specs.append({
                "key": f"aux:{aux_key}:{year_for_call}",
                "layer_type": f"aux:{aux_key}",
                "year": year_for_call,
                "map_name": f"{safe_label}{name_year}",
                "title": f"{label}{(' ' + str(year)) if per_year and year else ''}",
            })

    return specs


def _resolve_raster_geometry(ee_geometry, buffer_geojson):
    """Clip footprint for raster overlays: territory ∪ buffer, so MapBiomas /
    Hansen pixels render inside both regions — not just the territory."""
    if ee_geometry is None or not buffer_geojson:
        return ee_geometry
    try:
        from .buffer_utils import convert_geojson_to_ee_geometry
        buf = convert_geojson_to_ee_geometry(buffer_geojson, "buffer (raster clip)")
        if buf is None:
            return ee_geometry
        return ee_geometry.union(buf, 1)
    except Exception as e:
        logger.warning(f"buffer union for raster clip failed: {e}")
        return ee_geometry


def prefetch_map_inputs(
    drawn_features: List[Dict],
    active_mapbiomas_years: Optional[List[int]] = None,
    active_hansen_layers: Optional[List[str]] = None,
    ee_geometry=None,
    territory_geojson: Optional[Dict] = None,
    buffer_geojson: Optional[Dict] = None,
    active_aux_layers: Optional[List[Tuple[str, Optional[int]]]] = None,
) -> Dict[str, Any]:
    """Fetch every image a map set needs, concurrently.

    Downloading rasters is network work — an ``getDownloadURL`` round-trip per
    layer plus the tile grid — and none of it touches matplotlib. Doing it here
    means the caller can run it *outside* the serialized render lock and in
    parallel, leaving only the actual compositing to be serialized.

    EE downloads go through the shared Earth Engine pool so they stay inside the
    tier budget and show up in the run's metering, exactly like the analysis
    calls do.

    Pass the result to :func:`create_map_set` as ``prefetched=``. Safe to skip
    entirely — ``create_map_set`` falls back to fetching inline.

    .. warning::
       Must **not** be called from a thread of the Earth Engine pool. It submits
       to that pool and blocks on the results, so running it there would let a
       few concurrent calls occupy every worker while waiting on work that can
       never be scheduled. Call it from the default executor.
    """
    from .ee_concurrency import ee_meter, get_ee_executor

    bounds = get_geometry_bounds(drawn_features, territory_geojson, buffer_geojson)
    raster_geometry = _resolve_raster_geometry(ee_geometry, buffer_geojson)
    specs = _raster_specs(
        active_mapbiomas_years, active_hansen_layers, active_aux_layers
    )

    out: Dict[str, Any] = {
        "bounds": bounds,
        "raster_geometry": raster_geometry,
        "rasters": {},
        "basemap": None,
    }

    def _one_raster(spec):
        # Metered by hand: this bypasses _ee_with_retry (which is async and
        # lives in the batch layer), so without this the pool would look idle
        # while doing real Earth Engine work.
        with ee_meter.track():
            return get_ee_layer_image(
                bounds, raster_geometry, spec["layer_type"], spec["year"]
            )

    futures = {}
    executor = get_ee_executor()
    if raster_geometry is not None:
        for spec in specs:
            futures[spec["key"]] = executor.submit(_one_raster, spec)

    # The satellite map always needs the basemap, and every raster map falls
    # back to it when its layer fails — so it is always worth having.
    #
    # Run on this thread rather than submitting it to the tile pool: it calls
    # into that pool itself, and a task that blocks on its own pool deadlocks
    # once enough of them run at once. Here it still overlaps the EE downloads
    # submitted above (different pool) and parallelises its own tiles.
    try:
        out["basemap"] = get_basemap_image(bounds, 'google_satellite')
    except Exception as e:  # noqa: BLE001
        logger.warning(f"prefetch of basemap failed: {e}")
        out["basemap"] = (None, None)

    for key, fut in futures.items():
        try:
            out["rasters"][key] = fut.result()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"prefetch of raster {key} failed: {e}")
            out["rasters"][key] = (None, None)

    return out


def create_map_set(
    drawn_features: List[Dict],
    territory_name: Optional[str] = None,
    active_mapbiomas_years: Optional[List[int]] = None,
    active_hansen_layers: Optional[List[str]] = None,
    ee_geometry=None,
    territory_geojson: Optional[Dict] = None,
    buffer_geojson: Optional[Dict] = None,
    image_format: str = "pdf",
    active_aux_layers: Optional[List[Tuple[str, Optional[int]]]] = None,
    prefetched: Optional[Dict[str, Any]] = None,
) -> Dict[str, bytes]:
    """
    Generate a set of maps for all active layers.

    Returns dict of {map_name: image_bytes}. The byte content is the file
    encoded with ``image_format`` (e.g. 'pdf' or 'png').

    *prefetched* is an optional :func:`prefetch_map_inputs` result. When given,
    no downloading happens here at all — only compositing — which is what lets
    the caller keep the network work out of the render lock.
    """
    maps = {}
    pf = prefetched or {}

    bounds = pf.get("bounds") or get_geometry_bounds(
        drawn_features, territory_geojson, buffer_geojson
    )
    raster_geometry = (
        pf["raster_geometry"] if "raster_geometry" in pf
        else _resolve_raster_geometry(ee_geometry, buffer_geojson)
    )
    prefetched_rasters = pf.get("rasters") or {}
    prefetched_basemap = pf.get("basemap")

    for spec in _raster_specs(
        active_mapbiomas_years, active_hansen_layers, active_aux_layers
    ):
        title = spec["title"]
        if territory_name:
            title += f" | {territory_name}"
        per_map = {}
        if spec["key"] in prefetched_rasters:
            per_map["raster"] = prefetched_rasters[spec["key"]]
        if prefetched_basemap is not None:
            per_map["basemap"] = prefetched_basemap
        img = create_pdf_map(
            bounds, spec["layer_type"], spec["year"], drawn_features,
            territory_geojson, buffer_geojson, title, raster_geometry,
            image_format=image_format,
            prefetched=per_map or None,
        )
        if img:
            maps[spec["map_name"]] = img

    # Satellite basemap
    img = create_pdf_map(
        bounds, 'satellite', None, drawn_features,
        territory_geojson, buffer_geojson,
        f"Satellite Basemap{' | ' + territory_name if territory_name else ''}",
        image_format=image_format,
        prefetched=(
            {"basemap": prefetched_basemap} if prefetched_basemap is not None else None
        ),
    )
    if img:
        maps["Satellite_Basemap"] = img

    return maps
