"""English text specific to Yvynation's Canada page.

Layered over the camposcope-derived ``en.py`` (see ``translations/__init__``):
rebranded strings (a protected area, not a parcel), the CPCAD / parts /
provinces vocabulary, the VLCE2 land-cover tab, and one "How to read this"
explanation per results tab.
"""

YVY_EN: dict[str, str] = {
    # --- header / shell ----------------------------------------------------
    "app_name": "Yvynation Canada — protected areas",
    "nav_subtitle": "Land-cover history of Canada's protected and conserved "
        "areas (CPCAD), British Columbia first",
    "mobile_parcel_zones_toggle": "Area & zones",
    "go_to_brazil": "Brazil",

    # --- search -------------------------------------------------------------
    "search_placeholder": "protected-area name, address, postal code, coordinate…",
    "search_areas_heading": "Protected areas",
    "search_places_note": "A place only frames the map and drops a pin. "
        "Click a protected area (teal outline) to analyse it.",
    "search_place_hint": "click a protected area on the map to analyse it",
    "echo_area_cpcad": "protected area",
    "erro_sem_area": "No protected area here in the provinces shown. The "
        "teal outlines on the map are the CPCAD areas you can select.",
    "candidates_note": "Several protected areas overlap here — designations "
        "often nest inside one another. Choose which one to analyse "
        "(smallest first):",

    # --- provinces and parts ------------------------------------------------
    "provinces_title": "Provinces shown",
    "ca_add_province": "Add a province…",
    "ca_provinces_hint": "BC loads first. Clicking the map or searching a "
        "place in another province adds it.",
    "ca_ocap_note": "Areas governed or owned by Indigenous peoples are not "
        "included, in keeping with the OCAP® principles of First Nations "
        "data sovereignty.",
    "ca_source_note": "Source: Canadian Protected and Conserved Areas "
        "Database (CPCAD), ECCC — Open Government Licence – Canada.",
    "ca_parts_title": "Parts of this area",
    "ca_parts_analysing_all": "Analysing the whole area — all {total} parts.",
    "ca_parts_analysing_some": "Analysing {n} of {total} parts.",
    "ca_parts_hint": "Tick parts below, or click them on the map, then "
        "analyse the selection.",
    "ca_parts_apply": "Analyse selected parts",
    "ca_parts_all": "Whole area",
    "ca_parts_clear": "Clear",
    "ca_parts_more": "Listing the {n} largest of {total} parts — click any "
        "part on the map to pick it.",
    "ca_parts_zoom": "Zoom to this part",

    # --- area card ------------------------------------------------------------
    "park_area_reported": "Reported area (CPCAD)",
    "area_card_title": "Protected area",
    "area_name_fr": "French name",
    "area_name_ind": "Indigenous name",
    "area_province": "Province / territory",
    "area_pa_oecm": "PA / OECM",
    "area_governance": "Governance",
    "area_owner_type": "Owner type",
    "area_cpcad_id": "CPCAD id",
    "area_disclosure": "Boundary and attributes as published in CPCAD "
        "(Environment and Climate Change Canada). Areas governed or owned by "
        "Indigenous peoples are not included (OCAP®). Yvynation describes "
        "land cover in and around a protected area; it issues no verdict "
        "about how the area is managed.",
    "zones_note": "The protected area plus rings measured outward from its "
        "boundary — compare inside with around.",
    "zona_park": "Protected area",

    # --- tabs -----------------------------------------------------------------
    "tab_cobertura": "Crops (AAFC)",
    "cobertura_empty": "No data yet — select a protected area.",
    "cobertura_out_of_range": "The AAFC crop inventory has no coverage this "
        "far north — expected above roughly 54–58°N, not a failure. The Land "
        "cover, Forest, Biomass and Fire tabs still answer.",
    "fogo_aci_empty": "No Crops (AAFC) data yet for this zone — open that tab, or "
        "wait for it to finish loading. The burnt-area class comes from that same "
        "fetch, at no extra cost.",
    "cite_sources_desc": "Every source this page draws on, whether or not the "
        "current area happens to use all of them.",
    "tab_vlce2": "Land cover",
    "legend_vlce2": "Land cover (NTEMS VLCE2)",
    "legend_vlce2_palette": "Classes appear here once the history has loaded.",
    "vlce2_running": "Fetching the 1984–2022 land-cover history…",
    "vlce2_empty": "No data yet — select a protected area.",
    "vlce2_out_of_range": "VLCE2 has no pixels here — it maps Canada's "
        "forested ecozones, not the prairie or the arctic. The Crops tab "
        "covers farmland.",
    "vlce2_attribution": "NTEMS VLCE2 — Hermosilla et al., NRCan / Canadian "
        "Forest Service · 30 m · 1984–2022",
    "erro_trajetoria_vlce2": "The land-cover history could not be computed: {detail}",
    "erro_vlce2_sem_classes": "No VLCE2 land cover over this area — outside "
        "the forested ecozones NTEMS maps.",
    "floresta_split_start_date": "Split at establishment year",
    "legend_hansen_split_start_date": "Split at establishment year",
    "floresta_before_parcel": "Before establishment",
    "floresta_after_parcel": "After establishment",
    "floresta_no_start_date_note": "CPCAD records no establishment year for "
        "this area, so loss is shown as one undivided series rather than "
        "split at an invented date.",
    "floresta_year_before_record_note": "This area was established in {year}, "
        "before Hansen's loss record begins ({first}) — so every year of loss "
        "shown is after establishment, and there is no earlier period to "
        "compare it with.",
    "floresta_year_after_record_note": "This area was established in {year}, "
        "after Hansen's loss record ends ({last}) — so every year of loss "
        "shown is before establishment.",
    "paisagem_legend_note": "Patch counts follow the crop inventory's own "
        "classes, which resolve crops finely and forest coarsely — "
        "comparable between this protected area and its rings, not between "
        "a farmed landscape and a forested one.",

    # --- how to read ------------------------------------------------------------
    "how_to_read": "How to read this",
    "read_cobertura": (
        "Chart — one bar per year (2009–2025). Each colour is a class of "
        "Agriculture and Agri-Food Canada's crop inventory; its height is "
        "the area it covers in the zone chosen above. Switch to Percent to "
        "compare years whatever the zone's size. The dashed line marks the "
        "year the area was established.\n"
        "Table — the classes present in the selected year, largest first, "
        "with hectares and share of the zone.\n"
        "Map — the same classification for the selected year; the legend in "
        "the map corner lists the classes present.\n"
        "Limits — an agricultural inventory: crops are mapped finely, forest "
        "coarsely; coverage stops around 54–58°N and is national only from "
        "2011. North of that, use the Land cover tab."),
    "read_vlce2": (
        "Chart — one bar per year, 1984–2022. Each colour is a land-cover "
        "class (coniferous, broadleaf, mixedwood, shrubs, herbs, wetland, "
        "water, barren…); its height is the area in the zone chosen above. A "
        "forest band that drops and then slowly grows back usually means a "
        "fire or harvest followed by regrowth through shrubs.\n"
        "Table — the classes in the selected year, largest first.\n"
        "Map — that year's classification; change the year in the map "
        "legend to see when a change happened.\n"
        "Limits — VLCE2 maps forested ecozones only (not the prairie or the "
        "arctic) and ends in 2022. Pixels it leaves unclassified are not "
        "counted, so a year's total can be below the zone's area."),
    "read_transicoes": (
        "Diagram — the left column is land cover in the first year, the "
        "right column in the second; each band's width is the area that "
        "went from one class to another. Level bands are land that did not "
        "change; bands that cross are change.\n"
        "Table — the largest transitions, in hectares.\n"
        "Map — the two years side by side; drag the divider to compare.\n"
        "Limits — built on the crop inventory: between nearby years many "
        "'transitions' are crop rotation or classification noise, which is "
        "why years too close together are refused."),
    "read_floresta": (
        "Chart — tree-cover loss per year (Hansen Global Forest Change, 2001 "
        "onward), split at the year the area was established: orange "
        "before, red after — whether clearing continued once the area was "
        "protected.\n"
        "Boxes — total loss in each period, and gain (2000–2012, undated, so "
        "never subtracted from 25 years of loss).\n"
        "Stand age — measured forest age as of 2019 (NTEMS): mean, median "
        "and the share of the zone that is forested.\n"
        "Map — the loss pixels, coloured by the same split.\n"
        "Limits — 'loss' is any stand-replacing disturbance (fire, harvest, "
        "insects, wind), not deforestation; it does not say why the trees "
        "went."),
    "read_biomassa": (
        "Chart — above-ground biomass in megagrams (tonnes) per hectare, for "
        "each year ESA CCI publishes. A drop that lines up with a loss year "
        "on the Forest tab is the same event seen by another sensor.\n"
        "Table — the yearly values and the zone's total.\n"
        "Map — biomass in the selected year; darker green holds more.\n"
        "Limits — 100 m pixels; retrieval is weaker over persistent snow and "
        "sparse northern woodland, so small year-to-year changes are within "
        "the product's uncertainty."),
    "read_paisagem": (
        "Table — one row per zone (the area and each ring). Patches: how "
        "many separate pieces the classes form. Largest %: share held by the "
        "biggest piece. Edge density: metres of edge per hectare. Meff "
        "(effective mesh size): the expected size of the piece a random "
        "point falls in — higher means less fragmented. Shannon, Simpson and "
        "Evenness: how mixed the classes are.\n"
        "Chart — Meff per zone: an area much less fragmented than its rings "
        "stands out.\n"
        "Map — the patches in the selected year.\n"
        "Limits — computed on crop-inventory classes: compare an area with "
        "its own rings, not a farmed landscape with a forested one."),
    "read_fogo": (
        "Chart — share of the zone that burned each year, from MODIS (500 m, "
        "2001 onward) or from the crop inventory's burnt-area class (30 m, "
        "2009 onward); the switch picks the source. A hatched bar is the "
        "current, unfinished year.\n"
        "Boxes — years with any burn, mean burn frequency and the most "
        "recent burn.\n"
        "Map — every year combined: darker red burned more often.\n"
        "Limits — MODIS pixels are about 21 ha, so for small zones edge "
        "effects dominate; the two sources are never merged into one "
        "number."),
    "read_validacao": (
        "Comparison — the crop inventory against VLCE2 for the same year, at "
        "a coarse group level both products can name (forest, shrub, grass, "
        "crop, water, wetland, barren, built).\n"
        "Agreement — the share of the zone where both name the same group; "
        "the table gives each crop-inventory group's area and agreement.\n"
        "Map — the two products side by side; drag the divider.\n"
        "Limits — two independent products disagreeing is information, not "
        "an error in either; part of the disagreement is the two grids not "
        "lining up at class edges."),

    # --- quick start ---------------------------------------------------------------
    "qs_title": "Get started in 30 seconds",
    "qs_step1_lead": "Find a protected area",
    "qs_step1_body": "by name, address, postal code or coordinate — or click "
        "a teal outline on the map. BC loads first; other provinces load "
        "when you go there.",
    "qs_step2_lead": "Read the tabs:",
    "qs_step2_body": "crops (AAFC) and land cover since 1984 load on their "
        "own; Forest, Biomass, Landscape and Fire run on request.",
    "qs_step3_lead": "Compare zones",
    "qs_step3_body": "— the area itself and rings at 500 m, 2 km and 5 km — "
        "to see inside against around.",
    "qs_step4_lead": "Pick parts:",
    "qs_step4_body": "an area made of separate polygons can be analysed part "
        "by part from the sidebar.",
    "qs_more": "Every tab opens with a short 'How to read this'. The full "
        "how-to covers layers, exports and what the data cannot say.",

    # --- how to use (dialog) ------------------------------------------------------
    "help_dialog_title": "How to use Yvynation Canada",
    "help_dialog_desc": "Seven steps from a protected area to an analysis, "
        "and what this page cannot tell you.",
    "help_step1_title": "1. Find a protected area",
    "help_step1_body": "Type an area's name, an address, a postal code or a "
        "coordinate, or click a teal outline on the map. Where designations "
        "overlap you choose which one. British Columbia loads first; a click "
        "or a search in another province adds that province.",
    "help_step2_title": "2. Read the area card",
    "help_step2_body": "CPCAD's fields as published — designation, PA or "
        "OECM, governance, status, establishment year — plus the reported "
        "area beside the area computed from the boundary.",
    "help_step3_title": "3. Zones and parts",
    "help_step3_body": "Every analysis runs on the area and on rings at "
        "500 m, 2 km and 5 km around it; pick the zone above each chart. An "
        "area made of separate polygons can be analysed part by part.",
    "help_step4_title": "4. Crops and land cover",
    "help_step4_body": "The AAFC crop inventory (2009–2025, south of about "
        "54–58°N) and the NTEMS VLCE2 land cover (1984–2022, forested "
        "ecozones) — two histories, each with a map layer and a table.",
    "help_step5_title": "5. Forest, biomass, landscape",
    "help_step5_body": "Hansen tree-cover loss split at the establishment "
        "year, NTEMS stand age, ESA CCI biomass, and fragmentation metrics "
        "for every zone at once.",
    "help_step6_title": "6. Fire and validation",
    "help_step6_body": "MODIS and crop-inventory burned area, and the crop "
        "inventory checked against VLCE2 for the same year.",
    "help_step7_title": "7. Export",
    "help_step7_body": "Every chart downloads as a PNG and every table as a "
        "CSV from the icon beside it; Export gathers the tables in one "
        "spreadsheet.",
    "help_limitations_title": "What this page cannot tell you",
    "help_limit_1": "Indigenous-governed or Indigenous-owned areas are not "
        "here, by design (OCAP®), and there is no Canadian Indigenous-lands "
        "analysis.",
    "help_limit_2": "The crop inventory stops around 54–58°N; VLCE2 covers "
        "forested ecozones only; MapBiomas (the Brazil page) does not cover "
        "Canada.",
    "help_limit_3": "Hansen 'loss' is any stand-replacing disturbance — "
        "fire, harvest, insects — not deforestation.",
    "help_limit_4": "No verdict on management or compliance is issued: the "
        "figures describe land cover, not stewardship.",
    "cite_dialog_desc": "Yvynation Canada and the datasets it draws on.",
    "region_brazil": "Brazil",
    "region_canada": "Canada",
    "region_label": "Region",
}
