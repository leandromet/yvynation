# The USA page (`/usa`, lower 48)

Protected areas from **PAD-US**, land cover from **Annual NLCD**, forest change from **Hansen**. Code in
`reflex_app/yvynation/usa/` (2026-11-04); own state root (`USState`), like the Canada page.

## Data

* **PAD-US** (USGS Gap Analysis Project) via public ArcGIS FeatureServers — queried **live**, nothing mirrored: search by
  name (largest first), click → every record containing the point (smallest first, the user chooses), boundary generalised
  to 30 m (`services/padus.py`). Sources: v4.1 **Fee** (`Fee_Managers_PADUS`: whole national parks, forests, refuges, state
  and local parks), v4.1 **Proclamation** (tribal reservations and trust lands), and **Designation** records (wilderness
  areas…) from the flattened national service. `Easement` is not offered. **Why not the flattened service for Fee:** it
  carves designations out of the parks (Yosemite National Park comes back as 16 000 ha instead of 300 000).
  The 70 national parks are there (Des_Tp `NP`, manager NPS). A federal unit that is several records (Yellowstone: three,
  one per state) is merged into one unit; a fee and a proclamation record of the same place are shown once (the fee one).
* **Map overlay:** PAD-US **3.0** cached tiles (`PADUS3_0Manager_Type`, coloured by manager type), for orientation only.
* **Annual NLCD** 1985–2025 (`projects/sat-io/open-datasets/USGS/ANNUAL_NLCD/LANDCOVER`), one stacked `reduceRegions`
  for years × zones. Areas are measured in NAD83 / Conus Albers (EPSG:5070).
* **Hansen GFC**: the Canada page's `services/hansen.forest_change`, reused unchanged (it takes zones).

Zones, Zone, `ee_zones`, tiles, the Leaflet map and the Hansen chart are imported from `canada/`.

## Tribal lands

PAD-US includes American Indian reservations and trust lands (`Des_Tp = 'TRIBL'`, 851 records, mostly `Proclamation`).
They are federal open data, so they are offered, flagged "Tribal land", with the **Indigenous-lands notice**
(`indigenous_data_notice_*` in `utils/translations`, four languages): the numbers are land cover, not statements by or
about the peoples; Yvynation does not speak for them; CARE principles; no consultation yet. The same notice now appears
on the Brazil page (territory sidebar while "Indigenous" is selected, the territory analysis page, and the citation panel).
The Canada page still excludes Indigenous-governed areas (OCAP).

## Not here (yet)

Tabs: land cover, forest, biomass (ESA CCI) and fire (MODIS) — no landscape-metrics, transitions or validation tabs (the
Canada page's depend on the ACI classes). No part selection for multipart units; no walkthrough; no PDF report; Alaska/Hawaii/territories out of scope.
Rural parcels (Camposcope) have no public national service: not started.
