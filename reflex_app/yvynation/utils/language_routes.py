"""Language-prefixed URLs for the country tools.

The pages live at ``/<lang>/`` (Brazil), ``/canada/<lang>/`` and ``/usa/<lang>/``,
one URL per language, so each language has its own address that search engines
and link previews can index (see ``yvynation/seo.py``).

The bare ``/``, ``/canada`` and ``/usa`` answer with a 302 to the prefixed URL,
decided on the server: a ``?lang=`` from an older link wins, then the browser's
``Accept-Language``, then English. The response varies on ``Accept-Language``.
Other query parameters (``?area=``, ``?modo=``, ``?busca=``) are kept.

Switching language in the app does not navigate (that would reset the analysis
on screen); it updates the address bar with ``history.replaceState`` instead.
"""

from __future__ import annotations

import json
from typing import Callable
from urllib.parse import urlencode

from html import escape

from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route

from ..components.lang_pref import STORAGE_KEY, detect_script, store_script

#: The languages each tool answers to, in toggle order. Brazil has all four.
TOOLS: dict[str, tuple[str, ...]] = {
    "/": ("en", "pt", "es", "fr"),
    "/canada": ("en", "pt", "fr"),
    "/usa": ("en", "pt"),
}
ALL_LANGS = ("en", "pt", "es", "fr")
DEFAULT = "en"


def variant_route(base: str, lang: str) -> str:
    """The Reflex route of one language version, without a trailing slash: ``/pt``, ``/canada/fr``."""
    return f"/{lang}" if base == "/" else f"{base}/{lang}"


def variant_path(base: str, lang: str) -> str:
    """The public path of one language version, with the trailing slash: ``/pt/``, ``/canada/fr/``."""
    return variant_route(base, lang) + "/"


def variant_routes() -> list[tuple[str, str, str]]:
    """``(base, lang, route)`` for every tool language, in registration order."""
    return [(base, lang, variant_route(base, lang)) for base, langs in TOOLS.items() for lang in langs]


def base_of(path: str) -> str:
    """Which tool a path belongs to: ``/canada`` or ``/usa`` by prefix, else ``/``."""
    for base in ("/canada", "/usa"):
        if path == base or path.startswith(base + "/"):
            return base
    return "/"


def language_from_path(path: str) -> str | None:
    """The language a prefixed path names, or ``None`` for any other path."""
    parts = [p for p in path.split("/") if p]
    if not parts or parts[-1] not in ALL_LANGS:
        return None
    base = base_of(path)
    if parts[-1] not in TOOLS[base]:
        return None
    return parts[-1]


def retarget_path(path: str, lang: str) -> str:
    """The same tool's path in another language (for the address bar)."""
    return variant_path(base_of(path), lang)


def replace_url_script(path: str, lang: str) -> str:
    """Script that rewrites the address bar to another language's URL, without a reload,
    and remembers the choice for the next visit (components/lang_pref.py)."""
    return (f"window.history.replaceState(window.history.state, '', {json.dumps(retarget_path(path, lang))});"
            + store_script(lang))


def _accepted(header: str) -> list[str]:
    """Primary language tags from an Accept-Language header, best first."""
    ranked: list[tuple[float, str]] = []
    for part in (header or "").split(","):
        bits = [b.strip() for b in part.split(";")]
        tag = bits[0].lower()
        if not tag or tag == "*":
            continue
        quality = 1.0
        for extra in bits[1:]:
            if extra.startswith("q="):
                try:
                    quality = float(extra[2:])
                except ValueError:
                    quality = 0.0
        if quality > 0:
            ranked.append((quality, tag.split("-")[0]))
    return [code for _, code in sorted(ranked, key=lambda item: -item[0])]


def negotiate(base: str, query_lang: str | None, accept_language: str | None) -> str:
    """The language a bare tool URL should land on."""
    supported = TOOLS[base]
    if query_lang in supported:
        return query_lang
    for code in _accepted(accept_language or ""):
        if code in supported:
            return code
    return DEFAULT


def redirect_script(base: str) -> str:
    """Browser script for a bare tool URL: send the reader to their language's page,
    keeping the other query parameters. The order is the suite's (lang_pref.py)."""
    supported = TOOLS[base]
    paths = json.dumps({lang: variant_path(base, lang) for lang in supported})
    supported_json = json.dumps(list(supported))
    return f"""(function () {{
  var supported = {supported_json};
  var paths = {paths};
  var params = new URLSearchParams(location.search);
  var asked = params.get('lang');
  if (supported.indexOf(asked) >= 0) {{ try {{ localStorage.setItem('{STORAGE_KEY}', asked); }} catch (e) {{}} }}
  var lang = {detect_script(supported)} || '{DEFAULT}';
  params.delete('lang');
  var rest = params.toString();
  location.replace(paths[lang] + (rest ? '?' + rest : ''));
}})();"""


def _shell(base: str) -> Callable:
    """The bare tool URL: a page that sends the reader to their language's page.

    The order is the suite's (components/lang_pref.py): ``?lang=`` (and it is then
    remembered), the remembered choice, the browser's languages. The browser runs
    that before the first paint. Without JavaScript the meta refresh goes to the
    server's guess (``Accept-Language``, then English), so the page never stalls.
    """
    supported = TOOLS[base]
    paths = json.dumps({lang: variant_path(base, lang) for lang in supported})
    supported_json = json.dumps(list(supported))

    async def endpoint(request: Request) -> HTMLResponse:
        query = request.query_params.get("lang")
        guess = negotiate(base, query, request.headers.get("accept-language"))
        kept = [(k, v) for k, v in request.query_params.multi_items() if k != "lang"]
        tail = f"?{urlencode(kept)}" if kept else ""
        fallback = variant_path(base, guess) + tail
        page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Yvynation</title>
<link rel="canonical" href="{escape(variant_path(base, DEFAULT))}">
<meta http-equiv="refresh" content="0; url={escape(fallback, quote=True)}">
<script>
(function () {{
  var supported = {supported_json};
  var paths = {paths};
  var params = new URLSearchParams(location.search);
  var asked = params.get('lang');
  if (supported.indexOf(asked) >= 0) {{ try {{ localStorage.setItem('{STORAGE_KEY}', asked); }} catch (e) {{}} }}
  var lang = {detect_script(supported)};
  if (!lang) return;
  params.delete('lang');
  var rest = params.toString();
  location.replace(paths[lang] + (rest ? '?' + rest : ''));
}})();
</script>
</head><body><a href="{escape(fallback, quote=True)}">Yvynation</a></body></html>
"""
        return HTMLResponse(page, headers={"Vary": "Accept-Language", "Cache-Control": "no-cache"})
    return endpoint


def language_redirect_routes() -> list[Route]:
    """Starlette routes for the bare tool URLs, with and without the trailing slash."""
    routes: list[Route] = []
    for base in TOOLS:
        for path in ({base, base + "/"} if base != "/" else {"/"}):
            routes.append(Route(path, _shell(base), methods=["GET", "HEAD"]))
    return routes
