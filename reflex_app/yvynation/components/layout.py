"""Shared layout vocabulary for the analysis workspace.

The three sibling apps keep the same things in the same file — see
``camposcope/components/layout.py`` and
``naturametrics/components/layout.py``. This module holds what
``pages/index.py`` and the two sidebars both need, so neither imports
chrome from the other.

What used to live here was ``main_page()``, an early sidebar+map layout that
nothing imported any more and that carried a ``calc(300vh - 160px)`` content
column — one of the three impossible heights this pass removed.
"""

import reflex as rx

from ..state import AppState

#: Yvynation's own hue. Used only through Radix's colour scales
#: (``var(--green-9)`` and friends), which are defined for every scale
#: regardless of the theme's chosen accent — so the new chrome can be
#: accent-coloured without setting ``theme=`` on the app and shifting every
#: existing control's colour.
ACCENT = "green"

MUTED = "var(--gray-11)"
BORDER = "1px solid var(--gray-5)"

#: The navbar's fixed height. The workspace below it is ``flex: 1`` of what
#: is left, so this is the only vertical number the shell needs.
HEADER_H = "70px"


def info_icon(text) -> rx.Component:
    """A tap/click affordance, not a hover tooltip.

    Ported from camposcope's ``components/layout.py::_info_icon``, which in
    turn came from naturametrics. The hints in this app were HTML ``title=``
    attributes, which do not exist on touch at all — a phone user could not
    reach them.
    """
    return rx.popover.root(
        rx.popover.trigger(
            rx.icon_button(
                rx.icon("info", size=12),
                size="1", variant="ghost", color_scheme="gray",
                aria_label=text,
            ),
        ),
        rx.popover.content(
            rx.text(text, size="1", style={"lineHeight": "1.4"}),
            max_width="260px",
        ),
    )


def group(value: str, icon: str, title, *sections: rx.Component,
          badge: rx.Component = None) -> rx.Component:
    """One collapsible cluster of related sidebar sections.

    Ported from ``naturametrics/components/layer_panel.py::_group``.
    ``variant="surface"`` on the enclosing root (see the two sidebars) draws
    a bordered card per group, so the grouping reads as a visible boundary
    rather than one more divider in a flat list — which is the whole point
    of grouping six previously-flat sections.

    ``padding_x="0"`` on the content: Radix's own AccordionContent bakes in
    ``padding_x: var(--space-4)`` (16px), which stacks on top of the
    sidebar's own padding and squeezes every control inward on a ~300px
    panel.

    Each group is one accordion *item*; which ones are open is driven by
    ``AppState.open_groups`` at the root, not by Radix's uncontrolled state,
    so the backend can force a group open (``AppState._open_group``) while
    ordinary user toggles still flow straight through.

    ``badge`` rides in the trigger row so an active-layer count stays
    readable while the group is closed — the flat sections this replaced
    carried those counts on their own headers, and folding three sections
    into one group would otherwise hide them.
    """
    body = []
    for i, section in enumerate(sections):
        if i:
            body.append(rx.divider())
        body.append(section)
    trigger_row = [
        rx.icon(icon, size=15),
        rx.text(title, size="2", weight="bold"),
    ]
    if badge is not None:
        trigger_row.append(badge)
    return rx.accordion.item(
        rx.accordion.header(
            rx.accordion.trigger(
                rx.hstack(*trigger_row, spacing="2", align="center"),
            ),
        ),
        rx.accordion.content(
            rx.vstack(*body, spacing="3", width="100%", padding_top="0.25rem"),
            padding_x="0",
        ),
        value=value,
    )


def sidebar_shell(*children: rx.Component) -> rx.Component:
    """The common wrapper both sidebars put their groups in.

    The ``--font-size-*`` overrides shrink every ``size="1"/"2"/"3"`` control
    in the panel by 3px at once, relative to the inherited value rather than
    a hard-coded px, so it stays correct if the theme's scaling ever changes.
    Same fix camposcope's ``_sidebar()`` and naturametrics' ``layer_panel()``
    apply, and for the same reason: a sidebar of real controls reads as
    cramped at the default size once it holds more than placeholders.
    """
    return rx.vstack(
        *children,
        width="100%",
        spacing="2",
        padding="0.5rem",
        align_items="stretch",
        style={
            "--font-size-1": "calc(var(--font-size-1) - 3px)",
            "--font-size-2": "calc(var(--font-size-2) - 3px)",
            "--font-size-3": "calc(var(--font-size-3) - 3px)",
        },
    )


def sidebar_groups_root(*groups: rx.Component) -> rx.Component:
    """The controlled accordion both sidebars hang their groups off.

    ``type="multiple"`` — more than one group can be open at a time, which
    the six sections this replaced could not manage: they were driven by
    only four booleans, so opening "MapBiomas layers" also opened "Analysis
    settings" (and in the geometry sidebar, three sections shared one
    boolean between them).
    """
    return rx.accordion.root(
        *groups,
        type="multiple",
        collapsible=True,
        variant="surface",
        width="100%",
        value=AppState.open_groups,
        on_value_change=AppState.set_open_groups,
    )
