/* Yvynation — demonstração em rolagem do processamento em lote (/demonstracao/lote, /walkthrough/batch).
 *
 * Os passos 1–5 mostram prints de uma execução real (assets/demo_prints/, com
 * a lista de arquivos do ZIP dessa execução em lote_zip.json). O passo 6 é
 * calculado: /_demonstracao/yvynation.json?modo=lote (utils/demonstracao.py::lote),
 * a mesma analyze_mapbiomas que o lote roda, para as TIs regularizadas de um estado.
 */
(function () {
  var R = window.Reportagem, fmt = R.fmt, graf = R.graf;
  var COR = { dentro: "#d98324", fora: "#4f8f6f" };
  var T;   // ctx.t(pt, en), guardado no primeiro uso

  function feat(g) { return { type: "Feature", properties: {}, geometry: g && g.geometry ? g.geometry : g }; }

  R.iniciar({
    dados: "/_demonstracao/yvynation.json?modo=lote",
    centro: [-22.5, -55], zoom: 7,

    aoCarregar: function (ctx, d) {
      T = ctx.t;
      var c = d.catalogo || {};
      ctx.preencher({
        "n-ti": fmt.n(c.terras_indigenas), "n-uc": fmt.n(c.unidades_conservacao),
        "n-lote": fmt.n((d.territorios || []).length),
        "n-lote-rot": T("terras de 200 a 1.000 ha de " + fmt.esc(c.uf || "—") + " no exemplo do passo 6", "lands of 200 to 1,000 ha in " + fmt.esc(c.uf || "—") + " in the step 6 example") +
          ' <span class="selo real">' + T("real", "measured") + "</span>"
      });
      ctx.$("#abertura-exemplo").innerHTML = T("Prints de uma execução real com duas terras pequenas de Mato Grosso do Sul. Tabela do passo 6 calculada pelas funções do lote em ",
        "Screenshots from a real run with two small lands in Mato Grosso do Sul. The step 6 table was computed by the batch's functions on ") +
        fmt.dataHora(d.gerado_em) + T(" e guardada com esta página.", " and stored with this page.");
      var erros = Object.keys(d.erros || {});
      ctx.$("#fim-extra").innerHTML = erros.length ? T("Neste cálculo não responderam: <b>", "Parts that did not respond in this run: <b>") + erros.map(fmt.esc).join(", ") + "</b>." : "";
      // a lista de arquivos do ZIP da execução dos prints
      fetch("/demo_prints/lote_zip.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (z) {
        if (!z) return;
        if (z.duracao_s) ctx.texto("executar", T("A execução dos prints, com " + z.territorios.length + " terras pequenas e as análises padrão, levou <b>" + fmt.n(z.duracao_s) +
          " segundos</b> do início ao ZIP. O tempo cresce com a área e com as análises ligadas: os mapas em PNG e os relatórios em PDF são a parte mais lenta.",
          "The run in the screenshots, with " + z.territorios.length + " small lands and the default analyses, took <b>" + fmt.n(z.duracao_s) +
          " seconds</b> from start to ZIP. Time grows with area and with the analyses switched on: the PNG maps and PDF reports are the slowest part."));
        var el = ctx.$("#fig-zip"); if (!el) return;
        el.innerHTML = '<div class="rp-caixa-tit">' + T("Dentro do ZIP dessa execução (", "Inside that run's ZIP (") + fmt.n(z.arquivos.length) + T(" arquivos, ", " files, ") + fmt.n(z.mb, 1) + " MB)</div>" +
          '<pre class="rp-formula" style="max-height:30vh;overflow:auto;white-space:pre">' + fmt.esc(z.arvore) + "</pre>";
      }).catch(function () { /* sem a lista, o print continua valendo */ });
    },

    passos: {
      comparar: function (ctx, d) {
        var el = ctx.$("#fig-comparar"), L = (d.territorios || []).slice();
        if (!L.length) { el.innerHTML = '<p class="rp-fig-estado erro">' + T("O lote de exemplo não respondeu", "The example batch did not respond") + ' <span class="selo ausente">' + T("ausente", "missing") + "</span></p>"; return; }
        ctx.tiles({});
        var cor = function (d, f) { var gap = (d || 0) - (f || 0); return gap > 40 ? "#c0392b" : gap > 15 ? "#d98324" : "#30a46c"; };
        var tis = { type: "FeatureCollection", features: L.map(function (t) { var f = feat(t.geojson); f.properties = { nome: t.nome, d: t.nativa_dentro_pct, f: t.nativa_buffer_pct }; return f; }) };
        var dica = function (f) { return fmt.esc(f.properties.nome) + ": " + fmt.pct(f.properties.d) + T(" dentro · ", " inside · ") + fmt.pct(f.properties.f) + T(" em volta", " around"); };
        // terras de 200 a 1.000 ha somem na escala do estado: um ponto por terra, na mesma cor do contorno
        var pontos = { type: "FeatureCollection", features: tis.features.map(function (f) {
          var c = ctx.L.geoJSON(f).getBounds().getCenter();
          return { type: "Feature", properties: f.properties, geometry: { type: "Point", coordinates: [c.lng, c.lat] } };
        }) };
        ctx.vetores({
          tis: { geojson: tis, estilo: function (f) { return { color: "#ffd400", weight: 2, fillColor: cor(f.properties.d, f.properties.f), fillOpacity: 0.35 }; }, popup: dica },
          pontos: { geojson: pontos, ponto: function (f) { return { radius: 7, color: "#fff", weight: 2, fillColor: cor(f.properties.d, f.properties.f), fillOpacity: 1 }; }, popup: dica }
        });
        ctx.enquadrar(tis, { maxZoom: 11 });
        ctx.legendaMapa(T("<b>Diferença dentro − em volta (vegetação nativa)</b>", "<b>Inside − around difference (native vegetation)</b>") + '<span><i style="background:#c0392b"></i>' + T("mais de 40 pontos", "over 40 points") +
          '</span><span><i style="background:#d98324"></i>' + T("15 a 40", "15 to 40") + '</span><span><i style="background:#30a46c"></i>' + T("menos de 15", "under 15") + "</span>");
        L.sort(function (a, b) { return ((b.nativa_dentro_pct || 0) - (b.nativa_buffer_pct || 0)) - ((a.nativa_dentro_pct || 0) - (a.nativa_buffer_pct || 0)); });
        var linhas = [];
        L.forEach(function (t) {
          linhas.push({ rotulo: t.nome + T(" · dentro", " · inside"), valor: t.nativa_dentro_pct, cor: COR.dentro, texto: fmt.pct(t.nativa_dentro_pct, 1) });
          linhas.push({ rotulo: t.nome + T(" · em volta", " · around"), valor: t.nativa_buffer_pct, cor: COR.fora, texto: fmt.pct(t.nativa_buffer_pct, 1) });
        });
        graf.barrasH(el, { linhas: linhas, max: 100, xRotulo: 240 });
        var a = L[0], z = L[L.length - 1];
        var med = function (k) { var v = L.map(function (t) { return t[k] || 0; }).sort(function (x, y) { return x - y; }); return v[Math.floor(v.length / 2)]; };
        var md = fmt.pct(med("nativa_dentro_pct")), mf = fmt.pct(med("nativa_buffer_pct"));
        ctx.texto("comparar", T("Em " + d.ano + ", a mediana das " + L.length + " terras é de <b>" + md + "</b> de vegetação nativa dentro e <b>" + mf + "</b> em volta. A maior diferença está em <b>" +
            fmt.esc(a.nome) + "</b> (" + fmt.pct(a.nativa_dentro_pct) + " dentro, " + fmt.pct(a.nativa_buffer_pct) + " em volta); a menor, em <b>" + fmt.esc(z.nome) + "</b> (" + fmt.pct(z.nativa_dentro_pct) + " e " + fmt.pct(z.nativa_buffer_pct) + ").",
          "In " + d.ano + ", the median across the " + L.length + " lands is <b>" + md + "</b> native vegetation inside and <b>" + mf + "</b> around. The largest gap is in <b>" +
            fmt.esc(a.nome) + "</b> (" + fmt.pct(a.nativa_dentro_pct) + " inside, " + fmt.pct(a.nativa_buffer_pct) + " around); the smallest, in <b>" + fmt.esc(z.nome) + "</b> (" + fmt.pct(z.nativa_dentro_pct) + " and " + fmt.pct(z.nativa_buffer_pct) + ")."));
      }
    }
  });
})();
