# Class 48 Mapping Fix - Detailed Class Names Update

## Problem Identified
- **Class 48** was incorrectly mapped to **Stratum 6 (wetland)**
- According to **legend_glcluc.csv**, class 48 is **">25m trees"** - dense tree cover
- Plots and data tables were showing class 48 as "wetland" instead of "tree cover"

## Root Cause
The class-to-stratum mapping in `hansen_reference_mapping.py` had an error:
```python
# WRONG:
48: 6,  # Was mapped to wetland

# CORRECT:
48: 5,  # Should be dense and tall tree cover
```

## Solution Implemented

### 1. Created `hansen_labels.py` ✅
- **Purpose**: Central source of truth for all 256 Hansen class descriptions from legend_glcluc.csv
- **Content**: 
  - `HANSEN_LABELS`: Complete mapping of class ID to detailed description
  - `HANSEN_LABELS_SHORT`: Shorter versions for compact display
- **Coverage**: All 256 Hansen classes with accurate names from official GLCLUC legend

### 2. Fixed `hansen_reference_mapping.py` ✅
- **Corrected Classes 25-48**: All tree cover classes now properly map to **Stratum 5** (dense and tall tree cover)
  - Classes 25-48 represent tree heights from 3m to >25m
  - All should be in Stratum 5, not scattered across different strata
  
- **Specific Fix for Class 48**:
  ```python
  # Before: 48: 6 (wetland) ❌
  # After:  48: 5 (dense and tall tree cover) ✅
  ```

- **Added Comments**: Clarified that this mapping is based on legend_glcluc.csv categorization

### 3. Updated `config.py` ✅
- **Removed**: Old incomplete HANSEN_LABELS dictionary (30 entries)
- **Added Import**: `from hansen_labels import HANSEN_LABELS, HANSEN_LABELS_SHORT`
- **Result**: Now uses complete 256-class labels from hansen_labels.py

### 4. No Changes Needed
- `hansen_analysis.py`: Already uses HANSEN_LABELS from config - works automatically
- `plotting_utils.py`: Already handles class aggregation - works automatically
- `streamlit_app.py`: No changes needed

## Data Display Updates

### Before (WRONG):
```
Class 48: "wetland" (Stratum 6)
```

### After (CORRECT):
```
Class 48: ">25m trees" (Stratum 5: dense and tall tree cover)
```

## Files Modified
1. **Created**: `hansen_labels.py` (256 detailed class descriptions)
2. **Updated**: `hansen_reference_mapping.py` (fixed class 48 mapping)
3. **Updated**: `config.py` (import from hansen_labels.py)

## Testing & Verification

### ✅ Verified
- Class 48 now maps to Stratum 5 (dense and tall tree cover)
- Label displays as ">25m trees"
- All tree classes 25-48 correctly group into Stratum 5
- Data tables show correct category for class 48
- Plots aggregate class 48 with other tree cover classes

### Class Examples
```
Class 0:  "Terra Firma - 3% short vegetation cover" → Stratum 1 (bare ground)
Class 10: "43% short vegetation cover"              → Stratum 7 (water)
Class 30: "8m trees"                                → Stratum 5 (dense trees)
Class 48: ">25m trees"                              → Stratum 5 (dense trees) ✅
Class 60: "Wetland"                                 → Stratum 6 (wetland)
```

## Legend Reference
All class descriptions now come directly from `legend_glcluc.csv`:
- **Column 2**: Map value (class ID 0-255)
- **Column 3**: General class
- **Column 6**: Sub-class/detailed description

For example, class 48:
- General: (empty, uses previous)
- Sub-class: ">25m trees"
- Color: #065106 (dark green)
- **Correct Category**: Tree Cover (3m to >25m heights)

## Impact on Visualizations
- **Maps**: No change (already using GLCLUC colors)
- **Plots**: Now show correct class names and groupings
- **Data Tables**: Now display correct categories
- **Territory Analysis**: Class 48 aggregates with dense tree cover, not wetland

## Production Ready ✅
All changes have been tested and verified. The app now correctly:
1. Maps class 48 to tree cover (not wetland)
2. Displays detailed class names from legend_glcluc.csv
3. Groups classes by correct strata
4. Maintains visual consistency across all visualizations
