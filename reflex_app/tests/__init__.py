"""
Tests for Yvynation state management and utilities.
"""

import pytest
from yvynation.state import AppState
from yvynation.utils.translations import t, TRANSLATIONS
from yvynation.utils.ee_service import EarthEngineService


class TestTranslations:
    """Test translation functionality."""
    
    def test_english_translation(self):
        """Test English translation."""
        assert t("page_title", "en") == "Yvynation - Indigenous Land Monitoring"
    
    def test_portuguese_translation(self):
        """Test Portuguese translation."""
        result = t("page_title", "pt")
        assert "Monitoramento" in result
    
    def test_translation_with_parameters(self):
        """Test translation with parameter substitution."""
        result = t("ee_init_error", "en", error="test error")
        assert "test error" in result
    
    def test_missing_key_returns_key(self):
        """Test that missing keys return the key itself."""
        assert t("nonexistent_key", "en") == "nonexistent_key"
    
    def test_language_options(self):
        """Test language options."""
        from yvynation.utils.translations import get_language_options
        options = get_language_options()
        assert "en" in options
        assert "pt" in options
        assert "es" in options


class TestAppState:
    """Test application state management."""
    
    def test_initial_state(self):
        """Test initial state values."""
        state = AppState()
        assert state.data_loaded == False
        assert state.language == "en"
        assert state.mapbiomas_current_year == 2023
    
    def test_set_language(self):
        """Test language change."""
        state = AppState()
        state.set_language("pt")
        assert state.language == "pt"
    
    def test_toggle_sidebar(self):
        """Test sidebar toggle."""
        state = AppState()
        initial = state.sidebar_open
        state.toggle_sidebar()
        assert state.sidebar_open == (not initial)
    
    def test_set_active_tab(self):
        """Test tab switching."""
        state = AppState()
        state.set_active_tab("analysis")
        assert state.active_tab == "analysis"
    
    def test_set_map_center(self):
        """Test map center update."""
        state = AppState()
        state.set_map_center(-5.0, -60.0, zoom=10)
        assert state.map_center == (-5.0, -60.0)
        assert state.map_zoom == 10
    
    def test_territory_selection(self):
        """Test territory selection."""
        state = AppState()
        state.set_selected_territory("Yanomami")
        assert state.selected_territory == "Yanomami"
    
    def test_pending_territory(self):
        """Test pending territory confirmation flow."""
        state = AppState()
        state.set_pending_territory("Kayapo")
        assert state.pending_territory == "Kayapo"
        
        state.confirm_territory()
        assert state.selected_territory == "Kayapo"
        assert state.pending_territory is None
    
    def test_toggle_mapbiomas_year(self):
        """Test MapBiomas year toggle."""
        state = AppState()
        state.toggle_mapbiomas_year(2020)
        assert state.mapbiomas_years_enabled.get(2020, False) == True
        
        state.toggle_mapbiomas_year(2020)
        assert state.mapbiomas_years_enabled.get(2020, False) == False
    
    def test_error_message_handling(self):
        """Test error message display."""
        state = AppState()
        state.set_error("Test error message")
        assert state.error_message == "Test error message"
        
        state.clear_error()
        assert state.error_message == ""
    
    def test_loading_state(self):
        """Test loading state."""
        state = AppState()
        state.set_loading("Analyzing...")
        assert state.loading_message == "Analyzing..."
        
        state.clear_loading()
        assert state.loading_message == ""


class TestEarthEngineService:
    """Test Earth Engine service layer."""
    
    @pytest.mark.skip(reason="Requires Earth Engine credentials")
    def test_initialize(self):
        """Test Earth Engine initialization."""
        # This would need valid service account
        result = EarthEngineService.initialize(use_service_account=True)
        # Would need mocking in real tests
    
    def test_service_initialization_check(self):
        """Test that service can be checked for initialization."""
        # Just verify the class exists and has methods
        assert hasattr(EarthEngineService, 'initialize')
        assert hasattr(EarthEngineService, 'load_mapbiomas')
        assert hasattr(EarthEngineService, 'load_territories')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
