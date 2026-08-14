"""Spanish translations for Yvynation.

One file per language: add/edit keys here only. English (en.py)
is the reference dictionary — every key must exist there; other
languages fall back to English for any missing key.
Check coverage with:  python -m yvynation.utils.translations
"""

TRANSLATIONS_ES = {
        # Page
    "page_title": "Yvynation - Monitoreo de Territorios Indígenas",
    "main_page_title": "Yvynation - Plataforma de Monitoreo de Territorios Indígenas",
    "app_title": "Yvynation",
    "app_subtitle": "Plataforma de Monitoreo de Territorios Indígenas",
    "app_description": "Plataforma Global de Monitoreo Forestal",
    "author": "Leandro M. Biondo - Candidato de PhD - IGS/UBCO",

    # Navigation
    "map_tab": "Mapa",
    "analysis_tab": "Análisis",
    "tutorial_tab": "Tutorial",
    "about_tab": "Acerca de",

    # Sidebar
    "sidebar_title": "Capas y Controles",
    "controls_badge": "Controles",
    "mapbiomas_label": "MapBiomas",
    "mapbiomas_section_title": "Capas MapBiomas",
    "mapbiomas_select_year": "Seleccionar Año MapBiomas",
    "mapbiomas_years": "Años MapBiomas",
    "mapbiomas_layers_label": "Capas MapBiomas",
    "mapbiomas_layers_hint": "Número de capas MapBiomas activas",
    "no_mapbiomas_selected": "Ningún año MapBiomas seleccionado",
    "no_mapbiomas_added": "Agregue capas MapBiomas en la barra lateral",
    "add_to_map": "Agregar al mapa",
    "clear_all": "Limpiar todo",

    "hansen_label": "Hansen GFC",
    "hansen_section_title": "Hansen GFC",
    "hansen_select_year": "Seleccionar Año Hansen",
    "hansen_years": "Años Hansen",
    "hansen_layers_label": "Capas Hansen",
    "hansen_layers_hint": "Número de capas Hansen activas",
    "hansen_gfc_label": "Cambio Forestal Global (GFC)",
    "hansen_gfc_layers_label": "Capas GFC",
    "no_hansen_selected": "Ningún año Hansen seleccionado",
    "no_hansen_added": "Agregue capas Hansen en la barra lateral",
    "no_hansen_gfc_added": "Ninguna capa GFC habilitada",
    "data_layers": "Capas de datos",
    "year_layers": "Capas por año",
    "tree_cover_btn": "Cobertura",
    "loss_btn": "Pérdida",
    "gain_btn": "Ganancia",
    "add_btn": "Agregar",

    "tree_cover_2000": "Cobertura Forestal 2000",
    "tree_loss_period": "Pérdida Forestal (2000-2023)",
    "tree_gain_period": "Ganancia Forestal (2000-2012)",

    # Base layer
    "base_layer": "Capa Base",
    "base_layer_hint": "Mapa base actual",

    # Active layers
    "active_layers": "Capas Activas",
    "analysis_active_badge": "Análisis Activo",

    # Territory section
    "territory_section_title": "Análisis de Territorio",
    "select_territory": "Seleccionar Territorio",
    "territory_by_country": "Filtrar por País",
    "territory_by_state": "Filtrar por Departamento",
    "selected_territory": "Territorio Seleccionado",
    "no_territory_selected": "Ningún territorio seleccionado",
    "search_territories": "Buscar territorios...",
    "select_territory_placeholder": "Seleccionar territorio",
    "click_map_to_select": "Haga clic en marcadores del mapa",
    "show_all_lands": "Mostrar Todas las Tierras",
    "hide_all_lands": "Ocultar Todas las Tierras",
    "select_territory_above": "Seleccione un territorio arriba",
    "compare_years": "Comparar años",
    "compare_mapbiomas_years": "Comparar Años MapBiomas",

    # Geometry section
    "geometry_section_title": "Geometría y Dibujo",
    "upload_geometry_file": "Cargar archivo de geometría",
    "analyze_selected_geometry": "Analizar geometría seleccionada",
    "map_overlays": "Superposiciones del mapa",
    "show_geometries": "Mostrar Geometrías",
    "hide_geometries": "Ocultar Geometrías",
    "show_change": "Mostrar Cambio",
    "hide_change": "Ocultar Cambio",

    # Map controls
    "draw_polygon": "Dibujar Polígono",
    "clear_drawings": "Limpiar Todo",
    "upload_geojson": "Cargar GeoJSON",

    # Analysis
    "run_analysis": "Ejecutar Análisis",
    "analysis_results": "Resultados del Análisis",
    "mapbiomas_analysis": "Análisis MapBiomas",
    "hansen_analysis": "Análisis Hansen",
    "export_results": "Exportar Resultados",
    "comparing_label": "Comparando...",

    # Comparison
    "compare_label": "Comparar:",
    "vs_label": "vs",
    "compare_btn": "Comparar",
    "year_comparison_results": "Resultados de Comparación de Años",
    "download_comparison_csv": "Descargar CSV de Comparación",
    "total_gains": "Ganancias Totales",
    "total_losses": "Pérdidas Totales",
    "net_change": "Cambio Neto",
    "comparison_available": "Comparación Disponible",

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
    "success": "Éxito",

    # Analysis results
    "class": "Clase",
    "area_hectares": "Área (ha)",
    "area_km2": "Área (km2)",
    "percentage": "Porcentaje (%)",
    "year": "Año",
    "change": "Cambio",
    "from_class": "De Clase",
    "to_class": "A Clase",
    "area_changed": "Área Cambiada",

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
    "draw_area": "Dibujar Área de Interés",
    "upload_geometry": "Cargar Geometría",
    "geometry_loaded": "Geometría cargada",

    # Export
    "export_as_csv": "Exportar como CSV",
    "export_as_pdf": "Exportar como PDF",
    "export_as_zip": "Exportar como ZIP",
    "exporting": "Exportando...",
    "export_complete": "Exportación completada",
    "export_analysis": "Exportar Análisis",

    # MapBiomas specific
    "mapbiomas_no_data": "No hay datos disponibles para el área seleccionada",
    "mapbiomas_process_error": "Error al procesar clase {class_id}: {error}",
    "mapbiomas_analysis_title": "Análisis de Cobertura Terrestre MapBiomas",
    "mapbiomas_year_range": "Rango de años: {start} - {end}",

    # Hansen specific
    "hansen_tree_cover": "Cobertura Forestal",
    "hansen_tree_loss": "Pérdida Forestal",
    "hansen_tree_gain": "Ganancia Forestal",
    "hansen_no_data": "Sin datos Hansen para el área seleccionada",

    # Settings / Quick settings
    "language": "Idioma",
    "theme": "Tema",
    "dark_mode": "Modo Oscuro",
    "light_mode": "Modo Claro",

    # Help & Info
    "help": "Ayuda",
    "documentation": "Documentación",
    "about": "Acerca de Yvynation",
    "version": "Versión",
    "powered_by": "Desarrollado por",

    # =====================================================================
    # Tutorial / Getting Started
    # =====================================================================
    "getting_started_header": "Como Usar Esta Plataforma",
    "getting_started_title": "Primeros Pasos",
    "getting_started_intro": "Esta plataforma permite análisis integral de cobertura del suelo para Brasil y monitoreo forestal global. Puede analizar áreas personalizadas, territorios indígenas y zonas de amortiguamiento externas.",

    "step_language_region": "Paso 0: Selección de Idioma y Región",
    "step0_language_region_intro": "Configure su idioma y seleccione su región de interes:",
    "step0_content": """**Autodetección en la Primera Visita**

En su primera visita, la app puede detectar su ubicación para configurar la región correcta:
- **América del Norte** (latitud > 10N) -> Configura Canadá
- **América del Sur** -> Usa el idioma del navegador o Portugués (PT)
- Puede revisar o cambiar la configuración en cualquier momento

**Selección Manual de Idioma**

Use los botones de idioma (EN / PT / ES) en la barra lateral. Su elección se guarda para su sesion.

**Selección Manual de Región**

Use los botones de región (Brasil / Canadá) en la barra lateral:
- **Brasil**: Cobertura completa MapBiomas (1985-2024) + datos globales Hansen/GLAD
- **Canadá**: Inventario de cultivos AAFC + datos globales Hansen/GLAD""",

    "step_custom_polygon": "Paso 1: Analizar un Polígono Personalizado",
    "step1_draw_intro": "Dibuje y analice cualquier área en el mapa:",
    "step1_content": """1. **Herramientas de Dibujo** (esquina superior izquierda del mapa):
   - Haga clic en **Rectángulo** para selecciones rectangulares rápidas
   - Haga clic en **Polígono** para formas personalizadas
   - Doble clic o clic en el primer punto para completar

2. **Seleccione Capas de Datos** (barra lateral):
   - **MapBiomas**: Cobertura del suelo brasileña (1985-2024, 62 clases, 30m)
   - **Hansen/GLAD**: Cambios forestales globales (2000-2020, 256 clases, 30m)
   - **Hansen GFC**: Cambios Forestales Globales (2000-2024, 30m)

3. **Resultados del Análisis**: Distribución, estadísticas de área, gráficos, CSV descargables

4. **Análisis de Zona de Buffer**: Cree buffers de 2km, 5km o 10km alrededor de polígonos""",

    "step_territory": "Paso 2: Analizar un Territorio Indígena",
    "step2_territory_intro": "Limites predefinidos de territorios indígenas con análisis histórico:",
    "step2_content": """1. **Seleccionar Territorio** (seccion Análisis de Territorio):
   - Busque entre 400+ tierras indígenas reconocidas
   - Vea metadatos: área, ubicación, estado

2. **Características del Análisis**: Cambios historicos (1985-2024), diagramas Sankey, exportación

3. **Zona de Amortiguamiento**: Cree zonas externas, compare uso del suelo dentro vs fuera""",

    "step_comparison": "Paso 3: Comparación Multi-Anual",
    "step3_comparison_intro": "Compare cambios de cobertura entre dos años:",
    "step3_content": """Seleccione 2+ años, dibuje un polígono o territorio, y compare con tablas lado a lado, gráficos de ganancias/pérdidas, y diagramas Sankey.""",

    "step_export": "Paso 4: Exportar y Descargar Resultados",
    "step4_export_intro": "Guarde sus resultados para informes:",
    "step4_content": """Downloads CSV, exportaciones PNG, y reportes PDF (futuro).""",

    "step_map_controls": "Paso 5: Controles del Mapa",
    "step5_map_controls_intro": "Navegue e interactúe con el mapa:",
    "step5_content": """Zoom, pan, herramientas de dibujo, controles de capas, y superposiciones de territorio.""",

    "step_data_understanding": "Paso 6: Entendiendo los Datos",
    "step6_data_understanding_intro": "Fuentes de datos e interpretacion de resultados:",
    "step6_content": """MapBiomas Collection 10 (Brasil, 1985-2024, 30m, 62 clases). Hansen/GLAD (Global, 30m, 256 clases). Área en hectáreas, píxeles de 900m2, cambios positivos/negativos.""",

    # About section
    "about_title": "Acerca de",
    "about_overview": "Visión General del Proyecto",
    "about_desc": "Esta herramienta de análisis de uso y cobertura del suelo es parte de un proyecto de investigación que estudia cambios ambientales en Territorios Indígenas Brasileños usando Google Earth Engine y datos MapBiomas.",
    "about_author": "Leandro Meneguelli Biondo",
    "about_role": "Candidato de PhD en Sostenibilidad",
    "about_university": "IGS/UBCO",
    "about_supervisor": "Director: Dr. Jon Corbett",
    "about_app_name": "Yvynation",
    "about_app_note": "es un nombre para esta aplicación, no es el contenido completo del proyecto.",
    "yvynation_meaning": '"Yvy" (Tupí-Guaraní) significa tierra, suelo o territorio.',
    "nation_meaning": '"Nación" se refiere a una comunidad autogobernada con cultura, historia, lengua y tierra compartidas.',
    "data_sources_title": "Fuentes de Datos",
    "mapbiomas_desc": "MapBiomas Collection 10 - Resolución: 30m, Período: 1985-2024, 62 categorías, CC BY 4.0",
    "territories_desc": "700+ territorios brasileños con límites vectoriales - Proyecto Territorios MapBiomas",
    "features_title": "Características",
    "tech_title": "Tecnologias",

    # Layer Reference Guide
    "layer_reference": "Guía de Referencia de Capas",
    "indigenous_territories_label": "Territorios Indígenas",
    "selected_territory_label": "Territorio Seleccionado",
    "drawn_polygon_label": "Polígono Dibujado",
    "buffer_zone_label": "Zona de Amortiguamiento Externa",
    "mapbiomas_legend": "Clases de Cobertura MapBiomas",
    "hansen_legend": "Clases de Cobertura Hansen/GLAD",
    "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
    "aafc_legend": "Inventario Anual de Cultivos AAFC (Canadá)",

    # Polygon analysis
    "polygon_analysis_header": "Análisis de Polígono y Estadísticas",
    "draw_polygon_instruction": "Dibuje un polígono en el mapa para comenzar a analizar la cobertura del suelo. Use las herramientas de dibujo en la esquina superior izquierda.",

    # Portal page
    "about_section": "Acerca de Yvynation",
    "about_description": "Yvynation es una plataforma integral para el monitoreo y análisis de tierras indígenas. Combina imágenes de satélite, herramientas de análisis geoespacial y deteccion de cambios forestales para proporcionar información sobre cambios en el uso del suelo y dinámicas de ecosistemas.",
    
    # Sidebar sections
    "geometry_tools": "Herramientas de Geometría",
    "geometry_section": "Geometría y Dibujo",
    "buffer_controls": "Controles de Buffer",
    "analysis_settings": "Configuración de Análisis",
    "territory_selection": "Selección de Territorio",
    "comparison_controls": "Controles de Comparación",
    
    # Form inputs
    "enter_distance": "Ingrese la distancia",
    "territory_search": "Buscar Territorio",
    "search_territory": "Busque territorio por nombre...",
    "country": "País",
    "territory_type": "Tipo de Territorio",
    "indigenous_lands_btn": "🪶 Indígenas",
    "conservation_units_btn": "🌿 Conservación",
    
    # Other
    "no_results": "No se encontraron resultados",
    "remove": "Eliminar",
    "aafc_section_title": "Capas AAFC (Canadá)",

    # =====================================================================
    # Navbar de análisis / contenido principal (index.py)
    # =====================================================================
    "nav_hide": "☰ Ocultar",
    "nav_show": "☰ Mostrar",
    "sidebar_narrow": "Estrecha",
    "sidebar_normal": "Normal",
    "sidebar_wide": "Ancha",
    "geometry_analysis_label": "🔷 Análisis de Geometría",
    "territory_analysis_label": "🗺️ Análisis de Territorio",
    "back_to_portal": "← Volver al Portal",
    "clear_btn": "🔄 Limpiar",
    "clear_btn_title": "Limpiar todos los datos de análisis y empezar de nuevo",
    "active_analysis_area": "Área de análisis activa",
    "no_areas_yet": "Aún no hay áreas — seleccione un territorio o dibuje una",
    "run_all_analysis": "▶ Ejecutar todos los análisis",
    "bundling": "Empaquetando…",
    "download_all": "⬇️ Descargar todo",
    "results_label": "📊 Resultados",
    "full_results": "⛶ Resultados a pantalla completa",
    "exit_full_results": "⛶ Salir de pantalla completa",
    "toggle_full_results_title": "Alternar resultados a pantalla completa",

    # =====================================================================
    # Página del portal (portal.py)
    # =====================================================================
    "portal_ds_mapbiomas": "MapBiomas: cobertura del suelo de Brasil (1985-2024, resolución de 30m)",
    "portal_ds_hansen": "Hansen/GFC: detección global de cambios forestales",
    "portal_ds_aafc": "AAFC: clasificación agrícola y forestal de Canadá",
    "portal_ds_gee": "Google Earth Engine: análisis geoespacial en la nube",
    "portal_ds_custom": "Geometrías personalizadas: dibuje o cargue sus propios elementos",
    "portal_choose_title": "🚀 Elija Su Ruta de Análisis",
    "portal_choose_desc": "Seleccione el tipo de análisis que mejor se adapte a su flujo de trabajo. Ambas rutas dan acceso a las mismas herramientas y conjuntos de datos.",
    "portal_geometry_sub": "Dibuje y analice áreas personalizadas",
    "portal_geometry_i1": "Dibuje polígonos en el mapa",
    "portal_geometry_i2": "Cargue GeoJSON/Shapefiles/KML",
    "portal_geometry_i3": "Cree zonas de amortiguamiento (buffer)",
    "portal_geometry_i4": "Analice cambios de cobertura del suelo",
    "portal_geometry_btn": "→ Iniciar Análisis de Geometría",
    "portal_territory_sub": "Monitoree tierras indígenas",
    "portal_territory_i1": "Seleccione entre 700+ territorios",
    "portal_territory_i2": "Busque por nombre",
    "portal_territory_i3": "Siga los cambios forestales (1985-2024)",
    "portal_territory_i4": "Compare múltiples años",
    "portal_territory_btn": "→ Iniciar Análisis de Territorio",
    "portal_batch_sub": "Procese varios territorios a la vez",
    "portal_batch_i1": "Seleccione cualquier número de territorios",
    "portal_batch_i2": "Ejecute MapBiomas, Hansen GLAD y GFC",
    "portal_batch_i3": "Territorio + buffer automáticamente",
    "portal_batch_i4": "Descargue un ZIP con todos los datos",
    "portal_batch_btn": "→ Iniciar Procesamiento por Lotes",
    "portal_resources": "📚 Recursos",
    "portal_link_methods": "Métodos e Investigación",
    "portal_support": "🎓 Soporte",
    "portal_link_tutorial": "Tutorial y Guía",
    "portal_link_faq": "Preguntas Frecuentes",
    "portal_link_contact": "Contacto y Comentarios",
    "portal_link_team": "Equipo y Colaboradores",
    "portal_link_cite": "Cómo Citar",

    # =====================================================================
    # Cita y agradecimientos (components/citation.py)
    # =====================================================================
    "citation_title": "Cómo Citar y Agradecimientos",
    "citation_mission": "Yvynation ofrece datos geoespaciales, gráficos y figuras abiertos para apoyar a comunidades y gestores de Tierras Indígenas y Unidades de Conservación, y para brindar a investigadores y periodistas cifras y tablas confiables para su propio trabajo.",
    "citation_acknowledgment_title": "Agradecimientos",
    "citation_acknowledgment_text": "El procesamiento geoespacial de esta plataforma se ejecuta en Google Earth Engine, bajo el proyecto ProtectedLandsYvynation-EE, registrado para uso de investigación no comercial. La infraestructura en la nube cuenta con el apoyo de Google Cloud Research Credits.",
    "citation_howto_title": "Cita sugerida",
    "citation_platform_text": "Biondo, L. M. (2026). Yvynation: plataforma de monitoreo geoespacial de Tierras Indígenas y Unidades de Conservación [Software]. Institute for Sustainability, Growth and Health (IGS), UBC Okanagan. Datos procesados mediante Google Earth Engine (proyecto ProtectedLandsYvynation-EE).",
    "citation_datasets_title": "Cite también las fuentes de datos utilizadas:",
    "citation_ds_mapbiomas": "Proyecto MapBiomas — Colección 10 de la Serie de Mapas de Cobertura y Uso del Suelo de Brasil, mapbiomas.org",
    "citation_ds_hansen": "Hansen, M.C. et al. (2013). High-Resolution Global Maps of 21st-Century Forest Cover Change. Science. (Global Forest Change / GLAD, UMD)",
    "citation_ds_aafc": "Agriculture and Agri-Food Canada (AAFC) — Annual Crop Inventory",
    "citation_ds_gee": "Gorelick, N. et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment.",
    "citation_hide": "Ocultar",

    # =====================================================================
    # Página de procesamiento por lotes (batch_processing.py)
    # =====================================================================
    "batch_title": "🔶 Procesamiento por Lotes",
    "batch_nav_subtitle": "Ejecute el análisis completo en varios territorios — descargue un único ZIP",
    "batch_select_territories": "🗺️ Seleccionar Territorios",
    "batch_selected_suffix": " seleccionado(s)",
    "batch_indigenous_btn": "🪶 Indígenas",
    "batch_conservation_btn": "🌿 Unidades de Conservación",
    "batch_search_placeholder": "🔍 Buscar territorios…",
    "batch_select_all_filtered": "Seleccionar todos los filtrados",
    "batch_shown_suffix": " mostrado(s)",
    "batch_paste_instruction": "📋 Pegue una lista de nombres (uno por línea) o cargue un .txt/.csv para seleccionarlos automáticamente:",
    "batch_select_from_list": "✓ Seleccionar de la lista",
    "batch_upload_list": "📁 Cargar lista",
    "batch_clear": "Limpiar",
    "batch_not_found_prefix": "⚠ No encontrados: ",
    "batch_configuration": "⚙️ Configuración",
    "batch_year1_label": "Año único (inicial)",
    "batch_year2_label": "Año final de la comparación",
    "batch_hansen_year_label": "Año Hansen GLAD",
    "batch_analysis_types": "Tipos de análisis",
    "batch_chk_mapbiomas": "🌿 MapBiomas año único",
    "batch_chk_comparison": "📊 Comparación entre años",
    "batch_chk_treemap": "🟦 Treemaps de transición de clases (por clase + Otras)",
    "batch_treemap_hint": "Agrega un treemap facetado (uno por clase, con las clases menores agrupadas en “Otras”) donde se produzcan transiciones — en la comparación de años y en cada paso multiventana.",
    "batch_chk_glad": "🌲 Cobertura forestal Hansen GLAD",
    "batch_chk_gfc": "🪓 Hansen GFC (pérdida / ganancia)",
    "batch_chk_pdf_maps": "🗺️ Mapas PNG y Gráficos (satélite + MapBiomas año1/año2)",
    "batch_aux_rasters_label": "Rásteres MapBiomas extra (año 2)",
    "batch_aux_deforestation": "🌳 Deforestación y vegetación secundaria",
    "batch_aux_fire_scar": "🔥 Área quemada anual (tamaño de la cicatriz)",
    "batch_aux_fire_frequency": "📊 Frecuencia de fuego (período completo 1985–2024)",
    "batch_aux_fire_year_last": "📅 Año del último fuego",
    "batch_aux_mining": "⛏️ Sustancias de minería",
    "batch_aux_agriculture": "🌾 Agricultura — número de ciclos",
    "batch_chk_multi_window": "🌀 MapBiomas en múltiples ventanas de tiempo (Sankey + Sunburst + Treemaps)",
    "batch_mw_mode": "Modo:",
    "batch_mw_step": "Paso (años):",
    "batch_mw_forced_note": "1985 → 2024 forzado como último año",
    "batch_mw_custom_label": "Años personalizados (3 o 4, separados por comas, 1985–2024)",
    "batch_mw_active_years": "Años activos: ",
    "batch_chk_timeline": "📈 Línea de tiempo de deforestación (Hansen + MapBiomas + Fuego) con contexto político",
    "batch_buffer_zone": "Zona de amortiguamiento",
    "batch_include_buffer": "Incluir análisis de buffer",
    "batch_km_ring": "km de anillo externo",
    "batch_progress": "📊 Progreso",
    "batch_territory_label": "Territorio:",
    "batch_step_label": "Paso:",
    "batch_done_label": "Completado:",
    "batch_complete_label": "— completado —",
    "batch_errors_suffix": " error(es))",
    "batch_processing_log": "Registro de procesamiento",
    "batch_about_title": "📖 Acerca del Procesamiento por Lotes",
    "batch_about_text": "Ejecute el pipeline completo de análisis de Yvynation (cobertura del suelo MapBiomas, cambio entre años, cobertura forestal Hansen GLAD y pérdida/ganancia Hansen GFC) en muchos territorios en una sola ejecución desatendida. Admite territorios indígenas de FUNAI (657) y unidades de conservación del CNUC (3.247). Cada territorio — y su buffer externo opcional — se procesa mediante Google Earth Engine y se empaqueta en un único archivo ZIP con tablas CSV, matrices de transición y figuras (HTML + PNG) por territorio.",
    "batch_time_note": "Espere de 2 a 10 minutos por territorio, según los análisis habilitados. La pestaña puede quedar abierta en segundo plano.",
    "batch_howto": "Cómo usar",
    "batch_howto_1_title": "Seleccione los territorios",
    "batch_howto_1_body": "Elija el tipo de fuente (Indígenas o Unidades de Conservación), use el buscador para filtrar y marque los territorios que desea incluir. 'Seleccionar todos los filtrados' agrega cada coincidencia de la búsqueda actual; 'Limpiar todo' reinicia. Cambiar el tipo borra la selección actual.",
    "batch_howto_2_title": "Elija los años MapBiomas",
    "batch_howto_2_body": "Defina el año inicial (instantánea única) y el año final (para la comparación entre años). Rango: 1985–2024.",
    "batch_howto_3_title": "Elija el año Hansen GLAD",
    "batch_howto_3_body": "Año de referencia (2000/2005/2010/2015/2020) usado para la instantánea de cobertura forestal Hansen GLAD.",
    "batch_howto_4_title": "Elija los tipos de análisis",
    "batch_howto_4_body": "Habilite cualquier combinación de MapBiomas año único, comparación entre años, Hansen GLAD y pérdida/ganancia Hansen GFC.",
    "batch_howto_5_title": "Zona de amortiguamiento opcional",
    "batch_howto_5_body": "Actívela para analizar también un anillo externo (por defecto 10 km) alrededor de cada territorio. Las salidas del buffer se escriben en buffer/{territory}_Buffer_{km}km/ dentro del ZIP.",
    "batch_howto_6_title": "Inicie el lote",
    "batch_howto_6_body": "Haga clic en 'Iniciar Procesamiento por Lotes'. El panel de configuración se reemplaza por la vista de progreso en vivo; puede detener después del territorio actual en cualquier momento.",
    "batch_howto_7_title": "Descargue el ZIP",
    "batch_howto_7_body": "Cuando termine la ejecución, haga clic en 'Descargar ZIP' para obtener todas las tablas, transiciones y figuras de cada territorio en un único archivo.",
    "batch_start_btn": "🚀 Iniciar Procesamiento por Lotes",
    "territories_word": "territorios",
    "batch_processing_ellipsis": "Procesando…",
    "batch_stop_btn": "⏹ Detener tras el actual",
    "batch_download_zip": "⬇️ Descargar ZIP",
    "batch_new_batch": "🔄 Nuevo Lote",
    "batch_territories_selected_suffix": " territorios seleccionados",
    "batch_no_territories": "Ningún territorio seleccionado",
}
