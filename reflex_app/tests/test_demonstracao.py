"""The scrolling walkthroughs (/demonstracao/<modo> pt, /walkthrough/<mode> en): examples, articles, pages.

No network: the examples are the committed snapshots
(scripts/build_demonstracao.py), the prints are files in assets/demo_prints/,
and the article checks are text checks on yvynation/reportagem/.
"""

import json
import re
from pathlib import Path

import pytest

from yvynation.utils import demonstracao

RAIZ = Path(__file__).resolve().parent.parent
ARTIGOS = RAIZ / "yvynation" / "reportagem"
PRINTS = RAIZ / "assets" / "demo_prints"

#: article html → handler js (three articles share one script)
SCRIPTS = {"terra_indigena": "yvynation_area", "unidade_conservacao": "yvynation_area",
           "desenho": "yvynation_area", "lote": "lote"}


@pytest.mark.parametrize("modo", demonstracao.MODOS)
def test_snapshot_is_clean_and_small(modo):
    alvo = demonstracao.PASTA_EXEMPLOS / f"{modo}.json"
    dados = json.loads(alvo.read_text(encoding="utf-8"))
    assert dados["erros"] == {}
    assert dados["modo"] == modo
    assert alvo.stat().st_size < 120_000
    assert "camadas" not in dados  # tile URLs expire; minted per request


def test_batch_example_uses_small_territories():
    dados = json.loads((demonstracao.PASTA_EXEMPLOS / "lote.json").read_text(encoding="utf-8"))
    assert len(dados["territorios"]) == len(demonstracao.LOTE)
    assert all(200 <= t["area_ha"] <= 1000 for t in dados["territorios"])


@pytest.mark.parametrize("sufixo", ["", ".en"])
@pytest.mark.parametrize("artigo", SCRIPTS)
def test_every_step_has_a_handler_and_every_print_exists(artigo, sufixo):
    html = (ARTIGOS / f"{artigo}{sufixo}.html").read_text(encoding="utf-8")
    js = (ARTIGOS / f"{SCRIPTS[artigo]}.js").read_text(encoding="utf-8")
    passos = re.findall(r'data-passo="([a-z0-9_-]+)"', html)
    assert passos
    # the batch article's first steps are prints only: no handler needed there
    com_dados = [p for p in passos if artigo != "lote" or p == "comparar"]
    assert [p for p in com_dados if not re.search(rf"\b{re.escape(p)}: function", js)] == []
    for img in re.findall(r'src="/demo_prints/([^"]+)"', html):
        assert (PRINTS / img).is_file(), img


@pytest.mark.parametrize("artigo", SCRIPTS)
def test_both_languages_match(artigo):
    pt, en = ((ARTIGOS / f"{artigo}{s}.html").read_text(encoding="utf-8") for s in ("", ".en"))
    for padrao in (r'data-passo="([a-z0-9_-]+)"', r'id="([a-z]+-[a-z-]+\d*)"', r'data-campo="([a-z-]+)"',
                   r'data-nota="(\d+)"', r'src="([^"]+)"'):
        assert re.findall(padrao, pt) == re.findall(padrao, en), padrao
    assert len(re.findall(r'<li id="nota-\d+">', pt)) == 5
    # each footer links to the other language
    assert 'lang="en"' in pt and 'lang="pt-BR"' in en


def test_english_routes_mirror_the_portuguese_ones():
    from yvynation.pages.demonstracao import PAGINAS, ROTA_EN

    rotas = [r for r, _p, _t in PAGINAS]
    # plus the English conservation walkthrough on a Kelowna park, which has no pt twin
    assert sorted(rotas) == sorted(list(ROTA_EN) + list(ROTA_EN.values()) + ["/walkthrough/conservation-unit"])
    assert all(r.startswith("/walkthrough/") for r in ROTA_EN.values())


def test_pages_render():
    from yvynation.pages.demonstracao import PAGINAS

    for _route, page, _title in PAGINAS:
        page().render()
