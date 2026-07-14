# Yvynation Reflex - README

🏞️ **Indigenous Land Monitoring Platform** - Modern Reflex Version

## Building the Future of Land Monitoring

This is a complete rewrite of Yvynation from Streamlit to **Reflex** for superior performance and user experience.

### 🚀 Key Improvements

| Metric | Streamlit | Reflex |
|--------|-----------|--------|
| **Time to Interaction** | 2-3 seconds | < 500ms |
| **Memory Usage** | High (full reload) | Optimized (persistent state) |
| **Concurrent Users** | Limited | Scales to 1000+ |
| **Development Speed** | 100% Python UI | 100% Python (no JS needed) |

### 📦 Features

- 🌍 **Multiple Earth Engine Datasets**: MapBiomas Collection 10.1 (1985–2024), Hansen/GLAD, Hansen Global Forest Change
- 🪶 **Two territory sources**: FUNAI indigenous lands (657 TIs) and CNUC conservation units (3,247 UCs), switchable in both the interactive sidebar and batch mode (local GeoPackages, no EE round-trip for boundaries)
- 🗺️ **Interactive Leaflet Maps**: click-to-select territory boundaries, draw/import custom geometries, auto-buffer rings
- 📊 **Real-time Analysis**: land cover classification, year comparison with transition Sankey/sunburst/treemap/matrix, forest loss detection
- 📈 **Deforestation timeline**: annual Hansen loss + MapBiomas deforestation/regrowth + fire scars, framed by Brazilian political stripes, an ENSO (ONI) El Niño/La Niña strip, and forest-policy milestone rows
- 🌀 **Multi-window transitions**: multi-stage Sankey + per-pair sunbursts across 3–N years
- 🏭 **Batch processing** (`/batch`): run the full analysis suite over dozens of areas — paste/upload a name list to auto-select; results appear live as files while the run progresses and are packed into a single ZIP (1 GB+ supported, streamed over HTTP)
- 📤 **Structured exports**: per-area folder trees with CSVs, Plotly figures (PNG + HTML), boundary GeoJSON, and PNG map sets — identical naming between interactive and batch exports so they merge cleanly
- 🌐 **Multi-language Support**: English, Portuguese, Spanish
- ☁️ **Cloud-optimized**: Deploys to Google Cloud Run in seconds

### 🛠️ Tech Stack

- **Framework**: Reflex (React-like framework for Python)
- **Mapping**: Leaflet.js (integrated as custom component)
- **Data**: Google Earth Engine, Google Cloud Storage
- **Cloud**: Google Cloud Run (serverless deployment)
- **Database**: SQLite (local) or PostgreSQL (production)

### 📋 Getting Started

```bash
# 1. Clone and setup
cd reflex_app/
python -m venv .venv
source .venv/bin/activate

# 2. Configure environment
cp .env.example .env
# Edit .env with your GCP credentials

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run locally
reflex run

# 5. Open browser
# http://localhost:3000
```

### ☁️ Deploy to Cloud Run

```bash
# Build Docker image
docker build -t yvynation .

# Deploy
gcloud run deploy yvynation \
  --source . \
  --platform managed \
  --memory 2Gi \
  --cpu 2 \
  --region us-central1 \
  --allow-unauthenticated
```

### 🏗️ Project Structure

```
yvynation/
├── state/                 # Reactive state: AppState + 8 domain mixins
│   ├── __init__.py        #   all state vars + computed vars (charts, tables)
│   ├── _territory.py      #   territory selection (indigenous/conservation)
│   ├── _analysis.py       #   analysis runs + per-area result bundles
│   ├── _advanced_viz.py   #   map sets, multi-window, deforestation timeline
│   ├── _batch.py          #   batch pipeline (live folder → final ZIP)
│   ├── _export.py         #   CSV / ZIP / PDF / download-all
│   └── _map.py, _geometry.py, _ui.py
├── components/            # rx.Component functions (sidebars, map, analysis tabs)
├── pages/                 # / (index), /batch, /portal, …
├── config/                # EE asset IDs, palettes, region of interest
└── utils/
    ├── territory_service.py       # indigenous_lands_br202605.gpkg (singleton)
    ├── conservation_service.py    # environment_conservation_br202605.gpkg
    ├── mapbiomas_analysis.py / hansen_analysis.py
    ├── visualization.py           # Plotly charts incl. timeline + ENSO strip
    ├── export_service.py          # export ZIP structure + exports dir helpers
    ├── enso_oni.json              # NOAA CPC Oceanic Niño Index (1950–present)
    └── translations.py            # i18n (EN/PT/ES)
```

### 📥 Exports & downloads

Large archives are never shipped through the websocket: they are written under
`uploaded_files/exports/` and downloaded over HTTP via Reflex's `/_upload`
mount (no practical size limit — 1 GB+ batch archives work). Batch runs write
plain files into a live `yvynation_batch_{timestamp}/` folder you can browse
while the run is in progress; the folder is compressed into the final ZIP at
the end (including on "Stop after current") and then removed. A folder without
its same-name `.zip` is an in-progress or crashed run and is never auto-deleted.

### 🔄 Migration from Streamlit

See [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for detailed instructions on:
- Converting Streamlit components to Reflex
- Refactoring event handlers
- Implementing async operations
- State management patterns

### 🧪 Development

```bash
# Format code
black yvynation/

# Type checking
mypy yvynation/

# Run tests
pytest

# Lint
flake8 yvynation/
```

### 📚 Resources

- [Reflex Documentation](https://reflex.dev/)
- [Earth Engine API](https://developers.google.com/earth-engine)
- [Leaflet Documentation](https://leafletjs.com/)
- [Google Cloud Run](https://cloud.google.com/run)

### 📄 License

Same as original Yvynation project

### 🤝 Contributing

1. Create a branch for your feature
2. Make changes with focus on performance
3. Test thoroughly with `pytest`
4. Submit PR with benchmark results

---

**Questions?** Check the MIGRATION_GUIDE.md or open an issue on the repository.
