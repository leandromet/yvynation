# Yvynation Streamlit Application - Comprehensive Codebase Analysis

**Last Updated:** March 26, 2026  
**Application:** Indigenous Land Monitoring Platform  
**Author:** Leandro M. Biondo, PhD Candidate, IGS/UBCO  
**Main Entry Point:** `streamlit_app.py`

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Layer 1: Core Infrastructure](#layer-1-core-infrastructure)
3. [Layer 2: Earth Engine & Authentication](#layer-2-earth-engine--authentication)
4. [Layer 3: Utility Modules](#layer-3-utility-modules)
5. [Layer 4: Analysis Modules](#layer-4-analysis-modules)
6. [Layer 5: Visualization & Mapping](#layer-5-visualization--mapping)
7. [Layer 6: Export & Output](#layer-6-export--output)
8. [Layer 7: UI Components](#layer-7-ui-components)
9. [Data Flow Architecture](#data-flow-architecture)
10. [Module Dependencies](#module-dependencies)
11. [Key Functions Summary](#key-functions-summary)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND                       │
│                (streamlit_app.py / main.py)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────┐
  │ Components  │ │ Analysis │ │ Visualization│
  │ (sidebar,   │ │ Modules  │ │ & Mapping    │
  │ main, etc)  │ │          │ │              │
  └─────────────┘ └──────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────┐
  │   Utility   │ │Config &  │ │  Earth       │
  │   Modules   │ │Data Load │ │  Engine API  │
  │             │ │          │ │              │
  └─────────────┘ └──────────┘ └──────────────┘
```

---

## Layer 1: Core Infrastructure

### Configuration (`config.py`)
**Purpose:** Central configuration hub for all Earth Engine datasets, project settings, and constants.

**Key Constants:**
- **Project ID:** `ee-leandromet` (Earth Engine project)
- **Region of Interest:** Brazil [-73.0°, -33.0°] to [-35.0°, 5.0°]
- **Output Bucket:** `gs://yvynation-bucket` (Google Cloud Storage)
- **Export Resolution:** 30 meters (Landsat/Sentinel-2 standard)

**MapBiomas Collections:**
```python
MAPBIOMAS_COLLECTIONS = {
    'v9': 'projects/mapbiomas-public/assets/brazil/lulc/collection9/...',
    'v8': 'projects/mapbiomas-public/assets/brazil/lulc/collection8/...'
}
```

**Hansen/GLAD Global Datasets:**
- GLCLU2020 v2: 5 snapshots (2000, 2005, 2010, 2015, 2020)
- Labels: 256 land cover classes (via `hansen_labels.py`)
- Ocean mask for data cleaning

**Hansen Global Forest Change (GFC):**
- Dataset: `UMD/hansen/global_forest_change_2024_v1_12`
- Bands: `treecover2000` (0-100%), `lossyear` (0-24 = 2001-2024), `gain` (0-1)

**Territory Collections:**
```python
TERRITORY_COLLECTIONS = {
    'indigenous': 'projects/mapbiomas-territories/assets/.../INDIGENOUS_TERRITORIES',
    'biomes': 'projects/mapbiomas-territories/assets/.../BIOMES'
}
```

**Satellite Collections:**
- Sentinel-2 SR (cloud-harmonized)
- Landsat 9 Collection 2
- SPOT 2008 (visual & analytic - restricted access)

**Color Palettes:**
- `MAPBIOMAS_PALETTE`: 62-class continuous palette
- `HANSEN_PALETTE`: 256-class palette for GLAD data
- `HANSEN_COLOR_MAP`: Discrete 18-class land cover colors

**Processing Parameters:**
- Cloud filter: ≤20% cloud cover
- NDVI thresholds: Forest (≥0.5), Urban (<0.2)
- Analysis scale: 30m pixels

### Translations (`translations.py`)
**Purpose:** Bilingual UI support (English, Portuguese-Brazil).

**Key Features:**
- Dictionary-based translations for all UI strings
- Support for dynamic string formatting
- Translation function: `t(key, **kwargs)` for interpolation
- Sections: App titles, sidebar labels, layer names, button text, error messages

**Translation Domains:**
- Page configuration (`page_title`, `page_icon`)
- Region selection (`select_region`, `current_region`)
- Language selection (`language`)
- Auto-detection workflow (`auto_detect_*`)
- Map layers (`mapbiomas_layer`, `hansen_layer`, etc.)
- Date/time labels
- Button labels and help text

### Auto-Detection (`auto_detect_preferences.py`)
**Purpose:** Detect language and region from user IP/browser settings.

**Key Function:**
```python
initialize_preferences()
```
- Detects country from IP geolocation
- Detects browser language from Accept-Language header
- Sets `st.session_state.language` and `st.session_state.region`
- Privacy-conscious: country-level only, no precise location

---

## Layer 2: Earth Engine & Authentication

### Earth Engine Authentication (`ee_auth.py`)
**Purpose:** Initialize and authenticate with Google Earth Engine API.

**Key Function:**
```python
initialize_earth_engine() → ee module
```

**Authentication Methods (in priority order):**
1. **Cloud Run Environment Variables** (production)
   - `EE_PRIVATE_KEY`: Service account private key
   - `EE_SERVICE_ACCOUNT_EMAIL`: Service account email
   - `GCP_PROJECT_ID`: Google Cloud project

2. **Application Default Credentials (ADC)** (Google Cloud)
   - Automatic for services running on Google Cloud infrastructure

3. **Streamlit Cloud Secrets** (legacy)
   - Manual setup via `st.secrets`

**Returns:** Initialized Earth Engine module ready for API calls

---

## Layer 3: Utility Modules

### Buffer Utilities (`buffer_utils.py`)
**Purpose:** Create external "donut" buffer zones around territories/polygons.

**Key Functions:**
```python
create_external_buffer(geometry, distance_km) → ee.Geometry
```
- Creates ring-shaped buffer around geometry
- Formula: `buffered = buffer - original_geometry`
- Use case: Analyze areas adjacent to protected territories

```python
add_buffer_to_session_state(geometry, buffer_size_km, source_name) → str
```
- Stores buffer in `st.session_state.buffer_geometries`
- Metadata in `st.session_state.buffer_metadata`
- Returns buffer name for reference

```python
get_buffer_as_feature(buffer_name) → dict
```
- Converts stored buffer to GeoJSON feature
- Compatible with `all_drawn_features`

**Use Case:** Analyze deforestation within 5km of territory boundary

### Geometry Upload (`geometry_upload.py`)
**Purpose:** Parse and validate user-uploaded geometry files (KML, GeoJSON, Shapefile).

**Key Functions:**
```python
parse_geojson(file_content, file_name) → dict
```
- Validates GeoJSON structure
- Converts raw geometries to FeatureCollections
- Supports: Point, LineString, Polygon, MultiPolygon

```python
parse_kml(file_content, file_name) → dict
```
- Parses KML Placemark elements
- Extracts coordinates and properties
- Handles KML namespaces

**Returns:** Standardized GeoJSON FeatureCollection

### Export Utilities (`export_utils.py`)
**Purpose:** Package analysis results into downloadable ZIP files.

**Key Function:**
```python
create_export_zip(
    polygon_features=None,
    territory_geom=None,
    territory_analysis_data=None,
    territory_figures=None,
    all_figures=None,
    map_exports=None,
    metadata=None
) → bytes
```

**ZIP Structure:**
```
export.zip
├── metadata.json              # Analysis timestamp, settings
├── geometries.geojson         # All drawn polygons + territory boundary
├── geojson/                   # Individual polygon GeoJSON files
├── analysis/
│   ├── mapbiomas_data/        # CSV tables by class
│   ├── hansen_data/           # CSV tables by stratum
│   └── territory_data/        # Territory-specific analysis
├── figures/
│   ├── mapbiomas/             # PNG plots (distribution, comparison)
│   ├── hansen/                # PNG plots (area histograms)
│   └── maps/                  # Exported map overlays (HTML/PNG)
└── reports/                   # Summary statistics
```

**Data Types Supported:**
- GeoJSON features (vector)
- Pandas DataFrames as CSV
- Matplotlib figures as PNG
- Metadata as JSON

### PNG Export (`png_export.py`)
**Purpose:** Export map visualizations as PNG for high-quality reports.

**Processing:**
- Converts Folium/Leaflet maps to static images
- Embeds map styling and legend
- Supports screenshots of specific regions

### PDF Export (`map_pdf_export.py`)
**Purpose:** Generate PDF reports with maps, tables, and analysis.

**Features:**
- MultiPage PDF documents
- Embeds metadata and timestamps
- Includes territory names and analysis parameters

### Load Data (`load_data.py`)
**Purpose:** Load Earth Engine assets and satellite collections.

**Key Functions:**
```python
load_mapbiomas(version='v9') → ee.Image
```
- Loads MapBiomas Brazil collection
- Multi-year stacked bands: `classification_1985` → `classification_2023`

```python
load_territories(territory_type='indigenous') → ee.FeatureCollection
```
- Loads official indigenous territory boundaries
- Returns all ~700 territories in Brazil

```python
load_sentinel2(roi, start_date, end_date, cloud_filter=20) → ee.ImageCollection
```
- Filters by bounds, date range, cloud cover
- Cloud-harmonized surface reflectance

```python
load_spot_visual() / load_spot_analytic() → ee.Image
```
- SPOT 2008 (restricted – checks access first)
- Visual (RGB) or analytic (multispectral)

---

## Layer 4: Analysis Modules

### Core Analysis (`analysis.py`)
**Purpose:** Low-level analysis algorithms for land cover classification.

**Key Functions:**
```python
clip_mapbiomas_to_geometry(mapbiomas, geometry, start_year, end_year) → ee.Image
```
- Selects classification bands for year range
- Clips to geometry boundaries

```python
calculate_area_by_class(image, geometry, year=None, scale=30) → pd.DataFrame
```
- Returns area (hectares) by land cover class
- Columns: `Year`, `Class_ID`, `Class_Name`, `Area_ha`
- Uses pixel area calculation + group reducer

```python
calculate_land_cover_change(mapbiomas, geometry, start_year, end_year) → dict
```
- Binary change detection between two years
- Returns: `{'change_image', 'change_area_km2'}`

```python
get_class_specific_change(mapbiomas, geometry, start_year, end_year, class_id) → dict
```
- Tracks loss/gain for single land cover class
- Returns: `{'loss_km2', 'gain_km2', 'loss_image', 'gain_image'}`

```python
compare_areas(area_df1, area_df2) → pd.DataFrame
```
- Merges two period's areas
- Calculates change: `Change_ha = Area_end - Area_start`
- Calculates % change: `Change_pct = Change_ha / Area_start × 100`

### MapBiomas Analysis (`mapbiomas_analysis.py`)
**Purpose:** Brazil-specific land cover analysis using MapBiomas collection.

**Key Functions:**
```python
calculate_area_by_class(image, geometry, year) → pd.DataFrame
```
- Streamlit-integrated area calculation
- Handles frequency histogram conversion
- Maps class IDs to names via `MAPBIOMAS_LABELS`
- Returns top classes by area

```python
plot_area_distribution(df, year=None, top_n=15) → matplotlib.figure.Figure
```
- Horizontal bar chart (top N classes)
- Uses MapBiomas color palette
- Year in title if provided

```python
plot_area_comparison(df_start, df_end, year_start, year_end) → matplotlib.figure.Figure
```
- Side-by-side comparison (2 years)
- Same classes aligned for visual comparison

```python
plot_temporal_trend(df, years=None) → matplotlib.figure.Figure
```
- Line plot tracking class area over time
- Shows gains/losses for key classes

```python
render_mapbiomas_area_analysis()``` (Streamlit UI function)
- Draws interactive polygon on map
- Analyzes with MapBiomas for selected year
- Displays area statistics table

```python
render_mapbiomas_territory_analysis()``` 
- Dropdown to select indigenous territory
- Analyzes all years (1985–2023)
- Shows comparison tables and trend plots

### Hansen/GLAD Analysis (`hansen_analysis.py`)
**Purpose:** Global forest cover analysis using Hansen/GLAD GLCLU2020 dataset.

**Key Functions:**
```python
get_hansen_color(class_id) → str
```
- Returns hex color for Hansen class (18 strata)

```python
hansen_histogram_to_dataframe(hist, year) → pd.DataFrame
```
- Converts frequency histogram to DataFrame
- Columns: `Class_ID`, `Class`, `Stratum`, `Name`, `Pixels`, `Area_ha`
- Groups by stratum for cleaner visualization

```python
render_hansen_area_analysis()```
- User draws polygon → analyzes with Hansen
- Selects year (2000, 2005, 2010, 2015, 2020)
- Shows stratum-level distribution
- Zoom to area on map after analysis

**Data Structure:**
- `st.session_state.hansen_drawn_areas`: Dict of `{area_name: {coordinates, properties}}`
- `st.session_state.hansen_drawn_area_count`: Number of areas

### Hansen Global Forest Change (`gfc_analysis.py`)
**Purpose:** Tree cover, loss, and gain analysis from Hansen GFC dataset.

**Key Functions:**
```python
analyze_hansen_gfc_geometry(geometry, area_name="Area") → dict
```
- Returns dictionary with three DataFrames:
  - `'tree_cover'`: Percent coverage (0-100%) histogram
  - `'tree_loss'`: Year of loss (2001–2024) histogram  
  - `'tree_gain'`: Binary gain pixels (0–1)
- Uses frequency histogram reducer
- Handles multiple output key names (error tolerance)

**Data Flow:**
1. Select geometry (drawn polygon or territory)
2. Extract treecover2000 band → frequency histogram
3. Extract lossyear band → loss year distribution
4. Extract gain band → gain pixels count
5. Calculate area: `pixels × 0.09 ha/pixel`

### GFC Consolidation (`hansen_consolidated_utils.py`, `hansen_consolidated_mapping.py`)
**Purpose:** Simplify 256 Hansen classes into 11 consolidated land cover strata.

**Key Functions:**
```python
get_consolidated_class(class_id) → str
```
- Maps class 0–255 → consolidated name
- Examples: "Water", "Evergreen Forest", "Cropland"

```python
get_consolidated_color(class_id) → str
```
- Returns hex color for consolidated class

```python
aggregate_to_consolidated(df_original) → pd.DataFrame
```
- Sums pixels/area across original classes
- Groups by consolidated name
- Sorted descending by area

### GFC Reference Mapping (`hansen_reference_mapping.py`, `hansen_labels.py`)
**Purpose:** Class ID lookup tables and label definitions.

**Contents:**
- `HANSEN_LABELS`: Dict mapping 0–255 → class names
- `HANSEN_STRATUM_NAMES`: Dict mapping stratum number → name
- `HANSEN_CLASS_TO_STRATUM`: Maps each class to stratum group
- `HANSEN_STRATUM_COLORS`: Hex colors for 18 strata

### Territory Analysis (`territory_analysis.py`)
**Purpose:** Indigenous territory-specific analysis.

**Key Functions:**
```python
get_territory_names(territories_fc) → tuple: (names_list, name_property)
```
- Extracts sorted territory names
- Identifies correct property name (name, Nome, territory_name, etc.)

```python
get_territory_geometry(territories_fc, territory_name, name_prop) → ee.Geometry
```
- Filters feature collection by name
- Returns geometry for analysis

```python
analyze_territory_mapbiomas(mapbiomas, territory_geom, year) → pd.DataFrame
```
- Analyzes single year within territory
- Returns area by class

```python
analyze_territory_hansen(hansen_image, territory_geom, year) → pd.DataFrame
```
- Hansen/GLAD analysis within territory
- Returns area by class/stratum

**Use Case Example:**
```
Select: Yanomami Territory
Year: 2020
→ MapBiomas analysis: 45% forest, 20% grassland, 15% agriculture
→ Hansen analysis: 42% forest, 18% water, 12% urban
```

### SPOT Analysis (`spot_module.py`)
**Purpose:** High-resolution 2008 SPOT satellite data analysis.

**Key Functions:**
```python
check_spot_access() → bool
```
- Verifies SPOT dataset accessibility
- Returns False if restricted (requires special permissions)

```python
load_spot_analytic() → ee.Image
```
- Loads multispectral data
- Bands: Blue, Green, Red, NIR, SWIR

```python
load_spot_visual() → ee.Image
```
- Loads RGB composite

**Status:** ⚠️ Restricted access – requires Google Earth Engine attribution

---

## Layer 5: Visualization & Mapping

### Visualization (`visualization.py`)
**Purpose:** High-level geemap-based visualization utilities (legacy/support).

**Key Functions:**
```python
create_map(center=[lon, lat], zoom=8) → geemap.Map
```
- Creates interactive geemap map object
- Default center: [-55.5, -15.8] (Brazil)

```python
add_mapbiomas_layer(Map, mapbiomas, year, name=None, visible=True) → geemap.Map
```
- Adds classification layer with palette
- Selects band: `classification_{year}`

```python
add_territories_layer(Map, territories, name='Indigenous Territories', color='red') → geemap.Map
```
- Vector layer with styling
- Transparent fill, colored borders

### Map Manager (`map_manager.py`)
**Purpose:** Folium-based map creation for web export.

**Key Functions:**
```python
create_base_map(country="Brazil", center_lat=None, center_lon=None, zoom=None) → folium.Map
```
- Creates base Folium map with multiple basemaps
- Country presets: Brazil (center: -15°, -50°, zoom 4), Canada (center: 56°, -95°, zoom 3)
- Basemaps: OpenStreetMap, Google Satellite, ArcGIS Street, ArcGIS Terrain

```python
add_territories_layer(m, territories, name='Indigenous Territories', opacity=0.7) → folium.Map
```
- Adds territories as vector overlay
- Styled with transparency

```python
add_layer_control(m) → folium.Map
```
- Adds layer toggle control (top-right corner)
- Enables on/off switching of overlays

### Earth Engine Layers (`ee_layers.py`)
**Purpose:** Convert Earth Engine imagery to Folium tile layers.

**Key Functions:**
```python
_cached_get_map_id(cache_key, image_fn, vis_params) → str
```
- Caches tile URLs in `st.session_state._tile_cache`
- Avoids redundant EE API calls on Streamlit reruns
- Returns tile_fetcher.url_format for Folium

```python
add_mapbiomas_layer(m, mapbiomas, year, opacity=1.0, shown=True) → folium.Map
```
- Converts MapBiomas image → tile layer
- Uses cached tile URL
- Defau opacity: 100%, visible by default

```python
add_hansen_layer(m, year, opacity=1.0, shown=True) → folium.Map
```
- Adds Hansen/GLAD GLCLU{year} layer
- Supports: 2000, 2005, 2010, 2015, 2020

```python
add_hansen_gfc_tree_cover(m, opacity=1.0, shown=True) → folium.Map
```
- Adds Hansen GFC tree cover 2000 (0-100% palette)

```python
add_hansen_gfc_tree_loss(m, opacity=1.0, shown=True) → folium.Map
```
- Adds tree loss year layer (2001-2024, yellow→red palette)

```python
add_hansen_gfc_tree_gain(m, opacity=1.0, shown=True) → folium.Map
```
- Adds tree gain pixels (binary, black→green)

```python
add_aafc_layer(m, year, opacity=1.0, shown=True) → folium.Map
```
- Adds AAFC crop inventory (Canada, if available)

```python
remove_layer(m, layer_name) → folium.Map
```
- Removes layer by name

**Tile Caching Strategy:**
- Problem: Each `map_id.getMapId()` call costs EE API quota + time
- Solution: Cache tile URLs in `session_state._tile_cache`
- Benefit: Instant reloads on Streamlit reruns without API calls

### Plotting Utilities (`plotting_utils.py`, `plots.py`)
**Purpose:** Consistent matplotlib/plotly visualizations.

**Key Functions:**
```python
get_bar_colors(df, id_column='Class_ID') → list
```
- Maps class IDs → colors from MapBiomas palette
- Fallback: grey (#808080) for unknown classes

```python
plot_area_distribution(area_df, year=None, top_n=15, figsize=(12, 6)) → matplotlib.figure.Figure
```
- Horizontal bar chart (top N classes)
- Colored by class ID
- Returns figure for `st.pyplot(fig)`

```python
plot_area_comparison(area_start, area_end, start_year, end_year, top_n=15) → matplotlib.figure.Figure
```
- 1×2 subplot grid (side-by-side comparison)
- Same color scheme for classes

**Note:** Supports both MapBiomas (62 classes) and Hansen (11–256 classes) DataFrames

---

## Layer 6: Export & Output

### Map Export Components (`map_export_components.py`)
**Purpose:** UI for exporting map visualizations.

**Features:**
- Button to screenshot current Folium map
- Save as PNG with metadata
- Include in ZIP export

### Test Exports (`test_png_export.py`, `test_ee_export.py`)
**Purpose:** Development/debugging for export functionality.

---

## Layer 7: UI Components

### Component Structure
```
components/
├── __init__.py
├── initialization.py   # Session state setup
├── sidebar.py         # Left sidebar controls
├── main_content.py    # Main page layout
└── tutorial.py        # In-app tutorial
```

### Sidebar Components (`components/sidebar.py`)
**Purpose:** All left-side controls and navigation.

**Sections:**
```python
render_sidebar()
├── _render_map_controls()          # Layer help text, basemap info
├── _render_layer_management()      # Add MapBiomas/Hansen layers
│   └── Year sliders + buttons
├── _render_territory_analysis()    # Territory dropdowns + analysis
└── _view_options() + _render_about_section()
```

**Key Controls:**
- Map controls explanation
- MapBiomas year slider (1985–2023)
- Hansen year selector (2000, 2005, 2010, 2015, 2020)
- Territory dropdown (auto-populates from data)
- View options (colorblind mode, etc.)

### Main Content (`components/main_content.py`)
**Purpose:** Central page layout and metrics.

**Key Functions:**
```python
render_main_content()
```
- Title and subtitle
- Tutorial (if first visit)

```python
render_layer_metrics()
```
- Displays active layer counts
- Shows selected years for each dataset

```python
render_footer()
```
- Credits and footer text

### Initialization (`components/initialization.py`)
**Purpose:** Session state setup on app load.

**Initializes:**
```python
st.session_state.data_loaded = False       # EE initialization status
st.session_state.mapbiomas_layers = {}     # {year: bool}
st.session_state.hansen_layers = {}        # {year: bool}
st.session_state.hansen_drawn_areas = {}   # {name: geom_data}
st.session_state.hansen_drawn_area_count = 0
st.session_state.buffer_geometries = {}
st.session_state.all_drawn_features = []
st.session_state._tile_cache = {}          # Tile URL cache
```

### Tutorial (`components/tutorial.py`)
**Purpose:** In-app guided walkthrough for new users.

**Content:**
- How to select region
- How to add map layers
- How to draw polygons
- How to interpret results
- Export options

### Analysis UI (`analysis_tabs_component.py`)
**Purpose:** Tabbed interface for different analysis types.

**Tabs:**
1. "🌱 MapBiomas" → MapBiomas drawn area analysis
2. "🌍 Hansen/GLAD" → Hansen drawn area analysis
3. "🏛️ Territories" → Territory analysis
4. "📊 Exports" → Download results

### Year/Date Selection (`year_selector_component.py`)
**Purpose:** Unified year selection UI.

**Features:**
- Slider for range selection
- Preset buttons (Last 5 years, Last 10 years, all years)
- Start/end year pickers

### Map Components (`map_components.py`)
**Purpose:** Map-specific UI elements.

**Features:**
- Draw toolbar control
- Basemap selector
- Layer opacity sliders
- Legend display

### Sidebar Helper Components
```python
sidebar_components.py
├── render_geometry_upload()     # File upload (KML, GeoJSON)
├── render_buffer_controls()     # Create buffer zones
├── render_drawn_area_list()     # List all drawn polygons
└── render_analysis_options()    # Toggle analysis types
```

---

## Data Flow Architecture

### Flow 1: User Draws Polygon → Analyzes with MapBiomas

```
User draws polygon on map
    ↓
Coordinates stored in st.session_state.all_drawn_features
    ↓
User selects year & clicks "Analyze"
    ↓
mapbiomas_analysis.py:
    • Convert polygon → ee.Geometry
    • Load mapbiomas image
    • Clip to polygon: mapbiomas.select(f'classification_{year}').clip(geometry)
    ↓
analysis.py: calculate_area_by_class()
    • Group by class using ee.Reducer.frequencyHistogram()
    • Calculate area: pixels × 0.09 ha
    • Get class names from MAPBIOMAS_LABELS
    ↓
plots.py: plot_area_distribution()
    • Create bar chart (top 15 classes)
    • Use MAPBIOMAS_COLOR_MAP for coloring
    ↓
Display DataFrame + visualization in st.write()
```

### Flow 2: User Selects Territory → Analyzes All Years

```
User selects from territory dropdown
    ↓
territory_analysis.py: get_territory_geometry()
    • Filter territories_fc by name
    • Return ee.Geometry
    ↓
User clicks "Analyze Territory"
    ↓
Loop over years 1985–2023:
    ├── analyze_territory_mapbiomas(mapbiomas, geom, year)
    │   └── calculate_area_by_class() for each year
    ├── Collect results in {year: dataframe}
    └── Store in st.session_state
    ↓
Generate comparison plots:
    • Temporal trend line plot
    • Year-over-year comparison bars
    ↓
Display annual tables + visualizations
```

### Flow 3: User Uploads Geometry File

```
User uploads KML/GeoJSON file
    ↓
geometry_upload.py:
    • parse_geojson() OR parse_kml()
    • Validate structure
    • Convert to FeatureCollection
    ↓
Extract coordinates from each feature
    ↓
Add to st.session_state.all_drawn_features[]
    ↓
Render on map as polygon layers
    ↓
Now can analyze each polygon independently
```

### Flow 4: User Exports Results

```
User clicks "Download Analysis Results"
    ↓
export_utils.py: create_export_zip()
    ├── Collect all DataFrames (area_df, change_df, etc.)
    ├── Collect all figures (matplotlib Figure objects)
    ├── Collect all GeoJSON features
    ├── Collect metadata (timestamp, project, settings)
    ↓
    └── Create ZIP with structure:
        ├── metadata.json
        ├── geometries.geojson
        ├── analysis/
        │   ├── mapbiomas_*.csv
        │   ├── hansen_*.csv
        │   └── comparison_*.csv
        └── figures/
            ├── mapbiomas_distribution.png
            ├── hansen_comparison.png
            └── territory_trend.png
    ↓
Return bytes to browser
    ↓
User downloads ZIP file
```

### Flow 5: Map Layer Rendering (with Tile Caching)

```
User adds MapBiomas 2020 layer
    ↓
ee_layers.py: add_mapbiomas_layer(m, mapbiomas, 2020)
    ├── Cache key: 'mapbiomas_2020'
    ├── Check st.session_state._tile_cache['mapbiomas_2020']
    │   ├── Hit: Return cached tile URL → Skip EE API call ✓
    │   └── Miss: Call mapbiomas.select('classification_2020').getMapId(vis_params)
    │        → Get tile_fetcher.url_format
    │        → Store in cache: _tile_cache['mapbiomas_2020'] = url
    ↓
folium.TileLayer(tiles=url, ...) added to map
    ↓
Map refreshes on user pan/zoom (same cached URL reused)
    ↓
On Streamlit rerun (e.g., user clicks button):
    • Session state persists, cache persists
    • Same layer added again uses cached URL (no API call)
```

---

## Module Dependencies

### Import Graph (High-Level)

```
streamlit_app.py (ENTRY)
├── components.sidebar
│   ├── territory_analysis
│   │   ├── mapbiomas_analysis
│   │   ├── hansen_analysis
│   │   └── analysis
│   ├── buffer_utils
│   ├── geometry_upload
│   └── config
├── components.main_content
├── map_manager
│   └── config (MAPBIOMAS_PALETTE)
├── ee_layers
│   ├── config (HANSEN_DATASETS, HANSEN_PALETTE, etc.)
│   ├── hansen_reference_mapping
│   ├── folium
│   └── ee
├── mapbiomas_analysis
│   ├── analysis
│   ├── config
│   ├── matplotlib
│   └── streamlit
├── hansen_analysis
│   ├── config
│   ├── hansen_reference_mapping
│   ├── hansen_labels
│   ├── pandas
│   └── streamlit
├── gfc_analysis
│   ├── config (HANSEN_GFC_DATASET)
│   ├── pandas
│   └── ee
├── load_data
│   ├── config (MAPBIOMAS_COLLECTIONS, TERRITORY_COLLECTIONS, etc.)
│   └── ee
├── ee_auth
│   ├── ee
│   └── google.oauth2.service_account
├── export_utils
│   ├── translations
│   ├── pandas
│   ├── matplotlib
│   ├── zipfile
│   └── json
├── visualization
│   ├── geemap
│   ├── config
│   └── ee
├── plots
│   ├── config (MAPBIOMAS_COLOR_MAP)
│   ├── matplotlib
│   └── pandas
└── translations
```

### Config-Dependent Modules (Direct)

```
config.py (hub)
├── MAPBIOMAS_COLLECTIONS        → load_data.py
├── MAPBIOMAS_LABELS             → analysis.py, mapbiomas_analysis.py, plots.py
├── MAPBIOMAS_PALETTE            → ee_layers.py, visualization.py, plotting_utils.py
├── MAPBIOMAS_COLOR_MAP          → plots.py, plotting_utils.py
├── HANSEN_DATASETS              → ee_layers.py, hansen_analysis.py
├── HANSEN_PALETTE               → ee_layers.py, config.py
├── HANSEN_COLOR_MAP             → config.py
├── HANSEN_LABELS                → config.py, hansen_analysis.py, hansen_labels.py
├── HANSEN_GFC_*                 → gfc_analysis.py, ee_layers.py
├── TERRITORY_COLLECTIONS        → load_data.py, territory_analysis.py
├── SENTINEL2_COLLECTION         → load_data.py
├── SPOT_*_ASSET                 → load_data.py, spot_module.py
└── PROJECT_ID, OUTPUT_BUCKET    → Export functions
```

### Cyclical/Peer Dependencies

```
analysis.py ↔ mapbiomas_analysis.py
territorio_analysis.py imports both

hansen_analysis.py ↔ gfc_analysis.py
Can be used independently

plot.py / plotting_utils.py (similar functionality)
Both available for visualization
```

---

## Key Functions Summary

### By Domain

#### Data Loading & Access
| Function | Module | Returns | Purpose |
|----------|--------|---------|---------|
| `initialize_earth_engine()` | `ee_auth.py` | `ee` module | Authenticate with Google EE |
| `load_mapbiomas()` | `load_data.py` | `ee.Image` | Load Brazil land cover stack |
| `load_territories()` | `load_data.py` | `ee.FeatureCollection` | Load indigenous territory boundaries |
| `load_sentinel2()` | `load_data.py` | `ee.ImageCollection` | Load Sentinel-2 scenes |
| `load_spot_visual()` | `load_data.py` | `ee.Image` | Load SPOT 2008 RGB (restricted) |

#### Analysis & Statistics
| Function | Module | Returns | Purpose |
|----------|--------|---------|---------|
| `calculate_area_by_class()` | `analysis.py` | `pd.DataFrame` | Area (ha) per class |
| `calculate_land_cover_change()` | `analysis.py` | `dict` | Change image + area |
| `get_class_specific_change()` | `analysis.py` | `dict` | Loss/gain for one class |
| `compare_areas()` | `analysis.py` | `pd.DataFrame` | Year-to-year comparison |
| `hansen_histogram_to_dataframe()` | `hansen_analysis.py` | `pd.DataFrame` | Class histogram → table |
| `analyze_hansen_gfc_geometry()` | `gfc_analysis.py` | `dict` | Tree cover/loss/gain stats |
| `get_territory_names()` | `territory_analysis.py` | `tuple` | (names list, property) |
| `analyze_territory_mapbiomas()` | `territory_analysis.py` | `pd.DataFrame` | Single year territory analysis |

#### Visualization
| Function | Module | Returns | Purpose |
|----------|--------|---------|---------|
| `create_base_map()` | `map_manager.py` | `folium.Map` | Basemap with 4 options |
| `add_mapbiomas_layer()` | `ee_layers.py` | `folium.Map` | Add MapBiomas tile layer |
| `add_hansen_layer()` | `ee_layers.py` | `folium.Map` | Add Hansen year layer |
| `add_hansen_gfc_tree_cover()` | `ee_layers.py` | `folium.Map` | Add tree cover 2000 |
| `plot_area_distribution()` | `plots.py` | `matplotlib.Figure` | Bar chart (top classes) |
| `plot_area_comparison()` | `plots.py` | `matplotlib.Figure` | Side-by-side year comparison |
| `plot_temporal_trend()` | `mapbiomas_analysis.py` | `matplotlib.Figure` | Line chart (time series) |

#### Geometry & Spatial
| Function | Module | Returns | Purpose |
|----------|--------|---------|---------|
| `parse_geojson()` | `geometry_upload.py` | `dict` | GeoJSON → FeatureCollection |
| `parse_kml()` | `geometry_upload.py` | `dict` | KML → FeatureCollection |
| `create_external_buffer()` | `buffer_utils.py` | `ee.Geometry` | Donut-shaped buffer zone |
| `add_buffer_to_session_state()` | `buffer_utils.py` | `str` | Store buffer for analysis |

#### Export
| Function | Module | Returns | Purpose |
|----------|--------|---------|---------|
| `create_export_zip()` | `export_utils.py` | `bytes` | ZIP with data, figures, metadata |

#### UI Rendering (Streamlit)
| Function | Module | Purpose |
|----------|--------|---------|
| `render_sidebar()` | `components/sidebar.py` | All left-side controls |
| `render_mapbiomas_area_analysis()` | `mapbiomas_analysis.py` | Polygon drawing + analysis UI |
| `render_hansen_area_analysis()` | `hansen_analysis.py` | Hansen polygon UI |
| `render_mapbiomas_territory_analysis()` | `mapbiomas_analysis.py` | Territory analysis UI |

---

## Session State Management

### Key Session Variables (Default Initialization)

```python
# Control flags
st.session_state.data_loaded = False           # EE initialized?
st.session_state.language = "en"               # "en" or "pt-br"
st.session_state.region = "brazil"             # "brazil" or "canada"

# Layer visibility toggles
st.session_state.mapbiomas_layers = {}         # {year: True/False}
st.session_state.hansen_layers = {}            # {year: True/False}
st.session_state.current_mapbiomas_year = 2023
st.session_state.current_hansen_year = "2020"

# User-drawn geometries
st.session_state.all_drawn_features = []       # List of GeoJSON-like feature dicts
st.session_state.hansen_drawn_areas = {}       # {area_name: {coordinates, properties}}
st.session_state.hansen_drawn_area_count = 0
st.session_state.hansen_selected_drawn_area = None

# Buffer geometries
st.session_state.buffer_geometries = {}        # {buffer_name: ee.Geometry}
st.session_state.buffer_metadata = {}          # {buffer_name: {properties}}

# EE tile caching (critical for performance)
st.session_state._tile_cache = {}              # {cache_key: tile_url}

# App references
st.session_state.app = None                    # YvynationApp instance (if using Reflex)

# Analysis results (ephemeral)
st.session_state.last_analysis_df = None       # Caches last computed DataFrame
```

---

## Performance Considerations

### Tile URL Caching (`_tile_cache`)
**Problem:** Each `ee.Image.getMapId()` call costs ~1-2 seconds + API quota  
**Solution:** Cache tile URL string in session state  
**Benefit:** On Streamlit rerun, same layer added instantly without API call  
**Cache Key Pattern:** `f"{dataset}_{year}_{variant}"`  
**Invalidation:** Never (tiles don't change unless data updates)

### Frequency Histogram Reducer
**Use Case:** Calculate area by class without storage objects  
**Performance:** Fast for <5000 unique classes  
**Output:** Dictionary `{class_id: pixel_count}`  
**Limitation:** May group classes > ~8000 into single bin

### Scale Parameter
**Default:** 30 meters (Landsat/Sentinel-2 native)  
**Considerations:**
- 30m = reasonable accuracy for land cover
- Smaller scale = more pixels = slower analysis
- Larger scale = less accuracy but faster

---

## Error Handling & Recovery

### EE Initialization Failures
```python
# ee_auth.py
tries in order:
1. Service account (Cloud Run env vars)
2. Application Default Credentials (Google Cloud)
3. Streamlit secrets (legacy)
→ Falls back to helpful error message if all fail
```

### Restricted Data Access
```python
# spot_module.py
check_spot_access() returns False if:
- SPOT asset inaccessible
- Insufficient permissions
→ Gracefully disables SPOT section in UI
```

### Streamlit Rerun Safety
```python
# All mutable objects checked for existence:
if 'mapbiomas_layers' not in st.session_state:
    st.session_state.mapbiomas_layers = {}

# Cache decorator prevents redundant NN calls:
@st.cache_data
def load_mapbiomas_cached():
    return load_mapbiomas()
```

---

## Testing Modules

### `test_ee_export.py`
- Tests export to Cloud Storage
- Verifies file creation in `gs://yvynation-bucket`

### `test_png_export.py`
- Tests map screenshot functionality
- Validates PNG file quality

### `test_hansen_consolidation.py` (archive)
- Legacy tests for consolidated class mapping

---

## Configuration & Secrets

### Environment Variables (Production)
```bash
# Google Cloud / Cloud Run
EE_PRIVATE_KEY          # Service account private key (newlines as \n)
EE_SERVICE_ACCOUNT_EMAIL # e.g., yvynation@ee-leandromet.iam.gserviceaccount.com
GCP_PROJECT_ID          # e.g., ee-leandromet
```

### Streamlit Cloud Secrets
```toml
# .streamlit/secrets.toml
[gcp]
private_key = "..."
service_account_email = "..."
project_id = "ee-leandromet"
```

---

## Related Documentation

See also:
- `DOCUMENTATION_INDEX.md` – Full documentation directory
- `PROJECT_STRUCTURE.md` – File/folder organization
- `REFLEX_CONVERSION_SUMMARY.md` – Planned Reflex UI migration
- `README.md` – User-facing overview

---

## Summary Table

| Layer | Module | Responsibility |
|-------|--------|-----------------|
| **Configuration** | `config.py`, `translations.py` | Constants, labels, project settings |
| **Auth & EE** | `ee_auth.py` | Google Earth Engine initialization |
| **Data Loading** | `load_data.py` | Load EE assets (MapBiomas, territories, satellites) |
| **Analysis (Core)** | `analysis.py` | Pixel-level area/change calculations |
| **Analysis (Regional)** | `mapbiomas_analysis.py`, `hansen_analysis.py`, `gfc_analysis.py`, `territory_analysis.py` | Dataset-specific analysis workflows |
| **Utilities** | `buffer_utils.py`, `geometry_upload.py`, `export_utils.py` | Spatial operations, I/O |
| **Visualization** | `map_manager.py`, `ee_layers.py`, `plots.py` | Maps, plots, layer rendering |
| **Mapping** | `visualization.py` | Geemap wrapper (legacy/support) |
| **UI Components** | `components/` | Streamlit-based interface |
| **UI Support** | `sidebar_components.py`, `map_components.py` | Sidebar controls, map tools |
| **Export** | `map_export_components.py`, `png_export.py`, `map_pdf_export.py` | Output generation |
| **Specialized** | `spot_module.py`, `hansen_consolidated_*.py`, `hansen_labels.py` | SPOT data, categorical mappings |

---

**End of Analysis**
