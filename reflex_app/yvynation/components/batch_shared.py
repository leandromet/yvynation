"""
Shared visual building blocks for the batch-processing page
(pages/batch_processing.py and the components/batch_*.py modules).
"""

import reflex as rx

from ..state import AppState

ORANGE = "#EA580C"
ORANGE_LIGHT = "#FFF7ED"
ORANGE_BORDER = "#FDBA74"
ORANGE_DARK = "#C2410C"


def _section_card(*children, fill: bool = False, **box_props) -> rx.Component:
    """A white card. ``fill=True`` makes it a flex column that fills its
    parent, so a child marked ``flex="1"`` stretches to the space left over.

    The inner vstack needs the height too, not just the box: it is the flex
    container the children actually live in, and without a definite height of
    its own it sizes to content and a `flex: 1` child has nothing to grow
    into. That is what let the territory list get away with a hard-coded
    ``calc(100vh - 380px)`` for so long.
    """
    inner = {"flex": "1", "min_height": "0", "height": "100%"} if fill else {}
    outer = {
        "padding": "1.25rem",
        "bg": "white",
        "border_radius": "var(--radius-4)",
        "border": "1px solid #e5e7eb",
        "box_shadow": "0 1px 4px rgba(0,0,0,0.06)",
        "width": "100%",
    }
    if fill:
        outer |= {"display": "flex", "flex_direction": "column", "min_height": "0"}
    # Merged, not double-splatted: a caller passing its own `min_height`
    # alongside `fill=True` would otherwise be a duplicate-keyword TypeError
    # rather than an override.
    outer |= box_props
    return rx.box(
        rx.vstack(*children, spacing="3", width="100%", **inner),
        **outer,
    )


def _label(text: str) -> rx.Component:
    return rx.text(text, font_size="xs", font_weight="600", color="#374151",
                   text_transform="uppercase", letter_spacing="0.05em")


def _step_badge(n: int, label, active, *, on_click=None,
                enabled=True) -> rx.Component:
    """One numbered stage in ``stage_bar()``.

    ``active`` and ``enabled`` take Reflex Vars, not plain bools — this used
    to be a pure-Python helper with `bool` defaults, which is why it sat
    unused since it was written: a stage indicator has to react to state,
    and a Python `if` cannot.
    """
    return rx.hstack(
        rx.box(
            rx.text(str(n), font_size="xs", font_weight="700", color="white"),
            bg=rx.cond(active, ORANGE, "#9CA3AF"),
            border_radius="9999px",
            width="1.4rem", height="1.4rem", flex_shrink="0",
            display="flex", align_items="center", justify_content="center",
        ),
        rx.text(
            label,
            font_size="sm",
            white_space="nowrap",
            color=rx.cond(active, ORANGE, "#6B7280"),
            font_weight=rx.cond(active, "600", "400"),
        ),
        on_click=on_click,
        cursor=rx.cond(enabled, "pointer", "default"),
        opacity=rx.cond(enabled, "1", "0.45"),
        align_items="center", spacing="2", flex_shrink="0",
        padding="0.3rem 0.6rem",
        border_radius="md",
        border=rx.cond(active, f"1px solid {ORANGE_BORDER}", "1px solid transparent"),
        bg=rx.cond(active, ORANGE_LIGHT, "transparent"),
        # Unconditional: `_hover` is a nested style dict, and an `rx.cond`
        # returning one is not a string swap the compiler can inline the way
        # the props above are. A faint hover on a stage that is already at
        # 0.45 opacity and has no click handler reads as inert anyway.
        _hover={"bg": ORANGE_LIGHT},
    )


def stage_bar() -> rx.Component:
    """Select → Configure → Run, the page's spine.

    The batch page is a job builder, not a workspace: there is a sequence to
    follow and it was previously implied only by where things happened to sit
    in two columns. Naming the three stages is what lets a phone show one at
    a time (pages/batch_processing.py::_narrow_body) instead of a single
    scroll holding a 3,000-row list, 26 controls and a progress log.

    "Run" stays disabled until a job exists — it has nothing to show
    otherwise — and becomes the only reachable stage while one is in flight,
    which `AppState.batch_stage_effective` enforces on the state side.
    """
    has_run = AppState.batch_running | AppState.batch_done
    return rx.hstack(
        _step_badge(
            1, AppState.tr["batch_stage_select"],
            AppState.batch_stage_effective == "select",
            on_click=AppState.set_batch_stage("select"),
            enabled=~has_run,
        ),
        rx.icon("chevron-right", size=14, color="#D1D5DB", flex_shrink="0"),
        _step_badge(
            2, AppState.tr["batch_stage_configure"],
            AppState.batch_stage_effective == "configure",
            on_click=AppState.set_batch_stage("configure"),
            enabled=~has_run,
        ),
        rx.icon("chevron-right", size=14, color="#D1D5DB", flex_shrink="0"),
        _step_badge(
            3, AppState.tr["batch_stage_run"],
            AppState.batch_stage_effective == "run",
            on_click=rx.cond(has_run, AppState.set_batch_stage("run"), rx.noop()),
            enabled=has_run,
        ),
        role="tablist",
        aria_label=AppState.tr["batch_step_label"],
        width="100%",
        align_items="center",
        spacing="1",
        padding="0.4rem 1rem",
        bg="white",
        border_bottom="1px solid #E5E7EB",
        flex_shrink="0",
        # Three stages plus two chevrons still exceed a 390px phone once the
        # labels are translated ("Configurar", "Configuration"). Scroll the
        # row rather than wrapping it into two lines above every screen.
        overflow_x="auto",
    )


def batch_groups_root(*groups: rx.Component) -> rx.Component:
    """The configuration accordion (components/batch_config_panel.py).

    Mirrors ``components/layout.py::sidebar_groups_root`` but binds to
    ``batch_config_groups``, so opening a group here cannot reach across and
    change the analysis page's sidebar.
    """
    return rx.accordion.root(
        *groups,
        type="multiple",
        collapsible=True,
        variant="surface",
        width="100%",
        color_scheme="orange",
        value=AppState.batch_config_groups,
        on_value_change=AppState.set_batch_config_groups,
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
