"""Right column (top): analysis year / option configuration for the batch page."""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE_BORDER, _label, _section_card


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
            # ── Figure export ────────────────────────────────────────────
            rx.text(
                AppState.tr["batch_figs_label"],
                font_size="xs", font_weight="600", color="#374151",
                text_transform="uppercase", letter_spacing="0.05em",
                margin_top="0.4rem",
            ),
            rx.checkbox(
                AppState.tr["batch_chk_export_png"],
                checked=AppState.batch_export_png,
                on_change=AppState.batch_toggle_export_png,
                color_scheme="orange",
            ),
            rx.text(
                AppState.tr["batch_png_hint"],
                font_size="2xs", color="#9CA3AF", margin_left="1.75rem",
                line_height="1.4",
            ),
            rx.cond(
                AppState.batch_export_png,
                rx.box(
                    rx.checkbox(
                        AppState.tr["batch_chk_png_high_res"],
                        checked=AppState.batch_png_high_res,
                        on_change=AppState.batch_toggle_png_high_res,
                        color_scheme="orange",
                    ),
                    margin_left="1.75rem",
                ),
                rx.fragment(),
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
            # Context bands nest under the timeline checkbox — same pattern as
            # the auxiliary rasters under PDF maps: they only mean anything
            # when their parent is on.
            rx.cond(
                AppState.batch_run_deforestation_timeline,
                rx.box(
                    rx.vstack(
                        rx.text(
                            AppState.tr["batch_timeline_bands_label"],
                            font_size="xs", font_weight="600", color="#374151",
                            text_transform="uppercase", letter_spacing="0.05em",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_chk_timeline_political"],
                            checked=AppState.batch_timeline_political,
                            on_change=AppState.batch_toggle_timeline_political,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_chk_timeline_policy"],
                            checked=AppState.batch_timeline_policy,
                            on_change=AppState.batch_toggle_timeline_policy,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            AppState.tr["batch_chk_timeline_enso"],
                            checked=AppState.batch_timeline_enso,
                            on_change=AppState.batch_toggle_timeline_enso,
                            color_scheme="orange",
                        ),
                        rx.text(
                            AppState.tr["batch_timeline_bands_hint"],
                            font_size="2xs", color="#9CA3AF", line_height="1.4",
                        ),
                        spacing="2", width="100%", align_items="flex-start",
                    ),
                    # Same indented card as the auxiliary rasters under PDF maps.
                    padding="0.75rem",
                    margin_left="1.75rem",
                    bg="#FFF7ED",
                    border="1px solid " + ORANGE_BORDER,
                    border_radius="md",
                    width="calc(100% - 1.75rem)",
                ),
                rx.fragment(),
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
                    rx.select(
                        ["1", "2", "5", "10", "20"],
                        value=AppState.batch_buffer_km,
                        on_change=AppState.batch_set_buffer_km,
                        size="2", width="80px",
                    ),
                    rx.text(AppState.tr["batch_km_ring"], font_size="sm", color="#6B7280"),
                    spacing="2", align_items="center",
                ),
                rx.box(),
            ),
            spacing="2",
        ),
    )
