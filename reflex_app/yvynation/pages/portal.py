"""
Portal/Introduction page for Yvynation Reflex app.
Explains the analysis, data, and methods.
Allows users to choose between geometry or indigenous territory analysis.
"""

import reflex as rx
from ..state import AppState


def portal_navbar() -> rx.Component:
    """Navigation bar for portal page."""
    return rx.hstack(
        rx.vstack(
            rx.heading(AppState.tr["app_title"], size="2"),
            rx.text(
                AppState.tr["app_subtitle"],
                font_size="sm",
                color="gray",
            ),
            spacing="0",
        ),
        rx.spacer(),
        rx.hstack(
            rx.select(
                ["en", "pt", "es"],
                value=AppState.language,
                on_change=AppState.set_language,
                width="100px",
            ),
            spacing="2",
        ),
        padding="1.5rem 2rem",
        bg="linear-gradient(135deg, #ffffff 0%, #f5f9ff 100%)",
        border_bottom="2px solid #e8f0e8",
        align_items="center",
        width="100%",
    )


def about_section() -> rx.Component:
    """Section explaining the application."""
    return rx.box(
        rx.vstack(
            rx.heading(AppState.tr.get("about_section", "About Yvynation"), size="3"),
            rx.text(
                AppState.tr.get(
                    "about_description",
                    "Yvynation is a comprehensive platform for indigenous land monitoring and analysis. "
                    "It combines satellite imagery, geospatial analysis tools, and forest change detection "
                    "to provide insights into land use changes and ecosystem dynamics.",
                ),
                font_size="md",
                line_height="1.8",
            ),
            rx.divider(),
            rx.heading("Data & Methods", size="4", margin_top="1.5rem"),
            rx.unordered_list(
                rx.list_item("MapBiomas: Land cover classification from 1985-2023"),
                rx.list_item("Hansen/GFC: Global forest change detection"),
                rx.list_item("AAFC: Canadian agricultural and forest classification"),
                rx.list_item("Google Earth Engine: Cloud-based geospatial processing"),
                rx.list_item("Custom geometries: Draw or upload your own features"),
                font_size="sm",
                line_height="1.8",
            ),
            spacing="4",
        ),
        padding="2rem",
        bg="white",
        border_radius="lg",
        border="1px solid #e0e0e0",
        max_width="800px",
        margin="0 auto",
    )


def analysis_choice_section() -> rx.Component:
    """Section to choose between analysis types."""
    return rx.box(
        rx.vstack(
            rx.heading("Choose Your Analysis", size="3", text_align="center"),
            rx.text(
                "Select the type of analysis that best fits your needs. Both options provide access "
                "to the same tools and datasets, but optimized for different workflows.",
                font_size="md",
                text_align="center",
                color="gray",
            ),
            rx.hstack(
                # Geometry Analysis Card
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "🔷 Geometry Analysis",
                            size="4",
                            text_align="center",
                        ),
                        rx.divider(),
                        rx.text(
                            "Draw, upload, or select custom geometries for analysis.",
                            font_size="sm",
                            text_align="center",
                            color="gray",
                            margin_bottom="1rem",
                        ),
                        rx.unordered_list(
                            rx.list_item("Draw geometries directly on the map"),
                            rx.list_item("Upload GeoJSON, Shapefiles, or KML files"),
                            rx.list_item("Create buffers around features"),
                            rx.list_item("Analyze land cover changes"),
                            font_size="sm",
                        ),
                        rx.divider(margin_top="1rem", margin_bottom="1rem"),
                        rx.button(
                            "Start Geometry Analysis",
                            on_click=AppState.go_to_geometry_analysis,
                            size="3",
                            color_scheme="blue",
                            width="100%",
                        ),
                        spacing="3",
                    ),
                    padding="2rem",
                    bg="blue.50",
                    border_radius="lg",
                    border="2px solid #3182ce",
                    flex="1",
                ),
                # Territory Analysis Card
                rx.box(
                    rx.vstack(
                        rx.heading(
                            "🗺️ Indigenous Territory Analysis",
                            size="4",
                            text_align="center",
                        ),
                        rx.divider(),
                        rx.text(
                            "Analyze indigenous lands and territories.",
                            font_size="sm",
                            text_align="center",
                            color="gray",
                            margin_bottom="1rem",
                        ),
                        rx.unordered_list(
                            rx.list_item("Select from predefined indigenous territories"),
                            rx.list_item("Search by territory name"),
                            rx.list_item("Analyze forest change over time"),
                            rx.list_item("Compare multiple years"),
                            font_size="sm",
                        ),
                        rx.divider(margin_top="1.5rem", margin_bottom="1rem"),
                        rx.button(
                            "Start Territory Analysis",
                            on_click=AppState.go_to_territory_analysis,
                            size="3",
                            color_scheme="green",
                            width="100%",
                        ),
                        spacing="3",
                    ),
                    padding="2rem",
                    bg="green.50",
                    border_radius="lg",
                    border="2px solid #22863a",
                    flex="1",
                ),
                width="100%",
                spacing="5",
                align_items="stretch",
            ),
            spacing="5",
        ),
        padding="2rem",
        bg="white",
        border_radius="lg",
        border="1px solid #e0e0e0",
        max_width="1000px",
        margin="0 auto",
    )


def footer_section() -> rx.Component:
    """Footer with additional information."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.heading("Resources", size="4"),
                    rx.link("Documentation", href="#", color="blue", is_external=True),
                    rx.link("Methods", href="#", color="blue", is_external=True),
                    rx.link("Data Sources", href="#", color="blue", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading("Support", size="4"),
                    rx.link("Tutorial", href="#", color="blue", is_external=True),
                    rx.link("FAQ", href="#", color="blue", is_external=True),
                    rx.link("Contact", href="#", color="blue", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.heading("About", size="4"),
                    rx.link("Project", href="#", color="blue", is_external=True),
                    rx.link("Team", href="#", color="blue", is_external=True),
                    rx.link("Citation", href="#", color="blue", is_external=True),
                    spacing="2",
                ),
                flex="1",
            ),
            width="100%",
            padding="2rem 0",
            gap="3rem",
            max_width="1000px",
            margin="0 auto",
        ),
        padding="0 2rem",
        border_top="1px solid #e0e0e0",
        bg="white",
    )


def portal() -> rx.Component:
    """Main portal page layout."""
    return rx.vstack(
        portal_navbar(),
        rx.box(
            rx.vstack(
                about_section(),
                analysis_choice_section(),
                spacing="8",
                padding="4rem 2rem",
                width="100%",
                max_width="1200px",
                margin="0 auto",
            ),
            width="100%",
            flex="1",
            bg="#f9fafb",
            overflow_y="auto",
        ),
        footer_section(),
        width="100%",
        height="100vh",
        spacing="0",
    )
