"""The territory kinds the analysis workspace can be opened on — one place to
ask "which service backs this kind?" and "is this a protected area?".

* ``indigenous``      — Brazilian Indigenous lands, FUNAI (TerritoryService).
* ``conservation``    — Brazilian conservation units, CNUC/MMA.
* ``conservation_ca`` — Canadian protected and conserved areas, CPCAD/ECCC
  (``protected_areas_ca*.gpkg.zip``, built by ``build_ca_protected_areas``).

There is deliberately **no Canadian Indigenous-lands kind.** Indigenous lands
data in Canada falls under OCAP (First Nations principles of Ownership,
Control, Access and Possession): its publication is not consent to be
analysed the way FUNAI's Brazilian data is, and the CPCAD build drops
Indigenous-governed and Indigenous-owned areas before anything is stored.
Adding such a kind is a partnership question, not a code change.
"""

from __future__ import annotations

KINDS = ("indigenous", "conservation", "conservation_ca")
CONSERVATION_KINDS = ("conservation", "conservation_ca")


def is_conservation(kind: str) -> bool:
    """A protected area (Brazilian UC or Canadian PA) rather than an
    Indigenous land — the branch most chart/report code cares about."""
    return kind in CONSERVATION_KINDS


def country_of(kind: str) -> str:
    return "Canada" if kind == "conservation_ca" else "Brazil"


def conservation_kind_for(country: str) -> str:
    return "conservation_ca" if country == "Canada" else "conservation"


def service_for(kind: str):
    """The GeoPackage service backing ``kind`` — all three share one API
    (display keys, GeoJSON, bounds, EE geometry, info)."""
    if kind == "conservation_ca":
        from .conservation_service import get_ca_protected_area_service
        return get_ca_protected_area_service()
    if kind == "conservation":
        from .conservation_service import get_conservation_unit_service
        return get_conservation_unit_service()
    from .territory_service import get_territory_service
    return get_territory_service()


__all__ = ["CONSERVATION_KINDS", "KINDS", "conservation_kind_for", "country_of",
           "is_conservation", "service_for"]
