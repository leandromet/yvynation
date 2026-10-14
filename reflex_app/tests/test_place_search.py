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


# --------------------------------------------------------------------------- #
# Canadian protected areas (CPCAD) — per-province files, OCAP exclusion
# --------------------------------------------------------------------------- #
import gzip
import os

from yvynation.utils.conservation_service import (
    CA_DEFAULT_PROVINCES, ProvincialProtectedAreaService)

_CA_DIR = os.path.join(os.path.dirname(ps.__file__), "protected_areas_ca")




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


def test_part_areas_agree_with_the_zone_areas():
    """Part hectares and the zone card must come from equal-area maths. An
    earlier version measured parts in EPSG:3978 (Lambert conformal) and was
    ~5% off at 58°N — which the card then flagged as a disagreement between
    two of our own numbers."""
    from yvynation.canada._shared.zones import area_ha
    svc = ProvincialProtectedAreaService()
    parts = svc.get_parts(_MK)[:2]
    zone_ha = area_ha(svc.get_parts_geojson(_MK, [p["id"] for p in parts]))
    assert sum(p["ha"] for p in parts) == pytest.approx(zone_ha, rel=1e-3)


@pytest.mark.parametrize("year,expect", [
    (0, "no_year"), (2000, "before"), (2001, "before"), (2010, "split"), (2030, "after")])
def test_unsplit_note_names_the_actual_reason(year, expect):
    """Hansen's record is 2001–2024. An area established in 2000 has every
    year of loss AFTER it — that is a finding, not a missing date."""
    from yvynation.canada.services import hansen
    split = hansen.splits_at(year)
    if expect == "split":
        assert split == year
        return
    assert split is None
    if expect == "before":
        assert year <= hansen.LOSS_YEAR_START
    elif expect == "after":
        assert year > hansen.LOSS_YEAR_END
    else:
        assert not year


def test_unsplit_note_keys_exist_in_both_languages():
    from yvynation.canada.translations import TRANSLATIONS_EN, TRANSLATIONS_PT
    for k in ("floresta_year_before_record_note", "floresta_year_after_record_note",
              "floresta_no_start_date_note"):
        assert k in TRANSLATIONS_EN and k in TRANSLATIONS_PT
    assert "{year}" in TRANSLATIONS_EN["floresta_year_before_record_note"]



# --------------------------------------------------------------------------- #
# The Canada page (/canada) — its own translations, API routes and data
# --------------------------------------------------------------------------- #
def test_there_is_no_canadian_indigenous_lands_path():
    """OCAP: Yvynation analyses Canadian protected areas only. The Brazil
    page's territory kinds are Brazilian; no Canadian Indigenous kind exists
    anywhere, and the page's data omits Indigenous-governed areas."""
    import yvynation.state._territory as terr
    src = open(terr.__file__, encoding="utf-8").read()
    assert "conservation_ca" not in src


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_canada_page_keys(lang):
    from yvynation.canada.translations import TRANSLATIONS_EN, TRANSLATIONS_PT
    table = {"en": TRANSLATIONS_EN, "pt": TRANSLATIONS_PT}[lang]
    keys = ["area_card_title", "area_disclosure", "ca_ocap_note", "ca_source_note",
            "ca_parts_title", "ca_parts_apply", "provinces_title", "candidates_note",
            "tab_vlce2", "how_to_read", "qs_title", "help_dialog_title",
            *[f"read_{t}" for t in ("cobertura", "vlce2", "transicoes", "floresta",
                                    "biomassa", "paisagem", "fogo", "validacao")]]
    assert not [k for k in keys if k not in table]


def test_every_results_tab_has_a_how_to_read_block():
    """One explanation per tab, in both languages — each figure encodes
    something non-obvious (stacked shares, flows, a split at a date…)."""
    import os
    from yvynation.canada import components
    root = os.path.dirname(components.__file__)
    src = open(os.path.join(root, "results.py"), encoding="utf-8").read() + \
          open(os.path.join(root, "validacao.py"), encoding="utf-8").read()
    for tab in ("cobertura", "vlce2", "transicoes", "floresta", "biomassa",
                "paisagem", "fogo", "validacao"):
        assert f'how_to_read("{tab}")' in src, tab


def test_canada_api_serves_province_files():
    from yvynation.canada import api
    paths = [r.path for r in api.routes()]
    assert "/_cpcad/{province}.geojson" in paths and "/_ecozones.geojson" in paths


def test_brazil_page_no_longer_offers_a_canada_mode():
    """Canada has its own page: Brazil switches to it through the header's
    region toggle (navigation), no sidebar switches region in place, and the
    AAFC placeholder tab is gone."""
    import os
    import yvynation.components as c
    import yvynation.pages as pg
    root = os.path.dirname(c.__file__)
    for f in ("territory_sidebar.py", "geometry_sidebar.py", "sidebar.py"):
        src = open(os.path.join(root, f), encoding="utf-8").read()
        assert 'set_country("Canada")' not in src, f
        assert "_region_selector" not in src, f
    assert 'value="aafc"' not in open(os.path.join(root, "analysis_tabs.py"), encoding="utf-8").read()
    assert 'region_toggle("brazil"' in open(os.path.join(os.path.dirname(pg.__file__), "index.py"), encoding="utf-8").read()


# --------------------------------------------------------------------------- #
# French on the Canada page
# --------------------------------------------------------------------------- #
import re as _re


def _placeholders(text: str) -> set:
    return set(_re.findall(r"\{[a-z_]+\}", text))


def test_french_covers_every_string_the_canada_page_reads():
    """Dead inherited keys (parcel_*, square_*, gbif_*) are not translated and
    need not be; everything the page can show must be."""
    import os
    from yvynation.canada import translations as T
    root = os.path.dirname(T.__file__)
    src = ""
    for base, _d, files in os.walk(os.path.dirname(root)):
        if "_shared" in base or "translations" in base:
            continue
        for f in files:
            if f.endswith(".py"):
                src += open(os.path.join(base, f), encoding="utf-8").read()
    src += open(os.path.join(os.path.dirname(root), "..", "components", "quickstart.py"),
                encoding="utf-8").read()
    # Translations are read as tr["key"] / msgs["key"]; a bare string such as a
    # dict key in the area record ("parcel_status") is not a UI string.
    literal = set(_re.findall(r'\[\s*f?["\']([a-z][a-z0-9_]*)["\']\s*\]', src))
    shown = {k for k in T.TRANSLATIONS_EN if k in literal and T.TRANSLATIONS_EN[k]}
    shown |= {k for k in T.TRANSLATIONS_EN if k.startswith(
        ("precision_", "read_", "qs_", "help_step", "help_limit", "region_"))}
    missing = sorted(k for k in shown if k not in T.TRANSLATIONS_FR)
    # keys deliberately left to the English fallback: none of the ones above
    assert not missing, missing


def test_french_placeholders_match_english():
    from yvynation.canada.translations import TRANSLATIONS_EN, TRANSLATIONS_FR
    bad = [k for k, v in TRANSLATIONS_FR.items()
           if k in TRANSLATIONS_EN and _placeholders(v) != _placeholders(TRANSLATIONS_EN[k])]
    assert not bad, bad


def test_french_falls_back_to_english_never_to_blank():
    from yvynation.canada.translations import get_translations, TRANSLATIONS_EN
    fr = get_translations("fr")
    assert set(fr) == set(TRANSLATIONS_EN)
    # every key that has text in English has text in French (a few are
    # deliberately empty in English, e.g. cite_example_body)
    assert all(fr[k] for k in fr if TRANSLATIONS_EN[k])
    assert fr["tab_vlce2"] == "Occupation du sol"


def test_french_is_a_supported_language_with_fr_vocabularies():
    from yvynation.canada.config import aafc, ecozones, settings, vlce2
    assert "fr" in settings.SUPPORTED_LANGUAGES
    assert set(aafc.ACI_LABELS_FR) == set(aafc.ACI_LABELS_EN)
    assert set(vlce2.VLCE2_LABELS_FR) == set(vlce2.VLCE2_LABELS_EN)
    assert set(vlce2.GROUP_LABELS_FR) == set(vlce2.GROUP_LABELS_EN)
    assert set(ecozones.ECOZONE_NAMES_FR) == set(ecozones.ECOZONE_NAMES_EN)
    assert aafc.label(210, "fr") == "Conifères" and vlce2.label(210, "fr") == "Conifères"
    assert aafc.label(99999, "fr") == "Classe 99999"
    assert ecozones.name(13, "fr") == "Maritime du Pacifique"


def test_french_chart_labels_and_decimal_comma():
    from yvynation.canada.components import charts
    from yvynation.canada.services import zones
    assert charts._t("fr", "Loss (ha)", "Perda (ha)", "Perte (ha)") == "Perte (ha)"
    assert charts.hansen_period_labels("fr")["antes_da_parcela"] == "Avant la création"
    fig = charts.land_cover_history_figure([], lang="fr")
    assert fig.layout.annotations[0].text == "Aucune donnée"
    assert "1,5 km" in zones._ring_label(0, 1500, "fr")
    assert "1.5 km" in zones._ring_label(0, 1500, "en")


def test_citation_sources_are_aligned_across_the_three_languages():
    from yvynation.canada.config import citation as c
    assert len(c.DATA_SOURCES_EN) == len(c.DATA_SOURCES_PT) == len(c.DATA_SOURCES_FR)
    # same dataset in the same slot: the English and French entries share a DOI/host
    for en, fr in zip(c.DATA_SOURCES_EN, c.DATA_SOURCES_FR):
        assert en[2].split("/")[2] == fr[2].split("/")[2], (en[0], fr[0])
    assert "Yvynation Canada" in c.CITATION_TEXT_FR
    # the descriptions name the tabs the page actually has
    for text in [d for _n, d, _u in c.DATA_SOURCES_EN]:
        assert "Cobertura" not in text and "Floresta" not in text


def test_ecozone_features_carry_a_french_zone_name():
    from yvynation.canada.services import ecozones
    spec = ecozones.vector_spec("ecozone", lang="fr")
    assert spec["tooltip"][0]["property"] == "name_fr"
    assert {"label": "Français", "property": "name_fr"} not in spec["tooltip"]
    spec = ecozones.vector_spec("ecoregion", lang="fr")
    assert any(t["property"] == "zone_name_fr" for t in spec["tooltip"])
    assert any(t["property"] == "parent_name_fr" for t in
               ecozones.vector_spec("ecodistrict", lang="fr")["tooltip"])
    # the cache filename carries the schema version, so old files cannot be reused
    from yvynation.canada.config import ecozones as cfg
    assert all(".v2." in lvl.cache_filename for lvl in cfg.LEVELS.values())


# --------------------------------------------------------------------------- #
# The Brazil / Canada region toggle
# --------------------------------------------------------------------------- #
def test_region_toggle_links_carry_the_language_and_mark_the_current_region():
    from yvynation.components.region_toggle import region_toggle
    import reflex as rx
    html = str(region_toggle("canada", language="fr", labels=("Brésil", "Canada"),
                             aria_label="Région"))
    assert "/?lang=fr" in html                       # Brazil is a link …
    assert "aria_current" in html or "aria-current" in html   # … Canada is current
    assert "/canada?lang=fr" not in html             # the current region is not a link


def test_translations_exist_for_the_toggle_everywhere():
    from yvynation.utils.translations import TRANSLATIONS
    from yvynation.canada.translations import get_translations
    for lang in ("en", "pt", "es", "fr"):
        for k in ("region_brazil", "region_canada", "region_label"):
            assert k in TRANSLATIONS[lang]
    for lang in ("en", "pt", "fr"):
        assert get_translations(lang)["region_label"]


def test_register_vocabulary_covers_every_value_in_the_data():
    """A value the table does not know would silently stay English in the
    French card — so every value occurring in any province file must be in it."""
    import glob
    import geopandas as gpd
    import pandas as pd
    from yvynation.canada.config import cpcad_vocab as V
    files = sorted(glob.glob(os.path.join(_CA_DIR, "*.gpkg.zip")))
    df = pd.concat([gpd.read_file(f"/vsizip/{f}/{os.path.basename(f)[:-4]}",
                                  layer="cpcad", ignore_geometry=True) for f in files])
    for col, table in (("grupo", "pa_oecm"), ("status", "status"),
                       ("esfera", "governance"), ("owner_type", "owner")):
        values = set(df[col].dropna().astype(str)) - {""}
        assert values <= set(V.TABLES[table]), (col, sorted(values - set(V.TABLES[table])))
    # IUCN categories (Ia … VI) are the same in every language; only the two
    # non-category values need translating
    assert {v for v in df["iucn_cat"].dropna().astype(str) if v.startswith("Not")} \
        <= set(V.TABLES["iucn"])


def test_register_vocabulary_translates_and_passes_unknowns_through():
    from yvynation.canada.config import cpcad_vocab as V
    assert V.translate("governance", "Sub-national government", "fr") == "Gouvernement infranational"
    assert V.translate("status", "Designated", "pt") == "Designada"
    assert V.translate("status", "Designated", "en") == "Designated"
    assert V.translate("status", "Something new", "fr") == "Something new"
    for table in V.TABLES.values():
        for tr in table.values():
            assert tr["pt"] and tr["fr"]


def test_quickstart_hides_while_an_area_is_selected():
    """The card's buttons sit at its bottom; with the results drawer open they
    would be underneath it. The Canada page hides the card once an area is
    chosen."""
    import os
    import yvynation.canada.pages as pg
    src = open(os.path.join(os.path.dirname(pg.__file__), "index.py"), encoding="utf-8").read()
    assert "hide_when=S.has_parcel" in src
