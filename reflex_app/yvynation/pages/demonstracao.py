"""``/demonstracao/<modo>`` — os passos a passo em rolagem, um por entrada do portal.

Os artigos são ``reportagem/*.html`` sobre o kit compartilhado; os números vêm
de ``/_demonstracao/yvynation.json`` (utils/demonstracao.py) e os prints de
``assets/demo_prints/``. ``?area=`` troca a TI ou a UC de exemplo.
"""

from __future__ import annotations

import reflex as rx

from ..reportagem.kit import pagina


def demonstracao_terra_indigena() -> rx.Component:
    return pagina("terra_indigena", script="yvynation_area")


def demonstracao_unidade_conservacao() -> rx.Component:
    return pagina("unidade_conservacao", script="yvynation_area")


def demonstracao_desenho() -> rx.Component:
    return pagina("desenho", script="yvynation_area")


def demonstracao_lote() -> rx.Component:
    return pagina("lote")


#: (rota, página, título) — registradas em yvynation.py
PAGINAS = (
    ("/demonstracao/terra-indigena", demonstracao_terra_indigena,
     "Yvynation — demonstração: uma terra indígena"),
    ("/demonstracao/unidade-conservacao", demonstracao_unidade_conservacao,
     "Yvynation — demonstração: uma unidade de conservação"),
    ("/demonstracao/desenho", demonstracao_desenho,
     "Yvynation — demonstração: uma área desenhada"),
    ("/demonstracao/lote", demonstracao_lote,
     "Yvynation — demonstração: processamento em lote"),
)
