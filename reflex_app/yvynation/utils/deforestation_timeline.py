"""
Yearly time-series collector for the deforestation/regrowth/fire timeline
analysis. Returns one dict per indicator with shape ``{year: area_ha}``.

Each indicator is computed with a single ``reduceRegion`` call by stacking
all year bands into a multi-band image — total EE round-trips per
territory stay low (≤ 4 + one cheap ``bandNames`` probe per asset, cached).

Indicators (all aggregated as area in hectares per calendar year):
  * ``hansen_loss``        — Hansen GFC ``lossyear`` band, per-year area.
  * ``mb_defor_primary``   — MapBiomas Coll. 10.1 deforestation/secondary
                             dataset. Two value semantics are auto-detected:
                             "year_value" (single band, pixel value = year of
                             event) or "class_value" (per-year band whose
                             pixel is class code 100).
  * ``mb_secondary_growth``— same dataset, class 200 / regrowth-year band.
  * ``mb_fire_scar``       — MapBiomas Fire Coll. 4 annual burned area
                             (any non-zero pixel in the per-year band).

All return values are dicts ``{int_year: float_ha}``; years with no
contribution are present with value ``0.0`` so consumers can iterate the
full requested range without ``None`` handling.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Hansen GFC — already has per-year breakdown in the existing gfc_result.
# ---------------------------------------------------------------------------

def hansen_loss_series(
    gfc_result: Optional[Dict],
    year_start: int,
    year_end: int,
) -> Dict[int, float]:
    """Build ``{year: loss_ha}`` from an existing Hansen GFC result.

    Hansen ``Year_Code`` values map to years as ``2000 + code`` (per the v1.13
    asset). ``Year_Code == 0`` means "no loss" and is excluded.
    """
    out: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    if not gfc_result:
        logger.warning(
            f"hansen_loss_series: gfc_result is None or empty; returning all zeros for {year_start}-{year_end}"
        )
        return out
    
    tree_loss_data = gfc_result.get("tree_loss_data", []) or []
    logger.info(
        f"hansen_loss_series: processing {len(tree_loss_data)} loss records "
        f"for year range {year_start}-{year_end}"
    )
    
    for rec in tree_loss_data:
        try:
            code = int(rec.get("Year_Code", 0))
        except (TypeError, ValueError):
            continue
        if code <= 0:
            continue
        y = 2000 + code
        if year_start <= y <= year_end:
            try:
                area = float(rec.get("Area_ha", 0.0) or 0.0)
                out[y] = out.get(y, 0.0) + area
                logger.debug(f"  Year {y}: +{area:.2f} ha")
            except (TypeError, ValueError):
                continue
    
    non_zero_count = sum(1 for v in out.values() if v > 0.0)
    logger.info(
        f"hansen_loss_series: completed with {non_zero_count}/{len(out)} years having data"
    )
    return out


# ---------------------------------------------------------------------------
# Stacked reduceRegion helper
# ---------------------------------------------------------------------------

def _reduce_stacked(bands, ee_geometry, scale: int = 30) -> Dict[str, float]:
    """One ``reduceRegion(Reducer.sum())`` over a list of single-band images.

    Returns the raw EE result dict (``{band_name: float_or_None}``). All
    bands must already be in units of hectares per pixel (see callers).
    """
    if not bands:
        logger.warning("_reduce_stacked: no bands provided")
        return {}
    try:
        import ee
    except Exception:
        logger.error("_reduce_stacked: failed to import ee")
        return {}
    try:
        logger.debug(f"_reduce_stacked: stacking {len(bands)} bands for reduceRegion")
        stacked = ee.Image.cat(bands)
        result = stacked.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=ee_geometry,
            scale=scale,
            maxPixels=int(1e10),
            bestEffort=True,
        ).getInfo() or {}
        logger.debug(f"_reduce_stacked: EE returned {len(result)} values")
    except Exception as exc:
        logger.warning(f"_reduce_stacked: reduceRegion failed: {exc}")
        return {}
    # Normalise None → 0.0 so consumers don't have to care.
    result_norm = {k: float(v or 0.0) for k, v in result.items()}
    non_zero = sum(1 for v in result_norm.values() if v > 0.0)
    logger.debug(f"_reduce_stacked: {non_zero}/{len(result_norm)} values non-zero after normalize")
    return result_norm


# ---------------------------------------------------------------------------
# Per-indicator collectors (probe-driven)
# ---------------------------------------------------------------------------

# Class codes used when the asset has per-year class-coded bands.
# MapBiomas Deforestation & Secondary Vegetation Collection 10.1
# (per the official MapBiomas spec — confirmed by upstream JS palette):
#   0 = Other / Não aplicável
#   1 = Anthropic / Antrópico (stable)
#   2 = Primary Vegetation / Vegetação Primária (stable)
#   3 = Secondary Vegetation / Vegetação Secundária (stable)
#   4 = Deforestation in Primary Vegetation        ← the per-year event we want
#   5 = Secondary Vegetation Regrowth (event year) ← the per-year event we want
#   6 = Deforestation in Secondary Vegetation
#   7 = Not applied / Ruído
#
# IMPORTANT: classes 2 and 3 are the *stable* primary and secondary states —
# their per-year pixel count is roughly constant over time and does NOT
# represent annual deforestation or regrowth. The yearly change-events are
# classes 4 and 5; that's what we sum.
_MB_CLASS_PRIMARY_DEFOR = 4        # Deforestation in Primary Vegetation
_MB_CLASS_SECONDARY_REGROWTH = 5   # Secondary Vegetation Regrowth (event year)


def _series_year_value(
    ee_geometry, asset_id: str, band_name: str,
    year_start: int, year_end: int,
) -> Dict[int, float]:
    """Single band, pixel value = year. ``{y: ha where band == y}``."""
    out: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    try:
        import ee
    except Exception:
        return out
    try:
        src = ee.Image(asset_id).select(band_name)
        px_area_ha = ee.Image.pixelArea().divide(10_000)
        masked = []
        for y in range(year_start, year_end + 1):
            masked.append(src.eq(y).multiply(px_area_ha).rename(f"y_{y}"))
        result = _reduce_stacked(masked, ee_geometry)
        for key, val in result.items():
            if not key.startswith("y_"):
                continue
            try:
                y = int(key[2:])
                out[y] = float(val or 0.0)
            except (ValueError, TypeError):
                continue
    except Exception as exc:
        logger.warning(
            f"year-value collector failed (asset={asset_id}, band={band_name}): {exc}"
        )
    return out


def _series_class_value(
    ee_geometry, asset_id: str, band_template: str, target_class: int,
    year_start: int, year_end: int,
) -> Dict[int, float]:
    """Per-year band, pixel value = class code. Mask ``== target_class`` and sum."""
    out: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    try:
        import ee
    except Exception:
        logger.error("_series_class_value: failed to import ee")
        return out
    try:
        logger.info(
            f"_series_class_value: starting for asset={asset_id}, "
            f"template={band_template}, class={target_class}, years={year_start}-{year_end}"
        )
        from ..config.config import _list_aux_bands
        available_bands = set(_list_aux_bands(asset_id))
        asset = ee.Image(asset_id)
        px_area_ha = ee.Image.pixelArea().divide(10_000)
        masked = []
        bands_found = 0
        bands_missing = 0
        for y in range(year_start, year_end + 1):
            band_name = band_template.format(year=y)
            # EE .select() is lazy — invalid bands only fail at getInfo() time,
            # corrupting the whole stacked reduceRegion. Check upfront.
            if band_name not in available_bands:
                bands_missing += 1
                logger.debug(f"  Band not in asset: {band_name}")
                continue
            src = asset.select(band_name)
            # Count how many pixels have our target class
            class_mask = src.eq(target_class)
            masked_band = class_mask.multiply(px_area_ha).rename(f"y_{y}")
            masked.append(masked_band)
            bands_found += 1
            logger.debug(f"  Band found: {band_name} (will mask for class={target_class})")
        logger.info(f"_series_class_value: found {bands_found} bands, missing {bands_missing}")
        if not masked:
            logger.warning(f"_series_class_value: no bands matched, returning all zeros")
            return out
        logger.debug(f"_series_class_value: stacking {len(masked)} class-masked bands for reduceRegion")
        result = _reduce_stacked(masked, ee_geometry)
        logger.debug(f"_series_class_value: reduceRegion returned {len(result)} results")
        
        # Log which years have non-zero results (helps diagnose class code issues)
        sample_year_for_stats = year_start
        if sample_year_for_stats in result or f"y_{sample_year_for_stats}" in result:
            sample_key = f"y_{sample_year_for_stats}"
            if sample_key in result:
                sample_val = result[sample_key]
                logger.info(
                    f"_series_class_value: sample {sample_year_for_stats} → {sample_val} ha "
                    f"(if 0, class {target_class} may not exist in data)"
                )
        
        for key, val in result.items():
            if not key.startswith("y_"):
                continue
            try:
                y = int(key[2:])
                out[y] = float(val or 0.0)
                if out[y] > 0.0:
                    logger.debug(f"  Year {y}: {out[y]:.2f} ha")
            except (ValueError, TypeError):
                continue
        non_zero_count = sum(1 for v in out.values() if v > 0.0)
        logger.info(f"_series_class_value: completed with {non_zero_count} non-zero years")
        if non_zero_count == 0:
            logger.warning(
                f"_series_class_value: zero years have data - class {target_class} may not exist in "
                f"{asset_id} or region may have no pixels with that class"
            )
    except Exception as exc:
        logger.warning(
            f"_series_class_value failed (asset={asset_id}, "
            f"template={band_template}, class={target_class}): {exc}",
            exc_info=True
        )
    return out


def _series_nonzero(
    ee_geometry, asset_id: str, band_template: str,
    year_start: int, year_end: int,
) -> Dict[int, float]:
    """Per-year band, any non-zero pixel counts as area (used for fire scar)."""
    out: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    try:
        import ee
    except Exception:
        logger.error("_series_nonzero: failed to import ee")
        return out
    try:
        logger.info(
            f"_series_nonzero: starting for asset={asset_id}, "
            f"template={band_template}, years={year_start}-{year_end}"
        )
        from ..config.config import _list_aux_bands
        available_bands = set(_list_aux_bands(asset_id))
        asset = ee.Image(asset_id)
        px_area_ha = ee.Image.pixelArea().divide(10_000)
        masked = []
        bands_found = 0
        bands_missing = 0
        for y in range(year_start, year_end + 1):
            band_name = band_template.format(year=y)
            # EE .select() is lazy — check band existence upfront to avoid
            # corrupting the entire stacked reduceRegion at getInfo() time.
            if band_name not in available_bands:
                bands_missing += 1
                logger.debug(f"  Band not in asset: {band_name}")
                continue
            src = asset.select(band_name)
            masked.append(src.gt(0).multiply(px_area_ha).rename(f"y_{y}"))
            bands_found += 1
            logger.debug(f"  Band found: {band_name}")
        logger.info(f"_series_nonzero: found {bands_found} bands, missing {bands_missing}")
        if not masked:
            logger.warning(f"_series_nonzero: no bands matched, returning all zeros")
            return out
        result = _reduce_stacked(masked, ee_geometry)
        for key, val in result.items():
            if not key.startswith("y_"):
                continue
            try:
                y = int(key[2:])
                out[y] = float(val or 0.0)
                if out[y] > 0.0:
                    logger.debug(f"  Year {y}: {out[y]:.2f} ha")
            except (ValueError, TypeError):
                continue
        non_zero_count = sum(1 for v in out.values() if v > 0.0)
        logger.info(f"_series_nonzero: completed with {non_zero_count} non-zero years")
    except Exception as exc:
        logger.warning(
            f"_series_nonzero failed (asset={asset_id}, "
            f"template={band_template}): {exc}",
            exc_info=True
        )
    return out


# ---------------------------------------------------------------------------
# Public per-indicator entry points
# ---------------------------------------------------------------------------

# Band candidates are now read from config.py per dataset.
# Each dataset (deforestation_secondary, fire_scar_size) defines band_candidates
# that match the actual EE asset structure. resolve_aux_band() is used to
# discover the correct band template at runtime.


def mapbiomas_primary_deforestation_series(
    ee_geometry, year_start: int, year_end: int
) -> Dict[int, float]:
    """Per-year area of MapBiomas primary deforestation.

    Uses resolve_aux_band() to match the correct band template from config,
    then collects data for the requested year range. Year range is clamped
    to the asset's valid range (typically 1987-2024 for deforestation_secondary).
    """
    from ..config.config import MAPBIOMAS_AUX_DATASETS, resolve_aux_band
    spec = MAPBIOMAS_AUX_DATASETS.get("deforestation_secondary") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    candidates = spec.get("band_candidates", [])
    if not candidates:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Clamp year range to asset's valid range (e.g., deforestation starts 1987, not 1985)
    collection_year_start = spec.get("year_start", 1985)
    collection_year_end = spec.get("year_end", 2024)
    clamped_start = max(year_start, collection_year_start)
    clamped_end = min(year_end, collection_year_end)
    
    if clamped_start > clamped_end:
        logger.warning(
            f"primary deforestation: requested range {year_start}-{year_end} does not overlap "
            f"collection range {collection_year_start}-{collection_year_end}"
        )
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Validate that one of the band templates is available by probing with clamped start year
    probe_year = clamped_start
    resolved_band = resolve_aux_band(asset_id, candidates, year=probe_year)
    
    # Find which candidate template matched, or fall back to first template
    band_template = None
    if resolved_band:
        # Match resolved band back to template
        for cand in candidates:
            if "{year}" in cand:
                test_name = cand.format(year=probe_year)
                if test_name == resolved_band:
                    band_template = cand
                    logger.info(f"primary deforestation: matched template '{cand}' at probe year {probe_year}")
                    break
    
    if not band_template:
        # Fallback: use first template candidate even if probe failed
        band_template = next((c for c in candidates if "{year}" in c), None)
        if band_template:
            logger.warning(
                f"primary deforestation: probe failed, falling back to template '{band_template}'"
            )
    
    if not band_template:
        logger.warning(f"primary deforestation: no template found in candidates {candidates}")
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    logger.info(f"primary deforestation: using band template '{band_template}'")
    # Data is class-value: classification_YYYY where pixels of class 4 are
    # "Deforestation in Primary Vegetation" for that year. Collect only for
    # the valid range, then fill full range with zeros.
    result = _series_class_value(
        ee_geometry, asset_id, band_template,
        _MB_CLASS_PRIMARY_DEFOR, clamped_start, clamped_end,
    )
    # Fill in the full requested range with zeros for years outside the collection
    full_result: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    full_result.update(result)
    return full_result


def mapbiomas_secondary_regrowth_series(
    ee_geometry, year_start: int, year_end: int
) -> Dict[int, float]:
    """Per-year area of MapBiomas secondary-vegetation regrowth.
    
    Uses the same asset as primary deforestation (deforestation_secondary),
    but looks for class == 3 (secondary vegetation) instead of class == 2 (deforestation).
    Year range is clamped to the asset's valid range (typically 1987-2024).
    """
    from ..config.config import MAPBIOMAS_AUX_DATASETS, resolve_aux_band
    spec = MAPBIOMAS_AUX_DATASETS.get("deforestation_secondary") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    candidates = spec.get("band_candidates", [])
    if not candidates:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Clamp year range to asset's valid range (e.g., deforestation starts 1987, not 1985)
    collection_year_start = spec.get("year_start", 1985)
    collection_year_end = spec.get("year_end", 2024)
    clamped_start = max(year_start, collection_year_start)
    clamped_end = min(year_end, collection_year_end)
    
    if clamped_start > clamped_end:
        logger.warning(
            f"secondary regrowth: requested range {year_start}-{year_end} does not overlap "
            f"collection range {collection_year_start}-{collection_year_end}"
        )
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Validate that one of the band templates is available by probing with clamped start year
    probe_year = clamped_start
    resolved_band = resolve_aux_band(asset_id, candidates, year=probe_year)
    
    # Find which candidate template matched, or fall back to first template
    band_template = None
    if resolved_band:
        for cand in candidates:
            if "{year}" in cand:
                test_name = cand.format(year=probe_year)
                if test_name == resolved_band:
                    band_template = cand
                    logger.info(f"secondary regrowth: matched template '{cand}' at probe year {probe_year}")
                    break
    
    if not band_template:
        # Fallback: use first template candidate even if probe failed
        band_template = next((c for c in candidates if "{year}" in c), None)
        if band_template:
            logger.warning(
                f"secondary regrowth: probe failed, falling back to template '{band_template}'"
            )
    
    if not band_template:
        logger.warning(f"secondary regrowth: no template found in candidates {candidates}")
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    logger.info(f"secondary regrowth: using band template '{band_template}'")
    # Data is class-value: classification_YYYY where pixels of class 5 are
    # "Secondary Vegetation Regrowth" (event in that year). Collect only for
    # the valid range, then fill full range with zeros.
    result = _series_class_value(
        ee_geometry, asset_id, band_template,
        _MB_CLASS_SECONDARY_REGROWTH, clamped_start, clamped_end,
    )
    # Fill in the full requested range with zeros for years outside the collection
    full_result: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    full_result.update(result)
    return full_result


def mapbiomas_fire_scar_series(
    ee_geometry, year_start: int, year_end: int,
) -> Dict[int, float]:
    """Per-year burned area (ha) from MapBiomas Fire Coll. 4 scar-size dataset.
    
    Uses resolve_aux_band() to match the correct band template (e.g., scar_area_ha_{year})
    and respects the fire collection's year range (1987-2024, not 1985).
    """
    from ..config.config import MAPBIOMAS_AUX_DATASETS, resolve_aux_band
    spec = MAPBIOMAS_AUX_DATASETS.get("fire_scar_size") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    candidates = spec.get("band_candidates", [])
    if not candidates:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Fire collection has different year ranges — respect them
    collection_year_start = spec.get("year_start", 1987)
    collection_year_end = spec.get("year_end", 2024)
    
    # Clamp the year range to the collection's valid range
    clamped_start = max(year_start, collection_year_start)
    clamped_end = min(year_end, collection_year_end)
    
    if clamped_start > clamped_end:
        logger.warning(
            f"fire scar: requested range {year_start}-{year_end} does not overlap "
            f"collection range {collection_year_start}-{collection_year_end}"
        )
        return {y: 0.0 for y in range(year_start, year_end + 1)}
    
    # Validate that one of the band templates is available by probing with clamped start year
    resolved_band = resolve_aux_band(asset_id, candidates, year=clamped_start)
    
    # Find which candidate template matched, or fall back to first template
    band_template = None
    if resolved_band:
        for cand in candidates:
            if "{year}" in cand:
                test_name = cand.format(year=clamped_start)
                if test_name == resolved_band:
                    band_template = cand
                    logger.info(f"fire scar: matched template '{cand}' at probe year {clamped_start}")
                    break
    
    if not band_template:
        # Fallback: use first template candidate even if probe failed
        band_template = next((c for c in candidates if "{year}" in c), None)
        if band_template:
            logger.warning(
                f"fire scar: probe failed, falling back to template '{band_template}'"
            )
    
    if not band_template:
        logger.warning(f"fire scar: no template found in candidates {candidates}")
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    logger.info(f"fire scar: using band template '{band_template}'")
    
    # Collect data only for years in the valid range
    result = _series_nonzero(
        ee_geometry, asset_id, band_template, clamped_start, clamped_end
    )
    
    # Fill in the full requested range with zeros for years outside the collection
    full_result: Dict[int, float] = {y: 0.0 for y in range(year_start, year_end + 1)}
    full_result.update(result)
    return full_result


# ---------------------------------------------------------------------------
# Top-level convenience helper
# ---------------------------------------------------------------------------

def collect_timeline(
    ee_geometry,
    year_start: int,
    year_end: int,
    *,
    gfc_result: Optional[Dict] = None,
    include_hansen: bool = True,
    include_mb_defor: bool = True,
    include_mb_secondary: bool = True,
    include_fire: bool = True,
) -> Dict[str, Dict[int, float]]:
    """Pull all yearly time-series for the deforestation-timeline chart."""
    out: Dict[str, Dict[int, float]] = {}
    
    logger.info(
        f"collect_timeline: starting for {year_start}-{year_end}, "
        f"gfc_result={'present' if gfc_result else 'None'}, "
        f"includes: hansen={include_hansen}, mb_defor={include_mb_defor}, "
        f"mb_secondary={include_mb_secondary}, fire={include_fire}"
    )
    
    if include_hansen:
        out["hansen_loss"] = hansen_loss_series(gfc_result, year_start, year_end)
        non_zero = sum(1 for v in out["hansen_loss"].values() if v > 0.0)
        logger.info(f"  hansen_loss: {non_zero} non-zero years")
    
    if include_mb_defor:
        out["mb_defor_primary"] = mapbiomas_primary_deforestation_series(
            ee_geometry, year_start, year_end
        )
        non_zero = sum(1 for v in out["mb_defor_primary"].values() if v > 0.0)
        logger.info(f"  mb_defor_primary: {non_zero} non-zero years")
    
    if include_mb_secondary:
        out["mb_secondary_growth"] = mapbiomas_secondary_regrowth_series(
            ee_geometry, year_start, year_end
        )
        non_zero = sum(1 for v in out["mb_secondary_growth"].values() if v > 0.0)
        logger.info(f"  mb_secondary_growth: {non_zero} non-zero years")
    
    if include_fire:
        out["mb_fire_scar"] = mapbiomas_fire_scar_series(
            ee_geometry, year_start, year_end
        )
        non_zero = sum(1 for v in out["mb_fire_scar"].values() if v > 0.0)
        logger.info(f"  mb_fire_scar: {non_zero} non-zero years")
    
    logger.info(f"collect_timeline: completed with {len(out)} series")
    return out


# ---------------------------------------------------------------------------
# State-code resolution for the political-context bar
# ---------------------------------------------------------------------------

def first_state_code(uf_sigla_value: Optional[str]) -> Optional[str]:
    """Pick the first 2-letter state code from a possibly multi-state field."""
    if not uf_sigla_value:
        return None
    for sep in (",", "/", ";", " "):
        if sep in uf_sigla_value:
            parts = [p.strip().upper() for p in uf_sigla_value.split(sep)]
            for p in parts:
                if len(p) == 2 and p.isalpha():
                    return p
            continue
    cleaned = uf_sigla_value.strip().upper()
    if len(cleaned) == 2 and cleaned.isalpha():
        return cleaned
    return None
