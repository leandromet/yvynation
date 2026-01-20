# Hansen/GLAD Land Cover Class Consolidation Guide

## Overview

The Hansen/GLAD global land cover dataset contains 256 classes with intermediate resolution classes that can be grouped into broader categories for simplified analysis. This guide documents the consolidation strategy and implementation.

## Problem

The original Hansen legend has **257 classes (0-255)** with very granular distinctions:
- **Unvegetated/Bare Ground**: 0-5 and 120-125 (6 classes each) for Terra firma and Wetland
- **Dense Short Vegetation**: 6-50 and 126-170 (45 classes each) - differentiated by % bare ground
- **Open Tree Cover**: 51-74 and 171-194 (24 classes each) - differentiated by tree height (3m to >25m)
- **Dense Tree Cover**: 75-91 and 195-211 (17 classes each) - differentiated by tree height (10m to >25m)
- **Tree Cover Gain**: 92-115 and 212-235 (24 classes each) - differentiated by tree height
- **Other classes**: Water, Ice, Cropland, Built-up, etc.

This granularity makes visualizations cluttered and analysis difficult when you just want to see major land cover changes.

## Solution: Class Consolidation

Classes are grouped into **12 consolidated categories** while maintaining information about the original detailed classes:

### Consolidated Classes

| Class | Original Ranges | Count | Purpose |
|-------|-----------------|-------|---------|
| **Unvegetated** | 0-5, 120-125 | 12 | Bare ground, desert, barren areas |
| **Dense Short Vegetation** | 6-50, 126-170 | 90 | Shrubland, grassland, sparse vegetation |
| **Open Tree Cover** | 51-74, 171-194 | 48 | Trees 3-25m height, low canopy density |
| **Dense Tree Cover** | 75-91, 195-211 | 34 | Trees 10-25m height, high canopy density |
| **Tree Cover Gain** | 92-115, 212-235 | 48 | Afforestation, forest regeneration |
| **Tree Cover Loss** | 116, 236 | 2 | Deforestation, forest loss |
| **Built-up** | 240-249 | 10 | Urban areas, infrastructure |
| **Water** | 250 | 1 | Lakes, rivers, water bodies |
| **Ice** | 251 | 1 | Permanent ice, glaciers |
| **Cropland** | 252 | 1 | Agricultural areas |
| **Ocean** | 254 | 1 | Oceanic areas |
| **No Data** | 255 | 1 | Missing or invalid data |

## Implementation Files

### 1. **legend_consolidated.csv**
- Mapping table with columns: `Map value`, `Original Class IDs`, `Strata`, `Consolidated Class`, `Sub-class`
- Contains all 256 original classes with their consolidated grouping
- Use for reference and documentation

### 2. **hansen_consolidated_mapping.py**
- `HANSEN_CONSOLIDATED_MAPPING`: Dictionary mapping pixel values (0-255) to consolidated class names
- `HANSEN_CONSOLIDATED_COLORS`: Color codes for each consolidated class (hex format)
- `HANSEN_CLASS_GROUPING`: Lists original classes grouped by consolidated category

### 3. **hansen_consolidated_utils.py**
Helper functions for working with consolidated classes:

```python
# Get consolidated class for a pixel value
get_consolidated_class(class_id) -> str

# Get color for consolidated class
get_consolidated_color(class_id) -> str

# Aggregate histogram DataFrame to consolidated classes
aggregate_to_consolidated(df_original) -> DataFrame

# Compare two years with consolidation
create_comparison_dataframe(df_start, df_end, year1, year2, use_consolidated=True) -> DataFrame

# Generate summary statistics
summarize_consolidated_stats(df_consolidated, year=None) -> dict
```

### 4. **config.py (updated)**
- `HANSEN_CONSOLIDATED_MAPPING`: Added mapping dictionary
- `HANSEN_CONSOLIDATED_COLORS`: Added color definitions

## Usage Examples

### Basic Consolidation

```python
from hansen_consolidated_utils import get_consolidated_class, aggregate_to_consolidated

# Get consolidated class for a pixel
pixel_value = 42
class_name = get_consolidated_class(pixel_value)  # Returns "Dense Short Vegetation"

# Aggregate histogram results
df_consolidated = aggregate_to_consolidated(df_original_histogram)
# Returns DataFrame with consolidated classes and summed areas
```

### Visualization with Consolidated Classes

```python
import matplotlib.pyplot as plt
from hansen_consolidated_utils import aggregate_to_consolidated, get_consolidated_color

# Consolidate the data
df_cons = aggregate_to_consolidated(df_original)

# Get colors for each class
colors = [get_consolidated_color(row['Class_ID']) for _, row in df_cons.iterrows()]

# Plot
fig, ax = plt.subplots()
ax.barh(df_cons['Consolidated_Class'], df_cons['Area_ha'], color=colors)
ax.set_xlabel('Area (hectares)')
ax.set_title('Hansen Land Cover Distribution (Consolidated)')
plt.tight_layout()
```

### Year-to-Year Comparison

```python
from hansen_consolidated_utils import create_comparison_dataframe

# Compare 2000 vs 2020 with consolidation
comparison = create_comparison_dataframe(
    df_2000_histogram, 
    df_2020_histogram, 
    start_year=2000, 
    end_year=2020, 
    use_consolidated=True
)

# Shows: 2000_area, 2020_area, Change (ha), % Change
print(comparison.sort_values('Change (ha)', key=abs, ascending=False))
```

### Summary Statistics

```python
from hansen_consolidated_utils import summarize_consolidated_stats, aggregate_to_consolidated

df_cons = aggregate_to_consolidated(df_histogram)
summary = summarize_consolidated_stats(df_cons, year=2020)

print(f"Total area: {summary['total_area_ha']} ha")
print(f"Largest class: {summary['largest_class']}")
print(f"Class breakdown: {summary['class_breakdown']}")
```

## Integration with hansen_analysis.py

The hansen_analysis.py module can be updated to provide:

1. **Toggle between detailed and consolidated views**:
   ```python
   show_consolidated = st.checkbox("Show consolidated classes")
   if show_consolidated:
       df_display = aggregate_to_consolidated(df_original)
   ```

2. **Consolidated comparison analysis**:
   ```python
   comparison = create_comparison_dataframe(df_start, df_end, year1, year2, use_consolidated=True)
   ```

3. **Better visualization with semantic grouping**:
   - Color coding by consolidated class
   - Simplified legend with fewer items
   - Focus on major land cover changes

## Benefits

1. **Cleaner Visualizations**: 12 consolidated classes vs 256 original classes
2. **Easier Analysis**: Group related classes for broader trends
3. **Better Storytelling**: Focus on major land cover changes (forest gain/loss, vegetation changes)
4. **Detail When Needed**: Can still access original pixel values for detailed analysis
5. **Consistent Grouping**: Same consolidation used across all analyses
6. **Color Consistency**: Uniform colors for consolidated classes across all charts

## File Relationships

```
config.py
├── HANSEN_CONSOLIDATED_MAPPING (dictionary)
└── HANSEN_CONSOLIDATED_COLORS (dictionary)

hansen_consolidated_mapping.py
├── HANSEN_CONSOLIDATED_MAPPING (detailed dictionary)
├── HANSEN_CONSOLIDATED_COLORS (detailed colors)
└── HANSEN_CLASS_GROUPING (class lists)

hansen_consolidated_utils.py
├── get_consolidated_class()
├── get_consolidated_color()
├── aggregate_to_consolidated()
├── create_comparison_dataframe()
└── summarize_consolidated_stats()

hansen_analysis.py
└── Uses hansen_consolidated_utils for advanced analysis

legend_consolidated.csv
└── Reference table for all mappings
```

## Future Enhancements

1. **Custom Consolidation**: Allow users to define their own groupings
2. **Multi-level Hierarchy**: Support parent/child class relationships
3. **Change Matrix**: Track transitions between specific classes
4. **Uncertainty Quantification**: Track confidence of classifications
5. **Temporal Smoothing**: Filter noise in multi-year sequences

## References

- **Hansen/GLAD Dataset**: projects/glad/GLCLU2020/v2/LCLUC_*year*
- **Original Legend**: legend_0.csv
- **Consolidated Legend**: legend_consolidated.csv
