"""
Hansen Class Consolidation - Code Examples
Practical examples for integrating consolidation into hansen_analysis.py
"""

# ==============================================================================
# EXAMPLE 1: Basic Consolidation of Histogram Results
# ==============================================================================

def example_basic_consolidation():
    """
    Shows how to consolidate a simple Hansen histogram
    """
    from hansen_consolidated_utils import get_consolidated_class, get_consolidated_color
    
    # Assuming we have histogram data with class IDs and areas
    histogram_results = {
        'b1': {
            '0': 100,    # 100 pixels of class 0 (Unvegetated)
            '42': 200,   # 200 pixels of class 42 (Dense Short Vegetation)
            '75': 500,   # 500 pixels of class 75 (Dense Tree Cover)
            '240': 50    # 50 pixels of class 240 (Built-up)
        }
    }
    
    # Process to get consolidated classes
    consolidated_results = {}
    for class_id, pixel_count in histogram_results['b1'].items():
        class_id_int = int(class_id)
        consolidated_class = get_consolidated_class(class_id_int)
        
        if consolidated_class not in consolidated_results:
            consolidated_results[consolidated_class] = 0
        consolidated_results[consolidated_class] += pixel_count
    
    print("Consolidated Results:")
    for class_name, pixels in consolidated_results.items():
        color = get_consolidated_color(list(histogram_results['b1'].keys())[0])
        area_ha = pixels * 0.9
        print(f"  {class_name}: {pixels} pixels, {area_ha:.1f} ha")


# ==============================================================================
# EXAMPLE 2: Consolidate a Full DataFrame Histogram
# ==============================================================================

def example_consolidate_dataframe():
    """
    Shows how to consolidate a complete Hansen histogram DataFrame
    """
    import pandas as pd
    from hansen_consolidated_utils import aggregate_to_consolidated
    
    # Simulated Hansen histogram DataFrame (as returned by hansen_histogram_to_dataframe)
    df_hansen = pd.DataFrame({
        'Class_ID': [0, 6, 42, 75, 85, 92, 240, 250, 255],
        'Class': ['Class 0', 'Class 6', 'Class 42', 'Class 75', 'Class 85', 'Class 92', 'Class 240', 'Class 250', 'Class 255'],
        'Pixels': [1000, 500, 2000, 5000, 3000, 1200, 800, 15000, 100],
        'Area_ha': [900, 450, 1800, 4500, 2700, 1080, 720, 13500, 90]
    })
    
    # Consolidate the DataFrame
    df_consolidated = aggregate_to_consolidated(df_hansen)
    
    print("Original DataFrame (9 classes):")
    print(df_hansen[['Class_ID', 'Area_ha']])
    print("\nConsolidated DataFrame:")
    print(df_consolidated[['Consolidated_Class', 'Area_ha']])
    # Output: 5 consolidated classes with aggregated areas


# ==============================================================================
# EXAMPLE 3: Create Year-to-Year Comparison with Consolidation
# ==============================================================================

def example_year_comparison():
    """
    Shows how to compare two years using consolidated classes
    """
    import pandas as pd
    from hansen_consolidated_utils import create_comparison_dataframe
    
    # Simulated data for 2000 and 2020
    df_2000 = pd.DataFrame({
        'Class_ID': [0, 42, 75, 240],
        'Area_ha': [1000, 5000, 50000, 500]
    })
    
    df_2020 = pd.DataFrame({
        'Class_ID': [0, 42, 75, 240],
        'Area_ha': [800, 4500, 48000, 800]  # Forest decreased, urban increased
    })
    
    # Create comparison
    comparison = create_comparison_dataframe(
        df_2000, df_2020, 
        start_year=2000, 
        end_year=2020,
        use_consolidated=True
    )
    
    print("2000-2020 Comparison (Consolidated):")
    print(comparison)
    # Shows: 2000, 2020, Change (ha), % Change for each consolidated class


# ==============================================================================
# EXAMPLE 4: Visualization with Consolidated Classes
# ==============================================================================

def example_visualization():
    """
    Shows how to create visualizations with consolidated colors
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    from hansen_consolidated_utils import (
        aggregate_to_consolidated, 
        get_consolidated_color
    )
    
    # Simulated histogram
    df_hansen = pd.DataFrame({
        'Class_ID': list(range(0, 50)) + [75, 92, 240, 250],
        'Area_ha': [100 + i*50 for i in range(50)] + [50000, 5000, 2000, 15000]
    })
    
    # Consolidate
    df_cons = aggregate_to_consolidated(df_hansen)
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get colors for each consolidated class
    colors = []
    for _, row in df_cons.iterrows():
        # Get color using the first class ID in that group
        color = get_consolidated_color(0)  # In real code, find actual class ID
        colors.append(color)
    
    # Plot
    ax.barh(df_cons['Consolidated_Class'], df_cons['Area_ha'], color=colors)
    ax.set_xlabel('Area (hectares)')
    ax.set_title('Hansen Land Cover Distribution (Consolidated)')
    plt.tight_layout()
    # plt.show()


# ==============================================================================
# EXAMPLE 5: Integration with hansen_analysis.py
# ==============================================================================

def example_hansen_analysis_integration():
    """
    Shows how to integrate consolidation into hansen_analysis.py functions
    """
    # This would go in hansen_analysis.py
    
    import streamlit as st
    import pandas as pd
    from config import HANSEN_DATASETS, HANSEN_LABELS
    from hansen_consolidated_utils import (
        aggregate_to_consolidated,
        get_consolidated_color,
        create_comparison_dataframe,
        summarize_consolidated_stats
    )
    
    def render_hansen_area_analysis_consolidated():
        """
        Updated version of render_hansen_area_analysis with consolidation
        """
        # Original analysis code...
        # df_hansen = hansen_histogram_to_dataframe(stats, hansen_year)
        
        # NEW: Consolidate the results
        # df_consolidated = aggregate_to_consolidated(df_hansen)
        
        # NEW: Visualization with consolidation
        # colors = [get_consolidated_color(int(cid)) for cid in df_consolidated['Class_ID']]
        # fig, ax = st.pyplot()
        # ax.barh(df_consolidated['Consolidated_Class'], df_consolidated['Area_ha'], color=colors)
        
        # NEW: Summary statistics
        # summary = summarize_consolidated_stats(df_consolidated, year=hansen_year)
        # st.metric("Total Area", f"{summary['total_area_ha']:,.0f} ha")
        # st.metric("Largest Class", summary['largest_class'])
        
        pass


# ==============================================================================
# EXAMPLE 6: Switching Between Detailed and Consolidated Views
# ==============================================================================

def example_view_toggle():
    """
    Shows how to add a UI toggle for consolidated vs detailed views
    """
    # This would go in the Streamlit UI
    
    # import streamlit as st
    # from hansen_consolidated_utils import aggregate_to_consolidated
    
    # hansen_view_mode = st.radio(
    #     "Hansen Analysis View",
    #     ["Detailed (256 classes)", "Consolidated (12 classes)"],
    #     index=1
    # )
    
    # if hansen_view_mode == "Consolidated (12 classes)":
    #     df_display = aggregate_to_consolidated(df_original_histogram)
    #     # Use consolidated colors in visualization
    # else:
    #     df_display = df_original_histogram
    #     # Use original colors


# ==============================================================================
# EXAMPLE 7: Summary Statistics by Consolidated Class
# ==============================================================================

def example_summary_statistics():
    """
    Shows how to generate and display summary statistics
    """
    from hansen_consolidated_utils import (
        aggregate_to_consolidated,
        summarize_consolidated_stats
    )
    
    # After consolidating...
    # df_cons = aggregate_to_consolidated(df_hansen)
    
    # Get summary statistics
    # summary = summarize_consolidated_stats(df_cons, year=2020)
    
    # Display summary
    # print(f"Total area analyzed: {summary['total_area_ha']:,.0f} ha")
    # print(f"Number of consolidated classes: {summary['num_classes']}")
    # print(f"Largest class: {summary['largest_class']} ({summary['largest_area_ha']:,.0f} ha)")
    # print("\nClass Breakdown:")
    # for class_name, stats in summary['class_breakdown'].items():
    #     print(f"  {class_name}: {stats['area_ha']:,.0f} ha ({stats['percent']:.1f}%)")


# ==============================================================================
# EXAMPLE 8: Track Deforestation (Tree Cover Loss Analysis)
# ==============================================================================

def example_deforestation_tracking():
    """
    Shows how to specifically track deforestation/afforestation
    """
    from hansen_consolidated_utils import (
        create_comparison_dataframe,
        get_consolidated_class
    )
    
    # Compare 2000 vs 2020
    # comparison = create_comparison_dataframe(df_2000, df_2020, 2000, 2020, use_consolidated=True)
    
    # Focus on tree cover changes
    # tree_classes = ['Dense Tree Cover', 'Open Tree Cover', 'Tree Cover Gain', 'Tree Cover Loss']
    # tree_changes = comparison[comparison.index.isin(tree_classes)]
    
    # Highlight losses (negative changes in Dense Tree Cover)
    # dense_tree_loss = tree_changes.loc['Dense Tree Cover', 'Change (ha)']
    # if dense_tree_loss < 0:
    #     print(f"⚠️ Dense tree cover loss: {abs(dense_tree_loss):,.0f} ha")
    
    # And gains
    # cover_gain = tree_changes.loc['Tree Cover Gain', 'Change (ha)']
    # if cover_gain > 0:
    #     print(f"✅ Tree cover gain: {cover_gain:,.0f} ha")


# ==============================================================================
# EXAMPLE 9: Export Consolidated Results
# ==============================================================================

def example_export_results():
    """
    Shows how to export consolidated results to CSV
    """
    from hansen_consolidated_utils import aggregate_to_consolidated
    
    # df_cons = aggregate_to_consolidated(df_hansen)
    
    # Export to CSV
    # df_cons.to_csv('hansen_consolidated_results.csv', index=False)
    
    # Export with formatting
    # export_df = df_cons.copy()
    # export_df['Area_km2'] = export_df['Area_ha'] / 100
    # export_df['Percent'] = (export_df['Area_ha'] / export_df['Area_ha'].sum() * 100).round(2)
    # export_df = export_df[['Consolidated_Class', 'Area_ha', 'Area_km2', 'Percent']]
    # export_df.to_csv('hansen_results.csv', index=False)


# ==============================================================================
# EXAMPLE 10: Map Pixel Values to Multiple Attributes
# ==============================================================================

def example_pixel_attributes():
    """
    Shows how to get multiple attributes for a pixel value
    """
    from hansen_consolidated_utils import (
        get_consolidated_class,
        get_consolidated_color
    )
    from hansen_consolidated_mapping import HANSEN_CLASS_GROUPING
    
    pixel_value = 42
    
    # Get consolidated class
    class_name = get_consolidated_class(pixel_value)  # "Dense Short Vegetation"
    
    # Get color
    color = get_consolidated_color(pixel_value)  # "#B8D4A8"
    
    # Find which group it belongs to
    # group_name = None
    # for group, classes in HANSEN_CLASS_GROUPING.items():
    #     if pixel_value in classes:
    #         group_name = group
    #         break
    
    # Build comprehensive pixel info
    pixel_info = {
        'pixel_value': pixel_value,
        'consolidated_class': class_name,
        'color': color,
        # 'group': group_name,
    }
    
    return pixel_info


# ==============================================================================
# RUN EXAMPLES
# ==============================================================================

if __name__ == "__main__":
    print("Hansen Class Consolidation - Code Examples")
    print("=" * 70)
    
    print("\n1. Basic Consolidation")
    print("-" * 70)
    example_basic_consolidation()
    
    print("\n2. DataFrame Consolidation")
    print("-" * 70)
    example_consolidate_dataframe()
    
    print("\n3. Year Comparison")
    print("-" * 70)
    example_year_comparison()
    
    print("\n✅ See docstrings above for examples 4-10")
    print("\nAll examples are documented with comments for easy integration!")
