# yvynation — Claude Code Context

Plataforma interativa de monitoramento de terras indígenas brasileiras com análise de cobertura florestal via Google Earth Engine e MapBiomas.

**Autor**: Leandro Meneguelli Biondo (PhD Candidate, UBC Okanagan)  
**Licença**: MIT

> O diretório de trabalho primário é `yvynation/`, mas **o app ativo fica em
> `yvynation/reflex_app/`** — todo desenvolvimento ocorre lá.
> A raiz do repositório git é `/home/leandromb/google_eengine/yvynation/`.
> Os arquivos na raiz (fora de `reflex_app/`) são **legado Streamlit** — não editar.

## Mapa rápido

```
yvynation/
├─ .claude/
│  ├─ CLAUDE.md           ← este arquivo (orientação, sempre carregado)
│  ├─ ARCHITECTURE.md     ← estado, componentes, pages, utils, API
│  └─ WORKFLOW.md         ← comandos, portas, env, deploy, testes
│
├─ reflex_app/            ← APP ATIVO (Reflex 0.8.27)
│  ├─ rxconfig.py         ← configuração do framework (portas, DB)
│  ├─ requirements.txt    ← dependências Python
│  ├─ Dockerfile          ← multi-stage build para Cloud Run
│  ├─ .env.example        ← template de variáveis de ambiente
│  └─ yvynation/          ← pacote principal
│     ├─ app.py           ← entry point
│     ├─ yvynation.py     ← inicialização/routing
│     ├─ state/           ← estado reativo (8 mixins + AppState)
│     ├─ components/      ← componentes Reflex UI (24 módulos)
│     ├─ pages/           ← páginas da aplicação (5 páginas)
│     ├─ utils/           ← serviços de análise e dados (22 módulos)
│     ├─ config/          ← constantes e datasets Earth Engine
│     └─ api/             ← endpoints REST (map tiles)
│
├─ reflex_app/tests/      ← testes unitários
├─ docs/                  ← documentação legada (Streamlit)
└─ [*.py, *.md na raiz]   ← LEGADO Streamlit — não mexer
```

Detalhes de arquitetura em [ARCHITECTURE.md](ARCHITECTURE.md); comandos e ambiente em [WORKFLOW.md](WORKFLOW.md).

## Stack

- **Python 3.11**, **Reflex 0.8.27** (web framework full-stack Python → React/Vite)
- **Google Earth Engine** API (`earthengine-api 1.7.4`) — análise geoespacial remota
- **GeoPandas / Shapely / PyProj** — geometrias locais
- **Plotly / Matplotlib / Seaborn / Kaleido** — visualizações + export PNG
- **Leaflet.js + Leaflet-Draw** — mapa interativo (embutido via componentes Reflex)
- **Docker / Cloud Run** — deploy produção (single-port mode)
- **SQLite** (dev) ou Cloud SQL (prod) — persistência de sessões Reflex

## Dados geoespaciais locais

| Arquivo | Descrição | Tamanho |
|---|---|---|
| `utils/indigenous_lands_br202605.gpkg` | 657 TIs FUNAI (EPSG:4326) | 3,5 MB |
| `utils/environment_conservation_br202605.gpkg` | 3.247 UCs CNUC (EPSG:4326) | 10 MB |
| `utils/enso_oni.json` | NOAA CPC Oceanic Niño Index 1950–presente (faixa ENSO na timeline) | pequeno |

Os GeoPackages são carregados uma vez em memória via `territory_service.py` e
`conservation_service.py` (singletons de API idêntica). Tanto a análise
interativa (`AppState.territory_type`) quanto o batch
(`batch_territory_type`) alternam entre `"indigenous"` e `"conservation"` —
seleção, overlay do mapa, análises e timeline funcionam igual para ambos.

## Datasets Earth Engine

| Dataset | Coleção | Período | Resolução |
|---|---|---|---|
| MapBiomas | Collection 10.1 | 1985–2024 | 30 m |
| Hansen/GLAD GLCLU2020 | v2 | 2000–2020 | 30 m |
| Hansen GFC | global_forest_change_2025_v1_13 | 2000–2024 | 30 m |

## Convenções

- Todo desenvolvimento em `reflex_app/yvynation/`. Nunca editar arquivos na raiz do repo.
- Estado reativo: **sempre usar mixins** — cada domínio tem seu `_mixin.py` em `state/`.
- Componentes Reflex: funções que retornam `rx.Component`, sem estado próprio.
- Multi-idioma: strings de UI em `utils/translations.py` (EN/PT/ES) — **nunca hardcodar texto de UI**.
- `rx.select` com itens string exige `value` string de verdade: use um computed
  var `*_str` (ex. `comparison_year1_str`) — `.to(str)` NÃO converte em runtime
  e deixa o dropdown vazio.
- **Exports grandes**: nunca `rx.download(data=...)` (data-URI via websocket
  falha acima de ~50 MB). Gravar em `uploaded_files/exports/` e baixar com
  `rx.download(url=rx.get_upload_url(...))` — helpers em `utils/export_service.py`
  (`get_export_dir`, `save_export_to_upload_dir`, `DirExportWriter`, `zip_directory`).
  **Nunca apagar pasta de run sem o `.zip` homônimo existir** (run em andamento
  ou crashed — `prune_old_exports` já respeita isso).
- Não commitar/push sem pedido explícito. Mensagens de commit em inglês.
- GeoPackages locais não vão para git (ver `.gitignore`).
