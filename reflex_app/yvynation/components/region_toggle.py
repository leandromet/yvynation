"""The Brazil / Canada region toggle, shared by both pages' headers.

Brazil and Canada are separate pages with their own data, sidebars and
results (the Canada page is ``yvynation/canada/``), so switching region is
**navigation**, not a state change — each segment is a plain link, the current
region is the highlighted one and is not clickable. The language travels in the
URL (``?lang=``), which both pages honour, so a French reader does not land in
English.

It is the only control in either header that carries a country flag; the
language controls are plain text (EN / PT / FR) so a flag never means two
things at once.
"""

from __future__ import annotations

import reflex as rx

#: Below this breakpoint only the flag shows: a phone header has no room for
#: two labelled segments beside the title, help, cite and language controls.
_LABEL_DISPLAY = ["none", "none", "inline", "inline"]


def _segment(*, flag: str, label, href: str | None, active: bool,
             accent: str) -> rx.Component:
    inner = rx.hstack(
        rx.text(flag, font_size="0.95rem", line_height="1"),
        rx.text(label, size="1", weight="medium", display=_LABEL_DISPLAY),
        spacing="1", align="center",
    )
    common = dict(
        padding="3px 10px",
        border_radius="var(--radius-2)",
        display="flex", align_items="center",
    )
    if active:
        return rx.box(
            inner, aria_current="page",
            background=f"var(--{accent}-9)", color="white",
            box_shadow="0 1px 2px rgba(0,0,0,0.2)", **common,
        )
    return rx.link(
        rx.box(
            inner,
            color="var(--gray-11)", cursor="pointer",
            _hover={"background": "var(--gray-4)", "color": "var(--gray-12)"},
            **common,
        ),
        href=href, underline="none",
    )


def region_toggle(current: str, *, language, labels, aria_label,
                  accent: str = "green") -> rx.Component:
    """``current`` is ``"brazil"`` or ``"canada"``. ``language`` is the page's
    language Var (appended to the link as ``?lang=``); ``labels`` is a
    ``(brazil, canada)`` pair of strings or Vars."""
    brazil_label, canada_label = labels
    return rx.hstack(
        _segment(flag="🇧🇷", label=brazil_label, href=f"/?lang={language}",
                 active=current == "brazil", accent=accent),
        _segment(flag="🇨🇦", label=canada_label, href=f"/canada?lang={language}",
                 active=current == "canada", accent=accent),
        role="navigation", aria_label=aria_label,
        spacing="1", align="center", flex_shrink="0",
        padding="2px",
        background="var(--gray-3)",
        border="1px solid var(--gray-6)",
        border_radius="var(--radius-3)",
    )
