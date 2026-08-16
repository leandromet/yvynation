"""Selected-territories review panel for the batch-processing page.

Lets you see (and remove) everything currently checked across BOTH
territory types in one place, since the list view only ever shows one
type at a time (see AppState.batch_set_territory_type).
"""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE_BORDER


def _review_row(item: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.badge(
            rx.cond(item["type"] == "conservation", "🌿", "🪶"),
            color_scheme=rx.cond(item["type"] == "conservation", "green", "orange"),
            variant="soft", size="1", flex_shrink="0",
        ),
        rx.vstack(
            rx.text(item["name"], font_size="sm", font_weight="500"),
            rx.text(
                rx.cond(item["uf"] != "", item["uf"] + "   ", "")
                + rx.cond(item["ha"] != "", "📐 " + item["ha"] + " ha", ""),
                font_size="xs", color="#6B7280",
            ),
            spacing="0", align_items="flex-start", flex="1",
        ),
        rx.button(
            "✕",
            on_click=AppState.batch_toggle_territory(item["name"]),
            size="1", variant="ghost", color_scheme="red",
        ),
        width="100%", align_items="center", spacing="2",
        padding="0.35rem 0.5rem", border_radius="md",
        _hover={"bg": "#FEF3C7"},
    )


def review_selection_modal() -> rx.Component:
    """Floating panel listing every selected territory, toggled by AppState.batch_show_review."""
    return rx.cond(
        AppState.batch_show_review,
        rx.box(
            # Backdrop
            rx.box(
                on_click=AppState.batch_toggle_review,
                position="fixed", top="0", left="0",
                width="100vw", height="100vh",
                bg="rgba(0,0,0,0.45)", z_index="9998",
            ),
            # Panel
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading(AppState.tr["batch_review_title"], size="4", color="#1a472a"),
                        rx.spacer(),
                        rx.badge(
                            AppState.batch_selected_count.to(str) + "/"
                            + AppState.batch_max_selection.to(str),
                            color_scheme="orange", variant="soft",
                        ),
                        rx.button(
                            "✕", on_click=AppState.batch_toggle_review,
                            size="1", variant="ghost",
                        ),
                        width="100%", align_items="center",
                    ),
                    rx.divider(border_color=ORANGE_BORDER),
                    rx.cond(
                        AppState.batch_selected_count == 0,
                        rx.text(
                            AppState.tr["batch_review_empty"],
                            font_size="sm", color="#6B7280",
                        ),
                        rx.box(
                            rx.foreach(AppState.batch_selected_territories_detail, _review_row),
                            width="100%",
                            max_height="50vh",
                            overflow_y="auto",
                            border="1px solid #e5e7eb",
                            border_radius="lg",
                            padding="0.5rem",
                        ),
                    ),
                    rx.hstack(
                        rx.cond(
                            AppState.batch_selected_count > 0,
                            rx.button(
                                AppState.tr["clear_all"],
                                on_click=AppState.batch_clear_selection,
                                size="1", variant="outline", color_scheme="red",
                            ),
                            rx.box(),
                        ),
                        rx.spacer(),
                        rx.button(
                            AppState.tr["batch_review_close"],
                            on_click=AppState.batch_toggle_review,
                            size="2", color_scheme="orange",
                        ),
                        width="100%", align_items="center",
                    ),
                    spacing="3", align_items="flex-start", width="100%",
                ),
                position="fixed", top="50%", left="50%",
                transform="translate(-50%, -50%)",
                bg="white", padding="1.5rem", border_radius="lg",
                box_shadow="0 12px 40px rgba(0,0,0,0.25)",
                width="min(560px, 92vw)",
                max_height="80vh", overflow_y="auto",
                z_index="9999",
            ),
        ),
        rx.fragment(),
    )
