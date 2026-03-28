# Yvynation: Streamlit → Reflex Migration Roadmap

## Overview
The old Streamlit app has **7 architectural layers**. We're porting them in order of dependency.

**Current Status: Phase 7 (Testing) - IN PROGRESS** ⏳

---

## Phase 1: Foundation (Completed) ✅
### ✅ Map Component (Folium)
- [x] Folium integration with multi-basemap support
- [x] OpenStreetMap, Google Satellite, ArcGIS alternatives
- [x] Layout fixes for proper button visibility

### ✅ Layer A: Core Config & Authentication
| Module | Purpose | Location | Status |
|--------|---------|----------|--------|
| `config.py` | EE project ID, color palettes, labels | `/reflex_app/config/config.py` | ✅ Done |
| `ee_service.py` | Service account auth (3-tier) | `/reflex_app/utils/ee_service.py` | ✅ Done |
| `translations.py` | EN/PT strings (40+ keys) | `/reflex_app/utils/translations.py` | ✅ Done |

**Phase 1 Effort:** 6 hours total  
**Completion:** March 26, 2026

---

## Phase 2: Utilities & Data Processing (In Progress) ⏳
### ⏳ Layer B: Geometry & Buffer Tools

| Module | Purpose | Reflex Approach | Dependencies | Status |
|--------|---------|-----------------|--------------|--------|
| `geometry_handler.py` | KML/GeoJSON parsing | `/reflex_app/utils/geometry_handler.py` | ee_service | ✅ Done |
| `buffer_utils.py` | Buffer zone creation | `/reflex_app/utils/buffer_utils.py` | geometry_handler | ✅ Done |
| `geometry_upload.py` | Upload UI component | `/reflex_app/components/geometry_upload.py` | buffer_utils | ✅ Done |
| `AppState` methods | Geometry upload handlers | `/reflex_app/state.py` | all above | ✅ Done |
| `sidebar` integration | File upload in sidebar | `/reflex_app/components/sidebar.py` | all above | ✅ Done |

**Implemented Functions:**
- `geometry_handler.parse_geojson()` - Parse GeoJSON files
- `geometry_handler.parse_kml()` - Parse KML files  
- `geometry_handler.validate_geometry()` - Validate geometries
- `geometry_handler.get_bbox_from_geojson()` - Get bounds
- `buffer_utils.create_external_buffer()` - Create donut-shaped buffers
- `buffer_utils.convert_geojson_to_ee_geometry()` - GeoJSON → EE conversion
- `buffer_utils.convert_ee_geometry_to_geojson()` - EE → GeoJSON conversion
- `AppState.upload_geometry_from_geojson()` - Handle uploads
- `AppState.create_buffer_from_geometry()` - Create buffers
- `AppState.handle_geometry_upload()` - File drop handler
- `AppState.handle_create_buffer()` - Buffer creation handler

**UI Components:**
- File upload widget in sidebar (📤 Upload Geometry section)
- Buffer distance input + Create button
- Geometry loaded confirmation
- Error/success messages

**Tests Performed:**
- ✅ Compilation successful (0.916s)
- ✅ Full module import chain validated
- ✅ Async file handlers ready
- ✅ Sidebar integration complete

**Phase 2 Effort:** ~8 hours (geometry parsing, buffer ops, file upload UI)  
**Estimated Completion:** March 27, 2026

---

## Phase 3: Analysis Core (Foundation Complete) ✅
### ✅ Layer C: Land Cover Analysis Modules

| Module | Purpose | Location | Functions | Status |
|--------|---------|----------|-----------|--------|
| `analysis.py` | Generic EE calculations | `/reflex_app/utils/analysis.py` | 10+ utility functions | ✅ Done |
| `mapbiomas_analysis.py` | Brazil land cover (1985-2023) | `/reflex_app/utils/mapbiomas_analysis.py` | MapBiomasAnalyzer class | ✅ Done |
| `hansen_analysis.py` | Global forest loss/gain | `/reflex_app/utils/hansen_analysis.py` | HansenAnalyzer class | ✅ Done |
| `AppState` methods | Analysis triggers | `/reflex_app/state.py` | 2 async handlers | ✅ Done |
| `Drawing tool` | Map-based geometry drawing | Folium/Leaflet Draw | Draw toolbar | ✅ Done |

**Phase 3A: Generic Analysis Utilities** (Complete)
- `clip_classification_to_geometry()` - Clip images to AOI
- `calculate_area_by_class()` - Area statistics by class
- `calculate_change_area()` - Binary change detection
- `calculate_class_specific_change()` - Class-by-class loss/gain
- `compare_areas()` - Time period comparison
- `get_geometry_bounds()` - Bounding box extraction

**Phase 3B: MapBiomas Analysis** (Complete)
- `MapBiomasAnalyzer` class with methods:
  - `analyze_single_year()` - Single year land cover
  - `analyze_year_range()` - Multi-year analysis (1985-2023)
  - `compare_years()` - Temporal comparison
  - `get_change_timeline()` - Class-specific time series
  - `identify_forest_change()` - Natural forest loss/gain

**Phase 3C: Hansen Analysis** (Complete)
- `HansenAnalyzer` class with methods:
  - `get_tree_cover_2000()` - Baseline coverage
  - `get_forest_loss()` - Annual loss 2000-2023
  - `get_forest_gain()` - Gain detection (2000-2012)
  - `create_loss_timeline()` - Loss time series
  - `analyze_forest_dynamics()` - Comprehensive analysis

**Drawing Tool** (Complete)
- Added Leaflet Draw to Folium map
- Draw toolbar with Polygon, Polyline, Rectangle, Marker
- Enables field-defined geometries for analysis

**AppState Integration** (Complete)
- `run_mapbiomas_analysis_on_geometry()` - Async analysis trigger
- `run_mapbiomas_comparison()` - Year comparison trigger
- Both use uploaded or drawn geometry as AOI

**Tests Performed:**
- ✅ Compilation successful (0.677s)
- ✅ All utility functions can be imported
- ✅ Analyzer classes instantiate without errors
- ✅ MapBiomas singleton pattern works
- ✅ Hansen singleton pattern works
- ✅ Drawing tools render in map (Leaflet Draw)

**Phase 3 Effort:** ~12 hours (analysis utilities, two analyzer classes, integration)  
**Completion:** March 26, 2026

**Next Steps:**
- Phase 4: Visualization (Plotly charts)
- Phase 5: Export functionality
- Phase 6: UI polish + result tabs
- Phase 7: Testing & optimization

---

## Phase 4: Visualization (In Progress) ⏳
### Layer D: Charts & Map Overlays

| Module | Purpose | Reflex Approach | Status |
|--------|---------|-----------------|--------|
| `visualization.py` | Plotly charts (bar, pie, comparison, gains/losses, Sankey) | `rx.plotly()` reactive charts | ✅ Done |
| `analysis_tabs.py` | 6-tab analysis UI (MapBiomas, Hansen, GFC, AAFC, Comparison, About) | Reflex tabs + Plotly | ✅ Done |
| `results_panel.py` | Results display with charts, data tables, CSV download | Integrated with analysis_tabs | ✅ Done |
| `ee_layers.py` | EE tile visualization | Folium GeoJSON layers + tile cache | ✅ Done (Phase 3) |
| `map_manager.py` | Map setup | Folium base + functions | ✅ Done (Phase 3) |

**Phase 4A: Plotly Visualization** (Complete)
- `MapBiomasVisualizer.create_area_bar_chart()` - Horizontal bar chart with MapBiomas class colors
- `MapBiomasVisualizer.create_pie_chart()` - Land cover composition pie chart
- `MapBiomasVisualizer.create_comparison_chart()` - Side-by-side year comparison bars
- `HansenVisualizer.create_loss_timeline_chart()` - Annual loss line chart
- `HansenVisualizer.create_forest_balance_chart()` - Cover/Loss/Gain summary bars
- `HansenVisualizer.create_area_distribution_chart()` - Hansen class distribution
- `calculate_gains_losses()` - Compute area changes between years (replaces Streamlit plotting_utils)
- `create_gains_losses_chart()` - Diverging bar chart: green gains, red losses
- `create_change_percentage_chart()` - Percentage change bars
- `create_sankey_transitions()` - Plotly Sankey diagram for class transitions

**Phase 4B: Analysis Tabs Component** (Complete)
- 6 tabs matching Streamlit: MapBiomas | Hansen/GLAD | Hansen GFC | AAFC | Comparison | About
- Each tab has: summary metrics, Plotly charts, data tables, CSV download
- Comparison tab shows: side-by-side, gains/losses, % change, net summary
- About tab shows: territory info, available datasets

**Phase 4C: State Integration** (Complete)
- Computed `@rx.var` properties for chart data (auto-regenerate on analysis_results change)
- `mapbiomas_bar_chart`, `mapbiomas_pie_chart`, `hansen_balance_chart` — Plotly JSON
- `comparison_chart`, `gains_losses_chart`, `change_pct_chart` — comparison charts
- `analysis_table_data`, `analysis_table_columns` — for `rx.data_table()`
- Summary formatters: `analysis_summary_total_area`, `hansen_summary_cover/loss/gain`
- Territory comparison: `run_territory_comparison()` with year1/year2 selection
- CSV export: `download_analysis_csv()`, `download_comparison_csv()`
- Year comparison controls in sidebar and navbar

**Phase 4D: Remaining** (Todo)
- [ ] AAFC analysis handler for Canadian territories
- [ ] Sankey diagram display in comparison tab (EE transitions query)
- [ ] Export chart images (Plotly to PNG)
- [ ] PDF map export (port from map_pdf_export.py)

**Tests Performed:**
- ✅ All files pass Python syntax check
- ✅ visualization.py imports and functions validated
- ✅ All component files compile without errors

**Phase 4 Effort:** ~14 hours (visualization, tabs, state integration, comparison)
**Completion:** March 27, 2026 (core), remaining items in Phase 5

---

## Phase 5: Export & Reporting ✅
### Layer E: Output Generation

| Module | Purpose | Reflex Location | Status |
|--------|---------|-----------------|--------|
| `export_service.py` | ZIP bundles (data+figures+metadata) | `/reflex_app/utils/export_service.py` | ✅ Done |
| `map_export_service.py` | PDF maps with EE layers & overlays | `/reflex_app/utils/map_export_service.py` | ✅ Done |
| `export_panel.py` | Export UI with tabs (ZIP/PDF) | `/reflex_app/components/export_panel.py` | ✅ Done |
| `AppState` handlers | Export triggers & download | `/reflex_app/state.py` | ✅ Done |

**Phase 5A: ZIP Export Service** (Complete)
- `create_export_zip()` - Generates organized ZIP with:
  - `metadata.json` - Export timestamp, territory, source info
  - `geometries.geojson` - All drawn features as FeatureCollection
  - `territory/{name}/boundary.geojson` - Territory boundary from EE
  - `territory/{name}/{source}_{year}_data.csv` - Analysis CSVs per year
  - `territory/{name}/comparison_{y1}_vs_{y2}.csv` - Comparison data
  - `analysis/transitions.json` - Transition matrix data
  - `figures/{name}.html` - Interactive Plotly charts
  - `figures/{name}.png` - Static chart images (requires kaleido)
  - `README.txt` - Summary text
- `collect_export_data_from_state()` - Collects all exportable data from AppState

**Phase 5B: PDF Map Export** (Complete)
- `get_basemap_image()` - Downloads & stitches Google/ArcGIS tiles
- `get_ee_layer_image()` - Downloads EE raster layers (MapBiomas, Hansen)
- `create_pdf_map()` - Publication-quality PDF with:
  - Basemap or EE raster overlay
  - Territory boundary (purple), buffer zone (blue dashed)
  - Drawn polygons with numbered labels
  - Scale bar, grid, legend, title, timestamp
- `create_map_set()` - Generates PDF set for all active layers + satellite basemap
- `add_scale_bar()` - Cartographic scale bar (5/10/25/50 km)
- `get_geometry_bounds()` - Bounding box from features with padding

**Phase 5C: Export UI** (Complete)
- `export_panel()` - Tabbed export interface (Data & Figures | PDF Maps)
- Export manifest showing what will be included
- Status indicators (check marks for available data)
- Map count for PDF generation
- Integrated below analysis results in main layout

**Phase 5D: State Handlers** (Complete)
- `export_analysis_zip()` - Generate ZIP + trigger `rx.download()`
- `export_pdf_maps()` - Generate PDF set (single PDF or ZIP of multiple)
- `export_pending`, `map_export_pending` flags for loading UI

**Tests Performed:**
- ✅ All files pass Python syntax check
- ✅ export_service.py imports validated
- ✅ map_export_service.py imports validated

**Phase 5 Effort:** ~10 hours
**Completion:** March 27, 2026

---

## Phase 6: UI Polish (Next) ⏳
### Layer F: Sidebar & Interactions

| Component | Purpose | Status |
|-----------|---------|--------|
| Territory selector | Dropdown with search filtering | ✅ Done |
| Year selector grid | MapBiomas 1985-2023 bingo-card style | ✅ Done |
| Year comparison | Side-by-side year selectors + compare button | ✅ Done (Phase 4) |
| Layer toggles | Show/hide MapBiomas, Hansen, GFC | ✅ Done |
| Analysis tabs | 6 tabs: MapBiomas, Hansen, GFC, AAFC, Comparison, About | ✅ Done (Phase 4) |
| Results panel | Plotly charts + data tables + CSV download | ✅ Done (Phase 4) |
| Export panel | ZIP + PDF export with manifest | ✅ Done (Phase 5) |
| AAFC analysis | Canadian crop inventory handler | ⏳ Todo |
| Sankey display | Pixel transitions via EE query | ⏳ Todo |
| Responsive layout | Mobile-friendly sidebar + map | ⏳ Todo |

**Remaining Tasks:**
- [ ] AAFC analysis handler for Canadian territories
- [ ] Sankey transitions computation (EE frequencyHistogram)
- [ ] Mobile responsive design
- [ ] Buffer zone analysis in export
- [ ] Keyboard shortcuts

**Effort:** 6-8 hours

---

## Phase 7: Testing & Optimization ⏳

### Drawing Capture Fix (Complete) ✅
- [x] JavaScript bridge injected into Folium map HTML (map_builder.py)
- [x] Leaflet Draw events (draw:created, draw:edited, draw:deleted) captured to `window._yvyDrawnFeatures`
- [x] "Save Drawing" button uses `rx.call_script()` to extract features from iframe
- [x] `load_geojson_from_browser()` receives and processes GeoJSON from browser
- [x] Error handling for bridge initialization failures and empty drawings

### Unit Tests (Complete) ✅
- [x] `test_geometry_handler.py` - 32 tests: GeoJSON/KML parsing, validation, bbox
- [x] `test_visualization.py` - 27 tests: MapBiomas/Hansen charts, gains/losses, Sankey
- [x] `test_export_service.py` - 14 tests: ZIP generation, GeoJSON export, metadata
- [x] `test_analysis.py` - 9 tests: compare_areas() pure logic
- [x] `test_state.py` - 9 tests: load_geojson_from_browser() all paths

### Remaining
- [ ] Performance testing (EE quota usage, tile caching)
- [ ] Documentation

**Effort:** 8-12 hours

---

## Implementation Priority Matrix

```
┌─────────────────────┬──────────────┬──────────────┐
│ Component           │ Dependencies │ User Impact  │
├─────────────────────┼──────────────┼──────────────┤
│ 1. Config & Auth    │ None         │ Foundation   │
│ 2. Geometry Upload  │ Config       │ High        │
│ 3. MapBiomas        │ Auth, Config │ High        │
│ 4. Hansen           │ MapBiomas    │ High        │
│ 5. Plotly Charts    │ Analysis     │ Medium      │
│ 6. Sidebar UI       │ All above    │ Medium      │
│ 7. Exports          │ All above    │ Low         │
│ 8. PDF Reports      │ Exports      │ Low         │
└─────────────────────┴──────────────┴──────────────┘
```

---

## Timeline Summary

| Phase | Components | Effort | Timeline |
|-------|-----------|--------|----------|
| ✅ 0 | Map (Folium) | 4h | Done |
| 1 | Config & Auth | 4h | Week 1 |
| 2 | Geometry & Buffers | 10h | Week 2-3 |
| 3 | Analysis Modules | 40h | Week 3-5 |
| 4 | Visualization | 14h | Week 5-6 |
| 5 | Export & Reports | 14h | Week 6-7 |
| 6 | UI Polish | 10h | Week 7 |
| 7 | Testing | 12h | Week 8 |
| **TOTAL** | **All Layers** | **~108h** | **8 weeks** |

---

## Reflex-Specific Considerations

### 1. **State Management**
- Use `AppState` for all analysis results
- Avoid storing large DataFrames in state (use session files)
- Implement caching for EE tile URLs

### 2. **Async Analysis**
- Long EE queries (>10 sec) should use background tasks
- Update UI with progress messages
- Implement timeout handling

### 3. **File Handling**
- Geometry uploads: Use `rx.upload()` with temp storage
- Use `/tmp/` for intermediate files
- Clean up after export

### 4. **Performance**
- Cache EE tile URLs aggressively
- Batch EE requests where possible
- Lazy-load layers (don't compute all layers upfront)

### 5. **Error Handling**
- Wrap all EE calls in try/catch
- Return user-friendly error messages
- Log technical errors server-side

---

## Next Steps

1. **This Week:** Ports config.py, ee_auth.py, update translations
2. **Week 2:** Implement geometry upload + buffer tools
3. **Week 3:** Start MapBiomas analysis
4. **Week 4:** Complete Hansen analysis
5. **Week 5:** Visualization layer (Plotly charts)
6. **Week 6:** Export functionality
7. **Week 7:** UI refinement
8. **Week 8:** Testing & deployment

---

## Questions Before Starting?

- Should we port PDF export (complex, lower priority)?
- Do we need all 28 MapBiomas years, or subset for MVP?
- Prioritize global (Hansen) or Brazil-focused (MapBiomas) first?
- File upload: KML/GeoJSON/Shapefile or just GeoJSON?
