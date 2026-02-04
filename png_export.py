"""
Simple PNG export module for Earth Engine layers.
Directly exports PNGs from Earth Engine, saves to temp files, then zips them.
Replicates the working test script approach.
"""

import io
import urllib.request
import tempfile
import os
from typing import Dict, Optional
from PIL import Image
import zipfile
import ee
from map_pdf_export import get_geometry_bounds, bounds_to_ee_geometry
from config import MAPBIOMAS_PALETTE, HANSEN_DATASETS


def export_pngs_direct(
    drawn_features: list,
    territory_geojson: Optional[dict],
    mapbiomas_years: list,
    hansen_years: list
) -> Dict[str, Dict[int, str]]:
    """
    Direct export of MapBiomas and Hansen PNGs using Earth Engine.
    Saves to temporary files (same as test script).
    
    Args:
        drawn_features: List of drawn polygon features
        territory_geojson: GeoJSON of territory data
        mapbiomas_years: List of MapBiomas years to export
        hansen_years: List of Hansen years to export
    
    Returns:
        Dictionary with structure:
        {
            'mapbiomas': {year: filepath},
            'hansen': {year: filepath}
        }
    """
    results = {'mapbiomas': {}, 'hansen': {}}
    
    # Calculate bounds once
    geom_bounds = get_geometry_bounds(drawn_features, territory_geojson)
    ee_geometry = bounds_to_ee_geometry(geom_bounds)
    min_lon, min_lat, max_lon, max_lat = geom_bounds
    
    # DEBUG: Print bounds
    print(f"DEBUG - Bounds: ({min_lon}, {min_lat}) to ({max_lon}, {max_lat})")
    print(f"DEBUG - EE geometry: {ee_geometry.getInfo()}")
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    print(f"Using temp directory: {temp_dir}")
    
    # Export MapBiomas layers
    for year in mapbiomas_years:
        try:
            print(f"Exporting MapBiomas {year}...")
            
            # Get MapBiomas asset
            mapbiomas_asset = 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1'
            mapbiomas_image = ee.Image(mapbiomas_asset)
            
            # Select band and clip
            band_name = f'classification_{year}'
            image = mapbiomas_image.select(band_name).clip(ee_geometry)
            
            # Apply visualization
            palette_str = ','.join(MAPBIOMAS_PALETTE)
            vis_params = {
                'min': 0,
                'max': 62,
                'palette': palette_str
            }
            visualized = image.visualize(**vis_params)
            
            # Calculate appropriate scale to avoid size limits
            lon_span = max_lon - min_lon
            max_pixels_width = max(512, min(2000, int(111000 * lon_span / 10)))
            scale = max(10, int(lon_span * 111000 / max_pixels_width))
            
            # Download URL
            url = visualized.getDownloadURL({
                'region': ee_geometry,
                'scale': scale,
                'format': 'png',
                'maxPixels': 1e8
            })
            
            # Download and save (same as test script)
            response = urllib.request.urlopen(url, timeout=30)
            img = Image.open(response)
            
            # DEBUG: Check what we downloaded
            import numpy as np
            img_array = np.array(img)
            print(f"  DEBUG - Image mode: {img.mode}, shape: {img_array.shape}")
            print(f"  DEBUG - Min: {img_array.min()}, Max: {img_array.max()}, Non-zero: {np.count_nonzero(img_array)}")
            print(f"  DEBUG - URL: {url[:100]}...")
            
            # Save to temp file
            output_path = os.path.join(temp_dir, f'mapbiomas_{year}.png')
            img.save(output_path)
            
            # Verify saved file
            file_size = os.path.getsize(output_path)
            print(f"  DEBUG - Saved file size: {file_size} bytes")
            
            results['mapbiomas'][year] = output_path
            print(f"✓ MapBiomas {year} saved to {output_path}, size: {img.size}")
            
        except Exception as e:
            print(f"✗ Error exporting MapBiomas {year}: {str(e)}")
    
    # Export Hansen layers
    for year in hansen_years:
        try:
            print(f"Exporting Hansen {year}...")
            
            if str(year) not in HANSEN_DATASETS:
                print(f"✗ Hansen {year} not available")
                continue
            
            # Get Hansen asset
            hansen_asset = HANSEN_DATASETS[str(year)]
            hansen_image = ee.Image(hansen_asset)
            
            # Clip and visualize
            image = hansen_image.clip(ee_geometry)
            vis_params = {
                'min': 0,
                'max': 255,
                'palette': 'ffffff,1a9850,66bd63,a6d96a,d9ef8b'
            }
            visualized = image.visualize(**vis_params)
            
            # Calculate scale
            lon_span = max_lon - min_lon
            max_pixels_width = max(512, min(2000, int(111000 * lon_span / 10)))
            scale = max(10, int(lon_span * 111000 / max_pixels_width))
            
            # Download URL
            url = visualized.getDownloadURL({
                'region': ee_geometry,
                'scale': scale,
                'format': 'png',
                'maxPixels': 1e8
            })
            
            # Download and save (same as test script)
            response = urllib.request.urlopen(url, timeout=30)
            img = Image.open(response)
            
            # Save to temp file
            output_path = os.path.join(temp_dir, f'hansen_{year}.png')
            img.save(output_path)
            
            results['hansen'][year] = output_path
            print(f"✓ Hansen {year} saved to {output_path}, size: {img.size}")
            
        except Exception as e:
            print(f"✗ Error exporting Hansen {year}: {str(e)}")
    
    return results


def create_pngs_zip(png_results: Dict[str, Dict[int, str]]) -> bytes:
    """
    Create a zip file containing all PNG images from temp files.
    
    Args:
        png_results: Dictionary with mapbiomas and hansen file paths
    
    Returns:
        Zip file contents as bytes
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add MapBiomas PNGs
        for year, filepath in png_results.get('mapbiomas', {}).items():
            if filepath and os.path.exists(filepath):
                zip_file.write(filepath, arcname=f'EE_Layers/MapBiomas/mapbiomas_{year}.png')
        
        # Add Hansen PNGs
        for year, filepath in png_results.get('hansen', {}).items():
            if filepath and os.path.exists(filepath):
                zip_file.write(filepath, arcname=f'EE_Layers/Hansen/hansen_{year}.png')
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()
