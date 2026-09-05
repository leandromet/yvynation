"""
Phase 4: Results panel component - integrates analysis tabs with Plotly charts.
Includes multi-result navigation for switching between territory/geometry analyses.

Rendered inside the desktop results drawer and inside the mobile sheet
(pages/index.py) — twice, safely, because it holds no client-side state of
its own. Its own chrome is deliberately light: the drawer around it already
supplies the border, the background and the scroll container.
"""

import reflex as rx
from ..state import AppState
from .analysis_tabs import analysis_tabs


def _result_nav_tabs() -> rx.Component:
    """Navigation bar for switching between multiple analysis results."""
    return rx.cond(
        AppState.result_keys_list.length() > 1,
        rx.hstack(
            rx.foreach(
                AppState.result_keys_list,
                lambda key: rx.button(
                    # Display label: extract name from "territory::Xingu" or "geometry::0"
                    rx.cond(
                        key.contains("territory"),
                        key.split("::")[1],
                        rx.cond(
                            key.contains("geometry"),
                            "Geom " + key.split("::")[1],
                            key,
                        ),
                    ),
                    on_click=AppState.switch_result(key),
                    size="1",
                    variant=rx.cond(AppState.active_result_key == key, "solid", "outline"),
                    color_scheme=rx.cond(key.contains("territory"), "green", "purple"),
                ),
            ),
            spacing="1",
            flex_wrap="wrap",
            padding="0.5rem",
            border_bottom="1px solid #e0e0e0",
            width="100%",
        ),
        rx.box(),
    )


def resize_button() -> rx.Component:
    """Steps the desktop results drawer through three fixed heights.

    Free-dragging the drawer's own handle already works
    (pages/index.py::_drag_handle, snap=False), but that plain bar reads as
    decoration rather than a control until someone already knows to try it.
    A labelled button needs no discovery at all. Ported from camposcope's
    ``components/results.py::_resize_button``.

    Hidden below "md", where the mobile sheet governs height instead and the
    drawer is not mounted.
    """
    return rx.button(
        rx.icon("unfold-vertical", size=14),
        rx.text(AppState.tr["results_resize_label"], font_size="xs"),
        on_click=rx.call_script(
            "window.__yvyResultsDrawerCycle && window.__yvyResultsDrawerCycle()"),
        size="1", variant="soft", color_scheme="gray",
        aria_label=AppState.tr["results_resize_aria"],
        display=["none", "none", "flex", "flex"],
    )


def fullscreen_button() -> rx.Component:
    """Expand the results drawer to the full workspace height, and back.

    Goes through the same client-side script the drag and the cycle button
    use rather than through a max-height prop, because that script owns the
    drawer's inline height once anything has been dragged — a React-set
    max-height cannot grow a box whose ``height`` is already pinned. The
    state flag is kept only so the button knows which label to show.
    """
    return rx.button(
        rx.cond(
            AppState.fullscreen_panel == "results",
            AppState.tr["exit_full_results"],
            AppState.tr["full_results"],
        ),
        on_click=AppState.toggle_fullscreen_results,
        size="1", variant="outline", color_scheme="gray",
        display=["none", "none", "flex", "flex"],
    )


def results_panel() -> rx.Component:
    """Main results panel with multi-result navigation and analysis tabs."""
    return rx.vstack(
        # Header: what this is, which area it describes, and the two size
        # controls. The old "Close" button that cleared analysis_results
        # outright is gone — the drawer is now resizable down to a sliver
        # and collapses on its own, so throwing the results away is no
        # longer the only way to get the map back.
        rx.hstack(
            rx.text(AppState.tr["results_label"], font_size="sm",
                    font_weight="700", color="#1a472a", flex_shrink="0"),
            rx.badge(
                AppState.analysis_results.get("geometry", ""),
                color_scheme="green",
                variant="outline",
            ),
            rx.spacer(),
            resize_button(),
            fullscreen_button(),
            width="100%",
            align_items="center",
            spacing="2",
            wrap="wrap",
            padding="0.25rem 0.5rem",
        ),
        # Multi-result navigation tabs
        _result_nav_tabs(),
        # Analysis tabs (MapBiomas, Hansen, GFC, AAFC, Comparison, …)
        analysis_tabs(),
        width="100%",
        spacing="2",
        align_items="stretch",
    )
