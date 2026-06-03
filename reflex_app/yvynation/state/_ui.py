"""
UI event handlers: sidebar, tabs, language, tutorial, error/loading helpers.
"""
import logging

import reflex as rx

logger = logging.getLogger(__name__)


class UIMixin(rx.State, mixin=True):
    """Event handlers for UI state (sidebar, tabs, tutorial, language, errors)."""

    # ---- Language -------------------------------------------------------

    def set_language(self, lang: str):
        """Change application language."""
        self.language = lang

    # ---- Country --------------------------------------------------------

    def set_country(self, country: str):
        """Change selected country/region."""
        self.selected_country = country

    # ---- Active tab -----------------------------------------------------

    def set_active_tab(self, tab: str):
        """Switch active content tab (map / analysis / tutorial / about)."""
        self.active_tab = tab

    def set_active_analysis_tab(self, tab: str):
        """Switch the active sub-tab inside the analysis panel."""
        self.active_analysis_tab = tab

    # ---- Sidebar --------------------------------------------------------

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar_open = not self.sidebar_open

    def toggle_sidebar_section(self, section: str):
        """Toggle sidebar section expansion."""
        if section == "mapbiomas":
            self.sidebar_mapbiomas_expanded = not self.sidebar_mapbiomas_expanded
        elif section == "hansen":
            self.sidebar_hansen_expanded = not self.sidebar_hansen_expanded
        elif section == "territory":
            self.sidebar_territory_expanded = not self.sidebar_territory_expanded
        elif section == "geometry":
            self.sidebar_geometry_expanded = not self.sidebar_geometry_expanded
        elif section == "upload_file":
            self.upload_file_expanded = not self.upload_file_expanded

    def start_resize(self):
        """Begin sidebar resize drag."""
        self.is_resizing_sidebar = True

    def end_resize(self):
        """End sidebar resize drag."""
        self.is_resizing_sidebar = False

    def update_sidebar_width(self, width: int):
        """Update sidebar width (constrained 200–500 px)."""
        self.sidebar_width = max(200, min(500, width))

    # ---- Full-screen results panel --------------------------------------
    # (The map uses Leaflet's own full-screen control; only the results area
    #  needs an app-level toggle.)

    def toggle_fullscreen_results(self):
        """Expand the results area to fill the content area (toggle to split)."""
        self.fullscreen_panel = "" if self.fullscreen_panel == "results" else "results"

    # ---- Tutorial -------------------------------------------------------

    def toggle_tutorial(self):
        """Toggle tutorial panel visibility."""
        self.show_tutorial = not self.show_tutorial

    def toggle_tutorial_step(self, step_index: int):
        """Expand or collapse a tutorial step."""
        if step_index in self.tutorial_expanded_steps:
            self.tutorial_expanded_steps = [
                s for s in self.tutorial_expanded_steps if s != step_index
            ]
        else:
            self.tutorial_expanded_steps = self.tutorial_expanded_steps + [step_index]

    # ---- Layer reference ------------------------------------------------

    def toggle_layer_reference(self):
        """Toggle layer reference guide visibility."""
        self.show_layer_reference = not self.show_layer_reference

    # ---- Error / Loading helpers ----------------------------------------

    def set_error(self, message: str):
        """Set error message for display."""
        self.error_message = message

    def clear_error(self):
        """Clear the displayed error message."""
        self.error_message = ""

    def set_loading(self, message: str = ""):
        """Set loading state with an optional message."""
        self.loading_message = message

    def clear_loading(self):
        """Clear loading state and type."""
        self.loading_message = ""
        self.loading_type = ""

    # ---- Navigation (analysis mode) ------------------------------------------

    def go_to_geometry_analysis(self):
        """Navigate to geometry analysis page, then kick off background EE load.

        Using a generator (yield) ensures the state mutation (analysis_mode) is
        sent to the frontend *before* the background task is dispatched, so the
        UI switches pages immediately and remains fully interactive while EE data
        loads in the background.
        """
        self.analysis_mode = "geometry"
        self.show_indigenous_lands = False
        bg_task = self.initialize_app()
        if bg_task is not None:
            yield bg_task

    def go_to_territory_analysis(self):
        """Navigate to territory analysis page, then kick off background EE load."""
        self.analysis_mode = "territory"
        self.show_indigenous_lands = True
        bg_task = self.initialize_app()
        if bg_task is not None:
            yield bg_task

    def go_to_batch_processing(self):
        """Navigate to batch processing page, loading territories in background."""
        self.analysis_mode = "batch"
        self.show_indigenous_lands = False
        bg_task = self.initialize_app()
        if bg_task is not None:
            yield bg_task

    def go_to_portal(self):
        """Navigate back to the portal/introduction page."""
        self.analysis_mode = "portal"
        self.show_indigenous_lands = False  # Hide on portal

    def mark_data_loaded(self):
        """Mark that core data has been loaded."""
        self.data_loaded = True
        self.ee_initialized = True

    # ---- Consolidated-class toggle --------------------------------------

    def toggle_consolidated_classes(self):
        """Toggle between full and consolidated Hansen classes."""
        self.use_consolidated_classes = not self.use_consolidated_classes

    # ---- Buffer distance input ------------------------------------------

    def set_buffer_distance_input(self, value: str):
        """Update buffer distance input field."""
        self.buffer_distance_input = value

    def set_auto_buffer_km(self, value: str):
        """Update the default auto-buffer distance (km)."""
        try:
            km = float(value)
            if km > 0:
                self.auto_buffer_km = km
        except (ValueError, TypeError):
            pass

    def toggle_auto_buffer(self):
        """Toggle automatic buffer creation on territory selection."""
        self.auto_buffer_enabled = not self.auto_buffer_enabled
