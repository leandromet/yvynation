#!/usr/bin/env python3
"""
Direct test script for PNG export from Earth Engine.
Run this to debug the export process.
"""

import ee
import urllib.request
from PIL import Image
import io
from config import MAPBIOMAS_PALETTE, HANSEN_DATASETS

# Initialize Earth Engine
print("Initializing Earth Engine...")
try:
    ee.Initialize()
    print("✓ EE initialized")
except Exception as e:
    print(f"✗ EE init failed: {e}")
    exit(1)

# Define a small test region (Bacurizinho area from your previous exports)
min_lon, min_lat, max_lon, max_lat = -58.9065, -12.3112, -58.8010, -12.2057
print(f"\nTest region: ({min_lat}, {min_lon}) to ({max_lat}, {max_lon})")

# Create geometry
geometry = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
print(f"✓ Geometry created")

# Calculate scale
lon_span = max_lon - min_lon
max_pixels_width = max(512, min(2000, int(111000 * lon_span / 10)))
scale = max(10, int(lon_span * 111000 / max_pixels_width))
print(f"Scale: {scale}m per pixel, target width: {max_pixels_width}px")

# Test MapBiomas 2023
print("\n" + "="*60)
print("Testing MapBiomas 2023")
print("="*60)

try:
    # Get asset
    print("Loading MapBiomas asset...")
    mapbiomas_asset = 'projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1'
    mapbiomas_image = ee.Image(mapbiomas_asset)
    print("✓ Asset loaded")
    
    # Select band
    print("Selecting classification_2023 band...")
    image = mapbiomas_image.select('classification_2023')
    print("✓ Band selected")
    
    # Clip
    print("Clipping to geometry...")
    clipped = image.clip(geometry)
    print("✓ Clipped")
    
    # Visualize
    print("Applying visualization...")
    palette_str = ','.join(MAPBIOMAS_PALETTE)
    print(f"  Palette has {len(MAPBIOMAS_PALETTE)} colors")
    vis_params = {
        'min': 0,
        'max': 62,
        'palette': palette_str
    }
    visualized = clipped.visualize(**vis_params)
    print("✓ Visualization applied")
    
    # Get download URL
    print("Generating download URL...")
    url = visualized.getDownloadURL({
        'region': geometry,
        'scale': scale,
        'format': 'png',
        'maxPixels': 1e8
    })
    print(f"✓ URL generated: {url[:100]}...")
    
    # Download
    print("Downloading image...")
    response = urllib.request.urlopen(url, timeout=30)
    img = Image.open(response)
    print(f"✓ Image downloaded: {img.size}, mode: {img.mode}")
    
    # Check image data
    import numpy as np
    img_array = np.array(img)
    print(f"  Array shape: {img_array.shape}")
    print(f"  Array dtype: {img_array.dtype}")
    print(f"  Min value: {img_array.min()}, Max value: {img_array.max()}")
    print(f"  Non-zero pixels: {np.count_nonzero(img_array)}")
    
    # Save to disk
    output_file = '/tmp/mapbiomas_2023_test.png'
    img.save(output_file)
    print(f"✓ Saved to {output_file}")
    
    # Check file size
    import os
    file_size = os.path.getsize(output_file)
    print(f"  File size: {file_size} bytes")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test complete!")
print("="*60)
