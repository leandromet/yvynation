"""
Hansen Global Forest Change (GFC) analysis utilities.
Extracts tree cover, loss, and gain analysis from Earth Engine data.
"""

import ee
import pandas as pd


def analyze_hansen_gfc_geometry(geometry, area_name="Area"):
    """
    Analyze Hansen Global Forest Change data for a given geometry.
    Analyzes tree cover 2000, tree loss years, and tree gain.
    
    Returns:
        dict: Dictionary with 'tree_cover', 'tree_loss', 'tree_gain' DataFrames
    """
    try:
        from config import HANSEN_GFC_DATASET
        dataset = ee.Image(HANSEN_GFC_DATASET)
        
        results = {}
        
        print(f"[GFC Analysis] Starting analysis for {area_name}")
        print(f"[GFC] Geometry type: {type(geometry)}")
        try:
            geom_info = geometry.getInfo()
            print(f"[GFC] Geometry info: {str(geom_info)[:200]}")
        except Exception as ge:
            print(f"[GFC] Could not get geometry info: {ge}")
        
        # Analyze Tree Cover 2000 (0-100% canopy cover)
        try:
            print("[GFC Analysis] Processing tree cover 2000...")
            tree_cover = dataset.select(['treecover2000'])
            cover_stats = tree_cover.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            print(f"[GFC] Cover stats type: {type(cover_stats)}, value: {cover_stats}")
            
            if cover_stats and isinstance(cover_stats, dict):
                # Try different key names
                histogram = None
                if 'treecover2000' in cover_stats:
                    histogram = cover_stats['treecover2000']
                    print(f"[GFC] Found 'treecover2000' key with {len(histogram) if isinstance(histogram, dict) else '?'} entries")
                else:
                    # Try first available dict key
                    print(f"[GFC] Available keys in cover_stats: {list(cover_stats.keys())}")
                    for key, value in cover_stats.items():
                        print(f"[GFC] Checking key '{key}': type={type(value)}, is_dict={isinstance(value, dict)}")
                        if isinstance(value, dict) and len(value) > 0:
                            histogram = value
                            print(f"[GFC] Using histogram key: {key} with {len(histogram)} entries")
                            break
                
                if histogram and isinstance(histogram, dict) and len(histogram) > 0:
                    records = []
                    for percent_str, count in histogram.items():
                        percent = int(percent_str)
                        area_ha = count * 0.09
                        records.append({
                            'Percent_Cover': percent,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    if records:
                        results['tree_cover'] = pd.DataFrame(records).sort_values('Percent_Cover')
                        print(f"[GFC Analysis] Tree cover: {len(records)} data points ✓")
                    else:
                        print(f"[GFC] Histogram had entries but created no records")
                else:
                    print(f"[GFC] No valid histogram found. histogram={histogram}, type={type(histogram)}, len={len(histogram) if isinstance(histogram, dict) else 'N/A'}")
            else:
                print(f"[GFC] cover_stats is not a dict or is None: {cover_stats}")
        except Exception as cover_err:
            print(f"[GFC Analysis] Exception - tree cover analysis failed: {cover_err}")
            import traceback
            traceback.print_exc()
        
        # Analyze Tree Loss Year (0=no loss, 1-24=year 2001-2024)
        try:
            print("[GFC Analysis] Processing tree loss...")
            tree_loss = dataset.select(['lossyear'])
            loss_stats = tree_loss.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            print(f"[GFC] Loss stats type: {type(loss_stats)}, keys: {list(loss_stats.keys()) if isinstance(loss_stats, dict) else 'N/A'}")
            
            if loss_stats and isinstance(loss_stats, dict):
                # Try different key names
                histogram = None
                if 'lossyear' in loss_stats:
                    histogram = loss_stats['lossyear']
                    print(f"[GFC] Found 'lossyear' key with {len(histogram) if isinstance(histogram, dict) else '?'} entries")
                else:
                    # Try first available dict key
                    print(f"[GFC] Available keys in loss_stats: {list(loss_stats.keys())}")
                    for key, value in loss_stats.items():
                        print(f"[GFC] Checking key '{key}': type={type(value)}, is_dict={isinstance(value, dict)}")
                        if isinstance(value, dict) and len(value) > 0:
                            histogram = value
                            print(f"[GFC] Using histogram key: {key} with {len(histogram)} entries")
                            break
                
                if histogram and isinstance(histogram, dict) and len(histogram) > 0:
                    records = []
                    for year_code_str, count in histogram.items():
                        year_code = int(year_code_str)
                        if year_code == 0:
                            year_label = 'No Loss'
                        else:
                            year_label = f'{2000 + year_code}'
                        area_ha = count * 0.09
                        records.append({
                            'Year_Code': year_code,
                            'Year': year_label,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    if records:
                        results['tree_loss'] = pd.DataFrame(records).sort_values('Year_Code')
                        print(f"[GFC Analysis] Tree loss: {len(records)} data points ✓")
                    else:
                        print(f"[GFC] Histogram had entries but created no records")
                else:
                    print(f"[GFC] No valid histogram found for loss")
            else:
                print(f"[GFC] loss_stats is not a dict or is None")
        except Exception as loss_err:
            print(f"[GFC Analysis] Exception - tree loss analysis failed: {loss_err}")
            import traceback
            traceback.print_exc()
        
        # Analyze Tree Gain (0=no gain, 1=gain 2000-2012)
        try:
            print("[GFC Analysis] Processing tree gain...")
            tree_gain = dataset.select(['gain'])
            gain_stats = tree_gain.reduceRegion(
                reducer=ee.Reducer.frequencyHistogram(),
                geometry=geometry,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            print(f"[GFC] Gain stats type: {type(gain_stats)}, keys: {list(gain_stats.keys()) if isinstance(gain_stats, dict) else 'N/A'}")
            
            if gain_stats and isinstance(gain_stats, dict):
                # Try different key names
                histogram = None
                if 'gain' in gain_stats:
                    histogram = gain_stats['gain']
                    print(f"[GFC] Found 'gain' key with {len(histogram) if isinstance(histogram, dict) else '?'} entries")
                else:
                    # Try first available dict key
                    print(f"[GFC] Available keys in gain_stats: {list(gain_stats.keys())}")
                    for key, value in gain_stats.items():
                        print(f"[GFC] Checking key '{key}': type={type(value)}, is_dict={isinstance(value, dict)}")
                        if isinstance(value, dict) and len(value) > 0:
                            histogram = value
                            print(f"[GFC] Using histogram key: {key} with {len(histogram)} entries")
                            break
                
                if histogram and isinstance(histogram, dict) and len(histogram) > 0:
                    records = []
                    for gain_code_str, count in histogram.items():
                        gain_code = int(gain_code_str)
                        gain_label = 'Gain (2000-2012)' if gain_code == 1 else 'No Gain'
                        area_ha = count * 0.09
                        records.append({
                            'Gain_Code': gain_code,
                            'Status': gain_label,
                            'Pixels': int(count),
                            'Area_ha': round(area_ha, 2)
                        })
                    if records:
                        results['tree_gain'] = pd.DataFrame(records).sort_values('Gain_Code')
                        print(f"[GFC Analysis] Tree gain: {len(records)} data points ✓")
                    else:
                        print(f"[GFC] Histogram had entries but created no records")
                else:
                    print(f"[GFC] No valid histogram found for gain")
            else:
                print(f"[GFC] gain_stats is not a dict or is None")
        except Exception as gain_err:
            print(f"[GFC Analysis] Exception - tree gain analysis failed: {gain_err}")
            import traceback
            traceback.print_exc()
        
        print(f"[GFC Analysis] Final results keys: {list(results.keys())}, total entries: {sum(len(v) for v in results.values())}")
        
        if results and len(results) > 0:
            print(f"[GFC Analysis] SUCCESS: Completed with {len(results)} datasets: {list(results.keys())}")
            return results
        else:
            print(f"[GFC Analysis] FAILED: No data returned. Results dict is {'empty' if not results else 'populated but all empty'}")
            print(f"[GFC Analysis] Dumping all stats for debugging:")
            print(f"  - cover_stats was retrieved")
            print(f"  - loss_stats was retrieved")
            print(f"  - gain_stats was retrieved")
            print(f"[GFC Analysis] Check Streamlit terminal for detailed debug messages")
            return None
    except Exception as e:
        print(f"[GFC Analysis] FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None
