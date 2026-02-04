# Map Export Functionality

## Overview

The Yvynation application now includes comprehensive **interactive map export** functionality. Users can export multiple map overlays with their drawn polygons, including MapBiomas layers, Hansen layers, and different basemaps (Google Satellite, Google Maps) all saved as interactive HTML files with scale bars.

## Features

### 🗺️ Map Export Types

1. **MapBiomas Overlays** - One map for each active MapBiomas year
   - Shows land cover classification with your drawn polygons
   - Interactive layer controls
   - Scale bar and measurement tools
   - Territory boundaries (if available)

2. **Hansen Global Forest Change** - One map for each active Hansen year
   - Shows forest change detection with your polygons
   - Interactive legend and controls
   - Scale bar for reference
   - Territory overlays

3. **Google Satellite Basemap**
   - Satellite imagery with your drawn polygons
   - Territory and analysis overlays
   - Scale bar for location reference
   - Perfect for ground-truthing and verification

4. **Google Maps Basemap**
   - Road map view with your polygons
   - Best for location context and accessibility
   - Includes territory boundaries
   - Scale bar and measurement tools

### 📊 What's Included in Each Map

- **Polygon Overlays**: All your drawn polygons displayed with:
  - Distinct colors (blue by default)
  - Polygon numbering (Polygon 1, 2, etc.)
  - Interactive popups with polygon information
  
- **Territory Boundaries**: Indigenous territory outlines (if analyzed)
  - Red boundaries for selected territory
  - Semi-transparent fill for visibility
  
- **Scale Bar**: Distance measurement reference
- **Measurement Tools**: Interactive measurement capabilities
- **Layer Control**: Toggle layers on/off for analysis
- **Interactive Features**: Zoom, pan, and explore

## How to Use

### Step 1: Prepare Your Data
```
1. Draw polygons on the interactive map
2. Select layers (MapBiomas years, Hansen years)
3. Optionally analyze territory (adds territory boundary)
```

### Step 2: Prepare Maps for Export
```
1. Scroll down to "🗺️ Export Maps with Polygon Overlays" section
2. Click "📊 Prepare Maps for Export" button
3. Wait for confirmation: "Maps prepared!"
```

### Step 3: Export All
```
1. Scroll to "💾 Export Analysis" section
2. Click "📦 Export All Data & Visualizations"
3. Click "📥 Download Export Package"
4. Extract ZIP file
5. Open any map file in a web browser
```

## File Structure in ZIP Export

```
yvynation_export_TERRITORY_DATE.zip
├── metadata.json
├── geometries.geojson
├── polygons/
│   └── polygon_1/
│       ├── mapbiomas_data.csv
│       ├── hansen_data.csv
│       └── *.png (visualizations)
├── territory/
│   └── TERRITORY_NAME/
│       ├── *.csv (analysis data)
│       └── *.png (visualizations)
├── figures/
│   └── *.html (Sankey diagrams)
└── maps/
    ├── MapBiomas_1985.html
    ├── MapBiomas_2023.html
    ├── Hansen_2000.html
    ├── Hansen_2020.html
    ├── Satellite_Basemap.html
    └── GoogleMaps_Basemap.html
```

## Technical Details

### New Modules

#### `map_export_components.py`
Main module for map export functionality.

**Key Functions:**

1. **`create_map_with_layer()`**
   - Creates a folium map with specific data layers
   - Adds scale bar and measurement tools
   - Includes polygon overlays
   - Parameters: layer_type, year(s), drawn_features, territories

2. **`create_export_map_set()`**
   - Creates ALL export maps at once
   - Generates maps for each active layer
   - Returns dict of {map_name: folium.Map}

3. **`render_map_export_section()`**
   - Renders UI for users to prepare maps
   - Shows polygon count
   - Provides feedback on preparation status

4. **`get_map_export_figures()`**
   - Retrieves prepared maps as HTML strings
   - Used by export functionality
   - Returns dict of {map_name: html_string}

### Updated Modules

#### `map_components.py`
Added session state storage for maps:
- Stores `map_object` for later export
- Stores `territories_geojson` for overlays
- Stores `territory_style` for consistent rendering

#### `export_utils.py`
Enhanced export functionality:
- **`create_export_zip()`** - Added `map_exports` parameter
- **`generate_export_button()`** - Now includes map export logic
- Maps are saved as interactive HTML files in `maps/` folder
- Metadata includes count of exported maps

#### `streamlit_app.py`
- Imported new `map_export_components` module
- Added `render_map_export_section()` call
- Maps are prepared before the main export button

## Usage Example

### For Analysis with Ground-Truthing

1. Draw a polygon over an area you want to verify
2. Prepare maps for export
3. Open `Satellite_Basemap.html` to see actual satellite imagery
4. Open `MapBiomas_2023.html` to see the land classification
5. Compare the two to verify accuracy

### For Report Generation

1. Analyze territory and draw comparison polygons
2. Prepare maps showing:
   - Historical MapBiomas changes
   - Hansen forest loss detection
   - Territory boundary context
3. Include in PowerPoint/PDF reports:
   - Export HTML maps (can be printed to PDF)
   - Save PNG exports of analysis figures
   - Include metadata and data tables

### For Collaborative Review

1. Prepare all maps with polygons
2. Share the `maps/` folder with colleagues
3. They can open any HTML map in their browser (no GIS software needed)
4. All maps are self-contained and interactive

## Map Features Explained

### Scale Bar
- Located at bottom-left of each map
- Shows distance in kilometers
- Helps estimate polygon size and distances

### Measurement Tool
- Click the ruler icon to measure distances
- Draw lines on map to measure
- Useful for polygon size verification

### Layer Control
- Top-right corner of map
- Toggle different data layers on/off
- Show/hide territories, polygons, etc.
- Check which layers are available

### Polygon Popups
- Click on polygon center marker (blue icon)
- Shows: "Polygon X - Type: Polygon"
- Helps identify which polygon is which

### Base Map Switching
- Different base maps show different contexts:
  - **MapBiomas/Hansen layers**: Show land cover data
  - **Satellite**: Actual satellite imagery for verification
  - **Google Maps**: Road/label reference for context

## Performance Considerations

- Maps are HTML-based (lightweight, ~1-5MB per map)
- No special software needed to view
- Works offline once downloaded
- Can be printed to PDF from browser
- Fully interactive in web browser

## Troubleshooting

### Maps not appearing in export
- Ensure "Prepare Maps for Export" was clicked
- Check that polygons are drawn on map
- Verify `export_maps_ready` is True in session state

### Maps display blank
- Check browser console for JavaScript errors
- Ensure map bounds are valid
- Try refreshing browser or re-exporting

### Maps are very slow to load
- Maps with many features can be large
- Try reducing active layers before export
- Use simpler basemaps (Google Maps vs Satellite)

### Colors not matching expected
- MapBiomas and Hansen have specific color palettes
- See map legend in reference guide
- Colors are configurable in `config.json`

## Integration Points

Maps are integrated with:
- **Polygon Analysis**: Exported maps show analyzed polygons
- **Territory Analysis**: Maps include territory boundaries
- **Layer Selection**: Exports only active layers
- **Export Workflow**: Included in ZIP alongside all other exports

## Future Enhancements

Possible improvements:
- [ ] Add heatmaps for change density
- [ ] Custom polygon coloring by analysis results
- [ ] Time-series animation across years
- [ ] Statistical overlays (mean values, etc.)
- [ ] Export as GeoTIFF for GIS software
- [ ] PDF export with annotations

## Dependencies

- `folium` - Interactive map creation
- `streamlit_folium` - Streamlit integration
- `ee` (Earth Engine) - Data layer sources
- Standard modules: `json`, `io`, `zipfile`

## Related Files

- [export_utils.py](export_utils.py) - ZIP export logic
- [map_components.py](map_components.py) - Base map building
- [sidebar_components.py](sidebar_components.py) - UI controls
- [config.json](config.json) - Colors and palettes

---

**Feature added:** February 2026
**Status:** ✅ Fully functional
**Testing:** All modules error-free and verified
