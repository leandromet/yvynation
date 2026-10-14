"""Settings the Canada page shares with the suite (ported from
camposcope/config/settings.py — only the names canada/ reads)."""

from __future__ import annotations

import os
import pathlib
from typing import List


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


#: Where canada/ keeps run-time data (ecozone cache). The package directory,
#: not the app root: everything Canadian stays under canada/.
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

EE_DEFAULT_SCALE_M = _int("YVY_CA_EE_SCALE_M", 30)
EE_TILE_SCALE = _int("YVY_CA_EE_TILE_SCALE", 4)
EE_MAX_PIXELS = _int("YVY_CA_EE_MAX_PIXELS", 1_000_000_000)

TILE_CACHE_TTL_SECONDS = _int("YVY_CA_TILE_CACHE_TTL", 3600)
TILE_CACHE_MAX_ENTRIES = _int("YVY_CA_TILE_CACHE_MAX", 512)

#: Rings measured outward from the protected area's boundary.
RING_RADII_M: List[int] = [500, 2000, 5000]

HANSEN_TREECOVER_THRESHOLD = _int("YVY_CA_HANSEN_TREECOVER_THRESHOLD", 30)

#: A boundary whose computed area differs from the registered one by more
#: than both of these is flagged on the area card.
AREA_DELTA_FLAG_PCT = float(os.environ.get("YVY_CA_AREA_DELTA_FLAG_PCT", "2.0"))
AREA_DELTA_FLAG_HA = float(os.environ.get("YVY_CA_AREA_DELTA_FLAG_HA", "5.0"))
