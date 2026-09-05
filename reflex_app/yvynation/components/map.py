"""
Map component for Yvynation Reflex app.
Renders Folium map with Earth Engine layers using reactive state.
Includes drawing capture with Leaflet Draw integration via JS bridge.
"""

import reflex as rx
from ..state import AppState
import logging

logger = logging.getLogger(__name__)


# JavaScript that reaches into the Folium iframe, extracts drawn features
# via the bridge we injected in map_builder.py, and returns the GeoJSON
# string to Reflex's call_script callback.
EXTRACT_DRAWINGS_JS = """
(function() {
    // The Folium map is rendered inside an iframe by rx.html()
    var iframes = document.querySelectorAll('#map-container iframe');
    if (!iframes.length) {
        // Might be embedded directly (no iframe)
        if (window._yvyExportFeatures) {
            var fc = window._yvyExportFeatures();
            return JSON.stringify(fc);
        }
        return JSON.stringify({"error": "No map iframe found and no direct bridge"});
    }

    var iframe = iframes[iframes.length - 1];
    try {
        var iframeWin = iframe.contentWindow || iframe.contentDocument;
        if (iframeWin && iframeWin._yvyExportFeatures) {
            var fc = iframeWin._yvyExportFeatures();
            return JSON.stringify(fc);
        } else if (iframeWin && iframeWin._yvyDrawnFeatures) {
            return JSON.stringify(iframeWin._yvyDrawnFeatures);
        } else {
            // Bridge not ready yet - try to find drawn items manually
            if (iframeWin && iframeWin.L) {
                var fc = {"type": "FeatureCollection", "features": []};
                // Search for drawn layers
                for (var key in iframeWin) {
                    try {
                        if (iframeWin[key] instanceof iframeWin.L.Map) {
                            iframeWin[key].eachLayer(function(layer) {
                                if (layer instanceof iframeWin.L.Path && layer.toGeoJSON && layer.editing) {
                                    fc.features.push(layer.toGeoJSON());
                                }
                            });
                            break;
                        }
                    } catch(e) {}
                }
                if (fc.features.length > 0) {
                    return JSON.stringify(fc);
                }
            }
            return JSON.stringify({"error": "Draw bridge not initialized. Draw something on the map first, then try again."});
        }
    } catch(e) {
        return JSON.stringify({"error": "Cannot access iframe: " + e.message + ". This may be a cross-origin issue."});
    }
})()
"""


EXTRACT_TERRITORY_JS = """
(function() {
    // First check if popup set the territory in the global window scope
    if (window._yvyTerritory) {
        var name = window._yvyTerritory;
        window._yvyTerritory = null;
        console.log('[ExtractTerritory] Found in global scope:', name);
        return name;
    }
    
    // Fall back to checking iframe
    var iframes = document.querySelectorAll('#map-container iframe');
    if (!iframes.length) {
        if (window._yvySelectedTerritory) {
            var name = window._yvySelectedTerritory;
            window._yvySelectedTerritory = null;
            return name;
        }
        return "";
    }
    var iframe = iframes[iframes.length - 1];
    try {
        var iframeWin = iframe.contentWindow || iframe.contentDocument;
        if (iframeWin && iframeWin._yvyTerritory) {
            var name = iframeWin._yvyTerritory;
            iframeWin._yvyTerritory = null;
            console.log('[ExtractTerritory] Found in iframe:', name);
            return name;
        }
        if (iframeWin && iframeWin._yvySelectedTerritory) {
            var name = iframeWin._yvySelectedTerritory;
            iframeWin._yvySelectedTerritory = null;
            return name;
        }
    } catch(e) {}
    return "";
})()
"""


def create_base_map():
    """
    Create a base Folium map (fallback, not used in normal flow).
    The actual map is generated via AppState.map_html computed property.
    """
    try:
        m = folium.Map(
            location=[-5, -60],
            zoom_start=4,
            tiles="OpenStreetMap"
        )
        
        # Add layer control
        folium.LayerControl(position='topright').add_to(m)
        
        return m._repr_html_()
    except Exception as e:
        logger.error(f"Error creating base map: {e}")
        m = folium.Map(location=[-5, -60], zoom_start=4, tiles="OpenStreetMap")
        folium.LayerControl().add_to(m)
        return m._repr_html_()


def drawing_toolbar() -> rx.Component:
    """Save/clear the features drawn on the map.

    A floating cluster over the map, not the full-width bar below it this
    used to be: as a flow sibling it took a row of the workspace column away
    from the map on every screen, including the ones with the least height
    to spare.

    Top-CENTRE specifically. The Folium document in the iframe puts its draw
    tools and zoom in the top-left and its layer control in the top-right,
    so both corners are already spoken for; the bottom belongs to the
    results drawer and the mobile sheet. The centre strip is the one place
    nothing else claims.
    """
    return rx.hstack(
        rx.cond(
            AppState.drawn_features.length() > 0,
            rx.badge(
                AppState.drawn_features.length().to(str) + " saved",
                color_scheme="green",
                variant="solid",
                size="1",
            ),
            rx.box(),
        ),
        rx.button(
            AppState.tr["save_drawing"],
            on_click=rx.call_script(
                EXTRACT_DRAWINGS_JS,
                callback=AppState.load_geojson_from_browser,
            ),
            color_scheme="green",
            size="1",
        ),
        rx.button(
            AppState.tr["clear_drawings"],
            on_click=AppState.clear_drawn_features,
            color_scheme="red",
            variant="soft",
            size="1",
        ),
        position="absolute",
        top="0.6rem",
        left="50%",
        transform="translateX(-50%)",
        max_width="calc(100% - 8rem)",
        # Leaflet's own panes go up to ~700 internally; anything below that
        # renders UNDER the map and is invisible. Below the results drawer
        # and mobile sheet (1000), which are allowed to cover it.
        z_index="800",
        padding="0.35rem 0.5rem",
        bg="white",
        border="1px solid #e0e0e0",
        border_radius="var(--radius-3)",
        box_shadow="0 2px 8px rgba(0, 0, 0, 0.15)",
        spacing="2",
        align_items="center",
    )


def leaflet_map() -> rx.Component:
    """
    Interactive map with Earth Engine layers and drawing capabilities.
    Uses AppState.map_html computed property which auto-updates when layers change.
    Popup buttons trigger territory loading via hidden button click.

    Returns ONE box that fills whatever container it is given, with its
    controls as absolutely-positioned overlays inside it. It used to return
    an ``rx.fragment`` of three siblings, which a fragment expands into three
    separate children of the parent — and the parent
    (``pages/index.py::main_content_area``) was a CSS grid declaring five
    template rows for what was really seven children, so the layer-reference
    guide and the whole results area landed in implicit rows the template
    never sized.
    """
    return rx.box(
        # Map iframe container - overflow hidden to clip the iframe
        rx.box(
            rx.html(AppState.map_html),
            width="100%",
            height="100%",
            overflow="hidden",
            id="map-container",
            # Force the iframe generated by rx.html to fill this box
            sx={"& iframe": {"width": "100%", "height": "100%", "border": "none"}},
        ),

        # Hidden button that popup can trigger
        rx.button(
            "Load Territory",
            on_click=rx.call_script(
                EXTRACT_TERRITORY_JS,
                callback=AppState.select_territory_from_map,
            ),
            color_scheme="purple",
            size="1",
            id="hidden-load-territory-btn",
            display="none",
        ),

        drawing_toolbar(),

        width="100%",
        height="100%",
        position="relative",
        overflow="hidden",
    )


def map_metrics() -> rx.Component:
    """Active-layer counts, as a chip row over the map's top-left corner.

    ``pointer_events="none"`` where it is mounted (pages/index.py::_map) —
    it is a readout, and it sits over the very map the user needs to click.
    """
    return rx.hstack(
        rx.badge(
            rx.cond(
                AppState.mapbiomas_displayed_years.length() > 0,
                rx.text(
                    f"🗺️ MapBiomas (",
                    AppState.mapbiomas_displayed_years.length(),
                    ")",
                ),
                "MapBiomas",
            ),
            color_scheme="green",
        ),
        rx.badge(
            rx.cond(
                AppState.hansen_displayed_layers.length() > 0,
                rx.text(
                    f"🌲 Hansen (",
                    AppState.hansen_displayed_layers.length(),
                    ")",
                ),
                "Hansen",
            ),
            color_scheme="blue",
        ),
        spacing="2",
    )
