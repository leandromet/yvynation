"""Resolving what the user typed into the "Find a place" box.

Same shape as the sibling apps' search (camposcope/naturametrics
``services/geocode.py``), sized to Yvynation's two regions: one box, five
resolvers, tried in a fixed order and stopping at the first match —

1. a Brazilian CEP (``78890-000``),
2. a Canadian postal code (``V1Y 2B3``),
3. a coordinate (decimal, degrees-minutes-seconds, or a Google Maps link),
4. a territory name from the list the current mode has loaded,
5. a place name or street address (Nominatim; BC's address register first
   for a BC civic address — see ``utils/address.py``).

The first four are exact; only the fifth guesses, so most searches never
reach a third party. :func:`resolve` classifies without any network call —
that is what lets the "read as" line update on every keystroke.

**A place frames the map and selects nothing.** A territory match is offered
as a territory, and only *choosing* it runs the existing selection
(``set_selected_territory``) — a fuzzy name match never silently loads one.
"""

from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

from . import address
from .address import Place

#: (west, south, east, north) — the two regions the app analyses.
BRAZIL_BBOX = (-74.5, -34.5, -33.5, 6.5)
CANADA_BBOX = (-141.5, 41.0, -52.0, 83.5)

GEOCODER_URL = os.environ.get("YVY_GEOCODER_URL",
                              "https://nominatim.openstreetmap.org/search")
GEOCODER_ENABLED = os.environ.get("YVY_GEOCODER_ENABLED", "true").lower() != "false"
GEOCODER_USER_AGENT = os.environ.get(
    "YVY_GEOCODER_USER_AGENT", "yvynation/1.0 (contact: leandromet@gmail.com)")


class GeocodeError(RuntimeError):
    """A failure talking to the geocoding service."""


def _in(bbox, lat: float, lon: float) -> bool:
    w, s, e, n = bbox
    return s <= lat <= n and w <= lon <= e


def in_regions(lat: float, lon: float) -> bool:
    return _in(BRAZIL_BBOX, lat, lon) or _in(CANADA_BBOX, lat, lon)


# --------------------------------------------------------------------------- #
# Coordinates  (the sibling apps' parser, accepting either region)
# --------------------------------------------------------------------------- #
_GMAPS_AT = re.compile(r"@(-?\d+(?:[.,]\d+)?),(-?\d+(?:[.,]\d+)?)")
_GMAPS_Q = re.compile(r"[?&]q=(-?\d+(?:[.,]\d+)?)(?:,|%2C)\s*(-?\d+(?:[.,]\d+)?)")
_DMS = re.compile(
    r"""(?P<deg>\d{1,3})\s*[°º:\s]\s*
        (?P<min>\d{1,2})\s*['′:\s]\s*
        (?P<sec>\d{1,2}(?:[.,]\d+)?)\s*(?:["”″']{0,2})\s*
        (?P<hem>[NSEWLO])""",
    re.VERBOSE | re.IGNORECASE,
)
_DECIMAL_PAIR = re.compile(
    r"^\s*(-?\d{1,3}(?:[.,]\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:[.,]\d+)?)\s*$"
)


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lon: float


def _f(raw: str) -> float:
    # pt-BR keyboards produce "-12,4979 -55,4977"; accept both separators.
    return float(raw.strip().replace(",", "."))


def parse_coordinates(text: str) -> Optional[Coordinate]:
    """``None`` when the text is not a coordinate; ``ValueError`` when it is
    one but unusable (outside both regions, or transposed) — that deserves a
    message, not a silent fall-through to a place search. Latitude first."""
    raw = (text or "").strip()
    if not raw:
        return None
    for pattern in (_GMAPS_AT, _GMAPS_Q):
        m = pattern.search(raw)
        if m:
            return _validated(_f(m.group(1)), _f(m.group(2)))
    dms = list(_DMS.finditer(raw))
    if len(dms) >= 2:
        values = {}
        for m in dms[:2]:
            hem = m.group("hem").upper()
            v = float(m.group("deg")) + float(m.group("min")) / 60 + _f(m.group("sec")) / 3600
            v *= -1 if hem in ("S", "W", "O") else 1
            values["lat" if hem in ("N", "S") else "lon"] = v
        if "lat" in values and "lon" in values:
            return _validated(values["lat"], values["lon"])
    m = _DECIMAL_PAIR.match(raw)
    if m:
        a, b = m.group(1), m.group(2)
        if "," in a and "." in a:
            raise ValueError(f"Ambiguous coordinate: {a!r}")
        return _validated(_f(a), _f(b))
    return None


def _validated(lat: float, lon: float) -> Coordinate:
    if in_regions(lat, lon):
        return Coordinate(lat, lon)
    if in_regions(lon, lat):
        raise ValueError(
            f"{lat:.4f}, {lon:.4f} is outside Brazil and Canada, but "
            f"{lon:.4f}, {lat:.4f} would be inside — the values look "
            "transposed. Latitude comes first.")
    raise ValueError(f"{lat:.4f}, {lon:.4f} is outside Brazil and Canada.")


# --------------------------------------------------------------------------- #
# Territory names  (local — the list the current mode already loaded)
# --------------------------------------------------------------------------- #
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def match_territories(text: str, names: Sequence[str], limit: int = 8) -> List[str]:
    """Prefix matches first, then substring — accent- and case-blind, so
    "jau" finds "Parque Nacional do Jaú". Needs three characters: shorter
    than that matches half the list."""
    needle = _norm(text)
    if len(needle) < 3:
        return []
    normed = [(n, _norm(n)) for n in names]
    prefix = [n for n, k in normed if k.startswith(needle)]
    rest = [n for n, k in normed if needle in k and n not in prefix]
    return (prefix + rest)[:limit]


# --------------------------------------------------------------------------- #
# The resolver
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Resolution:
    kind: str        # "cep" | "postal" | "coordenada" | "territorio" | "lugar" | "vazio"
    payload: Any = None
    territories: List[str] = field(default_factory=list)


def resolve(text: str, territory_names: Sequence[str] = ()) -> Resolution:
    """Classify the input without performing any network call."""
    raw = (text or "").strip()
    if not raw:
        return Resolution("vazio")
    cep = address.parse_cep(raw)
    if cep:
        return Resolution("cep", cep)
    postal = address.parse_ca_postal(raw)
    if postal:
        return Resolution("postal", postal)
    coord = parse_coordinates(raw)
    if coord is not None:
        return Resolution("coordenada", coord)
    hits = match_territories(raw, territory_names)
    if hits:
        return Resolution("territorio", hits, hits)
    return Resolution("lugar", raw)


# --------------------------------------------------------------------------- #
# Network side
# --------------------------------------------------------------------------- #
_geocoder = address.AddressGeocoder(
    url=GEOCODER_URL,
    user_agent=GEOCODER_USER_AGENT,
    accept_language="pt-BR,pt,en,fr",
    countrycodes="br,ca",
    enabled=GEOCODER_ENABLED,
    keep=in_regions,
)


def _guard() -> None:
    if not GEOCODER_ENABLED:
        raise GeocodeError("Place search is disabled in this installation.")


def search_places(query: str, *, limit: int = 6) -> List[Place]:
    _guard()
    bc = (_geocoder.search_bc_address(query)
          if address.looks_like_street_address(query) else [])
    if any(p.precision == "endereco" for p in bc):
        return bc[:limit]
    try:
        osm = _geocoder.search(query, limit=limit)
    except address.AddressError as exc:
        if bc:
            return bc[:limit]
        raise GeocodeError(f"Could not reach the place-search service: {exc}")
    return address.merge(bc, osm, limit=limit)


def search_cep(digits: str) -> List[Place]:
    _guard()
    try:
        places, _info = _geocoder.search_cep(digits)
    except address.AddressError as exc:
        raise GeocodeError(f"Could not reach the place-search service: {exc}")
    return places


def search_postal(code: str) -> List[Place]:
    _guard()
    try:
        return _geocoder.search_ca_postal(code)
    except address.AddressError as exc:
        raise GeocodeError(f"Could not reach the place-search service: {exc}")


# --------------------------------------------------------------------------- #
# Framing the Folium map
# --------------------------------------------------------------------------- #
#: The map is a Folium document inside a same-origin ``srcdoc`` iframe and is
#: rebuilt server-side whenever its *layers* change. Re-rendering it to move
#: the view would cost an Earth Engine round trip per search, so the view is
#: moved in the browser instead: find the iframe's ``L.Map`` (the same lookup
#: ``components/map.py``'s draw bridge uses) and fit / centre it, dropping a
#: pin.
#:
#: **Surviving a rebuild.** Rebuilds happen without the user doing anything —
#: the territory list finishing its background load is one — and each new
#: document opens at build_map's default view, silently undoing the search.
#: So the last framing is kept on the parent window and a light watcher
#: re-applies it to each new map document — but only when that document came
#: up at *exactly* the untouched default (``DEFAULT_VIEW`` below). A rebuild
#: that fitted itself to a selected territory or drawing starts somewhere else
#: and is left alone: an analysis subject always wins over a search.
DEFAULT_VIEW = {"lat": -15.0, "lng": -52.0, "zoom": 5}   # utils/map_builder.py

_FRAME_JS = """
(function () {
  var spec = {bounds: %(bounds)s, pin: %(pin)s, zoom: %(zoom)s, view: %(view)s};
  var DEF = %(default)s;
  function findMap() {
    var ifr = document.querySelectorAll('#map-container iframe');
    var w = ifr.length ? ifr[ifr.length - 1].contentWindow : null;
    if (!w || !w.L) return null;
    for (var k in w) {
      try { if (w[k] instanceof w.L.Map) return {w: w, map: w[k]}; } catch (e) {}
    }
    return null;
  }
  function apply(w, map, f) {
    if (f.bounds) map.fitBounds(f.bounds, {padding: [24, 24], maxZoom: 14});
    else if (f.view) map.setView([f.view[0], f.view[1]], f.view[2]);
    else if (f.pin) map.setView(f.pin, f.zoom);
    if (w.__yvySearchPin) { map.removeLayer(w.__yvySearchPin); w.__yvySearchPin = null; }
    if (f.pin) {
      w.__yvySearchPin = w.L.circleMarker(f.pin, {radius: 8, color: '#ffffff',
        weight: 3, fillColor: '#0090ff', fillOpacity: 1, interactive: false}).addTo(map);
    }
    w.__yvyFramed = true;
  }
  window.__yvyLastFrame = spec;
  function go() {
    var m = findMap();
    if (!m) return false;
    apply(m.w, m.map, spec);
    return true;
  }
  if (!go()) {
    var n = 0, t = setInterval(function () { if (go() || ++n > 40) clearInterval(t); }, 250);
  }
  if (!window.__yvyFrameWatch) {
    window.__yvyFrameWatch = setInterval(function () {
      var f = window.__yvyLastFrame;
      if (!f) return;
      var m = findMap();
      if (!m || m.w.__yvyFramed) return;
      m.w.__yvyFramed = true;            // look at each new document once
      var c = m.map.getCenter();
      if (m.map.getZoom() === DEF.zoom && Math.abs(c.lat - DEF.lat) < 1e-6 &&
          Math.abs(c.lng - DEF.lng) < 1e-6) {
        apply(m.w, m.map, f);
      }
    }, 400);
  }
})();
"""

#: Map clicks → Reflex, for loading a Canadian province on demand. The Folium
#: map lives in an iframe that is rebuilt now and then, so a light watcher
#: binds a click listener to each new map document once. The listener only
#: forwards when ``#yvy-ca-click-btn`` exists — rendered only in Canadian
#: protected-area mode (components/map.py) — so no other mode sends a thing.
CLICK_BRIDGE_JS = """
(function () {
  if (window.__yvyClickBridge) return;
  window.__yvyClickBridge = true;
  setInterval(function () {
    var ifr = document.querySelectorAll('#map-container iframe');
    var w = ifr.length ? ifr[ifr.length - 1].contentWindow : null;
    if (!w || !w.L || w.__yvyClickBound) return;
    var map = null;
    for (var k in w) {
      try { if (w[k] instanceof w.L.Map) { map = w[k]; break; } } catch (e) {}
    }
    if (!map) return;
    w.__yvyClickBound = true;
    map.on('click', function (e) {
      var btn = document.getElementById('yvy-ca-click-btn');
      if (!btn) return;
      // The view travels with the point: loading a province rebuilds the
      // map, and the rebuild should come back to where the user was looking.
      var c = map.getCenter();
      window.__yvyCaClick = [e.latlng.lat, e.latlng.lng, c.lat, c.lng, map.getZoom()];
      btn.click();
    });
  }, 500);
})();
"""

#: Forget the last framing and remove the pin (the search box's ✕).
CLEAR_JS = """
(function () {
  window.__yvyLastFrame = null;
  var f = document.querySelectorAll('#map-container iframe');
  var w = f.length ? f[f.length - 1].contentWindow : null;
  if (w && w.__yvySearchPin) {
    try { w.__yvySearchPin.remove(); } catch (e) {}
    w.__yvySearchPin = null;
  }
})();
"""


def frame_js(*, bounds: Optional[list] = None, pin: Optional[list] = None,
             zoom: int = 14, view: Optional[list] = None) -> str:
    """JS that frames the Folium map on ``bounds`` (``[[s, w], [n, e]]``),
    restores ``view`` (``[lat, lon, zoom]``, no pin), or centres it on ``pin``
    (``[lat, lon]``) at ``zoom``, pinning ``pin``."""
    import json
    return _FRAME_JS % {"bounds": json.dumps(bounds), "pin": json.dumps(pin),
                        "zoom": int(zoom), "view": json.dumps(view),
                        "default": json.dumps(DEFAULT_VIEW)}


#: Whole-region framings for the Brazil/Canada switch.
REGION_BOUNDS = {
    "Brazil": [[-33.8, -74.0], [5.3, -34.7]],
    # Capped at 70°N: framing to the Arctic islands would leave the populated
    # south — where nearly every analysis happens — a strip along the bottom.
    "Canada": [[41.7, -141.0], [70.0, -52.6]],
    # Where Canadian protected-area mode opens — the suite's focus province.
    "BC": [[48.2, -139.1], [60.0, -114.0]],
}


__all__ = [
    "CLEAR_JS", "CLICK_BRIDGE_JS", "Coordinate", "DEFAULT_VIEW", "GeocodeError", "Place",
    "REGION_BOUNDS", "Resolution",
    "frame_js", "in_regions", "match_territories", "parse_coordinates",
    "resolve", "search_cep", "search_places", "search_postal",
]
