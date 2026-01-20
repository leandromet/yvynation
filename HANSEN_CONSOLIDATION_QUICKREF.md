# Hansen Class Consolidation - Quick Reference

## What Was Done

✅ **Created consolidated mapping for Hansen/GLAD land cover classes**
- Original: 256 classes (0-255) with very fine granularity
- Consolidated: 12 major classes for cleaner analysis

## Files Created/Modified

| File | Purpose |
|------|---------|
| `legend_consolidated.csv` | Reference table mapping all 256 classes to 12 consolidated groups |
| `hansen_consolidated_mapping.py` | Python dictionaries for class mapping and colors |
| `hansen_consolidated_utils.py` | Utility functions for consolidation operations |
| `config.py` | Updated with consolidated mapping definitions |
| `HANSEN_CONSOLIDATION_GUIDE.md` | Detailed documentation and usage guide |

## Consolidated Classes (12)

```
1. Unvegetated          - Bare ground, desert (original: 0-5, 120-125)
2. Dense Short Veg      - Shrubland, grassland (original: 6-50, 126-170)
3. Open Tree Cover      - Sparse trees 3-25m (original: 51-74, 171-194)
4. Dense Tree Cover     - Dense trees 10-25m (original: 75-91, 195-211)
5. Tree Cover Gain      - Afforestation (original: 92-115, 212-235)
6. Tree Cover Loss      - Deforestation (original: 116, 236)
7. Built-up             - Urban areas (original: 240-249)
8. Water                - Lakes/rivers (original: 250)
9. Ice                  - Glaciers (original: 251)
10. Cropland            - Agricultural (original: 252)
11. Ocean               - Ocean areas (original: 254)
12. No Data             - Missing values (original: 255)
```

## Key Functions

```python
from hansen_consolidated_utils import *

# Convert individual class
get_consolidated_class(42)  # → "Dense Short Vegetation"

# Convert colors
get_consolidated_color(42)  # → "#B8D4A8"

# Aggregate histogram
df_cons = aggregate_to_consolidated(df_histogram)

# Compare years with consolidation
comparison = create_comparison_dataframe(
    df_2000, df_2020, 2000, 2020, use_consolidated=True
)

# Get summary statistics
stats = summarize_consolidated_stats(df_cons, year=2020)
```

## Integration Tips

### In hansen_analysis.py
```python
from hansen_consolidated_utils import (
    aggregate_to_consolidated,
    get_consolidated_color,
    create_comparison_dataframe
)

# Use consolidated in analysis
df_consolidated = aggregate_to_consolidated(df_original)

# Better charts with unified colors
colors = [get_consolidated_color(cid) for cid in df_consolidated['Class_ID']]
```

### Visualization
```python
import matplotlib.pyplot as plt

# Plot with consolidated classes
df_cons = aggregate_to_consolidated(df_original)
fig, ax = plt.subplots(figsize=(10, 8))
colors = [get_consolidated_color(cid) for cid in df_cons['Class_ID']]
ax.barh(df_cons['Consolidated_Class'], df_cons['Area_ha'], color=colors)
ax.set_xlabel('Area (hectares)')
ax.set_title('Hansen Land Cover (Consolidated)')
```

## Color Palette

| Class | Hex Color | Appearance |
|-------|-----------|-----------|
| Unvegetated | #D4D4A8 | Tan/beige |
| Dense Short Veg | #B8D4A8 | Light tan-green |
| Open Tree Cover | #90C090 | Light green |
| Dense Tree Cover | #1F8040 | Dark green |
| Tree Cover Gain | #4CAF50 | Forest green |
| Tree Cover Loss | #E53935 | Red |
| Built-up | #FF6B35 | Orange-red |
| Water | #2196F3 | Blue |
| Ice | #E0F7FA | Light cyan |
| Cropland | #FFD700 | Gold |
| Ocean | #0D47A1 | Dark blue |
| No Data | #CCCCCC | Gray |

## Example: Multi-Year Comparison

```python
from hansen_consolidated_utils import create_comparison_dataframe

# Get Hansen data for 2000 and 2020
df_2000 = hansen_histogram_to_dataframe(stats_2000, 2000)
df_2020 = hansen_histogram_to_dataframe(stats_2020, 2020)

# Create comparison with consolidation
comparison = create_comparison_dataframe(
    df_2000, df_2020, 
    start_year=2000, 
    end_year=2020, 
    use_consolidated=True
)

# View largest changes
print(comparison.sort_values('Change (ha)', key=abs, ascending=False).head(10))

# Output:
#                          2000    2020  Change (ha)  % Change
# Dense Tree Cover      50000.0 45000.0    -5000.00    -10.00
# Tree Cover Gain       10000.0 15000.0     5000.00     50.00
# Built-up              2000.0  3000.0     1000.00     50.00
```

## Testing the Setup

```python
# Quick test to verify everything works
from hansen_consolidated_utils import get_consolidated_class, aggregate_to_consolidated
from config import HANSEN_CONSOLIDATED_MAPPING, HANSEN_CONSOLIDATED_COLORS

# Test mappings
assert get_consolidated_class(42) == "Dense Short Vegetation"
assert get_consolidated_class(75) == "Dense Tree Cover"
assert get_consolidated_class(240) == "Built-up"

# Test colors
assert HANSEN_CONSOLIDATED_COLORS["Dense Tree Cover"] == "#1F8040"

print("✅ All consolidation files working correctly!")
```

## Next Steps

1. **Update hansen_analysis.py** to use consolidation functions
2. **Add toggle in UI** for detailed vs consolidated views
3. **Update visualizations** to use consolidated class colors
4. **Enhance comparison analysis** with consolidation by default
5. **Add summary statistics** showing consolidated class breakdown

---
**Date**: January 20, 2026 | **Status**: Implementation Complete
