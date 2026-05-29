"""
policy_context_brazil.py
=========================
Annual policy/institutional context for Brazilian land use and
indigenous land research (1985–2024).

This module encodes:
  1. LEGAL_MILESTONES     — key legislation and constitutional events (point-in-time)
  2. POLICY_PERIODS       — annual scores for thematic policy dimensions
  3. build_policy_series()— returns a tidy DataFrame (one row per year)

Thematic dimensions (all encoded as integers or floats per year):
  - forest_law_strength      : 0–3  (0 = absent/unenforced, 3 = strong + enforced)
  - indigenous_rights_score  : 0–3  (0 = hostile, 3 = protective + demarcating)
  - enforcement_capacity     : 0–3  (relative IBAMA/FUNAI field capacity)
  - amazon_plan_phase        : 0–4  (0 = no plan; 1–4 = PPCDAm phase number)
  - amazon_fund_active       : 0/1  (Amazon Fund operational and receiving donations)
  - car_registry_stage       : 0–3  (0 = no CAR; 1 = voluntary; 2 = mandatory rollout; 3 = mature)
  - demarcation_posture      : -1/0/1 (−1 = hostile/zero; 0 = stalled; +1 = active)
  - licensing_strictness     : 0–3  (0 = weak/captured; 3 = robust CONAMA-backed)

All scores are ordinal and relative to the 1985–2024 range.
Use them as control variables or breakpoint indicators, not absolute metrics.

Sources:
  - User-provided timeline (see docstring of LEGAL_MILESTONES)
  - Nature Scientific Reports doi:10.1038/s41598-024-52180-7
  - HRW Amazon Crisis report (2021)
  - CPI/PUC-Rio enforcement analysis
  - Mongabay PPCDAm history (2025)
  - Brasil de Fato IBAMA budget series (2025)
  - Amazon Watch, InfoAmazonia, APIB (marco temporal timeline)
  - OHCHR Special Rapporteur statements (2021–2025)
"""

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# 1. LEGAL MILESTONES (point-in-time reference table)
# ─────────────────────────────────────────────────────────────────────────────

LEGAL_MILESTONES = [
    # (year, instrument, scope, land_cover_implication, category)
    # category: FOREST_LAW | INDIGENOUS | INSTITUTION | ENFORCEMENT | PLANNING | FINANCE | CLIMATE

    # ── Pre-period baselines inherited ────────────────────────────────────────
    (1965, "Lei 4.771 — 2nd Forest Code",
     "National (regionalised Legal Reserve 20–50%)",
     "Codified Legal Reserve (RL) and Permanent Preservation Areas (APP); baseline for all subsequent reform",
     "FOREST_LAW"),

    (1981, "Lei 6.938 — National Environmental Policy (PNMA)",
     "National",
     "Created SISNAMA (federal env. system) and CONAMA (national env. council); institutional architecture",
     "INSTITUTION"),

    (1985, "Re-democratisation / Nova República begins",
     "National",
     "End of military government; environmental civil society gains space; Chico Mendes period",
     "INSTITUTION"),

    # ── 1988 Constitution and immediate sequels ────────────────────────────────
    (1988, "Constituição Federal — Art. 225 + Art. 231",
     "National, constitutional weight",
     "Amazon + Atlantic Forest = national heritage (Art. 225); Indigenous lands inalienable, "
     "original rights recognised (Art. 231); 5-year demarcation deadline set",
     "INDIGENOUS"),

    (1989, "Lei 7.735 — creates IBAMA",
     "National",
     "Single federal enforcement body merging SEMA, SUDEPE, SUDHEVEA, IBDF; modern env. police born",
     "INSTITUTION"),

    (1989, "Lei 7.797 — National Environmental Fund (FNMA)",
     "National",
     "First dedicated environmental finance mechanism",
     "FINANCE"),

    (1992, "Lei 8.490 — Ministry of the Environment (MMA) created",
     "National",
     "Cabinet-level authority for environment; separated from Interior Ministry",
     "INSTITUTION"),

    (1993, "Decree 1.141 — Indigenous land protection in border areas",
     "Amazon border regions",
     "Environmental programmes for indigenous lands formalised; Calha Norte context",
     "INDIGENOUS"),

    (1996, "MP 1.511 — Moratorium on deforestation authorisations in Amazon",
     "Legal Amazon",
     "Emergency freeze on clearing authorisations; Legal Reserve raised to 80% in Amazon by executive order",
     "FOREST_LAW"),

    (1998, "Lei 9.605 — Environmental Crimes Law",
     "National",
     "Criminal and administrative penalties for unauthorised clearing; fines, equipment seizure",
     "ENFORCEMENT"),

    (1998, "Portaria MMA 289 — PRODES remote-sensing deforestation monitoring",
     "Legal Amazon",
     "Annual INPE deforestation mapping institutionalised; monitoring basis for all policy evaluation",
     "ENFORCEMENT"),

    (2000, "Lei 9.985 — SNUC (National Protected Areas System)",
     "National",
     "Statutory typology of Conservation Units (Integral + Sustainable Use); management councils required",
     "FOREST_LAW"),

    (2001, "MP 2.166-67 — Legal Reserve reform",
     "National (biome-stratified)",
     "80% RL in Amazon forest; 35% in Cerrado; 20% elsewhere; APP rules tightened; still unenforced",
     "FOREST_LAW"),

    (2002, "ARPA (Amazon Region Protected Areas Programme) launched",
     "Legal Amazon",
     "R$395 million commitment over 10 years to create/consolidate 50 Mha of protected areas",
     "PLANNING"),

    (2004, "PPCDAm Phase I launched (2004–2008)",
     "Legal Amazon",
     "Command-and-control + 26 million ha of new protected areas; 83% deforestation drop 2004–2012; "
     "Marina Silva as Environment Minister",
     "PLANNING"),

    (2004, "DETER real-time deforestation alert system (INPE) — operational 2004",
     "Legal Amazon",
     "Near-real-time alerts enabled rapid enforcement; key operational tool of PPCDAm",
     "ENFORCEMENT"),

    (2006, "Lei 11.284 — Public Forest Management Law",
     "National",
     "Concessions in public forests; created SFB (Brazilian Forest Service); sustainable timber framework",
     "FOREST_LAW"),

    (2006, "Lei 11.428 — Atlantic Forest Law (Mata Atlântica)",
     "Atlantic Forest biome",
     "Strict protection regime; suppression only in exceptional cases; restoration obligations",
     "FOREST_LAW"),

    (2006, "DETER integrated with Sisbio and embargo system",
     "Legal Amazon",
     "Real-time alerts linked to enforcement actions; rural credit suspension for embargoed properties",
     "ENFORCEMENT"),

    (2007, "ICMBio created (Lei 11.516)",
     "National",
     "Chico Mendes Institute for Biodiversity Conservation; separated from IBAMA; manages 334 protected areas",
     "INSTITUTION"),

    (2008, "Amazon Fund (Fundo Amazônia) created — BNDES management",
     "Legal Amazon",
     "Results-based finance (Norway + Germany + others); performance-linked to PRODES deforestation data; "
     "first disbursements 2009",
     "FINANCE"),

    (2008, "Rural Credit Suspension for embargoed properties (Decree 6.321)",
     "Legal Amazon",
     "Denied bank credit to farms on IBAMA embargo list; powerful economic disincentive for deforesters",
     "ENFORCEMENT"),

    (2008, "Soy Moratorium (private sector) renewed",
     "Legal Amazon / Cerrado border",
     "Cargill-led voluntary ban on soy from newly deforested Amazon land; informal but effective",
     "FOREST_LAW"),

    (2009, "Política Nacional sobre Mudança do Clima (PNMC) — Lei 12.187",
     "National",
     "Brazil's domestic climate law; 80% Amazon deforestation reduction target by 2020",
     "CLIMATE"),

    (2009, "PPCDAm Phase II (2009–2011)",
     "Legal Amazon",
     "Territorial ordering focus; land tenure regularisation; PPCDAM targets met early",
     "PLANNING"),

    (2009, "Raposa Serra do Sol TI homologated (contiguous) — STF ruling",
     "Roraima",
     "Landmark ruling upholding contiguous demarcation; expelled rice farmers; strengthened Art. 231",
     "INDIGENOUS"),

    (2012, "Lei 12.651 — New Forest Code",
     "National",
     "Replaced 1965 code; CAR (Cadastro Ambiental Rural) mandatory; amnesty for pre-Jul/2008 deforesters; "
     "reduced APPs on small properties; widely seen as weakening forest protection",
     "FOREST_LAW"),

    (2012, "CAR — Rural Environmental Registry — mandatory rollout begins",
     "National (property-level)",
     "Digital georeferenced registry of all rural properties; required for rural credit from 2014",
     "ENFORCEMENT"),

    (2012, "PPCDAm Phase III (2012–2015)",
     "Legal Amazon",
     "Economic instruments + territorial governance; deforestation at historic low (~4,500 km²)",
     "PLANNING"),

    (2013, "PRA (Programa de Regularização Ambiental) — implementation",
     "National",
     "Environmental compliance programme tied to CAR; amnesty provisions activate",
     "FOREST_LAW"),

    (2014, "CAR deadline extended; rural credit conditional on registration",
     "National",
     "CAR registration required for all rural credit lines from BB, Caixa and BNDES",
     "ENFORCEMENT"),

    (2016, "PPCDAm Phase IV (2016–2020) — weakened under Temer",
     "Legal Amazon",
     "Phase continues formally but enforcement resources cut; deforestation rebounds from 2016",
     "PLANNING"),

    (2016, "Emenda Constitucional 95 — Spending Ceiling (Teto de Gastos)",
     "National",
     "20-year public spending freeze; accelerated cuts to IBAMA, FUNAI, ICMBio budgets",
     "INSTITUTION"),

    (2017, "Planaveg — National Native Vegetation Recovery Plan",
     "National",
     "Recovery targets: 12 Mha by 2030; compliance mechanism for New Forest Code amnesty debtors",
     "FOREST_LAW"),

    (2018, "Soy Moratorium renewed (ABIOVE/Cargill)",
     "Legal Amazon",
     "Private sector commitment extended; Amazon Fund compliance monitoring continued",
     "FOREST_LAW"),

    (2019, "Bolsonaro Decree 9.667 — FUNAI restructured; demarcation frozen",
     "National",
     "Zero new indigenous land demarcations 2019–2022; first government since democracy with no demarcations; "
     "FUNAI militarised (Marcelo Xavier); demarcation staff removed",
     "INDIGENOUS"),

    (2019, "Decreto 9.760 — IBAMA enforcement procedure reformed",
     "National",
     "Conciliation hearings introduced; fines collected dropped 85%; embargoes −59%; efficiency loss",
     "ENFORCEMENT"),

    (2019, "PPCDAm formally discontinued; replaced by 'Operação Verde Brasil'",
     "Legal Amazon",
     "Military-led operation replaced civilian command-and-control; enforcement politicised",
     "PLANNING"),

    (2019, "Amazon Fund suspended (Bolsonaro government)",
     "Legal Amazon",
     "Norway and Germany halt disbursements citing lack of governance; ~R$ 2.9 billion frozen",
     "FINANCE"),

    (2020, "IBAMA budget −30%; ICMBio −32.7% vs 2019",
     "National",
     "Field inspectors dropped: 1,800 (2009) → 667 (2020); fire-prevention funds nearly exhausted",
     "ENFORCEMENT"),

    (2021, "PL 490 — 'Marco Temporal' bill advances in Congress",
     "National / Indigenous Lands",
     "Legislation encoding the time-frame thesis; opened IL to mining, agribusiness; Bolsonaro-backed",
     "INDIGENOUS"),

    (2022, "Decreto 11.226 — FUNAI regional committees abolished",
     "National",
     "Regional indigenous consultation bodies removed; further dismantling of demarcation capacity",
     "INDIGENOUS"),

    (2023, "Ministry of Indigenous Peoples (MPI) created — Lei 14.502",
     "National",
     "First dedicated indigenous cabinet ministry; Sônia Guajajara as minister; FUNAI remains under Justice",
     "INDIGENOUS"),

    (2023, "PPCDAm Phase V relaunched — Lula 3rd term",
     "Legal Amazon + other biomes",
     "Extended to Cerrado, Caatinga, Pantanal; zero deforestation by 2030 target; enforcement surge",
     "PLANNING"),

    (2023, "Amazon Fund reactivated; Norway + Germany resume donations",
     "Legal Amazon",
     "R$ 1.7 billion disbursed 2023; new governance framework; expanded to other biomes",
     "FINANCE"),

    (2023, "STF rules Marco Temporal unconstitutional (RE 1.017.365) — Sep 21",
     "National / Indigenous Lands",
     "9–2 ruling: indigenous rights not bound by Oct 5, 1988 occupation date; binding on all courts",
     "INDIGENOUS"),

    (2023, "Lei 14.701/2023 — Congress overrides STF; Marco Temporal enshrined",
     "National / Indigenous Lands",
     "Bancada ruralista passes law reinstating 1988 time-frame; Lula veto overridden Dec 27, 2023; "
     "STF constitutionality challenge pending",
     "INDIGENOUS"),

    (2023, "CAR maturation — >95% of rural properties registered",
     "National",
     "Registry near-complete; compliance monitoring (PRA) begins systematic review",
     "ENFORCEMENT"),

    (2024, "Gilmar Mendes suspends marco temporal lawsuits; conciliation chamber",
     "National / Indigenous Lands",
     "All STF cases on Law 14.701 suspended pending mediation; 24-member conciliation commission",
     "INDIGENOUS"),

    (2025, "Lei 15.190/2025 — 'PL do Licenciamento' / Devastation Bill",
     "National",
     "Weakened environmental licensing; removed federal role for many project categories; "
     "retroactively grants licences; widely criticised by env. groups",
     "ENFORCEMENT"),

    (2026, "STF mining-on-Indigenous-Land ruling + 2-year Congress deadline",
     "National / Indigenous Lands",
     "STF sets 2-year deadline for Congress to regulate mining on ILs; legal uncertainty continues",
     "INDIGENOUS"),
]


# ─────────────────────────────────────────────────────────────────────────────
# 2. ANNUAL POLICY SCORES  (1985–2024)
# ─────────────────────────────────────────────────────────────────────────────
#
# Each year is a dict with the following keys:
#   forest_law_strength    : 0–3  overall strength of the forest legal framework
#   indigenous_rights_score: 0–3  institutional posture toward IL rights
#   enforcement_capacity   : 0–3  relative IBAMA/FUNAI field capacity
#   amazon_plan_phase      : 0–4  PPCDAm phase (0 = none)
#   amazon_fund_active     : 0/1
#   car_registry_stage     : 0–3
#   demarcation_posture    : -1/0/1
#   licensing_strictness   : 0–3
#   key_events             : short label(s) for the year
#
# Score rationale for each dimension:
#
# forest_law_strength
#   0 = no binding national law or wholly unenforced
#   1 = law exists, enforcement weak/absent
#   2 = law + partial enforcement
#   3 = law + strong enforcement + monitoring
#
# indigenous_rights_score
#   0 = hostile / demarcation frozen or reversed
#   1 = passive / no new demarcations
#   2 = active but slow / some demarcations
#   3 = strong protection + multiple demarcations + budget support
#
# enforcement_capacity (IBAMA+ICMBio+FUNAI combined)
#   0 = effectively non-functional
#   1 = minimal, severely understaffed/underfunded
#   2 = functional but constrained
#   3 = full operational capacity (benchmark ≈ 2006–2008)
#
# amazon_plan_phase: 0 (none), 1 (PPCDAm-I 2004-08), 2 (PPCDAm-II 2009-11),
#                   3 (PPCDAm-III 2012-15), 4 (PPCDAm-IV 2016-20 degraded),
#                   5 (PPCDAm-V 2023-)
#
# car_registry_stage: 0 (no CAR), 1 (voluntary/pilot), 2 (mandatory rollout),
#                     3 (mature/near-complete)
#
# demarcation_posture: -1 (hostile/zero), 0 (stalled/passive), +1 (active)
#
# licensing_strictness: 0 (captured/absent), 1 (weak), 2 (moderate), 3 (strict)

POLICY_SCORES = {
    # ── Pre-Constitution period (1985–1987) ──────────────────────────────────
    1985: dict(forest_law_strength=1, indigenous_rights_score=1, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=0, licensing_strictness=1,
               key_events="Nova República; 1965 Forest Code unenforced; Chico Mendes movement"),
    1986: dict(forest_law_strength=1, indigenous_rights_score=1, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=0, licensing_strictness=1,
               key_events="Carajás / Grande Carajás programme expands; rubber-tappers organise"),
    1987: dict(forest_law_strength=1, indigenous_rights_score=1, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=0, licensing_strictness=1,
               key_events="Constituent Assembly; Chico Mendes murder campaign peaks"),

    # ── Constitution + IBAMA (1988–1989) ─────────────────────────────────────
    1988: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=1,
               key_events="CF/88: Art.225 (Amazon heritage) + Art.231 (indigenous rights); "
                           "5-yr demarcation deadline; Chico Mendes assassinated Dec 22"),
    1989: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=1,
               key_events="IBAMA created (Lei 7.735); Yanomami territory demarcation begins"),

    # ── Early 1990s — Collor + Itamar (1990–1994) ────────────────────────────
    1990: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=1,
               key_events="IBAMA first operational year; Collor suspends garimpeiros from Yanomami TI"),
    1991: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Yanomami TI demarcated (Decreto 22); largest IL in Brazil at 9.4 Mha"),
    1992: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="MMA created; Rio Earth Summit (UNCED); CBD signed; FNMA operational"),
    1993: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Haximu massacre (Yanomami); Amazon deforestation ~11,000 km²"),
    1994: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Plano Real; end of Itamar; soy frontier expanding in Mato Grosso"),

    # ── FHC two terms (1995–2002) ─────────────────────────────────────────────
    1995: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="FHC inaugurated; deforestation ~12,000 km²; MP 1.511 (Legal Reserve to 80% in Amazon)"),
    1996: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="MP 1.511 consolidates 80% RL in Amazon; Eldorado dos Carajás massacre (Apr 17)"),
    1997: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Multiple IL demarcations; Kyoto Protocol; Decreto 2.519 (CBD)"),
    1998: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Lei 9.605 (Environmental Crimes); PRODES satellite monitoring institutionalised"),
    1999: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Deforestation rebounds to ~17,000 km²; soy boom; Geisel-era roads in use"),
    2000: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="SNUC (Lei 9.985); ARPA framework; deforestation ~18,000 km²"),
    2001: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="MP 2.166-67: 80/35/20% RL by biome; Portaria FUNAI 542 (isolated peoples)"),
    2002: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="ARPA launched; Lula elected; deforestation ~21,000 km² (near peak)"),

    # ── Lula I + II — peak enforcement (2003–2010) ────────────────────────────
    2003: dict(forest_law_strength=2, indigenous_rights_score=3, enforcement_capacity=2,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Lula I; Marina Silva as MMA minister; pre-PPCDAm enforcement ramp-up; "
                           "deforestation 25,400 km² (near-record); Dorothy Stang context"),
    2004: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=1, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="PPCDAm Phase I launched; DETER operational; 26 Mha new protected areas; "
                           "deforestation 27,800 km² (historic peak); Dorothy Stang murdered Feb 2005"),
    2005: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=1, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="PPCDAm I; deforestation begins declining (19,014 km²); "
                           "41,000+ fines USD 3.9B issued 2004-2012; Dorothy Stang murder Feb 12"),
    2006: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=1, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="Lei 11.284 (public forest concessions); Lei 11.428 (Atlantic Forest Law); "
                           "DETER linked to rural credit embargo; deforestation 14,286 km²"),
    2007: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=1, amazon_fund_active=0, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="ICMBio created (Lei 11.516); deforestation 11,651 km²; "
                           "Marina Silva resigns Aug (Belo Monte conflict)"),
    2008: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=1, amazon_fund_active=1, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="Amazon Fund created (BNDES); Decreto 6.321 (rural credit suspended for embargoed farms); "
                           "PNMC climate law; deforestation 12,911 km²; Blairo Maggi/Soy Moratorium context"),
    2009: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=2, amazon_fund_active=1, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="PPCDAm Phase II; Amazon Fund first disbursements; Raposa Serra do Sol STF ruling "
                           "(contiguous); deforestation 7,464 km²; Copenhagen COP15"),
    2010: dict(forest_law_strength=3, indigenous_rights_score=3, enforcement_capacity=3,
               amazon_plan_phase=2, amazon_fund_active=1, car_registry_stage=0,
               demarcation_posture=1, licensing_strictness=3,
               key_events="PPCDAm II; deforestation 7,000 km²; 1,800 IBAMA field agents (historical peak); "
                           "Lula II ends"),

    # ── Dilma I + II — mixed enforcement (2011–2016) ──────────────────────────
    2011: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=3, amazon_fund_active=1, car_registry_stage=1,
               demarcation_posture=0, licensing_strictness=2,
               key_events="PPCDAm Phase III; Dilma I; Belo Monte licence issued; IBAMA offices cut (91 of 168); "
                           "deforestation 6,418 km²"),
    2012: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=3, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=2,
               key_events="Lei 12.651 — New Forest Code (amnesty; CAR mandatory); "
                           "deforestation 4,571 km² (historic low since satellite era); CAR rollout begins"),
    2013: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=3, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=2,
               key_events="PRA (regularisation programme) operational; Belo Monte construction peak; "
                           "deforestation 5,891 km²"),
    2014: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=3, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=2,
               key_events="CAR deadline; rural credit conditional on CAR; Dilma re-elected; "
                           "deforestation 4,848 km²"),
    2015: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=3, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=2,
               key_events="Spending cuts (recession); Mariana dam disaster; deforestation 6,207 km²; "
                           "Dilma at Paris COP21"),
    2016: dict(forest_law_strength=2, indigenous_rights_score=1, enforcement_capacity=2,
               amazon_plan_phase=4, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=2,
               key_events="EC 95 Spending Ceiling; Temer impeaches Dilma; PPCDAm IV begins (degraded); "
                           "deforestation rebounds to 7,893 km²; Temer: 1 IL demarcated (suspended)"),

    # ── Temer — enforcement decline (2017–2018) ────────────────────────────────
    2017: dict(forest_law_strength=2, indigenous_rights_score=1, enforcement_capacity=2,
               amazon_plan_phase=4, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=1,
               key_events="Planaveg; IBAMA budget cuts continue; PL 3.729 (licensing weakening) tabled; "
                           "deforestation 6,947 km²"),
    2018: dict(forest_law_strength=2, indigenous_rights_score=1, enforcement_capacity=2,
               amazon_plan_phase=4, amazon_fund_active=1, car_registry_stage=2,
               demarcation_posture=0, licensing_strictness=1,
               key_events="Amazon Fund last Norway disbursement (pre-freeze); Soy Moratorium renewed; "
                           "Bolsonaro elected Oct; deforestation 7,536 km²"),

    # ── Bolsonaro — dismantling phase (2019–2022) ──────────────────────────────
    2019: dict(forest_law_strength=1, indigenous_rights_score=0, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=2,
               demarcation_posture=-1, licensing_strictness=1,
               key_events="PPCDAm discontinued; Decreto 9.667 (FUNAI restructured, militarised); "
                           "Amazon Fund suspended; Decreto 9.760 (IBAMA enforcement weakened); "
                           "IBAMA fines collected −85%; embargoes −59%; deforestation 10,129 km²"),
    2020: dict(forest_law_strength=1, indigenous_rights_score=0, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=2,
               demarcation_posture=-1, licensing_strictness=1,
               key_events="IBAMA −30% budget; ICMBio −32.7%; inspectors 780→667; "
                           "COVID used to fast-track deforestation; deforestation 10,851 km²"),
    2021: dict(forest_law_strength=1, indigenous_rights_score=0, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=2,
               demarcation_posture=-1, licensing_strictness=1,
               key_events="PL 490 (marco temporal bill); lowest env. budget since 2008; "
                           "MMA budget lowest since 2010; IBAMA 630 field agents; deforestation 13,038 km²"),
    2022: dict(forest_law_strength=1, indigenous_rights_score=0, enforcement_capacity=1,
               amazon_plan_phase=0, amazon_fund_active=0, car_registry_stage=2,
               demarcation_posture=-1, licensing_strictness=1,
               key_events="Decreto 11.226 abolishes FUNAI regional committees; Bruno Pereira/Dom Phillips "
                           "murders; zero IL demarcations 4th consecutive year; deforestation 11,568 km²; "
                           "Lula elected Oct"),

    # ── Lula III — recovery phase (2023–2024) ─────────────────────────────────
    2023: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=5, amazon_fund_active=1, car_registry_stage=3,
               demarcation_posture=1, licensing_strictness=2,
               key_events="PPCDAm V relaunched; MPI (Sônia Guajajara); Amazon Fund reactivated; "
                           "Yanomami health emergency declared; STF rules MT unconstitutional (Sep 21); "
                           "Congress passes Lei 14.701 overriding STF (Oct–Dec); "
                           "FUNAI indigenous land spending +249% vs 2021; deforestation ~11,568→~5,000 km²"),
    2024: dict(forest_law_strength=2, indigenous_rights_score=2, enforcement_capacity=2,
               amazon_plan_phase=5, amazon_fund_active=1, car_registry_stage=3,
               demarcation_posture=1, licensing_strictness=2,
               key_events="Gilmar Mendes suspends marco temporal lawsuits (Apr); conciliation chamber; "
                           "IBAMA budget +165% for monitoring vs Bolsonaro nadir; "
                           "CAR >95% complete; env. budget recovering but staffing still limited "
                           "(771 field agents vs 1,800 in 2009)"),
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. BUILD FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_policy_series(years=range(1985, 2025)) -> pd.DataFrame:
    """
    Return a tidy DataFrame with one row per year.

    Columns
    -------
    year, forest_law_strength, indigenous_rights_score, enforcement_capacity,
    amazon_plan_phase, amazon_fund_active, car_registry_stage,
    demarcation_posture, licensing_strictness, key_events
    """
    rows = []
    for year in years:
        if year in POLICY_SCORES:
            row = {"year": year}
            row.update(POLICY_SCORES[year])
            rows.append(row)
        else:
            rows.append({"year": year, "key_events": "CHECK — year not in POLICY_SCORES"})
    return pd.DataFrame(rows)


def build_milestones_df() -> pd.DataFrame:
    """Return the legal milestones as a DataFrame for easy filtering."""
    cols = ["year", "instrument", "scope", "land_cover_implication", "category"]
    return pd.DataFrame(LEGAL_MILESTONES, columns=cols)


def get_milestones_for_year(year: int) -> pd.DataFrame:
    """Return all legal milestones for a given year."""
    df = build_milestones_df()
    return df[df["year"] == year]


def get_milestones_by_category(category: str) -> pd.DataFrame:
    """
    Filter milestones by category.
    Valid: FOREST_LAW, INDIGENOUS, INSTITUTION, ENFORCEMENT, PLANNING, FINANCE, CLIMATE
    """
    df = build_milestones_df()
    return df[df["category"] == category.upper()]


def build_combined_context(years=range(1985, 2025)) -> pd.DataFrame:
    """
    Merge policy scores with political context (if available).
    Standalone: returns policy series with a 'regime' helper column.

    Regime labels (for quick visualisation):
      'redemocratisation'  1985–1988
      'new_republic_early' 1989–1994
      'FHC'                1995–2002
      'Lula_I_II'          2003–2010
      'Dilma'              2011–2016
      'Temer'              2017–2018
      'Bolsonaro'          2019–2022
      'Lula_III'           2023–2024
    """
    REGIMES = [
        (1985, 1988, "redemocratisation"),
        (1989, 1994, "new_republic_early"),
        (1995, 2002, "FHC"),
        (2003, 2010, "Lula_I_II"),
        (2011, 2016, "Dilma"),
        (2017, 2018, "Temer"),
        (2019, 2022, "Bolsonaro"),
        (2023, 2024, "Lula_III"),
    ]

    df = build_policy_series(years)

    def get_regime(year):
        for start, end, label in REGIMES:
            if start <= year <= end:
                return label
        return None

    df["regime"] = df["year"].apply(get_regime)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 4. MERGING WITH POLITICAL CONTEXT
# ─────────────────────────────────────────────────────────────────────────────
# To merge with political_context_brazil.py:
#
#   from political_context_brazil import build_political_context
#   from policy_context_brazil import build_policy_series
#
#   policy_df   = build_policy_series()
#   politics_df = build_political_context()   # already has year + state columns
#
#   # For state-level analysis (policy is national, politics is state×year):
#   full_df = politics_df.merge(policy_df, on="year", how="left")
#
#   # For president-level analysis only:
#   from political_context_brazil import build_president_series
#   pres_df = build_president_series()
#   pres_policy = pres_df.merge(policy_df, on="year", how="left")


# ─────────────────────────────────────────────────────────────────────────────
# 5. QUICK USAGE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = build_combined_context()

    print("Policy context series (1985–2024):")
    print(df[["year", "regime", "forest_law_strength", "indigenous_rights_score",
              "enforcement_capacity", "amazon_plan_phase", "amazon_fund_active",
              "demarcation_posture"]].to_string(index=False))

    print("\n--- INDIGENOUS milestones ---")
    print(get_milestones_by_category("INDIGENOUS")[
        ["year", "instrument", "land_cover_implication"]
    ].to_string(index=False))

    print("\n--- Regime means (enforcement_capacity) ---")
    print(df.groupby("regime")[
        ["forest_law_strength", "indigenous_rights_score",
         "enforcement_capacity", "demarcation_posture"]
    ].mean().round(2))
