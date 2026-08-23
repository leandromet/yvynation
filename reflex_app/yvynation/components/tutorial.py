"""
Tutorial component for Yvynation Reflex app.
Bilingual Getting Started guide with 7 collapsible steps.
"""

import reflex as rx
from ..state import AppState


def _tutorial_step(
    title_key: str,
    intro_key: str,
    content_key: str,
    step_index: int,
) -> rx.Component:
    """A single collapsible tutorial step with translated content."""
    return rx.box(
        rx.button(
            rx.hstack(
                rx.text(
                    rx.cond(
                        AppState.tutorial_expanded_steps.contains(step_index),
                        "v",
                        ">",
                    ),
                    font_size="xs",
                    width="14px",
                    font_family="monospace",
                ),
                rx.text(
                    AppState.tr[title_key],
                    font_weight="600",
                    font_size="sm",
                ),
                width="100%",
                align_items="center",
                spacing="2",
            ),
            on_click=lambda: AppState.toggle_tutorial_step(step_index),
            width="100%",
            size="1",
            variant="ghost",
            padding="0.5rem 0.75rem",
        ),
        rx.cond(
            AppState.tutorial_expanded_steps.contains(step_index),
            rx.box(
                rx.vstack(
                    rx.text(
                        AppState.tr[intro_key],
                        font_weight="500",
                        font_size="sm",
                        color="gray",
                    ),
                    rx.markdown(
                        AppState.tr[content_key],
                        component_map={
                            "p": lambda text: rx.text(text, font_size="sm", margin_bottom="0.5rem"),
                        },
                    ),
                    spacing="2",
                    width="100%",
                ),
                padding="0.5rem 1rem 0.75rem 1.5rem",
                border_left="3px solid #4ade80",
                margin_left="0.5rem",
            ),
            rx.box(),
        ),
        width="100%",
        border_bottom="1px solid #f0f0f0",
    )


def tutorial_section() -> rx.Component:
    """Complete Getting Started tutorial with collapsible steps."""
    return rx.box(
        # Main collapsible header
        rx.button(
            rx.hstack(
                rx.icon("book-open", size=16, color="green"),
                rx.text(
                    AppState.tr["getting_started_header"],
                    font_weight="600",
                    font_size="md",
                ),
                rx.spacer(),
                rx.text(
                    rx.cond(AppState.show_tutorial, "v", ">"),
                    font_size="xs",
                    color="gray",
                    font_family="monospace",
                ),
                width="100%",
                align_items="center",
                spacing="2",
            ),
            on_click=AppState.toggle_tutorial,
            width="100%",
            variant="ghost",
            padding="0.75rem 1rem",
        ),
        rx.cond(
            AppState.show_tutorial,
            rx.box(
                rx.vstack(
                    # Intro text
                    rx.box(
                        rx.vstack(
                            rx.heading(
                                AppState.tr["getting_started_title"],
                                size="3",
                            ),
                            rx.text(
                                AppState.tr["getting_started_intro"],
                                font_size="sm",
                                color="gray",
                            ),
                            spacing="1",
                        ),
                        padding="0.5rem 1rem",
                    ),
                    # Steps
                    _tutorial_step("step_language_region", "step0_language_region_intro", "step0_content", 0),
                    _tutorial_step("step_custom_polygon", "step1_draw_intro", "step1_content", 1),
                    _tutorial_step("step_territory", "step2_territory_intro", "step2_content", 2),
                    _tutorial_step("step_comparison", "step3_comparison_intro", "step3_content", 3),
                    _tutorial_step("step_export", "step4_export_intro", "step4_content", 4),
                    _tutorial_step("step_map_controls", "step5_map_controls_intro", "step5_content", 5),
                    _tutorial_step("step_data_understanding", "step6_data_understanding_intro", "step6_content", 6),
                    spacing="0",
                    width="100%",
                ),
                padding="0.25rem 0",
            ),
            rx.box(),
        ),
        width="100%",
        border="1px solid #e0e0e0",
        border_radius="md",
        bg="white",
        margin_bottom="0.5rem",
    )
