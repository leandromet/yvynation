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
                    rx.heading(AppState.tr["app_title"], size="3"),
                    rx.text("•", color=ORANGE, font_weight="bold"),
                    rx.text(
                        AppState.tr["batch_title"],
                        font_size="sm", color=ORANGE_DARK, font_weight="600",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.text(
                    AppState.tr["batch_nav_subtitle"],
                    font_size="xs", color="#6B7280",
                ),
                spacing="0",
            ),
            spacing="3", align_items="center",
        ),
        rx.spacer(),
        language_selector(),
        rx.button(
            "📂 " + AppState.tr["previous_runs_title"],
            on_click=AppState.go_to_previous_runs,
            size="1", variant="outline", color_scheme="orange",
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
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)",
        border_bottom=f"3px solid {ORANGE_BORDER}",
        align_items="center",
        width="100%",
        height="70px",
        position="sticky",
        top="0",
        z_index="100",
    )
