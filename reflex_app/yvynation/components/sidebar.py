"""
Sidebar component for Yvynation Reflex app.
Handles layer selection, territory filtering, and map controls.
"""

import reflex as rx
from ..state import AppState
from ..utils.translations import t, TRANSLATIONS
from ..config import MAPBIOMAS_YEARS, HANSEN_YEARS


def language_selector() -> rx.Component:
    """Language selection dropdown."""
    return rx.hstack(
        rx.text("🌐 Language:", font_weight="bold", font_size="1"),
        rx.select(
            items=list(TRANSLATIONS.keys()),
            value=AppState.language,
            on_change=AppState.set_language,
            size="1",
        ),
        width="100%",
        padding="0.5rem",
    )


def mapbiomas_layer_controls() -> rx.Component:
    """MapBiomas layer selection controls."""
    return rx.vstack(
        rx.heading("🌿 MapBiomas", size="2"),
        rx.text(
            t("mapbiomas_select_year"),
            font_size="xs",
            color="gray",
        ),
        rx.select(
            items=[str(y) for y in MAPBIOMAS_YEARS],
            value=rx.cond(
                AppState.mapbiomas_current_year > 0,
                str(AppState.mapbiomas_current_year),
                ""
            ),
            on_change=lambda v: AppState.set_mapbiomas_year(v),
            size="1",
            placeholder="Select year",
        ),
        rx.checkbox(
            "Add to map",
            is_checked=AppState.mapbiomas_years_enabled.get(AppState.mapbiomas_current_year, False),
            on_change=lambda _: AppState.toggle_mapbiomas_year(AppState.mapbiomas_current_year),
        ),
        rx.divider(),
        width="100%",
    )


def hansen_layer_controls() -> rx.Component:
    """Hansen layer selection controls."""
    return rx.vstack(
        rx.heading("🌲 Hansen GFC", size="2"),
        rx.text(
            t("hansen_select_year"),
            font_size="xs",
            color="gray",
        ),
        rx.select(
            items=HANSEN_YEARS,
            value=AppState.hansen_current_year,
            on_change=AppState.set_hansen_year,
            size="1",
        ),
        rx.checkbox(
            "Add to map",
            is_checked=AppState.hansen_years_enabled.get(AppState.hansen_current_year, False),
            on_change=lambda _: AppState.toggle_hansen_year(AppState.hansen_current_year),
        ),
        rx.divider(),
        rx.heading("Tree Cover & Loss Layers", size="1"),
        rx.checkbox(
            "🌳 Tree Cover 2000",
            is_checked=AppState.show_hansen_gfc_tree_cover,
            on_change=lambda _: AppState.toggle_gfc_layer("tree_cover"),
        ),
        rx.checkbox(
            "🔴 Tree Loss (2000-2023)",
            is_checked=AppState.show_hansen_gfc_tree_loss,
            on_change=lambda _: AppState.toggle_gfc_layer("tree_loss"),
        ),
        rx.checkbox(
            "🟢 Tree Gain (2000-2012)",
            is_checked=AppState.show_hansen_gfc_tree_gain,
            on_change=lambda _: AppState.toggle_gfc_layer("tree_gain"),
        ),
        rx.divider(),
        width="100%",
    )


def territory_selection_controls() -> rx.Component:
    """Territory and country selection controls."""
    return rx.vstack(
        rx.heading("📍 Territories", size="2"),
        rx.select(
            items=["Brazil", "Peru", "Colombia", "Ecuador", "Bolivia"],
            value=AppState.selected_country,
            on_change=AppState.set_country,
            placeholder="Select country",
            size="1",
        ),
        rx.input(
            placeholder="Search territory...",
            size="1",
        ),
        rx.cond(
            AppState.selected_territory != "",
            rx.vstack(
                rx.badge(AppState.selected_territory, color_scheme="green"),
                rx.button(
                    "Clear Selection",
                    on_click=lambda: AppState.set_selected_territory(""),
                    size="1",
                    width="100%",
                ),
                width="100%",
            ),
            rx.text(
                t("no_territory_selected"),
                font_size="xs",
                color="gray",
            ),
        ),
        rx.divider(),
        width="100%",
    )


def sidebar() -> rx.Component:
    """Main sidebar component."""
    return rx.vstack(
        language_selector(),
        rx.divider(),
        mapbiomas_layer_controls(),
        hansen_layer_controls(),
        territory_selection_controls(),
        spacing="4",
        padding="1rem",
        height="100vh",
        overflow_y="auto",
        bg="gray.50",
        border_right="1px solid #e0e0e0",
    )
