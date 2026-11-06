"""The Brazil / Canada region toggle, shared by both pages' headers.

Brazil and Canada are separate pages with their own data, sidebars and
results (the Canada page is ``yvynation/canada/``), so switching region is
**navigation**, not a state change — each segment is a plain link, the current
region is the highlighted one and is not clickable. The language travels in the
URL (``/fr/``, ``/canada/fr/``…), so a French reader does not land in English.

It is the only control in either header that carries a country flag; the
language controls are plain text (EN / PT / FR) so a flag never means two
things at once.
"""

from __future__ import annotations

import reflex as rx

from ..utils.language_routes import ALL_LANGS, TOOLS


def tool_href(base: str, language):
    """The link to a country tool in a language: ``/pt/``, ``/canada/fr/``, ``/usa/en/``.

    ``language`` is a plain string or a state Var. A tool that lacks the language
    (the USA page has no Spanish or French) links to its English page.
    """
    prefix = "" if base == "/" else base
    supported = TOOLS[base]
    if isinstance(language, str):
        code = language if language in supported else "en"
        return f"{prefix}/{code}/"
    if set(supported) == set(ALL_LANGS):
        return f"{prefix}/{language}/"
    cases = [(code, f"{prefix}/{code}/") for code in supported if code != "en"]
    return rx.match(language, *cases, f"{prefix}/en/")


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


def region_toggle(current: str, *, language, names, goto, aria_label,
                  accent: str = "green") -> rx.Component:
    """The Brazil / Canada / USA switch. ``current`` is ``"brazil"``, ``"canada"`` or
    ``"usa"``: the page you are on shows its own name, and the other two read
    "Go to …" (``goto``) and are links. ``names`` and ``goto`` are the three
    ``(brazil, canada, usa)`` labels, strings or Vars. Plain text, no flags: the
    language switch beside it is plain text too, so the two never look alike.
    ``language`` is the page's language Var (the link is that language's page,
    see ``tool_href``)."""
    hrefs = {"brazil": tool_href("/", language), "canada": tool_href("/canada", language),
             "usa": tool_href("/usa", language)}
    segments = [
        _segment(flag="", label=names[i] if region == current else goto[i],
                 href=None if region == current else hrefs[region],
                 active=region == current, accent=accent)
        for i, region in enumerate(("brazil", "canada", "usa"))
    ]
    return rx.hstack(
        *segments,
        role="navigation", aria_label=aria_label,
        spacing="1", align="center", flex_shrink="0",
        padding="2px",
        background="var(--gray-3)",
        border="1px solid var(--gray-6)",
        border_radius="var(--radius-3)",
    )
