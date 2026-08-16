"""Right column (bottom): explanation of the batch module and usage guide."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, _section_card


def _howto_step(n: int, title: str, body: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(str(n), font_size="sm", font_weight="700", color="white"),
            bg=ORANGE,
            border_radius="full",
            min_width="1.6rem", height="1.6rem",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(title, font_size="sm", font_weight="600", color="#111827"),
            rx.text(body, font_size="xs", color="#4B5563", line_height="1.5"),
            spacing="1", align_items="flex-start",
        ),
        spacing="3", align_items="flex-start", width="100%",
    )


def howto_panel() -> rx.Component:
    """Explanation of the batch module and a step-by-step usage guide."""
    return _section_card(
        rx.hstack(
            rx.heading(AppState.tr["batch_about_title"], size="3", color="#1a472a"),
            width="100%", align_items="center",
        ),
        rx.text(
            AppState.tr["batch_about_text"],
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.hstack(
            rx.icon("clock", size=14, color=ORANGE),
            rx.text(
                AppState.tr["batch_time_note"],
                font_size="xs", color="#6B7280", line_height="1.5",
            ),
            spacing="2", align_items="flex-start",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.accordion.root(
            rx.accordion.item(
                header=rx.text(
                    AppState.tr["batch_howto"],
                    font_size="xs", font_weight="600", color="#374151",
                    text_transform="uppercase", letter_spacing="0.05em",
                ),
                content=rx.vstack(
                    _howto_step(
                        1,
                        AppState.tr["batch_howto_1_title"],
                        AppState.tr["batch_howto_1_body"],
                    ),
                    _howto_step(
                        2,
                        AppState.tr["batch_howto_2_title"],
                        AppState.tr["batch_howto_2_body"],
                    ),
                    _howto_step(
                        3,
                        AppState.tr["batch_howto_3_title"],
                        AppState.tr["batch_howto_3_body"],
                    ),
                    _howto_step(
                        4,
                        AppState.tr["batch_howto_4_title"],
                        AppState.tr["batch_howto_4_body"],
                    ),
                    _howto_step(
                        5,
                        AppState.tr["batch_howto_5_title"],
                        AppState.tr["batch_howto_5_body"],
                    ),
                    _howto_step(
                        6,
                        AppState.tr["batch_howto_6_title"],
                        AppState.tr["batch_howto_6_body"],
                    ),
                    _howto_step(
                        7,
                        AppState.tr["batch_howto_7_title"],
                        AppState.tr["batch_howto_7_body"],
                    ),
                    spacing="3", width="100%", padding_top="0.75rem",
                ),
                value="howto",
            ),
            type="single",
            collapsible=True,
            default_value=None,
            variant="ghost",
            width="100%",
            color_scheme="orange",
        ),
    )
