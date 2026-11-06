"""The head tags, sitemap, robots.txt and share images agree with the routes.

``yvynation/seo.py`` is the single source; ``assets/sitemap.xml`` is generated from
it and ``assets/robots.txt`` points at it. These tests fail when a route gets a
page without its head data, when a share image is missing or the wrong size, or
when the static files were not regenerated after a route change.
"""

import json
import re
from pathlib import Path

import pytest

from yvynation import seo
from yvynation.pages.demonstracao import PAGINAS as DEMONSTRACOES
from yvynation.utils import language_routes as lr

ASSETS = Path(__file__).resolve().parent.parent / "assets"
WALKTHROUGH_ROUTES = [route for route, _page, _title in DEMONSTRACOES]
TOOL_ROUTES = [route for _base, _lang, route in lr.variant_routes()]


def test_every_registered_route_has_seo_data():
    assert set(TOOL_ROUTES + WALKTHROUGH_ROUTES) == set(seo.PAGES)


def test_canonical_urls_end_in_a_slash_and_are_absolute():
    for route in seo.PAGES:
        url = seo.url(route)
        assert url.startswith(seo.SITE + "/"), url
        assert url.endswith("/"), url


def test_every_page_with_alternates_declares_itself():
    # The Kelowna walkthrough has no pt twin, so it declares no alternates at all.
    for route in seo.PAGES:
        found = seo.alternates(route)
        if found:
            assert seo.url(route) in [href for _code, href in found], route


def test_sitemap_lists_exactly_the_canonical_urls():
    text = (ASSETS / "sitemap.xml").read_text(encoding="utf-8")
    locs = set(re.findall(r"<loc>([^<]+)</loc>", text))
    assert locs == {seo.url(route) for route in seo.PAGES}


def test_sitemap_carries_the_alternates_of_every_page():
    text = (ASSETS / "sitemap.xml").read_text(encoding="utf-8")
    blocks = re.findall(r"<url><loc>([^<]+)</loc>(.*?)</url>", text)
    assert len(blocks) == len(seo.PAGES)
    for loc, body in blocks:
        route = next(r for r in seo.PAGES if seo.url(r) == loc)
        declared = re.findall(r'hreflang="([^"]+)" href="([^"]+)"', body)
        assert declared == seo.alternates(route), loc


def test_robots_points_at_the_sitemap_and_keeps_the_socket_out():
    text = (ASSETS / "robots.txt").read_text(encoding="utf-8")
    assert "User-agent: *" in text
    assert f"Sitemap: {seo.SITE}/sitemap.xml" in text
    assert "Disallow: /_event" in text


@pytest.mark.parametrize("route", sorted(seo.PAGES))
def test_share_image_exists_and_is_a_card(route):
    pil = pytest.importorskip("PIL.Image")
    path = ASSETS / "og" / f"{seo.PAGES[route].image}.jpg"
    assert path.is_file(), path
    with pil.open(path) as im:
        assert im.size == (seo.IMAGE_W, seo.IMAGE_H)


def test_negotiation_prefers_query_then_browser_then_english():
    assert lr.negotiate("/", "fr", "pt-BR,pt;q=0.9") == "fr"
    assert lr.negotiate("/", None, "pt-BR,pt;q=0.9,en;q=0.5") == "pt"
    assert lr.negotiate("/canada", None, "es-ES,es;q=0.9") == "en"  # Canada has no Spanish
    assert lr.negotiate("/usa", "fr", None) == "en"                 # USA has no French
    assert lr.negotiate("/", None, None) == "en"
    assert lr.negotiate("/", None, "de;q=0.9,fr;q=0.2") == "fr"


def test_language_is_read_from_the_path():
    assert lr.language_from_path("/pt/") == "pt"
    assert lr.language_from_path("/canada/fr/") == "fr"
    assert lr.language_from_path("/usa/pt") == "pt"
    assert lr.language_from_path("/usa/fr/") is None      # USA has no French page
    assert lr.language_from_path("/demonstracao/lote/") is None


def test_switching_language_keeps_the_same_tool():
    assert lr.retarget_path("/canada/en/", "fr") == "/canada/fr/"
    assert lr.retarget_path("/pt/", "es") == "/es/"


def test_tool_alternates_cover_each_language_it_answers_to():
    for base, langs in lr.TOOLS.items():
        route = lr.variant_route(base, "en")
        codes = [code for code, _ in seo.alternates(route)]
        assert codes == [seo.HREFLANG[lang] for lang in langs] + ["x-default"], base


def test_walkthrough_pairs_point_at_each_other():
    for pt, en in seo.WALKTHROUGH_PAIRS:
        assert ("en", seo.url(en)) in seo.alternates(pt)
        assert ("pt-BR", seo.url(pt)) in seo.alternates(en)


def test_country_tools_link_to_the_other_two_in_the_same_language():
    assert set(seo.json_ld("/pt")["relatedLink"]) == {seo.url("/canada/pt"), seo.url("/usa/pt")}
    assert set(seo.json_ld("/usa/en")["relatedLink"]) == {seo.url("/en"), seo.url("/canada/en")}
    # Canada has no Spanish: the Spanish Brazil page falls back to English there.
    assert set(seo.json_ld("/es")["relatedLink"]) == {seo.url("/canada/en"), seo.url("/usa/en")}


def test_walkthroughs_link_to_their_own_country_tool():
    assert seo.json_ld("/walkthrough/batch")["relatedLink"] == [seo.url("/en")]
    assert seo.json_ld("/demonstracao/lote")["relatedLink"] == [seo.url("/pt")]
    assert seo.json_ld("/walkthrough/conservation-unit")["relatedLink"] == [seo.url("/canada/en")]


def test_json_ld_is_valid_and_names_the_country():
    for route in seo.PAGES:
        data = json.loads(json.dumps(seo.json_ld(route)))
        assert data["@context"] == "https://schema.org"
        assert data["spatialCoverage"]["name"] == seo.PAGES[route].country
        assert data["url"] == seo.url(route)


def test_page_head_does_not_repeat_what_add_page_emits():
    # title, description and og:image come from add_page's own arguments; a second
    # copy in the head would be emitted twice.
    for route in seo.PAGES:
        kwargs = seo.page_kwargs(route)
        assert kwargs["image"] == seo.image_url(seo.PAGES[route])
        assert all("og:image" not in str(component) or "og:image:" in str(component)
                   for component in kwargs["meta"])
        assert kwargs["title"] == seo.PAGES[route].title


def test_alternate_links_carry_their_hreflang_attribute():
    # rx.el.link drops unknown keyword arguments, so hreflang must travel in custom_attrs.
    for route in seo.PAGES:
        links = [str(c) for c in seo.page_kwargs(route)["meta"] if 'rel:"alternate"' in str(c)]
        expected = seo.alternates(route)
        assert len(links) == len(expected), route
        for link, (code, href) in zip(links, expected):
            assert f'hreflang:"{code}"' in link, (route, code)
            assert f'href:"{href}"' in link, (route, href)
