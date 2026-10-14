"""Event handlers for the "Find a place" box and the quick-start card.

The variables live on ``AppState`` (state/__init__.py), per this package's
convention; the resolving itself is ``utils/place_search.py``. A place, a
postal code or a coordinate frames the map in the browser and drops a pin
(``place_search.frame_js``) — nothing is selected. A territory match is
offered, and only choosing it runs the ordinary territory selection.
"""

from __future__ import annotations

import logging

import reflex as rx

from ..utils import address, place_search
from ..utils.place_search import GeocodeError

logger = logging.getLogger(__name__)


class PlaceSearchMixin(rx.State, mixin=True):
    """Event handlers for place search and the quick-start card."""

    # ---- helpers ---------------------------------------------------------

    def _territory_names(self) -> list:
        # Only where choosing one means something: the territory workspace.
        if getattr(self, "analysis_mode", "") == "geometry":
            return []
        return list(getattr(self, "available_territories", []) or [])

    def _echo_for(self, resolution) -> str:
        tr = self.tr
        kind, payload = resolution.kind, resolution.payload
        if kind == "cep":
            return f"{tr['ps_echo_cep']} {address.format_cep(payload)}"
        if kind == "postal":
            return f"{tr['ps_echo_postal']} {payload}"
        if kind == "coordenada":
            return f"{tr['ps_echo_coordinate']} {payload.lat:.4f}, {payload.lon:.4f}"
        if kind == "territorio":
            return f"{tr['ps_echo_territory']} {payload[0]}"
        if kind == "lugar":
            return f"{tr['ps_echo_place']} “{payload}”"
        return ""

    # ---- typing ----------------------------------------------------------

    def set_place_query(self, value: str):
        """Live "read as" line — a regex and a list scan, never a request."""
        self.place_query = value
        self.place_error = ""
        if not value.strip():
            self.place_echo = ""
            self.place_echo_kind = ""
            return
        try:
            r = place_search.resolve(value, self._territory_names())
            self.place_echo = self._echo_for(r)
            self.place_echo_kind = r.kind
        except ValueError as exc:
            self.place_echo = ""
            self.place_echo_kind = "erro"
            self.place_error = str(exc)

    # ---- submitting --------------------------------------------------------

    @rx.event(background=True)
    async def submit_place_search(self):
        async with self:
            raw = self.place_query.strip()
            self.place_error = ""
            self.place_hits = []
            self.place_territory_hits = []
            names = self._territory_names()
            if not raw:
                return
        try:
            r = place_search.resolve(raw, names)
        except ValueError as exc:
            async with self:
                self.place_error = str(exc)
            return

        if r.kind == "coordenada":
            c = r.payload
            async with self:
                self.place_echo = self._echo_for(r)
                self.place_echo_kind = "coordenada"
            return rx.call_script(place_search.frame_js(
                pin=[c.lat, c.lon], zoom=address.ZOOM_BY_PRECISION["endereco"] - 2))

        if r.kind == "territorio":
            async with self:
                self.place_territory_hits = r.territories
            return

        async with self:
            self.place_searching = True
            lang_tr = self.tr
        try:
            if r.kind == "cep":
                places = place_search.search_cep(r.payload)
            elif r.kind == "postal":
                places = place_search.search_postal(r.payload)
            else:
                places = place_search.search_places(raw, limit=6)
        except GeocodeError as exc:
            async with self:
                self.place_searching = False
                self.place_error = str(exc)
            return

        async with self:
            self.place_searching = False
            self.place_hits = [p.to_hit() for p in places]
            if not places:
                self.place_error = lang_tr["ps_not_found"].format(query=raw)
        if len(places) == 1:
            return self.__class__.choose_place(0)

    # ---- acting on a result ------------------------------------------------

    def choose_place(self, index: int):
        """Frame the map on a geocoded place and pin it. Selects nothing."""
        try:
            place = self.place_hits[int(index)]
        except (IndexError, ValueError, TypeError):
            return
        precision = place.get("precision", "lugar")
        pin = [place["lat"], place["lon"]]
        title = place.get("title") or place["label"]
        subtitle = place.get("subtitle") or ""
        self.place_query = f"{title}, {subtitle}" if subtitle else title
        self.place_echo = f"{self.tr['ps_echo_place']} — {self.tr['ps_place_hint']}"
        self.place_echo_kind = "lugar"
        if place.get("bounds") and precision not in address.POINT_PRECISIONS:
            return rx.call_script(place_search.frame_js(bounds=place["bounds"], pin=pin))
        return rx.call_script(place_search.frame_js(
            pin=pin, zoom=address.ZOOM_BY_PRECISION.get(precision, 14)))

    def choose_place_territory(self, name: str):
        """Hand a territory match to the ordinary selection, which loads its
        boundary and frames the map on it."""
        self.place_territory_hits = []
        self.place_query = name
        return self.__class__.set_selected_territory(name)

    def clear_place_search(self):
        self.place_query = ""
        self.place_echo = ""
        self.place_echo_kind = ""
        self.place_error = ""
        self.place_hits = []
        self.place_territory_hits = []
        return rx.call_script(place_search.CLEAR_JS)

    # ---- quick start + how-to ---------------------------------------------

    def set_howto_open(self, value: bool):
        self.howto_open = value

    def dismiss_quickstart(self):
        self.quickstart_seen = "1"

    def open_full_howto(self):
        """The quick-start card's last line: hand over to the full guide."""
        self.quickstart_seen = "1"
        self.howto_open = True

    def reset_quickstart(self):
        self.quickstart_seen = ""
        self.howto_open = False
