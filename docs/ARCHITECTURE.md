# Yvynation Refactored Architecture

## Overview
The application has been reorganized into modular components with a clean tab-based interface separating MapBiomas and Hansen/GLAD analysis.

## File Structure

### Core Application
- **streamlit_app.py** (345 lines)
  - Main entry point with tab-based UI
  - Session state initialization
  - Earth Engine setup and caching
  - Map creation function
  - Sidebar configuration
  - Two main tabs: MapBiomas and Hansen

### Analysis Modules

#### mapbiomas_analysis.py
Handles all MapBiomas (Brazil) specific analysis:
- `render_mapbiomas_area_analysis()` - Draw and analyze custom areas
- `render_mapbiomas_territory_analysis()` - Analyze indigenous territories
- `render_mapbiomas_multiyear_analysis()` - Compare years 1985-2023
- `render_mapbiomas_change_analysis()` - Detect land cover changes

#### hansen_analysis.py
Handles all Hansen/GLAD (Global) specific analysis:
- `render_hansen_area_analysis()` - Draw and analyze custom areas
- `hansen_histogram_to_dataframe()` - Convert histogram data to DataFrames
- `render_hansen_multiyear_analysis()` - Compare snapshots (2000-2020)
- `render_hansen_change_analysis()` - Change detection between snapshots

#### ui_components.py
Shared UI components and utilities:
- `render_map_controls()` - MapBiomas map controls
- `render_hansen_map_controls()` - Hansen map controls
- `render_map_instructions()` - Drawing tool instructions
- `render_load_button()` - Data loading button
- `render_about_section()` - About information

### Existing Modules (Unchanged)
- **app_file.py** - YvynationApp class for data management
- **analysis.py** - Analysis functions (area calculation, territory filtering)
- **plots.py** - Visualization functions
- **visualization.py** - Legend and map visualization utilities
- **config.py** - Configuration (datasets, palettes)

## Architecture Benefits

✅ **Modularity**: Each analysis type is in its own file  
✅ **Clean UI**: Tab-based separation eliminates back-and-forth switching  
✅ **Maintainability**: Smaller files are easier to debug and extend  
✅ **Reusability**: Components can be imported and used elsewhere  
✅ **Scalability**: Easy to add new data sources or analysis types  

## Session State Organization

### Core State
- `app` - YvynationApp instance
- `data_loaded` - Boolean flag
- `ee_module` - Earth Engine module reference

### Map State
- `map_center_lat/lon` - Map center coordinates
- `map_zoom` - Current zoom level
- `map_object` - Folium map instance

### Drawn Areas
- `drawn_areas` - Dictionary of drawn geometries
- `drawn_area_count` - Number of areas drawn
- `selected_drawn_area` - Currently selected area

### Analysis Results (MapBiomas)
- `drawn_area_result` - Area analysis DataFrame
- `territory_result` - Territory analysis DataFrame
- `multiyear_results` - Multi-year comparison results
- `last_analyzed_geom` - Last analyzed geometry

### Analysis Results (Hansen)
- `hansen_area_result` - Hansen area analysis DataFrame
- `hansen_area_year` - Selected Hansen year

### Layer Controls
- `split_compare_mode` - Layer comparison enabled
- `split_left/right_year` - Layer years
- `split_left/right_opacity` - Layer opacities
- `hansen_year` - Selected Hansen year

## Usage

### For Users
1. Open the app
2. Click "Load Core Data" in sidebar
3. Choose tab:
   - **MapBiomas**: Analyze Brazilian land cover (1985-2023)
   - **Hansen**: Analyze global coverage (2000-2020)
4. Draw areas on the map
5. Run analyses in the expandable sections

### For Developers
To add a new analysis type:
1. Create a new module (e.g., `my_analysis.py`)
2. Add render functions (e.g., `render_my_analysis()`)
3. Import in streamlit_app.py
4. Add to appropriate tab

To modify MapBiomas analysis:
- Edit `mapbiomas_analysis.py`

To modify Hansen analysis:
- Edit `hansen_analysis.py`

To modify shared UI:
- Edit `ui_components.py`

## Key Improvements Over Previous Version

| Aspect | Before | After |
|--------|--------|-------|
| Main file lines | 1412+ | 345 |
| Data source handling | Radio button switching | Separate tabs |
| Code organization | Single monolithic file | Modular components |
| Analysis code | Mixed with UI | Separated into modules |
| Result persistence | Needed reset logic | Automatic via tabs |
| Map switching | Complex change detection | Separate map instances |

## Testing Checklist

- [ ] Load Core Data button works
- [ ] MapBiomas tab displays map correctly
- [ ] Hansen tab displays map correctly
- [ ] Drawing areas works in both tabs
- [ ] Area analysis returns results
- [ ] Multi-year analysis works
- [ ] Change detection works
- [ ] Tab switching is smooth
- [ ] Results persist when navigating tabs
- [ ] All expanders work correctly
