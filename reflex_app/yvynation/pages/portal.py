"""
Portal/Introduction page for Yvynation Reflex app.
Explains the analysis, data, and methods.
Allows users to choose between geometry or indigenous territory analysis.
"""

import reflex as rx
from ..state import AppState
from ..components.language_selector import language_selector
from ..components.citation import citation_modal, cite_trigger


def portal_navbar() -> rx.Component:
    """Navigation bar for portal page with enhanced styling."""
    return rx.hstack(
        rx.vstack(
            rx.heading(AppState.tr["app_title"], size="1", color="#1a472a", font_weight="bold"),
            rx.text(
                AppState.tr["app_subtitle"],
                font_size="xs",
                color="#4a7c59",
                font_weight="500",
            ),
            spacing="0",
        ),
        rx.spacer(),
        rx.hstack(
            language_selector(),
            spacing="2",
        ),
        padding="0.75rem 1.5rem",
        bg="linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%)",
        border_bottom="3px solid #4a7c59",
        align_items="center",
        width="100%",
        box_shadow="0 2px 8px rgba(0,0,0,0.05)",
    )


def _bullet(text) -> rx.Component:
    """One bulleted line. Hand-built rather than rx.list_item so each entry is
    an independent grid cell — a real <ul> would keep them in one column."""
    return rx.hstack(
        rx.text("•", color="#15803d", flex_shrink="0"),
        rx.text(text, font_size="sm", line_height="1.6", color="#444"),
        spacing="2",
        align_items="flex-start",
    )


def data_sources_section() -> rx.Component:
    """Data sources, collapsed by default.

    Five dense provider lines sat between the introduction and the analysis
    choices, pushing the actual entry points below the fold. Collapsed they are
    one line; expanded they lay out across the available width instead of as a
    tall single column.
    """
    is_open = AppState.portal_data_sources_open
    return rx.vstack(
        rx.hstack(
            rx.text(rx.cond(is_open, "▾", "▸"), font_size="sm", color="#2d5a3d"),
            rx.heading(
                "📊 " + AppState.tr["data_sources_title"], size="4", color="#2d5a3d",
            ),
            rx.text(
                rx.cond(is_open, AppState.tr["portal_hide"], AppState.tr["portal_show"]),
                font_size="xs", color="#6B7280",
            ),
            spacing="2",
            align_items="center",
            on_click=AppState.toggle_portal_data_sources,
            cursor="pointer",
            width="100%",
        ),
        rx.cond(
            is_open,
            rx.box(
                # auto-fit rather than a fixed column count: the list reflows
                # from three columns to one as the viewport narrows, with no
                # breakpoint bookkeeping.
                *[
                    _bullet(AppState.tr[key])
                    for key in (
                        "portal_ds_mapbiomas",
                        "portal_ds_hansen",
                        "portal_ds_aafc",
                        "portal_ds_gee",
                        "portal_ds_custom",
                    )
                ],
                display="grid",
                grid_template_columns="repeat(auto-fit, minmax(280px, 1fr))",
                gap="0.5rem 2rem",
                width="100%",
                padding_top="0.5rem",
            ),
            rx.fragment(),
        ),
        spacing="1",
        width="100%",
        align_items="flex-start",
    )


def about_section() -> rx.Component:
    """Section explaining the application with enhanced styling."""
    return rx.box(
        rx.vstack(
            rx.heading("🌍 " + AppState.tr["about_section"], size="3", color="#1a472a"),
            rx.text(
                AppState.tr["about_description"],
                font_size="md",
                line_height="1.8",
                color="#333",
            ),
            rx.divider(border_color="#d0e8d8"),
            data_sources_section(),
            rx.divider(border_color="#d0e8d8"),
            rx.box(
                rx.vstack(
                    rx.heading(
                        "🛰️ " + AppState.tr["citation_acknowledgment_title"],
                        size="4",
                        color="#2d5a3d",
                    ),
                    rx.text(
                        AppState.tr["citation_mission"],
                        font_size="sm",
                        line_height="1.8",
                        color="#444",
                    ),
                    # Short form only. The full acknowledgements — people,
                    # institutions, funding — are in the "How to Cite" panel,
                    # which the trigger below opens.
                    rx.text(
                        AppState.tr["citation_ack_summary"],
                        font_size="sm",
                        line_height="1.8",
                        color="#444",
                    ),
                    cite_trigger(),
                    spacing="2",
                    align_items="flex-start",
                ),
                padding="1rem",
                bg="#f0fdf4",
                border="1px solid #bbf7d0",
                border_radius="md",
            ),
            spacing="2",
        ),
        padding="1.5rem",
        bg="linear-gradient(135deg, #f8fdf6 0%, #f0f9f4 100%)",
        border_radius="lg",
        border="2px solid #d0e8d8",
        max_width="1200px",
        margin="0 auto",
        box_shadow="0 4px 12px rgba(0,0,0,0.08)",
    )


def analysis_choice_section() -> rx.Component:
    """Section to choose between analysis types with enhanced styling."""
    return rx.box(
        rx.vstack(
            rx.heading(AppState.tr["portal_choose_title"], size="2", text_align="center", color="#1a472a"),
            rx.text(
                AppState.tr["portal_choose_desc"],
                font_size="md",
                text_align="center",
                color="#555",
                margin_bottom="1rem",
            ),
            rx.hstack(
                # Geometry Analysis Card
                rx.box(
                    rx.vstack(
                        rx.heading(
                            AppState.tr["geometry_analysis_label"],
                            size="3",
                            text_align="center",
                            color="#1e40af",
                        ),
                        rx.text(
                            AppState.tr["portal_geometry_sub"],
                            font_size="sm",
                            text_align="center",
                            color="#666",
                            margin_bottom="0.75rem",
                        ),
                        rx.divider(border_color="#bfdbfe"),
                        rx.unordered_list(
                            rx.list_item(AppState.tr["portal_geometry_i1"]),
                            rx.list_item(AppState.tr["portal_geometry_i2"]),
                            rx.list_item(AppState.tr["portal_geometry_i3"]),
                            rx.list_item(AppState.tr["portal_geometry_i4"]),
                            font_size="sm",
                            color="#333",
                            line_height="1.8",
                        ),
                        rx.spacer(),
                        rx.button(
                            AppState.tr["portal_geometry_btn"],
                            on_click=lambda: AppState.go_to_geometry_analysis(),
                            size="2",
                            color_scheme="blue",
                            width="100%",
                            font_weight="bold",
                        ),
                        spacing="2",
                    ),
                    padding="1.5rem",
                    bg="linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)",
                    border_radius="xl",
                    border="2px solid #60a5fa",
                    flex="1",
                    box_shadow="0 4px 6px rgba(30, 64, 175, 0.1)",
                    transition="all 0.3s ease",
                ),
                # Territory Analysis Card
                rx.box(
                    rx.vstack(
                        rx.heading(
                            AppState.tr["territory_analysis_label"],
                            size="3",
                            text_align="center",
                            color="#15803d",
                        ),
                        rx.text(
                            AppState.tr["portal_territory_sub"],
                            font_size="sm",
                            text_align="center",
                            color="#666",
                            margin_bottom="0.75rem",
                        ),
                        rx.divider(border_color="#bbf7d0"),
                        rx.unordered_list(
                            rx.list_item(AppState.tr["portal_territory_i1"]),
                            rx.list_item(AppState.tr["portal_territory_i2"]),
                            rx.list_item(AppState.tr["portal_territory_i3"]),
                            rx.list_item(AppState.tr["portal_territory_i4"]),
                            font_size="sm",
                            color="#333",
                            line_height="1.8",
                        ),
                        rx.spacer(),
                        rx.button(
                            AppState.tr["portal_territory_btn"],
                            on_click=lambda: AppState.go_to_territory_analysis(),
                            size="2",
                            color_scheme="green",
                            width="100%",
                            font_weight="bold",
                        ),
                        spacing="2",
                    ),
                    padding="1.5rem",
                    bg="linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)",
                    border_radius="xl",
                    border="2px solid #4ade80",
                    flex="1",
                    box_shadow="0 4px 6px rgba(21, 128, 61, 0.1)",
                    transition="all 0.3s ease",
                ),
                # Batch Processing Card
                rx.box(
                    rx.vstack(
                        rx.heading(
                            AppState.tr["batch_title"],
                            size="3",
                            text_align="center",
                            color="#C2410C",
                        ),
                        rx.text(
                            AppState.tr["portal_batch_sub"],
                            font_size="sm",
                            text_align="center",
                            color="#666",
                            margin_bottom="0.75rem",
                        ),
                        rx.divider(border_color="#FDBA74"),
                        rx.unordered_list(
                            rx.list_item(AppState.tr["portal_batch_i1"]),
                            rx.list_item(AppState.tr["portal_batch_i2"]),
                            rx.list_item(AppState.tr["portal_batch_i3"]),
                            rx.list_item(AppState.tr["portal_batch_i4"]),
                            font_size="sm",
                            color="#333",
                            line_height="1.8",
                        ),
                        rx.spacer(),
                        rx.button(
                            AppState.tr["portal_batch_btn"],
                            on_click=lambda: AppState.go_to_batch_processing(),
                            size="2",
                            bg="#EA580C",
                            color="white",
                            width="100%",
                            font_weight="bold",
                            _hover={"bg": "#C2410C"},
                        ),
                        spacing="2",
                    ),
                    padding="1.5rem",
                    bg="linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%)",
                    border_radius="xl",
                    border="2px solid #FDBA74",
                    flex="1",
                    box_shadow="0 4px 6px rgba(234, 88, 12, 0.12)",
                    transition="all 0.3s ease",
                ),
                width="100%",
                spacing="2",
                align_items="stretch",
            ),
            spacing="3",
        ),
        padding="1.5rem 1.5rem",
        bg="white",
        border_radius="lg",
        max_width="1200px",
        margin="0 auto",
    )


# One type size for the whole footer. Headings are set apart by weight and
# colour, not size — mixing sizes in a five-column strip reads as noise.
FOOTER_FONT = "xs"
FOOTER_LINE = "1.7"
_FOOTER_TEXT = dict(font_size=FOOTER_FONT, line_height=FOOTER_LINE, font_weight="500")


def _footer_heading(label) -> rx.Component:
    return rx.text(label, color="#1a472a", font_size=FOOTER_FONT,
                   line_height=FOOTER_LINE, font_weight="700")


def _footer_link(label, href: str = "#") -> rx.Component:
    return rx.link(label, href=href, color="#15803d", is_external=True,
                   **_FOOTER_TEXT)


def _footer_action(label, on_click) -> rx.Component:
    """An in-app action styled exactly like the links around it.

    Deliberately not ``rx.button``: a Radix button carries its own typography
    from ``size=``, which no amount of ``font_size`` fully overrides — that
    mismatch is why these two items rendered larger than everything else.
    """
    return rx.text(label, on_click=on_click, color="#15803d", cursor="pointer",
                   _hover={"text_decoration": "underline"}, **_FOOTER_TEXT)


def _footer_group(title, *items) -> rx.Component:
    """One footer column: a heading over its links."""
    return rx.vstack(
        _footer_heading(title),
        *items,
        spacing="1",
        align_items="flex-start",
    )


def _license_block() -> rx.Component:
    """CC BY 4.0 notice, filling the space to the right of the link columns.

    Label and licence share the first line — "License: CC BY 4.0" — so the
    heading carries the answer instead of costing a line of its own; the terms
    follow underneath.
    """
    return rx.vstack(
        rx.hstack(
            _footer_heading(AppState.tr["license_title"] + ":"),
            rx.link(
                "CC BY 4.0",
                href="https://creativecommons.org/licenses/by/4.0/",
                is_external=True,
                color="#15803d",
                font_size=FOOTER_FONT,
                line_height=FOOTER_LINE,
                font_weight="700",
            ),
            spacing="2",
            align_items="baseline",
        ),
        rx.text(AppState.tr["license_summary"], color="#4b5563",
                font_size=FOOTER_FONT, line_height=FOOTER_LINE, font_weight="500"),
        spacing="1",
        align_items="flex-start",
        max_width="320px",
    )


def footer_section() -> rx.Component:
    """Footer: five compact link columns, with the licence notice on the right.

    Ten links previously sat in three ``flex="1"`` columns inside a 1200px cap,
    so a wide screen showed three tall narrow columns with empty space either
    side. Five auto-fit columns at one small type size use the real width and
    keep the footer short. The licence block takes the space that remains to
    the right, and wraps underneath on narrow screens rather than squeezing the
    columns.
    """
    link_columns = rx.box(
        _footer_group(
            AppState.tr["portal_resources"],
            _footer_link(AppState.tr["documentation"]),
            _footer_link(AppState.tr["portal_link_methods"]),
        ),
        _footer_group(
            AppState.tr["portal_footer_data"],
            _footer_link(AppState.tr["data_sources_title"]),
            _footer_action(
                AppState.tr["previous_runs_title"], AppState.go_to_previous_runs
            ),
        ),
        _footer_group(
            AppState.tr["portal_support"],
            _footer_link(AppState.tr["portal_link_tutorial"]),
            _footer_link(AppState.tr["portal_link_faq"]),
        ),
        _footer_group(
            AppState.tr["about_title"],
            _footer_link(AppState.tr["about_overview"]),
            _footer_link(AppState.tr["portal_link_team"]),
        ),
        _footer_group(
            AppState.tr["portal_footer_contact"],
            _footer_link(AppState.tr["portal_link_contact"]),
            _footer_action(AppState.tr["portal_link_cite"], AppState.toggle_citation),
        ),
        display="grid",
        grid_template_columns="repeat(auto-fit, minmax(150px, 1fr))",
        gap="0.75rem 1.5rem",
        flex="1",
        min_width="320px",
    )

    return rx.box(
        rx.flex(
            link_columns,
            _license_block(),
            wrap="wrap",
            gap="1.5rem",
            align_items="flex-start",
            width="100%",
            max_width="1600px",
            margin="0 auto",
            padding="0.9rem 0",
        ),
        # Border and background sit on the outer box so they span the full
        # viewport; only the content inside is capped at 1600px.
        width="100%",
        padding="0 2rem",
        border_top="3px solid #d0e8d8",
        bg="linear-gradient(135deg, #fafdf8 0%, #f5fdf0 100%)",
    )


def portal() -> rx.Component:
    """Main portal page layout with enhanced design."""
    return rx.vstack(
        portal_navbar(),
        rx.box(
            rx.vstack(
                about_section(),
                analysis_choice_section(),
                spacing="4",
                padding="2rem 1.5rem",
                width="100%",
                max_width="1200px",
                margin="0 auto",
            ),
            width="100%",
            flex="1",
            bg="linear-gradient(180deg, #fafdf8 0%, #f5f9f7 100%)",
            overflow_y="auto",
        ),
        footer_section(),
        citation_modal(),
        width="100%",
        height="100vh",
        spacing="0",
    )
