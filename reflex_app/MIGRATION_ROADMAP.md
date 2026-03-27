# Yvynation: Streamlit → Reflex Migration Roadmap

## Overview
The old Streamlit app has **7 architectural layers**. We're porting them in order of dependency.

**Current Status: Phase 3 (Analysis) - FOUNDATION COMPLETE** ✅

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

## Phase 4: Visualization (Next) ⏸️
### Layer D: Charts & Map Overlays

| Module | Purpose | Reflex Approach | Status |
|--------|---------|-----------------|--------|
| `plots.py` | Matplotlib bar/line charts | → `rx.plotly()` (more interactive) | ⏳ Todo |
| `ee_layers.py` | EE tile visualization | → Folium GeoJSON layers | ⏳ Todo |
| `map_manager.py` | Map setup | → Folium base + functions | ✅ 50% |

**Implementation Details:**

#### Plotly Integration (Better than Matplotlib)
```python
# Instead of Streamlit's st.pyplot(fig):
# Create Plotly figures directly, embed in Reflex

# Example: Land cover bar chart
def plot_mapbiomas_results(df):
    fig = go.Figure(data=[
        go.Bar(x=df['Class_Name'], y=df['Area_ha'], name='Area (ha)')
    ])
    return fig

# In Reflex:
rx.plotly(data=result_plot)
```

**Tasks:**
- [ ] Port all matplotlib → plotly conversions
- [ ] Create visualization functions for each analysis type
- [ ] Add export-to-image for charts
- [ ] Create dashboard-style layouts

**Effort:** 8-10 hours

#### EE Tile Layer Caching
```python
# Critical for performance:
# Cache getMapId() results in AppState._tile_cache
# Avoid 1-2 sec delay on each layer toggle

def add_ee_layer_with_cache(map_obj, ee_image, name, year):
    cache_key = f"{name}_{year}"
    if cache_key not in AppState._tile_cache:
        tile_id = ee_image.getMapId()  # 1-2 sec EE call
        AppState._tile_cache[cache_key] = tile_id
    return AppState._tile_cache[cache_key]
```

**Tasks:**
- [ ] Implement tile caching in AppState
- [ ] Add EE tile layers to Folium map
- [ ] Create layer toggle buttons in sidebar
- [ ] Test with multiple layers

**Effort:** 6-8 hours

---

## Phase 5: Export & Reporting (Week 6)
### Layer E: Output Generation

| Module | Purpose | Reflex Approach | Status |
|--------|---------|-----------------|--------|
| `export_utils.py` | ZIP bundles (data+figures) | → Backend task queue | ⏳ Todo |
| `png_export.py` | Static map pngs | → Selenium headless or API | ⏳ Todo |
| `map_pdf_export.py` | PDF reports with maps | → ReportLab or WeasyPrint | ⏳ Todo |

**Implementation Strategy:**

#### ZIP Export
```python
# AppState.export_analysis_results()
#   → Collects all CSVs, images, metadata
#   → Creates ZIP file
#   → Returns download link

# Reflex approach: Backend task queue + file download
```

**Tasks:**
- [ ] Create `ExportManager` utility class
- [ ] Port ZIP creation logic
- [ ] Implement result file staging
- [ ] Add download button to results panel

**Effort:** 6-8 hours

#### PDF Reports (Optional - Phase 2)
```python
# Advanced: Create formatted PDF with:
# - Territory name & metadata
# - Results table
# - Chart images
# - Map snapshot
```

**Effort:** 8-12 hours (optional)

---

## Phase 6: UI Polish (Week 7)
### Layer F: Sidebar & Interactions

| Component | Purpose | Status |
|-----------|---------|--------|
| Territory selector | Dropdown with 28 Brazilian territories | ⏳ In Progress |
| Year range slider | MapBiomas 1985-2023 selection | ⏳ Todo |
| Layer toggles | Show/hide MapBiomas, Hansen, GFC | ⏳ Todo |
| Analysis tabs | MapBiomas, Hansen, GFC, Territory compare | ⏳ Todo |
| Results panel | Show analysis DataFrame + charts | ⏳ Todo |

**Tasks:**
- [ ] Organize sidebar with collapsible sections (already has structure)
- [ ] Add MapBiomas year selector
- [ ] Add Hansen year range
- [ ] Create analysis result tabs
- [ ] Add loading progress indicators
- [ ] Add error/success messages

**Effort:** 8-10 hours

---

## Phase 7: Testing & Optimization (Week 8)
- [ ] Unit tests for analysis functions
- [ ] Integration tests for AppState
- [ ] Performance testing (EE quota usage, tile caching)
- [ ] Error handling for edge cases
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
