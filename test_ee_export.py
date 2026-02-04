"""
Test script to export MapBiomas from Earth Engine with geolocation
"""
import ee
from config import MAPBIOMAS_PALETTE
import urllib.request
from PIL import Image
import numpy as np
from datetime import datetime

# Initialize Earth Engine
ee.Initialize()

# Define test bounds (same as in the debug output)
min_lon, min_lat = -57.5951, -14.7473
max_lon, max_lat = -57.2663, -14.4092

# Create geometry
geometry = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

# Load MapBiomas
mapbiomas_asset = 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1'
mapbiomas_image = ee.Image(mapbiomas_asset)

# Select 2002 band
image = mapbiomas_image.select('classification_2002')
clipped = image.clip(geometry)

# Create visualization parameters
palette_str = ','.join(MAPBIOMAS_PALETTE)
vis_params = {
    'min': 0,
    'max': 62,
    'palette': palette_str
}

print("Test 1: Using getDownloadURL with visualization")
print("=" * 60)

# Try getDownloadURL with visualization parameters
try:
    url = clipped.visualize(**vis_params).getDownloadURL({
        'region': geometry,
        'scale': 30,
        'format': 'png'
    })
    print(f"Download URL: {url[:150]}...")
    response = urllib.request.urlopen(url, timeout=30)
    img = Image.open(response)
    print(f"Image downloaded: size={img.size}, mode={img.mode}")
    
    # Save to disk
    img.save('/tmp/mapbiomas_test.png')
    print(f"Saved to /tmp/mapbiomas_test.png")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest 2: Using getDownloadURL with GeoTIFF format")
print("=" * 60)

# Try GeoTIFF which might preserve geolocation
try:
    url = clipped.visualize(**vis_params).getDownloadURL({
        'region': geometry,
        'scale': 30,
        'format': 'GeoTIFF'
    })
    print(f"Download URL: {url[:150]}...")
    response = urllib.request.urlopen(url, timeout=30)
    
    # Save raw bytes first
    with open('/tmp/mapbiomas_test.tif', 'wb') as f:
        f.write(response.read())
    print(f"Saved to /tmp/mapbiomas_test.tif")
    
    # Try to open with PIL
    from osgeo import gdal
    ds = gdal.Open('/tmp/mapbiomas_test.tif')
    if ds:
        print(f"GeoTIFF opened successfully")
        print(f"  Size: {ds.RasterXSize}x{ds.RasterYSize}")
        print(f"  Bands: {ds.RasterCount}")
        geotransform = ds.GetGeoTransform()
        print(f"  GeoTransform: {geotransform}")
    else:
        print("Could not open GeoTIFF with GDAL")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTest 3: Manual image + bounds approach")
print("=" * 60)

try:
    # Get the visualization as base64 data URL
    url = clipped.visualize(**vis_params).getDownloadURL({
        'region': geometry,
        'scale': 30,
        'format': 'png'
    })
    response = urllib.request.urlopen(url, timeout=30)
    img = Image.open(response)
    
    # Save with bounds metadata
    print(f"Downloaded image: {img.size}")
    print(f"Bounds: ({min_lat:.4f}, {min_lon:.4f}) to ({max_lat:.4f}, {max_lon:.4f})")
    
    # Create a simple TIFF with world file
    img_rgb = img.convert('RGB')
    img_rgb.save('/tmp/mapbiomas_test_rgb.png')
    
    # Create world file (.pgw for PNG)
    # World file format: pixel size X, rotation1, rotation2, pixel size Y, top-left X, top-left Y
    pixel_width = (max_lon - min_lon) / img.width
    pixel_height = (max_lat - min_lat) / img.height
    
    world_data = f"""{pixel_width}
0
0
{-pixel_height}
{min_lon}
{max_lat}
"""
    
    with open('/tmp/mapbiomas_test_rgb.pgw', 'w') as f:
        f.write(world_data)
    
    print(f"Saved PNG with world file to /tmp/mapbiomas_test_rgb.*")
    print(f"Pixel width: {pixel_width}")
    print(f"Pixel height: {pixel_height}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nDone! Check /tmp/ for test files")
