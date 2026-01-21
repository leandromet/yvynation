'''
Plotting module for Yvynation.
Handles charts, graphs, and visualizations for analysis results.
'''

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
from config import MAPBIOMAS_COLOR_MAP


def get_bar_colors(df, id_column='Class_ID'):
    '''
    Get colors for bar chart based on MapBiomas class IDs.
    
    Args:
        df (pd.DataFrame): DataFrame with class IDs
        id_column (str): Name of class ID column
    
    Returns:
        list: Colors for each class
    '''
    colors = []
    for class_id in df[id_column]:
        if class_id in MAPBIOMAS_COLOR_MAP:
            colors.append(MAPBIOMAS_COLOR_MAP[class_id])
        else:
            colors.append('#808080')  # Grey for unknown
    return colors


def plot_area_distribution(area_df, year=None, top_n=15, figsize=(12, 6)):
    '''
    Plot horizontal bar chart of land cover areas.
    
    Args:
        area_df (pd.DataFrame): Area statistics
        year (int): Year for title
        top_n (int): Number of top classes to show
        figsize (tuple): Figure size
    
    Returns:
        matplotlib figure object for rendering with st.pyplot()
    '''
    df_top = area_df.head(top_n).copy()
    df_top['Class_Name'] = df_top['Class_Name'].fillna('Unknown')
    colors = get_bar_colors(df_top, 'Class_ID')
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(df_top['Class_Name'], df_top['Area_ha'], color=colors)
    ax.set_xlabel('Area (hectares)', fontsize=12)
    title = f'Land Cover Distribution - {year}' if year else 'Land Cover Distribution'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.invert_yaxis()
    
    plt.tight_layout()
    return fig


def plot_area_comparison(area_start, area_end, start_year, end_year, top_n=15, figsize=(16, 6)):
    '''
    Plot side-by-side comparison of land cover distributions.
    
    Args:
        area_start (pd.DataFrame): Area statistics for start year
        area_end (pd.DataFrame): Area statistics for end year
        start_year (int): Start year
        end_year (int): End year
        top_n (int): Number of top classes to show
        figsize (tuple): Figure size
    
    Returns:
        matplotlib figure object for rendering with st.pyplot()
    '''
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    
    # Start year
    df_start = area_start.head(top_n).copy()
    df_start['Class_Name'] = df_start['Class_Name'].fillna('Unknown')
    colors_start = get_bar_colors(df_start, 'Class_ID')
    
    axes[0].barh(df_start['Class_Name'], df_start['Area_ha'], color=colors_start)
    axes[0].set_xlabel('Area (hectares)', fontsize=11)
    axes[0].set_title(f'Land Cover Distribution - {start_year}', fontsize=12, fontweight='bold')
    axes[0].invert_yaxis()
    
    # End year
    df_end = area_end.head(top_n).copy()
    df_end['Class_Name'] = df_end['Class_Name'].fillna('Unknown')
    colors_end = get_bar_colors(df_end, 'Class_ID')
    
    axes[1].barh(df_end['Class_Name'], df_end['Area_ha'], color=colors_end)
    axes[1].set_xlabel('Area (hectares)', fontsize=11)
    axes[1].set_title(f'Land Cover Distribution - {end_year}', fontsize=12, fontweight='bold')
    axes[1].invert_yaxis()
    
    plt.tight_layout()
    return fig


def plot_area_changes(comparison, start_year, end_year, top_n=15, figsize=(12, 6)):
    '''
    Plot land cover changes as diverging bar chart.
    
    Args:
        comparison (pd.DataFrame): Comparison dataframe with changes
        start_year (int): Start year
        end_year (int): End year
        top_n (int): Number of top changes to show
        figsize (tuple): Figure size
    
    Returns:
        matplotlib figure object for rendering with st.pyplot()
    '''
    df = comparison.head(top_n).copy()
    df['Class_Name'] = df['Class_Name'].fillna('Unknown')
    
    # Color based on gain or loss
    colors = ['green' if x > 0 else 'red' for x in df['Change_km2']]
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(df['Class_Name'], df['Change_km2'], color=colors)
    ax.set_xlabel('Area Change (hectares)', fontsize=12)
    ax.set_title(f'Land Cover Changes ({start_year} to {end_year})', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
    ax.invert_yaxis()
    
    plt.tight_layout()
    return fig


def plot_change_percentage(comparison, start_year, end_year, top_n=15, figsize=(12, 6)):
    '''
    Plot percentage changes in land cover.
    
    Args:
        comparison (pd.DataFrame): Comparison dataframe
        start_year (int): Start year
        end_year (int): End year
        top_n (int): Number of top changes to show
        figsize (tuple): Figure size
    
    Returns:
        matplotlib figure object for rendering with st.pyplot()
    '''
    df = comparison.dropna(subset=['Change_pct']).head(top_n).copy()
    df['Class_Name'] = df['Class_Name'].fillna('Unknown')
    
    colors = ['green' if x > 0 else 'red' for x in df['Change_pct']]
    
    fig, ax = plt.subplots(figsize=figsize)
    ax.barh(df['Class_Name'], df['Change_pct'], color=colors)
    ax.set_xlabel('Percentage Change (%)', fontsize=12)
    ax.set_title(f'Percentage Change in Land Cover ({start_year} to {end_year})', 
                 fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
    ax.invert_yaxis()
    
    plt.tight_layout()
    return fig


def plot_temporal_trend(df_list, years, class_names_to_plot=None, figsize=(12, 6)):
    '''
    Plot temporal trends for selected land cover classes.
    
    Args:
        df_list (list): List of area DataFrames for each year
        years (list): Corresponding years
        class_names_to_plot (list): Class names to include (if None, plot all)
        figsize (tuple): Figure size
    
    Returns:
        matplotlib figure object for rendering with st.pyplot()
    '''
    if len(df_list) != len(years):
        raise ValueError("df_list and years must have same length")
    
    # Combine all data
    combined = pd.concat(df_list, ignore_index=True)
    
    fig, ax = plt.subplots(figsize=figsize)
    
    if class_names_to_plot is None:
        class_names_to_plot = combined['Class_Name'].unique()[:10]
    
    for class_name in class_names_to_plot:
        data = combined[combined['Class_Name'] == class_name].copy()
        data = data.sort_values('Year')
        ax.plot(data['Year'], data['Area_km2'], marker='o', label=class_name, linewidth=2)
    
    ax.set_xlabel('Year', fontsize=12)
    ax.set_ylabel('Area (km²)', fontsize=12)
    ax.set_title('Temporal Trends in Land Cover', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def create_sankey_transitions(transitions_dict, year_start, year_end):
    '''
    Create Sankey diagram for land cover transitions (left to right, ordered by flow).
    Nodes with larger values appear at the top with area displayed.
    
    Args:
        transitions_dict (dict): Transition matrix {source: {target: area, ...}, ...}
                                 Can have '_source_id' key to store representative class ID for coloring
        year_start (int): Start year
        year_end (int): End year
    
    Returns:
        plotly.graph_objects.Figure: Sankey diagram with left-right layout
    '''
    from hansen_consolidated_utils import get_consolidated_color
    
    # Prepare nodes and links
    sources = []
    targets = []
    values = []
    source_colors = []
    
    # Build a mapping of class names to representative IDs for coloring
    class_id_map = {}
    
    for source_id, targets_dict in transitions_dict.items():
        # Extract and store representative class ID if available
        source_id_for_color = targets_dict.pop('_source_id', None) if isinstance(targets_dict, dict) and '_source_id' in targets_dict else None
        
        for target_id, area in targets_dict.items():
            if isinstance(area, (int, float)) and area > 0:
                sources.append(f"{source_id} ({year_start})")
                targets.append(f"{target_id} ({year_end})")
                values.append(area)
                
                # Determine color: use class ID if numeric, otherwise use consolidated color
                if isinstance(source_id, int):
                    color = MAPBIOMAS_COLOR_MAP.get(source_id, '#cccccc')
                elif source_id_for_color is not None:
                    color = get_consolidated_color(source_id_for_color)
                else:
                    color = '#cccccc'
                source_colors.append(color)
    
    if not sources:
        return None
    
    # Get all unique nodes
    all_nodes = list(set(sources + targets))
    
    # Calculate node flow for ordering
    node_flow = {}
    for source, target, value in zip(sources, targets, values):
        node_flow[source] = node_flow.get(source, 0) + value
        node_flow[target] = node_flow.get(target, 0) + value
    
    # Sort nodes by flow (descending - largest values at top)
    sorted_nodes = sorted(all_nodes, key=lambda x: node_flow.get(x, 0), reverse=True)
    
    # Create node labels with area values
    node_labels = []
    for node in sorted_nodes:
        area = node_flow.get(node, 0)
        node_labels.append(f"{node}\n({area:.0f} ha)")
    
    # Create node to index mapping
    node_to_idx = {node: i for i, node in enumerate(sorted_nodes)}
    
    # Get node colors
    node_colors = []
    for node in sorted_nodes:
        # Extract class ID from node label
        class_id_str = node.split(' (')[0]
        try:
            # Try to parse as integer (for numeric class IDs)
            class_id = int(class_id_str)
            color = MAPBIOMAS_COLOR_MAP.get(class_id, '#cccccc')
        except ValueError:
            # It's a consolidated class name, try to get color from consolidated utils
            try:
                color = get_consolidated_color(class_id_str)
            except:
                color = '#cccccc'
        node_colors.append(color)
    
    # Create Sankey
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=node_labels,
            color=node_colors
        ),
        link=dict(
            source=[node_to_idx[s] for s in sources],
            target=[node_to_idx[t] for t in targets],
            value=values,
            color=source_colors,
            label=[f"{s} → {t} ({v:.1f} ha)" for s, t, v in zip(sources, targets, values)]
        )
    )])
    
    fig.update_layout(
        title=f'Land Cover Transitions ({year_start} to {year_end})',
        font=dict(size=10),
        height=1200,
        width=1200
    )
    
    return fig
