"""Backend route for the scrolling demonstrations (``/demonstracao/<modo>``).

The pages carry no numbers of their own: they fetch
``/_demonstracao/yvynation.json?modo=…[&area=…]`` from here, built by
``utils/demonstracao.py`` out of the same analysis functions the app's pages
call. Plain HTTP rather than the WebSocket, like the Canada geometry routes
(``canada/api.py``): the package is identical for every visitor.

Mounted on the ``api_transformer`` Starlette app
(``utils/download_routes.py::download_app``), so it is matched before Reflex.
"""

from __future__ import annotations

import logging

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from ..canada.services import demonstracao as demonstracao_ca
from ..utils import demonstracao

logger = logging.getLogger(__name__)


async def _run_blocking(fn):
    import asyncio

    return await asyncio.get_running_loop().run_in_executor(None, fn)


async def demonstracao_json(request: Request) -> Response:
    """``?modo=`` (desenho, terra-indigena, unidade-conservacao, lote) and,
    for the two catalogue modes, ``?area=<display key>``. An unknown mode or
    area answers 400 with a message the page shows as-is."""
    modo = request.query_params.get("modo") or "terra-indigena"
    area = request.query_params.get("area") or None
    try:
        payload = await _run_blocking(lambda: demonstracao.pacote(modo, area))
    except demonstracao.AreaInvalida as exc:
        return JSONResponse({"error": "área inválida", "detail": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Demonstração não pôde ser montada")
        return JSONResponse({"error": "demonstração indisponível", "detail": str(exc)},
                            status_code=503)
    return JSONResponse(payload, headers={"Cache-Control": "public, max-age=600"})


async def demonstracao_ca_json(request: Request) -> Response:
    """The Canada conservation walkthrough (Okanagan Mountain Park); ``?area=``
    swaps in another BC area by its CPCAD name."""
    area = request.query_params.get("area") or None
    try:
        payload = await _run_blocking(lambda: demonstracao_ca.pacote(area))
    except demonstracao_ca.AreaInvalida as exc:
        return JSONResponse({"error": "unknown area", "detail": str(exc)}, status_code=400)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Canada walkthrough could not be built")
        return JSONResponse({"error": "walkthrough unavailable", "detail": str(exc)}, status_code=503)
    return JSONResponse(payload, headers={"Cache-Control": "public, max-age=600"})


def routes() -> list:
    return [Route(demonstracao.ROTA, demonstracao_json, methods=["GET"]),
            Route(demonstracao_ca.ROTA, demonstracao_ca_json, methods=["GET"])]
