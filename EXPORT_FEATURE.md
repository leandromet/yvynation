# Export All Feature - Yvynation

## Overview

The "Export All" feature packages all analysis results, visualizations, and geographic data into a single ZIP file for download. This includes drawn polygons, selected territories, analysis data, and metadata.

## What Gets Exported

### 📂 File Structure
```
yvynation_export_[territory_name]_[timestamp].zip
├── metadata.json              # Analysis metadata and parameters
├── geometries.geojson         # All drawn polygons + territory boundary
├── data/                      # CSV files with analysis tables
│   └── [territory_name]_analysis_[year].csv
├── comparison/                # CSV files with comparison data
│   └── [territory_name]_analysis_[year2].csv
└── figures/                   # PNG images of all visualizations
    └── [figure_name].png
```

## How to Use

1. **Prepare your analysis** by:
   - Drawing polygons on the map
   - Selecting and analyzing an indigenous territory
   - Comparing multiple years if desired

2. **Click the "📦 Export All Data & Visualizations" button** located at the top of the Analysis section

3. **Download the package** when ready

## Contents of the Export

### 1. **metadata.json**
Contains analysis parameters:
- Export timestamp
- Territory name and year(s) analyzed
- Data source (MapBiomas or Hansen)
- Number of drawn polygons
- Application version and author

### 2. **geometries.geojson**
GeoJSON FeatureCollection with:
- All drawn polygons (numbered as "Drawn Polygon 1", "Drawn Polygon 2", etc.)
- Indigenous territory boundary (if analyzed)
- Timestamps for each feature

Can be imported into:
- QGIS
- ArcGIS
- Leaflet/Mapbox applications
- Any GIS software supporting GeoJSON

### 3. **data/ & comparison/ folders**
CSV files with analysis tables:
- Class IDs and names
- Pixel counts
- Area in hectares
- Percentage distribution
- Can be opened in Excel, Python, R, etc.

### 4. **figures/ folder**
High-resolution PNG images (150 DPI) of:
- Land cover distribution charts
- Comparison plots
- Change analysis graphs
- Sankey transition diagrams
- All other visualizations generated during analysis

## Use Cases

### Academic Research
- Include in research papers and presentations
- Preserve analysis methodology and parameters
- Share reproducible results with collaborators

### Policy Analysis
- Document deforestation trends in specific territories
- Create presentations with visualizations
- Export data for further statistical analysis

### GIS Analysis
- Import geometries into QGIS or ArcGIS
- Overlay with other spatial datasets
- Perform additional spatial analysis

### Data Sharing
- Send analysis results to colleagues
- Archive analysis with associated data
- Create reproducible analysis packages

## Technical Details

### Geospatial Formats
- **GeoJSON**: WGS84 (EPSG:4326) coordinate system
- **Coordinates**: Longitude, Latitude (standard GeoJSON order)
- **Projection**: Can be reprojected in QGIS or other GIS software

### Data Formats
- **CSV**: UTF-8 encoding, comma-separated
- **PNG**: 150 DPI, compressed
- **JSON**: Pretty-printed for readability

### File Size
Typical export sizes:
- Small analysis (1-2 polygons): 5-10 MB
- Territory analysis: 10-20 MB
- Multi-year comparison: 15-30 MB
- Depends on visualization complexity and number of figures

## Troubleshooting

### "No data to export yet"
- Draw at least one polygon on the map OR
- Select and analyze an indigenous territory
- The export button will activate when data is available

### Export contains fewer files than expected
- Some visualizations are only generated when:
  - Multiple years are compared (Sankey diagram)
  - Analysis is performed (land cover charts)
  - Specific conditions are met
- This is expected behavior

### Import into QGIS
1. Open QGIS
2. Layer → Add Layer → Add Vector Layer
3. Select the `geometries.geojson` file
4. Geometries will be added to your map

### Import into Python
```python
import geopandas as gpd
import pandas as pd

# Load geometries
gdf = gpd.read_file('geometries.geojson')

# Load data
df = pd.read_csv('data/territory_name_analysis_2023.csv')
```

## Limitations

- Analysis figures must be generated in the app before export
- Only currently displayed data is exported (refresh or regenerate analysis to include new visualizations)
- Maximum file size: ~100 MB (typical analysis will be much smaller)

## Future Enhancements

Potential additions to export feature:
- Interactive HTML maps
- PDF reports with analysis summary
- Raster GeoTIFF files of analyzed layers
- Statistical summaries and interpretations
- Custom branding/logos in reports

