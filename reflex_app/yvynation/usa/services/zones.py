"""Protected-area polygon → the zones every analysis consumes (USA page).

A port of the Canada page's ``services/zones.py``. The one substantive change is the
equal-area projection: areas are measured in **NAD83 / Conus Albers (EPSG:5070)**, the
standard equal-area projection for the lower 48 (and the grid Annual NLCD itself is
published on), so the area computed here and the pixel counts agree on the same surface.

Everything else is unchanged: rings measured **outward from the boundary** rather than
from a centroid, buffering in UTM so "500 m from the boundary" is 500 m in every
direction while areas are measured in the equal-area CRS, true disjoint rings that can
be summed without double-counting, ``buffer(0)`` repair of an invalid polygon.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pyproj import CRS, Transformer
from shapely.geometry import Point, box, mapping, shape
from shapely.ops import transform as shapely_transform

from ...canada._shared.settings import RING_RADII_M
# Zone itself is imported, not redefined: every ported analysis service takes a
# ``Zone`` and the two pages must agree on what one is, or a shared helper
# silently stops type-checking.
from ...canada._shared.zones import Zone

logger = logging.getLogger(__name__)

WGS84 = CRS.from_epsg(4326)

#: NAD83 / Conus Albers: the lower 48's standard equal-area projection.
CONUS_ALBERS = CRS.from_epsg(5070)


#: PAD-US publishes ``GIS_Acres`` computed by the steward, not by us, so small
#: disagreements are routine; flag only a clear difference.
AREA_DELTA_FLAG_PCT_US = 2.0
AREA_DELTA_FLAG_HA_US = 5.0


# --------------------------------------------------------------------------- #
# Projection
# --------------------------------------------------------------------------- #
def _utm_crs_for(lon: float, lat: float) -> CRS:
    """The UTM zone containing this point.

    Buffering happens in UTM rather than in BC Albers because a buffer must
    preserve *distance*; areas are then measured in the equal-area CRS, which
    preserves the other thing. BC spans UTM zones 7 through 11, so this genuinely
    varies across the province rather than being a formality.
    """
    zone = int((lon + 180) // 6) + 1
    epsg = (32600 if lat >= 0 else 32700) + zone
    return CRS.from_epsg(epsg)


def _transformer(src: CRS, dst: CRS) -> Transformer:
    return Transformer.from_crs(src, dst, always_xy=True)


def _reproject(geom, src: CRS, dst: CRS):
    return shapely_transform(_transformer(src, dst).transform, geom)


def area_ha(geojson: Dict[str, Any]) -> float:
    """Geometric area in hectares, in BC Albers.

    This is the number compared against the fabric's published
    ``FEATURE_AREA_SQM``. It never replaces it.
    """
    geom = shape(geojson)
    projected = _reproject(geom, WGS84, CONUS_ALBERS)
    return projected.area / 10_000.0


def centroid_lat_lon(geojson: Dict[str, Any]) -> Tuple[float, float]:
    """The analysis area's own centroid, in WGS84 — no reprojection needed,
    the source geometry already is WGS84.

    A plain planar centroid, not an area-weighted geodesic one: for a
    sidebar reference point on parcels and parks up to a few thousand
    hectares, the difference is not worth the added dependency. It reads
    ``(lat, lon)`` — the same order every other coordinate in this app uses.
    """
    c = shape(geojson).centroid
    return c.y, c.x


# --------------------------------------------------------------------------- #
# Area reconciliation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class AreaCheck:
    """Published vs. computed, and whether the gap is worth showing."""

    registered_ha: float
    computed_ha: float

    @property
    def delta_ha(self) -> float:
        return self.computed_ha - self.registered_ha

    @property
    def delta_pct(self) -> float:
        if not self.registered_ha:
            return 0.0
        return 100.0 * self.delta_ha / self.registered_ha

    @property
    def flagged(self) -> bool:
        """Above 0.5 % *or* 0.05 ha, whichever is larger."""
        threshold_ha = max(
            AREA_DELTA_FLAG_HA_US,
            abs(self.registered_ha) * AREA_DELTA_FLAG_PCT_US / 100.0,
        )
        return abs(self.delta_ha) > threshold_ha


def check_area(registered_ha: float, geojson: Dict[str, Any]) -> AreaCheck:
    return AreaCheck(registered_ha=float(registered_ha),
                     computed_ha=area_ha(geojson))


# --------------------------------------------------------------------------- #
# Zones
# --------------------------------------------------------------------------- #
def _ring_label(inner_m: int, outer_m: int, lang: str = "en") -> str:
    """``"0 – 500 m"``, ``"500 m – 2 km"``.

    Distances are near language-neutral, but the decimal separator is not: a
    Portuguese reader expects ``1,5 km`` and an English one ``1.5 km``. The
    Brazil module hardcodes the comma; this takes the language, because on this
    page English is the default and a comma would read as a thousands
    separator.
    """
    def fmt(m: int) -> str:
        if m < 1000:
            return f"{m} m"
        text = f"{m / 1000:g} km"
        return text.replace(".", ",") if lang in ("pt", "fr") else text

    return f"{fmt(inner_m)} – {fmt(outer_m)}" if inner_m else f"0 – {fmt(outer_m)}"


def _ring_key(outer_m: int) -> str:
    return f"ring_{outer_m}m" if outer_m < 1000 else f"ring_{outer_m // 1000}km"


#: The zone key of the parcel itself. ``"parcela"`` rather than the Brazil
#: page's ``"imovel"`` — every ported service keys zones by string, and two
#: pages sharing a key namespace would make a cached row from one legible to
#: the other, which it is not.
PARCEL_ZONE_KEY = "parcela"


def synthetic_square_geojson(lat: float, lon: float,
                             area_ha: float = 500.0) -> Dict[str, Any]:
    """A square of exactly ``area_ha``, centred on ``(lat, lon)``, north-aligned.

    The fallback analysis area for a click that lands on neither a parcel nor
    a protected area — most of Canada, since ParcelMap BC is provincial and
    even inside BC most land is unsurveyed Crown land. Rather than refuse the
    click (there is real land-cover, forest and biomass signal to show, the
    same as everywhere else in the country) or silently invent a boundary that
    looks authoritative, this hands back an explicitly synthetic square: round
    in area, obviously not a legal parcel, centred exactly where the user
    clicked.

    Built in the point's own local UTM zone so "500 ha" means 500 ha there —
    same reasoning ``build_zones`` applies to buffering, and the same zone
    lookup it uses. North-aligned rather than rotated to any real boundary,
    because there is no boundary here to align to; a plain square is the
    honest shape for "an area of this size around this point," not an
    attempt to look like a survey.
    """
    side_m = (area_ha * 10_000.0) ** 0.5
    half = side_m / 2.0

    utm = _utm_crs_for(lon, lat)
    to_utm = _transformer(WGS84, utm).transform
    to_wgs = _transformer(utm, WGS84).transform

    center_utm = shapely_transform(to_utm, Point(lon, lat))
    cx, cy = center_utm.x, center_utm.y
    square_utm = box(cx - half, cy - half, cx + half, cy + half)
    square_wgs = shapely_transform(to_wgs, square_utm)
    return mapping(square_wgs)


def build_zones(
    parcel_geojson: Dict[str, Any],
    *,
    radii_m: Sequence[int] = tuple(RING_RADII_M),
    parcel_label: str = "Parcel",
    lang: str = "en",
) -> List[Zone]:
    """The parcel, then one true ring per radius."""
    geom = shape(parcel_geojson)
    if geom.is_empty:
        raise ValueError("Parcel geometry is empty.")
    if not geom.is_valid:
        # A fabric polygon should be clean, unlike a self-declared CAR polygon —
        # but a multipart parcel with a shared vertex can still fail shapely's
        # validity test. buffer(0) is the standard repair and is preferable to
        # refusing to analyse the parcel; it is also the most likely reason the
        # area check below would flag, which is why the repair is logged.
        logger.warning("Parcel geometry invalid; repairing with buffer(0)")
        geom = geom.buffer(0)

    centroid = geom.centroid
    utm = _utm_crs_for(centroid.x, centroid.y)
    to_utm = _transformer(WGS84, utm).transform
    to_wgs = _transformer(utm, WGS84).transform

    geom_utm = shapely_transform(to_utm, geom)

    zones: List[Zone] = [
        Zone(
            key=PARCEL_ZONE_KEY,
            label=parcel_label,
            kind="property",
            geojson=mapping(geom),
            area_ha=area_ha(parcel_geojson),
        )
    ]

    ordered = sorted(int(r) for r in radii_m)
    previous = geom_utm
    for index, radius in enumerate(ordered):
        grown = geom_utm.buffer(radius)
        ring_utm = grown.difference(previous)
        previous = grown
        if ring_utm.is_empty:
            continue
        ring_wgs = shapely_transform(to_wgs, ring_utm)
        ring_geojson = mapping(ring_wgs)
        inner = 0 if index == 0 else ordered[index - 1]
        zones.append(
            Zone(
                key=_ring_key(radius),
                label=_ring_label(inner, radius, lang),
                kind="ring",
                geojson=ring_geojson,
                area_ha=area_ha(ring_geojson),
                radius_m=radius,
            )
        )

    return zones


# --------------------------------------------------------------------------- #
# Overlaps
# --------------------------------------------------------------------------- #
#: A shared edge between two surveyed parcels produces a sliver of intersection
#: from coordinate rounding alone. On the Brazil page any non-zero overlap is
#: worth listing because it means two people claimed the same ground; here it
#: usually means two parcels are neighbours. Anything under this is dropped as
#: topology noise rather than reported as a finding.
MIN_OVERLAP_HA = 0.01


def overlap_areas(
    parcel_geojson: Dict[str, Any],
    others: Sequence[Tuple[str, Optional[Dict[str, Any]]]],
) -> List[Dict[str, Any]]:
    """How much of this parcel each neighbouring parcel actually covers.

    Returns only genuine area overlaps, largest first — edge-touching neighbours
    and rounding slivers are dropped (see :data:`MIN_OVERLAP_HA`). What survives
    is worth showing precisely because a surveyed fabric is not supposed to
    produce it: in practice it is an air-space or strata parcel stacked over the
    same ground, which is exactly what the parcel card should say.
    """
    base = shape(parcel_geojson)
    if not base.is_valid:
        base = base.buffer(0)
    base_ha = area_ha(parcel_geojson)

    rows: List[Dict[str, Any]] = []
    for identifier, other_geojson in others:
        if not other_geojson:
            continue
        other = shape(other_geojson)
        if not other.is_valid:
            other = other.buffer(0)
        inter = base.intersection(other)
        if inter.is_empty or inter.area == 0:
            continue
        inter_ha = area_ha(mapping(inter))
        if inter_ha < MIN_OVERLAP_HA:
            continue
        rows.append({
            "identifier": identifier,
            "overlap_ha": round(inter_ha, 4),
            "overlap_pct_of_parcel": (round(100.0 * inter_ha / base_ha, 2)
                                      if base_ha else 0.0),
        })

    rows.sort(key=lambda r: r["overlap_ha"], reverse=True)
    return rows


__all__ = [
    "Zone", "AreaCheck", "PARCEL_ZONE_KEY",
    "build_zones", "area_ha", "check_area", "overlap_areas",
    "synthetic_square_geojson", "centroid_lat_lon",
    "CONUS_ALBERS", "MIN_OVERLAP_HA",
]
