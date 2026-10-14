"""Choosing what to analyse on the Canada page: a protected area.

Replaces camposcope's ``_parcel.py`` (BC parcel fabric → WDPA park → square).
Yvynation's Canada page analyses **protected and conserved areas from CPCAD**
(``utils/conservation_service.py::ProvincialProtectedAreaService``), so there
is one kind of subject, chosen four ways:

* by name — the search box matches CPCAD names in the provinces shown;
* by clicking the map — the smallest loaded area containing the click; when
  areas overlap, the user chooses (smallest first, never decided silently);
* by place — an address, postal code or coordinate frames the map and pins it
  (selects nothing) — the same rule as every page in the suite;
* by deep link — ``/canada?area=<name>``.

**BC first, other provinces on demand.** ``ca_provinces`` is this session's
view; a click, a search or the picker adds a province (the files load once
per server process — the service is shared, the view is not).

**Parts.** One CPCAD record is often many separate polygons (Muskwa-Kechika
Special Wildland Areas: 39). Parts can be ticked or clicked on the map and
analysed alone; the selection becomes the analysed geometry.

The downstream contract is camposcope's, unchanged — ``parcel`` (always kind
``"park"`` here), ``parcel_geojson``, ``zones`` and ``active_zone`` — so every
analysis mixin and results component ported from camposcope works as is.

**OCAP.** Indigenous-governed and Indigenous-owned areas are not in the data
at all (``utils/build_ca_protected_areas.py``); ``disclosure`` says so.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import reflex as rx

from ...utils import address, place_search
from ...utils.place_search import GeocodeError
from .._shared.proxy import plain  # noqa: F401  (re-exported for sibling mixins)
from ..services.zones import build_zones, centroid_lat_lon
from ..translations import get_translations

logger = logging.getLogger(__name__)

#: How many parts the sidebar lists (largest first); any part can still be
#: picked on the map.
PART_LIST_LIMIT = 300

_NUDGE = "window.__caSheetNudgeOpen && window.__caSheetNudgeOpen()"


def ca_service():
    """The shared CPCAD service (one per server process)."""
    from ...utils.conservation_service import get_ca_protected_area_service
    return get_ca_protected_area_service()


def _in_canada(lat: float, lon: float) -> bool:
    w, s, e, n = place_search.CANADA_BBOX
    return s <= lat <= n and w <= lon <= e


class CanadaAreaMixin(rx.State, mixin=True):
    """Search box, selection, parts and provinces."""

    # --- search box --------------------------------------------------------
    query: str = ""
    echo: str = ""
    echo_kind: str = ""
    search_error: str = ""
    searching: bool = False
    searching_place: bool = False
    #: CPCAD names matching the query (display keys).
    area_hits: List[str] = []
    place_hits: List[Dict[str, Any]] = []
    search_pin: List[float] = []

    #: Overlapping areas under a click, smallest first — offered, not chosen.
    candidates: List[Dict[str, Any]] = []

    # --- the selected area -------------------------------------------------
    area_key: str = ""
    parcel: Dict[str, Any] = {}
    parcel_geojson: Dict[str, Any] = {}
    parcel_error: str = ""

    # --- zones ---------------------------------------------------------------
    ring_radii_m: List[int] = [500, 2000, 5000]
    zones: List[Dict[str, Any]] = []
    zones_geojson: Dict[str, Any] = {}
    area_registered_ha: float = 0.0
    area_calculated_ha: float = 0.0
    area_delta_ha: float = 0.0
    area_delta_pct: float = 0.0
    area_flagged: bool = False
    overlaps: List[Dict[str, Any]] = []
    active_zone: str = "parcela"
    zones_error: str = ""

    # --- provinces and parts --------------------------------------------------
    ca_provinces: List[str] = ["BC"]
    ca_parts: List[Dict[str, Any]] = []
    ca_parts_total: int = 0
    ca_part_pick: List[str] = []
    ca_parts_applied: List[str] = []

    # ------------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------------
    @rx.var
    def has_parcel(self) -> bool:
        """Whether an area is selected (name kept from camposcope: every
        results tab, layer and export gates on it)."""
        return bool(self.parcel.get("identifier"))

    @rx.var
    def has_results(self) -> bool:
        return bool(self.area_hits or self.place_hits or self.candidates)

    @rx.var
    def zone_count(self) -> int:
        return len(self.zones)

    @rx.var
    def map_overlays(self) -> Dict[str, Any]:
        base = self.zones_geojson or {"type": "FeatureCollection", "features": []}
        if len(self.search_pin) != 2:
            return base
        lat, lon = self.search_pin
        return {
            "type": "FeatureCollection",
            "features": list(base.get("features") or []) + [{
                "type": "Feature",
                "properties": {"role": "search_pin"},
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
            }],
        }

    @rx.var
    def cpcad_vectors(self) -> List[Dict[str, Any]]:
        """Every shown province's protected-area outlines, fetched by the
        browser from ``/_cpcad/<PROV>.geojson`` (canada/api.py) — clickable,
        named on hover."""
        lang = getattr(self, "language", "en")
        name_lbl = {"pt": "Área protegida", "fr": "Aire protégée"}.get(lang, "Protected area")
        type_lbl = {"pt": "Designação", "fr": "Désignation"}.get(lang, "Designation")
        return [{
            "id": f"cpcad:{prov}",
            "path": f"/_cpcad/{prov}.geojson",
            "opacity": 0.12,
            "z_index": 6,
            "weight": 1.2,
            "default_color": "0f766e",
            "attribution": "CPCAD © ECCC (OGL-Canada)",
            "tooltip": [{"label": name_lbl, "property": "nome_uc"},
                        {"label": type_lbl, "property": "categoria"}],
        } for prov in self.ca_provinces]

    @rx.var
    def place_attribution(self) -> str:
        return address.attributions(self.place_hits)

    @rx.var(cache=True, deps=["language"], auto_deps=False)
    def disclosure(self) -> str:
        return get_translations(getattr(self, "language", "en"))["area_disclosure"]

    @rx.var
    def ca_parts_status(self) -> str:
        tr = get_translations(getattr(self, "language", "en"))
        n, total = len(self.ca_parts_applied), self.ca_parts_total
        if not n:
            return tr["ca_parts_analysing_all"].format(total=total)
        return tr["ca_parts_analysing_some"].format(n=n, total=total)

    @rx.var
    def ca_parts_more_note(self) -> str:
        if self.ca_parts_total <= len(self.ca_parts):
            return ""
        tr = get_translations(getattr(self, "language", "en"))
        return tr["ca_parts_more"].format(n=len(self.ca_parts), total=self.ca_parts_total)

    @rx.var
    def ca_part_pick_count(self) -> int:
        return len(self.ca_part_pick)

    # ------------------------------------------------------------------------
    # Typing and searching
    # ------------------------------------------------------------------------
    def _names(self) -> List[str]:
        return ca_service().get_all_display_keys(provinces=list(self.ca_provinces))

    def _tr(self) -> Dict[str, str]:
        return get_translations(getattr(self, "language", "en"))

    def _echo_for(self, r) -> str:
        tr = self._tr()
        if r.kind == "postal":
            return f"{tr['echo_postal']} {r.payload}"
        if r.kind == "coordenada":
            return f"{tr['echo_coordenada']} {r.payload.lat:.4f}, {r.payload.lon:.4f}"
        if r.kind == "territorio":
            return f"{tr['echo_area_cpcad']} {r.payload[0]}"
        return f"{tr['echo_lugar']} “{r.payload}”"

    def set_query(self, value: str) -> None:
        """Live "read as" line — a regex and a name scan, no request."""
        self.query = value
        self.search_error = ""
        if not value.strip():
            self.echo = ""
            self.echo_kind = ""
            return
        try:
            r = place_search.resolve(value, self._names())
            if r.kind == "cep":          # a Brazilian postcode means nothing here
                r = place_search.Resolution("lugar", value.strip())
            self.echo = self._echo_for(r)
            self.echo_kind = r.kind
        except ValueError as exc:
            self.echo = ""
            self.echo_kind = "erro"
            self.search_error = str(exc)

    @rx.event(background=True)
    async def submit_search(self):
        async with self:
            raw = self.query.strip()
            self.search_error = ""
            self.area_hits = []
            self.place_hits = []
            names = self._names()
            tr = self._tr()
            if not raw:
                return
        try:
            r = place_search.resolve(raw, names)
        except ValueError as exc:
            async with self:
                self.search_error = str(exc)
            return

        if r.kind == "coordenada":
            c = r.payload
            if not _in_canada(c.lat, c.lon):
                async with self:
                    self.search_error = tr["erro_fora_canada"]
                return
            return self.__class__.select_at_point(c.lat, c.lon)

        if r.kind == "territorio":
            async with self:
                self.area_hits = r.territories
            if len(r.territories) == 1:
                return self.__class__.choose_area(r.territories[0])
            return

        async with self:
            self.searching_place = True
        try:
            if r.kind == "postal":
                places = place_search.search_postal(r.payload)
            else:
                places = [p for p in place_search.search_places(raw, limit=8)
                          if _in_canada(p.lat, p.lon)][:6]
        except GeocodeError as exc:
            async with self:
                self.searching_place = False
                self.search_error = str(exc)
            return
        async with self:
            self.searching_place = False
            self.place_hits = [p.to_hit() for p in places]
            if not places:
                self.search_error = tr["erro_lugar_nao_encontrado"].format(query=raw)
        if len(places) == 1:
            return self.__class__.choose_place(0)

    def choose_place(self, index: int):
        """Frame the map on a geocoded place and pin it. **Selects nothing**
        — but loads the place's province if this session does not show it."""
        try:
            place = self.place_hits[int(index)]
        except (IndexError, ValueError, TypeError):
            return
        precision = place.get("precision", "lugar")
        lat, lon = place["lat"], place["lon"]
        if place.get("bounds") and precision not in address.POINT_PRECISIONS:
            self.fit_bounds = place["bounds"]
        else:
            self.center = [lat, lon]
            self.zoom = address.ZOOM_BY_PRECISION.get(precision, 14)
        self.search_pin = [lat, lon]
        title = place.get("title") or place["label"]
        sub = place.get("subtitle") or ""
        self.query = f"{title}, {sub}" if sub else title
        tr = self._tr()
        self.echo = f"{tr['echo_lugar']} — {tr['search_place_hint']}"
        self.echo_kind = "lugar"
        code = ca_service().province_at(lat, lon)
        if code and code not in self.ca_provinces:
            return self.__class__.add_ca_province(code)

    def clear_search(self) -> None:
        self.query = ""
        self.echo = ""
        self.echo_kind = ""
        self.search_error = ""
        self.area_hits = []
        self.place_hits = []
        self.search_pin = []

    # ------------------------------------------------------------------------
    # Selecting
    # ------------------------------------------------------------------------
    @rx.event(background=True)
    async def choose_area(self, key: str):
        """Select a protected area by display key (list, search, overlap
        chooser, deep link)."""
        async with self:
            self.area_hits = []
            self.candidates = []
            self.ca_parts_applied = []
            self.ca_part_pick = []
            self.searching = True
        loaded = await self._load_area(key, None, None)
        async with self:
            self.searching = False
        if loaded:
            return [self.__class__.run_aci_history, self.__class__.run_vlce2_history,
                    self.__class__.mint_analysis_layer, rx.call_script(_NUDGE)]

    @rx.event(background=True)
    async def select_at_point(self, lat: float, lon: float):
        """A map click (or a typed coordinate).

        1. Inside the selected multi-part area → toggle that part.
        2. In a province not shown yet → load it.
        3. The protected areas under the click: one → select it; several →
           offer them, smallest first; none → say so.
        """
        import asyncio

        async with self:
            self.parcel_error = ""
            self.candidates = []
            key = self.area_key
            parts_total = self.ca_parts_total
            provinces = list(self.ca_provinces)
            tr = self._tr()

        svc = ca_service()
        loop = asyncio.get_running_loop()

        if key and parts_total > 1:
            pid = await loop.run_in_executor(None, lambda: svc.part_at(key, lat, lon))
            if pid is not None:
                return self.__class__.toggle_ca_part(pid)

        code = svc.province_at(lat, lon)
        if code is None:
            async with self:
                self.parcel_error = tr["erro_fora_canada"]
            return
        if code not in provinces:
            provinces.append(code)
            await loop.run_in_executor(None, lambda: svc.ensure_provinces(provinces))
            async with self:
                self.ca_provinces = provinces

        hits = await loop.run_in_executor(None, lambda: svc.areas_at(lat, lon, provinces))
        if not hits:
            async with self:
                self.parcel_error = tr["erro_sem_area"]
            return
        if len(hits) > 1:
            async with self:
                self.candidates = [self._candidate_row(k) for k in hits[:12]]
            return
        async with self:
            self.searching = True
            self.ca_parts_applied = []
            self.ca_part_pick = []
        loaded = await self._load_area(hits[0], lat, lon)
        async with self:
            self.searching = False
        if loaded:
            return [self.__class__.run_aci_history, self.__class__.run_vlce2_history,
                    self.__class__.mint_analysis_layer, rx.call_script(_NUDGE)]

    @staticmethod
    def _candidate_row(key: str) -> Dict[str, Any]:
        info = ca_service().get_territory_info(key)
        return {"key": key, "name": info.get("nome_uc", key),
                "designation": info.get("categoria", ""),
                "area_ha": round(float(info.get("superficie_ha") or 0), 1)}

    @rx.event(background=True)
    async def choose_candidate(self, key: str):
        async with self:
            self.candidates = []
            self.ca_parts_applied = []
            self.ca_part_pick = []
            self.searching = True
        loaded = await self._load_area(key, None, None)
        async with self:
            self.searching = False
        if loaded:
            return [self.__class__.run_aci_history, self.__class__.run_vlce2_history,
                    self.__class__.mint_analysis_layer, rx.call_script(_NUDGE)]

    async def _load_area(self, key: str, lat, lon) -> bool:
        """Fetch geometry + parts off the event loop, then adopt under lock.
        Honours ``ca_parts_applied`` (read under lock first)."""
        import asyncio

        async with self:
            applied = list(self.ca_parts_applied)
            tr = self._tr()
        svc = ca_service()

        def _fetch():
            info = svc.get_territory_info(key)
            parts = svc.get_parts(key)
            if applied:
                geom = svc.get_parts_geojson(key, applied)
                chosen = {p["id"]: p for p in parts}
                ha = sum(chosen[i]["ha"] for i in applied if i in chosen)
            else:
                geom = svc.get_geojson_for_key(key)
                ha = float(info.get("superficie_ha") or 0)
            row = svc._get_row(key)
            extra = {} if row is None else {
                c: (row.get(c) if row.get(c) == row.get(c) else "")
                for c in ("iucn_cat", "status", "est_year", "owner_type", "owner",
                          "name_fr", "name_ind", "mechanism", "provider", "org_gestor")}
            return info, parts, geom, ha, extra

        try:
            info, parts, geom, ha, extra = await asyncio.get_running_loop().run_in_executor(None, _fetch)
        except Exception as exc:                       # noqa: BLE001
            logger.exception("CPCAD area load failed")
            async with self:
                self.parcel_error = str(exc)
            return False
        if not geom:
            async with self:
                self.parcel_error = tr["erro_sem_area"]
            return False

        async with self:
            self._adopt_cpcad(key, info, extra, geom, ha, parts, applied, lat, lon)
        return True

    def _adopt_cpcad(self, key, info, extra, geom, ha, parts, applied, lat, lon) -> None:
        self._clear_analysis_results()
        self.area_key = key
        name = info.get("nome_uc", key)
        identifier = (f"{name} · {len(applied)}/{len(parts)}" if applied else name)
        self.parcel = self._base_dict("park", identifier, ha, "")
        self.parcel.update({
            "designation": info.get("categoria", ""),
            "designation_type": info.get("grupo", ""),
            "iucn_category": str(extra.get("iucn_cat") or ""),
            "park_status": str(extra.get("status") or ""),
            "status_year": int(extra.get("est_year") or 0),
            "managing_authority": str(extra.get("org_gestor") or ""),
            "governance": info.get("esfera", ""),
            "owner_type": str(extra.get("owner_type") or ""),
            "owner": str(extra.get("owner") or ""),
            "name_fr": str(extra.get("name_fr") or ""),
            "name_ind": str(extra.get("name_ind") or ""),
            "province": info.get("uf_sigla", ""),
            # The Forest tab splits Hansen loss at "start_year": for a protected
            # area that is its establishment year — before vs after protection.
            "start_year": int(extra.get("est_year") or 0),
            "cpcad_id": info.get("cd_cnuc", ""),
            "area_name": name,
        })
        self.parcel_geojson = geom
        self.ca_parts_total = len(parts)
        self.ca_parts = ([{**p, "label": f"#{p['rank']} · {p['ha']:,.0f} ha"}
                          for p in parts[:PART_LIST_LIMIT]] if len(parts) > 1 else [])
        self._reference_point(geom, lat, lon)
        self.build_zones()
        self.frame_geometry(geom)
        self.active_zone = "parcela"
        self.query = name
        self.echo = ""
        self.echo_kind = ""

    def adopt_area_param(self):
        """Honour ``/canada?area=<display key>`` (a shareable selection)."""
        key = self.router.url.query_parameters.get("area", "")
        if key:
            return self.__class__.choose_area(key)

    # ------------------------------------------------------------------------
    # Parts
    # ------------------------------------------------------------------------
    def toggle_ca_part(self, part_id: str):
        pick = list(self.ca_part_pick)
        if part_id in pick:
            pick.remove(part_id)
        else:
            pick.append(part_id)
        self.ca_part_pick = pick

    def clear_ca_part_pick(self):
        self.ca_part_pick = []

    def apply_ca_parts(self):
        """Analyse only the ticked parts."""
        if not self.ca_part_pick or not self.area_key:
            return
        self.ca_parts_applied = sorted(self.ca_part_pick, key=int)
        return self.__class__.reload_area

    def analyse_all_ca_parts(self):
        if not self.area_key or not self.ca_parts_applied:
            return
        self.ca_parts_applied = []
        self.ca_part_pick = []
        return self.__class__.reload_area

    @rx.event(background=True)
    async def reload_area(self):
        async with self:
            key = self.area_key
            self.searching = True
        loaded = await self._load_area(key, None, None) if key else False
        async with self:
            self.searching = False
        if loaded:
            return [self.__class__.run_aci_history, self.__class__.run_vlce2_history, self.__class__.mint_analysis_layer]

    def zoom_to_ca_part(self, part_id: str):
        for p in self.ca_parts:
            if p.get("id") == part_id:
                self.fit_bounds = p["bounds"]
                return

    # ------------------------------------------------------------------------
    # Provinces
    # ------------------------------------------------------------------------
    @rx.event(background=True)
    async def add_ca_province(self, code: str):
        import asyncio
        async with self:
            if code in self.ca_provinces:
                return
            provinces = list(self.ca_provinces) + [code]
        svc = ca_service()
        if code not in svc.available_provinces():
            return
        await asyncio.get_running_loop().run_in_executor(
            None, lambda: svc.ensure_provinces(provinces))
        async with self:
            self.ca_provinces = provinces

    # ------------------------------------------------------------------------
    # Ported unchanged from camposcope's _parcel.py
    # ------------------------------------------------------------------------
    @staticmethod
    def _base_dict(kind: str, identifier: str, area_ha: float,
                   queried_at: str) -> Dict[str, Any]:
        return {
            "kind": kind,
            "identifier": identifier,
            "area_registered_ha": round(area_ha, 4),
            "queried_at": queried_at,
            "fabric_id": 0, "pid": "", "pid_formatted": "", "parcel_name": "",
            "plan_number": "", "parcel_status": "", "parcel_class": "",
            "owner_type": "", "parcel_start_date": "", "start_year": 0,
            "municipality": "", "regional_district": "", "when_updated": "",
            "is_non_land": False,
            "wdpa_id": 0, "designation": "", "designation_type": "",
            "iucn_category": "", "park_status": "", "status_year": 0,
            "managing_authority": "",
            "governance": "", "owner": "", "name_fr": "", "name_ind": "",
            "province": "", "cpcad_id": "", "area_name": "",
            "click_lat": 0.0, "click_lon": 0.0,
            "centroid_lat": 0.0, "centroid_lon": 0.0,
        }

    def _reference_point(self, geojson: Dict[str, Any], lat, lon) -> None:
        centroid_lat, centroid_lon = centroid_lat_lon(geojson)
        self.parcel["centroid_lat"] = round(centroid_lat, 5)
        self.parcel["centroid_lon"] = round(centroid_lon, 5)
        if lat is not None and lon is not None:
            self.parcel["click_lat"] = round(lat, 5)
            self.parcel["click_lon"] = round(lon, 5)

    def _clear_analysis_results(self) -> None:
        """Wipe every opt-in tab's output before a new area is adopted —
        otherwise the previous area's numbers stay on screen, unlabelled as
        stale (camposcope's _parcel.py has the bug report behind this)."""
        for prefix, fields in (
            ("fire", ("rows", "table_rows")), ("biomass", ("rows",)),
            ("age", ("rows",)), ("landscape", ("rows",)),
            ("connectivity", ("rows",)), ("validation", ("summary", "matrix")),
        ):
            setattr(self, f"{prefix}_running", False)
            setattr(self, f"{prefix}_error", "")
            for f in fields:
                setattr(self, f"{prefix}_{f}", [])
            setattr(self, f"{prefix}_provenance", {})
        self.connectivity_degraded = False
        self.age_has_run = False
        self.hansen_running = False
        self.hansen_error = ""
        self.hansen_loss_rows = []
        self.hansen_gain_ha = 0.0
        self.hansen_has_run = False
        self.hansen_split_year = 0
        self.hansen_provenance = {}
        self.sankey_running = False
        self.sankey_error = ""
        self.sankey_transitions = {}
        self.sankey_provenance = {}
        self.sankey_zone_label = ""

    def build_zones(self) -> None:
        geojson = getattr(self, "parcel_geojson", None)
        lang = getattr(self, "language", "en")
        if not geojson:
            self.zones = []
            self.zones_geojson = {}
            self.overlaps = []
            return
        self.zones_error = ""
        try:
            built = build_zones(geojson,
                                radii_m=getattr(self, "ring_radii_m", [500, 2000, 5000]),
                                parcel_label=get_translations(lang)["zona_park"],
                                lang=lang)
        except Exception as exc:                       # noqa: BLE001
            logger.exception("zone construction failed")
            self.zones_error = get_translations(lang)["erro_zonas"].format(detail=exc)
            self.zones = []
            self.zones_geojson = {}
            return
        self.zones = [z.to_row() for z in built]
        self.zones_geojson = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "properties": {"role": "property" if z.kind == "property" else "ring",
                               "zone_key": z.key, "label": z.label,
                               "area_ha": round(z.area_ha, 2)},
                "geometry": z.geojson,
            } for z in built],
        }
        from ..services.zones import check_area
        declared = float(self.parcel.get("area_registered_ha", 0.0))
        check = check_area(declared, geojson)
        self.area_registered_ha = check.registered_ha
        self.area_calculated_ha = round(check.computed_ha, 4)
        self.area_delta_ha = round(check.delta_ha, 4)
        self.area_delta_pct = round(check.delta_pct, 3)
        self.area_flagged = check.flagged

    def set_active_zone(self, zone_key: str) -> None:
        self.active_zone = zone_key
