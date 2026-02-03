# Yvynation Export - Folder Organization Guide

## Overview
The "Export All" feature packages all analysis results into a downloadable ZIP file with **organized folder hierarchy** so you can work with individual polygon and territory results independently.

---

## ZIP File Structure

```
yvynation_export_[territory]_[timestamp].zip
│
├── metadata.json                    # Analysis parameters, dates, data sources
├── geometries.geojson              # All drawn polygons + territory boundary (WGS84)
│
├── polygons/                        # Individual polygon analysis results
│   ├── polygon_1/
│   │   ├── mapbiomas_data.csv       # MapBiomas class frequency per year
│   │   ├── mapbiomas_figure1.png    # MapBiomas comparison chart
│   │   ├── mapbiomas_figure2.png    # MapBiomas class distribution
│   │   ├── hansen_data.csv          # Hansen forest change data
│   │   ├── hansen_figure1.png       # Hansen gains/losses chart
│   │   └── hansen_figure2.png       # Hansen trend visualization
│   │
│   ├── polygon_2/                   # (same structure if multiple polygons analyzed)
│   │   ├── mapbiomas_data.csv
│   │   ├── mapbiomas_figure*.png
│   │   └── ...
│   │
│   └── polygon_N/
│
└── territory/
    └── [Territory_Name]/            # Territory-specific results
        ├── analysis_2023.csv        # Territory composition by class
        ├── analysis_2022.csv        # (if comparing years)
        ├── comparison_data.csv      # Year-over-year comparison
        ├── territory_comparison.png # Class distribution chart
        ├── territory_gains_losses.png
        ├── territory_change_percentage.png
        └── ...
```

---

## Folder Organization

### Root Level Files

| File | Contents | Format |
|------|----------|--------|
| `metadata.json` | Analysis parameters, timestamps, data sources, years analyzed | JSON |
| `geometries.geojson` | All drawn polygons + territory boundary | GeoJSON (WGS84/EPSG:4326) |

### `polygons/` Folder
- **Purpose**: Stores analysis results for each individually drawn polygon
- **Organization**: One subfolder per polygon (`polygon_1`, `polygon_2`, etc.)
- **Contents per polygon**:
  - MapBiomas analysis (if analyzed):
    - `mapbiomas_data.csv` - Class frequency over years
    - `mapbiomas_figure*.png` - Visualization charts
  - Hansen analysis (if analyzed):
    - `hansen_data.csv` - Forest change metrics
    - `hansen_figure*.png` - Change visualizations
- **Why**: Allows you to process different analysis types on different polygons without mixing results

### `territory/` Folder
- **Purpose**: Stores analysis results for the selected indigenous territory
- **Organization**: Subfolder named after territory (`[Territory_Name]/`)
- **Contents**:
  - `analysis_[year].csv` - Territory composition data
  - `comparison_[year].csv` - Change metrics between years
  - `territory_*.png` - All territory visualization charts
- **Why**: Separates territory results from polygon results for clear isolation

---

## Usage Scenarios

### Scenario 1: Single Polygon + Territory Analysis
```
📦 yvynation_export_Marãnon_20240115_143022.zip
├── metadata.json
├── geometries.geojson
├── polygons/
│   └── polygon_1/
│       ├── mapbiomas_data.csv
│       └── mapbiomas_figure1.png
└── territory/
    └── Marãnon/
        ├── analysis_2023.csv
        └── territory_comparison.png
```

### Scenario 2: Multiple Polygons + Territory
```
📦 yvynation_export_Marãnon_20240115_143022.zip
├── metadata.json
├── geometries.geojson
├── polygons/
│   ├── polygon_1/          # First polygon analysis
│   │   ├── mapbiomas_*.csv
│   │   ├── mapbiomas_*.png
│   │   ├── hansen_*.csv
│   │   └── hansen_*.png
│   ├── polygon_2/          # Second polygon analysis
│   │   └── ...
│   └── polygon_3/          # (etc.)
└── territory/
    └── Marãnon/
        └── ...
```

### Scenario 3: Concurrent Multiple Analyses
```
Run simultaneously:
  → MapBiomas on Polygon 1 → results go to polygons/polygon_1/
  → Hansen on Polygon 1 → results go to polygons/polygon_1/
  → Territory analysis → results go to territory/[name]/
  → MapBiomas on Polygon 2 → results go to polygons/polygon_2/

All isolated in their respective folders ✓
```

---

## Opening Exported Files

### GeoJSON in GIS Software
1. **QGIS**: Drag `geometries.geojson` onto canvas (auto-reprojects if needed)
2. **ArcGIS**: Import → Add Data → Select `geometries.geojson`
3. **Leaflet/Web**: Read as JSON in mapping library
4. **Python**: `geopandas.read_file('geometries.geojson')`

### CSV Data in Excel/Sheets
- Open any `*.csv` file directly
- Organize by polygon or territory subfolder
- All data already cleaned and formatted

### PNG Visualizations
- View in any image viewer
- Use in presentations/reports
- All generated at 150 DPI (publication quality)

### Metadata
- Open `metadata.json` in text editor
- Shows analysis parameters, dates, data sources
- Useful for documentation/reproducibility

---

## What Gets Exported?

### Automatically Included
✅ All drawn polygons (as GeoJSON)  
✅ Selected territory boundary (as GeoJSON)  
✅ All analysis results (CSVs)  
✅ All generated visualizations (PNGs)  
✅ Analysis metadata and timestamps  

### Per Analysis Type
**MapBiomas Analysis** (if run):
- Class frequency data (CSV)
- Area comparison charts (PNG)
- Class distribution visualizations (PNG)

**Hansen Analysis** (if run):
- Forest change metrics (CSV)
- Gains/losses charts (PNG)
- Change trends over time (PNG)

**Territory Analysis** (if run):
- Composition analysis (CSV)
- Comparison across years (CSV)
- Distribution charts (PNG)
- Change percentage visualizations (PNG)

---

## File Naming Convention

### Data Files
- `mapbiomas_data.csv` - MapBiomas analysis
- `hansen_data.csv` - Hansen analysis
- `analysis_[year].csv` - Territory composition
- `comparison_[year].csv` - Year comparison

### Figure Files
- `[analysis_type]_figure[N].png` - Numbered visualizations
- `territory_[figure_type].png` - Territory-specific charts

### Territory Folders
- Space-converted to underscores: "Marãnon" → `Marãnon/`
- Slashes removed: "A / B" → `A_B/`

---

## Tips for Organization

1. **Extract to Dedicated Folder**: Create a project folder for each export
   ```bash
   mkdir -p ~/analysis_results/marãnon_jan2024/
   unzip yvynation_export_Marãnon_20240115_143022.zip -d ~/analysis_results/marãnon_jan2024/
   ```

2. **Share Specific Results**: Send only the folder you need
   ```bash
   # Share just polygon 1 results
   zip -r polygon_1_analysis.zip polygons/polygon_1/
   ```

3. **Combine Multiple Exports**: Extract multiple ZIPs, rename folders with dates
   ```bash
   polygons/
   ├── polygon_1_2024-01-15/
   ├── polygon_1_2024-02-20/
   └── polygon_1_2024-03-10/
   ```

4. **Import to GIS**: Drag `geometries.geojson` directly into QGIS, then import specific CSVs as attribute tables

---

## Troubleshooting

**Q: Some folders are empty**  
A: Only analyses actually performed are exported. If you didn't run MapBiomas on a polygon, there's no `mapbiomas_*.csv` file.

**Q: Territory folder not created**  
A: You must select a territory and run analysis. Territory-only exports require territory selection first.

**Q: File names have special characters**  
A: Territory names with spaces/slashes are converted to underscores for compatibility. Original geometry in `geometries.geojson` preserves actual names.

**Q: Why duplicate data in metadata.json and CSV headers?**  
A: Both are intentional. CSV is standalone, metadata documents the analysis parameters for reproducibility.

---

## Next Steps

1. **Extract ZIP** to your working directory
2. **Open `geometries.geojson`** in QGIS/ArcGIS to visualize spatial data
3. **Open `metadata.json`** to understand analysis parameters
4. **Use CSVs** for further analysis in spreadsheet tools
5. **Import PNGs** into reports/presentations

All files are ready to use immediately—no processing required! 🎉
