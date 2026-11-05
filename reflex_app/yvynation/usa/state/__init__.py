"""USA page state: choose a PAD-US protected area, build its zones, run the analyses.

``USState`` is its own root state (not a mixin of the Brazil ``AppState``), same reasoning
as the Canada page. Earth Engine objects never live in state: it holds GeoJSON dicts and
plain values, and services rebuild the Earth Engine objects.

Flow: search by name or click → (candidates, smallest first) → ``choose_unit`` → boundary
from the PAD-US service → zones (area + rings) → two background analyses, each with its
**own** error channel: NLCD land-cover history and Hansen forest change.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List

import plotly.graph_objects as go
import reflex as rx

from ...canada._shared.layers import basemap_spec
from ...canada._shared.proxy import plain
from ...canada._shared.zones import Zone
from ...canada._shared.datasets import BASEMAPS
from ...canada.services.fire import FIRE_YEAR_END
from ..components import charts
from ..config import nlcd
from ..config.settings import DEFAULT_LANGUAGE, MAP_CENTER, MAP_ZOOM, PADUS_TILES, USA_BBOX
from ..services import layers as layer_service
from ..services import padus
from ..services.zones import build_zones
from ..translations import get_translations

logger = logging.getLogger(__name__)

_COORD = re.compile(r"^\s*(-?\d{1,3}(?:\.\d+)?)\s*[,;\s]\s*(-?\d{1,3}(?:\.\d+)?)\s*$")


#: PAD-US public-access codes.
_ACCESS = {"OA": "Open", "RA": "Restricted", "XA": "Closed"}


def _in_usa(lat: float, lon: float) -> bool:
    w, s, e, n = USA_BBOX
    return s <= lat <= n and w <= lon <= e


class USState(rx.State):
    """Root state for the ``/usa`` route."""

    # --- chrome -----------------------------------------------------------
    language: str = DEFAULT_LANGUAGE
    help_open: bool = False
    results_tab: str = "cover"

    # --- search / selection ----------------------------------------------
    query: str = ""
    searching: bool = False
    search_error: str = ""
    hits: List[Dict[str, Any]] = []
    candidates: List[Dict[str, Any]] = []
    searched: bool = False

    # --- the selected area -------------------------------------------------
    unit: Dict[str, Any] = {}
    area_geojson: Dict[str, Any] = {}
    zones: List[Dict[str, Any]] = []
    zones_geojson: Dict[str, Any] = {}
    active_zone: str = "parcela"
    fit_bounds: List[List[float]] = []
    loading_area: bool = False

    # --- map ----------------------------------------------------------------
    center: List[float] = [MAP_CENTER[0], MAP_CENTER[1]]
    zoom: int = MAP_ZOOM
    basemap: str = "google_hybrid"
    show_nlcd: bool = False
    nlcd_year: int = nlcd.NLCD_YEAR_END
    nlcd_opacity: float = 0.75
    show_change: bool = False
    change_from_year: int = 2001
    _urls: Dict[str, Any] = {}
    map_layers: List[Dict[str, Any]] = []

    # --- analyses -----------------------------------------------------------
    cover_running: bool = False
    cover_error: str = ""
    cover_rows: List[Dict[str, Any]] = []
    cover_normalise: bool = False
    forest_running: bool = False
    forest_error: str = ""
    forest_rows: List[Dict[str, Any]] = []
    forest_gain_ha: float = 0.0
    biomass_running: bool = False
    biomass_error: str = ""
    biomass_rows: List[Dict[str, Any]] = []
    fire_running: bool = False
    fire_error: str = ""
    fire_rows: List[Dict[str, Any]] = []
    fire_summary: List[Dict[str, Any]] = []
    show_padus: bool = False

    # ----------------------------------------------------------------------- #
    # Derived
    # ----------------------------------------------------------------------- #
    @rx.var
    def tr(self) -> Dict[str, str]:
        return get_translations(self.language)

    @rx.var
    def has_unit(self) -> bool:
        return bool(self.unit)

    @rx.var
    def unit_rows(self) -> List[Dict[str, str]]:
        """The area card's attribute rows, already formatted."""
        u = self.unit
        if not u:
            return []
        t = self.tr
        zones = {z["zone_key"]: z for z in self.zones}
        computed = zones.get("parcela", {}).get("area_ha")
        rows = [
            (t["area_category"], u.get("category", "")),
            (t["area_designation"], u.get("des_label", "")),
            (t["area_manager"], u.get("manager", "")),
            (t["area_gap"], u.get("gap_status", "")),
            (t["area_iucn"], u.get("iucn", "")),
            (t["area_access"], _ACCESS.get(u.get("access", ""), "")),
            (t["area_state"], "" if u.get("state") == "Not Applicable" else u.get("state", "")),
            (t["area_size"], f"{u.get('ha', 0):,.0f} ha"),
            (t["area_computed"], f"{computed:,.0f} ha" if computed else "—"),
            (t["area_id"], f"{u.get('key', '')}" + (f" (+{u['pieces'] - 1})" if u.get("pieces", 1) > 1 else "")),
        ]
        return [{"label": a, "value": str(b)} for a, b in rows if str(b) not in ("", "Unassigned")]

    @rx.var
    def map_overlays(self) -> Dict[str, Any]:
        return self.zones_geojson or {"type": "FeatureCollection", "features": []}

    @rx.var
    def cover_rows_zone(self) -> List[Dict[str, Any]]:
        return [r for r in self.cover_rows if r["zone_key"] == self.active_zone]

    @rx.var
    def has_cover(self) -> bool:
        return bool(self.cover_rows)

    @rx.var
    def cover_figure(self) -> go.Figure:
        return charts.land_cover_figure(self.cover_rows_zone, lang=self.language,
                                        normalise=self.cover_normalise)

    @rx.var
    def cover_table(self) -> List[Dict[str, Any]]:
        key = "class_pt" if self.language == "pt" else "class_en"
        rows = [r for r in self.cover_rows_zone if r["year"] == self.nlcd_year]
        total = sum(r["area_ha"] for r in rows) or 1.0
        out = [{"name": r[key], "color": r["color"], "ha": f"{r['area_ha']:,.0f}",
                "pct": f"{100 * r['area_ha'] / total:.1f}", "_v": r["area_ha"]} for r in rows]
        out.sort(key=lambda r: -r["_v"])
        return out

    @rx.var
    def table_title(self) -> str:
        return self.tr["table_title"].format(year=self.nlcd_year)

    @rx.var
    def has_forest(self) -> bool:
        return bool(self.forest_rows)

    @rx.var
    def forest_figure(self) -> go.Figure:
        rows = [r for r in self.forest_rows if r["zone_key"] == self.active_zone]
        return charts.hansen_figure(rows, lang=self.language)

    @rx.var
    def has_biomass(self) -> bool:
        return bool(self.biomass_rows)

    @rx.var
    def biomass_figure(self) -> go.Figure:
        rows = [r for r in self.biomass_rows if r["zone_key"] == self.active_zone]
        return charts.biomass_figure(rows, lang=self.language)

    @rx.var
    def has_fire(self) -> bool:
        return bool(self.fire_rows)

    @rx.var
    def fire_figure(self) -> go.Figure:
        rows = [r for r in self.fire_rows if r["zone_key"] == self.active_zone]
        return charts.fire_figure(rows, lang=self.language, current_year=FIRE_YEAR_END)

    @rx.var
    def fire_stats(self) -> List[Dict[str, str]]:
        """Headline numbers for the active zone."""
        row = next((r for r in self.fire_summary if r["zone_key"] == self.active_zone), None)
        if not row:
            return []
        t = self.tr
        last = row.get("fire_last_year")
        out = [{"label": t["fire_history"], "value": f"{row['fire_history_pct']:.0f}%"},
               {"label": t["fire_frequency"], "value": f"{row['fire_frequency']:.2f}"},
               {"label": t["fire_last"], "value": str(last) if last else "—"}]
        if row.get("below_resolution"):
            out.append({"label": "", "value": t["fire_small"]})
        return out

    @rx.var
    def years(self) -> List[str]:
        return [str(y) for y in nlcd.NLCD_YEARS]

    @rx.var
    def basemap_options(self) -> List[str]:
        col = "label_pt" if self.language == "pt" else "label_en"
        return [v[col] for v in BASEMAPS.values()]

    @rx.var
    def basemap_label(self) -> str:
        col = "label_pt" if self.language == "pt" else "label_en"
        return BASEMAPS[self.basemap][col]

    # ----------------------------------------------------------------------- #
    # Chrome
    # ----------------------------------------------------------------------- #
    def set_language(self, lang: str | list[str]):
        raw = lang[0] if isinstance(lang, (list, tuple)) and lang else lang
        if raw in ("en", "pt"):
            self.language = raw
            self._rebuild_zone_labels()

    def adopt_on_load(self):
        self._refresh_layers()          # the base map must be there before any selection
        q = self.router.url.query_parameters or {}
        if q.get("lang") in ("en", "pt"):
            self.language = q["lang"]
        key = q.get("area")
        if key and ":" in str(key):
            return USState.choose_unit(str(key))

    def set_help_open(self, value: bool):
        self.help_open = value

    def set_results_tab(self, tab: str):
        self.results_tab = tab

    @rx.var
    def brazil_href(self) -> str:
        return f"/?lang={self.language}"

    @rx.var
    def canada_href(self) -> str:
        return f"/canada?lang={self.language}"

    # ----------------------------------------------------------------------- #
    # Search and selection
    # ----------------------------------------------------------------------- #
    def set_query(self, value: str):
        self.query = value

    def search_key(self, key: str):
        if key == "Enter":
            return USState.submit_search

    @rx.event(background=True)
    async def submit_search(self):
        async with self:
            text = self.query.strip()
            self.search_error = ""
            self.candidates = []
            if not text:
                return
            m = _COORD.match(text)
            if m:
                lat, lon = float(m.group(1)), float(m.group(2))
                self.searching = True
            else:
                self.searching = True
        if m:
            return USState.select_at_point(lat, lon)
        try:
            units = await asyncio.get_running_loop().run_in_executor(None, padus.search, text)
        except padus.PadusError as exc:
            async with self:
                self.searching = False
                self.search_error = self.tr["service_error"].format(detail=exc)
            return
        async with self:
            self.searching = False
            self.searched = True
            self.hits = [u.as_dict() for u in units]

    @rx.event(background=True)
    async def select_at_point(self, lat: float, lon: float):
        async with self:
            if not _in_usa(lat, lon):
                self.search_error = self.tr["click_outside"]
                self.searching = False
                return
            self.search_error = ""
            self.searching = True
            self.hits = []
        try:
            units = await asyncio.get_running_loop().run_in_executor(None, padus.at_point, lat, lon)
        except padus.PadusError as exc:
            async with self:
                self.searching = False
                self.search_error = self.tr["service_error"].format(detail=exc)
            return
        async with self:
            self.searching = False
            if not units:
                self.candidates = []
                self.search_error = self.tr["no_area_here"]
                return
            if len(units) == 1:
                self.candidates = []
            else:
                self.candidates = [u.as_dict() for u in units]
                return
        return USState.choose_unit(units[0].key)

    @rx.event(background=True)
    async def choose_unit(self, key: str):
        async with self:
            self.loading_area = True
            self.candidates = []
            self.hits = []
            self.search_error = ""
        loop = asyncio.get_running_loop()
        try:
            unit = await loop.run_in_executor(None, padus.get_unit, key)
            geom = await loop.run_in_executor(None, padus.geometry, key) if unit else None
        except padus.PadusError as exc:
            async with self:
                self.loading_area = False
                self.search_error = self.tr["service_error"].format(detail=exc)
            return
        if not unit or not geom:
            async with self:
                self.loading_area = False
                self.search_error = self.tr["no_area_here"]
            return
        async with self:
            self.loading_area = False
            self.unit = unit.as_dict()
            self.query = unit.name
            self.area_geojson = geom
            self.active_zone = "parcela"
            self.cover_rows, self.forest_rows = [], []
            self.biomass_rows, self.fire_rows, self.fire_summary = [], [], []
            self.cover_error = self.forest_error = self.biomass_error = self.fire_error = ""
            self._build_zones()
            self._frame(geom)
            self._refresh_layers()
        return [USState.run_cover, USState.run_forest, USState.run_biomass, USState.run_fire]

    def clear_area(self):
        self.unit, self.area_geojson, self.zones, self.zones_geojson = {}, {}, [], {}
        self.cover_rows, self.forest_rows = [], []
        self.biomass_rows, self.fire_rows, self.fire_summary = [], [], []

    # ----------------------------------------------------------------------- #
    # Zones
    # ----------------------------------------------------------------------- #
    def _build_zones(self) -> None:
        if not self.area_geojson:
            self.zones, self.zones_geojson = [], {}
            return
        try:
            built = build_zones(plain(self.area_geojson), radii_m=[500, 2000, 5000],
                                parcel_label=self.tr["zone_area"], lang=self.language)
        except Exception as exc:                          # noqa: BLE001
            logger.exception("zone construction failed")
            self.search_error = str(exc)
            self.zones, self.zones_geojson = [], {}
            return
        self.zones = [z.to_row() for z in built]
        self.zones_geojson = {"type": "FeatureCollection", "features": [{
            "type": "Feature",
            "properties": {"role": "property" if z.kind == "property" else "ring",
                           "zone_key": z.key, "label": z.label, "area_ha": round(z.area_ha, 2)},
            "geometry": z.geojson} for z in built]}

    def _rebuild_zone_labels(self) -> None:
        if self.area_geojson:
            self._build_zones()

    def _frame(self, geom: Dict[str, Any]) -> None:
        from shapely.geometry import shape
        w, s, e, n = shape(plain(geom)).bounds
        pad_x, pad_y = (e - w) * 0.5, (n - s) * 0.5
        self.fit_bounds = [[s - pad_y, w - pad_x], [n + pad_y, e + pad_x]]

    def set_active_zone(self, key: str):
        self.active_zone = key

    def _zone_objects(self) -> List[Zone]:
        by_key = {f["properties"]["zone_key"]: f["geometry"]
                  for f in plain(self.zones_geojson).get("features", [])}
        return [Zone(key=z["zone_key"], label=z["zone_label"], kind=z["zone_kind"],
                     geojson=by_key[z["zone_key"]], area_ha=z["area_ha"], radius_m=z.get("radius_m"))
                for z in plain(self.zones) if z["zone_key"] in by_key]

    # ----------------------------------------------------------------------- #
    # Analyses
    # ----------------------------------------------------------------------- #
    @rx.event(background=True)
    async def run_cover(self):
        from ..services.nlcd_history import land_cover_history
        async with self:
            zones = self._zone_objects()
            self.cover_running, self.cover_error, self.cover_rows = True, "", []
        if not zones:
            async with self:
                self.cover_running = False
            return
        try:
            df, _prov = await asyncio.get_running_loop().run_in_executor(None, land_cover_history, zones)
        except Exception as exc:                          # noqa: BLE001
            logger.exception("NLCD history failed")
            async with self:
                self.cover_running = False
                self.cover_error = self.tr["cover_error"].format(detail=exc)
            return
        async with self:
            self.cover_running = False
            self.cover_rows = df.to_dict("records")

    @rx.event(background=True)
    async def run_forest(self):
        from ...canada.services.hansen import forest_change
        async with self:
            zones = self._zone_objects()
            self.forest_running, self.forest_error, self.forest_rows = True, "", []
        if not zones:
            async with self:
                self.forest_running = False
            return
        try:
            loss, gain, _prov = await asyncio.get_running_loop().run_in_executor(
                None, lambda: forest_change(zones, parcel_year=None))
        except Exception as exc:                          # noqa: BLE001
            logger.exception("Hansen failed")
            async with self:
                self.forest_running = False
                self.forest_error = self.tr["forest_error"].format(detail=exc)
            return
        async with self:
            self.forest_running = False
            self.forest_rows = loss.to_dict("records")
            self.forest_gain_ha = round(float(gain), 1)

    @rx.event(background=True)
    async def run_biomass(self):
        from ...canada.services.biomass import above_ground_biomass
        async with self:
            zones = self._zone_objects()
            self.biomass_running, self.biomass_error, self.biomass_rows = True, "", []
        if not zones:
            async with self:
                self.biomass_running = False
            return
        try:
            df, _prov = await asyncio.get_running_loop().run_in_executor(None, above_ground_biomass, zones)
        except Exception as exc:                          # noqa: BLE001
            logger.exception("Biomass failed")
            async with self:
                self.biomass_running = False
                self.biomass_error = self.tr["biomass_error"].format(detail=exc)
            return
        async with self:
            self.biomass_running = False
            self.biomass_rows = df.to_dict("records") if not df.empty else []

    @rx.event(background=True)
    async def run_fire(self):
        from ...canada.services.fire import fire_analysis
        async with self:
            zones = self._zone_objects()
            self.fire_running, self.fire_error, self.fire_rows, self.fire_summary = True, "", [], []
        if not zones:
            async with self:
                self.fire_running = False
            return
        try:
            summary, annual, _prov = await asyncio.get_running_loop().run_in_executor(None, fire_analysis, zones)
        except Exception as exc:                          # noqa: BLE001
            logger.exception("Fire failed")
            async with self:
                self.fire_running = False
                self.fire_error = self.tr["fire_error"].format(detail=exc)
            return
        async with self:
            self.fire_running = False
            self.fire_rows = annual.to_dict("records") if not annual.empty else []
            self.fire_summary = summary.to_dict("records") if not summary.empty else []

    def toggle_normalise(self):
        self.cover_normalise = not self.cover_normalise

    # ----------------------------------------------------------------------- #
    # Layers
    # ----------------------------------------------------------------------- #
    def _refresh_layers(self) -> None:
        specs = []
        base = basemap_spec(self.basemap, z_index=0)
        if base:
            specs.append(base)
        if self.show_nlcd and f"us:nlcd:{self.nlcd_year}" in self._urls:
            s = dict(self._urls[f"us:nlcd:{self.nlcd_year}"]); s["opacity"] = self.nlcd_opacity
            specs.append(s)
        if self.show_padus:
            specs.append({"id": "padus:tiles", "url": PADUS_TILES, "opacity": 0.55, "z_index": 5,
                          "attribution": "PAD-US 3.0 — USGS Gap Analysis Project",
                          "max_native_zoom": 14})
        key = f"us:change:{self.change_from_year}"
        if self.show_change and key in self._urls:
            specs.append(self._urls[key])
        self.map_layers = specs

    async def _mint(self, key: str, builder) -> None:
        if key in self._urls:
            async with self:
                self._refresh_layers()
            return
        spec = await asyncio.get_running_loop().run_in_executor(None, builder)
        async with self:
            if spec:
                self._urls[key] = spec
            self._refresh_layers()

    def set_basemap(self, label: str):
        col = "label_pt" if self.language == "pt" else "label_en"
        key = next((k for k, v in BASEMAPS.items() if v[col] == label), None)
        if key:
            self.basemap = key
            self._refresh_layers()

    @rx.event(background=True)
    async def toggle_nlcd(self, on: bool):
        async with self:
            self.show_nlcd = on
            year = self.nlcd_year
            self._refresh_layers()
        if on:
            await self._mint(f"us:nlcd:{year}", lambda: layer_service.nlcd_year_spec(year))

    @rx.event(background=True)
    async def set_nlcd_year(self, value: str):
        async with self:
            self.nlcd_year = int(value)
            year, on = self.nlcd_year, self.show_nlcd
            self._refresh_layers()
        if on:
            await self._mint(f"us:nlcd:{year}", lambda: layer_service.nlcd_year_spec(year))

    def set_nlcd_opacity(self, value: List[float]):
        self.nlcd_opacity = round(float(value[0]) / 100.0, 2)
        self._refresh_layers()

    @rx.event(background=True)
    async def toggle_change(self, on: bool):
        async with self:
            self.show_change = on
            yr = self.change_from_year
            self._refresh_layers()
        if on:
            await self._mint(f"us:change:{yr}", lambda: layer_service.hansen_change_spec(yr))

    def toggle_padus(self, on: bool):
        self.show_padus = on
        self._refresh_layers()
