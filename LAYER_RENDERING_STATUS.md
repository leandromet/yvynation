# Layer Rendering Implementation Status

## ✅ COMPLETED
- [x] State management for layer selections
  - `mapbiomas_displayed_years: List[int]` - tracks selected years
  - `hansen_displayed_layers: List[str]` - tracks selected layer types
  
- [x] Sidebar UI for adding/removing layers
  - Year selector grid (MapBiomas 1985-2023)
  - Hansen year buttons + data type selectors
  - Active layers display with remove buttons
  
- [x] Clear layers functionality
  - Added `AppState.clear_all_layers()` method
  - Clears both MapBiomas and Hansen selections
  
- [x] Map component basic structure
  - Base Folium map with multiple basemaps
  - Leaflet Draw tool for geometry
  - Layer control panel
  - Status badges showing selected layers count

## ⚠️ IN PROGRESS / PARTIAL
- [ ] **Earth Engine tile rendering** (BLOCKING ISSUE)
  - State correctly tracks selected layers ✓
  - Map HTML is generated once ✗
  - Map doesn't re-render when state changes ✗
  - EE layer tiles are never added ✗

## 🔴 NOT IMPLEMENTED

### The Core Problem
Reflex and Folium don't easily integrate for reactive map updates:

1. **Folium generates static HTML** - once created, HTML doesn't change
2. **Reflex is reactive** - components re-render when state changes
3. **Python Earth Engine calls can't be in React render** - causes issues with hydration

When user clicks "Add MapBiomas 1985":
```
User clicks → AppState.add_mapbiomas_layer(1985)
          ↓
State updates: mapbiomas_displayed_years = [1985] ✓
          ↓
Component re-renders
          ↓
create_base_map() called again... BUT it doesn't check state!
          ↓
Same HTML generated, no EE tiles added ✗
```

### Solutions (in order of preference)

#### **Solution 1: Custom Leaflet Component** (RECOMMENDED)
**Complexity:** High | **Performance:** Excellent | **Time:** 2-4 hours

Create a new component that:
- Uses Leaflet.js directly (not Folium's HTML)
- Renders to a div instead of HTML string
- Listens to AppState changes
- Dynamically adds WMS tile layers when state changes
- Handles EE tile URL generation

```python
# In map.py - pseudocode
class MapComponent(rx.Component):
    def render(self):
        return rx.html("""
            <div id='map'></div>
            <script>
                // Initialize Leaflet
                // Set up state listener
                // When mapbiomas_displayed_years changes:
                //   - Get MapBiomas tiles
                //   - Add to map
            </script>
        """)
```

#### **Solution 2: Backend Map Generator** (SIMPLE)
**Complexity:** Low | **Performance:** OK | **Time:** 1-2 hours

- Add route in backend that generates Folium map with layers
- Pass selected layers as parameters
- Have frontend call endpoint when state changes
- Cache generated maps to reduce EE calls

```python
# endpoints.py
@router.post("/api/map/generate")
def generate_map(years: List[int], hansen: List[str]):
    m = create_folium_map()
    for year in years:
        m = add_mapbiomas_layer(m, mapbiomas_coll, year)
    return {"map_html": m._repr_html_()}
```

#### **Solution 3: JavaScript Tile Injection** (QUICK)
**Complexity:** Medium | **Performance:** OK | **Time:** 1 hour

- Keep current Folium base map
- Inject JavaScript after HTML loads
- Use Leaflet's addLayer methods
- Load tile URLs from backend API

### Current Code Files

**State Management** (`state.py`)
- `mapbiomas_displayed_years: List[int]`
- `hansen_displayed_layers: List[str]`
- `add_mapbiomas_layer(year)` - adds to list
- `add_hansen_layer(layer_type)` - adds to list  
- `clear_all_layers()` - clears both lists (NEW)

**Map Component** (`components/map.py`)
- `create_base_map()` - creates Folium map (no layer logic yet)
- `leaflet_map()` - Reflex component with base map + status badges
- `map_metrics()` - displays layer counts

**EE Service** (`utils/ee_service_extended.py`)
- `get_mapbiomas()` - loads MapBiomas ImageCollection (NEW)
- `analyze_mapbiomas()` - analysis function

**EE Layers** (`utils/ee_layers.py`)
- `add_mapbiomas_layer(m, coll, year)` - adds layer to Folium map
- `add_hansen_layer(m, year)` - adds layer to Folium map
- `_cached_get_map_id()` - caches EE tile URLs

### What Works Now
```
User selects "MapBiomas 1985"
  ↓
on_click triggers: AppState.add_mapbiomas_layer(1985)
  ↓
State updates: mapbiomas_displayed_years = [1985]
  ↓
Sidebar updates to show "MapBiomas: 1 layer" ✓ WORKS
  ↓
Map status badge shows "MapBiomas: 1" ✓ WORKS
  ↓  
But: Map still shows only base layer ✗ DOESN'T WORK
```

### Next Steps

**Short term** (to unblock user):
1. Implement Solution 2 (Backend map generator)
   - Less refactoring than custom component
   - Works with existing Folium code
   - Can show working demo quickly

**Medium term**:
2. Switch to Solution 1 (Custom Leaflet)
   - Better UX
   - More responsive
   - Supports advanced features

**Technical debt**:
3. Fix missing config imports (HANSEN_OCEAN_MASK, etc.)
4. Add proper error handling for EE call failures
5. Cache strategy for tile generation

## Configuration
**MapBiomas**: `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1`  
**Hansen**: `projects/glad/GLCLU2020/v2/LCLUC_YYYY` (YYYY = 2000, 2005, 2010, 2015, 2020)

## Testing
To test current state tracking:
1. Run app: `reflex run` 
2. Click "Add Layer" buttons in sidebar
3. Observe sidebar updates ✓
4. Observe status badge updates ✓
5. Observe map (currently only base map visible) ✗

To test layer rendering (once implemented):
1. Click "Add MapBiomas 1985"
2. Observe satellite data appears on map ✓
