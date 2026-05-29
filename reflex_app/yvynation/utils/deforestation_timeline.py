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
        return out
    for rec in gfc_result.get("tree_loss_data", []) or []:
        try:
            code = int(rec.get("Year_Code", 0))
        except (TypeError, ValueError):
            continue
        if code <= 0:
            continue
        y = 2000 + code
        if year_start <= y <= year_end:
            try:
                out[y] = out.get(y, 0.0) + float(rec.get("Area_ha", 0.0) or 0.0)
            except (TypeError, ValueError):
                continue
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
        return {}
    try:
        import ee
    except Exception:
        return {}
    try:
        stacked = ee.Image.cat(bands)
        result = stacked.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=ee_geometry,
            scale=scale,
            maxPixels=int(1e10),
            bestEffort=True,
        ).getInfo() or {}
    except Exception as exc:
        logger.warning(f"stacked reduceRegion failed: {exc}")
        return {}
    # Normalise None → 0.0 so consumers don't have to care.
    return {k: float(v or 0.0) for k, v in result.items()}


# ---------------------------------------------------------------------------
# Per-indicator collectors (probe-driven)
# ---------------------------------------------------------------------------

# Class codes used when the asset has per-year class-coded bands.
_MB_CLASS_PRIMARY_DEFOR = 100
_MB_CLASS_SECONDARY_REGROWTH = 200


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
        return out
    try:
        asset = ee.Image(asset_id)
        px_area_ha = ee.Image.pixelArea().divide(10_000)
        masked = []
        for y in range(year_start, year_end + 1):
            band_name = band_template.format(year=y)
            try:
                src = asset.select(band_name)
            except Exception:
                continue
            masked.append(
                src.eq(target_class).multiply(px_area_ha).rename(f"y_{y}")
            )
        if not masked:
            return out
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
            f"class-value collector failed (asset={asset_id}, "
            f"template={band_template}, class={target_class}): {exc}"
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
        return out
    try:
        asset = ee.Image(asset_id)
        px_area_ha = ee.Image.pixelArea().divide(10_000)
        masked = []
        for y in range(year_start, year_end + 1):
            band_name = band_template.format(year=y)
            try:
                src = asset.select(band_name)
            except Exception:
                continue
            masked.append(src.gt(0).multiply(px_area_ha).rename(f"y_{y}"))
        if not masked:
            return out
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
            f"nonzero collector failed (asset={asset_id}, "
            f"template={band_template}): {exc}"
        )
    return out


# ---------------------------------------------------------------------------
# Public per-indicator entry points
# ---------------------------------------------------------------------------

# Bands likely to encode primary deforestation (pixel value = year of event).
_PRIMARY_DEFOR_YEAR_BANDS = [
    "primary_vegetation_loss",
    "primary_vegetation_year_to_secondary",
    "primary_loss_year",
    "deforestation_year",
]
# Bands likely to encode secondary regrowth (pixel value = year of event).
_SECONDARY_REGROWTH_YEAR_BANDS = [
    "secondary_vegetation_regrowth",
    "secondary_regrowth_year",
    "regrowth_year",
]
# Bands likely to encode fire scar (per-year, value = scar size bin > 0).
_FIRE_SCAR_BANDS = [
    "scar_size_{year}",
    "burned_area_{year}",
    "classification_{year}",
]


def _pick_band(asset_id: str, candidates: List[str]) -> Optional[str]:
    """Return the first candidate present in the asset, or ``None``."""
    try:
        from ..config.config import _list_aux_bands
    except Exception:
        return None
    try:
        available = set(_list_aux_bands(asset_id))
    except Exception:
        return None
    for c in candidates:
        if c in available:
            return c
    return None


def mapbiomas_primary_deforestation_series(
    ee_geometry, year_start: int, year_end: int
) -> Dict[int, float]:
    """Per-year area of MapBiomas primary deforestation.

    Tries the single-band-with-year-value pattern first (the user's
    observed semantics for the v3 asset), then falls back to a per-year
    class-coded band where class == 100.
    """
    from ..config.config import MAPBIOMAS_AUX_DATASETS
    spec = MAPBIOMAS_AUX_DATASETS.get("deforestation_secondary") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # year-value bands
    band = _pick_band(asset_id, _PRIMARY_DEFOR_YEAR_BANDS)
    if band:
        logger.info(f"primary deforestation: using year-value band '{band}'")
        return _series_year_value(ee_geometry, asset_id, band, year_start, year_end)

    # class-value fallback
    logger.info("primary deforestation: falling back to classification_{year}==100")
    return _series_class_value(
        ee_geometry, asset_id, "classification_{year}",
        _MB_CLASS_PRIMARY_DEFOR, year_start, year_end,
    )


def mapbiomas_secondary_regrowth_series(
    ee_geometry, year_start: int, year_end: int
) -> Dict[int, float]:
    """Per-year area of MapBiomas secondary-vegetation regrowth."""
    from ..config.config import MAPBIOMAS_AUX_DATASETS
    spec = MAPBIOMAS_AUX_DATASETS.get("deforestation_secondary") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    band = _pick_band(asset_id, _SECONDARY_REGROWTH_YEAR_BANDS)
    if band:
        logger.info(f"secondary regrowth: using year-value band '{band}'")
        return _series_year_value(ee_geometry, asset_id, band, year_start, year_end)

    logger.info("secondary regrowth: falling back to classification_{year}==200")
    return _series_class_value(
        ee_geometry, asset_id, "classification_{year}",
        _MB_CLASS_SECONDARY_REGROWTH, year_start, year_end,
    )


def mapbiomas_fire_scar_series(
    ee_geometry, year_start: int, year_end: int,
) -> Dict[int, float]:
    """Per-year burned area (ha) from MapBiomas Fire Coll. 4 scar-size dataset."""
    from ..config.config import MAPBIOMAS_AUX_DATASETS
    spec = MAPBIOMAS_AUX_DATASETS.get("fire_scar_size") or {}
    asset_id = spec.get("asset")
    if not asset_id:
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    # Pick a template by probing one year — works whether the asset uses
    # ``scar_size_YYYY`` or ``classification_YYYY``.
    probe_year = year_start
    chosen_template = None
    try:
        from ..config.config import _list_aux_bands
        available = set(_list_aux_bands(asset_id))
        for tpl in _FIRE_SCAR_BANDS:
            if tpl.format(year=probe_year) in available:
                chosen_template = tpl
                break
    except Exception:
        chosen_template = None

    if chosen_template is None:
        logger.warning(
            f"fire scar: no known band template matched in {asset_id}; tried {_FIRE_SCAR_BANDS}"
        )
        return {y: 0.0 for y in range(year_start, year_end + 1)}

    logger.info(f"fire scar: using band template '{chosen_template}'")
    return _series_nonzero(ee_geometry, asset_id, chosen_template, year_start, year_end)


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
    if include_hansen:
        out["hansen_loss"] = hansen_loss_series(gfc_result, year_start, year_end)
    if include_mb_defor:
        out["mb_defor_primary"] = mapbiomas_primary_deforestation_series(
            ee_geometry, year_start, year_end
        )
    if include_mb_secondary:
        out["mb_secondary_growth"] = mapbiomas_secondary_regrowth_series(
            ee_geometry, year_start, year_end
        )
    if include_fire:
        out["mb_fire_scar"] = mapbiomas_fire_scar_series(
            ee_geometry, year_start, year_end
        )
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
