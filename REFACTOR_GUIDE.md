# Refactored Yvynation - Setup & Quick Start

## What Changed?

The application has been completely refactored into a **tab-based architecture** with **modular Python components**:

### New Structure
```
streamlit_app.py (main entry, 345 lines)
├── mapbiomas_analysis.py (MapBiomas-specific UI rendering)
├── hansen_analysis.py (Hansen-specific UI rendering)
├── ui_components.py (shared UI components)
└── [existing modules: app_file.py, analysis.py, plots.py, config.py, etc.]
```

### Key Benefits
✅ **Cleaner Code**: Main file reduced from 1412 to 345 lines  
✅ **Tab-Based UI**: No more switching between data sources  
✅ **Modular Design**: Easy to maintain and extend  
✅ **Better Organization**: Analysis logic separated from UI  

## How to Run

### 1. Verify Files Exist
```bash
ls -la | grep -E "streamlit_app.py|mapbiomas_analysis.py|hansen_analysis.py|ui_components.py"
```

### 2. Start the App
```bash
streamlit run streamlit_app.py
```

### 3. In the Browser
- Click **Load Core Data** in the sidebar
- Choose a tab:
  - **🇧🇷 MapBiomas (Brazil)** - 1985-2023 detailed classification
  - **🌍 Hansen/GLAD (Global)** - 2000-2020 global coverage
- Draw an area on the map
- Run analyses from expandable sections

## File Organization

### streamlit_app.py
- App initialization and config
- Session state setup
- Sidebar with "Load Core Data" button
- Two tabs for MapBiomas and Hansen
- Map creation function
- **No analysis code here** - all delegated to modules

### mapbiomas_analysis.py
Four render functions:
1. `render_mapbiomas_area_analysis()` - Analyze drawn areas
2. `render_mapbiomas_territory_analysis()` - Analyze indigenous territories
3. `render_mapbiomas_multiyear_analysis()` - Multi-year comparison
4. `render_mapbiomas_change_analysis()` - Change detection

### hansen_analysis.py
Four render functions:
1. `render_hansen_area_analysis()` - Analyze drawn areas
2. `render_hansen_multiyear_analysis()` - Compare snapshots
3. `render_hansen_change_analysis()` - Change detection
4. `hansen_histogram_to_dataframe()` - Data conversion helper

### ui_components.py
UI utilities:
- Map control panels
- Map instructions
- Load button
- About section

## Tab-Based Workflow

### MapBiomas Tab
```
Draw Area → Select Year → Analyze → View Results
           ↓
     Territory Tab → Select Territory/Year → Analyze
           ↓
     Multi-Year → Select Years → Analyze Trends
           ↓
     Change Detection → View Changes
```

### Hansen Tab
```
Draw Area → Select Year → Analyze → View Results
           ↓
     Compare Snapshots → Select 2 Years → Compare
           ↓
     Change Analysis → View Changes
```

## Data Flow

```
User Interaction
     ↓
Appropriate Tab (MapBiomas or Hansen)
     ↓
render_*_analysis() function
     ↓
Analysis module (analysis.py, app_file.py)
     ↓
Store in st.session_state
     ↓
Display with visualization module
```

## Switching Between Tabs

**Why tabs are better:**
- ❌ OLD: Switch data source → Reset map → Reset results → Re-analyze
- ✅ NEW: Click tab → Keep your analysis → Instant switch

Each tab maintains its own context, so you can:
1. Analyze an area in MapBiomas
2. Switch to Hansen and analyze the same area
3. Go back to MapBiomas - your results are still there
4. Compare insights side-by-side

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
cd /home/leandromb/google_eengine/yvynation
python3 -m py_compile streamlit_app.py mapbiomas_analysis.py hansen_analysis.py ui_components.py
```

### Missing Data
Click "Load Core Data" in the sidebar. Wait for the spinner to complete.

### Map Not Showing
- Verify you clicked "Load Core Data"
- Check that Earth Engine is initialized (check sidebar)
- Try refreshing the browser

## Adding New Features

### To add a new MapBiomas analysis:
1. Create function in `mapbiomas_analysis.py`
2. Add to MapBiomas tab in `streamlit_app.py`
```python
with st.expander("📌 New Analysis"):
    render_mapbiomas_new_analysis()
```

### To add a new Hansen analysis:
1. Create function in `hansen_analysis.py`
2. Add to Hansen tab in `streamlit_app.py`
```python
with st.expander("📌 New Analysis"):
    render_hansen_new_analysis()
```

### To add shared UI component:
1. Create function in `ui_components.py`
2. Import and use in both tabs

## Performance Notes

- Maps are created fresh for each tab to prevent layer conflicts
- Session state persists analysis results across tab switches
- Use `@st.cache_resource` for expensive operations
- Each tab can have different zoom levels without affecting the other

## Next Steps

Suggested improvements:
1. Add export functionality (GeoJSON, CSV, PDF)
2. Create comparison view (MapBiomas vs Hansen side-by-side)
3. Add time-series charts for multi-year analysis
4. Implement territory boundary highlighting
5. Add satellite imagery overlay option
