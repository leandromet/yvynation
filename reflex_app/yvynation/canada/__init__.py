"""The ``/canada`` workspace — Canadian protected and conserved areas.

Ported from Camposcope's Canada page (``camposcope/canada/``), which analyses
British Columbia land parcels, and reshaped around a different object: a
protected or conserved area from CPCAD, the federal register compiled by
Environment and Climate Change Canada (``utils/build_ca_protected_areas.py``,
``utils/conservation_service.py``). The question is Yvynation's — *what has
happened inside this protected area and around it* — and the engineering is the
port's (Earth Engine access, the tile cache, the persistent Leaflet map, the
zone abstraction, provenance, the ODS writer).

What changed in the port:

======================  ==========================================
Camposcope /canada      Yvynation /canada
======================  ==========================================
ParcelMap BC parcel     CPCAD protected or conserved area
BC only                 every province and territory; BC loads
                        first, others when a click or search
                        lands there
one polygon             multi-part areas, analysable part by part
parcel start date       CPCAD establishment year (Hansen split)
======================  ==========================================

Unchanged from the port: the AAFC Annual Crop Inventory, NTEMS VLCE2 and stand
age, Hansen Global Forest Change, ESA CCI Biomass, MODIS burned area, and the
Ecozones of Canada.

Internal names still say ``parcel`` (``CanadaAreaMixin`` keeps Camposcope's
``parcel`` / ``zones`` / ``select_at_point`` contract), deliberately: the ported
analysis mixins run unchanged against a protected area. A ``parcel`` here is
the selected protected area or part.

**Indigenous lands are not analysed here.** Areas the register records as
Indigenous Protected and Conserved Areas, as governed by Indigenous peoples, or
as Indigenous-owned are removed when the data are built, in keeping with the
First Nations principles of OCAP® — see ``utils/build_ca_protected_areas.py``.
"""
