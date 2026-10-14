"""The "Find a place" resolver (utils/place_search.py) and its UI keys.

utils/address.py is shared verbatim with camposcope, whose
tests/test_address.py covers its parsing and labelling in depth."""

from __future__ import annotations

import json

import pytest

from yvynation.utils import address, place_search as ps

NAMES = ["Yanomami", "Parque Nacional do Jaú", "Kayapó", "Jauaperi"]


@pytest.mark.parametrize("text,kind", [
    ("78890-000", "cep"),
    ("V1Y 2B3", "postal"),
    ("-12.5, -55.7", "coordenada"),
    ("49.88, -119.49", "coordenada"),
    ("12°29'52.5\"S 55°29'51.7\"W", "coordenada"),
    ("Yanomami", "territorio"),
    ("Rua XV de Novembro, Curitiba", "lugar"),
    ("", "vazio"),
])
def test_resolver_order(text, kind):
    assert ps.resolve(text, NAMES).kind == kind


def test_territory_match_is_accent_blind_and_prefix_first():
    hits = ps.match_territories("jau", NAMES)
    assert hits[0] == "Jauaperi" and "Parque Nacional do Jaú" in hits


def test_short_queries_match_no_territory():
    assert ps.match_territories("ja", NAMES) == []


def test_transposed_pair_is_named():
    with pytest.raises(ValueError, match="transposed"):
        ps.resolve("-55.7, -12.5", NAMES)


def test_outside_both_regions():
    with pytest.raises(ValueError, match="outside Brazil and Canada"):
        ps.resolve("48.85, 2.35", NAMES)          # Paris


def test_resolve_performs_no_network_call(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("resolve() must not touch the network")
    monkeypatch.setattr(ps._geocoder, "_nominatim", boom)
    ps.resolve("Some Farm Road 12", NAMES)


def test_frame_js_embeds_valid_json():
    js = ps.frame_js(bounds=[[-1.0, -2.0], [3.0, 4.0]], pin=[1.5, 2.5], zoom=15)
    assert json.dumps([[-1.0, -2.0], [3.0, 4.0]]) in js and "[1.5, 2.5]" in js
    assert "null" in ps.frame_js(pin=[1.0, 2.0])     # no bounds → setView path


def test_region_bounds_cover_both_regions_and_bc():
    assert set(ps.REGION_BOUNDS) == {"Brazil", "Canada", "BC"}


_KEYS = ["ps_title", "ps_placeholder", "ps_read_as", "ps_button", "ps_button_busy",
         "ps_clear_aria", "ps_echo_cep", "ps_echo_postal", "ps_echo_coordinate",
         "ps_echo_territory", "ps_echo_place", "ps_place_hint", "ps_not_found",
         "ps_territories_heading", "ps_places_heading", "ps_places_note",
         "ps_howto_title", "ps_close", "qs_title", "qs_more", "qs_got_it",
         "qs_full_howto", "qs_close_aria", "help_show_quickstart",
         *[f"qs_step{n}_{p}" for n in range(1, 5) for p in ("lead", "body")],
         *[f"ps_precision_{p}" for p in address.ZOOM_BY_PRECISION]]


@pytest.mark.parametrize("lang", ["en", "pt", "es", "fr"])
def test_every_language_has_the_keys(lang):
    from yvynation.utils.translations import TRANSLATIONS
    assert not [k for k in _KEYS if k not in TRANSLATIONS[lang]]


# --------------------------------------------------------------------------- #
# Canadian protected areas (CPCAD) — per-province files, OCAP exclusion
# --------------------------------------------------------------------------- #
import gzip
import os

from yvynation.utils import territory_kinds
from yvynation.utils.conservation_service import (
    CA_DEFAULT_PROVINCES, ProvincialProtectedAreaService)

_CA_DIR = os.path.join(os.path.dirname(ps.__file__), "protected_areas_ca")


def test_kinds_route_to_their_services():
    assert territory_kinds.is_conservation("conservation_ca")
    assert not territory_kinds.is_conservation("indigenous")
    assert territory_kinds.country_of("conservation_ca") == "Canada"
    assert territory_kinds.conservation_kind_for("Canada") == "conservation_ca"
    assert isinstance(territory_kinds.service_for("conservation_ca"),
                      ProvincialProtectedAreaService)


def test_no_canadian_indigenous_lands_kind():
    """OCAP: there is deliberately no kind for Canadian Indigenous lands."""
    assert set(territory_kinds.KINDS) == {"indigenous", "conservation", "conservation_ca"}


def test_bc_is_the_only_province_loaded_on_start():
    assert CA_DEFAULT_PROVINCES == ("BC",)
    svc = ProvincialProtectedAreaService()
    assert svc.loaded_provinces() == ["BC"]
    keys = svc.get_all_display_keys(provinces=["BC"])
    assert len(keys) > 1000
    info = svc.get_territory_info(keys[0])
    assert info["uf_sigla"] == "BC"


def test_loading_a_province_never_renames_another_provinces_areas():
    svc = ProvincialProtectedAreaService()
    before = set(svc.get_all_display_keys(provinces=["BC"]))
    assert svc.ensure_provinces(["AB"]) == ["AB"]
    assert set(svc.get_all_display_keys(provinces=["BC"])) == before
    assert svc.ensure_provinces(["AB"]) == []          # idempotent
    banff = [k for k in svc.get_all_display_keys(provinces=["AB"]) if k.startswith("Banff")]
    assert banff and svc.get_bounds_for_key(banff[0])["min_lat"] > 50


def test_session_view_is_filtered_by_province():
    svc = ProvincialProtectedAreaService()
    svc.ensure_provinces(["AB"])
    fc = svc.get_all_geojson_fc(provinces=["BC"])
    assert fc["features"] and {f["properties"]["uf"] for f in fc["features"]} == {"BC"}


def test_province_lookup():
    svc = ProvincialProtectedAreaService()
    assert svc.province_at(49.88, -119.49) == "BC"     # Kelowna
    assert svc.province_at(51.04, -114.07) == "AB"     # Calgary
    assert svc.province_at(45.50, -73.57) == "QC"      # Montréal
    assert svc.province_at(45.0, -40.0) is None        # Atlantic


def test_ocap_exclusion_is_recorded_and_applied():
    with open(os.path.join(_CA_DIR, "meta.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta["ocap_excluded_areas"] > 0
    assert "Indigenous" in meta["ocap_rule"]
    import geopandas as gpd
    df = gpd.read_file(f"/vsizip/{_CA_DIR}/BC.gpkg.zip/BC.gpkg", layer="cpcad",
                       ignore_geometry=True)
    assert not (df["esfera"] == "Indigenous peoples").any()
    assert not (df["owner_type"] == "Indigenous").any()


def test_every_province_file_has_an_overview():
    for name in os.listdir(_CA_DIR):
        if name.endswith(".gpkg.zip"):
            prov = name.split(".")[0]
            with gzip.open(os.path.join(_CA_DIR, f"{prov}.overview.geojson.gz"), "rt") as fh:
                assert json.load(fh)["features"]


@pytest.mark.parametrize("lang", ["en", "pt", "es", "fr"])
def test_canada_keys_in_every_language(lang):
    from yvynation.utils.translations import TRANSLATIONS
    keys = ["portal_conservation_ca_btn", "ca_pa_badge", "ca_provinces_label",
            "ca_add_province", "ca_provinces_hint", "ca_analysis_note",
            "ca_ocap_note", "ca_source_note", "ca_indigenous_ocap_title",
            "ca_indigenous_ocap_body", "ca_show_protected_areas"]
    assert not [k for k in keys if k not in TRANSLATIONS[lang]]


# --------------------------------------------------------------------------- #
# Parts of one protected area
# --------------------------------------------------------------------------- #
_MK = "Muskwa-Kechika Special Wildland Areas"


def test_parts_are_listed_largest_first_with_stable_ids():
    svc = ProvincialProtectedAreaService()
    parts = svc.get_parts(_MK)
    assert len(parts) == 39
    assert [p["rank"] for p in parts] == list(range(1, 40))
    assert all(a["ha"] >= b["ha"] for a, b in zip(parts, parts[1:]))
    assert len({p["id"] for p in parts}) == 39


def test_parts_geojson_holds_only_the_chosen_parts():
    svc = ProvincialProtectedAreaService()
    ids = [p["id"] for p in svc.get_parts(_MK)[:3]]
    gj = svc.get_parts_geojson(_MK, ids)
    assert gj["type"] == "MultiPolygon" and len(gj["coordinates"]) >= 3
    one = svc.get_parts_geojson(_MK, ids[:1])
    assert one["type"] in ("Polygon", "MultiPolygon")
    assert svc.get_parts_geojson(_MK, ["99999"]) is None


def test_a_point_picks_its_part():
    from shapely.geometry import shape
    svc = ProvincialProtectedAreaService()
    biggest = svc.get_parts(_MK)[0]
    pt = shape(svc.get_parts_geojson(_MK, [biggest["id"]])).representative_point()
    assert svc.part_at(_MK, pt.y, pt.x) == biggest["id"]
    assert svc.part_at(_MK, 49.0, -123.0) is None
