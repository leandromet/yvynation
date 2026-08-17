"""English translations for Yvynation.

One file per language: add/edit keys here only. English (en.py)
is the reference dictionary — every key must exist there; other
languages fall back to English for any missing key.
Check coverage with:  python -m yvynation.utils.translations
"""

TRANSLATIONS_EN = {
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
- **Brazil**: Full MapBiomas coverage (1985-2024) + Hansen/GLAD global data
- **Canada**: AAFC crop inventory + Hansen/GLAD global data

The map will center on your selected region.""",

    "step_custom_polygon": "Step 1: Analyze a Custom Polygon",
    "step1_draw_intro": "Draw and analyze any area on the map:",
    "step1_content": """1. **Drawing Tools** (top-left corner of map):
   - Click the **Rectangle** tool for quick rectangular selections
   - Click the **Polygon** tool for custom shapes with multiple points
   - Double-click or click the first point again to complete a polygon

2. **Select Data Layers** (left sidebar):
   - **MapBiomas**: Brazilian land cover (1985-2024, 62 classes, 30m resolution)
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
   - Historical land cover changes (1985-2024)
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

**MapBiomas Collection 10** (Brazil):
- Coverage: All of Brazil, 1985-2024
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
    "mapbiomas_desc": "MapBiomas Collection 10 - Resolution: 30m, Period: 1985-2024 (annual), 62 land cover categories, CC BY 4.0",
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

    # Portal page
    "about_section": "About Yvynation",
    "about_description": "Yvynation is a comprehensive platform for indigenous land monitoring and analysis. It combines satellite imagery, geospatial analysis tools, and forest change detection to provide insights into land use changes and ecosystem dynamics.",
    
    # Sidebar sections
    "geometry_tools": "Geometry Tools",
    "geometry_section": "Geometry & Drawing",
    "buffer_controls": "Buffer Controls",
    "analysis_settings": "Analysis Settings",
    "territory_selection": "Territory Selection",
    "comparison_controls": "Comparison Controls",
    
    # Form inputs
    "enter_distance": "Enter distance",
    "territory_search": "Search Territory",
    "search_territory": "Search territory by name...",
    "country": "Country",
    "territory_type": "Territory Type",
    "indigenous_lands_btn": "🪶 Indigenous",
    "conservation_units_btn": "🌿 Conservation",
    
    # Other
    "no_results": "No results found",
    "remove": "Remove",
    "aafc_section_title": "AAFC Layers (Canada)",

    # =====================================================================
    # Analysis navbar / main content (index.py)
    # =====================================================================
    "nav_hide": "☰ Hide",
    "nav_show": "☰ Show",
    "sidebar_narrow": "Narrow",
    "sidebar_normal": "Normal",
    "sidebar_wide": "Wide",
    "geometry_analysis_label": "🔷 Geometry Analysis",
    "territory_analysis_label": "🗺️ Territory Analysis",
    "back_to_portal": "← Back to Portal",
    "back_to_batch": "← Back to Batch",
    "clear_btn": "🔄 Clear",
    "clear_btn_title": "Clear all analysis data and start fresh",
    "active_analysis_area": "Active analysis area",
    "no_areas_yet": "No areas yet — select a territory or draw one",
    "run_all_analysis": "▶ Run all analysis",
    "bundling": "Bundling…",
    "download_all": "⬇️ Download all",
    "results_label": "📊 Results",
    "full_results": "⛶ Full results",
    "exit_full_results": "⛶ Exit full results",
    "toggle_full_results_title": "Toggle full-screen results",

    # =====================================================================
    # Portal page (portal.py)
    # =====================================================================
    "portal_ds_mapbiomas": "MapBiomas: Brazilian land cover (1985-2024, 30m resolution)",
    "portal_ds_hansen": "Hansen/GFC: Global forest change detection",
    "portal_ds_aafc": "AAFC: Canadian agricultural and forest classification",
    "portal_ds_gee": "Google Earth Engine: Cloud-based geospatial analysis",
    "portal_ds_custom": "Custom geometries: Draw or upload your own features",
    "portal_choose_title": "🚀 Choose Your Analysis Path",
    "portal_choose_desc": "Select the analysis type that best fits your workflow. Both paths provide access to the same tools and datasets, optimized for your use case.",
    "portal_geometry_sub": "Draw & analyze custom areas",
    "portal_geometry_i1": "Draw polygons on the map",
    "portal_geometry_i2": "Upload GeoJSON/Shapefiles/KML",
    "portal_geometry_i3": "Create buffer zones",
    "portal_geometry_i4": "Analyze land cover changes",
    "portal_geometry_btn": "→ Start Geometry Analysis",
    "portal_territory_sub": "Monitor indigenous lands",
    "portal_territory_i1": "Select from 700+ territories",
    "portal_territory_i2": "Search by name",
    "portal_territory_i3": "Track forest changes (1985-2024)",
    "portal_territory_i4": "Compare multiple years",
    "portal_territory_btn": "→ Start Territory Analysis",
    "portal_batch_sub": "Process multiple territories at once",
    "portal_batch_i1": "Select any number of territories",
    "portal_batch_i2": "Run MapBiomas, Hansen GLAD & GFC",
    "portal_batch_i3": "Territory + buffer automatically",
    "portal_batch_i4": "Download one ZIP with all data",
    "portal_batch_btn": "→ Start Batch Processing",
    "portal_resources": "📚 Resources",
    "portal_footer_data": "Data",
    "portal_footer_contact": "Contact",
    "portal_show": "(show)",
    "portal_hide": "(hide)",
    "portal_link_methods": "Methods & Research",
    "portal_support": "🎓 Support",
    "portal_link_tutorial": "Tutorial & Guide",
    "portal_link_faq": "FAQ",
    "portal_link_contact": "Contact & Feedback",
    "portal_link_team": "Team & Contributors",
    "portal_link_cite": "How to Cite",

    # =====================================================================
    # Citation & acknowledgments (components/citation.py)
    # =====================================================================
    "citation_title": "How to Cite & Acknowledgments",
    "citation_mission": "Yvynation provides open geospatial data, charts, and figures to support communities and managers of Indigenous Lands and Conservation Units, and to give researchers and journalists reliable figures and tables for their own work.",
    "citation_acknowledgment_title": "Acknowledgments",
    "citation_acknowledgment_text": "Geospatial processing for this platform runs on Google Earth Engine, under the project ProtectedLandsYvynation-EE, registered for noncommercial research use. Cloud infrastructure is supported by Google Cloud Research Credits.",
    "citation_ack_people": "Thanks to Jon Corbett (supervisor) and the doctoral committee — Jonathan Cinnamon, Robert Friberg and Tim Paulson — for guidance on the framework; to Pedro de Almeida Salles, who co-developed the Brazilian forest-policy timeline corpus; to Alexander Biondo, Gabriel Silva Santos, Clayton Borges, Bernardo Trovão and Aparicio Biondo for the ideas, discussion and testing behind the Yvynation pipeline and design; and to the MapBiomas and Hansen/GLAD teams for their open land-cover products.",
    "citation_ack_compute": "Computation is supported by the Google Cloud Research Credits programme (Earth Engine project ee-leandromet). Discussions with the Brazilian Rural Environmental Registry team (Ministry of Management and Innovation in Public Services), Google's Earth Engine and Google Brazil teams, MapBiomas and Imazon — on acquiring and publicising the 2008 SPOT imagery used for rural-property analysis under the 2012 Forest Code — shaped this work. The National Institute of the Atlantic Forest (Brazilian Ministry of Technology and Innovation) and the Brazilian Forest Service (Brazilian Ministry of Climate Change and Environment) authorised the sabbatical leave for these graduate studies.",
    "citation_ack_funding": "Financial support comes from Environment and Climate Change Canada (ECCC) through the Climate Action and Awareness Fund (CAAF), including a research assistantship under the UBCO Transportation and Climate Action Research initiative, led by the UBC Integrated Transportation Research (UiTR) Laboratory at the Okanagan campus. Academic, social and intellectual support comes from the UBCO Interdisciplinary Graduate Studies (IGS) – Sustainability Theme and the Institute for Community Engaged Research (ICER).",
    "citation_ack_summary": "Open land-cover data from MapBiomas and Hansen/GLAD, processed on Google Earth Engine with Google Cloud Research Credits. Research support from ECCC/CAAF and ICER/IGS/CliMr on UBC Okanagan — full acknowledgements under “How to Cite”.",
    "license_summary": "Data generated in Yvynation are public, open and free to use, with attribution.",
    "license_title": "License",
    "citation_howto_title": "Suggested citation",
    "citation_platform_text": "Biondo, L. M. (2026). Yvynation: a geospatial monitoring platform for Indigenous Lands and Conservation Units [Software]. Interdisciplinary Graduate Studies – Sustainability Theme (IGS), UBC Okanagan. Data processed via Google Earth Engine (project ProtectedLandsYvynation-EE).",
    "citation_datasets_title": "Please also cite the underlying data sources you used:",
    "citation_ds_mapbiomas": "MapBiomas Project — Collection 10 of the Brazilian Land Cover & Use Map Series, mapbiomas.org",
    "citation_ds_hansen": "Hansen, M.C. et al. (2013). High-Resolution Global Maps of 21st-Century Forest Cover Change. Science. (Global Forest Change / GLAD, UMD)",
    "citation_ds_aafc": "Agriculture and Agri-Food Canada (AAFC) — Annual Crop Inventory",
    "citation_ds_gee": "Gorelick, N. et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment.",
    "citation_hide": "Hide",

    # =====================================================================
    # Batch processing page (batch_processing.py)
    # =====================================================================
    "batch_title": "🔶 Batch Processing",
    "batch_nav_subtitle": "Run full analysis on multiple territories — download one ZIP",
    "batch_select_territories": "🗺️ Select Territories",
    "batch_selected_suffix": " selected",
    "batch_indigenous_btn": "🪶 Indigenous",
    "batch_conservation_btn": "🌿 Conservation Units",
    "batch_search_placeholder": "🔍 Search territories…",
    "batch_select_all_filtered": "Select all filtered",
    "batch_shown_suffix": " shown",
    "batch_area_filter_label": "Area:",
    "batch_min_ha_placeholder": "Min",
    "batch_max_ha_placeholder": "Max",
    "batch_ha_suffix": "ha",
    "batch_filter_uf_label": "State (UF)",
    "batch_filter_fase_label": "Stage",
    "batch_filter_modalidade_label": "Modality",
    "batch_filter_categoria_label": "Category",
    "batch_filter_esfera_label": "Jurisdiction",
    "batch_filter_grupo_label": "Protection",
    "batch_clear_filters": "Clear filters",
    "batch_sort_label": "Sort",
    "batch_sort_name_asc": "Name A–Z",
    "batch_sort_name_desc": "Name Z–A",
    "batch_sort_area_asc": "Area: smallest first",
    "batch_sort_area_desc": "Area: largest first",
    "batch_review_btn": "Review",
    "batch_review_title": "Selected Territories",
    "batch_review_empty": "No territories selected yet.",
    "batch_review_close": "Close",
    "batch_paste_instruction": "📋 Paste a list of names (one per line) or upload a .txt/.csv to select them automatically:",
    "batch_select_from_list": "✓ Select from list",
    "batch_upload_list": "📁 Upload list",
    "batch_clear": "Clear",
    "batch_not_found_prefix": "⚠ Not found: ",
    "batch_configuration": "⚙️ Configuration",
    "batch_year1_label": "Single-year snapshot or Initial",
    "batch_year2_label": "Comparison final year",
    "batch_hansen_year_label": "Hansen GLAD year",
    "batch_analysis_types": "Analysis types",
    "batch_chk_mapbiomas": "🌿 MapBiomas single-year",
    "batch_chk_comparison": "📊 Year-over-year comparison",
    "batch_chk_treemap": "🟦 Class-transition treemaps (per-class + Others)",
    "batch_treemap_hint": "Adds a faceted treemap (one per class, smaller classes rolled into “Others”) wherever transitions are produced — the year comparison and each multi-window step.",
    "batch_chk_glad": "🌲 Hansen GLAD forest cover",
    "batch_chk_gfc": "🪓 Hansen GFC (loss / gain)",
    "batch_figs_label": "FIGURE EXPORT",
    "batch_chk_export_png": "🖼 Also export figures as PNG",
    "batch_png_hint": "HTML is always written. PNGs are ~90% of an archive's size but only a few percent of its run time — turning them off saves space, not time.",
    "batch_chk_png_high_res": "Full resolution (larger files)",
    "batch_timeline_bands_label": "TIMELINE CONTEXT BANDS",
    "batch_chk_timeline_political": "Presidents / governors stripe",
    "batch_chk_timeline_policy": "Policy rows + milestone key",
    "batch_chk_timeline_enso": "El Niño / La Niña (ENSO) strip",
    "batch_timeline_bands_hint": "Each band you drop also removes the space it reserved, so the chart gets shorter.",
    "batch_chk_pdf_maps": "🗺️ PNG maps and Charts (satellite + MapBiomas y1/y2)",
    "batch_aux_rasters_label": "Extra MapBiomas rasters (year2)",
    "batch_aux_deforestation": "🌳 Deforestation & secondary vegetation",
    "batch_aux_fire_scar": "🔥 Annual burned area (fire scar size)",
    "batch_aux_fire_frequency": "📊 Fire frequency (1985–2024 full period)",
    "batch_aux_fire_year_last": "📅 Year of last fire",
    "batch_aux_mining": "⛏️ Mining substances",
    "batch_aux_agriculture": "🌾 Agriculture — number of cycles",
    "batch_chk_multi_window": "🌀 Multiple time-window MapBiomas (Sankey + Sunburst + Treemaps)",
    "batch_mw_mode": "Mode:",
    "batch_mw_step": "Step (years):",
    "batch_mw_forced_note": "1985 → 2024 forced as last year",
    "batch_mw_custom_label": "Custom years (3 or 4, comma-separated, 1985–2024)",
    "batch_mw_active_years": "Active years: ",
    "batch_chk_timeline": "📈 Deforestation timeline (Hansen + MapBiomas + Fire) with political/policy context",
    "batch_buffer_zone": "Buffer zone",
    "batch_include_buffer": "Include buffer analysis",
    "batch_km_ring": "km external ring",
    "batch_progress": "📊 Progress",
    "batch_territory_label": "Territory:",
    "batch_step_label": "Step:",
    "batch_in_flight_label": "Running:",
    "batch_done_label": "Done:",
    "batch_complete_label": "— complete —",
    "batch_errors_suffix": " errors)",
    "batch_processing_log": "Processing log",
    "batch_about_title": "📖 About Batch Processing",
    "batch_about_text": "Run the full Yvynation analysis pipeline (MapBiomas land cover, year-over-year change, Hansen GLAD forest cover, and Hansen GFC loss/gain) across many territories in one unattended run. Supports both FUNAI indigenous territories (657) and CNUC conservation units (3,247). Each territory — and its optional external buffer — is processed via Google Earth Engine and packaged into a single ZIP archive containing CSV tables, transition matrices, and chart figures (HTML + PNG) per territory.",
    "batch_time_note": "Expect 2–10 minutes per territory depending on which analyses are enabled. The tab can stay open in the background.",
    "batch_howto": "How to use",
    "batch_howto_1_title": "Select territories",
    "batch_howto_1_body": "Choose the source type (Indigenous or Conservation Units) then use the search box to filter, and tick the territories you want to include. 'Select all filtered' adds every match of the current search; 'Clear all' starts over. Switching type clears the current selection.",
    "batch_howto_2_title": "Pick MapBiomas years",
    "batch_howto_2_body": "Set the initial year (single snapshot) and the final year (for the year-over-year comparison). Range: 1985–2024.",
    "batch_howto_3_title": "Pick the Hansen GLAD year",
    "batch_howto_3_body": "Reference year (2000/2005/2010/2015/2020) used for the Hansen GLAD forest-cover snapshot.",
    "batch_howto_4_title": "Choose analysis types",
    "batch_howto_4_body": "Enable any combination of MapBiomas single-year, year-over-year comparison, Hansen GLAD, and Hansen GFC loss/gain.",
    "batch_howto_5_title": "Optional buffer zone",
    "batch_howto_5_body": "Toggle on to also analyse an external ring (default 10 km) around each territory. Buffer outputs are written to buffer/{territory}_Buffer_{km}km/ inside the ZIP.",
    "batch_howto_6_title": "Start the batch",
    "batch_howto_6_body": "Click 'Start Batch Processing'. The configuration panel is replaced by the live progress view; you can stop after the current territory at any time.",
    "batch_howto_7_title": "Download the ZIP",
    "batch_howto_7_body": "When the run finishes, hit 'Download ZIP' to grab all tables, transitions, and figures for every territory in one self-describing archive.",
    "batch_start_btn": "🚀 Start Batch Processing",
    "territories_word": "territories",
    "batch_large_run_warning": "Large selection — consider splitting this into a few smaller runs (e.g. 20-25 territories each) to keep the run reliable. If it's interrupted, partial results stay available on the Previous Runs page.",
    "batch_processing_ellipsis": "Processing…",
    "batch_stop_btn": "⏹ Stop after current",
    "batch_download_zip": "⬇️ Download ZIP",
    "batch_new_batch": "🔄 New Batch",
    "batch_territories_selected_suffix": " territories selected",
    "batch_no_territories": "No territories selected",

    # =====================================================================
    # Previous Runs page (previous_runs.py)
    # =====================================================================
    "previous_runs_title": "Previous Runs",
    "previous_runs_subtitle": "Recover finished or interrupted batch exports",
    "previous_runs_intro": "Every batch/export run shows up here, including ones interrupted by a crash or a stopped process — nothing is deleted until you download it or clear it out yourself.",
    "previous_runs_refresh": "Refresh",
    "previous_runs_status_zip": "✅ Finished",
    "previous_runs_status_partial": "⚠ Partial — recoverable",
    "previous_runs_download": "Download",
    "previous_runs_zip_download": "Zip & Download",
    "previous_runs_zipping": "Zipping…",
    "previous_runs_delete": "Delete",
    "previous_runs_copy": "Copy",
    "previous_runs_bucket_section": "Direct bucket link",
    "previous_runs_bucket_hint": "For copying into gcloud/gsutil or the Cloud console. The Download button above does not use these.",
    "previous_runs_detail_config": "Run configuration",
    "previous_runs_detail_territories": "Territories",
    "previous_runs_detail_performance": "Performance",
    "previous_runs_detail_loading": "Reading run details…",
    "previous_runs_files_suffix": "files",
    "previous_runs_empty": "No previous runs yet — batch and export downloads will appear here.",
}
