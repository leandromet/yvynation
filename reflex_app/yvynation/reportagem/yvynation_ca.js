/* Yvynation — the Canada conservation walkthrough (/walkthrough/conservation-unit,
 * Okanagan Mountain Park).
 *
 * The numbers come from /_demonstracao/yvynation_ca.json
 * (canada/services/demonstracao.py), built by the Canada page's own services. The
 * Canada page keeps Camposcope's analysis contract, so this file keeps the
 * structure of Camposcope's Canada walkthrough (camposcope_ca.js there). English
 * only: the Portuguese walkthrough opens a Brazilian reserve (yvynation_area.js).
 */
(function () {
  var R = window.Reportagem, fmt = R.fmt, graf = R.graf;

  var ZONA = { parcela: "Park", ring_500m: "0–500 m", ring_2km: "500 m–2 km", ring_5km: "2–5 km" };
  var COR_ZONA = { parcela: "#d98324", ring_500m: "#1f6f4a", ring_2km: "#4f8f6f", ring_5km: "#9cc2ac" };
  var CONTORNO = { color: "#ffd400", weight: 3, fillOpacity: 0 };

  function area(ctx) { return ctx.params.get("area") || ""; }
  function nomeZona(k) { return ZONA[k] || k; }
  function parcelaGeo(d) { return { type: "Feature", properties: {}, geometry: d.area.geometry }; }
  function classesNoAno(d, zona, i) {
    var h = d.historico, z = h.zonas[zona] || {};
    return Object.keys(z).map(function (c) { return { id: c, ha: z[c][i] || 0, nome: h.classes[c].nome_en || h.classes[c].nome, cor: h.classes[c].cor }; })
      .filter(function (x) { return x.ha > 0; }).sort(function (a, b) { return b.ha - a.ha; });
  }
  function legendaClasses(d, ano, zona) {
    var i = d.historico.anos.indexOf(ano); if (i < 0) return "";
    return "<b>AAFC crop inventory " + ano + " · classes " + (zona === "ring_5km" ? "2–5 km band" : "in the park") + "</b>" +
      classesNoAno(d, zona || "parcela", i).slice(0, 6).map(function (c) { return '<span><i style="background:' + c.cor + '"></i>' + fmt.esc(c.nome) + "</span>"; }).join("");
  }
  function nativaPct(d, zona) {
    var h = d.historico, z = h.zonas[zona] || {}, nat = h.nativas.map(String);
    return h.anos.map(function (_, i) {
      var tot = 0, n = 0;
      Object.keys(z).forEach(function (c) { tot += z[c][i] || 0; if (nat.indexOf(c) >= 0) n += z[c][i] || 0; });
      return tot > 0 ? (100 * n) / tot : null;
    });
  }
  function camada(d, k, op) { var c = d.camadas[k]; return c ? Object.assign({}, c, op ? { opacity: op } : {}) : null; }
  function faltou(el, nome) {
    el.innerHTML = '<p class="rp-fig-estado erro">' + nome + ' did not respond this time <span class="selo ausente">missing</span></p>';
  }
  function grupo(d, k) { var g = (d.vlce2 && d.vlce2.grupos[k]) || {}; return g.nome_en || k; }
  // the chart's short labels: "Cropland and pasture" → "Cropland"
  function grupoCurto(d, k) { return grupo(d, k).split(/ and |, | \/ /)[0]; }

  R.iniciar({
    dados: function (ctx) { var a = area(ctx); return "/_demonstracao/yvynation_ca.json" + (a ? "?area=" + encodeURIComponent(a) : ""); },
    centro: [49.73, -119.58], zoom: 10,

    aoCarregar: function (ctx, d) {
      var A = d.area, h = d.historico, F = d.fogo, H = d.hansen;
      var anual = F ? (F.anual.parcela || []) : [], pior = anual.slice().sort(function (a, b) { return b.pct - a.pct; })[0];
      var perda = H ? (H.perda.parcela || []).reduce(function (s, x) { return s + x.ha; }, 0) : null;
      var conif = h && h.zonas.parcela["210"], dc = conif ? conif[conif.length - 1] - conif[0] : null;
      ctx.preencher({
        "n-area": fmt.ha(A.area_calculada_ha),
        "n-fogo": pior && pior.pct > 0 ? fmt.pct(pior.pct) : "—",
        "n-fogo-rot": pior && pior.pct > 0 ? "of the park burned in " + pior.ano + ' (MODIS) <span class="selo real">measured</span>' : "of the park burned in its worst fire year",
        "n-perda": perda === null ? "—" : fmt.ha(perda),
        "n-perda-rot": 'of tree cover lost in the park since 2001 (Hansen) <span class="selo real">measured</span>',
        "n-conifera": dc === null ? "—" : fmt.sinal(dc, 0) + " ha",
        "n-conifera-rot": "change in coniferous forest, " + (h ? h.anos[0] + "–" + h.anos[h.anos.length - 1] : "") + ' <span class="selo real">measured</span>'
      });
      ctx.$("#topo-exemplo").textContent = A.nome + " · " + A.provincia;
      var app = "/canada?area=" + encodeURIComponent(A.chave) + "&lang=en";
      ctx.$("#link-app").href = app; ctx.$("#cta-app").href = app;
      ctx.$("#rp-fig-url").textContent = "yvynation.umaterra.com.br" + app;
      ctx.$("#abertura-exemplo").innerHTML = (d.exemplo_padrao ? "This page's example: " : "Chosen area: ") + "<b>" + fmt.esc(A.nome) + "</b>, " + fmt.esc(A.categoria) +
        (A.ano_criacao ? ", established " + A.ano_criacao : "") + ", computed by the app's services on " + fmt.dataHora(d.gerado_em) +
        (d.exemplo_padrao ? " and stored with this page." : " (the result is kept for a few hours).");
      var erros = Object.keys(d.erros || {});
      ctx.$("#fim-extra").innerHTML = erros.length
        ? "These did not respond this time: <b>" + erros.map(fmt.esc).join(", ") + "</b>. The matching steps say what is missing."
        : "Every analysis responded in the run of " + fmt.dataHora(d.gerado_em) + ".";
      ctx.texto("area", "CPCAD records <b>" + fmt.esc(A.nome) + "</b> as " + fmt.esc(A.categoria) + (A.iucn ? ", IUCN category " + fmt.esc(A.iucn) : "") +
        (A.ano_criacao ? ", established in " + A.ano_criacao : "") + ", managed by " + fmt.esc(A.gestor || "—") + ". It registers " + fmt.ha(A.area_registrada_ha) +
        ", and its polygon measures " + fmt.ha(A.area_calculada_ha) + (A.partes > 1 ? ", in " + A.partes + " parts." : ", in one part."));
      var z = d.zonas;
      ctx.texto("zonas", "For a park of " + fmt.ha(z[0].area_ha) + ", the bands cover " + z.slice(1).map(function (x) { return "<b>" + fmt.ha(x.area_ha) + "</b>"; }).join(", ") +
        (d.exemplo_padrao ? ". On the west the inner bands fall on the lake; on the east, on forest, the Kettle Valley neighbourhoods and the bench farms." : "."));
    },

    passos: {
      area: function (ctx, d) {
        var A = d.area;
        ctx.tiles({});
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa('<b>CPCAD</b><span><i style="background:#ffd400"></i>' + fmt.esc(A.nome) + "</span>");
        ctx.$("#fig-area").innerHTML = '<dl class="rp-ficha"><dt>Name</dt><dd>' + fmt.esc(A.nome) + "</dd><dt>Category</dt><dd>" + fmt.esc(A.categoria) +
          "</dd><dt>IUCN</dt><dd>" + fmt.esc(A.iucn || "—") + "</dd><dt>Established</dt><dd>" + (A.ano_criacao || "—") + "</dd><dt>Governance</dt><dd>" + fmt.esc(A.governanca) +
          "</dd><dt>Registered area</dt><dd>" + fmt.ha(A.area_registrada_ha) + "</dd><dt>Measured</dt><dd>" + fmt.ha(A.area_calculada_ha) + "</dd></dl>";
      },

      zonas: function (ctx, d) {
        ctx.tiles({});
        var aneis = d.zonas.slice(1).map(function (z) { return { type: "Feature", properties: { key: z.key }, geometry: z.geojson.geometry || z.geojson }; });
        ctx.vetores({
          aneis: { geojson: { type: "FeatureCollection", features: aneis }, estilo: function (f) { return { color: COR_ZONA[f.properties.key], weight: 2, dashArray: "5 4", fillColor: COR_ZONA[f.properties.key], fillOpacity: 0.12 }; } },
          parcela: { geojson: parcelaGeo(d), estilo: CONTORNO }
        });
        ctx.enquadrar(aneis[aneis.length - 1], { maxZoom: 13 });
        ctx.legendaMapa(d.zonas.map(function (z) { return '<span><i style="background:' + (z.key === "parcela" ? "#ffd400" : COR_ZONA[z.key]) + '"></i>' + fmt.esc(nomeZona(z.key)) + "</span>"; }).join(""));
        graf.tabela(ctx.$("#fig-zonas"), {
          colunas: [{ rotulo: "Zone" }, { rotulo: "Area", n: true }, { rotulo: "× park", n: true }],
          linhas: d.zonas.map(function (z) { return [graf.qd(z.key === "parcela" ? "#ffd400" : COR_ZONA[z.key]) + fmt.esc(nomeZona(z.key)), fmt.ha(z.area_ha), fmt.n(z.area_ha / d.zonas[0].area_ha, 1)]; })
        });
      },

      cobertura: function (ctx, d) {
        var el = ctx.$("#fig-cobertura"), h = d.historico;
        if (!h) return faltou(el, "The crop inventory");
        var ultimo = h.anos[h.anos.length - 1];
        ctx.tiles({ aci: camada(d, "aci_" + ultimo, 0.8) });
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa(legendaClasses(d, ultimo));
        var series = Object.keys(h.zonas.parcela).map(function (c) { return { rotulo: h.classes[c].nome_en || h.classes[c].nome, cor: h.classes[c].cor, valores: h.zonas.parcela[c] }; })
          .filter(function (s) { return s.valores.some(function (v) { return v > 0; }); })
          .sort(function (a, b) { return b.valores[b.valores.length - 1] - a.valores[a.valores.length - 1]; });
        graf.empilhado(el, { anos: h.anos, series: series, unidade: "ha" });
        var c0 = classesNoAno(d, "parcela", 0)[0], cf = classesNoAno(d, "parcela", h.anos.length - 1)[0], troca = null;
        for (var i = 1; i < h.anos.length; i++) { var ci = classesNoAno(d, "parcela", i)[0]; if (ci && c0 && ci.id !== c0.id) { troca = { ano: h.anos[i], c: ci }; break; } }
        var b = function (x) { return "<b>" + fmt.esc(x ? x.nome.toLowerCase() : "—") + "</b>"; };
        ctx.texto("cobertura", "In " + h.anos[0] + ", the largest class in the park was " + b(c0) + " (" + fmt.ha(c0 && c0.ha) + "). " +
          (troca ? "In <b>" + troca.ano + "</b>, " + b(troca.c) + " takes over. " : "") + "In " + ultimo + ", " + b(cf) + " covers " + fmt.ha(cf && cf.ha) + ". " +
          "Inside a park, a swing from conifer to shrub and grass is what a stand-replacing fire leaves behind.");
      },

      vizinhanca: function (ctx, d) {
        var el = ctx.$("#fig-vizinhanca"), h = d.historico;
        if (!h) return faltou(el, "The crop inventory");
        ctx.tiles({ aci: camada(d, "aci_" + h.anos[0], 0.8) });
        ctx.vetores({
          aneis: { geojson: d.zonas[d.zonas.length - 1].geojson, estilo: { color: COR_ZONA.ring_5km, weight: 2, dashArray: "5 4", fillOpacity: 0 } },
          parcela: { geojson: parcelaGeo(d), estilo: CONTORNO }
        });
        ctx.enquadrar(d.zonas[d.zonas.length - 1].geojson, { maxZoom: 13 });
        ctx.legendaMapa(legendaClasses(d, h.anos[0], "ring_5km"));
        var series = d.zonas.map(function (z) { return { rotulo: nomeZona(z.key), cor: COR_ZONA[z.key], valores: nativaPct(d, z.key), espessura: z.key === "parcela" ? 3 : 2 }; });
        graf.linhas(el, { x: h.anos, series: series, unidade: "% natural vegetation", min: 0, max: 100 });
        var p = series[0].valores, a = series[series.length - 1].valores, n = p.length - 1;
        var juntas = Math.abs((p[0] - p[n]) - (a[0] - a[n])) < 10;
        ctx.texto("vizinhanca", "In the park, natural vegetation goes from <b>" + fmt.pct(p[0]) + "</b> in " + h.anos[0] + " to <b>" + fmt.pct(p[n]) + "</b> in " + h.anos[n] +
          "; in the 2–5 km band, from " + fmt.pct(a[0]) + " to " + fmt.pct(a[n]) + ". " +
          (juntas ? "The curves move together: whatever changed, changed across the valley." : "The curves part ways: the park took its own path, or the inventory changed its mind about it."));
      },

      transicoes: function (ctx, d) {
        var el = ctx.$("#fig-transicoes"), T = d.transicoes, h = d.historico;
        if (!T || !h) return faltou(el, "The transitions");
        ctx.tiles({ aci: camada(d, "aci_" + T.ano_b, 0.8) });
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa("");
        var fl = T.zonas.parcela || [], ids = {};
        fl.forEach(function (f) { ids[f.de] = 1; ids[f.para] = 1; });
        var nome = function (c) { var k = h.classes[c]; return k ? (k.nome_en || k.nome) : "class " + c; };
        var nos = Object.keys(ids).map(function (c) { return { id: Number(c), rotulo: nome(c), cor: (h.classes[c] || {}).cor || "#9aa8a1" }; });
        graf.sankey(el, { esq: nos, dir: nos, fluxos: fl.map(function (f) { return { de: f.de, para: f.para, valor: f.ha }; }), rotuloEsq: String(T.ano_a), rotuloDir: String(T.ano_b) });
        var mud = fl.filter(function (f) { return f.de !== f.para; }).sort(function (a, b) { return b.ha - a.ha; });
        var tot = fl.reduce(function (a, f) { return a + f.ha; }, 0), mudou = mud.reduce(function (a, f) { return a + f.ha; }, 0);
        ctx.texto("transicoes", "Between " + T.ano_a + " and " + T.ano_b + ", <b>" + fmt.ha(mudou) + "</b> of the park (" + fmt.pct(100 * mudou / tot) + ") changed class. " +
          (mud.length ? "The largest flow: <b>" + fmt.esc(nome(mud[0].de).toLowerCase()) + "</b> → <b>" + fmt.esc(nome(mud[0].para).toLowerCase()) + "</b>, " + fmt.ha(mud[0].ha) + "." : ""));
      },

      floresta: function (ctx, d) {
        var el = ctx.$("#fig-floresta"), H = d.hansen;
        if (!H) return faltou(el, "Hansen/GLAD");
        ctx.tiles({ hansen: camada(d, "hansen", 0.9) });
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa('<b>Hansen/GLAD</b><span><i style="background:#d4271e"></i>loss since 2001</span><span><i style="background:#02d659"></i>gain (undated)</span>');
        var fim = 2024, por = {};
        Object.keys(H.perda).forEach(function (z) { H.perda[z].forEach(function (x) { if (x.ano > fim) fim = x.ano; }); });
        (H.perda.parcela || []).forEach(function (x) { por[x.ano] = x.ha; });
        var anos = []; for (var a = 2001; a <= fim; a++) anos.push(a);
        graf.colunas(el, { x: anos.map(String), valores: anos.map(function (a) { return por[a] || 0; }), unidade: "ha of tree cover lost per year, in the park", cor: "#e5484d" });
        var tot = (H.perda.parcela || []).reduce(function (s, x) { return s + x.ha; }, 0);
        var top = (H.perda.parcela || []).slice().sort(function (x, y) { return y.ha - x.ha; }).slice(0, 2).sort(function (x, y) { return x.ano - y.ano; });
        var soma2 = top.reduce(function (s, x) { return s + x.ha; }, 0);
        ctx.texto("floresta", "Counting canopy above " + H.limiar_pct + "% as forest, the park lost <b>" + fmt.ha(tot) + "</b> of tree cover since 2001. <b>" +
          top.map(function (x) { return x.ano; }).join(" and ") + "</b> alone hold " + fmt.ha(soma2) + " (" + fmt.pct(100 * soma2 / tot) + "). " +
          (d.exemplo_padrao ? "That is the Okanagan Mountain Park fire, started by lightning inside the park in August 2003; Hansen books part of a late-summer fire in the following year. " : "") +
          (H.divide_em ? "" : "Established in " + (d.area.ano_criacao || "—") + ", before the record starts, the park has the whole series after protection."));
      },

      fogo: function (ctx, d) {
        var el = ctx.$("#fig-fogo"), F = d.fogo;
        if (!F) return faltou(el, "MODIS");
        ctx.tiles({ fogo: camada(d, "fogo", 0.85) });
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa('<b>MODIS · times burned since 2001</b><span><i class="g" style="background:linear-gradient(90deg,#ffffb2,#fd8d3c,#bd0026)"></i>1 → many</span>');
        // fire_history_pct is the share of the record's YEARS with any burn, not of the area
        var an = F.anual.parcela || [];
        graf.colunas(el, { x: an.map(function (x) { return String(x.ano); }), valores: an.map(function (x) { return x.pct; }),
          unidade: "% of the park burned that year (MODIS, 500 m)", cor: "#d9480f" });
        var comFogo = an.filter(function (x) { return x.pct > 0; }), pior = an.slice().sort(function (a, b) { return b.pct - a.pct; })[0];
        var ultimoAno = an.length ? an[an.length - 1].ano : null;
        ctx.texto("fogo", (comFogo.length ? "MODIS saw fire in the park in <b>" + comFogo.length + " of " + an.length + " years</b>; the worst was <b>" + pior.ano +
            "</b>, when " + fmt.pct(pior.pct, 1) + " of the park burned. " : "No burn has been mapped in the park since 2001. ") +
          (ultimoAno ? "The " + ultimoAno + " column is the year in progress." : ""));
      },

      validacao: function (ctx, d) {
        var el = ctx.$("#fig-validacao"), V = d.vlce2;
        if (!V) return faltou(el, "VLCE2");
        ctx.tiles({ v: camada(d, "vlce2_" + V.ano, 0.8) });
        ctx.vetores({ parcela: { geojson: parcelaGeo(d), estilo: CONTORNO } });
        ctx.enquadrar(parcelaGeo(d), { maxZoom: 12 });
        ctx.legendaMapa("<b>VLCE2 " + V.ano + " · Canadian Forest Service land cover</b>");
        var M = V.matriz.parcela || [], tot = M.reduce(function (s, x) { return s + x.ha; }, 0);
        graf.barrasH(el, { xRotulo: 190, max: 100, linhas: M.slice().sort(function (a, b) { return b.ha - a.ha; }).slice(0, 7).map(function (x) {
          return { rotulo: grupoCurto(d, x.aci) + " → " + grupoCurto(d, x.vlce2), sub: x.aci === x.vlce2 ? "agree" : "disagree", valor: 100 * x.ha / tot,
                   cor: x.aci === x.vlce2 ? "#1f6f4a" : "#d98324", texto: fmt.pct(100 * x.ha / tot, 1) + " · " + fmt.ha(x.ha) };
        }), rotulo: "Crop inventory → VLCE2, " + V.ano });
        var top = M.slice().sort(function (a, b) { return b.ha - a.ha; })[0], s = V.resumo;
        ctx.texto("validacao", "In this park the two maps agree on <b>" + fmt.pct(s.parcela.concordancia_pct) + "</b> of the area, and on " + fmt.pct(s.ring_5km.concordancia_pct) +
          " of the 2–5 km band. " + (top && top.aci !== top.vlce2 ? "The biggest disagreement: what the crop inventory calls <b>" + fmt.esc(grupo(d, top.aci).toLowerCase()) +
          "</b>, VLCE2 calls <b>" + fmt.esc(grupo(d, top.vlce2).toLowerCase()) + "</b> (" + fmt.ha(top.ha) + "). After a fire, standing dead trees and young regrowth are where a farm map and a forest map part ways." : ""));
      },

      procedencia: function (ctx, d) {
        ctx.tiles({}); ctx.vetores({}); ctx.legendaMapa("");
        graf.tabela(ctx.$("#fig-procedencia"), {
          colunas: [{ rotulo: "Analysis" }, { rotulo: "Source (asset)" }, { rotulo: "Scale", n: true }, { rotulo: "Computed", n: true }],
          linhas: (d.procedencia || []).map(function (p) { return [fmt.esc(p.nome), '<code style="font-size:11px;overflow-wrap:anywhere">' + fmt.esc(p.dataset) + "</code>", p.escala_m ? p.escala_m + " m" : "—", fmt.data(p.calculado_em)]; }),
          nota: "Boundary from CPCAD (" + fmt.esc(d.area.provincia) + "). This table travels with the report and the spreadsheet."
        });
        ctx.texto("procedencia", "This park took " + (d.procedencia || []).length + " Earth Engine analyses, all from the run of " + fmt.dataHora(d.gerado_em) + ".");
      }
    }
  });
})();
