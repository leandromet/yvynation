"""Switching between analysed areas must not mix their results.

Regression (docs/PDF_REPORT.md §1, pitfall 1): switch_result restored only the
bundle's own entries, so GLAD/GFC/buffer/territory results stayed from the
LAST area analysed; the results panel, the ZIP, "Download all" and the PDF
report then attributed one area's numbers to another. Selecting a territory
also left them in place. Exercised on the plain methods with a stand-in
object — no Reflex runtime or Earth Engine needed.
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from yvynation.state._analysis import (  # noqa: E402
    AREA_LABEL_FIELDS, AREA_RESULT_FIELDS, AnalysisMixin,
)

save = AnalysisMixin._save_area_fields
clear = AnalysisMixin._clear_area_fields
switch = AnalysisMixin.switch_result


def _state():
    s = SimpleNamespace(all_analysis_results={}, active_result_key="",
                        analysis_results={}, mapbiomas_comparison_result=None,
                        map_zoom_bounds={}, territory_name="", territory_year=2024,
                        territory_year2=None, territory_source="MapBiomas")
    for f in AREA_RESULT_FIELDS:
        setattr(s, f, None)
    # advanced-viz fields switch_result also restores
    for f in ("timeline_series", "buffer_timeline_series", "mw_result",
              "buffer_mw_result"):
        setattr(s, f, {})
    for f in ("mw_sunburst_figs", "mw_treemap_figs", "buffer_mw_sunburst_figs",
              "buffer_mw_treemap_figs"):
        setattr(s, f, [])
    s.timeline_state_code = s.timeline_territory_name = ""
    s.timeline_year_start = s.timeline_year_end = 0
    s.timeline_territory_type = "indigenous"
    return s


def test_results_follow_their_area_across_switches():
    s = _state()
    # Area A: full run, buffer included.
    s.territory_name = "A"
    s.geometry_glad_result = {"area": "A-glad"}
    s.geometry_gfc_result = {"area": "A-gfc"}
    s.buffer_gfc_result = {"area": "A-buf-gfc"}
    s.all_analysis_results["territory::A"] = {"result": {"r": "A"}}
    save(s, "territory::A")

    # Select B: stale fields must go (set_selected_territory calls this).
    clear(s)
    assert all(getattr(s, f) is None for f in AREA_RESULT_FIELDS)

    # Area B: only GLAD run.
    s.territory_name = "B"
    s.geometry_glad_result = {"area": "B-glad"}
    s.all_analysis_results["territory::B"] = {"result": {"r": "B"}}
    save(s, "territory::B")

    switch(s, "territory::A")
    assert s.geometry_glad_result == {"area": "A-glad"}
    assert s.buffer_gfc_result == {"area": "A-buf-gfc"}
    assert s.territory_name == "A"

    switch(s, "territory::B")
    assert s.geometry_glad_result == {"area": "B-glad"}
    # B never ran GFC or a buffer: None, never A's leftovers
    assert s.geometry_gfc_result is None
    assert s.buffer_gfc_result is None
    assert s.territory_name == "B"


def test_saved_bundle_does_not_alias_live_fields():
    s = _state()
    s.geometry_gfc_result = {"loss": [1, 2]}
    s.all_analysis_results["k"] = {}
    save(s, "k")
    s.geometry_gfc_result["loss"].append(3)  # the next run mutates in place
    assert s.all_analysis_results["k"]["area"]["geometry_gfc_result"] == {"loss": [1, 2]}


def test_save_keeps_other_bundle_entries():
    s = _state()
    s.all_analysis_results["k"] = {"result": {"x": 1}, "timeline": {"series": {"a": 1}}}
    save(s, "k")
    b = s.all_analysis_results["k"]
    assert b["result"] == {"x": 1} and b["timeline"] == {"series": {"a": 1}}
    assert set(b["area"]) == set(AREA_RESULT_FIELDS + AREA_LABEL_FIELDS)
