"""
Citation & acknowledgments component for Yvynation Reflex app.

Shown (via a trigger link/button + floating panel) on the portal and all
three analysis pages, so every page credits the underlying data sources,
Google Earth Engine / Google Cloud Research Credits, and gives a proper
"how to cite" text for researchers and journalists reusing the platform's
figures and data.
"""

import reflex as rx
from ..state import AppState


def cite_trigger(color_scheme: str = "green", variant: str = "ghost") -> rx.Component:
    """Small reusable trigger that opens the citation panel."""
    return rx.button(
        "📜 " + AppState.tr["portal_link_cite"],
        on_click=AppState.toggle_citation,
        size="1",
        variant=variant,
        color_scheme=color_scheme,
    )


def citation_modal() -> rx.Component:
    """Floating 'How to cite & acknowledgments' panel, toggled by AppState.show_citation."""
    return rx.cond(
        AppState.show_citation,
        rx.box(
            # Backdrop
            rx.box(
                on_click=AppState.toggle_citation,
                position="fixed",
                top="0",
                left="0",
                width="100vw",
                height="100vh",
                bg="rgba(0,0,0,0.45)",
                z_index="9998",
            ),
            # Panel
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.heading("📜 " + AppState.tr["citation_title"], size="4", color="#1a472a"),
                        rx.spacer(),
                        rx.button(
                            "✕",
                            on_click=AppState.toggle_citation,
                            size="1",
                            variant="ghost",
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    rx.divider(border_color="#d0e8d8"),
                    rx.text(
                        AppState.tr["citation_mission"],
                        font_size="sm",
                        line_height="1.7",
                        color="#333",
                    ),
                    rx.box(
                        rx.vstack(
                            rx.heading(
                                "🛰️ " + AppState.tr["citation_acknowledgment_title"],
                                size="2",
                                color="#1a472a",
                            ),
                            rx.text(
                                AppState.tr["citation_acknowledgment_text"],
                                font_size="sm",
                                line_height="1.7",
                                color="#333",
                            ),
                            # Full acknowledgements live here rather than on the
                            # portal: three dense paragraphs on the landing page
                            # would undo its decluttering, and this panel is
                            # already where people come to credit the work.
                            *[
                                rx.text(
                                    AppState.tr[key],
                                    font_size="xs",
                                    line_height="1.7",
                                    color="#444",
                                )
                                for key in (
                                    "citation_ack_people",
                                    "citation_ack_compute",
                                    "citation_ack_funding",
                                )
                            ],
                            spacing="2",
                            align_items="flex-start",
                        ),
                        padding="0.85rem",
                        bg="#f0fdf4",
                        border="1px solid #bbf7d0",
                        border_radius="md",
                        width="100%",
                    ),
                    rx.heading(AppState.tr["citation_howto_title"], size="3", color="#1a472a"),
                    rx.text(
                        AppState.tr["citation_platform_text"],
                        font_size="sm",
                        font_family="monospace",
                        white_space="pre-wrap",
                        color="#333",
                        bg="#f5f9f7",
                        padding="0.75rem",
                        border="1px solid #e0e0e0",
                        border_radius="md",
                        width="100%",
                    ),
                    rx.text(
                        AppState.tr["citation_datasets_title"],
                        font_size="sm",
                        font_weight="700",
                        color="#2d5a3d",
                        margin_top="0.25rem",
                    ),
                    rx.unordered_list(
                        rx.list_item(AppState.tr["citation_ds_mapbiomas"]),
                        rx.list_item(AppState.tr["citation_ds_hansen"]),
                        rx.list_item(AppState.tr["citation_ds_aafc"]),
                        rx.list_item(AppState.tr["citation_ds_gee"]),
                        font_size="xs",
                        color="#444",
                        line_height="1.8",
                    ),
                    spacing="3",
                    align_items="flex-start",
                    width="100%",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                bg="white",
                padding="1.75rem",
                border_radius="lg",
                box_shadow="0 12px 40px rgba(0,0,0,0.25)",
                width="min(620px, 92vw)",
                max_height="85vh",
                overflow_y="auto",
                z_index="9999",
            ),
        ),
        rx.fragment(),
    )
