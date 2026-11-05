"""PAD-US (USGS Protected Areas Database of the United States), queried live.

The Canada page ships precomputed per-province CPCAD files. For the United States the same
job is done against the **public ArcGIS FeatureServers** USGS publishes (no key), so there
is nothing to download, mirror or keep in sync:

* by name — a ``LIKE`` query on each source, largest first;
* by click — every record that contains the point, **smallest first** (areas overlap: a
  wilderness inside a national park; the user chooses, nothing is decided silently);
* a unit's boundary — fetched when chosen, generalised to ``PADUS_SIMPLIFY_M`` so it can go
  to Earth Engine inline and be drawn on the map.

**Sources** (``config.settings.PADUS_SOURCES``): ``fee`` (v4.1 fee managers — whole national
parks, forests, refuges, state and local parks), ``proclamation`` (v4.1 — the federal
proclamation boundaries, which is where the **tribal** reservations and trust lands are) and
``designation`` (wilderness areas and similar, from the flattened national service). The
flattened service is not used for Fee because it carves designations out of the parks.

**One unit, several records.** A federal unit is often several records — Yellowstone National
Park is three, one per state. For federal fee units the records sharing name, manager and
designation are one unit: ``Unit.key`` names the *anchor* record and the boundary and area are
those of the whole group. Other records stand alone (two "Navajo Park"s are two parks).

**Tribal lands.** They are boundaries published by the federal government and open; the page
shows them with the same notice as the Brazil page's Indigenous lands
(``indigenous_data_notice_*``): the numbers are land cover, not statements by or about the
peoples, and Yvynation does not speak for them.
"""

from __future__ import annotations

import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import requests

from ..config.settings import PADUS_SIMPLIFY_M, PADUS_SOURCES, USER_AGENT

logger = logging.getLogger(__name__)

TIMEOUT = (6, 45)
ACRES_TO_HA = 0.40468564224
#: A federal fee unit with more pieces than this is cut off (and says so in ``notes``).
MAX_GROUP = 400

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_lock = threading.Lock()
_geom_cache: Dict[str, Dict[str, Any]] = {}
_labels_cache: Dict[str, str] = {}

#: Designation-type codes with a label of our own, for the few the service gives as codes only.
_FALLBACK_LABELS = {"TRIBL": "Native American Land Area", "NP": "National Park",
                    "NM": "National Monument", "NF": "National Forest", "WA": "Wilderness Area"}


class PadusError(RuntimeError):
    """The USGS service did not answer, or answered with an error."""


@dataclass(frozen=True)
class Unit:
    key: str                     # "fee:<anchor OBJECTID>" | "proclamation:<id>" | "designation:<id>"
    name: str
    source: str
    category: str
    des_type: str
    des_label: str
    manager: str
    manager_type: str
    gap_status: str
    iucn: str
    access: str
    ha: float
    state: str
    tribal: bool
    pieces: int = 1

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------- #
# Plumbing
# --------------------------------------------------------------------------- #
def _fields(source: str) -> str:
    st = "ST_Name" if source == "designation" else "State_Nm"
    iucn = ",IUCN_Cat" if source != "fee" else ""
    return f"OBJECTID,Unit_Nm,Category,Des_Tp,Mang_Name,Mang_Type,GAP_Sts,GIS_Acres,Pub_Access,{st}{iucn}"


def _query(source: str, params: Dict[str, Any]) -> Dict[str, Any]:
    params = {"f": "json", **params}
    try:
        r = _session.get(f"{PADUS_SOURCES[source]}/query", params=params, timeout=TIMEOUT)
        data = r.json()
    except (requests.RequestException, ValueError) as exc:
        raise PadusError(f"PAD-US service unavailable: {exc}") from exc
    if "error" in data:
        raise PadusError(f"PAD-US query failed: {data['error'].get('message')}")
    return data


def _escape(text: str) -> str:
    """Quote for a SQL string literal and drop wildcard characters the user typed."""
    return re.sub(r"[%_\\]", " ", text).replace("'", "''").strip()


def _des_labels() -> Dict[str, str]:
    """Designation-type code → label, read once from the service's own coded-value domain."""
    with _lock:
        if _labels_cache:
            return _labels_cache
    try:
        meta = _session.get(f"{PADUS_SOURCES['fee']}?f=json", timeout=TIMEOUT).json()
        for fld in meta.get("fields", []):
            if fld.get("name") == "Des_Tp" and fld.get("domain"):
                labels = {str(c["code"]): str(c["name"]) for c in fld["domain"].get("codedValues", [])}
                break
        else:
            labels = {}
    except (requests.RequestException, ValueError):
        labels = {}
    labels = {**_FALLBACK_LABELS, **labels}
    with _lock:
        _labels_cache.update(labels)
    return labels


def _unit(attrs: Dict[str, Any], source: str, pieces: int = 1, ha: Optional[float] = None) -> Unit:
    des = str(attrs.get("Des_Tp") or "")
    acres = float(attrs.get("GIS_Acres") or 0)
    state = str(attrs.get("State_Nm") or attrs.get("ST_Name") or "")
    return Unit(
        key=f"{source}:{int(attrs['OBJECTID'])}",
        name=str(attrs.get("Unit_Nm") or "").strip() or f"PAD-US #{attrs['OBJECTID']}",
        source=source,
        category=str(attrs.get("Category") or ""),
        des_type=des,
        des_label=_des_labels().get(des, des),
        manager=str(attrs.get("Mang_Name") or ""),
        manager_type=str(attrs.get("Mang_Type") or ""),
        gap_status=str(attrs.get("GAP_Sts") or ""),
        iucn=str(attrs.get("IUCN_Cat") or ""),
        access=str(attrs.get("Pub_Access") or ""),
        ha=round(ha if ha is not None else acres * ACRES_TO_HA, 1),
        state="" if state in ("Not Applicable", "NA") else state,
        tribal=(des == "TRIBL" or attrs.get("Mang_Type") == "TRIB"),
        pieces=pieces,
    )


def _is_group(attrs: Dict[str, Any], source: str) -> bool:
    return source == "fee" and attrs.get("Mang_Type") == "FED"


def _group_where(attrs: Dict[str, Any]) -> str:
    return (f"Unit_Nm='{_escape(str(attrs.get('Unit_Nm') or ''))}' AND "
            f"Mang_Name='{_escape(str(attrs.get('Mang_Name') or ''))}' AND "
            f"Des_Tp='{_escape(str(attrs.get('Des_Tp') or ''))}' AND Category='Fee'")


def _merge(records: List[Tuple[str, Dict[str, Any]]]) -> List[Unit]:
    """Records → units: federal fee pieces with the same name/manager/designation become one."""
    groups: Dict[Tuple, List[Dict[str, Any]]] = {}
    units: List[Unit] = []
    for source, a in records:
        if _is_group(a, source):
            k = (a.get("Unit_Nm"), a.get("Mang_Name"), a.get("Des_Tp"))
            groups.setdefault(k, []).append(a)
        else:
            units.append(_unit(a, source))
    for pieces in groups.values():
        anchor = max(pieces, key=lambda a: float(a.get("GIS_Acres") or 0))
        total = sum(float(a.get("GIS_Acres") or 0) for a in pieces) * ACRES_TO_HA
        units.append(_unit(anchor, "fee", pieces=len(pieces), ha=total))
    # The same place often has a fee record and a proclamation record: show the fee one.
    fee = {(u.name, u.manager): u.ha for u in units if u.source == "fee"}
    return [u for u in units
            if not (u.source == "proclamation" and (u.name, u.manager) in fee
                    and abs(fee[(u.name, u.manager)] - u.ha) <= 0.05 * max(u.ha, 1))]


def _fan_out(build) -> List[Tuple[str, Dict[str, Any]]]:
    """Run one query per source in parallel; return ``(source, attributes)`` pairs."""
    def one(source: str):
        data = build(source)
        return [(source, f["attributes"]) for f in data.get("features", [])]
    with ThreadPoolExecutor(max_workers=3) as ex:
        out: List[Tuple[str, Dict[str, Any]]] = []
        for part in ex.map(one, PADUS_SOURCES):
            out.extend(part)
    return out


def _category_filter(source: str) -> str:
    return "Category='Designation'" if source == "designation" else "1=1"


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def search(text: str, *, limit: int = 30) -> List[Unit]:
    """Units whose name contains ``text``, largest first."""
    text = _escape(text)
    if len(text) < 2:
        return []

    def build(source: str):
        return _query(source, {
            "where": f"UPPER(Unit_Nm) LIKE UPPER('%{text}%') AND {_category_filter(source)}",
            "outFields": _fields(source), "returnGeometry": "false",
            "orderByFields": "GIS_Acres DESC", "resultRecordCount": 60})
    units = _merge(_fan_out(build))
    units.sort(key=lambda u: -u.ha)
    return units[:limit]


def at_point(lat: float, lon: float) -> List[Unit]:
    """Every unit containing the point, smallest first."""
    def build(source: str):
        return _query(source, {
            "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects", "where": _category_filter(source),
            "outFields": _fields(source), "returnGeometry": "false", "resultRecordCount": 50})
    units = _merge(_fan_out(build))
    return sorted(units, key=lambda u: (u.ha, u.name))


def _split(key: str) -> Tuple[str, int]:
    source, _, oid = key.partition(":")
    if source not in PADUS_SOURCES or not oid.isdigit():
        raise PadusError(f"bad unit key {key!r}")
    return source, int(oid)


def get_unit(key: str) -> Optional[Unit]:
    source, oid = _split(key)
    data = _query(source, {"where": f"OBJECTID={oid}", "outFields": _fields(source),
                           "returnGeometry": "false"})
    feats = data.get("features", [])
    if not feats:
        return None
    a = feats[0]["attributes"]
    if not _is_group(a, source):
        return _unit(a, source)
    members = _query(source, {"where": _group_where(a), "outFields": _fields(source),
                              "returnGeometry": "false", "resultRecordCount": MAX_GROUP})
    pieces = [m["attributes"] for m in members.get("features", [])] or [a]
    total = sum(float(p.get("GIS_Acres") or 0) for p in pieces) * ACRES_TO_HA
    return _unit(a, source, pieces=len(pieces), ha=total)


def geometry(key: str, *, simplify_m: float = PADUS_SIMPLIFY_M) -> Optional[Dict[str, Any]]:
    """The unit's boundary as a GeoJSON geometry in EPSG:4326, generalised (all the pieces of
    a federal fee unit, concatenated into one MultiPolygon)."""
    with _lock:
        if key in _geom_cache:
            return _geom_cache[key]
    source, oid = _split(key)
    where = f"OBJECTID={oid}"
    anchor = _query(source, {"where": where, "outFields": _fields(source), "returnGeometry": "false"})
    feats = anchor.get("features", [])
    if feats and _is_group(feats[0]["attributes"], source):
        where = _group_where(feats[0]["attributes"])
    data = _query(source, {
        "where": where, "outFields": "OBJECTID", "returnGeometry": "true", "outSR": 4326,
        "maxAllowableOffset": simplify_m / 111_320.0, "geometryPrecision": 5,
        "resultRecordCount": MAX_GROUP, "f": "geojson"})
    polys: List[Any] = []
    for f in data.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon":
            polys.append(g["coordinates"])
        elif g.get("type") == "MultiPolygon":
            polys.extend(g["coordinates"])
    if not polys:
        return None
    geom = ({"type": "Polygon", "coordinates": polys[0]} if len(polys) == 1
            else {"type": "MultiPolygon", "coordinates": polys})
    with _lock:
        if len(_geom_cache) > 64:
            _geom_cache.pop(next(iter(_geom_cache)))
        _geom_cache[key] = geom
    return geom


def parts(geom: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The separate polygons of a multipart boundary, largest first."""
    from shapely.geometry import shape

    from .zones import area_ha

    if not geom or geom.get("type") != "MultiPolygon":
        return []
    out = []
    for i, coords in enumerate(geom["coordinates"]):
        g = {"type": "Polygon", "coordinates": coords}
        out.append({"id": str(i), "ha": area_ha(g), "bounds": list(shape(g).bounds)})
    out.sort(key=lambda p: -p["ha"])
    for rank, p in enumerate(out, 1):
        p["rank"] = rank
    return out


def parts_geometry(geom: Dict[str, Any], ids: Sequence[str]) -> Dict[str, Any]:
    keep = {int(i) for i in ids}
    polys = [c for i, c in enumerate(geom["coordinates"]) if i in keep]
    return {"type": "MultiPolygon", "coordinates": polys} if len(polys) != 1 else \
           {"type": "Polygon", "coordinates": polys[0]}
