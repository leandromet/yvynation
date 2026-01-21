"""
Plotting Utilities for Yvynation.
Provides consistent plotting functions for land cover analysis.
"""

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from config import MAPBIOMAS_COLOR_MAP
from hansen_glcluc_colors import get_hansen_class_color, HANSEN_CLASS_COLORS


def plot_area_distribution(area_df, year=None, top_n=15, figsize=(12, 6)):
    """
    Plot horizontal bar chart of land cover areas.
    
    Args:
        area_df (pd.DataFrame): DataFrame with Class, Class_ID, and Area_ha columns
        year (int or str): Year being displayed (for title)
        top_n (int): Number of top classes to display (ignored if consolidating)
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: Plotted figure
    """
    df = area_df.copy()
    
    # Aggregate by stratum name if available (Hansen data)
    if 'Name' in df.columns and 'Stratum' in df.columns:
        # Group by stratum name and sum the areas
        df_agg = df.groupby('Name', as_index=False).agg({
            'Area_ha': 'sum',
            'Pixels': 'sum',
            'Stratum': 'first',
            'Class_ID': 'first'  # Get one representative class ID for coloring
        }).sort_values('Area_ha', ascending=False)
        label_col = 'Name'
        # Use the color of the first class in each stratum
        colors = [get_hansen_class_color(cid) for cid in df_agg['Class_ID']]
    elif 'Consolidated_Class' in df.columns:
        # Consolidated Hansen classes - use first top_n by area
        df_agg = df.head(top_n).copy()
        label_col = 'Consolidated_Class'
        # Get colors from consolidated class names
        from hansen_consolidated_utils import HANSEN_CONSOLIDATED_COLORS
        colors = []
        for consolidated_name in df_agg['Consolidated_Class']:
            color = HANSEN_CONSOLIDATED_COLORS.get(consolidated_name, '#808080')
            colors.append(color)
    else:
        # If no Name column, use top N original classes
        df_agg = df.head(top_n).copy()
        # Determine label column
        if 'Class' in df_agg.columns:
            label_col = 'Class'
        elif 'Consolidated_Class' in df_agg.columns:
            label_col = 'Consolidated_Class'
        elif 'Class_ID' in df_agg.columns:
            label_col = 'Class_ID'
        else:
            label_col = df_agg.columns[0]
        
        # Get colors from MapBiomas color map if Class_ID exists, otherwise gray
        if 'Class_ID' in df_agg.columns:
            colors = [MAPBIOMAS_COLOR_MAP.get(int(cid), '#808080') for cid in df_agg['Class_ID']]
        else:
            colors = ['#808080'] * len(df_agg)
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(df_agg[label_col], df_agg['Area_ha'], color=colors)
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
        top_n (int): Number of top classes to display (ignored if consolidating)
        figsize (tuple): Figure size (width, height)
    
    Returns:
        matplotlib.figure.Figure: Plotted figure with side-by-side charts
    """
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    for idx, (data, year, ax) in enumerate([(area_start, start_year, axes[0]), (area_end, end_year, axes[1])]):
        df = data.copy()
        
        # Aggregate by stratum name if available (Hansen data)
        if 'Name' in df.columns and 'Stratum' in df.columns:
            # Group by stratum name and sum the areas
            df_agg = df.groupby('Name', as_index=False).agg({
                'Area_ha': 'sum',
                'Pixels': 'sum',
                'Stratum': 'first',
                'Class_ID': 'first'
            }).sort_values('Area_ha', ascending=False)
            label_col = 'Name'
            # Use the color of the first class in each stratum
            colors = [get_hansen_class_color(cid) for cid in df_agg['Class_ID']]
        elif 'Consolidated_Class' in df.columns:
            # Consolidated Hansen classes - use first top_n by area
            df_agg = df.head(top_n).copy()
            label_col = 'Consolidated_Class'
            # Get colors from consolidated class names
            from hansen_consolidated_utils import get_consolidated_color
            colors = []
            for consolidated_name in df_agg['Consolidated_Class']:
                try:
                    color = get_consolidated_color(consolidated_name)
                except:
                    color = '#808080'
                colors.append(color)
        else:
            # If no Name or Consolidated_Class column, use top N original classes
            df_agg = df.head(top_n).copy()
            # Determine label column
            if 'Class' in df_agg.columns:
                label_col = 'Class'
            elif 'Class_ID' in df_agg.columns:
                label_col = 'Class_ID'
            else:
                label_col = df_agg.columns[0]
            
            # Get colors from MapBiomas color map if Class_ID exists
            if 'Class_ID' in df_agg.columns:
                colors = [MAPBIOMAS_COLOR_MAP.get(int(cid), '#808080') for cid in df_agg['Class_ID']]
            else:
                colors = ['#808080'] * len(df_agg)
        
        ax.barh(df_agg[label_col], df_agg['Area_ha'], color=colors)
        ax.set_xlabel('Area (hectares)', fontsize=11)
        ax.set_title(f'Land Cover Distribution - {year}', fontsize=12, fontweight='bold')
        ax.invert_yaxis()
    
    plt.tight_layout()
    return fig


def get_hansen_color(class_id):
    """
    Get color for Hansen class ID based on stratum.
    
    Args:
        class_id (int or float): Hansen class ID (0-255)
    
    Returns:
        str: Hex color code
    """
    return get_stratum_color(class_id)


def calculate_gains_losses(df_year1, df_year2, class_col='Class_ID', area_col='Area_ha'):
    '''
    Calculate gains and losses for land cover classes between two years.
    
    Args:
        df_year1 (pd.DataFrame): DataFrame for year 1
        df_year2 (pd.DataFrame): DataFrame for year 2
        class_col (str): Column name for class identifier
        area_col (str): Column name for area
    
    Returns:
        pd.DataFrame: Comparison DataFrame with Change_km2, Change_pct, Gains, Losses
    '''
    df1 = df_year1.copy()
    df2 = df_year2.copy()
    
    # Check if we have class names
    has_class_names = 'Class' in df1.columns and class_col != 'Class'
    
    # Prepare merge data with class and area
    merge1 = df1[[class_col, area_col]].copy()
    merge1.columns = [class_col, 'Area_Year1']
    
    merge2 = df2[[class_col, area_col]].copy()
    merge2.columns = [class_col, 'Area_Year2']
    
    # Add class names from year 1 if they exist
    if has_class_names:
        class_names = df1[[class_col, 'Class']].drop_duplicates(subset=[class_col])
        merge1 = merge1.merge(class_names, on=class_col, how='left')
    
    # Drop duplicates to ensure clean merge
    merge1 = merge1.drop_duplicates(subset=[class_col])
    merge2 = merge2.drop_duplicates(subset=[class_col])
    
    # Merge the data
    comparison = pd.merge(merge1, merge2, on=class_col, how='outer')
    
    # Fill NaN values in Area columns
    comparison['Area_Year1'] = comparison['Area_Year1'].fillna(0)
    comparison['Area_Year2'] = comparison['Area_Year2'].fillna(0)
    
    # Calculate changes
    comparison['Change_ha'] = comparison['Area_Year2'] - comparison['Area_Year1']
    comparison['Change_km2'] = comparison['Change_ha'] / 100  # Convert to km²
    comparison['Change_pct'] = (comparison['Change_ha'] / (comparison['Area_Year1'] + 1)) * 100
    
    # Rename class_col to 'Class' only if we don't already have class names
    if not has_class_names and class_col != 'Class':
        comparison.rename(columns={class_col: 'Class'}, inplace=True)
    
    # Sort by absolute change
    comparison['Abs_Change'] = comparison['Change_ha'].abs()
    comparison = comparison.sort_values('Abs_Change', ascending=False)
    
    return comparison


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
