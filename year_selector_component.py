"""
Year selector component with visual grid (bingo card) style interface.
"""
import streamlit as st


def render_year_selector_grid(
    title: str,
    available_years: list,
    selected_year_key: str,
    cols_per_row: int = 5,
    key_suffix: str = "",
    help_text: str = None,
    show_count: bool = True
):
    """
    Render a visual grid of year buttons (bingo card style).
    
    Args:
        title: Display title for the selector
        available_years: List of years to display
        selected_year_key: Session state key to store selected year
        cols_per_row: Number of columns in the grid (default 7 for calendar-like layout)
        key_suffix: Unique suffix for widget keys
        help_text: Optional help text to display
        show_count: Whether to show count of available years
    
    Returns:
        int: The selected year
    """
    # Initialize selected year if not set
    if selected_year_key not in st.session_state:
        # Default to latest year (last in list)
        st.session_state[selected_year_key] = available_years[-1] if available_years else None
    
    # Display header
    st.write(f"**{title}**")
    
    if help_text:
        st.caption(help_text)
    
    if show_count:
        st.caption(f"📅 {len(available_years)} years available ({min(available_years)} - {max(available_years)})")
    
    # Create grid of years
    current_selected = st.session_state[selected_year_key]
    
    # Organize years into rows
    year_rows = []
    for i in range(0, len(available_years), cols_per_row):
        year_rows.append(available_years[i:i + cols_per_row])
    
    selected_year = None
    
    # Render each row
    for row_idx, year_row in enumerate(year_rows):
        cols = st.columns(len(year_row))
        
        for col_idx, year in enumerate(year_row):
            with cols[col_idx]:
                # Determine button styling
                is_selected = year == current_selected
                button_type = "primary" if is_selected else "secondary"
                button_label = f"{'✓ ' if is_selected else ''}{year}"
                
                # Create button
                if st.button(
                    button_label,
                    key=f"year_btn_{year}_{row_idx}_{col_idx}_{key_suffix}",
                    type=button_type,
                    use_container_width=True
                ):
                    selected_year = year
                    st.session_state[selected_year_key] = year
                    st.rerun()
    
    return st.session_state[selected_year_key]


def render_year_range_selector(
    start_year_key: str,
    end_year_key: str,
    available_years: list,
    key_suffix: str = "",
):
    """
    Render dual year selectors for year range comparison (from year to year).
    
    Args:
        start_year_key: Session state key for start year
        end_year_key: Session state key for end year
        available_years: List of available years
        key_suffix: Unique suffix for widget keys
    """
    # Create two columns for year range
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**From Year:**")
        start_year = render_year_selector_grid(
            title="",
            available_years=available_years,
            selected_year_key=start_year_key,
            cols_per_row=4,
            key_suffix=f"{key_suffix}_from",
            show_count=False
        )
    
    with col2:
        st.write("**To Year:**")
        end_year = render_year_selector_grid(
            title="",
            available_years=available_years,
            selected_year_key=end_year_key,
            cols_per_row=4,
            key_suffix=f"{key_suffix}_to",
            show_count=False
        )
    
    # Validation: end year should be after start year
    if start_year and end_year and start_year >= end_year:
        st.warning(f"⚠️ 'To Year' ({end_year}) should be after 'From Year' ({start_year})")
    
    return start_year, end_year
