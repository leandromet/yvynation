"""
Tutorial Component for Yvynation Platform
Displays bilingual Getting Started guide with 6 steps for using the platform
"""

import streamlit as st
from translations import t, get_translation


def get_lang():
    """Get current language from session state"""
    return st.session_state.get('language', 'en')


def render_getting_started_tutorial():
    """Render the complete bilingual Getting Started tutorial with all 6 steps"""
    
    with st.expander(f"📚 {t('getting_started_header')}", expanded=False):
        st.markdown(f"### {t('getting_started_title')}\n\n{t('getting_started_intro')}")
        
        # Step 0: Language & Region Selection
        with st.expander(t('step_language_region'), expanded=False):
            st.markdown(f"**{t('step0_language_region_intro')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
        ### **Seleção de Idioma**
        
        Clique no botão 🌐 **Idioma** no canto superior direito para alternar entre Inglês e Português (Brasil). Sua escolha é salva para sua sessão.
        
        ### **Seleção de Região**
        
        Use o menu suspenso **🌎 Selecionar Região** na barra lateral para escolher entre:
        
        - **🇧🇷 Brasil**: Cobertura completa de MapBiomas (1985-2023) + dados globais de Hansen/GLAD
        - **🇨🇦 Canadá**: Inventário de cultivos AAFC + dados globais de Hansen/GLAD
        
        O mapa será centralizado em sua região selecionada. Você ainda pode analisar outras áreas globais usando as ferramentas de desenho.
                """)
            else:
                st.markdown("""
        ### **Language Selection**
        
        Click the 🌐 **Language** button in the top-right corner to switch between English and Portuguese (Brazil). Your choice is saved for your session.
        
        ### **Region Selection**
        
        Use the **🌎 Select Region** dropdown in the sidebar to choose between:
        
        - **🇧🇷 Brazil**: Full MapBiomas coverage (1985-2023) + Hansen/GLAD global data
        - **🇨🇦 Canada**: AAFC crop inventory + Hansen/GLAD global data
        
        The map will center on your selected region. You can still analyze other global areas using the drawing tools.
                """)
        
        # Step 1: Custom Polygon Analysis
        with st.expander(t('step_custom_polygon'), expanded=False):
            st.markdown(f"**{t('step1_draw_intro')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
        1. **Ferramentas de Desenho** (canto superior esquerdo do mapa):
           - Clique na ferramenta **Retângulo** (⬜) para seleções retangulares rápidas
           - Clique na ferramenta **Polígono** (🔷) para formas personalizadas com múltiplos pontos
           - Clique duplo ou clique no primeiro ponto novamente para completar um polígono
        
        2. **Selecione Camadas de Dados** (barra lateral esquerda):
           - **MapBiomas**: Cobertura do solo brasileira (1985-2023, 62 classes, resolução 30m)
           - **Hansen/GLAD**: Mudanças florestais globais (2000-2020, 256 classes, resolução 30m)
           - **Hansen GFC**: Mudanças Globais de Floresta (2000-2024, resolução 30m) - incluindo ganho e perda de cobertura florestal
           - Alterne vários anos para ativar comparações
        
        3. **Resultados da Análise**:
           - Distribuição de cobertura do solo por classe
           - Estatísticas de área (hectares e percentuais)
           - Gráficos visuais e tabelas de dados
           - Arquivos CSV para download com prefixo "original_"
        
        4. **Análise de Zona de Buffer** (NOVO):
           - Após desenhar, clique em "🔵 Adicionar Zona de Buffer"
           - Escolha a distância do buffer: **2km**, **5km** ou **10km**
           - Cria uma zona em forma de anel ao redor do seu polígono
           - Ative "📊 Comparar Polígono vs Buffer" para analisar ambas as áreas lado a lado
           - Arquivos CSV terão prefixo "buffer_" para dados da zona de buffer
        
        💡 **Dicas**:
        - Exclua polígonos indesejados clicando no ícone de lixeira (🗑️) nas ferramentas de desenho
        - Desenhe múltiplas áreas pequenas para comparar diferentes locais
        - Use zonas de buffer para entender efeitos de borda e uso do solo circundante
        - Hansen GFC é ideal para monitorar perda e ganho florestal em qualquer lugar do mundo
                """)
            else:
                st.markdown("""
        1. **Drawing Tools** (top-left corner of map):
           - Click the **Rectangle** tool (⬜) for quick rectangular selections
           - Click the **Polygon** tool (🔷) for custom shapes with multiple points
           - Double-click or click the first point again to complete a polygon
        
        2. **Select Data Layers** (left sidebar):
           - **MapBiomas**: Brazilian land cover (1985-2023, 62 classes, 30m resolution)
           - **Hansen/GLAD**: Global forest change (2000-2020, 256 classes, 30m resolution)
           - **Hansen GFC**: Global Forest Change (2000-2024, 30m resolution) - includes forest cover gain and loss
           - Toggle multiple years to enable comparisons
        
        3. **Analysis Results**:
           - Land cover distribution by class
           - Area statistics (hectares and percentages)
           - Visual charts and data tables
           - Downloadable CSV files with "original_" prefix
        
        4. **Buffer Zone Analysis** (NEW):
           - After drawing, click "🔵 Add Buffer Zone"
           - Choose buffer distance: **2km**, **5km**, or **10km**
           - Creates a ring-shaped zone around your polygon
           - Enable "📊 Compare Polygon vs Buffer" to analyze both areas side-by-side
           - CSV files will have "buffer_" prefix for buffer zone data
        
        💡 **Tips**:
        - Delete unwanted polygons by clicking the trash icon (🗑️) in drawing tools
        - Draw multiple small areas to compare different locations
        - Use buffer zones to understand edge effects and surrounding land use
        - Hansen GFC is ideal for monitoring forest loss and gain anywhere in the world
                """)
        
        # Step 2: Territory Analysis
        with st.expander(t('step_territory'), expanded=False):
            st.markdown(f"**{t('step2_territory_intro')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
        **Limites de territórios indígenas pré-definidos com análise histórica:**
        
        1. **Selecionar Território** (aba 📊 Territory Analysis na barra lateral):
           - Filtrar por **Estado** ou explorar todos os territórios
           - Escolher entre 400+ terras indígenas oficialmente reconhecidas
           - Ver metadados do território: área, localização, status de reconhecimento
        
        2. **Recursos de Análise de Território**:
           - Mudanças históricas de cobertura do solo (1985-2023)
           - Mudanças de área por classe de cobertura
           - Tendências de desmatamento e regeneração
           - Diagramas de transição (gráficos Sankey) mostrando conversões entre classes
           - Exportar todos os dados e visualizações
        
        3. **Análise de Zona de Amortecimento para Territórios**:
           - Criar **zonas de amortecimento externas** (2km/5km/10km) ao redor de todo o território
           - Comparar uso do solo **dentro vs fora** da fronteira protegida
           - Identificar zonas de pressão e padrões de invasão
           - Ativar caixa "📊 Compare Territory vs Buffer"
           - Resultados aparecem em abas separadas: **"📍 Original Area"** e **"🔵 Buffer Zone Xkm"**
        
        💡 **Dicas**:
        - Compare múltiplos territórios no mesmo estado para identificar padrões regionais
        - Use análise de amortecimento para avaliar ameaças externas e integridade de limites
        - Comparações de longo prazo (1985 vs 2023) revelam efetividade da proteção
        - Exporte dados para integração com software SIG ou relatórios
                """)
            else:
                st.markdown("""
        **Pre-defined indigenous territory boundaries with historical analysis:**
        
        1. **Select Territory** (📊 Territory Analysis tab in sidebar):
           - Filter by **State** or browse all territories
           - Choose from 400+ officially recognized indigenous lands
           - View territory metadata: area, location, recognition status
        
        2. **Territory Analysis Features**:
           - Historical land cover changes (1985-2023)
           - Area changes by land cover class
           - Deforestation and regeneration trends
           - Transition diagrams (Sankey charts) showing conversions between classes
           - Export all data and visualizations
        
        3. **Buffer Zone Analysis for Territories**:
           - Create **external buffer zones** (2km/5km/10km) around the entire territory
           - Compare land use **inside vs outside** the protected boundary
           - Identify pressure zones and encroachment patterns
           - Enable "📊 Compare Territory vs Buffer" checkbox
           - Results appear in separate tabs: **"📍 Original Area"** and **"🔵 Buffer Zone Xkm"**
        
        💡 **Tips**:
        - Compare multiple territories in the same state to identify regional patterns
        - Use buffer analysis to assess external threats and boundary integrity
        - Long-term comparisons (1985 vs 2023) reveal protection effectiveness
        - Export data for integration with GIS software or reports
                """)
        
        # Step 3: Multi-Year Comparison
        with st.expander(t('step_comparison'), expanded=False):
            st.markdown(f"**{t('step3_comparison_intro')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
        **Compare mudanças de cobertura do solo entre quaisquer dois anos:**
        
        1. **Configurar Comparação** (aba 📈 Comparison):
           - Primeiro selecione **2+ anos** nos controles de camada (barra lateral)
           - Desenhe um polígono ou selecione um território
           - Navegue até a aba **📈 Comparison**
           - Escolha **Year 1** (linha de base) e **Year 2** (comparação)
        
        2. **Clique nos Botões de Comparação**:
           - **🔄 Compare MapBiomas Years**: Mudanças de cobertura do solo brasileira
           - **🔄 Compare Hansen Years**: Mudanças de floresta global
        
        3. **Ver Resultados**:
           - **Data Table**: Valores de área lado a lado com cálculos de mudança
           - **Side-by-side Charts**: Distribuição visual para cada ano
           - **Gains & Losses**: Gráfico de barras horizontal mostrando aumentos/diminuições
           - **Sankey Diagram**: Gráfico de fluxo mostrando transições de cobertura do solo
           - **Summary Metrics**: Estatísticas-chave de uma olhada
        
        4. **Modo de Comparação de Amortecimento**:
           - Quando comparação de amortecimento está habilitada, execute comparações em ambas as áreas
           - Resultados aparecem em abas separadas para zonas originais e de amortecimento
           - Baixe arquivos CSV separados para cada área
        
        💡 **Dicas**:
        - **Tendências de longo prazo**: Compare 1985 vs 2023 para 38 anos de mudança
        - **Mudanças recentes**: Compare anos consecutivos (2022 vs 2023) para atividade atual
        - **Impacto de política**: Compare anos antes/depois da implementação de política
        - **Eventos de desmatamento**: Use intervalos de 5 anos para identificar grandes mudanças
                """)
            else:
                st.markdown("""
        **Compare land cover changes between any two years:**
        
        1. **Setup Comparison** (📈 Comparison tab):
           - First select **2+ years** in the layer controls (sidebar)
           - Draw a polygon or select a territory
           - Navigate to the **📈 Comparison** tab
           - Choose **Year 1** (baseline) and **Year 2** (comparison)
        
        2. **Click Comparison Buttons**:
           - **🔄 Compare MapBiomas Years**: Brazilian land cover changes
           - **🔄 Compare Hansen Years**: Global forest changes
        
        3. **View Results**:
           - **Data Table**: Side-by-side area values with change calculations
           - **Side-by-side Charts**: Visual distribution for each year
           - **Gains & Losses**: Horizontal bar chart showing increases/decreases
           - **Sankey Diagram**: Flow chart showing land cover transitions
           - **Summary Metrics**: Total change, loss, and gain values
        
        4. **Buffer Comparison Mode**:
           - When buffer compare is enabled, perform comparisons on both areas
           - Results appear in separate tabs for original and buffer zones
           - Download separate CSV files for each area
        
        💡 **Tips**:
        - **Long-term trends**: Compare 1985 vs 2023 for 38 years of change
        - **Recent changes**: Compare consecutive years (2022 vs 2023) for current activity
        - **Policy impact**: Compare years before/after policy implementation
        - **Deforestation events**: Use 5-year intervals to identify major changes
                """)
        
        # Step 4: Export & Download
        with st.expander(t('step_export'), expanded=False):
            st.markdown(f"**{t('step4_export_intro')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
        **Salve os resultados da sua análise para relatórios e análise adicional:**
        
        - **Downloads CSV**: Clique em botões "📥 Download CSV" em cada aba de análise
          - Dados de ano individual: `original_mapbiomas_2023.csv`
          - Dados de zona de amortecimento: `buffer_mapbiomas_2023.csv`
          - Tabelas de comparação com cálculos de mudança
        
        - **Exportações PNG**: Imagens de alta resolução do Earth Engine
          - Exporte regiões de análise como imagens georreferenciadas
          - Adequado para software SIG e publicações
        
        - **Relatórios PDF** (futuro): Resumos de análise abrangentes
        
        💡 **Dica**: Todos os downloads usam convenções de nomenclatura consistentes para fácil organização
                """)
            else:
                st.markdown("""
        **Save your analysis results for reports and further analysis:**
        
        - **CSV Downloads**: Click "📥 Download CSV" buttons in each analysis tab
          - Individual year data: `original_mapbiomas_2023.csv`
          - Buffer zone data: `buffer_mapbiomas_2023.csv`
          - Comparison tables with change calculations
        
        - **PNG Exports**: High-resolution images from Earth Engine
          - Export analysis regions as georeferenced images
          - Suitable for GIS software and publications
        
        - **PDF Reports** (future): Comprehensive analysis summaries
        
        💡 **Tip**: All downloads use consistent naming conventions for easy organization
                """)
        
        # Step 5: Map Controls & Navigation
        with st.expander(t('step_map_controls'), expanded=False):
            st.markdown(f"**{t('step5_map_controls_intro', default='Map Controls & Navigation')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
            **Navegação Básica:**
            - **Zoom In/Out**: 
              - Roda de scroll do mouse
              - Botões **+/−** (canto superior esquerdo)
              - Clique duplo para fazer zoom
            - **Pan**: Clique e arraste em qualquer lugar do mapa
            - **Fullscreen**: Clique no botão de tela cheia (área superior esquerda) para vista maior
            
            **Ferramentas de Desenho** (canto superior esquerdo):
            - **✏️ Edit Layers**: Modifique polígonos existentes
            - **🗑️ Delete Layers**: Remova polígonos indesejados
            - **⬜ Draw Rectangle**: Áreas retangulares rápidas
            - **🔷 Draw Polygon**: Formas personalizadas com múltiplos pontos
            - **Finish Drawing**: Clique duplo ou clique no primeiro ponto para completar
            
            **Controles de Camada** (canto superior direito):
            - **Base Layers**: Alterne entre visualizações OpenStreetMap, Satélite, Terreno
            - **Overlays**: Alterne camadas MapBiomas e Hansen ligadas/desligadas
            - **Transparency**: Algumas camadas suportam ajuste de transparência
            - **Territory Boundaries**: Mostrar/ocultar limites de territórios indígenas
            
            **Recursos do Mapa:**
            - **Anéis azul-céu**: Zonas de amortecimento externas (quando criadas)
            - **Polígonos coloridos**: Suas áreas de análise desenhadas
            - **Limites de território**: Limites de terras indígenas pré-carregados
            - **Barra de escala**: Parte inferior esquerda mostra escala do mapa
            - **Coordenadas**: Passe o mouse para ver latitude/longitude (se habilitado)
            
            💡 **Dica de Navegação**: Clique no botão de início para redefinir o mapa para vista inicial do Brasil
                """)
            else:
                st.markdown("""
            **Basic Navigation:**
            - **Zoom In/Out**: 
              - Mouse scroll wheel
              - **+/−** buttons (top-left corner)
              - Double-click to zoom in
            - **Pan**: Click and drag anywhere on the map
            - **Fullscreen**: Click fullscreen button (top-left area) for larger view
            
            **Drawing Tools** (top-left corner):
            - **✏️ Edit Layers**: Modify existing polygons
            - **🗑️ Delete Layers**: Remove unwanted polygons
            - **⬜ Draw Rectangle**: Quick rectangular areas
            - **🔷 Draw Polygon**: Custom multi-point shapes
            - **Finish Drawing**: Double-click or click first point to complete
            
            **Layer Controls** (top-right corner):
            - **Base Layers**: Switch between OpenStreetMap, Satellite, Terrain views
            - **Overlays**: Toggle MapBiomas and Hansen layers on/off
            - **Transparency**: Some layers support transparency adjustment
            - **Territory Boundaries**: Show/hide indigenous territory outlines
            
            **Map Features:**
            - **Sky-blue rings**: External buffer zones (when created)
            - **Colored polygons**: Your drawn analysis areas
            - **Territory boundaries**: Pre-loaded indigenous land boundaries
            - **Scale bar**: Bottom-left shows map scale
            - **Coordinates**: Hover to see latitude/longitude (if enabled)
            
            💡 **Navigation Tip**: Click the home button to reset the map to initial Brazil view
                """)
        
        # Step 6: Understanding Data & Results
        with st.expander(t('step_data_understanding'), expanded=False):
            st.markdown(f"**{t('step6_data_understanding_intro', default='Understanding Data & Results')}**")
            if get_lang() == 'pt-br':
                st.markdown("""
            **Fontes de Dados:**
            
            **MapBiomas Collection 9** (Brasil):
            - **Cobertura**: Todo o Brasil, 1985-2023
            - **Resolução**: 30 metros (baseado em Landsat)
            - **Classes**: 62 tipos de cobertura do solo incluindo:
              - Vegetação natural (floresta, savana, pastagem, zona úmida)
              - Agricultura (culturas, pastagem, plantações)
              - Áreas urbanas, corpos d'água, mineração
            - **Frequência de atualização**: Lançamentos anuais
            - **Precisão**: ~90% no geral (varia por classe e região)
            
            **Hansen/GLAD Global Forest Change**:
            - **Cobertura**: Global (todos os continentes)
            - **Resolução**: 30 metros (baseado em Landsat)
            - **Classes**: 256 classes de uso do solo combinando:
              - Presença/ausência de cobertura florestal
              - Ano de perda de floresta (2000-2020)
              - Ganho de floresta (2000-2012)
              - Categorias de uso do solo
            - **Melhor para**: Detecção e monitoramento de mudanças florestais
            - **Consolidação**: Alterne "Use consolidated classes" para vista simplificada de 12 classes
            
            **Interpretação de Resultados:**
            - **Área (ha)**: Hectares = 10.000 m² (cerca de 2,5 acres)
            - **Pixels**: Cada pixel = 900 m² (30m × 30m)
            - **Percentagens**: Calculadas a partir da área total analisada
            - **Valores de mudança**: Positivo = aumento, Negativo = diminuição
            - **Transições**: Fluxo de uma classe de cobertura do solo para outra
            
            **Gráficos & Visualizações:**
            - **Gráficos de barras**: 15 principais classes por área (personalizável)
            - **Diagramas Sankey**: Fluxo de transições de cobertura do solo entre anos
            - **Ganhos & Perdas**: Barras horizontais mostrando aumentos (direita) e diminuições (esquerda)
            - **Métricas de resumo**: Estatísticas-chave de uma olhada
            
            💡 **Nota de Precisão**: Os resultados dependem da qualidade dos dados de origem. Valide referenciando os dois conjuntos de dados.
                """)
            else:
                st.markdown("""
            **Data Sources:**
            
            **MapBiomas Collection 9** (Brazil):
            - **Coverage**: All of Brazil, 1985-2023
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 62 land cover types including:
              - Natural vegetation (forest, savanna, grassland, wetland)
              - Agriculture (crops, pasture, plantations)
              - Urban areas, water bodies, mining
            - **Update frequency**: Annual releases
            - **Accuracy**: ~90% overall (varies by class and region)
            
            **Hansen/GLAD Global Forest Change**:
            - **Coverage**: Global (all continents)
            - **Resolution**: 30 meters (Landsat-based)
            - **Classes**: 256 land use classes combining:
              - Forest cover presence/absence
              - Forest loss year (2000-2020)
              - Forest gain (2000-2012)
              - Land use categories
            - **Best for**: Forest change detection and monitoring
            - **Consolidation**: Toggle "Use consolidated classes" for simplified 12-class view
            
            **Result Interpretation:**
            - **Area (ha)**: Hectares = 10,000 m² (about 2.5 acres)
            - **Pixels**: Each pixel = 900 m² (30m × 30m)
            - **Percentages**: Calculated from total analyzed area
            - **Change values**: Positive = increase, Negative = decrease
            - **Transitions**: Flow from one land cover class to another
            
            **Charts & Visualizations:**
            - **Bar charts**: Top 15 classes by area (customizable)
            - **Sankey diagrams**: Flow of land cover transitions between years
            - **Gains & Losses**: Horizontal bars showing increases (right) and decreases (left)
            - **Summary metrics**: Key statistics at a glance
            
            💡 **Accuracy Note**: Results depend on source data quality. Cross-reference with both datasets for validation.
                """)
