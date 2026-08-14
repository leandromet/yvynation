"""
Previous Runs page for Yvynation Reflex app.

Lists everything sitting in the exports directory: finished batch/export
ZIPs, plus any leftover run folder from an interrupted or crashed run (see
utils/export_service.list_export_runs — a folder without a matching ZIP is
never auto-deleted, specifically so it can be recovered here). In
production the exports directory is GCS-backed (see CLOUD_RUN_DEPLOYMENT.md
/ project memory project_yvynation_citation... see also the batch OOM fix
notes), so this page keeps working across container restarts.
"""

import reflex as rx

from ..state import AppState
from ..components.language_selector import language_selector

ORANGE = "#EA580C"
ORANGE_DARK = "#C2410C"


def previous_runs_navbar() -> rx.Component:
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
                        AppState.tr["previous_runs_title"],
                        font_size="sm", color=ORANGE_DARK, font_weight="600",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.text(
                    AppState.tr["previous_runs_subtitle"],
                    font_size="xs", color="#6B7280",
                ),
                spacing="0",
            ),
            spacing="3", align_items="center",
        ),
        rx.spacer(),
        language_selector(),
        rx.button(
            "🔄 " + AppState.tr["previous_runs_refresh"],
            on_click=AppState.load_previous_runs,
            size="2", variant="outline", color_scheme="orange",
        ),
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)",
        border_bottom=f"3px solid {ORANGE}",
        align_items="center",
        width="100%",
        height="70px",
        position="sticky",
        top="0",
        z_index="100",
    )


def _status_badge(kind: rx.Var) -> rx.Component:
    return rx.cond(
        kind == "zip",
        rx.badge(AppState.tr["previous_runs_status_zip"], color_scheme="green", variant="soft"),
        rx.badge(AppState.tr["previous_runs_status_partial"], color_scheme="orange", variant="soft"),
    )


def _run_row(run: rx.Var) -> rx.Component:
    is_busy = AppState.previous_runs_busy == run["name"]
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(run["name"], font_size="sm", font_weight="600", color="#1F2937"),
                _status_badge(run["kind"]),
                spacing="2", align_items="center",
            ),
            rx.hstack(
                rx.text(run["time_label"], font_size="xs", color="gray"),
                rx.text("·", color="gray"),
                rx.text(run["size_label"], font_size="xs", color="gray"),
                rx.cond(
                    run["kind"] != "zip",
                    rx.hstack(
                        rx.text("·", color="gray"),
                        rx.text(
                            run["file_count"].to_string() + " " + AppState.tr["previous_runs_files_suffix"],
                            font_size="xs", color="gray",
                        ),
                        spacing="1",
                    ),
                    rx.fragment(),
                ),
                spacing="1", align_items="center",
            ),
            spacing="0", align_items="flex-start",
        ),
        rx.spacer(),
        rx.cond(
            run["kind"] == "zip",
            rx.button(
                "⬇️ " + AppState.tr["previous_runs_download"],
                on_click=lambda: AppState.download_previous_run(run["relpath"]),
                size="1", bg="#16A34A", color="white", font_weight="bold",
                _hover={"bg": "#15803D"},
            ),
            rx.button(
                rx.cond(
                    is_busy,
                    rx.hstack(rx.spinner(size="1"), rx.text(AppState.tr["previous_runs_zipping"]),
                              spacing="2", align_items="center"),
                    rx.text("🗜 " + AppState.tr["previous_runs_zip_download"]),
                ),
                on_click=lambda: AppState.zip_and_download_run(run["name"]),
                is_disabled=is_busy,
                size="1", bg=ORANGE, color="white", font_weight="bold",
                _hover={"bg": ORANGE_DARK},
            ),
        ),
        rx.button(
            "🗑",
            on_click=lambda: AppState.delete_previous_run(run["name"], run["kind"]),
            is_disabled=is_busy,
            size="1", variant="ghost", color_scheme="red",
            title=AppState.tr["previous_runs_delete"],
        ),
        width="100%",
        padding="0.85rem 1rem",
        bg="white",
        border="1px solid #E5E7EB",
        border_radius="md",
        align_items="center",
        spacing="3",
    )


def previous_runs_list() -> rx.Component:
    return rx.cond(
        AppState.previous_runs.length() > 0,
        rx.vstack(
            rx.foreach(AppState.previous_runs, _run_row),
            spacing="2", width="100%",
        ),
        rx.box(
            rx.vstack(
                rx.icon("folder-open", size=32, color="#9CA3AF"),
                rx.text(AppState.tr["previous_runs_empty"], color="gray", font_size="sm"),
                spacing="2", align_items="center",
            ),
            padding="3rem", width="100%", text_align="center",
        ),
    )


def previous_runs_page() -> rx.Component:
    """Full Previous Runs page layout."""
    return rx.vstack(
        previous_runs_navbar(),
        rx.box(
            rx.vstack(
                rx.text(
                    AppState.tr["previous_runs_intro"],
                    font_size="sm", color="#4B5563", line_height="1.7",
                ),
                previous_runs_list(),
                spacing="4",
                padding="2rem 1.5rem",
                width="100%",
                max_width="900px",
                margin="0 auto",
            ),
            width="100%",
            flex="1",
            bg="#F9FAFB",
            overflow_y="auto",
        ),
        width="100%",
        height="100vh",
        spacing="0",
    )
