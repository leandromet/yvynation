"""
Main content module for Yvynation
Handles main page layout and display components
"""

import streamlit as st
from translations import t


def render_main_content():
    """Render the main content area with title and tutorials."""
    st.title(t("main_page_title"))
    
    # Import and render tutorial from components
    from .tutorial import render_tutorial
    render_tutorial()


def render_layer_metrics():
    """Render layer configuration metrics."""
    if st.session_state.data_loaded:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(t("base_layer"), "OpenStreetMap", help=t("base_layer_hint"))
            
        with col2:
            mapbiomas_count = len([y for y, v in st.session_state.mapbiomas_layers.items() if v])
            st.metric(t("mapbiomas_layers_label"), mapbiomas_count, help=t("mapbiomas_layers_hint"))
            
        with col3:
            hansen_count = len([y for y, v in st.session_state.hansen_layers.items() if v])
            st.metric(t("hansen_layers_label"), hansen_count, help=t("hansen_layers_hint"))
        
        # Show active layers
        st.divider()
        st.subheader(t("active_layers"))
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.mapbiomas_layers:
                years = sorted([y for y, v in st.session_state.mapbiomas_layers.items() if v])
                if years:
                    st.write(f"**{t('mapbiomas_years')}**")
                    st.write(", ".join(map(str, years)))
                else:
                    st.caption(t("no_mapbiomas_selected"))
            else:
                st.caption(t("no_mapbiomas_added"))
        
        with col2:
            if st.session_state.hansen_layers:
                years = sorted([y for y, v in st.session_state.hansen_layers.items() if v])
                if years:
                    st.write(f"**{t('hansen_years')}**")
                    st.write(", ".join(map(str, years)))
                else:
                    st.caption(t("no_hansen_selected"))
            else:
                st.caption(t("no_hansen_added"))


def render_footer():
    """Render page footer."""
    st.divider()
    st.markdown(
        f"""
        <div style='text-align: center'>
        <small>
        {t("footer_description")}
        <br/>
        {t("footer_credits")}
        </small>
        </div>
        """,
        unsafe_allow_html=True
    )
