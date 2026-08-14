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
            rx.vstack(
                rx.heading("📊 " + AppState.tr["data_sources_title"], size="4", color="#2d5a3d"),
                rx.unordered_list(
                    rx.list_item(AppState.tr["portal_ds_mapbiomas"]),
                    rx.list_item(AppState.tr["portal_ds_hansen"]),
                    rx.list_item(AppState.tr["portal_ds_aafc"]),
                    rx.list_item(AppState.tr["portal_ds_gee"]),
                    rx.list_item(AppState.tr["portal_ds_custom"]),
                    font_size="sm",
                    line_height="1.8",
                    color="#444",
                ),
                spacing="2",
            ),
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
                    rx.text(
                        AppState.tr["citation_acknowledgment_text"],
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


def footer_section() -> rx.Component:
    """Footer with enhanced styling."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.heading(AppState.tr["portal_resources"], size="4", color="#1a472a"),
                    rx.link(AppState.tr["documentation"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link(AppState.tr["portal_link_methods"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link(AppState.tr["data_sources_title"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.button(
                        "📂 " + AppState.tr["previous_runs_title"],
                        on_click=AppState.go_to_previous_runs,
                        variant="ghost",
                        size="1",
                        color="#15803d",
                        font_weight="500",
                        padding="0",
                        height="auto",
                        justify_content="flex-start",
                        _hover={"text_decoration": "underline", "bg": "transparent"},
                    ),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading(AppState.tr["portal_support"], size="4", color="#1a472a"),
                    rx.link(AppState.tr["portal_link_tutorial"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link(AppState.tr["portal_link_faq"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link(AppState.tr["portal_link_contact"], href="#", color="#15803d", font_weight="500", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading("ℹ️ " + AppState.tr["about_title"], size="4", color="#1a472a"),
                    rx.link(AppState.tr["about_overview"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link(AppState.tr["portal_link_team"], href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.button(
                        AppState.tr["portal_link_cite"],
                        on_click=AppState.toggle_citation,
                        variant="ghost",
                        size="1",
                        color="#15803d",
                        font_weight="500",
                        padding="0",
                        height="auto",
                        justify_content="flex-start",
                        _hover={"text_decoration": "underline", "bg": "transparent"},
                    ),
                    spacing="2",
                ),
                flex="1",
            ),
            width="100%",
            padding="1.5rem 0",
            gap="2rem",
            max_width="1200px",
            margin="0 auto",
        ),
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
