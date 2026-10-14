"""Plain XYZ basemap specs (camposcope/services/layers.py::basemap_spec)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from . import datasets as ds

logger = logging.getLogger(__name__)


def basemap_spec(key: str, *, z_index: int = 0) -> Optional[Dict[str, Any]]:
    """Plain XYZ basemap — infallible, synchronous."""
    conf = ds.BASEMAPS.get(key)
    if conf is None:
        logger.warning("Unknown XYZ basemap %r", key)
        return None
    return {
        "id": f"basemap:{key}",
        "url": conf["url"],
        "opacity": 1.0,
        "attribution": conf["attribution"],
        "z_index": z_index,
        "max_native_zoom": conf.get("max_native_zoom", 19),
    }
