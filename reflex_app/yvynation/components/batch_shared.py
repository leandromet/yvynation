"""
Shared visual building blocks for the batch-processing page
(pages/batch_processing.py and the components/batch_*.py modules).
"""

import reflex as rx

ORANGE = "#EA580C"
ORANGE_LIGHT = "#FFF7ED"
ORANGE_BORDER = "#FDBA74"
ORANGE_DARK = "#C2410C"


def _section_card(*children, **box_props) -> rx.Component:
    return rx.box(
        rx.vstack(*children, spacing="3", width="100%"),
        padding="1.25rem",
        bg="white",
        border_radius="xl",
        border=f"1px solid #e5e7eb",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        width="100%",
        **box_props,
    )


def _label(text: str) -> rx.Component:
    return rx.text(text, font_size="xs", font_weight="600", color="#374151",
                   text_transform="uppercase", letter_spacing="0.05em")


def _step_badge(n: int, label: str, active: bool = False) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(str(n), font_size="xs", font_weight="700", color="white"),
            bg=ORANGE if active else "#9CA3AF",
            border_radius="full",
            width="1.4rem", height="1.4rem",
            display="flex", align_items="center", justify_content="center",
        ),
        rx.text(label, font_size="sm",
                color=ORANGE if active else "#6B7280",
                font_weight="600" if active else "400"),
        align_items="center", spacing="2",
    )


def multi_select_dropdown(
    label: str,
    options,
    selected,
    on_toggle,
    accent: str = "orange",
) -> rx.Component:
    """Popover-based multi-select checkbox filter (e.g. UF, category, stage).

    Renders nothing when ``options`` is empty — callers don't need to wrap
    type-specific filters (e.g. a conservation-only field) in their own
    visibility check when the other territory type is active alone.
    """
    return rx.cond(
        options.length() > 0,
        rx.popover.root(
            rx.popover.trigger(
                rx.button(
                    rx.hstack(
                        rx.text(label, font_size="xs"),
                        rx.cond(
                            selected.length() > 0,
                            rx.badge(selected.length().to(str), size="1",
                                     color_scheme=accent, variant="solid"),
                            rx.box(),
                        ),
                        rx.icon("chevron-down", size=12),
                        spacing="1", align_items="center",
                    ),
                    size="1",
                    variant="outline",
                    color_scheme=rx.cond(selected.length() > 0, accent, "gray"),
                    cursor="pointer",
                ),
            ),
            rx.popover.content(
                rx.vstack(
                    rx.foreach(
                        options,
                        lambda opt: rx.hstack(
                            rx.checkbox(
                                checked=selected.contains(opt),
                                on_change=lambda _: on_toggle(opt),
                                color_scheme=accent,
                                size="1",
                            ),
                            rx.text(
                                opt, font_size="xs", cursor="pointer",
                                on_click=lambda: on_toggle(opt),
                            ),
                            spacing="2", align_items="center", width="100%",
                        ),
                    ),
                    spacing="1", width="100%",
                    max_height="260px", overflow_y="auto",
                    padding="0.25rem",
                ),
                size="2",
            ),
        ),
        rx.box(),
    )
