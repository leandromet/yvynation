# Buffer Compare Mode - Feature Documentation

## Overview
Extension of the external buffer feature that enables **side-by-side comparison** of land cover analysis between:
- **Original Area** (territory or drawn polygon)
- **Buffer Zone** (external ring around the area)

This allows researchers to compare land cover patterns inside territories with their immediate surroundings.

## User Workflow

### 1. Enable Buffer Compare Mode

**For Territories:**
1. Sidebar → "🏛️ Indigenous Territories Analysis"
2. Select a territory
3. ✅ Check "📊 Compare Territory vs Buffer"
4. Select buffer distance (2km/5km/10km)
5. Click "🔵 Create Buffer"

**For Drawn Polygons:**
1. Draw a polygon on the map
2. Select it from the polygon dropdown
3. ✅ Check "📊 Compare Polygon vs Buffer"
4. Select buffer distance
5. Click "🔵 Create Buffer"

### 2. View Comparison Results

When compare mode is active, the analysis section shows **5 tabs** instead of 4:

**Standard Mode (4 tabs):**
- 📍 MapBiomas Analysis
- 🌍 Hansen Analysis
- 📈 Comparison
- ℹ️ About

**Compare Mode (5 tabs):**
- 📍 MapBiomas (Original)
- 🔵 MapBiomas (Buffer)
- 🌍 Hansen (Original)
- 🔵 Hansen (Buffer)
- ℹ️ About

### 3. Export Data

**CSV Downloads:**
Each tab includes individual "📥 Download CSV" buttons:
- Original MapBiomas: `original_mapbiomas_{year}.csv`
- Buffer MapBiomas: `buffer_{size}km_mapbiomas_{year}.csv`
- Original Hansen: `original_hansen_{year}.csv`
- Buffer Hansen: `buffer_{size}km_hansen_{year}.csv`

**PDF/PNG Exports:**
Use the "Map Export" section below to export maps for both areas.

## Technical Implementation

### Session State Variables
```python
st.session_state.buffer_compare_mode  # Boolean: compare mode active
st.session_state.current_buffer_for_analysis  # String: buffer name for comparison
st.session_state.buffer_analysis_results  # Dict: {buffer_name: {dataset_year: dataframe}}
```

### Helper Functions

**`analyze_mapbiomas_geometry(geometry, year, area_name)`**
- Runs MapBiomas analysis on any geometry
- Returns DataFrame with land cover statistics
- Used for both original and buffer areas
- Handles errors gracefully

**`analyze_hansen_geometry(geometry, year, area_name)`**
- Runs Hansen analysis on any geometry
- Returns DataFrame with forest change statistics
- Supports consolidated view toggle
- Used for both original and buffer areas

### Tab Structure Logic
```python
if compare_with_buffer:
    # 5 tabs with separate original/buffer analysis
    tab1: MapBiomas Original
    tab2: MapBiomas Buffer
    tab3: Hansen Original
    tab4: Hansen Buffer
    tab5: About + Compare Mode Info
else:
    # Standard 4 tabs
    tab1: MapBiomas
    tab2: Hansen
    tab3: Multi-Year Comparison
    tab4: About
```

## Features

### ✅ Completed
- [x] Buffer compare mode toggle in territory section
- [x] Buffer compare mode toggle in polygon section
- [x] Separate tabs for original vs buffer analysis
- [x] MapBiomas analysis for both areas
- [x] Hansen analysis for both areas
- [x] Individual CSV downloads for each area
- [x] Results stored in session state for export
- [x] Visual indicators (🔵 for buffer tabs)
- [x] About tab explains compare mode
- [x] Consolidated view support for Hansen buffer

### Data Stored for Export
```python
# MapBiomas buffer results
st.session_state.buffer_analysis_results[buffer_name]['mapbiomas_2023'] = DataFrame

# Hansen buffer results  
st.session_state.buffer_analysis_results[buffer_name]['hansen_2020'] = DataFrame
```

## Use Cases

### 1. Territory Protection Analysis
Compare land cover **inside** an indigenous territory vs the **surrounding buffer zone**:
- Is deforestation higher outside the protected area?
- Are forest cover percentages similar or different?
- What land uses dominate the buffer zone?

### 2. Edge Effect Studies
Analyze the transition zone around territories:
- How does land cover change at territory boundaries?
- Are there different pressures in the buffer zone?
- What is the land use in the 5km surrounding the territory?

### 3. Context Understanding
Understand the landscape context:
- What surrounds this territory?
- Is the buffer zone agricultural, forested, or urban?
- How does the territory differ from its surroundings?

### 4. Comparative Statistics
Generate statistics for reports:
- "Territory: 85% forest coverage"
- "Buffer zone: 45% forest coverage"
- "Territory has 40% more forest than surrounding area"

## Export Capabilities

### CSV Exports (Individual)
- ✅ MapBiomas original area
- ✅ MapBiomas buffer zone
- ✅ Hansen original area
- ✅ Hansen buffer zone

Each CSV includes:
- Class ID and Name
- Pixel count
- Area in hectares
- Percentage of total

### PDF/PNG Exports (Map Export Section)
The map export functionality can generate:
- Maps with both original and buffer boundaries visible
- Separate exports for original vs buffer area
- Combined view showing both areas

## User Interface Indicators

**Compare Mode Active:**
- Info message: "📊 Compare Mode: Analyzing original area vs Xkm buffer zone"
- Success message: "✅ Created Xkm buffer - Compare mode enabled!"
- Tab names include (Original) and (Buffer) labels
- 🔵 emoji marks buffer-specific tabs

**Compare Mode Inactive:**
- Standard 4-tab layout
- Buffer appears in polygon selector for manual selection
- Info message: "📍 Buffer added to polygon list"

## Benefits

1. **Side-by-Side Analysis**: View both areas simultaneously in different tabs
2. **Independent Downloads**: Separate CSVs for each area
3. **No Manual Switching**: Compare mode handles both analyses automatically
4. **Research-Ready**: Perfect for studies comparing protected vs unprotected areas
5. **Flexible Export**: Download data separately or together for further analysis
6. **Same Tools**: Uses identical analysis methods for fair comparison

## Example Workflow

**Research Question:** *"How does forest cover in Yanomami Territory compare to the surrounding 10km buffer zone?"*

**Steps:**
1. Select Yanomami Territory
2. Enable "📊 Compare Territory vs Buffer"
3. Choose 10km buffer
4. Click "Create Buffer"
5. Add MapBiomas 2023 layer
6. View results:
   - Tab 1: Yanomami Territory MapBiomas results
   - Tab 2: 10km Buffer MapBiomas results
7. Download both CSVs
8. Compare forest percentages
9. Export maps showing both areas

**Result:** Clear comparison data showing land cover differences between protected territory and surrounding area.

## Notes

- Compare mode persists across page interactions (session-based)
- Buffer geometry calculated using Earth Engine (geodesic distances)
- Analysis runs independently for each area (no interference)
- Multiple years can be analyzed in compare mode
- Consolidated Hansen view works in compare mode
- Buffer results stored for potential future export enhancements
