# Yvynation Translation Strategy

## Overview
The Yvynation application is being progressively translated into English and Portuguese (Brazil). This document tracks the translation roadmap and provides guidelines for consistent implementation.

## Current Status

### ✅ COMPLETED
- **translations.py** - Complete translation dictionary with 150+ keys
- **sidebar_components.py - render_language_selection()** - Language selector UI
- **sidebar_components.py - render_layer_selection()** - All map layer controls translated

### 🔄 IN PROGRESS
1. Remaining sidebar components (territory analysis, view options, map controls)
2. Main streamlit_app.py content
3. Modal dialogs and popup messages

### ⏳ PENDING
- map_components.py content
- Detailed error messages and warnings
- Inline help text and tooltips

## Implementation Pattern

All translated UI elements should follow this pattern:

```python
# 1. Import the translation helper
from translations import t

# 2. Use for labels and buttons
st.write(t("key_name"))
st.button(t("button_label"))

# 3. Use for formatted strings
st.success(f"✓ {t('success_message')} - {value}")
st.error(f"❌ {t('error_message')}: {details}")

# 4. Use for markdown
st.markdown(f"**{t('section_title')}**")

# 5. Use for help text
st.info(t("info_message"), icon="ℹ️")
```

## Translation Key Naming Convention

Use snake_case with semantic grouping:

```
layer_<name>           # Map layers (layer_mapbiomas, layer_aafc)
analysis_<name>        # Analysis sections (analysis_title, analysis_results)
button_<name>          # Button labels (button_add, button_export)
label_<name>           # Form labels (label_year, label_territory)
msg_<type>_<name>      # Messages (msg_success_added, msg_error_connection)
help_<feature>         # Help text (help_buffer_zone, help_consolidation)
title_<section>        # Section titles (title_analysis, title_about)
```

## Priority Order for Remaining Work

### Phase 2: Core Sidebar Functions
**Files:** `sidebar_components.py` (lines 179-430)

| Function | Status | Keys Needed |
|----------|--------|------------|
| render_territory_analysis() | ⏳ | 8-10 keys |
| render_view_options() | ⏳ | 6-8 keys |
| render_map_controls() | ⏳ | 5-7 keys |
| render_about_section() | ⏳ | 10-15 keys |
| render_complete_sidebar() | ✅ | - |

### Phase 3: Main Application Content
**Files:** `streamlit_app.py` (lines 1-800)

| Section | Status | Keys Needed |
|---------|--------|------------|
| Page config & title | ⏳ | 3-5 keys |
| Getting Started tutorial | ⏳ | 6-8 keys |
| Main sidebar init | ✅ | - |
| Analysis execution | ⏳ | 10-15 keys |
| Data export UI | ⏳ | 4-6 keys |
| Success/error messages | ⏳ | 12-20 keys |

### Phase 4: Map Components
**Files:** `map_components.py` (lines 1-400)

| Component | Status | Keys Needed |
|-----------|--------|------------|
| Map instructions | ⏳ | 5-8 keys |
| Layer legends | ⏳ | 15-25 keys |
| Pop-up tooltips | ⏳ | 10-15 keys |
| Basemap labels | ⏳ | 6-10 keys |

### Phase 5: Analysis Functions
**Files:** `streamlit_app.py` (lines 800-2200)

| Function | Status | Keys Needed |
|----------|--------|------------|
| render_analysis_tabs() | ⏳ | 20-30 keys |
| Tab titles and descriptions | ⏳ | 12-18 keys |
| Result summaries | ⏳ | 15-25 keys |
| Export options | ⏳ | 8-12 keys |

## Quick Reference: Common Translation Keys

### Currently Available
```python
# Languages
t("english")  # "English" / "Inglês"
t("portuguese")  # "Portuguese (Brazil)" / "Português (Brasil)"

# Common buttons
t("add_layer")  # "Add to Map" / "Adicionar ao Mapa"
t("yes")  # "Yes" / "Sim"
t("no")  # "No" / "Não"

# Common messages
t("select_territory")  # "Select a territory" / "Selecione um território"
t("calculating")  # "Calculating..." / "Calculando..."

# Map layers
t("mapbiomas_layer")  # "MapBiomas (Brazil)" / "MapBiomas (Brasil)"
t("hansen_layer")  # "Hansen Global Forest Watch" / "Hansen Vigilância Florestal Global"
t("aafc_layer")  # "AAFC Annual Crop Inventory" / "Inventário Anual de Cultivos AAFC"
```

## Adding New Translation Keys

When adding a new UI element, follow these steps:

1. **Identify the text** that needs translation
2. **Create a key** following the naming convention above
3. **Add to translations.py** with entries for both 'en' and 'pt-br'
4. **Use t("key_name")** in your code
5. **Test both languages** in the sidebar language selector

### Example: Adding a new button
```python
# In translations.py, add:
"button_export_csv": "Export as CSV" / "Exportar como CSV"

# In streamlit_app.py, use:
if st.button(t("button_export_csv")):
    # ... export logic
```

## Testing Checklist

After translating a component, verify:

- [ ] English text displays correctly
- [ ] Portuguese text displays correctly  
- [ ] Language switching updates all translated elements
- [ ] No hardcoded strings remain in translated section
- [ ] Session state persists language selection
- [ ] Page refresh maintains language selection
- [ ] All buttons, labels, and messages are translated

## Notes

- The `t()` helper function automatically uses `st.session_state.language`
- Default language is 'en' (English)
- Language preference should persist across app reruns
- Formatted strings with variables should use f-strings: `f"{t('key')} {value}"`

## Related Files

- **translations.py** - Main translation dictionary and helpers
- **sidebar_components.py** - Sidebar UI components (partially translated)
- **streamlit_app.py** - Main application logic
- **map_components.py** - Map-specific components
- **config.py** - Configuration (minimal translation needed)
- **ee_layers.py** - Earth Engine layers (minimal translation needed)

