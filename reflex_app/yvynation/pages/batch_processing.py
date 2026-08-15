"""
Batch Processing page for Yvynation.

Lets users select multiple indigenous territories, configure analysis years
and options, and kick off a full automated analysis run.  All results are
packaged into a single ZIP archive — no charts are rendered during processing.
"""

import reflex as rx
from ..state import AppState
from ..components.language_selector import language_selector
from ..components.citation import citation_modal, cite_trigger


# ---------------------------------------------------------------------------
# Helper widgets
# ---------------------------------------------------------------------------

ORANGE = "#EA580C"
ORANGE_LIGHT = "#FFF7ED"
ORANGE_BORDER = "#FDBA74"
ORANGE_DARK = "#C2410C"


def _section_card(*children, **box_props) -> rx.Component:
    return rx.box(
        rx.vstack(*children, spacing="3", width="100%"),
        padding="1.25rem",
        bg="white",
        border_radius="xl",
        border=f"1px solid #e5e7eb",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        width="100%",
        **box_props,
    )


def _label(text: str) -> rx.Component:
    return rx.text(text, font_size="xs", font_weight="600", color="#374151",
                   text_transform="uppercase", letter_spacing="0.05em")


def _step_badge(n: int, label: str, active: bool = False) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(str(n), font_size="xs", font_weight="700", color="white"),
            bg=ORANGE if active else "#9CA3AF",
            border_radius="full",
            width="1.4rem", height="1.4rem",
            display="flex", align_items="center", justify_content="center",
        ),
        rx.text(label, font_size="sm",
                color=ORANGE if active else "#6B7280",
                font_weight="600" if active else "400"),
        align_items="center", spacing="2",
    )


# ---------------------------------------------------------------------------
# Left column: territory selector
# ---------------------------------------------------------------------------

def territory_selector() -> rx.Component:
    """Scrollable checkable list of territories with search."""
    return _section_card(
        # Header
        rx.hstack(
            rx.heading(AppState.tr["batch_select_territories"], size="3", color="#1a472a"),
            rx.spacer(),
            rx.badge(
                rx.text(AppState.batch_selected_count.to(str) + AppState.tr["batch_selected_suffix"]),
                color_scheme="orange", variant="soft",
            ),
            width="100%", align_items="center",
        ),
        # Territory type toggle — both may be active at once (mixed batches)
        rx.hstack(
            rx.button(
                AppState.tr["batch_indigenous_btn"],
                on_click=AppState.batch_toggle_territory_type("indigenous"),
                size="1",
                bg=rx.cond(
                    AppState.batch_territory_types.contains("indigenous"),
                    ORANGE, "white",
                ),
                color=rx.cond(
                    AppState.batch_territory_types.contains("indigenous"),
                    "white", "#6B7280",
                ),
                border=rx.cond(
                    AppState.batch_territory_types.contains("indigenous"),
                    f"1px solid {ORANGE}",
                    f"1px solid #D1D5DB",
                ),
                border_radius="md",
                flex="1",
                cursor="pointer",
                _hover={"bg": rx.cond(
                    AppState.batch_territory_types.contains("indigenous"),
                    ORANGE_DARK, "#F9FAFB",
                )},
            ),
            rx.button(
                AppState.tr["batch_conservation_btn"],
                on_click=AppState.batch_toggle_territory_type("conservation"),
                size="1",
                bg=rx.cond(
                    AppState.batch_territory_types.contains("conservation"),
                    "#16A34A", "white",
                ),
                color=rx.cond(
                    AppState.batch_territory_types.contains("conservation"),
                    "white", "#6B7280",
                ),
                border=rx.cond(
                    AppState.batch_territory_types.contains("conservation"),
                    "1px solid #16A34A",
                    "1px solid #D1D5DB",
                ),
                border_radius="md",
                flex="1",
                cursor="pointer",
                _hover={"bg": rx.cond(
                    AppState.batch_territory_types.contains("conservation"),
                    "#15803D", "#F9FAFB",
                )},
            ),
            width="100%", spacing="2",
        ),
        # Area range filter (hectares)
        rx.hstack(
            rx.text(AppState.tr["batch_area_filter_label"], font_size="xs", color="#6B7280", flex_shrink="0"),
            rx.input(
                placeholder=AppState.tr["batch_min_ha_placeholder"],
                value=AppState.batch_min_area_ha,
                on_change=AppState.batch_set_min_area_ha,
                type="number",
                min="0",
                size="1",
                width="90px",
            ),
            rx.text("–", color="#9CA3AF", flex_shrink="0"),
            rx.input(
                placeholder=AppState.tr["batch_max_ha_placeholder"],
                value=AppState.batch_max_area_ha,
                on_change=AppState.batch_set_max_area_ha,
                type="number",
                min="0",
                size="1",
                width="90px",
            ),
            rx.text(AppState.tr["batch_ha_suffix"], font_size="xs", color="#9CA3AF", flex_shrink="0"),
            rx.cond(
                (AppState.batch_min_area_ha != "") | (AppState.batch_max_area_ha != ""),
                rx.button(
                    "✕",
                    on_click=AppState.batch_clear_area_filter,
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                ),
                rx.box(),
            ),
            width="100%", align_items="center", spacing="2",
        ),
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
            rx.text(
                AppState.batch_filtered_territories.length().to(str) + AppState.tr["batch_shown_suffix"],
                font_size="xs", color="#9CA3AF",
            ),
            width="100%", align_items="center",
        ),
        # Paste / upload a list of names → auto-select
        rx.box(
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
        ),
        # Scrollable list
        rx.box(
            rx.foreach(
                AppState.batch_filtered_territories,
                lambda t: rx.hstack(
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
                ),
            ),
            height="calc(100vh - 380px)",
            overflow_y="auto",
            width="100%",
            border="1px solid #e5e7eb",
            border_radius="lg",
            padding="0.5rem",
        ),
        height="100%",
    )


# ---------------------------------------------------------------------------
# Right column: configuration
# ---------------------------------------------------------------------------

def config_panel() -> rx.Component:
    """Analysis year / option configuration."""
    return _section_card(
        rx.heading(AppState.tr["batch_configuration"], size="3", color="#1a472a"),

        # MapBiomas years
        rx.vstack(
            _label(AppState.tr["mapbiomas_years"]),
            rx.hstack(
                rx.vstack(
                    rx.text(AppState.tr["batch_year1_label"], font_size="xs", color="#6B7280"),
                    rx.select(
                        [str(y) for y in range(2024, 1984, -1)],
                        value=AppState.batch_year,
                        on_change=AppState.batch_set_year,
                        size="2", width="110px",
                    ),
                    spacing="1",
                ),
                rx.text("↔", font_size="lg", color="#9CA3AF", padding_top="1.2rem"),
                rx.vstack(
                    rx.text(AppState.tr["batch_year2_label"], font_size="xs", color="#6B7280"),
                    rx.select(
                        [str(y) for y in range(2024, 1984, -1)],
                        value=AppState.batch_year2,
                        on_change=AppState.batch_set_year2,
                        size="2", width="110px",
                    ),
                    spacing="1",
                ),
                spacing="3", align_items="flex-start",
            ),
            spacing="1", width="100%",
        ),

        # Hansen GLAD year
        rx.vstack(
            _label(AppState.tr["batch_hansen_year_label"]),
            rx.select(
                ["2000", "2005", "2010", "2015", "2020"],
                value=AppState.batch_hansen_year,
                on_change=AppState.batch_set_hansen_year,
                size="2", width="110px",
            ),
            spacing="1",
        ),

        rx.divider(border_color="#F3F4F6"),

        # Analysis types
        rx.vstack(
            _label(AppState.tr["batch_analysis_types"]),
            rx.checkbox(
                AppState.tr["batch_chk_mapbiomas"],
                checked=AppState.batch_run_mapbiomas,
                on_change=AppState.batch_toggle_run_mapbiomas,
                color_scheme="orange",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_comparison"],
                checked=AppState.batch_run_comparison,
                on_change=AppState.batch_toggle_run_comparison,
                color_scheme="orange",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_treemap"],
                checked=AppState.batch_run_treemap,
                on_change=AppState.batch_toggle_run_treemap,
                color_scheme="orange",
            ),
            rx.text(
                AppState.tr["batch_treemap_hint"],
                font_size="2xs", color="#9CA3AF", margin_left="1.75rem",
                line_height="1.4",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_glad"],
                checked=AppState.batch_run_glad,
                on_change=AppState.batch_toggle_run_glad,
                color_scheme="orange",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_gfc"],
                checked=AppState.batch_run_gfc,
                on_change=AppState.batch_toggle_run_gfc,
                color_scheme="orange",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_pdf_maps"],
                checked=AppState.batch_run_pdf_maps,
                on_change=AppState.batch_toggle_run_pdf_maps,
                color_scheme="orange",
            ),
            # Extra MapBiomas auxiliary raster layers (one PNG per layer per
            # territory). Per-year layers render for the configured batch
            # year2; fire frequency is a single full-period image.
            rx.cond(
                AppState.batch_run_pdf_maps,
                rx.box(
                    rx.vstack(
                        rx.text(
                            AppState.tr["batch_aux_rasters_label"],
                            font_size="xs", font_weight="600",
                            color="#374151",
                            text_transform="uppercase", letter_spacing="0.05em",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_deforestation"],
                            checked=AppState.batch_run_aux_deforestation,
                            on_change=AppState.batch_toggle_aux_deforestation,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_fire_scar"],
                            checked=AppState.batch_run_aux_fire_scar,
                            on_change=AppState.batch_toggle_aux_fire_scar,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_fire_frequency"],
                            checked=AppState.batch_run_aux_fire_frequency,
                            on_change=AppState.batch_toggle_aux_fire_frequency,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_fire_year_last"],
                            checked=AppState.batch_run_aux_fire_year_last,
                            on_change=AppState.batch_toggle_aux_fire_year_last,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_mining"],
                            checked=AppState.batch_run_aux_mining_substances,
                            on_change=AppState.batch_toggle_aux_mining_substances,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_aux_agriculture"],
                            checked=AppState.batch_run_aux_agriculture_cycles,
                            on_change=AppState.batch_toggle_aux_agriculture_cycles,
                            color_scheme="orange",
                        ),
                        spacing="2", width="100%",
                    ),
                    padding="0.75rem",
                    margin_left="1.75rem",
                    bg="#FFF7ED",
                    border="1px solid " + ORANGE_BORDER,
                    border_radius="md",
                    width="calc(100% - 1.75rem)",
                ),
                rx.box(),
            ),
            rx.checkbox(
                AppState.tr["batch_chk_multi_window"],
                checked=AppState.batch_run_multi_window,
                on_change=AppState.batch_toggle_run_multi_window,
                color_scheme="orange",
            ),
            rx.cond(
                AppState.batch_run_multi_window,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text(AppState.tr["batch_mw_mode"], font_size="xs", color="#6B7280", width="70px"),
                            rx.select(
                                ["constant", "custom"],
                                value=AppState.batch_multi_window_mode,
                                on_change=AppState.batch_set_multi_window_mode,
                                size="2", width="130px",
                            ),
                            spacing="2", align_items="center",
                        ),
                        rx.cond(
                            AppState.batch_multi_window_mode == "constant",
                            rx.hstack(
                                rx.text(AppState.tr["batch_mw_step"], font_size="xs", color="#6B7280", width="100px"),
                                rx.select(
                                    ["1", "2", "4", "5", "8"],
                                    value=AppState.batch_multi_window_step,
                                    on_change=AppState.batch_set_multi_window_step,
                                    size="2", width="80px",
                                ),
                                rx.text(
                                    AppState.tr["batch_mw_forced_note"],
                                    font_size="xs", color="#9CA3AF",
                                ),
                                spacing="2", align_items="center",
                            ),
                            rx.vstack(
                                rx.text(
                                    AppState.tr["batch_mw_custom_label"],
                                    font_size="xs", color="#6B7280",
                                ),
                                rx.input(
                                    value=AppState.batch_multi_window_custom_years,
                                    on_change=AppState.batch_set_multi_window_custom_years,
                                    placeholder="1985, 1994, 2004, 2014, 2024",
                                    size="2", width="100%",
                                ),
                                spacing="1", width="100%",
                            ),
                        ),
                        rx.text(
                            AppState.tr["batch_mw_active_years"] + AppState.batch_multi_window_resolved_years.to(str),
                            font_size="xs", color="#374151",
                        ),
                        spacing="2", width="100%",
                    ),
                    padding="0.75rem",
                    margin_left="1.75rem",
                    bg="#FFF7ED",
                    border="1px solid " + ORANGE_BORDER,
                    border_radius="md",
                    width="calc(100% - 1.75rem)",
                ),
                rx.box(),
            ),
            rx.checkbox(
                AppState.tr["batch_chk_timeline"],
                checked=AppState.batch_run_deforestation_timeline,
                on_change=AppState.batch_toggle_run_deforestation_timeline,
                color_scheme="orange",
            ),
            spacing="2",
        ),

        rx.divider(border_color="#F3F4F6"),

        # Buffer
        rx.vstack(
            _label(AppState.tr["batch_buffer_zone"]),
            rx.hstack(
                rx.switch(
                    checked=AppState.batch_buffer_enabled,
                    on_change=AppState.batch_toggle_buffer_enabled,
                    color_scheme="orange",
                ),
                rx.text(AppState.tr["batch_include_buffer"], font_size="sm"),
                spacing="2", align_items="center",
            ),
            rx.cond(
                AppState.batch_buffer_enabled,
                rx.hstack(
                    rx.input(
                        value=AppState.batch_buffer_km.to(str),
                        on_blur=AppState.batch_set_buffer_km,
                        type="number",
                        min="1", max="100",
                        width="80px",
                        size="2",
                    ),
                    rx.text(AppState.tr["batch_km_ring"], font_size="sm", color="#6B7280"),
                    spacing="2", align_items="center",
                ),
                rx.box(),
            ),
            spacing="2",
        ),
    )


# ---------------------------------------------------------------------------
# Status / progress panel
# ---------------------------------------------------------------------------

def _log_line(line: str) -> rx.Component:
    return rx.text(line, font_size="xs", font_family="monospace",
                   color=rx.cond(
                       line.startswith("  ✅"),
                       "#16A34A",
                       rx.cond(line.startswith("  ❌"), "#DC2626", "#374151"),
                   ))


def status_panel() -> rx.Component:
    """Progress bar, current step, and scrollable log."""
    return _section_card(
        # Header + progress percentage
        rx.hstack(
            rx.heading(AppState.tr["batch_progress"], size="3", color="#1a472a"),
            rx.spacer(),
            rx.text(
                AppState.batch_progress_pct.to(str) + "%",
                font_size="xl", font_weight="700",
                color=rx.cond(AppState.batch_done, "#16A34A", ORANGE),
            ),
            width="100%", align_items="center",
        ),

        # Progress bar
        rx.box(
            rx.box(
                width=AppState.batch_progress_pct.to(str) + "%",
                height="100%",
                bg=rx.cond(AppState.batch_done, "#16A34A", ORANGE),
                border_radius="full",
                transition="width 0.4s ease",
            ),
            width="100%", height="10px",
            bg="#F3F4F6", border_radius="full", overflow="hidden",
        ),

        # Territory / step labels
        rx.cond(
            AppState.batch_running | AppState.batch_done,
            rx.vstack(
                rx.hstack(
                    rx.text(AppState.tr["batch_territory_label"], font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        rx.cond(
                            AppState.batch_done,
                            AppState.tr["batch_complete_label"],
                            AppState.batch_current_territory,
                        ),
                        font_size="sm", font_weight="600",
                        color=rx.cond(AppState.batch_done, "#16A34A", "#111827"),
                    ),
                    spacing="2", align_items="center",
                ),
                rx.hstack(
                    rx.text(AppState.tr["batch_step_label"], font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        AppState.batch_current_step,
                        font_size="sm", color="#374151",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.hstack(
                    rx.text(AppState.tr["batch_done_label"], font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        AppState.batch_completed.length().to(str)
                        + " / "
                        + AppState.batch_total.to(str)
                        + rx.cond(
                            AppState.batch_failed.length() > 0,
                            " (" + AppState.batch_failed.length().to(str) + AppState.tr["batch_errors_suffix"],
                            "",
                        ),
                        font_size="sm", color="#374151",
                    ),
                    spacing="2", align_items="center",
                ),
                spacing="1", width="100%",
            ),
            rx.box(),
        ),

        # Live log
        rx.cond(
            AppState.batch_log.length() > 0,
            rx.vstack(
                _label(AppState.tr["batch_processing_log"]),
                rx.box(
                    rx.vstack(
                        rx.foreach(AppState.batch_log, _log_line),
                        spacing="0",
                        width="100%",
                        align_items="flex-start",
                    ),
                    width="100%",
                    height="200px",
                    overflow_y="auto",
                    bg="#F9FAFB",
                    border="1px solid #E5E7EB",
                    border_radius="md",
                    padding="0.75rem",
                ),
                width="100%", spacing="1",
            ),
            rx.box(),
        ),
    )


# ---------------------------------------------------------------------------
# How-to / explanation panel
# ---------------------------------------------------------------------------

def _howto_step(n: int, title: str, body: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(str(n), font_size="sm", font_weight="700", color="white"),
            bg=ORANGE,
            border_radius="full",
            min_width="1.6rem", height="1.6rem",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(title, font_size="sm", font_weight="600", color="#111827"),
            rx.text(body, font_size="xs", color="#4B5563", line_height="1.5"),
            spacing="1", align_items="flex-start",
        ),
        spacing="3", align_items="flex-start", width="100%",
    )


def howto_panel() -> rx.Component:
    """Explanation of the batch module and a step-by-step usage guide."""
    return _section_card(
        rx.hstack(
            rx.heading(AppState.tr["batch_about_title"], size="3", color="#1a472a"),
            width="100%", align_items="center",
        ),
        rx.text(
            AppState.tr["batch_about_text"],
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.hstack(
            rx.icon("clock", size=14, color=ORANGE),
            rx.text(
                AppState.tr["batch_time_note"],
                font_size="xs", color="#6B7280", line_height="1.5",
            ),
            spacing="2", align_items="flex-start",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.accordion.root(
            rx.accordion.item(
                header=rx.text(
                    AppState.tr["batch_howto"],
                    font_size="xs", font_weight="600", color="#374151",
                    text_transform="uppercase", letter_spacing="0.05em",
                ),
                content=rx.vstack(
                    _howto_step(
                        1,
                        AppState.tr["batch_howto_1_title"],
                        AppState.tr["batch_howto_1_body"],
                    ),
                    _howto_step(
                        2,
                        AppState.tr["batch_howto_2_title"],
                        AppState.tr["batch_howto_2_body"],
                    ),
                    _howto_step(
                        3,
                        AppState.tr["batch_howto_3_title"],
                        AppState.tr["batch_howto_3_body"],
                    ),
                    _howto_step(
                        4,
                        AppState.tr["batch_howto_4_title"],
                        AppState.tr["batch_howto_4_body"],
                    ),
                    _howto_step(
                        5,
                        AppState.tr["batch_howto_5_title"],
                        AppState.tr["batch_howto_5_body"],
                    ),
                    _howto_step(
                        6,
                        AppState.tr["batch_howto_6_title"],
                        AppState.tr["batch_howto_6_body"],
                    ),
                    _howto_step(
                        7,
                        AppState.tr["batch_howto_7_title"],
                        AppState.tr["batch_howto_7_body"],
                    ),
                    spacing="3", width="100%", padding_top="0.75rem",
                ),
                value="howto",
            ),
            type="single",
            collapsible=True,
            default_value=None,
            variant="ghost",
            width="100%",
            color_scheme="orange",
        ),
    )


# ---------------------------------------------------------------------------
# Action buttons panel
# ---------------------------------------------------------------------------

def large_run_warning() -> rx.Component:
    """Soft warning shown above the start button for oversized selections.

    Never blocks the run — just nudges the user toward splitting large jobs
    into a few smaller ones, which keeps peak memory bounded per run.
    """
    return rx.cond(
        AppState.batch_is_large_run & ~AppState.batch_running & ~AppState.batch_done,
        rx.hstack(
            rx.icon("triangle-alert", size=16, color="#B45309"),
            rx.text(
                AppState.tr["batch_large_run_warning"],
                font_size="xs", color="#92400E",
            ),
            padding="0.5rem 0.75rem",
            bg="#FFFBEB",
            border="1px solid #FDE68A",
            border_radius="md",
            align_items="center",
            spacing="2",
            width="100%",
            margin_bottom="0.5rem",
        ),
        rx.box(),
    )


def action_panel() -> rx.Component:
    return rx.vstack(
        large_run_warning(),
        rx.hstack(
            # Start button (shown when not running and not done)
            rx.cond(
                ~AppState.batch_running & ~AppState.batch_done,
                rx.button(
                    rx.cond(
                        AppState.batch_selected_count > 0,
                        AppState.tr["batch_start_btn"] + " ("
                        + AppState.batch_selected_count.to(str)
                        + " " + AppState.tr["territories_word"] + ")",
                        AppState.tr["batch_start_btn"],
                    ),
                    on_click=AppState.run_batch_processing,
                    is_disabled=AppState.batch_selected_count == 0,
                    size="3",
                    bg=rx.cond(
                        AppState.batch_selected_count > 0, ORANGE, "#9CA3AF"
                    ),
                    color="white",
                    font_weight="bold",
                    _hover={"bg": ORANGE_DARK},
                    width="100%",
                ),
                rx.box(),
            ),

            # Running: spinner + stop button
            rx.cond(
                AppState.batch_running,
                rx.hstack(
                    rx.hstack(
                        rx.spinner(size="2", color=ORANGE),
                        rx.text(AppState.tr["batch_processing_ellipsis"], font_size="sm", font_weight="600",
                                color=ORANGE),
                        spacing="2", align_items="center",
                    ),
                    rx.spacer(),
                    rx.button(
                        AppState.tr["batch_stop_btn"],
                        on_click=AppState.batch_stop,
                        size="2",
                        variant="outline",
                        color_scheme="red",
                    ),
                    width="100%", align_items="center",
                ),
                rx.box(),
            ),

            # Done: download + new batch
            rx.cond(
                AppState.batch_done,
                rx.hstack(
                    rx.button(
                        AppState.tr["batch_download_zip"],
                        on_click=AppState.download_batch_zip,
                        is_disabled=~AppState.batch_zip_ready,
                        size="3",
                        bg="#16A34A",
                        color="white",
                        font_weight="bold",
                        _hover={"bg": "#15803D"},
                        flex="1",
                    ),
                    rx.button(
                        AppState.tr["batch_new_batch"],
                        on_click=AppState.batch_reset,
                        size="3",
                        variant="outline",
                        color_scheme="gray",
                        flex="1",
                    ),
                    width="100%", spacing="3",
                ),
                rx.box(),
            ),

            width="100%",
        ),
        width="100%",
        spacing="0",
    )


# ---------------------------------------------------------------------------
# Page navbar
# ---------------------------------------------------------------------------

def batch_navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.button(
                AppState.tr["back_to_portal"],
                on_click=AppState.go_to_portal,
                size="1",
                variant="outline",
                color_scheme="orange",
            ),
            rx.vstack(
                rx.hstack(
                    rx.heading(AppState.tr["app_title"], size="3"),
                    rx.text("•", color=ORANGE, font_weight="bold"),
                    rx.text(
                        AppState.tr["batch_title"],
                        font_size="sm", color=ORANGE_DARK, font_weight="600",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.text(
                    AppState.tr["batch_nav_subtitle"],
                    font_size="xs", color="#6B7280",
                ),
                spacing="0",
            ),
            spacing="3", align_items="center",
        ),
        rx.spacer(),
        language_selector(),
        rx.button(
            "📂 " + AppState.tr["previous_runs_title"],
            on_click=AppState.go_to_previous_runs,
            size="1", variant="outline", color_scheme="orange",
        ),
        cite_trigger(color_scheme="orange"),
        rx.cond(
            AppState.batch_done & AppState.batch_zip_ready,
            rx.button(
                AppState.tr["batch_download_zip"],
                on_click=AppState.download_batch_zip,
                size="2",
                bg="#16A34A",
                color="white",
                font_weight="bold",
            ),
            rx.badge(
                rx.cond(
                    AppState.batch_running,
                    AppState.tr["batch_processing_ellipsis"],
                    rx.cond(
                        AppState.batch_selected_count > 0,
                        AppState.batch_selected_count.to(str) + AppState.tr["batch_territories_selected_suffix"],
                        AppState.tr["batch_no_territories"],
                    ),
                ),
                color_scheme=rx.cond(
                    AppState.batch_running,
                    "orange",
                    rx.cond(AppState.batch_selected_count > 0, "green", "gray"),
                ),
                variant="soft",
                size="2",
            ),
        ),
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)",
        border_bottom=f"3px solid {ORANGE_BORDER}",
        align_items="center",
        width="100%",
        height="70px",
        position="sticky",
        top="0",
        z_index="100",
    )


# ---------------------------------------------------------------------------
# Main page component
# ---------------------------------------------------------------------------

def batch_processing_page() -> rx.Component:
    """Full batch processing page layout."""
    return rx.vstack(
        batch_navbar(),

        # Main two-column layout
        rx.box(
            rx.hstack(
                # ── Left: territory selector (40%) ──
                rx.box(
                    territory_selector(),
                    width="38%",
                    min_width="300px",
                    padding="1rem",
                    height="calc(100vh - 70px)",
                    overflow_y="auto",
                ),

                # ── Divider ──
                rx.divider(orientation="vertical", border_color="#E5E7EB"),

                # ── Right: config + status + actions (60%) ──
                rx.box(
                    rx.vstack(
                        # Config (hidden while running)
                        rx.cond(
                            ~AppState.batch_running & ~AppState.batch_done,
                            config_panel(),
                            rx.box(),
                        ),

                        # Status (visible once started)
                        rx.cond(
                            AppState.batch_running | AppState.batch_done,
                            status_panel(),
                            rx.box(),
                        ),

                        # Action buttons
                        action_panel(),

                        # How-to / explanation (always visible — fills the
                        # empty space below the ~1/3-height progress area)
                        howto_panel(),

                        spacing="4",
                        width="100%",
                    ),
                    width="62%",
                    padding="1rem",
                    height="calc(100vh - 70px)",
                    overflow_y="auto",
                ),

                width="100%",
                height="calc(100vh - 70px)",
                spacing="0",
                align_items="stretch",
            ),
            width="100%",
            flex="1",
        ),

        # Error toast (re-use from index)
        rx.cond(
            AppState.error_message != "",
            rx.box(
                rx.hstack(
                    rx.icon("alert-circle", color="red", size=16),
                    rx.text(AppState.error_message, font_size="sm"),
                    rx.spacer(),
                    rx.button(
                        "✕", on_click=AppState.clear_error,
                        size="1", variant="ghost",
                    ),
                    width="100%", align_items="center",
                ),
                padding="0.75rem 1rem",
                bg="red.50",
                border="1px solid red",
                border_radius="md",
                position="fixed",
                bottom="1rem",
                right="1rem",
                z_index="9999",
                max_width="420px",
            ),
            rx.box(),
        ),

        citation_modal(),

        width="100%",
        height="100vh",
        spacing="0",
        bg="#F9FAFB",
    )
