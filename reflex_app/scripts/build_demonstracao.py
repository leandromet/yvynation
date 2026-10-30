"""Regrava os exemplos das demonstrações (yvynation/reportagem/exemplos/*.json).

    python scripts/build_demonstracao.py            # os quatro modos
    python scripts/build_demonstracao.py lote       # um só
    python scripts/build_demonstracao.py ca         # o parque de Kelowna (UC em inglês)

Calcula o exemplo de cada modo pelas mesmas funções das páginas de análise
(utils/demonstracao.py::instantaneo) e grava o pacote sem as camadas, com
geometrias leves, para as páginas /demonstracao/<modo> abrirem na hora. Rode de
novo quando uma coleção mudar (MapBiomas, Hansen) e faça commit dos arquivos.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from yvynation.canada.services import demonstracao as demonstracao_ca  # noqa: E402
from yvynation.utils import demonstracao  # noqa: E402


def main(modos: list[str]) -> int:
    pasta = demonstracao.PASTA_EXEMPLOS
    pasta.mkdir(parents=True, exist_ok=True)
    falhas = 0
    for modo in modos or (*demonstracao.MODOS, "ca"):
        if modo == "ca":
            from yvynation.utils.ee_service import initialize_earth_engine
            initialize_earth_engine()
            dados = demonstracao_ca.instantaneo()
            if dados["erros"]:
                print(f"ca: análises com erro, nada gravado: {dados['erros']}")
                falhas += 1
                continue
            alvo = demonstracao_ca.ARQUIVO_EXEMPLO
            alvo.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            print(f"{alvo} — {alvo.stat().st_size // 1024} KB")
            continue
        dados = demonstracao.instantaneo(modo)
        if dados["erros"]:
            print(f"{modo}: análises com erro, nada gravado: {dados['erros']}")
            falhas += 1
            continue
        alvo = pasta / f"{modo}.json"
        alvo.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"{alvo} — {alvo.stat().st_size // 1024} KB")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
