"""
Main content module for Yvynation
Handles main page layout and display components
"""

import streamlit as st


def render_main_content():
    """Render the main content area with title and tutorials."""
    st.title("🌎 Yvynation - Land Cover Analysis 🏞️")
    
    # Import and render tutorial from components
    from .tutorial import render_tutorial
    render_tutorial()


def render_layer_metrics():
    """Render layer configuration metrics."""
    if st.session_state.data_loaded:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Base Layer", "OpenStreetMap", help="Switch in map controls (top-right)")
            
        with col2:
            mapbiomas_count = len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            st.metric("MapBiomas Layers", mapbiomas_count, help="Brazil land cover (1985-2023)")
            
        with col3:
            hansen_count = len([y for y, v in st.session_state.hansen_layers.items() if v])
            st.metric("Hansen Layers", hansen_count, help="Global forest change (2000-2020)")
        
        # Show active layers
        st.divider()
        st.subheader("📋 Active Layers")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.mapbiomas_layers:
                years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
                if years:
                    st.write("**MapBiomas Years:**")
                    st.write(", ".join(map(str, years)))
                else:
                    st.caption("No MapBiomas layers selected")
            else:
                st.caption("No MapBiomas layers added")
        
        with col2:
            if st.session_state.hansen_layers:
                years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
                if years:
                    st.write("**Hansen Years:**")
                    st.write(", ".join(map(str, years)))
                else:
                    st.caption("No Hansen layers selected")
            else:
                st.caption("No Hansen layers added")


def render_footer():
    """Render page footer."""
    st.divider()
    st.markdown(
        """
        <div style='text-align: center'>
        <small>
        🌎 Yvynation | MapBiomas + Indigenous Territories Analysis
        <br/>
        Built with Earth Engine, geemap, and Streamlit
        </small>
        </div>
        """,
        unsafe_allow_html=True
    )
