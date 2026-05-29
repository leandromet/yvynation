"""
Batch Processing page for Yvynation.

Lets users select multiple indigenous territories, configure analysis years
and options, and kick off a full automated analysis run.  All results are
packaged into a single ZIP archive — no charts are rendered during processing.
"""

import reflex as rx
from ..state import AppState


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
            rx.heading("🗺️ Select Territories", size="3", color="#1a472a"),
            rx.spacer(),
            rx.badge(
                rx.text(AppState.batch_selected_count.to(str) + " selected"),
                color_scheme="orange", variant="soft",
            ),
            width="100%", align_items="center",
        ),
        # Search
        rx.input(
            placeholder="🔍 Search territories…",
            value=AppState.batch_territory_search,
            on_change=AppState.batch_set_territory_search,
            width="100%",
            size="2",
        ),
        # Select-all / Clear row
        rx.hstack(
            rx.button(
                "Select all filtered",
                on_click=AppState.batch_select_all_filtered,
                size="1",
                variant="outline",
                color_scheme="orange",
            ),
            rx.button(
                "Clear all",
                on_click=AppState.batch_clear_selection,
                size="1",
                variant="ghost",
                color_scheme="gray",
            ),
            rx.spacer(),
            rx.text(
                AppState.batch_filtered_territories.length().to(str) + " shown",
                font_size="xs", color="#9CA3AF",
            ),
            width="100%", align_items="center",
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
                        spacing="0", align_items="flex-start", width="100%",
                    ),
                    width="100%",
                    align_items="flex-start",
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
        rx.heading("⚙️ Configuration", size="3", color="#1a472a"),

        # MapBiomas years
        rx.vstack(
            _label("MapBiomas years"),
            rx.hstack(
                rx.vstack(
                    rx.text("Single-year snapshot or Initial", font_size="xs", color="#6B7280"),
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
                    rx.text("Comparison final year", font_size="xs", color="#6B7280"),
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
            _label("Hansen GLAD year"),
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
            _label("Analysis types"),
            rx.checkbox(
                "🌿 MapBiomas single-year",
                checked=AppState.batch_run_mapbiomas,
                on_change=AppState.batch_toggle_run_mapbiomas,
                color_scheme="orange",
            ),
            rx.checkbox(
                "📊 Year-over-year comparison",
                checked=AppState.batch_run_comparison,
                on_change=AppState.batch_toggle_run_comparison,
                color_scheme="orange",
            ),
            rx.checkbox(
                "🌲 Hansen GLAD forest cover",
                checked=AppState.batch_run_glad,
                on_change=AppState.batch_toggle_run_glad,
                color_scheme="orange",
            ),
            rx.checkbox(
                "🪓 Hansen GFC (loss / gain)",
                checked=AppState.batch_run_gfc,
                on_change=AppState.batch_toggle_run_gfc,
                color_scheme="orange",
            ),
            rx.checkbox(
                "🗺️ PNG maps (satellite + MapBiomas y1/y2)",
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
                            "Extra MapBiomas rasters (year2)",
                            font_size="xs", font_weight="600",
                            color="#374151",
                            text_transform="uppercase", letter_spacing="0.05em",
                        ),
                        rx.checkbox(
                            "🌳 Deforestation & secondary vegetation",
                            checked=AppState.batch_run_aux_deforestation,
                            on_change=AppState.batch_toggle_aux_deforestation,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            "🔥 Annual burned area (fire scar size)",
                            checked=AppState.batch_run_aux_fire_scar,
                            on_change=AppState.batch_toggle_aux_fire_scar,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            "📊 Fire frequency (1985–2024 full period)",
                            checked=AppState.batch_run_aux_fire_frequency,
                            on_change=AppState.batch_toggle_aux_fire_frequency,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            "📅 Year of last fire",
                            checked=AppState.batch_run_aux_fire_year_last,
                            on_change=AppState.batch_toggle_aux_fire_year_last,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            "⛏️ Mining substances",
                            checked=AppState.batch_run_aux_mining_substances,
                            on_change=AppState.batch_toggle_aux_mining_substances,
                            color_scheme="orange",
                        ),
                        rx.checkbox(
                            "🌾 Agriculture — number of cycles",
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
                "🌀 Multiple time-window MapBiomas (Sankey + Sunburst)",
                checked=AppState.batch_run_multi_window,
                on_change=AppState.batch_toggle_run_multi_window,
                color_scheme="orange",
            ),
            rx.cond(
                AppState.batch_run_multi_window,
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Mode:", font_size="xs", color="#6B7280", width="70px"),
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
                                rx.text("Step (years):", font_size="xs", color="#6B7280", width="100px"),
                                rx.select(
                                    ["1", "2", "4", "5", "8"],
                                    value=AppState.batch_multi_window_step,
                                    on_change=AppState.batch_set_multi_window_step,
                                    size="2", width="80px",
                                ),
                                rx.text(
                                    "1985 → 2024 forced as last year",
                                    font_size="xs", color="#9CA3AF",
                                ),
                                spacing="2", align_items="center",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Custom years (3 or 4, comma-separated, 1985–2024)",
                                    font_size="xs", color="#6B7280",
                                ),
                                rx.input(
                                    value=AppState.batch_multi_window_custom_years,
                                    on_change=AppState.batch_set_multi_window_custom_years,
                                    placeholder="1985, 2004, 2012, 2023",
                                    size="2", width="100%",
                                ),
                                spacing="1", width="100%",
                            ),
                        ),
                        rx.text(
                            "Active years: " + AppState.batch_multi_window_resolved_years.to(str),
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
                "📈 Deforestation timeline (Hansen + MapBiomas + Fire) with political/policy context",
                checked=AppState.batch_run_deforestation_timeline,
                on_change=AppState.batch_toggle_run_deforestation_timeline,
                color_scheme="orange",
            ),
            spacing="2",
        ),

        rx.divider(border_color="#F3F4F6"),

        # Buffer
        rx.vstack(
            _label("Buffer zone"),
            rx.hstack(
                rx.switch(
                    checked=AppState.batch_buffer_enabled,
                    on_change=AppState.batch_toggle_buffer_enabled,
                    color_scheme="orange",
                ),
                rx.text("Include buffer analysis", font_size="sm"),
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
                    rx.text("km external ring", font_size="sm", color="#6B7280"),
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
            rx.heading("📊 Progress", size="3", color="#1a472a"),
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
                    rx.text("Territory:", font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        rx.cond(
                            AppState.batch_done,
                            "— complete —",
                            AppState.batch_current_territory,
                        ),
                        font_size="sm", font_weight="600",
                        color=rx.cond(AppState.batch_done, "#16A34A", "#111827"),
                    ),
                    spacing="2", align_items="center",
                ),
                rx.hstack(
                    rx.text("Step:", font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        AppState.batch_current_step,
                        font_size="sm", color="#374151",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.hstack(
                    rx.text("Done:", font_size="xs", color="#6B7280", width="80px"),
                    rx.text(
                        AppState.batch_completed.length().to(str)
                        + " / "
                        + AppState.batch_total.to(str)
                        + rx.cond(
                            AppState.batch_failed.length() > 0,
                            " (" + AppState.batch_failed.length().to(str) + " errors)",
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
                _label("Processing log"),
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
            rx.heading("📖 About Batch Processing", size="3", color="#1a472a"),
            width="100%", align_items="center",
        ),
        rx.text(
            "Run the full Yvynation analysis pipeline (MapBiomas land cover, "
            "year-over-year change, Hansen GLAD forest cover, and Hansen GFC "
            "loss/gain) across many indigenous territories in one unattended "
            "run. Each territory — and its optional external buffer — is "
            "processed via Google Earth Engine and packaged into a single ZIP "
            "archive containing CSV tables, transition matrices, and chart "
            "figures (HTML + PNG) per territory.",
            font_size="sm", color="#374151", line_height="1.6",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.hstack(
            rx.icon("clock", size=14, color=ORANGE),
            rx.text(
                "Expect 2–10 minutes per territory depending on which analyses "
                "are enabled. The tab can stay open in the background.",
                font_size="xs", color="#6B7280", line_height="1.5",
            ),
            spacing="2", align_items="flex-start",
        ),
        rx.divider(border_color="#F3F4F6"),

        rx.accordion.root(
            rx.accordion.item(
                header=rx.text(
                    "How to use",
                    font_size="xs", font_weight="600", color="#374151",
                    text_transform="uppercase", letter_spacing="0.05em",
                ),
                content=rx.vstack(
                    _howto_step(
                        1,
                        "Select territories",
                        "Use the search box on the left, then tick the territories you "
                        "want to include. “Select all filtered” adds every match of the "
                        "current search; “Clear all” starts over.",
                    ),
                    _howto_step(
                        2,
                        "Pick MapBiomas years",
                        "Set the initial year (single snapshot) and the final year "
                        "(for the year-over-year comparison). Range: 1985–2024.",
                    ),
                    _howto_step(
                        3,
                        "Pick the Hansen GLAD year",
                        "Reference year (2000/2005/2010/2015/2020) used for the Hansen "
                        "GLAD forest-cover snapshot.",
                    ),
                    _howto_step(
                        4,
                        "Choose analysis types",
                        "Enable any combination of MapBiomas single-year, year-over-"
                        "year comparison, Hansen GLAD, and Hansen GFC loss/gain.",
                    ),
                    _howto_step(
                        5,
                        "Optional buffer zone",
                        "Toggle on to also analyse an external ring (default 10 km) "
                        "around each territory. Buffer outputs are written to "
                        "buffer/{territory}_Buffer_{km}km/ inside the ZIP.",
                    ),
                    _howto_step(
                        6,
                        "Start the batch",
                        "Click “Start Batch Processing”. The configuration panel is "
                        "replaced by the live progress view; you can stop after the "
                        "current territory at any time.",
                    ),
                    _howto_step(
                        7,
                        "Download the ZIP",
                        "When the run finishes, hit “Download ZIP” to grab all "
                        "tables, transitions, and figures for every territory in one "
                        "self-describing archive.",
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

def action_panel() -> rx.Component:
    return rx.hstack(
        # Start button (shown when not running and not done)
        rx.cond(
            ~AppState.batch_running & ~AppState.batch_done,
            rx.button(
                rx.cond(
                    AppState.batch_selected_count > 0,
                    "🚀 Start Batch Processing ("
                    + AppState.batch_selected_count.to(str)
                    + " territories)",
                    "🚀 Start Batch Processing",
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
                    rx.text("Processing…", font_size="sm", font_weight="600",
                            color=ORANGE),
                    spacing="2", align_items="center",
                ),
                rx.spacer(),
                rx.button(
                    "⏹ Stop after current",
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
                    "⬇️ Download ZIP",
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
                    "🔄 New Batch",
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
    )


# ---------------------------------------------------------------------------
# Page navbar
# ---------------------------------------------------------------------------

def batch_navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.button(
                "← Back to Portal",
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
                        "🔶 Batch Processing",
                        font_size="sm", color=ORANGE_DARK, font_weight="600",
                    ),
                    spacing="2", align_items="center",
                ),
                rx.text(
                    "Run full analysis on multiple territories — download one ZIP",
                    font_size="xs", color="#6B7280",
                ),
                spacing="0",
            ),
            spacing="3", align_items="center",
        ),
        rx.spacer(),
        rx.cond(
            AppState.batch_done & AppState.batch_zip_ready,
            rx.button(
                "⬇️ Download ZIP",
                on_click=AppState.download_batch_zip,
                size="2",
                bg="#16A34A",
                color="white",
                font_weight="bold",
            ),
            rx.badge(
                rx.cond(
                    AppState.batch_running,
                    "Processing…",
                    rx.cond(
                        AppState.batch_selected_count > 0,
                        AppState.batch_selected_count.to(str) + " territories selected",
                        "No territories selected",
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

        width="100%",
        height="100vh",
        spacing="0",
        bg="#F9FAFB",
    )
