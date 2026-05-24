Summary of changes
🔧 Fixed: App unresponsive on initial load
Root cause: _load_territories_background() ran synchronously inside go_to_territory_analysis(), blocking the entire Reflex event loop while making 3 sequential EE API calls (10–30s). Every click during that period queued up and replayed after.

Fix (_territory.py, _ui.py):

_load_territories_background → load_territories_background, decorated with @rx.event(background=True) — runs in a worker thread
EE calls wrapped in asyncio.run_in_executor() so they don't block the async loop
State mutations batched in two async with self: blocks → map rebuilds only once at the end (was 3+ times before)
go_to_territory_analysis / go_to_geometry_analysis now yield the background task after switching the page — UI responds immediately
Removed the debug_all_territories() call that was silently making a full EE dump on every startup
🗺️ Fixed: Buffer not visible on map
Fix (_geometry.py, map_builder.py, state/init.py):

New state var buffer_geojson_features stores the buffer ring as GeoJSON after calling .getInfo() during creation
build_map() takes a new buffer_features param and renders them as a blue dashed ring (distinct from territory's orange)
map_html depends on buffer_geojson_features so it rebuilds when a buffer is created
✅ Fixed: "Select a geometry first" on territory buffer
Fix (_geometry.py, territory_sidebar.py):

handle_create_buffer now falls back to selected_territory when no drawn feature is selected
create_buffer_from_geometry checks the GeoJSON cache first (no extra EE call), then drawn features, then EE service as last resort
Buffer input now shows km (not m), default placeholder 10
Active buffer name shown in sidebar
Added ⚡ Auto-buffer notice when enabled
⚡ Auto-buffer on territory selection
New state vars: auto_buffer_enabled: bool = True, auto_buffer_km: float = 10.0
set_selected_territory auto-calls create_territory_auto_buffer(10.0) after GeoJSON is cached — uses the fast cache path (no extra EE round-trip until analysis runs)
📊 Side-by-side buffer analysis results
Fix (_analysis.py, analysis_tabs.py):

run_mapbiomas_analysis_on_territory and run_hansen_glad_analysis_on_territory automatically run the same analysis on the buffer if current_buffer_for_analysis is active
Results stored in buffer_mapbiomas_result / buffer_hansen_result
MapBiomas tab and Hansen/GLAD tab show a blue "Buffer Zone Comparison" section below with side-by-side metric cards and charts (territory vs buffer)