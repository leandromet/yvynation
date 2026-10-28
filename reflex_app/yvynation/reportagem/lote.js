/* Yvynation — demonstração em rolagem do processamento em lote (/demonstracao/lote).
 *
 * Os passos 1–5 mostram prints de uma execução real (assets/demo_prints/, com
 * a lista de arquivos do ZIP dessa execução em lote_zip.json). O passo 6 é
 * calculado: /_demonstracao/yvynation.json?modo=lote (utils/demonstracao.py::lote),
 * a mesma analyze_mapbiomas que o lote roda, para as TIs regularizadas de um estado.
 */
(function () {
  var R = window.Reportagem, fmt = R.fmt, graf = R.graf;
  var COR = { dentro: "#d98324", fora: "#4f8f6f" };

  function feat(g) { return { type: "Feature", properties: {}, geometry: g && g.geometry ? g.geometry : g }; }

  R.iniciar({
    dados: "/_demonstracao/yvynation.json?modo=lote",
    centro: [-22.5, -55], zoom: 7,

    aoCarregar: function (ctx, d) {
      var c = d.catalogo || {};
      ctx.preencher({
        "n-ti": fmt.n(c.terras_indigenas), "n-uc": fmt.n(c.unidades_conservacao),
        "n-lote": fmt.n((d.territorios || []).length),
        "n-lote-rot": "terras de 200 a 1.000 ha de " + fmt.esc(c.uf || "—") + ' no exemplo do passo 6 <span class="selo real">real</span>'
      });
      ctx.$("#abertura-exemplo").innerHTML = "Prints de uma execução real com duas terras pequenas de Mato Grosso do Sul. Tabela do passo 6 calculada pelas funções do lote em " +
        fmt.dataHora(d.gerado_em) + " e guardada com esta página.";
      var erros = Object.keys(d.erros || {});
      ctx.$("#fim-extra").innerHTML = erros.length ? "Neste cálculo não responderam: <b>" + erros.map(fmt.esc).join(", ") + "</b>." : "";
      // a lista de arquivos do ZIP da execução dos prints
      fetch("/demo_prints/lote_zip.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (z) {
        if (!z) return;
        if (z.duracao_s) ctx.texto("executar", "A execução dos prints, com " + z.territorios.length + " terras pequenas e as análises padrão, levou <b>" + fmt.n(z.duracao_s) +
          " segundos</b> do início ao ZIP. O tempo cresce com a área e com as análises ligadas: os mapas em PNG e os relatórios em PDF são a parte mais lenta.");
        var el = ctx.$("#fig-zip"); if (!el) return;
        el.innerHTML = '<div class="rp-caixa-tit">Dentro do ZIP dessa execução (' + fmt.n(z.arquivos.length) + " arquivos, " + fmt.n(z.mb, 1) + " MB)</div>" +
          '<pre class="rp-formula" style="max-height:30vh;overflow:auto;white-space:pre">' + fmt.esc(z.arvore) + "</pre>";
      }).catch(function () { /* sem a lista, o print continua valendo */ });
    },

    passos: {
      comparar: function (ctx, d) {
        var el = ctx.$("#fig-comparar"), T = (d.territorios || []).slice();
        if (!T.length) { el.innerHTML = '<p class="rp-fig-estado erro">O lote de exemplo não respondeu <span class="selo ausente">ausente</span></p>'; return; }
        ctx.tiles({});
        var cor = function (d, f) { var gap = (d || 0) - (f || 0); return gap > 40 ? "#c0392b" : gap > 15 ? "#d98324" : "#30a46c"; };
        var tis = { type: "FeatureCollection", features: T.map(function (t) { var f = feat(t.geojson); f.properties = { nome: t.nome, d: t.nativa_dentro_pct, f: t.nativa_buffer_pct }; return f; }) };
        var dica = function (f) { return fmt.esc(f.properties.nome) + ": " + fmt.pct(f.properties.d) + " dentro · " + fmt.pct(f.properties.f) + " em volta"; };
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
        ctx.legendaMapa("<b>Diferença dentro − em volta (vegetação nativa)</b>" + '<span><i style="background:#c0392b"></i>mais de 40 pontos</span><span><i style="background:#d98324"></i>15 a 40</span><span><i style="background:#30a46c"></i>menos de 15</span>');
        T.sort(function (a, b) { return ((b.nativa_dentro_pct || 0) - (b.nativa_buffer_pct || 0)) - ((a.nativa_dentro_pct || 0) - (a.nativa_buffer_pct || 0)); });
        var linhas = [];
        T.forEach(function (t) {
          linhas.push({ rotulo: t.nome + " · dentro", valor: t.nativa_dentro_pct, cor: COR.dentro, texto: fmt.pct(t.nativa_dentro_pct, 1) });
          linhas.push({ rotulo: t.nome + " · em volta", valor: t.nativa_buffer_pct, cor: COR.fora, texto: fmt.pct(t.nativa_buffer_pct, 1) });
        });
        graf.barrasH(el, { linhas: linhas, max: 100, xRotulo: 240 });
        var a = T[0], z = T[T.length - 1];
        var med = function (k) { var v = T.map(function (t) { return t[k] || 0; }).sort(function (x, y) { return x - y; }); return v[Math.floor(v.length / 2)]; };
        ctx.texto("comparar", "Em " + d.ano + ", a mediana das " + T.length + " terras é de <b>" + fmt.pct(med("nativa_dentro_pct")) + "</b> de vegetação nativa dentro e <b>" +
          fmt.pct(med("nativa_buffer_pct")) + "</b> em volta. A maior diferença está em <b>" + fmt.esc(a.nome) + "</b> (" + fmt.pct(a.nativa_dentro_pct) + " dentro, " + fmt.pct(a.nativa_buffer_pct) +
          " em volta); a menor, em <b>" + fmt.esc(z.nome) + "</b> (" + fmt.pct(z.nativa_dentro_pct) + " e " + fmt.pct(z.nativa_buffer_pct) + ").");
      }
    }
  });
})();
