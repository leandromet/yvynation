"""The scrolling walkthroughs (/demonstracao/<modo>): examples, articles, pages.

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


@pytest.mark.parametrize("artigo", SCRIPTS)
def test_every_step_has_a_handler_and_every_print_exists(artigo):
    html = (ARTIGOS / f"{artigo}.html").read_text(encoding="utf-8")
    js = (ARTIGOS / f"{SCRIPTS[artigo]}.js").read_text(encoding="utf-8")
    passos = re.findall(r'data-passo="([a-z0-9_-]+)"', html)
    assert passos
    # the batch article's first steps are prints only: no handler needed there
    com_dados = [p for p in passos if artigo != "lote" or p == "comparar"]
    assert [p for p in com_dados if not re.search(rf"\b{re.escape(p)}: function", js)] == []
    for img in re.findall(r'src="/demo_prints/([^"]+)"', html):
        assert (PRINTS / img).is_file(), img


def test_pages_render():
    from yvynation.pages.demonstracao import PAGINAS

    for _route, page, _title in PAGINAS:
        page().render()
