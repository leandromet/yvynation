# Yvynation Quick Start Guide

## 🚀 Installation

```bash
cd /home/leandromb/google_eengine/yvynation
pip install -r requirements.txt
```

## 📖 Usage Examples

### Example 1: Quick Map
```python
import ee
from app_file import YvynationApp

ee.Initialize(project="ee-leandromet")

app = YvynationApp()
app.load_core_data()

# Create and display map
Map = app.create_basic_map(center=[-45.3, -4.5], zoom=7)
Map.to_streamlit(height=600)
```

### Example 2: Territory Analysis
```python
# Analyze specific state
app = YvynationApp()
app.load_core_data()

results = app.analyze_territories(start_year=1985, end_year=2023)

# Display results
print(f"Area in 1985:\n{results['area_start'].head()}")
print(f"\nArea in 2023:\n{results['area_end'].head()}")
print(f"\nChanges:\n{results['comparison'].head()}")
```

### Example 3: Visualizations
```python
from plots import plot_area_comparison, plot_area_changes

# Create comparison charts
plot_area_comparison(
    results['area_start'],
    results['area_end'],
    1985, 2023,
    top_n=12,
    figsize=(16, 6)
)

# Plot changes
plot_area_changes(
    results['comparison'],
    1985, 2023,
    top_n=12
)
```

### Example 4: Territory Filtering
```python
# Maranhão state with multiple time periods
territory_map = app.create_territory_map(
    state_code='MA',
    years_to_show=[1985, 2000, 2023],
    zoom=7
)

# Specific territories
territory_map = app.create_territory_map(
    territory_names=['Bacurizinho', 'Porquinhos'],
    zoom=9
)
```

### Example 5: SPOT Data (if available)
```python
# Check and load SPOT
app.load_spot_if_available()

if app.spot_available:
    print("SPOT data available!")
    # Use SPOT classification
    from spot_module import classify_spot_ndvi
    spot_class = classify_spot_ndvi(app.spot_analytic)
else:
    print("SPOT not available (restricted access)")
    # Continue with MapBiomas
```

## 📊 Module Overview

| Module | Purpose | Key Functions |
|--------|---------|----------------|
| `config.py` | Constants & assets | MapBiomas paths, colors, labels |
| `load_data.py` | Data loading | `load_mapbiomas()`, `load_territories()` |
| `analysis.py` | Statistical analysis | Area calculations, change detection |
| `visualization.py` | Interactive maps | Map creation, layer management |
| `plots.py` | Charts & graphs | Bar charts, trends, comparisons |
| `spot_module.py` | SPOT data | Restricted access handling |
| `app_file.py` | Main app | `YvynationApp` orchestration class |

## 🎯 Key Classes & Functions

### YvynationApp Methods
```python
app = YvynationApp()

# Data loading
app.load_core_data()              # Load MapBiomas & territories
app.load_spot_if_available()      # Try to load SPOT

# Analysis
results = app.analyze_territories(start_year=1985, end_year=2023)

# Visualization
map1 = app.create_basic_map()
map2 = app.create_territory_map(state_code='MA')
app.create_comparison_visualization(results, 1985, 2023)

# Export
task = app.export_results(image, name='my_export')
```

### Analysis Functions
```python
from analysis import *

# Calculate area
df = calculate_area_by_class(image, geometry, year=2023)

# Detect change
change = calculate_land_cover_change(mapbiomas, geometry, 1985, 2023)

# Filter territories
ma_territories = filter_territories_by_state(territories, 'MA')
specific = filter_territories_by_names(territories, ['Bacurizinho'])
```

### Plotting Functions
```python
from plots import *

# Bar charts
plot_area_distribution(df, year=2023, top_n=15)
plot_area_comparison(df1, df2, 1985, 2023)
plot_area_changes(comparison_df, 1985, 2023)

# Trends
plot_temporal_trend([df1, df2, df3], [1985, 2000, 2023])

# Advanced
fig = create_sankey_transitions(transitions_dict, 1985, 2023)
```

## 🗺️ Available Land Cover Classes

Main classes (from MapBiomas Collection 9):
- 1/2/3: Forest (Natural/Formation)
- 4: Savanna Formation
- 9: Forest Plantation
- 15: Pasture
- 18/19/20: Agriculture
- 24: Urban Area
- 26: Water
- 33: Reservoir

See `config.py` for complete list (50+ classes).

## 📥 Data Sources

**MapBiomas Brazil Collection 9**
- Asset: `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1`
- Resolution: 30m
- Years: 1985-2023
- License: Creative Commons

**Indigenous Territories**
- Asset: `projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES`
- Type: Vector (FeatureCollection)
- Count: 700+ territories
- License: Public (MapBiomas Territories)

**SPOT 2008** (Restricted)
- Asset: `projects/google/brazil_forest_code/spot_bfc_ms_mosaic_v02`
- Resolution: High resolution multispectral
- Date: 2008
- Access: Request via Earth Engine

## 🐛 Troubleshooting

### "Cannot load SPOT data"
- This is expected - SPOT requires special access
- App continues to work with MapBiomas
- Request access at: https://code.earthengine.google.com

### "Timeout on large analysis"
- Reduce geometry size
- Increase `scale` parameter (30m → 60m)
- Filter to specific years
- Use smaller territories

### "Memory error with visualization"
- Reduce `top_n` in plotting functions
- Use fewer years in temporal analysis
- Clip to smaller region first

## 📚 Documentation

- `BUILD_SUMMARY.md` - Complete architecture & conversion details
- `README.md` - Project overview
- `demo_yvynation_app.ipynb` - Interactive walkthrough (START HERE!)

## 🔗 External Resources

- [Earth Engine Docs](https://developers.google.com/earth-engine)
- [geemap Documentation](https://geemap.org/)
- [MapBiomas Website](https://mapbiomas.org/)
- [Earth Engine Code Editor](https://code.earthengine.google.com)

## 💡 Pro Tips

1. **Always check collection size first**
   ```python
   size = territories.size().getInfo()
   print(f"Processing {size} territories")
   ```

2. **Use `.getInfo()` sparingly** - it blocks computation
   - Good: Call once per analysis
   - Bad: Call in loops

3. **Filter early** - reduce data before expensive operations
   ```python
   ma_territories = filter_territories_by_state(territories, 'MA')
   # Now operate on smaller collection
   ```

4. **Visualize with zoom levels**
   - National: zoom=4
   - State: zoom=7
   - Territory: zoom=10
   - Detailed: zoom=12+

## 📞 Support

For issues or questions:
1. Check `demo_yvynation_app.ipynb` for examples
2. Review `BUILD_SUMMARY.md` for architecture
3. Check module docstrings
4. Review Earth Engine documentation

---

**Ready to start?** → Open `demo_yvynation_app.ipynb` in Jupyter!
