"""The numbers of the Canada conservation walkthrough (``/walkthrough/conservation-unit``).

The English conservation-unit walkthrough opens a CPCAD park above Kelowna
instead of a Brazilian reserve, so Canadian readers see land they know. Like the
Brazil package (``utils/demonstracao.py``) it has no numbers of its own: it is
built by the services the Canada page runs on a chosen area — the AAFC crop
inventory, transitions, Hansen, ESA CCI biomass, MODIS fire and the VLCE2
cross-check — over the park and three rings around it (or another CPCAD area,
by ``?area=``). If a number on the page disagrees with the app, the defect is
here, not in the text.

Only the conservation walkthrough has a Canadian twin: the Canada page analyses
CPCAD areas only, with no drawing and no batch, and Indigenous lands are not in
its data at all (OCAP®). The other three English walkthroughs stay Brazilian.

Measured on the example (2026-10-29): ~10 s cold in parallel. The example is
stored so the page opens at once; tile URLs are minted per request.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .._shared.settings import HANSEN_TREECOVER_THRESHOLD
from ..config import aafc
from ..config import vlce2 as vcfg
from ..config.datasets import AGB_YEARS
from . import biomass, fire, hansen, layers, transitions, vlce2
from . import zones as cz
from .aci_history import land_cover_history

logger = logging.getLogger(__name__)

#: Okanagan Mountain Provincial Park, 11,321 ha on the east shore of Okanagan
#: Lake: established in 1973 and the origin of the August 2003 fire that burned
#: into south-east Kelowna.
EXEMPLO_PADRAO = "OKANAGAN MOUNTAIN PARK"
PROVINCIA = "BC"
ROTA = "/_demonstracao/yvynation_ca.json"
ARQUIVO_EXEMPLO = Path(__file__).resolve().parents[2] / "reportagem" / "exemplos" / "unidade-conservacao.ca.json"

_TTL_S = 6 * 3600
_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
_travas: Dict[str, threading.Lock] = {}
_trava_global = threading.Lock()


class AreaInvalida(ValueError):
    """An ``?area=`` that is not in the loaded CPCAD catalogue."""


def _trava(chave: str) -> threading.Lock:
    with _trava_global:
        return _travas.setdefault(chave, threading.Lock())


def _seguro(nome: str, fn: Callable[[], Any], erros: Dict[str, str]) -> Any:
    """An analysis that fails becomes a declared gap, not a broken page."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        logger.exception("walkthrough: %s failed", nome)
        erros[nome] = str(exc)[:300]
        return None


def _prov(p: Any) -> Dict[str, Any]:
    return {"nome": getattr(p, "name", ""), "dataset": getattr(p, "dataset_id", ""),
            "escala_m": getattr(p, "scale_m", None), "calculado_em": getattr(p, "computed_at", "")}


def _num(v: Any) -> Optional[float]:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else round(f, 3)


def _leve(geom: Optional[Dict[str, Any]], tol: float) -> Optional[Dict[str, Any]]:
    """A geometry to draw: simplified, five decimals (~1 m)."""
    if not geom:
        return geom
    from shapely.geometry import mapping, shape
    g = shape(geom.get("geometry", geom))
    s = g.simplify(tol, preserve_topology=True)
    g = s if not s.is_empty else g

    def arred(c):
        return [arred(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]

    m = mapping(g)
    return {"type": m["type"], "coordinates": arred(m["coordinates"])}


def _historico(df) -> Dict[str, Any]:
    anos = sorted(int(a) for a in df["year"].unique())
    por_zona: Dict[str, Dict[str, List[float]]] = {}
    classes: Dict[str, Dict[str, str]] = {}
    for (zona, classe), g in df.groupby(["zone_key", "class_id"]):
        serie = dict(zip(g["year"].astype(int), g["area_ha"].astype(float)))
        por_zona.setdefault(zona, {})[str(int(classe))] = [round(serie.get(a, 0.0), 2) for a in anos]
        if str(int(classe)) not in classes:
            linha = g.iloc[0]
            classes[str(int(classe))] = {"nome": str(linha["class_pt"]), "nome_en": str(linha["class_en"]),
                                         "cor": str(linha["color"])}
    return {"anos": anos, "zonas": por_zona, "classes": classes, "nativas": sorted(aafc.NATURAL_VEGETATION)}


def _area(chave: str) -> Dict[str, Any]:
    from ...utils.conservation_service import get_ca_protected_area_service
    svc = get_ca_protected_area_service()
    svc.ensure_provinces([PROVINCIA])
    if chave not in svc.get_all_display_keys([PROVINCIA]):
        raise AreaInvalida(f"{chave!r} is not a CPCAD area in {PROVINCIA}.")
    info = svc.get_territory_info(chave)
    row = svc._get_row(chave)
    extra = {} if row is None else {c: (row.get(c) if row.get(c) == row.get(c) else "")
                                    for c in ("iucn_cat", "status", "est_year", "owner_type", "org_gestor")}
    return {"chave": chave, "nome": info.get("nome_uc", chave), "categoria": info.get("categoria", ""),
            "governanca": info.get("esfera", ""), "provincia": info.get("uf_sigla", PROVINCIA),
            "area_registrada_ha": float(info.get("superficie_ha") or 0),
            "iucn": str(extra.get("iucn_cat") or ""), "ano_criacao": int(extra.get("est_year") or 0) or None,
            "gestor": str(extra.get("org_gestor") or ""), "partes": len(svc.get_parts(chave)),
            "geometry": svc.get_geojson_for_key(chave)}


def _calcular(chave: str) -> Dict[str, Any]:
    area = _area(chave)
    geom = area["geometry"].get("geometry", area["geometry"]) if area["geometry"].get("type") == "Feature" else area["geometry"]
    zonas = cz.build_zones(geom, radii_m=[500, 2000, 5000], parcel_label="Park")
    ano_a, ano_b = transitions.default_year_pair()
    ano_v = vlce2.default_year()
    erros: Dict[str, str] = {}
    tarefas: Dict[str, Callable[[], Any]] = {
        "historico": lambda: land_cover_history(zonas),
        "transicoes": lambda: transitions.compute_transitions(zonas, ano_a, ano_b),
        "hansen": lambda: hansen.forest_change(zonas, parcel_year=area["ano_criacao"]),
        "biomassa": lambda: biomass.above_ground_biomass(zonas),
        "fogo": lambda: fire.fire_analysis(zonas),
        "vlce2": lambda: vlce2.agreement(zonas, ano_v),
    }
    with ThreadPoolExecutor(max_workers=len(tarefas)) as pool:
        futuros = {k: pool.submit(_seguro, k, fn, erros) for k, fn in tarefas.items()}
        r = {k: f.result() for k, f in futuros.items()}

    area = {**area, "geometry": geom, "area_calculada_ha": round(zonas[0].area_ha, 2)}
    out: Dict[str, Any] = {
        "area": area,
        "zonas": [{"key": z.key, "label": z.label, "area_ha": round(z.area_ha, 2), "geojson": z.geojson} for z in zonas],
        "procedencia": [], "erros": erros,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if r["historico"]:
        df, p = r["historico"]
        out["historico"] = _historico(df)
        out["procedencia"].append(_prov(p))
    if r["transicoes"]:
        T, p = r["transicoes"]
        out["transicoes"] = {"ano_a": ano_a, "ano_b": ano_b, "zonas": {
            zona: [{"de": int(a), "para": int(b), "ha": round(float(v), 2)}
                   for a, destinos in fluxos.items() for b, v in destinos.items() if v > 0]
            for zona, fluxos in T.items()}}
        out["procedencia"].append(_prov(p))
    if r["hansen"]:
        perda, ganho, p = r["hansen"]
        out["hansen"] = {"limiar_pct": HANSEN_TREECOVER_THRESHOLD, "ganho_ha": round(float(ganho), 2),
                         "divide_em": hansen.splits_at(area["ano_criacao"]),
                         "perda": {zona: [{"ano": int(x.year), "ha": round(float(x.area_ha), 2)} for x in g.itertuples()]
                                   for zona, g in perda.groupby("zone_key")}}
        out["procedencia"].append(_prov(p))
    if r["biomassa"]:
        B, p = r["biomassa"]
        out["biomassa"] = {zona: [{"ano": int(x.year), "mgha": round(float(x.agb_mean_mgha), 2)} for x in g.itertuples()]
                           for zona, g in B.groupby("zone_key")}
        out["procedencia"].append(_prov(p))
    if r["fogo"]:
        resumo, anual, p = r["fogo"]
        out["fogo"] = {
            "resumo": {x.zone_key: {"historico_pct": _num(x.fire_history_pct), "ultimo_ano": int(x.fire_last_year) if _num(x.fire_last_year) else None}
                       for x in resumo.itertuples()},
            "anual": {zona: [{"ano": int(x.year), "pct": round(float(x.fire_pct), 2)} for x in g.itertuples()]
                      for zona, g in anual.groupby("zone_key")},
        }
        out["procedencia"].append(_prov(p))
    if r["vlce2"]:
        resumo, matriz, p = r["vlce2"]
        out["vlce2"] = {
            "ano": ano_v,
            "grupos": {k: {"nome_en": vcfg.GROUP_LABELS_EN.get(k, k), "cor": vcfg.GROUP_COLORS.get(k, "#9aa8a1")} for k in vcfg.GROUP_LABELS_EN},
            "resumo": {x.zone_key: {"concordancia_pct": _num(x.agreement_pct)} for x in resumo.itertuples()},
            "matriz": {zona: [{"aci": x.aci_group, "vlce2": x.vlce2_group, "ha": round(float(x.area_ha), 2)}
                              for x in g.itertuples() if x.area_ha > 0]
                       for zona, g in matriz.groupby("zone_key")},
        }
        out["procedencia"].append(_prov(p))
    return out


def _camadas(pacote: Dict[str, Any]) -> Dict[str, Any]:
    anos = (pacote.get("historico") or {}).get("anos") or [aafc.ACI_YEAR_END]
    ano_v = (pacote.get("vlce2") or {}).get("ano")
    specs: Dict[str, Callable[[], Any]] = {
        f"aci_{anos[0]}": lambda: layers.aci_year_spec(anos[0]),
        f"aci_{anos[-1]}": lambda: layers.aci_year_spec(anos[-1]),
        "hansen": lambda: layers.hansen_change_spec(2001),
        "biomassa": lambda: layers.biomass_year_spec(AGB_YEARS[-1]),
        "fogo": lambda: layers.fire_frequency_spec(),
    }
    if ano_v:
        specs[f"vlce2_{ano_v}"] = lambda: layers.vlce2_year_spec(ano_v)
    erros: Dict[str, str] = {}
    out: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(specs)) as pool:
        futuros = {k: pool.submit(_seguro, f"layer {k}", fn, erros) for k, fn in specs.items()}
        for k, f in futuros.items():
            spec = f.result()
            if spec and spec.get("url"):
                out[k] = {"url": spec["url"], "attribution": spec.get("attribution", ""), "opacity": spec.get("opacity", 0.8)}
    return out


def instantaneo(chave: str = EXEMPLO_PADRAO) -> Dict[str, Any]:
    """The package without layers and with light geometries — ``ARQUIVO_EXEMPLO``."""
    dados = _calcular(chave)
    dados["area"]["geometry"] = _leve(dados["area"]["geometry"], 0.0002)
    for z in dados["zonas"]:
        z["geojson"] = _leve(z["geojson"], 0.0004)
    return dados


def _exemplo_guardado() -> Optional[Dict[str, Any]]:
    try:
        return json.loads(ARQUIVO_EXEMPLO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def pacote(chave: Optional[str] = None) -> Dict[str, Any]:
    chave = (chave or EXEMPLO_PADRAO).strip()
    if chave == EXEMPLO_PADRAO:
        guardado = _exemplo_guardado()
        if guardado:
            return {**guardado, "camadas": _camadas(guardado), "exemplo_padrao": True}
    with _trava(chave):
        guardado = _cache.get(chave)
        if guardado and time.time() - guardado[0] < _TTL_S:
            dados = guardado[1]
        else:
            t0 = time.time()
            dados = _calcular(chave)
            logger.info("walkthrough %s computed in %.1f s", chave, time.time() - t0)
            if not dados["erros"]:
                _cache[chave] = (time.time(), dados)
    return {**dados, "camadas": _camadas(dados), "exemplo_padrao": chave == EXEMPLO_PADRAO}
