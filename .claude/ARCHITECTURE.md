# yvynation — Arquitetura

Todos os caminhos abaixo são relativos a `reflex_app/yvynation/` salvo indicação contrária.

## Estado reativo (`state/`)

AppState é composto por herança múltipla de 8 mixins (padrão Reflex `mixin=True`):

```
AppState(
    BatchMixin,        # batch_processing.py — seleção múltipla, execução em lote
    AdvancedVizMixin,  # _advanced_viz.py — overlays multi-dataset, timelines
    ExportMixin,       # _export.py — CSV / ZIP / PDF
    AnalysisMixin,     # _analysis.py — execução MapBiomas/Hansen, cache de resultados
    GeometryMixin,     # _geometry.py — geometrias desenhadas, buffers, upload
    TerritoryMixin,    # _territory.py — seleção de TI, busca, geometria EE
    MapMixin,          # _map.py — toggles de camadas, anos, base layer
    UIMixin,           # _ui.py — sidebar, abas, idioma, tutorial, erros
    rx.State,
)
```

### Variáveis de estado principais

| Grupo | Variáveis-chave |
|---|---|
| Init | `data_loaded`, `ee_initialized`, `loading_message`, `loading_type`, `error_message` |
| Idioma | `language` ("en"/"pt"/"es"), `auto_detect_enabled` |
| Mapa | `map_center`, `map_zoom`, `map_bounds`, `selected_base_layer` |
| Camadas | `mapbiomas_year`, `hansen_year`, `show_hansen_gfc_tree_cover`, `_tree_loss`, `_tree_gain` |
| Território | `selected_territory`, `territory_type` ("indigenous"/"conservation"), `territory_search_query`, `available_territories`, `territory_filter_state` |
| Geometrias | `drawn_features`, `buffer_geometries`, `current_buffer_for_analysis` |
| Análise | `analysis_results`, `all_analysis_results`, `active_target_kind`, `active_target_id` |
| Sidebar | `sidebar_open`, `sidebar_width`, `sidebar_*_expanded`, `is_resizing_sidebar` |
| Export | `export_pending`, `pending_export_zip_data` |
| Batch | `batch_mode`, `batch_selected_territories`, `batch_selected_count` |

### Event handlers por mixin

**UIMixin (`_ui.py`)**:
- `set_language(lang)` — troca idioma
- `toggle_sidebar()`, `update_sidebar_width(width)` — controle de sidebar
- `set_active_tab(tab)` — troca aba ativa
- `toggle_tutorial()`, `toggle_layer_reference()`
- `set_error(message)`

**MapMixin (`_map.py`)**:
- Toggles de camadas (MapBiomas, Hansen, AAFC, GFC)
- `set_mapbiomas_year(year)`, `set_hansen_year(year)`
- `set_base_layer(layer)`

**TerritoryMixin (`_territory.py`)**:
- `set_territory_type(t)` — alterna "indigenous" ↔ "conservation"; limpa a
  seleção e recarrega `available_territories` do serviço certo (`_get_service`)
- `set_selected_territory(name)` — seleciona área + despacha carga de geometria
  em background (GeoPackage local, sem EE)
- `select_territory_from_map(name)` — bridge JS do popup do mapa
- `set_territory_search_query(query)` — filtro reativo da lista
- `load_territory_geometry_bg()` — GeoJSON + bounds + auto-buffer

**GeometryMixin (`_geometry.py`)**:
- `save_drawing()` — salva feature desenhada + deduplica
- `delete_drawing(idx)`, `apply_buffer()`, `update_buffer_settings()`
- `toggle_buffer_compare_mode()`
- `handle_geometry_upload()` — processa upload de arquivo
- Classe: `BufferGeometry` (dataclass: name, distance, unit, geojson)

**AnalysisMixin (`_analysis.py`)**:
- `run_analysis(kind, source, year)` — executa MapBiomas/Hansen
- `run_comparison_analysis()` — comparação entre anos
- `_store_result(key, result)` — bundle por área em `all_analysis_results`
  (merge: preserva payloads de timeline/multi-window já salvos)
- `_save_adv_to_bundle(field, payload)` — anexa resultados de advanced-viz
  ("timeline" / "mw") ao bundle da área ativa
- `switch_result(key)` — reativa um bundle: resultado + comparação + timeline +
  multi-window (reconstrói as figuras por par)
- `remove_result(key)`, `set_active_target()`

**AdvancedVizMixin (`_advanced_viz.py`)**:
- `run_all_analysis()` — botão "Run all": despacha comparação + GLAD + GFC +
  multi-window + timeline + map set sobre o alvo ativo
- `run_multi_window_analysis_bg()` — transições multi-janela (Sankey multi-estágio,
  sunbursts/treemaps por par) para território e buffer
- `run_deforestation_timeline_bg()` — série anual Hansen/MapBiomas/fogo; a figura
  (em `visualization.create_deforestation_timeline_chart`) inclui faixas políticas,
  faixa ENSO (ONI) e tabela de políticas; `territory_type` muda demarcação → criação de UC
- `generate_map_set_bg()` — conjunto de mapas PNG (satélite + MapBiomas + aux)

**ExportMixin (`_export.py`)**:
- `export_analysis_zip()`, `export_pdf_maps()`, CSVs por dataset
- `download_all_results()` — ZIP com TODAS as áreas analisadas (dados + figuras +
  mapas + timeline + multi-window, uma pasta por área), montado direto em disco
- Entrega: ZIPs grandes vão para `uploaded_files/exports/` e baixam via
  `rx.download(url=rx.get_upload_url(...))` — nunca data-URI (ver CLAUDE.md)

---

## Componentes (`components/`)

Funções Python que retornam `rx.Component`. Sem estado próprio — leem do AppState.

| Arquivo | Linhas | Propósito |
|---|---|---|
| `analysis_tabs.py` | 2305 | Abas de resultados: MapBiomas, Hansen, geometria; gráficos Plotly; tabelas |
| `geometry_sidebar.py` | 723 | Controles de desenho, lista de features, configuração de buffer |
| `territory_sidebar.py` | 692 | Busca de TI, filtro por estado, lista com checkbox, metadados |
| `sidebar.py` | 564 | Controle de camadas: MapBiomas, Hansen, AAFC, GFC, base layer |
| `export_panel.py` | 225 | Botões CSV/ZIP/PDF, indicador de progresso |
| `map.py` | 230 | Container Leaflet, inicialização JS, overlay de camadas, métricas |
| `loading_indicator.py` | 188 | Overlay de loading com mensagem |
| `geometry_selector.py` | 276 | Seleção de geometria para análise |
| `geometry_manager.py` | 249 | Gerenciamento de features desenhadas |
| `layer_reference.py` | 219 | Guia de referência de camadas |
| `geometry_upload.py` | 216 | Handler de upload de arquivo |
| `map_simple.py` | 170 | Mapa simplificado |
| `feature_capture.py` | 132 | Captura de screenshot do mapa |
| `year_selector.py` | 130 | Seletor de ano |
| `tutorial.py` | 143 | Conteúdo do tutorial in-app |
| `leaflet.py` | 104 | Integração Leaflet.js |
| `layout.py` | 85 | Helpers de layout |
| `analysis_controls.py` | 73 | Botões de controle de análise |
| `results_panel.py` | 78 | Switcher de resultados armazenados |

---

## Páginas (`pages/`)

| Arquivo | Rota | Propósito |
|---|---|---|
| `index.py` | `/` | Página principal: navbar, sidebar, mapa Leaflet, abas de análise |
| `batch_processing.py` | `/batch` | Processamento em lote (3 etapas: seleção → config → execução + ZIP) |
| `portal.py` | `/portal` | Visualizador/portal de dados por território |
| `geometry_analysis.py` | `/geometry-analysis` | Stub para análise de geometria específica |
| `territory_analysis.py` | `/territory-analysis` | Stub para análise de território específico |

**`index.py`** expõe:
- `active_target_bar()` — switcher de alvo de análise + botão "Run all"
- `navbar()` — navegação superior com toggle de sidebar
- Layout: `navbar` + `sidebar` + `map` + `analysis_tabs`

---

## Utilitários (`utils/`)

### Serviços de dados

| Módulo | Propósito |
|---|---|
| `ee_service.py` | Init Earth Engine (multi-método: env vars → ADC → service account); suporte Cloud Run |
| `territory_service.py` | Singleton: carrega `indigenous_lands_br202605.gpkg` (657 TIs) em memória |
| `conservation_service.py` | Singleton: carrega `environment_conservation_br202605.gpkg` (10 MB) |

**Auth Earth Engine** (ordem de tentativa em `ee_service.py`):
1. `EE_PRIVATE_KEY` env var (Cloud Run — chave split)
2. Application Default Credentials (ADC)
3. JSON file em `SERVICE_ACCOUNT_JSON`

### Análise geoespacial

| Módulo | Propósito |
|---|---|
| `mapbiomas_analysis.py` | Extração de áreas por classe, matriz de transição, comparação entre anos |
| `hansen_analysis.py` | Cobertura arbórea, perda/ganho florestal, filtro temporal |
| `aafc_analysis.py` | Dados de cobertura do solo AAFC (canadense) |
| `deforestation_timeline.py` | Tendências anuais de desmatamento, totais cumulativos |
| `analysis.py` | Helpers genéricos de análise |
| `geometry_handler.py` | Processamento Shapely (transformações, validação) |
| `buffer_utils.py` | Cálculo de buffers em metros sobre feature collections |

### Visualização e exportação

| Módulo | Tamanho | Propósito |
|---|---|---|
| `visualization.py` | ~80 KB | Gráficos Plotly (barras, sankey, sunburst, treemap, matriz); timeline de desmatamento com contexto político + faixa ENSO (lê `enso_oni.json`) + tabela de políticas |
| `export_service.py` | ~45 KB | Estrutura do ZIP de export (seções mapbiomas/glad/gfc/multi-window/timeline); entrega via `uploaded_files/exports/` (`get_export_dir`, `save_export_to_upload_dir`, `DirExportWriter`, `zip_directory`, `prune_old_exports`) |
| `map_export_service.py` | 24 KB | Captura Leaflet + PNG (Kaleido) + layout PDF com metadados |
| `map_builder.py` | 39 KB | Construção de mapas Leaflet: tile layers, WMS, GeoJSON styling, Leaflet-Draw |

### Infraestrutura

| Módulo | Propósito |
|---|---|
| `translations.py` | 52 KB — ~1000+ strings EN/PT/ES; sempre usar para texto de UI |
| `ee_layers.py` | Definições de camadas Earth Engine |
| `tile_manager.py` | Gerenciamento de tiles/camadas web |
| `map_manager.py` | Instância de mapa |
| `ee_service_extended.py` | Operações EE avançadas |
| `policy_context_brazil.py` | Dados de políticas ambientais por estado (38 KB) |
| `political_context_brazil.py` | Contexto político/administrativo (35 KB) |

---

## API (`api/`)

**`map_routes.py`** (6,5 KB):
- Endpoints REST para servir tiles de mapa (estilo WMS/XYZ)
- Endpoints GeoJSON
- Serving de dados raster

---

## Configuração (`config/`)

**`config.py`** (24 KB):
- IDs de assets Earth Engine (MapBiomas v10.1, Hansen GLCLU2020 v2, GFC 2025)
- `GCP_PROJECT_ID`: `"ee-leandromet"`
- Export bucket: `"gs://yvynation-bucket"`
- Resolução export: 30 m
- Região de interesse: Brasil `[-73°, -33°, -35°, 5°]`
- Paletas de cores (Hansen 256 cores, MapBiomas 62 classes)

**`mapbiomas-user-toolkit-lulc.js`** e **`mapbiomas-deforestation-secondary.js`**: scripts JS MapBiomas para Earth Engine Code Editor (referência).

---

## Fluxo de dados

```
Interação usuário
    → Event handler (state/mixin)
    → Mutação de variável de estado
    → Re-render automático dos componentes dependentes

Análise:
    AppState._analysis.run_analysis()
    → ee_service.py (init EE)
    → mapbiomas_analysis.py / hansen_analysis.py
    → visualization.py (gera gráficos Plotly)
    → _store_result() → all_analysis_results dict

Export:
    AppState._export.export_analysis_zip() / download_all_results()
    → export_service.collect_export_data_from_state() + create_export_zip()
      (mapbiomas + hansen_glad + hansen_gfc + mapbiomas_multi_window +
       deforestation_timeline, território e buffer)
    → uploaded_files/exports/*.zip
    → rx.download(url=rx.get_upload_url(...)) — HTTP streaming, sem limite de tamanho

Batch:
    pages/batch_processing.py  (lista colável/upload → auto-seleção;
                                fontes: indigenous | conservation)
    → BatchMixin.run_batch_processing (state/_batch.py)
      N workers puxam territórios de uma asyncio.Queue (paralelo);
      dentro de cada região, TODAS as análises EE independentes vão
      juntas via asyncio.gather; renderização (kaleido/pyplot) é
      SERIALIZADA num pool de 1 worker — ver utils/ee_concurrency.py
      e docs/BATCH_CONCURRENCY.md (perfis de tier + rollback)
    → DirExportWriter grava arquivos AO VIVO em
      uploaded_files/exports/yvynation_batch_{YYYYMMDD_HHMMSS}/
      (navegável durante a execução; sem compressão no loop)
    → zip_directory() ao final (inclusive no "Stop after current")
      → yvynation_batch_{ts}.zip; pasta removida após sucesso
    → download_batch_zip() via rx.get_upload_url
    Regra: prune_old_exports() só apaga pasta se existir o .zip homônimo
    (pasta sem zip = run em andamento ou crashed — nunca tocar)
```
