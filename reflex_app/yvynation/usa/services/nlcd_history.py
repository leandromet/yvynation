"""Annual NLCD history for a protected area's zones (USA page).

The United States' counterpart to the Canada page's ACI history: the whole "N years ×
M zones" matrix is a **single** ``reduceRegions`` call. NLCD is an ``ImageCollection``
of one single-band image per year, so it is stacked first (each year's ``b1`` renamed
``nlcd_<year>``, then ``ee.Image.cat``). Annual NLCD covers the whole lower 48 for all
41 years, so unlike the Canada page there is no "empty is an answer" case.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from ...canada._shared.settings import EE_DEFAULT_SCALE_M, EE_MAX_PIXELS, EE_TILE_SCALE
from ...canada._shared.ee_client import get_ee
from ...canada._shared.provenance import Provenance
from ...canada._shared.zones import Zone
from ..config import nlcd
from ...canada.services.ee_zones import mean_pixel_area, px_area_by_zone, zone_feature_collection

logger = logging.getLogger(__name__)

NLCD_ASSET = nlcd.NLCD_DATASET


def nlcd_year_image(year: int):
    """One year's classification (band ``b1``)."""
    import ee

    col = ee.ImageCollection(NLCD_ASSET)
    return ee.Image(col.filterDate(f"{year}-01-01", f"{year + 1}-01-01").first())


def stacked_nlcd_image(years: List[int] | None = None):
    """The collection flattened into one multi-band image, one band per year."""
    import ee

    years = years or nlcd.NLCD_YEARS
    return ee.Image.cat([
        nlcd_year_image(y).select(nlcd.NLCD_BAND).rename(nlcd.band_for_year(y))
        for y in years
    ])


def _histogram_call(fc, image, scale: int, tile_scale: int):
    import ee
    return image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.frequencyHistogram(),
        scale=scale,
        tileScale=tile_scale,
    ).getInfo()


def land_cover_history(
    zones: Sequence[Zone],
    *,
    years: List[int] | None = None,
) -> Tuple[pd.DataFrame, Provenance]:
    """Land-cover area by year, class and zone.

    Returns a long-format frame — ``zone_key, zone_label, year, class_id,
    pixels, area_ha`` plus label/colour columns — and the provenance record that
    must travel with it. Long format rather than wide-by-year, for the same
    reason the Brazil module gives: 17 years × ~20 classes × N zones is a
    natural long table, and wide-by-year breaks the moment the year range
    changes.
    """
    if not zones:
        raise ValueError("No zones to analyse.")

    get_ee()

    years = years or nlcd.NLCD_YEARS
    bands = [nlcd.band_for_year(y) for y in years]
    fc = zone_feature_collection(zones)
    image = stacked_nlcd_image(years)

    prov = Provenance(
        name="usa_nlcd_history",
        dataset_id=NLCD_ASSET,
        bands=bands,
        scale_m=EE_DEFAULT_SCALE_M,
        reducer="frequencyHistogram",
        pixel_area_basis="mean ee.Image.pixelArea() per zone",
        max_pixels=EE_MAX_PIXELS,
        tile_scale=EE_TILE_SCALE,
        geometry=zones[0].geojson,          # the parcel; rings are in extra
        extra={
            "zones": [z.key for z in zones],
            "year_start": years[0],
            "year_end": years[-1],
            "coverage": "lower 48 states",
        },
    )

    scale, tile_scale = EE_DEFAULT_SCALE_M, EE_TILE_SCALE
    hist = areas = None

    # Retry ladder, same as the Brazil path. Never coarsen without recording it
    # via prov.degrade — a degraded result is usable and exportable, but it must
    # say so.
    for attempt, (s, ts) in enumerate([(scale, tile_scale), (scale, 8), (60, 8)]):
        try:
            # Both calls are independent, so issue them together: the pair costs
            # one round trip of wall-clock, not two.
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_hist = ex.submit(_histogram_call, fc, image, s, ts)
                f_area = ex.submit(mean_pixel_area, fc, s, ts, image)
                hist, areas = f_hist.result(), f_area.result()
            if attempt > 0:
                prov.degrade(
                    f"Retried at scale={s} m, tileScale={ts} after a failure at "
                    f"scale={scale} m, tileScale={tile_scale}.",
                    scale_m=s, tile_scale=ts,
                )
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("NLCD history attempt %s (scale=%s, tileScale=%s) "
                           "failed: %s", attempt + 1, s, ts, exc)
            if attempt == 2:
                raise

    px_area = px_area_by_zone(areas)
    zone_labels = {z.key: z.label for z in zones}

    records: List[Dict[str, Any]] = []
    single_band = len(bands) == 1
    for feat in hist["features"]:
        props = feat["properties"]
        zone_key = props["zone_key"]
        area_per_px_ha = px_area.get(zone_key, 900.0) / 10_000.0

        for key, histogram in props.items():
            if not isinstance(histogram, dict):
                continue
            # The same Earth Engine quirk the Brazil parser documents:
            # reduceRegions names its output per band when several are selected
            # but falls back to the reducer's own name for exactly one.
            if key.startswith("nlcd_"):
                year = int(key.rsplit("_", 1)[1])
            elif single_band and key == "histogram":
                year = years[0]
            else:
                continue
            for class_id, count in histogram.items():
                count = float(count)
                if count <= 0:
                    continue
                records.append({
                    "zone_key": zone_key,
                    "zone_label": zone_labels.get(zone_key, zone_key),
                    "year": year,
                    "class_id": int(float(class_id)),
                    "pixels": count,
                    "area_ha": count * area_per_px_ha,
                })

    df = pd.DataFrame.from_records(
        records,
        columns=["zone_key", "zone_label", "year", "class_id", "pixels", "area_ha"],
    )
    if not df.empty:
        df["class_en"] = df["class_id"].map(lambda c: nlcd.label(int(c), "en"))
        df["class_pt"] = df["class_id"].map(lambda c: nlcd.label(int(c), "pt"))
        df["class_fr"] = df["class_id"].map(lambda c: nlcd.label(int(c), "fr"))
        df["color"] = df["class_id"].map(lambda c: nlcd.color(int(c)))
        # Zones in the order they were passed (parcel first, rings outward),
        # not alphabetically — the order the UI reasons about them in.
        order = {z.key: i for i, z in enumerate(zones)}
        df["_zone_order"] = df["zone_key"].map(order)
        df = df.sort_values(
            ["_zone_order", "year", "area_ha"], ascending=[True, True, False]
        ).drop(columns="_zone_order").reset_index(drop=True)

    prov.extra["mean_pixel_area_m2"] = {k: round(v, 2) for k, v in px_area.items()}
    prov.extra["n_records"] = len(df)
    logger.info("NLCD history: %s records across %s zones", len(df), len(zones))
    return df, prov


def to_shares(df: pd.DataFrame, zone_key: str) -> pd.DataFrame:
    """Per-year percentage shares for one zone — what the stacked chart plots."""
    if df is None or df.empty or "zone_key" not in df.columns:
        return pd.DataFrame()
    sub = df[df["zone_key"] == zone_key].copy()
    if sub.empty:
        return sub
    totals = sub.groupby("year")["area_ha"].transform("sum")
    sub["area_pct"] = (sub["area_ha"] / totals * 100.0).fillna(0.0)
    return sub


__all__ = ["land_cover_history", "stacked_nlcd_image", "nlcd_year_image",
           "to_shares", "NLCD_ASSET"]
