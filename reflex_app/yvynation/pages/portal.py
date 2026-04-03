"""
Portal/Introduction page for Yvynation Reflex app.
Explains the analysis, data, and methods.
Allows users to choose between geometry or indigenous territory analysis.
"""

import reflex as rx
from ..state import AppState


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
            rx.select(
                {"🇬🇧 English": "en", "🇧🇷 Português": "pt", "🇪🇸 Español": "es"},
                value=AppState.language,
                on_change=AppState.set_language,
                width="300px",
            ),
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
            rx.heading("🌍 About Yvynation", size="3", color="#1a472a"),
            rx.text(
                AppState.tr.get(
                    "about_description",
                    "Yvynation is a comprehensive platform for indigenous land monitoring and analysis. "
                    "It combines satellite imagery, geospatial analysis tools, and forest change detection "
                    "to provide insights into land use changes and ecosystem dynamics.",
                ),
                font_size="md",
                line_height="1.8",
                color="#333",
            ),
            rx.divider(border_color="#d0e8d8"),
            rx.vstack(
                rx.heading("📊 Data Sources", size="4", color="#2d5a3d"),
                rx.unordered_list(
                    rx.list_item("MapBiomas: Brazilian land cover (1985-2023, 30m resolution)"),
                    rx.list_item("Hansen/GFC: Global forest change detection"),
                    rx.list_item("AAFC: Canadian agricultural and forest classification"),
                    rx.list_item("Google Earth Engine: Cloud-based geospatial analysis"),
                    rx.list_item("Custom geometries: Draw or upload your own features"),
                    font_size="sm",
                    line_height="1.8",
                    color="#444",
                ),
                spacing="2",
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
            rx.heading("🚀 Choose Your Analysis Path", size="2", text_align="center", color="#1a472a"),
            rx.text(
                "Select the analysis type that best fits your workflow. Both paths provide access to the same "
                "tools and datasets, optimized for your use case.",
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
                            "🔷 Geometry Analysis",
                            size="3",
                            text_align="center",
                            color="#1e40af",
                        ),
                        rx.text(
                            "Draw & analyze custom areas",
                            font_size="sm",
                            text_align="center",
                            color="#666",
                            margin_bottom="0.75rem",
                        ),
                        rx.divider(border_color="#bfdbfe"),
                        rx.unordered_list(
                            rx.list_item("Draw polygons on the map"),
                            rx.list_item("Upload GeoJSON/Shapefiles/KML"),
                            rx.list_item("Create buffer zones"),
                            rx.list_item("Analyze land cover changes"),
                            font_size="sm",
                            color="#333",
                            line_height="1.8",
                        ),
                        rx.spacer(),
                        rx.button(
                            "→ Start Geometry Analysis",
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
                            "🗺️  Territory Analysis",
                            size="3",
                            text_align="center",
                            color="#15803d",
                        ),
                        rx.text(
                            "Monitor indigenous lands",
                            font_size="sm",
                            text_align="center",
                            color="#666",
                            margin_bottom="0.75rem",
                        ),
                        rx.divider(border_color="#bbf7d0"),
                        rx.unordered_list(
                            rx.list_item("Select from 700+ territories"),
                            rx.list_item("Search by name"),
                            rx.list_item("Track forest changes (1985-2023)"),
                            rx.list_item("Compare multiple years"),
                            font_size="sm",
                            color="#333",
                            line_height="1.8",
                        ),
                        rx.spacer(),
                        rx.button(
                            "→ Start Territory Analysis",
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
                    rx.heading("📚 Resources", size="4", color="#1a472a"),
                    rx.link("Documentation", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("Methods & Research", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("Data Sources", href="#", color="#15803d", font_weight="500", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading("🎓 Support", size="4", color="#1a472a"),
                    rx.link("Tutorial & Guide", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("FAQ", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("Contact & Feedback", href="#", color="#15803d", font_weight="500", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading("ℹ️ About", size="4", color="#1a472a"),
                    rx.link("Project Overview", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("Team & Contributors", href="#", color="#15803d", font_weight="500", is_external=True),
                    rx.link("How to Cite", href="#", color="#15803d", font_weight="500", is_external=True),
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
        width="100%",
        height="100vh",
        spacing="0",
    )
