"""
Translation dictionaries for Yvynation app.
Supports English and Portuguese (Brazil).
"""

import streamlit as st

TRANSLATIONS = {
    "en": {
        # Header
        "app_title": "🌎🌍🌏🏞️ Yvynation 🛰️🗺️🌳🌲",
        "app_subtitle": "Indigenous Land Monitoring Platform",
        "author": "Leandro M. Biondo - PhD Candidate - IGS/UBCO",
        
        # Sidebar sections
        "select_region": "🌎 Select Region",
        "current_region": "Current region:",
        "language": "🌐 Language",
        
        # Countries
        "brazil": "🇧🇷 Brazil",
        "canada": "🇨🇦 Canada",
        
        # Layers
        "mapbiomas_layer": "🌱 MapBiomas Land Cover",
        "hansen_layer": "🌍 Hansen/GLAD Forest Change",
        "hansen_gfc_layer": "🌲 Hansen Global Forest Change",
        "aafc_layer": "🚜 AAFC Crop Inventory",
        "year": "Year",
        "add_layer": "➕ Add Layer",
        "remove_layer": "➖ Remove Layer",
        
        # Map
        "interactive_map": "🗺️ Interactive Map",
        "draw_instruction": "🎨 Draw polygons on the map to analyze land cover. Use the layer control (⌗ top-right) to toggle layers.",
        "active_layers": "Active Layers",
        "polygon_analysis": "📊 Polygon Analysis & Statistics",
        "select_polygon": "🎨 Select Polygon to Analyze",
        "choose_polygon": "Choose a polygon to analyze:",
        "polygon_selected": "✓ Selected Polygon",
        "buffer_comparison": "📊 Compare Polygon vs Buffer",
        "buffer_distance": "Buffer Distance",
        "create_buffer": "🔵 Create Buffer",
        
        # Analysis tabs
        "mapbiomas_analysis": "📍 MapBiomas Analysis",
        "hansen_analysis": "🌍 Hansen/GLAD Analysis",
        "hansen_gfc_analysis": "🌲 Hansen GFC Analysis",
        "aafc_analysis": "🚜 AAFC Analysis",
        "comparison": "📈 Comparison",
        "about": "ℹ️ About",
        "analyzing": "Analyzing",
        "analyze_button": "🔍 Analyze",
        "download_csv": "📥 Download CSV",
        "total_area": "Total Area",
        "classes_detected": "Classes Detected",
        "largest_class": "Largest Class",
        "analysis_complete": "Analysis complete",
        
        # AAFC specific
        "aafc_title": "AAFC Annual Crop Inventory Analysis (Canada)",
        "aafc_subtitle": "Analyze crop and land cover classifications from Canada's Agricultural and Agri-Food dataset",
        "aafc_only_canada": "🍁 AAFC data is only available for Canada. Select Canada from the country selector to analyze crop inventory.",
        "no_aafc_data": "No AAFC data found for",
        "aafc_year_complete": "✓ {}: Analysis complete",
        
        # Forest data labels
        "tree_cover": "🌳 Tree Cover 2000",
        "tree_loss": "🔥 Tree Loss",
        "tree_gain": "🌲 Tree Gain",
        "tree_cover_desc": "Tree canopy cover in year 2000 (0-100%)",
        "tree_loss_desc": "Forest loss by year 2001-2024",
        "tree_gain_desc": "Forest regrowth 2000-2012",
        "no_tree_data": "No tree cover data available",
        "no_tree_loss": "No tree loss detected in this area",
        "no_tree_gain": "No tree gain detected in this area during 2000-2012",
        
        # Comparisons
        "multi_year_comparison": "Multi-Year Comparison",
        "mapbiomas_comparison": "📊 MapBiomas Change Analysis",
        "year_baseline": "Year 1 (baseline)",
        "year_comparison": "Year 2 (comparison)",
        "compare_years": "🔄 Compare Years",
        
        # Info
        "mapbiomas_info": "MapBiomas: Brazilian land cover mapping",
        "hansen_info": "Hansen/GLAD: Global forest changes",
        "gfc_info": "Hansen Global Forest Change: Comprehensive forest monitoring",
        "aafc_info": "AAFC: Canada's agricultural land cover dataset",
        
        # References
        "layer_reference": "📚 Layer Reference Guide - legends",
        "indigenous_lands": "📍 Indigenous Lands & Territories",
        "mapbiomas_classes": "🌱 MapBiomas Land Cover Classes",
        "hansen_classes": "🌍 Hansen/GLAD Global Land Cover Classes",
        "gfc_classes": "🌲 Hansen Global Forest Change (UMD 2024)",
        "aafc_classes": "🚜 AAFC Annual Crop Inventory (Canada)",
        "basemaps": "Basemaps",
        "controls": "Controls",
        "data_layers_overview": "Data Layers Overview",
        
        # Getting Started / Tutorial
        "getting_started": "🚀 Getting Started",
        "tutorial_title": "How to Use Yvynation",
        "step1_select_region": "Step 1: Select Your Region",
        "step1_desc": "Choose between Brazil or Canada at the top of the sidebar to analyze specific regions.",
        "step2_add_layers": "Step 2: Add Data Layers",
        "step2_desc": "select MapBiomas, Hansen, or AAFC layers from the sidebar to visualize on the map.",
        "step3_draw_polygon": "Step 3: Draw Polygon",
        "step3_desc": "Use the drawing tools (top-left of map) to draw a polygon on the area you want to analyze.",
        "step4_analyze": "Step 4: Analyze Results",
        "step4_desc": "View detailed statistics for your selected area in the analysis tabs below the map.",
        
        # Map Tools
        "map_tools": "🛠️ Map Tools",
        "zoom_in": "Zoom In",
        "zoom_out": "Zoom Out",
        "reset_view": "Reset View",
        "draw_polygon": "📐 Draw Polygon",
        "draw_rectangle": "📦 Draw Rectangle",
        "edit_shape": "✏️ Edit Shape",
        "delete_shape": "🗑️ Delete Shape",
        "measure_distance": "📏 Measure Distance",
        
        # Territory Analysis
        "territory_analysis": "📍 Territory Analysis",
        "select_territory": "Select Indigenous Territory",
        "territory_name": "Territory Name",
        "analyze_territory": "🔍 Analyze Territory",
        "no_territory_selected": "No territory selected",
        "territory_info": "Select a territory from the list and click 'Analyze Territory' to view land cover statistics.",
        
        # View Options
        "view_options": "👁️ View Options",
        "layer_opacity": "Layer Opacity",
        "consolidated_classes": "Use Consolidated Classes (11 categories)",
        "show_grid": "Show Grid",
        "show_scale": "Show Scale",
        "auto_center_territory": "Auto-center on Territory",
        
        # Export
        "export": "📤 Export Results",
        "export_map": "Export Map as PNG",
        "export_data": "Export Data as CSV",
        "export_pdf": "Export Report as PDF",
        "exporting": "Exporting...",
        "export_complete": "Export complete!",
        
        # About
        "about": "ℹ️ About Yvynation",
        "platform_description": "Yvynation is an interactive platform for monitoring changes in indigenous territories and regions.",
        "data_sources": "Data Sources",
        "technologies": "Technologies Used",
        "contact": "Contact & Support",
        
        # Errors & Warnings
        "error_map": "Error displaying map",
        "error_analysis": "Error analyzing data",
        "error_export": "Error exporting data",
        "warning_no_data": "No data available for this area",
        "loading_data": "Loading data...",
        "calculating": "Calculating...",
        
        # Map Controls
        "map_controls": "🎛️ Map Controls",
        "layer_control": "Layer Control",
        "layer_control_hint": "Look for the ⌗ icon in the top-right corner to toggle layers on/off",
        "basemaps_section": "Basemaps",
        "basemaps_info": "6 basemap options available (OpenStreetMap, Google Maps, Google Satellite, ArcGIS Street, ArcGIS Satellite, ArcGIS Terrain)",
        "basemap_default": "Google Maps is selected by default",
        "overlay_tip": "Tip: Overlay multiple basemaps and data layers to compare different views",
        
        # Territory Analysis
        "territory_analysis_title": "🏛️ Indigenous Territories Analysis",
        "analyze_territory_intro": "Analyze land cover in indigenous territories:",
        "territories_not_loaded": "❌ Territories data not loaded.",
        "territory_names_error": "❌ Could not load territory names",
        "select_a_territory": "Select a territory",
        "data_source_label": "Data Source",
        "year_1": "Year 1",
        "year_2": "Year 2",
        "compare_years_label": "Compare Years",
        "btn_analyze": "📊 Analyze",
        "btn_zoom_territory": "➕ Zoom to Territory",
        "territory_added": "✅ Territory '{territory}' added to map",
        "territory_add_failed": "❌ Failed to add territory layer: {error}",
        "analyzing_territory": "Analyzing {territory}...",
        "territory_geometry_error": "❌ Could not get territory geometry",
        "analysis_complete": "✅ Analysis complete for {territory}",
        "analysis_failed": "❌ Analysis failed: {error}",
        "hansen_analysis_failed": "❌ Hansen analysis failed: {error}",
        "territory_error": "❌ Territory analysis error: {error}",
        
        # Buffer Zone
        "buffer_zone_title": "⭕ Territory External Buffer Zone Analysis",
        "buffer_zone_desc": "Create External Buffer Zone",
        "buffer_zone_hint": "Create a ring-shaped buffer around the territory for analysis",
        "compare_buffer": "📊 Compare Territory vs Buffer",
        "compare_buffer_help": "Analyze both territory and buffer zone side-by-side",
        "buffer_distance_label": "Buffer Distance",
        "btn_create_buffer": "🔵 Create Buffer",
        "km_format": "{distance} km",
        "buffer_created": "✅ Created {distance}km buffer - Compare mode enabled!",
        "buffer_created_compare": "✅ Created {distance}km buffer around '{territory}'",
        "buffer_compare_info": "📊 Click 'Analyze' to compare territory vs buffer zone",
        "buffer_analyze_info": "🔽 Use 'Analyze Buffer' button below to analyze just the buffer zone",
        "buffer_create_failed": "❌ Failed to create buffer: {error}",
        "buffer_zone_analysis": "🔵 Buffer Zone Analysis",
        "buffer_analysis_hint": "Analyze the {distance}km buffer zone around {territory}",
        "btn_analyze_buffer": "🔍 Analyze Buffer Zone",
        "btn_zoom_buffer": "🔭 Zoom to Buffer",
        "buffer_added": "✅ Buffer '{distance}km' added to map - scroll down to see map",
        "buffer_added_error": "❌ Failed to add buffer layer: {error}",
        "buffer_analyzing": "Analyzing buffer zone...",
        "buffer_analysis_complete": "✅ Buffer zone analysis complete!",
        "buffer_analysis_info": "📊 Scroll down to see results",
        "buffer_analysis_failed": "❌ Failed to analyze buffer: {error}",
        
        # View Options
        "view_options": "🎨 View Options",
        "show_consolidated": "Show Consolidated Classes",
        "consolidated_help": "Group Hansen 256 classes into 12 consolidated categories for cleaner visualization",
        "consolidated_view": "📊 Consolidated view: 256 classes → 12 categories",
        "detailed_view": "📊 Detailed view: All 256 original classes",
        
        # Add Map Layers
        "add_layer_to_analyze": "🗺️ Add Map Layers {layers}",
        
        # About Section
        "about_title": "ℹ️ About",
        "about_overview": "Project Overview",
        "about_desc": "This land use and land cover analysis tool is part of a research project studying environmental changes in Brazilian Indigenous Territories using Google Earth Engine and MapBiomas data. This data is compared with policy changes and deforestation trends to understand the impacts on these critical lands.",
        "about_author": "Leandro Meneguelli Biondo",
        "about_role": "PhD Candidate in Sustainability",
        "about_university": "IGS/UBCO",
        "about_supervisor": "Supervisor: Dr. Jon Corbett",
        "about_app_name": "Yvynation",
        "about_app_note": "is a name for this app, as it is not the full project content.",
        "yvynation_meaning": "\"Yvy\" (Tupi–Guarani) means land, earth, or territory — emphasizing the ground we walk on and our sacred connection to nature. It often relates to the concept of \"Yvy marãe'ỹ\" (Land without evil).",
        "nation_meaning": "\"Nation\" refers to a self-governing community or people with shared culture, history, language, and land. It signifies self-determination and governance.",
        "data_sources_title": "Data Sources",
        "mapbiomas_title": "MapBiomas Collection 9",
        "mapbiomas_resolution": "Resolution: 30 m",
        "mapbiomas_period": "Period: 1985–2023 (annual)",
        "mapbiomas_classes": "Classes: 62 land cover categories",
        "mapbiomas_license": "License: Creative Commons Attribution 4.0",
        "territories_title": "Indigenous Territories",
        "territories_desc": "700+ Brazilian territories with vector boundaries and attributes - MapBiomas Territories Project",
        "features_title": "Features",
        "feature_mapping": "Interactive mapping with real-time data",
        "feature_calculation": "Area calculations and change detection",
        "feature_filtering": "Territory filtering by state or name",
        "feature_visualization": "Statistical visualizations",
        "feature_export": "Data export capabilities",
        "tech_title": "Technologies",
        "tech_python": "Python 3.8+",
        "tech_gee": "Google Earth Engine API",
        "tech_geemap": "geemap (interactive mapping)",
        "tech_streamlit": "Streamlit (web interface)",
        "tech_science": "pandas, matplotlib, seaborn (analysis & visualization)",
        
        # Main App Content - Page Title & Meta
        "page_title": "Yvynation - Earth Engine Analysis",
        
        # Analysis Section Headers
        "mapbiomas_header": "📍 MapBiomas Land Cover Analysis",
        "hansen_header": "🌍 Hansen/GLAD Forest Change Analysis",
        "hansen_gfc_header": "🌲 Hansen Global Forest Change Analysis",
        "aafc_header": "🚜 AAFC Annual Crop Inventory Analysis (Canada)",
        "comparison_header": "📈 Comparison Analysis",
        
        # Analysis Status Messages
        "analyzing_years": "Analyzing {count} year(s) of data...",
        "analyzing_aafc_years": "Analyzing {count} year(s) of AAFC data...",
        "year_analysis_complete": "✓ {year}: Analysis complete",
        "year_classes_found": "✓ {year}: {count} classes found",
        "year_analysis_failed": "Error analyzing {year}: {error}",
        "no_mapbiomas_layer": "Add a MapBiomas layer from the sidebar to analyze",
        "no_hansen_layer": "Add a Hansen layer from the sidebar to analyze",
        "no_aafc_layer": "Add an AAFC layer from the sidebar to analyze",
        "load_data_mapbiomas": "Load data and add a MapBiomas layer to begin analysis",
        "load_data_hansen": "Load data and add a Hansen layer to begin analysis",
        
        # Forest Analysis Headers
        "tree_cover_header": "Tree Canopy Cover in Year 2000",
        "tree_loss_header": "Forest Loss by Year (2001-2024)",
        "tree_gain_header": "Tree Cover Gain (2000-2012)",
        
        # Data Availability Messages
        "no_tree_data": "No tree cover data available",
        "no_tree_loss_data": "No tree loss data available",
        "no_tree_gain_data": "No tree gain data available",
        "no_loss_detected": "✅ No forest loss detected in this area!",
        "intact_forest_area": "Total area with intact forest: {area:,} ha",
        "no_gain_detected": "No tree gain detected in this area during 2000-2012",
        "add_gfc_layers": "👆 Add Hansen Global Forest Change layers from the sidebar to analyze tree cover dynamics",
        "aafc_canada_only": "🍁 AAFC data is only available for Canada. Select Canada from the country selector to analyze crop inventory.",
        
        # Empty States
        "empty_histogram": "Empty histogram for {year}",
        "no_stats_returned": "No stats returned for {year}",
        "no_data_area": "No data in selected area for this year",
        "no_aafc_data_year": "No AAFC data found for {year} in this area",
        
        # Results Display
        "consolidated_view": "Consolidated View (12 classes)",
        "detailed_view": "Detailed View (256 classes)",
        "loss_by_year": "Loss by Year:",
        
        # Error Messages
        "error_analyzing": "Error analyzing {area}: {error}",
        "error_analyzing_year": "Error analyzing {year}: {error}",
        "error_analyzing_gfc": "Error analyzing Hansen GFC for {area}: {error}",
        "error_analyzing_aafc": "Error analyzing AAFC for {area}: {error}",
        "analysis_partial": "{type} analysis partial: {error}",
        
        # Warnings
        "analysis_complete_partial": "✓ Analysis complete! Found data for: {sources}",
        "no_gfc_data": "No Hansen GFC data found in this area",
        "tree_cover_partial": "Tree cover analysis partial: {error}",
        "tree_loss_partial": "Tree loss analysis partial: {error}",
        "tree_gain_partial": "Tree gain analysis partial: {error}",
        
        # Getting Started / Tutorial Headers
        "getting_started_header": "How to Use This Platform",
        "getting_started_title": "🎯 Getting Started",
        "getting_started_intro": "This platform enables comprehensive land cover analysis for Brazil and global forest monitoring. You can analyze custom areas, indigenous territories, and external buffer zones.",
        
        # Tutorial Step Titles
        "step_custom_polygon": "1️⃣ **Analyze a Custom Polygon**",
        "step_territory": "2️⃣ **Analyze an Indigenous Territory**",
        "step_comparison": "3️⃣ **Multi-Year Comparison**",
        "step_export": "4️⃣ **Export and Download Results**",
        "step_map_controls": "🗺️ **Map Controls & Navigation**",
        "step_data_understanding": "📊 **Understanding the Data & Results**",
        
        # Tutorial Content - Step 1
        "step1_draw_intro": "Draw and analyze any area on the map:",
        # Tutorial Content - Step 2
        "step2_territory_intro": "Pre-defined indigenous territory boundaries with historical analysis:",
        # Tutorial Content - Step 3
        "step3_comparison_intro": "Compare land cover changes between any two years:",
        # Tutorial Content - Step 4
        "step4_export_intro": "Save your analysis results for reports and further analysis:",
        # Tutorial Content - Step 5
        "step5_map_controls_intro": "Map Controls & Navigation",
        # Tutorial Content - Step 6
        "step6_data_understanding_intro": "Understanding Data & Results",
        
        # Map Components - Territory & Buffer
        "territory_layer": "Territory: {territory_name}",
        "buffer_layer": "Buffer: {buffer_name}",
        "buffer_geojson": "Buffer: {buffer_name}",
        "captured_polygons": "✓ Captured {count} polygon(s). Select one below to analyze.",
        "polygon_captured": "✓ Polygon captured. Scroll down to analyze.",
        "buffer_label": "Buffer {number}",
        "polygon_bounds": "Polygon {number} - {type} - Bounds: {bounds}",
        "selected_buffer": "✓ Selected: {buffer_name}",
        "selected_polygon": "✓ Selected Polygon {number} for analysis",
        "buffer_ring_help": "Create a ring-shaped buffer around this polygon for analysis",
        "compare_help": "Analyze both polygon and buffer zone side-by-side",
        "map_display_error": "Map display error: {error}",
        "polygon_only_error": "❌ Can only create buffers for polygon features",
        "buffer_creation_error": "❌ Failed to create buffer: {error}",
        "buffer_created_compare": "✅ Created {distance}km buffer - Compare mode enabled!",
        "analysis_compare_info": "📊 Analysis tabs will show both polygon and buffer results",
        "buffer_created": "✅ Created {distance}km buffer around {name}",
        "buffer_added_info": "📍 Buffer added to polygon list - refresh to select it",
        "territory_added_map": "Territory layer added: {name}",
        "buffer_added_map": "Buffer layer added: {name}",
        "analysis_layer_added": "✓ Analysis layer added to map: {name}",
        "comparison_layer_added": "✓ Comparison layer added to map: {name}",
        "year2_analysis_error": "⚠️ Could not add second year analysis: {error}",
        "analysis_error": "❌ Error adding analysis layer: {error}",
        "adding_territory_error": "[Error] Adding territory layer failed: {error}",
        "adding_buffer_error": "[Error] Adding buffer layer failed for {name}: {error}",
        
        # Analysis Messages - Additional
        "no_forest_loss": "✅ No forest loss detected in this area!",
        "forest_loss_intact": "Total area with intact forest: {area:,.0f} ha",
        "area_with_gain": "Area with Gain",
        "area_without_gain": "Area without Gain",
        "download_gain_data": "📥 Download Gain Data",
        "gfc_available_layers": "Available Layers:",
        "gfc_layer_tree_cover": "🌳 **Tree Cover 2000**: Baseline canopy cover percentage",
        "gfc_layer_tree_loss": "🔥 **Tree Loss Year**: Annual forest loss from 2001-2024",
        "gfc_layer_tree_gain": "🌲 **Tree Gain**: Forest regrowth from 2000-2012",
        "gfc_add_from_sidebar": "Add these layers from the sidebar under **🌲 Hansen Global Forest Change** section.",
        "aafc_analyzing_years": "Analyzing {count} year(s) of AAFC data...",
        "aafc_year_label": "Year {year}",
        "aafc_total_area": "Total Area",
        "aafc_classes_detected": "Classes Detected",
        "aafc_largest_class": "Largest Class",
        "aafc_download_csv": "📥 Download CSV ({year})",
        "aafc_analysis_complete": "✓ {year}: Analysis complete",
        "aafc_no_data_year": "No AAFC data found for {year} in this area",
        "aafc_analysis_error": "Error analyzing AAFC {year}: {error}",
        
        # Legend and Display
        "legend_areas_with_forest_loss": "Areas with forest loss detected",
        "legend_no_forest_loss": "Areas with no forest loss",
        "legend_areas_with_gain": "Areas with forest gain",
        "legend_no_forest_gain": "Areas with no forest gain",
        
        # Initialization & Loading
        "initializing_ee": "Initializing Earth Engine...",
        "loading_data": "Loading data...",
        "ee_init_error": "❌ Failed to initialize Earth Engine: {error}",
        "data_loaded": "✅ Data loaded successfully",
        "data_load_error": "❌ Error loading data: {error}",
        
        # Comparison Messages
        "no_comparison_data": "No comparison data available",
        "hansen_unavailable": "Hansen data not available for years {year1} and {year2}",
        "sankey_generation_error": "Could not generate Sankey diagram",
        "no_transition_data": "No transition data available",
        "geometry_not_available": "Geometry not available. Run analysis first.",
        "sankey_display_error": "Could not display Sankey diagram: {error}",
        
        # Buffer Comparison Messages
        "buffer_compare_on": "✓ Buffer Compare Mode: ON",
        "buffer_compare_off": "Buffer Compare Mode: OFF",
        "buffer_compare_active": "✓ Buffer: {buffer_name}",
        "buffer_compare_none": "⚠ No Buffer Created",
        
        # Download and Export
        "download_csv_label": "📥 Download CSV",
        "download_success": "✅ Download ready",
        "export_error": "❌ Error exporting data: {error}",
        
        # Layer Reference Guide
        "layer_reference_full": "📚 Layer Reference Guide - legends",
        "indigenous_territories_legend": "📍 Indigenous Lands & Territories",
        "indigenous_territories_label": "Indigenous Territories",
        "selected_territory_label": "Selected Territory",
        "drawn_polygon_label": "Drawn Polygon",
        "buffer_zone_label": "External Buffer Zone",
        "mapbiomas_legend": "🌱 MapBiomas Land Cover Classes",
        "hansen_legend": "🌍 Hansen/GLAD Global Land Cover Classes",
        "gfc_legend": "🌲 Hansen Global Forest Change (UMD 2024)",
        "gfc_legend_desc": "Tree cover change analysis from 2000-2024",
        "aafc_legend": "🚜 AAFC Annual Crop Inventory (Canada)",
        "aafc_legend_desc": "Agricultural land cover in Canada (2009-2024, 30m resolution)",
        "legend_controls": "Control Instructions",
        "legend_layer_control": "Layer Control: top-right corner",
        "legend_drawing_tools": "Drawing Tools: top-left corner",
        "legend_opacity": "Opacity: Adjust in sidebar",
        "legend_data_overview": "Data Layers Overview",
        "legend_data_brazilian": "🌱 MapBiomas: Brazilian land cover (1985-2023)",
        "legend_data_global": "🌍 Hansen: Global forest change (2000-2020)",
        "legend_data_agriculture": "🚜 AAFC: Canadian crop inventory (2009-2024)",
        "legend_data_territories": "📍 Indigenous Territories"


    },
    "pt-br": {
        # Header
        "app_title": "🌎🌍🌏🏞️ Yvynation 🛰️🗺️🌳🌲",
        "app_subtitle": "Plataforma de Monitoramento de Terras Indígenas",
        "author": "Leandro M. Biondo - Candidato de PhD - IGS/UBCO",
        
        # Sidebar sections
        "select_region": "🌎 Selecione Região",
        "current_region": "Região atual:",
        "language": "🌐 Idioma",
        
        # Countries
        "brazil": "🇧🇷 Brasil",
        "canada": "🇨🇦 Canadá",
        
        # Layers
        "mapbiomas_layer": "🌱 MapBiomas Cobertura do Solo",
        "hansen_layer": "🌍 Hansen/GLAD Mudanças Florestais",
        "hansen_gfc_layer": "🌲 Hansen Mudanças Florestais Globais",
        "aafc_layer": "🚜 Inventário de Cultivos AAFC",
        "year": "Ano",
        "add_layer": "➕ Adicionar Camada",
        "remove_layer": "➖ Remover Camada",
        
        # Map
        "interactive_map": "🗺️ Mapa Interativo",
        "draw_instruction": "🎨 Desenhe polígonos no mapa para analisar cobertura do solo. Use o controle de camadas (⌗ canto superior direito) para alternar camadas.",
        "active_layers": "Camadas Ativas",
        "polygon_analysis": "📊 Análise e Estatísticas de Polígono",
        "select_polygon": "🎨 Selecione Polígono para Analisar",
        "choose_polygon": "Escolha um polígono para analisar:",
        "polygon_selected": "✓ Polígono Selecionado",
        "buffer_comparison": "📊 Comparar Polígono vs Buffer",
        "buffer_distance": "Distância do Buffer",
        "create_buffer": "🔵 Criar Buffer",
        
        # Analysis tabs
        "mapbiomas_analysis": "📍 Análise MapBiomas",
        "hansen_analysis": "🌍 Análise Hansen/GLAD",
        "hansen_gfc_analysis": "🌲 Análise Hansen GFC",
        "aafc_analysis": "🚜 Análise AAFC",
        "comparison": "📈 Comparação",
        "about": "ℹ️ Sobre",
        "analyzing": "Analisando",
        "analyze_button": "🔍 Analisar",
        "download_csv": "📥 Baixar CSV",
        "total_area": "Área Total",
        "classes_detected": "Classes Detectadas",
        "largest_class": "Classe Maior",
        "analysis_complete": "Análise concluída",
        
        # AAFC specific
        "aafc_title": "Análise de Inventário Anual de Cultivos AAFC (Canadá)",
        "aafc_subtitle": "Analise classificações de cultivos e cobertura do solo do conjunto de dados Agrícola e Agroalimentar do Canadá",
        "aafc_only_canada": "🍁 Os dados AAFC estão disponíveis apenas para o Canadá. Selecione o Canadá no seletor de país para analisar o inventário de cultivos.",
        "no_aafc_data": "Nenhum dado AAFC encontrado para",
        "aafc_year_complete": "✓ {}: Análise concluída",
        
        # Forest data labels
        "tree_cover": "🌳 Cobertura Arbórea 2000",
        "tree_loss": "🔥 Perda Florestal",
        "tree_gain": "🌲 Ganho Florestal",
        "tree_cover_desc": "Cobertura de dossel de árvores no ano 2000 (0-100%)",
        "tree_loss_desc": "Perda florestal por ano 2001-2024",
        "tree_gain_desc": "Regrowth florestal 2000-2012",
        "no_tree_data": "Nenhum dado de cobertura arbórea disponível",
        "no_tree_loss": "Nenhuma perda florestal detectada nesta área",
        "no_tree_gain": "Nenhum ganho florestal detectado nesta área durante 2000-2012",
        
        # Comparisons
        "multi_year_comparison": "Comparação Multi-Ano",
        "mapbiomas_comparison": "📊 Análise de Mudança MapBiomas",
        "year_baseline": "Ano 1 (baseline)",
        "year_comparison": "Ano 2 (comparação)",
        "compare_years": "🔄 Comparar Anos",
        
        # Info
        "mapbiomas_info": "MapBiomas: Mapeamento de cobertura do solo brasileira",
        "hansen_info": "Hansen/GLAD: Mudanças florestais globais",
        "gfc_info": "Hansen Mudanças Florestais Globais: Monitoramento florestal abrangente",
        "aafc_info": "AAFC: Conjunto de dados de cobertura do solo agrícola do Canadá",
        
        # References
        "layer_reference": "📚 Guia de Referência de Camadas - legendas",
        "indigenous_lands": "📍 Terras e Territórios Indígenas",
        "mapbiomas_classes": "🌱 Classes de Cobertura do Solo MapBiomas",
        "hansen_classes": "🌍 Classes de Cobertura Global Hansen/GLAD",
        "gfc_classes": "🌲 Hansen Mudanças Florestais Globais (UMD 2024)",
        "aafc_classes": "🚜 Inventário Anual de Cultivos AAFC (Canadá)",
        "basemaps": "Mapas Base",
        "controls": "Controles",
        "data_layers_overview": "Visão Geral de Camadas de Dados",
        
        # Getting Started / Tutorial
        "getting_started": "🚀 Primeiros Passos",
        "tutorial_title": "Como Usar o Yvynation",
        "step1_select_region": "Passo 1: Selecione sua Região",
        "step1_desc": "Escolha entre Brasil ou Canadá no topo da barra lateral para analisar regiões específicas.",
        "step2_add_layers": "Passo 2: Adicione Camadas de Dados",
        "step2_desc": "Selecione camadas MapBiomas, Hansen ou AAFC na barra lateral para visualizar no mapa.",
        "step3_draw_polygon": "Passo 3: Desenhe um Polígono",
        "step3_desc": "Use as ferramentas de desenho (canto superior esquerdo do mapa) para desenhar um polígono na área que deseja analisar.",
        "step4_analyze": "Passo 4: Analise os Resultados",
        "step4_desc": "Visualize estatísticas detalhadas da sua área selecionada nas abas de análise abaixo do mapa.",
        
        # Map Tools
        "map_tools": "🛠️ Ferramentas do Mapa",
        "zoom_in": "Ampliar",
        "zoom_out": "Reduzir",
        "reset_view": "Redefinir Visualização",
        "draw_polygon": "📐 Desenhar Polígono",
        "draw_rectangle": "📦 Desenhar Retângulo",
        "edit_shape": "✏️ Editar Forma",
        "delete_shape": "🗑️ Deletar Forma",
        "measure_distance": "📏 Medir Distância",
        
        # Territory Analysis
        "territory_analysis": "📍 Análise de Territórios",
        "select_territory": "Selecione Território Indígena",
        "territory_name": "Nome do Território",
        "analyze_territory": "🔍 Analisar Território",
        "no_territory_selected": "Nenhum território selecionado",
        "territory_info": "Selecione um território da lista e clique em 'Analisar Território' para visualizar estatísticas de cobertura do solo.",
        
        # View Options
        "view_options": "👁️ Opções de Visualização",
        "layer_opacity": "Opacidade da Camada",
        "consolidated_classes": "Usar Classes Consolidadas (11 categorias)",
        "show_grid": "Mostrar Grade",
        "show_scale": "Mostrar Escala",
        "auto_center_territory": "Auto-centralizar no Território",
        
        # Export
        "export": "📤 Exportar Resultados",
        "export_map": "Exportar Mapa como PNG",
        "export_data": "Exportar Dados como CSV",
        "export_pdf": "Exportar Relatório como PDF",
        "exporting": "Exportando...",
        "export_complete": "Exportação concluída!",
        
        # About
        "about": "ℹ️ Sobre o Yvynation",
        "platform_description": "Yvynation é uma plataforma interativa para monitorar mudanças em territórios indígenas e regiões.",
        "data_sources": "Fontes de Dados",
        "technologies": "Tecnologias Utilizadas",
        "contact": "Contato & Suporte",
        
        # Errors & Warnings
        "error_map": "Erro ao exibir mapa",
        "error_analysis": "Erro ao analisar dados",
        "error_export": "Erro ao exportar dados",
        "warning_no_data": "Nenhum dado disponível para esta área",
        "loading_data": "Carregando dados...",
        "calculating": "Calculando...",
        
        # Map Controls
        "map_controls": "🎛️ Controles do Mapa",
        "layer_control": "Controle de Camadas",
        "layer_control_hint": "Procure pelo ícone ⌗ no canto superior direito para alternar camadas",
        "basemaps_section": "Mapas Base",
        "basemaps_info": "6 opções de mapa base disponíveis (OpenStreetMap, Google Maps, Google Satellite, ArcGIS Street, ArcGIS Satellite, ArcGIS Terrain)",
        "basemap_default": "Google Maps está selecionado por padrão",
        "overlay_tip": "Dica: Sobreponha múltiplos mapas base e camadas de dados para comparar diferentes visualizações",
        
        # Territory Analysis
        "territory_analysis_title": "🏛️ Análise de Territórios Indígenas",
        "analyze_territory_intro": "Analise cobertura do solo em territórios indígenas:",
        "territories_not_loaded": "❌ Dados de territórios não carregados.",
        "territory_names_error": "❌ Não foi possível carregar nomes de territórios",
        "select_a_territory": "Selecione um território",
        "data_source_label": "Fonte de Dados",
        "year_1": "Ano 1",
        "year_2": "Ano 2",
        "compare_years_label": "Comparar Anos",
        "btn_analyze": "📊 Analisar",
        "btn_zoom_territory": "➕ Zoom para Território",
        "territory_added": "✅ Território '{territory}' adicionado ao mapa",
        "territory_add_failed": "❌ Falha ao adicionar camada de território: {error}",
        "analyzing_territory": "Analisando {territory}...",
        "territory_geometry_error": "❌ Não foi possível obter geometria do território",
        "analysis_complete": "✅ Análise concluída para {territory}",
        "analysis_failed": "❌ Análise falhou: {error}",
        "hansen_analysis_failed": "❌ Análise Hansen falhou: {error}",
        "territory_error": "❌ Erro na análise de território: {error}",
        
        # Buffer Zone
        "buffer_zone_title": "⭕ Análise de Zona de Buffer Externa do Território",
        "buffer_zone_desc": "Criar Zona de Buffer Externa",
        "buffer_zone_hint": "Crie uma zona de buffer em forma de anel ao redor do território para análise",
        "compare_buffer": "📊 Comparar Território vs Buffer",
        "compare_buffer_help": "Analise zona de território e buffer lado a lado",
        "buffer_distance_label": "Distância do Buffer",
        "btn_create_buffer": "🔵 Criar Buffer",
        "km_format": "{distance} km",
        "buffer_created": "✅ Buffer de {distance}km criado - Modo de comparação ativado!",
        "buffer_created_compare": "✅ Buffer de {distance}km criado ao redor de '{territory}'",
        "buffer_compare_info": "📊 Clique em 'Analisar' para comparar zona de território vs buffer",
        "buffer_analyze_info": "🔽 Use o botão 'Analisar Zona de Buffer' abaixo para analisar apenas a zona de buffer",
        "buffer_create_failed": "❌ Falha ao criar buffer: {error}",
        "buffer_zone_analysis": "🔵 Análise de Zona de Buffer",
        "buffer_analysis_hint": "Analise a zona de buffer de {distance}km ao redor de {territory}",
        "btn_analyze_buffer": "🔍 Analisar Zona de Buffer",
        "btn_zoom_buffer": "🔭 Zoom para Buffer",
        "buffer_added": "✅ Buffer '{distance}km' adicionado ao mapa - role para baixo para ver mapa",
        "buffer_added_error": "❌ Falha ao adicionar camada de buffer: {error}",
        "buffer_analyzing": "Analisando zona de buffer...",
        "buffer_analysis_complete": "✅ Análise da zona de buffer concluída!",
        "buffer_analysis_info": "📊 Role para baixo para ver resultados",
        "buffer_analysis_failed": "❌ Falha ao analisar buffer: {error}",
        
        # View Options
        "view_options": "🎨 Opções de Visualização",
        "show_consolidated": "Mostrar Classes Consolidadas",
        "consolidated_help": "Agrupe 256 classes Hansen em 12 categorias consolidadas para visualização mais limpa",
        "consolidated_view": "📊 Visualização consolidada: 256 classes → 12 categorias",
        "detailed_view": "📊 Visualização detalhada: Todas as 256 classes originais",
        
        # Add Map Layers
        "add_layer_to_analyze": "🗺️ Adicionar Camadas de Mapa {layers}",
        
        # About Section
        "about_title": "ℹ️ Sobre",
        "about_overview": "Visão Geral do Projeto",
        "about_desc": "Esta ferramenta de análise de uso e cobertura do solo faz parte de um projeto de pesquisa que estuda mudanças ambientais em Territórios Indígenas Brasileiros usando Google Earth Engine e dados MapBiomas. Estes dados são comparados com mudanças políticas e tendências de desmatamento para compreender os impactos nestas terras críticas.",
        "about_author": "Leandro Meneguelli Biondo",
        "about_role": "Candidato de PhD em Sustentabilidade",
        "about_university": "IGS/UBCO",
        "about_supervisor": "Supervisor: Dr. Jon Corbett",
        "about_app_name": "Yvynation",
        "about_app_note": "é um nome para este aplicativo, pois não é o conteúdo completo do projeto.",
        "yvynation_meaning": "\"Yvy\" (Tupi–Guarani) significa terra, terra ou território — enfatizando a terra que pisamos e nossa conexão sagrada com a natureza. Frequentemente se relaciona com o conceito de \"Yvy marãe'ỹ\" (Terra sem mal).",
        "nation_meaning": "\"Nation\" refere-se a uma comunidade ou povo autogovernable com cultura, história, idioma e terra compartilhados. Significa auto-determinação e governança.",
        "data_sources_title": "Fontes de Dados",
        "mapbiomas_title": "MapBiomas Coleção 9",
        "mapbiomas_resolution": "Resolução: 30 m",
        "mapbiomas_period": "Período: 1985–2023 (anual)",
        "mapbiomas_classes": "Classes: 62 categorias de cobertura do solo",
        "mapbiomas_license": "Licença: Creative Commons Attribution 4.0",
        "territories_title": "Territórios Indígenas",
        "territories_desc": "700+ territórios brasileiros com limites vetoriais e atributos - Projeto Territórios MapBiomas",
        "features_title": "Recursos",
        "feature_mapping": "Mapeamento interativo com dados em tempo real",
        "feature_calculation": "Cálculos de área e detecção de mudanças",
        "feature_filtering": "Filtragem de território por estado ou nome",
        "feature_visualization": "Visualizações estatísticas",
        "feature_export": "Capacidades de exportação de dados",
        "tech_title": "Tecnologias",
        "tech_python": "Python 3.8+",
        "tech_gee": "Google Earth Engine API",
        "tech_geemap": "geemap (mapeamento interativo)",
        "tech_streamlit": "Streamlit (interface web)",
        "tech_science": "pandas, matplotlib, seaborn (análise e visualização)",
        
        # Main App Content - Page Title & Meta
        "page_title": "Yvynation - Análise Earth Engine",
        
        # Analysis Section Headers
        "mapbiomas_header": "📍 Análise de Cobertura do Solo MapBiomas",
        "hansen_header": "🌍 Análise de Mudanças Florestais Hansen/GLAD",
        "hansen_gfc_header": "🌲 Análise de Mudanças Florestais Globais Hansen",
        "aafc_header": "🚜 Análise do Inventário Anual de Cultivos AAFC (Canadá)",
        "comparison_header": "📈 Análise Comparativa",
        
        # Analysis Status Messages
        "analyzing_years": "Analisando {count} ano(s) de dados...",
        "analyzing_aafc_years": "Analisando {count} ano(s) de dados AAFC...",
        "year_analysis_complete": "✓ {year}: Análise concluída",
        "year_classes_found": "✓ {year}: {count} classes encontradas",
        "year_analysis_failed": "Erro ao analisar {year}: {error}",
        "no_mapbiomas_layer": "Adicione uma camada MapBiomas da barra lateral para analisar",
        "no_hansen_layer": "Adicione uma camada Hansen da barra lateral para analisar",
        "no_aafc_layer": "Adicione uma camada AAFC da barra lateral para analisar",
        "load_data_mapbiomas": "Carregue dados e adicione uma camada MapBiomas para começar a análise",
        "load_data_hansen": "Carregue dados e adicione uma camada Hansen para começar a análise",
        
        # Forest Analysis Headers
        "tree_cover_header": "Cobertura de Dossel de Árvores no Ano 2000",
        "tree_loss_header": "Perda Florestal por Ano (2001-2024)",
        "tree_gain_header": "Ganho de Cobertura Arbórea (2000-2012)",
        
        # Data Availability Messages
        "no_tree_data": "Nenhum dado de cobertura arbórea disponível",
        "no_tree_loss_data": "Nenhum dado de perda florestal disponível",
        "no_tree_gain_data": "Nenhum dado de ganho de cobertura disponível",
        "no_loss_detected": "✅ Nenhuma perda florestal detectada nesta área!",
        "intact_forest_area": "Área total com floresta intacta: {area:,} ha",
        "no_gain_detected": "Nenhum ganho de cobertura detectado nesta área durante 2000-2012",
        "add_gfc_layers": "👆 Adicione camadas de Mudanças Florestais Globais Hansen da barra lateral para analisar dinâmica de cobertura arbórea",
        "aafc_canada_only": "🍁 Os dados AAFC estão disponíveis apenas para o Canadá. Selecione o Canadá no seletor de país para analisar o inventário de cultivos.",
        
        # Empty States
        "empty_histogram": "Histograma vazio para {year}",
        "no_stats_returned": "Nenhuma estatística retornada para {year}",
        "no_data_area": "Nenhum dado na área selecionada para este ano",
        "no_aafc_data_year": "Nenhum dado AAFC encontrado para {year} nesta área",
        
        # Results Display
        "consolidated_view": "Visualização Consolidada (12 classes)",
        "detailed_view": "Visualização Detalhada (256 classes)",
        "loss_by_year": "Perda por Ano:",
        
        # Error Messages
        "error_analyzing": "Erro ao analisar {area}: {error}",
        "error_analyzing_year": "Erro ao analisar {year}: {error}",
        "error_analyzing_gfc": "Erro ao analisar Hansen GFC para {area}: {error}",
        "error_analyzing_aafc": "Erro ao analisar AAFC para {area}: {error}",
        "analysis_partial": "Análise de {type} parcial: {error}",
        
        # Warnings
        "analysis_complete_partial": "✓ Análise concluída! Dados encontrados para: {sources}",
        "no_gfc_data": "Nenhum dado Hansen GFC encontrado nesta área",
        "tree_cover_partial": "Análise de cobertura arbórea parcial: {error}",
        "tree_loss_partial": "Análise de perda florestal parcial: {error}",
        "tree_gain_partial": "Análise de ganho arbóreo parcial: {error}",
        
        # Getting Started / Tutorial Headers
        "getting_started_header": "Como Usar Esta Plataforma",
        "getting_started_title": "🎯 Primeiros Passos",
        "getting_started_intro": "Esta plataforma permite análise completa de cobertura do solo para Brasil e monitoramento global de florestas. Você pode analisar áreas personalizadas, territórios indígenas e zonas de buffer externas.",
        
        # Tutorial Step Titles
        "step_custom_polygon": "1️⃣ **Analisar um Polígono Personalizado**",
        "step_territory": "2️⃣ **Analisar um Território Indígena**",
        "step_comparison": "3️⃣ **Comparação Multi-Ano**",
        "step_export": "4️⃣ **Exportar e Baixar Resultados**",
        "step_map_controls": "🗺️ **Controles do Mapa e Navegação**",
        "step_data_understanding": "📊 **Entendendo os Dados e Resultados**",
        
        # Tutorial Content - Step 1
        "step1_draw_intro": "Desenhe e analise qualquer área no mapa:",
        # Tutorial Content - Step 2
        "step2_territory_intro": "Limites de territórios indígenas pré-definidos com análise histórica:",
        # Tutorial Content - Step 3
        "step3_comparison_intro": "Compare mudanças de cobertura do solo entre dois anos:",
        # Tutorial Content - Step 4
        "step4_export_intro": "Salve os resultados da sua análise para relatórios e análise posterior:",
        # Tutorial Content - Step 5
        "step5_map_controls_intro": "Controles de Mapa & Navegação",
        # Tutorial Content - Step 6
        "step6_data_understanding_intro": "Compreendendo Dados & Resultados",
        
        # Map Components - Territory & Buffer
        "territory_layer": "Território: {territory_name}",
        "buffer_layer": "Buffer: {buffer_name}",
        "buffer_geojson": "Buffer: {buffer_name}",
        "captured_polygons": "✓ Capturadas {count} polígono(s). Selecione um abaixo para analisar.",
        "polygon_captured": "✓ Polígono capturado. Role para baixo para analisar.",
        "buffer_label": "Buffer {number}",
        "polygon_bounds": "Polígono {number} - {type} - Limites: {bounds}",
        "selected_buffer": "✓ Selecionado: {buffer_name}",
        "selected_polygon": "✓ Polígono Selecionado {number} para análise",
        "buffer_ring_help": "Crie um buffer em forma de anel ao redor deste polígono para análise",
        "compare_help": "Analise tanto a zona do polígono quanto a do buffer lado a lado",
        "map_display_error": "Erro de exibição do mapa: {error}",
        "polygon_only_error": "❌ Buffers podem ser criados apenas para recursos poligonais",
        "buffer_creation_error": "❌ Falha ao criar buffer: {error}",
        "buffer_created_compare": "✅ Buffer de {distance}km criado - Modo de comparação ativado!",
        "analysis_compare_info": "📊 As abas de análise mostrarão resultados tanto do polígono quanto do buffer",
        "buffer_created": "✅ Buffer de {distance}km criado ao redor de {name}",
        "buffer_added_info": "📍 Buffer adicionado à lista de polígonos - atualize para selecioná-lo",
        "territory_added_map": "Camada de territórios adicionada: {name}",
        "buffer_added_map": "Camada de buffer adicionada: {name}",
        "analysis_layer_added": "✓ Camada de análise adicionada ao mapa: {name}",
        "comparison_layer_added": "✓ Camada de comparação adicionada ao mapa: {name}",
        "year2_analysis_error": "⚠️ Não foi possível adicionar análise do segundo ano: {error}",
        "analysis_error": "❌ Erro ao adicionar camada de análise: {error}",
        "adding_territory_error": "[Erro] Falha ao adicionar camada de territórios: {error}",
        "adding_buffer_error": "[Erro] Falha ao adicionar camada de buffer para {name}: {error}",
        
        # Layer Reference Guide
        "layer_reference_full": "📚 Guia de Referência de Camadas - legendas",
        "indigenous_territories_legend": "📍 Terras & Territórios Indígenas",
        "indigenous_territories_label": "Territórios Indígenas",
        "selected_territory_label": "Território Selecionado",
        "drawn_polygon_label": "Polígono Desenhado",
        "buffer_zone_label": "Zona de Buffer Externo",
        "mapbiomas_legend": "🌱 Classes de Cobertura do Solo MapBiomas",
        "hansen_legend": "🌍 Classes de Cobertura do Solo Global Hansen/GLAD",
        "gfc_legend": "🌲 Mudanças Florestais Globais Hansen (UMD 2024)",
        "gfc_legend_desc": "Análise de mudança de cobertura florestal de 2000-2024",
        "aafc_legend": "🚜 Inventário Anual de Cultivos AAFC (Canadá)",
        "aafc_legend_desc": "Cobertura de terra agrícola no Canadá (2009-2024, resolução 30m)",
        "legend_controls": "Instruções de Controle",
        "legend_layer_control": "Controle de Camadas: canto superior direito",
        "legend_drawing_tools": "Ferramentas de Desenho: canto superior esquerdo",
        "legend_opacity": "Opacidade: Ajuste na barra lateral",
        "legend_data_overview": "Visão Geral de Camadas de Dados",
        "legend_data_brazilian": "🌱 MapBiomas: Cobertura do solo brasileiro (1985-2023)",
        "legend_data_global": "🌍 Hansen: Mudança florestal global (2000-2020)",
        "legend_data_agriculture": "🚜 AAFC: Inventário de cultivos canadense (2009-2024)",
        "legend_data_territories": "📍 Territórios Indígenas",
        
        # Analysis Messages - Additional
        "no_forest_loss": "✅ Nenhuma perda florestal detectada nesta área!",
        "forest_loss_intact": "Área total com floresta intacta: {area:,.0f} ha",
        "area_with_gain": "Área com Ganho",
        "area_without_gain": "Área sem Ganho",
        "download_gain_data": "📥 Baixar Dados de Ganho",
        "gfc_available_layers": "Camadas Disponíveis:",
        "gfc_layer_tree_cover": "🌳 **Cobertura Florestal 2000**: Percentual de cobertura basal de referência",
        "gfc_layer_tree_loss": "🔥 **Ano de Perda Florestal**: Perda florestal anual de 2001-2024",
        "gfc_layer_tree_gain": "🌲 **Ganho Florestal**: Reflorestamento de 2000-2012",
        "gfc_add_from_sidebar": "Adicione essas camadas da barra lateral sob **🌲 Mudanças Florestais Globais Hansen**.",
        "aafc_analyzing_years": "Analisando {count} ano(s) de dados AAFC...",
        "aafc_year_label": "Ano {year}",
        "aafc_total_area": "Área Total",
        "aafc_classes_detected": "Classes Detectadas",
        "aafc_largest_class": "Classe Maior",
        "aafc_download_csv": "📥 Baixar CSV ({year})",
        "aafc_analysis_complete": "✓ {year}: Análise concluída",
        "aafc_no_data_year": "Nenhum dado AAFC encontrado para {year} nesta área",
        "aafc_analysis_error": "Erro ao analisar AAFC {year}: {error}",
        
        # Legend and Display
        "legend_areas_with_forest_loss": "Áreas com perda florestal detectada",
        "legend_no_forest_loss": "Áreas sem perda florestal",
        "legend_areas_with_gain": "Áreas com ganho florestal",
        "legend_no_forest_gain": "Áreas sem ganho florestal",
        
        # Initialization & Loading
        "initializing_ee": "Inicializando Google Earth Engine...",
        "loading_data": "Carregando dados...",
        "ee_init_error": "❌ Falha ao inicializar Earth Engine: {error}",
        "data_loaded": "✅ Dados carregados com sucesso",
        "data_load_error": "❌ Erro ao carregar dados: {error}",
        
        # Comparison Messages
        "no_comparison_data": "Nenhum dado de comparação disponível",
        "hansen_unavailable": "Dados Hansen não disponíveis para os anos {year1} e {year2}",
        "sankey_generation_error": "Não foi possível gerar diagrama de Sankey",
        "no_transition_data": "Nenhum dado de transição disponível",
        "geometry_not_available": "Geometria não disponível. Execute análise primeiro.",
        "sankey_display_error": "Não foi possível exibir diagrama de Sankey: {error}",
        
        # Buffer Comparison Messages
        "buffer_compare_on": "✓ Modo de Comparação de Buffer: ATIVO",
        "buffer_compare_off": "Modo de Comparação de Buffer: INATIVO",
        "buffer_compare_active": "✓ Buffer: {buffer_name}",
        "buffer_compare_none": "⚠ Nenhum Buffer Criado",
        
        # Download and Export
        "download_csv_label": "📥 Baixar CSV",
        "download_success": "✅ Download pronto",
        "export_error": "❌ Erro ao exportar dados: {error}",
        
        # Export Maps Section
        "export_maps_intro": "🗺️ Export Maps with Polygon Overlays",
        "export_maps_description": "Export interactive maps showing each active layer with your drawn polygons and scale bars. Maps are saved as HTML files and can be opened in any web browser.",
        "export_maps_caption": "Maps include: MapBiomas overlays, Hansen overlays, Google Satellite, Google Maps, scale bars, and layer controls",
        "export_maps_ready": "✓ {count} polygon(s) ready for export",
        "export_maps_warning": "⚠ Draw at least one polygon on the map to export with overlays",
        "export_maps_no_polygons": "Please draw at least one polygon on the map first",
        "export_maps_no_object": "Map object not found. Please refresh the page and try again.",
        "export_maps_preparing": "Creating export maps...",
        "export_maps_button": "📊 Prepare Maps for Export",
        "export_maps_success": "✓ {count} map(s) prepared! They will be included in the Export All ZIP file.",
        "export_maps_no_created": "No maps were successfully created. Check console for errors.",
        "export_maps_error": "Error preparing maps: {error}",
        "export_maps_convert_error": "Could not convert {name} to HTML: {error}",
        "export_maps_export_error": "Could not export {name}: {error}",
        "export_analysis": "💾 Export Analysis",
        "polygon_analysis_header": "📊 Polygon Analysis & Statistics",
        "analyzing_polygon": "🔵 Analyzing: {name}",
        "export_analysis": "💾 Exportar Análise",
        "polygon_analysis_header": "📊 Análise e Estatísticas de Polígonos",
        "analyzing_polygon": "🔵 Analisando: {name}",
        "download_csv_label": "📥 Baixar CSV",
        "download_success": "✅ Download pronto",
        "export_error": "❌ Erro ao exportar dados: {error}",
        
        # Export Maps Section
        "export_maps_intro": "🗺️ Exportar Mapas com Sobreposições de Polígonos",
        "export_maps_description": "Exporte mapas interativos mostrando cada camada ativa com seus polígonos desenhados e barras de escala. Os mapas são salvos como arquivos HTML e podem ser abertos em qualquer navegador da web.",
        "export_maps_caption": "Os mapas incluem: sobreposições MapBiomas, sobreposições Hansen, Satélite Google, Google Maps, barras de escala e controles de camadas",
        "export_maps_ready": "✓ {count} polígono(s) pronto(s) para exportar",
        "export_maps_warning": "⚠ Desenhe pelo menos um polígono no mapa para exportar com sobreposições",
        "export_maps_no_polygons": "Por favor, desenhe pelo menos um polígono no mapa primeiro",
        "export_maps_no_object": "Objeto do mapa não encontrado. Por favor, atualize a página e tente novamente.",
        "export_maps_preparing": "Criando mapas para exportação...",
        "export_maps_button": "📊 Preparar Mapas para Exportação",
        "export_maps_success": "✓ {count} mapa(s) preparado(s)! Será(ão) incluído(s) no arquivo ZIP de Exportação Completa.",
        "export_maps_no_created": "Nenhum mapa foi criado com sucesso. Verifique o console para erros.",
        "export_maps_error": "Erro ao preparar mapas: {error}",
        "export_maps_convert_error": "Não foi possível converter {name} em HTML: {error}",
        "export_maps_export_error": "Não foi possível exportar {name}: {error}"
    }
}


def get_translation(language: str, key: str, **kwargs) -> str:
    """
    Get translation for a given key in the specified language.

    Args:
        language: Language code ('en' or 'pt-br')
        key: Translation key
        **kwargs: Format arguments for the translation string

    Returns:
        Translated string or the key if not found
    """
    if language not in TRANSLATIONS:
        language = "en"

    translation = TRANSLATIONS[language].get(key, key)

    # Format with any provided arguments
    if kwargs:
        try:
            return translation.format(**kwargs)
        except KeyError:
            return translation

    return translation


def t(key: str, **kwargs) -> str:
    """
    Shorthand for getting translation based on selected language in session state.

    Args:
        key: Translation key
        **kwargs: Format arguments

    Returns:
        Translated string
    """
    language = st.session_state.get('language', 'en')
    return get_translation(language, key, **kwargs)
