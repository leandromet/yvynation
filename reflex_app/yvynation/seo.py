"""Head tags for every Yvynation page: what search engines, AI answer tools and
link previews (WhatsApp, Slack, LinkedIn, X) read before any JavaScript runs.

Each page gets:

* a ``canonical`` link with a trailing slash. Every language version has its own
  URL (``/pt/``, ``/canada/fr/``, ``/usa/en/``…) and canonicals to itself;
* ``hreflang`` alternates to every other version of the same page, and
  ``x-default`` (English), in the head and in ``sitemap.xml``;
* an Open Graph and Twitter card with its own title, description and share
  image (``assets/og/<image>.jpg``, 1200×630, cut from the app's own maps);
* a schema.org ``WebApplication`` (``Article`` for the walkthroughs) that names
  the country it covers and points at the other country tools, in the same
  language where that tool has it, via ``relatedLink``.

The walkthroughs keep their own pt and en routes; they are real pairs.

``robots.txt`` and the share images are static files in ``assets/``;
``tests/test_seo.py`` keeps them in step with the routes here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import reflex as rx

from .utils.language_routes import TOOLS as TOOL_LANGS
from .utils.language_routes import variant_route

SITE = "https://yvynation.umaterra.com.br"
#: Yvynation's content is CC BY 4.0 (the footer of every page says so).
LICENSE = "https://creativecommons.org/licenses/by/4.0/"
IMAGE_W, IMAGE_H = 1200, 630

_LOCALE = {"en": "en_US", "pt": "pt_BR", "es": "es_ES", "fr": "fr_FR"}
_IN_LANGUAGE = {"en": "en", "pt": "pt-BR", "es": "es", "fr": "fr"}

#: hreflang code for each language the app speaks.
HREFLANG = {"en": "en", "pt": "pt-BR", "es": "es", "fr": "fr"}

BRAZIL, CANADA, USA = "Brazil", "Canada", "United States"
#: The tool each country's pages live under.
TOOL_BY_COUNTRY = {BRAZIL: "/", CANADA: "/canada", USA: "/usa"}


@dataclass(frozen=True)
class Page:
    route: str        # the route as registered with add_page
    title: str
    description: str
    image: str        # name of the file in assets/og/, without extension
    lang: str         # language of the title and description
    country: str      # the country the tool covers
    kind: str = "WebApplication"


#: Title and description of each tool, per language it answers to.
TOOL_COPY: dict[str, dict[str, tuple[str, str]]] = {
    "/": {
        "en": ("Yvynation - Land Monitoring Platform",
               "Land-cover history and forest change for Indigenous lands, conservation units "
               "and drawn areas in Brazil, from MapBiomas and Hansen."),
        "pt": ("Yvynation - Monitoramento de terras",
               "Histórico de cobertura do solo e de mudança florestal para terras indígenas, "
               "unidades de conservação e áreas desenhadas no Brasil, com MapBiomas e Hansen."),
        "es": ("Yvynation - Monitoreo de tierras",
               "Historial de cobertura del suelo y cambio forestal para tierras indígenas, "
               "unidades de conservación y áreas dibujadas en Brasil, con MapBiomas y Hansen."),
        "fr": ("Yvynation - Surveillance des terres",
               "Historique de la couverture terrestre et des changements forestiers pour les terres "
               "autochtones, les unités de conservation et les zones dessinées au Brésil, avec MapBiomas et Hansen."),
    },
    "/canada": {
        "en": ("Yvynation — Canada protected areas",
               "Land-cover history and forest change inside and around Canadian protected areas "
               "(CPCAD), starting with British Columbia."),
        "pt": ("Yvynation — Áreas protegidas do Canadá",
               "Histórico de cobertura do solo e de mudança florestal dentro e no entorno das áreas "
               "protegidas canadenses (CPCAD), começando pela Colúmbia Britânica."),
        "fr": ("Yvynation — Aires protégées du Canada",
               "Historique de la couverture terrestre et des changements forestiers dans et autour des "
               "aires protégées canadiennes (CPCAD), à commencer par la Colombie-Britannique."),
    },
    "/usa": {
        "en": ("Yvynation — USA protected areas",
               "Land-cover history and forest change inside and around protected areas of the lower 48 "
               "states (PAD-US, USGS), with Annual NLCD and Hansen."),
        "pt": ("Yvynation — Áreas protegidas dos EUA",
               "Histórico de cobertura do solo e de mudança florestal dentro e no entorno das áreas "
               "protegidas dos 48 estados contíguos (PAD-US, USGS), com NLCD anual e Hansen."),
    },
}
#: The share image of each tool (the same picture serves all its languages).
TOOL_IMAGE = {"/": "yvynation", "/canada": "canada", "/usa": "usa"}
TOOL_COUNTRY = {"/": BRAZIL, "/canada": CANADA, "/usa": USA}

_TOOL_PAGES = tuple(
    Page(variant_route(base, lang), title, description, TOOL_IMAGE[base], lang, TOOL_COUNTRY[base])
    for base, copy in TOOL_COPY.items()
    for lang, (title, description) in copy.items()
)

_WALKTHROUGH_PAGES = (
    Page("/demonstracao/terra-indigena", "Yvynation — demonstração: uma terra indígena",
         "Passo a passo: analisar uma terra indígena no Yvynation, com o histórico de "
         "cobertura do solo e a perda florestal da área.",
         "terra-indigena", "pt", BRAZIL, "Article"),
    Page("/walkthrough/indigenous-land", "Yvynation — walkthrough: an Indigenous land",
         "Step by step: analyse an Indigenous land in Yvynation, with its land-cover "
         "history and forest loss.",
         "terra-indigena", "en", BRAZIL, "Article"),
    Page("/demonstracao/unidade-conservacao", "Yvynation — demonstração: uma unidade de conservação",
         "Passo a passo: analisar uma unidade de conservação no Yvynation e compará-la "
         "com o entorno.",
         "unidade-conservacao", "pt", BRAZIL, "Article"),
    Page("/walkthrough/conservation-unit/brazil", "Yvynation — walkthrough: a conservation unit (Brazil)",
         "Step by step: analyse a Brazilian conservation unit in Yvynation and compare it "
         "with the land around it.",
         "unidade-conservacao", "en", BRAZIL, "Article"),
    Page("/walkthrough/conservation-unit", "Yvynation — walkthrough: a protected area in Kelowna",
         "Step by step: analyse a protected area in Kelowna, British Columbia, in Yvynation, "
         "and compare it with the land around it.",
         "canada", "en", CANADA, "Article"),
    Page("/demonstracao/desenho", "Yvynation — demonstração: uma área desenhada",
         "Passo a passo: analisar uma área que você desenha no mapa do Yvynation.",
         "desenho", "pt", BRAZIL, "Article"),
    Page("/walkthrough/drawn-area", "Yvynation — walkthrough: a drawn area",
         "Step by step: analyse an area you draw on the map in Yvynation.",
         "desenho", "en", BRAZIL, "Article"),
    Page("/demonstracao/lote", "Yvynation — demonstração: processamento em lote",
         "Passo a passo: analisar vários territórios de uma vez no Yvynation, do envio à "
         "exportação dos resultados.",
         "lote", "pt", BRAZIL, "Article"),
    Page("/walkthrough/batch", "Yvynation — walkthrough: batch processing",
         "Step by step: analyse up to 100 territories at once in Yvynation, from upload to "
         "exported results.",
         "lote", "en", BRAZIL, "Article"),
)

PAGES: dict[str, Page] = {p.route: p for p in (*_TOOL_PAGES, *_WALKTHROUGH_PAGES)}

#: The walkthrough pairs: (pt route, en route). The Kelowna walkthrough has no pt twin.
WALKTHROUGH_PAIRS = (
    ("/demonstracao/terra-indigena", "/walkthrough/indigenous-land"),
    ("/demonstracao/unidade-conservacao", "/walkthrough/conservation-unit/brazil"),
    ("/demonstracao/desenho", "/walkthrough/drawn-area"),
    ("/demonstracao/lote", "/walkthrough/batch"),
)


def canonical_path(route: str) -> str:
    """The URL path a page is known by: trailing slash, except the root."""
    return route.rstrip("/") + "/"


def url(route: str) -> str:
    return SITE + canonical_path(route)


def image_url(page: Page) -> str:
    return f"{SITE}/og/{page.image}.jpg"


def _tool_base(route: str) -> str | None:
    """The tool a language-version route belongs to, or ``None`` for a walkthrough."""
    for base, langs in TOOL_LANGS.items():
        for lang in langs:
            if route == variant_route(base, lang):
                return base
    return None


def alternates(route: str) -> list[tuple[str, str]]:
    """``(hreflang, absolute URL)`` for every language version of a page, x-default last."""
    base = _tool_base(route)
    if base is not None:
        out = [(HREFLANG[lang], url(variant_route(base, lang))) for lang in TOOL_LANGS[base]]
        return out + [("x-default", url(variant_route(base, "en")))]
    for pt, en in WALKTHROUGH_PAIRS:
        if route in (pt, en):
            return [("pt-BR", url(pt)), ("en", url(en)), ("x-default", url(pt))]
    return []


def sitemap_xml() -> str:
    """The sitemap: one ``<url>`` per canonical page, carrying its alternates."""
    blocks = []
    for route in sorted(PAGES, key=lambda r: url(r)):
        links = "".join(
            f'<xhtml:link rel="alternate" hreflang="{code}" href="{href}"/>'
            for code, href in alternates(route))
        blocks.append(f"  <url><loc>{url(route)}</loc>{links}</url>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!-- Generated from yvynation/seo.py (sitemap_xml); tests/test_seo.py fails when they drift. -->\n"
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(blocks) + "\n</urlset>\n"
    )


def _related(page: Page) -> list[str]:
    """A country tool links to the other two in the same language where they have it,
    English otherwise; a walkthrough links to its own country's tool in its language."""
    def in_language(base: str) -> str:
        lang = page.lang if page.lang in TOOL_LANGS[base] else "en"
        return url(variant_route(base, lang))

    if page.kind == "Article":
        return [in_language(TOOL_BY_COUNTRY[page.country])]
    return [in_language(base) for country, base in TOOL_BY_COUNTRY.items() if country != page.country]


def json_ld(route: str) -> dict:
    page = PAGES[route]
    here = url(route)
    return {
        "@context": "https://schema.org",
        "@type": page.kind,
        "name": page.title,
        "description": page.description,
        "url": here,
        "image": image_url(page),
        "inLanguage": _IN_LANGUAGE[page.lang],
        "isAccessibleForFree": True,
        "license": LICENSE,
        "spatialCoverage": {"@type": "Country", "name": page.country},
        "publisher": {"@type": "Organization", "name": "Yvynation", "url": SITE},
        "isPartOf": {"@type": "WebSite", "name": "Yvynation", "url": SITE},
        "relatedLink": _related(page),
    }


def page_kwargs(route: str) -> dict:
    """Keyword arguments for ``App.add_page``: title, description, share image and head tags."""
    page = PAGES[route]
    here = url(route)
    image = image_url(page)
    head = [
        rx.el.link(rel="canonical", href=here),
        *[rx.el.link(rel="alternate", href=href, custom_attrs={"hreflang": code})
          for code, href in alternates(route)],
        rx.el.meta(property="og:type", content="website"),
        rx.el.meta(property="og:site_name", content="Yvynation"),
        rx.el.meta(property="og:title", content=page.title),
        rx.el.meta(property="og:description", content=page.description),
        rx.el.meta(property="og:url", content=here),
        rx.el.meta(property="og:image:width", content=str(IMAGE_W)),
        rx.el.meta(property="og:image:height", content=str(IMAGE_H)),
        rx.el.meta(property="og:locale", content=_LOCALE[page.lang]),
        rx.el.meta(name="twitter:card", content="summary_large_image"),
        rx.el.meta(name="twitter:title", content=page.title),
        rx.el.meta(name="twitter:description", content=page.description),
        rx.el.meta(name="twitter:image", content=image),
        rx.el.script(custom_attrs={
            "type": "application/ld+json",
            # Raw JSON: the text-child form would be HTML-escaped by React's server render.
            "dangerouslySetInnerHTML": {"__html": json.dumps(json_ld(route), ensure_ascii=False)},
        }),
    ]
    # ``title`` and ``description`` become <title> and <meta name="description">; ``image``
    # becomes <meta property="og:image">. They are passed here rather than in ``head``
    # so Reflex emits each tag once.
    return {"title": page.title, "description": page.description, "image": image, "meta": head}
