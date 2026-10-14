"""The "Find a place" box at the top of both sidebars (and the mobile sheet).

One field takes a CEP, a Canadian postal code, a coordinate, a territory name
or a street address / place, and **says how it read the input** before acting
— the line that stops a transposed coordinate pair from quietly resolving
somewhere plausible and wrong. Ported in spirit from the sibling apps' search
(camposcope/naturametrics ``components/search.py``); see
``utils/place_search.py`` for the resolver order.
"""

from __future__ import annotations

import reflex as rx

from ..state import AppState

_ECHO_COLOR = {"cep": "cyan", "postal": "cyan", "coordenada": "blue",
               "territorio": "purple", "lugar": "gray", "erro": "red"}

#: Precision → badge colour: a street-level hit is a pin, a town-level one
#: only a framed area, and the two must not look alike.
_PRECISION_COLOR = {
    "endereco": "grass", "rua": "grass", "cep": "cyan", "bairro": "amber",
    "cidade": "amber", "regiao": "gray", "lugar": "gray",
}


def _row(*children, on_click) -> rx.Component:
    return rx.box(
        rx.vstack(*children, spacing="1", align_items="start", width="100%"),
        on_click=on_click,
        padding="6px 8px",
        border="1px solid var(--gray-5)",
        border_radius="var(--radius-2)",
        cursor="pointer",
        width="100%",
        _hover={"background": "var(--gray-3)"},
    )


def _precision_badge(precision) -> rx.Component:
    return rx.badge(
        rx.match(precision,
                 *[(k, AppState.tr[f"ps_precision_{k}"]) for k in _PRECISION_COLOR],
                 AppState.tr["ps_precision_lugar"]),
        size="1", variant="soft", flex_shrink="0",
        color_scheme=rx.match(precision,
                              *[(k, v) for k, v in _PRECISION_COLOR.items()],
                              "gray"),
    )


def place_search() -> rx.Component:
    return rx.vstack(
        rx.text(AppState.tr["ps_title"], font_size="xs", font_weight="700",
                color="gray", text_transform="uppercase", letter_spacing="0.06em"),
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=14)),
                placeholder=AppState.tr["ps_placeholder"],
                value=AppState.place_query,
                on_change=AppState.set_place_query,
                on_key_down=lambda key: rx.cond(
                    key == "Enter", AppState.submit_place_search, rx.noop()),
                size="2",
                width="100%",
            ),
            rx.cond(
                AppState.place_query,
                rx.icon_button(
                    rx.icon("x", size=14),
                    on_click=AppState.clear_place_search,
                    size="2", variant="soft", color_scheme="gray",
                    aria_label=AppState.tr["ps_clear_aria"],
                ),
                rx.fragment(),
            ),
            spacing="1",
            width="100%",
        ),
        rx.cond(
            AppState.place_echo,
            rx.hstack(
                rx.text(AppState.tr["ps_read_as"], font_size="xs", color="gray",
                        flex_shrink="0"),
                rx.badge(
                    AppState.place_echo, size="1", variant="soft",
                    color_scheme=rx.match(
                        AppState.place_echo_kind,
                        *[(k, v) for k, v in _ECHO_COLOR.items()], "gray"),
                    style={"whiteSpace": "normal", "height": "auto",
                           "maxWidth": "100%"},
                ),
                spacing="2", align="center", width="100%", wrap="wrap",
            ),
            rx.fragment(),
        ),
        rx.button(
            rx.cond(AppState.place_searching, AppState.tr["ps_button_busy"],
                    AppState.tr["ps_button"]),
            on_click=AppState.submit_place_search,
            disabled=AppState.place_searching,
            size="2", width="100%", color_scheme="green",
        ),
        rx.cond(
            AppState.place_error,
            rx.callout(AppState.place_error, icon="triangle-alert",
                       color_scheme="amber", size="1", width="100%"),
            rx.fragment(),
        ),
        rx.cond(
            AppState.place_territory_hits,
            rx.vstack(
                rx.text(AppState.tr["ps_territories_heading"], font_size="xs",
                        color="gray", font_weight="500"),
                rx.foreach(
                    AppState.place_territory_hits,
                    lambda name: _row(
                        rx.text(name, font_size="sm", font_weight="500"),
                        on_click=AppState.choose_place_territory(name),
                    ),
                ),
                spacing="1", width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            AppState.place_hits,
            rx.vstack(
                rx.text(AppState.tr["ps_places_heading"], font_size="xs",
                        color="gray", font_weight="500"),
                rx.foreach(
                    AppState.place_hits,
                    lambda p, i: _row(
                        rx.hstack(
                            rx.text(p["title"], font_size="sm", font_weight="500"),
                            rx.spacer(),
                            _precision_badge(p["precision"]),
                            spacing="2", align="start", width="100%",
                        ),
                        rx.cond(p["subtitle"],
                                rx.text(p["subtitle"], font_size="xs", color="gray"),
                                rx.fragment()),
                        on_click=AppState.choose_place(i),
                    ),
                ),
                rx.text(AppState.tr["ps_places_note"], font_size="xs", color="gray"),
                rx.text(AppState.place_attribution, font_size="xs", color="gray"),
                spacing="1", width="100%",
            ),
            rx.fragment(),
        ),
        spacing="2",
        align="stretch",
        width="100%",
        padding="0.75rem 0.75rem 0.5rem",
        border_bottom="1px solid var(--gray-5)",
    )


def howto_dialog() -> rx.Component:
    """The full guide the quick-start card hands over to — the same
    Getting-Started steps as the sidebar's Help group, reachable from the
    navbar on any screen size (on a phone the sidebar's Help group sits at the
    bottom of the sheet)."""
    from .tutorial import tutorial_steps

    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(AppState.tr["ps_howto_title"]),
            rx.scroll_area(
                tutorial_steps(),
                type="auto", scrollbars="vertical",
                style={"maxHeight": "62vh", "paddingRight": "0.75rem"},
            ),
            rx.flex(
                rx.button(
                    rx.icon("rocket", size=14),
                    AppState.tr["help_show_quickstart"],
                    size="2", variant="ghost", color_scheme="gray",
                    on_click=AppState.reset_quickstart,
                ),
                rx.spacer(),
                # A plain button driving state, not rx.dialog.close — the
                # sibling apps found Dialog.Close's asChild cloning never
                # reaches a button Reflex extracted into its own component.
                rx.button(AppState.tr["ps_close"], size="2", variant="soft",
                          on_click=AppState.set_howto_open(False)),
                align="center", margin_top="1rem", wrap="wrap", gap="2",
            ),
            max_width=["94vw", "94vw", "640px", "640px"],
        ),
        open=AppState.howto_open,
        on_open_change=AppState.set_howto_open,
    )


def howto_trigger() -> rx.Component:
    return rx.icon_button(
        rx.icon("circle-help", size=16),
        on_click=AppState.set_howto_open(True),
        size="1", variant="ghost", color_scheme="green",
        aria_label=AppState.tr["ps_howto_title"],
        title=AppState.tr["ps_howto_title"],
    )
