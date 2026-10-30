"""``/demonstracao/<modo>`` (pt) e ``/walkthrough/<mode>`` (en) — os passos a passo
em rolagem, um por entrada do portal.

Os artigos são ``reportagem/*.html`` (pt) e ``*.en.html`` (en) sobre o kit
compartilhado; os números vêm de ``/_demonstracao/yvynation.json``
(utils/demonstracao.py) e os prints de ``assets/demo_prints/``. ``?area=``
troca a TI ou a UC de exemplo.

A UC em inglês abre um parque de Kelowna (``unidade_conservacao_ca`` +
``yvynation_ca.js``, números de ``canada/services/demonstracao.py``); a versão
em inglês do exemplo brasileiro fica em ``/walkthrough/conservation-unit/brazil``.
As outras três seguem brasileiras em inglês: a página do Canadá não tem
desenho nem lote, e terras indígenas não entram nela (OCAP®).
"""

from __future__ import annotations

from functools import partial

import reflex as rx

from ..reportagem.kit import pagina

#: (rota pt, rota en, artigo, script, título pt, título en)
_ARTIGOS = (
    ("/demonstracao/terra-indigena", "/walkthrough/indigenous-land", "terra_indigena", "yvynation_area",
     "Yvynation — demonstração: uma terra indígena", "Yvynation — walkthrough: an Indigenous land"),
    ("/demonstracao/unidade-conservacao", "/walkthrough/conservation-unit/brazil", "unidade_conservacao", "yvynation_area",
     "Yvynation — demonstração: uma unidade de conservação", "Yvynation — walkthrough: a conservation unit (Brazil)"),
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
) + (
    # the English conservation walkthrough: a park in Kelowna, from the Canada page's services
    ("/walkthrough/conservation-unit", partial(_pagina, "unidade_conservacao_ca", "yvynation_ca", "en"),
     "Yvynation — walkthrough: a protected area in Kelowna"),
)

#: rota pt → rota en, para os links do aplicativo seguirem a língua
ROTA_EN = {pt: en for pt, en, *_ in _ARTIGOS}
