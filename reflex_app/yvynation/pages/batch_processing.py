"""
Batch Processing page for Yvynation.

Lets users select multiple indigenous territories and/or conservation units,
configure analysis years and options, and kick off a full automated analysis
run. All results are packaged into a single ZIP archive — no charts are
rendered during processing.

Layout pieces live in components/batch_*.py:
  batch_shared.py             shared style tokens + the multi-select filter widget
  batch_territory_selector.py left column — type/area/attribute filters + list
  batch_config_panel.py       right column — years/options/buffer
  batch_status_panel.py       right column — progress bar + live log
  batch_howto_panel.py        right column — usage guide accordion
  batch_action_panel.py       start/stop/download controls
  batch_navbar.py             sticky top navbar
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


def batch_processing_page() -> rx.Component:
    """Full batch processing page layout."""
    return rx.vstack(
        batch_navbar(),

        # Main two-column layout
        rx.box(
            rx.hstack(
                # ── Left: territory selector (40%) ──
                rx.box(
                    territory_selector(),
                    width="38%",
                    min_width="300px",
                    padding="1rem",
                    height="calc(100vh - 70px)",
                    overflow_y="auto",
                ),

                # ── Divider ──
                rx.divider(orientation="vertical", border_color="#E5E7EB"),

                # ── Right: config + status + actions (60%) ──
                rx.box(
                    rx.vstack(
                        # Config (hidden while running)
                        rx.cond(
                            ~AppState.batch_running & ~AppState.batch_done,
                            config_panel(),
                            rx.box(),
                        ),

                        # Status (visible once started)
                        rx.cond(
                            AppState.batch_running | AppState.batch_done,
                            status_panel(),
                            rx.box(),
                        ),

                        # Action buttons
                        action_panel(),

                        # How-to / explanation (always visible — fills the
                        # empty space below the ~1/3-height progress area)
                        howto_panel(),

                        spacing="4",
                        width="100%",
                    ),
                    width="62%",
                    padding="1rem",
                    height="calc(100vh - 70px)",
                    overflow_y="auto",
                ),

                width="100%",
                height="calc(100vh - 70px)",
                spacing="0",
                align_items="stretch",
            ),
            width="100%",
            flex="1",
        ),

        # Error toast (re-use from index)
        rx.cond(
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
                bottom="1rem",
                right="1rem",
                z_index="9999",
                max_width="420px",
            ),
            rx.box(),
        ),

        citation_modal(),
        review_selection_modal(),

        width="100%",
        height="100vh",
        spacing="0",
        bg="#F9FAFB",
    )
