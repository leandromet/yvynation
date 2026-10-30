"""French text for the Canada page.

Canada is officially bilingual, and the AAFC and NTEMS products publish their
own French legends — this table follows their vocabulary (*aire protégée*,
*Agriculture et Agroalimentaire Canada*, *Inventaire annuel des cultures*) and
Canadian French usage. Keys that are never shown are not translated; any key
missing here falls back to English, never to a blank (see ``__init__``).

Coverage and placeholder parity with English are checked by
``tests/test_place_search.py``.
"""

from __future__ import annotations

TRANSLATIONS_FR: dict[str, str] = {
    # --- shell -----------------------------------------------------------------
    "app_name": "Yvynation Canada — aires protégées",
    "go_to_brazil": "Brésil",
    "language_label": "Langue",
    "start_hint": "Cliquez n'importe où au Canada pour commencer",
    "sidebar_show_aria": "Afficher le panneau latéral",
    "sidebar_hide_aria": "Masquer le panneau latéral",
    "sheet_handle_aria": "Redimensionner le panneau — glissez ou utilisez les flèches",
    "results_resize_aria": "Redimensionner le panneau des résultats",
    "results_resize_label": "Redimensionner",
    "results_resize_hint": "Fait passer la hauteur du panneau de compacte à moyenne puis étendue.",
    "mobile_options_toggle": "Options de recherche",
    "mobile_layers_group_toggle": "Couches",
    "mobile_panel_toggle": "Données et options",
    "mobile_parcel_zones_toggle": "Aire et zones",
    "close_button": "Fermer",
    "calcular": "Calculer",
    "calculando": "Calcul en cours…",

    # --- search ------------------------------------------------------------------
    "search_title": "Recherche",
    "search_placeholder": "nom d'aire protégée, adresse, code postal, coordonnées…",
    "search_read_as": "lu comme :",
    "search_button": "Rechercher",
    "search_button_busy": "Recherche…",
    "search_areas_heading": "Aires protégées",
    "search_places_heading": "Lieux et adresses",
    "search_places_note": "Un lieu ne fait que cadrer la carte et poser un repère. "
        "Cliquez sur une aire protégée (contour vert-bleu) pour l'analyser.",
    "echo_coordenada": "coordonnées",
    "echo_lugar": "lieu",
    "echo_postal": "code postal",
    "echo_area_cpcad": "aire protégée",
    "search_place_hint": "cliquez sur une aire protégée sur la carte pour l'analyser",
    "precision_endereco": "adresse",
    "precision_rua": "rue",
    "precision_cep": "code postal",
    "precision_bairro": "quartier",
    "precision_cidade": "ville",
    "precision_regiao": "région",
    "precision_lugar": "lieu",

    # --- quick start ---------------------------------------------------------------
    "qs_step1_lead": "Trouvez une aire protégée",
    "qs_step1_body": "par son nom, une adresse, un code postal ou des coordonnées — "
        "ou cliquez sur un contour vert-bleu de la carte. La Colombie-Britannique "
        "se charge d'abord; les autres provinces se chargent quand vous y allez.",
    "qs_step2_lead": "Lisez les onglets :",
    "qs_step2_body": "les cultures (AAC) et l'occupation du sol depuis 1984 se "
        "chargent seules; Forêt, Biomasse, Paysage et Feux s'exécutent sur demande.",
    "qs_step3_lead": "Comparez les zones",
    "qs_step3_body": "— l'aire elle-même et des anneaux à 500 m, 2 km et 5 km — "
        "pour voir l'intérieur par rapport aux alentours.",
    "qs_step4_lead": "Choisissez des parties :",
    "qs_step4_body": "une aire formée de polygones séparés peut être analysée "
        "partie par partie depuis le panneau latéral.",
    "help_show_quickstart": "Revoir le démarrage rapide",

    # --- area card -------------------------------------------------------------------
    "zones_title": "Zones",
    "zones_note": "L'aire protégée et des anneaux mesurés vers l'extérieur à partir "
        "de sa limite — comparez l'intérieur avec les alentours.",
    "zona_park": "Aire protégée",
    "park_name": "Nom",
    "park_designation": "Désignation",
    "park_iucn_category": "Catégorie de l'UICN",
    "park_status": "Statut",
    "park_status_year": "Statut depuis",
    "park_managing_authority": "Autorité de gestion",
    "park_area_reported": "Superficie déclarée (BDCAPC)",
    "park_area_calculated": "Superficie calculée (géométrie)",
    "park_area_disagreement_prefix": "La superficie déclarée et la superficie géométrique diffèrent de",
    "park_area_disagreement_suffix": "Les deux sont présentées telles que déclarées.",
    "coord_clicked": "Point cliqué",
    "coord_centroid": "Centroïde",

    # --- layers and legend ---------------------------------------------------------------
    "layers_title": "Fond de carte",
    "layers_loading": "Chargement…",
    "layers_landsat_hint": "Composite annuel — choisissez l'année ci-dessous.",
    "layers_ecozones": "Cadre écologique",
    "layers_ecozone_level_ecozone": "Écozone",
    "layers_ecozone_level_ecoregion": "Écorégion",
    "layers_ecozone_level_ecodistrict": "Écodistrict",
    "layers_ecozones_note": "À titre indicatif seulement — les limites sont approximatives "
        "et ne décident de rien. Les écozones sont larges (quinze couvrent tout le "
        "Canada); l'écorégion et l'écodistrict sont des niveaux plus fins du même "
        "cadre — l'écodistrict n'a pas de nom propre, seulement l'écorégion et "
        "l'écozone qui le contiennent.",
    "legend_title": "Légende",
    "legend_collapse_aria": "Réduire la légende",
    "legend_expand_aria": "Agrandir la légende",
    "legend_aci": "Inventaire des cultures d'AAC",
    "legend_aci_palette": "Couleurs officielles de la légende d'AAC.",
    "legend_run_calcular": "Cliquez sur Calculer dans l'onglet Validation pour voir les classes.",
    "legend_landsat": "Composite Landsat",
    "legend_landsat_error": "Impossible de charger le composite Landsat de cette année.",
    "legend_floresta_hansen": "Changement du couvert forestier (Hansen)",
    "legend_hansen_split_start_date": "Divisé à l'année de création",
    "legend_hansen_split_undivided": "Série non divisée",
    "legend_perda": "Perte",
    "legend_ganho": "Gain (non daté)",
    "legend_choose_years": "Choisissez les années dans l'onglet Transitions.",
    "legend_drag_to_compare": "Faites glisser la barre sur la carte pour comparer.",
    "map_layer_note": "La couche cartographique de cet onglet peut être activée ou "
        "désactivée depuis la légende, dans le coin de la carte.",

    # --- cover (AAFC) ----------------------------------------------------------------------------
    "tab_cobertura": "Cultures (AAC)",
    "cobertura_ano": "Année",
    "cobertura_classe": "Classe",
    "cobertura_hectares": "Hectares",
    "cobertura_percentual": "Pourcentage",
    "cobertura_running": "Récupération de l'évolution de l'inventaire des cultures…",
    "cobertura_empty": "Aucune donnée pour l'instant — sélectionnez une aire protégée.",
    "cobertura_degraded": "Ce résultat a été recalculé à une échelle plus grossière "
        "après un échec d'Earth Engine. Il est utilisable, mais consultez la fiche de "
        "provenance pour savoir ce qui a changé.",
    "cobertura_out_of_range": "L'inventaire des cultures d'AAC ne couvre pas cette "
        "latitude — attendu au-delà d'environ 54–58° N, ce n'est pas une panne. Les "
        "onglets Occupation du sol, Forêt, Biomasse et Feux répondent toujours.",
    "cobertura_attribution": "Agriculture et Agroalimentaire Canada — Inventaire annuel des cultures · 30 m",

    # --- transitions --------------------------------------------------------------------------------
    "tab_transicoes": "Transitions",
    "transicoes_intro": "Comment l'occupation du sol a changé entre deux années, pour la zone active.",
    "transicoes_de": "De",
    "transicoes_para": "Vers",
    "transicoes_maiores": "Principales transitions",
    "transicoes_min_gap_note_prefix": "Les années distantes de moins de",
    "transicoes_min_gap_note_suffix": "sont refusées — entre années consécutives, la "
        "plupart des « transitions » de l'inventaire sont des rotations de cultures, "
        "pas un changement d'usage du sol.",

    # --- forest ---------------------------------------------------------------------------------------
    "tab_floresta": "Forêt",
    "floresta_split_start_date": "Divisé à l'année de création",
    "floresta_split_undivided": "Non divisé",
    "floresta_before_parcel": "Avant la création",
    "floresta_after_parcel": "Après la création",
    "floresta_undivided_total": "Perte totale (non divisée)",
    "floresta_ganho_sem_data": "Gain (non daté)",
    "floresta_no_start_date_note": "La BDCAPC n'enregistre aucune année de création pour "
        "cette aire; la perte est donc présentée en une seule série non divisée plutôt "
        "que coupée à une date inventée.",
    "floresta_col_ano": "Année",
    "floresta_col_perda": "Perte (ha)",
    "floresta_col_periodo": "Période",
    "floresta_attribution": "Hansen/UMD/Google/USGS/NASA — Global Forest Change · 30 m",
    "floresta_age_title": "Âge des peuplements (SNSTE, 2019)",
    "floresta_age_run_button": "Obtenir l'âge des peuplements",
    "floresta_age_mean": "Âge moyen",
    "floresta_age_median": "Âge médian",
    "floresta_age_unit": "ans",
    "floresta_age_forested_pct": "Part boisée de la zone",
    "floresta_age_note": "Les âges sont ceux publiés, en date de 2019 — non projetés "
        "à aujourd'hui. Limités aux pixels boisés : une faible part boisée signifie "
        "que les âges ne décrivent qu'une petite partie de cette zone.",
    "floresta_age_attribution": "RNCan / SNIF — SNSTE, âge des forêts du Canada (2019) · 30 m",
    "tab_biomassa": "Biomasse",
    "biomassa_col_ano": "Année",
    "biomassa_col_mg_ha": "Mg/ha",
    "biomassa_col_total_mg": "Total (Mg)",
    "biomassa_attribution": "ESA CCI Biomass v6.0 — Santoro et Cartus (2025) · 100 m",
    "biomassa_canada_note": "L'estimation est plus faible sur les terrains à couverture "
        "de neige persistante et dans les boisés nordiques clairsemés que dans la forêt "
        "tempérée fermée.",
    "tab_paisagem": "Paysage",
    "paisagem_ano": "Année",
    "paisagem_empty": "Aucune donnée pour l'instant.",
    "paisagem_legend_note": "Le nombre de fragments suit les classes propres à "
        "l'inventaire des cultures, qui distinguent finement les cultures et grossièrement "
        "la forêt — comparable entre cette aire protégée et ses anneaux, pas entre un "
        "paysage agricole et un paysage forestier.",
    "paisagem_col_zona": "Zone",
    "paisagem_col_area": "Superficie (ha)",
    "paisagem_col_fragmentos": "Fragments",
    "paisagem_col_densidade": "Densité",
    "paisagem_col_maior": "Plus grand (%)",
    "paisagem_col_borda": "Densité de lisière",
    "paisagem_col_meff": "Meff (ha)",
    "paisagem_col_shannon": "Shannon",
    "paisagem_col_simpson": "Simpson",
    "paisagem_col_evenness": "Équitabilité",
    "paisagem_attribution": "Inventaire annuel des cultures d'AAC · 30 m",
    "connectivity_hint": "Distance moyenne entre les fragments forestiers — un second "
        "appel à Earth Engine plus une recherche locale, donc exécuté sur demande.",
    "connectivity_run_button": "Obtenir la distance entre fragments",
    "connectivity_degraded": "Plus de fragments que le plafond dans une zone ou plus — "
        "la distance ne tient compte que des premiers fragments retournés.",
    "connectivity_empty": "Aucun résultat pour l'instant.",
    "connectivity_n_fragments": "Fragments",
    "connectivity_enn_mean": "Distance moyenne (m)",
    "connectivity_enn_median": "Distance médiane (m)",

    # --- fire ---------------------------------------------------------------------------------------------
    "tab_fogo": "Feux",
    "fogo_historio_anos": "Années avec au moins un feu",
    "fogo_frequencia_ocorrencias": "Fréquence moyenne des feux",
    "fogo_ultima_queimada": "Dernière année de feu",
    "fogo_below_resolution_prefix": "Cette zone est plus petite qu'environ ",
    "fogo_below_resolution_suffix": " ha — les pixels MODIS font ~21 ha, de sorte que ces "
        "chiffres reflètent surtout des effets de bordure de pixel plutôt qu'une "
        "résolution de la zone.",
    "fogo_attribution": "MODIS MCD64A1 v6.1 Burned Area — NASA LP DAAC · 463 m",
    "fogo_current_year_prefix": "L'année ",
    "fogo_current_year_suffix": " est en cours — MODIS publie de nouveaux mois tout au long "
        "de l'année; cette barre (hachurée sur le graphique) est donc un cumul en cours, "
        "pas une saison terminée.",
    "fogo_source_modis": "MODIS · 500 m",
    "fogo_source_aci": "AAC · 30 m",
    "fogo_modis_layer_note_prefix": "La carte montre toutes les années enregistrées "
        "combinées (2001–",
    "fogo_modis_layer_note_suffix": ") — plus le rouge est foncé, plus la zone a brûlé "
        "souvent. La dernière année est en cours.",
    "fogo_aci_layer_note": "La carte montre toutes les années enregistrées combinées "
        "(2009–2025) — plus le rouge est foncé, plus la zone a brûlé souvent.",
    "fogo_aci_years_detected": "Années avec feu détecté",
    "fogo_aci_last_year": "Année brûlée la plus récente",
    "fogo_aci_empty": "Aucune donnée de l'onglet Cultures (AAC) pour cette zone — ouvrez "
        "cet onglet ou attendez la fin du chargement. La classe de superficie brûlée "
        "provient de cette même requête, sans coût supplémentaire.",
    "fogo_aci_note": "La classe de superficie brûlée de l'inventaire des cultures "
        "(2009–2025, national à partir de 2011), 30 m — sept fois plus fine que MODIS, "
        "mais une classe d'occupation du sol et non un produit dédié aux feux : elle peut "
        "manquer un feu que MODIS détecte si la cicatrice avait déjà reverdi lors du "
        "passage du satellite de cette année-là, comme elle peut résoudre la forme d'un "
        "feu que MODIS ne voit que comme une tache floue. Les deux ne sont jamais "
        "fusionnés en un seul chiffre.",
    "fogo_aci_attribution": "Agriculture et Agroalimentaire Canada — Inventaire annuel "
        "des cultures, classe 60 « Feu de forêt et superficie brûlée » · 30 m",

    # --- validation -----------------------------------------------------------------------------------------
    "tab_validacao": "Validation",
    "validacao_intro": "L'Inventaire annuel des cultures comparé à SNSTE VLCE2, un produit "
        "national indépendant d'occupation du sol, pour la même année. Comparaison à un "
        "niveau de groupes grossier seulement — voir la note ci-dessous.",
    "validacao_ano": "Année",
    "validacao_agreement_label": "Concordance au niveau des groupes",
    "validacao_area_label": "Superficie comparée",
    "validacao_no_verdict": "Le désaccord entre deux produits indépendants n'est pas une "
        "erreur de l'un ou l'autre — ceci indique où ils diffèrent et ne dit rien sur "
        "lequel a raison.",
    "validacao_group_note": "Comparé au niveau des groupes, non des classes : l'inventaire "
        "distingue les cultures sans détail sur les types de forêt, VLCE2 l'inverse. Un "
        "taux de concordance par classe n'aurait aucun sens.",
    "validacao_col_aci": "Groupe de l'inventaire",
    "validacao_col_vlce2": "Groupe VLCE2",
    "validacao_col_area": "Superficie (ha)",
    "validacao_col_agreement": "Concordance?",
    "validacao_attribution": "Inventaire annuel des cultures d'AAC · SNSTE VLCE2 "
        "(Hermosilla et al., Service canadien des forêts)",

    # --- errors -----------------------------------------------------------------------------------------------
    "erro_fora_canada": "Ce point est hors du Canada. Cette page couvre le Canada; "
        "utilisez la page du Brésil pour des coordonnées d'Amérique du Sud.",
    "erro_zonas": "Impossible de construire les zones : {detail}",
    "erro_camada_aba": "La couche cartographique de cet onglet n'a pas pu être chargée.",
    "erro_trajetoria_aci": "L'évolution de l'inventaire des cultures a échoué : {detail}",
    "erro_aci_sem_classes": "Aucune donnée de l'inventaire des cultures sur cette zone — "
        "attendu au nord de la couverture de l'inventaire.",
    "erro_lugar_nao_encontrado": "Aucun lieu trouvé pour « {query} ».",
    "erro_transicao": "Les transitions ont échoué : {detail}",
    "erro_perda_florestal": "Le changement du couvert forestier a échoué : {detail}",
    "erro_idade_floresta": "L'âge des peuplements a échoué : {detail}",
    "erro_biomassa": "La biomasse a échoué : {detail}",
    "erro_fogo": "L'analyse des superficies brûlées a échoué : {detail}",
    "erro_paisagem": "Les métriques du paysage ont échoué : {detail}",
    "erro_connectivity": "La connectivité entre fragments a échoué : {detail}",
    "erro_validacao": "La comparaison de validation a échoué : {detail}",

    # --- export / help / cite -----------------------------------------------------------------------------------
    "export_chart_aria": "Télécharger ce graphique",
    "export_chart_label": "Télécharger le graphique (PNG)",
    "export_table_aria": "Télécharger ce tableau",
    "export_table_label": "Télécharger le tableau (CSV)",
    "help_trigger": "Mode d'emploi",
    "help_dialog_title": "Comment utiliser Yvynation Canada",
    "help_demo_link": "Envie de le voir à l'œuvre ? Ouvrez la visite guidée du parc Okanagan Mountain (en anglais) →",
    "help_dialog_desc": "Sept étapes pour aller d'une aire protégée à une analyse, et "
        "ce que cette page ne peut pas dire.",
    "help_step1_title": "1. Trouvez une aire protégée",
    "help_step1_body": "Saisissez le nom d'une aire, une adresse, un code postal ou des "
        "coordonnées, ou cliquez sur un contour vert-bleu de la carte. Quand des "
        "désignations se chevauchent, vous choisissez laquelle. La Colombie-Britannique "
        "se charge d'abord; un clic ou une recherche dans une autre province ajoute "
        "cette province.",
    "help_step2_title": "2. Lisez la fiche de l'aire",
    "help_step2_body": "Les champs de la BDCAPC tels que publiés — désignation, aire "
        "protégée ou AMCEZ, gouvernance, statut, année de création — et la superficie "
        "déclarée à côté de celle calculée à partir de la limite.",
    "help_step3_title": "3. Zones et parties",
    "help_step3_body": "Chaque analyse porte sur l'aire et sur des anneaux de 500 m, 2 km "
        "et 5 km autour d'elle; choisissez la zone au-dessus de chaque graphique. Une "
        "aire formée de polygones séparés peut être analysée partie par partie.",
    "help_step4_title": "4. Cultures et occupation du sol",
    "help_step4_body": "L'inventaire des cultures d'AAC (2009–2025, au sud d'environ "
        "54–58° N) et l'occupation du sol SNSTE VLCE2 (1984–2022, écozones forestières) "
        "— deux historiques, chacun avec une couche cartographique et un tableau.",
    "help_step5_title": "5. Forêt, biomasse, paysage",
    "help_step5_body": "La perte du couvert arboré de Hansen divisée à l'année de création, "
        "l'âge des peuplements du SNSTE, la biomasse ESA CCI et des métriques de "
        "fragmentation pour toutes les zones à la fois.",
    "help_step6_title": "6. Feux et validation",
    "help_step6_body": "Les superficies brûlées selon MODIS et selon l'inventaire des "
        "cultures, et l'inventaire des cultures comparé à VLCE2 pour la même année.",
    "help_step7_title": "7. Exporter",
    "help_step7_body": "Chaque graphique se télécharge en PNG et chaque tableau en CSV "
        "depuis l'icône voisine; Exporter réunit les tableaux dans un seul classeur.",
    "help_limitations_title": "Ce que cette page ne peut pas dire",
    "help_limit_1": "Les aires gouvernées ou détenues par des peuples autochtones ne "
        "figurent pas ici, par principe (PCAP®/OCAP®), et il n'y a pas d'analyse des "
        "terres autochtones canadiennes.",
    "help_limit_2": "L'inventaire des cultures s'arrête vers 54–58° N; VLCE2 ne couvre "
        "que les écozones forestières; MapBiomas (page du Brésil) ne couvre pas le Canada.",
    "help_limit_3": "La « perte » de Hansen est toute perturbation qui remplace le "
        "peuplement — feu, récolte, insectes — pas du déboisement.",
    "help_limit_4": "Aucun verdict sur la gestion ou la conformité n'est émis : les "
        "chiffres décrivent l'occupation du sol, pas l'intendance.",
    "cite_trigger": "Citer",
    "cite_dialog_title": "Comment citer",
    "cite_dialog_desc": "Yvynation Canada et les jeux de données sur lesquels il repose.",
    "cite_sources_title": "Sources de données",
    "cite_sources_desc": "Toutes les sources utilisées par cette page, que l'aire "
        "courante les utilise toutes ou non.",
    "cite_example_title": "Citation suggérée",
    "download_button": "Exporter",
    "export_dialog_title": "Exporter",
    "export_dialog_desc": "Des PNG par graphique et des CSV par tableau sont disponibles "
        "depuis l'icône voisine de chacun. Un classeur combiné et un rapport ne sont pas "
        "encore offerts sur cette page.",

    # --- protected areas: selection, provinces, parts ----------------------------------------------------------------
    "erro_sem_area": "Aucune aire protégée ici dans les provinces affichées. Les contours "
        "vert-bleu de la carte sont les aires de la BDCAPC que vous pouvez sélectionner.",
    "candidates_note": "Plusieurs aires protégées se chevauchent ici — les désignations "
        "s'emboîtent souvent. Choisissez laquelle analyser (la plus petite d'abord) :",
    "provinces_title": "Provinces affichées",
    "ca_add_province": "Ajouter une province…",
    "ca_provinces_hint": "La Colombie-Britannique se charge d'abord. Cliquer sur la carte "
        "ou rechercher un lieu dans une autre province l'ajoute.",
    "ca_ocap_note": "Les aires gouvernées ou détenues par des peuples autochtones ne sont "
        "pas incluses, conformément aux principes PCAP®/OCAP® de souveraineté des "
        "données des Premières Nations.",
    "ca_source_note": "Source : Base de données canadienne sur les aires protégées et de "
        "conservation (BDCAPC), ECCC — Licence du gouvernement ouvert – Canada.",
    "ca_parts_title": "Parties de cette aire",
    "ca_parts_analysing_all": "Analyse de l'aire entière — les {total} parties.",
    "ca_parts_analysing_some": "Analyse de {n} parties sur {total}.",
    "ca_parts_hint": "Cochez des parties ci-dessous, ou cliquez-les sur la carte, puis "
        "analysez la sélection.",
    "ca_parts_apply": "Analyser les parties choisies",
    "ca_parts_all": "Aire entière",
    "ca_parts_clear": "Effacer",
    "ca_parts_more": "Les {n} plus grandes parties sur {total} sont listées — cliquez sur "
        "n'importe quelle partie de la carte pour la choisir.",
    "ca_parts_zoom": "Zoomer sur cette partie",
    "area_card_title": "Aire protégée",
    "area_name_fr": "Nom en français",
    "area_name_ind": "Nom autochtone",
    "area_province": "Province / territoire",
    "area_pa_oecm": "AP / AMCEZ",
    "area_governance": "Gouvernance",
    "area_owner_type": "Type de propriétaire",
    "area_cpcad_id": "Identifiant BDCAPC",
    "area_disclosure": "Limite et attributs tels que publiés dans la BDCAPC "
        "(Environnement et Changement climatique Canada). Les aires gouvernées ou "
        "détenues par des peuples autochtones ne sont pas incluses (PCAP®/OCAP®). "
        "Yvynation décrit l'occupation du sol dans et autour d'une aire protégée; il "
        "ne rend aucun verdict sur la gestion de l'aire.",

    # --- land cover (VLCE2) -----------------------------------------------------------------------------------------------------
    "tab_vlce2": "Occupation du sol",
    "legend_vlce2": "Occupation du sol (SNSTE VLCE2)",
    "legend_vlce2_palette": "Les classes apparaissent ici une fois l'historique chargé.",
    "vlce2_running": "Récupération de l'historique d'occupation du sol 1984–2022…",
    "vlce2_empty": "Aucune donnée pour l'instant — sélectionnez une aire protégée.",
    "vlce2_out_of_range": "VLCE2 n'a aucun pixel ici — il cartographie les écozones "
        "forestières du Canada, pas les Prairies ni l'Arctique. L'onglet Cultures couvre "
        "les terres agricoles.",
    "vlce2_attribution": "SNSTE VLCE2 — Hermosilla et al., RNCan / Service canadien des forêts · 30 m · 1984–2022",
    "erro_trajetoria_vlce2": "L'historique d'occupation du sol n'a pas pu être calculé : {detail}",
    "erro_vlce2_sem_classes": "Aucune occupation du sol VLCE2 sur cette aire — hors des "
        "écozones forestières cartographiées par le SNSTE.",
    "floresta_year_before_record_note": "Cette aire a été créée en {year}, avant le début "
        "du registre de pertes de Hansen ({first}) — toutes les années de perte "
        "présentées sont donc postérieures à la création, et il n'y a pas de période "
        "antérieure à laquelle les comparer.",
    "floresta_year_after_record_note": "Cette aire a été créée en {year}, après la fin du "
        "registre de pertes de Hansen ({last}) — toutes les années de perte présentées "
        "sont donc antérieures à la création.",

    # --- how to read this ------------------------------------------------------------------------------------------------------------
    "how_to_read": "Comment lire ceci",
    "read_cobertura": (
        "Graphique — une barre par année (2009–2025). Chaque couleur est une classe de "
        "l'inventaire des cultures d'Agriculture et Agroalimentaire Canada; sa hauteur "
        "est la superficie qu'elle occupe dans la zone choisie ci-dessus. Passez à "
        "Pourcentage pour comparer les années quelle que soit la taille de la zone. La "
        "ligne pointillée marque l'année de création de l'aire.\n"
        "Tableau — les classes présentes dans l'année choisie, de la plus grande à la "
        "plus petite, avec hectares et part de la zone.\n"
        "Carte — la même classification pour l'année choisie; la légende dans le coin de "
        "la carte énumère les classes présentes.\n"
        "Limites — un inventaire agricole : les cultures sont cartographiées finement, la "
        "forêt grossièrement; la couverture s'arrête vers 54–58° N et n'est nationale "
        "qu'à partir de 2011. Plus au nord, utilisez l'onglet Occupation du sol."),
    "read_vlce2": (
        "Graphique — une barre par année, 1984–2022. Chaque couleur est une classe "
        "d'occupation du sol (conifères, feuillus, mixte, arbustes, herbes, milieux "
        "humides, eau, sol nu…); sa hauteur est la superficie dans la zone choisie "
        "ci-dessus. Une bande de forêt qui chute puis repousse lentement signifie "
        "généralement un feu ou une récolte suivis d'une repousse par les arbustes.\n"
        "Tableau — les classes de l'année choisie, de la plus grande à la plus petite.\n"
        "Carte — la classification de cette année; changez l'année dans la légende de la "
        "carte pour voir quand un changement s'est produit.\n"
        "Limites — VLCE2 ne cartographie que les écozones forestières (pas les Prairies "
        "ni l'Arctique) et s'arrête en 2022. Les pixels qu'il laisse non classés ne sont "
        "pas comptés; le total d'une année peut donc être inférieur à la superficie de "
        "la zone."),
    "read_transicoes": (
        "Diagramme — la colonne de gauche est l'occupation du sol de la première année, "
        "celle de droite de la seconde; la largeur de chaque bande est la superficie "
        "passée d'une classe à une autre. Les bandes horizontales sont des terres qui "
        "n'ont pas changé; les bandes qui se croisent sont du changement.\n"
        "Tableau — les principales transitions, en hectares.\n"
        "Carte — les deux années côte à côte; faites glisser le séparateur pour comparer.\n"
        "Limites — fondé sur l'inventaire des cultures : entre des années proches, "
        "beaucoup de « transitions » sont des rotations de cultures ou du bruit de "
        "classification, d'où le refus des années trop rapprochées."),
    "read_floresta": (
        "Graphique — perte du couvert arboré par année (Hansen Global Forest Change, "
        "depuis 2001), divisée à l'année de création de l'aire : orange avant, rouge "
        "après — pour voir si les coupes ont continué une fois l'aire protégée.\n"
        "Encadrés — perte totale de chaque période, et gain (2000–2012, non daté, donc "
        "jamais soustrait de 25 ans de perte).\n"
        "Âge des peuplements — âge mesuré de la forêt en 2019 (SNSTE) : moyenne, médiane "
        "et part de la zone qui est boisée.\n"
        "Carte — les pixels de perte, colorés selon la même division.\n"
        "Limites — la « perte » est toute perturbation qui remplace le peuplement (feu, "
        "récolte, insectes, vent), pas du déboisement; elle ne dit pas pourquoi les "
        "arbres ont disparu."),
    "read_biomassa": (
        "Graphique — biomasse aérienne en mégagrammes (tonnes) par hectare, pour chaque "
        "année publiée par ESA CCI. Une baisse qui coïncide avec une année de perte dans "
        "l'onglet Forêt est le même événement vu par un autre capteur.\n"
        "Tableau — les valeurs annuelles et le total de la zone.\n"
        "Carte — la biomasse de l'année choisie; plus le vert est foncé, plus il y en a.\n"
        "Limites — pixels de 100 m; l'estimation est plus faible sur la neige persistante "
        "et les boisés nordiques clairsemés; les petites variations d'une année à "
        "l'autre sont donc dans l'incertitude du produit."),
    "read_paisagem": (
        "Tableau — une ligne par zone (l'aire et chaque anneau). Fragments : en combien de "
        "morceaux séparés les classes se divisent. Plus grand % : part occupée par le plus "
        "grand morceau. Densité de lisière : mètres de lisière par hectare. Meff (taille "
        "effective de maille) : la taille attendue du morceau où tombe un point au hasard "
        "— plus elle est élevée, moins le paysage est fragmenté. Shannon, Simpson et "
        "Équitabilité : à quel point les classes sont mélangées.\n"
        "Graphique — Meff par zone : une aire bien moins fragmentée que ses anneaux se "
        "démarque.\n"
        "Carte — les fragments de l'année choisie.\n"
        "Limites — calculé sur les classes de l'inventaire des cultures : comparez une "
        "aire avec ses propres anneaux, pas un paysage agricole avec un paysage forestier."),
    "read_fogo": (
        "Graphique — part de la zone qui a brûlé chaque année, selon MODIS (500 m, depuis "
        "2001) ou selon la classe de superficie brûlée de l'inventaire des cultures (30 m, "
        "depuis 2009); le sélecteur choisit la source. Une barre hachurée est l'année en "
        "cours, non terminée.\n"
        "Encadrés — années avec au moins un feu, fréquence moyenne des feux et feu le plus "
        "récent.\n"
        "Carte — toutes les années combinées : plus le rouge est foncé, plus la zone a "
        "brûlé souvent.\n"
        "Limites — les pixels MODIS font environ 21 ha, donc pour de petites zones les "
        "effets de bordure dominent; les deux sources ne sont jamais fusionnées en un seul "
        "chiffre."),
    "read_validacao": (
        "Comparaison — l'inventaire des cultures contre VLCE2 pour la même année, à un "
        "niveau de groupes grossier que les deux produits savent nommer (forêt, arbustes, "
        "herbes, cultures, eau, milieux humides, sol nu, bâti).\n"
        "Concordance — la part de la zone où les deux nomment le même groupe; le tableau "
        "donne la superficie et la concordance de chaque groupe de l'inventaire.\n"
        "Carte — les deux produits côte à côte; faites glisser le séparateur.\n"
        "Limites — le désaccord entre deux produits indépendants est une information, pas "
        "une erreur de l'un ou l'autre; une part du désaccord vient de ce que les deux "
        "grilles ne s'alignent pas aux bords des classes."),

    # --- quick start (card) --------------------------------------------------------------------------------------------------------------
    "qs_title": "Commencez en 30 secondes",
    "qs_more": "Chaque onglet s'ouvre sur un court « Comment lire ceci ». Le mode d'emploi "
        "complet couvre les couches, les exportations et ce que les données ne peuvent "
        "pas dire.",
    "qs_got_it": "Compris",
    "qs_full_howto": "Voir le mode d'emploi complet",
    "qs_close_aria": "Fermer le démarrage rapide",
    "region_brazil": "Brésil",
    "region_canada": "Canada",
    "region_label": "Région",
}


def _typo(text: str) -> str:
    """French typography: a non-breaking space before ``: ; ? !`` and inside
    « », so a colon or a closing guillemet is never stranded at the start of
    the next line. Applied once to the whole table, so the strings above stay
    readable (invisible characters are not something to type by hand)."""
    nb = " "
    for mark in (":", ";", "?", "!"):
        text = text.replace(f" {mark}", f"{nb}{mark}")
    return text.replace("« ", f"«{nb}").replace(" »", f"{nb}»")


TRANSLATIONS_FR = {k: _typo(v) for k, v in TRANSLATIONS_FR.items()}
