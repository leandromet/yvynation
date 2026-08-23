"""
Tests for analysis.py - specifically the pure-logic compare_areas function.
EE-dependent functions are tested via integration tests with mocked EE.
"""

import pytest
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from yvynation.utils.analysis import compare_areas


@pytest.fixture
def df_2018():
    return pd.DataFrame({
        'Class_ID': [3, 4, 12, 15],
        'Class_Name': ['Forest', 'Savanna', 'Grassland', 'Pasture'],
        'Area_ha': [50000.0, 20000.0, 15000.0, 10000.0],
    })


@pytest.fixture
def df_2023():
    return pd.DataFrame({
        'Class_ID': [3, 4, 12, 15, 33],
        'Class_Name': ['Forest', 'Savanna', 'Grassland', 'Pasture', 'Water'],
        'Area_ha': [45000.0, 18000.0, 16000.0, 15000.0, 6000.0],
    })


class TestCompareAreas:
    def test_basic_comparison(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023, 2018, 2023)
        assert not result.empty
        assert 'Change_ha' in result.columns
        assert 'Change_pct' in result.columns

    def test_forest_loss(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023)
        forest = result[result['Class_ID'] == 3].iloc[0]
        assert forest['Change_ha'] == -5000.0

    def test_pasture_gain(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023)
        pasture = result[result['Class_ID'] == 15].iloc[0]
        assert pasture['Change_ha'] == 5000.0

    def test_new_class_appears(self, df_2018, df_2023):
        """Class 33 (Water) only in year2 - should appear with 0 start area."""
        result = compare_areas(df_2018, df_2023)
        water = result[result['Class_ID'] == 33]
        assert len(water) == 1
        assert water.iloc[0]['Area_ha_start'] == 0

    def test_year_labels_added(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023, 2018, 2023)
        assert 'Year_Start' in result.columns
        assert 'Year_End' in result.columns
        assert result['Year_Start'].iloc[0] == 2018
        assert result['Year_End'].iloc[0] == 2023

    def test_sorted_by_change(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023)
        changes = result['Change_ha'].tolist()
        assert changes == sorted(changes, reverse=True)

    def test_empty_dfs(self):
        result = compare_areas(pd.DataFrame(), pd.DataFrame())
        assert result.empty

    def test_one_empty_df(self, df_2018):
        result = compare_areas(df_2018, pd.DataFrame())
        assert result.empty

    def test_no_year_labels(self, df_2018, df_2023):
        result = compare_areas(df_2018, df_2023)
        assert 'Year_Start' not in result.columns
