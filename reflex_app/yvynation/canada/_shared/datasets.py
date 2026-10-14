"""Dataset constants the Canada page shares with the suite — copied from
camposcope/config/datasets.py (only what canada/ imports)."""

from __future__ import annotations

from typing import Any, Dict

BASEMAPS: Dict[str, Dict[str, Any]] = {
    "google_hybrid": {
        "label_pt": "Google — Híbrido",
        "label_en": "Google — Hybrid",
        "url": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "attribution": "© Google",
        "max_native_zoom": 20,
    },
    "google_satellite": {
        "label_pt": "Google — Satélite",
        "label_en": "Google — Satellite",
        "url": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "attribution": "© Google",
        "max_native_zoom": 20,
    },
    "esri_imagery": {
        "label_pt": "Esri — Satélite",
        "label_en": "Esri — Imagery",
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attribution": "Tiles © Esri",
        "max_native_zoom": 19,
    },
    "osm": {
        "label_pt": "OpenStreetMap",
        "label_en": "OpenStreetMap",
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "© OpenStreetMap contributors",
        "max_native_zoom": 19,
    },
}

HANSEN_GFC = {
    "asset": "UMD/hansen/global_forest_change_2025_v1_13",
    "loss_year_start": 2001,
    "loss_year_end": 2024,          # lossyear band: 1..24 → 2001..2024
    "treecover_vis": {"min": 0, "max": 100,
                      "palette": ["ffffff", "d9f0a3", "78c679", "238443", "004529"]},
    "loss_color": "#d4271e",
    #: `gain` is a single UNDATED 2000–2012 layer. It cannot go on a timeline and
    #: must never be summed with loss (doc/04 §3).
    "gain_color": "#02d659",
    "attribution": "Hansen/UMD/Google/USGS/NASA — Global Forest Change",
}

AGB_YEARS = [2007, 2010, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]

AGB = {
    "asset_template": "ESA/CCI/Above_Ground_Biomass/V6_0/{year}",
    "dataset_id": "ESA/CCI/Above_Ground_Biomass/V6_0",
    #: The product's native resolution. Reducing at MapBiomas' 30 m adds no
    #: detail — EE just resamples a 100 m raster and bills for it.
    "scale_m": 100,
    "vis": {"min": 0, "max": 500, "palette": ["white", "green"]},
    "attribution": "ESA CCI Biomass v6.0 — Santoro & Cartus (2025), CC BY 4.0",
}
