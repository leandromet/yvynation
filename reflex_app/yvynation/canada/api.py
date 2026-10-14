"""Backend HTTP routes for the Canada page.

Geometry travels as ordinary, cacheable HTTP GETs rather than through the
Reflex WebSocket (see camposcope/api/__init__.py, from which the ecozone
handler is ported): a province's protected-area outlines are megabytes that
every viewer of that province shares, and a state var would re-send them per
session and per reload.

Mounted on Yvynation's ``api_transformer`` Starlette app
(``utils/download_routes.py::download_app``), so they are matched before
Reflex's own routes.
"""

from __future__ import annotations

import gzip
import logging
import os
import re

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from .config import ecozones as ecozones_cfg
from .services import ecozones

logger = logging.getLogger(__name__)

_CACHE_CONTROL = "public, max-age=86400"
_CPCAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils",
                          "protected_areas_ca")
CPCAD_PATH = "/_cpcad/{province}.geojson"


async def _run_blocking(fn):
    import asyncio
    return await asyncio.get_running_loop().run_in_executor(None, fn)


def _gz_response(request: Request, payload: bytes) -> Response:
    headers = {"Cache-Control": _CACHE_CONTROL}
    if "gzip" in request.headers.get("accept-encoding", ""):
        headers["Content-Encoding"] = "gzip"
    else:
        payload = gzip.decompress(payload)
    headers["Content-Length"] = str(len(payload))
    return Response(content=payload, media_type="application/geo+json",
                    headers=headers)


async def _ecoframework_geojson(request: Request, level: str) -> Response:
    try:
        payload = await _run_blocking(lambda: ecozones.geojson_gzipped(level))
    except Exception as exc:  # noqa: BLE001
        logger.exception("%s GeoJSON could not be produced", level)
        return JSONResponse({"error": f"{level} unavailable", "detail": str(exc)},
                            status_code=503)
    return _gz_response(request, payload)


async def ecozones_geojson(request: Request) -> Response:
    return await _ecoframework_geojson(request, "ecozone")


async def ecoregions_geojson(request: Request) -> Response:
    return await _ecoframework_geojson(request, "ecoregion")


async def ecodistricts_geojson(request: Request) -> Response:
    return await _ecoframework_geojson(request, "ecodistrict")


async def cpcad_geojson(request: Request) -> Response:
    """One province's protected-area outlines (precomputed overview, already
    gzipped on disk by build_ca_protected_areas — served as-is)."""
    prov = request.path_params.get("province", "")
    if not re.fullmatch(r"[A-Z]{2}", prov):
        return JSONResponse({"error": "bad province"}, status_code=400)
    path = os.path.join(_CPCAD_DIR, f"{prov}.overview.geojson.gz")
    if not os.path.exists(path):
        return JSONResponse({"error": f"no data for {prov}"}, status_code=404)
    payload = await _run_blocking(lambda: open(path, "rb").read())
    return _gz_response(request, payload)


def routes() -> list:
    return [
        Route(ecozones_cfg.LEVELS["ecozone"].geojson_path, ecozones_geojson, methods=["GET"]),
        Route(ecozones_cfg.LEVELS["ecoregion"].geojson_path, ecoregions_geojson, methods=["GET"]),
        Route(ecozones_cfg.LEVELS["ecodistrict"].geojson_path, ecodistricts_geojson, methods=["GET"]),
        Route(CPCAD_PATH, cpcad_geojson, methods=["GET"]),
    ]
