"""Finding and choosing a protected area: the search box, the overlap
chooser, the provinces shown, and the parts of the selected area.

One field reads a protected-area name, a coordinate, a postal code or an
address, and **says how it read the input** before acting (the suite-wide
"read as" line). A name selects the area; a place only frames the map and
drops a pin.
"""

from __future__ import annotations

import reflex as rx

from ..state import CanadaState as S
from .layout import BORDER, MUTED, section

_ECHO_COLOR = {"postal": "cyan", "coordenada": "blue", "territorio": "teal",
               "lugar": "gray", "erro": "red"}
_PRECISION_COLOR = {"endereco": "grass", "rua": "grass", "cep": "cyan",
                    "bairro": "amber", "cidade": "amber", "regiao": "gray",
                    "lugar": "gray"}

#: Provinces/territories with a CPCAD file, for the "add" picker.
CA_PROVINCES = [
    ("AB", "Alberta"), ("BC", "British Columbia"), ("MB", "Manitoba"),
    ("NB", "New Brunswick"), ("NL", "Newfoundland and Labrador"),
    ("NS", "Nova Scotia"), ("NT", "Northwest Territories"), ("NU", "Nunavut"),
    ("ON", "Ontario"), ("PE", "Prince Edward Island"), ("QC", "Quebec"),
    ("SK", "Saskatchewan"), ("YT", "Yukon"),
]


def _row(*children, on_click) -> rx.Component:
    return rx.box(
        rx.vstack(*children, spacing="1", align_items="start", width="100%"),
        on_click=on_click, padding="2", border=BORDER,
        border_radius="var(--radius-2)", cursor="pointer", width="100%",
        _hover={"background": "var(--gray-3)"},
    )


def _echo_line() -> rx.Component:
    return rx.cond(
        S.echo,
        rx.hstack(
            rx.text(S.tr["search_read_as"], size="1", color=MUTED, flex_shrink="0"),
            rx.badge(S.echo, size="1", variant="soft",
                     color_scheme=rx.match(S.echo_kind,
                                           *[(k, v) for k, v in _ECHO_COLOR.items()],
                                           "gray"),
                     style={"whiteSpace": "normal", "height": "auto",
                            "maxWidth": "100%"}),
            spacing="2", align="center", width="100%", wrap="wrap",
        ),
    )


def _precision_badge(precision) -> rx.Component:
    return rx.badge(
        rx.match(precision, *[(k, S.tr[f"precision_{k}"]) for k in _PRECISION_COLOR],
                 S.tr["precision_lugar"]),
        size="1", variant="soft", flex_shrink="0",
        color_scheme=rx.match(precision, *[(k, v) for k, v in _PRECISION_COLOR.items()],
                              "gray"),
    )


def search_panel() -> rx.Component:
    return section(
        S.tr["search_title"],
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=14)),
                placeholder=S.tr["search_placeholder"],
                value=S.query, on_change=S.set_query,
                on_key_down=lambda key: rx.cond(key == "Enter", S.submit_search,
                                                rx.noop()),
                size="2", width="100%",
            ),
            rx.cond(S.query,
                    rx.icon_button(rx.icon("x", size=14), on_click=S.clear_search,
                                   size="2", variant="soft", color_scheme="gray")),
            spacing="1", width="100%",
        ),
        _echo_line(),
        rx.button(
            rx.cond(S.searching | S.searching_place, S.tr["search_button_busy"],
                    S.tr["search_button"]),
            on_click=S.submit_search, disabled=S.searching | S.searching_place,
            size="2", width="100%",
        ),
        rx.cond(S.search_error,
                rx.callout(S.search_error, icon="triangle-alert",
                           color_scheme="amber", size="1")),
        rx.cond(S.parcel_error,
                rx.callout(S.parcel_error, icon="info", color_scheme="gray", size="1")),
        rx.cond(
            S.area_hits,
            rx.vstack(
                rx.text(S.tr["search_areas_heading"], size="1", weight="medium",
                        color=MUTED),
                rx.foreach(S.area_hits, lambda k: _row(
                    rx.text(k, size="1", weight="medium"),
                    on_click=S.choose_area(k))),
                spacing="1", width="100%",
            ),
        ),
        rx.cond(
            S.place_hits,
            rx.vstack(
                rx.text(S.tr["search_places_heading"], size="1", weight="medium",
                        color=MUTED),
                rx.foreach(S.place_hits, lambda p, i: _row(
                    rx.hstack(rx.text(p["title"], size="1", weight="medium"),
                              rx.spacer(), _precision_badge(p["precision"]),
                              spacing="2", align="start", width="100%"),
                    rx.cond(p["subtitle"], rx.text(p["subtitle"], size="1", color=MUTED)),
                    on_click=S.choose_place(i))),
                rx.text(S.tr["search_places_note"], size="1", color=MUTED),
                rx.text(S.place_attribution, size="1", color=MUTED),
                spacing="1", width="100%",
            ),
        ),
    )


def candidate_chooser() -> rx.Component:
    """Several protected areas under one click — common, since designations
    nest. Smallest first; the user picks, nothing is decided for them."""
    return rx.cond(
        S.candidates,
        rx.vstack(
            rx.text(S.tr["candidates_note"], size="1", weight="medium"),
            rx.foreach(S.candidates, lambda c: _row(
                rx.text(c["name"], size="1", weight="medium"),
                rx.hstack(rx.text(f"{c['area_ha']} ha", size="1", weight="bold"),
                          rx.text(c["designation"], size="1", color=MUTED),
                          spacing="2", wrap="wrap"),
                on_click=S.choose_candidate(c["key"]))),
            spacing="2", width="100%",
        ),
    )


def provinces_panel() -> rx.Component:
    return section(
        S.tr["provinces_title"],
        rx.hstack(
            rx.foreach(S.ca_provinces,
                       lambda p: rx.badge(p, color_scheme="teal", variant="soft")),
            spacing="1", wrap="wrap", width="100%",
        ),
        rx.select.root(
            rx.select.trigger(placeholder=S.tr["ca_add_province"], width="100%"),
            rx.select.content(*[rx.select.item(f"{name} ({code})", value=code)
                                for code, name in CA_PROVINCES]),
            value="", on_change=S.add_ca_province, size="1",
        ),
        rx.text(S.tr["ca_provinces_hint"], size="1", color=MUTED),
        rx.text(S.tr["ca_ocap_note"], size="1", color="#0F766E"),
        rx.text(S.tr["ca_source_note"], size="1", color=MUTED),
    )


def parts_panel() -> rx.Component:
    """Pick which separate polygons of the selected area to analyse."""
    row = lambda p: rx.hstack(
        rx.checkbox(checked=S.ca_part_pick.contains(p["id"]),
                    on_change=lambda _v: S.toggle_ca_part(p["id"]), size="1"),
        rx.text(p["label"], size="1", flex="1"),
        rx.icon_button(rx.icon("zoom-in", size=12), on_click=S.zoom_to_ca_part(p["id"]),
                       size="1", variant="ghost", color_scheme="teal",
                       aria_label=S.tr["ca_parts_zoom"]),
        spacing="2", align="center", width="100%",
    )
    return rx.cond(
        S.ca_parts_total > 1,
        section(
            S.tr["ca_parts_title"],
            rx.text(S.ca_parts_status, size="1", color="#0F766E"),
            rx.text(S.tr["ca_parts_hint"], size="1", color=MUTED),
            rx.hstack(
                rx.button(S.tr["ca_parts_apply"], " (", S.ca_part_pick_count, ")",
                          on_click=S.apply_ca_parts, disabled=S.ca_part_pick_count == 0,
                          size="1", color_scheme="teal"),
                rx.button(S.tr["ca_parts_all"], on_click=S.analyse_all_ca_parts,
                          disabled=S.ca_parts_applied.length() == 0,
                          size="1", variant="soft", color_scheme="teal"),
                rx.button(S.tr["ca_parts_clear"], on_click=S.clear_ca_part_pick,
                          size="1", variant="ghost", color_scheme="gray"),
                spacing="1", wrap="wrap",
            ),
            rx.box(rx.vstack(rx.foreach(S.ca_parts, row), spacing="0", width="100%"),
                   max_height="240px", overflow_y="auto", width="100%",
                   border=BORDER, border_radius="var(--radius-2)", padding="1"),
            rx.cond(S.ca_parts_more_note,
                    rx.text(S.ca_parts_more_note, size="1", color=MUTED)),
        ),
    )
