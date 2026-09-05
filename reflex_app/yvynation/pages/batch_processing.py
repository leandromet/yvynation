"""
Batch Processing page for Yvynation.

Lets users select multiple indigenous territories and/or conservation units,
configure analysis years and options, and kick off a full automated analysis
run. All results are packaged into a single ZIP archive — no charts are
rendered during processing.

Unlike the analysis workspace, this page has no map. It is a job builder with
a sequence to it, so it is laid out as three named stages — Select, Configure,
Run — rather than as a workspace around a subject. The stage bar
(components/batch_shared.py::stage_bar) is what lets a phone show one stage at
a time instead of one scroll holding a 3,000-row list, 26 controls and a live
log, and the action bar is pinned to the bottom of the viewport so Start is
reachable at any config length rather than buried below it.

Layout pieces live in components/batch_*.py:
  batch_shared.py             shared style tokens, the stage bar, the filter widget
  batch_territory_selector.py the checkable territory list and its filters
  batch_config_panel.py       years/options/buffer, in six accordion groups
  batch_status_panel.py       progress bar + live log
  batch_howto_panel.py        usage guide accordion
  batch_action_panel.py       start/stop/download controls
  batch_navbar.py             top navbar
  batch_review_modal.py       selected-territories review panel (both types)
"""

import reflex as rx
from ..state import AppState
from ..components.citation import citation_modal
from ..components.batch_territory_selector import territory_selector
from ..components.batch_config_panel import config_panel
from ..components.batch_status_panel import status_panel
from ..components.batch_howto_panel import howto_panel
from ..components.batch_action_panel import action_panel
from ..components.batch_navbar import batch_navbar
from ..components.batch_review_modal import review_selection_modal
from ..components.batch_shared import ORANGE_BORDER, stage_bar

#: Same Radix breakpoint scale the analysis workspace uses
#: (``[initial, 30em, 48em, 62em]``); the split is at "md" (48em / 768px).
_WIDE_ONLY = ["none", "none", "flex", "flex"]
_NARROW_ONLY = ["flex", "flex", "none", "none"]


def _scroll_column(*children: rx.Component, **props) -> rx.Component:
    """One independently scrolling column. Nothing scrolls at page level on
    this page any more, so every region that can overflow owns its own
    scroller."""
    return rx.box(
        rx.vstack(*children, spacing="4", width="100%", align_items="stretch"),
        overflow_y="auto",
        min_height="0",
        padding="1rem",
        **props,
    )


def _select_stage() -> rx.Component:
    """Stage 1. The list is the hero; the guide sits under it.

    One scrolling column, so the list is given a definite ``60dvh`` rather
    than being asked to fill space that a scroller does not have — see
    ``territory_selector``'s own docstring for the two sizing modes.

    ``howto_panel()`` used to render at the bottom of the right column with a
    comment explaining it was there to "fill the empty space below the
    ~1/3-height progress area" — space that only exists once a run is in
    progress, which is exactly when nobody is reading a how-to. Here it is
    below the thing a first-time user is already looking at.
    """
    return rx.vstack(
        territory_selector(list_height="60dvh"),
        howto_panel(),
        spacing="4", width="100%", align_items="stretch",
    )


def _run_stage() -> rx.Component:
    """Stage 3: progress and the live log, with the configuration kept
    readable below it.

    The config panel used to be hidden outright behind
    ``~batch_running & ~batch_done``, so the moment a job started there was no
    way to check what you had actually asked for — on a run that takes tens of
    minutes, over a list you may have spent a while assembling.
    """
    return rx.vstack(
        status_panel(),
        config_panel(),
        spacing="4", width="100%", align_items="stretch",
    )


def _wide_body() -> rx.Component:
    """Tablet and up: selection beside configuration, each scrolling itself.

    ``flex="1 1 360px"`` / ``flex="1.6 1 460px"``, not the ``width="38%"`` and
    ``width="62%"`` with a ``min_width="300px"`` floor this replaced. Those
    percentages needed 542px of a 390px phone and simply overflowed sideways;
    flex bases shrink, and wrap rather than overflow at the narrowest tablet.
    """
    return rx.flex(
        # NOT a _scroll_column: the selector manages its own scrolling (only
        # its list overflows) and needs an unbroken flex chain from here down
        # to stretch into the column. A scroll wrapper would put a
        # content-height box in the middle of that chain, and the card's
        # `flex: 1` would have nothing to grow into — the failure mode the
        # old `calc(100vh - 380px)` was papering over.
        rx.box(
            territory_selector(),
            display="flex", flex_direction="column",
            flex="1 1 360px", min_width="0", min_height="0", height="100%",
            padding="1rem",
            border_right="1px solid #E5E7EB",
        ),
        _scroll_column(
            rx.cond(
                AppState.batch_running | AppState.batch_done,
                status_panel(),
                rx.box(),
            ),
            config_panel(),
            howto_panel(),
            flex="1.6 1 460px", min_width="0", height="100%",
        ),
        id="batch-wide-body",
        display=_WIDE_ONLY,
        width="100%", height="100%",
        align_items="stretch",
        wrap="wrap",
        overflow="hidden",
    )


def _narrow_body() -> rx.Component:
    """Below "md": exactly one stage, chosen by ``batch_stage_effective``.

    A run in flight pins this to the Run stage on its own — see that var — so
    starting a job always shows its progress without any handler having to
    navigate, and nobody lands back on a selector whose result is already
    committed.
    """
    return rx.box(
        rx.match(
            AppState.batch_stage_effective,
            ("configure", _scroll_column(config_panel(), height="100%")),
            ("run", _scroll_column(_run_stage(), height="100%")),
            _scroll_column(_select_stage(), height="100%"),
        ),
        id="batch-narrow-body",
        display=_NARROW_ONLY,
        flex_direction="column",
        width="100%", height="100%",
        min_height="0",
        overflow="hidden",
    )


def _action_bar() -> rx.Component:
    """Start / Stop / Download, pinned to the bottom at every breakpoint.

    On desktop this is what stops the primary action from sitting below 26
    configuration controls; on a phone it also puts it within thumb reach. The
    selected-count badge rides alongside so the number the Start button is
    about to act on is never off-screen either.
    """
    return rx.hstack(
        rx.badge(
            AppState.batch_selected_count.to(str) + "/"
            + AppState.batch_max_selection.to(str),
            color_scheme=rx.cond(AppState.batch_selected_count > 0, "orange", "gray"),
            variant="soft", size="2", flex_shrink="0",
        ),
        rx.box(action_panel(), flex="1", min_width="0"),
        width="100%",
        align_items="center",
        spacing="3",
        padding="0.6rem 1rem",
        bg="white",
        border_top=f"2px solid {ORANGE_BORDER}",
        box_shadow="0 -2px 12px rgba(0, 0, 0, 0.08)",
        flex_shrink="0",
    )


def _error_toast() -> rx.Component:
    return rx.cond(
        AppState.error_message != "",
        rx.box(
            rx.hstack(
                rx.icon("alert-circle", color="red", size=16),
                rx.text(AppState.error_message, font_size="sm"),
                rx.spacer(),
                rx.button(
                    "✕", on_click=AppState.clear_error,
                    size="1", variant="ghost",
                ),
                width="100%", align_items="center",
            ),
            padding="0.75rem 1rem",
            bg="red.50",
            border="1px solid red",
            border_radius="md",
            position="fixed",
            # Above the action bar, not under it.
            bottom="5rem",
            right="1rem",
            z_index="9999",
            max_width="min(420px, calc(100vw - 2rem))",
        ),
        rx.box(),
    )


def batch_processing_page() -> rx.Component:
    """Full batch processing page layout.

    Viewport-locked, like the analysis workspace: ``100dvh`` (``vh`` on mobile
    browsers includes the collapsing URL bar, which would put the action bar
    permanently under the chrome), ``overflow: hidden``, and every scrolling
    region owning its own scroller.
    """
    return rx.vstack(
        batch_navbar(),
        stage_bar(),
        rx.box(
            _wide_body(),
            _narrow_body(),
            flex="1", min_height="0", width="100%",
            overflow="hidden",
        ),
        _action_bar(),
        _error_toast(),
        citation_modal(),
        review_selection_modal(),
        width="100vw",
        height=["100dvh", "100dvh", "100dvh", "100vh"],
        spacing="0",
        align_items="stretch",
        overflow="hidden",
        bg="#F9FAFB",
    )
