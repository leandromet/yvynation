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


def territory_selector() -> rx.Component:
    """Scrollable checkable list of territories with type/area/attribute filters and search."""
    return _section_card(
        # Header
        rx.hstack(
            rx.heading(AppState.tr["batch_select_territories"], size="3", color="#1a472a"),
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
            width="100%", align_items="center",
        ),
        _type_toggle(),
        _area_range_filter(),
        _attribute_filters(),
        # Search
        rx.input(
            placeholder=AppState.tr["batch_search_placeholder"],
            value=AppState.batch_territory_search,
            on_change=AppState.batch_set_territory_search,
            width="100%",
            size="2",
        ),
        # Select-all / Clear row
        rx.hstack(
            rx.button(
                AppState.tr["batch_select_all_filtered"],
                on_click=AppState.batch_select_all_filtered,
                size="1",
                variant="outline",
                color_scheme="orange",
            ),
            rx.button(
                AppState.tr["clear_all"],
                on_click=AppState.batch_clear_selection,
                size="1",
                variant="ghost",
                color_scheme="gray",
            ),
            rx.spacer(),
            _sort_select(),
            rx.text(
                AppState.batch_filtered_territories.length().to(str) + AppState.tr["batch_shown_suffix"],
                font_size="xs", color="#9CA3AF",
            ),
            width="100%", align_items="center",
        ),
        _paste_upload_box(),
        # Scrollable list
        rx.box(
            rx.foreach(AppState.batch_filtered_territories, _territory_row),
            height="calc(100vh - 380px)",
            overflow_y="auto",
            width="100%",
            border="1px solid #e5e7eb",
            border_radius="lg",
            padding="0.5rem",
        ),
        height="100%",
    )
