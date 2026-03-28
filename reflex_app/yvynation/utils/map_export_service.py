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
from typing import Dict, Any, Optional, List, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
    url_template = TILE_URLS.get(tile_provider, TILE_URLS['google_satellite'])

    x1, y1 = _lat_lon_to_tile(max_lat, min_lon, zoom)
    x2, y2 = _lat_lon_to_tile(min_lat, max_lon, zoom)

    if x1 > x2:
        x1, x2 = x2, x1
    if y1 > y2:
        y1, y2 = y2, y1

    cols = x2 - x1 + 1
    rows = y2 - y1 + 1

    composite = Image.new('RGB', (cols * 256, rows * 256), (255, 255, 255))

    for xi in range(x1, x2 + 1):
        for yi in range(y1, y2 + 1):
            url = url_template.format(x=xi, y=yi, z=zoom)
            try:
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    tile = Image.open(io.BytesIO(resp.content))
                    composite.paste(tile, ((xi - x1) * 256, (yi - y1) * 256))
            except Exception:
                pass  # Leave white tile on failure

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
            from ..config.config import MAPBIOMAS_PALETTE
            asset = 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1'
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
                        padding: float = 0.1) -> Tuple[float, float, float, float]:
    """
    Get bounding box from features and/or territory GeoJSON.
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

    # Territory bounds first
    if territory_geojson:
        coords = territory_geojson.get('coordinates', [])
        if not coords and 'features' in territory_geojson:
            for f in territory_geojson['features']:
                _extract_coords(f.get('geometry', {}).get('coordinates', []))
        else:
            _extract_coords(coords)

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
) -> Optional[bytes]:
    """
    Create a publication-quality PDF map.

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

    Returns:
        bytes: PDF file content, or None on error
    """
    try:
        min_lon, min_lat, max_lon, max_lat = bounds
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        ax.set_xlim(min_lon, max_lon)
        ax.set_ylim(min_lat, max_lat)
        ax.set_aspect('equal')

        # 1. Basemap
        if layer_type in ('satellite', 'google_satellite', 'arcgis_satellite'):
            basemap, bm_bounds = get_basemap_image(bounds, 'google_satellite')
            if basemap:
                ax.imshow(basemap, extent=[bm_bounds[0], bm_bounds[2], bm_bounds[1], bm_bounds[3]],
                          aspect='auto', zorder=0)
        elif layer_type == 'roadmap':
            basemap, bm_bounds = get_basemap_image(bounds, 'google')
            if basemap:
                ax.imshow(basemap, extent=[bm_bounds[0], bm_bounds[2], bm_bounds[1], bm_bounds[3]],
                          aspect='auto', zorder=0)
        elif layer_type in ('mapbiomas', 'hansen') and ee_geometry and year:
            # EE raster overlay
            ee_img, ee_bounds = get_ee_layer_image(bounds, ee_geometry, layer_type, year)
            if ee_img:
                ax.imshow(ee_img, extent=[ee_bounds[0], ee_bounds[2], ee_bounds[1], ee_bounds[3]],
                          aspect='auto', zorder=1, alpha=0.85)
            else:
                # Fallback to satellite basemap
                basemap, bm_bounds = get_basemap_image(bounds, 'google_satellite')
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

        plt.tight_layout()

        # Export to PDF bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='pdf', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        logger.error(f"PDF map creation failed: {e}")
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


def create_map_set(
    drawn_features: List[Dict],
    territory_name: Optional[str] = None,
    active_mapbiomas_years: Optional[List[int]] = None,
    active_hansen_layers: Optional[List[str]] = None,
    ee_geometry=None,
    territory_geojson: Optional[Dict] = None,
    buffer_geojson: Optional[Dict] = None,
) -> Dict[str, bytes]:
    """
    Generate a set of PDF maps for all active layers.

    Returns dict of {map_name: pdf_bytes}.
    """
    maps = {}

    bounds = get_geometry_bounds(drawn_features, territory_geojson)

    # MapBiomas maps
    for year in (active_mapbiomas_years or []):
        name = f"MapBiomas_{year}"
        title = f"MapBiomas Land Cover - {year}"
        if territory_name:
            title += f" | {territory_name}"
        pdf = create_pdf_map(
            bounds, 'mapbiomas', year, drawn_features,
            territory_geojson, buffer_geojson, title, ee_geometry,
        )
        if pdf:
            maps[name] = pdf

    # Hansen maps
    for layer in (active_hansen_layers or []):
        try:
            year = int(layer)
        except (ValueError, TypeError):
            continue
        name = f"Hansen_{year}"
        title = f"Hansen/GLAD - {year}"
        if territory_name:
            title += f" | {territory_name}"
        pdf = create_pdf_map(
            bounds, 'hansen', year, drawn_features,
            territory_geojson, buffer_geojson, title, ee_geometry,
        )
        if pdf:
            maps[name] = pdf

    # Satellite basemap
    pdf = create_pdf_map(
        bounds, 'satellite', None, drawn_features,
        territory_geojson, buffer_geojson,
        f"Satellite Basemap{' | ' + territory_name if territory_name else ''}",
    )
    if pdf:
        maps["Satellite_Basemap"] = pdf

    return maps
