"""Sticky top navbar for the batch-processing page."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, ORANGE_BORDER, ORANGE_DARK
from .language_selector import language_selector
from .citation import cite_trigger


def batch_navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.button(
                AppState.tr["back_to_portal"],
                on_click=AppState.go_to_portal,
                size="1",
                variant="outline",
                color_scheme="orange",
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(AppState.tr["app_title"], size="3",
                               white_space="nowrap"),
                    rx.text("•", color=ORANGE, font_weight="bold"),
                    rx.text(
                        AppState.tr["batch_title"],
                        font_size="sm", color=ORANGE_DARK, font_weight="600",
                        white_space="nowrap",
                    ),
                    spacing="2", align_items="center",
                ),
                # Hidden below "md": the row has five controls to fit, and on
                # a 390px phone this second line was what tipped the header
                # into wrapping to three lines.
                rx.text(
                    AppState.tr["batch_nav_subtitle"],
                    font_size="xs", color="#6B7280",
                    display=["none", "none", "block", "block"],
                ),
                spacing="0", align_items="flex-start",
            ),
            spacing="3", align_items="center", min_width="0",
        ),
        rx.spacer(),
        language_selector(),
        rx.button(
            rx.text("📂"),
            # Label on tablet and up; the icon alone carries it on a phone.
            rx.text(AppState.tr["previous_runs_title"],
                    display=["none", "none", "block", "block"]),
            on_click=AppState.go_to_previous_runs,
            size="1", variant="outline", color_scheme="orange",
            aria_label=AppState.tr["previous_runs_title"],
        ),
        cite_trigger(color_scheme="orange"),
        rx.cond(
            AppState.batch_done & AppState.batch_zip_ready,
            rx.button(
                AppState.tr["batch_download_zip"],
                on_click=AppState.download_batch_zip,
                size="2",
                bg="#16A34A",
                color="white",
                font_weight="bold",
            ),
            rx.badge(
                rx.cond(
                    AppState.batch_running,
                    AppState.tr["batch_processing_ellipsis"],
                    rx.cond(
                        AppState.batch_selected_count > 0,
                        AppState.batch_selected_count.to(str) + AppState.tr["batch_territories_selected_suffix"],
                        AppState.tr["batch_no_territories"],
                    ),
                ),
                color_scheme=rx.cond(
                    AppState.batch_running,
                    "orange",
                    rx.cond(AppState.batch_selected_count > 0, "green", "gray"),
                ),
                variant="soft",
                size="2",
            ),
        ),
        padding=["0.5rem 0.75rem", "0.5rem 0.75rem", "0.75rem 1.5rem",
                 "0.75rem 1.5rem"],
        bg="linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)",
        border_bottom=f"3px solid {ORANGE_BORDER}",
        align_items="center",
        spacing="2",
        width="100%",
        height="70px",
        # flex_shrink, not position: sticky. The page is a locked 100dvh
        # column now (pages/batch_processing.py) with no document-level
        # scroll left for a sticky element to stick against — but a flex
        # child with content this dense will happily be squashed by its
        # siblings unless told not to.
        flex_shrink="0",
        overflow="hidden",
        z_index="100",
    )
