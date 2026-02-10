# Yvynation Translation Keys Reference

## All Available Translation Keys (150+)

### Languages & Selection
- `english`
- `portuguese`
- `select_language`
- `language_changed`

### Navigation & Sidebar
- `getting_started`
- `getting_started_intro`
- `step1_select_territory`
- `step1_desc`
- `step2_add_layers`
- `step2_desc`
- `step3_analyze`
- `step3_desc`
- `step4_export`
- `step4_desc`

### Map Layers
- `add_map_layers`
- `mapbiomas_layer`
- `mapbiomas_year`
- `mapbiomas_select_year`
- `mapbiomas_add_info`
- `hansen_layer`
- `hansen_loss_year`
- `hansen_loss_select`
- `hansen_gfc_layer`
- `hansen_gfc_canopy`
- `hansen_gfc_select`
- `aafc_layer`
- `aafc_year`
- `aafc_select_year`
- `aafc_add_info`
- `add_layer`

### Map Tools
- `map_tools_title`
- `zoom_instructions`
- `pan_instructions`
- `draw_instructions`
- `edit_instructions`
- `measure_instructions`
- `recenter_map`
- `clear_drawing`
- `map_toolbox`

### Territory Analysis
- `territory_analysis`
- `territory_analysis_subtitle`
- `get_territories`
- `selected_territory`
- `territory_bounds`
- `select_territory`

### View Options
- `view_options`
- `layer_opacity`
- `consolidate_toggle`
- `consolidate_hint`
- `buffer_zone`
- `buffer_km`

### Export Options
- `export_data`
- `export_as_png`
- `export_as_csv`
- `export_as_pdf`
- `download`

### Analysis & Results
- `analysis_title`
- `running_analysis`
- `results`
- `data_summary`
- `create_plots`
- `area_hectares`
- `pixel_count`
- `class_name`
- `year_label`

### Messages
- `year`
- `loading_data`
- `calculating`
- `success_added`
- `analysis_complete`
- `file_exported`

### Additional UI
- `map_control`
- `layer_control_hint`
- `basemaps`
- `basemap_hint`
- `overlay_tip`
- `select_year`
- `select_data_source`
- `mapbiomas_brazil_only`
- `aafc_canada_only`
- `global_forest_subtitle`
- `year_2000_text`
- `show_years`

### About & Help
- `about_section`
- `technology_stack`
- `data_sources`
- `contact_info`
- `license`
- `feedback`

---

## Missing Translation Keys (Still to Add)

These are commonly needed strings that should be added to translations.py:

### Error Messages
- `error_invalid_input`
- `error_no_data`
- `error_gee_connection`
- `error_geometry_invalid`
- `error_area_too_large`

### Confirmation Dialogs
- `confirm_action`
- `are_you_sure`
- `delete_confirmation`

### Data Format Labels
- `class_id`
- `class_count`
- `total_area`
- `percentage`
- `confidence`

### Button Labels
- `button_apply`
- `button_cancel`
- `button_clear`
- `button_refresh`
- `button_reset`
- `button_export`
- `button_download`

### Titles & Headers  
- `title_analysis`
- `title_about`
- `title_settings`
- `title_help`

### Help Text
- `help_buffer_zone`
- `help_consolidation`
- `help_layer_opacity`

### Status Messages
- `status_ready`
- `status_loading`
- `status_processing`
- `status_error`
- `status_complete`

### Data Source Names
- `source_mapbiomas`
- `source_hansen`
- `source_aafc`
- `source_gfw`

---

## How to Use This Reference

1. **When translating a new section**, check if the key already exists here
2. **If it exists**, use `t("key_name")` directly
3. **If it doesn't exist**, add it to translations.py following the naming convention
4. **Update this file** after adding new keys (mark as ✅)

## Progress Tracker

- ✅ Sidebar layer selection (24 keys)
- ✅ Language selection (4 keys)  
- ✅ Getting Started steps (8 keys)
- ✅ Map tools (9 keys)
- ✅ Territory analysis (6 keys)
- ✅ View options (6 keys)
- ✅ Export section (4 keys)
- ⏳ Main app content
- ⏳ Analysis tabs
- ⏳ Map components
- ⏳ Error handling
- ⏳ Modal dialogs

---

## Commands to Check Available Keys

```python
# View all available keys
import sys
sys.path.append('/home/leandromb/google_eengine/yvynation')
from translations import TRANSLATIONS

# List all English keys
for key in TRANSLATIONS['en'].keys():
    print(key)

# Check if a key exists
if 'my_key' in TRANSLATIONS['en']:
    print("Key exists!")
```
