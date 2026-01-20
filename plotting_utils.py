"""
Plotting Utilities for Yvynation.
Provides consistent plotting functions for land cover analysis.
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from config import MAPBIOMAS_COLOR_MAP, HANSEN_CONSOLIDATED_COLORS
from hansen_consolidated_utils import get_consolidated_class, get_consolidated_color


def plot_area_distribution(area_df, year=None, top_n=15, figsize=(12, 6)):
    """
    Plot horizontal bar chart of land cover areas.
    
    Args:
        area_df (pd.DataFrame): DataFrame with Class, Class_ID, and Area_ha columns
        year (int or str): Year being displayed (for title)
        top_n (int): Number of top classes to display
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: Plotted figure
    """
    df_top = area_df.head(top_n).copy()
    
    # Determine label column - use "Name" for consolidated classes, otherwise "Class"
    if 'Name' in df_top.columns:
        label_col = 'Name'
    else:
        label_col = 'Class' if 'Class' in df_top.columns else 'Class_ID'
    
    # Get colors based on Class_ID
    if 'Class_ID' in df_top.columns:
        colors = [get_hansen_color(cid) for cid in df_top['Class_ID']]
    else:
        colors = ['#808080'] * len(df_top)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(df_top[label_col], df_top['Area_ha'], color=colors)
    ax.set_xlabel('Area (hectares)', fontsize=12)
    title = f'Land Cover Distribution - {year}' if year else 'Land Cover Distribution'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    plt.tight_layout()
    return fig


def plot_area_comparison(area_start, area_end, start_year, end_year, top_n=15, figsize=(16, 6)):
    """
    Plot side-by-side comparison of land cover distributions.
    
    Args:
        area_start (pd.DataFrame): Land cover data for first year
        area_end (pd.DataFrame): Land cover data for second year
        start_year (int or str): First year
        end_year (int or str): Second year
        top_n (int): Number of top classes to display
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: Plotted figure with side-by-side charts
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    for idx, (data, year, ax) in enumerate([(area_start, start_year, axes[0]), (area_end, end_year, axes[1])]):
        df = data.head(top_n).copy()
        
        # Determine label column - use "Name" for consolidated classes, otherwise "Class"
        if 'Name' in df.columns:
            label_col = 'Name'
        else:
            label_col = 'Class'
        
        # Get colors based on Class_ID
        if 'Class_ID' in df.columns:
            colors = [get_hansen_color(cid) for cid in df['Class_ID']]
        else:
            colors = ['#808080'] * len(df)
        
        ax.barh(df[label_col], df['Area_ha'], color=colors)
        ax.set_xlabel('Area (hectares)', fontsize=11)
        ax.set_title(f'Land Cover Distribution - {year}', fontsize=12, fontweight='bold')
        ax.invert_yaxis()
    
    plt.tight_layout()
    return fig


def get_hansen_color(class_id):
    """
    Get color for Hansen class ID.
    
    Args:
        class_id (int or float): Hansen class ID (0-255)
    
    Returns:
        str: Hex color code
    """
    if isinstance(class_id, (int, float)):
        class_id = int(class_id)
    consolidated = get_consolidated_class(class_id)
    return HANSEN_CONSOLIDATED_COLORS.get(consolidated, "#808080")


def display_summary_metrics(df, title="Summary Statistics"):
    """
    Display summary metrics for a land cover analysis.
    
    Args:
        df (pd.DataFrame): Land cover DataFrame
        title (str): Title for the metrics
    """
    st.markdown(f"### {title}")
    
    total_area = df['Area_ha'].sum()
    num_classes = len(df)
    largest_class = df.loc[df['Area_ha'].idxmax()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Area", f"{total_area:,.0f} ha", help="Total area analyzed")
    with col2:
        st.metric("Classes", num_classes, help="Number of land cover classes detected")
    with col3:
        st.metric("Largest Class", largest_class['Class'], help=f"{largest_class['Area_ha']:,.0f} ha")
