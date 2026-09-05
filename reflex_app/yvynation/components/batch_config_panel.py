"""Analysis year / option configuration for the batch page.

The same 26 controls and the same handlers as before, but grouped into six
collapsible clusters instead of one flat card. Flat, this panel ran to
roughly a screen and a half on a laptop and pushed the Start button below
the fold; on a phone it was most of the page.

The six explanatory captions that used to sit between the controls as
permanent ``font_size="2xs"`` gray lines are now tap-to-open (i) popovers
next to the control they describe (``components/layout.py::info_icon``).
Same strings, no new translation keys, and — unlike a caption or an HTML
``title=`` — they work on touch without spending vertical space until asked
for.
"""

import reflex as rx
from ..state import AppState
from .batch_shared import ORANGE_BORDER, _label, _section_card, batch_groups_root
from .layout import group, info_icon


def _nested_card(*children: rx.Component) -> rx.Component:
    """The indented sub-card a dependent option group renders into — the
    auxiliary rasters under PDF maps, the timeline's context bands, the
    multi-window settings. Unchanged from the flat panel; only its callers
    moved."""
    return rx.box(
        rx.vstack(*children, spacing="2", width="100%", align_items="flex-start"),
        padding="0.75rem",
        margin_left="1.75rem",
        bg="#FFF7ED",
        border="1px solid " + ORANGE_BORDER,
        border_radius="md",
        width="calc(100% - 1.75rem)",
    )


def _check(label, checked, on_change, *, hint=None) -> rx.Component:
    """A batch option checkbox, optionally with its explanation behind an
    (i) icon rather than a caption line under it."""
    box = rx.checkbox(label, checked=checked, on_change=on_change,
                      color_scheme="orange")
    if hint is None:
        return box
    return rx.hstack(box, info_icon(hint), spacing="1", align="center",
                     width="100%")


# --- 1. Years -------------------------------------------------------------

def _years_group() -> rx.Component:
    return group(
        "years", "calendar", AppState.tr["batch_group_years"],
        rx.vstack(
            _label(AppState.tr["mapbiomas_years"]),
            rx.hstack(
                rx.vstack(
                    rx.text(AppState.tr["batch_year1_label"], font_size="xs",
                            color="#6B7280"),
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
                    rx.text(AppState.tr["batch_year2_label"], font_size="xs",
                            color="#6B7280"),
                    rx.select(
                        [str(y) for y in range(2024, 1984, -1)],
                        value=AppState.batch_year2,
                        on_change=AppState.batch_set_year2,
                        size="2", width="110px",
                    ),
                    spacing="1",
                ),
                spacing="3", align_items="flex-start", wrap="wrap",
            ),
            spacing="1", width="100%", align_items="flex-start",
        ),
        rx.vstack(
            _label(AppState.tr["batch_hansen_year_label"]),
            rx.select(
                ["2000", "2005", "2010", "2015", "2020"],
                value=AppState.batch_hansen_year,
                on_change=AppState.batch_set_hansen_year,
                size="2", width="110px",
            ),
            spacing="1", align_items="flex-start",
        ),
    )


# --- 2. Analyses ----------------------------------------------------------

def _analyses_group() -> rx.Component:
    return group(
        "analyses", "list-checks", AppState.tr["batch_group_analyses"],
        rx.vstack(
            _check(AppState.tr["batch_chk_mapbiomas"],
                   AppState.batch_run_mapbiomas,
                   AppState.batch_toggle_run_mapbiomas),
            _check(AppState.tr["batch_chk_comparison"],
                   AppState.batch_run_comparison,
                   AppState.batch_toggle_run_comparison),
            _check(AppState.tr["batch_chk_treemap"],
                   AppState.batch_run_treemap,
                   AppState.batch_toggle_run_treemap,
                   hint=AppState.tr["batch_treemap_hint"]),
            _check(AppState.tr["batch_chk_glad"],
                   AppState.batch_run_glad,
                   AppState.batch_toggle_run_glad),
            _check(AppState.tr["batch_chk_gfc"],
                   AppState.batch_run_gfc,
                   AppState.batch_toggle_run_gfc),
            _check(AppState.tr["batch_chk_pdf_maps"],
                   AppState.batch_run_pdf_maps,
                   AppState.batch_toggle_run_pdf_maps),
            spacing="2", width="100%", align_items="flex-start",
        ),
    )


# --- 3. Figures -----------------------------------------------------------

def _figures_group() -> rx.Component:
    """PNG export, and the auxiliary rasters that ride along with PDF maps.

    The aux-raster block is gated on ``batch_run_pdf_maps``, whose checkbox
    lives one group up in Analyses. That is deliberate: the option belongs
    with the run's analyses, but what it *produces* is a stack of images,
    which belongs here. When the group is empty because PDF maps are off,
    the `rx.cond` simply renders nothing.
    """
    return group(
        "figures", "image", AppState.tr["batch_group_figures"],
        rx.vstack(
            _label(AppState.tr["batch_figs_label"]),
            _check(AppState.tr["batch_chk_export_png"],
                   AppState.batch_export_png,
                   AppState.batch_toggle_export_png,
                   hint=AppState.tr["batch_png_hint"]),
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
                _nested_card(
                    rx.text(
                        AppState.tr["batch_aux_rasters_label"],
                        font_size="xs", font_weight="600", color="#374151",
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
                ),
                rx.box(),
            ),
            spacing="2", width="100%", align_items="flex-start",
        ),
    )


# --- 4. Multi-window ------------------------------------------------------

def _multiwindow_group() -> rx.Component:
    return group(
        "multiwindow", "layout-grid", AppState.tr["batch_group_multiwindow"],
        rx.vstack(
            _check(AppState.tr["batch_chk_multi_window"],
                   AppState.batch_run_multi_window,
                   AppState.batch_toggle_run_multi_window),
            rx.cond(
                AppState.batch_run_multi_window,
                _nested_card(
                    rx.hstack(
                        rx.text(AppState.tr["batch_mw_mode"], font_size="xs",
                                color="#6B7280", width="70px"),
                        rx.select(
                            ["constant", "custom"],
                            value=AppState.batch_multi_window_mode,
                            on_change=AppState.batch_set_multi_window_mode,
                            size="2", width="130px",
                        ),
                        spacing="2", align_items="center", wrap="wrap",
                    ),
                    rx.cond(
                        AppState.batch_multi_window_mode == "constant",
                        rx.hstack(
                            rx.text(AppState.tr["batch_mw_step"], font_size="xs",
                                    color="#6B7280", width="100px"),
                            rx.select(
                                ["1", "2", "4", "5", "8"],
                                value=AppState.batch_multi_window_step,
                                on_change=AppState.batch_set_multi_window_step,
                                size="2", width="80px",
                            ),
                            info_icon(AppState.tr["batch_mw_forced_note"]),
                            spacing="2", align_items="center", wrap="wrap",
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
                        AppState.tr["batch_mw_active_years"]
                        + AppState.batch_multi_window_resolved_years.to(str),
                        font_size="xs", color="#374151",
                    ),
                ),
                rx.box(),
            ),
            spacing="2", width="100%", align_items="flex-start",
        ),
    )


# --- 5. Timeline ----------------------------------------------------------

def _timeline_group() -> rx.Component:
    return group(
        "timeline", "chart-line", AppState.tr["batch_group_timeline"],
        rx.vstack(
            _check(AppState.tr["batch_chk_timeline"],
                   AppState.batch_run_deforestation_timeline,
                   AppState.batch_toggle_run_deforestation_timeline),
            # Context bands nest under the timeline checkbox — same pattern as
            # the auxiliary rasters under PDF maps: they only mean anything
            # when their parent is on.
            rx.cond(
                AppState.batch_run_deforestation_timeline,
                _nested_card(
                    rx.hstack(
                        rx.text(
                            AppState.tr["batch_timeline_bands_label"],
                            font_size="xs", font_weight="600", color="#374151",
                            text_transform="uppercase", letter_spacing="0.05em",
                        ),
                        info_icon(AppState.tr["batch_timeline_bands_hint"]),
                        spacing="1", align="center",
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
                ),
                rx.fragment(),
            ),
            spacing="2", width="100%", align_items="flex-start",
        ),
    )


# --- 6. Buffer ------------------------------------------------------------

def _buffer_group() -> rx.Component:
    return group(
        "buffer", "circle-dashed", AppState.tr["batch_group_buffer"],
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
                    rx.text(AppState.tr["batch_km_ring"], font_size="sm",
                            color="#6B7280"),
                    spacing="2", align_items="center",
                ),
                rx.box(),
            ),
            spacing="2", width="100%", align_items="flex-start",
        ),
    )


def config_panel() -> rx.Component:
    """Analysis year / option configuration.

    Rendered in both page bodies (wide and narrow) and, unlike before, kept
    on screen while a run is in progress: it used to be hidden behind
    ``~batch_running & ~batch_done``, so once you started a job there was no
    way to check what you had actually asked it to do.
    """
    return _section_card(
        rx.heading(AppState.tr["batch_configuration"], size="3", color="#1a472a"),
        batch_groups_root(
            _years_group(),
            _analyses_group(),
            _figures_group(),
            _multiwindow_group(),
            _timeline_group(),
            _buffer_group(),
        ),
    )
