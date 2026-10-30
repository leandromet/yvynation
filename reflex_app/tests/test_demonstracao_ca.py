"""The English conservation walkthrough (/walkthrough/conservation-unit): Okanagan Mountain Park.

No network: the example is the committed snapshot (scripts/build_demonstracao.py ca),
and the article checks are text checks on reportagem/unidade_conservacao_ca.en.html + yvynation_ca.js.
"""

import json
import re
from pathlib import Path

from yvynation.canada.services import demonstracao

ARTIGO = Path(__file__).resolve().parent.parent / "yvynation" / "reportagem"


def _dados():
    return json.loads(demonstracao.ARQUIVO_EXEMPLO.read_text(encoding="utf-8"))


def test_snapshot_is_clean_and_small():
    dados = _dados()
    assert dados["erros"] == {}
    assert demonstracao.ARQUIVO_EXEMPLO.stat().st_size < 120_000
    assert "camadas" not in dados
    assert dados["area"]["chave"] == demonstracao.EXEMPLO_PADRAO


def test_land_cover_adds_up_to_each_zone():
    """Pixel count × pixel area on one grid (canada/services/ee_zones.mean_pixel_area)."""
    dados = _dados()
    h = dados["historico"]
    for z in dados["zonas"]:
        soma = sum(serie[-1] for serie in h["zonas"][z["key"]].values())
        assert abs(soma - z["area_ha"]) / z["area_ha"] < 0.03, (z["key"], soma, z["area_ha"])


def test_every_step_has_a_handler():
    html = (ARTIGO / "unidade_conservacao_ca.en.html").read_text(encoding="utf-8")
    js = (ARTIGO / "yvynation_ca.js").read_text(encoding="utf-8")
    passos = re.findall(r'data-passo="([a-z0-9_-]+)"', html)
    assert len(passos) == 9
    assert [p for p in passos if not re.search(rf"\b{re.escape(p)}: function", js)] == []
    assert set(passos) <= set(re.findall(r'id="camada-([a-z0-9_-]+)"', html))
    assert sorted(set(re.findall(r'data-nota="(\d+)"', html))) == sorted(set(re.findall(r'id="nota-(\d+)"', html)))


def test_routes_and_pages():
    from yvynation.pages.demonstracao import PAGINAS, ROTA_EN

    rotas = {r: p for r, p, _ in PAGINAS}
    assert "/walkthrough/conservation-unit" in rotas and "/walkthrough/conservation-unit/brazil" in rotas
    # the Brazil page's own how-to keeps English readers on the Brazilian example
    assert ROTA_EN["/demonstracao/unidade-conservacao"] == "/walkthrough/conservation-unit/brazil"
    rotas["/walkthrough/conservation-unit"]().render()
