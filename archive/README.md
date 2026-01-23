# Archive Folder

This folder contains unused and legacy files that are not part of the current Yvynation application.

## Structure

### `legacy_code/`
Contains Python files that are no longer actively used in the application. These include:
- **Old app versions**: `streamlit_app_old.py`, `streamlit_app_old_backup.py`, `streamlit_drawing_app.py`
- **Deprecated modules**: `analysis.py`, `plots.py`, `ui_components.py`, `visualization.py`
- **Legacy Hansen utilities**: `hansen_consolidated_mapping.py`, `hansen_glcluc_colors.py`, `hansen_labels.py`, `hansen_reference_mapping.py`, `hansen_consolidation_visual_reference.py`, `HANSEN_CONSOLIDATION_EXAMPLES.py`
- **Unused utilities**: `load_data.py`, `spot_module.py`, `test_hansen_consolidation.py`

### `data/`
Contains reference data files:
- **Legend/Reference CSVs**: `legend_0.csv`, `legend_consolidated.csv`, `legend_glcluc.csv`, `legend_glcluc_year.csv`, `reference-labels (2).csv`
- **Documentation**: `BEFORE_AFTER.txt`

## Usage

These files are kept for reference and historical purposes but are not imported or used by the current application. 

To recover a file from the archive:
```bash
# Move file from archive back to root
mv archive/legacy_code/filename.py .
```

## Notes

- The active codebase uses only the modules in the root directory and `components/` folder
- Current app depends on: `config.py`, `ee_auth.py`, `app_file.py`, `map_manager.py`, `ee_layers.py`, `mapbiomas_analysis.py`, `hansen_analysis.py`, `hansen_consolidated_utils.py`, `plotting_utils.py`, `territory_analysis.py`, and `main.py`
- All documentation has been moved to the `docs/` folder
