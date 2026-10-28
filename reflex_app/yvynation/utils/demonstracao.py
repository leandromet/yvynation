"""Os números das demonstrações em rolagem (``/demonstracao/<modo>``).

As páginas de demonstração não têm números próprios: pedem este pacote à rota
``/_demonstracao/yvynation.json?modo=…`` e ele é montado pelas mesmas funções
que as páginas de análise chamam — ``analyze_mapbiomas`` por ano, as
transições do ``MapBiomasAnalyzer``, o GFC do ``HansenAnalyzer``, a linha do
tempo de ``deforestation_timeline`` e o buffer externo de ``buffer_utils`` —
para a área de exemplo de cada modo:

* ``terra-indigena``: TI Karipuna (RO), regularizada em 1998;
* ``unidade-conservacao``: Resex Jaci-Paraná (RO), vizinha da Karipuna;
* ``desenho``: um polígono desenhado sobre os reservatórios do rio Madeira;
* ``lote``: as oito terras indígenas de 200 a 1.000 ha de Mato Grosso do Sul (ver ``lote()``).

``?area=`` troca a TI ou a UC por outra do catálogo, pela chave de exibição.

Medido no exemplo da TI (2026-10-27): cada ``analyze_mapbiomas`` ~1–2 s, as
transições ~1 s, o GFC ~2 s, a linha do tempo ~34 s (quatro séries anuais). Em
paralelo, ~35 s a frio; por isso o pacote fica em memória por algumas horas,
com uma trava por área para que visitas simultâneas calculem uma vez só.
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

logger = logging.getLogger(__name__)

ROTA = "/_demonstracao/yvynation.json"

#: Os exemplos padrão de cada modo, já calculados e com geometrias leves, para
#: as páginas abrirem na hora (uma TI calculada a frio leva ~35 s):
#: ``scripts/build_demonstracao.py`` os regrava a partir destas mesmas funções.
#: Um ``?area=`` diferente continua calculado na hora.
PASTA_EXEMPLOS = Path(__file__).resolve().parents[1] / "reportagem" / "exemplos"

MODOS = ("desenho", "terra-indigena", "unidade-conservacao", "lote")

EXEMPLO_TI = "Karipuna"
EXEMPLO_UC = "RESERVA EXTRATIVISTA JACI-PARANÁ"

#: O polígono do modo desenho: uma faixa de ~13 km de largura ao longo do rio
#: Madeira, de Jirau a Santo Antônio, desenhada à mão (os pontos seguem o rio
#: em escala regional). Não é limite oficial de nada — é o tipo de pergunta
#: que só uma área desenhada responde: o que os reservatórios inundaram.
_MADEIRA = [(-64.66, -9.30), (-64.45, -9.18), (-64.30, -9.08), (-64.15, -8.98),
            (-64.02, -8.88), (-63.92, -8.80)]
NOME_DESENHO = "Reservatórios do rio Madeira (área desenhada)"

#: O lote de exemplo: as oito terras indígenas regularizadas de Mato Grosso do
#: Sul com 200 a 1.000 ha (catálogo de 2026-05), quase todas guarani kaiowá e
#: cercadas de lavoura e pasto. Pequenas de propósito: o lote inteiro calcula
#: em segundos. Uma lista fixa, para o exemplo não mudar com o catálogo.
LOTE_UF = "MS"
LOTE = ("Aldeia Limão Verde", "Guaimbé", "Guasuti", "Jaguari", "Ofayé-Xavante (31402)",
        "Pilad Rebuá", "Rancho Jacaré", "Sucuriy")

ANOS = (1985, 2005, 2025)

#: Vegetação nativa, Coleção 11: floresta, savana e campos, sem silvicultura —
#: o mesmo conjunto de Camposcope e Naturametrics (config/mapbiomas.py lá).
NATIVAS = frozenset({3, 4, 5, 6, 49, 10, 11, 12, 13, 29, 32, 50, 77, 84})
BUFFER_KM = 10

_TTL_S = 6 * 3600
_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}
_travas: Dict[str, threading.Lock] = {}
_trava_global = threading.Lock()


class AreaInvalida(ValueError):
    """Um ``?modo=`` desconhecido ou uma ``?area=`` fora do catálogo."""


def _trava(chave: str) -> threading.Lock:
    with _trava_global:
        return _travas.setdefault(chave, threading.Lock())


def _seguro(nome: str, fn: Callable[[], Any], erros: Dict[str, str]) -> Any:
    """Uma análise que falha vira uma lacuna declarada, não uma página quebrada."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        logger.exception("demonstração: %s falhou", nome)
        erros[nome] = str(exc)[:300]
        return None


def _ee():
    from .ee_service import initialize_earth_engine
    if not initialize_earth_engine():
        raise RuntimeError("Earth Engine indisponível")
    import ee
    return ee


def _simplificar(geojson: Dict[str, Any], tol: float = 0.002) -> Dict[str, Any]:
    """Uma geometria leve para desenhar; as contas usam a original."""
    from shapely.geometry import mapping, shape
    g = shape(geojson.get("geometry", geojson))
    s = g.simplify(tol, preserve_topology=True)
    return mapping(s if not s.is_empty else g)


def _classes(df, ano: int) -> List[Dict[str, Any]]:
    from ..config import mapbiomas_legend as leg
    if df is None or df.empty:
        return []
    return [{"id": int(r.Class_ID), "nome": leg.label(int(r.Class_ID), "pt"),
             "nome_en": leg.label(int(r.Class_ID), "en"),
             "cor": leg.color(int(r.Class_ID)), "ha": round(float(r.Area_ha), 1)}
            for r in df.sort_values("Area_ha", ascending=False).itertuples()]


def _gfc(res: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not res or res.get("error"):
        return None
    s = res.get("summary") or {}
    if isinstance(s, str):
        import ast
        s = ast.literal_eval(s)
    return {k: s.get(k) for k in ("tree_cover_2000_ha", "forest_loss_ha", "forest_gain_ha", "net_change_ha")}


def _area(modo: str, chave: Optional[str]) -> Dict[str, Any]:
    """A área de estudo do modo: geometria (GeoJSON) e atributos do catálogo."""
    if modo == "desenho":
        from shapely.geometry import LineString, mapping
        g = mapping(LineString(_MADEIRA).buffer(0.06, quad_segs=8))
        return {"nome": NOME_DESENHO, "tipo": "desenho", "geojson": g, "info": {}, "datas": {}}
    if modo == "terra-indigena":
        from .territory_service import get_territory_service
        svc, chave = get_territory_service(), chave or EXEMPLO_TI
        geo = svc.get_geojson_for_key(chave)
        if geo is None:
            raise AreaInvalida(f"Terra indígena {chave!r} não está no catálogo.")
        info = svc.get_territory_info(chave)
        return {"nome": chave, "tipo": "terra-indigena", "geojson": geo.get("geometry", geo),
                "info": {k: info.get(k) for k in ("terrai_cod", "uf_sigla", "municipio", "etnia", "fase_ti", "modalidade", "superficie_ha")},
                "datas": svc.get_demarcation_dates(chave)}
    if modo == "unidade-conservacao":
        from .conservation_service import get_conservation_unit_service
        svc, chave = get_conservation_unit_service(), chave or EXEMPLO_UC
        geo = svc.get_geojson_for_key(chave)
        if geo is None:
            raise AreaInvalida(f"Unidade de conservação {chave!r} não está no catálogo.")
        info = svc.get_territory_info(chave)
        return {"nome": chave, "tipo": "unidade-conservacao", "geojson": geo.get("geometry", geo),
                "info": {k: info.get(k) for k in ("cd_cnuc", "uf_sigla", "municipio", "grupo", "categoria", "esfera", "superficie_ha")},
                "datas": {}}
    raise AreaInvalida(f"Modo {modo!r} desconhecido; use um de {', '.join(MODOS)}.")


def _calcular(modo: str, chave: Optional[str]) -> Dict[str, Any]:
    ee = _ee()
    from . import buffer_utils as bu
    from . import deforestation_timeline as dt
    from .ee_service_extended import get_ee_service
    from .geometry_handler import sanitize_geometry
    from .hansen_analysis import get_hansen_analyzer
    from .mapbiomas_analysis import get_mapbiomas_analyzer

    area = _area(modo, chave)
    geom = ee.Geometry(sanitize_geometry(area["geojson"], area["nome"]) or area["geojson"])
    buf = bu.create_external_buffer(geom, BUFFER_KM)
    svc, mba, han = get_ee_service(), get_mapbiomas_analyzer(), get_hansen_analyzer()
    erros: Dict[str, str] = {}

    tarefas: Dict[str, Callable[[], Any]] = {
        "buffer_geojson": lambda: bu.convert_ee_geometry_to_geojson(buf.simplify(200)),
        "area_ha": lambda: geom.area(10).divide(1e4).getInfo(),
        "transicoes": lambda: mba.compute_transitions(geom, ANOS[0], ANOS[-1], include_unchanged=True),
        "gfc_area": lambda: han.analyze_gfc(geom),
        "gfc_buffer": lambda: han.analyze_gfc(buf),
        # the Hansen series is read off a GFC result (as the analysis page
        # passes it); computing it again here costs ~2 s in parallel and keeps
        # the two tasks independent
        "linha_area": lambda: dt.collect_timeline(geom, ANOS[0], ANOS[-1], gfc_result=han.analyze_gfc(geom)),
        "linha_buffer": lambda: dt.collect_timeline(buf, ANOS[0], ANOS[-1], gfc_result=han.analyze_gfc(buf)),
    }
    for ano in ANOS:
        tarefas[f"mb_area_{ano}"] = (lambda a=ano: svc.analyze_mapbiomas(geom, a))
        tarefas[f"mb_buffer_{ano}"] = (lambda a=ano: svc.analyze_mapbiomas(buf, a))
    with ThreadPoolExecutor(max_workers=len(tarefas)) as pool:
        futuros = {k: pool.submit(_seguro, k, fn, erros) for k, fn in tarefas.items()}
        r = {k: f.result() for k, f in futuros.items()}

    from ..config.config import MAPBIOMAS_DEFAULT_COLLECTION
    out: Dict[str, Any] = {
        "modo": modo,
        "area": {**{k: area[k] for k in ("nome", "tipo", "info", "datas")},
                 "area_ha": round(float(r["area_ha"]), 1) if r["area_ha"] else None,
                 "geojson": _simplificar(area["geojson"]),
                 "buffer_geojson": r["buffer_geojson"], "buffer_km": BUFFER_KM},
        "anos": list(ANOS),
        "mapbiomas": {z: {str(a): _classes(r[f"mb_{z}_{a}"], a) for a in ANOS} for z in ("area", "buffer")},
        "transicoes": [{"de": int(a), "para": int(b), "ha": round(float(v), 1)}
                       for a, d in (r["transicoes"] or {}).items() for b, v in d.items() if v > 0],
        "gfc": {"area": _gfc(r["gfc_area"]), "buffer": _gfc(r["gfc_buffer"])},
        "linha": {z: {serie: {str(a): round(float(v), 1) for a, v in valores.items()}
                      for serie, valores in (r[f"linha_{z}"] or {}).items()}
                  for z in ("area", "buffer")},
        "procedencia": [
            {"nome": "MapBiomas", "nome_en": "MapBiomas",
             "dataset": f"MapBiomas Brasil, coleção {MAPBIOMAS_DEFAULT_COLLECTION}",
             "dataset_en": f"MapBiomas Brazil, collection {MAPBIOMAS_DEFAULT_COLLECTION}", "escala_m": 30},
            {"nome": "Hansen GFC", "nome_en": "Hansen GFC", "dataset": "UMD/hansen/global_forest_change", "escala_m": 30},
            {"nome": "Desmatamento e vegetação secundária", "nome_en": "Deforestation and secondary vegetation",
             "dataset": "MapBiomas DSV", "escala_m": 30},
            {"nome": "Cicatrizes de fogo", "nome_en": "Fire scars", "dataset": "MapBiomas Fogo",
             "dataset_en": "MapBiomas Fire", "escala_m": 30},
        ],
        "erros": erros,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return out


def _camadas() -> Dict[str, Any]:
    """Os mesmos tiles que o mapa do aplicativo usa (cache em ee_layers)."""
    ee = _ee()
    from ..config.config import HANSEN_GFC_DATASET, HANSEN_GFC_TREE_LOSS_VIS
    from .ee_layers import MAPBIOMAS_PALETTE, _cached_get_map_id
    from .ee_service_extended import get_ee_service

    mb = get_ee_service().get_mapbiomas()
    vis = {"min": 0, "max": len(MAPBIOMAS_PALETTE) - 1, "palette": MAPBIOMAS_PALETTE}
    out: Dict[str, Any] = {}
    for ano in (ANOS[0], ANOS[-1]):
        url = _cached_get_map_id(f"mapbiomas_{ano}", lambda a=ano: mb.select(f"classification_{a}"), vis)
        if url:
            out[f"mb_{ano}"] = {"url": url, "attribution": "MapBiomas", "opacity": 0.8}
    url = _cached_get_map_id(
        "hansen_gfc_lossyear",
        lambda: ee.Image(HANSEN_GFC_DATASET).select(["lossyear"]).updateMask(
            ee.Image(HANSEN_GFC_DATASET).select(["lossyear"]).gt(0)),
        HANSEN_GFC_TREE_LOSS_VIS)
    if url:
        out["hansen_perda"] = {"url": url, "attribution": "Hansen/UMD/Google/USGS/NASA", "opacity": 0.85,
                               "palette": HANSEN_GFC_TREE_LOSS_VIS.get("palette")}
    return out


def lote() -> Dict[str, Any]:
    """O lote de exemplo (``LOTE``) e um indicador por TI — vegetação nativa
    dentro e no buffer em 2025 — calculado pela mesma ``analyze_mapbiomas``
    que o lote roda."""
    ee = _ee()
    from . import buffer_utils as bu
    from .conservation_service import get_conservation_unit_service
    from .ee_service_extended import get_ee_service
    from .territory_service import get_territory_service

    tis, ucs = get_territory_service(), get_conservation_unit_service()
    chaves = tis.get_all_display_keys()
    escolhidas = [k for k in LOTE if k in chaves]
    infos = {k: tis.get_territory_info(k) for k in escolhidas}
    svc, ano = get_ee_service(), ANOS[-1]
    nativas = NATIVAS
    erros: Dict[str, str] = {}

    def uma(k: str) -> Dict[str, Any]:
        g = tis.get_ee_geometry(k)
        b = bu.create_external_buffer(g, BUFFER_KM)
        fora = svc.analyze_mapbiomas(b, ano)
        dentro = svc.analyze_mapbiomas(g, ano)
        def pct(df):
            if df is None or df.empty:
                return None
            tot = float(df["Area_ha"].sum())
            return round(100.0 * float(df[df["Class_ID"].isin(nativas)]["Area_ha"].sum()) / tot, 1) if tot else None
        return {"nome": k, "uf": infos[k].get("uf_sigla"), "etnia": infos[k].get("etnia"),
                "area_ha": round(float(infos[k].get("superficie_ha") or 0), 1),
                "homologada": tis.get_demarcation_dates(k).get("homologada"),
                "nativa_dentro_pct": pct(dentro), "nativa_buffer_pct": pct(fora),
                "geojson": _simplificar(tis.get_geojson_for_key(k), 0.0005)}

    with ThreadPoolExecutor(max_workers=len(escolhidas) or 1) as pool:
        futuros = {k: pool.submit(_seguro, k, (lambda k=k: uma(k)), erros) for k in escolhidas}
        linhas = [f.result() for f in futuros.values() if f.result()]

    return {
        "modo": "lote",
        "catalogo": {"terras_indigenas": len(chaves), "unidades_conservacao": len(ucs.get_all_display_keys()),
                     "uf": LOTE_UF},
        "ano": ano, "buffer_km": BUFFER_KM, "territorios": linhas,
        "erros": erros, "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def _arred(geom: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Coordenadas com 5 casas (~1 m): a geometria só é desenhada."""
    if not geom or "coordinates" not in geom:
        return geom

    def r(c):
        return [r(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]

    return {"type": geom["type"], "coordinates": r(geom["coordinates"])}


def instantaneo(modo: str) -> Dict[str, Any]:
    """O exemplo padrão de um modo, sem camadas e com geometrias leves — o
    conteúdo de ``PASTA_EXEMPLOS/<modo>.json``. Só a área de exemplo e a sua
    zona de 10 km (ou os contornos do lote), nada mais do catálogo."""
    if modo == "lote":
        dados = lote()
        for t in dados["territorios"]:
            t["geojson"] = _arred(t["geojson"])
        return dados
    dados = _calcular(modo, None)
    a = dados["area"]
    a["geojson"] = _arred(a["geojson"])
    if a.get("buffer_geojson"):
        a["buffer_geojson"] = _arred(_simplificar(a["buffer_geojson"], 0.002))
    return dados


def _exemplo_guardado(modo: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads((PASTA_EXEMPLOS / f"{modo}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def pacote(modo: str, area: Optional[str] = None) -> Dict[str, Any]:
    """O pacote de um modo, do cache quando possível."""
    if modo not in MODOS:
        raise AreaInvalida(f"Modo {modo!r} desconhecido; use um de {', '.join(MODOS)}.")
    if not area:
        guardado = _exemplo_guardado(modo)
        if guardado:
            if modo == "lote":
                return guardado
            return {**guardado, "camadas": _camadas(), "exemplo_padrao": True}
    chave = f"{modo}::{area or ''}"
    with _trava(chave):
        guardado = _cache.get(chave)
        if guardado and time.time() - guardado[0] < _TTL_S:
            dados = guardado[1]
        else:
            t0 = time.time()
            dados = lote() if modo == "lote" else _calcular(modo, area)
            logger.info("demonstração %s calculada em %.1f s", chave, time.time() - t0)
            if not dados["erros"]:
                _cache[chave] = (time.time(), dados)
    if modo == "lote":
        return dados
    return {**dados, "camadas": _camadas(), "exemplo_padrao": not area}
