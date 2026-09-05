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
        """Change application language (manual choice wins over auto-detect)."""
        self.language = lang
        self.language_user_set = True

    def detect_browser_language(self):
        """On page load, ask the browser for its preferred language.

        Runs client-side via navigator.language (no permission prompt, unlike
        geolocation) and feeds the result to apply_browser_language. Skipped
        when the user has already picked a language or disabled auto-detect.
        """
        if self.language_user_set or not self.auto_detect_enabled:
            return
        yield rx.call_script(
            "navigator.language || 'en'",
            callback=type(self).apply_browser_language,
        )

    def apply_browser_language(self, browser_lang: str):
        """Map a BCP-47 browser tag (pt-BR, fr-CA, es-419…) to a supported language."""
        from ..utils.translations import TRANSLATIONS

        if self.language_user_set or not self.auto_detect_enabled:
            return
        code = (browser_lang or "").lower()[:2]
        if code in TRANSLATIONS and code != self.language:
            self.language = code
            logger.info("Auto-detected browser language: %s -> %s", browser_lang, code)

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

    def update_sidebar_width(self, width: int):
        """Set the sidebar width (constrained 200–640 px).

        Legacy: the live workspace no longer routes width through state at
        all. Dragging it is pure client-side DOM
        (pages/index.py::_PANEL_SCRIPT) and the chosen width is kept in the
        viewer's own localStorage — a state round trip per `pointermove`
        would be visibly laggy, and this is a per-viewer convenience nothing
        else reads. Only the unrouted pages/{geometry,territory}_analysis.py
        still size their sidebar from `sidebar_width`.

        The bound is 640 rather than the 500 this used to clamp to, matching
        the drag range in the script. The old value was a silent trap: the
        navbar's "wide" preset button asked for 600 and got 500 with no
        indication that it had been overruled.
        """
        try:
            px = int(width)
        except (TypeError, ValueError):
            return
        self.sidebar_width = max(200, min(640, px))

    # ---- Sidebar groups (accordion) --------------------------------------

    def set_open_groups(self, value):
        """The sidebar accordion's own `on_value_change`.

        Every manual open/close passes back through here as the whole new
        array (`type="multiple"`), same as any other controlled Radix
        component. Accepts a bare string too because Reflex's accordion
        event spec is shared with `type="single"`, which reports one — this
        accordion is always `type="multiple"`, but the signature has to
        accept both to pass Reflex's own event-handler type check.
        """
        self.open_groups = [value] if isinstance(value, str) else list(value)

    def _open_group(self, name: str) -> None:
        """Force one sidebar group open, once per session.

        A first-time user has no reason to know that the controls answering
        "what did that just do?" are inside a collapsed group until
        something puts them in front of them. One-shot, so a user who then
        deliberately collapses the group stays collapsed — the same guard
        naturametrics' `_open_study_area` uses, and for the same reason.
        """
        if name in self._groups_auto_opened:
            return
        self._groups_auto_opened = [*self._groups_auto_opened, name]
        if name not in self.open_groups:
            self.open_groups = [*self.open_groups, name]

    # ---- Full-screen results panel --------------------------------------
    # (The map uses Leaflet's own full-screen control; only the results area
    #  needs an app-level toggle.)

    def toggle_fullscreen_results(self):
        """Expand the results drawer to fill the workspace (toggle to split).

        The height itself is set client-side, by the same script that owns
        every other drawer/sheet size (pages/index.py::_PANEL_SCRIPT): once
        the drawer has been dragged, its inline `height` is pinned, and a
        max-height coming from a Reflex prop could neither grow nor shrink
        it. One owner for the height, and the flag here only decides which
        label the button shows.
        """
        self.fullscreen_panel = "" if self.fullscreen_panel == "results" else "results"
        on = "true" if self.fullscreen_panel == "results" else "false"
        yield rx.call_script(
            f"window.__yvyResultsDrawerFull && window.__yvyResultsDrawerFull({on})"
        )

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

    # ---- Portal ----------------------------------------------------------

    def toggle_portal_data_sources(self):
        """Expand or collapse the portal's data-sources list."""
        self.portal_data_sources_open = not self.portal_data_sources_open

    # ---- Citation / acknowledgments --------------------------------------

    def toggle_citation(self):
        """Toggle the 'How to cite & acknowledgments' panel visibility."""
        self.show_citation = not self.show_citation

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

    def go_to_territory_analysis(self, territory_type: str = "indigenous"):
        """Navigate to territory analysis for indigenous lands or conservation
        units, then kick off background loading for that type.

        The portal picks the territory type up front (indigenous vs.
        conservation are now separate entry points, no in-page switch), so on
        a first-ever visit this seeds ``territory_type`` before
        ``initialize_app`` does its one-time load; on a later visit (EE
        already initialized) it reuses ``set_territory_type`` to (re)load the
        right GeoPackage if the user picked a different type this time.
        """
        self.analysis_mode = "territory"
        self.show_indigenous_lands = True
        if territory_type not in ("indigenous", "conservation"):
            territory_type = "indigenous"

        if not self.ee_initialized:
            self.territory_type = territory_type
            bg_task = self.initialize_app()
        else:
            bg_task = self.set_territory_type(territory_type)

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

    def go_to_previous_runs(self):
        """Navigate to the Previous Runs page and refresh its listing.

        Remembers where the user came from — the page is reachable both from the
        portal and from the batch navbar, and sending everyone back to the portal
        loses a configured batch selection.
        """
        if self.analysis_mode in ("portal", "batch"):
            self.previous_runs_return_to = self.analysis_mode
        self.analysis_mode = "previous_runs"
        self.show_indigenous_lands = False
        self.load_previous_runs()

    def leave_previous_runs(self):
        """Go back to whichever page opened Previous Runs."""
        self.show_indigenous_lands = False
        if self.previous_runs_return_to == "batch":
            self.analysis_mode = "batch"
            # Same background load as go_to_batch_processing: the selection and
            # territory list survive in state, but a cold container may not have
            # loaded them yet.
            bg_task = self.initialize_app()
            if bg_task is not None:
                yield bg_task
        else:
            self.analysis_mode = "portal"

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
