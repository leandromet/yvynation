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
            # Returns to whichever page opened this one — going back to the
            # portal from batch would drop a configured selection.
            rx.button(
                rx.cond(
                    AppState.previous_runs_return_to == "batch",
                    AppState.tr["back_to_batch"],
                    AppState.tr["back_to_portal"],
                ),
                on_click=AppState.leave_previous_runs,
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


def _kv_row(item: rx.Var) -> rx.Component:
    """One label/value line in the detail panel."""
    return rx.hstack(
        rx.text(item["label"], font_size="xs", color="#6B7280",
                width="140px", flex_shrink="0"),
        rx.text(item["value"], font_size="xs", color="#374151"),
        spacing="2", align_items="flex-start", width="100%",
    )


def _territory_row(t: rx.Var) -> rx.Component:
    ok = t["status"] == "ok"
    return rx.hstack(
        rx.text(rx.cond(ok, "✅", "❌"), font_size="xs", flex_shrink="0"),
        rx.text(t["name"], font_size="xs", font_weight="600",
                color=rx.cond(ok, "#166534", "#991B1B"), flex_shrink="0"),
        rx.text(t["detail"], font_size="xs", color="#6B7280"),
        spacing="2", align_items="flex-start", width="100%",
    )


def _copy_link(label: rx.Var, url: rx.Var) -> rx.Component:
    """A selectable link with a copy button. The bucket is not necessarily
    public, so this is for the user to paste into gsutil / the console — it is
    not how the Download button works."""
    return rx.hstack(
        rx.text(label, font_size="xs", color="#6B7280",
                width="70px", flex_shrink="0"),
        rx.box(
            rx.text(url, font_size="xs", font_family="monospace",
                    color="#374151", word_break="break-all"),
            flex="1", padding="0.25rem 0.5rem", bg="#F3F4F6",
            border="1px solid #E5E7EB", border_radius="sm",
            user_select="all",
        ),
        rx.button(
            "📋", size="1", variant="ghost", color_scheme="gray",
            on_click=lambda: AppState.copy_bucket_link(url),
            title=AppState.tr["previous_runs_copy"],
            flex_shrink="0",
        ),
        spacing="2", align_items="center", width="100%",
    )


def _section(title: rx.Var, body: rx.Component) -> rx.Component:
    return rx.vstack(
        rx.text(title, font_size="xs", font_weight="700",
                color=ORANGE_DARK, text_transform="uppercase",
                letter_spacing="0.05em"),
        body,
        spacing="1", width="100%", align_items="flex-start",
    )


def _run_details(run: rx.Var) -> rx.Component:
    """Expanded panel: bucket links plus whatever the run's own
    batch_summary.json / batch_report.md records."""
    return rx.box(
        rx.cond(
            AppState.previous_runs_detail_busy == run["name"],
            rx.hstack(
                rx.spinner(size="1"),
                rx.text(AppState.tr["previous_runs_detail_loading"],
                        font_size="xs", color="gray"),
                spacing="2", align_items="center", padding="0.5rem 0",
            ),
            rx.vstack(
                # ── Bucket links (finished archives only) ──
                rx.cond(
                    run["bucket_url"] != "",
                    _section(
                        AppState.tr["previous_runs_bucket_section"],
                        rx.vstack(
                            _copy_link("HTTPS", run["bucket_url"]),
                            _copy_link("gs://", run["gs_uri"]),
                            rx.text(AppState.tr["previous_runs_bucket_hint"],
                                    font_size="xs", color="#9CA3AF"),
                            spacing="1", width="100%",
                        ),
                    ),
                    rx.fragment(),
                ),

                # ── Run configuration ──
                rx.cond(
                    AppState.previous_runs_detail_config.length() > 0,
                    _section(
                        AppState.tr["previous_runs_detail_config"],
                        rx.vstack(rx.foreach(AppState.previous_runs_detail_config, _kv_row),
                                  spacing="0", width="100%"),
                    ),
                    rx.fragment(),
                ),

                # ── Territories ──
                rx.cond(
                    AppState.previous_runs_detail_territories.length() > 0,
                    _section(
                        AppState.tr["previous_runs_detail_territories"],
                        rx.vstack(rx.foreach(AppState.previous_runs_detail_territories, _territory_row),
                                  spacing="0", width="100%"),
                    ),
                    rx.fragment(),
                ),

                # ── Performance (runs from the parallel pipeline onward) ──
                rx.cond(
                    AppState.previous_runs_detail_perf.length() > 0,
                    _section(
                        AppState.tr["previous_runs_detail_performance"],
                        rx.vstack(
                            rx.foreach(AppState.previous_runs_detail_perf, _kv_row),
                            rx.cond(
                                AppState.previous_runs_detail_verdict != "",
                                rx.text(AppState.previous_runs_detail_verdict, font_size="xs",
                                        color="#92400E", bg="#FEF3C7",
                                        padding="0.4rem 0.6rem",
                                        border_radius="sm", width="100%"),
                                rx.fragment(),
                            ),
                            spacing="1", width="100%",
                        ),
                    ),
                    rx.fragment(),
                ),

                # ── Fallback: raw report, or why there is nothing to show ──
                rx.cond(
                    AppState.previous_runs_detail_report != "",
                    rx.box(
                        rx.text(AppState.previous_runs_detail_report, font_size="xs",
                                font_family="monospace", white_space="pre-wrap",
                                color="#374151"),
                        width="100%", max_height="220px", overflow_y="auto",
                        bg="#F9FAFB", border="1px solid #E5E7EB",
                        border_radius="sm", padding="0.5rem",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    AppState.previous_runs_detail_message != "",
                    rx.text(AppState.previous_runs_detail_message, font_size="xs", color="#9CA3AF"),
                    rx.fragment(),
                ),

                spacing="3", width="100%", align_items="flex-start",
            ),
        ),
        width="100%",
        padding="0.75rem 1rem 1rem 1rem",
        bg="#FFFBF5",
        border="1px solid #E5E7EB",
        border_top="none",
        border_radius="0 0 6px 6px",
    )


def _run_row(run: rx.Var) -> rx.Component:
    is_busy = AppState.previous_runs_busy == run["name"]
    is_open = AppState.previous_runs_expanded == run["name"]
    header = rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(rx.cond(is_open, "▾", "▸"), font_size="sm", color=ORANGE),
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
            # Only the name/meta block toggles the panel — the buttons to the
            # right must not open it as a side effect of being clicked.
            on_click=lambda: AppState.toggle_run_details(run["name"], run["kind"]),
            cursor="pointer",
            flex="1",
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
        border_radius=rx.cond(is_open, "6px 6px 0 0", "6px"),
        align_items="center",
        spacing="3",
    )

    return rx.vstack(
        header,
        rx.cond(is_open, _run_details(run), rx.fragment()),
        spacing="0", width="100%",
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
