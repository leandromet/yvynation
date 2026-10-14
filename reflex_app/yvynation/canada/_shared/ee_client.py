"""Earth Engine for the Canada page — Yvynation's own initialisation.

Camposcope's Canada services call ``get_ee()``; here it delegates to
``utils.ee_service.initialize_earth_engine`` so both pages run under the same
project (ProtectedLandsYvynation-EE) and credentials.
"""

from __future__ import annotations

import ee

_initialized = False


def get_ee():
    """Return the ``ee`` module, initialising on first use."""
    global _initialized
    if not _initialized:
        from ...utils.ee_service import initialize_earth_engine
        _initialized = bool(initialize_earth_engine())
    return ee
