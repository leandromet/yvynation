"""
Tests for export_service.py - ZIP export generation.
Tests pure logic functions (no Earth Engine required).
"""

import pytest
import json
import zipfile
import io
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from yvynation.utils.export_service import (
    _geojson_from_features,
    _df_to_csv_bytes,
    _plotly_to_html_bytes,
    create_export_zip,
)


# ===== _geojson_from_features tests =====

class TestGeoJSONFromFeatures:
    def test_standard_feature(self):
        features = [{
            "geometry": {"type": "Polygon", "coordinates": [[[-50, -10], [-49, -10], [-49, -9], [-50, -10]]]},
            "properties": {"name": "Test"},
        }]
        result = _geojson_from_features(features)
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 1
        assert result["features"][0]["type"] == "Feature"

    def test_feature_with_coordinates_key(self):
        """Features stored with coordinates at top level (like drawn features)."""
        features = [{
            "type": "Polygon",
            "coordinates": [[[-50, -10], [-49, -10], [-49, -9], [-50, -10]]],
            "name": "Drawn",
        }]
        result = _geojson_from_features(features)
        assert len(result["features"]) == 1

    def test_empty_features(self):
        result = _geojson_from_features([])
        assert result["type"] == "FeatureCollection"
        assert len(result["features"]) == 0

    def test_feature_without_geometry(self):
        features = [{"properties": {"name": "No geom"}}]
        result = _geojson_from_features(features)
        assert len(result["features"]) == 0


# ===== _df_to_csv_bytes tests =====

class TestDFToCSV:
    def test_basic_df(self):
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        result = _df_to_csv_bytes(df)
        assert isinstance(result, bytes)
        csv_str = result.decode('utf-8')
        assert "col1" in csv_str
        assert "col2" in csv_str

    def test_empty_df(self):
        df = pd.DataFrame()
        result = _df_to_csv_bytes(df)
        assert isinstance(result, bytes)


# ===== _plotly_to_html_bytes tests =====

class TestPlotlyToHTML:
    def test_basic_figure(self):
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(x=[1, 2], y=[3, 4])])
        result = _plotly_to_html_bytes(fig)
        assert result is not None
        assert b"plotly" in result.lower()

    def test_empty_figure(self):
        import plotly.graph_objects as go
        fig = go.Figure()
        result = _plotly_to_html_bytes(fig)
        assert result is not None


# ===== create_export_zip tests =====

class TestCreateExportZip:
    def test_minimal_zip(self):
        """ZIP with only analysis results."""
        result = create_export_zip(
            analysis_results={"type": "mapbiomas", "year": 2023, "data": []},
        )
        assert isinstance(result, bytes)
        assert len(result) > 0

        # Verify it's a valid ZIP
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            assert "metadata.json" in names
            assert "README.txt" in names

    def test_zip_with_analysis_data(self):
        """ZIP includes CSV when analysis data is present."""
        data = [
            {"Class_ID": 3, "Class_Name": "Forest", "Area_ha": 50000},
            {"Class_ID": 15, "Class_Name": "Pasture", "Area_ha": 10000},
        ]
        result = create_export_zip(
            analysis_results={"type": "mapbiomas", "year": 2023, "data": data},
            territory_name="Test Territory",
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            # Should have a CSV in territory folder
            csv_files = [n for n in names if n.endswith('.csv')]
            assert len(csv_files) >= 1

    def test_zip_with_geometries(self):
        """ZIP includes GeoJSON when drawn features present."""
        features = [{
            "geometry": {"type": "Polygon", "coordinates": [[[-50, -10], [-49, -10], [-49, -9], [-50, -10]]]},
            "properties": {"name": "Test"},
        }]
        result = create_export_zip(
            analysis_results={"type": "test"},
            drawn_features=features,
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            assert "geometries.geojson" in zf.namelist()
            geojson = json.loads(zf.read("geometries.geojson"))
            assert geojson["type"] == "FeatureCollection"

    def test_zip_with_comparison(self):
        """ZIP includes comparison CSV."""
        result = create_export_zip(
            analysis_results={"type": "mapbiomas"},
            comparison_result={
                "year_start": 2018,
                "year_end": 2023,
                "data": [{"Class_ID": 3, "Change_ha": -500}],
            },
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            comparison_files = [n for n in names if "comparison" in n]
            assert len(comparison_files) >= 1

    def test_zip_metadata_content(self):
        """Verify metadata.json has expected fields."""
        result = create_export_zip(
            analysis_results={"type": "mapbiomas"},
            territory_name="Xingu",
            territory_year=2023,
            territory_source="MapBiomas",
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            metadata = json.loads(zf.read("metadata.json"))
            assert metadata["territory"] == "Xingu"
            assert metadata["year"] == 2023
            assert metadata["source"] == "MapBiomas"
            assert "export_timestamp" in metadata

    def test_zip_with_plotly_figures(self):
        """ZIP includes Plotly HTML figures."""
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Bar(x=[1, 2], y=[3, 4])])
        result = create_export_zip(
            analysis_results={"type": "test"},
            plotly_figures={"test_chart": fig.to_dict()},
        )
        buf = io.BytesIO(result)
        with zipfile.ZipFile(buf, 'r') as zf:
            names = zf.namelist()
            html_files = [n for n in names if n.endswith('.html')]
            assert len(html_files) >= 1
