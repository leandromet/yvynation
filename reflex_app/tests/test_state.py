"""
Tests for AppState methods that can be tested without Reflex runtime.
Focuses on load_geojson_from_browser and drawing capture logic.
"""

import pytest
import json
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class FakeAppState:
    """Minimal mock of AppState for testing load_geojson_from_browser logic."""

    def __init__(self):
        self.drawn_features = []
        self.all_drawn_features = []
        self.error_message = ""

    def load_geojson_from_browser(self, geojson_data: str):
        """Direct copy of the method logic from state.py for isolated testing."""
        try:
            data = json.loads(geojson_data) if isinstance(geojson_data, str) else geojson_data

            if "error" in data and "features" not in data:
                self.error_message = str(data["error"])
                return

            features = data.get("features", [])

            if not features:
                self.error_message = "No drawn geometries found on the map. Draw a polygon or rectangle first."
                return

            new_count = 0
            for feature in features:
                try:
                    geom = feature.get("geometry", {})
                    geom_type = geom.get("type", "Unknown")

                    if not geom or not geom.get("coordinates"):
                        continue

                    idx = len(self.drawn_features)
                    feature_obj = {
                        "_idx": idx,
                        "_display_idx": idx + 1,
                        "type": geom_type,
                        "name": f"Drawing {idx + 1}",
                        "geometry": geom,
                        "properties": feature.get("properties", {}),
                        "coordinates": geom.get("coordinates", []),
                    }

                    self.drawn_features.append(feature_obj)
                    self.all_drawn_features.append(feature_obj)
                    new_count += 1
                except Exception:
                    pass

            if new_count:
                self.error_message = f"Captured {new_count} drawing(s) from map ({len(self.drawn_features)} total)"
            else:
                self.error_message = "No valid geometries could be extracted"

        except json.JSONDecodeError as e:
            self.error_message = f"Error parsing GeoJSON: {str(e)}"
        except Exception as e:
            self.error_message = f"Error loading geometries: {str(e)}"


SAMPLE_FC = json.dumps({
    "type": "FeatureCollection",
    "features": [{
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[-50, -10], [-49, -10], [-49, -9], [-50, -9], [-50, -10]]],
        },
        "properties": {},
    }],
})

SAMPLE_MULTI_FC = json.dumps({
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[-50, -10], [-49, -10], [-49, -9], [-50, -10]]]},
            "properties": {},
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-48, -8]},
            "properties": {},
        },
    ],
})


class TestLoadGeoJSONFromBrowser:
    def test_valid_feature_collection(self):
        state = FakeAppState()
        state.load_geojson_from_browser(SAMPLE_FC)
        assert len(state.drawn_features) == 1
        assert state.drawn_features[0]["type"] == "Polygon"
        assert "Captured 1" in state.error_message

    def test_multiple_features(self):
        state = FakeAppState()
        state.load_geojson_from_browser(SAMPLE_MULTI_FC)
        assert len(state.drawn_features) == 2
        assert "Captured 2" in state.error_message

    def test_js_bridge_error(self):
        state = FakeAppState()
        error_json = json.dumps({"error": "No map iframe found"})
        state.load_geojson_from_browser(error_json)
        assert len(state.drawn_features) == 0
        assert "No map iframe" in state.error_message

    def test_empty_features(self):
        state = FakeAppState()
        empty = json.dumps({"type": "FeatureCollection", "features": []})
        state.load_geojson_from_browser(empty)
        assert len(state.drawn_features) == 0
        assert "No drawn geometries" in state.error_message

    def test_invalid_json(self):
        state = FakeAppState()
        state.load_geojson_from_browser("not json at all")
        assert len(state.drawn_features) == 0
        assert "Error parsing" in state.error_message

    def test_feature_without_coordinates(self):
        """Feature with empty geometry should be skipped."""
        state = FakeAppState()
        bad_fc = json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Polygon"},
                "properties": {},
            }],
        })
        state.load_geojson_from_browser(bad_fc)
        assert len(state.drawn_features) == 0
        assert "No valid geometries" in state.error_message

    def test_appends_to_existing(self):
        """Should append, not replace existing features."""
        state = FakeAppState()
        state.load_geojson_from_browser(SAMPLE_FC)
        assert len(state.drawn_features) == 1

        state.load_geojson_from_browser(SAMPLE_FC)
        assert len(state.drawn_features) == 2

    def test_indexing(self):
        state = FakeAppState()
        state.load_geojson_from_browser(SAMPLE_FC)
        feat = state.drawn_features[0]
        assert feat["_idx"] == 0
        assert feat["_display_idx"] == 1
        assert feat["name"] == "Drawing 1"

    def test_rectangle_geometry(self):
        """Leaflet Draw rectangles come as Polygons."""
        rect_fc = json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-50, -10], [-48, -10], [-48, -8], [-50, -8], [-50, -10]]],
                },
                "properties": {},
            }],
        })
        state = FakeAppState()
        state.load_geojson_from_browser(rect_fc)
        assert len(state.drawn_features) == 1
        assert state.drawn_features[0]["type"] == "Polygon"
