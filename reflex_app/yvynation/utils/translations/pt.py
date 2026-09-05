"""Portuguese translations for Yvynation.

One file per language: add/edit keys here only. English (en.py)
is the reference dictionary — every key must exist there; other
languages fall back to English for any missing key.
Check coverage with:  python -m yvynation.utils.translations
"""

TRANSLATIONS_PT = {
        # Page
    "page_title": "Yvynation - Monitoramento Territorial Indígena",
    "main_page_title": "Yvynation - Plataforma de Monitoramento Territorial",
    "app_title": "Yvynation",
    "app_subtitle": "Plataforma de Monitoramento Territorial",
    "app_description": "Plataforma Global de Monitoramento Florestal",
    "author": "Leandro M. Biondo - Candidato de PhD - IGS/UBCO",

    # Navigation
    "map_tab": "Mapa",
    "analysis_tab": "Análise",
    "tutorial_tab": "Tutorial",
    "about_tab": "Sobre",

    # Sidebar
    "sidebar_title": "Camadas e Controles",
    "controls_badge": "Controles",
    "mapbiomas_label": "MapBiomas",
    "mapbiomas_section_title": "Camadas MapBiomas",
    "mapbiomas_select_year": "Selecionar Ano MapBiomas",
    "mapbiomas_years": "Anos MapBiomas",
    "mapbiomas_layers_label": "Camadas MapBiomas",
    "mapbiomas_layers_hint": "Número de camadas MapBiomas ativas",
    "no_mapbiomas_selected": "Nenhum ano MapBiomas selecionado",
    "no_mapbiomas_added": "Adicione camadas MapBiomas na barra lateral",
    "add_to_map": "Adicionar ao mapa",
    "clear_all": "Limpar tudo",

    "hansen_label": "Hansen GFC",
    "hansen_section_title": "Hansen GFC",
    "hansen_select_year": "Selecionar Ano Hansen",
    "hansen_years": "Anos Hansen",
    "hansen_layers_label": "Camadas Hansen",
    "hansen_layers_hint": "Número de camadas Hansen ativas",
    "hansen_gfc_label": "Mudança Florestal Global (GFC)",
    "hansen_gfc_layers_label": "Camadas GFC",
    "no_hansen_selected": "Nenhum ano Hansen selecionado",
    "no_hansen_added": "Adicione camadas Hansen na barra lateral",
    "no_hansen_gfc_added": "Nenhuma camada GFC habilitada",
    "data_layers": "Camadas de dados",
    "year_layers": "Camadas por ano",
    "tree_cover_btn": "Cobertura",
    "loss_btn": "Perda",
    "gain_btn": "Ganho",
    "add_btn": "Adicionar",

    "tree_cover_2000": "Cobertura Arbórea 2000",
    "tree_loss_period": "Perda Florestal (2000-2023)",
    "tree_gain_period": "Ganho Florestal (2000-2012)",

    # Base layer
    "base_layer": "Camada Base",
    "base_layer_hint": "Mapa base atual",

    # Active layers
    "active_layers": "Camadas Ativas",
    "analysis_active_badge": "Análise Ativa",

    # Territory section
    "territory_section_title": "Análise de Território",
    "select_territory": "Selecionar Território",
    "territory_by_country": "Filtrar por País",
    "territory_by_state": "Filtrar por Estado",
    "selected_territory": "Território Selecionado",
    "no_territory_selected": "Nenhum território selecionado",
    "search_territories": "Buscar territórios...",
    "select_territory_placeholder": "Selecionar território",
    "click_map_to_select": "Clique nos marcadores do mapa",
    "show_all_lands": "Mostrar Todas as Terras",
    "hide_all_lands": "Ocultar Todas as Terras",
    "select_territory_above": "Selecione um território acima",
    "compare_years": "Comparar anos",
    "compare_mapbiomas_years": "Comparar Anos MapBiomas",

    # Geometry section
    "geometry_section_title": "Geometria e Desenho",
    "upload_geometry_file": "Enviar arquivo de geometria",
    "analyze_selected_geometry": "Analisar geometria selecionada",
    "map_overlays": "Sobreposições do mapa",
    "show_geometries": "Mostrar Geometrias",
    "hide_geometries": "Ocultar Geometrias",
    "show_change": "Mostrar Mudança",
    "hide_change": "Ocultar Mudança",

    # Map controls
    "draw_polygon": "Desenhar Polígono",
    "clear_drawings": "Limpar Tudo",
    "upload_geojson": "Upload GeoJSON",

    # Analysis
    "run_analysis": "Executar Análise",
    "analysis_results": "Resultados da Análise",
    "mapbiomas_analysis": "Análise MapBiomas",
    "hansen_analysis": "Análise Hansen",
    "export_results": "Exportar Resultados",
    "comparing_label": "Comparando...",

    # Comparison
    "compare_label": "Comparar:",
    "vs_label": "vs",
    "compare_btn": "Comparar",
    "year_comparison_results": "Resultados da Comparação de Anos",
    "download_comparison_csv": "Baixar CSV da Comparação",
    "total_gains": "Ganhos Totais",
    "total_losses": "Perdas Totais",
    "net_change": "Mudança Líquida",
    "comparison_available": "Comparação Disponível",

    # Buttons
    "confirm": "Confirmar",
    "cancel": "Cancelar",
    "close": "Fechar",
    "select": "Selecionar",
    "dismiss": "Dispensar",

    # Messages
    "loading": "Carregando...",
    "analyzing": "Analisando...",
    "initializing": "Inicializando Plataforma Yvynation...",
    "ee_init_error": "Falha ao inicializar Earth Engine: {error}",
    "error": "Erro",
    "success": "Sucesso",

    # Analysis results
    "class": "Classe",
    "area_hectares": "Área (ha)",
    "area_km2": "Área (km2)",
    "percentage": "Percentual (%)",
    "year": "Ano",
    "change": "Mudança",
    "from_class": "De Classe",
    "to_class": "Para Classe",
    "area_changed": "Área Mudada",

    # File upload
    "upload_file": "Enviar Arquivo",
    "file_uploaded": "Arquivo enviado com sucesso",
    "file_upload_error": "Erro ao enviar arquivo",
    "select_file": "Selecione arquivo (GeoJSON, KML, Shapefile)",

    # Buffer operations
    "buffer_distance": "Distância do Buffer (metros)",
    "create_buffer": "Criar Buffer",
    "buffer_created": "Buffer criado com sucesso",

    # Geometry
    "draw_area": "Desenhar Área de Interesse",
    "upload_geometry": "Enviar Geometria",
    "geometry_loaded": "Geometria carregada",

    # Export
    "export_as_csv": "Exportar como CSV",
    "export_as_pdf": "Exportar como PDF",
    "export_as_zip": "Exportar como ZIP",
    "exporting": "Exportando...",
    "export_complete": "Exportação concluida",
    "export_analysis": "Exportar Análise",

    # MapBiomas specific
    "mapbiomas_no_data": "Nenhum dado disponível para a área selecionada",
    "mapbiomas_process_error": "Erro ao processar classe {class_id}: {error}",
    "mapbiomas_analysis_title": "Análise de Cobertura Terrestre MapBiomas",
    "mapbiomas_year_range": "Intervalo de anos: {start} - {end}",
    "area_basis_note": "A área é calculada a partir do tamanho geodésico real de cada pixel (pixelArea do Earth Engine), não de uma suposição fixa de 900 m² (0,09 ha) — assim permanece precisa em qualquer latitude.",

    # Hansen specific
    "hansen_tree_cover": "Cobertura Arbórea",
    "hansen_tree_loss": "Perda Florestal",
    "hansen_tree_gain": "Ganho Florestal",
    "hansen_no_data": "Nenhum dado Hansen para a área selecionada",

    # Settings / Quick settings
    "language": "Idioma",
    "theme": "Tema",
    "dark_mode": "Modo Escuro",
    "light_mode": "Modo Claro",

    # Help & Info
    "help": "Ajuda",
    "documentation": "Documentação",
    "about": "Sobre Yvynation",
    "version": "Versão",
    "powered_by": "Desenvolvido por",

    # =====================================================================
    # Tutorial / Getting Started
    # =====================================================================
    "getting_started_header": "Como Usar Esta Plataforma",
    "getting_started_title": "Primeiros Passos",
    "getting_started_intro": "Esta plataforma permite análise abrangente de cobertura do solo para o Brasil e monitoramento florestal global. Você pode analisar áreas personalizadas, territórios indígenas e zonas de amortecimento externas.",

    "step_language_region": "Passo 0: Seleção de Idioma e Região",
    "step0_language_region_intro": "Configure seu idioma e selecione sua região de interesse:",
    "step0_content": """**Autodetecção na Primeira Visita**

Na sua primeira visita, o aplicativo pode detectar sua localização para definir a região correta:
- **América do Norte** (latitude > 10N) -> Define Canadá
- **América do Sul** -> Usa o idioma do navegador ou Português (PT)
- Você pode revisar ou alterar a configuração a qualquer momento

**Seleção Manual de Idioma**

Use os botões de idioma (EN / PT / ES) na barra lateral para trocar o idioma. Sua escolha é salva para sua sessão.

**Seleção Manual de Região**

Use os botões de região (Brasil / Canadá) na barra lateral para escolher entre:
- **Brasil**: Cobertura completa MapBiomas (1985-2024) + dados globais Hansen/GLAD
- **Canadá**: Inventário de cultivos AAFC + dados globais Hansen/GLAD

O mapa será centralizado na região selecionada.""",

    "step_custom_polygon": "Passo 1: Analisar um Polígono Personalizado",
    "step1_draw_intro": "Desenhe e análise qualquer área no mapa:",
    "step1_content": """1. **Ferramentas de Desenho** (canto superior esquerdo do mapa):
   - Clique na ferramenta **Retângulo** para seleções retangulares rápidas
   - Clique na ferramenta **Polígono** para formas personalizadas
   - Clique duplo ou clique no primeiro ponto novamente para completar

2. **Selecione Camadas de Dados** (barra lateral esquerda):
   - **MapBiomas**: Cobertura do solo brasileira (1985-2024, 62 classes, 30m)
   - **Hansen/GLAD**: Mudanças florestais globais (2000-2020, 256 classes, 30m)
   - **Hansen GFC**: Mudanças Florestais Globais (2000-2024, 30m)
   - Alterne vários anos para habilitar comparações

3. **Resultados da Análise**:
   - Distribuição de cobertura do solo por classe
   - Estatísticas de área (hectares e percentuais)
   - Gráficos visuais e tabelas de dados
   - Arquivos CSV para download

4. **Análise de Zona de Buffer**:
   - Após desenhar, clique em "Criar Buffer"
   - Escolha a distância: 2km, 5km ou 10km
   - Cria uma zona em forma de anel ao redor do polígono
   - Análise ambas as áreas lado a lado

**Dicas**: Exclua polígonos indesejados com o ícone de lixeira. Use zonas de buffer para entender efeitos de borda.""",

    "step_territory": "Passo 2: Analisar um Território Indígena",
    "step2_territory_intro": "Limites de territórios indígenas pré-definidos com análise histórica:",
    "step2_content": """1. **Selecionar Território** (seção Análise de Território na barra lateral):
   - Pesquise ou navegue por todos os territórios
   - Escolha entre 400+ terras indígenas reconhecidas
   - Veja metadados do território: área, localização, status

2. **Recursos de Análise de Território**:
   - Mudanças históricas de cobertura do solo (1985-2024)
   - Mudanças de área por classe de cobertura
   - Tendências de desmatamento e regeneração
   - Diagramas de transição (Sankey) mostrando conversões entre classes
   - Exportar todos os dados e visualizações

3. **Análise de Zona de Amortecimento**:
   - Crie zonas externas (2km/5km/10km) ao redor do território
   - Compare uso do solo dentro vs fora da fronteira protegida
   - Identifique zonas de pressão e padrões de invasão
   - Resultados aparecem em abas separadas

**Dicas**: Compare múltiplos territórios. Comparações de longo prazo (1985 vs 2023) revelam efetividade da proteção.""",

    "step_comparison": "Passo 3: Comparação Multi-Anual",
    "step3_comparison_intro": "Compare mudanças de cobertura do solo entre quaisquer dois anos:",
    "step3_content": """1. **Configurar Comparação** (aba Comparação):
   - Selecione 2+ anos nos controles de camada (barra lateral)
   - Desenhe um polígono ou selecione um território
   - Escolha Ano 1 (linha de base) e Ano 2 (comparação)

2. **Clique nos Botoes de Comparação**:
   - **Comparar Anos MapBiomas**: Mudanças de cobertura do solo
   - **Comparar Anos Hansen**: Mudanças de floresta global

3. **Ver Resultados**:
   - **Tabela de Dados**: Valores de área lado a lado com calculos de mudança
   - **Gráficos lado a lado**: Distribuição visual para cada ano
   - **Ganhos e Perdas**: Gráfico de barras horizontal
   - **Diagrama Sankey**: Fluxo de transições de cobertura
   - **Métricas de Resumo**: Valores totais de mudança, perda e ganho

**Dicas**: Compare 1985 vs 2023 para 38 anos de mudança. Use intervalos de 5 anos para identificar grandes eventos.""",

    "step_export": "Passo 4: Exportar e Baixar Resultados",
    "step4_export_intro": "Salve seus resultados para relatórios e análise adicional:",
    "step4_content": """- **Downloads CSV**: Clique nos botões "Baixar CSV" em cada aba de análise
  - Dados de ano individual com estatísticas de área
  - Tabelas de comparação com calculos de mudança

- **Exportações PNG**: Imagens de alta resolucao do Earth Engine
  - Exporte regioes de análise como imagens georreferenciadas
  - Adequado para software SIG e publicacoes

- **Relatórios PDF** (futuro): Resumos de análise abrangentes

**Dica**: Todos os downloads usam convenções de nomenclatura consistentes para facil organização.""",

    "step_map_controls": "Passo 5: Controles do Mapa e Navegação",
    "step5_map_controls_intro": "Navegue e interaja com o mapa:",
    "step5_content": """**Navegação Básica:**
- **Zoom In/Out**: Roda de scroll do mouse, botões +/-, ou clique duplo
- **Pan**: Clique e arraste em qualquer lugar do mapa
- **Tela Cheia**: Clique no botão de tela cheia para vista maior

**Ferramentas de Desenho** (canto superior esquerdo):
- Editar Camadas: Modifique polígonos existentes
- Excluir Camadas: Remova polígonos indesejados
- Desenhar Retângulo: Áreas retangulares rápidas
- Desenhar Polígono: Formas com múltiplos pontos
- Finalizar Desenho: Clique duplo ou clique no primeiro ponto

**Controles de Camada** (canto superior direito):
- Camadas Base: Alterne entre OpenStreetMap, Satélite, Terreno
- Sobreposições: Alterne camadas MapBiomas e Hansen
- Limites de Território: Mostrar/ocultar limites de territórios indígenas

**Recursos do Mapa:**
- Anéis azuis: Zonas de amortecimento externas
- Polígonos coloridos: Áreas de análise desenhadas
- Limites de território: Limites de terras indígenas pré-carregados""",

    "step_data_understanding": "Passo 6: Entendendo os Dados e Resultados",
    "step6_data_understanding_intro": "Saiba sobre as fontes de dados e como interpretar resultados:",
    "step6_content": """**Fontes de Dados:**

**MapBiomas Collection 10** (Brasil):
- Cobertura: Todo o Brasil, 1985-2024
- Resolução: 30 metros (baseado em Landsat)
- Classes: 62 tipos de cobertura (floresta, savana, agricultura, urbano, etc.)
- Precisão: ~90% no geral (varia por classe e região)

**Hansen/GLAD Global Forest Change**:
- Cobertura: Global (todos os continentes)
- Resolução: 30 metros (baseado em Landsat)
- Classes: 256 classes combinando cobertura florestal, ano de perda (2000-2020), ganho (2000-2012)
- Melhor para: Detecção e monitoramento de mudanças florestais

**Interpretação de Resultados:**
- **Área (ha)**: Hectares = 10.000 m2 (cerca de 2,5 acres)
- **Pixels**: Cada pixel = 900 m2 (30m x 30m)
- **Percentagens**: Calculadas a partir da área total analisada
- **Valores de mudança**: Positivo = aumento, Negativo = diminuição

**Gráficos**: Gráficos de barras mostram as 15 principais classes. Diagramas Sankey mostram transições. Barras de Ganhos e Perdas mostram aumentos (direita) e diminuições (esquerda).""",

    # About section
    "about_title": "Sobre",
    "about_overview": "Visão Geral do Projeto",
    "about_desc": "Esta ferramenta de análise de uso e cobertura do solo faz parte de um projeto de pesquisa que estuda mudanças ambientais em Territórios Indígenas Brasileiros usando Google Earth Engine e dados MapBiomas. Estes dados sao comparados com mudanças de políticas e tendências de desmatamento para entender os impactos nestas terras críticas.",
    "about_author": "Leandro Meneguelli Biondo",
    "about_role": "Candidato de PhD em Sustentabilidade",
    "about_university": "IGS/UBCO",
    "about_supervisor": "Orientador: Dr. Jon Corbett",
    "about_app_name": "Yvynation",
    "about_app_note": "é um nome para este aplicativo, não é o conteúdo completo do projeto.",
    "yvynation_meaning": '"Yvy" (Tupi-Guarani) significa terra, solo ou território - enfatizando o chao que pisamos e nossa conexao sagrada com a natureza. Frequentemente se relaciona ao conceito de "Yvy marae\'y" (Terra sem mal).',
    "nation_meaning": '"Nação" refere-se a uma comunidade auto-governada ou povo com cultura, história, língua e terra compartilhadas. Significa autodeterminacao e governança.',
    "data_sources_title": "Fontes de Dados",
    "mapbiomas_desc": "MapBiomas Collection 10 - Resolução: 30m, Período: 1985-2024 (anual), 62 categorias de cobertura, CC BY 4.0",
    "territories_desc": "700+ territórios brasileiros com limites vetoriais e atributos - Projeto Territórios MapBiomas",
    "features_title": "Funcionalidades",
    "tech_title": "Tecnologias",

    # Layer Reference Guide
    "layer_reference": "Guia de Referência de Camadas",
    "indigenous_territories_label": "Territórios Indígenas",
    "selected_territory_label": "Território Selecionado",
    "drawn_polygon_label": "Polígono Desenhado",
    "buffer_zone_label": "Zona de Amortecimento Externa",
    "mapbiomas_legend": "Classes de Cobertura MapBiomas",
    "hansen_legend": "Classes de Cobertura Hansen/GLAD",
    "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
    "aafc_legend": "Inventário Anual de Cultivos AAFC (Canadá)",

    # Polygon analysis
    "polygon_analysis_header": "Análise de Polígono e Estatísticas",
    "draw_polygon_instruction": "Desenhe um polígono no mapa para começar a analisar a cobertura do solo nessa área. Use as ferramentas de desenho no canto superior esquerdo do mapa.",

    # Portal page
    "about_section": "Sobre Yvynation",
    "about_description": "Yvynation é uma plataforma abrangente para monitoramento e análise de terras indígenas. Combina imagens de satélite, ferramentas de análise geoespacial e detecção de mudanças florestais para fornecer insights sobre mudanças no uso da terra e dinâmicas de ecossistemas.",
    
    # Sidebar sections
    "geometry_tools": "Ferramentas de Geometria",
    "geometry_section": "Geometria e Desenho",
    "buffer_controls": "Controles de Buffer",
    "analysis_settings": "Configurações de Análise",
    "territory_selection": "Seleção de Território",
    "comparison_controls": "Controles de Comparação",
    
    # Form inputs
    "enter_distance": "Digite a distância",
    "territory_search": "Pesquisar Território",
    "search_territory": "Pesquise território por nome...",
    "country": "País",
    "territory_type": "Tipo de Território",
    "indigenous_lands_btn": "🪶 Indígenas",
    "conservation_units_btn": "🌿 Conservação",
    
    # Other
    "no_results": "Nenhum resultado encontrado",
    "remove": "Remover",
    "aafc_section_title": "Camadas AAFC (Canadá)",

    # =====================================================================
    # Navbar de análise / conteúdo principal (index.py)
    # =====================================================================
    "nav_hide": "☰ Ocultar",
    "nav_show": "☰ Mostrar",
    # Estrutura da área de trabalho: grupos da barra lateral, alças de
    # arraste, redimensionamento do painel de resultados
    "group_study_area": "Área de estudo",
    "group_analysis": "Análise",
    "group_layers": "Camadas do mapa",
    "group_help": "Ajuda e legenda",
    "sidebar_hide_aria": "Ocultar o painel de controles",
    "sidebar_show_aria": "Mostrar o painel de controles",
    "sidebar_resize_aria": "Redimensionar o painel de controles — arraste ou use as setas; clique duplo para restaurar",
    "sheet_handle_aria": "Redimensionar o painel — arraste, toque ou use as setas",
    "results_resize_label": "Tamanho",
    "results_resize_aria": "Alternar a altura do painel de resultados entre três tamanhos",
    "save_drawing": "Salvar Desenho",
    "geometry_analysis_label": "🔷 Análise de Geometria",
    "territory_analysis_label": "🗺️ Análise de Território",
    "back_to_portal": "← Voltar ao Portal",
    "back_to_batch": "← Voltar ao Lote",
    "clear_btn": "🔄 Limpar",
    "clear_btn_title": "Limpar todos os dados de análise e recomeçar",
    "active_analysis_area": "Área de análise ativa",
    "no_areas_yet": "Nenhuma área ainda — selecione um território ou desenhe uma",
    "run_all_analysis": "▶ Executar todas as análises",
    "bundling": "Empacotando…",
    "download_all": "⬇️ Baixar tudo",
    "results_label": "📊 Resultados",
    "full_results": "⛶ Resultados em tela cheia",
    "exit_full_results": "⛶ Sair da tela cheia",
    "toggle_full_results_title": "Alternar resultados em tela cheia",

    # =====================================================================
    # Página do portal (portal.py)
    # =====================================================================
    "portal_ds_mapbiomas": "MapBiomas: cobertura do solo do Brasil (1985-2024, resolução de 30m)",
    "portal_ds_hansen": "Hansen/GFC: detecção global de mudanças florestais",
    "portal_ds_aafc": "AAFC: classificação agrícola e florestal do Canadá",
    "portal_ds_gee": "Google Earth Engine: análise geoespacial na nuvem",
    "portal_ds_custom": "Geometrias personalizadas: desenhe ou envie suas próprias feições",
    "portal_choose_title": "🚀 Escolha Seu Caminho de Análise",
    "portal_choose_desc": "Selecione o tipo de análise que melhor se adapta ao seu fluxo de trabalho. Ambos os caminhos dão acesso às mesmas ferramentas e conjuntos de dados.",
    "portal_geometry_sub": "Desenhe e analise áreas personalizadas",
    "portal_geometry_i1": "Desenhe polígonos no mapa",
    "portal_geometry_i2": "Envie GeoJSON/Shapefiles/KML",
    "portal_geometry_i3": "Crie zonas de amortecimento (buffer)",
    "portal_geometry_i4": "Analise mudanças de cobertura do solo",
    "portal_geometry_btn": "→ Inicia Geometria",
    "indigenous_analysis_label": "🪶 Análise de Terras Indígenas",
    "portal_indigenous_sub": "Monitore terras indígenas",
    "portal_indigenous_i1": "Selecione entre 650+ terras indígenas",
    "portal_indigenous_i2": "Pesquise por nome",
    "portal_indigenous_i3": "Acompanhe mudanças florestais (1985-2024)",
    "portal_indigenous_i4": "Compare múltiplos anos",
    "portal_indigenous_btn": "→ Inicia Terras Indígenas",
    "conservation_analysis_label": "🌿 Análise de Unidades de Conservação",
    "portal_conservation_sub": "Monitore unidades de conservação",
    "portal_conservation_i1": "Selecione entre 3.200+ unidades de conservação",
    "portal_conservation_i2": "Pesquise por nome",
    "portal_conservation_i3": "Acompanhe mudanças florestais (1985-2024)",
    "portal_conservation_i4": "Compare múltiplos anos",
    "portal_conservation_btn": "→Inicia Un. Conservação",
    "portal_batch_sub": "Processe vários territórios de uma vez",
    "portal_batch_i1": "Selecione qualquer número de territórios",
    "portal_batch_i2": "Execute MapBiomas, Hansen GLAD e GFC",
    "portal_batch_i3": "Território + buffer automaticamente",
    "portal_batch_i4": "Baixe um ZIP com todos os dados",
    "portal_batch_btn": "→ Iniciar Process. em Lote",
    "portal_resources": "📚 Recursos",
    "portal_footer_data": "Dados",
    "portal_footer_contact": "Contato",
    "portal_show": "(mostrar)",
    "portal_hide": "(ocultar)",
    "portal_link_methods": "Métodos e Pesquisa",
    "portal_support": "🎓 Suporte",
    "portal_link_tutorial": "Tutorial e Guia",
    "portal_link_faq": "Perguntas Frequentes",
    "portal_link_contact": "Contato e Feedback",
    "portal_link_team": "Equipe e Colaboradores",
    "portal_link_cite": "Como Citar",

    # =====================================================================
    # Citação e agradecimentos (components/citation.py)
    # =====================================================================
    "citation_title": "Como Citar e Agradecimentos",
    "citation_mission": "A Yvynation disponibiliza dados geoespaciais, gráficos e figuras abertos para apoiar comunidades e gestores de Terras Indígenas e Unidades de Conservação, além de fornecer a pesquisadores e jornalistas informações, figuras e tabelas confiáveis para seus próprios trabalhos.",
    "citation_acknowledgment_title": "Agradecimentos",
    "citation_acknowledgment_text": "O processamento geoespacial desta plataforma roda no Google Earth Engine, no projeto ProtectedLandsYvynation-EE, registrado para uso não comercial em pesquisa. A infraestrutura em nuvem é apoiada por créditos do Google Cloud Research Credits.",
    "citation_ack_people": "Agradecimentos a Jon Corbett (orientador) e à banca de doutorado — Jonathan Cinnamon, Robert Friberg e Tim Paulson — pela orientação sobre o arcabouço; a Pedro de Almeida Salles, que codesenvolveu o corpus da linha do tempo da política florestal brasileira; a Alexander Biondo, Gabriel Silva Santos, Clayton Borges, Bernardo Trovão e Aparicio Biondo pelas ideias, discussões e testes por trás do pipeline e do design do Yvynation; e às equipes do MapBiomas e Hansen/GLAD pelos produtos abertos de cobertura do solo.",
    "citation_ack_compute": "O processamento conta com o apoio do programa Google Cloud Research Credits (projeto Earth Engine ee-leandromet). Discussões com a equipe do Cadastro Ambiental Rural (Ministério da Gestão e da Inovação em Serviços Públicos), com as equipes do Earth Engine e do Google Brasil, com o MapBiomas e o Imazon — sobre a aquisição e a divulgação das imagens SPOT de 2008 usadas na análise de imóveis rurais sob o Código Florestal de 2012 — moldaram este trabalho. O Instituto Nacional da Mata Atlântica (Ministério da Tecnologia e Inovação) e o Serviço Florestal Brasileiro (Ministério da Mudança do Clima e Meio Ambiente) autorizaram a licença sabática para estes estudos de pós-graduação.",
    "citation_ack_funding": "O apoio financeiro vem do Environment and Climate Change Canada (ECCC), por meio do Climate Action and Awareness Fund (CAAF), incluindo uma bolsa de pesquisa na iniciativa UBCO Transportation and Climate Action Research, conduzida pelo UBC Integrated Transportation Research (UiTR) Laboratory no campus Okanagan. O apoio acadêmico, social e intelectual vem do UBCO Interdisciplinary Graduate Studies (IGS) – Sustainability Theme e do Institute for Community Engaged Research (ICER).",
    "citation_ack_summary": "Dados abertos de cobertura do solo do MapBiomas e Hansen/GLAD, processados no Google Earth Engine com Google Cloud Research Credits. Apoio à pesquisa do ECCC/CAAF e da UBC Okanagan — agradecimentos completos em “Como Citar”.",
    "license_summary": "Dados e figuras gerados no Yvynation são de uso público, aberto e gratuito mediante referência.",
    "license_title": "Licença",
    "citation_howto_title": "Sugestão de citação",
    "citation_platform_text": "Biondo, L. M. (2026). Yvynation: plataforma de monitoramento geoespacial de Terras Indígenas e Unidades de Conservação [Software]. Interdisciplinary Graduate Studies – Sustainability Theme (IGS), UBC Okanagan. Dados processados via Google Earth Engine (projeto ProtectedLandsYvynation-EE).",
    "citation_datasets_title": "Cite também as fontes de dados utilizadas:",
    "citation_ds_mapbiomas": "Projeto MapBiomas — Coleção 10 da Série de Mapas de Uso e Cobertura da Terra do Brasil, mapbiomas.org",
    "citation_ds_hansen": "Hansen, M.C. et al. (2013). High-Resolution Global Maps of 21st-Century Forest Cover Change. Science. (Global Forest Change / GLAD, UMD)",
    "citation_ds_aafc": "Agriculture and Agri-Food Canada (AAFC) — Annual Crop Inventory",
    "citation_ds_gee": "Gorelick, N. et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment.",
    "citation_hide": "Ocultar",

    # =====================================================================
    # Página de processamento em lote (batch_processing.py)
    # =====================================================================
    "batch_title": "🔶 Processamento em Lote",
    "batch_nav_subtitle": "Execute a análise completa em vários territórios — baixe um único ZIP",
    "batch_select_territories": "🗺️ Selecionar Territórios",
    "batch_selected_suffix": " selecionado(s)",
    "batch_indigenous_btn": "🪶 Indígenas",
    "batch_conservation_btn": "🌿 Unidades de Conservação",
    "batch_search_placeholder": "🔍 Buscar territórios…",
    "batch_select_all_filtered": "Selecionar todos os filtrados",
    "batch_shown_suffix": " exibido(s)",
    "batch_area_filter_label": "Área:",
    "batch_min_ha_placeholder": "Mín",
    "batch_max_ha_placeholder": "Máx",
    "batch_ha_suffix": "ha",
    "batch_filter_uf_label": "UF (Estado)",
    "batch_filter_fase_label": "Fase",
    "batch_filter_modalidade_label": "Modalidade",
    "batch_filter_categoria_label": "Categoria",
    "batch_filter_esfera_label": "Esfera",
    "batch_filter_grupo_label": "Grupo",
    "batch_clear_filters": "Limpar filtros",
    "batch_sort_label": "Ordenar",
    "batch_sort_name_asc": "Nome A–Z",
    "batch_sort_name_desc": "Nome Z–A",
    "batch_sort_area_asc": "Área: menor primeiro",
    "batch_sort_area_desc": "Área: maior primeiro",
    "batch_review_btn": "Revisar",
    "batch_review_title": "Territórios Selecionados",
    "batch_review_empty": "Nenhum território selecionado ainda.",
    "batch_review_close": "Fechar",
    "batch_paste_instruction": "📋 Cole uma lista de nomes (um por linha) ou envie um .txt/.csv para selecioná-los automaticamente:",
    "batch_select_from_list": "✓ Selecionar da lista",
    "batch_upload_list": "📁 Enviar lista",
    "batch_clear": "Limpar",
    "batch_not_found_prefix": "⚠ Não encontrados: ",
    "batch_configuration": "⚙️ Configuração",
    "batch_year1_label": "Ano único (inicial)",
    "batch_year2_label": "Ano final da comparação",
    "batch_hansen_year_label": "Ano Hansen GLAD",
    "batch_analysis_types": "Tipos de análise",
    "batch_chk_mapbiomas": "🌿 MapBiomas ano único",
    "batch_chk_comparison": "📊 Comparação entre anos",
    "batch_chk_treemap": "🟦 Treemaps de transição de classes (por classe + Outras)",
    "batch_treemap_hint": "Adiciona um treemap facetado (um por classe, classes menores agrupadas em “Outras”) onde transições forem produzidas — na comparação de anos e em cada etapa multi-janela.",
    "batch_chk_glad": "🌲 Cobertura florestal Hansen GLAD",
    "batch_chk_gfc": "🪓 Hansen GFC (perda / ganho)",
    "batch_figs_label": "EXPORTAÇÃO DE FIGURAS",
    "batch_chk_export_png": "🖼 Exportar figuras também em PNG",
    "batch_png_hint": "O HTML é sempre gerado. Os PNGs representam ~90% do tamanho do arquivo, mas apenas alguns por cento do tempo de execução — desligá-los economiza espaço, não tempo.",
    "batch_chk_png_high_res": "Resolução completa (arquivos maiores)",
    "batch_timeline_bands_label": "FAIXAS DE CONTEXTO DA LINHA DO TEMPO",
    "batch_chk_timeline_political": "Faixa de presidentes / governadores",
    "batch_chk_timeline_policy": "Linhas de políticas + marcos",
    "batch_chk_timeline_enso": "Faixa El Niño / La Niña (ENSO)",
    "batch_timeline_bands_hint": "Cada faixa removida também libera o espaço reservado, deixando o gráfico mais curto.",
    "batch_chk_pdf_maps": "🗺️ Mapas PNG e Gráficos (satélite + MapBiomas ano1/ano2)",
    "batch_aux_rasters_label": "Rasters MapBiomas extras (ano 2)",
    "batch_aux_deforestation": "🌳 Desmatamento e vegetação secundária",
    "batch_aux_fire_scar": "🔥 Área queimada anual (tamanho da cicatriz)",
    "batch_aux_fire_frequency": "📊 Frequência de fogo (período completo 1985–2024)",
    "batch_aux_fire_year_last": "📅 Ano do último fogo",
    "batch_aux_mining": "⛏️ Substâncias de mineração",
    "batch_aux_agriculture": "🌾 Agricultura — número de ciclos",
    "batch_chk_multi_window": "🌀 MapBiomas em múltiplas janelas de tempo (Sankey + Sunburst + Treemaps)",
    "batch_mw_mode": "Modo:",
    "batch_mw_step": "Passo (anos):",
    "batch_mw_forced_note": "1985 → 2024 forçado como último ano",
    "batch_mw_custom_label": "Anos personalizados (3 a 10, separados por vírgula, 1985–2024)",
    "batch_mw_active_years": "Anos ativos: ",
    "batch_chk_timeline": "📈 Linha do tempo de desmatamento (Hansen + MapBiomas + Fogo) com contexto político",
    "batch_buffer_zone": "Zona de amortecimento",
    "batch_include_buffer": "Incluir análise de buffer",
    "batch_km_ring": "km de anel externo",
    "batch_progress": "📊 Progresso",
    "batch_territory_label": "Território:",
    "batch_step_label": "Etapa:",
    # Fluxo de etapas, filtros recolhíveis e grupos de configuração
    "batch_stage_select": "Selecionar",
    "batch_stage_configure": "Configurar",
    "batch_stage_run": "Executar",
    "batch_filters_toggle": "Filtros e listas",
    "batch_list_capped": "Mostrando os primeiros {shown} de {total} — busque ou filtre para alcançar o restante. \u201cSelecionar todos filtrados\u201d ainda usa os {total}.",
    "batch_group_years": "Anos",
    "batch_group_analyses": "Análises",
    "batch_group_figures": "Figuras e imagens",
    "batch_group_multiwindow": "Multi-janela",
    "batch_group_timeline": "Linha do tempo",
    "batch_group_buffer": "Zona de amortecimento",
    "batch_in_flight_label": "Em curso:",
    "batch_done_label": "Concluído:",
    "batch_complete_label": "— concluído —",
    "batch_errors_suffix": " erro(s))",
    "batch_processing_log": "Registro de processamento",
    "batch_about_title": "📖 Sobre o Processamento em Lote",
    "batch_about_text": "Execute o pipeline completo de análise do Yvynation (cobertura do solo MapBiomas, mudança entre anos, cobertura florestal Hansen GLAD e perda/ganho Hansen GFC) em vários territórios de uma só vez, sem supervisão. Suporta territórios indígenas da FUNAI (657) e unidades de conservação do CNUC (3.247). Cada território — e seu buffer externo opcional — é processado via Google Earth Engine e empacotado em um único arquivo ZIP contendo tabelas CSV, matrizes de transição e figuras (HTML + PNG) por território.",
    "batch_time_note": "Espere de 2 a 10 minutos por território, dependendo das análises habilitadas. A aba pode ficar aberta em segundo plano.",
    "batch_howto": "Como usar",
    "batch_howto_1_title": "Selecione os territórios",
    "batch_howto_1_body": "Escolha o tipo de fonte (Indígenas ou Unidades de Conservação), use a busca para filtrar e marque os territórios que deseja incluir. 'Selecionar todos os filtrados' adiciona todas as correspondências da busca atual; 'Limpar tudo' recomeça. Trocar o tipo limpa a seleção atual.",
    "batch_howto_2_title": "Escolha os anos MapBiomas",
    "batch_howto_2_body": "Defina o ano inicial (retrato único) e o ano final (para a comparação entre anos). Intervalo: 1985–2024.",
    "batch_howto_3_title": "Escolha o ano Hansen GLAD",
    "batch_howto_3_body": "Ano de referência (2000/2005/2010/2015/2020) usado para o retrato de cobertura florestal Hansen GLAD.",
    "batch_howto_4_title": "Escolha os tipos de análise",
    "batch_howto_4_body": "Habilite qualquer combinação de MapBiomas ano único, comparação entre anos, Hansen GLAD e perda/ganho Hansen GFC.",
    "batch_howto_5_title": "Zona de amortecimento opcional",
    "batch_howto_5_body": "Ative para analisar também um anel externo (padrão 10 km) ao redor de cada território. As saídas do buffer são gravadas em buffer/{territory}_Buffer_{km}km/ dentro do ZIP.",
    "batch_howto_6_title": "Inicie o lote",
    "batch_howto_6_body": "Clique em 'Iniciar Processamento em Lote'. O painel de configuração é substituído pela visão de progresso ao vivo; você pode parar após o território atual a qualquer momento.",
    "batch_howto_7_title": "Baixe o ZIP",
    "batch_howto_7_body": "Quando a execução terminar, clique em 'Baixar ZIP' para obter todas as tabelas, transições e figuras de todos os territórios em um único arquivo.",
    "batch_start_btn": "🚀 Iniciar Processamento em Lote",
    "territories_word": "territórios",
    "batch_confirm_prefix": "Isso vai executar a análise do Earth Engine para",
    "batch_confirm_suffix": ". Continuar?",
    "batch_large_run_warning": "Seleção grande — considere dividir em algumas execuções menores (ex.: 20-25 territórios cada) para manter a execução confiável. Se for interrompida, os resultados parciais continuam disponíveis na página Execuções Anteriores.",
    "batch_processing_ellipsis": "Processando…",
    "batch_stop_btn": "⏹ Parar após o atual",
    "batch_download_zip": "⬇️ Baixar ZIP",
    "batch_new_batch": "🔄 Novo Lote",
    "batch_territories_selected_suffix": " territórios selecionados",
    "batch_no_territories": "Nenhum território selecionado",

    # =====================================================================
    # Página Execuções Anteriores (previous_runs.py)
    # =====================================================================
    "previous_runs_title": "Execuções Anteriores",
    "previous_runs_subtitle": "Recupere exportações em lote finalizadas ou interrompidas",
    "previous_runs_intro": "Toda execução em lote/exportação aparece aqui, incluindo as interrompidas por uma queda ou processo parado — nada é apagado até você baixar ou remover manualmente.",
    "previous_runs_refresh": "Atualizar",
    "previous_runs_status_zip": "✅ Concluída",
    "previous_runs_status_partial": "⚠ Parcial — recuperável",
    "previous_runs_download": "Baixar",
    "previous_runs_zip_download": "Compactar e Baixar",
    "previous_runs_zipping": "Compactando…",
    "previous_runs_delete": "Excluir",
    "previous_runs_copy": "Copiar",
    "previous_runs_bucket_section": "Link direto do bucket",
    "previous_runs_bucket_hint": "Para copiar no gcloud/gsutil ou no console do Cloud. O botão Baixar acima não usa estes links.",
    "previous_runs_detail_config": "Configuração da execução",
    "previous_runs_detail_territories": "Territórios",
    "previous_runs_detail_performance": "Desempenho",
    "previous_runs_detail_loading": "Lendo detalhes da execução…",
    "previous_runs_files_suffix": "arquivos",
    "previous_runs_empty": "Ainda não há execuções anteriores — downloads de lote/exportação aparecerão aqui.",
}
