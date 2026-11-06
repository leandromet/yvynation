"""A "More" menu for a navbar that has run out of room.

The bar keeps the controls a reader switches often (the country, the language,
the analysis itself); the rest (How to use, Cite, Export, Back to portal, Clear)
sit behind one button. Each item is a state event, the same one the button it
replaces used.
"""

from __future__ import annotations

import reflex as rx


def header_menu(label, items) -> rx.Component:
    """``items`` is a list of ``(text, event)``: a text (string or Var) and the event
    it fires (an event spec or a lambda)."""
    return rx.menu.root(
        rx.menu.trigger(
            rx.button(
                rx.icon("ellipsis", size=16),
                rx.text(label, display=["none", "none", "block", "block"]),
                size="1", variant="soft", color_scheme="gray",
                aria_label=label,
            ),
        ),
        rx.menu.content(
            *[rx.menu.item(text, on_click=event) for text, event in items],
            align="end",
        ),
    )
