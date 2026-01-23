"""
Initialization module for Yvynation
Handles Earth Engine setup and session state initialization
"""

import streamlit as st
from ee_auth import initialize_earth_engine
from app_file import YvynationApp
from territory_analysis import initialize_territory_session_state


def initialize_earth_engine_and_data():
    """
    Initialize Earth Engine and load core data with caching.
    
    This function:
    1. Sets up Earth Engine authentication
    2. Loads MapBiomas and territories data
    3. Initializes session state variables
    """
    print("\n🚀 Yvynation App Starting...")

    # Initialize Earth Engine
    try:
        st.session_state.ee_module = initialize_earth_engine()
        print("✓ Earth Engine initialized")
    except Exception as e:
        st.error(f"❌ Failed to initialize Earth Engine: {e}")
        st.stop()

    # Auto-load core data
    @st.cache_resource
    def load_core_data():
        """Load MapBiomas and territories data once and cache it."""
        print("Loading core datasets...")
        try:
            app = YvynationApp()
            success = app.load_core_data()
            if success:
                print("✓ Core data loaded and cached")
                return app
            else:
                print("❌ Failed to load core data")
                return None
        except Exception as e:
            print(f"❌ Error loading core data: {e}")
            return None

    # Load data automatically
    if "app" not in st.session_state:
        st.session_state.app = load_core_data()
        if st.session_state.app:
            st.session_state.data_loaded = True

    # Initialize session state
    _initialize_session_state()


def _initialize_session_state():
    """Initialize all session state variables for the application."""
    
    # Core data state
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    
    # Layer state
    if "current_mapbiomas_year" not in st.session_state:
        st.session_state.current_mapbiomas_year = 2023
    if "current_hansen_year" not in st.session_state:
        st.session_state.current_hansen_year = "2020"
    if "mapbiomas_layers" not in st.session_state:
        st.session_state.mapbiomas_layers = {}  # {year: True/False}
    if "hansen_layers" not in st.session_state:
        st.session_state.hansen_layers = {}  # {year: True/False}
    
    # Drawing and analysis state
    if "last_drawn_feature" not in st.session_state:
        st.session_state.last_drawn_feature = None
    if "all_drawn_features" not in st.session_state:
        st.session_state.all_drawn_features = []  # List of all captured polygons
    if "selected_feature_index" not in st.session_state:
        st.session_state.selected_feature_index = None
    if "analysis_results" not in st.session_state:
        st.session_state.analysis_results = None
    
    # Comparison state
    if "mapbiomas_comparison_result" not in st.session_state:
        st.session_state.mapbiomas_comparison_result = None
    if "hansen_comparison_result" not in st.session_state:
        st.session_state.hansen_comparison_result = None
    
    # View options
    if "use_consolidated_classes" not in st.session_state:
        st.session_state.use_consolidated_classes = True
    
    # Initialize territory analysis session state
    initialize_territory_session_state()
