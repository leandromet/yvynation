"""Left column of the batch-processing page: territory type/attribute filters
and the scrollable checkable territory list."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE, ORANGE_DARK, ORANGE_LIGHT, _section_card, multi_select_dropdown


def _type_toggle() -> rx.Component:
    """Indigenous / Conservation source toggle — exclusive, exactly one active at a time.

    The batch *selection* can still span both types — switching the view
    doesn't clear checked territories, it only changes which list you're
    looking at (see ``AppState.batch_set_territory_type``).
    """
    return rx.hstack(
        rx.button(
            AppState.tr["batch_indigenous_btn"],
            on_click=AppState.batch_set_territory_type("indigenous"),
            size="1",
            bg=rx.cond(AppState.batch_territory_types.contains("indigenous"), ORANGE, "white"),
            color=rx.cond(AppState.batch_territory_types.contains("indigenous"), "white", "#6B7280"),
            border=rx.cond(
                AppState.batch_territory_types.contains("indigenous"),
                f"1px solid {ORANGE}", "1px solid #D1D5DB",
            ),
            border_radius="md", flex="1", cursor="pointer",
            _hover={"bg": rx.cond(
                AppState.batch_territory_types.contains("indigenous"), ORANGE_DARK, "#F9FAFB",
            )},
        ),
        rx.button(
            AppState.tr["batch_conservation_btn"],
            on_click=AppState.batch_set_territory_type("conservation"),
            size="1",
            bg=rx.cond(AppState.batch_territory_types.contains("conservation"), "#16A34A", "white"),
            color=rx.cond(AppState.batch_territory_types.contains("conservation"), "white", "#6B7280"),
            border=rx.cond(
                AppState.batch_territory_types.contains("conservation"),
                "1px solid #16A34A", "1px solid #D1D5DB",
            ),
            border_radius="md", flex="1", cursor="pointer",
            _hover={"bg": rx.cond(
                AppState.batch_territory_types.contains("conservation"), "#15803D", "#F9FAFB",
            )},
        ),
        width="100%", spacing="2",
    )


def _area_range_filter() -> rx.Component:
    return rx.hstack(
        rx.text(AppState.tr["batch_area_filter_label"], font_size="xs", color="#6B7280", flex_shrink="0"),
        rx.input(
            placeholder=AppState.tr["batch_min_ha_placeholder"],
            value=AppState.batch_min_area_ha,
            on_change=AppState.batch_set_min_area_ha,
            type="number", min="0", size="1", width="90px",
        ),
        rx.text("–", color="#9CA3AF", flex_shrink="0"),
        rx.input(
            placeholder=AppState.tr["batch_max_ha_placeholder"],
            value=AppState.batch_max_area_ha,
            on_change=AppState.batch_set_max_area_ha,
            type="number", min="0", size="1", width="90px",
        ),
        rx.text(AppState.tr["batch_ha_suffix"], font_size="xs", color="#9CA3AF", flex_shrink="0"),
        rx.cond(
            (AppState.batch_min_area_ha != "") | (AppState.batch_max_area_ha != ""),
            rx.button("✕", on_click=AppState.batch_clear_area_filter,
                      size="1", variant="ghost", color_scheme="gray"),
            rx.box(),
        ),
        width="100%", align_items="center", spacing="2",
    )


def _attribute_filters() -> rx.Component:
    """UF (state) + type-specific attribute dropdowns.

    Each dropdown self-hides when its option list is empty (e.g. the
    conservation-only fields disappear while only indigenous is active),
    so this row adapts automatically to the current type toggle.
    """
    return rx.box(
        multi_select_dropdown(
            AppState.tr["batch_filter_uf_label"],
            AppState.batch_uf_options, AppState.batch_selected_ufs,
            AppState.batch_toggle_uf, accent="gray",
        ),
        multi_select_dropdown(
            AppState.tr["batch_filter_fase_label"],
            AppState.batch_fase_options, AppState.batch_selected_fase,
            AppState.batch_toggle_fase, accent="orange",
        ),
        multi_select_dropdown(
            AppState.tr["batch_filter_modalidade_label"],
            AppState.batch_modalidade_options, AppState.batch_selected_modalidade,
            AppState.batch_toggle_modalidade, accent="orange",
        ),
        multi_select_dropdown(
            AppState.tr["batch_filter_categoria_label"],
            AppState.batch_categoria_options, AppState.batch_selected_categoria,
            AppState.batch_toggle_categoria, accent="green",
        ),
        multi_select_dropdown(
            AppState.tr["batch_filter_esfera_label"],
            AppState.batch_esfera_options, AppState.batch_selected_esfera,
            AppState.batch_toggle_esfera, accent="green",
        ),
        multi_select_dropdown(
            AppState.tr["batch_filter_grupo_label"],
            AppState.batch_grupo_options, AppState.batch_selected_grupo,
            AppState.batch_toggle_grupo, accent="green",
        ),
        rx.cond(
            AppState.batch_has_active_filters,
            rx.button(
                AppState.tr["batch_clear_filters"],
                on_click=AppState.batch_clear_all_filters,
                size="1", variant="ghost", color_scheme="gray",
            ),
            rx.box(),
        ),
        display="flex", flex_wrap="wrap", gap="0.4rem",
        align_items="center", width="100%",
    )


_SORT_OPTIONS = [
    ("name_asc", "batch_sort_name_asc"),
    ("name_desc", "batch_sort_name_desc"),
    ("area_asc", "batch_sort_area_asc"),
    ("area_desc", "batch_sort_area_desc"),
]


def _sort_select() -> rx.Component:
    return rx.select.root(
        rx.select.trigger(placeholder=AppState.tr["batch_sort_label"], size="1", variant="soft"),
        rx.select.content(
            *[rx.select.item(AppState.tr[key], value=value) for value, key in _SORT_OPTIONS],
        ),
        value=AppState.batch_sort_by,
        on_change=AppState.batch_set_sort_by,
    )


def _paste_upload_box() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                AppState.tr["batch_paste_instruction"],
                font_size="xs", color="#6B7280", font_weight="600",
            ),
            rx.text_area(
                placeholder="Apinayé\nApucarana\nBacurizinho\n…",
                value=AppState.batch_paste_text,
                on_change=AppState.batch_set_paste_text,
                width="100%",
                rows="4",
                size="1",
            ),
            rx.hstack(
                rx.button(
                    AppState.tr["batch_select_from_list"],
                    on_click=AppState.batch_select_from_list,
                    size="1",
                    color_scheme="orange",
                ),
                rx.upload(
                    rx.button(
                        AppState.tr["batch_upload_list"],
                        size="1",
                        variant="outline",
                        color_scheme="gray",
                    ),
                    id="batch_list_upload",
                    multiple=False,
                    accept={"text/plain": [".txt"], "text/csv": [".csv"]},
                    on_drop=AppState.batch_upload_territory_list,
                    border="none",
                    padding="0",
                ),
                rx.button(
                    AppState.tr["batch_clear"],
                    on_click=AppState.batch_clear_paste,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                spacing="2",
                align_items="center",
            ),
            rx.cond(
                AppState.batch_paste_feedback != "",
                rx.text(AppState.batch_paste_feedback, font_size="xs", color="#374151"),
                rx.box(),
            ),
            rx.cond(
                AppState.batch_paste_unmatched.length() > 0,
                rx.text(
                    AppState.tr["batch_not_found_prefix"] + AppState.batch_paste_unmatched.join(", "),
                    font_size="xs", color="#B45309",
                ),
                rx.box(),
            ),
            spacing="2", width="100%",
        ),
        padding="0.5rem",
        border="1px dashed #D1D5DB",
        border_radius="md",
        width="100%",
    )


def _territory_row(t: str) -> rx.Component:
    return rx.hstack(
        rx.checkbox(
            checked=AppState.batch_is_territory_selected.get(t, False),
            on_change=lambda _: AppState.batch_toggle_territory(t),
            color_scheme="orange",
        ),
        rx.vstack(
            rx.text(
                t, font_size="sm", cursor="pointer",
                on_click=AppState.batch_toggle_territory(t),
                font_weight="500",
            ),
            rx.text(
                AppState.batch_territory_meta.get(t, ""),
                font_size="xs", color="#6B7280",
                cursor="pointer",
                on_click=AppState.batch_toggle_territory(t),
            ),
            spacing="0", align_items="flex-start", flex="1",
        ),
        rx.cond(
            AppState.batch_territory_uf.get(t, "") != "",
            rx.badge(
                AppState.batch_territory_uf.get(t, ""),
                font_size="xs",
                color_scheme="gray",
                variant="soft",
                flex_shrink="0",
            ),
            rx.box(),
        ),
        width="100%",
        align_items="center",
        spacing="2",
        padding="0.35rem 0.5rem",
        border_radius="md",
        bg=rx.cond(
            AppState.batch_is_territory_selected.get(t, False),
            ORANGE_LIGHT,
            "transparent",
        ),
        _hover={"bg": "#FEF3C7"},
    )


def _filters_disclosure() -> rx.Component:
    """Area range, attribute dropdowns, sorting and the paste/upload box, all
    behind one collapsed disclosure.

    Together they are eight controls plus a four-row text area — taller than
    a phone screen, so before this the list they filter was not visible at
    all until you scrolled past them. Closed by default: the common case is
    typing a name into the search box that stays above, not building a
    multi-attribute query.
    """
    return rx.accordion.root(
        rx.accordion.item(
            rx.accordion.header(
                rx.accordion.trigger(
                    rx.hstack(
                        rx.icon("sliders-horizontal", size=14),
                        rx.text(AppState.tr["batch_filters_toggle"], font_size="sm",
                                font_weight="600"),
                        rx.cond(
                            AppState.batch_has_active_filters,
                            rx.badge("●", color_scheme="orange", variant="solid",
                                     size="1"),
                            rx.box(),
                        ),
                        spacing="2", align="center",
                    ),
                ),
            ),
            rx.accordion.content(
                rx.vstack(
                    _area_range_filter(),
                    _attribute_filters(),
                    rx.hstack(
                        _sort_select(),
                        rx.spacer(),
                        width="100%", align_items="center",
                    ),
                    _paste_upload_box(),
                    spacing="3", width="100%",
                ),
                # Radix bakes 16px of its own horizontal padding into
                # AccordionContent, which sits on top of the card's — same
                # adjustment components/layout.py::group makes.
                padding_x="0",
            ),
            value="filters",
        ),
        type="single", collapsible=True, variant="ghost",
        color_scheme="orange", width="100%",
    )


def territory_selector(*, list_height: str | None = None) -> rx.Component:
    """Scrollable checkable list of territories with type/area/attribute
    filters and search.

    Two sizing modes, because the two places this renders give it genuinely
    different room:

    * ``list_height=None`` (the desktop column) — the card is a flex column
      filling its parent and the list takes whatever is left below the
      fixed-height controls. This needs an unbroken flex chain from the
      column down; see ``_section_card(fill=True)`` for the half of it that
      is easy to get wrong.
    * ``list_height="60dvh"`` (the narrow stage) — the stage is one
      scrolling column, so there is no "space left over" to fill and the
      list is given a definite share of the viewport instead, with the
      how-to guide scrolling below it.

    Either way it replaces ``calc(100vh - 380px)``, where 380 was a guess at
    the height of the desktop chrome above it — on a landscape phone (390px
    tall) that resolved to a 10px list.
    """
    if list_height is None:
        list_box = {"flex": "1", "min_height": "140px"}
        card = {"fill": True, "flex": "1", "min_height": "0"}
    else:
        list_box = {"height": list_height}
        card = {}
    return _section_card(
        # Header
        rx.hstack(
            rx.heading(AppState.tr["batch_select_territories"], size="3",
                       color="#1a472a"),
            rx.spacer(),
            rx.button(
                "📋 " + AppState.tr["batch_review_btn"],
                on_click=AppState.batch_toggle_review,
                size="1", variant="outline", color_scheme="orange",
            ),
            rx.badge(
                rx.text(
                    AppState.batch_selected_count.to(str) + "/"
                    + AppState.batch_max_selection.to(str)
                    + AppState.tr["batch_selected_suffix"]
                ),
                color_scheme="orange", variant="soft",
            ),
            width="100%", align_items="center", wrap="wrap", flex_shrink="0",
        ),
        _type_toggle(),
        # Search stays outside the disclosure: it is the one filter almost
        # every session uses, and hiding it behind a tap would be the same
        # mistake in miniature.
        rx.input(
            placeholder=AppState.tr["batch_search_placeholder"],
            value=AppState.batch_territory_search,
            on_change=AppState.batch_set_territory_search,
            width="100%",
            size="2",
        ),
        # Select-all / Clear, above the filter disclosure rather than below
        # it: they act on whatever the list currently shows, so they belong
        # with the search box that most sessions narrow it with, not tucked
        # under a collapsible most sessions never open. `size="2"` — these
        # are the two bulk actions of the whole stage, and at "1" they read
        # as incidental next to the row of small filter chips.
        rx.hstack(
            rx.button(
                AppState.tr["batch_select_all_filtered"],
                on_click=AppState.batch_select_all_filtered,
                size="2",
                variant="solid",
                color_scheme="orange",
                cursor="pointer",
            ),
            rx.button(
                AppState.tr["clear_all"],
                on_click=AppState.batch_clear_selection,
                size="2",
                variant="outline",
                color_scheme="gray",
                cursor="pointer",
            ),
            rx.spacer(),
            rx.text(
                AppState.batch_filtered_territories.length().to(str)
                + AppState.tr["batch_shown_suffix"],
                font_size="xs", color="#9CA3AF",
            ),
            width="100%", align_items="center", wrap="wrap", spacing="2",
            flex_shrink="0",
        ),
        _filters_disclosure(),
        # Scrollable list. `batch_capped_territories`, not
        # `batch_filtered_territories` — see that var for why, and note that
        # "select all filtered" above still acts on the full list.
        rx.box(
            rx.foreach(AppState.batch_capped_territories, _territory_row),
            rx.cond(
                AppState.batch_list_is_capped,
                rx.text(
                    AppState.batch_list_capped_note,
                    font_size="xs", color="#B45309", padding="0.5rem",
                    text_align="center",
                ),
                rx.box(),
            ),
            overflow_y="auto",
            width="100%",
            border="1px solid #e5e7eb",
            border_radius="var(--radius-3)",
            padding="0.5rem",
            **list_box,
        ),
        **card,
    )
