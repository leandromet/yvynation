"""Canada-page settings.

Deliberately thin: everything about *Earth Engine* or *this deployment* —
project id, concurrency, tile cache, scale, ring radii, area-flag thresholds —
comes from ``canada/_shared/settings.py``. Only what is genuinely Canadian lives
here.

The ``CS_CA_`` prefix of the environment variables is inherited from
Camposcope's Canada page, which this package was ported from; it is kept so
that no existing deployment's variables change meaning.
"""

from __future__ import annotations

import os

from .._shared.settings import _int

# --------------------------------------------------------------------------- #
# Outbound HTTP
# --------------------------------------------------------------------------- #
# Camposcope's Canada page queries ParcelMap BC here; this page queries no
# parcels, so only the request settings survive, used by the ecozone fetch
# (``services/ecozones.py``, AAFC's ArcGIS service). The ``PMBC_`` names are
# kept so the ported module imports them unchanged.

#: Never leave these unset: requests' default is *no timeout*, which hangs a
#: Reflex background handler with no way out.
PMBC_TIMEOUT_CONNECT = _int("CS_CA_PMBC_TIMEOUT_CONNECT", 10)
PMBC_TIMEOUT_READ = _int("CS_CA_PMBC_TIMEOUT_READ", 60)

#: Public services run for everyone deserve an identifiable User-Agent — and the
#: right one: until 2026-10-14 this still said "Camposcope/0.1", so requests
#: from Yvynation identified themselves as the app they were ported from.
PMBC_USER_AGENT = os.environ.get(
    "CS_CA_PMBC_USER_AGENT",
    "Yvynation/2.0 (+https://github.com/leandromet/yvynation)",
)

# --------------------------------------------------------------------------- #
# Extent
# --------------------------------------------------------------------------- #
#: British Columbia, padded. west, south, east, north. Read only by
#: ``services/bc_lookup.py``, a module kept from the port that nothing imports.
BC_BBOX = (-139.2, 48.2, -113.9, 60.1)

#: Canada as a whole, padded. Read only by ``services/bc_lookup.py``; the page's
#: own "is this in Canada?" test uses ``utils/place_search.CANADA_BBOX``.
CANADA_BBOX = (-141.5, 41.0, -52.0, 83.5)

# --------------------------------------------------------------------------- #
# Map
# --------------------------------------------------------------------------- #
DEFAULT_BASEMAP = os.environ.get("CS_CA_BASEMAP", "google_hybrid")
#: Centred on BC's interior rather than its centroid: the centroid sits in a
#: mountain range nobody searches, and the populated south would be a sliver.
DEFAULT_CENTER = (53.7, -123.0)
DEFAULT_ZOOM = _int("CS_CA_DEFAULT_ZOOM", 5)

#: Initial framing as ``[[south, west], [north, east]]``.
BC_VIEW_BOUNDS = ((48.2, -139.2), (60.1, -113.9))

# --------------------------------------------------------------------------- #
# Language
# --------------------------------------------------------------------------- #
#: The Canada page opens in English; the Brazil page opens in Portuguese. An
#: explicit choice wins over both — the header link between the pages carries
#: ``?lang=`` and ``state/_ui.py`` honours it.
DEFAULT_LANGUAGE = os.environ.get("CS_CA_LANGUAGE", "en")

#: The Brazil page hardcodes its two-language check inline (``UIMixin.set_lang``
#: accepts only "pt"/"en" literally); this page names the set instead, since
#: ``_ui.py`` checks against it in two places and a literal in each risks the
#: two drifting apart.
SUPPORTED_LANGUAGES = ("en", "pt", "fr")

# --------------------------------------------------------------------------- #
# Geocoding
# --------------------------------------------------------------------------- #
#: Never widen this. The page covers British Columbia; a search that can wander
#: off it will. Nominatim has no province filter, so the country filter plus the
#: BC bbox check in ``services/geocode.py`` is what actually bounds it.
GEOCODER_COUNTRY_CODES = "ca"
