"""
Key architectural differences and optimization tips.
"""

# PERFORMANCE OPTIMIZATION GUIDE

## 1. State Management Best Practices

### ✅ DO
- Keep state flat and simple
- Use computed properties for derived values
- Cache expensive computations

```python
class AppState(rx.State):
    territories: List[str] = []
    selected_territory: str = ""
    
    @rx.var
    def is_territory_selected(self) -> bool:
        """Computed property."""
        return bool(self.selected_territory)
```

### ❌ DON'T
- Create nested state structures
- Store UI-only state in AppState (use local component state)
- Run heavy computations in render phase

## 2. Component Rendering

### ✅ DO
- Use `rx.cond()` for conditional rendering
- Use `rx.foreach()` for list rendering
- Memoize expensive components

```python
def expensive_component() -> rx.Component:
    """Cache this if computation is expensive."""
    return rx.box(...)

# In render:
rx.cond(
    AppState.show_component,
    expensive_component(),
)
```

### ❌ DON'T
- Render all variations and hide with CSS
- Create components inside events
- Use complex Python logic in render functions

## 3. Async Operations

### ✅ DO
- Use async/await for I/O operations
- Show loading state immediately
- Handle errors gracefully

```python
class AppState(rx.State):
    is_analyzing: bool = False
    
    async def analyze_territory(self):
        self.is_analyzing = True
        try:
            results = await EarthEngineService.analyze_mapbiomas_geometry(...)
            self.analysis_results = results
        except Exception as e:
            self.set_error(str(e))
        finally:
            self.is_analyzing = False
```

### ❌ DON'T
- Block the main thread with sync operations
- Forget error handling
- Leave loading states hanging

## 4. Earth Engine Integration

### ✅ DO
- Use service layer for EE operations
- Cache results in state
- Handle rate limits with retries

```python
from yvynation.utils.ee_service import EarthEngineService

class AppState(rx.State):
    async def fetch_analysis(self):
        df = await EarthEngineService.analyze_mapbiomas_geometry(...)
        self.results = df.to_dict()  # Convert to serializable format
```

### ❌ DON'T
- Call EE API directly from components
- Store EE objects in state (not serializable)
- Ignore authentication errors

## 5. Map Interactions

### ✅ DO
- Handle map events in JavaScript, push results to state
- Debounce pan/zoom events (avoid 100s of updates)
- Cache tile layers

```python
# In leaflet.py:
# JavaScript debounces map events, sends only meaningful changes
map.on('moveend', debounce(() => {
    updateReflex({bounds, center, zoom})
}, 500))
```

### ❌ DON'T
- Update state on every pixel movement
- Re-render entire map on state change
- Load full-resolution tiles for overview

## 6. Data Serialization

### ✅ DO
- Convert DataFrames to dicts/JSON before storing
- Keep state serializable (JSON-compatible)
- Use TypedDict for complex state

```python
class AppState(rx.State):
    # ✅ Serializable
    results: Dict[str, Any] = {}
    
    # ❌ NOT serializable
    # dataframe: pd.DataFrame = None
    # geometry: ee.Geometry = None
```

### ❌ DON'T
- Store non-serializable objects (EE, GDF, etc.)
- Keep DataFrames in state
- Use datetime objects (convert to ISO strings)

## 7. Network Requests

### ✅ DO
- Use httpx for async requests
- Set reasonable timeouts
- Implement retry logic

```python
import httpx

async def fetch_data(url: str):
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        return response.json()
```

### ❌ DON'T
- Use requests (blocking)
- Set no timeout
- Ignore failed requests silently

## 8. Memory Management

### Challenge
For large analyses (10K+ territories), memory can grow:
- Each state instance is ~1MB
- 1000 concurrent users = ~1GB
- Cloud Run instances have 2GB limit

### Solution

**Use database persistence:**
```python
# Save large results to database, keep pointer in state
class AppState(rx.State):
    analysis_id: str = ""  # Reference to DB record
    
    async def save_analysis(self):
        # Save to database
        db_id = await save_to_database(self.analysis_results)
        self.analysis_id = db_id
        self.analysis_results = {}  # Clear memory
```

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Map pan/zoom | < 100ms | JS handles, debounced |
| Layer toggle | < 200ms | Server-side TMS or GEE |
| Territory select | < 50ms | State update only |
| Analysis start | < 500ms | Load dialog appears |
| Analysis complete | < 30s | For ~100 sq km area |

## Monitoring

```python
import time

class AppState(rx.State):
    def time_operation(self, op_name: str):
        start = time.time()
        # ... operation ...
        elapsed = time.time() - start
        logger.info(f"{op_name} took {elapsed:.2f}s")
```

## Cloud Run Sizing

For production:

```bash
# Small: < 100 concurrent users
--memory 1Gi --cpu 1

# Medium: 100-500 users
--memory 2Gi --cpu 2

# Large: 500+ users
--memory 4Gi --cpu 4
--max-instances 100
--region us-central1
```

---

**Remember**: Reactive state management is fast, but network I/O is the bottleneck. 
Optimize data fetching over rendering speed.
