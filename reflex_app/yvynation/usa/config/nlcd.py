"""Annual NLCD (USGS), the land-cover series of the Yvynation USA page.

One 30 m land-cover map per year, **1985–2025**, for the lower 48 (verified in
Earth Engine 2026-11-04: 41 images, band ``b1``, community catalog
``projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER``). Unlike Canada's
Annual Crop Inventory it is a true land-cover map with national coverage from the
first year, so there is no "starts late" or "stops at 58°N" caveat to carry.

Alaska is **not** in this series (its NLCD has only 2001, 2011 and 2016) and is
left out of this page for now; Hawaii and Puerto Rico are too. The page says so.

The module keeps the names the Canada page's ``nlcd`` module had (``band_for_year``,
``label``, ``color``, the group sets, ``STACK_PRIORITY``) so the history, chart and
export code reads the same in both countries. The standard NLCD legend and colours
(USGS/MRLC) are used as published.
"""

from __future__ import annotations

from typing import Dict, List

NLCD_DATASET = "projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER"
NLCD_BAND = "b1"

NLCD_YEAR_START = 1985
NLCD_YEAR_END = 2025
NLCD_YEARS: List[int] = list(range(NLCD_YEAR_START, NLCD_YEAR_END + 1))


def band_for_year(year: int) -> str:
    """Band name after stacking — see ``services/nlcd_history.py``."""
    return f"nlcd_{year}"


def all_bands() -> List[str]:
    return [band_for_year(y) for y in NLCD_YEARS]


NLCD_LABELS_EN: Dict[int, str] = {
    11: "Open water", 12: "Perennial ice/snow", 21: "Developed, open space",
    22: "Developed, low intensity", 23: "Developed, medium intensity",
    24: "Developed, high intensity", 31: "Barren land", 41: "Deciduous forest",
    42: "Evergreen forest", 43: "Mixed forest", 52: "Shrub/scrub",
    71: "Grassland/herbaceous", 81: "Pasture/hay", 82: "Cultivated crops",
    90: "Woody wetlands", 95: "Emergent herbaceous wetlands",
}

NLCD_LABELS_PT: Dict[int, str] = {
    11: "Água", 12: "Gelo e neve perenes", 21: "Área urbanizada, espaço aberto",
    22: "Área urbanizada, baixa densidade", 23: "Área urbanizada, média densidade",
    24: "Área urbanizada, alta densidade", 31: "Solo exposto",
    41: "Floresta decídua", 42: "Floresta perene", 43: "Floresta mista",
    52: "Arbustos", 71: "Campo herbáceo", 81: "Pastagem e feno", 82: "Lavouras",
    90: "Áreas úmidas arborizadas", 95: "Áreas úmidas herbáceas",
}

NLCD_LABELS: Dict[str, Dict[int, str]] = {"en": NLCD_LABELS_EN, "pt": NLCD_LABELS_PT}


def label(class_id: int, lang: str = "en") -> str:
    table = NLCD_LABELS.get(lang, NLCD_LABELS_EN)
    return table.get(class_id, f"Classe {class_id}" if lang == "pt" else f"Class {class_id}")


#: The official NLCD legend colours (MRLC). Prescribed, not colour-blind safe, so
#: the legend always pairs swatch with label.
NLCD_COLOR_MAP: Dict[int, str] = {
    11: "#466b9f", 12: "#d1def8", 21: "#dec5c5", 22: "#d99282", 23: "#eb0000",
    24: "#ab0000", 31: "#b3ac9f", 41: "#68ab5f", 42: "#1c5f2c", 43: "#b5c58f",
    52: "#ccb879", 71: "#dfdfc2", 81: "#dcd939", 82: "#ab6c28", 90: "#b8d9eb",
    95: "#6c9fb8",
}
NLCD_GAP_COLOR = "cccccc"

#: Dense 0..95 palette for ``getMapId`` (one entry per index; codes are sparse).
NLCD_PALETTE: List[str] = [
    NLCD_COLOR_MAP[i].lstrip("#") if i in NLCD_COLOR_MAP else NLCD_GAP_COLOR
    for i in range(96)
]
NLCD_VIS = {"min": 0, "max": 95, "palette": NLCD_PALETTE}


def color(class_id: int) -> str:
    return NLCD_COLOR_MAP.get(class_id, f"#{NLCD_GAP_COLOR}")


# --------------------------------------------------------------------------- #
# Class groups — same names as the Canada page's, so shared code keeps working.
# --------------------------------------------------------------------------- #
FOREST = frozenset({41, 42, 43})
WETLAND = frozenset({90, 95})
GRASS_SHRUB = frozenset({52, 71})
WATER = frozenset({11})
BARREN = frozenset({31, 12})
BURNT: frozenset = frozenset()      # NLCD has no burnt-area class (Canada's ACI does)
URBAN = frozenset({21, 22, 23, 24})
NO_DATA: frozenset = frozenset()
CROPLAND = frozenset({81, 82})

NATURAL_VEGETATION = FOREST | WETLAND | GRASS_SHRUB

STACK_PRIORITY: List[int] = (
    sorted(FOREST) + sorted(WETLAND) + sorted(GRASS_SHRUB) + sorted(BARREN)
)
