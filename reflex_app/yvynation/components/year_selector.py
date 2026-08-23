"""
Year selector grid component for Reflex.
Provides visual grid (bingo card) style year selection like Streamlit version.
"""

import reflex as rx
from ..state import AppState
from typing import List, Callable


def year_selector_grid(
    title: str,
    available_years: List[int | str],
    selected_year_var,
    on_year_select: Callable,
    cols_per_row: int = 4,
) -> rx.Component:
    """
    Render a visual grid of year buttons (bingo card style).
    
    Args:
        title: Display title for the selector
        available_years: List of years to display
        selected_year_var: Current selected year from state
        on_year_select: Callback function when year is selected
        cols_per_row: Number of columns in the grid
    
    Returns:
        Reflex component with year grid
    """
    # Store years as immutable list
    years_list = [str(y) for y in available_years]
    
    # Create rows of years
    year_rows_data = []
    for i in range(0, len(years_list), cols_per_row):
        year_rows_data.append(years_list[i:i + cols_per_row])
    
    # Convert to a list that can be safely iterated in Reflex
    year_rows = [[str(y) for y in row] for row in year_rows_data]
    
    return rx.vstack(
        rx.text(
            f"📅 {title}",
            font_weight="bold",
            font_size="sm",
        ),
        rx.text(
            f"{len(available_years)} years available ({min(available_years)} - {max(available_years)})",
            font_size="xs",
            color="gray",
        ),
        # Grid of year buttons
        rx.vstack(
            rx.foreach(
                year_rows,
                lambda row: rx.hstack(
                    rx.foreach(
                        row,
                        lambda year: rx.button(
                            rx.cond(
                                selected_year_var == year,
                                rx.text(f"✓ {year}", font_weight="bold"),
                                rx.text(year),
                            ),
                            on_click=lambda y=year: on_year_select(int(y)),
                            width="100%",
                            size="1",
                            is_outline=rx.cond(
                                selected_year_var == year,
                                False,
                                True,
                            ),
                            color_scheme=rx.cond(
                                selected_year_var == year,
                                "green",
                                "gray",
                            ),
                        ),
                    ),
                    width="100%",
                    spacing="1",
                ),
            ),
            width="100%",
            spacing="1",
        ),
        width="100%",
        spacing="2",
    )


def year_range_selector(
    from_year_var,
    to_year_var,
    available_years: List[int | str],
    on_from_year_select: Callable,
    on_to_year_select: Callable,
) -> rx.Component:
    """
    Render dual year selectors for year range comparison.
    
    Args:
        from_year_var: Current start year from state
        to_year_var: Current end year from state
        available_years: List of available years
        on_from_year_select: Callback for start year selection
        on_to_year_select: Callback for end year selection
    
    Returns:
        Reflex component with dual year grids
    """
    return rx.hstack(
        year_selector_grid(
            "From Year",
            available_years,
            from_year_var,
            on_from_year_select,
            cols_per_row=3,
        ),
        year_selector_grid(
            "To Year",
            available_years,
            to_year_var,
            on_to_year_select,
            cols_per_row=3,
        ),
        width="100%",
        spacing="2",
    )
