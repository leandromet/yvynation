"""``/demonstracao/<modo>`` (pt) e ``/walkthrough/<mode>`` (en) — os passos a passo
em rolagem, um por entrada do portal.

Os artigos são ``reportagem/*.html`` (pt) e ``*.en.html`` (en) sobre o kit
compartilhado; os números vêm de ``/_demonstracao/yvynation.json``
(utils/demonstracao.py) e os prints de ``assets/demo_prints/``. ``?area=``
troca a TI ou a UC de exemplo.
"""

from __future__ import annotations

from functools import partial

import reflex as rx

from ..reportagem.kit import pagina

#: (rota pt, rota en, artigo, script, título pt, título en)
_ARTIGOS = (
    ("/demonstracao/terra-indigena", "/walkthrough/indigenous-land", "terra_indigena", "yvynation_area",
     "Yvynation — demonstração: uma terra indígena", "Yvynation — walkthrough: an Indigenous land"),
    ("/demonstracao/unidade-conservacao", "/walkthrough/conservation-unit", "unidade_conservacao", "yvynation_area",
     "Yvynation — demonstração: uma unidade de conservação", "Yvynation — walkthrough: a conservation unit"),
    ("/demonstracao/desenho", "/walkthrough/drawn-area", "desenho", "yvynation_area",
     "Yvynation — demonstração: uma área desenhada", "Yvynation — walkthrough: a drawn area"),
    ("/demonstracao/lote", "/walkthrough/batch", "lote", None,
     "Yvynation — demonstração: processamento em lote", "Yvynation — walkthrough: batch processing"),
)


def _pagina(artigo: str, script: str | None, lingua: str) -> rx.Component:
    return pagina(artigo, script=script, lingua=lingua)


#: (rota, página, título) — registradas em yvynation.py
PAGINAS = tuple(
    (rota, partial(_pagina, artigo, script, lingua), titulo)
    for rota_pt, rota_en, artigo, script, titulo_pt, titulo_en in _ARTIGOS
    for rota, lingua, titulo in ((rota_pt, "pt", titulo_pt), (rota_en, "en", titulo_en))
)

#: rota pt → rota en, para os links do aplicativo seguirem a língua
ROTA_EN = {pt: en for pt, en, *_ in _ARTIGOS}
