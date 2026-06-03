"""
Advanced interactive visualizations for the geometry / territory analysis pages.

Ports three batch-only visualization groups into the live (interactive) flow,
each gated behind an explicit "Run"/"Generate" button so heavy Earth Engine
calls only fire on demand:

  1. PNG map set    — satellite basemap + MapBiomas y1/y2 (+ optional aux
                      rasters: deforestation, fire, mining, agriculture),
                      rendered inline and downloadable as a ZIP.
  2. Multi-window   — multi-stage Sankey + per-pair Sunburst across 3–N years.
  3. Deforestation  — Hansen loss + MapBiomas primary defor + secondary regrowth
     timeline         + fire scar, with Brazilian political / policy context bars.

All heavy lifting reuses existing utils (``map_export_service``,
``visualization``, ``deforestation_timeline``); this mixin only wires them to
interactive state, the on-demand background handlers, and the per-pair figure
lists.  The computed Plotly ``Figure`` vars live in ``state/__init__.py`` beside
the other chart vars (``sankey_chart`` etc.).

Mirrors the established patterns in ``_analysis.py`` (``run_territory_comparison_bg``)
and ``_batch.py``: ``@rx.event(background=True)`` async handlers, EE calls via
``run_in_executor``, and state mutated only inside ``async with self`` blocks.
"""

import asyncio
import base64
import io
import logging
import zipfile
from typing import Any, Dict, List

import reflex as rx
from plotly.graph_objs import Figure

logger = logging.getLogger(__name__)

# Inclusive MapBiomas year range (matches batch).
START_YEAR, END_YEAR = 1985, 2024

# Aux-layer toggle attribute → MAPBIOMAS_AUX_DATASETS key.  Mirrors the mapping
# built in ``state/_batch.py`` (``aux_layer_keys``).
_AUX_KEY_MAP = [
    ("map_aux_deforestation", "deforestation_secondary"),
    ("map_aux_fire_scar", "fire_scar_size"),
    ("map_aux_fire_frequency", "fire_frequency"),
    ("map_aux_fire_year_last", "fire_year_last"),
    ("map_aux_mining", "mining_substances"),
    ("map_aux_agriculture", "agriculture_cycles"),
]


def _str_keys(d):
    """Recursively stringify dict keys (Reflex requires str keys)."""
    if not isinstance(d, dict):
        return d
    return {str(k): _str_keys(v) for k, v in d.items()}


def _ordered_pair(a: int, b: int):
    """Return ``(low, high)`` so callers never pass an inverted year range."""
    a, b = int(a), int(b)
    return (a, b) if a <= b else (b, a)


def _features_to_ee(features, drawn, territory):
    """Resolve an ``ee.Geometry`` + GeoJSON dict for the active selection.

    Prefers an explicit territory boundary, then a drawn/uploaded geometry, then
    a slow fallback to the EE service keyed on the selected territory name.
    Returns ``(ee_geometry, geojson_dict_or_None)``.
    """
    from ..utils.buffer_utils import convert_geojson_to_ee_geometry

    ee_geom = None
    geojson = None
    src = (features[0] if features else None) or (drawn[0] if drawn else None)
    if src is not None:
        ee_geom = convert_geojson_to_ee_geometry(src)
        geojson = src.get("geometry") if src.get("type") == "Feature" else src
    if ee_geom is None and territory:
        try:
            from ..utils.ee_service_extended import get_ee_service
            ee_geom = get_ee_service().get_territory_geometry(territory)
            if ee_geom is not None:
                try:
                    geojson = ee_geom.getInfo()
                except Exception:
                    geojson = None
        except Exception as e:
            logger.warning(f"[ADV-VIZ] EE geometry fallback failed: {e}")
    return ee_geom, geojson


class AdvancedVizMixin(rx.State, mixin=True):
    """On-demand interactive ports of the three batch visualization groups."""

    # ── Config: PNG map set ────────────────────────────────────────────────
    map_aux_deforestation: bool = False
    map_aux_fire_scar: bool = False
    map_aux_fire_frequency: bool = False
    map_aux_fire_year_last: bool = False
    map_aux_mining: bool = False
    map_aux_agriculture: bool = False

    # ── Config: multi-window ───────────────────────────────────────────────
    mw_mode: str = "custom"                 # "constant" | "custom"
    mw_step: str = "8"                      # constant-mode step in years
    mw_custom_years: str = "1985, 2004, 2012, 2023"

    # ── Config: deforestation timeline ─────────────────────────────────────
    tl_include_hansen: bool = True
    tl_include_defor: bool = True
    tl_include_secondary: bool = True
    tl_include_fire: bool = True

    # ── Pending flags ──────────────────────────────────────────────────────
    mapset_pending: bool = False
    mw_pending: bool = False
    timeline_pending: bool = False

    # ── Results: PNG map set ───────────────────────────────────────────────
    mapset_images: List[Dict[str, str]] = []   # [{"name", "data_uri"}]
    mapset_zip_b64: str = ""                    # base64 ZIP for download

    # ── Results: multi-window ──────────────────────────────────────────────
    mw_result: Dict[str, Any] = {}             # {"years", "pairs"}
    buffer_mw_result: Dict[str, Any] = {}
    # Per-pair Sunbursts as real Figures so rx.foreach + rx.plotly type-check.
    mw_sunburst_figs: List[Figure] = []
    buffer_mw_sunburst_figs: List[Figure] = []

    # ── Results: deforestation timeline ────────────────────────────────────
    timeline_series: Dict[str, Any] = {}       # {indicator: {year: ha}}
    buffer_timeline_series: Dict[str, Any] = {}
    timeline_state_code: str = ""              # 2-letter UF for governor stripe
    timeline_year_start: int = 0
    timeline_year_end: int = 0
    timeline_territory_name: str = ""
    timeline_territory_type: str = "indigenous"

    # =======================================================================
    # Setters / togglers
    # =======================================================================
    def toggle_map_aux_deforestation(self, v: bool):
        self.map_aux_deforestation = v

    def toggle_map_aux_fire_scar(self, v: bool):
        self.map_aux_fire_scar = v

    def toggle_map_aux_fire_frequency(self, v: bool):
        self.map_aux_fire_frequency = v

    def toggle_map_aux_fire_year_last(self, v: bool):
        self.map_aux_fire_year_last = v

    def toggle_map_aux_mining(self, v: bool):
        self.map_aux_mining = v

    def toggle_map_aux_agriculture(self, v: bool):
        self.map_aux_agriculture = v

    def set_mw_mode(self, mode: str):
        if mode in ("constant", "custom"):
            self.mw_mode = mode

    def set_mw_step(self, step: str):
        self.mw_step = step

    def set_mw_custom_years(self, txt: str):
        self.mw_custom_years = txt

    def toggle_tl_include_hansen(self, v: bool):
        self.tl_include_hansen = v

    def toggle_tl_include_defor(self, v: bool):
        self.tl_include_defor = v

    def toggle_tl_include_secondary(self, v: bool):
        self.tl_include_secondary = v

    def toggle_tl_include_fire(self, v: bool):
        self.tl_include_fire = v

    # =======================================================================
    # Computed: resolved multi-window years (mirrors batch logic)
    # =======================================================================
    @rx.var
    def mw_resolved_years(self) -> List[int]:
        """Active year list for the multi-window analysis.

        Constant mode: start at 1985, step by ``mw_step`` years, always include
        2024.  Custom mode: parse 3–4 valid comma-separated years (1985–2024).
        Returns an empty list when the input is invalid.
        """
        try:
            if self.mw_mode == "custom":
                years: List[int] = []
                for p in self.mw_custom_years.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    try:
                        y = int(p)
                    except ValueError:
                        continue
                    if START_YEAR <= y <= END_YEAR and y not in years:
                        years.append(y)
                years.sort()
                return years if 3 <= len(years) <= 4 else []
            step = int(self.mw_step)
            if step <= 0:
                return []
            years = list(range(START_YEAR, END_YEAR + 1, step))
            if years[-1] != END_YEAR:
                years.append(END_YEAR)
            return years
        except Exception:
            return []

    # ----- result presence flags (clean rx.cond gating) -----
    @rx.var
    def mw_has_result(self) -> bool:
        return bool((self.mw_result or {}).get("pairs"))

    @rx.var
    def mw_has_buffer(self) -> bool:
        return bool((self.buffer_mw_result or {}).get("pairs"))

    @rx.var
    def timeline_has_data(self) -> bool:
        return bool(self.timeline_series)

    @rx.var
    def timeline_has_buffer(self) -> bool:
        return bool(self.buffer_timeline_series)

    # =======================================================================
    # 1. PNG map set — generate + download
    # =======================================================================
    def generate_map_set(self):
        """Kick off the background PNG map-set builder."""
        if not (self.selected_territory or self.territory_geojson_features
                or self.drawn_features):
            self.error_message = "Select a territory or draw a geometry first"
            return
        self.mapset_pending = True
        self.error_message = ""
        self.loading_message = "Generating maps…"
        return type(self).generate_map_set_bg()

    @rx.event(background=True)
    async def generate_map_set_bg(self):
        loop = asyncio.get_event_loop()
        try:
            async with self:
                territory = self.selected_territory
                terr_feats = list(self.territory_geojson_features)
                drawn = list(self.drawn_features)
                buf_feats = list(self.buffer_geojson_features)
                y1, y2 = int(self.comparison_year1), int(self.comparison_year2)
                hansen_layers = list(self.hansen_displayed_layers)
                aux_keys = [key for attr, key in _AUX_KEY_MAP if getattr(self, attr)]
                name = self.territory_name or territory or "geometry"

            def _resolve():
                from ..utils.buffer_utils import convert_geojson_to_ee_geometry
                ee_geom, geojson = _features_to_ee(terr_feats, drawn, territory)
                buf_geojson = None
                if buf_feats:
                    bg = convert_geojson_to_ee_geometry(buf_feats[0])
                    if bg is not None:
                        try:
                            buf_geojson = bg.getInfo()
                        except Exception:
                            f0 = buf_feats[0]
                            buf_geojson = f0.get("geometry") if f0.get("type") == "Feature" else f0
                return ee_geom, geojson, buf_geojson

            ee_geom, geojson, buf_geojson = await loop.run_in_executor(None, _resolve)

            def _build():
                from ..utils.map_export_service import create_map_set
                mb_years = [y1] if y1 == y2 else sorted({y1, y2})
                aux_layers = [(k, y2) for k in aux_keys]
                return create_map_set(
                    drawn_features=drawn,
                    territory_name=name,
                    active_mapbiomas_years=mb_years,
                    active_hansen_layers=hansen_layers or None,
                    ee_geometry=ee_geom,
                    territory_geojson=geojson,
                    buffer_geojson=buf_geojson,
                    image_format="png",
                    active_aux_layers=aux_layers or None,
                )

            maps = await loop.run_in_executor(None, _build)

            images: List[Dict[str, str]] = []
            zip_b64 = ""
            if maps:
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    for nm, b in maps.items():
                        zf.writestr(f"maps/{nm}.png", b)
                        images.append({
                            "name": nm,
                            "data_uri": "data:image/png;base64," + base64.b64encode(b).decode(),
                        })
                buf.seek(0)
                zip_b64 = base64.b64encode(buf.read()).decode()

            async with self:
                self.mapset_images = images
                self.mapset_zip_b64 = zip_b64
                self.mapset_pending = False
                self.loading_message = ""
                if not images:
                    self.error_message = (
                        "No maps generated — run a year comparison or add layers first."
                    )
                else:
                    self.active_analysis_tab = "maps"
        except Exception as e:
            logger.error(f"[ADV-VIZ] map set failed: {e}", exc_info=True)
            async with self:
                self.mapset_pending = False
                self.loading_message = ""
                self.error_message = f"Map generation failed: {e}"

    def download_map_set_zip(self):
        """Download the most recently generated PNG map ZIP."""
        if not self.mapset_zip_b64:
            self.error_message = "No maps to download — generate maps first"
            return
        from datetime import datetime
        data = base64.b64decode(self.mapset_zip_b64)
        terr = (self.territory_name or self.selected_territory or "maps").replace(" ", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        return rx.download(data=data, filename=f"yvynation_maps_{terr}_{ts}.zip")

    # =======================================================================
    # 2. Multi-window MapBiomas — Sankey + per-pair Sunburst
    # =======================================================================
    def run_multi_window_analysis(self):
        """Kick off the background multi-window transition analysis."""
        if not (self.selected_territory or self.territory_geojson_features
                or self.drawn_features):
            self.error_message = "Select a territory or draw a geometry first"
            return
        if len(self.mw_resolved_years) < 2:
            self.error_message = (
                "Multi-window needs at least 3 valid years (custom) "
                "or a valid step (constant)."
            )
            return
        self.mw_pending = True
        self.error_message = ""
        self.loading_message = "Computing multi-window transitions…"
        return type(self).run_multi_window_analysis_bg()

    @rx.event(background=True)
    async def run_multi_window_analysis_bg(self):
        loop = asyncio.get_event_loop()
        try:
            async with self:
                territory = self.selected_territory
                terr_feats = list(self.territory_geojson_features)
                drawn = list(self.drawn_features)
                buf_feats = list(self.buffer_geojson_features)
                years = [int(y) for y in self.mw_resolved_years]

            def _resolve():
                from ..utils.buffer_utils import convert_geojson_to_ee_geometry
                ee_geom, _ = _features_to_ee(terr_feats, drawn, territory)
                buf_geom = convert_geojson_to_ee_geometry(buf_feats[0]) if buf_feats else None
                return ee_geom, buf_geom

            ee_geom, buf_geom = await loop.run_in_executor(None, _resolve)
            if ee_geom is None:
                async with self:
                    self.mw_pending = False
                    self.loading_message = ""
                    self.error_message = "Could not resolve geometry for multi-window analysis"
                return

            def _pairs(geom):
                from ..utils.mapbiomas_analysis import get_mapbiomas_analyzer
                analyzer = get_mapbiomas_analyzer()
                out = []
                for ya, yb in zip(years[:-1], years[1:]):
                    try:
                        tr = analyzer.compute_transitions(geom, ya, yb, 30,
                                                          include_unchanged=True)
                    except Exception as e:
                        logger.warning(f"[ADV-VIZ] mw transitions {ya}->{yb}: {e}")
                        tr = {}
                    out.append({
                        "year_from": int(ya),
                        "year_to": int(yb),
                        "transitions": _str_keys(tr or {}),
                    })
                return out

            def _sunbursts(pairs):
                from ..utils.visualization import create_sunburst_transitions
                figs = []
                for p in pairs:
                    tr = p.get("transitions") or {}
                    if not tr:
                        continue
                    try:
                        fig = create_sunburst_transitions(
                            tr, p["year_from"], p["year_to"])
                        if fig is not None:
                            figs.append(fig)
                    except Exception as e:
                        logger.warning(f"[ADV-VIZ] mw sunburst build: {e}")
                return figs

            async with self:
                self.loading_message = "Multi-window — territory transitions…"
            t_pairs = await loop.run_in_executor(None, _pairs, ee_geom)
            t_figs = await loop.run_in_executor(None, _sunbursts, t_pairs)

            b_pairs, b_figs = [], []
            if buf_geom is not None:
                async with self:
                    self.loading_message = "Multi-window — buffer transitions…"
                b_pairs = await loop.run_in_executor(None, _pairs, buf_geom)
                b_figs = await loop.run_in_executor(None, _sunbursts, b_pairs)

            async with self:
                self.mw_result = {"years": years, "pairs": t_pairs}
                self.mw_sunburst_figs = t_figs
                self.buffer_mw_result = (
                    {"years": years, "pairs": b_pairs} if b_pairs else {}
                )
                self.buffer_mw_sunburst_figs = b_figs
                self.mw_pending = False
                self.loading_message = ""
                self.active_analysis_tab = "multiwindow"
        except Exception as e:
            logger.error(f"[ADV-VIZ] multi-window failed: {e}", exc_info=True)
            async with self:
                self.mw_pending = False
                self.loading_message = ""
                self.error_message = f"Multi-window analysis failed: {e}"

    # =======================================================================
    # 3. Deforestation timeline — Hansen + MapBiomas + Fire + context bars
    # =======================================================================
    def run_deforestation_timeline(self):
        """Kick off the background deforestation-timeline collection."""
        if not (self.selected_territory or self.territory_geojson_features
                or self.drawn_features):
            self.error_message = "Select a territory or draw a geometry first"
            return
        self.timeline_pending = True
        self.error_message = ""
        self.loading_message = "Building deforestation timeline…"
        return type(self).run_deforestation_timeline_bg()

    @rx.event(background=True)
    async def run_deforestation_timeline_bg(self):
        loop = asyncio.get_event_loop()
        try:
            async with self:
                territory = self.selected_territory
                terr_feats = list(self.territory_geojson_features)
                drawn = list(self.drawn_features)
                buf_feats = list(self.buffer_geojson_features)
                y_start, y_end = _ordered_pair(self.comparison_year1, self.comparison_year2)
                inc = dict(
                    hansen=self.tl_include_hansen,
                    defor=self.tl_include_defor,
                    secondary=self.tl_include_secondary,
                    fire=self.tl_include_fire,
                )
                gfc_result = self.geometry_gfc_result
                buffer_gfc_result = self.buffer_gfc_result
                name = self.territory_name or territory or ""

            def _resolve():
                from ..utils.buffer_utils import convert_geojson_to_ee_geometry
                ee_geom, _ = _features_to_ee(terr_feats, drawn, territory)
                buf_geom = convert_geojson_to_ee_geometry(buf_feats[0]) if buf_feats else None
                # State code for the governor stripe (indigenous service).
                state_code = ""
                if territory:
                    try:
                        from ..utils.territory_service import get_territory_service
                        from ..utils.deforestation_timeline import first_state_code
                        info = get_territory_service().get_territory_info(territory) or {}
                        sc = first_state_code(info.get("uf_sigla"))
                        state_code = sc or ""
                    except Exception as e:
                        logger.warning(f"[ADV-VIZ] state code resolve: {e}")
                return ee_geom, buf_geom, state_code

            ee_geom, buf_geom, state_code = await loop.run_in_executor(None, _resolve)
            if ee_geom is None:
                async with self:
                    self.timeline_pending = False
                    self.loading_message = ""
                    self.error_message = "Could not resolve geometry for timeline"
                return

            def _series(geom, gfc):
                from ..utils.deforestation_timeline import collect_timeline
                return collect_timeline(
                    geom, y_start, y_end,
                    gfc_result=gfc,
                    include_hansen=inc["hansen"],
                    include_mb_defor=inc["defor"],
                    include_mb_secondary=inc["secondary"],
                    include_fire=inc["fire"],
                )

            async with self:
                self.loading_message = "Timeline — territory series…"
            t_series = await loop.run_in_executor(None, _series, ee_geom, gfc_result)

            b_series = {}
            if buf_geom is not None:
                async with self:
                    self.loading_message = "Timeline — buffer series…"
                b_series = await loop.run_in_executor(None, _series, buf_geom, buffer_gfc_result)

            async with self:
                self.timeline_series = t_series or {}
                self.buffer_timeline_series = b_series or {}
                self.timeline_state_code = state_code
                self.timeline_year_start = y_start
                self.timeline_year_end = y_end
                self.timeline_territory_name = name
                self.timeline_territory_type = "indigenous"
                self.timeline_pending = False
                self.loading_message = ""
                self.active_analysis_tab = "timeline"
        except Exception as e:
            logger.error(f"[ADV-VIZ] timeline failed: {e}", exc_info=True)
            async with self:
                self.timeline_pending = False
                self.loading_message = ""
                self.error_message = f"Deforestation timeline failed: {e}"
