"""
Debug MapBiomas Auxiliary Datasets
Queries samples from each dataset to identify issues with data fetching/interpretation.
"""

import ee
import logging
import json
from typing import Dict, List, Optional

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Earth Engine
try:
    ee.Authenticate()
except:
    pass  # Already authenticated
ee.Initialize()

# MapBiomas auxiliary datasets configuration (from config.py)
MAPBIOMAS_AUX_DATASETS = {
    "deforestation_secondary": {
        "asset": "projects/mapbiomas-public/assets/brazil/lulc/collection10_1/"
                 "mapbiomas_brazil_collection10_1_deforestation_secondary_vegetation_v3",
        "label": "Deforestation & Secondary Vegetation",
        "value_semantics": "year_value",
        "band_candidates": [
            "primary_vegetation_loss",
            "primary_vegetation_year_to_secondary",
            "deforestation_year",
            "secondary_vegetation_regrowth",
            "classification_{year}",
        ],
        "per_year": True,
        "vis": {
            "min": 1985, "max": 2024,
            "palette": ["440154", "3b528b", "21918c", "5ec962", "fde725"],
        },
    },
    "fire_scar_size": {
        "asset": "projects/mapbiomas-public/assets/brazil/fire/collection4/"
                 "mapbiomas_fire_collection4_annual_burned_scar_size_range_v1",
        "label": "Annual Burned Area (scar size)",
        "value_semantics": "class_value",
        "band_candidates": [
            "scar_size_{year}",
            "burned_area_{year}",
            "classification_{year}",
        ],
        "per_year": True,
        "vis": {
            "min": 0, "max": 5,
            "palette": ["000000", "fee08b", "fdae61", "f46d43", "d73027", "7f0000"],
        },
    },
    "fire_frequency": {
        "asset": "projects/mapbiomas-public/assets/brazil/fire/collection4/"
                 "mapbiomas_fire_collection4_fire_frequency_v1",
        "label": "Fire Frequency (1985–2024)",
        "value_semantics": "class_value",
        "band_candidates": [
            "fire_frequency_1985_2024",
            "fire_frequency",
        ],
        "per_year": False,
        "vis": {
            "min": 0, "max": 20,
            "palette": ["ffffff", "ffffb2", "fecc5c", "fd8d3c", "f03b20", "bd0026"],
        },
    },
    "fire_year_last": {
        "asset": "projects/mapbiomas-public/assets/brazil/fire/collection4/"
                 "mapbiomas_fire_collection4_year_last_fire_v1",
        "label": "Year of Last Fire",
        "value_semantics": "year_value",
        "band_candidates": [
            "classification_{year}",
            "year_last_fire_{year}",
            "year_last_fire",
        ],
        "per_year": True,
        "vis": {
            "min": 1985, "max": 2024,
            "palette": ["440154", "3b528b", "21918c", "5ec962", "fde725"],
        },
    },
    "mining_substances": {
        "asset": "projects/mapbiomas-public/assets/brazil/lulc/collection10/"
                 "mapbiomas_brazil_collection10_mining_substances_v3",
        "label": "Mining Substances",
        "value_semantics": "class_value",
        "band_candidates": [
            "mining_substances_{year}",
            "classification_{year}",
            "substance_{year}",
            "mining_{year}",
        ],
        "per_year": True,
        "vis": {
            "min": 0, "max": 10,
            "palette": [
                "000000", "9c0027", "e6194b", "f58231", "ffe119",
                "bcf60c", "3cb44b", "46f0f0", "4363d8", "911eb4", "f032e6",
            ],
        },
    },
    "agriculture_cycles": {
        "asset": "projects/mapbiomas-public/assets/brazil/lulc/collection10/"
                 "mapbiomas_brazil_collection10_agriculture_cycles_v2",
        "label": "Agriculture — Cycles per Year",
        "value_semantics": "class_value",
        "band_candidates": [
            "number_of_cycles_{year}",
            "cycles_{year}",
            "classification_{year}",
        ],
        "per_year": True,
        "vis": {
            "min": 0, "max": 3,
            "palette": ["ffffff", "ffffcc", "ffeda0", "fed976", "feb24c", "fd8d3c"],
        },
    },
}


def list_aux_bands(asset_id: str) -> List[str]:
    """List all available bands in a MapBiomas auxiliary asset."""
    try:
        image = ee.Image(asset_id)
        bands = image.bandNames().getInfo()
        return bands or []
    except Exception as e:
        logger.error(f"Failed to list bands for {asset_id}: {e}")
        return []


def query_sample_data(asset_id: str, band_name: str, geometry: ee.Geometry, year: int = None) -> Dict:
    """Query a sample of data from a MapBiomas auxiliary asset."""
    try:
        image = ee.Image(asset_id).select(band_name)
        
        # Get min/max/mean statistics
        stats = image.reduceRegion(
            reducer=ee.Reducer.minMax().combine(ee.Reducer.mean(), sharedInputs=True),
            geometry=geometry,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        # Get histogram of values
        hist = image.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=geometry,
            scale=30,
            maxPixels=1e9
        ).getInfo()
        
        return {
            "band": band_name,
            "year": year,
            "stats": stats,
            "histogram": hist.get(band_name, {}) if hist else {},
        }
    except Exception as e:
        logger.error(f"Failed to query sample data for {band_name}: {e}")
        return {"error": str(e), "band": band_name}


def debug_aux_dataset(key: str, spec: Dict, sample_geometry: ee.Geometry = None) -> Dict:
    """Debug a single auxiliary dataset."""
    print(f"\n{'='*80}")
    print(f"Debugging: {key} ({spec['label']})")
    print(f"{'='*80}")
    
    asset_id = spec["asset"]
    print(f"\n📍 Asset ID: {asset_id}")
    
    # Step 1: List available bands
    print(f"\n1️⃣  Available Bands:")
    bands = list_aux_bands(asset_id)
    if bands:
        for i, band in enumerate(bands[:20], 1):  # Show first 20
            print(f"   {i:2d}. {band}")
        if len(bands) > 20:
            print(f"   ... and {len(bands) - 20} more")
    else:
        print("   ❌ No bands found!")
        return {"key": key, "status": "failed", "reason": "No bands"}
    
    # Step 2: Check band candidates
    print(f"\n2️⃣  Band Candidates (will be tried in order):")
    candidates = spec.get("band_candidates", [])
    for i, cand in enumerate(candidates, 1):
        # If per_year, try with year 2023 as example
        if "{year}" in cand and spec.get("per_year"):
            test_name = cand.format(year=2023)
            found = "✅" if test_name in bands else "❌"
            print(f"   {i}. {cand} → {test_name} {found}")
        else:
            found = "✅" if cand in bands else "❌"
            print(f"   {i}. {cand} {found}")
    
    # Step 3: Find first matching band
    print(f"\n3️⃣  Band Resolution (2023):")
    resolved_band = None
    for cand in candidates:
        if "{year}" in cand:
            band_to_try = cand.format(year=2023)
        else:
            band_to_try = cand
        if band_to_try in bands:
            resolved_band = band_to_try
            print(f"   ✅ Resolved to: {resolved_band}")
            break
    
    if not resolved_band:
        print(f"   ❌ Could not resolve any candidate band!")
        return {"key": key, "status": "failed", "reason": "No matching band candidate"}
    
    # Step 4: Query sample data if geometry provided
    if sample_geometry is not None:
        print(f"\n4️⃣  Sample Data Query (using {resolved_band}):")
        sample = query_sample_data(asset_id, resolved_band, sample_geometry, year=2023)
        if "error" not in sample:
            print(f"   Stats: {json.dumps(sample['stats'], indent=6)}")
            hist = sample.get("histogram", {})
            if hist:
                # Show top 10 values
                sorted_vals = sorted(hist.items(), key=lambda x: x[1], reverse=True)[:10]
                print(f"   Top 10 pixel values (value: count):")
                for val, count in sorted_vals:
                    print(f"      {val}: {count}")
        else:
            print(f"   ❌ Query failed: {sample['error']}")
    
    # Step 5: Visualization parameters
    print(f"\n5️⃣  Visualization Parameters:")
    vis = spec.get("vis", {})
    print(f"   Min: {vis.get('min', 'N/A')}")
    print(f"   Max: {vis.get('max', 'N/A')}")
    print(f"   Palette: {vis.get('palette', 'N/A')}")
    print(f"   Value Semantics: {spec.get('value_semantics', 'N/A')}")
    print(f"   Per Year: {spec.get('per_year', False)}")
    
    return {
        "key": key,
        "status": "success",
        "asset": asset_id,
        "resolved_band": resolved_band,
        "available_bands": len(bands),
        "candidates_tried": len(candidates),
    }


def main():
    """Main debugging function."""
    print("\n" + "="*80)
    print("MapBiomas Auxiliary Datasets Debugger")
    print("="*80)
    
    # Sample geometry: a small test area in the Amazon
    # Using Kayapó territory area as sample
    sample_coords = [
        [-53.0, -7.5],
        [-52.0, -7.5],
        [-52.0, -8.5],
        [-53.0, -8.5],
        [-53.0, -7.5],
    ]
    sample_geometry = ee.Geometry.Polygon(sample_coords)
    
    results = []
    
    # Debug each dataset
    for key, spec in MAPBIOMAS_AUX_DATASETS.items():
        result = debug_aux_dataset(key, spec, sample_geometry=sample_geometry)
        results.append(result)
    
    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    for result in results:
        status = "✅" if result.get("status") == "success" else "❌"
        print(f"{status} {result.get('key')}: {result.get('resolved_band', 'FAILED')}")
    
    # Recommendations
    print(f"\n\n{'='*80}")
    print("RECOMMENDATIONS")
    print(f"{'='*80}\n")
    
    for result in results:
        if result.get("status") == "failed":
            print(f"⚠️  {result['key']}: {result.get('reason')}")
            print(f"   Action: Check asset path or band candidates in config.py")


if __name__ == "__main__":
    main()
