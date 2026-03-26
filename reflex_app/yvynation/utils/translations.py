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
