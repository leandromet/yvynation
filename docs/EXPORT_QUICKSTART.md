# Quick Start: Using the Export Feature

## 🎯 In 3 Steps

### Step 1: Generate Analysis Data
```
1. Draw polygons on the map, OR
2. Select an indigenous territory and click "Analyze", OR  
3. Compare multiple years
```

### Step 2: Click Export Button
Look for the **"💾 Export Analysis"** section at the top of the page:
```
┌─────────────────────────────────────────────────┐
│  💾 Export Analysis                             │
│  ┌──────────────────────────────────────────┐   │
│  │ 📦 Export All Data & Visualizations  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Step 3: Download & Use
Click the green **"📥 Download Export Package"** button that appears

## 📦 What You Get

**One ZIP file containing:**

| Item | Count | Format | Use |
|------|-------|--------|-----|
| 🗺️ Geometries | All drawn + territory | GeoJSON | Import to QGIS, ArcGIS |
| 📊 Data | Analysis tables | CSV | Excel, Python, R, SQL |
| 📈 Charts | Land cover plots | PNG (150 DPI) | Reports, presentations |
| 📋 Metadata | Analysis info | JSON | Reference, automation |

## 🎨 Example Use Cases

### Academic Paper
1. Export analysis
2. Include PNG charts in paper
3. Attach GeoJSON for data availability

### GIS Project
1. Extract `geometries.geojson`
2. Open in QGIS
3. Combine with other spatial data

### Data Analysis
1. Extract CSV files from `data/` folder
2. Load into Python, R, or Excel
3. Perform additional statistical analysis

### Policy Report
1. Export visualizations
2. Add to presentation slides
3. Include data tables in appendices

## 📋 File Details

### metadata.json
```json
{
  "export_timestamp": "2024-01-15T10:30:45.123456",
  "territory_analyzed": "Yanomami Territory",
  "analysis_year": 2023,
  "comparison_year": 2020,
  "data_source": "MapBiomas",
  "drawn_polygons_count": 2,
  "has_territory": true
}
```

### geometries.geojson
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {"name": "Drawn Polygon 1"},
      "geometry": {...}
    },
    {
      "type": "Feature", 
      "properties": {"name": "Yanomami Territory"},
      "geometry": {...}
    }
  ]
}
```

### CSV Example (data/Yanomami_analysis_2023.csv)
```
Class,Class_ID,Pixels,Area_ha,Percentage
Dense Forest,3,1234567,111111,45.2
Open Forest,4,567890,51111,20.8
Pasture,15,234567,21111,8.6
...
```

## 💻 Importing into GIS Software

### QGIS (Free)
1. **Layer** → **Add Layer** → **Add Vector Layer**
2. Select `geometries.geojson`
3. Click **Add**

### ArcGIS
1. **Insert** → **New Layer** → **GeoJSON**
2. Browse to `geometries.geojson`
3. Click **Add**

### Python/GeoPandas
```python
import geopandas as gpd
import pandas as pd

# Load geometries
gdf = gpd.read_file('geometries.geojson')
print(gdf)

# Load data
df = pd.read_csv('data/analysis_2023.csv')
print(df)
```

## ❓ FAQ

**Q: Can I edit the exported GeoJSON?**  
A: Yes! Open in any text editor or import into GIS software to modify.

**Q: How large is a typical export?**  
A: 5-30 MB depending on number of visualizations and analysis complexity.

**Q: Can I share the export with collaborators?**  
A: Yes! Everything is self-contained in the ZIP file. Just share the file.

**Q: Are the coordinates in any specific projection?**  
A: Yes, WGS84 (EPSG:4326) - standard for web mapping and most GIS software.

**Q: Can I merge multiple exports?**  
A: Yes, extract GeoJSON and CSV files from multiple ZIPs and combine them.

## 🔗 Related Documentation

- See [EXPORT_FEATURE.md](EXPORT_FEATURE.md) for detailed technical documentation
- See [EXPORT_IMPLEMENTATION.md](EXPORT_IMPLEMENTATION.md) for implementation details
- Check the app's built-in tutorial for full platform overview
