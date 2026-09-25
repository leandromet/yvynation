"""The laid-out territory report (docs/PDF_REPORT.md §3, §11).

Synthetic TI and UC snapshots — no Earth Engine, no GeoPackage, no kaleido:
charts are stand-in PNGs, maps are stand-in overlays on a real MapView.
"""

import io
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from yvynation.report_kit import MapComposition, render_html, render_pdf  # noqa: E402
from yvynation.report_kit.maps import MapView  # noqa: E402
from yvynation.utils import report_builder as rb  # noqa: E402
from yvynation.utils.report_text import LANGS, TEXT, missing_keys  # noqa: E402

GEOM = {"type": "Polygon", "coordinates": [[[-52.0, -11.0], [-51.6, -11.0],
                                            [-51.6, -10.6], [-52.0, -10.6], [-52.0, -11.0]]]}
BUFFER = {"type": "Polygon", "coordinates": [
    [[-52.1, -11.1], [-51.5, -11.1], [-51.5, -10.5], [-52.1, -10.5], [-52.1, -11.1]],
    [[-52.0, -11.0], [-52.0, -10.6], [-51.6, -10.6], [-51.6, -11.0], [-52.0, -11.0]]]}


def _png(w=600, h=340, color=(40, 120, 60)):
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, "PNG")
    return buf.getvalue()


def _recs(areas):
    names = {3: "Forest Formation", 15: "Pasture", 12: "Grassland", 33: "River Lake and Ocean"}
    return [{"Class_ID": c, "Class": names[c], "Area_ha": a} for c, a in areas.items()]


def _cmp_rows(a1, a2):
    rows = []
    for c in set(a1) | set(a2):
        rows.append({"Class_ID": c, "Class": _recs({c: 0})[0]["Class"],
                     "Area_Year1": a1.get(c, 0.0), "Area_Year2": a2.get(c, 0.0)})
    return rows


def _gfc(loss_by_code, cover=90000.0, nocover=10000.0, gain=500.0):
    return {
        "type": "hansen_gfc",
        "tree_cover_data": [{"Percent_Cover": 0, "Pixels": 1, "Area_ha": nocover},
                            {"Percent_Cover": 80, "Pixels": 1, "Area_ha": cover}],
        "tree_loss_data": [{"Year_Code": 0, "Year": "No Loss", "Pixels": 1, "Area_ha": 1.0}]
        + [{"Year_Code": c, "Year": str(2000 + c), "Pixels": 1, "Area_ha": a}
           for c, a in loss_by_code.items()],
        "tree_gain_data": [{"Gain_Code": 0, "Pixels": 1, "Area_ha": 1.0},
                           {"Gain_Code": 1, "Pixels": 1, "Area_ha": gain}],
    }


FIG = {"data": [{"type": "bar", "x": ["a", "b"], "y": [1, 2]}], "layout": {}}


def ti_snapshot(**over):
    a1 = {3: 91000.0, 15: 5000.0, 12: 3000.0, 33: 1000.0}
    a2 = {3: 86000.0, 15: 10500.0, 12: 2500.0, 33: 1000.0}
    b1 = {3: 60000.0, 15: 30000.0, 12: 8000.0, 33: 2000.0}
    b2 = {3: 45000.0, 15: 45000.0, 12: 8000.0, 33: 2000.0}
    export = {
        "territory_name": "Terra Teste",
        "comparison_result": {"year_start": 1985, "year_end": 2024,
                              "data": _cmp_rows(a1, a2)},
        "territory_result": _recs(a1), "territory_result_year2": _recs(a2),
        "territory_transitions": {"3": {"15": 5000.0, "12": 200.0}, "12": {"15": 700.0}},
        "glad_result": {"year": 2020, "data": [
            {"Class_ID": 75, "Class": "Dense tree cover", "Area_ha": 80000.0},
            {"Class_ID": 6, "Class": "Short vegetation", "Area_ha": 20000.0}]},
        "gfc_result": _gfc({5: 300.0, 19: 2310.0, 24: 800.0}),
        "buffer_mapbiomas_comparison_result": {"data": _cmp_rows(b1, b2)},
        "buffer_gfc_result": _gfc({19: 9000.0}, cover=70000.0),
        "territory_geojson_cached": GEOM,
    }
    export.update(over)
    figs = {k: FIG for k in rb.FIGURE_SPECS}
    return rb.snapshot_from_export(rb.plain(export), territory_type="indigenous",
                                   geometry=GEOM, buffer_geometry=BUFFER, buffer_km=10.0,
                                   figure_json=figs)


TI_META = {"type": "indigenous", "info": {
    "terrai_nom": "Terra Teste", "terrai_cod": 123, "etnia": "Guarani Kaiowá",
    "fase_ti": "Regularizada", "modalidade": "Tradicionalmente ocupada",
    "uf_sigla": "MT", "municipio": "Querência", "superficie_ha": 100500.0},
    "demarcation": {"em_estudo": 1990, "delimitada": 1995, "declarada": 1998,
                    "homologada": 2001, "regularizada": 2003}}
UC_META = {"type": "conservation", "info": {
    "nome_uc": "Parque Teste", "cd_cnuc": "0000.00.0001", "grupo": "Proteção Integral",
    "categoria": "Parque", "esfera": "Federal", "uf_sigla": "PA", "municipio": "Altamira",
    "superficie_ha": 100000.0}, "creation": {"creation_year": 2006}}


def fake_maps(snap):
    view_h = MapView.from_geojson([GEOM, BUFFER], slot="half")
    view_f = MapView.from_geojson([GEOM, BUFFER], slot="full")
    ov = _png(view_h.px_w, view_h.px_h)
    comp = MapComposition(view=view_h, overlays=[ov], clip_to=BUFFER, attribution="test")
    full = MapComposition(view=view_f, overlays=[_png(view_f.px_w, view_f.px_h, (200, 30, 30))],
                          attribution="test")
    return {"mb_y1": comp, "mb_y2": comp, "gfc": full, "imagery": full,
            "imagery_attr": "Landsat 2024: USGS/NASA", "no_imagery": False, "error": ""}


def pngs_for(snap, options):
    return {k: _png() for k in rb.figure_plan(snap, options)}


def _keys(report):
    return [s.key for s in report.sections]


def _contents(report):
    about = next(s for s in report.sections if s.key == "about")
    return {i.title: i.status for i in about.blocks[0].items}


def test_ti_sections_follow_outline_order():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, pngs_for(snap, {}), fake_maps(snap),
                                       "en", {"appendix": True})
    keys = _keys(report)
    assert keys == [k for k in rb.SECTION_ORDER if k in keys]
    for k in ("identification", "about", "maps", "landcover", "gains_losses", "transitions",
              "gfc", "glad", "buffer", "methods", "citation", "appendix"):
        assert k in keys, k
    status = _contents(report)
    assert status["Multi-window transitions"] == "not_run"
    assert status["Deforestation timeline"] == "not_run"
    assert status["Hansen Global Forest Change"] == "included"
    assert status["Territory vs buffer"] == "included"


def test_ti_identification_names_land_group_stage_state():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, None, "pt", {})
    kv = report.sections[0].blocks[0].left
    text = " ".join(f"{k} {v}" for k, v in kv.rows)
    for needle in ("Terra Teste", "Guarani Kaiowá", "Regularizada", "MT", "homologada 2001"):
        assert needle in text


def test_buffer_table_and_reading():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, None, "en", {})
    sec = next(s for s in report.sections if s.key == "buffer")
    table = next(b for b in sec.blocks if isinstance(b, rb.Table))
    change = next(r for r in table.rows if r[0].startswith("Change in forest"))
    assert change[1] == pytest.approx(-5.0)      # 91 % → 86 %
    assert change[2] == pytest.approx(-15.0)     # 60 % → 45 %
    reading = " ".join(b.text for b in sec.blocks if isinstance(b, rb.Paragraph))
    assert "-5.0 pp" in reading and "-15.0 pp" in reading and "-10.0 pp" in reading


def test_gfc_reading_matches_table():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, None, "en", {})
    sec = next(s for s in report.sections if s.key == "gfc")
    reading = sec.blocks[-1].text
    assert "3,410 ha" in reading and "2019 (2,310 ha)" in reading


def test_uc_missing_analyses_are_not_run():
    snap = ti_snapshot(glad_result=None, gfc_result=None, territory_transitions=None,
                       buffer_mapbiomas_comparison_result=None, buffer_gfc_result=None)
    snap["transitions"] = None
    snap["territory_type"] = "conservation"
    report = rb.build_territory_report(snap, UC_META, {}, None, "en", {"maps": False})
    keys = _keys(report)
    assert keys == [k for k in rb.SECTION_ORDER if k in keys]
    for k in ("gfc", "glad", "transitions", "buffer", "maps", "appendix"):
        assert k not in keys
    status = _contents(report)
    assert status["Hansen Global Forest Change"] == "not_run"
    assert status["GLAD land cover"] == "not_run"
    assert status["Territory vs buffer"] == "not_run"
    assert status["Maps"] == "excluded"
    kv = report.sections[0].blocks[0].left
    text = " ".join(f"{k} {v}" for k, v in kv.rows)
    assert "0000.00.0001" in text and "2006" in text and "Parque Teste" in text
    assert "Conservation Unit" in report.meta.subject


def test_batch_forces_appendix_off():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, None, "en",
                                       {"appendix": True, "batch": True})
    assert "appendix" not in _keys(report)
    assert _contents(report)["Appendix (full tables)"] == "excluded"


def test_templates_complete_in_every_language():
    assert missing_keys() == {lang: [] for lang in LANGS if lang != "en"}


def _report_text(report):
    parts = [report.meta.title, report.meta.subject]
    for sec in report.sections:
        parts.append(sec.title)
    for b in report.blocks():
        for attr in ("text", "caption", "label", "title"):
            v = getattr(b, attr, None)
            if isinstance(v, str):
                parts.append(v)
        if isinstance(b, rb.KeyValues):
            parts += [k for k, _ in b.rows]
        if isinstance(b, rb.Table):
            parts += list(b.columns)
        if isinstance(b, rb.ContentsList):
            parts += [f"{i.title} {i.reason}" for i in b.items]
    return "\n".join(parts)


def _static_fragments(template):
    return [f.strip(" ,.;:()") for f in re.split(r"\{[^}]*\}", template)]


@pytest.mark.parametrize("lang", ["es", "fr"])
def test_no_english_template_text(lang):
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, fake_maps(snap), lang,
                                       {"appendix": True})
    text = _report_text(report)
    leaks = []
    for key, en in TEXT["en"].items():
        if TEXT[lang].get(key) == en:        # identical by design (e.g. "Hansen GFC")
            continue
        for frag in _static_fragments(en):
            if len(frag) >= 15 and frag not in TEXT[lang].get(key, "") and frag in text:
                leaks.append((key, frag))
    assert not leaks


@pytest.mark.parametrize("lang", ["en", "pt"])
def test_both_formats_render_within_budget(lang):
    snap = ti_snapshot()
    opts = {"appendix": True}
    report = rb.build_territory_report(snap, TI_META, pngs_for(snap, opts), fake_maps(snap),
                                       lang, opts)
    pdf = render_pdf(report)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) <= 3 * 1024 * 1024
    html_report = rb.build_territory_report(snap, TI_META, None, fake_maps(snap), lang,
                                            {**opts, "fmt": "html"})
    html = render_html(html_report)
    assert html.startswith(b"<!doctype html>")
    assert b"Terra Teste" in html
    # interactive charts are inlined, never fetched from a CDN
    assert not re.search(rb"<script[^>]+src=", html)


def test_missing_png_is_a_placeholder_not_an_error():
    snap = ti_snapshot()
    report = rb.build_territory_report(snap, TI_META, {}, None, "en", {})
    figs = [b for b in report.blocks() if isinstance(b, rb.Figure)]
    assert figs and all(f.png is None and f.unavailable_reason for f in figs)
    assert render_pdf(report)[:4] == b"%PDF"


def test_snapshot_is_plain_data():
    snap = ti_snapshot()
    import json
    json.dumps({k: v for k, v in snap.items() if k != "figures"})
    assert snap["y1"] == 1985 and snap["y2"] == 2024
    assert snap["buffer_km"] == 10.0
    assert rb.figure_plan(snap, {"figures": False}) == []
    assert "sankey" in rb.figure_plan(snap, {})
