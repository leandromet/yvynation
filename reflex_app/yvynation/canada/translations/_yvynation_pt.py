"""Portuguese text specific to Yvynation's Canada page (see _yvynation_en)."""

YVY_PT: dict[str, str] = {
    "app_name": "Yvynation Canadá — áreas protegidas",
    "nav_subtitle": "Histórico da cobertura do solo nas áreas protegidas e "
        "conservadas do Canadá (CPCAD), começando pela Colúmbia Britânica",
    "mobile_parcel_zones_toggle": "Área e zonas",
    "go_to_brazil": "Brasil",

    "search_placeholder": "nome da área protegida, endereço, código postal, coordenada…",
    "search_areas_heading": "Áreas protegidas",
    "search_places_note": "Um lugar apenas enquadra o mapa e marca um "
        "alfinete. Clique em uma área protegida (contorno verde-azulado) "
        "para analisá-la.",
    "search_place_hint": "clique em uma área protegida no mapa para analisá-la",
    "echo_area_cpcad": "área protegida",
    "erro_sem_area": "Nenhuma área protegida aqui nas províncias exibidas. "
        "Os contornos verde-azulados no mapa são as áreas do CPCAD que você "
        "pode selecionar.",
    "candidates_note": "Várias áreas protegidas se sobrepõem aqui — "
        "designações costumam estar umas dentro das outras. Escolha qual "
        "analisar (a menor primeiro):",

    "provinces_title": "Províncias exibidas",
    "ca_add_province": "Adicionar uma província…",
    "ca_provinces_hint": "A Colúmbia Britânica carrega primeiro. Clicar no "
        "mapa ou buscar um lugar em outra província a adiciona.",
    "ca_ocap_note": "Áreas governadas ou de propriedade de povos indígenas "
        "não estão incluídas, em respeito aos princípios OCAP® de soberania "
        "de dados das Primeiras Nações.",
    "ca_source_note": "Fonte: Canadian Protected and Conserved Areas "
        "Database (CPCAD), ECCC — Open Government Licence – Canada.",
    "ca_parts_title": "Partes desta área",
    "ca_parts_analysing_all": "Analisando a área inteira — todas as {total} partes.",
    "ca_parts_analysing_some": "Analisando {n} de {total} partes.",
    "ca_parts_hint": "Marque partes abaixo, ou clique nelas no mapa, e "
        "analise a seleção.",
    "ca_parts_apply": "Analisar partes selecionadas",
    "ca_parts_all": "Área inteira",
    "ca_parts_clear": "Limpar",
    "ca_parts_more": "Listando as {n} maiores de {total} partes — clique em "
        "qualquer parte no mapa para escolhê-la.",
    "ca_parts_zoom": "Aproximar desta parte",

    "park_area_reported": "Área informada (CPCAD)",
    "area_card_title": "Área protegida",
    "area_name_fr": "Nome em francês",
    "area_name_ind": "Nome indígena",
    "area_province": "Província / território",
    "area_pa_oecm": "AP / OMEC",
    "area_governance": "Governança",
    "area_owner_type": "Tipo de proprietário",
    "area_cpcad_id": "Código CPCAD",
    "area_disclosure": "Limite e atributos como publicados no CPCAD "
        "(Environment and Climate Change Canada). Áreas governadas ou de "
        "propriedade de povos indígenas não estão incluídas (OCAP®). O "
        "Yvynation descreve a cobertura do solo dentro e ao redor de uma área "
        "protegida; não emite parecer sobre a gestão da área.",
    "zones_note": "A área protegida e anéis medidos para fora do seu limite "
        "— compare dentro com ao redor.",
    "zona_park": "Área protegida",

    "tab_cobertura": "Culturas (AAFC)",
    "cobertura_empty": "Sem dados ainda — selecione uma área protegida.",
    "cobertura_out_of_range": "O inventário agrícola da AAFC não cobre esta "
        "latitude — esperado acima de cerca de 54–58°N, não é uma falha. As "
        "abas Cobertura do solo, Floresta, Biomassa e Fogo continuam "
        "respondendo.",
    "tab_vlce2": "Cobertura do solo",
    "legend_vlce2": "Cobertura do solo (NTEMS VLCE2)",
    "legend_vlce2_palette": "As classes aparecem aqui quando o histórico carregar.",
    "vlce2_running": "Buscando o histórico de cobertura 1984–2022…",
    "vlce2_empty": "Sem dados ainda — selecione uma área protegida.",
    "vlce2_out_of_range": "O VLCE2 não tem pixels aqui — ele mapeia as "
        "ecozonas florestais do Canadá, não as pradarias nem o ártico. A aba "
        "Culturas cobre as áreas agrícolas.",
    "vlce2_attribution": "NTEMS VLCE2 — Hermosilla et al., NRCan / Canadian "
        "Forest Service · 30 m · 1984–2022",
    "erro_trajetoria_vlce2": "Não foi possível calcular o histórico de cobertura: {detail}",
    "erro_vlce2_sem_classes": "Sem cobertura VLCE2 nesta área — fora das "
        "ecozonas florestais mapeadas pelo NTEMS.",
    "floresta_split_start_date": "Dividido no ano de criação",
    "legend_hansen_split_start_date": "Dividido no ano de criação",
    "floresta_before_parcel": "Antes da criação",
    "floresta_after_parcel": "Depois da criação",
    "floresta_no_start_date_note": "O CPCAD não registra ano de criação para "
        "esta área, então a perda aparece como uma série única, sem dividir "
        "numa data inventada.",
    "paisagem_legend_note": "A contagem de fragmentos segue as classes do "
        "inventário agrícola, que separam culturas em detalhe e floresta de "
        "forma grosseira — comparável entre esta área protegida e seus "
        "anéis, não entre uma paisagem agrícola e uma florestal.",

    "how_to_read": "Como ler",
    "read_cobertura": (
        "Gráfico — uma barra por ano (2009–2025). Cada cor é uma classe do "
        "inventário agrícola da Agriculture and Agri-Food Canada; a altura é "
        "a área que ela ocupa na zona escolhida acima. Mude para Percentual "
        "para comparar anos independentemente do tamanho da zona. A linha "
        "tracejada marca o ano de criação da área.\n"
        "Tabela — as classes presentes no ano selecionado, da maior para a "
        "menor, com hectares e participação na zona.\n"
        "Mapa — a mesma classificação no ano selecionado; a legenda no canto "
        "do mapa lista as classes presentes.\n"
        "Limites — um inventário agrícola: culturas são mapeadas em detalhe, "
        "floresta de forma grosseira; a cobertura termina por volta de "
        "54–58°N e só é nacional a partir de 2011. Mais ao norte, use a aba "
        "Cobertura do solo."),
    "read_vlce2": (
        "Gráfico — uma barra por ano, 1984–2022. Cada cor é uma classe de "
        "cobertura (conífera, folhosa, mista, arbustos, herbáceas, áreas "
        "úmidas, água, solo exposto…); a altura é a área na zona escolhida "
        "acima. Uma faixa de floresta que cai e depois cresce devagar "
        "costuma ser fogo ou corte seguidos de regeneração por arbustos.\n"
        "Tabela — as classes no ano selecionado, da maior para a menor.\n"
        "Mapa — a classificação daquele ano; troque o ano na legenda do mapa "
        "para ver quando uma mudança aconteceu.\n"
        "Limites — o VLCE2 mapeia só as ecozonas florestais (não as pradarias "
        "nem o ártico) e termina em 2022. Pixels não classificados não são "
        "contados, então o total de um ano pode ficar abaixo da área da "
        "zona."),
    "read_transicoes": (
        "Diagrama — a coluna da esquerda é a cobertura no primeiro ano, a da "
        "direita no segundo; a largura de cada faixa é a área que passou de "
        "uma classe para outra. Faixas retas são terra que não mudou; faixas "
        "que se cruzam são mudança.\n"
        "Tabela — as maiores transições, em hectares.\n"
        "Mapa — os dois anos lado a lado; arraste o divisor para comparar.\n"
        "Limites — feito sobre o inventário agrícola: entre anos próximos, "
        "muitas 'transições' são rotação de culturas ou ruído de "
        "classificação, por isso anos muito próximos são recusados."),
    "read_floresta": (
        "Gráfico — perda de cobertura arbórea por ano (Hansen Global Forest "
        "Change, desde 2001), dividida no ano de criação da área: laranja "
        "antes, vermelho depois — se o desmate continuou depois que a área "
        "foi protegida.\n"
        "Quadros — perda total em cada período, e ganho (2000–2012, sem data, "
        "por isso nunca subtraído de 25 anos de perda).\n"
        "Idade do povoamento — idade medida da floresta em 2019 (NTEMS): "
        "média, mediana e a parte da zona que é floresta.\n"
        "Mapa — os pixels de perda, coloridos pela mesma divisão.\n"
        "Limites — 'perda' é qualquer distúrbio que remove o povoamento "
        "(fogo, corte, insetos, vento), não desmatamento; não diz por que as "
        "árvores sumiram."),
    "read_biomassa": (
        "Gráfico — biomassa acima do solo em megagramas (toneladas) por "
        "hectare, para cada ano publicado pelo ESA CCI. Uma queda que "
        "coincide com um ano de perda na aba Floresta é o mesmo evento visto "
        "por outro sensor.\n"
        "Tabela — os valores anuais e o total da zona.\n"
        "Mapa — a biomassa no ano selecionado; verde mais escuro tem mais.\n"
        "Limites — pixels de 100 m; a estimativa é mais fraca sobre neve "
        "persistente e florestas esparsas do norte, então pequenas variações "
        "entre anos estão dentro da incerteza do produto."),
    "read_paisagem": (
        "Tabela — uma linha por zona (a área e cada anel). Fragmentos: em "
        "quantos pedaços separados as classes se dividem. Maior %: parte "
        "ocupada pelo maior pedaço. Densidade de borda: metros de borda por "
        "hectare. Meff (tamanho efetivo de malha): o tamanho esperado do "
        "pedaço onde cai um ponto ao acaso — maior significa menos "
        "fragmentado. Shannon, Simpson e Equitabilidade: quão misturadas "
        "estão as classes.\n"
        "Gráfico — Meff por zona: uma área bem menos fragmentada que seus "
        "anéis se destaca.\n"
        "Mapa — os fragmentos no ano selecionado.\n"
        "Limites — calculado sobre as classes do inventário agrícola: compare "
        "uma área com os próprios anéis, não uma paisagem agrícola com uma "
        "florestal."),
    "read_fogo": (
        "Gráfico — parte da zona que queimou a cada ano, pelo MODIS (500 m, "
        "desde 2001) ou pela classe de área queimada do inventário agrícola "
        "(30 m, desde 2009); o seletor escolhe a fonte. Barra hachurada é o "
        "ano corrente, ainda incompleto.\n"
        "Quadros — anos com alguma queima, frequência média e a queima mais "
        "recente.\n"
        "Mapa — todos os anos somados: vermelho mais escuro queimou mais "
        "vezes.\n"
        "Limites — pixels MODIS têm cerca de 21 ha, então em zonas pequenas "
        "os efeitos de borda dominam; as duas fontes nunca são somadas num "
        "só número."),
    "read_validacao": (
        "Comparação — o inventário agrícola contra o VLCE2 no mesmo ano, num "
        "nível de grupos que os dois produtos sabem nomear (floresta, "
        "arbustos, campo, cultura, água, área úmida, solo exposto, "
        "construído).\n"
        "Concordância — a parte da zona em que os dois indicam o mesmo grupo; "
        "a tabela traz a área e a concordância de cada grupo do inventário.\n"
        "Mapa — os dois produtos lado a lado; arraste o divisor.\n"
        "Limites — dois produtos independentes discordarem é informação, não "
        "erro de um deles; parte da discordância vem das duas grades não se "
        "alinharem nas bordas das classes."),

    "qs_title": "Comece em 30 segundos",
    "qs_step1_lead": "Encontre uma área protegida",
    "qs_step1_body": "pelo nome, endereço, código postal ou coordenada — ou "
        "clique num contorno verde-azulado no mapa. A Colúmbia Britânica "
        "carrega primeiro; outras províncias carregam quando você vai até "
        "elas.",
    "qs_step2_lead": "Leia as abas:",
    "qs_step2_body": "culturas (AAFC) e cobertura do solo desde 1984 "
        "carregam sozinhas; Floresta, Biomassa, Paisagem e Fogo rodam sob "
        "demanda.",
    "qs_step3_lead": "Compare zonas",
    "qs_step3_body": "— a própria área e anéis de 500 m, 2 km e 5 km — para "
        "ver dentro contra ao redor.",
    "qs_step4_lead": "Escolha partes:",
    "qs_step4_body": "uma área formada por polígonos separados pode ser "
        "analisada parte por parte na barra lateral.",
    "qs_more": "Cada aba começa com um breve 'Como ler'. O guia completo "
        "explica camadas, exportação e o que os dados não podem dizer.",

    "help_dialog_title": "Como usar o Yvynation Canadá",
    "help_dialog_desc": "Sete passos de uma área protegida até a análise, e "
        "o que esta página não pode afirmar.",
    "help_step1_title": "1. Encontre uma área protegida",
    "help_step1_body": "Digite o nome da área, um endereço, um código postal "
        "ou uma coordenada, ou clique num contorno verde-azulado no mapa. "
        "Onde designações se sobrepõem, você escolhe qual. A Colúmbia "
        "Britânica carrega primeiro; um clique ou busca em outra província a "
        "adiciona.",
    "help_step2_title": "2. Leia o cartão da área",
    "help_step2_body": "Os campos do CPCAD como publicados — designação, AP "
        "ou OMEC, governança, situação, ano de criação — e a área informada "
        "ao lado da área calculada pelo limite.",
    "help_step3_title": "3. Zonas e partes",
    "help_step3_body": "Toda análise roda na área e em anéis de 500 m, 2 km "
        "e 5 km ao redor; escolha a zona acima de cada gráfico. Uma área "
        "formada por polígonos separados pode ser analisada parte por parte.",
    "help_step4_title": "4. Culturas e cobertura do solo",
    "help_step4_body": "O inventário agrícola da AAFC (2009–2025, ao sul de "
        "cerca de 54–58°N) e a cobertura NTEMS VLCE2 (1984–2022, ecozonas "
        "florestais) — dois históricos, cada um com camada no mapa e tabela.",
    "help_step5_title": "5. Floresta, biomassa, paisagem",
    "help_step5_body": "Perda Hansen dividida no ano de criação, idade do "
        "povoamento NTEMS, biomassa ESA CCI e métricas de fragmentação para "
        "todas as zonas de uma vez.",
    "help_step6_title": "6. Fogo e validação",
    "help_step6_body": "Área queimada pelo MODIS e pelo inventário agrícola, "
        "e o inventário conferido contra o VLCE2 no mesmo ano.",
    "help_step7_title": "7. Exportar",
    "help_step7_body": "Cada gráfico baixa como PNG e cada tabela como CSV "
        "pelo ícone ao lado; Exportar reúne as tabelas numa planilha.",
    "help_limitations_title": "O que esta página não pode dizer",
    "help_limit_1": "Áreas governadas ou de propriedade indígena não estão "
        "aqui, por princípio (OCAP®), e não há análise de terras indígenas "
        "canadenses.",
    "help_limit_2": "O inventário agrícola termina por volta de 54–58°N; o "
        "VLCE2 cobre só ecozonas florestais; o MapBiomas (página do Brasil) "
        "não cobre o Canadá.",
    "help_limit_3": "A 'perda' Hansen é qualquer distúrbio que remove o "
        "povoamento — fogo, corte, insetos — não desmatamento.",
    "help_limit_4": "Nenhum parecer sobre gestão ou conformidade é emitido: "
        "os números descrevem a cobertura do solo, não a gestão.",
    "cite_dialog_desc": "O Yvynation Canadá e os dados que ele usa.",
}
