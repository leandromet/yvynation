"""
Translation and internationalization support for Reflex app.
Provides dictionary-based translations with a reactive computed var pattern.
"""

from typing import Dict, Optional, Any


# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Page
        "page_title": "Yvynation - Indigenous Land Monitoring",
        "main_page_title": "Yvynation - Indigenous Land Monitoring Platform",
        "app_title": "Yvynation",
        "app_subtitle": "Indigenous Land Monitoring Platform",
        "app_description": "Global Forest Monitoring Platform",
        "author": "Leandro M. Biondo - PhD Candidate - IGS/UBCO",

        # Navigation
        "map_tab": "Map",
        "analysis_tab": "Analysis",
        "tutorial_tab": "Tutorial",
        "about_tab": "About",

        # Sidebar
        "sidebar_title": "Layers & Controls",
        "controls_badge": "Controls",
        "mapbiomas_label": "MapBiomas",
        "mapbiomas_section_title": "MapBiomas Layers",
        "mapbiomas_select_year": "Select MapBiomas Year",
        "mapbiomas_years": "MapBiomas Years",
        "mapbiomas_layers_label": "MapBiomas Layers",
        "mapbiomas_layers_hint": "Number of active MapBiomas layers",
        "no_mapbiomas_selected": "No MapBiomas years selected",
        "no_mapbiomas_added": "Add MapBiomas layers in sidebar",
        "add_to_map": "Add to map",
        "clear_all": "Clear all",

        "hansen_label": "Hansen GFC",
        "hansen_section_title": "Hansen GFC",
        "hansen_select_year": "Select Hansen Year",
        "hansen_years": "Hansen Years",
        "hansen_layers_label": "Hansen Layers",
        "hansen_layers_hint": "Number of active Hansen layers",
        "hansen_gfc_label": "Global Forest Change (GFC)",
        "hansen_gfc_layers_label": "GFC Layers",
        "no_hansen_selected": "No Hansen years selected",
        "no_hansen_added": "Add Hansen layers in sidebar",
        "no_hansen_gfc_added": "No GFC layers enabled",
        "data_layers": "Data layers",
        "year_layers": "Year layers",
        "tree_cover_btn": "Tree Cover",
        "loss_btn": "Loss",
        "gain_btn": "Gain",
        "add_btn": "Add",

        "tree_cover_2000": "Tree Cover 2000",
        "tree_loss_period": "Tree Loss (2000-2023)",
        "tree_gain_period": "Tree Gain (2000-2012)",

        # Base layer
        "base_layer": "Base Layer",
        "base_layer_hint": "Current base map",

        # Active layers
        "active_layers": "Active Layers",
        "analysis_active_badge": "Analysis Active",

        # Territory section
        "territory_section_title": "Territory Analysis",
        "select_territory": "Select Territory",
        "territory_by_country": "Filter by Country",
        "territory_by_state": "Filter by State",
        "selected_territory": "Selected Territory",
        "no_territory_selected": "No territory selected",
        "search_territories": "Search territories...",
        "select_territory_placeholder": "Select territory",
        "click_map_to_select": "Click map markers to select",
        "show_all_lands": "Show All Lands",
        "hide_all_lands": "Hide All Lands",
        "select_territory_above": "Select a territory above",
        "compare_years": "Compare years",
        "compare_mapbiomas_years": "Compare MapBiomas Years",

        # Geometry section
        "geometry_section_title": "Geometry & Drawing",
        "upload_geometry_file": "Upload geometry file",
        "analyze_selected_geometry": "Analyze selected geometry",
        "map_overlays": "Map overlays",
        "show_geometries": "Show Geometries",
        "hide_geometries": "Hide Geometries",
        "show_change": "Show Change",
        "hide_change": "Hide Change",

        # Map controls
        "draw_polygon": "Draw Polygon",
        "clear_drawings": "Clear All",
        "upload_geojson": "Upload GeoJSON",

        # Analysis
        "run_analysis": "Run Analysis",
        "analysis_results": "Analysis Results",
        "mapbiomas_analysis": "MapBiomas Analysis",
        "hansen_analysis": "Hansen Analysis",
        "export_results": "Export Results",
        "comparing_label": "Comparing...",

        # Comparison
        "compare_label": "Compare:",
        "vs_label": "vs",
        "compare_btn": "Compare",
        "year_comparison_results": "Year Comparison Results",
        "download_comparison_csv": "Download Comparison CSV",
        "total_gains": "Total Gains",
        "total_losses": "Total Losses",
        "net_change": "Net Change",
        "comparison_available": "Comparison Available",

        # Buttons
        "confirm": "Confirm",
        "cancel": "Cancel",
        "close": "Close",
        "select": "Select",
        "dismiss": "Dismiss",

        # Messages
        "loading": "Loading...",
        "analyzing": "Analyzing...",
        "initializing": "Initializing Yvynation Platform...",
        "ee_init_error": "Failed to initialize Earth Engine: {error}",
        "error": "Error",
        "success": "Success",

        # Analysis results
        "class": "Class",
        "area_hectares": "Area (ha)",
        "area_km2": "Area (km2)",
        "percentage": "Percentage (%)",
        "year": "Year",
        "change": "Change",
        "from_class": "From Class",
        "to_class": "To Class",
        "area_changed": "Area Changed",

        # File upload
        "upload_file": "Upload File",
        "file_uploaded": "File uploaded successfully",
        "file_upload_error": "Error uploading file",
        "select_file": "Select file (GeoJSON, KML, Shapefile)",

        # Buffer operations
        "buffer_distance": "Buffer Distance (meters)",
        "create_buffer": "Create Buffer",
        "buffer_created": "Buffer created successfully",

        # Geometry
        "draw_area": "Draw Area of Interest",
        "upload_geometry": "Upload Geometry",
        "geometry_loaded": "Geometry loaded",

        # Export
        "export_as_csv": "Export as CSV",
        "export_as_pdf": "Export as PDF",
        "export_as_zip": "Export as ZIP",
        "exporting": "Exporting...",
        "export_complete": "Export complete",
        "export_analysis": "Export Analysis",

        # MapBiomas specific
        "mapbiomas_no_data": "No data available for selected area",
        "mapbiomas_process_error": "Error processing class {class_id}: {error}",
        "mapbiomas_analysis_title": "MapBiomas Land Cover Analysis",
        "mapbiomas_year_range": "Year range: {start} - {end}",

        # Hansen specific
        "hansen_tree_cover": "Tree Cover",
        "hansen_tree_loss": "Tree Loss",
        "hansen_tree_gain": "Tree Gain",
        "hansen_no_data": "No Hansen data for selected area",

        # Settings / Quick settings
        "language": "Language",
        "theme": "Theme",
        "dark_mode": "Dark Mode",
        "light_mode": "Light Mode",

        # Help & Info
        "help": "Help",
        "documentation": "Documentation",
        "about": "About Yvynation",
        "version": "Version",
        "powered_by": "Powered by",

        # =====================================================================
        # Tutorial / Getting Started
        # =====================================================================
        "getting_started_header": "How to Use This Platform",
        "getting_started_title": "Getting Started",
        "getting_started_intro": "This platform enables comprehensive land cover analysis for Brazil and global forest monitoring. You can analyze custom areas, indigenous territories, and external buffer zones.",

        "step_language_region": "Step 0: Language & Region Selection",
        "step0_language_region_intro": "Configure your language and select your region of interest:",
        "step0_content": """**Auto-Detection on First Visit**

On your first visit, the app can detect your location to set the right region:
- **North America** (latitude > 10N) -> Sets Canada
- **South America** -> Uses browser language or Portuguese (PT)
- You can review or change the setting at any time

**Manual Language Selection**

Use the language buttons (EN / PT / ES) in the sidebar to switch languages. Your choice is saved for your session.

**Manual Region Selection**

Use the region buttons (Brazil / Canada) in the sidebar to choose between:
- **Brazil**: Full MapBiomas coverage (1985-2023) + Hansen/GLAD global data
- **Canada**: AAFC crop inventory + Hansen/GLAD global data

The map will center on your selected region.""",

        "step_custom_polygon": "Step 1: Analyze a Custom Polygon",
        "step1_draw_intro": "Draw and analyze any area on the map:",
        "step1_content": """1. **Drawing Tools** (top-left corner of map):
   - Click the **Rectangle** tool for quick rectangular selections
   - Click the **Polygon** tool for custom shapes with multiple points
   - Double-click or click the first point again to complete a polygon

2. **Select Data Layers** (left sidebar):
   - **MapBiomas**: Brazilian land cover (1985-2023, 62 classes, 30m resolution)
   - **Hansen/GLAD**: Global forest change (2000-2020, 256 classes, 30m resolution)
   - **Hansen GFC**: Global Forest Change (2000-2024, 30m resolution)
   - Toggle multiple years to enable comparisons

3. **Analysis Results**:
   - Land cover distribution by class
   - Area statistics (hectares and percentages)
   - Visual charts and data tables
   - Downloadable CSV files

4. **Buffer Zone Analysis**:
   - After drawing, click "Create Buffer"
   - Choose buffer distance: 2km, 5km, or 10km
   - Creates a ring-shaped zone around your polygon
   - Analyze both areas side-by-side

**Tips**: Delete unwanted polygons with the trash icon. Use buffer zones to understand edge effects and surrounding land use.""",

        "step_territory": "Step 2: Analyze an Indigenous Territory",
        "step2_territory_intro": "Pre-defined indigenous territory boundaries with historical analysis:",
        "step2_content": """1. **Select Territory** (Territory Analysis section in sidebar):
   - Search or browse all territories
   - Choose from 400+ officially recognized indigenous lands
   - View territory metadata: area, location, recognition status

2. **Territory Analysis Features**:
   - Historical land cover changes (1985-2023)
   - Area changes by land cover class
   - Deforestation and regeneration trends
   - Transition diagrams (Sankey charts) showing conversions between classes
   - Export all data and visualizations

3. **Buffer Zone Analysis for Territories**:
   - Create external buffer zones (2km/5km/10km) around the entire territory
   - Compare land use inside vs outside the protected boundary
   - Identify pressure zones and encroachment patterns
   - Results appear in separate tabs

**Tips**: Compare multiple territories in the same state. Long-term comparisons (1985 vs 2023) reveal protection effectiveness.""",

        "step_comparison": "Step 3: Multi-Year Comparison",
        "step3_comparison_intro": "Compare land cover changes between any two years:",
        "step3_content": """1. **Setup Comparison** (Comparison tab):
   - Select 2+ years in the layer controls (sidebar)
   - Draw a polygon or select a territory
   - Choose Year 1 (baseline) and Year 2 (comparison)

2. **Click Comparison Buttons**:
   - **Compare MapBiomas Years**: Brazilian land cover changes
   - **Compare Hansen Years**: Global forest changes

3. **View Results**:
   - **Data Table**: Side-by-side area values with change calculations
   - **Side-by-side Charts**: Visual distribution for each year
   - **Gains & Losses**: Horizontal bar chart showing increases/decreases
   - **Sankey Diagram**: Flow chart showing land cover transitions
   - **Summary Metrics**: Total change, loss, and gain values

**Tips**: Compare 1985 vs 2023 for 38 years of change. Use 5-year intervals to identify major deforestation events.""",

        "step_export": "Step 4: Export and Download Results",
        "step4_export_intro": "Save your analysis results for reports and further analysis:",
        "step4_content": """- **CSV Downloads**: Click "Download CSV" buttons in each analysis tab
  - Individual year data with area statistics
  - Comparison tables with change calculations

- **PNG Exports**: High-resolution images from Earth Engine
  - Export analysis regions as georeferenced images
  - Suitable for GIS software and publications

- **PDF Reports** (future): Comprehensive analysis summaries

**Tip**: All downloads use consistent naming conventions for easy organization.""",

        "step_map_controls": "Step 5: Map Controls & Navigation",
        "step5_map_controls_intro": "Navigate and interact with the map:",
        "step5_content": """**Basic Navigation:**
- **Zoom In/Out**: Mouse scroll wheel, +/- buttons, or double-click
- **Pan**: Click and drag anywhere on the map
- **Fullscreen**: Click fullscreen button for larger view

**Drawing Tools** (top-left corner):
- Edit Layers: Modify existing polygons
- Delete Layers: Remove unwanted polygons
- Draw Rectangle: Quick rectangular areas
- Draw Polygon: Custom multi-point shapes
- Finish Drawing: Double-click or click first point to complete

**Layer Controls** (top-right corner):
- Base Layers: Switch between OpenStreetMap, Satellite, Terrain views
- Overlays: Toggle MapBiomas and Hansen layers on/off
- Territory Boundaries: Show/hide indigenous territory outlines

**Map Features:**
- Blue rings: External buffer zones (when created)
- Colored polygons: Your drawn analysis areas
- Territory boundaries: Pre-loaded indigenous land boundaries""",

        "step_data_understanding": "Step 6: Understanding Data & Results",
        "step6_data_understanding_intro": "Learn about data sources and how to interpret results:",
        "step6_content": """**Data Sources:**

**MapBiomas Collection 9** (Brazil):
- Coverage: All of Brazil, 1985-2023
- Resolution: 30 meters (Landsat-based)
- Classes: 62 land cover types (forest, savanna, agriculture, urban, etc.)
- Accuracy: ~90% overall (varies by class and region)

**Hansen/GLAD Global Forest Change**:
- Coverage: Global (all continents)
- Resolution: 30 meters (Landsat-based)
- Classes: 256 land use classes combining forest cover, loss year (2000-2020), gain (2000-2012)
- Best for: Forest change detection and monitoring

**Result Interpretation:**
- **Area (ha)**: Hectares = 10,000 m2 (about 2.5 acres)
- **Pixels**: Each pixel = 900 m2 (30m x 30m)
- **Percentages**: Calculated from total analyzed area
- **Change values**: Positive = increase, Negative = decrease

**Charts**: Bar charts show top 15 classes. Sankey diagrams show land cover transitions. Gains & Losses bars show increases (right) and decreases (left).""",

        # About section
        "about_title": "About",
        "about_overview": "Project Overview",
        "about_desc": "This land use and land cover analysis tool is part of a research project studying environmental changes in Brazilian Indigenous Territories using Google Earth Engine and MapBiomas data. This data is compared with policy changes and deforestation trends to understand the impacts on these critical lands.",
        "about_author": "Leandro Meneguelli Biondo",
        "about_role": "PhD Candidate in Sustainability",
        "about_university": "IGS/UBCO",
        "about_supervisor": "Supervisor: Dr. Jon Corbett",
        "about_app_name": "Yvynation",
        "about_app_note": "is a name for this app, as it is not the full project content.",
        "yvynation_meaning": '"Yvy" (Tupi-Guarani) means land, earth, or territory - emphasizing the ground we walk on and our sacred connection to nature. It often relates to the concept of "Yvy marae\'y" (Land without evil).',
        "nation_meaning": '"Nation" refers to a self-governing community or people with shared culture, history, language, and land. It signifies self-determination and governance.',
        "data_sources_title": "Data Sources",
        "mapbiomas_desc": "MapBiomas Collection 9 - Resolution: 30m, Period: 1985-2023 (annual), 62 land cover categories, CC BY 4.0",
        "territories_desc": "700+ Brazilian territories with vector boundaries and attributes - MapBiomas Territories Project",
        "features_title": "Features",
        "tech_title": "Technologies",

        # Layer Reference Guide
        "layer_reference": "Layer Reference Guide",
        "indigenous_territories_label": "Indigenous Territories",
        "selected_territory_label": "Selected Territory",
        "drawn_polygon_label": "Drawn Polygon",
        "buffer_zone_label": "External Buffer Zone",
        "mapbiomas_legend": "MapBiomas Land Cover Classes",
        "hansen_legend": "Hansen/GLAD Global Land Cover Classes",
        "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
        "aafc_legend": "AAFC Annual Crop Inventory (Canada)",

        # Polygon analysis
        "polygon_analysis_header": "Polygon Analysis & Statistics",
        "draw_polygon_instruction": "Draw a polygon on the map to start analyzing land cover in that area. Use the drawing tools in the top-left of the map.",
    },
    "pt": {
        # Page
        "page_title": "Yvynation - Monitoramento Territorial Indigena",
        "main_page_title": "Yvynation - Plataforma de Monitoramento Territorial Indigena",
        "app_title": "Yvynation",
        "app_subtitle": "Plataforma de Monitoramento Territorial Indigena",
        "app_description": "Plataforma Global de Monitoramento Florestal",
        "author": "Leandro M. Biondo - Candidato de PhD - IGS/UBCO",

        # Navigation
        "map_tab": "Mapa",
        "analysis_tab": "Analise",
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
        "mapbiomas_layers_hint": "Numero de camadas MapBiomas ativas",
        "no_mapbiomas_selected": "Nenhum ano MapBiomas selecionado",
        "no_mapbiomas_added": "Adicione camadas MapBiomas na barra lateral",
        "add_to_map": "Adicionar ao mapa",
        "clear_all": "Limpar tudo",

        "hansen_label": "Hansen GFC",
        "hansen_section_title": "Hansen GFC",
        "hansen_select_year": "Selecionar Ano Hansen",
        "hansen_years": "Anos Hansen",
        "hansen_layers_label": "Camadas Hansen",
        "hansen_layers_hint": "Numero de camadas Hansen ativas",
        "hansen_gfc_label": "Mudanca Florestal Global (GFC)",
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

        "tree_cover_2000": "Cobertura Arborea 2000",
        "tree_loss_period": "Perda Florestal (2000-2023)",
        "tree_gain_period": "Ganho Florestal (2000-2012)",

        # Base layer
        "base_layer": "Camada Base",
        "base_layer_hint": "Mapa base atual",

        # Active layers
        "active_layers": "Camadas Ativas",
        "analysis_active_badge": "Analise Ativa",

        # Territory section
        "territory_section_title": "Analise de Territorio",
        "select_territory": "Selecionar Territorio",
        "territory_by_country": "Filtrar por Pais",
        "territory_by_state": "Filtrar por Estado",
        "selected_territory": "Territorio Selecionado",
        "no_territory_selected": "Nenhum territorio selecionado",
        "search_territories": "Buscar territorios...",
        "select_territory_placeholder": "Selecionar territorio",
        "click_map_to_select": "Clique nos marcadores do mapa",
        "show_all_lands": "Mostrar Todas as Terras",
        "hide_all_lands": "Ocultar Todas as Terras",
        "select_territory_above": "Selecione um territorio acima",
        "compare_years": "Comparar anos",
        "compare_mapbiomas_years": "Comparar Anos MapBiomas",

        # Geometry section
        "geometry_section_title": "Geometria e Desenho",
        "upload_geometry_file": "Enviar arquivo de geometria",
        "analyze_selected_geometry": "Analisar geometria selecionada",
        "map_overlays": "Sobreposicoes do mapa",
        "show_geometries": "Mostrar Geometrias",
        "hide_geometries": "Ocultar Geometrias",
        "show_change": "Mostrar Mudanca",
        "hide_change": "Ocultar Mudanca",

        # Map controls
        "draw_polygon": "Desenhar Poligono",
        "clear_drawings": "Limpar Tudo",
        "upload_geojson": "Upload GeoJSON",

        # Analysis
        "run_analysis": "Executar Analise",
        "analysis_results": "Resultados da Analise",
        "mapbiomas_analysis": "Analise MapBiomas",
        "hansen_analysis": "Analise Hansen",
        "export_results": "Exportar Resultados",
        "comparing_label": "Comparando...",

        # Comparison
        "compare_label": "Comparar:",
        "vs_label": "vs",
        "compare_btn": "Comparar",
        "year_comparison_results": "Resultados da Comparacao de Anos",
        "download_comparison_csv": "Baixar CSV da Comparacao",
        "total_gains": "Ganhos Totais",
        "total_losses": "Perdas Totais",
        "net_change": "Mudanca Liquida",
        "comparison_available": "Comparacao Disponivel",

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
        "area_hectares": "Area (ha)",
        "area_km2": "Area (km2)",
        "percentage": "Percentual (%)",
        "year": "Ano",
        "change": "Mudanca",
        "from_class": "De Classe",
        "to_class": "Para Classe",
        "area_changed": "Area Mudada",

        # File upload
        "upload_file": "Enviar Arquivo",
        "file_uploaded": "Arquivo enviado com sucesso",
        "file_upload_error": "Erro ao enviar arquivo",
        "select_file": "Selecione arquivo (GeoJSON, KML, Shapefile)",

        # Buffer operations
        "buffer_distance": "Distancia do Buffer (metros)",
        "create_buffer": "Criar Buffer",
        "buffer_created": "Buffer criado com sucesso",

        # Geometry
        "draw_area": "Desenhar Area de Interesse",
        "upload_geometry": "Enviar Geometria",
        "geometry_loaded": "Geometria carregada",

        # Export
        "export_as_csv": "Exportar como CSV",
        "export_as_pdf": "Exportar como PDF",
        "export_as_zip": "Exportar como ZIP",
        "exporting": "Exportando...",
        "export_complete": "Exportacao concluida",
        "export_analysis": "Exportar Analise",

        # MapBiomas specific
        "mapbiomas_no_data": "Nenhum dado disponivel para a area selecionada",
        "mapbiomas_process_error": "Erro ao processar classe {class_id}: {error}",
        "mapbiomas_analysis_title": "Analise de Cobertura Terrestre MapBiomas",
        "mapbiomas_year_range": "Intervalo de anos: {start} - {end}",

        # Hansen specific
        "hansen_tree_cover": "Cobertura Arborea",
        "hansen_tree_loss": "Perda Florestal",
        "hansen_tree_gain": "Ganho Florestal",
        "hansen_no_data": "Nenhum dado Hansen para a area selecionada",

        # Settings / Quick settings
        "language": "Idioma",
        "theme": "Tema",
        "dark_mode": "Modo Escuro",
        "light_mode": "Modo Claro",

        # Help & Info
        "help": "Ajuda",
        "documentation": "Documentacao",
        "about": "Sobre Yvynation",
        "version": "Versao",
        "powered_by": "Desenvolvido por",

        # =====================================================================
        # Tutorial / Getting Started
        # =====================================================================
        "getting_started_header": "Como Usar Esta Plataforma",
        "getting_started_title": "Primeiros Passos",
        "getting_started_intro": "Esta plataforma permite analise abrangente de cobertura do solo para o Brasil e monitoramento florestal global. Voce pode analisar areas personalizadas, territorios indigenas e zonas de amortecimento externas.",

        "step_language_region": "Passo 0: Selecao de Idioma e Regiao",
        "step0_language_region_intro": "Configure seu idioma e selecione sua regiao de interesse:",
        "step0_content": """**Auto-Deteccao na Primeira Visita**

Na sua primeira visita, o aplicativo pode detectar sua localizacao para definir a regiao correta:
- **America do Norte** (latitude > 10N) -> Define Canada
- **America do Sul** -> Usa o idioma do navegador ou Portugues (PT)
- Voce pode revisar ou alterar a configuracao a qualquer momento

**Selecao Manual de Idioma**

Use os botoes de idioma (EN / PT / ES) na barra lateral para trocar o idioma. Sua escolha e salva para sua sessao.

**Selecao Manual de Regiao**

Use os botoes de regiao (Brasil / Canada) na barra lateral para escolher entre:
- **Brasil**: Cobertura completa MapBiomas (1985-2023) + dados globais Hansen/GLAD
- **Canada**: Inventario de cultivos AAFC + dados globais Hansen/GLAD

O mapa sera centralizado na regiao selecionada.""",

        "step_custom_polygon": "Passo 1: Analisar um Poligono Personalizado",
        "step1_draw_intro": "Desenhe e analise qualquer area no mapa:",
        "step1_content": """1. **Ferramentas de Desenho** (canto superior esquerdo do mapa):
   - Clique na ferramenta **Retangulo** para selecoes retangulares rapidas
   - Clique na ferramenta **Poligono** para formas personalizadas
   - Clique duplo ou clique no primeiro ponto novamente para completar

2. **Selecione Camadas de Dados** (barra lateral esquerda):
   - **MapBiomas**: Cobertura do solo brasileira (1985-2023, 62 classes, 30m)
   - **Hansen/GLAD**: Mudancas florestais globais (2000-2020, 256 classes, 30m)
   - **Hansen GFC**: Mudancas Florestais Globais (2000-2024, 30m)
   - Alterne varios anos para habilitar comparacoes

3. **Resultados da Analise**:
   - Distribuicao de cobertura do solo por classe
   - Estatisticas de area (hectares e percentuais)
   - Graficos visuais e tabelas de dados
   - Arquivos CSV para download

4. **Analise de Zona de Buffer**:
   - Apos desenhar, clique em "Criar Buffer"
   - Escolha a distancia: 2km, 5km ou 10km
   - Cria uma zona em forma de anel ao redor do poligono
   - Analise ambas as areas lado a lado

**Dicas**: Exclua poligonos indesejados com o icone de lixeira. Use zonas de buffer para entender efeitos de borda.""",

        "step_territory": "Passo 2: Analisar um Territorio Indigena",
        "step2_territory_intro": "Limites de territorios indigenas pre-definidos com analise historica:",
        "step2_content": """1. **Selecionar Territorio** (secao Analise de Territorio na barra lateral):
   - Pesquise ou navegue por todos os territorios
   - Escolha entre 400+ terras indigenas reconhecidas
   - Veja metadados do territorio: area, localizacao, status

2. **Recursos de Analise de Territorio**:
   - Mudancas historicas de cobertura do solo (1985-2023)
   - Mudancas de area por classe de cobertura
   - Tendencias de desmatamento e regeneracao
   - Diagramas de transicao (Sankey) mostrando conversoes entre classes
   - Exportar todos os dados e visualizacoes

3. **Analise de Zona de Amortecimento**:
   - Crie zonas externas (2km/5km/10km) ao redor do territorio
   - Compare uso do solo dentro vs fora da fronteira protegida
   - Identifique zonas de pressao e padroes de invasao
   - Resultados aparecem em abas separadas

**Dicas**: Compare multiplos territorios. Comparacoes de longo prazo (1985 vs 2023) revelam efetividade da protecao.""",

        "step_comparison": "Passo 3: Comparacao Multi-Anual",
        "step3_comparison_intro": "Compare mudancas de cobertura do solo entre quaisquer dois anos:",
        "step3_content": """1. **Configurar Comparacao** (aba Comparacao):
   - Selecione 2+ anos nos controles de camada (barra lateral)
   - Desenhe um poligono ou selecione um territorio
   - Escolha Ano 1 (linha de base) e Ano 2 (comparacao)

2. **Clique nos Botoes de Comparacao**:
   - **Comparar Anos MapBiomas**: Mudancas de cobertura do solo
   - **Comparar Anos Hansen**: Mudancas de floresta global

3. **Ver Resultados**:
   - **Tabela de Dados**: Valores de area lado a lado com calculos de mudanca
   - **Graficos lado a lado**: Distribuicao visual para cada ano
   - **Ganhos e Perdas**: Grafico de barras horizontal
   - **Diagrama Sankey**: Fluxo de transicoes de cobertura
   - **Metricas de Resumo**: Valores totais de mudanca, perda e ganho

**Dicas**: Compare 1985 vs 2023 para 38 anos de mudanca. Use intervalos de 5 anos para identificar grandes eventos.""",

        "step_export": "Passo 4: Exportar e Baixar Resultados",
        "step4_export_intro": "Salve seus resultados para relatorios e analise adicional:",
        "step4_content": """- **Downloads CSV**: Clique nos botoes "Baixar CSV" em cada aba de analise
  - Dados de ano individual com estatisticas de area
  - Tabelas de comparacao com calculos de mudanca

- **Exportacoes PNG**: Imagens de alta resolucao do Earth Engine
  - Exporte regioes de analise como imagens georreferenciadas
  - Adequado para software SIG e publicacoes

- **Relatorios PDF** (futuro): Resumos de analise abrangentes

**Dica**: Todos os downloads usam convencoes de nomenclatura consistentes para facil organizacao.""",

        "step_map_controls": "Passo 5: Controles do Mapa e Navegacao",
        "step5_map_controls_intro": "Navegue e interaja com o mapa:",
        "step5_content": """**Navegacao Basica:**
- **Zoom In/Out**: Roda de scroll do mouse, botoes +/-, ou clique duplo
- **Pan**: Clique e arraste em qualquer lugar do mapa
- **Tela Cheia**: Clique no botao de tela cheia para vista maior

**Ferramentas de Desenho** (canto superior esquerdo):
- Editar Camadas: Modifique poligonos existentes
- Excluir Camadas: Remova poligonos indesejados
- Desenhar Retangulo: Areas retangulares rapidas
- Desenhar Poligono: Formas com multiplos pontos
- Finalizar Desenho: Clique duplo ou clique no primeiro ponto

**Controles de Camada** (canto superior direito):
- Camadas Base: Alterne entre OpenStreetMap, Satelite, Terreno
- Sobreposicoes: Alterne camadas MapBiomas e Hansen
- Limites de Territorio: Mostrar/ocultar limites de territorios indigenas

**Recursos do Mapa:**
- Aneis azuis: Zonas de amortecimento externas
- Poligonos coloridos: Areas de analise desenhadas
- Limites de territorio: Limites de terras indigenas pre-carregados""",

        "step_data_understanding": "Passo 6: Entendendo os Dados e Resultados",
        "step6_data_understanding_intro": "Saiba sobre as fontes de dados e como interpretar resultados:",
        "step6_content": """**Fontes de Dados:**

**MapBiomas Collection 9** (Brasil):
- Cobertura: Todo o Brasil, 1985-2023
- Resolucao: 30 metros (baseado em Landsat)
- Classes: 62 tipos de cobertura (floresta, savana, agricultura, urbano, etc.)
- Precisao: ~90% no geral (varia por classe e regiao)

**Hansen/GLAD Global Forest Change**:
- Cobertura: Global (todos os continentes)
- Resolucao: 30 metros (baseado em Landsat)
- Classes: 256 classes combinando cobertura florestal, ano de perda (2000-2020), ganho (2000-2012)
- Melhor para: Deteccao e monitoramento de mudancas florestais

**Interpretacao de Resultados:**
- **Area (ha)**: Hectares = 10.000 m2 (cerca de 2,5 acres)
- **Pixels**: Cada pixel = 900 m2 (30m x 30m)
- **Percentagens**: Calculadas a partir da area total analisada
- **Valores de mudanca**: Positivo = aumento, Negativo = diminuicao

**Graficos**: Graficos de barras mostram as 15 principais classes. Diagramas Sankey mostram transicoes. Barras de Ganhos e Perdas mostram aumentos (direita) e diminuicoes (esquerda).""",

        # About section
        "about_title": "Sobre",
        "about_overview": "Visao Geral do Projeto",
        "about_desc": "Esta ferramenta de analise de uso e cobertura do solo faz parte de um projeto de pesquisa que estuda mudancas ambientais em Territorios Indigenas Brasileiros usando Google Earth Engine e dados MapBiomas. Estes dados sao comparados com mudancas de politicas e tendencias de desmatamento para entender os impactos nestas terras criticas.",
        "about_author": "Leandro Meneguelli Biondo",
        "about_role": "Candidato de PhD em Sustentabilidade",
        "about_university": "IGS/UBCO",
        "about_supervisor": "Orientador: Dr. Jon Corbett",
        "about_app_name": "Yvynation",
        "about_app_note": "e um nome para este aplicativo, nao e o conteudo completo do projeto.",
        "yvynation_meaning": '"Yvy" (Tupi-Guarani) significa terra, solo ou territorio - enfatizando o chao que pisamos e nossa conexao sagrada com a natureza. Frequentemente se relaciona ao conceito de "Yvy marae\'y" (Terra sem mal).',
        "nation_meaning": '"Nacao" refere-se a uma comunidade auto-governada ou povo com cultura, historia, lingua e terra compartilhadas. Significa autodeterminacao e governanca.',
        "data_sources_title": "Fontes de Dados",
        "mapbiomas_desc": "MapBiomas Collection 9 - Resolucao: 30m, Periodo: 1985-2023 (anual), 62 categorias de cobertura, CC BY 4.0",
        "territories_desc": "700+ territorios brasileiros com limites vetoriais e atributos - Projeto Territorios MapBiomas",
        "features_title": "Funcionalidades",
        "tech_title": "Tecnologias",

        # Layer Reference Guide
        "layer_reference": "Guia de Referencia de Camadas",
        "indigenous_territories_label": "Territorios Indigenas",
        "selected_territory_label": "Territorio Selecionado",
        "drawn_polygon_label": "Poligono Desenhado",
        "buffer_zone_label": "Zona de Amortecimento Externa",
        "mapbiomas_legend": "Classes de Cobertura MapBiomas",
        "hansen_legend": "Classes de Cobertura Hansen/GLAD",
        "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
        "aafc_legend": "Inventario Anual de Cultivos AAFC (Canada)",

        # Polygon analysis
        "polygon_analysis_header": "Analise de Poligono e Estatisticas",
        "draw_polygon_instruction": "Desenhe um poligono no mapa para comecar a analisar a cobertura do solo nessa area. Use as ferramentas de desenho no canto superior esquerdo do mapa.",
    },
    "es": {
        # Page
        "page_title": "Yvynation - Monitoreo de Territorios Indigenas",
        "main_page_title": "Yvynation - Plataforma de Monitoreo de Territorios Indigenas",
        "app_title": "Yvynation",
        "app_subtitle": "Plataforma de Monitoreo de Territorios Indigenas",
        "app_description": "Plataforma Global de Monitoreo Forestal",
        "author": "Leandro M. Biondo - Candidato de PhD - IGS/UBCO",

        # Navigation
        "map_tab": "Mapa",
        "analysis_tab": "Analisis",
        "tutorial_tab": "Tutorial",
        "about_tab": "Acerca de",

        # Sidebar
        "sidebar_title": "Capas y Controles",
        "controls_badge": "Controles",
        "mapbiomas_label": "MapBiomas",
        "mapbiomas_section_title": "Capas MapBiomas",
        "mapbiomas_select_year": "Seleccionar Ano MapBiomas",
        "mapbiomas_years": "Anos MapBiomas",
        "mapbiomas_layers_label": "Capas MapBiomas",
        "mapbiomas_layers_hint": "Numero de capas MapBiomas activas",
        "no_mapbiomas_selected": "Ningun ano MapBiomas seleccionado",
        "no_mapbiomas_added": "Agregue capas MapBiomas en la barra lateral",
        "add_to_map": "Agregar al mapa",
        "clear_all": "Limpiar todo",

        "hansen_label": "Hansen GFC",
        "hansen_section_title": "Hansen GFC",
        "hansen_select_year": "Seleccionar Ano Hansen",
        "hansen_years": "Anos Hansen",
        "hansen_layers_label": "Capas Hansen",
        "hansen_layers_hint": "Numero de capas Hansen activas",
        "hansen_gfc_label": "Cambio Forestal Global (GFC)",
        "hansen_gfc_layers_label": "Capas GFC",
        "no_hansen_selected": "Ningun ano Hansen seleccionado",
        "no_hansen_added": "Agregue capas Hansen en la barra lateral",
        "no_hansen_gfc_added": "Ninguna capa GFC habilitada",
        "data_layers": "Capas de datos",
        "year_layers": "Capas por ano",
        "tree_cover_btn": "Cobertura",
        "loss_btn": "Perdida",
        "gain_btn": "Ganancia",
        "add_btn": "Agregar",

        "tree_cover_2000": "Cobertura Forestal 2000",
        "tree_loss_period": "Perdida Forestal (2000-2023)",
        "tree_gain_period": "Ganancia Forestal (2000-2012)",

        # Base layer
        "base_layer": "Capa Base",
        "base_layer_hint": "Mapa base actual",

        # Active layers
        "active_layers": "Capas Activas",
        "analysis_active_badge": "Analisis Activo",

        # Territory section
        "territory_section_title": "Analisis de Territorio",
        "select_territory": "Seleccionar Territorio",
        "territory_by_country": "Filtrar por Pais",
        "territory_by_state": "Filtrar por Departamento",
        "selected_territory": "Territorio Seleccionado",
        "no_territory_selected": "Ningun territorio seleccionado",
        "search_territories": "Buscar territorios...",
        "select_territory_placeholder": "Seleccionar territorio",
        "click_map_to_select": "Haga clic en marcadores del mapa",
        "show_all_lands": "Mostrar Todas las Tierras",
        "hide_all_lands": "Ocultar Todas las Tierras",
        "select_territory_above": "Seleccione un territorio arriba",
        "compare_years": "Comparar anos",
        "compare_mapbiomas_years": "Comparar Anos MapBiomas",

        # Geometry section
        "geometry_section_title": "Geometria y Dibujo",
        "upload_geometry_file": "Cargar archivo de geometria",
        "analyze_selected_geometry": "Analizar geometria seleccionada",
        "map_overlays": "Superposiciones del mapa",
        "show_geometries": "Mostrar Geometrias",
        "hide_geometries": "Ocultar Geometrias",
        "show_change": "Mostrar Cambio",
        "hide_change": "Ocultar Cambio",

        # Map controls
        "draw_polygon": "Dibujar Poligono",
        "clear_drawings": "Limpiar Todo",
        "upload_geojson": "Cargar GeoJSON",

        # Analysis
        "run_analysis": "Ejecutar Analisis",
        "analysis_results": "Resultados del Analisis",
        "mapbiomas_analysis": "Analisis MapBiomas",
        "hansen_analysis": "Analisis Hansen",
        "export_results": "Exportar Resultados",
        "comparing_label": "Comparando...",

        # Comparison
        "compare_label": "Comparar:",
        "vs_label": "vs",
        "compare_btn": "Comparar",
        "year_comparison_results": "Resultados de Comparacion de Anos",
        "download_comparison_csv": "Descargar CSV de Comparacion",
        "total_gains": "Ganancias Totales",
        "total_losses": "Perdidas Totales",
        "net_change": "Cambio Neto",
        "comparison_available": "Comparacion Disponible",

        # Buttons
        "confirm": "Confirmar",
        "cancel": "Cancelar",
        "close": "Cerrar",
        "select": "Seleccionar",
        "dismiss": "Descartar",

        # Messages
        "loading": "Cargando...",
        "analyzing": "Analizando...",
        "initializing": "Inicializando Plataforma Yvynation...",
        "ee_init_error": "Error al inicializar Earth Engine: {error}",
        "error": "Error",
        "success": "Exito",

        # Analysis results
        "class": "Clase",
        "area_hectares": "Area (ha)",
        "area_km2": "Area (km2)",
        "percentage": "Porcentaje (%)",
        "year": "Ano",
        "change": "Cambio",
        "from_class": "De Clase",
        "to_class": "Para Clase",
        "area_changed": "Area Cambiada",

        # File upload
        "upload_file": "Cargar Archivo",
        "file_uploaded": "Archivo cargado exitosamente",
        "file_upload_error": "Error al cargar archivo",
        "select_file": "Seleccione archivo (GeoJSON, KML, Shapefile)",

        # Buffer operations
        "buffer_distance": "Distancia del Buffer (metros)",
        "create_buffer": "Crear Buffer",
        "buffer_created": "Buffer creado exitosamente",

        # Geometry
        "draw_area": "Dibujar Area de Interes",
        "upload_geometry": "Cargar Geometria",
        "geometry_loaded": "Geometria cargada",

        # Export
        "export_as_csv": "Exportar como CSV",
        "export_as_pdf": "Exportar como PDF",
        "export_as_zip": "Exportar como ZIP",
        "exporting": "Exportando...",
        "export_complete": "Exportacion completada",
        "export_analysis": "Exportar Analisis",

        # MapBiomas specific
        "mapbiomas_no_data": "No hay datos disponibles para el area seleccionada",
        "mapbiomas_process_error": "Error al procesar clase {class_id}: {error}",
        "mapbiomas_analysis_title": "Analisis de Cobertura Terrestre MapBiomas",
        "mapbiomas_year_range": "Rango de anos: {start} - {end}",

        # Hansen specific
        "hansen_tree_cover": "Cobertura Forestal",
        "hansen_tree_loss": "Perdida Forestal",
        "hansen_tree_gain": "Ganancia Forestal",
        "hansen_no_data": "Sin datos Hansen para el area seleccionada",

        # Settings / Quick settings
        "language": "Idioma",
        "theme": "Tema",
        "dark_mode": "Modo Oscuro",
        "light_mode": "Modo Claro",

        # Help & Info
        "help": "Ayuda",
        "documentation": "Documentacion",
        "about": "Acerca de Yvynation",
        "version": "Version",
        "powered_by": "Desarrollado por",

        # =====================================================================
        # Tutorial / Getting Started
        # =====================================================================
        "getting_started_header": "Como Usar Esta Plataforma",
        "getting_started_title": "Primeros Pasos",
        "getting_started_intro": "Esta plataforma permite analisis integral de cobertura del suelo para Brasil y monitoreo forestal global. Puede analizar areas personalizadas, territorios indigenas y zonas de amortiguamiento externas.",

        "step_language_region": "Paso 0: Seleccion de Idioma y Region",
        "step0_language_region_intro": "Configure su idioma y seleccione su region de interes:",
        "step0_content": """**Auto-Deteccion en la Primera Visita**

En su primera visita, la app puede detectar su ubicacion para configurar la region correcta:
- **America del Norte** (latitud > 10N) -> Configura Canada
- **America del Sur** -> Usa el idioma del navegador o Portugues (PT)
- Puede revisar o cambiar la configuracion en cualquier momento

**Seleccion Manual de Idioma**

Use los botones de idioma (EN / PT / ES) en la barra lateral. Su eleccion se guarda para su sesion.

**Seleccion Manual de Region**

Use los botones de region (Brasil / Canada) en la barra lateral:
- **Brasil**: Cobertura completa MapBiomas (1985-2023) + datos globales Hansen/GLAD
- **Canada**: Inventario de cultivos AAFC + datos globales Hansen/GLAD""",

        "step_custom_polygon": "Paso 1: Analizar un Poligono Personalizado",
        "step1_draw_intro": "Dibuje y analice cualquier area en el mapa:",
        "step1_content": """1. **Herramientas de Dibujo** (esquina superior izquierda del mapa):
   - Haga clic en **Rectangulo** para selecciones rectangulares rapidas
   - Haga clic en **Poligono** para formas personalizadas
   - Doble clic o clic en el primer punto para completar

2. **Seleccione Capas de Datos** (barra lateral):
   - **MapBiomas**: Cobertura del suelo brasilena (1985-2023, 62 clases, 30m)
   - **Hansen/GLAD**: Cambios forestales globales (2000-2020, 256 clases, 30m)
   - **Hansen GFC**: Cambios Forestales Globales (2000-2024, 30m)

3. **Resultados del Analisis**: Distribucion, estadisticas de area, graficos, CSV descargables

4. **Analisis de Zona de Buffer**: Cree buffers de 2km, 5km o 10km alrededor de poligonos""",

        "step_territory": "Paso 2: Analizar un Territorio Indigena",
        "step2_territory_intro": "Limites predefinidos de territorios indigenas con analisis historico:",
        "step2_content": """1. **Seleccionar Territorio** (seccion Analisis de Territorio):
   - Busque entre 400+ tierras indigenas reconocidas
   - Vea metadatos: area, ubicacion, estado

2. **Caracteristicas del Analisis**: Cambios historicos (1985-2023), diagramas Sankey, exportacion

3. **Zona de Amortiguamiento**: Cree zonas externas, compare uso del suelo dentro vs fuera""",

        "step_comparison": "Paso 3: Comparacion Multi-Anual",
        "step3_comparison_intro": "Compare cambios de cobertura entre dos anos:",
        "step3_content": """Seleccione 2+ anos, dibuje un poligono o territorio, y compare con tablas lado a lado, graficos de ganancias/perdidas, y diagramas Sankey.""",

        "step_export": "Paso 4: Exportar y Descargar Resultados",
        "step4_export_intro": "Guarde sus resultados para informes:",
        "step4_content": """Downloads CSV, exportaciones PNG, y reportes PDF (futuro).""",

        "step_map_controls": "Paso 5: Controles del Mapa",
        "step5_map_controls_intro": "Navegue e interactue con el mapa:",
        "step5_content": """Zoom, pan, herramientas de dibujo, controles de capas, y superposiciones de territorio.""",

        "step_data_understanding": "Paso 6: Entendiendo los Datos",
        "step6_data_understanding_intro": "Fuentes de datos e interpretacion de resultados:",
        "step6_content": """MapBiomas Collection 9 (Brasil, 1985-2023, 30m, 62 clases). Hansen/GLAD (Global, 30m, 256 clases). Area en hectares, pixels de 900m2, cambios positivos/negativos.""",

        # About section
        "about_title": "Acerca de",
        "about_overview": "Vision General del Proyecto",
        "about_desc": "Esta herramienta de analisis de uso y cobertura del suelo es parte de un proyecto de investigacion que estudia cambios ambientales en Territorios Indigenas Brasilenios usando Google Earth Engine y datos MapBiomas.",
        "about_author": "Leandro Meneguelli Biondo",
        "about_role": "Candidato de PhD en Sostenibilidad",
        "about_university": "IGS/UBCO",
        "about_supervisor": "Director: Dr. Jon Corbett",
        "about_app_name": "Yvynation",
        "about_app_note": "es un nombre para esta aplicacion, no es el contenido completo del proyecto.",
        "yvynation_meaning": '"Yvy" (Tupi-Guarani) significa tierra, suelo o territorio.',
        "nation_meaning": '"Nacion" se refiere a una comunidad autogobernada con cultura, historia, lengua y tierra compartidas.',
        "data_sources_title": "Fuentes de Datos",
        "mapbiomas_desc": "MapBiomas Collection 9 - Resolucion: 30m, Periodo: 1985-2023, 62 categorias, CC BY 4.0",
        "territories_desc": "700+ territorios brasilenios con limites vectoriales - Proyecto Territorios MapBiomas",
        "features_title": "Caracteristicas",
        "tech_title": "Tecnologias",

        # Layer Reference Guide
        "layer_reference": "Guia de Referencia de Capas",
        "indigenous_territories_label": "Territorios Indigenas",
        "selected_territory_label": "Territorio Seleccionado",
        "drawn_polygon_label": "Poligono Dibujado",
        "buffer_zone_label": "Zona de Amortiguamiento Externa",
        "mapbiomas_legend": "Clases de Cobertura MapBiomas",
        "hansen_legend": "Clases de Cobertura Hansen/GLAD",
        "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
        "aafc_legend": "Inventario Anual de Cultivos AAFC (Canada)",

        # Polygon analysis
        "polygon_analysis_header": "Analisis de Poligono y Estadisticas",
        "draw_polygon_instruction": "Dibuje un poligono en el mapa para comenzar a analizar la cobertura del suelo. Use las herramientas de dibujo en la esquina superior izquierda.",
    },
}


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Get translated string.

    Args:
        key: Translation key
        lang: Language code (defaults to 'en')
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string or key if not found
    """
    if lang is None:
        lang = "en"

    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    result = translations.get(key, TRANSLATIONS["en"].get(key, key))

    if kwargs:
        try:
            result = result.format(**kwargs)
        except KeyError:
            pass

    return result


def get_language_options() -> Dict[str, str]:
    """Get available languages."""
    return {
        "en": "English",
        "pt": "Portugues",
        "es": "Espanol",
    }
