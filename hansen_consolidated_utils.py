"""
Hansen/GLAD Consolidated Analysis Utilities
Provides functions for working with consolidated Hansen land cover classes
"""

import pandas as pd
from hansen_consolidated_mapping import (
    HANSEN_CONSOLIDATED_MAPPING,
    HANSEN_CONSOLIDATED_COLORS,
    HANSEN_CLASS_GROUPING
)


def get_consolidated_class(class_id):
    """
    Map original Hansen class ID to consolidated class name
    
    Args:
        class_id: Original Hansen pixel value (0-255)
        
    Returns:
        Consolidated class name (str)
    """
    class_id = int(class_id)
    return HANSEN_CONSOLIDATED_MAPPING.get(class_id, f"Unknown ({class_id})")


def get_consolidated_color(class_id):
    """
    Get color hex code for consolidated Hansen class
    
    Args:
        class_id: Original Hansen pixel value (0-255)
        
    Returns:
        Color hex code (str)
    """
    consolidated_class = get_consolidated_class(class_id)
    return HANSEN_CONSOLIDATED_COLORS.get(consolidated_class, "#808080")


def aggregate_to_consolidated(df_original):
    """
    Aggregate original Hansen histogram DataFrame to consolidated classes
    
    Args:
        df_original: DataFrame with columns ['Class_ID', 'Class', 'Pixels', 'Area_ha']
        
    Returns:
        DataFrame aggregated by consolidated class
    """
    if df_original.empty:
        return pd.DataFrame()
    
    # Add consolidated class mapping
    df_original = df_original.copy()
    df_original['Consolidated_Class'] = df_original['Class_ID'].apply(get_consolidated_class)
    
    # Aggregate by consolidated class
    consolidated = df_original.groupby('Consolidated_Class').agg({
        'Pixels': 'sum',
        'Area_ha': 'sum'
    }).reset_index()
    
    # Sort by area
    consolidated = consolidated.sort_values('Area_ha', ascending=False)
    
    return consolidated


def get_consolidated_class_count(consolidated_class):
    """
    Get count of original classes in a consolidated class
    
    Args:
        consolidated_class: Name of consolidated class (str)
        
    Returns:
        Number of original classes in this group (int)
    """
    return len(HANSEN_CLASS_GROUPING.get(consolidated_class, []))


def create_comparison_dataframe(df_start, df_end, start_year, end_year, use_consolidated=True):
    """
    Create change comparison between two years
    
    Args:
        df_start: Start year Hansen histogram DataFrame
        df_end: End year Hansen histogram DataFrame
        start_year: Start year (int)
        end_year: End year (int)
        use_consolidated: If True, aggregate to consolidated classes (bool)
        
    Returns:
        DataFrame with change calculations
    """
    if use_consolidated:
        df_start = aggregate_to_consolidated(df_start)
        df_end = aggregate_to_consolidated(df_end)
        index_col = 'Consolidated_Class'
    else:
        index_col = 'Class_ID'
    
    # Merge on index
    df_start_indexed = df_start.set_index(index_col)[['Area_ha']]
    df_end_indexed = df_end.set_index(index_col)[['Area_ha']]
    
    # Full outer join to capture all classes
    comparison = pd.concat([
        df_start_indexed.rename(columns={'Area_ha': f'{start_year}'}),
        df_end_indexed.rename(columns={'Area_ha': f'{end_year}'})
    ], axis=1).fillna(0)
    
    # Calculate changes
    comparison['Change (ha)'] = comparison[str(end_year)] - comparison[str(start_year)]
    comparison['% Change'] = (comparison['Change (ha)'] / comparison[str(start_year)].replace(0, 1) * 100).round(2)
    
    return comparison.sort_values('Change (ha)', key=abs, ascending=False)


def summarize_consolidated_stats(df_consolidated, year=None):
    """
    Generate summary statistics for consolidated classes
    
    Args:
        df_consolidated: DataFrame from aggregate_to_consolidated()
        year: Optional year for reporting (int)
        
    Returns:
        Dictionary with summary statistics
    """
    if df_consolidated.empty:
        return {}
    
    total_area = df_consolidated['Area_ha'].sum()
    
    summary = {
        'total_area_ha': round(total_area, 2),
        'num_classes': len(df_consolidated),
        'largest_class': df_consolidated.iloc[0]['Consolidated_Class'] if len(df_consolidated) > 0 else None,
        'largest_area_ha': round(df_consolidated.iloc[0]['Area_ha'], 2) if len(df_consolidated) > 0 else 0,
        'class_breakdown': {}
    }
    
    for _, row in df_consolidated.iterrows():
        summary['class_breakdown'][row['Consolidated_Class']] = {
            'area_ha': round(row['Area_ha'], 2),
            'percent': round((row['Area_ha'] / total_area * 100), 2),
            'pixels': int(row['Pixels'])
        }
    
    return summary
