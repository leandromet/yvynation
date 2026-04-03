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
        """Switch active content tab."""
        self.active_tab = tab

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

    def start_resize(self):
        """Begin sidebar resize drag."""
        self.is_resizing_sidebar = True

    def end_resize(self):
        """End sidebar resize drag."""
        self.is_resizing_sidebar = False

    def update_sidebar_width(self, width: int):
        """Update sidebar width (constrained 200–500 px)."""
        self.sidebar_width = max(200, min(500, width))

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
