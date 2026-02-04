# External Buffer Zone Feature Implementation

## Overview
Added functionality to create external buffer zones (ring/donut shapes) around indigenous territories and drawn polygons for land cover analysis. Buffers appear in the polygon selector and can be analyzed like regular polygons.

## Files Created

### 1. buffer_utils.py (NEW)
Location: `/home/leandromb/google_eengine/yvynation/buffer_utils.py`

**Key Functions:**
- `create_external_buffer(geometry, distance_km)` - Creates ring-shaped buffer using Earth Engine's `.buffer()` and `.difference()` methods
- `add_buffer_to_session_state(geometry, buffer_size_km, source_name)` - Stores buffer in session state with metadata
- `get_buffer_as_feature(buffer_name)` - Converts buffer to GeoJSON feature format
- `add_buffer_to_polygon_list(buffer_name)` - Adds buffer to all_drawn_features list for selection
- `get_buffer_info(buffer_name)` - Retrieves buffer metadata
- `remove_buffer(buffer_name)` - Removes buffer from session
- `list_all_buffers()` - Lists all active buffers

## Files Modified

### 2. sidebar_components.py
**Changes:**
- Added import: `from buffer_utils import add_buffer_to_session_state, add_buffer_to_polygon_list`
- Added buffer UI in `render_territory_analysis()`:
  - Buffer distance selector (2km/5km/10km dropdown)
  - "🔵 Create Buffer" button
  - Success messages and user guidance
  - Automatic addition to polygon list

**Location in code:** After territory "Zoom to Territory" button, before territory analysis logic

### 3. map_components.py
**Changes:**
- Added imports: `from buffer_utils import add_buffer_to_session_state, add_buffer_to_polygon_list`, `import traceback`
- Modified `render_polygon_selector()`:
  - Detects buffer features via `properties.type == 'external_buffer'`
  - Shows buffer indicator (🔵) in polygon labels
  - Adds buffer creation UI for regular polygons (same 2km/5km/10km options)
  - Automatically refreshes page after buffer creation
- Modified `build_and_display_map()`:
  - Added buffer visualization section after analysis layers
  - Buffers rendered as GeoJson layers with sky-blue color (#00BFFF)
  - Distinct styling with semi-transparent fill (opacity 0.15)
  - Highlight on hover
- Modified `render_layer_reference_guide()`:
  - Added "External Buffer Zone" to legend with sky-blue color indicator

### 4. streamlit_app.py
**Changes:**
- Added session state initialization:
  ```python
  if "buffer_geometries" not in st.session_state:
      st.session_state.buffer_geometries = {}
  if "buffer_metadata" not in st.session_state:
      st.session_state.buffer_metadata = {}
  ```
- Modified geometry extraction logic:
  - Detects buffer features via `properties.type == 'external_buffer'`
  - Shows buffer name in analysis section
  - Existing analysis workflow automatically works with buffers

## User Workflow

### Creating Buffer from Territory:
1. Navigate to sidebar → "🏛️ Indigenous Territories Analysis"
2. Select a territory
3. Scroll to "Create External Buffer Zone" section
4. Choose distance (2km, 5km, or 10km)
5. Click "🔵 Create Buffer"
6. Buffer appears in polygon selector below the map

### Creating Buffer from Drawn Polygon:
1. Draw a polygon on the map
2. Polygon appears in "🎨 Select Polygon to Analyze" section
3. Select the polygon
4. "Create External Buffer Zone" UI appears
5. Choose distance and click "🔵 Create Buffer"
6. Buffer automatically added to polygon list

### Analyzing a Buffer:
1. Select buffer from polygon dropdown (marked with 🔵)
2. Buffer geometry automatically loaded
3. Use any analysis tab (MapBiomas, Hansen, Comparison)
4. Results show land cover within the buffer zone (excluding original area)

## Technical Details

**Buffer Geometry Creation:**
```python
distance_meters = distance_km * 1000
buffered = geometry.buffer(distance_meters)
external_buffer = buffered.difference(geometry)  # Creates donut shape
```

**Buffer Storage:**
- `buffer_geometries`: {buffer_name: ee.Geometry}
- `buffer_metadata`: {buffer_name: {source_name, buffer_size_km, source_geometry, type}}

**Buffer Naming:**
- Format: "External Buffer {size}km - {source_name}"
- Example: "External Buffer 5km - Polygon 2"
- Example: "External Buffer 10km - Yanomami Territory"

**Map Visualization:**
- Color: Sky blue (#00BFFF / #0080FF)
- Fill opacity: 0.15
- Border weight: 2px
- Highlight on hover with increased opacity
- Visible in layer control as "Buffer: {name}"

## Integration Points

**Session State Variables:**
- `buffer_geometries` - Dictionary of buffer geometries
- `buffer_metadata` - Dictionary of buffer information
- `all_drawn_features` - Buffers added here for selection

**Feature Properties:**
- Buffer features have `properties.type = 'external_buffer'`
- Buffer features have `properties.name` with full buffer name
- Buffer features have `properties.metadata` with creation details

## Benefits

1. **Non-destructive Analysis**: Original geometry preserved, only buffer zone analyzed
2. **Consistent Interface**: Buffers work with existing analysis tools (no new UI needed)
3. **Persistent Storage**: Buffers stored in session state, survives page interactions
4. **Visual Feedback**: Buffers visible on map with distinct styling
5. **Flexible Distances**: Three common buffer sizes (2km, 5km, 10km)
6. **Clear Labeling**: Buffer names indicate source and distance
7. **Integrated Workflow**: Appears alongside regular polygons in selector

## Future Enhancements (Possible)

- Custom buffer distances (user input)
- Inner buffer zones (within geometry)
- Multiple concurrent buffers per source
- Buffer-to-buffer comparisons
- Export buffer geometries
- Save buffer configurations
- Buffer analysis history

## Testing Checklist

- [x] Create buffer from territory
- [x] Create buffer from drawn polygon
- [x] Buffer appears in polygon selector
- [x] Buffer visible on map
- [x] Buffer can be selected for analysis
- [x] Buffer geometry correct (ring shape)
- [x] MapBiomas analysis works with buffer
- [x] Hansen analysis works with buffer
- [x] Buffer labeled correctly in UI
- [x] Multiple buffers can coexist
- [x] Page refresh preserves buffers (within session)
- [x] Legend includes buffer indicator

## Notes

- Buffers are Earth Engine geometries, processed server-side
- Buffer calculation happens instantly (no loading time)
- GeoJSON conversion for map display may take 1-2 seconds for large territories
- Buffers excluded from original geometry ensure no double-counting in analysis
- Buffer distances are geodesic (true distances on Earth's surface)
