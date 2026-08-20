"""Start/stop/download controls for the batch-processing page."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, ORANGE_DARK


def large_run_warning() -> rx.Component:
    """Soft warning shown above the start button for oversized selections.

    Never blocks the run — just nudges the user toward splitting large jobs
    into a few smaller ones, which keeps peak memory bounded per run.
    """
    return rx.cond(
        AppState.batch_is_large_run & ~AppState.batch_running & ~AppState.batch_done,
        rx.hstack(
            rx.icon("triangle-alert", size=16, color="#B45309"),
            rx.text(
                AppState.tr["batch_large_run_warning"],
                font_size="xs", color="#92400E",
            ),
            padding="0.5rem 0.75rem",
            bg="#FFFBEB",
            border="1px solid #FDE68A",
            border_radius="md",
            align_items="center",
            spacing="2",
            width="100%",
            margin_bottom="0.5rem",
        ),
        rx.box(),
    )


def _start_confirm() -> rx.Component:
    """Friction step shown after the first click of the Start button — see
    request_batch_run / abuse_control.py. Only ever the UI half; the actual
    enforcement runs server-side inside run_batch_processing regardless of
    whether this was shown."""
    return rx.hstack(
        rx.icon("shield-alert", size=16, color="#92400E"),
        rx.text(AppState.batch_confirm_message, font_size="xs", color="#92400E", flex="1"),
        rx.button(
            AppState.tr["cancel"], on_click=AppState.cancel_batch_run,
            size="2", variant="outline", color_scheme="gray",
        ),
        rx.button(
            AppState.tr["confirm"], on_click=AppState.request_batch_run,
            size="2", bg=ORANGE, color="white", font_weight="bold",
            _hover={"bg": ORANGE_DARK},
        ),
        padding="0.5rem 0.75rem",
        bg="#FFFBEB",
        border="1px solid #FDE68A",
        border_radius="md",
        align_items="center",
        spacing="2",
        width="100%",
    )


def action_panel() -> rx.Component:
    return rx.vstack(
        large_run_warning(),
        rx.hstack(
            # Start button (shown when not running and not done)
            rx.cond(
                ~AppState.batch_running & ~AppState.batch_done,
                rx.cond(
                    AppState.batch_confirm_pending,
                    _start_confirm(),
                    rx.button(
                        rx.cond(
                            AppState.batch_selected_count > 0,
                            AppState.tr["batch_start_btn"] + " ("
                            + AppState.batch_selected_count.to(str)
                            + " " + AppState.tr["territories_word"] + ")",
                            AppState.tr["batch_start_btn"],
                        ),
                        on_click=AppState.request_batch_run,
                        is_disabled=AppState.batch_selected_count == 0,
                        size="3",
                        bg=rx.cond(
                            AppState.batch_selected_count > 0, ORANGE, "#9CA3AF"
                        ),
                        color="white",
                        font_weight="bold",
                        _hover={"bg": ORANGE_DARK},
                        width="100%",
                    ),
                ),
                rx.box(),
            ),

            # Running: spinner + stop button
            rx.cond(
                AppState.batch_running,
                rx.hstack(
                    rx.hstack(
                        rx.spinner(size="2", color=ORANGE),
                        rx.text(AppState.tr["batch_processing_ellipsis"], font_size="sm", font_weight="600",
                                color=ORANGE),
                        spacing="2", align_items="center",
                    ),
                    rx.spacer(),
                    rx.button(
                        AppState.tr["batch_stop_btn"],
                        on_click=AppState.batch_stop,
                        size="2",
                        variant="outline",
                        color_scheme="red",
                    ),
                    width="100%", align_items="center",
                ),
                rx.box(),
            ),

            # Done: download + new batch
            rx.cond(
                AppState.batch_done,
                rx.hstack(
                    rx.button(
                        AppState.tr["batch_download_zip"],
                        on_click=AppState.download_batch_zip,
                        is_disabled=~AppState.batch_zip_ready,
                        size="3",
                        bg="#16A34A",
                        color="white",
                        font_weight="bold",
                        _hover={"bg": "#15803D"},
                        flex="1",
                    ),
                    rx.button(
                        AppState.tr["batch_new_batch"],
                        on_click=AppState.batch_reset,
                        size="3",
                        variant="outline",
                        color_scheme="gray",
                        flex="1",
                    ),
                    width="100%", spacing="3",
                ),
                rx.box(),
            ),

            width="100%",
        ),
        width="100%",
        spacing="0",
    )
