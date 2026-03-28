"""
Map builder module - generates Folium maps with Earth Engine layers.
Replicates the Streamlit pattern: iterate through selected layers and add them to the map.
"""

import folium
from folium.plugins import Draw
from typing import List, Optional
import logging
import ee

logger = logging.getLogger(__name__)


def _ensure_ee_initialized():
    """Ensure Earth Engine is initialized."""
    try:
        # Test if EE is already initialized
        ee.Image('USGS/SRTM90_V4').getInfo()
        logger.info("✓ Earth Engine already initialized")
        return True
    except Exception as e:
        try:
            logger.info("Initializing Earth Engine...")
            ee.Initialize()
            logger.info("✓ Earth Engine initialized")
            return True
        except Exception as init_error:
            logger.error(f"Failed to initialize Earth Engine: {init_error}")
            return False


def build_map(
    mapbiomas_years: List[int] = None,
    hansen_layers: List[str] = None,
    geometry_features: List[dict] = None,
    change_mask_years: Optional[tuple] = None,
    change_mask_geometry: Optional[dict] = None,
) -> str:
    """
    Build a complete Folium map with Earth Engine layers, geometry overlays,
    and optional change mask.

    Args:
        mapbiomas_years: List of years to display (e.g., [1985, 2023])
        hansen_layers: List of Hansen layer identifiers (e.g., ["2020"])
        geometry_features: List of GeoJSON feature dicts to overlay on the map
        change_mask_years: Tuple (year1, year2) for MapBiomas change mask layer
        change_mask_geometry: GeoJSON geometry dict to clip the change mask to

    Returns:
        HTML string of the complete map
    """
    try:
        # Ensure EE is initialized
        if not _ensure_ee_initialized():
            logger.warning("Earth Engine not initialized - layers may not work")
        
        # Create base map centered on Brazil
        display_map = folium.Map(
            location=[-10, -52],
            zoom_start=5,
            tiles="OpenStreetMap"
        )
        
        logger.info(f"Base map created. MapBiomas years: {mapbiomas_years}, Hansen: {hansen_layers}")
        
        # Add alternative basemaps
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=False,
            control=True
        ).add_to(display_map)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri',
            name='ArcGIS Street',
            overlay=False,
            control=True
        ).add_to(display_map)
        
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles &copy; Esri',
            name='ArcGIS Satellite',
            overlay=False,
            control=True
        ).add_to(display_map)
        
        # ADD MAPBIOMAS LAYERS - following Streamlit pattern
        layers_added = 0
        if mapbiomas_years and len(mapbiomas_years) > 0:
            try:
                from .ee_service_extended import ExtendedEarthEngineService
                from .ee_layers import add_mapbiomas_layer
                
                ee_service = ExtendedEarthEngineService()
                mapbiomas_coll = ee_service.get_mapbiomas()
                logger.info(f"MapBiomas collection loaded")
                
                # Iterate through selected years (same as Streamlit)
                for year in mapbiomas_years:
                    try:
                        logger.info(f"Adding MapBiomas {year}...")
                        result = add_mapbiomas_layer(
                            display_map,
                            mapbiomas_coll,
                            year,
                            opacity=0.8,
                            shown=True
                        )
                        if result is not None:
                            display_map = result
                            # Check if layer was actually added
                            layer_count = len(display_map._children)
                            logger.info(f"✓ Added MapBiomas {year} - map now has {layer_count} children")
                            layers_added += 1
                        else:
                            logger.warning(f"Failed to add MapBiomas {year} - function returned None")
                    except Exception as e:
                        logger.error(f"Error adding MapBiomas {year}: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                logger.error(f"Error setting up MapBiomas layers: {e}")
                import traceback
                traceback.print_exc()
        
        # ADD HANSEN LAYERS - following Streamlit pattern
        if hansen_layers and len(hansen_layers) > 0:
            try:
                from .ee_layers import (
                    add_hansen_layer, 
                    add_hansen_gfc_tree_cover,
                    add_hansen_gfc_tree_loss,
                    add_hansen_gfc_tree_gain
                )
                
                # Iterate through selected layers (same as Streamlit)
                for layer_str in hansen_layers:
                    try:
                        # Check if it's a GFC layer type (cover, loss, gain) or a year
                        if layer_str in ['cover', 'loss', 'gain']:
                            # Route to GFC functions
                            logger.info(f"Adding Hansen {layer_str} layer (GFC)...")
                            if layer_str == 'cover':
                                result = add_hansen_gfc_tree_cover(display_map, opacity=0.8, shown=True)
                            elif layer_str == 'loss':
                                result = add_hansen_gfc_tree_loss(display_map, opacity=0.8, shown=True)
                            elif layer_str == 'gain':
                                result = add_hansen_gfc_tree_gain(display_map, opacity=0.8, shown=True)
                        else:
                            # Extract year from strings like "2020" or "Hansen 2020"
                            year_str = layer_str.split()[-1] if ' ' in layer_str else layer_str
                            logger.info(f"Adding Hansen {year_str}...")
                            
                            result = add_hansen_layer(
                                display_map,
                                year_str,
                                opacity=0.8,
                                shown=True,
                                use_consolidated=False
                            )
                        
                        if result is not None:
                            display_map = result
                            layer_count = len(display_map._children)
                            logger.info(f"✓ Added Hansen {layer_str} - map now has {layer_count} children")
                            layers_added += 1
                        else:
                            logger.warning(f"Failed to add Hansen {layer_str} - function returned None")
                    except Exception as e:
                        logger.error(f"Error adding Hansen {layer_str}: {e}")
                        import traceback
                        traceback.print_exc()
            except Exception as e:
                logger.error(f"Error setting up Hansen layers: {e}")
                import traceback
                traceback.print_exc()
        
        logger.info(f"Layers added: {layers_added}")

        # ADD GEOMETRY OVERLAYS - drawn/uploaded features shown on the map
        bounds_to_fit = None
        if geometry_features:
            try:
                import json
                fg = folium.FeatureGroup(name="Drawn Geometries", show=True)
                all_coords = []

                for idx, feat in enumerate(geometry_features):
                    geom = feat.get("geometry") or feat
                    geom_type = geom.get("type", "")
                    coords = geom.get("coordinates", [])

                    if not geom_type or not coords:
                        continue

                    name = feat.get("name", f"Geometry {idx + 1}")

                    # Collect coordinates for bounds calculation
                    def _flatten_coords(c, acc):
                        if isinstance(c[0], (int, float)):
                            acc.append(c[:2])
                        else:
                            for sub in c:
                                _flatten_coords(sub, acc)
                    _flatten_coords(coords, all_coords)

                    # Style: green dashed for territories, purple for drawn
                    if feat.get("_source") == "territory":
                        style = {
                            "fillColor": "#228B22",
                            "color": "#006400",
                            "weight": 3,
                            "fillOpacity": 0.1,
                            "dashArray": "5,5",
                        }
                    else:
                        style = {
                            "fillColor": "#8B5CF6",
                            "color": "#6D28D9",
                            "weight": 2.5,
                            "fillOpacity": 0.15,
                        }

                    geojson_feature = {
                        "type": "Feature",
                        "geometry": geom,
                        "properties": {"name": name, "index": idx},
                    }
                    folium.GeoJson(
                        geojson_feature,
                        name=name,
                        style_function=lambda x, s=style: s,
                        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Geometry:"]),
                    ).add_to(fg)

                fg.add_to(display_map)
                layers_added += 1
                logger.info(f"Added {len(geometry_features)} geometry overlay(s)")

                # Calculate bounds for zoom
                if all_coords:
                    lons = [c[0] for c in all_coords]
                    lats = [c[1] for c in all_coords]
                    bounds_to_fit = [[min(lats), min(lons)], [max(lats), max(lons)]]

            except Exception as e:
                logger.error(f"Error adding geometry overlays: {e}")
                import traceback
                traceback.print_exc()

        # ADD CHANGE MASK LAYER - difference between two MapBiomas years
        if change_mask_years and len(change_mask_years) == 2:
            try:
                year1, year2 = int(change_mask_years[0]), int(change_mask_years[1])
                from .ee_service_extended import ExtendedEarthEngineService
                ee_svc = ExtendedEarthEngineService()
                mapbiomas = ee_svc.get_mapbiomas()

                if mapbiomas:
                    img1 = mapbiomas.select(f"classification_{year1}")
                    img2 = mapbiomas.select(f"classification_{year2}")
                    # Change mask: 1 where class changed, 0 where same
                    change = img1.neq(img2).selfMask()

                    clip_geom = None
                    if change_mask_geometry:
                        clip_geom = ee.Geometry(change_mask_geometry)
                        change = change.clip(clip_geom)

                    vis = {"min": 0, "max": 1, "palette": ["#FF4444"]}
                    map_id = change.getMapId(vis)
                    tile_url = map_id["tile_fetcher"].url_format

                    folium.TileLayer(
                        tiles=tile_url,
                        attr=f"MapBiomas Change {year1}-{year2}",
                        name=f"Change Mask {year1} vs {year2}",
                        overlay=True,
                        control=True,
                        opacity=0.6,
                    ).add_to(display_map)
                    layers_added += 1
                    logger.info(f"Added change mask layer: {year1} vs {year2}")

                    # Add reference MapBiomas layers (deactivated) for the two years
                    try:
                        from ..config import MAPBIOMAS_PALETTE
                        ref_vis = {'min': 0, 'max': 62, 'palette': MAPBIOMAS_PALETTE}
                        for ref_year, ref_img in [(year1, img1), (year2, img2)]:
                            if clip_geom:
                                ref_img = ref_img.clip(clip_geom)
                            ref_map_id = ref_img.getMapId(ref_vis)
                            ref_tile_url = ref_map_id["tile_fetcher"].url_format
                            folium.TileLayer(
                                tiles=ref_tile_url,
                                attr=f"MapBiomas {ref_year}",
                                name=f"MapBiomas {ref_year} (ref)",
                                overlay=True,
                                control=True,
                                show=False,
                                opacity=0.8,
                            ).add_to(display_map)
                        logger.info(f"Added reference layers: {year1}, {year2} (deactivated)")
                    except Exception as ref_e:
                        logger.warning(f"Could not add reference layers: {ref_e}")

            except Exception as e:
                logger.error(f"Error adding change mask: {e}")
                import traceback
                traceback.print_exc()

        # Zoom to geometry bounds if available
        if bounds_to_fit:
            display_map.fit_bounds(bounds_to_fit, padding=(20, 20))
            logger.info(f"Map zoomed to geometry bounds: {bounds_to_fit}")

        # Add Leaflet Draw tool
        Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': True,
                'polygon': True,
                'rectangle': True,
                'circle': False,
                'circlemarker': False,
                'marker': True,
            }
        ).add_to(display_map)

        # Add layer control - IMPORTANT: this must be added AFTER all layers
        layer_control = folium.LayerControl(position='topright', collapsed=False)
        display_map.add_child(layer_control)
        logger.info(f"Layer control added")

        # Inject JavaScript bridge: captures Leaflet Draw events and stores
        # features in window._yvyDrawnFeatures so Reflex can read them via
        # rx.call_script(). This bridges the Folium iframe → Reflex gap.
        draw_bridge_js = """
        <script>
        (function() {
            // Wait for the map to be ready
            function initDrawBridge() {
                // Find the Leaflet map instance
                var mapEl = document.querySelector('.folium-map');
                if (!mapEl || !mapEl._leaflet_id) {
                    setTimeout(initDrawBridge, 200);
                    return;
                }

                // Get the map object from Leaflet's internal registry
                var map = null;
                for (var key in L.Map._instances || {}) {
                    map = L.Map._instances[key];
                    break;
                }

                // Fallback: iterate window properties to find the map
                if (!map) {
                    var maps = document.querySelectorAll('.folium-map');
                    for (var i = 0; i < maps.length; i++) {
                        var el = maps[i];
                        if (el._leaflet_id) {
                            // Access via Leaflet internal
                            for (var k in window) {
                                try {
                                    if (window[k] instanceof L.Map) {
                                        map = window[k];
                                        break;
                                    }
                                } catch(e) {}
                            }
                        }
                    }
                }

                if (!map) {
                    // Last resort: find map variable by searching Folium's generated names
                    var scripts = document.querySelectorAll('script');
                    for (var s = 0; s < scripts.length; s++) {
                        var txt = scripts[s].textContent;
                        var match = txt.match(/var\\s+(map_[a-f0-9]+)\\s*=\\s*L\\.map/);
                        if (match && window[match[1]]) {
                            map = window[match[1]];
                            break;
                        }
                    }
                }

                if (!map) {
                    console.warn('[YvyBridge] Could not find Leaflet map instance');
                    return;
                }

                console.log('[YvyBridge] Map found, setting up draw event listeners');

                // Find the FeatureGroup used by Leaflet Draw
                var drawnItems = null;
                map.eachLayer(function(layer) {
                    if (layer instanceof L.FeatureGroup && !(layer instanceof L.TileLayer)) {
                        drawnItems = layer;
                    }
                });

                if (!drawnItems) {
                    drawnItems = new L.FeatureGroup();
                    map.addLayer(drawnItems);
                }

                // Store reference globally
                window._yvyDrawnItems = drawnItems;
                window._yvyDrawnFeatures = {"type": "FeatureCollection", "features": []};
                window._yvyMap = map;

                // Helper: export all drawn features to GeoJSON
                function exportFeatures() {
                    var fc = {"type": "FeatureCollection", "features": []};
                    drawnItems.eachLayer(function(layer) {
                        if (layer.toGeoJSON) {
                            fc.features.push(layer.toGeoJSON());
                        }
                    });
                    // Also check for any draw layers on the map directly
                    map.eachLayer(function(layer) {
                        if (layer instanceof L.Path && layer.toGeoJSON && !drawnItems.hasLayer(layer)) {
                            // Check if it's a user-drawn layer (not a tile or base layer)
                            if (layer._leaflet_id && layer.editing) {
                                fc.features.push(layer.toGeoJSON());
                            }
                        }
                    });
                    window._yvyDrawnFeatures = fc;
                    console.log('[YvyBridge] Features exported:', fc.features.length);
                    return fc;
                }

                window._yvyExportFeatures = exportFeatures;

                // Listen for draw events
                map.on('draw:created', function(e) {
                    var layer = e.layer;
                    drawnItems.addLayer(layer);
                    exportFeatures();
                    console.log('[YvyBridge] draw:created -', e.layerType);
                });

                map.on('draw:edited', function(e) {
                    exportFeatures();
                    console.log('[YvyBridge] draw:edited');
                });

                map.on('draw:deleted', function(e) {
                    exportFeatures();
                    console.log('[YvyBridge] draw:deleted');
                });

                console.log('[YvyBridge] Draw bridge initialized successfully');
            }

            // Start initialization after a short delay to let Folium render
            if (document.readyState === 'complete') {
                setTimeout(initDrawBridge, 500);
            } else {
                window.addEventListener('load', function() {
                    setTimeout(initDrawBridge, 500);
                });
            }
        })();
        </script>
        """

        # Inject the bridge script into the map HTML
        from branca.element import Element
        bridge_element = Element(draw_bridge_js)
        display_map.get_root().html.add_child(bridge_element)
        logger.info("Draw bridge JavaScript injected")

        # Get the map HTML
        map_html = display_map._repr_html_()
        logger.info(f"Map HTML generated - length: {len(map_html)}")
        
        return map_html
        
    except Exception as e:
        logger.error(f"Critical error in build_map: {e}")
        import traceback
        traceback.print_exc()
        
        # Return basic map on error
        m = folium.Map(location=[-10, -52], zoom_start=5, tiles="OpenStreetMap")
        folium.LayerControl().add_to(m)
        return m._repr_html_()
