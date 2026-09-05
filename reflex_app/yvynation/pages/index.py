"""
Main application layout and routing for Yvynation Reflex app.

The analysis workspace is one viewport-locked screen: a fixed navbar, a
collapsible and drag-resizable sidebar, and a map that owns the whole
remaining column with the results drawer floating over it. Below the "md"
breakpoint the sidebar and the results collapse into a single draggable
bottom sheet. The shape and its mechanics are ported from the two sibling
apps — see ``camposcope/pages/index.py`` and
``naturametrics/pages/index.py``.

What this replaced: a page column declaring ``height="120vh"`` over a
workspace row of ``calc(220vh - 70px)``, so the document itself scrolled and
the map slid out from under the header; and a five-row CSS grid in
``main_content_area()`` whose template was shorter than its own child list.
"""

import reflex as rx
from ..state import AppState
from ..components.geometry_sidebar import geometry_sidebar
from ..components.territory_sidebar import territory_sidebar
from ..components.layout import ACCENT, BORDER, HEADER_H
from ..components.map import leaflet_map, map_metrics
from ..components.results_panel import results_panel
from ..components.export_panel import export_panel
from ..components.geometry_popup import geometry_info_popup
from ..components.loading_indicator import loading_indicator
from ..components.language_selector import language_selector
from ..components.citation import citation_modal, cite_trigger
from .portal import portal
from .batch_processing import batch_processing_page
from .previous_runs import previous_runs_page

#: Mirrors the Radix breakpoint scale Reflex's ``display=[...]`` lists use
#: (``[initial, 30em, 48em, 62em]`` → phone, large phone, tablet, desktop).
#: The workspace splits at "md" (48em / 768px): tablet and up get the
#: sidebar + results drawer, below that gets the bottom sheet.
_WIDE_ONLY = ["none", "none", "flex", "flex"]
_NARROW_ONLY = ["flex", "flex", "none", "none"]

#: The sidebar's width before anyone drags it, and the width a double-click
#: on the resize strip returns to. The dragged width itself lives in the
#: viewer's own ``localStorage`` rather than in Reflex state — see
#: ``_PANEL_SCRIPT``.
SIDEBAR_DEFAULT_W = 300
SIDEBAR_MIN_W = 200
SIDEBAR_MAX_W = 640


#: Drag-to-resize for all three panels, ported from camposcope's
#: ``_SHEET_SCRIPT`` with a third, horizontal branch added for this app's
#: sidebar. Deliberately pure client-side DOM manipulation, not a Python
#: event per pixel of pointer movement — a state round trip over the
#: WebSocket for every ``pointermove`` would be visibly laggy, and a dragged
#: size is a per-viewer convenience, not data anything else needs to know
#: about.
#:
#: **Pointer Events, not mouse events.** A mouse-only version does not
#: respond to touch at all, which is most of the point here.
#: ``setPointerCapture`` is what a fast finger-drag actually needs: without
#: it, intermediate ``pointermove`` events can land on whatever element the
#: finger is currently over rather than staying with the handle.
#:
#: **Event DELEGATION on ``document``**, not listeners on the handle nodes.
#: The panels these handles belong to are conditionally rendered, so React
#: tears down and recreates those nodes on state changes far more often than
#: expected, silently orphaning any direct listener. Looking the handle up
#: *inside* the event callback means there is nothing to re-attach.
#:
#: **Three consumers, told apart by their own data attributes.**
#: ``data-snap="free"`` — the desktop results drawer, free vertical drag.
#: ``data-snap="snap"`` — the mobile sheet, three stops plus tap-to-toggle.
#: ``data-col-handle`` — the sidebar, horizontal, its width persisted to
#: ``localStorage`` so it survives both the sidebar's own hide/show remount
#: and a page reload. It is not persisted to Reflex state: writing it back
#: would be a round trip for something no other part of the app reads, and
#: state would still lose it on reload.
_PANEL_SCRIPT_TEMPLATE = """
(function () {
  if (window._yvyPanelInit) return;
  window._yvyPanelInit = true;

  var SIDEBAR_KEY = 'yvySidebarWidth';
  var SIDEBAR_DEFAULT = __DEFAULT_W__;
  var SIDEBAR_MIN = __MIN_W__, SIDEBAR_MAX = __MAX_W__;
  var HEADER_PX = __HEADER_PX__;

  var dragging = false, pointerId = null, startY = 0, startX = 0;
  var startHeight = 0, startWidth = 0;
  var targetEl = null, mode = 'free', movedFar = false;

  // How far a pointer has to travel before this counts as a drag rather
  // than a tap. Touch pointer events fire less consistent `pointermove`
  // sequences than a mouse does on some Android browsers, so a plain tap is
  // the primary, reliable way to open/close the mobile sheet — see
  // `tapTarget()` and the `end()` handler. Dragging still works wherever
  // the browser's pointer events behave.
  var TAP_SLOP_PX = 6;

  function snapPoints() {
    // peek / half / full. Capped at 3/4 of the viewport: past that the map
    // stops being useful as a map, and the whole point of a sheet over a
    // separate results page is that the map stays visible alongside it.
    return [80, window.innerHeight * 0.45, window.innerHeight * 0.75];
  }

  // The two-state toggle a plain tap moves between: 30% / 70% of the
  // viewport, whichever is on the other side of "roughly expanded" from
  // where the sheet is now (so tapping from peek opens to 70%, and tapping
  // again collapses back to 30%).
  function tapTarget(height) {
    var lo = window.innerHeight * 0.30, hi = window.innerHeight * 0.70;
    return height > (lo + hi) / 2 ? lo : hi;
  }

  function nearest(value, points) {
    var best = points[0], bestDist = Math.abs(value - points[0]);
    for (var i = 1; i < points.length; i++) {
      var d = Math.abs(value - points[i]);
      if (d < bestDist) { best = points[i]; bestDist = d; }
    }
    return best;
  }

  function settle(el, target) {
    el.style.transition = 'height 200ms ease-out';
    // height, not just maxHeight: neither panel has an explicit height of
    // its own, so it sizes to its CONTENT — a short tab's content stops
    // growing well under the cap and the handle stops tracking the pointer
    // right there, which reads as "hit a limit" even though maxHeight is
    // nowhere near it. Setting height forces the box to the dragged size
    // regardless of how much is in it.
    el.style.height = target + 'px';
    el.style.maxHeight = target + 'px';
    window.setTimeout(function () { el.style.transition = ''; }, 220);
    updateTab(el);
  }

  // The sheet's handle is a coloured tab with a chevron, not a plain bar —
  // a plain grey bar does not read as an interactive control at all. The
  // chevron flips to point the way dragging would go: up while still closer
  // to peek, down once past it. 160px sits well below every snap point but
  // peek, so it flips early rather than only at the very top.
  function updateTab(el) {
    var tab = el.querySelector && el.querySelector('[data-sheet-tab]');
    if (!tab) return;
    var chevron = tab.querySelector('[data-chevron]');
    if (!chevron) return;
    chevron.style.transform = el.offsetHeight > 160 ? 'rotate(180deg)' : 'rotate(0deg)';
  }

  // ---- sidebar width -------------------------------------------------
  function readStoredWidth() {
    // localStorage throws outright in some contexts (a browser set to block
    // site data, a previewing embedder), so every read and write is guarded
    // and the default stands in.
    try {
      var raw = window.localStorage.getItem(SIDEBAR_KEY);
      var px = parseInt(raw, 10);
      if (!isNaN(px)) return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, px));
    } catch (err) { /* storage unavailable */ }
    return SIDEBAR_DEFAULT;
  }

  function storeWidth(px) {
    try { window.localStorage.setItem(SIDEBAR_KEY, String(px)); }
    catch (err) { /* storage unavailable */ }
  }

  function applyWidth(px) {
    var el = document.getElementById('yvy-desktop-sidebar');
    if (!el) return;
    el.style.width = px + 'px';
    el.style.minWidth = px + 'px';
    el.style.maxWidth = px + 'px';
  }

  // Called from the sidebar box's own on_mount, so a width chosen earlier
  // is restored after the hide/show toggle remounts the panel, and after a
  // reload.
  window.__yvyApplySidebarWidth = function () {
    applyWidth(readStoredWidth());
  };

  window.__yvyResetSidebarWidth = function () {
    storeWidth(SIDEBAR_DEFAULT);
    applyWidth(SIDEBAR_DEFAULT);
  };

  // ---- results drawer ------------------------------------------------
  function resultsDrawerPoints() {
    return [window.innerHeight * 0.22, window.innerHeight * 0.42,
            window.innerHeight * 0.68];
  }

  // Free-dragging the drawer's own handle works, but a plain bar reads as
  // decoration until someone already knows to try it. A button that steps
  // through three fixed heights needs no discovery at all — see
  // components/results_panel.py::resize_button.
  window.__yvyResultsDrawerCycle = function () {
    var el = document.getElementById('yvy-results-drawer');
    if (!el) return;
    var pts = resultsDrawerPoints();
    var idx = (pts.indexOf(nearest(el.offsetHeight, pts)) + 1) % pts.length;
    settle(el, pts[idx]);
  };

  // The full-screen results toggle. It goes through this rather than
  // through a max-height prop on the box because JS owns the drawer's
  // height once anything has been dragged: a React-set max-height cannot
  // shrink or grow a box whose inline `height` this script has already
  // pinned. One owner, no fight.
  window.__yvyResultsDrawerFull = function (on) {
    var el = document.getElementById('yvy-results-drawer');
    if (!el) return;
    settle(el, on ? Math.max(200, window.innerHeight - HEADER_PX)
                  : window.innerHeight * 0.42);
  };

  // ---- mobile sheet --------------------------------------------------
  window.__yvySheetSnapTo = function (name) {
    var el = document.getElementById('yvy-mobile-sheet');
    if (!el) return;
    var pts = snapPoints();
    var target = name === 'full' ? pts[2] : name === 'peek' ? pts[0] : pts[1];
    // Never collapses an already-more-open sheet: a fresh result should
    // reveal itself, not interrupt someone already reading a wider sheet.
    if (el.offsetHeight >= target) return;
    settle(el, target);
  };

  // Nudging the sheet open only makes sense the FIRST time, before anyone
  // knows there is something to see down there. Past that it should stay
  // out of the way of whatever height the user has since chosen. Does not
  // persist across a reload — a fresh page load is a fresh "first time".
  var nudged = false;
  window.__yvySheetNudgeOpen = function () {
    if (nudged) return;
    nudged = true;
    window.__yvySheetSnapTo('half');
  };

  // ---- pointer plumbing ----------------------------------------------
  document.addEventListener('pointerdown', function (e) {
    if (!e.target.closest) return;
    // The handle the pointer went down on, whichever kind it is — it is
    // also what captures the pointer, so a fast drag that leaves the
    // handle's own box keeps sending moves here.
    var captureEl = e.target.closest('[data-col-handle]');
    if (captureEl) {
      targetEl = document.getElementById(captureEl.getAttribute('data-col-handle'));
      if (!targetEl) return;
      mode = 'col';
      startX = e.clientX;
      startWidth = targetEl.offsetWidth;
    } else {
      captureEl = e.target.closest('[data-drawer-handle]');
      if (!captureEl) return;
      targetEl = document.getElementById(captureEl.getAttribute('data-drawer-handle'));
      if (!targetEl) return;
      mode = captureEl.getAttribute('data-snap') || 'free';
      startY = e.clientY;
      startHeight = targetEl.offsetHeight;
    }
    dragging = true;
    movedFar = false;
    pointerId = e.pointerId;
    try { captureEl.setPointerCapture(e.pointerId); } catch (err) { /* older browsers */ }
    document.body.style.userSelect = 'none';
  });

  document.addEventListener('pointermove', function (e) {
    if (!dragging || e.pointerId !== pointerId || !targetEl) return;
    if (mode === 'col') {
      var dx = e.clientX - startX;
      if (Math.abs(dx) > TAP_SLOP_PX) movedFar = true;
      applyWidth(Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, startWidth + dx)));
      return;
    }
    var delta = startY - e.clientY;
    if (Math.abs(delta) > TAP_SLOP_PX) movedFar = true;
    var next = Math.min(window.innerHeight * 0.75, Math.max(80, startHeight + delta));
    targetEl.style.height = next + 'px';
    targetEl.style.maxHeight = next + 'px';
    updateTab(targetEl);
  });

  function end(e) {
    if (!dragging || e.pointerId !== pointerId || !targetEl) return;
    dragging = false;
    document.body.style.userSelect = '';
    if (mode === 'col') {
      if (movedFar) storeWidth(targetEl.offsetWidth);
    } else if (mode === 'snap') {
      // A plain tap (no meaningful movement): jump straight to whichever of
      // the 30%/70% targets isn't roughly where the sheet already is. There
      // is nothing to be "nearest to" when nothing was dragged.
      settle(targetEl, movedFar
        ? nearest(targetEl.offsetHeight, snapPoints())
        : tapTarget(startHeight));
    }
    targetEl = null;
  }
  document.addEventListener('pointerup', end);
  document.addEventListener('pointercancel', end);

  // ---- keyboard ------------------------------------------------------
  document.addEventListener('keydown', function (e) {
    var active = document.activeElement;
    if (!active || !active.closest) return;

    var col = active.closest('[data-col-handle]');
    if (col && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
      var el = document.getElementById(col.getAttribute('data-col-handle'));
      if (!el) return;
      var w = Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN,
        el.offsetWidth + (e.key === 'ArrowRight' ? 40 : -40)));
      applyWidth(w);
      storeWidth(w);
      e.preventDefault();
      return;
    }

    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    var handle = active.closest('[data-drawer-handle][data-snap="snap"]');
    if (!handle) return;
    var sheet = document.getElementById(handle.getAttribute('data-drawer-handle'));
    if (!sheet) return;
    var pts = snapPoints();
    var idx = pts.indexOf(nearest(sheet.offsetHeight, pts));
    idx = e.key === 'ArrowUp' ? Math.min(pts.length - 1, idx + 1) : Math.max(0, idx - 1);
    settle(sheet, pts[idx]);
    e.preventDefault();
  });

  // Match the chevron to the sheet's own starting height (it opens at
  // "half", not "peek") rather than waiting for the first drag to set it.
  var initialSheet = document.getElementById('yvy-mobile-sheet');
  if (initialSheet) updateTab(initialSheet);
  window.__yvyApplySidebarWidth();
})();
"""

#: Plain textual substitution rather than %-formatting or str.format: the
#: script body contains both a JS modulo (`% pts.length`) and object
#: literals, either of which a real format string would have to escape.
_PANEL_SCRIPT = (
    _PANEL_SCRIPT_TEMPLATE
    .replace("__DEFAULT_W__", str(SIDEBAR_DEFAULT_W))
    .replace("__MIN_W__", str(SIDEBAR_MIN_W))
    .replace("__MAX_W__", str(SIDEBAR_MAX_W))
    .replace("__HEADER_PX__", HEADER_H.replace("px", ""))
)


def _drag_handle(*, drawer_id: str, handle_id: str, snap: bool) -> rx.Component:
    """A vertical drag target for ``_PANEL_SCRIPT``.

    ``snap=True`` marks the mobile sheet's handle: it gets keyboard
    stepping, the three-stop snap behaviour, and a solid accent-coloured tab
    with a chevron that flips to show which way dragging goes. It is the
    sheet's only "open" affordance, so it has to actually read as one — a
    plain grey bar does not. ``snap=False`` (the desktop results drawer)
    keeps the plain-bar free-drag feel; it has a labelled button beside it
    for discoverability instead (components/results_panel.py).
    """
    if snap:
        handle_content = rx.box(
            rx.icon("chevron-up", size=16, color="white",
                    custom_attrs={"data-chevron": "1"},
                    style={"transition": "transform 200ms ease"}),
            custom_attrs={"data-sheet-tab": "1"},
            display="flex", align_items="center", justify_content="center",
            width="56px", height="22px",
            background=f"var(--{ACCENT}-9)",
            border_radius="11px",
            box_shadow="0 2px 6px rgba(0, 0, 0, 0.3)",
        )
    else:
        handle_content = rx.box(width="36px", height="4px", border_radius="2px",
                                background="var(--gray-6)")
    return rx.box(
        handle_content,
        id=handle_id,
        custom_attrs={
            "data-drawer-handle": drawer_id,
            "data-snap": "snap" if snap else "free",
        },
        tab_index=0 if snap else None,
        role="slider" if snap else None,
        aria_label=AppState.tr["sheet_handle_aria"] if snap else None,
        outline="none",
        display="flex", justify_content="center", align_items="center",
        width="100%", height="30px" if snap else "14px",
        cursor="ns-resize", flex_shrink="0",
        padding_top="4px" if snap else "0",
        _hover={} if snap else {"background": "var(--gray-3)"},
        _focus_visible={"background": "var(--gray-4)",
                        "box_shadow": "inset 0 0 0 2px var(--accent-8)"},
    )


def _sidebar_resize() -> rx.Component:
    """The strip between the sidebar and the map: drag to resize.

    Replaces the three preset buttons (``◀ / resize / ▶``) that used to sit
    in the navbar and set 200/300/600 px — the last of which silently landed
    on 500 because the handler clamped there. Arrow keys step ±40 px when it
    has focus; double-click returns to the default width.

    Mounted only while the sidebar is open: collapsed, the panel is a 28px
    tab, and there is nothing there worth widening.
    """
    return rx.cond(
        AppState.sidebar_open,
        rx.box(
            rx.box(width="2px", height="28px", border_radius="1px",
                   background="var(--gray-6)"),
            id="yvy-sidebar-resize",
            custom_attrs={"data-col-handle": "yvy-desktop-sidebar"},
            on_double_click=rx.call_script(
                "window.__yvyResetSidebarWidth && window.__yvyResetSidebarWidth()"),
            tab_index=0,
            role="separator",
            aria_label=AppState.tr["sidebar_resize_aria"],
            outline="none",
            display=_WIDE_ONLY,
            align_items="center", justify_content="center",
            width="7px", flex_shrink="0", height="100%",
            cursor="col-resize",
            background="var(--color-panel-solid)",
            border_right=BORDER,
            _hover={"background": "var(--gray-3)"},
            _focus_visible={"background": "var(--gray-4)",
                            "box_shadow": "inset 0 0 0 2px var(--accent-8)"},
        ),
        rx.box(),
    )


def sidebar_content() -> rx.Component:
    """Whichever sidebar the current analysis mode calls for.

    Safe to render twice (desktop panel and mobile sheet) — both sidebars
    are pure presentations of ``AppState`` with no client-side state of
    their own. The map is not like that and is built exactly once, in
    ``_map()``.
    """
    return rx.cond(
        AppState.analysis_mode == "geometry",
        geometry_sidebar(),
        territory_sidebar(),
    )


def _sidebar() -> rx.Component:
    """Tablet and up: the in-flow controls panel, or a slim tab when hidden.

    ``id="yvy-desktop-sidebar"`` is what ``_PANEL_SCRIPT`` resizes and what
    the landscape-phone override in ``yvynation.py`` hides — width-only
    breakpoints put a rotated phone (often 700–930px wide) into this branch
    on a viewport with nowhere near the height it assumes.
    """
    return rx.cond(
        AppState.sidebar_open,
        rx.box(
            sidebar_content(),
            id="yvy-desktop-sidebar",
            display=_WIDE_ONLY,
            flex_direction="column",
            width=f"{SIDEBAR_DEFAULT_W}px",
            min_width=f"{SIDEBAR_DEFAULT_W}px",
            max_width=f"{SIDEBAR_DEFAULT_W}px",
            height="100%",
            overflow_y="auto",
            overflow_x="hidden",
            background="var(--color-panel-solid)",
            # Restores a width chosen earlier in this browser: the panel is
            # inside an rx.cond, so hide/show remounts it with the default
            # width prop above, and a reload starts from scratch.
            on_mount=rx.call_script(
                "window.__yvyApplySidebarWidth && window.__yvyApplySidebarWidth()"),
        ),
        # A coloured tab, not a small grey icon button: collapsed to its
        # smallest state, a tiny ghost control in a thin rail does not read
        # as "click here". Same visual language as the mobile sheet's handle.
        rx.box(
            rx.box(
                rx.icon("chevron-right", size=18, color="white"),
                on_click=AppState.toggle_sidebar,
                role="button", cursor="pointer",
                aria_label=AppState.tr["sidebar_show_aria"],
                display="flex", align_items="center", justify_content="center",
                width="28px", height="56px",
                background=f"var(--{ACCENT}-9)",
                border_radius="0 8px 8px 0",
                box_shadow="2px 0 6px rgba(0, 0, 0, 0.2)",
                _hover={"background": f"var(--{ACCENT}-10)"},
            ),
            id="yvy-desktop-sidebar",
            display=_WIDE_ONLY,
            align_items="center",
            padding="2",
            border_right=BORDER,
            background="var(--color-panel-solid)",
            height="100%",
        ),
    )


def _mobile_sheet() -> rx.Component:
    """Below "md": the map's only interaction surface.

    One draggable bottom sheet holding both the sidebar's controls and the
    results, **always mounted and never "closed"** — "closed" is just its own
    peek snap point (80px: the handle plus a sliver). The alternative, an
    overlay that is either full-screen or entirely absent, is two DOM states
    to keep in sync and leaves everything unreachable the moment it is shut.

    Starts at "half", not peek: the way in should be visible on load, not
    hidden a gesture away.
    """
    return rx.vstack(
        _drag_handle(drawer_id="yvy-mobile-sheet",
                     handle_id="yvy-mobile-sheet-handle", snap=True),
        rx.box(
            sidebar_content(),
            results_column(),
            overflow_y="auto", flex="1", min_height="0",
        ),
        id="yvy-mobile-sheet",
        display=_NARROW_ONLY,
        flex_direction="column",
        # align="stretch", NOT rx.vstack's own default of "start". `align:
        # start` compiles to `align-items: flex-start`, which sizes the
        # scrolling box above to its own CONTENT width rather than the
        # sheet's — and the results content (a ten-tab list plus data
        # tables) runs far wider than a portrait phone, so that box rendered
        # wider than the sheet and `overflow: hidden` below cut the excess
        # off with no scrollbar and no way to reach it. Measured in both
        # sibling apps, which had the same bug from the same default: 390px
        # sheet, 835px content box. `stretch` pins the box to the sheet's
        # width, and its own overflow then scrolls what is still too wide.
        align="stretch",
        position="absolute", bottom="0", left="0", right="0",
        height="45vh", max_height="45vh",
        background="var(--color-panel-solid)",
        border_top_left_radius="var(--radius-4)",
        border_top_right_radius="var(--radius-4)",
        box_shadow="0 -4px 24px rgba(0, 0, 0, 0.25)",
        # Leaflet's own panes reach ~700 internally; anything lower renders
        # under the map and is invisible.
        z_index="1000",
        overflow="hidden",
        spacing="0",
        style={
            "--font-size-1": "calc(var(--font-size-1) - 3px)",
            "--font-size-2": "calc(var(--font-size-2) - 3px)",
            "--font-size-3": "calc(var(--font-size-3) - 3px)",
        },
    )


def active_target_bar() -> rx.Component:
    """Top-center active-analysis-target switcher + 'Run all' (shared by both pages).

    Shows what every "Analyse" run will use (subject · buffer · years), lets the
    user switch the active geometry (territory or any drawing — which also zooms
    the map to it), and runs all analyses on it in one click.
    """
    return rx.cond(
        AppState.analysis_mode != "portal",
        rx.hstack(
            # Active-target switcher
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.hstack(
                            rx.text("🎯", font_size="md"),
                            rx.vstack(
                                rx.text(
                                    AppState.active_target_label,
                                    font_size="sm", font_weight="700",
                                    color="#1a472a", no_of_lines=1,
                                ),
                                rx.text(
                                    AppState.active_target_kind_label
                                    + "  ·  🔵 " + AppState.active_buffer_label,
                                    font_size="xs", color="gray",
                                ),
                                spacing="0", align_items="flex-start",
                            ),
                            rx.icon("chevron-down", size=14),
                            spacing="2", align_items="center",
                        ),
                        variant="outline", color_scheme="green", size="2",
                    ),
                ),
                rx.menu.content(
                    rx.text(
                        AppState.tr["active_analysis_area"],
                        font_size="xs", font_weight="600", color="gray",
                        padding="0.25rem 0.5rem",
                    ),
                    rx.cond(
                        AppState.active_target_options.length() > 0,
                        rx.foreach(
                            AppState.active_target_options,
                            lambda o: rx.menu.item(
                                o["label"],
                                on_click=lambda: AppState.set_active_target(o["id"]),
                            ),
                        ),
                        rx.text(AppState.tr["no_areas_yet"],
                                font_size="xs", color="gray",
                                padding="0.25rem 0.5rem"),
                    ),
                ),
            ),
            # Comparison years
            rx.badge(
                "MapBiomas " + AppState.comparison_year1.to(str)
                + " → " + AppState.comparison_year2.to(str),
                color_scheme="green", variant="soft", size="2",
                display=["none", "none", "none", "inline-flex"],
            ),
            # Run-all button
            rx.button(
                AppState.tr["run_all_analysis"],
                on_click=AppState.run_all_analysis,
                is_disabled=~AppState.has_active_target,
                size="2", bg="#16A34A", color="white", font_weight="bold",
                _hover={"bg": "#15803D"}, cursor="pointer",
            ),
            # Download-all (every analyzed area: data + viz + maps)
            rx.cond(
                AppState.analyzed_target_count > 0,
                rx.button(
                    rx.cond(
                        AppState.export_pending,
                        rx.hstack(rx.spinner(size="1"), rx.text(AppState.tr["bundling"]),
                                  spacing="2", align_items="center"),
                        rx.text(AppState.tr["download_all"] + " ("
                                + AppState.analyzed_target_count.to(str) + ")"),
                    ),
                    on_click=AppState.download_all_results,
                    is_disabled=AppState.export_pending,
                    size="2", variant="outline", color_scheme="green",
                    cursor="pointer",
                ),
                rx.fragment(),
            ),
            spacing="3", align_items="center", wrap="wrap",
        ),
        rx.fragment(),
    )


def navbar() -> rx.Component:
    """Modern top navigation bar.

    Fixed at ``HEADER_H``; the workspace below it takes the rest of the
    viewport. The three sidebar-width preset buttons that used to live in
    the left cluster are gone — the sidebar has a real drag handle now
    (``_sidebar_resize``).
    """
    return rx.hstack(
        # Left side - toggle & branding
        rx.hstack(
            rx.box(
                rx.cond(
                    AppState.sidebar_open,
                    rx.icon("panel-left-close", size=18),
                    rx.icon("panel-left-open", size=18),
                ),
                on_click=AppState.toggle_sidebar,
                role="button", cursor="pointer",
                aria_label=rx.cond(
                    AppState.sidebar_open,
                    AppState.tr["sidebar_hide_aria"],
                    AppState.tr["sidebar_show_aria"],
                ),
                display="flex", align_items="center", justify_content="center",
                width="28px", height="28px", flex_shrink="0",
                border_radius="var(--radius-2)",
                _hover={"background": "var(--gray-4)"},
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(AppState.tr["app_title"], size="3",
                               white_space="nowrap"),
                    rx.cond(
                        AppState.analysis_mode != "portal",
                        rx.hstack(
                            rx.text("•", color="#4a7c59", font_weight="bold"),
                            rx.text(
                                rx.cond(
                                    AppState.analysis_mode == "geometry",
                                    AppState.tr["geometry_analysis_label"],
                                    AppState.tr["territory_analysis_label"],
                                ),
                                font_size="sm",
                                color="#1a472a",
                                font_weight="500",
                            ),
                            spacing="1",
                            align_items="center",
                            display=["none", "none", "flex", "flex"],
                        ),
                        rx.box(),
                    ),
                    spacing="2",
                    align_items="center",
                ),
                rx.text(
                    AppState.tr["app_subtitle"],
                    font_size="xs",
                    color="gray",
                    display=["none", "none", "none", "block"],
                ),
                spacing="0",
                margin="0",
                align_items="flex-start",
            ),
            width="auto",
            align_items="center",
            spacing="2",
            min_width="0",
        ),
        # Center - active analysis target switcher + Run all
        rx.spacer(),
        active_target_bar(),
        rx.spacer(),
        # Right side - layer counts, language, back, clear, analysis indicator
        rx.hstack(
            # The active-layer counts. In the navbar rather than floating
            # over the map, which is where they would otherwise go: the
            # Folium document owns both top corners of its own viewport —
            # zoom, fullscreen and the draw tools at top-left, and an
            # expanded (`collapsed=False`) layer control at top-right, see
            # utils/map_builder.py — and the bottom belongs to the results
            # drawer. There is no free corner, and this is a status readout
            # that never needed to be on the map to begin with.
            rx.box(
                map_metrics(),
                display=["none", "none", "none", "flex"],
            ),
            language_selector(),
            cite_trigger(),
            rx.button(
                AppState.tr["back_to_portal"],
                on_click=lambda: AppState.go_to_portal(),
                size="1",
                variant="outline",
                color_scheme="green",
            ),
            rx.button(
                AppState.tr["clear_btn"],
                on_click=AppState.clear_all_state(),
                size="1",
                variant="outline",
                color_scheme="red",
            ),
            rx.cond(
                (AppState.analysis_results != {}) & (AppState.analysis_results != None),
                rx.badge(
                    AppState.tr["analysis_active_badge"],
                    color_scheme="green",
                    variant="solid",
                    size="1",
                ),
                rx.box(),
            ),
            align_items="center",
            spacing="3",
            flex_shrink="0",
        ),
        padding="0.5rem 1rem",
        bg="linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%)",
        border_bottom="2px solid #e8f0e8",
        align_items="center",
        width="100%",
        height=HEADER_H,
        flex_shrink="0",
        overflow="hidden",
        z_index="100",
    )


def error_toast(state: AppState) -> rx.Component:
    """Display error messages."""
    return rx.cond(
        state.error_message != "",
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon("alert-circle", color="red"),
                    rx.text(state.error_message),
                    width="100%",
                ),
                rx.button(
                    AppState.tr["dismiss"],
                    size="1",
                    on_click=state.clear_error,
                ),
                width="100%",
            ),
            padding="1rem",
            bg="red.50",
            border="1px solid red",
            border_radius="md",
            position="fixed",
            bottom="1rem",
            right="1rem",
            z_index="9999",
            max_width="400px",
        ),
        rx.box(),
    )


def comparison_results_section() -> rx.Component:
    """Year comparison results: charts + summary cards."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading(AppState.tr["year_comparison_results"], size="3"),
                rx.spacer(),
                rx.button(
                    AppState.tr["download_comparison_csv"],
                    on_click=AppState.download_comparison_csv,
                    size="1",
                    color_scheme="blue",
                    variant="outline",
                ),
                width="100%",
                align_items="center",
            ),
            rx.divider(),
            rx.plotly(data=AppState.gains_losses_chart, use_resize_handler=True),
            rx.divider(),
            rx.plotly(data=AppState.change_pct_chart, use_resize_handler=True),
            rx.divider(),
            # Summary cards
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["total_gains"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_total_gains,
                                font_weight="bold", color="green"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="green.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["total_losses"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_total_losses,
                                font_weight="bold", color="red"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="red.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.text(AppState.tr["net_change"], font_size="xs", color="gray"),
                        rx.text(AppState.comparison_net_change,
                                font_weight="bold"),
                        spacing="0", align="center",
                    ),
                    padding="0.75rem", bg="blue.50", border_radius="md",
                    flex="1", text_align="center",
                ),
                width="100%",
                spacing="2",
                wrap="wrap",
            ),
            spacing="3",
            width="100%",
            padding="1rem",
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
    )


def results_column() -> rx.Component:
    """Everything an analysis produces: tabs, comparison charts, exports.

    Rendered in two places — the desktop drawer and the mobile sheet — and
    safe there for the same reason the sidebar is: it holds no client-side
    state, only ``AppState``.
    """
    return rx.cond(
        (AppState.analysis_results != {}) & (AppState.analysis_results != None),
        rx.vstack(
            results_panel(),
            rx.cond(
                AppState.comparison_available,
                comparison_results_section(),
                rx.box(),
            ),
            export_panel(),
            width="100%",
            spacing="3",
            padding="0.5rem",
            align_items="stretch",
            # This subtree mounts exactly when the first analysis lands, so
            # it is also the right moment to nudge a collapsed mobile sheet
            # open — otherwise a user who dragged the sheet down to see more
            # map gets results they are never told about. One-shot on the JS
            # side (`nudged`), so it never fights a height the user has
            # since chosen, and a no-op on the second of the two places this
            # renders. Declarative rather than yielded from the analysis
            # handlers: those set results from several paths, most of them
            # background tasks that reach this through plain method calls
            # that cannot yield an event of their own.
            on_mount=rx.call_script(
                "window.__yvySheetNudgeOpen && window.__yvySheetNudgeOpen()"),
        ),
        rx.box(),
    )


def _map() -> rx.Component:
    """The map, filling its column, with everything else floating over it.

    Neither overlay resizes the map's own container — both are
    ``position: absolute`` over it — so dragging a panel changes only how
    much of the map is covered, never the map element's own box. That
    matters here more than in the sibling apps: this map is a Folium
    document inside an iframe, and a container that actually changed size
    would need the embedded Leaflet to be told about it.

    Exactly one map is built, here. The sidebar and the results are the ones
    rendered twice (desktop and sheet), because they are pure presentations
    of state.
    """
    return rx.box(
        leaflet_map(),
        # Tablet and up: the results drawer, floating over the map's bottom
        # edge rather than sharing the column with it. z-index must clear
        # Leaflet's own panes (~700) or it renders under the map. Mounted
        # only once there is something to show — an empty drawer would still
        # leave its handle bar sitting on the map.
        rx.cond(
            (AppState.analysis_results != {}) & (AppState.analysis_results != None),
            rx.box(
                _drag_handle(drawer_id="yvy-results-drawer",
                             handle_id="yvy-results-drag-handle", snap=False),
                rx.box(
                    results_column(),
                    overflow_y="auto", flex="1", min_height="0", width="100%",
                ),
                id="yvy-results-drawer",
                display=_WIDE_ONLY,
                flex_direction="column",
                position="absolute", bottom="0", left="0", right="0",
                max_height="42vh",
                background="var(--color-panel-solid)",
                border_top=BORDER,
                box_shadow="0 -4px 24px rgba(0, 0, 0, 0.18)",
                z_index="1000",
                overflow="hidden",
                style={
                    "--font-size-1": "calc(var(--font-size-1) - 3px)",
                    "--font-size-2": "calc(var(--font-size-2) - 3px)",
                    "--font-size-3": "calc(var(--font-size-3) - 3px)",
                },
            ),
        ),
        _mobile_sheet(),
        flex="1",
        height="100%",
        min_width="0",
        position="relative",
        overflow="hidden",
        # NOT rx.script(...) as a child — a script inserted as a JSX child is
        # set via innerHTML, which browsers refuse to execute, so it would
        # never run. on_mount=rx.call_script fires through Reflex's own event
        # pipeline instead. Confirmed the hard way in camposcope, whose
        # docstring records the same finding.
        on_mount=rx.call_script(_PANEL_SCRIPT),
    )


def workspace() -> rx.Component:
    """Navbar + sidebar + map, locked to the viewport.

    ``100dvh``, not ``100vh``: on mobile browsers ``vh`` includes the
    collapsing URL bar, so ``100vh`` leaves the bottom of the page
    permanently under the chrome — and the bottom is where the sheet's
    handle lives.
    """
    return rx.vstack(
        navbar(),
        rx.hstack(
            _sidebar(),
            _sidebar_resize(),
            _map(),
            width="100%",
            flex="1",
            min_height="0",
            spacing="0",
            align_items="stretch",
            overflow="hidden",
        ),
        error_toast(AppState),
        loading_indicator(),
        geometry_info_popup(),
        citation_modal(),
        width="100vw",
        height=["100dvh", "100dvh", "100dvh", "100vh"],
        spacing="0",
        align_items="stretch",
        overflow="hidden",
    )


def index() -> rx.Component:
    """Main application layout with dynamic content based on analysis mode."""
    return rx.cond(
        AppState.analysis_mode == "portal",
        portal(),
        rx.cond(
            AppState.analysis_mode == "batch",
            batch_processing_page(),
            rx.cond(
                AppState.analysis_mode == "previous_runs",
                previous_runs_page(),
                # Analysis pages (geometry or territory mode)
                workspace(),
            ),
        ),
    )
