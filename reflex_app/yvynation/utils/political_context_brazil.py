"""
political_context_brazil.py
============================
Political context data for land use / environmental policy analysis (1985–2024).
Covers ALL 26 Brazilian states + Distrito Federal + Federal Presidents.

Ideology scale (gov_ideology / president_ideology):
    -1 = Left
     0 = Centre / Centrist / Patronage machine (no clear env. posture)
     1 = Centre-Right / Moderate conservative
     2 = Right / Pro-agribusiness / Anti-environment enforcement

Ideology scores reflect the administration's dominant posture toward
environment and indigenous rights enforcement, not party label alone.
PMDB/MDB governors vary widely; each is coded individually.

Notes on data quality:
  - Acting/interim governors who served <6 months retain their predecessor's
    score unless policy demonstrably changed.
  - Tocantins (TO) created 1988; Amapá (AP) and Roraima (RR) created as states 1988.
  - Distrito Federal governors listed from 1991 (first elected governor).
  - Some year overlaps at transitions (Jan 1) are mapped to the incoming government.

Sources: Wikipedia, TSE, Geni Genealogy Projects, news archives, DIAP.
"""

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# 1. FEDERAL PRESIDENTS  (1985–2024)
# ─────────────────────────────────────────────────────────────────────────────

PRESIDENTS = [
    # (name, party, start_year, end_year, ideology, notes)
    ("José Sarney",               "PMDB",   1985, 1989,  0, "Transition govt; Amazon highway expansion, Chico Mendes era"),
    ("Fernando Collor",           "PRN",    1990, 1992,  1, "Impeached Dec 1992; created IBAMA 1989 pre-term"),
    ("Itamar Franco",             "PMDB",   1992, 1994,  0, "Acting after Collor impeachment; Plano Real"),
    ("Fernando Henrique Cardoso", "PSDB",   1995, 2002,  1, "Two terms; expanded protected areas, but weak enforcement"),
    ("Luiz Inácio Lula da Silva", "PT",     2003, 2010, -1, "Two terms; peak IBAMA/FUNAI enforcement 2004-2008"),
    ("Dilma Rousseff",            "PT",     2011, 2016, -1, "Impeached May 2016; weakened Forest Code 2012"),
    ("Michel Temer",              "PMDB",   2016, 2018,  1, "Acting/full after impeachment; rollbacks begin"),
    ("Jair Bolsonaro",            "PSL/PL", 2019, 2022,  2, "Dismantled IBAMA/FUNAI; Yanomami crisis; peak deforestation"),
    ("Luiz Inácio Lula da Silva", "PT",     2023, 2024, -1, "Third term; restored enforcement; Yanomami emergency"),
]


def build_president_series(years=range(1985, 2025)):
    rows = []
    for year in years:
        for name, party, start, end, ideo, notes in PRESIDENTS:
            if start <= year <= end:
                rows.append({
                    "year": year,
                    "president": name,
                    "president_party": party,
                    "president_ideology": ideo,
                    "president_notes": notes,
                })
                break
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 2. STATE GOVERNORS — ALL 26 STATES + DISTRITO FEDERAL
# ─────────────────────────────────────────────────────────────────────────────
# Each tuple: (name, party, start_year, end_year, ideology, notes)
# Year range = calendar years of tenure (start_year to end_year inclusive).
# Short acting periods (<6 mo) collapsed into predecessor or successor.

GOVERNORS = {

    # ── NORTE ─────────────────────────────────────────────────────────────────

    # ACRE (AC) — Amazon state; PT dominated 1999-2018
    "AC": [
        ("Nabor Júnior",       "PMDB",  1985, 1985,  0, ""),
        ("Iolanda Fleming",    "PMDB",  1986, 1986,  0, "First female gov in Brazil; acting after Nabor resignation"),
        ("Flaviano Melo",      "PMDB",  1987, 1989,  0, ""),
        ("Édison Cadaxo",      "PMDB",  1990, 1990,  0, "Acting vice-gov"),
        ("Edmundo Pinto",      "PSDB",  1991, 1991,  1, "Assassinated May 1992"),
        ("Romildo Magalhães",  "PSDB",  1992, 1994,  1, "Acting after Edmundo Pinto murder"),
        ("Orleir Cameli",      "PPR",   1995, 1998,  1, "Timber businessman; logging interests"),
        ("Jorge Viana",        "PT",    1999, 2006, -1, "Two terms; forest conservation focus"),
        ("Binho Marques",      "PT",    2007, 2010, -1, ""),
        ("Tião Viana",         "PT",    2011, 2018, -1, "Two terms"),
        ("Gladson Cameli",     "PP",    2019, 2024,  1, "Reelected 2022; Bolsonaro ally"),
    ],

    # AMAPÁ (AP) — became state 1988; territory until then
    "AP": [
        ("Anníbal Barcellos",  "PDS",   1985, 1986,  1, "Federal territory governor, military-era appointee"),
        ("Barcellos/Zanon",    "PDS",   1987, 1990,  1, "Territory phase; João Alberto Capiberibe opposition emerging"),
        ("Jorge Nova da Costa","PDS",   1991, 1994,  1, "First state governor (territory→state 1988); PDS"),
        ("João Capiberibe",    "PSB",   1995, 2002, -1, "Two terms; progressive; strong env. agenda"),
        ("Waldez Goés",        "PDT",   2003, 2006,  0, ""),
        ("João Capiberibe",    "PSB",   2007, 2010, -1, "Returned for second pair of terms"),
        ("Camilo Capiberibe",  "PSB",   2011, 2014, -1, "Son of João; same political line"),
        ("Waldez Goés",        "PDT",   2015, 2022,  0, "Two more terms"),
        ("Clécio Luís",        "SD",    2023, 2024,  0, "Elected 2022"),
    ],

    # AMAZONAS (AM) — deep Amazon; Yanomami territory
    "AM": [
        ("Gilberto Mestrinho", "PMDB",  1985, 1986,  0, "Second term; openly anti-env rhetoric"),
        ("Amazonino Mendes",   "PDC",   1987, 1989,  1, "First term; extractivist economics"),
        ("Vivaldo Frota",      "PDC",   1990, 1990,  1, "Acting vice-gov after Amazonino resignation"),
        ("Gilberto Mestrinho", "PMDB",  1991, 1994,  0, "Third term"),
        ("Amazonino Mendes",   "PPR",   1995, 2002,  1, "Two more terms (2nd + 3rd)"),
        ("Eduardo Braga",      "PMDB",  2003, 2009,  0, "Two terms; resigned for Senate Mar 2010"),
        ("Omar Aziz",          "PMN",   2010, 2013,  0, "Acting vice-gov + elected 2010; resigned 2014"),
        ("José Melo",          "PROS",  2014, 2016,  1, "Acting + elected 2014; impeached Oct 2017"),
        ("Amazonino Mendes",   "PDT",   2017, 2018,  1, "Supplementary election after Melo impeachment"),
        ("Wilson Lima",        "PSC",   2019, 2024,  1, "Reelected 2022 (União Brasil); Bolsonaro-aligned"),
    ],

    # PARÁ (PA) — major Amazon state; Kayapó, Munduruku, Xikrin territories
    "PA": [
        ("Jader Barbalho",    "PMDB",  1985, 1986,  0, "First term; SUDAM patronage politics"),
        ("Hélio Gueiros",     "PMDB",  1987, 1990,  0, ""),
        ("Jader Barbalho",    "PMDB",  1991, 1993,  0, "Second term; resigned Apr 1994"),
        ("Carlos Santos",     "PMDB",  1994, 1994,  0, "Acting vice-gov"),
        ("Almir Gabriel",     "PSDB",  1995, 2002,  1, "Two terms"),
        ("Simão Jatene",      "PSDB",  2003, 2006,  1, "First term"),
        ("Ana Júlia Carepa",  "PT",    2007, 2010, -1, "Only PT governor in PA history"),
        ("Simão Jatene",      "PSDB",  2011, 2018,  1, "Two more terms (2nd + 3rd)"),
        ("Helder Barbalho",   "MDB",   2019, 2024,  0, "Reelected 2022; centrist; COP30 host"),
    ],

    # RONDÔNIA (RO) — high deforestation frontier state
    "RO": [
        ("Ângelo Angelin",        "PMDB",  1985, 1986,  0, "Last appointed governor before direct elections"),
        ("Jerônimo Santana",      "PMDB",  1987, 1990,  0, "First elected governor"),
        ("Oswaldo Piana",         "PDS",   1991, 1994,  1, ""),
        ("Valdir Raupp",          "PMDB",  1995, 1998,  0, ""),
        ("José Bianco",           "PMDB",  1999, 2002,  0, ""),
        ("Ivo Cassol",            "PSDB",  2003, 2010,  1, "Two terms; pro-agribusiness"),
        ("Confúcio Moura",        "PMDB",  2011, 2017,  0, "Resigned to run for Senate Apr 2018"),
        ("Daniel Pereira",        "PMDB",  2018, 2018,  0, "Acting after Confúcio resignation"),
        ("Marcos Rocha",          "PSC",   2019, 2024,  2, "Reelected 2022 (União Brasil); Bolsonaro-aligned"),
    ],

    # RORAIMA (RR) — became state 1988; Yanomami territory
    "RR": [
        ("Romero Jucá",          "PDS",   1985, 1987,  1, "Federal territory governor (appointed)"),
        ("Getúlio Cruz",         "PDS",   1988, 1990,  1, "First state governor (ex-territory)"),
        ("Ottomar Pinto",        "PPR",   1991, 1994,  1, "First elected governor; military background"),
        ("Neudo Campos",         "PPB",   1995, 2002,  1, "Two terms; pro-mining, anti-demarcation"),
        ("Francisco Flamarion",  "PTB",   2003, 2006,  0, ""),
        ("José Anchieta Jr.",    "PSDB",  2007, 2014,  1, "Two terms"),
        ("Chico Rodrigues",      "PSB",   2014, 2015,  0, "Acting after Anchieta resignation for Senate"),
        ("Suely Campos",         "PP",    2015, 2018,  1, ""),
        ("Antônio Denarium",     "PROS",  2019, 2024,  2, "Reelected 2022 (PP); Bolsonaro ally; Yanomami crisis"),
    ],

    # TOCANTINS (TO) — created 1988 from northern Goiás; cerrado/Amazon ecotone
    "TO": [
        ("Siqueira Campos",     "PPR",   1989, 1994,  1, "First governor; founding father of TO; resigned for Senate"),
        ("Moisés Avelino",      "PPR",   1994, 1994,  1, "Acting after Siqueira resignation"),
        ("José Wilson Siqueira","PSDB",  1995, 1998,  1, ""),
        ("Siqueira Campos",     "PPR",   1999, 2002,  1, "Returned for second term"),
        ("Marcelo Miranda",     "PMDB",  2003, 2006,  0, ""),
        ("Siqueira Campos",     "DEM",   2007, 2010,  1, "Third term"),
        ("Siqueira Campos",     "DEM",   2011, 2014,  1, "Fourth term; impeachment proceedings"),
        ("Marcelo Miranda",     "PMDB",  2015, 2018,  0, "Returned for second stint"),
        ("Mauro Carlesse",      "DEM",   2018, 2021,  1, "Acting (Assembly president); then elected 2018; resigned 2022"),
        ("Wanderlei Barbosa",   "Republicanos", 2022, 2024, 1, "Elected 2022"),
    ],

    # ── NORDESTE ──────────────────────────────────────────────────────────────

    # ALAGOAS (AL)
    "AL": [
        ("Divaldo Suruagy",      "PDS",  1985, 1986,  1, ""),
        ("Epitácio Cafeteira",   "PMDB", 1987, 1987,  0, "Brief stint; moved to MA"),
        ("Fernando Collor",      "PFL",  1987, 1989,  1, "Later became president; resigned to run"),
        ("Geraldo Bulhões",      "PRN",  1990, 1990,  1, "Acting after Collor resignation"),
        ("Moacir Andrade",       "PRN",  1991, 1994,  1, ""),
        ("Divaldo Suruagy",      "PSDB", 1995, 1998,  1, "Second term"),
        ("Ronaldo Lessa",        "PDT",  1999, 2006, -1, "Two terms; left-leaning"),
        ("Teotônio Vilela Filho","PSDB", 2007, 2014,  1, "Two terms"),
        ("Renan Filho",          "PMDB", 2015, 2022,  0, "Two terms"),
        ("Paulo Dantas",         "MDB",  2023, 2024,  0, "Elected 2022"),
    ],

    # BAHIA (BA) — largest NE state; Atlantic Forest + cerrado
    "BA": [
        ("João Durval Carneiro", "PMDB", 1985, 1986,  0, ""),
        ("Waldir Pires",         "PMDB", 1987, 1988,  0, "Resigned to run for VP"),
        ("Nilo Moraes Coelho",   "PMDB", 1989, 1990,  0, "Acting lieutenant-gov"),
        ("Antônio Carlos Magalhães","PFL",1991, 1993,  1, "Third term; ACM machine"),
        ("Antônio Imbassahy",    "PFL",  1994, 1994,  1, "Acting after ACM resignation"),
        ("Paulo Souto",          "PFL",  1995, 1998,  1, ""),
        ("César Borges",         "PFL",  1999, 2001,  1, "Resigned for ministerial position"),
        ("Otto Alencar",         "PFL",  2002, 2002,  1, "Acting after César Borges resignation"),
        ("Paulo Souto",          "PFL",  2003, 2006,  1, "Second term"),
        ("Jaques Wagner",        "PT",   2007, 2014, -1, "Two terms; PT break with ACM machine"),
        ("Rui Costa",            "PT",   2015, 2022, -1, "Two terms"),
        ("Jerônimo Rodrigues",   "PT",   2023, 2024, -1, "Elected 2022"),
    ],

    # CEARÁ (CE) — semi-arid + caatinga; increasingly PT-aligned
    "CE": [
        ("Gonzaga Mota",         "PMDB", 1985, 1986,  0, ""),
        ("Tasso Jereissati",     "PSDB", 1987, 1990,  1, "First term; 'governo das mudanças'"),
        ("Ciro Gomes",           "PSDB", 1991, 1994,  0, "Centrist populist; resigned for minister"),
        ("Tasso Jereissati",     "PSDB", 1995, 2002,  1, "Two more terms"),
        ("Lúcio Alcântara",      "PSDB", 2003, 2006,  1, ""),
        ("Cid Gomes",            "PSB",  2007, 2014,  0, "Two terms; brother of Ciro Gomes"),
        ("Camilo Santana",       "PT",   2015, 2021, -1, "Two terms; resigned for Senate"),
        ("Izolda Cela",          "PDT",  2022, 2022, -1, "Acting after Camilo resignation"),
        ("Elmano de Freitas",    "PT",   2023, 2024, -1, "Elected 2022"),
    ],

    # MARANHÃO (MA) — Amazon/cerrado transition; Awá, Guajajara territories
    "MA": [
        ("Luís Rocha",              "PDS",   1985, 1986,  1, "Military-era holdover"),
        ("Epitácio Cafeteira",      "PMDB",  1987, 1989,  0, ""),
        ("João Alberto de Souza",   "PMDB",  1990, 1990,  0, "Acting after Cafeteira resignation"),
        ("Edison Lobão",            "PFL",   1991, 1993,  1, "Resigned Apr 1994"),
        ("J. Ribamar Fiquene",      "PFL",   1994, 1994,  1, "Acting vice-gov"),
        ("Roseana Sarney",          "PFL",   1995, 2001,  1, "Two terms; Sarney family machine"),
        ("José Reinaldo Tavares",   "PFL",   2002, 2006,  1, "Acting after Roseana resignation + reelected"),
        ("Jackson Lago",            "PDT",   2007, 2008, -1, "Cassated by TSE Mar 2009"),
        ("Roseana Sarney",          "PMDB",  2009, 2014,  1, "Returned after Lago cassation + reelected"),
        ("Flávio Dino",             "PCdoB", 2015, 2021, -1, "Resigned Apr 2022 to run for Senate"),
        ("Carlos Brandão",          "PSB",   2022, 2024,  0, "Acting vice-gov; reelected 2022"),
    ],

    # PARAÍBA (PB)
    "PB": [
        ("Wilson Braga",         "PDS",  1985, 1986,  1, ""),
        ("Tarcísio Burity",      "PMDB", 1987, 1990,  0, ""),
        ("Ronaldo Cunha Lima",   "PMDB", 1991, 1993,  0, "Resigned to run for Senate"),
        ("Antônio Mariz",        "PMDB", 1994, 1994,  0, "Acting"),
        ("Cássio Cunha Lima",    "PSDB", 1995, 1998,  1, ""),
        ("José Maranhão",        "PMDB", 1999, 2002,  0, ""),
        ("Cássio Cunha Lima",    "PSDB", 2003, 2006,  1, "Second term"),
        ("José Maranhão",        "PMDB", 2007, 2010,  0, "Second term"),
        ("Ricardo Coutinho",     "PSB",  2011, 2018, -1, "Two terms; left-leaning"),
        ("João Azevêdo",         "Cidadania", 2019, 2024, 0, "Reelected 2022 (PSB)"),
    ],

    # PERNAMBUCO (PE) — Atlantic Forest + semi-arid; large indigenous pop
    "PE": [
        ("Roberto Magalhães",    "PDS",  1985, 1986,  1, ""),
        ("Miguel Arraes",        "PMDB", 1987, 1990, -1, "First term; historic left figure"),
        ("Joaquim Francisco",    "PFL",  1991, 1994,  1, ""),
        ("Miguel Arraes",        "PMDB", 1995, 1998, -1, "Second term"),
        ("Jarbas Vasconcelos",   "PMDB", 1999, 2006,  0, "Two terms; centrist"),
        ("Eduardo Campos",       "PSB",  2007, 2014, -1, "Two terms; died in 2014 plane crash"),
        ("João Lyra Neto",       "PSB",  2014, 2014, -1, "Acting after Campos death"),
        ("Paulo Câmara",         "PSB",  2015, 2022, -1, "Two terms"),
        ("Raquel Lyra",          "PSDB", 2023, 2024,  1, "First woman to govern PE"),
    ],

    # PIAUÍ (PI)
    "PI": [
        ("Hugo Napoleão",       "PDS",  1985, 1986,  1, ""),
        ("Alberto Silva",       "PMDB", 1987, 1990,  0, ""),
        ("Freitas Neto",        "PFL",  1991, 1994,  1, ""),
        ("Mão Santa",           "PMDB", 1995, 2002,  0, "Two terms"),
        ("Wellington Dias",     "PT",   2003, 2010, -1, "Two terms"),
        ("Wilson Martins",      "PMDB", 2011, 2014,  0, ""),
        ("Wellington Dias",     "PT",   2015, 2022, -1, "Two more terms"),
        ("Rafael Fonteles",     "PT",   2023, 2024, -1, "Elected 2022"),
    ],

    # RIO GRANDE DO NORTE (RN)
    "RN": [
        ("José Agripino",       "PDS",  1985, 1986,  1, ""),
        ("Geraldo Melo",        "PMDB", 1987, 1990,  0, ""),
        ("José Agripino",       "PFL",  1991, 1994,  1, "Second term"),
        ("Garibaldi Alves",     "PMDB", 1995, 2002,  0, "Two terms"),
        ("Wilma de Faria",      "PSB",  2003, 2010,  0, "Two terms"),
        ("Rosalba Ciarlini",    "DEM",  2011, 2014,  1, ""),
        ("Robinson Faria",      "PSD",  2015, 2018,  1, ""),
        ("Fátima Bezerra",      "PT",   2019, 2024, -1, "Reelected 2022"),
    ],

    # SERGIPE (SE)
    "SE": [
        ("João Alves Filho",    "PDS",  1985, 1986,  1, ""),
        ("Antônio Maynard",     "PMDB", 1987, 1990,  0, ""),
        ("João Alves Filho",    "PFL",  1991, 1994,  1, "Second term"),
        ("Albano Franco",       "PSDB", 1995, 2002,  1, "Two terms"),
        ("João Alves Filho",    "PFL",  2003, 2006,  1, "Third term"),
        ("Marcelo Déda",        "PT",   2007, 2013, -1, "Two terms; died in office Dec 2013"),
        ("Jackson Barreto",     "PMDB", 2014, 2014,  0, "Acting after Déda death"),
        ("Jackson Barreto",     "PMDB", 2015, 2018,  0, "Elected 2014"),
        ("Belivaldo Chagas",    "PSD",  2019, 2022,  0, ""),
        ("Fábio Mitidieri",     "PSD",  2023, 2024,  0, "Elected 2022"),
    ],

    # ── CENTRO-OESTE ──────────────────────────────────────────────────────────

    # DISTRITO FEDERAL (DF) — elected governors from 1991
    "DF": [
        ("José Ornelas Motta",  "PMDB", 1985, 1987,  0, "Appointed governor (territory/federal district)"),
        ("Joaquim Roriz",       "PMDB", 1988, 1990,  0, "Appointed by Sarney; clientelist politics"),
        ("Joaquim Roriz",       "PMDB", 1991, 1994,  0, "First elected governor"),
        ("Cristovam Buarque",   "PT",   1995, 1998, -1, "Progressive; education reform"),
        ("Joaquim Roriz",       "PMDB", 1999, 2006,  0, "Two more terms; clientelism"),
        ("José Roberto Arruda", "DEM",  2007, 2009,  1, "Resigned amid corruption scandal"),
        ("Paulo Otávio",        "DEM",  2010, 2010,  1, "Acting; then impeached"),
        ("Rogério Rosso",       "PMDB", 2010, 2010,  0, "Acting Assembly president"),
        ("Agnelo Queiroz",      "PT",   2011, 2014, -1, ""),
        ("Rodrigo Rollemberg",  "PSB",  2015, 2018,  0, ""),
        ("Ibaneis Rocha",       "MDB",  2019, 2024,  0, "Reelected 2022; suspended briefly by STF 2023"),
    ],

    # GOIÁS (GO) — cerrado heartland; soy/beef expansion
    "GO": [
        ("Iris Rezende",        "PMDB", 1985, 1986,  0, "First term"),
        ("Henrique Santillo",   "PMDB", 1987, 1990,  0, ""),
        ("Iris Rezende",        "PMDB", 1991, 1994,  0, "Second term"),
        ("Maguito Vilela",      "PMDB", 1995, 1998,  0, ""),
        ("Marconi Perillo",     "PSDB", 1999, 2006,  1, "Two terms"),
        ("Alcides Rodrigues",   "PP",   2007, 2010,  1, ""),
        ("Marconi Perillo",     "PSDB", 2011, 2018,  1, "Two more terms"),
        ("Ronaldo Caiado",      "DEM",  2019, 2024,  2, "Reelected 2022 (União Brasil); strong agribusiness/anti-env posture"),
    ],

    # MATO GROSSO (MT) — agribusiness frontier; highest Amazon deforestation
    "MT": [
        ("Júlio Campos",        "PDS",  1985, 1986,  1, ""),
        ("Carlos Bezerra",      "PMDB", 1987, 1989,  0, ""),
        ("Jaime Campos",        "PFL",  1990, 1990,  1, "Acting after Carlos Bezerra resignation"),
        ("Dante de Oliveira",   "PMDB", 1991, 1994,  0, ""),
        ("Dante de Oliveira",   "PMDB", 1995, 1998,  0, "Reelected"),
        ("Blairo Maggi",        "PPS",  1999, 2006,  2, "Two terms; 'soy king'; Greenpeace 'Chainsaw Award'"),
        ("Silval Cunha",        "PMDB", 2007, 2014,  1, "Two terms; soy-aligned"),
        ("Pedro Taques",        "PSDB", 2015, 2018,  1, ""),
        ("Mauro Mendes",        "PSB",  2019, 2024,  2, "Reelected 2022 (União Brasil); agro-conservative"),
    ],

    # MATO GROSSO DO SUL (MS) — Pantanal + cerrado; Terena, Guarani territories
    "MS": [
        ("Marcelo Miranda Soares","PDS", 1985, 1986,  1, ""),
        ("Marcelo Miranda Soares","PMDB",1987, 1990,  1, ""),
        ("Pedro Pedrossian",    "PTB",  1991, 1994,  1, "Second term"),
        ("Wilson Barbosa Martins","PMDB",1995, 1998,  0, ""),
        ("José Orcírio dos Santos","PT", 1999, 2006, -1, "Two terms; first PT governor of MS"),
        ("André Puccinelli",    "PMDB", 2007, 2014,  0, "Two terms"),
        ("Reinaldo Azambuja",   "PSDB", 2015, 2022,  1, "Two terms"),
        ("Eduardo Riedel",      "PSDB", 2023, 2024,  1, "Elected 2022"),
    ],

    # ── SUDESTE ───────────────────────────────────────────────────────────────

    # ESPÍRITO SANTO (ES)
    "ES": [
        ("Gerson Camata",       "PMDB", 1985, 1986,  0, ""),
        ("Max Mauro",           "PMDB", 1987, 1990,  0, ""),
        ("Albuíno Azeredo",     "PDT",  1991, 1994,  0, ""),
        ("Vitor Buaiz",         "PT",   1995, 1998, -1, ""),
        ("José Ignácio",        "PSDB", 1999, 2002,  1, ""),
        ("Paulo Hartung",       "PMDB", 2003, 2010,  0, "Two terms"),
        ("Renato Casagrande",   "PSB",  2011, 2014,  0, ""),
        ("Paulo Hartung",       "PMDB", 2015, 2018,  0, "Third term"),
        ("Renato Casagrande",   "PSB",  2019, 2024,  0, "Second pair of terms; reelected 2022"),
    ],

    # MINAS GERAIS (MG) — cerrado + Atlantic Forest; indigenous territories
    "MG": [
        ("Hélio Garcia",        "PMDB", 1985, 1986,  0, "Completed Tancredo Neves' term"),
        ("Newton Cardoso",      "PMDB", 1987, 1990,  0, ""),
        ("Hélio Garcia",        "PTB",  1991, 1994,  0, "Second term, different party"),
        ("Eduardo Azeredo",     "PSDB", 1995, 1998,  1, ""),
        ("Itamar Franco",       "PMDB", 1999, 2002,  0, "Former president; broke with FHC"),
        ("Aécio Neves",         "PSDB", 2003, 2009,  1, "Two terms; resigned to run for Senate"),
        ("Antônio Anastasia",   "PSDB", 2010, 2013,  1, "Completed Aécio's term + reelected"),
        ("Alberto Pinto Coelho","PSDB", 2014, 2014,  1, "Acting; Anastasia resigned for Senate"),
        ("Fernando Pimentel",   "PT",   2015, 2018, -1, ""),
        ("Romeu Zema",          "NOVO", 2019, 2024,  2, "Reelected 2022; fiscal/anti-env posture"),
    ],

    # RIO DE JANEIRO (RJ) — Atlantic Forest remnants; Guarani territory
    "RJ": [
        ("Leonel Brizola",      "PDT",  1985, 1986, -1, "First term; historic left figure"),
        ("Moreira Franco",      "PMDB", 1987, 1990,  0, ""),
        ("Leonel Brizola",      "PDT",  1991, 1993, -1, "Second term; resigned for VP campaign"),
        ("Nilo Batista",        "PDT",  1994, 1994, -1, "Acting after Brizola resignation"),
        ("Marcello Alencar",    "PSDB", 1995, 1998,  1, ""),
        ("Anthony Garotinho",   "PDT",  1999, 2001,  0, "Resigned to run for president"),
        ("Benedita da Silva",   "PT",   2002, 2002, -1, "Acting after Garotinho resignation"),
        ("Rosinha Garotinho",   "PMDB", 2003, 2006,  0, ""),
        ("Sérgio Cabral",       "PMDB", 2007, 2013,  0, "Two terms; resigned amid Lava Jato"),
        ("Luiz Fernando Pezão", "PMDB", 2014, 2018,  0, "Arrested Nov 2018 while still in office"),
        ("Wilson Witzel",       "PSC",  2019, 2020,  1, "Impeached Apr 2021"),
        ("Cláudio Castro",      "PL",   2021, 2024,  1, "Vice-gov; assumed after Witzel impeachment; reelected 2022"),
    ],

    # SÃO PAULO (SP) — largest state; Atlantic Forest; PSDB bastion 1995-2018
    "SP": [
        ("Franco Montoro",      "PMDB", 1985, 1986,  0, "Transition-era centrist"),
        ("Orestes Quércia",     "PMDB", 1987, 1990,  0, ""),
        ("Luiz Fleury",         "PMDB", 1991, 1994,  0, ""),
        ("Mário Covas",         "PSDB", 1995, 2001,  1, "Two terms; died in office Mar 2001"),
        ("Geraldo Alckmin",     "PSDB", 2001, 2006,  1, "Completed Covas + 1st full term"),
        ("Cláudio Lembo",       "PFL",  2006, 2006,  1, "Acting after Alckmin resignation for pres. race"),
        ("José Serra",          "PSDB", 2007, 2010,  1, "Resigned to run for president"),
        ("Alberto Goldman",     "PSDB", 2010, 2010,  1, "Acting after Serra resignation"),
        ("Geraldo Alckmin",     "PSDB", 2011, 2018,  1, "Two more terms; resigned 2018 for pres. race"),
        ("Márcio França",       "PSB",  2018, 2018,  0, "Acting after Alckmin resignation"),
        ("João Doria",          "PSDB", 2019, 2022,  1, "Resigned Apr 2022 for pres. race"),
        ("Rodrigo Garcia",      "PSDB", 2022, 2022,  1, "Acting after Doria resignation"),
        ("Tarcísio de Freitas", "Republicanos", 2023, 2024, 2, "Elected 2022; Bolsonaro ally; anti-env posture"),
    ],

    # ── SUL ───────────────────────────────────────────────────────────────────

    # PARANÁ (PR)
    "PR": [
        ("José Richa",          "PMDB", 1985, 1986,  0, ""),
        ("Álvaro Dias",         "PMDB", 1987, 1990,  0, ""),
        ("Roberto Requião",     "PMDB", 1991, 1994,  0, "First term; nationalist-populist"),
        ("Jaime Lerner",        "PDT",  1995, 2002,  1, "Two terms; urban planner; pro-market"),
        ("Roberto Requião",     "PMDB", 2003, 2010,  0, "Two more terms"),
        ("Beto Richa",          "PSDB", 2011, 2018,  1, "Two terms; resigned 2018 for Senate"),
        ("Cida Borghetti",      "PP",   2018, 2018,  1, "Acting after Beto Richa resignation"),
        ("Ratinho Júnior",      "PSD",  2019, 2024,  1, "Reelected 2022; conservative-centrist"),
    ],

    # RIO GRANDE DO SUL (RS)
    "RS": [
        ("Jair Soares",         "PDS",  1985, 1986,  1, ""),
        ("Pedro Simon",         "PMDB", 1987, 1990,  0, ""),
        ("Alceu Collares",      "PDT",  1991, 1994,  0, ""),
        ("Antônio Britto",      "PMDB", 1995, 1998,  0, ""),
        ("Olívio Dutra",        "PT",   1999, 2002, -1, ""),
        ("Germano Rigotto",     "PMDB", 2003, 2006,  0, ""),
        ("Yeda Crusius",        "PSDB", 2007, 2010,  1, ""),
        ("Tarso Genro",         "PT",   2011, 2014, -1, ""),
        ("José Ivo Sartori",    "PMDB", 2015, 2018,  0, ""),
        ("Eduardo Leite",       "PSDB", 2019, 2021,  1, "Resigned to run for PSDB leadership"),
        ("Ranolfo Vieira Jr.",  "PSDB", 2022, 2022,  1, "Acting after Leite resignation"),
        ("Eduardo Leite",       "PSDB", 2023, 2024,  1, "Returned; reelected 2022"),
    ],

    # SANTA CATARINA (SC)
    "SC": [
        ("Pedro Ivo Campos",    "PMDB", 1985, 1986,  0, ""),
        ("Pedro Ivo Campos",    "PMDB", 1987, 1990,  0, "First elected; died in office 1990"),
        ("Casildo Maldaner",    "PMDB", 1990, 1990,  0, "Acting after Pedro Ivo death"),
        ("Vilson Kleinübing",   "PFL",  1991, 1994,  1, ""),
        ("Paulo Afonso",        "PMDB", 1995, 1998,  0, ""),
        ("Esperidião Amin",     "PPB",  1999, 2002,  1, "Second term (first was 1983-87)"),
        ("Luiz Henrique",       "PMDB", 2003, 2010,  0, "Two terms"),
        ("Raimundo Colombo",    "DEM",  2011, 2018,  1, "Two terms"),
        ("Carlos Moisés",       "PSL",  2019, 2022,  2, "Bolsonaro-aligned"),
        ("Jorginho Mello",      "PL",   2023, 2024,  2, "Elected 2022; Bolsonaro ally"),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. BUILDER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def build_president_series(years=range(1985, 2025)) -> pd.DataFrame:
    rows = []
    for year in years:
        for name, party, start, end, ideo, notes in PRESIDENTS:
            if start <= year <= end:
                rows.append({
                    "year": year,
                    "president": name,
                    "president_party": party,
                    "president_ideology": ideo,
                    "president_notes": notes,
                })
                break
    return pd.DataFrame(rows)


def build_governor_series(state: str, years=range(1985, 2025)) -> pd.DataFrame:
    """Return a DataFrame with one row per year for the given state."""
    gov_list = GOVERNORS[state]
    rows = []
    for year in years:
        matched = False
        for name, party, start, end, ideo, notes in gov_list:
            if start <= year <= end:
                rows.append({
                    "year": year,
                    "state": state,
                    "governor": name,
                    "gov_party": party,
                    "gov_ideology": ideo,
                    "gov_notes": notes,
                })
                matched = True
                break
        if not matched:
            rows.append({
                "year": year,
                "state": state,
                "governor": None,
                "gov_party": None,
                "gov_ideology": None,
                "gov_notes": "CHECK — gap in data",
            })
    return pd.DataFrame(rows)


def build_political_context(
    states: tuple = None,
    years=range(1985, 2025)
) -> pd.DataFrame:
    """
    Master table: one row per (state × year) with federal + state
    political variables.

    Parameters
    ----------
    states : tuple of state abbreviations, or None for ALL states + DF.
    years  : iterable of years (default 1985–2024).

    Columns
    -------
    year, state,
    president, president_party, president_ideology, president_notes,
    governor, gov_party, gov_ideology, gov_notes,
    alignment        : 1 if both executive levels on same ideological side,
                       0 if opposed, None if data missing.
    combined_pressure: mean of (president_ideology + gov_ideology).
                       Higher → more right/conservative/pro-agribusiness.
                       Range: -2 (both left) to +2 (both right).
    """
    if states is None:
        states = tuple(GOVERNORS.keys())

    pres_df = build_president_series(years)

    def alignment(row):
        if pd.isna(row["gov_ideology"]) or pd.isna(row["president_ideology"]):
            return None
        left_gov  = row["gov_ideology"] <= 0
        left_pres = row["president_ideology"] <= 0
        return int(left_gov == left_pres)

    all_dfs = []
    for state in states:
        gov_df = build_governor_series(state, years)
        merged = gov_df.merge(pres_df, on="year", how="left")
        merged["alignment"] = merged.apply(alignment, axis=1)
        merged["combined_pressure"] = (
            merged["gov_ideology"].fillna(0) + merged["president_ideology"].fillna(0)
        ) / 2
        all_dfs.append(merged)

    df = pd.concat(all_dfs, ignore_index=True)

    cols = [
        "year", "state",
        "president", "president_party", "president_ideology", "president_notes",
        "governor",  "gov_party",       "gov_ideology",       "gov_notes",
        "alignment", "combined_pressure",
    ]
    return df[cols]


# ─────────────────────────────────────────────────────────────────────────────
# 4. CONVENIENCE LOOKUPS
# ─────────────────────────────────────────────────────────────────────────────

ALL_STATES = tuple(GOVERNORS.keys())

# Grouped by region — useful for regional analysis
REGIONS = {
    "Norte":       ("AC", "AP", "AM", "PA", "RO", "RR", "TO"),
    "Nordeste":    ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "Centro-Oeste":("DF", "GO", "MT", "MS"),
    "Sudeste":     ("ES", "MG", "RJ", "SP"),
    "Sul":         ("PR", "RS", "SC"),
}


def build_regional_context(region: str, years=range(1985, 2025)) -> pd.DataFrame:
    """Convenience wrapper to build context for all states in a region."""
    return build_political_context(states=REGIONS[region], years=years)


# ─────────────────────────────────────────────────────────────────────────────
# 5. QUICK USAGE EXAMPLE
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    # Full national dataset
    df = build_political_context()
    print(f"Total rows: {len(df)} ({len(df['state'].unique())} states × up to 40 years)")
    print(f"States covered: {sorted(df['state'].unique())}\n")

    # Preview Norte region — most relevant for Amazon analysis
    norte = build_regional_context("Norte")
    print("Norte region preview (2019-2022):")
    mask = norte["year"].between(2019, 2022)
    print(norte[mask][["year","state","governor","gov_ideology","president_ideology","combined_pressure"]].to_string(index=False))

    # --- Merging with your land use data ---
    #
    # land_use_df must have columns: year, state (two-letter abbreviation)
    #
    # analysis_df = land_use_df.merge(
    #     build_political_context(),
    #     on=["year", "state"],
    #     how="left"
    # )
    #
    # --- Original 4-state case studies ---
    #
    # case_studies = build_political_context(states=("MG", "MA", "PA", "AM"))
