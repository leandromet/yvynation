"""
PDF Map Export Components
Creates publication-quality PDF maps with layers and polygon overlays
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from PIL import Image
import io
import json
from datetime import datetime
import ee
from config import MAPBIOMAS_COLOR_MAP, MAPBIOMAS_PALETTE, HANSEN_CONSOLIDATED_COLORS
import urllib.request
import urllib.parse
import warnings
warnings.filterwarnings('ignore')
from contextlib import suppress


def get_basemap_image(geom_bounds, tile_provider='google'):
    """
    Get basemap tiles for a given bounding box
    
    Args:
        geom_bounds: Tuple of (min_lon, min_lat, max_lon, max_lat) in [lon, lat] order
        tile_provider: 'google' (roadmap), 'google_satellite', or 'arcgis_satellite'
    
    Returns:
        PIL.Image or None
    """
    try:
        min_lon, min_lat, max_lon, max_lat = geom_bounds
        print(f"DEBUG: Fetching {tile_provider} basemap for bounds: ({min_lat:.4f}, {min_lon:.4f}) to ({max_lat:.4f}, {max_lon:.4f})")
        
        # Mercator projection functions
        def latlng2tiles(lat, lng, z):
            """Convert lat/lng to tile coordinates"""
            n = 2.0 ** z
            x = int((lng + 180.0) / 360.0 * n)
            y = int((1.0 - np.log(np.tan(np.radians(lat)) + 1.0 / np.cos(np.radians(lat))) / np.pi) / 2.0 * n)
            return (x, y)
        
        def tile2latlng(x, y, z):
            """Convert tile coordinates to lat/lng"""
            n = 2.0 ** z
            lng = x / n * 360.0 - 180.0
            lat = np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * y / n))))
            return (lat, lng)
        
        # Calculate optimal zoom level based on bounds extent
        # Zoom formula: z = log2(360 / span_lon) where span_lon is the longitude span
        lon_span = max_lon - min_lon
        lat_span = max_lat - min_lat
        
        # Start with a zoom that shows the full extent at reasonable resolution
        # Using a target of ~256 pixels per tile to maintain reasonable detail
        # Add +1 for one step more detailed resolution
        z = max(6, min(15, int(np.log2(360.0 / max(lon_span, lat_span * 1.2))) + 1))
        print(f"DEBUG: Bounds span: lon={lon_span:.4f}°, lat={lat_span:.4f}°, calculated zoom={z}")
        
        # Get tile coordinates for bounds - careful with lat/lng order!
        # Top-left is max_lat, min_lon; bottom-right is min_lat, max_lon
        (x_min, y_max) = latlng2tiles(max_lat, min_lon, z)
        (x_max, y_min) = latlng2tiles(min_lat, max_lon, z)
        
        # Ensure x_min <= x_max and y_min <= y_max
        if x_min > x_max:
            x_min, x_max = x_max, x_min
        if y_min > y_max:
            y_min, y_max = y_max, y_min
        
        tiles_needed = (x_max - x_min + 1) * (y_max - y_min + 1)
        print(f"DEBUG: Zoom {z} needs {tiles_needed} tiles ({x_max - x_min + 1}x{y_max - y_min + 1})")
        
        # Limit to reasonable number of tiles - adjust zoom down if too many
        while tiles_needed > 40 and z > 6:
            z -= 1
            (x_min, y_max) = latlng2tiles(max_lat, min_lon, z)
            (x_max, y_min) = latlng2tiles(min_lat, max_lon, z)
            
            if x_min > x_max:
                x_min, x_max = x_max, x_min
            if y_min > y_max:
                y_min, y_max = y_max, y_min
            
            tiles_needed = (x_max - x_min + 1) * (y_max - y_min + 1)
            print(f"DEBUG: Adjusted to zoom {z}, needs {tiles_needed} tiles ({x_max - x_min + 1}x{y_max - y_min + 1})")
        
        # Create composite image
        tile_size = 256
        width = (x_max - x_min + 1) * tile_size
        height = (y_max - y_min + 1) * tile_size
        print(f"DEBUG: Creating composite image {width}x{height} for zoom {z}")
        composite = Image.new('RGB', (width, height))
        
        # Download tiles - use Google Maps instead of OSM
        if tile_provider == 'google_satellite':
            base_url = 'https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
        elif tile_provider == 'arcgis_satellite':
            base_url = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
        else:  # google roadmap (default)
            base_url = 'https://mt0.google.com/vt/lyrs=m&x={x}&y={y}&z={z}'
        
        failed_tiles = 0
        success_tiles = 0
        
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                try:
                    url = base_url.format(z=z, x=x, y=y)
                    
                    response = urllib.request.urlopen(url, timeout=10)
                    tile = Image.open(response)
                    composite.paste(tile, ((x - x_min) * tile_size, (y - y_min) * tile_size))
                    success_tiles += 1
                except Exception as e:
                    # Tile failed, use white fill
                    failed_tiles += 1
                    tile = Image.new('RGB', (tile_size, tile_size), color=(255, 255, 255))
                    composite.paste(tile, ((x - x_min) * tile_size, (y - y_min) * tile_size))
        
        print(f"DEBUG: Tiles downloaded - Success: {success_tiles}, Failed: {failed_tiles}")
        
        # Calculate actual bounds of composite
        ul_lat, ul_lng = tile2latlng(x_min, y_min, z)
        lr_lat, lr_lng = tile2latlng(x_max + 1, y_max + 1, z)
        
        print(f"DEBUG: Basemap created successfully at zoom {z}")
        return composite, (lr_lat, ul_lng, ul_lat, lr_lng)
    
    except Exception as e:
        print(f"WARNING: Could not fetch basemap: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def get_ee_layer_image(geom_bounds, geometry, layer_type, year, vis_params=None):
    """
    Get Earth Engine layer as a PIL Image for a given geometry and year
    Uses getDownloadURL() to export a complete image instead of tile stitching
    
    Note: This requires proper Earth Engine authentication and asset access.
    MapBiomas Collection 9 and Hansen GFC datasets must be accessible to your EE account.
    
    Args:
        geom_bounds: Tuple of (min_lon, min_lat, max_lon, max_lat) for display extent
        geometry: ee.Geometry bounding box for clipping
        layer_type: 'mapbiomas' or 'hansen'
        year: Year for the layer
        vis_params: Visualization parameters dict
    
    Returns:
        (PIL.Image, bounds_tuple) or (None, None) if failed
    """
    try:
        if layer_type == 'mapbiomas':
            # Get MapBiomas image - use correct public asset path
            print(f"DEBUG: Accessing MapBiomas Collection 9 for year {year}...")
            mapbiomas_asset = 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1'
            mapbiomas_image = ee.Image(mapbiomas_asset)
            print(f"DEBUG: Loaded MapBiomas asset")
            
            # Select the classification band for the specific year
            band_name = f'classification_{year}'
            print(f"DEBUG: Selecting band: {band_name}")
            image = mapbiomas_image.select(band_name)
            print(f"DEBUG: Band selected successfully")
            
            # Use MapBiomas color palette (0-62 range with proper colors)
            if vis_params is None:
                # MAPBIOMAS_PALETTE is a list of hex colors (without '#') for classes 0-62
                palette_str = ','.join(MAPBIOMAS_PALETTE)
                print(f"DEBUG: Using MapBiomas palette with {len(MAPBIOMAS_PALETTE)} colors")
                vis_params = {
                    'min': 0,
                    'max': 62,
                    'palette': palette_str
                }
        
        elif layer_type == 'hansen':
            # Get Hansen Global Forest Change layer
            print(f"DEBUG: Accessing Hansen GFC 2021 dataset for year {year}...")
            # Use the correct Hansen dataset path
            from config import HANSEN_DATASETS
            
            if str(year) not in HANSEN_DATASETS:
                print(f"WARNING: Hansen dataset not available for year {year}")
                return None, None
            
            hansen_asset = HANSEN_DATASETS[str(year)]
            hansen_image = ee.Image(hansen_asset)
            image = hansen_image
            
            if vis_params is None:
                vis_params = {
                    'min': 0,
                    'max': 255,
                    'palette': 'ffffff,1a9850,66bd63,a6d96a,d9ef8b'
                }
        
        else:
            return None, None
        
        # Clip to geometry
        print(f"DEBUG: Clipping image to geometry...")
        clipped = image.clip(geometry)
        print(f"DEBUG: Image clipped successfully")
        
        # Visualize the image with the palette
        print(f"DEBUG: Applying visualization with palette...")
        print(f"DEBUG: Vis params - min: {vis_params.get('min')}, max: {vis_params.get('max')}")
        print(f"DEBUG: Palette length: {len(vis_params.get('palette', ''))}")
        visualized = clipped.visualize(**vis_params)
        print(f"DEBUG: Visualization applied")
        
        # Use getDownloadURL() to export the complete image as PNG
        print(f"DEBUG: Generating download URL for complete {layer_type} image...")
        min_lon, min_lat, max_lon, max_lat = geom_bounds
        
        # Get download URL with proper region and scale
        # Use maxPixels to allow larger exports, but respect Earth Engine's 50MB limit
        # For large regions, we need a coarser scale to stay under the limit
        lon_span = max_lon - min_lon
        
        # Earth Engine has a ~50MB limit for downloads
        # Each RGBA pixel is 4 bytes, so ~50MB ÷ 4 = ~12.5M pixels max
        # For a square region: sqrt(12.5M) ≈ 3500 pixels per side
        # Conservative target: ~2000 pixels wide to stay well under the limit
        # But for very large regions, we need to scale back further
        max_pixels_width = max(512, min(2000, int(111000 * lon_span / 10)))  # pixels
        scale = max(10, int(lon_span * 111000 / max_pixels_width))  # meters per pixel
        print(f"DEBUG: Calculated scale for region: {scale}m per pixel, target width: {max_pixels_width}px")
        
        url = visualized.getDownloadURL({
            'region': geometry,
            'scale': scale,
            'format': 'png',
            'maxPixels': 1e8  # 100 million pixels (more conservative)
        })
        
        print(f"DEBUG: Download URL generated successfully")
        print(f"DEBUG: URL length: {len(url)}, first 150 chars: {url[:150]}...")
        
        # Download image
        print(f"DEBUG: Downloading complete image from Earth Engine...")
        response = urllib.request.urlopen(url, timeout=30)
        print(f"DEBUG: Response received, downloading...")
        img = Image.open(response)
        print(f"DEBUG: Image opened, size: {img.size}, mode: {img.mode}")
        
        # Calculate accurate bounds based on actual image dimensions
        # Earth Engine returns images at the specified scale, so bounds need to account for pixel size
        img_width, img_height = img.size
        lon_span = max_lon - min_lon
        lat_span = max_lat - min_lat
        
        # Pixel size in degrees
        pixel_lon = lon_span / img_width
        pixel_lat = lat_span / img_height
        
        # Adjust bounds to align with pixel boundaries (top-left corner registration)
        # This ensures the image pixels align exactly with the geographic coordinates
        adjusted_max_lat = max_lat  # Top edge stays at max_lat
        adjusted_min_lon = min_lon  # Left edge stays at min_lon
        adjusted_min_lat = adjusted_max_lat - (img_height * pixel_lat)
        adjusted_max_lon = adjusted_min_lon + (img_width * pixel_lon)
        
        ee_bounds = (adjusted_min_lat, adjusted_min_lon, adjusted_max_lat, adjusted_max_lon)
        print(f"DEBUG: Actual image bounds: ({adjusted_min_lat:.6f}, {adjusted_min_lon:.6f}) to ({adjusted_max_lat:.6f}, {adjusted_max_lon:.6f})")
        print(f"DEBUG: Pixel size: lon={pixel_lon:.8f}°, lat={pixel_lat:.8f}°")
        
        # Return image with calculated bounds
        print(f"DEBUG: Successfully loaded {layer_type} {year} image")
        return img, ee_bounds
    
    except Exception as e:
        error_msg = str(e)
        print(f"DEBUG: Error occurred in get_ee_layer_image: {type(e).__name__}")
        print(f"DEBUG: Error message: {error_msg}")
        import traceback
        traceback.print_exc()
        
        if "not found" in error_msg or "does not exist" in error_msg:
            print(f"ERROR: {layer_type} dataset not accessible: {e}")
            print(f"       Check your Earth Engine credentials and dataset permissions")
        elif "permission" in error_msg.lower():
            print(f"ERROR: Permission denied accessing {layer_type}: {e}")
            print(f"       Your Earth Engine account may not have access to this dataset")
        elif "400" in error_msg or "400 Bad Request" in error_msg:
            print(f"ERROR: Bad request to Earth Engine (400): {e}")
            print(f"       This may indicate invalid visualization parameters or geometry")
        else:
            print(f"ERROR: Could not get {layer_type} {year} image: {e}")
        return None, None



def create_pdf_map_figure(
    geom_bounds,
    layer_name,
    layer_type,
    year=None,
    drawn_features=None,
    territory_geojson=None,
    buffer_geojson=None,
    title=None,
    figsize=(12, 10),
    ee_geometry=None
):
    """
    Create a static matplotlib figure for a map with layers and polygons
    
    Args:
        geom_bounds: Tuple of (min_lat, min_lon, max_lat, max_lon) for map extent
        layer_name: Name of the layer being displayed
        layer_type: Type of layer ('mapbiomas', 'hansen', 'satellite', 'maps')
        year: Year for the layer (if applicable)
        drawn_features: List of GeoJSON polygon features
        territory_geojson: GeoJSON of territory boundary
        buffer_geojson: GeoJSON of buffer zone boundary
        title: Title for the map
        figsize: Figure size in inches
        ee_geometry: Earth Engine geometry for fetching raster data
    
    Returns:
        matplotlib.figure.Figure object
    """
    
    fig, ax = plt.subplots(figsize=figsize, dpi=100)
    
    # Set map extent
    min_lon, min_lat, max_lon, max_lat = geom_bounds
    ax.set_xlim(min_lon, max_lon)
    ax.set_ylim(min_lat, max_lat)
    ax.set_aspect('equal')
    
    # Add basemap background
    basemap_added = False
    
    # Try to get basemap tiles - use Google Maps (respect usage policy)
    print(f"DEBUG: Creating map for layer_type={layer_type}, year={year}, bounds=({min_lat:.4f}, {min_lon:.4f}) to ({max_lat:.4f}, {max_lon:.4f})")
    
    # Determine which basemap to use (skip for mapbiomas and hansen - they have their own layers)
    if layer_type in ['mapbiomas', 'hansen']:
        # For MapBiomas and Hansen, don't use basemap - show only the EE layer
        print(f"DEBUG: Skipping basemap for {layer_type} - showing EE layer only")
        basemap, basemap_bounds = None, None
    elif layer_type == 'satellite':
        print(f"DEBUG: Fetching Google satellite basemap...")
        basemap, basemap_bounds = get_basemap_image(geom_bounds, 'google_satellite')
    else:
        # For all other types (maps, etc), use Google Maps roadmap as background
        print(f"DEBUG: Fetching Google Maps basemap...")
        basemap, basemap_bounds = get_basemap_image(geom_bounds, 'google')
    
    if basemap and basemap_bounds:
        try:
            basemap_min_lat, basemap_min_lon, basemap_max_lat, basemap_max_lon = basemap_bounds
            print(f"DEBUG: Displaying basemap at extent: ({basemap_min_lat:.4f}, {basemap_min_lon:.4f}) to ({basemap_max_lat:.4f}, {basemap_max_lon:.4f})")
            ax.imshow(basemap, extent=[basemap_min_lon, basemap_max_lon, basemap_min_lat, basemap_max_lat], 
                     origin='upper', zorder=0, alpha=0.95)
            basemap_added = True
        except Exception as e:
            print(f"WARNING: Could not display basemap: {e}")
    
    # Add Earth Engine raster data on top of basemap (for MapBiomas and Hansen only)
    if ee_geometry and year and layer_type in ['mapbiomas', 'hansen']:
        try:
            print(f"DEBUG: Fetching {layer_type} raster data for year {year}...")
            result = get_ee_layer_image(geom_bounds, ee_geometry, layer_type, year)
            if result and isinstance(result, tuple):
                ee_img, ee_bounds = result
                print(f"DEBUG: Got {layer_type} image, size: {ee_img.size}")
                print(f"DEBUG: Displaying {layer_type} overlay with full opacity...")
                # Display the image covering the tile bounds (not the original bounds)
                ee_min_lat, ee_min_lon, ee_max_lat, ee_max_lon = ee_bounds
                ax.imshow(ee_img, extent=[ee_min_lon, ee_max_lon, ee_min_lat, ee_max_lat], 
                         origin='upper', zorder=1, alpha=1.0)
                print(f"DEBUG: {layer_type} overlay displayed successfully")
            else:
                print(f"WARNING: {layer_type} image is None - fetch may have failed")
        except Exception as e:
            print(f"WARNING: Could not display {layer_name} EE data: {e}")
            import traceback
            traceback.print_exc()
    
    # Add background color only if no basemap was added
    if not basemap_added:
        if layer_type == 'satellite':
            ax.set_facecolor('#87ceeb')  # Sky blue for satellite
        elif layer_type == 'maps':
            ax.set_facecolor('#f0f0f0')  # Light gray for maps
        else:
            ax.set_facecolor('#e8f4f8')  # Light cyan for data layers
    
    # Add grid
    ax.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax.set_xlabel('Longitude', fontsize=10)
    ax.set_ylabel('Latitude', fontsize=10)
    
    # Add territory boundary if provided
    if territory_geojson:
        try:
            territory_geom = territory_geojson
            if territory_geom.get('type') == 'Polygon':
                coords = territory_geom.get('coordinates', [[]])[0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    ax.plot(lons, lats, 'purple', linewidth=2, label='Territory Boundary', alpha=0.7)
                    ax.fill(lons, lats, color='purple', alpha=0.05)
        except Exception as e:
            print(f"Warning: Could not plot territory: {e}")
    
    # Add buffer zone boundary if provided
    if buffer_geojson:
        try:
            buffer_geom = buffer_geojson
            if buffer_geom.get('type') == 'Polygon':
                coords = buffer_geom.get('coordinates', [[]])[0]
                if coords:
                    lons = [c[0] for c in coords]
                    lats = [c[1] for c in coords]
                    ax.plot(lons, lats, 'blue', linewidth=2, label='Buffer Zone', alpha=0.8, linestyle='--')
                    ax.fill(lons, lats, color='blue', alpha=0.08)
            elif buffer_geom.get('type') == 'MultiPolygon':
                # Handle multipolygon buffers
                for poly_coords in buffer_geom.get('coordinates', []):
                    if poly_coords:
                        coords = poly_coords[0] if poly_coords else []
                        if coords:
                            lons = [c[0] for c in coords]
                            lats = [c[1] for c in coords]
                            ax.plot(lons, lats, 'blue', linewidth=2, alpha=0.8, linestyle='--')
                            ax.fill(lons, lats, color='blue', alpha=0.08)
        except Exception as e:
            print(f"Warning: Could not plot buffer zone: {e}")
    
    # Add drawn polygons
    if drawn_features:
        for idx, feature in enumerate(drawn_features):
            try:
                geom = feature.get('geometry', {})
                if geom.get('type') == 'Polygon':
                    coords = geom.get('coordinates', [[]])[0]
                    if coords:
                        lons = [c[0] for c in coords]
                        lats = [c[1] for c in coords]
                        ax.plot(lons, lats, 'blue', linewidth=2.5, label=f'Polygon {idx + 1}' if idx == 0 else '')
                        ax.fill(lons, lats, color='blue', alpha=0.1)
                        
                        # Add polygon label at center
                        center_lon = np.mean(lons)
                        center_lat = np.mean(lats)
                        ax.text(center_lon, center_lat, str(idx + 1), 
                               fontsize=12, fontweight='bold', color='blue',
                               ha='center', va='center',
                               bbox=dict(boxstyle='circle', facecolor='white', alpha=0.8))
            except Exception as e:
                print(f"Warning: Could not plot polygon {idx}: {e}")
    
    # Add scale bar
    add_scale_bar(ax, min_lon, min_lat, max_lon, max_lat)
    
    # Title and labels
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    else:
        ax.set_title(f'{layer_name} Map with Polygon Overlays', fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # Add metadata
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ax.text(0.01, 0.01, f'Generated: {timestamp}\nYvynation - Land Cover Analysis',
           transform=ax.transAxes, fontsize=8, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    return fig


def add_scale_bar(ax, min_lon, min_lat, max_lon, max_lat):
    """
    Add a scale bar to the map
    
    Args:
        ax: matplotlib axis object
        min_lon, min_lat, max_lon, max_lat: Map bounds
    """
    # Calculate scale (rough approximation: 1 degree ≈ 111 km at equator)
    map_width = (max_lon - min_lon) * 111 * np.cos(np.radians((max_lat + min_lat) / 2))
    
    # Determine scale bar length
    if map_width > 100:
        scale_length = 50  # km
    elif map_width > 50:
        scale_length = 25  # km
    elif map_width > 20:
        scale_length = 10  # km
    else:
        scale_length = 5  # km
    
    # Convert to degrees
    scale_degrees = scale_length / (111 * np.cos(np.radians((max_lat + min_lat) / 2)))
    
    # Draw scale bar in lower left
    scale_x = min_lon + (max_lon - min_lon) * 0.05
    scale_y = min_lat + (max_lat - min_lat) * 0.05
    
    ax.plot([scale_x, scale_x + scale_degrees], [scale_y, scale_y], 'k-', linewidth=2)
    ax.plot([scale_x, scale_x], [scale_y - (max_lat - min_lat) * 0.01, scale_y + (max_lat - min_lat) * 0.01], 'k-', linewidth=2)
    ax.plot([scale_x + scale_degrees, scale_x + scale_degrees], [scale_y - (max_lat - min_lat) * 0.01, scale_y + (max_lat - min_lat) * 0.01], 'k-', linewidth=2)
    
    ax.text(scale_x + scale_degrees / 2, scale_y + (max_lat - min_lat) * 0.02, 
           f'{scale_length} km', ha='center', fontsize=9, fontweight='bold')


def get_geometry_bounds(features, territory_geojson=None):
    """
    Calculate bounding box from features and territory
    Prioritizes territory bounds if available since that's usually what we want to focus on
    
    Args:
        features: List of GeoJSON features or single feature
        territory_geojson: Territory GeoJSON (optional, usually prioritized)
    
    Returns:
        Tuple of (min_lon, min_lat, max_lon, max_lat)
    """
    lats = []
    lons = []
    
    # Add territory bounds FIRST (they're usually the main feature)
    if territory_geojson:
        try:
            # Handle both direct GeoJSON and nested geometry
            territory_geom = territory_geojson
            if isinstance(territory_geom, dict):
                if territory_geom.get('type') == 'Polygon':
                    coords = territory_geom.get('coordinates', [[]])[0]
                    lons.extend([c[0] for c in coords])
                    lats.extend([c[1] for c in coords])
                elif territory_geom.get('type') == 'MultiPolygon':
                    for polygon in territory_geom.get('coordinates', []):
                        coords = polygon[0]
                        lons.extend([c[0] for c in coords])
                        lats.extend([c[1] for c in coords])
                elif territory_geom.get('type') == 'FeatureCollection':
                    for feature in territory_geom.get('features', []):
                        geom = feature.get('geometry', {})
                        if geom.get('type') == 'Polygon':
                            coords = geom.get('coordinates', [[]])[0]
                            lons.extend([c[0] for c in coords])
                            lats.extend([c[1] for c in coords])
        except Exception as e:
            print(f"Warning: Could not extract territory bounds: {e}")
    
    # Add polygon bounds
    if features:
        if not isinstance(features, list):
            features = [features]
        
        for feature in features:
            try:
                geom = feature.get('geometry', {})
                if geom.get('type') == 'Polygon':
                    coords = geom.get('coordinates', [[]])[0]
                    lons.extend([c[0] for c in coords])
                    lats.extend([c[1] for c in coords])
            except:
                pass
    
    if not lats or not lons:
        # Default bounds (Brazil area) - [lon, lat] order
        return (-75, -35, -35, 5)
    
    # Add 10% buffer
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    lat_buffer = (max_lat - min_lat) * 0.1 if (max_lat - min_lat) > 0 else 1
    lon_buffer = (max_lon - min_lon) * 0.1 if (max_lon - min_lon) > 0 else 1
    
    return (min_lon - lon_buffer, min_lat - lat_buffer, 
            max_lon + lon_buffer, max_lat + lat_buffer)


def bounds_to_ee_geometry(geom_bounds):
    """
    Convert bounds tuple to ee.Geometry.Rectangle
    
    Args:
        geom_bounds: Tuple of (min_lon, min_lat, max_lon, max_lat) in [lon, lat] order
    
    Returns:
        ee.Geometry.Rectangle
    """
    try:
        min_lon, min_lat, max_lon, max_lat = geom_bounds
        return ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
    except Exception as e:
        print(f"Warning: Could not create EE geometry: {e}")
        return None


def create_pdf_map_set(drawn_features, territories_geojson, active_layers, buffer_geojson=None):
    """
    Create a set of static PDF maps for all active layers
    
    Args:
        drawn_features: List of drawn polygon GeoJSON features
        territories_geojson: Territory boundary GeoJSON
        active_layers: Dict of {layer_name: {year: bool}}
        buffer_geojson: Optional buffer zone boundary GeoJSON
    
    Returns:
        Dict of {map_name: matplotlib.figure.Figure}
    """
    map_figures = {}
    
    print(f"DEBUG: Starting PDF map creation")
    print(f"DEBUG: drawn_features: {len(drawn_features) if drawn_features else 0}")
    print(f"DEBUG: territories_geojson: {territories_geojson is not None}")
    print(f"DEBUG: buffer_geojson: {buffer_geojson is not None}")
    
    # Check if we have anything to map
    if not drawn_features and not territories_geojson:
        st.warning("No polygons or territory selected. Cannot create maps.")
        return map_figures
    
    # Get bounds from features and territory combined
    geom_bounds = get_geometry_bounds(drawn_features, territories_geojson)
    print(f"DEBUG: Map bounds calculated: {geom_bounds}")
    
    # Create EE geometry for fetching raster data
    ee_geometry = bounds_to_ee_geometry(geom_bounds)
    print(f"DEBUG: EE geometry created: {ee_geometry is not None}")
    
    # Convert territory to proper GeoJSON if it's an EE geometry
    territory_geojson = None
    if territories_geojson:
        try:
            if isinstance(territories_geojson, dict):
                territory_geojson = territories_geojson
            else:
                # Try to get info if it's an EE object
                territory_geojson = territories_geojson.getInfo() if hasattr(territories_geojson, 'getInfo') else territories_geojson
        except Exception as e:
            print(f"Warning: Could not convert territory to GeoJSON: {e}")
            territory_geojson = None
    
    # Create maps for each active layer
    if active_layers:
        mapbiomas_years = active_layers.get('mapbiomas_layers', {})
        hansen_years = active_layers.get('hansen_layers', {})
        
        # MapBiomas maps
        for year, is_active in mapbiomas_years.items():
            if is_active:
                map_name = f"MapBiomas_{year}"
                try:
                    fig = create_pdf_map_figure(
                        geom_bounds=geom_bounds,
                        layer_name=f"MapBiomas {year}",
                        layer_type='mapbiomas',
                        year=year,
                        drawn_features=drawn_features,
                        territory_geojson=territory_geojson,
                        buffer_geojson=buffer_geojson,
                        title=f"MapBiomas Land Cover Classification - {year}",
                        ee_geometry=ee_geometry
                    )
                    map_figures[map_name] = fig
                    st.info(f"✓ Created {map_name}")
                except Exception as e:
                    st.warning(f"Could not create {map_name}: {e}")
        
        # Hansen maps
        for year, is_active in hansen_years.items():
            if is_active:
                map_name = f"Hansen_{year}"
                try:
                    fig = create_pdf_map_figure(
                        geom_bounds=geom_bounds,
                        layer_name=f"Hansen Global Forest Change {year}",
                        layer_type='hansen',
                        year=year,
                        drawn_features=drawn_features,
                        territory_geojson=territory_geojson,
                        buffer_geojson=buffer_geojson,
                        title=f"Hansen Forest Change - {year}",
                        ee_geometry=ee_geometry
                    )
                    map_figures[map_name] = fig
                    st.info(f"✓ Created {map_name}")
                except Exception as e:
                    st.warning(f"Could not create {map_name}: {e}")
    
    # Add territory analysis layers if available
    if st.session_state.get('territory_analysis_image') and st.session_state.get('territory_analysis_source'):
        try:
            analysis_year = int(st.session_state.get('territory_year', 2020))
            analysis_source = st.session_state.get('territory_analysis_source', 'Unknown')
            map_name = f"{analysis_source}_Analysis_{analysis_year}"
            
            # Create analysis map
            fig = create_pdf_map_figure(
                geom_bounds=geom_bounds,
                layer_name=f"{analysis_source} Analysis {analysis_year}",
                layer_type=analysis_source.lower(),
                year=analysis_year,
                drawn_features=drawn_features,
                territory_geojson=territory_geojson,
                buffer_geojson=buffer_geojson,
                title=f"{analysis_source} Territory Analysis - {analysis_year}",
                ee_geometry=ee_geometry
            )
            map_figures[map_name] = fig
            st.info(f"✓ Created {map_name}")
        except Exception as e:
            st.warning(f"Could not create analysis map: {e}")
    
    # Add second year analysis if available
    if st.session_state.get('territory_analysis_image_year2') and st.session_state.get('territory_analysis_source_year2'):
        try:
            analysis_year2 = int(st.session_state.get('territory_year2', 2020))
            analysis_source2 = st.session_state.get('territory_analysis_source_year2', 'Unknown')
            map_name2 = f"{analysis_source2}_Analysis_{analysis_year2}"
            
            # Create second analysis map
            fig = create_pdf_map_figure(
                geom_bounds=geom_bounds,
                layer_name=f"{analysis_source2} Analysis {analysis_year2}",
                layer_type=analysis_source2.lower(),
                year=analysis_year2,
                drawn_features=drawn_features,
                territory_geojson=territory_geojson,
                buffer_geojson=buffer_geojson,
                title=f"{analysis_source2} Territory Analysis - {analysis_year2}",
                ee_geometry=ee_geometry
            )
            map_figures[map_name2] = fig
            st.info(f"✓ Created {map_name2}")
        except Exception as e:
            st.warning(f"Could not create second analysis map: {e}")
    
    # Always create satellite and maps basemaps
    try:
        fig_satellite = create_pdf_map_figure(
            geom_bounds=geom_bounds,
            layer_name="Satellite Reference",
            layer_type='satellite',
            drawn_features=drawn_features,
            territory_geojson=territory_geojson,
            buffer_geojson=buffer_geojson,
            title="Satellite Basemap - Location Reference"
        )
        map_figures['Satellite_Basemap'] = fig_satellite
        st.info("✓ Created Satellite_Basemap")
    except Exception as e:
        st.warning(f"Could not create Satellite_Basemap: {e}")
    
    try:
        fig_maps = create_pdf_map_figure(
            geom_bounds=geom_bounds,
            layer_name="Google Maps Reference",
            layer_type='maps',
            drawn_features=drawn_features,
            territory_geojson=territory_geojson,
            buffer_geojson=buffer_geojson,
            title="Maps Basemap - Location Reference"
        )
        map_figures['GoogleMaps_Basemap'] = fig_maps
        st.info("✓ Created GoogleMaps_Basemap")
    except Exception as e:
        st.warning(f"Could not create GoogleMaps_Basemap: {e}")
    
    return map_figures


def render_map_export_section():
    """
    Render UI section for exporting maps with polygon overlays and territory boundaries
    Shows options to export maps as PDFs and PNGs
    """
    st.divider()
    st.subheader("🗺️ Export Maps")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.caption(
            "Export static maps showing drawn polygons and/or territory boundaries "
            "with scale bars. Available formats: PDF (all layer types) and PNG (MapBiomas/Hansen)"
        )
    
    with col2:
        has_polygons = st.session_state.get('all_drawn_features') is not None and len(st.session_state.get('all_drawn_features', [])) > 0
        has_territory = st.session_state.get('territory_geom') is not None
        
        if has_polygons:
            st.success(f"✓ {len(st.session_state.get('all_drawn_features', []))} polygon(s)")
        if has_territory:
            st.success(f"✓ Territory selected")
        if not has_polygons and not has_territory:
            st.warning("⚠ Draw polygons or select a territory")
    
    # Tab interface for PDF and PNG exports
    tab_pdf, tab_png = st.tabs(["📄 PDF Export (All Layers)", "🖼️ PNG Export (MapBiomas/Hansen)"])
    
    with tab_pdf:
        # PDF Export section
        export_button_col, info_col = st.columns([1, 2])
        
        with export_button_col:
            if st.button("📊 Prepare PDF Maps", key="prepare_maps_export", width="stretch"):
                has_polygons = st.session_state.get('all_drawn_features') is not None and len(st.session_state.get('all_drawn_features', [])) > 0
                has_territory = st.session_state.get('territory_geom') is not None
                
                if not has_polygons and not has_territory:
                    st.error("Please draw at least one polygon or select a territory")
                else:
                    with st.spinner("Creating PDF maps..."):
                        try:
                            # Get active layers
                            active_layers = {
                                'mapbiomas_layers': st.session_state.get('mapbiomas_layers', {}),
                                'hansen_layers': st.session_state.get('hansen_layers', {})
                            }
                            
                            # Get territories - can be from territories_geojson or territory_geom
                            territories_geojson = None
                            if st.session_state.get('territory_geom'):
                                try:
                                    # territory_geom is an EE geometry, get its info
                                    territories_geojson = st.session_state.get('territory_geom').getInfo()
                                except:
                                    territories_geojson = st.session_state.get('territories_geojson')
                            else:
                                territories_geojson = st.session_state.get('territories_geojson')
                            
                            # Get buffer geometry if available
                            buffer_geojson = None
                            if st.session_state.get('current_buffer_for_analysis') and st.session_state.get('buffer_geometries'):
                                buffer_name = st.session_state.current_buffer_for_analysis
                                if buffer_name in st.session_state.buffer_geometries:
                                    try:
                                        buffer_geom = st.session_state.buffer_geometries[buffer_name]
                                        buffer_geojson = buffer_geom.getInfo()
                                        print(f"DEBUG: Buffer GeoJSON obtained: {buffer_geojson is not None}")
                                    except Exception as e:
                                        print(f"Warning: Could not convert buffer to GeoJSON: {e}")
                                        buffer_geojson = None
                            
                            # Create maps
                            map_figures = create_pdf_map_set(
                                drawn_features=st.session_state.get('all_drawn_features') if has_polygons else None,
                                territories_geojson=territories_geojson if has_territory else None,
                                active_layers=active_layers,
                                buffer_geojson=buffer_geojson
                            )
                            
                            # Store in session state for export
                            st.session_state.prepared_map_exports = map_figures
                            st.session_state.export_maps_ready = True
                            
                            if map_figures:
                                st.success(f"✓ {len(map_figures)} PDF map(s) prepared!")
                            else:
                                st.warning("No maps were successfully created.")
                        except Exception as e:
                            st.error(f"Error preparing maps: {str(e)}")
                            import traceback
                            traceback.print_exc()
        
        with info_col:
            st.caption(
                "Creates PDF maps: MapBiomas, Hansen, Satellite, and Maps "
                "basemaps with your polygons and scale bars"
            )
    
    with tab_png:
        # PNG Export section for MapBiomas and Hansen
        from png_export import export_pngs_direct, create_pngs_zip
        
        st.caption("Export MapBiomas and Hansen layers as PNG images (organized in zip)")
        
        # Get available MapBiomas and Hansen years
        mapbiomas_years = [int(y) for y, enabled in st.session_state.get('mapbiomas_layers', {}).items() if enabled]
        hansen_years = [int(y) for y, enabled in st.session_state.get('hansen_layers', {}).items() if enabled]
        
        if not mapbiomas_years and not hansen_years:
            st.info("Enable MapBiomas or Hansen layers from the analysis tabs to export as PNG")
        else:
            # Single button to export all layers as a zip
            if st.button("📦 Export All PNGs as ZIP", key="export_all_pngs_zip", width="stretch"):
                has_polygons = st.session_state.get('all_drawn_features') is not None and len(st.session_state.get('all_drawn_features', [])) > 0
                has_territory = st.session_state.get('territory_geom') is not None
                
                if not has_polygons and not has_territory:
                    st.error("Please draw at least one polygon or select a territory")
                else:
                    with st.spinner("Exporting Earth Engine layers as PNGs..."):
                        try:
                            # Get geometry data
                            drawn_features = st.session_state.get('all_drawn_features') if has_polygons else None
                            territory_geojson = None
                            
                            if has_territory and st.session_state.get('territory_geom'):
                                territory_geom = st.session_state.get('territory_geom')
                                try:
                                    territory_geojson = territory_geom.getInfo()
                                except:
                                    pass
                            
                            # Batch export all PNGs directly
                            png_results = export_pngs_direct(
                                drawn_features=drawn_features,
                                territory_geojson=territory_geojson,
                                mapbiomas_years=mapbiomas_years,
                                hansen_years=hansen_years
                            )
                            
                            # Check if any images were successfully exported
                            total_images = len(png_results.get('mapbiomas', {})) + len(png_results.get('hansen', {}))
                            if total_images == 0:
                                st.error("No images were successfully exported. Check Earth Engine access and dataset availability.")
                            else:
                                # Create zip file
                                zip_bytes = create_pngs_zip(png_results)
                                
                                # Offer zip download
                                st.download_button(
                                    label="✅ Download PNG ZIP",
                                    data=zip_bytes,
                                    file_name="EE_Layers_PNGs.zip",
                                    mime="application/zip",
                                    key="download_pngs_zip"
                                )
                                
                                st.success("✓ All PNGs exported successfully!")
                                st.info(f"📦 ZIP contains: {len(png_results.get('mapbiomas', {}))} MapBiomas + {len(png_results.get('hansen', {}))} Hansen layers")
                        except Exception as e:
                            st.error(f"Error exporting PNGs: {str(e)}")
                            import traceback
                            traceback.print_exc()
