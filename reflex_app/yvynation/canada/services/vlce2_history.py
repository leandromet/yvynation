"""NTEMS VLCE2 land-cover history, 1984–2022, by zone.

The AAFC crop inventory (``aci_history.py``) is an *agricultural* product: it
stops around 54–58°N and starts nationally only in 2011, so for most protected
areas in BC's north and mountains it is empty. VLCE2 (Hermosilla et al.,
Canada's National Terrestrial Ecosystem Monitoring System) is the land-cover
history that does answer there: annual, 30 m, every forested ecozone, 39 years.

Same single-round-trip shape as the ACI history: the collection is flattened
into one multi-band image (one band per year) and one ``frequencyHistogram``
``reduceRegions`` covers every year × every zone. Images are addressed by
``system:index`` (``config/vlce2.py::image_id``) — ``filterDate`` on this
collection silently matches nothing.

Outside VLCE2's forested-ecozone footprint (the prairie and arctic) pixels are
masked, so the history is empty there — the AAFC tab covers the prairie.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd

from .._shared.ee_client import get_ee
from .._shared.provenance import Provenance
from .._shared.settings import EE_DEFAULT_SCALE_M, EE_MAX_PIXELS, EE_TILE_SCALE
from .._shared.zones import Zone
from ..config import vlce2 as cfg
from .ee_zones import mean_pixel_area, px_area_by_zone, zone_feature_collection

logger = logging.getLogger(__name__)


def band_for_year(year: int) -> str:
    return f"vlce2_{year}"


def stacked_vlce2_image(years: List[int]):
    """VLCE2 as one image, one band per year."""
    import ee

    col = ee.ImageCollection(cfg.VLCE2_DATASET)
    bands = [
        ee.Image(col.filter(ee.Filter.eq("system:index", cfg.image_id(y))).first())
        .select([cfg.VLCE2_BAND]).rename(band_for_year(y))
        for y in years
    ]
    return ee.Image.cat(bands)


def _histogram_call(fc, image, scale: int, tile_scale: int):
    import ee
    return image.reduceRegions(collection=fc, reducer=ee.Reducer.frequencyHistogram(),
                               scale=scale, tileScale=tile_scale).getInfo()


def land_cover_history(zones: Sequence[Zone], *, years: List[int] | None = None
                       ) -> Tuple[pd.DataFrame, Provenance]:
    """Area by year, class and zone — the ACI history's long format."""
    if not zones:
        raise ValueError("No zones to analyse.")
    get_ee()
    years = years or cfg.VLCE2_YEARS
    fc = zone_feature_collection(zones)
    image = stacked_vlce2_image(years)

    prov = Provenance(
        name="ntems_vlce2_history",
        dataset_id=cfg.VLCE2_DATASET,
        bands=[band_for_year(y) for y in years],
        scale_m=EE_DEFAULT_SCALE_M,
        reducer="frequencyHistogram",
        pixel_area_basis="mean ee.Image.pixelArea() per zone",
        max_pixels=EE_MAX_PIXELS,
        tile_scale=EE_TILE_SCALE,
        geometry=zones[0].geojson,
        extra={"zones": [z.key for z in zones], "year_start": years[0],
               "year_end": years[-1]},
    )

    scale, tile_scale = EE_DEFAULT_SCALE_M, EE_TILE_SCALE
    hist = areas = None
    # 39 bands over a park of hundreds of thousands of hectares is a heavy
    # reduction; the ladder ends coarser than the ACI's. Any rung past the
    # first is recorded as a degradation, never silently.
    ladder = [(scale, tile_scale), (scale, 8), (60, 8), (120, 16)]
    for attempt, (s, ts) in enumerate(ladder):
        try:
            with ThreadPoolExecutor(max_workers=2) as ex:
                f_hist = ex.submit(_histogram_call, fc, image, s, ts)
                f_area = ex.submit(mean_pixel_area, fc, s, ts)
                hist, areas = f_hist.result(), f_area.result()
            if attempt > 0:
                prov.degrade(f"Retried at scale={s} m, tileScale={ts} after a "
                             f"failure at scale={scale} m.", scale_m=s, tile_scale=ts)
            break
        except Exception as exc:  # noqa: BLE001
            logger.warning("VLCE2 history attempt %s (scale=%s) failed: %s",
                           attempt + 1, s, exc)
            if attempt == len(ladder) - 1:
                raise

    px_area = px_area_by_zone(areas)
    labels = {z.key: z.label for z in zones}
    records: List[Dict[str, Any]] = []
    single = len(years) == 1
    for feat in hist["features"]:
        props = feat["properties"]
        zk = props["zone_key"]
        ha_per_px = px_area.get(zk, 900.0) / 10_000.0
        for key, histogram in props.items():
            if not isinstance(histogram, dict):
                continue
            if key.startswith("vlce2_"):
                year = int(key.rsplit("_", 1)[1])
            elif single and key == "histogram":
                year = years[0]
            else:
                continue
            for class_id, count in histogram.items():
                count = float(count)
                cid = int(float(class_id))
                # 0 is VLCE2's "no data / unclassified" — not a land cover.
                if count <= 0 or cid == 0:
                    continue
                records.append({"zone_key": zk, "zone_label": labels.get(zk, zk),
                                "year": year, "class_id": cid, "pixels": count,
                                "area_ha": count * ha_per_px})

    df = pd.DataFrame.from_records(
        records, columns=["zone_key", "zone_label", "year", "class_id", "pixels", "area_ha"])
    if not df.empty:
        df["class_en"] = df["class_id"].map(lambda c: cfg.label(int(c), "en"))
        df["class_pt"] = df["class_id"].map(lambda c: cfg.label(int(c), "pt"))
        df["class_fr"] = df["class_id"].map(lambda c: cfg.label(int(c), "fr"))
        df["color"] = df["class_id"].map(lambda c: cfg.color(int(c)))
        order = {z.key: i for i, z in enumerate(zones)}
        df["_o"] = df["zone_key"].map(order)
        df = df.sort_values(["_o", "year", "area_ha"], ascending=[True, True, False]
                            ).drop(columns="_o").reset_index(drop=True)
    else:
        prov.extra["empty_reason"] = (
            "No VLCE2 pixels over these zones — outside the forested ecozones "
            "NTEMS maps (prairie, arctic).")
    prov.extra["n_records"] = len(df)
    logger.info("VLCE2 history: %s records across %s zones", len(df), len(zones))
    return df, prov


__all__ = ["land_cover_history", "stacked_vlce2_image", "band_for_year"]
