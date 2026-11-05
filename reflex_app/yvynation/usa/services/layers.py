"""Layer specs for the USA map: the shared XYZ basemaps, Annual NLCD and Hansen change."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ...canada._shared.layers import basemap_spec  # noqa: F401  (re-exported unchanged)
from ...canada._shared.tiles import get_tile_url
from ...canada.services.layers import hansen_change_spec, landsat_basemap_spec  # noqa: F401
from ..config import nlcd

logger = logging.getLogger(__name__)

NLCD_ATTRIBUTION = "USGS — Annual National Land Cover Database (Collection 1 v2)"


def nlcd_year_spec(year: int, *, opacity: float = 0.75, z_index: int = 10
                   ) -> Optional[Dict[str, Any]]:
    """Annual NLCD for one year."""
    if year not in nlcd.NLCD_YEARS:
        logger.warning("NLCD year %s outside %s–%s", year, nlcd.NLCD_YEAR_START, nlcd.NLCD_YEAR_END)
        return None
    from .nlcd_history import nlcd_year_image

    key = f"us:nlcd:{year}"
    try:
        url = get_tile_url(key, lambda: nlcd_year_image(year).select(nlcd.NLCD_BAND), nlcd.NLCD_VIS)
    except Exception as exc:                      # noqa: BLE001
        logger.warning("Layer %s failed: %s", key, exc)
        return None
    if url is None:
        return None
    return {"id": key, "url": url, "opacity": opacity, "z_index": z_index,
            "attribution": f"{NLCD_ATTRIBUTION} {year}", "max_native_zoom": 15}
