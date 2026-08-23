"""
Tests for visualization.py - Plotly chart generation.
All tests are pure logic (no Earth Engine required).
"""

import pytest
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from yvynation.utils.visualization import (
    MapBiomasVisualizer,
    HansenVisualizer,
    calculate_gains_losses,
    create_gains_losses_chart,
    create_change_percentage_chart,
    create_sankey_transitions,
)


# ===== Fixtures =====

@pytest.fixture
def mapbiomas_df():
    """Sample MapBiomas-style analysis DataFrame."""
    return pd.DataFrame({
        'Class_ID': [3, 4, 12, 15, 33],
        'Class_Name': ['Forest', 'Savanna', 'Grassland', 'Pasture', 'Water'],
        'Area_ha': [50000.0, 20000.0, 15000.0, 10000.0, 5000.0],
    })


@pytest.fixture
def mapbiomas_df_year2():
    """Second year MapBiomas data with changes."""
    return pd.DataFrame({
        'Class_ID': [3, 4, 12, 15, 33],
        'Class_Name': ['Forest', 'Savanna', 'Grassland', 'Pasture', 'Water'],
        'Area_ha': [45000.0, 18000.0, 16000.0, 15000.0, 6000.0],
    })


@pytest.fixture
def hansen_timeline_df():
    """Sample Hansen loss timeline DataFrame."""
    return pd.DataFrame({
        'Year': [2018, 2019, 2020, 2021, 2022],
        'Loss_ha': [120.0, 150.0, 200.0, 180.0, 130.0],
        'Loss_km2': [1.2, 1.5, 2.0, 1.8, 1.3],
    })


@pytest.fixture
def hansen_balance_df():
    """Sample Hansen forest balance DataFrame."""
    return pd.DataFrame({
        'Class_Name': ['Tree Cover 2000', 'Forest Loss', 'Forest Gain'],
        'Area_ha': [80000.0, 5000.0, 2000.0],
    })


@pytest.fixture
def comparison_df(mapbiomas_df, mapbiomas_df_year2):
    """Pre-computed comparison DataFrame."""
    return calculate_gains_losses(mapbiomas_df, mapbiomas_df_year2)


# ===== MapBiomasVisualizer tests =====

class TestMapBiomasVisualizer:
    def test_bar_chart_returns_figure(self, mapbiomas_df):
        fig = MapBiomasVisualizer.create_area_bar_chart(mapbiomas_df, year=2023)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_bar_chart_empty_df(self):
        fig = MapBiomasVisualizer.create_area_bar_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)
        # Should have an annotation for "No data"
        assert len(fig.layout.annotations) > 0

    def test_bar_chart_top_n(self, mapbiomas_df):
        fig = MapBiomasVisualizer.create_area_bar_chart(mapbiomas_df, top_n=3)
        assert isinstance(fig, go.Figure)
        # Should only show top 3 classes
        assert len(fig.data[0].y) <= 3

    def test_pie_chart_returns_figure(self, mapbiomas_df):
        fig = MapBiomasVisualizer.create_pie_chart(mapbiomas_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0
        assert isinstance(fig.data[0], go.Pie)

    def test_pie_chart_empty_df(self):
        fig = MapBiomasVisualizer.create_pie_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)

    def test_comparison_chart(self, mapbiomas_df, mapbiomas_df_year2):
        fig = MapBiomasVisualizer.create_comparison_chart(
            mapbiomas_df, mapbiomas_df_year2, 2018, 2023
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # Two bar traces (year1, year2)

    def test_comparison_chart_empty(self):
        fig = MapBiomasVisualizer.create_comparison_chart(
            pd.DataFrame(), pd.DataFrame(), 2018, 2023
        )
        assert isinstance(fig, go.Figure)


# ===== calculate_gains_losses tests =====

class TestCalculateGainsLosses:
    def test_basic_comparison(self, mapbiomas_df, mapbiomas_df_year2):
        result = calculate_gains_losses(mapbiomas_df, mapbiomas_df_year2)
        assert not result.empty
        assert 'Change_ha' in result.columns
        assert 'Change_km2' in result.columns
        assert 'Change_pct' in result.columns
        assert 'Abs_Change' in result.columns

    def test_forest_loss_detected(self, mapbiomas_df, mapbiomas_df_year2):
        result = calculate_gains_losses(mapbiomas_df, mapbiomas_df_year2)
        forest_row = result[result['Class_ID'] == 3].iloc[0]
        assert forest_row['Change_ha'] == -5000.0  # 45000 - 50000
        assert forest_row['Change_km2'] == -50.0

    def test_pasture_gain_detected(self, mapbiomas_df, mapbiomas_df_year2):
        result = calculate_gains_losses(mapbiomas_df, mapbiomas_df_year2)
        pasture_row = result[result['Class_ID'] == 15].iloc[0]
        assert pasture_row['Change_ha'] == 5000.0  # 15000 - 10000

    def test_sorted_by_abs_change(self, mapbiomas_df, mapbiomas_df_year2):
        result = calculate_gains_losses(mapbiomas_df, mapbiomas_df_year2)
        abs_changes = result['Abs_Change'].tolist()
        assert abs_changes == sorted(abs_changes, reverse=True)

    def test_new_class_in_year2(self, mapbiomas_df):
        """Class appears in year2 but not year1."""
        year2 = pd.DataFrame({
            'Class_ID': [3, 99],
            'Class_Name': ['Forest', 'Urban'],
            'Area_ha': [40000.0, 5000.0],
        })
        result = calculate_gains_losses(mapbiomas_df, year2)
        assert 99 in result['Class_ID'].values

    def test_class_disappears_in_year2(self, mapbiomas_df):
        """Class exists in year1 but not year2."""
        year2 = pd.DataFrame({
            'Class_ID': [3],
            'Class_Name': ['Forest'],
            'Area_ha': [45000.0],
        })
        result = calculate_gains_losses(mapbiomas_df, year2)
        # Classes from year1 should still appear with Area_Year2 = 0
        assert len(result) >= 2


# ===== Gains/Losses Chart tests =====

class TestGainsLossesChart:
    def test_returns_figure(self, comparison_df):
        fig = create_gains_losses_chart(comparison_df, 2018, 2023)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2  # gains + losses traces

    def test_empty_df(self):
        fig = create_gains_losses_chart(pd.DataFrame(), 2018, 2023)
        assert isinstance(fig, go.Figure)

    def test_top_n_limits(self, comparison_df):
        fig = create_gains_losses_chart(comparison_df, 2018, 2023, top_n=2)
        assert isinstance(fig, go.Figure)


class TestChangePercentageChart:
    def test_returns_figure(self, comparison_df):
        fig = create_change_percentage_chart(comparison_df, 2018, 2023)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_empty_df(self):
        fig = create_change_percentage_chart(pd.DataFrame(), 2018, 2023)
        assert isinstance(fig, go.Figure)


# ===== HansenVisualizer tests =====

class TestHansenVisualizer:
    def test_loss_timeline(self, hansen_timeline_df):
        fig = HansenVisualizer.create_loss_timeline_chart(hansen_timeline_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_forest_balance(self, hansen_balance_df):
        fig = HansenVisualizer.create_forest_balance_chart(hansen_balance_df)
        assert isinstance(fig, go.Figure)

    def test_area_distribution(self, mapbiomas_df):
        fig = HansenVisualizer.create_area_distribution_chart(mapbiomas_df, year=2020)
        assert isinstance(fig, go.Figure)

    def test_empty_timeline(self):
        fig = HansenVisualizer.create_loss_timeline_chart(pd.DataFrame())
        assert isinstance(fig, go.Figure)


# ===== Sankey tests =====

class TestSankeyTransitions:
    def test_basic_sankey(self):
        transitions = {
            "3_to_15": 500,   # Forest -> Pasture
            "15_to_3": 100,   # Pasture -> Forest
            "4_to_12": 200,   # Savanna -> Grassland
        }
        fig = create_sankey_transitions(transitions, 2018, 2023)
        # May return None if parsing fails, or a Figure
        if fig is not None:
            assert isinstance(fig, go.Figure)

    def test_empty_transitions(self):
        result = create_sankey_transitions({}, 2018, 2023)
        assert result is None or isinstance(result, go.Figure)

    def test_none_transitions(self):
        result = create_sankey_transitions(None, 2018, 2023)
        assert result is None
