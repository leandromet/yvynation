# yvynation — Workflow e Comandos

## Setup inicial

```bash
# A partir da raiz do repo
cd /home/leandromb/google_eengine/yvynation/reflex_app

# Ambiente virtual (já existe em ../.venv)
source ../.venv/bin/activate       # ou: python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Variáveis de ambiente
cp .env.example .env
# Editar .env: GCP_PROJECT_ID, SERVICE_ACCOUNT_JSON
```

## Comandos de desenvolvimento

Todos executados a partir de `reflex_app/`:

```bash
# Iniciar app (desenvolvimento)
reflex run

# Build de produção
reflex export

# Inicializar projeto (primeira vez ou após limpar .web/)
reflex init

# Rodar com ambiente específico
REFLEX_ENV=prod reflex run --env prod
```

**Portas**:
- Frontend: **3000**
- Backend (API): **8000**
- Cloud Run: `$PORT` (single-port mode)

## Variáveis de ambiente (`.env`)

```bash
GCP_PROJECT_ID=ee-leandromet              # ID projeto Google Cloud
SERVICE_ACCOUNT_JSON=/path/to/key.json    # Service account para Earth Engine
REFLEX_ENV=dev                             # dev | prod
REFLEX_LOG_LEVEL=info                      # info | debug
DEBUG=false
PORT=3000
HOST=0.0.0.0
EE_INITIALIZE_ON_STARTUP=true
EE_USE_SERVICE_ACCOUNT=true
REFLEX_DB_URL=sqlite:///reflex.db         # ou Cloud SQL URL em prod
EE_PRIVATE_KEY=...                        # Cloud Run: chave EE como env var (formato split)
```

## Autenticação Earth Engine

Hierarquia de autenticação em `utils/ee_service.py`:
1. `EE_PRIVATE_KEY` env var (Cloud Run)
2. Application Default Credentials: `gcloud auth application-default login`
3. JSON file apontado por `SERVICE_ACCOUNT_JSON`

```bash
# ADC local
gcloud auth application-default login
gcloud config set project ee-leandromet
```

## Testes

```bash
cd reflex_app
pytest tests/                        # todos os testes
pytest tests/test_state.py          # testes de estado
pytest tests/test_analysis.py       # testes de análise
pytest -v tests/                    # verbose
```

## Docker / Cloud Run

```bash
cd reflex_app

# Build local
docker build -t yvynation .

# Run local
docker run -p 8080:8080 \
  -e GCP_PROJECT_ID=ee-leandromet \
  -e EE_PRIVATE_KEY="..." \
  yvynation

# Deploy Cloud Run (via gcloud)
gcloud run deploy yvynation \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=ee-leandromet
```

**Dockerfile**: multi-stage, base Python 3.11-slim, instala GDAL + Bun, executa `reflex init` no build.  
**Modo produção**: `reflex run --env prod --single-port --backend-port ${PORT}`

## Estrutura de deploy

| Ambiente | Framework | Porta | Autenticação EE |
|---|---|---|---|
| Desenvolvimento local | Reflex dev server | 3000 (FE) + 8000 (BE) | ADC ou JSON file |
| Docker local | Reflex prod | 8080 | Env vars |
| Cloud Run | Reflex prod single-port | $PORT (8080) | `EE_PRIVATE_KEY` env var |

## Git

```bash
# Root do repositório git
cd /home/leandromb/google_eengine/yvynation

git status
git log --oneline -10
git diff HEAD

# Nunca commitar/push sem pedido explícito do usuário
# GeoPackages (.gpkg) estão no .gitignore — não forçar
```

## Convenções de código

- **Texto de UI**: sempre usar chave de `utils/translations.py` — nunca hardcodar strings
- **Estado**: adicionar variáveis e handlers no mixin correto (`state/_ui.py`, `state/_map.py`, etc.)
- **Novo domínio de estado**: criar `state/_novo_dominio.py` como mixin e adicionar a `AppState` em `state/__init__.py`
- **Componentes**: funções Python retornando `rx.Component`; sem estado próprio
- **Renderização condicional**: `rx.cond(var, true_component, false_component)`
- **Loops**: `rx.foreach(state_list, lambda item: component_fn(item))`
- **Computed vars**: `@rx.var` decorador para derivações de estado

## Localização dos serviços externos

| Serviço | Onde |
|---|---|
| Earth Engine | `utils/ee_service.py` + `utils/ee_service_extended.py` |
| MapBiomas API | `utils/mapbiomas_analysis.py` |
| Hansen/GLAD | `utils/hansen_analysis.py` |
| Export GCS | `utils/export_service.py` (bucket `gs://yvynation-bucket`) |
| Configuração de assets EE | `config/config.py` |

## Arquivos para NÃO editar

- Qualquer arquivo na raiz `/home/leandromb/google_eengine/yvynation/` fora de `reflex_app/` — são legado Streamlit
- `reflex_app/.web/` — artefatos de build gerados pelo Reflex
- `reflex_app/yvynation/utils/indigenous_lands_br202605.gpkg` — dado geoespacial fixo
- `reflex_app/yvynation/utils/environment_conservation_br202605.gpkg` — dado geoespacial fixo
- `reflex_app/reflex.db` — banco SQLite de sessões (gerado em runtime)
