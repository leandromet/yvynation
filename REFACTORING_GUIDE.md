"""
REFACTORING GUIDE - How to Update streamlit_app.py

This guide explains how to replace large sections of code in streamlit_app.py
with imports from the new modular components.

CREATED MODULES:
================

1. sidebar_components.py
   - render_sidebar_header()
   - render_map_controls()
   - render_layer_selection()
   - render_territory_analysis()
   - render_view_options()
   - render_about_section()
   - render_complete_sidebar()  ← Use this to replace entire sidebar section

2. map_components.py
   - build_and_display_map()    ← Use to replace map building code
   - process_drawn_features()   ← Use to replace drawing processing
   - render_polygon_selector()  ← Use to replace polygon selector UI
   - render_layer_reference_guide()  ← Use to replace legend section


HOW TO UPDATE streamlit_app.py:
===============================

STEP 1: Add imports at the top of streamlit_app.py
--------
Add these lines after the other imports:

    from sidebar_components import render_complete_sidebar
    from map_components import (
        build_and_display_map,
        process_drawn_features,
        render_polygon_selector,
        render_layer_reference_guide
    )


STEP 2: Replace the entire sidebar section (~lines 108-430)
--------
Find the section starting with:
    st.sidebar.title("🌎🌍🌏🏞️ Yvynation 🛰️🗺️🌳🌲")

Replace the ENTIRE sidebar code (up to st.sidebar.divider() at line ~430) with:
    render_complete_sidebar()


STEP 3: Replace the map display code (~lines 437-700)
--------
Find the section "# Build map fresh each time with current layers"

Replace all that code until "Display the map" section with:
    map_data = build_and_display_map()
    process_drawn_features(map_data)


STEP 4: Replace polygon selector (~lines 702-732)
--------
Find the "# Polygon selector if multiple drawings exist" section

Replace it with:
    render_polygon_selector()


STEP 5: Replace layer reference guide (~lines 734-819)
--------
Find the "# Display layer reference guide" section

Replace it with:
    render_layer_reference_guide()


RESULT:
=======
After refactoring:
- streamlit_app.py will go from ~1860 lines to ~1100 lines
- Sidebar code moved to sidebar_components.py (~300 lines)
- Map code moved to map_components.py (~350 lines)
- Main app stays clean and focused on analysis logic

BENEFITS:
=========
✅ Easier to maintain and modify sidebar independently
✅ Easier to modify map components without touching main app
✅ Better code organization and reusability
✅ Can test components separately
✅ Easier to add new features to sidebar/map in future
"""
