"""Right column (middle): progress bar, current step, and live log."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, _label, _section_card


def _log_line(line: str) -> rx.Component:
    return rx.text(line, font_size="xs", font_family="monospace",
                   color=rx.cond(
                       line.startswith("  ✅"),
                       "#16A34A",
                       rx.cond(line.startswith("  ❌"), "#DC2626", "#374151"),
                   ))


def _active_row(row: dict) -> rx.Component:
    """One in-flight territory and the step it is currently on."""
    return rx.hstack(
        rx.box(width="80px", flex_shrink="0"),
        rx.text(row["territory"], font_size="sm", font_weight="600",
                color="#111827", no_of_lines=1),
        rx.text(row["step"], font_size="xs", color="#6B7280", no_of_lines=1),
        spacing="2", align_items="center", width="100%",
    )


def _starting_notice() -> rx.Component:
    """Shown between dispatch and the first progress tick.

    `run_batch_processing` snapshots the configuration and awaits two
    abuse-control checks before it sets `batch_running`, so there is a real
    gap during which the progress bar reads 0% with nothing happening. Saying
    what is going on is the difference between "it's working on it" and "my
    click did nothing" — and the latter is what produced a second click, and
    two identical ZIPs.
    """
    return rx.cond(
        AppState.batch_starting,
        rx.hstack(
            rx.spinner(size="2", color=ORANGE),
            rx.text(AppState.tr["batch_starting_hint"], font_size="sm",
                    color="#92400E"),
            padding="0.6rem 0.75rem",
            bg="#FFFBEB",
            border="1px solid #FDE68A",
            border_radius="md",
            align_items="center", spacing="2", width="100%",
        ),
        rx.box(),
    )


def status_panel() -> rx.Component:
    """Progress bar, current step, and scrollable log."""
    return _section_card(
        _starting_notice(),
        # Header + progress percentage
        rx.hstack(
            rx.heading(AppState.tr["batch_progress"], size="3", color="#1a472a"),
            rx.spacer(),
            rx.text(
                AppState.batch_progress_pct.to(str) + "%",
                font_size="xl", font_weight="700",
                color=rx.cond(AppState.batch_done, "#16A34A", ORANGE),
            ),
            width="100%", align_items="center",
        ),

        # Progress bar
        rx.box(
            rx.box(
                width=AppState.batch_progress_pct.to(str) + "%",
                height="100%",
                bg=rx.cond(AppState.batch_done, "#16A34A", ORANGE),
                border_radius="full",
                transition="width 0.4s ease",
            ),
            width="100%", height="10px",
            bg="#F3F4F6", border_radius="full", overflow="hidden",
        ),

        # Territory / step labels
        rx.cond(
            AppState.batch_running | AppState.batch_done,
            rx.vstack(
                # While running, several territories are processed at once, so
                # there is no single "current" one — list every worker's slot.
                # Once done the list is empty and the completion label shows.
                rx.cond(
                    AppState.batch_done,
                    rx.hstack(
                        rx.text(AppState.tr["batch_territory_label"], font_size="xs",
                                color="#6B7280", width="80px"),
                        rx.text(
                            AppState.tr["batch_complete_label"],
                            font_size="sm", font_weight="600", color="#16A34A",
                        ),
                        spacing="2", align_items="center",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text(AppState.tr["batch_in_flight_label"], font_size="xs",
                                    color="#6B7280", width="80px"),
                            rx.badge(
                                AppState.batch_active_rows.length().to(str),
                                color_scheme="orange", variant="soft", size="1",
                            ),
                            spacing="2", align_items="center",
                        ),
                        rx.foreach(AppState.batch_active_rows, _active_row),
                        spacing="1", width="100%", align_items="flex-start",
                    ),
                ),
                rx.hstack(
                    rx.text(AppState.tr["batch_done_label"], font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        AppState.batch_completed.length().to(str)
                        + " / "
                        + AppState.batch_total.to(str)
                        + rx.cond(
                            AppState.batch_failed.length() > 0,
                            " (" + AppState.batch_failed.length().to(str) + AppState.tr["batch_errors_suffix"],
                            "",
                        ),
                        font_size="sm", color="#374151",
                    ),
                    spacing="2", align_items="center",
                ),
                spacing="1", width="100%",
            ),
            rx.box(),
        ),

        # Live log
        rx.cond(
            AppState.batch_log.length() > 0,
            rx.vstack(
                _label(AppState.tr["batch_processing_log"]),
                rx.box(
                    rx.vstack(
                        rx.foreach(AppState.batch_log, _log_line),
                        spacing="0",
                        width="100%",
                        align_items="flex-start",
                    ),
                    width="100%",
                    height="200px",
                    overflow_y="auto",
                    bg="#F9FAFB",
                    border="1px solid #E5E7EB",
                    border_radius="md",
                    padding="0.75rem",
                ),
                width="100%", spacing="1",
            ),
            rx.box(),
        ),
    )
