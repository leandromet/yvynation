# Export Function Fix - Summary of Changes

## Problem Identified
The export zip file was missing Hansen GLAD and Hansen GFC (Global Forest Change) CSV files for polygon analysis. Only MapBiomas data was being exported completely.

### Root Causes:
1. **Hansen GLAD Bug**: The export function tried to extract `result['df']` but Hansen comparison results store the data in `result['df_comp']` (the comparison dataframe)
2. **GFC Not Captured**: GFC analysis results stored in `hansen_gfc_results_original` and `hansen_gfc_results_buffer` were never captured for export
3. **Documentation Outdated**: The "What's included" section didn't mention GFC exports

## Solutions Implemented

### 1. Fixed Hansen GLAD Data Extraction (export_utils.py)
**Location**: `capture_current_analysis_exports()` function, line ~331

**Changed from**:
```python
if isinstance(result, dict) and 'df' in result:
    polygon_analyses[polygon_idx]['hansen'] = {
        'data': result['df'],  # ❌ Wrong key - df doesn't exist
```

**Changed to**:
```python
if isinstance(result, dict) and 'df_comp' in result:
    polygon_analyses[polygon_idx]['hansen'] = {
        'data': result['df_comp'],  # ✅ Correct - comparison dataframe
        'df1_disp': result.get('df1_disp'),  # Year 1 display data
        'df2_disp': result.get('df2_disp'),  # Year 2 display data
```

### 2. Added GFC Analysis Capture (export_utils.py)
**Location**: `capture_current_analysis_exports()` function, after line ~387

**Added new code block**:
```python
# Capture Hansen GFC (Global Forest Change) analysis results
for area_prefix in ['original', 'buffer']:
    gfc_session_key = f'hansen_gfc_results_{area_prefix}'
    gfc_results = session_state.get(gfc_session_key)
    
    if gfc_results and isinstance(gfc_results, dict):
        # Captures 'tree_cover', 'tree_loss', 'tree_gain' DataFrames
        # and stores them organized by area_prefix
```

### 3. Updated Zip Creation for GFC Data (export_utils.py)
**Location**: `create_export_zip()` function, line ~134

**Added special handling for nested GFC structure**:
```python
# Handle nested GFC analysis data (tree_cover, tree_loss, tree_gain)
if analysis_type in ['gfc', 'gfc_buffer']:
    if isinstance(results, dict):
        for gfc_component, gfc_data in results.items():
            # gfc_component: 'tree_cover', 'tree_loss', 'tree_gain'
            if gfc_data.get('data') is not None:
                df = gfc_data['data']
                if isinstance(df, pd.DataFrame):
                    csv_str = df.to_csv(index=False)
                    prefix = 'gfc_buffer' if analysis_type == 'gfc_buffer' else 'gfc'
                    zf.writestr(f'{polygon_folder}/{prefix}_{gfc_component}.csv', csv_str)
```

### 4. Updated Export Documentation (export_utils.py)
**Location**: `render_export_section()` function, line ~496

**Added to "📍 Polygon Results" section**:
```
| `gfc_tree_cover.csv` | **NEW:** Hansen GFC tree cover distribution (% canopy, 0-100) |
| `gfc_tree_loss.csv` | **NEW:** Hansen GFC tree loss by year (2001-2024) |
| `gfc_tree_gain.csv` | **NEW:** Hansen GFC tree gain (2000-2012) |
| `gfc_buffer_tree_cover.csv` | **NEW:** GFC tree cover for buffer zone (if analyzed) |
| `gfc_buffer_tree_loss.csv` | **NEW:** GFC tree loss for buffer zone (if analyzed) |
| `gfc_buffer_tree_gain.csv` | **NEW:** GFC tree gain for buffer zone (if analyzed) |
```

**Added GFC status indicators to export metadata table**:
```
| **Hansen/GLAD comparison** | {"✅" if _has_hansen_comparison else "—"} |
| **Hansen GFC (Polygon)** | {"✅ tree cover, loss, gain" if _has_gfc_original else "—"} |
| **Hansen GFC (Buffer)** | {"✅ tree cover, loss, gain" if _has_gfc_buffer else "—"} |
```

## Files Modified
- ✅ `/home/leandromb/google_eengine/yvynation/export_utils.py`

## Expected Changes to Zip File Structure

### Before Fix ❌
```
polygons/polygon_1/
├── mapbiomas_transitions.json
├── mapbiomas_data.csv
├── mapbiomas_comparison.csv
└── [only MapBiomas files]
```

### After Fix ✅
```
polygons/polygon_1/
├── mapbiomas_transitions.json
├── mapbiomas_data.csv
├── mapbiomas_comparison.csv
├── hansen_comparison.csv (NEW - was broken before)
├── hansen_transitions.json
├── gfc_tree_cover.csv (NEW)
├── gfc_tree_loss.csv (NEW)
├── gfc_tree_gain.csv (NEW)
├── gfc_buffer_tree_cover.csv (NEW - if buffer analyzed)
├── gfc_buffer_tree_loss.csv (NEW - if buffer analyzed)
└── gfc_buffer_tree_gain.csv (NEW - if buffer analyzed)
```

## Testing the Fix

1. **Create a polygon** on the map
2. **Run GFC analysis**: "Hansen GFC Analysis" tab → "Analyze GFC" button
3. **Run Hansen comparison**: "Hansen/GLAD Analysis" tab → Compare two years
4. **Export**: Click "📦 Export All Data & Visualizations"
5. **Verify**: Check the zip file for CSV files in `polygons/polygon_1/`
   - Should see `gfc_tree_cover.csv`, `gfc_tree_loss.csv`, `gfc_tree_gain.csv`
   - Should see `hansen_comparison.csv` with proper data
   - Should see `hansen_transitions.json`

## Benefits
✅ **Complete Data Export**: All three analysis types (MapBiomas, Hansen GLAD, Hansen GFC) now properly exported  
✅ **Prevents Data Loss**: GFC analyses no longer lost when exporting  
✅ **Transparent Documentation**: Users can see what's included before exporting  
✅ **Buffer Zone Support**: GFC data captured for both original polygon and buffer zone  
✅ **Fixed Bug**: Hansen comparison was broken but now exports correct `df_comp` data
