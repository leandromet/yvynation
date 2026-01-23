# Documentation Index

Welcome to the Yvynation documentation! This folder contains comprehensive guides for using, developing, and deploying the platform.

## 📋 Quick Navigation

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Service Account Setup](SERVICE_ACCOUNT_SETUP.md)** - Configure Earth Engine authentication
- **[Cloud Run Setup](CLOUD_RUN_SETUP.md)** - Deploy to Google Cloud

### Architecture & Design
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design overview
- **[ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md)** - Visual architecture diagram
- **[Project Structure](../PROJECT_STRUCTURE.md)** - Detailed folder organization

### Development
- **[Refactor Guide](REFACTOR_GUIDE.md)** - Code refactoring and best practices
- **[Build Summary](BUILD_SUMMARY.md)** - Project build history
- **[Bug Fixes](BUG_FIXES.md)** - Known issues and fixes
- **[Migrations](MIGRATION_SUMMARY.md)** - Code migrations and updates

### Data & Analysis
- **[Color Map Updates](COLOR_MAP_UPDATE_SUMMARY.md)** - Land cover color mappings
- **[Class Updates](CLASS_48_FIX_SUMMARY.md)** - Land cover classification updates
- **[Consolidation Examples](../archive/legacy_code/HANSEN_CONSOLIDATION_EXAMPLES.py)** - Hansen data processing examples

### Other Resources
- **[Streamlit Integration](STREAMLIT_INTEGRATION_SUMMARY.md)** - Streamlit setup guide
- **[Completion Checklist](COMPLETION_CHECKLIST.md)** - Project completion status
- **[Refactoring Complete](REFACTORING_COMPLETE.md)** - Refactoring summary

## 📚 Documentation Sections

### For Users
1. Start with [QUICKSTART.md](QUICKSTART.md)
2. Review [../README.md](../README.md) for overview
3. Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design

### For Developers
1. Read [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
2. Review [REFACTOR_GUIDE.md](REFACTOR_GUIDE.md)
3. Check [ARCHITECTURE.md](ARCHITECTURE.md)
4. See [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) for recent changes

### For DevOps/Deployment
1. [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md) - Earth Engine setup
2. [CLOUD_RUN_SETUP.md](CLOUD_RUN_SETUP.md) - Google Cloud deployment
3. [STREAMLIT_INTEGRATION_SUMMARY.md](STREAMLIT_INTEGRATION_SUMMARY.md) - Streamlit deployment

## 📁 Documentation Files

| File | Purpose |
|------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup guide |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design and structure |
| [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) | Visual system diagram |
| [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md) | Earth Engine authentication |
| [CLOUD_RUN_SETUP.md](CLOUD_RUN_SETUP.md) | Google Cloud deployment |
| [REFACTOR_GUIDE.md](REFACTOR_GUIDE.md) | Code refactoring guide |
| [BUILD_SUMMARY.md](BUILD_SUMMARY.md) | Build history and updates |
| [BUG_FIXES.md](BUG_FIXES.md) | Known issues and solutions |
| [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) | Code migration notes |
| [STREAMLIT_INTEGRATION_SUMMARY.md](STREAMLIT_INTEGRATION_SUMMARY.md) | Streamlit setup |
| [COLOR_MAP_UPDATE_SUMMARY.md](COLOR_MAP_UPDATE_SUMMARY.md) | Color mapping details |
| [CLASS_48_FIX_SUMMARY.md](CLASS_48_FIX_SUMMARY.md) | Land cover classification |
| [COMPLETION_CHECKLIST.md](COMPLETION_CHECKLIST.md) | Project status |
| [REFACTORING_COMPLETE.md](REFACTORING_COMPLETE.md) | Refactoring summary |

## 🔍 Find What You Need

**"How do I..."**
- **...get started?** → [QUICKSTART.md](QUICKSTART.md)
- **...set up Earth Engine?** → [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md)
- **...deploy to the cloud?** → [CLOUD_RUN_SETUP.md](CLOUD_RUN_SETUP.md)
- **...understand the code?** → [ARCHITECTURE.md](ARCHITECTURE.md) + [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)
- **...refactor code?** → [REFACTOR_GUIDE.md](REFACTOR_GUIDE.md)
- **...deploy with Streamlit?** → [STREAMLIT_INTEGRATION_SUMMARY.md](STREAMLIT_INTEGRATION_SUMMARY.md)

## 📖 Reading Order (by Role)

### New Users
1. [../README.md](../README.md) - Project overview
2. [QUICKSTART.md](QUICKSTART.md) - Get it running
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system

### Developers
1. [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md) - Code organization
2. [ARCHITECTURE.md](ARCHITECTURE.md) - System design
3. [REFACTOR_GUIDE.md](REFACTOR_GUIDE.md) - Code standards
4. [MIGRATION_SUMMARY.md](MIGRATION_SUMMARY.md) - Recent changes

### DevOps Engineers
1. [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md) - Prerequisites
2. [CLOUD_RUN_SETUP.md](CLOUD_RUN_SETUP.md) - Deployment
3. [STREAMLIT_INTEGRATION_SUMMARY.md](STREAMLIT_INTEGRATION_SUMMARY.md) - App deployment

## 📞 Need Help?

- **Installation Issues**: See [QUICKSTART.md](QUICKSTART.md) troubleshooting
- **Earth Engine Auth**: Check [SERVICE_ACCOUNT_SETUP.md](SERVICE_ACCOUNT_SETUP.md)
- **Code Questions**: Review [ARCHITECTURE.md](ARCHITECTURE.md)
- **Bugs/Issues**: See [BUG_FIXES.md](BUG_FIXES.md)

## 🔗 External Resources

- [Google Earth Engine Documentation](https://developers.google.com/earth-engine)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [MapBiomas](https://mapbiomas.org/)
- [geemap Documentation](https://geemap.org/)

---

**Last Updated**: January 2026  
**Version**: 1.0.0
- All features demonstrated
- Results visualization
- **Run this in Jupyter/VSCode!**

### 3. **Architecture Deep Dive** → [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
- Notebook-to-app conversion details
- Module responsibilities
- Design patterns & solutions
- Data source documentation
- Complete code listings

### 4. **Project Overview** → [README.md](README.md)
- Project goals & motivation
- Key features
- Data sources (MapBiomas, Territories, SPOT)
- Setup instructions

---

## 🗂️ Project Structure

```
/home/leandromb/google_eengine/yvynation/
│
├── 📚 DOCUMENTATION
│   ├── README.md                    # Project overview
│   ├── QUICKSTART.md               # Quick start guide (START HERE!)
│   ├── BUILD_SUMMARY.md            # Architecture & conversion details
│   └── INDEX.md                    # This file
│
├── 🎯 MAIN APPLICATION
│   ├── app_file.py                 # YvynationApp orchestration class
│   ├── config.py                   # Constants, assets, colors, labels
│   └── main.py                     # CLI entry point
│
├── 🔧 MODULES (Import as needed)
│   ├── load_data.py                # Load MapBiomas & territories
│   ├── analysis.py                 # Area calculations, change detection
│   ├── visualization.py            # Interactive maps with geemap
│   ├── plots.py                    # Charts, trends, Sankey diagrams
│   └── spot_module.py              # Graceful SPOT data handling
│
├── 📖 NOTEBOOKS
│   └── demo_yvynation_app.ipynb    # Interactive 11-section demo
│
├── 📦 DEPENDENCIES
│   └── requirements.txt             # All Python packages
│
└── 🔐 VERSION CONTROL
    └── .git/                        # Git repository (4 commits)
```

---

## 🚀 Quick Start (30 seconds)

```bash
cd /home/leandromb/google_eengine/yvynation
pip install -r requirements.txt
# Then open demo_yvynation_app.ipynb in Jupyter or VSCode
```

Or in Python:
```python
import ee
from app_file import YvynationApp

ee.Initialize(project="ee-leandromet")
app = YvynationApp()
app.load_core_data()
Map = app.create_basic_map()
Map.to_streamlit(height=600)
```

---

## 📊 What's Included

### Core Functionality
✅ **Interactive Maps** - MapBiomas layers, territories, change detection  
✅ **Area Analysis** - Land cover distribution for 62 classes (1985-2023)  
✅ **Change Detection** - Forest loss/gain quantification  
✅ **Territory Filtering** - By state, name, or custom geometry  
✅ **Visualizations** - Bar charts, comparisons, temporal trends, Sankey  
✅ **SPOT Data** - Graceful access handling for restricted satellite data  
✅ **Data Export** - Cloud Storage export tasks  

### Data Coverage
✅ **MapBiomas Collection 9** - Annual land cover 1985-2023 (30m resolution)  
✅ **Indigenous Territories** - 700+ Brazilian territories (vector)  
✅ **Sentinel-2** - Recent satellite imagery (optional)  
✅ **SPOT 2008** - High-resolution multispectral (if access granted)  

---

## 📖 Module Quick Reference

| Module | Purpose | Key Classes/Functions |
|--------|---------|----------------------|
| **app_file.py** | Main application orchestration | `YvynationApp` class with 7 methods |
| **config.py** | All constants & settings | Paths, colors, labels, thresholds |
| **load_data.py** | Data loading from Earth Engine | `load_mapbiomas()`, `load_territories()` |
| **analysis.py** | Statistical analysis | Area calc, change detection, filtering |
| **visualization.py** | Interactive maps | Map creation, layers, legends |
| **plots.py** | Charts & graphs | Bar charts, trends, comparisons |
| **spot_module.py** | Restricted SPOT access | Graceful access checking |

---

## 🎯 Common Tasks

### Task: Create a map of Maranhão territories
```python
from app_file import YvynationApp
app = YvynationApp()
app.load_core_data()
Map = app.create_territory_map(state_code='MA', zoom=7)
Map.to_streamlit(height=600)
```

### Task: Analyze land cover changes 1985-2023
```python
results = app.analyze_territories(start_year=1985, end_year=2023)
from plots import plot_area_changes
plot_area_changes(results['comparison'], 1985, 2023)
```

### Task: Get area distribution for specific territories
```python
from analysis import filter_territories_by_names
territories = app.territories
bacurizinho = filter_territories_by_names(territories, ['Bacurizinho'])
results = app.analyze_territories(geometry=bacurizinho)
```

### Task: Export analysis to Cloud Storage
```python
task = app.export_results(
    app.mapbiomas['2023'],
    name='yvynation_2023_analysis'
)
print(task.status())
```

---

## 💡 Design Highlights

### Graceful SPOT Access
The app automatically checks SPOT data availability:
```python
app.load_spot_if_available()
if app.spot_available:
    # Use SPOT analysis
else:
    # Continue with MapBiomas (always available)
```
This ensures the app never breaks due to restricted data access.

### Modular Architecture
Each module has a single responsibility:
- **analysis.py** - Pure data operations (no visualization)
- **visualization.py** - Map rendering only
- **plots.py** - Chart generation only
- **spot_module.py** - SPOT-specific logic isolated

### Centralized Configuration
All constants in one place:
```python
from config import MAPBIOMAS_COLOR_MAP, MAPBIOMAS_LABELS, PROJECT_ID
```
Easy to modify colors, asset paths, or processing parameters.

---

## 🔍 Code Statistics

- **Total Lines of Code:** ~1,100
- **Number of Modules:** 7 core modules
- **Functions Created:** 50+
- **Class Methods:** 7 (YvynationApp)
- **Source Material:** 94-cell Jupyter notebook converted to production code
- **Git Commits:** 4 (organized development history)

---

## 📥 Data Sources

### MapBiomas Brazil Collection 9
- **Asset:** `projects/mapbiomas-public/assets/brazil/lulc/collection9/mapbiomas_collection90_integration_v1`
- **Resolution:** 30 meters
- **Time Period:** 1985-2023 (annual)
- **Classes:** 62 land cover classes
- **License:** Creative Commons Attribution 4.0

### Indigenous Territories
- **Asset:** `projects/mapbiomas-territories/assets/TERRITORIES-OLD/LULC/BRAZIL/COLLECTION9/WORKSPACE/INDIGENOUS_TERRITORIES`
- **Type:** Vector (FeatureCollection)
- **Count:** 700+ territories
- **Attributes:** Name, state, year, area, geometry
- **License:** Public (MapBiomas Territories Project)

### SPOT 2008 (Restricted)
- **Asset:** `projects/google/brazil_forest_code/spot_bfc_ms_mosaic_v02`
- **Resolution:** High resolution multispectral
- **Bands:** Multispectral + visual
- **Access:** Special request required
- **Handled by:** `spot_module.py` with graceful degradation

---

## 🛠️ Development Tools

All work managed via:
- **Git:** Version control with 4 commits
- **Earth Engine:** Core processing engine
- **geemap:** Interactive Jupyter/VSCode mapping
- **Jupyter:** Interactive notebook environment
- **VSCode:** Development editor

---

## 🔗 Next Steps

1. **Immediate (Now):**
   - Read [QUICKSTART.md](QUICKSTART.md)
   - Run [demo_yvynation_app.ipynb](demo_yvynation_app.ipynb)
   - Try one of the 5 code examples

2. **Short-term (Today):**
   - Explore your territories of interest
   - Customize analysis parameters
   - Generate maps and charts for your region

3. **Medium-term (This week):**
   - Request SPOT data access (if needed)
   - Extend YvynationApp with custom analyses
   - Export results to Cloud Storage

4. **Long-term (Ongoing):**
   - Add deforestation-specific metrics
   - Integrate additional data sources
   - Deploy in production environments

---

## 📚 Resources

- [Earth Engine Python API Docs](https://developers.google.com/earth-engine/tutorials/community/intro-to-python-api)
- [geemap Documentation](https://geemap.org/)
- [MapBiomas Project](https://mapbiomas.org/)
- [Earth Engine Code Editor](https://code.earthengine.google.com/)
- [Jupyter Notebook Docs](https://jupyter.org/)

---

## 🎯 Key Concepts

### YvynationApp
Main orchestration class that:
- Loads MapBiomas and territory data
- Performs analysis and filtering
- Creates visualizations
- Attempts SPOT access (gracefully fails if unavailable)
- Exports results

### Territory Filtering
Filter datasets by:
- **State code** (`state_code='MA'` for Maranhão)
- **Territory names** (`territory_names=['Bacurizinho']`)
- **Custom geometry** (any ee.Geometry)

### Time Series Analysis
Compare any years from 1985-2023:
```python
results = app.analyze_territories(start_year=1985, end_year=2023)
```
Returns area for start & end years plus calculated changes.

### Change Quantification
Automatically calculates:
- Absolute change (km²)
- Percentage change
- Class-specific gains/losses
- Transition matrices (framework)

---

## ✅ Verification Checklist

- [x] All modules created and tested
- [x] YvynationApp class fully integrated
- [x] Demo notebook with 11 complete sections
- [x] SPOT access properly isolated (graceful handling)
- [x] All 4 documentation files (README, BUILD_SUMMARY, QUICKSTART, INDEX)
- [x] 4 git commits with clean history
- [x] Requirements.txt updated with all dependencies
- [x] Ready for production use

---

**Last Updated:** 2024  
**Version:** 1.0 (Complete)  
**Status:** ✅ Ready for Use  
**Git Commits:** 4 (b80f18e latest)

---

### Getting Help

1. **Quick answers?** → Check [QUICKSTART.md](QUICKSTART.md)
2. **Want to learn?** → Run [demo_yvynation_app.ipynb](demo_yvynation_app.ipynb)
3. **Architecture questions?** → Read [BUILD_SUMMARY.md](BUILD_SUMMARY.md)
4. **Module details?** → Check docstrings in Python files
5. **Earth Engine help?** → Visit [code.earthengine.google.com](https://code.earthengine.google.com/)

---

**Happy analyzing! 🌍**
