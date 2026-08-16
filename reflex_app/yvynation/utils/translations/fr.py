"""French translations for Yvynation.

One file per language: add/edit keys here only. English (en.py)
is the reference dictionary — every key must exist there; other
languages fall back to English for any missing key.
Check coverage with:  python -m yvynation.utils.translations
"""

TRANSLATIONS_FR = {
    # Page
    "page_title": "Yvynation - Surveillance des Territoires Autochtones",
    "main_page_title": "Yvynation - Plateforme de Surveillance des Territoires Autochtones",
    "app_title": "Yvynation",
    "app_subtitle": "Plateforme de Surveillance des Territoires Autochtones",
    "app_description": "Plateforme Mondiale de Surveillance Forestière",
    "author": "Leandro M. Biondo - Doctorant - IGS/UBCO",

    # Navigation
    "map_tab": "Carte",
    "analysis_tab": "Analyse",
    "tutorial_tab": "Tutoriel",
    "about_tab": "À propos",

    # Sidebar
    "sidebar_title": "Couches et Contrôles",
    "controls_badge": "Contrôles",
    "mapbiomas_label": "MapBiomas",
    "mapbiomas_section_title": "Couches MapBiomas",
    "mapbiomas_select_year": "Sélectionner l'année MapBiomas",
    "mapbiomas_years": "Années MapBiomas",
    "mapbiomas_layers_label": "Couches MapBiomas",
    "mapbiomas_layers_hint": "Nombre de couches MapBiomas actives",
    "no_mapbiomas_selected": "Aucune année MapBiomas sélectionnée",
    "no_mapbiomas_added": "Ajoutez des couches MapBiomas dans la barre latérale",
    "add_to_map": "Ajouter à la carte",
    "clear_all": "Tout effacer",

    "hansen_label": "Hansen GFC",
    "hansen_section_title": "Hansen GFC",
    "hansen_select_year": "Sélectionner l'année Hansen",
    "hansen_years": "Années Hansen",
    "hansen_layers_label": "Couches Hansen",
    "hansen_layers_hint": "Nombre de couches Hansen actives",
    "hansen_gfc_label": "Changement Forestier Mondial (GFC)",
    "hansen_gfc_layers_label": "Couches GFC",
    "no_hansen_selected": "Aucune année Hansen sélectionnée",
    "no_hansen_added": "Ajoutez des couches Hansen dans la barre latérale",
    "no_hansen_gfc_added": "Aucune couche GFC activée",
    "data_layers": "Couches de données",
    "year_layers": "Couches par année",
    "tree_cover_btn": "Couvert",
    "loss_btn": "Perte",
    "gain_btn": "Gain",
    "add_btn": "Ajouter",

    "tree_cover_2000": "Couvert Forestier 2000",
    "tree_loss_period": "Perte Forestière (2000-2023)",
    "tree_gain_period": "Gain Forestier (2000-2012)",

    # Base layer
    "base_layer": "Fond de Carte",
    "base_layer_hint": "Fond de carte actuel",

    # Active layers
    "active_layers": "Couches Actives",
    "analysis_active_badge": "Analyse Active",

    # Territory section
    "territory_section_title": "Analyse de Territoire",
    "select_territory": "Sélectionner un Territoire",
    "territory_by_country": "Filtrer par Pays",
    "territory_by_state": "Filtrer par État/Province",
    "selected_territory": "Territoire Sélectionné",
    "no_territory_selected": "Aucun territoire sélectionné",
    "search_territories": "Rechercher des territoires...",
    "select_territory_placeholder": "Sélectionner un territoire",
    "click_map_to_select": "Cliquez sur les marqueurs de la carte",
    "show_all_lands": "Afficher Toutes les Terres",
    "hide_all_lands": "Masquer Toutes les Terres",
    "select_territory_above": "Sélectionnez un territoire ci-dessus",
    "compare_years": "Comparer les années",
    "compare_mapbiomas_years": "Comparer les Années MapBiomas",

    # Geometry section
    "geometry_section_title": "Géométrie et Dessin",
    "upload_geometry_file": "Téléverser un fichier de géométrie",
    "analyze_selected_geometry": "Analyser la géométrie sélectionnée",
    "map_overlays": "Superpositions de la carte",
    "show_geometries": "Afficher les Géométries",
    "hide_geometries": "Masquer les Géométries",
    "show_change": "Afficher le Changement",
    "hide_change": "Masquer le Changement",

    # Map controls
    "draw_polygon": "Dessiner un Polygone",
    "clear_drawings": "Tout Effacer",
    "upload_geojson": "Téléverser un GeoJSON",

    # Analysis
    "run_analysis": "Lancer l'Analyse",
    "analysis_results": "Résultats de l'Analyse",
    "mapbiomas_analysis": "Analyse MapBiomas",
    "hansen_analysis": "Analyse Hansen",
    "export_results": "Exporter les Résultats",
    "comparing_label": "Comparaison en cours...",

    # Comparison
    "compare_label": "Comparer :",
    "vs_label": "vs",
    "compare_btn": "Comparer",
    "year_comparison_results": "Résultats de la Comparaison d'Années",
    "download_comparison_csv": "Télécharger le CSV de Comparaison",
    "total_gains": "Gains Totaux",
    "total_losses": "Pertes Totales",
    "net_change": "Changement Net",
    "comparison_available": "Comparaison Disponible",

    # Buttons
    "confirm": "Confirmer",
    "cancel": "Annuler",
    "close": "Fermer",
    "select": "Sélectionner",
    "dismiss": "Ignorer",

    # Messages
    "loading": "Chargement...",
    "analyzing": "Analyse en cours...",
    "initializing": "Initialisation de la Plateforme Yvynation...",
    "ee_init_error": "Échec de l'initialisation d'Earth Engine : {error}",
    "error": "Erreur",
    "success": "Succès",

    # Analysis results
    "class": "Classe",
    "area_hectares": "Superficie (ha)",
    "area_km2": "Superficie (km2)",
    "percentage": "Pourcentage (%)",
    "year": "Année",
    "change": "Changement",
    "from_class": "De la Classe",
    "to_class": "Vers la Classe",
    "area_changed": "Superficie Modifiée",

    # File upload
    "upload_file": "Téléverser un Fichier",
    "file_uploaded": "Fichier téléversé avec succès",
    "file_upload_error": "Erreur lors du téléversement du fichier",
    "select_file": "Sélectionnez un fichier (GeoJSON, KML, Shapefile)",

    # Buffer operations
    "buffer_distance": "Distance de la Zone Tampon (mètres)",
    "create_buffer": "Créer une Zone Tampon",
    "buffer_created": "Zone tampon créée avec succès",

    # Geometry
    "draw_area": "Dessiner une Zone d'Intérêt",
    "upload_geometry": "Téléverser une Géométrie",
    "geometry_loaded": "Géométrie chargée",

    # Export
    "export_as_csv": "Exporter en CSV",
    "export_as_pdf": "Exporter en PDF",
    "export_as_zip": "Exporter en ZIP",
    "exporting": "Exportation en cours...",
    "export_complete": "Exportation terminée",
    "export_analysis": "Exporter l'Analyse",

    # MapBiomas specific
    "mapbiomas_no_data": "Aucune donnée disponible pour la zone sélectionnée",
    "mapbiomas_process_error": "Erreur lors du traitement de la classe {class_id} : {error}",
    "mapbiomas_analysis_title": "Analyse de la Couverture Terrestre MapBiomas",
    "mapbiomas_year_range": "Plage d'années : {start} - {end}",

    # Hansen specific
    "hansen_tree_cover": "Couvert Forestier",
    "hansen_tree_loss": "Perte Forestière",
    "hansen_tree_gain": "Gain Forestier",
    "hansen_no_data": "Aucune donnée Hansen pour la zone sélectionnée",

    # Settings / Quick settings
    "language": "Langue",
    "theme": "Thème",
    "dark_mode": "Mode Sombre",
    "light_mode": "Mode Clair",

    # Help & Info
    "help": "Aide",
    "documentation": "Documentation",
    "about": "À propos de Yvynation",
    "version": "Version",
    "powered_by": "Propulsé par",

    # =====================================================================
    # Tutorial / Getting Started
    # =====================================================================
    "getting_started_header": "Comment Utiliser Cette Plateforme",
    "getting_started_title": "Premiers Pas",
    "getting_started_intro": "Cette plateforme permet une analyse complète de la couverture terrestre pour le Brésil et une surveillance forestière mondiale. Vous pouvez analyser des zones personnalisées, des territoires autochtones et des zones tampons externes.",

    "step_language_region": "Étape 0 : Choix de la Langue et de la Région",
    "step0_language_region_intro": "Configurez votre langue et sélectionnez votre région d'intérêt :",
    "step0_content": """**Détection Automatique à la Première Visite**

Lors de votre première visite, l'application peut détecter votre position pour définir la bonne région :
- **Amérique du Nord** (latitude > 10N) -> Définit le Canada
- **Amérique du Sud** -> Utilise la langue du navigateur ou le portugais (PT)
- Vous pouvez revoir ou modifier ce réglage à tout moment

**Choix Manuel de la Langue**

Utilisez les boutons de langue (EN / PT / ES / FR) dans la barre latérale. Votre choix est conservé pour votre session.

**Choix Manuel de la Région**

Utilisez les boutons de région (Brésil / Canada) dans la barre latérale :
- **Brésil** : Couverture complète MapBiomas (1985-2024) + données mondiales Hansen/GLAD
- **Canada** : Inventaire des cultures AAFC + données mondiales Hansen/GLAD

La carte sera centrée sur la région sélectionnée.""",

    "step_custom_polygon": "Étape 1 : Analyser un Polygone Personnalisé",
    "step1_draw_intro": "Dessinez et analysez n'importe quelle zone sur la carte :",
    "step1_content": """1. **Outils de Dessin** (coin supérieur gauche de la carte) :
   - Cliquez sur **Rectangle** pour des sélections rectangulaires rapides
   - Cliquez sur **Polygone** pour des formes personnalisées
   - Double-cliquez ou cliquez sur le premier point pour terminer

2. **Sélectionnez les Couches de Données** (barre latérale) :
   - **MapBiomas** : couverture terrestre du Brésil (1985-2024, 62 classes, 30 m)
   - **Hansen/GLAD** : changements forestiers mondiaux (2000-2020, 256 classes, 30 m)
   - **Hansen GFC** : changement forestier mondial (2000-2024, 30 m)

3. **Résultats de l'Analyse** : distribution, statistiques de superficie, graphiques, CSV téléchargeables

4. **Analyse de Zone Tampon** : créez des zones tampons de 2, 5 ou 10 km autour des polygones""",

    "step_territory": "Étape 2 : Analyser un Territoire Autochtone",
    "step2_territory_intro": "Limites prédéfinies des territoires autochtones avec analyse historique :",
    "step2_content": """1. **Sélectionner un Territoire** (section Analyse de Territoire) :
   - Recherchez parmi 400+ terres autochtones reconnues
   - Consultez les métadonnées : superficie, localisation, statut

2. **Fonctionnalités de l'Analyse** : changements historiques (1985-2024), diagrammes de Sankey, exportation

3. **Zone Tampon** : créez des zones externes, comparez l'usage des terres à l'intérieur et à l'extérieur""",

    "step_comparison": "Étape 3 : Comparaison Multi-Années",
    "step3_comparison_intro": "Comparez les changements de couverture entre deux années :",
    "step3_content": """Sélectionnez 2+ années, dessinez un polygone ou choisissez un territoire, puis comparez avec des tableaux côte à côte, des graphiques de gains/pertes et des diagrammes de Sankey.""",

    "step_export": "Étape 4 : Exporter et Télécharger les Résultats",
    "step4_export_intro": "Enregistrez vos résultats pour vos rapports :",
    "step4_content": """Téléchargements CSV, exports PNG et rapports PDF (à venir).""",

    "step_map_controls": "Étape 5 : Contrôles de la Carte",
    "step5_map_controls_intro": "Naviguez et interagissez avec la carte :",
    "step5_content": """Zoom, déplacement, outils de dessin, contrôles des couches et superpositions de territoires.""",

    "step_data_understanding": "Étape 6 : Comprendre les Données",
    "step6_data_understanding_intro": "Sources de données et interprétation des résultats :",
    "step6_content": """MapBiomas Collection 10 (Brésil, 1985-2024, 30 m, 62 classes). Hansen/GLAD (mondial, 30 m, 256 classes). Superficie en hectares, pixels de 900 m2, changements positifs/négatifs.""",

    # About section
    "about_title": "À propos",
    "about_overview": "Aperçu du Projet",
    "about_desc": "Cet outil d'analyse de l'usage et de la couverture des terres fait partie d'un projet de recherche qui étudie les changements environnementaux dans les Territoires Autochtones Brésiliens à l'aide de Google Earth Engine et des données MapBiomas. Ces données sont comparées aux changements de politiques et aux tendances de déforestation pour comprendre les impacts sur ces terres essentielles.",
    "about_author": "Leandro Meneguelli Biondo",
    "about_role": "Doctorant en Durabilité",
    "about_university": "IGS/UBCO",
    "about_supervisor": "Directeur : Dr. Jon Corbett",
    "about_app_name": "Yvynation",
    "about_app_note": "est un nom pour cette application, ce n'est pas le contenu complet du projet.",
    "yvynation_meaning": "« Yvy » (tupi-guarani) signifie terre, sol ou territoire — soulignant le sol que nous foulons et notre lien sacré avec la nature. Ce mot se rattache souvent au concept de « Yvy marae'y » (Terre sans mal).",
    "nation_meaning": "« Nation » désigne une communauté autonome ou un peuple partageant culture, histoire, langue et terre. Il évoque l'autodétermination et la gouvernance.",
    "data_sources_title": "Sources de Données",
    "mapbiomas_desc": "MapBiomas Collection 10 - Résolution : 30 m, Période : 1985-2024 (annuel), 62 catégories de couverture, CC BY 4.0",
    "territories_desc": "700+ territoires brésiliens avec limites vectorielles et attributs - Projet Territoires MapBiomas",
    "features_title": "Fonctionnalités",
    "tech_title": "Technologies",

    # Layer Reference Guide
    "layer_reference": "Guide de Référence des Couches",
    "indigenous_territories_label": "Territoires Autochtones",
    "selected_territory_label": "Territoire Sélectionné",
    "drawn_polygon_label": "Polygone Dessiné",
    "buffer_zone_label": "Zone Tampon Externe",
    "mapbiomas_legend": "Classes de Couverture MapBiomas",
    "hansen_legend": "Classes de Couverture Hansen/GLAD",
    "gfc_legend": "Hansen Global Forest Change (UMD 2024)",
    "aafc_legend": "Inventaire Annuel des Cultures AAFC (Canada)",

    # Polygon analysis
    "polygon_analysis_header": "Analyse de Polygone et Statistiques",
    "draw_polygon_instruction": "Dessinez un polygone sur la carte pour commencer à analyser la couverture terrestre de cette zone. Utilisez les outils de dessin dans le coin supérieur gauche de la carte.",

    # Portal page
    "about_section": "À propos de Yvynation",
    "about_description": "Yvynation est une plateforme complète de surveillance et d'analyse des terres autochtones. Elle combine imagerie satellitaire, outils d'analyse géospatiale et détection des changements forestiers pour éclairer les changements d'usage des terres et la dynamique des écosystèmes.",

    # Sidebar sections
    "geometry_tools": "Outils de Géométrie",
    "geometry_section": "Géométrie et Dessin",
    "buffer_controls": "Contrôles de Zone Tampon",
    "analysis_settings": "Paramètres d'Analyse",
    "territory_selection": "Sélection de Territoire",
    "comparison_controls": "Contrôles de Comparaison",

    # Form inputs
    "enter_distance": "Saisissez la distance",
    "territory_search": "Rechercher un Territoire",
    "search_territory": "Recherchez un territoire par nom...",
    "country": "Pays",
    "territory_type": "Type de Territoire",
    "indigenous_lands_btn": "🪶 Autochtones",
    "conservation_units_btn": "🌿 Conservation",

    # Other
    "no_results": "Aucun résultat trouvé",
    "remove": "Retirer",
    "aafc_section_title": "Couches AAFC (Canada)",

    # =====================================================================
    # Analysis navbar / main content (index.py)
    # =====================================================================
    "nav_hide": "☰ Masquer",
    "nav_show": "☰ Afficher",
    "sidebar_narrow": "Étroite",
    "sidebar_normal": "Normale",
    "sidebar_wide": "Large",
    "geometry_analysis_label": "🔷 Analyse de Géométrie",
    "territory_analysis_label": "🗺️ Analyse de Territoire",
    "back_to_portal": "← Retour au Portail",
    "back_to_batch": "← Retour au Lot",
    "clear_btn": "🔄 Effacer",
    "clear_btn_title": "Effacer toutes les données d'analyse et recommencer",
    "active_analysis_area": "Zone d'analyse active",
    "no_areas_yet": "Aucune zone pour l'instant — sélectionnez un territoire ou dessinez-en une",
    "run_all_analysis": "▶ Lancer toutes les analyses",
    "bundling": "Assemblage…",
    "download_all": "⬇️ Tout télécharger",
    "results_label": "📊 Résultats",
    "full_results": "⛶ Résultats en plein écran",
    "exit_full_results": "⛶ Quitter le plein écran",
    "toggle_full_results_title": "Basculer les résultats en plein écran",

    # =====================================================================
    # Portal page (portal.py)
    # =====================================================================
    "portal_ds_mapbiomas": "MapBiomas : couverture terrestre du Brésil (1985-2024, résolution 30 m)",
    "portal_ds_hansen": "Hansen/GFC : détection mondiale des changements forestiers",
    "portal_ds_aafc": "AAFC : classification agricole et forestière du Canada",
    "portal_ds_gee": "Google Earth Engine : analyse géospatiale infonuagique",
    "portal_ds_custom": "Géométries personnalisées : dessinez ou téléversez vos propres entités",
    "portal_choose_title": "🚀 Choisissez Votre Parcours d'Analyse",
    "portal_choose_desc": "Sélectionnez le type d'analyse qui convient le mieux à votre flux de travail. Les deux parcours donnent accès aux mêmes outils et jeux de données.",
    "portal_geometry_sub": "Dessinez et analysez des zones personnalisées",
    "portal_geometry_i1": "Dessinez des polygones sur la carte",
    "portal_geometry_i2": "Téléversez des GeoJSON/Shapefiles/KML",
    "portal_geometry_i3": "Créez des zones tampons",
    "portal_geometry_i4": "Analysez les changements de couverture terrestre",
    "portal_geometry_btn": "→ Démarrer l'Analyse de Géométrie",
    "portal_territory_sub": "Surveillez les terres autochtones",
    "portal_territory_i1": "Choisissez parmi 700+ territoires",
    "portal_territory_i2": "Recherchez par nom",
    "portal_territory_i3": "Suivez les changements forestiers (1985-2024)",
    "portal_territory_i4": "Comparez plusieurs années",
    "portal_territory_btn": "→ Démarrer l'Analyse de Territoire",
    "portal_batch_sub": "Traitez plusieurs territoires à la fois",
    "portal_batch_i1": "Sélectionnez autant de territoires que voulu",
    "portal_batch_i2": "Exécutez MapBiomas, Hansen GLAD et GFC",
    "portal_batch_i3": "Territoire + zone tampon automatiquement",
    "portal_batch_i4": "Téléchargez un seul ZIP avec toutes les données",
    "portal_batch_btn": "→ Démarrer le Traitement par Lots",
    "portal_resources": "📚 Ressources",
    "portal_footer_data": "Données",
    "portal_footer_contact": "Contact",
    "portal_show": "(afficher)",
    "portal_hide": "(masquer)",
    "portal_link_methods": "Méthodes et Recherche",
    "portal_support": "🎓 Soutien",
    "portal_link_tutorial": "Tutoriel et Guide",
    "portal_link_faq": "FAQ",
    "portal_link_contact": "Contact et Commentaires",
    "portal_link_team": "Équipe et Collaborateurs",
    "portal_link_cite": "Comment Citer",

    # =====================================================================
    # Citation et remerciements (components/citation.py)
    # =====================================================================
    "citation_title": "Comment Citer et Remerciements",
    "citation_mission": "Yvynation fournit des données géospatiales, des graphiques et des figures en libre accès pour soutenir les communautés et les gestionnaires de Terres Indigènes et d'Unités de Conservation, ainsi que des chiffres et tableaux fiables pour les chercheurs et les journalistes.",
    "citation_acknowledgment_title": "Remerciements",
    "citation_acknowledgment_text": "Le traitement géospatial de cette plateforme s'exécute sur Google Earth Engine, dans le cadre du projet ProtectedLandsYvynation-EE, enregistré pour un usage de recherche non commercial. L'infrastructure cloud est soutenue par des crédits Google Cloud Research Credits.",
    "citation_ack_people": "Remerciements à Jon Corbett (directeur de thèse) et au comité doctoral — Jonathan Cinnamon, Robert Friberg et Tim Paulson — pour leurs conseils sur le cadre; à Pedro de Almeida Salles, qui a codéveloppé le corpus chronologique de la politique forestière brésilienne; à Alexander Biondo, Gabriel Silva Santos, Clayton Borges, Bernardo Trovão et Aparicio Biondo pour les idées, les discussions et les tests à l'origine du pipeline et de la conception de Yvynation; et aux équipes MapBiomas et Hansen/GLAD pour leurs produits ouverts d'occupation du sol.",
    "citation_ack_compute": "Le calcul est soutenu par le programme Google Cloud Research Credits (projet Earth Engine ee-leandromet). Les échanges avec l'équipe du Registre environnemental rural brésilien (ministère de la Gestion et de l'Innovation dans les services publics), les équipes Earth Engine et Google Brésil, MapBiomas et Imazon — sur l'acquisition et la diffusion des images SPOT de 2008 utilisées pour l'analyse des propriétés rurales sous le Code forestier de 2012 — ont façonné ce travail. L'Institut national de la forêt atlantique (ministère brésilien de la Technologie et de l'Innovation) et le Service forestier brésilien (ministère brésilien du Changement climatique et de l'Environnement) ont autorisé le congé sabbatique pour ces études supérieures.",
    "citation_ack_funding": "Le soutien financier provient d'Environment and Climate Change Canada (ECCC), par le Climate Action and Awareness Fund (CAAF), incluant un assistanat de recherche dans l'initiative UBCO Transportation and Climate Action Research, menée par le UBC Integrated Transportation Research (UiTR) Laboratory au campus Okanagan. Le soutien académique, social et intellectuel provient du UBCO Interdisciplinary Graduate Studies (IGS) – Sustainability Theme et de l'Institute for Community Engaged Research (ICER).",
    "citation_ack_summary": "Données ouvertes d'occupation du sol de MapBiomas et Hansen/GLAD, traitées sur Google Earth Engine avec Google Cloud Research Credits. Soutien à la recherche d'ECCC/CAAF et de UBC Okanagan — remerciements complets sous « Comment Citer ».",
    "license_summary": "Les données et figures générées dans Yvynation sont d'usage public, ouvert et gratuit, sous réserve d'attribution.",
    "license_title": "Licence",
    "citation_howto_title": "Citation suggérée",
    "citation_platform_text": "Biondo, L. M. (2026). Yvynation : une plateforme de surveillance géospatiale des Terres Indigènes et des Unités de Conservation [Logiciel]. Interdisciplinary Graduate Studies – Sustainability Theme (IGS), UBC Okanagan. Données traitées via Google Earth Engine (projet ProtectedLandsYvynation-EE).",
    "citation_datasets_title": "Veuillez également citer les sources de données utilisées :",
    "citation_ds_mapbiomas": "Projet MapBiomas — Collection 10 de la série de cartes d'occupation du sol du Brésil, mapbiomas.org",
    "citation_ds_hansen": "Hansen, M.C. et al. (2013). High-Resolution Global Maps of 21st-Century Forest Cover Change. Science. (Global Forest Change / GLAD, UMD)",
    "citation_ds_aafc": "Agriculture et Agroalimentaire Canada (AAFC) — Inventaire annuel des cultures",
    "citation_ds_gee": "Gorelick, N. et al. (2017). Google Earth Engine: Planetary-scale geospatial analysis for everyone. Remote Sensing of Environment.",
    "citation_hide": "Masquer",

    # =====================================================================
    # Batch processing page (batch_processing.py)
    # =====================================================================
    "batch_title": "🔶 Traitement par Lots",
    "batch_nav_subtitle": "Exécutez l'analyse complète sur plusieurs territoires — téléchargez un seul ZIP",
    "batch_select_territories": "🗺️ Sélectionner les Territoires",
    "batch_selected_suffix": " sélectionné(s)",
    "batch_indigenous_btn": "🪶 Autochtones",
    "batch_conservation_btn": "🌿 Unités de Conservation",
    "batch_search_placeholder": "🔍 Rechercher des territoires…",
    "batch_select_all_filtered": "Sélectionner tous les filtrés",
    "batch_shown_suffix": " affiché(s)",
    "batch_area_filter_label": "Superficie :",
    "batch_min_ha_placeholder": "Min",
    "batch_max_ha_placeholder": "Max",
    "batch_ha_suffix": "ha",
    "batch_filter_uf_label": "État (UF)",
    "batch_filter_fase_label": "Phase",
    "batch_filter_modalidade_label": "Modalité",
    "batch_filter_categoria_label": "Catégorie",
    "batch_filter_esfera_label": "Juridiction",
    "batch_filter_grupo_label": "Groupe",
    "batch_clear_filters": "Effacer les filtres",
    "batch_sort_label": "Trier",
    "batch_sort_name_asc": "Nom A–Z",
    "batch_sort_name_desc": "Nom Z–A",
    "batch_sort_area_asc": "Superficie : plus petite d'abord",
    "batch_sort_area_desc": "Superficie : plus grande d'abord",
    "batch_review_btn": "Réviser",
    "batch_review_title": "Territoires Sélectionnés",
    "batch_review_close": "Fermer",
    "batch_review_empty": "Aucun territoire sélectionné pour l'instant.",
    "batch_paste_instruction": "📋 Collez une liste de noms (un par ligne) ou téléversez un .txt/.csv pour les sélectionner automatiquement :",
    "batch_select_from_list": "✓ Sélectionner depuis la liste",
    "batch_upload_list": "📁 Téléverser une liste",
    "batch_clear": "Effacer",
    "batch_not_found_prefix": "⚠ Introuvables : ",
    "batch_configuration": "⚙️ Configuration",
    "batch_year1_label": "Année unique (initiale)",
    "batch_year2_label": "Année finale de la comparaison",
    "batch_hansen_year_label": "Année Hansen GLAD",
    "batch_analysis_types": "Types d'analyse",
    "batch_chk_mapbiomas": "🌿 MapBiomas année unique",
    "batch_chk_comparison": "📊 Comparaison d'une année à l'autre",
    "batch_chk_treemap": "🟦 Treemaps de transition de classes (par classe + Autres)",
    "batch_treemap_hint": "Ajoute un treemap à facettes (un par classe, les classes mineures regroupées dans « Autres ») partout où des transitions sont produites — la comparaison d'années et chaque étape multi-fenêtres.",
    "batch_chk_glad": "🌲 Couvert forestier Hansen GLAD",
    "batch_chk_gfc": "🪓 Hansen GFC (perte / gain)",
    "batch_chk_pdf_maps": "🗺️ Cartes PNG et Graphiques (satellite + MapBiomas année1/année2)",
    "batch_aux_rasters_label": "Rasters MapBiomas supplémentaires (année 2)",
    "batch_aux_deforestation": "🌳 Déforestation et végétation secondaire",
    "batch_aux_fire_scar": "🔥 Superficie brûlée annuelle (taille de la cicatrice)",
    "batch_aux_fire_frequency": "📊 Fréquence des feux (période complète 1985–2024)",
    "batch_aux_fire_year_last": "📅 Année du dernier feu",
    "batch_aux_mining": "⛏️ Substances minières",
    "batch_aux_agriculture": "🌾 Agriculture — nombre de cycles",
    "batch_chk_multi_window": "🌀 MapBiomas en fenêtres temporelles multiples (Sankey + Sunburst + Treemaps)",
    "batch_mw_mode": "Mode :",
    "batch_mw_step": "Pas (années) :",
    "batch_mw_forced_note": "1985 → 2024 imposé comme dernière année",
    "batch_mw_custom_label": "Années personnalisées (3 ou 4, séparées par des virgules, 1985–2024)",
    "batch_mw_active_years": "Années actives : ",
    "batch_chk_timeline": "📈 Chronologie de la déforestation (Hansen + MapBiomas + Feux) avec contexte politique",
    "batch_buffer_zone": "Zone tampon",
    "batch_include_buffer": "Inclure l'analyse de la zone tampon",
    "batch_km_ring": "km d'anneau externe",
    "batch_progress": "📊 Progression",
    "batch_territory_label": "Territoire :",
    "batch_step_label": "Étape :",
    "batch_in_flight_label": "En cours :",
    "batch_done_label": "Terminé :",
    "batch_complete_label": "— terminé —",
    "batch_errors_suffix": " erreur(s))",
    "batch_processing_log": "Journal de traitement",
    "batch_about_title": "📖 À propos du Traitement par Lots",
    "batch_about_text": "Exécutez le pipeline complet d'analyse Yvynation (couverture terrestre MapBiomas, changement d'une année à l'autre, couvert forestier Hansen GLAD et perte/gain Hansen GFC) sur de nombreux territoires en une seule exécution sans surveillance. Prend en charge les territoires autochtones FUNAI (657) et les unités de conservation CNUC (3 247). Chaque territoire — et sa zone tampon externe optionnelle — est traité via Google Earth Engine et regroupé dans une seule archive ZIP contenant des tableaux CSV, des matrices de transition et des figures (HTML + PNG) par territoire.",
    "batch_time_note": "Comptez de 2 à 10 minutes par territoire selon les analyses activées. L'onglet peut rester ouvert en arrière-plan.",
    "batch_howto": "Mode d'emploi",
    "batch_howto_1_title": "Sélectionnez les territoires",
    "batch_howto_1_body": "Choisissez le type de source (Autochtones ou Unités de Conservation), utilisez la recherche pour filtrer et cochez les territoires à inclure. « Sélectionner tous les filtrés » ajoute chaque correspondance de la recherche en cours ; « Tout effacer » repart de zéro. Changer de type efface la sélection en cours.",
    "batch_howto_2_title": "Choisissez les années MapBiomas",
    "batch_howto_2_body": "Définissez l'année initiale (instantané unique) et l'année finale (pour la comparaison d'une année à l'autre). Plage : 1985–2024.",
    "batch_howto_3_title": "Choisissez l'année Hansen GLAD",
    "batch_howto_3_body": "Année de référence (2000/2005/2010/2015/2020) utilisée pour l'instantané du couvert forestier Hansen GLAD.",
    "batch_howto_4_title": "Choisissez les types d'analyse",
    "batch_howto_4_body": "Activez toute combinaison de MapBiomas année unique, comparaison d'une année à l'autre, Hansen GLAD et perte/gain Hansen GFC.",
    "batch_howto_5_title": "Zone tampon optionnelle",
    "batch_howto_5_body": "Activez pour analyser aussi un anneau externe (10 km par défaut) autour de chaque territoire. Les sorties de la zone tampon sont écrites dans buffer/{territory}_Buffer_{km}km/ à l'intérieur du ZIP.",
    "batch_howto_6_title": "Lancez le lot",
    "batch_howto_6_body": "Cliquez sur « Démarrer le Traitement par Lots ». Le panneau de configuration est remplacé par la vue de progression en direct ; vous pouvez arrêter après le territoire en cours à tout moment.",
    "batch_howto_7_title": "Téléchargez le ZIP",
    "batch_howto_7_body": "À la fin de l'exécution, cliquez sur « Télécharger le ZIP » pour récupérer tous les tableaux, transitions et figures de chaque territoire dans une seule archive.",
    "batch_start_btn": "🚀 Démarrer le Traitement par Lots",
    "territories_word": "territoires",
    "batch_large_run_warning": "Sélection importante — envisagez de la diviser en plusieurs exécutions plus petites (ex. 20-25 territoires chacune) pour rester fiable. En cas d'interruption, les résultats partiels restent disponibles sur la page Exécutions Précédentes.",
    "batch_processing_ellipsis": "Traitement…",
    "batch_stop_btn": "⏹ Arrêter après le territoire en cours",
    "batch_download_zip": "⬇️ Télécharger le ZIP",
    "batch_new_batch": "🔄 Nouveau Lot",
    "batch_territories_selected_suffix": " territoires sélectionnés",
    "batch_no_territories": "Aucun territoire sélectionné",

    # =====================================================================
    # Page Exécutions Précédentes (previous_runs.py)
    # =====================================================================
    "previous_runs_title": "Exécutions Précédentes",
    "previous_runs_subtitle": "Récupérez les exports par lots terminés ou interrompus",
    "previous_runs_intro": "Chaque exécution par lots/export apparaît ici, y compris celles interrompues par un plantage ou un arrêt — rien n'est supprimé tant que vous ne l'avez pas téléchargé ou supprimé vous-même.",
    "previous_runs_refresh": "Actualiser",
    "previous_runs_status_zip": "✅ Terminée",
    "previous_runs_status_partial": "⚠ Partielle — récupérable",
    "previous_runs_download": "Télécharger",
    "previous_runs_zip_download": "Compresser et Télécharger",
    "previous_runs_zipping": "Compression…",
    "previous_runs_delete": "Supprimer",
    "previous_runs_copy": "Copier",
    "previous_runs_bucket_section": "Lien direct du bucket",
    "previous_runs_bucket_hint": "À copier dans gcloud/gsutil ou la console Cloud. Le bouton Télécharger ci-dessus n'utilise pas ces liens.",
    "previous_runs_detail_config": "Configuration de l'exécution",
    "previous_runs_detail_territories": "Territoires",
    "previous_runs_detail_performance": "Performance",
    "previous_runs_detail_loading": "Lecture des détails de l'exécution…",
    "previous_runs_files_suffix": "fichiers",
    "previous_runs_empty": "Aucune exécution précédente pour l'instant — les téléchargements de lots/exports apparaîtront ici.",
}
