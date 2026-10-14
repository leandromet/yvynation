"""The NTEMS VLCE2 land-cover trajectory, 1984–2022 (Land cover tab).

A copy of ``_cover.py`` (the AAFC tab) over ``services/vlce2_history.py`` —
the history that answers north of the crop inventory's ~54–58°N limit.

Original AAFC docstring follows.

The Canadian counterpart of ``camposcope/state/_analysis.py::AnalysisMixin``.
Runs as a background handler for the same reason: the parcel card and rings are
already on screen and interactive while this is still fetching.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import plotly.graph_objects as go
import reflex as rx

from .._shared.proxy import plain
from ..components import charts
from ..config import aafc as mb
from ..config import vlce2 as vlce2_cfg
from ..translations import get_translations

logger = logging.getLogger(__name__)


class CanadaVlce2Mixin(rx.State, mixin=True):
    """VLCE2 history: the job, its result, its failure."""

    vlce2_running: bool = False
    vlce2_error: str = ""
    vlce2_rows: List[Dict[str, Any]] = []
    vlce2_degraded: bool = False
    vlce2_notes: List[str] = []
    vlce2_provenance: Dict[str, Any] = {}
    #: Set when the parcel is north of the ACI's coverage — an empty result
    #: is expected there and the tab says so instead of reading as an error.
    vlce2_out_of_range: bool = False

    vlce2_normalise: bool = False
    vlce2_layer_year: int = vlce2_cfg.VLCE2_YEAR_END

    @rx.var
    def has_vlce2(self) -> bool:
        return bool(self.vlce2_rows)

    @rx.var
    def vlce2_rows_for_zone(self) -> List[Dict[str, Any]]:
        zone = self.active_zone
        return [r for r in self.vlce2_rows if r["zone_key"] == zone]

    @rx.var(cache=True,
            deps=["vlce2_rows", "active_zone", "vlce2_layer_year", "language"],
            auto_deps=False)
    def vlce2_table_rows(self) -> List[Dict[str, Any]]:
        year = self.vlce2_layer_year
        lang = getattr(self, "language", "en")
        class_key = f"class_{lang}" if lang in ("pt", "fr") else "class_en"
        rows = [r for r in self.vlce2_rows_for_zone if r["year"] == year]
        total = sum(r["area_ha"] for r in rows) or 1.0
        out = [
            {"class_label": r[class_key], "color": r["color"],
             "area_ha": round(r["area_ha"], 2),
             "area_pct": round(100.0 * r["area_ha"] / total, 1)}
            for r in rows
        ]
        out.sort(key=lambda r: r["area_ha"], reverse=True)
        return out

    def set_vlce2_layer_year(self, year: str) -> None:
        self.vlce2_layer_year = int(year)
        return self.__class__.mint_analysis_layer

    @rx.var(cache=True,
            deps=["vlce2_rows", "active_zone", "vlce2_normalise", "parcel",
                  "language"],
            auto_deps=False)
    def vlce2_figure(self) -> go.Figure:
        return charts.land_cover_history_figure(
            self.vlce2_rows_for_zone,
            lang=getattr(self, "language", "en"),
            normalise=self.vlce2_normalise,
            start_year=getattr(self, "parcel", {}).get("start_year") or None,
            vocab=vlce2_cfg,
        )

    def toggle_vlce2_normalise(self) -> None:
        self.vlce2_normalise = not self.vlce2_normalise

    @rx.event(background=True)
    async def run_vlce2_history(self):
        from ..services.vlce2_history import land_cover_history
        from .._shared.zones import Zone

        async with self:
            zones_geojson = plain(self.zones_geojson) or {}
            zones_meta = list(self.zones or [])
            lang = getattr(self, "language", "en")
            self.vlce2_running = True
            self.vlce2_error = ""
            self.vlce2_rows = []
            self.vlce2_degraded = False
            self.vlce2_notes = []
            self.vlce2_provenance = {}
            self.vlce2_out_of_range = False

        if not zones_meta or not zones_geojson.get("features"):
            async with self:
                self.vlce2_running = False
            return

        try:
            geom_by_key = {f["properties"]["zone_key"]: f["geometry"]
                          for f in zones_geojson["features"]}
            zone_objs = [
                Zone(key=z["zone_key"], label=z["zone_label"], kind=z["zone_kind"],
                    geojson=geom_by_key[z["zone_key"]], area_ha=z["area_ha"],
                    radius_m=z.get("radius_m"))
                for z in zones_meta if z["zone_key"] in geom_by_key
            ]
            df, prov = land_cover_history(zone_objs)
        except Exception as exc:                       # noqa: BLE001
            logger.exception("VLCE2 history failed")
            async with self:
                self.vlce2_running = False
                self.vlce2_error = get_translations(lang)[
                    "erro_trajetoria_vlce2"].format(detail=exc)
            return

        async with self:
            self.vlce2_running = False
            self.vlce2_rows = df.to_dict("records") if not df.empty else []
            self.vlce2_degraded = prov.degraded
            self.vlce2_notes = list(prov.notes)
            self.vlce2_provenance = prov.to_dict()
            if df.empty:
                self.vlce2_out_of_range = True
                self.vlce2_error = get_translations(lang)["erro_vlce2_sem_classes"]
