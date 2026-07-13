# Yvynation — Four Indigenous Territories: methodology & results documentation

This folder documents the analytical work behind the case-study report
`LeandroBiondo_case_studies(1).txt` — a PhD results report on four Brazilian
Indigenous Territories (six polygons) analysed with the **Yvynation Reflex**
application. These notes make the *method* explicit and connect it to the
*outputs* produced by the software, so the chapter narratives can be read
against the numbers that generated them.

## What links to what

| Piece | Where it lives |
|---|---|
| Narrative report (chapters 7–11) | `docs/LeandroBiondo_case_studies(1).txt` |
| The software that produces the results | `yvynation/pages/batch_processing.py` (+ `state/`) |
| Beta deployment | https://yvynation-reflex-652582010777.us-west1.run.app/ |
| Source code | https://github.com/leandromet/yvynation |
| April 2026 run outputs (MapBiomas Coll. 9) | `~/Documents/2026_ubc/four_indigenous_territories/data/yvynation_reflex_results/` |
| May 2026 batch run (MapBiomas Coll. 10 + buffers) | Drive `case_studies/` folder; summarised in `multi_window.md` |

## Documentation set

1. **[METHODOLOGY.md](METHODOLOGY.md)** — the analytical framework: data
   sources, the batch pipeline in `batch_processing.py`, the metrics computed,
   the output artefacts, the 10 km buffer counterfactual, the quadrant clipping
   for very large areas, and the two data-version epochs (Coll. 9 vs Coll. 10).
2. **[RESULTS.md](RESULTS.md)** — a territory-by-territory reading of the April
   2026 run outputs, grounded in the exported CSVs, explaining what each
   polygon's numbers mean and how they refine the chapter narrative.
3. **[SYNTHESIS.md](SYNTHESIS.md)** — the cross-case argument: the coast-to-west
   policy gradient, the three temporal signatures of "policy lag", the buffer
   protective-effect finding, and the comparative land-market / ecosystem-service
   valuation.

## The two other notes already here

- `multi_window.md` — territory-vs-buffer summary from the May 2026 Collection 10
  batch (the numbers behind the "Territory and Buffer Batch Run" section of the
  report). It is the buffer counterpart to `RESULTS.md`.
- `buffer_changes.md` — engineering changelog for the buffer/map features.
- `local_llm_mistral24b.md` — unrelated local-LLM note.

## One caveat to carry through all of this

The report mixes two data epochs. The **per-territory result folders** examined
in `RESULTS.md` are the **April 2026 run on MapBiomas Collection 9 (1985–2023)**
with Hansen GFC to 2024. The **buffer and multi-window** figures in
`multi_window.md` and the report's batch section are the **May 2026 run on
MapBiomas Collection 10 (1985–2024)** with Hansen to 2025. Class areas, forest
percentages, and end-years therefore differ slightly between the two — this is
expected, and the report flags it explicitly (§11.1). Collection 11 (1985–2025)
is expected August 2026 and will trigger a re-run.
