/* Yvynation — demonstrações em rolagem de uma área (/demonstracao/<modo>, /walkthrough/<mode>).
 *
 * Um arquivo para três artigos — terra indígena, unidade de conservação e
 * área desenhada — que diferem no texto (terra_indigena.html,
 * unidade_conservacao.html, desenho.html e as versões .en.html) e não nas
 * contas. O modo vem do atributo data-modo do topo; a língua, do lang da raiz
 * (ctx.t(pt, en)). Os números vêm de /_demonstracao/yvynation.json
 * (utils/demonstracao.py), das mesmas funções das páginas de análise.
 */
(function () {
  var R = window.Reportagem, fmt = R.fmt, graf = R.graf;

  // vegetação nativa na Coleção 11 (utils/demonstracao.py::NATIVAS)
  var NATIVAS = [3, 4, 5, 6, 49, 10, 11, 12, 13, 29, 32, 50, 77, 84];
  var COR = { area: "#d98324", buffer: "#4f8f6f" };
  var SERIE = {
    mb_defor_primary: { rotulo: ["desmatamento de vegetação primária (MapBiomas)", "primary vegetation clearing (MapBiomas)"], cor: "#c0392b" },
    mb_secondary_growth: { rotulo: ["regeneração, vegetação secundária (MapBiomas)", "regrowth, secondary vegetation (MapBiomas)"], cor: "#30a46c" },
    hansen_loss: { rotulo: ["perda de cobertura arbórea (Hansen)", "tree cover loss (Hansen)"], cor: "#7b3294" },
    mb_fire_scar: { rotulo: ["cicatriz de fogo (MapBiomas Fogo)", "fire scar (MapBiomas Fire)"], cor: "#f08c00" }
  };
  var T;   // ctx.t, guardado no primeiro uso

  function modo(ctx) { var t = ctx.$(".rp-topo"); return (t && t.dataset.modo) || "terra-indigena"; }
  function en() { return T("pt", "en") === "en"; }
  function nm(c) { return (en() && c.nome_en) || c.nome; }
  // "da terra indígena" / "the Indigenous land"
  function rotuloArea(d) {
    return { "terra-indigena": T("terra indígena", "Indigenous land"), "unidade-conservacao": T("unidade de conservação", "conservation unit"),
             desenho: T("área desenhada", "drawn area") }[d.modo] || T("área", "area");
  }
  function feat(g) { return { type: "Feature", properties: {}, geometry: g && g.geometry ? g.geometry : g }; }
  function vet(d, comBuffer) {
    var v = { area: { geojson: feat(d.area.geojson), estilo: { color: "#ffd400", weight: 2.5, fillOpacity: 0 } } };
    if (comBuffer && d.area.buffer_geojson) v.buffer = { geojson: feat(d.area.buffer_geojson), estilo: { color: "#9cc2ac", weight: 2, dashArray: "6 5", fillColor: "#9cc2ac", fillOpacity: 0.08 } };
    return v;
  }
  function camada(d, k, op) { var c = d.camadas && d.camadas[k]; return c ? Object.assign({}, c, op ? { opacity: op } : {}) : null; }
  function soma(lista) { return (lista || []).reduce(function (a, c) { return a + c.ha; }, 0); }
  function nativa(lista) { return (lista || []).filter(function (c) { return NATIVAS.indexOf(c.id) >= 0; }).reduce(function (a, c) { return a + c.ha; }, 0); }
  function pctNativa(d, zona, ano) { var l = d.mapbiomas[zona][String(ano)]; var t = soma(l); return t ? (100 * nativa(l)) / t : null; }
  function legenda(lista, titulo) {
    return "<b>" + titulo + "</b>" + (lista || []).slice(0, 6).map(function (c) { return '<span><i style="background:' + c.cor + '"></i>' + fmt.esc(nm(c)) + "</span>"; }).join("");
  }
  function faltou(el, nome) {
    el.innerHTML = '<p class="rp-fig-estado erro">' + nome + T(" não respondeu neste cálculo", " did not respond in this run") +
      ' <span class="selo ausente">' + T("ausente", "missing") + "</span></p>";
  }
  function selo() { return ' <span class="selo real">' + T("real", "measured") + "</span>"; }
  function linkApp(ctx, d) {
    var m = modo(ctx);
    return "/?modo=" + m + (m !== "desenho" ? "&busca=" + encodeURIComponent(d.area.nome) : "") + "&lang=" + (en() ? "en" : "pt");
  }
  function seriesDe(d, zona) {
    var L = d.linha[zona] || {}, anos = [];
    for (var a = d.anos[0]; a <= d.anos[d.anos.length - 1]; a++) anos.push(String(a));
    return { anos: anos, series: Object.keys(SERIE).filter(function (k) { return L[k]; }).map(function (k) {
      return { rotulo: T(SERIE[k].rotulo[0], SERIE[k].rotulo[1]), cor: SERIE[k].cor, valores: anos.map(function (a) { return L[k][a] || 0; }), espessura: 2 };
    }) };
  }
  function marcasDatas(d) {
    var m = [], dt = d.area.datas || {};
    if (dt.homologada) m.push({ x: String(dt.homologada), rotulo: T("homologada ", "ratified ") + dt.homologada, cor: "#1f6f4a" });
    return m;
  }

  R.iniciar({
    dados: function (ctx) {
      var a = ctx.params.get("area");
      return "/_demonstracao/yvynation.json?modo=" + modo(ctx) + (a ? "&area=" + encodeURIComponent(a) : "");
    },
    centro: [-9.3, -64], zoom: 6,

    aoCarregar: function (ctx, d) {
      T = ctx.t;
      var A = d.area, ult = d.anos[d.anos.length - 1];
      var dentro = pctNativa(d, "area", ult), fora = pctNativa(d, "buffer", ult);
      var gfc = d.gfc && d.gfc.area;
      ctx.preencher({
        "n-area": fmt.ha(A.area_ha),
        "n-dentro": fmt.pct(dentro),
        "n-dentro-rot": T("vegetação nativa dentro da " + rotuloArea(d) + " em " + ult, "native vegetation inside the " + rotuloArea(d) + " in " + ult) + selo(),
        "n-fora": fmt.pct(fora),
        "n-fora-rot": T("vegetação nativa nos " + A.buffer_km + " km em volta, no mesmo ano", "native vegetation in the surrounding " + A.buffer_km + " km, same year") + selo(),
        "n-perda": gfc ? fmt.ha(gfc.forest_loss_ha) : "—"
      });
      ctx.$("#topo-exemplo").textContent = A.nome;
      var app = linkApp(ctx, d);
      ctx.$("#link-app").href = app; ctx.$("#cta-app").href = app;
      ctx.$("#rp-fig-url").textContent = "yvynation.umaterra.com.br" + app;
      ctx.$("#abertura-exemplo").innerHTML = (d.exemplo_padrao ? T("Exemplo desta página: ", "This page's example: ") : T("Área escolhida: ", "Chosen area: ")) + "<b>" + fmt.esc(A.nome) + "</b>" +
        (A.info && A.info.uf_sigla ? " (" + fmt.esc(A.info.uf_sigla) + ")" : "") + T(". Calculado pelas funções do aplicativo em ", ". Computed by the app's own functions on ") + fmt.dataHora(d.gerado_em) +
        (d.exemplo_padrao ? T(" e guardado com esta página.", " and stored with this page.") : T(" (o resultado fica guardado por algumas horas).", " (the result is kept for a few hours)."));
      var erros = Object.keys(d.erros || {});
      ctx.$("#fim-extra").innerHTML = erros.length
        ? T("Neste cálculo não responderam: <b>", "Parts that did not respond in this run: <b>") + erros.map(fmt.esc).join(", ") + T("</b>. Os passos correspondentes dizem o que faltou.", "</b>. The matching steps say what is missing.")
        : T("Todas as análises responderam no cálculo de ", "Every analysis responded in the run of ") + fmt.dataHora(d.gerado_em) + ".";
      var b0 = soma(d.mapbiomas.buffer[String(ult)]);
      ctx.texto("buffer", T("Aqui a " + rotuloArea(d) + " tem <b>" + fmt.ha(A.area_ha) + "</b>, e o anel de " + A.buffer_km + " km em volta, <b>" + fmt.ha(b0) + "</b>: " +
                              fmt.n(b0 / A.area_ha, 1) + " vezes a área. As duas zonas passam pelas mesmas contas, lado a lado.",
                            "Here the " + rotuloArea(d) + " covers <b>" + fmt.ha(A.area_ha) + "</b> and the " + A.buffer_km + " km ring around it <b>" + fmt.ha(b0) + "</b>, " +
                              fmt.n(b0 / A.area_ha, 1) + " times the area. Both zones go through the same sums, side by side."));
    },

    passos: {
      area: function (ctx, d) {
        var A = d.area, I = A.info || {}, D = A.datas || {};
        ctx.tiles({});
        ctx.vetores(vet(d));
        ctx.enquadrar(feat(A.geojson), { maxZoom: 12 });
        ctx.legendaMapa('<span><i style="background:#ffd400"></i>' + fmt.esc(A.nome) + "</span>");
        var linhas = [[T("Área", "Area"), fmt.ha(A.area_ha)]];
        // os valores do catálogo (fase, categoria, grupo…) ficam como a FUNAI e o CNUC os publicam
        if (d.modo === "terra-indigena") linhas = linhas.concat([[T("Povo", "People"), I.etnia], [T("Fase", "Phase"), I.fase_ti], [T("Município(s)", "Municipality"), I.municipio], [T("UF", "State"), I.uf_sigla],
          [T("Declarada", "Declared"), D.declarada], [T("Homologada", "Ratified"), D.homologada], [T("Regularizada", "Registered"), D.regularizada]]);
        if (d.modo === "unidade-conservacao") linhas = linhas.concat([[T("Categoria", "Category"), I.categoria], [T("Grupo", "Group"), I.grupo], [T("Esfera", "Level"), I.esfera], [T("Município(s)", "Municipality"), I.municipio], [T("Código CNUC", "CNUC code"), I.cd_cnuc]]);
        if (d.modo === "desenho") linhas = linhas.concat([[T("Origem", "Source"), T("desenhada à mão sobre o mapa", "drawn by hand on the map")], [T("Forma", "Shape"), T("faixa ao longo do rio Madeira, de Jirau a Santo Antônio", "a strip along the Madeira river, from Jirau to Santo Antônio")]]);
        ctx.$("#fig-area").innerHTML = '<dl class="rp-ficha">' + linhas.filter(function (l) { return l[1] !== null && l[1] !== undefined && l[1] !== ""; })
          .map(function (l) { return "<dt>" + l[0] + "</dt><dd>" + fmt.esc(l[1]) + "</dd>"; }).join("") + "</dl>";
        var nomeUC = fmt.esc(A.nome.toLowerCase().replace(/(^|\s)\S/g, function (s) { return s.toUpperCase(); }));
        var t = {
          "terra-indigena": T("A <b>" + fmt.esc(A.nome) + "</b>, do povo " + fmt.esc(I.etnia || "—") + ", foi declarada em " + (D.declarada || "—") + " e homologada em " + (D.homologada || "—") + ".",
                              "<b>" + fmt.esc(A.nome) + "</b>, land of the " + fmt.esc(I.etnia || "—") + " people, was declared in " + (D.declarada || "—") + " and ratified in " + (D.homologada || "—") + "."),
          "unidade-conservacao": T("A <b>" + nomeUC + "</b> é uma unidade " + fmt.esc((I.esfera || "").toLowerCase()) + " de " + fmt.esc((I.grupo || "").toLowerCase()) + ", na categoria " + fmt.esc((I.categoria || "").toLowerCase()) + ".",
                                   "<b>" + nomeUC + "</b> is a unit in the registry's category <i>" + fmt.esc(I.categoria || "—") + "</i>, group <i>" + fmt.esc(I.grupo || "—") + "</i>, level <i>" + fmt.esc(I.esfera || "—") + "</i>."),
          desenho: T("A área deste exemplo tem <b>" + fmt.ha(A.area_ha) + "</b> e segue o rio Madeira entre as usinas de Jirau e Santo Antônio, perto de Porto Velho.",
                     "This example's area covers <b>" + fmt.ha(A.area_ha) + "</b> and follows the Madeira river between the Jirau and Santo Antônio dams, near Porto Velho.")
        };
        ctx.texto("area", t[d.modo]);
      },

      buffer: function (ctx, d) {
        ctx.tiles({});
        ctx.vetores(vet(d, true));
        ctx.enquadrar(feat(d.area.buffer_geojson || d.area.geojson), { maxZoom: 11 });
        ctx.legendaMapa('<span><i style="background:#ffd400"></i>' + rotuloArea(d) + '</span><span><i style="background:#9cc2ac"></i>' +
          T("zona de " + d.area.buffer_km + " km em volta", d.area.buffer_km + " km surrounding zone") + "</span>");
        var ult = String(d.anos[d.anos.length - 1]);
        graf.tabela(ctx.$("#fig-buffer"), {
          colunas: [{ rotulo: T("Zona", "Zone") }, { rotulo: T("Área", "Area"), n: true }],
          linhas: [[graf.qd("#ffd400") + rotuloArea(d), fmt.ha(d.area.area_ha)], [graf.qd("#9cc2ac") + T("anel de " + d.area.buffer_km + " km", d.area.buffer_km + " km ring"), fmt.ha(soma(d.mapbiomas.buffer[ult]))]]
        });
      },

      cobertura: function (ctx, d) {
        var el = ctx.$("#fig-cobertura"), ult = String(d.anos[d.anos.length - 1]);
        var den = d.mapbiomas.area[ult], fora = d.mapbiomas.buffer[ult];
        ctx.tiles({ mb: camada(d, "mb_" + ult, 0.8) });
        ctx.vetores(vet(d, true));
        ctx.enquadrar(feat(d.area.buffer_geojson || d.area.geojson), { maxZoom: 11 });
        if (!den || !den.length) return faltou(el, "MapBiomas");
        ctx.legendaMapa(legenda(den, "MapBiomas " + ult));
        var td = soma(den), tf = soma(fora), ids = {};
        var ha = function (lista, id) { return (lista.filter(function (c) { return c.id === id; })[0] || { ha: 0 }).ha; };
        den.concat(fora).forEach(function (c) { ids[c.id] = c; });
        var top = Object.keys(ids).map(function (k) { return ids[k]; }).sort(function (a, b) {
          return Math.max(ha(den, b.id) / td, ha(fora, b.id) / tf) - Math.max(ha(den, a.id) / td, ha(fora, a.id) / tf);
        }).slice(0, 5);
        var linhas = [];
        top.forEach(function (c) {
          var a = ha(den, c.id), b = ha(fora, c.id);
          linhas.push({ rotulo: nm(c) + T(" · dentro", " · inside"), valor: 100 * a / td, cor: c.cor, texto: fmt.pct(100 * a / td, 1) });
          linhas.push({ rotulo: nm(c) + T(" · em volta", " · around"), valor: 100 * b / tf, cor: c.cor, texto: fmt.pct(100 * b / tf, 1) });
        });
        graf.barrasH(el, { linhas: linhas, max: 100, xRotulo: 260 });
        var c0 = den[0], f0 = fora[0];
        ctx.texto("cobertura", T("Em " + ult + ", a maior classe dentro é <b>" + fmt.esc(nm(c0)) + "</b> (" + fmt.pct(100 * c0.ha / td) + "); nos " + d.area.buffer_km + " km em volta, <b>" + fmt.esc(nm(f0)) + "</b> (" + fmt.pct(100 * f0.ha / tf) + ").",
                                 "In " + ult + ", the largest class inside is <b>" + fmt.esc(nm(c0)) + "</b> (" + fmt.pct(100 * c0.ha / td) + "); in the surrounding " + d.area.buffer_km + " km, <b>" + fmt.esc(nm(f0)) + "</b> (" + fmt.pct(100 * f0.ha / tf) + ")."));
      },

      tempo: function (ctx, d) {
        var el = ctx.$("#fig-tempo");
        ctx.tiles({ mb: camada(d, "mb_" + d.anos[0], 0.8) });
        ctx.vetores(vet(d, true));
        ctx.enquadrar(feat(d.area.buffer_geojson || d.area.geojson), { maxZoom: 11 });
        ctx.legendaMapa(legenda(d.mapbiomas.buffer[String(d.anos[0])], "MapBiomas " + d.anos[0] + T(" · em volta", " · around")));
        var linhas = [];
        d.anos.forEach(function (a) {
          linhas.push({ rotulo: a + T(" · dentro", " · inside"), valor: pctNativa(d, "area", a), cor: COR.area, texto: fmt.pct(pctNativa(d, "area", a)) });
          linhas.push({ rotulo: a + T(" · em volta", " · around"), valor: pctNativa(d, "buffer", a), cor: COR.buffer, texto: fmt.pct(pctNativa(d, "buffer", a)) });
        });
        graf.barrasH(el, { linhas: linhas, max: 100, xRotulo: 170 });
        var a0 = d.anos[0], a1 = d.anos[d.anos.length - 1];
        var di = [fmt.pct(pctNativa(d, "area", a0)), fmt.pct(pctNativa(d, "area", a1))], fo = [fmt.pct(pctNativa(d, "buffer", a0)), fmt.pct(pctNativa(d, "buffer", a1))];
        ctx.texto("tempo", T("Vegetação nativa dentro: <b>" + di[0] + "</b> em " + a0 + " e <b>" + di[1] + "</b> em " + a1 + ". Em volta: " + fo[0] + " e " + fo[1] + ".",
                             "Native vegetation inside: <b>" + di[0] + "</b> in " + a0 + " and <b>" + di[1] + "</b> in " + a1 + ". Around: " + fo[0] + " and " + fo[1] + "."));
      },

      transicoes: function (ctx, d) {
        var el = ctx.$("#fig-transicoes"), F = d.transicoes || [];
        ctx.tiles({ mb: camada(d, "mb_" + d.anos[d.anos.length - 1], 0.8) });
        ctx.vetores(vet(d));
        ctx.enquadrar(feat(d.area.geojson), { maxZoom: 12 });
        ctx.legendaMapa("");
        if (!F.length) return faltou(el, T("As transições", "The transitions"));
        var nomes = {};
        d.anos.forEach(function (a) { ["area", "buffer"].forEach(function (z) { (d.mapbiomas[z][String(a)] || []).forEach(function (c) { nomes[c.id] = c; }); }); });
        // as classes que somam menos de 0,3% saem do diagrama (ficam na conta do texto)
        var tot = F.reduce(function (s, f) { return s + f.ha; }, 0);
        var fl = F.filter(function (f) { return f.ha >= tot * 0.003; });
        var ids = {}; fl.forEach(function (f) { ids[f.de] = 1; ids[f.para] = 1; });
        var nos = Object.keys(ids).map(function (k) { var c = nomes[k] || { nome: T("classe ", "class ") + k, cor: "#9aa8a1" }; return { id: Number(k), rotulo: nm(c), cor: c.cor }; });
        graf.sankey(el, { esq: nos, dir: nos, fluxos: fl.map(function (f) { return { de: f.de, para: f.para, valor: f.ha }; }), rotuloEsq: String(d.anos[0]), rotuloDir: String(d.anos[d.anos.length - 1]) });
        var mud = F.filter(function (f) { return f.de !== f.para; }).sort(function (a, b) { return b.ha - a.ha; });
        var mudou = mud.reduce(function (s, f) { return s + f.ha; }, 0);
        ctx.texto("transicoes", T("Entre " + d.anos[0] + " e " + d.anos[d.anos.length - 1] + ", <b>" + fmt.ha(mudou) + "</b> (" + fmt.pct(100 * mudou / tot, 1) + " da área) mudaram de classe. ",
                                  "Between " + d.anos[0] + " and " + d.anos[d.anos.length - 1] + ", <b>" + fmt.ha(mudou) + "</b> (" + fmt.pct(100 * mudou / tot, 1) + " of the area) changed class. ") +
          mud.slice(0, 2).map(function (f) { return fmt.esc(nm(nomes[f.de] || {})) + " → " + fmt.esc(nm(nomes[f.para] || {})) + ": <b>" + fmt.ha(f.ha) + "</b>"; }).join("; ") + ".");
      },

      hansen: function (ctx, d) {
        var el = ctx.$("#fig-hansen"), G = d.gfc || {};
        ctx.tiles({ hansen: camada(d, "hansen_perda", 0.9) });
        ctx.vetores(vet(d, true));
        ctx.enquadrar(feat(d.area.buffer_geojson || d.area.geojson), { maxZoom: 11 });
        var pal = ((d.camadas || {}).hansen_perda || {}).palette;
        ctx.legendaMapa(T("<b>Hansen GFC · ano da perda</b>", "<b>Hansen GFC · year of loss</b>") + (pal ? '<span><i class="g" style="background:linear-gradient(90deg,' + pal.map(function (c) { return c.charAt(0) === "#" ? c : "#" + c; }).join(",") + ')"></i>2001 → 2024</span>' : ""));
        if (!G.area) return faltou(el, "Hansen GFC");
        graf.tabela(el, {
          colunas: [{ rotulo: "" }, { rotulo: T("Cobertura arbórea 2000", "Tree cover 2000"), n: true }, { rotulo: T("Perda 2001–2024", "Loss 2001–2024"), n: true },
                    { rotulo: T("% da cobertura", "% of cover"), n: true }, { rotulo: T("Ganho", "Gain"), n: true }],
          linhas: [["area", T("Dentro", "Inside")], ["buffer", T("Em volta (", "Around (") + d.area.buffer_km + " km)"]].filter(function (z) { return G[z[0]]; }).map(function (z) {
            var g = G[z[0]]; return [graf.qd(COR[z[0]]) + z[1], fmt.ha(g.tree_cover_2000_ha), "<b>" + fmt.ha(g.forest_loss_ha) + "</b>", fmt.pct(100 * g.forest_loss_ha / g.tree_cover_2000_ha, 1), fmt.ha(g.forest_gain_ha)];
          }),
          nota: T("Hansen/UMD Global Forest Change: pixel de 30 m com mais de 0% de copa em 2000; a perda é marcada por ano, o ganho (2000–2012) não tem data.",
                  "Hansen/UMD Global Forest Change: 30 m pixels with more than 0% canopy in 2000; loss is dated by year, gain (2000–2012) is undated.")
        });
        var a = G.area, b = G.buffer;
        ctx.texto("hansen", T("Dentro, o Hansen marca a perda de <b>", "Inside, Hansen records the loss of <b>") + fmt.pct(100 * a.forest_loss_ha / a.tree_cover_2000_ha, 1) + T("</b> da cobertura arbórea de 2000", "</b> of the 2000 tree cover") +
          (b ? T("; em volta, <b>", "; around it, <b>") + fmt.pct(100 * b.forest_loss_ha / b.tree_cover_2000_ha, 1) + "</b>." : "."));
      },

      linha: function (ctx, d) {
        var el = ctx.$("#fig-linha");
        ctx.tiles({}); ctx.vetores({}); ctx.legendaMapa("");
        var s = seriesDe(d, "area");
        if (!s.series.length) return faltou(el, T("A linha do tempo", "The timeline"));
        graf.linhas(el, { x: s.anos, series: s.series, unidade: T("ha por ano, dentro da " + rotuloArea(d), "ha a year, inside the " + rotuloArea(d)), min: 0, marcas: marcasDatas(d) });
        var L = d.linha.area, pico = null;
        Object.keys(L.mb_defor_primary || {}).forEach(function (a) { if (!pico || L.mb_defor_primary[a] > L.mb_defor_primary[pico]) pico = a; });
        var tot = function (k) { return Object.keys(L[k] || {}).reduce(function (s, a) { return s + L[k][a]; }, 0); };
        ctx.texto("linha", T("Dentro, o MapBiomas soma <b>" + fmt.ha(tot("mb_defor_primary")) + "</b> de desmatamento de vegetação primária na série", "Inside, MapBiomas adds up <b>" + fmt.ha(tot("mb_defor_primary")) + "</b> of primary vegetation clearing over the series") +
          (pico ? T(", com o pior ano em <b>", ", the worst year being <b>") + pico + "</b> (" + fmt.ha(L.mb_defor_primary[pico]) + ")" : "") +
          T(", e " + fmt.ha(tot("mb_secondary_growth")) + " de regeneração.", ", and " + fmt.ha(tot("mb_secondary_growth")) + " of regrowth."));
      },

      contraste: function (ctx, d) {
        var el = ctx.$("#fig-contraste");
        ctx.tiles({}); ctx.vetores({}); ctx.legendaMapa("");
        var la = d.linha.area.mb_defor_primary || {}, lb = d.linha.buffer.mb_defor_primary || {};
        var anos = []; for (var a = d.anos[0]; a <= d.anos[d.anos.length - 1]; a++) anos.push(String(a));
        // por 1.000 ha de cada zona, para que um anel maior não pareça pior só por ser maior
        var ta = d.area.area_ha, tb = soma(d.mapbiomas.buffer[String(d.anos[0])]);
        graf.linhas(el, { x: anos, min: 0, unidade: T("desmatamento primário, ha por 1.000 ha da zona", "primary clearing, ha per 1,000 ha of the zone"), marcas: marcasDatas(d), series: [
          { rotulo: T("dentro", "inside"), cor: COR.area, valores: anos.map(function (y) { return 1000 * (la[y] || 0) / ta; }), espessura: 3 },
          { rotulo: T("em volta (", "around (") + d.area.buffer_km + " km)", cor: COR.buffer, valores: anos.map(function (y) { return 1000 * (lb[y] || 0) / tb; }), espessura: 2 }
        ] });
        var sa = anos.reduce(function (s, y) { return s + (la[y] || 0); }, 0), sb = anos.reduce(function (s, y) { return s + (lb[y] || 0); }, 0);
        var xa = fmt.n(1000 * sa / ta, 0), xb = fmt.n(1000 * sb / tb, 0);
        ctx.texto("contraste", T("Somando a série: <b>" + xa + " ha</b> desmatados por 1.000 ha dentro, contra <b>" + xb + " ha</b> por 1.000 ha em volta.",
                                 "Over the whole series: <b>" + xa + " ha</b> cleared per 1,000 ha inside, against <b>" + xb + " ha</b> per 1,000 ha around."));
      },

      exportar: function (ctx, d) {
        ctx.tiles({}); ctx.vetores({}); ctx.legendaMapa("");
        var el = ctx.$("#fig-exportar"), img = ctx.$("#fig-exportar-print");
        graf.tabela(el, {
          colunas: [{ rotulo: T("Análise", "Analysis") }, { rotulo: T("Fonte", "Source") }, { rotulo: T("Escala", "Scale"), n: true }],
          linhas: (d.procedencia || []).map(function (p) { return [fmt.esc(nm(p)), fmt.esc((en() && p.dataset_en) || p.dataset), p.escala_m + " m"]; })
        });
        if (img) img.style.display = "";
      }
    }
  });
})();
