"""Start/stop/download controls for the batch-processing page.

Lives in the bar pinned to the bottom of the viewport
(pages/batch_processing.py::_action_bar), so everything here has to read as
the page's primary action at a glance rather than as one more row of
controls — it is the only thing down there.
"""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, ORANGE_DARK


def large_run_warning() -> rx.Component:
    """Soft warning shown above the start button for oversized selections.

    Never blocks the run — just nudges the user toward splitting large jobs
    into a few smaller ones, which keeps peak memory bounded per run.
    """
    return rx.cond(
        AppState.batch_is_large_run & ~AppState.batch_busy & ~AppState.batch_done,
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


def _no_selection_hint() -> rx.Component:
    """Says *why* Start does nothing yet.

    A disabled button explains nothing — the run needs at least one
    territory, and until this the only signal was that clicking had no
    effect. Tapping the hint goes to the Select stage, which is where the
    answer is (and on a phone that stage is not even on screen).
    """
    return rx.hstack(
        rx.icon("info", size=15, color="#92400E", flex_shrink="0"),
        rx.text(
            AppState.tr["batch_no_selection_hint"],
            font_size="xs", color="#92400E", flex="1",
        ),
        rx.icon("chevron-right", size=14, color="#92400E", flex_shrink="0"),
        on_click=AppState.set_batch_stage("select"),
        cursor="pointer",
        padding="0.55rem 0.75rem",
        bg="#FFFBEB",
        border="1px solid #FDE68A",
        border_radius="md",
        align_items="center",
        spacing="2",
        width="100%",
        _hover={"bg": "#FEF3C7"},
    )


def _start_button() -> rx.Component:
    """The page's primary action, and styled to look like it.

    A ring and a coloured shadow, not just a filled background: this sits in
    a bar at the bottom of the viewport with nothing around it to give it
    weight, and the plain fill read as chrome rather than as the thing to
    press.
    """
    return rx.button(
        rx.icon("play", size=16),
        rx.text(
            AppState.tr["batch_start_btn"] + " ("
            + AppState.batch_selected_count.to(str)
            + " " + AppState.tr["territories_word"] + ")",
        ),
        on_click=AppState.request_batch_run,
        size="3",
        bg=ORANGE,
        color="white",
        font_weight="bold",
        _hover={"bg": ORANGE_DARK, "transform": "translateY(-1px)"},
        box_shadow=f"0 2px 10px {ORANGE}59, 0 0 0 3px {ORANGE}26",
        transition="transform 120ms ease, box-shadow 120ms ease",
        cursor="pointer",
        width="100%",
    )


def _starting_button() -> rx.Component:
    """The gap between the click and the progress bar.

    `run_batch_processing` snapshots the configuration and then awaits two
    abuse-control checks before it sets `batch_running`, which took seconds
    in practice. With nothing on screen changing, that read as a click that
    had not registered — and a second click started a genuine second run,
    producing two identical ZIPs seconds apart. `batch_starting` closes that
    window on the state side; this is the half the user can see.
    """
    return rx.hstack(
        rx.button(
            rx.spinner(size="2"),
            rx.text(AppState.tr["batch_starting_label"], font_weight="bold"),
            is_disabled=True,
            size="3",
            bg=ORANGE,
            color="white",
            opacity="0.85",
            flex="1",
        ),
        # Stop is mounted here too, not only once `batch_running` is set.
        # Partly so these seconds are cancellable like the rest of the run,
        # and partly as the escape hatch if anything ever strands
        # `batch_starting`: `batch_stop` clears it, so the page can always be
        # recovered without a reload.
        rx.button(
            AppState.tr["batch_stop_btn"],
            on_click=AppState.batch_stop,
            size="2",
            variant="outline",
            color_scheme="red",
            flex_shrink="0",
        ),
        width="100%", align_items="center", spacing="2",
    )


def action_panel() -> rx.Component:
    return rx.vstack(
        large_run_warning(),
        rx.hstack(
            # Idle: either the reason Start is unavailable, the confirm step,
            # or Start itself.
            rx.cond(
                ~AppState.batch_busy & ~AppState.batch_done,
                rx.cond(
                    AppState.batch_selected_count == 0,
                    _no_selection_hint(),
                    rx.cond(
                        AppState.batch_confirm_pending,
                        _start_confirm(),
                        _start_button(),
                    ),
                ),
                rx.box(),
            ),

            # Dispatched, not yet reporting progress.
            rx.cond(
                AppState.batch_starting,
                _starting_button(),
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
