# Application Architecture Diagram

## Overall Application Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    Yvynation - Main Entry                       │
│                  (streamlit_app.py - 345 lines)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    SIDEBAR                               │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  📊 Yvynation                                            │  │
│  │  └─ Load Core Data Button                               │  │
│  │  └─ Data Status                                         │  │
│  │  └─ About Section                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  MAIN CONTENT TABS                       │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │ [🇧🇷 MapBiomas] [🌍 Hansen/GLAD]                       │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Tab 1: MapBiomas (Brazil)                         │ │  │
│  │  │  ├─ Map (left column)                             │ │  │
│  │  │  │  ├─ render_map_controls()                      │ │  │
│  │  │  │  └─ create_ee_folium_map()                     │ │  │
│  │  │  └─ Analysis (right column)                        │ │  │
│  │  │     ├─ render_mapbiomas_area_analysis()           │ │  │
│  │  │     ├─ render_mapbiomas_territory_analysis()      │ │  │
│  │  │     ├─ render_mapbiomas_multiyear_analysis()      │ │  │
│  │  │     └─ render_mapbiomas_change_analysis()         │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Tab 2: Hansen/GLAD (Global)                       │ │  │
│  │  │  ├─ Map (left column)                             │ │  │
│  │  │  │  ├─ render_hansen_map_controls()               │ │  │
│  │  │  │  └─ create_ee_folium_map()                     │ │  │
│  │  │  └─ Analysis (right column)                        │ │  │
│  │  │     ├─ render_hansen_area_analysis()              │ │  │
│  │  │     ├─ render_hansen_multiyear_analysis()         │ │  │
│  │  │     └─ render_hansen_change_analysis()            │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                │                │
         ▼                ▼                ▼
   ┌──────────┐    ┌────────────┐    ┌─────────────┐
   │ mapbiomas│    │  hansen    │    │     ui      │
   │_analysis │    │ _analysis  │    │ _components │
   │  .py     │    │   .py      │    │    .py      │
   │~260 lines│    │~230 lines  │    │~120 lines   │
   └──────────┘    └────────────┘    └─────────────┘
```

## Module Responsibilities

### streamlit_app.py - Orchestrator
```
Responsibilities:
├─ Initialize Streamlit page config
├─ Setup session state
├─ Initialize Earth Engine
├─ Manage sidebar
├─ Create and manage tabs
├─ Create folium maps
└─ Import and call render functions

Lines: 345
Functions: 2 (init_earth_engine, create_ee_folium_map)
Expanders: 0
```

### mapbiomas_analysis.py - MapBiomas Analysis
```
Responsibilities:
├─ Render area analysis UI & logic
├─ Render territory analysis UI & logic
├─ Render multi-year analysis UI & logic
├─ Render change detection UI & logic
└─ Store results in session state

Lines: ~260
Functions: 4
  ├─ render_mapbiomas_area_analysis()
  ├─ render_mapbiomas_territory_analysis()
  ├─ render_mapbiomas_multiyear_analysis()
  └─ render_mapbiomas_change_analysis()
```

### hansen_analysis.py - Hansen Analysis
```
Responsibilities:
├─ Render area analysis UI & logic
├─ Render snapshot comparison UI & logic
├─ Render change detection UI & logic
├─ Convert histogram data to DataFrames
└─ Store results in session state

Lines: ~230
Functions: 4
  ├─ hansen_histogram_to_dataframe()  [helper]
  ├─ render_hansen_area_analysis()
  ├─ render_hansen_multiyear_analysis()
  └─ render_hansen_change_analysis()
```

### ui_components.py - Shared UI
```
Responsibilities:
├─ Render map controls (MapBiomas)
├─ Render map controls (Hansen)
├─ Render map instructions
├─ Render about section
└─ Provide reusable UI functions

Lines: ~120
Functions: 5
  ├─ render_map_controls()
  ├─ render_hansen_map_controls()
  ├─ render_map_instructions()
  ├─ render_load_button()
  └─ render_about_section()
```

## Data Flow Diagram

### MapBiomas Analysis Flow
```
User draws area on MapBiomas map
         │
         ▼
st.session_state.drawn_areas (geometry stored)
         │
         ▼
render_mapbiomas_area_analysis()
         │
         ├─ User selects year
         ├─ User clicks "Analyze"
         │
         ▼
calculate_area_by_class() [from analysis.py]
         │
         ▼
st.session_state.drawn_area_result (DataFrame)
st.session_state.drawn_area_year
         │
         ▼
plot_area_distribution() [from plots.py]
         │
         ▼
Display chart + statistics
```

### Hansen Analysis Flow
```
User draws area on Hansen map
         │
         ▼
st.session_state.drawn_areas (geometry stored)
         │
         ▼
render_hansen_area_analysis()
         │
         ├─ User selects year
         ├─ User clicks "Analyze"
         │
         ▼
Hansen Image Reduction (frequencyHistogram)
         │
         ▼
hansen_histogram_to_dataframe()
         │
         ▼
st.session_state.hansen_area_result (DataFrame)
st.session_state.hansen_area_year
         │
         ▼
matplotlib.pyplot (barh chart)
         │
         ▼
Display chart + statistics
```

## Session State Management

```
┌─────────────────────────────────────────────────────────┐
│                  st.session_state                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Core State                                             │
│  ├─ app: YvynationApp instance                         │
│  ├─ data_loaded: boolean                               │
│  └─ ee_module: Earth Engine module                     │
│                                                         │
│  Map State                                              │
│  ├─ map_center_lat, map_center_lon                    │
│  ├─ map_zoom                                           │
│  └─ map_object: folium map instance                   │
│                                                         │
│  Drawn Areas (shared)                                  │
│  ├─ drawn_areas: dict of geometries                   │
│  ├─ drawn_area_count: int                             │
│  └─ selected_drawn_area: str (name)                   │
│                                                         │
│  MapBiomas Results                                      │
│  ├─ drawn_area_result: DataFrame                       │
│  ├─ territory_result: DataFrame                        │
│  ├─ multiyear_results: dict                            │
│  └─ last_analyzed_geom: ee.Geometry                   │
│                                                         │
│  Hansen Results                                         │
│  ├─ hansen_area_result: DataFrame                      │
│  └─ hansen_area_year: str                              │
│                                                         │
│  Layer Controls                                         │
│  ├─ split_compare_mode: boolean                        │
│  ├─ split_left/right_year, opacity                     │
│  └─ hansen_year: str                                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Tab Isolation

```
┌────────────────────────────────────┐  ┌────────────────────────────────────┐
│     MapBiomas Tab (Active)         │  │    Hansen Tab (Inactive)           │
├────────────────────────────────────┤  ├────────────────────────────────────┤
│                                    │  │                                    │
│  Map: MapBiomas layers             │  │  Map: Hansen layers (separate)    │
│  Data: drawn_area_result           │  │  Data: hansen_area_result         │
│  (if analyzed)                     │  │  (if analyzed)                    │
│                                    │  │                                    │
│  Session State:                    │  │  Session State:                   │
│  ✓ Uses shared state               │  │  ✓ Uses shared state              │
│  ✓ Isolated data                   │  │  ✓ Isolated data                  │
│                                    │  │                                    │
│  Result: Clean, no reset needed   │  │  Result: Clean, no reset needed   │
│                                    │  │                                    │
└────────────────────────────────────┘  └────────────────────────────────────┘
     Click Hansen tab ──────────────────────────────────→
     (switch context, keep all session state)
```

## Function Call Hierarchy

```
streamlit_app.py
├─ init_earth_engine()
│  └─ ee.Initialize()
│
├─ MapBiomas Tab
│  ├─ render_map_controls()
│  │  └─ st.slider(), st.checkbox()
│  ├─ create_ee_folium_map(data_source="MapBiomas")
│  │  └─ geemap.ee_tile_layer()
│  ├─ render_mapbiomas_area_analysis()
│  │  ├─ calculate_area_by_class()
│  │  └─ plot_area_distribution()
│  ├─ render_mapbiomas_territory_analysis()
│  │  ├─ filter_territories_by_state()
│  │  └─ calculate_area_by_class()
│  ├─ render_mapbiomas_multiyear_analysis()
│  │  ├─ calculate_area_by_class()
│  │  └─ plot_area_comparison()
│  └─ render_mapbiomas_change_analysis()
│     └─ plot_temporal_trend()
│
└─ Hansen Tab
   ├─ render_hansen_map_controls()
   ├─ create_ee_folium_map(data_source="Hansen")
   ├─ render_hansen_area_analysis()
   │  ├─ ee.Image.reduceRegion()
   │  ├─ hansen_histogram_to_dataframe()
   │  └─ matplotlib.pyplot.barh()
   ├─ render_hansen_multiyear_analysis()
   │  ├─ hansen_histogram_to_dataframe()
   │  └─ matplotlib.pyplot.barh()
   └─ render_hansen_change_analysis()
      └─ matplotlib.pyplot.barh()
```

## File Dependencies

```
streamlit_app.py
├─ imports: mapbiomas_analysis
├─ imports: hansen_analysis
├─ imports: ui_components
├─ imports: app_file (YvynationApp)
├─ imports: visualization
└─ imports: config

mapbiomas_analysis.py
├─ imports: streamlit
├─ imports: ee
├─ imports: analysis (calculate_area_by_class)
└─ imports: plots

hansen_analysis.py
├─ imports: streamlit
├─ imports: ee
└─ imports: config (HANSEN_DATASETS)

ui_components.py
└─ imports: streamlit

All modules
└─ depend on: existing modules (analysis.py, plots.py, app_file.py, config.py, etc.)
```

