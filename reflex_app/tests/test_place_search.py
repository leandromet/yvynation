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


def test_region_bounds_cover_both_regions():
    assert set(ps.REGION_BOUNDS) == {"Brazil", "Canada"}


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
