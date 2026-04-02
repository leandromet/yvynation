"""
Loading indicator component - shows in top right with different styles for different load types.
Types: "ee" (Earth Engine - blue), "processing" (compute - orange), "preparing" (data prep - purple)
"""

import reflex as rx
from ..state import AppState


def loading_indicator() -> rx.Component:
    """Top-right loading indicator with type-specific colors and symbols."""
    
    # Color and symbol map for different loading types
    def get_indicator() -> rx.Component:
        return rx.cond(
            AppState.loading_message != "",
            rx.cond(
                AppState.loading_type == "ee",
                # Earth Engine - blue, globe symbol
                rx.hstack(
                    rx.spinner(
                        color="rgb(59, 130, 246)",
                        size="2",
                    ),
                    rx.vstack(
                        rx.text(
                            "Earth Engine",
                            font_size="xs",
                            font_weight="bold",
                            color="rgb(59, 130, 246)",
                        ),
                        rx.text(
                            AppState.loading_message,
                            font_size="2xs",
                            color="gray",
                            max_width="180px",
                            overflow="hidden",
                            text_overflow="ellipsis",
                            white_space="nowrap",
                        ),
                        spacing="0",
                    ),
                    spacing="2",
                    padding="0.75rem 1rem",
                    bg="rgb(219, 234, 254)",  # light blue
                    border="1px solid rgb(59, 130, 246)",
                    border_radius="md",
                    align_items="start",
                ),
                rx.cond(
                    AppState.loading_type == "processing",
                    # Processing - orange, gear symbol
                    rx.hstack(
                        rx.spinner(
                            color="rgb(249, 115, 22)",
                            size="2",
                        ),
                        rx.vstack(
                            rx.text(
                                "Processing",
                                font_size="xs",
                                font_weight="bold",
                                color="rgb(249, 115, 22)",
                            ),
                            rx.text(
                                AppState.loading_message,
                                font_size="2xs",
                                color="gray",
                                max_width="180px",
                                overflow="hidden",
                                text_overflow="ellipsis",
                                white_space="nowrap",
                            ),
                            spacing="0",
                        ),
                        spacing="2",
                        padding="0.75rem 1rem",
                        bg="rgb(254, 237, 213)",  # light orange
                        border="1px solid rgb(249, 115, 22)",
                        border_radius="md",
                        align_items="start",
                    ),
                    rx.cond(
                        AppState.loading_type == "preparing",
                        # Preparing - purple, package symbol
                        rx.hstack(
                            rx.spinner(
                                color="rgb(147, 51, 234)",
                                size="2",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Preparing Data",
                                    font_size="xs",
                                    font_weight="bold",
                                    color="rgb(147, 51, 234)",
                                ),
                                rx.text(
                                    AppState.loading_message,
                                    font_size="2xs",
                                    color="gray",
                                    max_width="180px",
                                    overflow="hidden",
                                    text_overflow="ellipsis",
                                    white_space="nowrap",
                                ),
                                spacing="0",
                            ),
                            spacing="2",
                            padding="0.75rem 1rem",
                            bg="rgb(233, 213, 255)",  # light purple
                            border="1px solid rgb(147, 51, 234)",
                            border_radius="md",
                            align_items="start",
                        ),
                        # Default - gray
                        rx.hstack(
                            rx.spinner(
                                color="gray",
                                size="2",
                            ),
                            rx.vstack(
                                rx.text(
                                    "Loading",
                                    font_size="xs",
                                    font_weight="bold",
                                    color="gray",
                                ),
                                rx.text(
                                    AppState.loading_message,
                                    font_size="2xs",
                                    color="gray",
                                    max_width="180px",
                                    overflow="hidden",
                                    text_overflow="ellipsis",
                                    white_space="nowrap",
                                ),
                                spacing="0",
                            ),
                            spacing="2",
                            padding="0.75rem 1rem",
                            bg="rgb(243, 244, 246)",  # light gray
                            border="1px solid rgb(209, 213, 219)",
                            border_radius="md",
                            align_items="start",
                        ),
                    ),
                ),
            ),
            rx.box(),
        )
    
    return rx.box(
        get_indicator(),
        position="fixed",
        top="75px",
        right="20px",
        z_index="99999",
        pointer_events="auto",
    )
