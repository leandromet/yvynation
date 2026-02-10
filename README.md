# 🌎 Yvynation - Indigenous Land Monitoring Platform

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)
![Earth Engine](https://img.shields.io/badge/Google%20Earth%20Engine-API-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

> 🚀 **[Try the Live Demo](https://yvynation-652582010777.us-west1.run.app/)** - Access the platform now!

**Yvynation** is an interactive web platform for analyzing land cover changes in indigenous territories using Google Earth Engine and MapBiomas data. The platform enables researchers, policymakers, and indigenous communities to understand deforestation trends and environmental changes in real-time.

## 📖 Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [Author](#author)
- [License](#license)

## ✨ Features

✅ **Interactive Mapping** - Real-time geospatial visualization using Folium and geemap  
✅ **Land Cover Analysis** - MapBiomas (1985-2023) and Hansen/GLAD global forest change data  
✅ **Territory Analysis** - 700+ Brazilian indigenous territories with detailed statistics  
✅ **Temporal Comparison** - Compare land cover changes between any two years  
✅ **Draw & Analyze** - Custom polygon drawing for area-specific analysis  
✅ **Statistical Visualizations** - Area distribution charts, transition diagrams, and metrics  
✅ **Data Export** - Download analysis results as CSV/DataFrame  

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Earth Engine account ([sign up here](https://earthengine.google.com/signup/))
- Google Cloud Project with Earth Engine API enabled

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd yvynation

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Authenticate with Earth Engine
earthengine authenticate
```

### Run the Application

```bash
#use an alternative python environment
source .venv/bin/activate
# Start the Streamlit app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## 📚 Documentation

Comprehensive documentation is available in the [docs/](docs/) folder:

### Core Documentation
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design and architecture
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Detailed project organization

### Setup & Configuration
- **[SERVICE_ACCOUNT_SETUP.md](docs/SERVICE_ACCOUNT_SETUP.md)** - Earth Engine authentication
- **[CLOUD_RUN_SETUP.md](docs/CLOUD_RUN_SETUP.md)** - Deploy to Google Cloud Run

### Development & References
- **[REFACTOR_GUIDE.md](docs/REFACTOR_GUIDE.md)** - Code refactoring guide
- **[BUILD_SUMMARY.md](docs/BUILD_SUMMARY.md)** - Project build history
- **[ARCHITECTURE_DIAGRAM.md](docs/ARCHITECTURE_DIAGRAM.md)** - Visual architecture
- **[INDEX.md](docs/INDEX.md)** - Complete documentation index

### Data & Analysis
- **[HANSEN_CONSOLIDATION_EXAMPLES.py](archive/legacy_code/HANSEN_CONSOLIDATION_EXAMPLES.py)** - Hansen data processing examples
- **[COLOR_MAP_UPDATE_SUMMARY.md](docs/COLOR_MAP_UPDATE_SUMMARY.md)** - Color mapping documentation

### Archives & Legacy
- **[archive/README.md](archive/README.md)** - Information about archived/unused files

## 📁 Project Structure

```
yvynation/
├── 📄 streamlit_app.py                    # Main application entry point
├── ⚙️  Core Modules (Active)
│   ├── config.py                          # Configuration & constants
│   ├── app_file.py                        # Core application logic
│   ├── ee_auth.py                         # Earth Engine authentication
│   ├── map_manager.py                     # Map creation & management
│   ├── ee_layers.py                       # Earth Engine layer management
│   ├── mapbiomas_analysis.py              # MapBiomas analysis
│   ├── hansen_analysis.py                 # Hansen data analysis
│   ├── territory_analysis.py              # Territory analysis
│   ├── plotting_utils.py                  # Visualization utilities
│   ├── main.py                            # Main analysis functions
│   └── requirements.txt                   # Python dependencies
│
├── 📦 components/                         # Modular UI Components
│   ├── __init__.py
│   ├── initialization.py                  # App initialization
│   ├── sidebar.py                         # Sidebar controls
│   ├── tutorial.py                        # Tutorial & help
│   └── main_content.py                    # Main page layout
│
├── 📚 docs/                               # Documentation (20+ files)
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   └── [More documentation files...]
│
├── 🗂️  utils/                             # Utilities (for expansion)
│   └── __init__.py
│
└── 📦 archive/                            # Unused/Legacy Files
    ├── legacy_code/                       # 16 deprecated Python files
    ├── data/                              # Reference data (CSVs, etc.)
    └── README.md                          # Archive guide

```

## 🛠️ Installation & Setup

### System Requirements
- Python 3.8 or higher
- pip package manager
- Earth Engine account with API access

### Detailed Setup Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd yvynation
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Earth Engine**
   ```bash
   earthengine authenticate
   ```
   This will open a browser window for Google authentication.

5. **Run Application**
   ```bash
   streamlit run streamlit_app.py
   ```

For detailed setup instructions, see [QUICKSTART.md](docs/QUICKSTART.md) or [SERVICE_ACCOUNT_SETUP.md](docs/SERVICE_ACCOUNT_SETUP.md).

## 💻 Usage

### Basic Workflow

1. **Access the Application**
   - Open `http://localhost:8501` in your web browser

2. **Add Map Layers**
   - Use sidebar controls to add MapBiomas or Hansen layers
   - Select year and data source
   - Click "Add Layer" to display on map

3. **Analyze Territory**
   - Select an indigenous territory from sidebar
   - Choose data source and year(s)
   - Click "Analyze" for statistics

4. **Draw Custom Area**
   - Use drawing tools in top-left of map
   - Draw polygon or rectangle
   - Analysis calculates automatically

5. **Compare Years**
   - Enable "Compare Years" in territory analysis
   - Select two different years
   - View side-by-side comparison

For detailed usage guide, see [QUICKSTART.md](docs/QUICKSTART.md).

## 🔧 Technologies

- **[Google Earth Engine](https://earthengine.google.com/)** - Geospatial analysis platform
- **[Streamlit](https://streamlit.io/)** - Web app framework
- **[Folium](https://folium.readthedocs.io/)** - Interactive maps
- **[geemap](https://geemap.org/)** - Earth Engine Python library
- **[Pandas](https://pandas.pydata.org/)** - Data analysis
- **[Matplotlib/Seaborn](https://matplotlib.org/)** - Visualization

## 📊 Data Sources

### MapBiomas Collection 9
- **Resolution**: 30 meters
- **Period**: 1985–2023 (annual)
- **Classes**: 62 land cover categories
- **License**: Creative Commons Attribution 4.0
- [Learn more](https://mapbiomas.org/)

### Hansen/GLAD Global Forest Change
- **Resolution**: 30 meters
- **Period**: 2000–2020
- **Coverage**: Global
- [Learn more](https://glad.umd.edu/)

### Indigenous Territories
- **Count**: 700+ Brazilian territories
- **Source**: MapBiomas Territories Project
- **Format**: Vector boundaries with attributes

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

For development guidelines, see [REFACTOR_GUIDE.md](docs/REFACTOR_GUIDE.md).

## 👤 Author

**Leandro Meneguelli Biondo**
- PhD Candidate in Sustainability
- Institute for Sustainable Hut Studies (IGS), University of British Columbia Okanagan
- Email: leandro.biondo@alumni.ubc.ca

**Supervisor**: Dr. Jon Corbett

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🔗 Related Links

- **Earth Engine Repository**: [users/leandromet/yvynation](https://code.earthengine.google.com/?accept_repo=users/leandromet/yvynation)
- **GitHub Repository**: [This repository](<repository-url>)
- **Documentation**: [Complete Documentation](docs/)

## 🐛 Issues & Support

Found a bug or have a question? Please:

1. Check [Existing Issues](../../issues)
2. Review [Documentation](docs/)
3. Create a [New Issue](../../issues/new) with detailed description

## 📝 Citation

If you use this platform in your research, please cite:

```bibtex
@software{biondo2026yvynation,
  author = {Biondo, Leandro Meneguelli},
  title = {Yvynation - Indigenous Land Monitoring Platform},
  year = {2026},
  url = {<repository-url>}
}
```

## 🙏 Acknowledgments

- **MapBiomas Project** for land cover classification data
- **Google Earth Engine** team for the geospatial analysis platform and API
- **Google Cloud Research Credits Program** for providing computing resources to support this research
- **Indigenous Communities of Brazil** for collaboration and data sharing
- **University of British Columbia Okanagan (UBCO)** for academic support and supervision

---

**Last Updated**: January 2026  
**Version**: 1.0.0

For the latest updates and detailed documentation, visit the [docs/](docs/) folder.
