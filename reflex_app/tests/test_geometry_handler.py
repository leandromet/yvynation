"""
Tests for geometry_handler.py - GeoJSON/KML parsing and validation.
All tests are pure logic (no Earth Engine required).
"""

import pytest
import json
import sys
import os

# Add parent to path so we can import the module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from yvynation.utils.geometry_handler import (
    parse_geojson,
    parse_kml,
    validate_geometry,
    get_bbox_from_geojson,
    _parse_kml_coordinates,
    _extract_all_coords,
)


# ===== Fixtures =====

SAMPLE_POLYGON_COORDS = [[[-50, -10], [-49, -10], [-49, -9], [-50, -9], [-50, -10]]]

SAMPLE_FEATURE = {
    "type": "Feature",
    "properties": {"name": "Test Area"},
    "geometry": {
        "type": "Polygon",
        "coordinates": SAMPLE_POLYGON_COORDS,
    },
}

SAMPLE_FC = {
    "type": "FeatureCollection",
    "features": [SAMPLE_FEATURE],
}

SAMPLE_KML = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Test KML</name>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>-50,-10,0 -49,-10,0 -49,-9,0 -50,-9,0 -50,-10,0</coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
  </Document>
</kml>"""

SAMPLE_KML_POINT = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Point</name>
      <Point>
        <coordinates>-50.5,-10.5,0</coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>"""


# ===== parse_geojson tests =====

class TestParseGeoJSON:
    def test_feature_collection(self):
        result = parse_geojson(json.dumps(SAMPLE_FC))
        assert result is not None
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1

    def test_single_feature(self):
        result = parse_geojson(json.dumps(SAMPLE_FEATURE))
        assert result is not None
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        assert result["features"][0]["geometry"]["type"] == "Polygon"

    def test_raw_geometry(self):
        raw_geom = {"type": "Polygon", "coordinates": SAMPLE_POLYGON_COORDS}
        result = parse_geojson(json.dumps(raw_geom), file_name="test.geojson")
        assert result is not None
        assert result["type"] == "FeatureCollection"
        assert result["features"][0]["properties"]["name"] == "test"

    def test_invalid_json(self):
        result = parse_geojson("not valid json")
        assert result is None

    def test_empty_json(self):
        result = parse_geojson("{}")
        assert result is None

    def test_missing_type(self):
        result = parse_geojson(json.dumps({"features": []}))
        assert result is None

    def test_multipolygon(self):
        multi = {
            "type": "MultiPolygon",
            "coordinates": [SAMPLE_POLYGON_COORDS],
        }
        result = parse_geojson(json.dumps(multi))
        assert result is not None
        assert result["features"][0]["geometry"]["type"] == "MultiPolygon"


# ===== parse_kml tests =====

class TestParseKML:
    def test_polygon_kml(self):
        result = parse_kml(SAMPLE_KML, "test.kml")
        assert result is not None
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        feat = result["features"][0]
        assert feat["geometry"]["type"] == "Polygon"
        assert feat["properties"]["name"] == "Test Polygon"

    def test_point_kml(self):
        result = parse_kml(SAMPLE_KML_POINT)
        assert result is not None
        feat = result["features"][0]
        assert feat["geometry"]["type"] == "Point"
        assert feat["geometry"]["coordinates"][0] == -50.5
        assert feat["geometry"]["coordinates"][1] == -10.5

    def test_invalid_kml(self):
        result = parse_kml("not xml at all")
        assert result is None

    def test_empty_kml(self):
        empty_kml = """<?xml version="1.0" encoding="UTF-8"?>
        <kml xmlns="http://www.opengis.net/kml/2.2">
          <Document></Document>
        </kml>"""
        result = parse_kml(empty_kml)
        assert result is None


# ===== _parse_kml_coordinates tests =====

class TestParseKMLCoordinates:
    def test_basic(self):
        result = _parse_kml_coordinates("-50,-10,0 -49,-10,0 -49,-9,0")
        assert result is not None
        assert len(result) == 3
        assert result[0] == [-50.0, -10.0]

    def test_no_altitude(self):
        result = _parse_kml_coordinates("-50,-10 -49,-10")
        assert result is not None
        assert len(result) == 2

    def test_empty_string(self):
        result = _parse_kml_coordinates("")
        assert result is None

    def test_whitespace(self):
        result = _parse_kml_coordinates("  -50,-10,0  -49,-9,0  ")
        assert result is not None
        assert len(result) == 2


# ===== validate_geometry tests =====

class TestValidateGeometry:
    def test_valid_fc(self):
        valid, msg = validate_geometry(SAMPLE_FC)
        assert valid is True
        assert msg == ""

    def test_valid_feature(self):
        valid, msg = validate_geometry(SAMPLE_FEATURE)
        assert valid is True

    def test_empty_fc(self):
        valid, msg = validate_geometry({"type": "FeatureCollection", "features": []})
        assert valid is False
        assert "no features" in msg.lower()

    def test_missing_features_key(self):
        valid, msg = validate_geometry({"type": "FeatureCollection"})
        assert valid is False

    def test_invalid_geometry_type(self):
        bad_feature = {
            "type": "Feature",
            "geometry": {"type": "InvalidType", "coordinates": []},
        }
        valid, msg = validate_geometry(bad_feature)
        assert valid is False
        assert "Invalid geometry type" in msg

    def test_missing_geometry(self):
        bad = {"type": "Feature", "properties": {}}
        valid, msg = validate_geometry(bad)
        assert valid is False

    def test_missing_coordinates(self):
        bad = {"type": "Feature", "geometry": {"type": "Point"}}
        valid, msg = validate_geometry(bad)
        assert valid is False

    def test_not_a_dict(self):
        valid, msg = validate_geometry("not a dict")
        assert valid is False


# ===== get_bbox_from_geojson tests =====

class TestGetBBox:
    def test_polygon_bbox(self):
        bbox = get_bbox_from_geojson(SAMPLE_FC)
        assert bbox is not None
        min_lon, min_lat, max_lon, max_lat = bbox
        assert min_lon == -50
        assert min_lat == -10
        assert max_lon == -49
        assert max_lat == -9

    def test_point_bbox(self):
        point_fc = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-50.5, -10.5]},
                "properties": {},
            }],
        }
        bbox = get_bbox_from_geojson(point_fc)
        assert bbox is not None
        assert bbox[0] == -50.5
        assert bbox[1] == -10.5

    def test_empty_fc(self):
        empty = {"type": "FeatureCollection", "features": []}
        bbox = get_bbox_from_geojson(empty)
        assert bbox is None

    def test_multipolygon_bbox(self):
        multi_fc = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        SAMPLE_POLYGON_COORDS,
                        [[[-60, -20], [-59, -20], [-59, -19], [-60, -19], [-60, -20]]],
                    ],
                },
                "properties": {},
            }],
        }
        bbox = get_bbox_from_geojson(multi_fc)
        assert bbox is not None
        assert bbox[0] == -60  # min_lon
        assert bbox[1] == -20  # min_lat


# ===== _extract_all_coords tests =====

class TestExtractAllCoords:
    def test_point(self):
        coords = _extract_all_coords({"type": "Point", "coordinates": [-50, -10]})
        assert len(coords) == 1
        assert coords[0] == (-50, -10)

    def test_polygon(self):
        coords = _extract_all_coords({
            "type": "Polygon",
            "coordinates": SAMPLE_POLYGON_COORDS,
        })
        assert len(coords) == 5

    def test_linestring(self):
        coords = _extract_all_coords({
            "type": "LineString",
            "coordinates": [[-50, -10], [-49, -9]],
        })
        assert len(coords) == 2

    def test_empty_geometry(self):
        coords = _extract_all_coords({})
        assert len(coords) == 0

    def test_none_geometry(self):
        coords = _extract_all_coords(None)
        assert len(coords) == 0
