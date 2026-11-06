"""The ``/usa`` workspace: sidebar (search, area, layers), map, results."""

from __future__ import annotations

import reflex as rx

from ...canada._shared.map.leaflet_map import leaflet_map
from ...components.quickstart import quickstart_card
from ..config import nlcd
from ..state import USState as S

ACCENT = "indigo"
HEADER_H = "56px"
MUTED = "var(--gray-11)"


def _section(title, *children) -> rx.Component:
    return rx.vstack(
        rx.text(title, size="1", weight="bold", color_scheme="gray",
                style={"textTransform": "uppercase", "letterSpacing": "0.06em"}),
        *children, spacing="2", align_items="stretch", width="100%")


# --------------------------------------------------------------------------- header
def _link(flag: str, label, href) -> rx.Component:
    return rx.link(rx.button(rx.text(label, display=["none", "none", "block", "block"]),
                             size="1", variant="soft", color_scheme="gray"), href=href)


def _lang() -> rx.Component:
    return rx.segmented_control.root(
        rx.segmented_control.item("🇧🇷 PT", value="pt"), rx.segmented_control.item("🇺🇸 EN", value="en"),
        value=S.language, on_change=S.set_language, size="1")


def header() -> rx.Component:
    return rx.hstack(
        rx.icon("trees", size=20, color=f"var(--{ACCENT}-11)"),
        rx.heading("Yvynation", size="4", weight="bold"),
        rx.badge("USA", variant="soft", color_scheme=ACCENT, size="1"),
        rx.spacer(),
        rx.text(S.tr["nav_subtitle"], size="1", color_scheme="gray",
                display=["none", "none", "none", "block"], max_width="520px", no_of_lines=2),
        rx.spacer(),
        _link(None, S.tr["go_to_brazil"], S.brazil_href),
        _link(None, S.tr["go_to_canada"], S.canada_href),
        _lang(),
        rx.dialog.root(
            rx.dialog.trigger(rx.button(rx.icon("circle-help", size=15),
                                        rx.text(S.tr["help"], display=["none", "none", "block", "block"]),
                                        size="1", variant="soft", color_scheme="gray")),
            rx.dialog.content(
                rx.dialog.title(S.tr["help_title"]),
                rx.vstack(
                    rx.text(S.tr["help_1"], size="2"), rx.text(S.tr["help_2"], size="2"),
                    rx.text(S.tr["help_3"], size="2"), rx.divider(),
                    rx.unordered_list(rx.list_item(S.tr["help_limit_1"]), rx.list_item(S.tr["help_limit_2"]),
                                      rx.list_item(S.tr["help_limit_3"]), size="2"),
                    rx.box(rx.text(S.tr["indigenous_data_notice_title"], size="2", weight="bold",
                                   color="#6d28d9"),
                           rx.text(S.tr["indigenous_data_notice_body"], size="1", color_scheme="gray"),
                           padding="8px", border_left="3px solid #8b5cf6", background="#f5f3ff",
                           border_radius="4px"),
                    rx.dialog.close(rx.button(S.tr["close"], size="2", variant="soft")),
                    spacing="3", align_items="start"),
                max_width="620px")),
        width="100%", padding="0.6rem 1rem", align="center", spacing="2", height=HEADER_H,
        border_bottom="1px solid var(--gray-5)", background="var(--color-panel-solid)", flex_shrink="0")


# --------------------------------------------------------------------------- sidebar
def _unit_row(u: rx.Var, on_pick) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(u["name"], size="2", weight="medium", no_of_lines=1),
                rx.text(u["des_label"], " · ", u["manager"], " · ", u["ha"].to_string(), " ha",
                        size="1", color_scheme="gray", no_of_lines=1),
                spacing="0", align_items="start", flex="1", min_width="0"),
            rx.cond(u["tribal"], rx.badge(S.tr["tribal_badge"], color_scheme="violet", size="1"),
                    rx.fragment()),
            align="center", spacing="2", width="100%"),
        on_click=on_pick(u["key"]),
        padding="6px 8px", border="1px solid var(--gray-5)", border_radius="6px",
        cursor="pointer", _hover={"background": "var(--gray-3)"}, width="100%")


def _search() -> rx.Component:
    return _section(
        S.tr["search_title"],
        rx.hstack(
            rx.input(placeholder=S.tr["search_placeholder"], value=S.query, on_change=S.set_query,
                     on_key_down=S.search_key,
                     size="2", flex="1"),
            rx.button(rx.cond(S.searching, S.tr["search_button_busy"], S.tr["search_button"]),
                      on_click=S.submit_search, size="2", color_scheme=ACCENT),
            width="100%", spacing="2"),
        rx.text(S.tr["search_tip"], size="1", color_scheme="gray"),
        rx.cond(S.search_error != "",
                rx.callout(S.search_error, icon="triangle-alert", color_scheme="amber", size="1"),
                rx.fragment()),
        rx.cond(S.candidates.length() > 0,
                rx.vstack(rx.text(S.tr["candidates_title"], size="1", weight="bold"),
                          rx.foreach(S.candidates, lambda u: _unit_row(u, S.choose_unit)),
                          spacing="1", width="100%"),
                rx.fragment()),
        rx.cond(S.hits.length() > 0,
                rx.vstack(rx.text(S.tr["search_hits"], size="1", weight="bold"),
                          rx.foreach(S.hits, lambda u: _unit_row(u, S.choose_unit)),
                          spacing="1", width="100%"),
                rx.cond(S.searched & (S.hits.length() == 0) & (S.query != "") & (~S.has_unit),
                        rx.text(S.tr["search_none"], size="1", color_scheme="gray"), rx.fragment())),
    )


def _area_card() -> rx.Component:
    return rx.cond(
        S.has_unit,
        _section(
            S.tr["area_card_title"],
            rx.hstack(rx.text(S.unit["name"], size="3", weight="bold"),
                      rx.cond(S.unit["tribal"], rx.badge(S.tr["tribal_badge"], color_scheme="violet"),
                              rx.fragment()), spacing="2", align="center", wrap="wrap"),
            rx.foreach(S.unit_rows, lambda r: rx.hstack(
                rx.text(r["label"], size="1", color_scheme="gray"), rx.spacer(),
                rx.text(r["value"], size="1", weight="medium"), width="100%")),
            rx.cond(S.unit["tribal"],
                    rx.box(rx.text(S.tr["indigenous_data_notice_title"], size="1", weight="bold",
                                   color="#6d28d9"),
                           rx.text(S.tr["indigenous_data_notice_body"], size="1", color_scheme="gray",
                                   line_height="1.45"),
                           padding="6px 8px", border_left="3px solid #8b5cf6", background="#f5f3ff",
                           border_radius="4px"),
                    rx.fragment()),
            rx.text(S.tr["area_disclosure"], size="1", color_scheme="gray"),
        ),
        rx.cond(S.loading_area, rx.spinner(size="2"), rx.fragment()))


def _zones() -> rx.Component:
    return rx.cond(S.zones.length() > 0, _section(
        S.tr["zones_title"],
        rx.hstack(rx.foreach(S.zones, lambda z: rx.button(
            z["zone_label"], on_click=S.set_active_zone(z["zone_key"]), size="1",
            variant=rx.cond(S.active_zone == z["zone_key"], "solid", "soft"), color_scheme=ACCENT)),
            wrap="wrap", spacing="1"),
        rx.text(S.tr["zones_note"], size="1", color_scheme="gray")), rx.fragment())


def _layers() -> rx.Component:
    return _section(
        S.tr["layers_title"],
        rx.select(S.basemap_options, value=S.basemap_label, on_change=S.set_basemap, size="1"),
        rx.hstack(rx.switch(checked=S.show_nlcd, on_change=S.toggle_nlcd),
                  rx.text(S.tr["nlcd_layer"], size="2"), spacing="2", align="center"),
        rx.cond(S.show_nlcd, rx.vstack(
            rx.hstack(rx.text(S.tr["year"], size="1", color_scheme="gray"), rx.spacer(),
                      rx.select(S.years, value=S.nlcd_year.to_string(), on_change=S.set_nlcd_year, size="1")),
            rx.hstack(rx.text(S.tr["opacity"], size="1", color_scheme="gray"),
                      rx.slider(min=0, max=100, step=5, default_value=[75],
                                on_change=S.set_nlcd_opacity, width="60%"), justify="between", width="100%"),
            spacing="1", width="100%"), rx.fragment()),
        rx.hstack(rx.switch(checked=S.show_change, on_change=S.toggle_change),
                  rx.text(S.tr["hansen_layer"], size="2"), spacing="2", align="center"),
        rx.hstack(rx.switch(checked=S.show_padus, on_change=S.toggle_padus),
                  rx.text(S.tr["padus_layer"], size="2"), spacing="2", align="center"),
        rx.cond(S.show_padus, rx.text(S.tr["padus_note"], size="1", color_scheme="gray"), rx.fragment()),
    )


def sidebar() -> rx.Component:
    return rx.vstack(_search(), rx.divider(), _area_card(), _zones(), rx.divider(), _layers(),
                     spacing="4", align_items="stretch", padding="1rem", width="100%")


# --------------------------------------------------------------------------- results
def _cover_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(S.cover_running, rx.hstack(rx.spinner(size="1"), rx.text(S.tr["cover_running"], size="1")),
                rx.fragment()),
        rx.cond(S.cover_error != "", rx.callout(S.cover_error, icon="triangle-alert", color_scheme="amber",
                                                size="1"), rx.fragment()),
        rx.cond(S.has_cover,
                rx.flex(
                    rx.vstack(
                        rx.hstack(rx.switch(checked=S.cover_normalise, on_change=S.toggle_normalise, size="1"),
                                  rx.text(S.tr["normalise"], size="1"), spacing="2", align="center"),
                        rx.plotly(data=S.cover_figure, width="100%",
                                  config={"displayModeBar": False, "responsive": True}),
                        rx.text(S.tr["cover_attribution"], size="1", color_scheme="gray"),
                        flex="1", min_width="0", align_items="stretch", spacing="2"),
                    rx.vstack(
                        rx.text(S.table_title, size="1", weight="bold"),
                        rx.foreach(S.cover_table, lambda r: rx.hstack(
                            rx.box(width="10px", height="10px", border_radius="2px", background=r["color"],
                                   flex_shrink="0"),
                            rx.text(r["name"], size="1", flex="1", no_of_lines=1),
                            rx.text(r["ha"], size="1", color_scheme="gray"),
                            rx.text(r["pct"], "%", size="1", weight="medium", width="52px",
                                    text_align="right"), width="100%", spacing="2")),
                        width=["100%", "100%", "100%", "260px"], spacing="1", align_items="stretch"),
                    direction=rx.breakpoints(initial="column", lg="row"), gap="1rem", width="100%"),
                rx.cond(~S.cover_running & (S.cover_error == ""),
                        rx.text(S.tr["cover_empty"], size="1", color_scheme="gray"), rx.fragment())),
        spacing="3", width="100%", align_items="stretch")


def _forest_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(S.forest_running, rx.hstack(rx.spinner(size="1"), rx.text(S.tr["forest_running"], size="1")),
                rx.fragment()),
        rx.cond(S.forest_error != "", rx.callout(S.forest_error, icon="triangle-alert", color_scheme="amber",
                                                 size="1"), rx.fragment()),
        rx.cond(S.has_forest, rx.vstack(
            rx.plotly(data=S.forest_figure, width="100%",
                      config={"displayModeBar": False, "responsive": True}),
            rx.text(S.tr["forest_note"], size="1", color_scheme="gray"),
            rx.text(S.tr["forest_attribution"], size="1", color_scheme="gray"),
            spacing="2", width="100%", align_items="stretch"),
                rx.cond(~S.forest_running & (S.forest_error == ""),
                        rx.text(S.tr["forest_empty"], size="1", color_scheme="gray"), rx.fragment())),
        spacing="3", width="100%", align_items="stretch")


def _simple_tab(running, error, has, figure, run_key, empty_key, err_key, note_key, attribution=None,
                extra=None) -> rx.Component:
    return rx.vstack(
        rx.cond(running, rx.hstack(rx.spinner(size="1"), rx.text(S.tr[run_key], size="1")), rx.fragment()),
        rx.cond(error != "", rx.callout(error, icon="triangle-alert", color_scheme="amber", size="1"),
                rx.fragment()),
        rx.cond(has, rx.vstack(
            *( [extra] if extra is not None else [] ),
            rx.plotly(data=figure, width="100%", config={"displayModeBar": False, "responsive": True}),
            rx.text(S.tr[note_key], size="1", color_scheme="gray"),
            spacing="2", width="100%", align_items="stretch"),
                rx.cond(~running & (error == ""),
                        rx.text(S.tr[empty_key], size="1", color_scheme="gray"), rx.fragment())),
        spacing="3", width="100%", align_items="stretch")


def _biomass_tab() -> rx.Component:
    return _simple_tab(S.biomass_running, S.biomass_error, S.has_biomass, S.biomass_figure,
                       "biomass_running", "biomass_empty", "biomass_error", "biomass_note")


def _fire_tab() -> rx.Component:
    stats = rx.flex(rx.foreach(S.fire_stats, lambda r: rx.vstack(
        rx.text(r["label"], size="1", color_scheme="gray"), rx.text(r["value"], size="2", weight="medium"),
        spacing="0", align_items="start")), gap="1.5rem", wrap="wrap")
    return _simple_tab(S.fire_running, S.fire_error, S.has_fire, S.fire_figure,
                       "fire_running", "fire_empty", "fire_error", "fire_note", extra=stats)


def results() -> rx.Component:
    return rx.box(
        rx.tabs.root(
            rx.tabs.list(rx.tabs.trigger(S.tr["tab_cover"], value="cover"),
                         rx.tabs.trigger(S.tr["tab_forest"], value="forest"),
                         rx.tabs.trigger(S.tr["tab_biomass"], value="biomass"),
                         rx.tabs.trigger(S.tr["tab_fire"], value="fire")),
            rx.tabs.content(_cover_tab(), value="cover", padding_top="0.75rem"),
            rx.tabs.content(_forest_tab(), value="forest", padding_top="0.75rem"),
            rx.tabs.content(_biomass_tab(), value="biomass", padding_top="0.75rem"),
            rx.tabs.content(_fire_tab(), value="fire", padding_top="0.75rem"),
            value=S.results_tab, on_change=S.set_results_tab),
        padding="0.75rem 1rem", width="100%", border_top="1px solid var(--gray-5)",
        background="var(--color-panel-solid)", max_height=["none", "none", "none", "44vh"],
        overflow_y="auto", flex_shrink="0")


def _map() -> rx.Component:
    return rx.box(
        leaflet_map(id="yvy-usa-map", center=S.center, zoom=S.zoom, layers=S.map_layers,
                    overlays=S.map_overlays, vectors=[], fit_bounds=S.fit_bounds,
                    on_map_click=S.select_at_point, swipe=False, width="100%", height="100%"),
        position="absolute", top="0", left="0", width="100%", height="100%")


def usa_index() -> rx.Component:
    return rx.vstack(
        header(),
        rx.flex(
            rx.box(sidebar(), width=["100%", "100%", "100%", "340px"], min_width="0",
                   flex_shrink="0", height=["auto", "auto", "auto", "100%"],
                   max_height=["46vh", "46vh", "46vh", "none"], overflow_y="auto",
                   border_right="1px solid var(--gray-5)", background="var(--color-panel-solid)"),
            rx.vstack(rx.box(_map(), quickstart_card(S, accent=ACCENT, desktop_from=2),
                             position="relative", flex="1 1 auto", min_height="320px", width="100%"),
                      results(), spacing="0", width="100%", height="100%", align_items="stretch",
                      min_width="0"),
            direction=rx.breakpoints(initial="column", lg="row"),
            width="100%", flex="1", gap="0", align_items="stretch", overflow="hidden",
            min_height="0"),
        width="100vw", height="100vh", spacing="0", align_items="stretch", overflow="hidden")
