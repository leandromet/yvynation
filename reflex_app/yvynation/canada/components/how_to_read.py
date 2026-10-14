""""How to read this" — a short, plain-language key under every tab.

Each figure on the page encodes something specific (stacked shares per year,
a flow between two years, loss split at a date, a ratio against a reference
product) and none of that is obvious from the chart alone. One block per tab,
open by default and collapsible, says what each axis, colour, row and map
layer means, and what the figure cannot tell you. Text lives in the
translation tables under ``read_<tab>``.
"""

from __future__ import annotations

import reflex as rx

from ..state import CanadaState as S
from .layout import MUTED


def how_to_read(key: str) -> rx.Component:
    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.header(
                rx.accordion.trigger(
                    rx.hstack(
                        rx.icon("book-open", size=13),
                        rx.text(S.tr["how_to_read"], size="1", weight="bold"),
                        spacing="2", align="center",
                    ),
                ),
            ),
            rx.accordion.content(
                rx.text(S.tr[f"read_{key}"], size="1", color=MUTED,
                        line_height="1.55", white_space="pre-line"),
            ),
            value="read",
        ),
        type="single", collapsible=True, default_value="read",
        variant="ghost", width="100%",
        background="var(--teal-2)", border_radius="var(--radius-2)",
    )
