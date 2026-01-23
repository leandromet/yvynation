# Yvynation Project Structure

This document describes the organized project structure following professional code organization practices.

## Directory Layout

```
yvynation/
├── components/                 # Modular Streamlit UI components
│   ├── __init__.py            # Package initialization
│   ├── initialization.py       # Earth Engine and session state setup
│   ├── sidebar.py             # Sidebar UI and controls
│   ├── tutorial.py            # Tutorial and help content
│   └── main_content.py        # Main page layout components
│
├── utils/                      # Utility modules and helpers
│   └── __init__.py
│
├── docs/                       # Documentation (markdown files)
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   └── [other documentation]
│
├── streamlit_app.py           # Main application entry point
├── config.py                  # Configuration and constants
├── requirements.txt           # Python dependencies
└── [other utility modules]    # Analysis, visualization, data processing

```

## Module Descriptions

### `components/` - Modular UI Components

The components folder contains all Streamlit UI elements organized by functionality:

- **`initialization.py`**: 
  - Earth Engine setup and authentication
  - Session state initialization
  - Core data loading and caching
  - Functions: `initialize_earth_engine_and_data()`

- **`sidebar.py`**: 
  - Complete sidebar rendering
  - Map controls section
  - Layer management (MapBiomas, Hansen)
  - Territory analysis controls
  - View options
  - About section
  - Functions: `render_sidebar()` and sub-functions

- **`tutorial.py`**: 
  - Interactive tutorial content
  - Help sections and guides
  - Functions: `render_tutorial()`

- **`main_content.py`**: 
  - Main page title and layout
  - Layer metrics display
  - Footer rendering
  - Functions: `render_main_content()`, `render_layer_metrics()`, `render_footer()`

### `utils/` - Utility Functions

Placeholder for future utility modules that may include:
- Data processing helpers
- Visualization utilities
- Analysis helpers
- File I/O functions

### `docs/` - Documentation

All markdown documentation files are organized here:
- `QUICKSTART.md` - Getting started guide
- `ARCHITECTURE.md` - System architecture
- `ARCHITECTURE_DIAGRAM.md` - Visual architecture
- Development guides and references
- Setup and deployment instructions

## Existing Modules (Core Functionality)

These existing modules provide core functionality and are imported by components:

- **`config.py`**: Configuration constants, labels, and color maps
- **`ee_auth.py`**: Earth Engine authentication
- **`app_file.py`**: Main application logic (YvynationApp class)
- **`map_manager.py`**: Map creation and management
- **`ee_layers.py`**: Earth Engine layer management
- **`territory_analysis.py`**: Territory-specific analysis
- **`plotting_utils.py`**: Visualization and plotting
- **`hansen_consolidated_utils.py`**: Hansen data processing

## How Components Work

### Main Entry Point (`streamlit_app.py`)

```python
from components import (
    initialize_earth_engine_and_data,
    render_sidebar,
    render_tutorial,
    render_main_content
)

# Initialize app
initialize_earth_engine_and_data()

# Render UI
render_main_content()
render_sidebar()
```

### Component Import Pattern

Each component is self-contained and can be imported independently:

```python
from components.sidebar import render_sidebar
from components.tutorial import render_tutorial
from components.initialization import initialize_earth_engine_and_data
```

## Code Organization Benefits

1. **Modularity**: Each component handles one responsibility
2. **Reusability**: Components can be imported into other projects
3. **Maintainability**: Easy to find and update specific functionality
4. **Testability**: Components can be tested independently
5. **Scalability**: New features can be added as new modules
6. **Documentation**: Organized docs folder for easy reference
7. **Clean Main App**: `streamlit_app.py` remains clean and readable

## Adding New Components

To add a new component:

1. Create a new file in `components/` with a descriptive name
2. Define a `render_*()` function as the main entry point
3. Keep helper functions private (prefix with `_`)
4. Add proper docstrings
5. Update `components/__init__.py` to export the component
6. Import and use in `streamlit_app.py`

Example:

```python
# components/new_feature.py
def render_new_feature():
    """Render the new feature component."""
    # Implementation here
    pass
```

## Documentation Access

All documentation is in the `docs/` folder. Key files:

- **Getting Started**: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Setup**: [docs/SERVICE_ACCOUNT_SETUP.md](docs/SERVICE_ACCOUNT_SETUP.md)
- **Development**: [docs/REFACTOR_GUIDE.md](docs/REFACTOR_GUIDE.md)

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the Streamlit app
streamlit run streamlit_app.py
```

## Future Improvements

- Add unit tests in a `tests/` folder
- Create `models/` folder for data models
- Add `services/` folder for API/external service interactions
- Implement logging configuration in `utils/`
