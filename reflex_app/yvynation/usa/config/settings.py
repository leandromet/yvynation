"""USA-page settings (lower 48)."""

from __future__ import annotations

import os

#: Conterminous US bounding box: min_lon, min_lat, max_lon, max_lat. A coarse test; PAD-US
#: itself is the arbiter of whether a click is on a protected area.
USA_BBOX = (-125.0, 24.4, -66.8, 49.5)
MAP_CENTER = (39.5, -98.5)
MAP_ZOOM = 4
DEFAULT_LANGUAGE = os.environ.get("YVY_US_LANGUAGE", "en")

_ARC = "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services"
#: PAD-US as published on the USGS ArcGIS Online organisation: public FeatureServers, no key,
#: 2000 records per page, queried live — nothing is mirrored or preprocessed. Three sources:
#: ``fee`` (v4.1 fee managers: whole parks, forests, refuges, state/local parks), ``proclamation``
#: (v4.1: includes the tribal reservations and trust lands) and ``designation`` (the flattened
#: "national" service, used only for its Designation records: wilderness areas and the like).
#: The flattened service is NOT used for Fee: it carves overlapping designations out of the
#: parks (Yosemite National Park comes back as 16 000 ha, not 300 000).
PADUS_SOURCES = {
    "fee": f"{_ARC}/Fee_Managers_PADUS/FeatureServer/0",
    "proclamation": f"{_ARC}/Proclamation_and_Other_Planning_Boundaries_PADUS/FeatureServer/0",
    "designation": f"{_ARC}/PADUS_Protected_Areas_National/FeatureServer/0",
}
#: Overview tiles of PAD-US (v3.0, cached, XYZ) for orientation on the map.
PADUS_TILES = f"{_ARC}/PADUS3_0Manager_Type/MapServer/tile/{{z}}/{{y}}/{{x}}"
#: Generalisation applied to a boundary before it is sent to Earth Engine / the map (m).
PADUS_SIMPLIFY_M = 30
USER_AGENT = "yvynation/1.0 (contact: leandromet@gmail.com)"
