"""The USA page: PAD-US client (offline, with the service stubbed), zones, nlcd config,
translations, and that the page builds."""

import re

import pytest

from yvynation.usa.config import nlcd
from yvynation.usa.services import padus, zones
from yvynation.usa.translations import get_translations
from yvynation.usa.translations.en import TRANSLATIONS_EN
from yvynation.usa.translations.pt import TRANSLATIONS_PT


def _attrs(**kw):
    base = dict(OBJECTID=1, Unit_Nm="Test Reservation", Category="Proclamation", Des_Tp="TRIBL",
                Des_Tp_Desc="Native American Land Area", Mang_Name="TRIB", Mang_Type="TRIB",
                GAP_Sts="4", IUCN_Cat="Unassigned", Pub_Access="UK", GIS_Acres=1000, ST_Name="Not Applicable")
    base.update(kw)
    return base


def test_unit_flags_tribal_land_and_converts_acres():
    u = padus._unit(_attrs(), "proclamation")
    assert u.tribal and u.ha == pytest.approx(404.7, abs=0.1)
    park = padus._unit(_attrs(OBJECTID=2, Des_Tp="NP", Mang_Type="FED", Category="Fee"), "fee")
    assert not park.tribal


def test_search_escapes_quotes_and_wildcards(monkeypatch):
    seen = {}
    monkeypatch.setattr(padus, "_query", lambda src, p: seen.update(p) or {"features": []})
    padus.search("O'Brien_%park")
    assert "O''Brien" in seen["where"] and "%park" not in seen["where"].replace("%'", "").replace("'%", "")
    assert padus.search("a") == []            # too short: no request


def test_at_point_sorts_smallest_first(monkeypatch):
    feats = [{"attributes": _attrs(OBJECTID=1, GIS_Acres=500000)},
             {"attributes": _attrs(OBJECTID=2, GIS_Acres=10)}]
    monkeypatch.setattr(padus, "_query", lambda src, p: {"features": feats if src == "fee" else []})
    assert [u.key for u in padus.at_point(37.0, -119.0)] == ["fee:2", "fee:1"]


def test_federal_pieces_of_one_unit_are_merged_and_other_names_are_not():
    fed = dict(Mang_Type="FED", Mang_Name="NPS", Des_Tp="NP", Category="Fee", Unit_Nm="Big Park")
    recs = [("fee", _attrs(OBJECTID=1, GIS_Acres=100, **fed)), ("fee", _attrs(OBJECTID=2, GIS_Acres=300, **fed)),
            ("fee", _attrs(OBJECTID=3, GIS_Acres=50, Unit_Nm="Navajo Park", Mang_Type="LOC", Category="Fee")),
            ("fee", _attrs(OBJECTID=4, GIS_Acres=60, Unit_Nm="Navajo Park", Mang_Type="LOC", Category="Fee"))]
    units = {u.key: u for u in padus._merge(recs)}
    assert units["fee:2"].pieces == 2 and units["fee:2"].ha == pytest.approx(400 * padus.ACRES_TO_HA, abs=0.1)
    assert "fee:3" in units and "fee:4" in units          # two parks that share a name stay two


def test_parts_are_ranked_largest_first():
    sq = lambda x, s: [[[x, 40], [x + s, 40], [x + s, 40 + s], [x, 40 + s], [x, 40]]]
    geom = {"type": "MultiPolygon", "coordinates": [sq(-100, 0.01), sq(-101, 0.1)]}
    p = padus.parts(geom)
    assert [x["id"] for x in p] == ["1", "0"] and p[0]["rank"] == 1
    assert padus.parts_geometry(geom, ["1"])["type"] == "Polygon"


def test_zones_use_the_conus_equal_area_projection():
    # 1° × 1° at 40°N is about 8.5 million ha... check a 0.1° square against the known area
    sq = {"type": "Polygon", "coordinates": [[[-100, 40], [-99.9, 40], [-99.9, 40.1],
                                               [-100, 40.1], [-100, 40]]]}
    assert zones.area_ha(sq) == pytest.approx(0.1 * 85.28 * 0.1 * 111.2 * 100, rel=0.02)
    zs = zones.build_zones(sq)
    assert [z.key for z in zs][:2] == ["parcela", "ring_500m"]


def test_nlcd_config_consistent():
    assert set(nlcd.NLCD_LABELS_EN) == set(nlcd.NLCD_LABELS_PT) == set(nlcd.NLCD_COLOR_MAP)
    assert nlcd.NLCD_YEARS[0] == 1985 and nlcd.NLCD_YEARS[-1] == 2025


def test_translations_match_placeholders_and_carry_the_indigenous_notice():
    pat = re.compile(r"\{[a-z_]+\}")
    for k, pt in TRANSLATIONS_PT.items():
        assert k in TRANSLATIONS_EN, k
        assert sorted(pat.findall(pt)) == sorted(pat.findall(TRANSLATIONS_EN[k])), k
    for lang in ("en", "pt"):
        t = get_translations(lang)
        assert "CARE" in t["indigenous_data_notice_body"]


def test_usa_page_builds():
    from yvynation.usa.pages.index import usa_index
    assert usa_index() is not None
