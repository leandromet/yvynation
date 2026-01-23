"""
Tutorial module for Yvynation
Handles tutorial and help content rendering
"""

import streamlit as st


def render_tutorial():
    """Render the tutorial section as a collapsible expander."""
    with st.expander("📚 How to Use This Platform", expanded=False):
        st.markdown("### 🎯 Getting Started\n\nThis platform allows you to analyze land cover changes in three main ways:")
        
        with st.expander("1️⃣ **Analyze a Custom Polygon**", expanded=False):
            st.markdown("""
            - Use the **Draw Tools** in the top-left corner of the map
            - Click the **Rectangle** or **Polygon** tool to draw your area of interest
            - Select your desired **year** and **data source** (MapBiomas or Hansen)
            - The analysis will automatically calculate:
              - Land cover distribution
              - Changes over time
              - Area statistics by land cover class
            - 💡 *Tip: You can draw multiple areas and compare them*
            """)
        
        with st.expander("2️⃣ **Analyze an Indigenous Territory**", expanded=False):
            st.markdown("""
            - Navigate to the **🏛️ Indigenous Territories Analysis** section in the sidebar
            - **Select a Territory** from the dropdown
            - **Choose a Data Source** (MapBiomas or Hansen/GLAD)
            - **Select Year(s)** for analysis
            - Click **📊 Analyze** to get detailed statistics
            - View:
              - Historical land cover changes (1985-2023)
              - Area changes by class
              - Deforestation trends
              - Transition diagrams showing land cover changes
            - 💡 *Tip: Compare historical trends across different territories to understand regional patterns*
            """)
        
        with st.expander("3️⃣ **Compare Two Years**", expanded=False):
            st.markdown("""
            - Use the territory or polygon analysis tools
            - Enable **Compare Years** option to select a second year
            - View side-by-side comparisons showing:
              - Land cover changes between years
              - Area distribution before and after
              - Change percentage and absolute values
              - Visual maps with color-coded changes
            - 💡 *Tip: Use 1985 vs 2023 to see long-term trends, or consecutive years for detailed change detection*
            """)
        
        with st.expander("🗺️ **Map Controls**", expanded=False):
            st.markdown("""
            - **Zoom**: Use scroll wheel or +/- buttons
            - **Pan**: Click and drag the map
            - **Toggle Layers**: Use the layer control icon (⌗) in the top-right
            - **Draw Tools**: Use the drawing toolbar in the top-left to create custom analysis areas
            - **Switch Base Map**: Click the layer control to change basemaps (OpenStreetMap, Satellite, etc.)
            - **Fullscreen**: Use the fullscreen button in the map controls
            """)
        
        with st.expander("📈 **Understanding the Results**", expanded=False):
            st.markdown("""
            - **MapBiomas**: 62 land cover classes (1985-2023, 30m resolution)
            - **Hansen/GLAD**: Global forest change detection (2000-2020, 30m resolution)
            - **Colors**: Represent different land cover types (see legend on maps)
            - **Areas**: Calculated in hectares and percentages
            - **Consolidated View**: Groups Hansen 256 classes into 12 categories for clearer insights
            """)
        
        with st.expander("⚙️ **Data Sources & Updates**", expanded=False):
            st.markdown("""
            - **MapBiomas Collection 9**: Updated annually, latest year is 2023
            - **Hansen/GLAD**: Updated periodically, latest complete data is 2020
            - **Indigenous Territories**: Updated from MapBiomas Territories Project
            - All data sources use 30-meter resolution for consistent analysis
            """)
