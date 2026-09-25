"""Batch quadrant merge for the per-area report (docs/PDF_REPORT.md §5).

A territory above SPLIT_THRESHOLD_HA is analysed as four quadrants; its report
must show whole-territory totals, never the last quadrant's.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from yvynation.utils import report_builder as rb  # noqa: E402


def _recs(areas):
    return [{"Class_ID": c, "Class": f"C{c}", "Area_ha": a, "Percentage": 99.0}
            for c, a in areas.items()]


def _gfc(cover, loss_by_code, gain):
    return {
        "tree_cover_data": [{"Percent_Cover": 0, "Pixels": 10, "Area_ha": 100.0},
                            {"Percent_Cover": 90, "Pixels": 10, "Area_ha": cover}],
        "tree_loss_data": [{"Year_Code": 0, "Year": "No Loss", "Pixels": 1, "Area_ha": 5.0}]
        + [{"Year_Code": c, "Year": str(2000 + c), "Pixels": 1, "Area_ha": a}
           for c, a in loss_by_code.items()],
        "tree_gain_data": [{"Gain_Code": 1, "Status": "Gain", "Pixels": 1, "Area_ha": gain}],
        "summary": {"tree_cover_2000_ha": -1},   # must be rebuilt, not reused
    }


QUADS = [
    # (y1 areas, y2 areas, transitions, gfc cover, gfc loss, gain, glad)
    ({3: 1000.0, 15: 100.0}, {3: 900.0, 15: 200.0}, {"3": {"15": 100.0}},
     1000.0, {5: 10.0, 19: 20.0}, 3.0, {75: 800.0, 6: 300.0}),
    ({3: 2000.0, 12: 50.0}, {3: 1950.0, 12: 100.0}, {"3": {"12": 50.0}},
     2000.0, {19: 30.0}, 4.0, {75: 1900.0, 6: 150.0}),
    ({3: 500.0, 15: 500.0}, {3: 300.0, 15: 700.0}, {"3": {"15": 200.0}},
     500.0, {24: 40.0}, 0.0, {75: 400.0}),
    ({33: 250.0}, {33: 250.0}, {}, 0.0, {}, 0.0, {250: 250.0}),
]


def _regions():
    out = []
    for i, (a1, a2, tr, cover, loss, gain, glad) in enumerate(QUADS):
        out.append({
            "name": "nw ne sw se".split()[i],
            "mb1": {"data": _recs(a1)}, "mb2": {"data": _recs(a2)},
            "cmp": {"year_start": 1985, "year_end": 2024, "_raw_y1": _recs(a1),
                    "_raw_y2": _recs(a2), "transitions": tr},
            "glad": {"year": 2020, "data": _recs(glad)},
            "gfc": _gfc(cover, loss, gain),
            "bmb": {"data": _recs({3: 10.0 * (i + 1)})},
            "bcmp": {"_raw_y1": _recs({3: 10.0 * (i + 1)}),
                     "_raw_y2": _recs({3: 5.0 * (i + 1), 15: 5.0 * (i + 1)}),
                     "transitions": {"3": {"15": 5.0 * (i + 1)}}},
            "bgfc": _gfc(10.0, {10: 1.0}, 0.0),
            "mw": {"years": [1985, 2000, 2024], "pairs": [
                {"year_from": 1985, "year_to": 2000, "transitions": {"3": {"3": 1.0}}},
                {"year_from": 2000, "year_to": 2024, "transitions": {"3": {"15": 2.0}}}]},
        })
    return out


def _by_id(records):
    return {r["Class_ID"]: r["Area_ha"] for r in records}


def test_four_quadrants_sum_class_areas():
    m = rb.merge_regions(_regions())
    assert m["n_parts"] == 4 and m["y1"] == 1985 and m["y2"] == 2024
    assert _by_id(m["t_y1"]) == {3: 3500.0, 15: 600.0, 12: 50.0, 33: 250.0}
    assert _by_id(m["t_y2"]) == {3: 3150.0, 15: 900.0, 12: 100.0, 33: 250.0}
    assert _by_id(m["b_y1"]) == {3: 100.0}
    assert _by_id(m["b_y2"]) == {3: 50.0, 15: 50.0}
    assert _by_id(m["glad"]["data"]) == {75: 3100.0, 6: 450.0, 250: 250.0}


@pytest.mark.parametrize("key", ["t_y1", "t_y2", "b_y1", "b_y2"])
def test_percentages_add_to_100(key):
    m = rb.merge_regions(_regions())
    assert sum(r["Percentage"] for r in m[key]) == pytest.approx(100.0, abs=0.01)


def test_transitions_gfc_and_mw_are_summed():
    m = rb.merge_regions(_regions())
    assert m["transitions"] == {"3": {"15": 300.0, "12": 50.0}}
    assert m["b_transitions"] == {"3": {"15": 50.0}}
    g = rb.gfc_numbers(m["gfc"])
    assert g["cover_ha"] == pytest.approx(3500.0)
    assert g["loss_ha"] == pytest.approx(100.0)
    assert g["gain_ha"] == pytest.approx(7.0)
    assert dict(g["by_year"]) == {2005: 10.0, 2019: 50.0, 2024: 40.0}
    assert m["gfc"]["summary"]["tree_cover_2000_ha"] == 3500
    assert m["gfc"]["summary"]["forest_loss_ha"] == 100
    pairs = {(p["year_from"], p["year_to"]): p["transitions"] for p in m["mw"]["pairs"]}
    assert pairs[(1985, 2000)] == {"3": {"3": 4.0}}
    assert pairs[(2000, 2024)] == {"3": {"15": 8.0}}


def test_single_region_passes_through():
    one = _regions()[:1]
    m = rb.merge_regions(one)
    assert m["n_parts"] == 1
    assert _by_id(m["t_y1"]) == {3: 1000.0, 15: 100.0}
    assert m["gfc"] is one[0]["gfc"]


def test_whole_territory_report_uses_merged_totals():
    m = rb.merge_regions(_regions())
    snap = rb.snapshot_from_batch(
        m, name="Big Flona", territory_type="conservation",
        geometry={"type": "Point", "coordinates": [-55, -5]}, buffer_geometry=None,
        buffer_km=10.0, hansen_year="2020", y1=1985, y2=2024)
    report = rb.build_territory_report(snap, {"type": "conservation", "info": {}}, {}, None,
                                       "en", {"batch": True, "maps": False})
    kv = report.sections[0].blocks[0].left
    computed = dict(kv.rows)["Computed area (MapBiomas 2024)"]
    assert computed == "4,400 ha"                    # 3150 + 900 + 100 + 250
    about = next(s for s in report.sections if s.key == "about")
    assert any("4 parts" in getattr(b, "text", "") for b in about.blocks)


def test_timeline_series_sum():
    out = rb.sum_timeline_series([{"hansen_loss": {2001: 1.0, "2002": 2.0}},
                                  {"hansen_loss": {2001: 3.0}}, None])
    assert out == {"hansen_loss": {2001: 4.0, 2002: 2.0}}
