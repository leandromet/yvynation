"""
Translation and internationalization support for Reflex app.
Replaces Streamlit translation functions with dictionary-based approach.
"""

from typing import Dict, Optional, Any

# Translation dictionaries
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Page
        "page_title": "Yvynation - Indigenous Land Monitoring",
        "main_page_title": "🏞️ Yvynation - Indigenous Land Monitoring Platform",
        
        # Navigation
        "map_tab": "Map",
        "analysis_tab": "Analysis",
        "tutorial_tab": "Tutorial",
        "about_tab": "About",
        
        # Sidebar
        "sidebar_title": "Layers & Controls",
        "mapbiomas_label": "MapBiomas",
        "mapbiomas_select_year": "Select MapBiomas Year",
        "mapbiomas_years": "MapBiomas Years",
        "mapbiomas_layers_label": "MapBiomas Layers",
        "mapbiomas_layers_hint": "Number of active MapBiomas layers",
        "no_mapbiomas_selected": "No MapBiomas years selected",
        "no_mapbiomas_added": "Add MapBiomas layers in sidebar",
        
        "hansen_label": "Hansen GFC",
        "hansen_select_year": "Select Hansen Year",
        "hansen_years": "Hansen Years",
        "hansen_layers_label": "Hansen Layers",
        "hansen_layers_hint": "Number of active Hansen layers",
        "hansen_gfc_label": "Global Forest Change (GFC)",
        "hansen_gfc_layers_label": "GFC Layers",
        "no_hansen_selected": "No Hansen years selected",
        "no_hansen_added": "Add Hansen layers in sidebar",
        "no_hansen_gfc_added": "No GFC layers enabled",
        
        "tree_cover_2000": "Tree Cover 2000",
        "tree_loss_period": "Tree Loss (2000-2023)",
        "tree_gain_period": "Tree Gain (2000-2012)",
        
        # Base layer
        "base_layer": "Base Layer",
        "base_layer_hint": "Current base map",
        
        # Active layers
        "active_layers": "Active Layers",
        
        # Territory selection
        "select_territory": "Select Territory",
        "territory_by_country": "Filter by Country",
        "territory_by_state": "Filter by State",
        "selected_territory": "Selected Territory",
        "no_territory_selected": "No territory selected",
        
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
        
        # Buttons
        "confirm": "Confirm",
        "cancel": "Cancel",
        "close": "Close",
        "select": "Select",
        
        # Messages
        "loading": "Loading...",
        "analyzing": "Analyzing...",
        "ee_init_error": "Failed to initialize Earth Engine: {error}",
        "error": "Error",
        "success": "Success",
        
        # Analysis results
        "class": "Class",
        "area_hectares": "Area (ha)",
        "area_km2": "Area (km²)",
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
        
        # Settings
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
    },
    "pt": {
        # Page
        "page_title": "Yvynation - Monitoramento Territorial Indígena",
        "main_page_title": "🏞️ Yvynation - Plataforma de Monitoramento Territorial Indígena",
        
        # Navigation
        "map_tab": "Mapa",
        "analysis_tab": "Análise",
        "tutorial_tab": "Tutorial",
        "about_tab": "Sobre",
        
        # Sidebar
        "sidebar_title": "Camadas e Controles",
        "mapbiomas_label": "MapBiomas",
        "mapbiomas_select_year": "Selecionar Ano MapBiomas",
        "mapbiomas_years": "Anos MapBiomas",
        "mapbiomas_layers_label": "Camadas MapBiomas",
        "mapbiomas_layers_hint": "Número de camadas MapBiomas ativas",
        "no_mapbiomas_selected": "Nenhum ano MapBiomas selecionado",
        "no_mapbiomas_added": "Adicione camadas MapBiomas na barra lateral",
        
        "hansen_label": "Hansen GFC",
        "hansen_select_year": "Selecionar Ano Hansen",
        "hansen_years": "Anos Hansen",
        "hansen_layers_label": "Camadas Hansen",
        "hansen_layers_hint": "Número de camadas Hansen ativas",
        "hansen_gfc_label": "Mudança Florestal Global (GFC)",
        "hansen_gfc_layers_label": "Camadas GFC",
        "no_hansen_selected": "Nenhum ano Hansen selecionado",
        "no_hansen_added": "Adicione camadas Hansen na barra lateral",
        "no_hansen_gfc_added": "Nenhuma camada GFC habilitada",
        
        "tree_cover_2000": "Cobertura Arbórea 2000",
        "tree_loss_period": "Perda Florestal (2000-2023)",
        "tree_gain_period": "Ganho Florestal (2000-2012)",
        
        # Base layer
        "base_layer": "Camada Base",
        "base_layer_hint": "Mapa base atual",
        
        # Active layers
        "active_layers": "Camadas Ativas",
        
        # Territory selection
        "select_territory": "Selecionar Território",
        "territory_by_country": "Filtrar por País",
        "territory_by_state": "Filtrar por Estado",
        "selected_territory": "Território Selecionado",
        "no_territory_selected": "Nenhum território selecionado",
        
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
        
        # Buttons
        "confirm": "Confirmar",
        "cancel": "Cancelar",
        "close": "Fechar",
        "select": "Selecionar",
        
        # Messages
        "loading": "Carregando...",
        "analyzing": "Analisando...",
        "ee_init_error": "Falha ao inicializar Earth Engine: {error}",
        "error": "Erro",
        "success": "Sucesso",
        
        # Analysis results
        "class": "Classe",
        "area_hectares": "Área (ha)",
        "area_km2": "Área (km²)",
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
        "export_complete": "Exportação concluída",
        
        # MapBiomas specific
        "mapbiomas_no_data": "Nenhum dado disponível para a área selecionada",
        "mapbiomas_process_error": "Erro ao processar classe {class_id}: {error}",
        "mapbiomas_analysis_title": "Análise de Cobertura Terrestre MapBiomas",
        "mapbiomas_year_range": "Intervalo de anos: {start} - {end}",
        
        # Hansen specific
        "hansen_tree_cover": "Cobertura Arbórea",
        "hansen_tree_loss": "Perda Florestal",
        "hansen_tree_gain": "Ganho Florestal",
        "hansen_no_data": "Nenhum dado Hansen para a área selecionada",
        
        # Settings
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
    },
    "es": {
        # Page
        "page_title": "Yvynation - Monitoreo de Territorios Indígenas",
        "main_page_title": "🏞️ Yvynation - Plataforma de Monitoreo de Territorios Indígenas",
        
        # Navigation
        "map_tab": "Mapa",
        "analysis_tab": "Análisis",
        "tutorial_tab": "Tutorial",
        "about_tab": "Acerca de",
        
        # Sidebar
        "sidebar_title": "Capas y Controles",
        "mapbiomas_label": "MapBiomas",
        "mapbiomas_select_year": "Seleccionar Año MapBiomas",
        "mapbiomas_years": "Años MapBiomas",
        "mapbiomas_layers_label": "Capas MapBiomas",
        "mapbiomas_layers_hint": "Número de capas MapBiomas activas",
        "no_mapbiomas_selected": "Ningún año MapBiomas seleccionado",
        "no_mapbiomas_added": "Agregue capas MapBiomas en la barra lateral",
        
        "hansen_label": "Hansen GFC",
        "hansen_select_year": "Seleccionar Año Hansen",
        "hansen_years": "Años Hansen",
        "hansen_layers_label": "Capas Hansen",
        "hansen_layers_hint": "Número de capas Hansen activas",
        "hansen_gfc_label": "Cambio Forestal Global (GFC)",
        "hansen_gfc_layers_label": "Capas GFC",
        "no_hansen_selected": "Ningún año Hansen seleccionado",
        "no_hansen_added": "Agregue capas Hansen en la barra lateral",
        "no_hansen_gfc_added": "Ninguna capa GFC habilitada",
        
        "tree_cover_2000": "Cobertura Forestal 2000",
        "tree_loss_period": "Pérdida Forestal (2000-2023)",
        "tree_gain_period": "Ganancia Forestal (2000-2012)",
        
        # Base layer
        "base_layer": "Capa Base",
        "base_layer_hint": "Mapa base actual",
        
        # Active layers
        "active_layers": "Capas Activas",
        
        # Territory selection
        "select_territory": "Seleccionar Territorio",
        "territory_by_country": "Filtrar por País",
        "territory_by_state": "Filtrar por Departamento",
        "selected_territory": "Territorio Seleccionado",
        "no_territory_selected": "Ningún territorio seleccionado",
        
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
        
        # Buttons
        "confirm": "Confirmar",
        "cancel": "Cancelar",
        "close": "Cerrar",
        "select": "Seleccionar",
        
        # Messages
        "loading": "Cargando...",
        "analyzing": "Analizando...",
        "ee_init_error": "Error al inicializar Earth Engine: {error}",
        "error": "Error",
        "success": "Éxito",
        
        # Analysis results
        "class": "Clase",
        "area_hectares": "Área (ha)",
        "area_km2": "Área (km²)",
        "percentage": "Porcentaje (%)",
        "year": "Año",
        "change": "Cambio",
        "from_class": "De Clase",
        "to_class": "Para Clase",
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
        
        # Settings
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
    }
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
    result = translations.get(key, key)
    
    # Support string formatting
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
        "pt": "Português",
        "es": "Español"
    }
