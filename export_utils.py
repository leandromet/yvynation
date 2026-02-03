"""
Export utilities for Yvynation analysis results.
Handles packaging visualizations, data, and geojson into zip downloads.
"""

import io
import json
import zipfile
import base64
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


def create_export_zip(
    polygon_features=None,
    polygon_analyses=None,
    territory_geom=None,
    territory_name=None,
    territory_analysis_data=None,
    territory_comparison_data=None,
    territory_figures=None,
    all_figures=None,
    metadata=None
):
    """
    Create a zip file with organized analysis exports in subfolders.
    
    Parameters:
    -----------
    polygon_features : list
        List of drawn polygon GeoJSON features
    polygon_analyses : dict
        Dict of {polygon_idx: {analysis_type: {data: df, figures: {name: fig}}}}
    territory_geom : ee.Geometry
        Earth Engine geometry of selected territory
    territory_name : str
        Name of the selected territory
    territory_analysis_data : dict
        Dict of {name: dataframe} for territory analysis tables
    territory_comparison_data : dict
        Dict of {name: dataframe} for territory comparison tables
    territory_figures : dict
        Dict of {name: matplotlib.figure.Figure} for territory plots
    all_figures : dict
        Dict of {name: matplotlib.figure.Figure} for all figures
    metadata : dict
        Metadata about the analysis
        
    Returns:
    --------
    bytes : ZIP file contents as bytes
    """
    
    # Create in-memory zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        
        # 1. Write metadata at root
        if metadata:
            metadata_json = json.dumps(metadata, indent=2, default=str)
            zf.writestr('metadata.json', metadata_json)
        
        # 2. Write GeoJSON data at root
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Add drawn polygons
        if polygon_features:
            for idx, feature in enumerate(polygon_features):
                feature_with_props = {
                    "type": "Feature",
                    "properties": {
                        "name": f"Drawn Polygon {idx + 1}",
                        "timestamp": datetime.now().isoformat()
                    },
                    "geometry": feature.get('geometry')
                }
                geojson_data['features'].append(feature_with_props)
        
        # Add territory boundary if available
        if territory_geom:
            try:
                territory_geojson = territory_geom.getInfo()
                territory_feature = {
                    "type": "Feature",
                    "properties": {
                        "name": territory_name or "Indigenous Territory",
                        "type": "indigenous_territory",
                        "timestamp": datetime.now().isoformat()
                    },
                    "geometry": territory_geojson
                }
                geojson_data['features'].append(territory_feature)
            except Exception as e:
                print(f"Warning: Could not export territory geometry: {e}")
        
        # Write geojson at root
        if geojson_data['features']:
            geojson_str = json.dumps(geojson_data, indent=2)
            zf.writestr('geometries.geojson', geojson_str)
        
        # 3. Write polygon analysis results in organized folders
        if polygon_analyses:
            for polygon_idx, analyses_by_type in polygon_analyses.items():
                polygon_folder = f'polygons/polygon_{polygon_idx + 1}'
                
                for analysis_type, results in analyses_by_type.items():
                    # Write CSV data
                    if results.get('data') is not None:
                        df = results['data']
                        if isinstance(df, pd.DataFrame):
                            csv_str = df.to_csv(index=False)
                            zf.writestr(f'{polygon_folder}/{analysis_type}_data.csv', csv_str)
                    
                    # Write figures for this polygon
                    if results.get('figures'):
                        for fig_name, fig in results['figures'].items():
                            if isinstance(fig, Figure):
                                img_buffer = io.BytesIO()
                                fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                                img_buffer.seek(0)
                                zf.writestr(f'{polygon_folder}/{analysis_type}_{fig_name}.png', img_buffer.getvalue())
                                plt.close(fig)
        
        # 4. Write territory analysis results in organized folder
        if territory_name and (territory_analysis_data or territory_comparison_data or territory_figures):
            territory_folder = f'territory/{territory_name.replace(" ", "_").replace("/", "_")}'
            
            # Write analysis data as CSV
            if territory_analysis_data:
                for name, df in territory_analysis_data.items():
                    if isinstance(df, pd.DataFrame):
                        csv_str = df.to_csv(index=False)
                        zf.writestr(f'{territory_folder}/{name}.csv', csv_str)
            
            # Write comparison data as CSV
            if territory_comparison_data:
                for name, df in territory_comparison_data.items():
                    if isinstance(df, pd.DataFrame):
                        csv_str = df.to_csv(index=False)
                        zf.writestr(f'{territory_folder}/{name}.csv', csv_str)
            
            # Write territory figures as PNG
            if territory_figures:
                for fig_name, fig in territory_figures.items():
                    if isinstance(fig, Figure):
                        img_buffer = io.BytesIO()
                        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                        img_buffer.seek(0)
                        zf.writestr(f'{territory_folder}/{fig_name}.png', img_buffer.getvalue())
                        plt.close(fig)
        
        # 5. Write remaining figures at root level
        if all_figures:
            for name, fig in all_figures.items():
                if isinstance(fig, Figure):
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    zf.writestr(f'figures/{name}.png', img_buffer.getvalue())
                    plt.close(fig)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def capture_current_analysis_exports(session_state):
    """
    Capture all current analysis data and figures from session state.
    Organizes them by polygon and territory for structured export.
    
    Returns:
    --------
    tuple : (polygon_analyses, territory_analysis_data, territory_comparison_data, 
             territory_figures, all_figures, metadata)
    """
    
    polygon_analyses = {}
    territory_analysis_data = {}
    territory_comparison_data = {}
    territory_figures = {}
    all_figures = {}
    
    metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "app": "Yvynation - Indigenous Land Monitoring Platform",
        "author": "Leandro M. Biondo"
    }
    
    # Capture territory analysis data
    if session_state.get('territory_result') is not None:
        territory_name = session_state.get('territory_name') or 'Unknown Territory'
        territory_year = session_state.get('territory_year') or 'Unknown'
        
        territory_analysis_data[f'{territory_name}_analysis_{territory_year}'] = session_state.territory_result
        
        metadata['territory_analyzed'] = str(territory_name)
        metadata['analysis_year'] = str(territory_year)
        metadata['data_source'] = session_state.get('territory_source') or 'Unknown'
        
        # Add comparison data if available
        if session_state.get('territory_result_year2') is not None:
            territory_year2 = session_state.get('territory_year2') or 'Unknown'
            territory_comparison_data[f'{territory_name}_comparison_{territory_year2}'] = session_state.territory_result_year2
            metadata['comparison_year'] = str(territory_year2)
    
    # Capture polygon analysis results
    # Note: These are organized by polygon index if available
    polygon_idx = session_state.get('selected_feature_index', 0)
    
    if session_state.get('mapbiomas_comparison_result') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        
        result = session_state.mapbiomas_comparison_result
        # Extract the DataFrame from the result dict
        if isinstance(result, dict) and 'df' in result:
            polygon_analyses[polygon_idx]['mapbiomas'] = {
                'data': result['df'],
                'year1': result.get('year1'),
                'year2': result.get('year2')
            }
        else:
            # Fallback if it's just a DataFrame
            polygon_analyses[polygon_idx]['mapbiomas'] = {
                'data': result
            }
        metadata['has_mapbiomas_polygon_comparison'] = True
    
    if session_state.get('hansen_comparison_result') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        
        result = session_state.hansen_comparison_result
        # Extract the DataFrame from the result dict
        if isinstance(result, dict) and 'df' in result:
            polygon_analyses[polygon_idx]['hansen'] = {
                'data': result['df'],
                'year1': result.get('year1'),
                'year2': result.get('year2')
            }
        else:
            # Fallback if it's just a DataFrame
            polygon_analyses[polygon_idx]['hansen'] = {
                'data': result
            }
        metadata['has_hansen_polygon_comparison'] = True
    
    # Capture figures organized by polygon
    if session_state.get('analysis_figures'):
        figures = session_state.analysis_figures
        
        # Territory figures
        territory_figure_keys = ['territory_comparison', 'territory_gains_losses', 
                                 'territory_change_percentage', 'territory_distribution']
        for key in territory_figure_keys:
            if key in figures:
                territory_figures[key] = figures[key]
        
        # Polygon figures (store in polygon_analyses if we have polygon analysis)
        polygon_figure_keys = [k for k in figures.keys() if not k.startswith('territory_')]
        for key in polygon_figure_keys:
            all_figures[key] = figures[key]
    
    metadata['num_drawn_polygons'] = len(session_state.get('all_drawn_features', []))
    metadata['num_polygon_analyses'] = len(polygon_analyses)
    metadata['has_territory_analysis'] = session_state.get('territory_result') is not None
    
    return polygon_analyses, territory_analysis_data, territory_comparison_data, territory_figures, all_figures, metadata


def generate_export_button(session_state):
    """
    Generate an export button for the current analysis.
    Organizes exports into folders by polygon and territory.
    
    Parameters:
    -----------
    session_state : streamlit.session_state
        Streamlit session state
        
    Returns:
    --------
    None (renders button and download widget)
    """
    
    # Check if there's anything to export
    has_data = (
        session_state.get('all_drawn_features') or
        session_state.get('territory_result') is not None or
        session_state.get('territory_geom') is not None
    )
    
    if not has_data:
        st.info("💡 No data to export yet. Draw polygons or analyze territories to generate exports.")
        return
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📦 Export All Data & Visualizations", use_container_width=True, key="export_all"):
            with st.spinner("🔄 Preparing export package..."):
                try:
                    # Get data from session state
                    polygon_analyses, territory_data, territory_comparison, territory_figs, all_figs, metadata = capture_current_analysis_exports(session_state)
                    
                    # Add polygon count to metadata
                    metadata['drawn_polygons_count'] = len(session_state.get('all_drawn_features', []))
                    metadata['has_territory'] = session_state.get('territory_geom') is not None
                    
                    # Create zip file with organized structure
                    zip_bytes = create_export_zip(
                        polygon_features=session_state.get('all_drawn_features'),
                        polygon_analyses=polygon_analyses if polygon_analyses else None,
                        territory_geom=session_state.get('territory_geom'),
                        territory_name=session_state.get('territory_name'),
                        territory_analysis_data=territory_data if territory_data else None,
                        territory_comparison_data=territory_comparison if territory_comparison else None,
                        territory_figures=territory_figs if territory_figs else None,
                        all_figures=all_figs if all_figs else None,
                        metadata=metadata
                    )
                    
                    # Generate filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    territory_name = session_state.get('territory_name') or 'analysis'
                    territory_name = territory_name.replace(' ', '_') if territory_name else 'analysis'
                    filename = f'yvynation_export_{territory_name}_{timestamp}.zip'
                    
                    # Provide download button
                    st.download_button(
                        label="📥 Download Export Package",
                        data=zip_bytes,
                        file_name=filename,
                        mime="application/zip",
                        key="download_export_zip"
                    )
                    
                    st.success(f"✅ Export ready! Click above to download {filename}")
                    
                    # Show what's included
                    with st.expander("📋 What's included in this export", expanded=False):
                        st.markdown(f"""
                        ### 📁 ZIP Structure:
                        
                        **Root Level:**
                        - `metadata.json` - Analysis parameters and timestamps
                        - `geometries.geojson` - All drawn polygons + territory boundary
                        
                        **Polygon Results:** (if available)
                        - `polygons/polygon_1/` - Analysis results for polygon 1
                          - `mapbiomas_data.csv` - MapBiomas analysis
                          - `hansen_data.csv` - Hansen analysis
                          - `mapbiomas_*.png` - MapBiomas visualizations
                          - `hansen_*.png` - Hansen visualizations
                        - `polygons/polygon_2/` - (same structure for each polygon)
                        
                        **Territory Results:** (if available)
                        - `territory/{territory_name}/` - All territory analysis results
                          - `*_analysis_*.csv` - Analysis data tables
                          - `*_comparison_*.csv` - Comparison data
                          - `*.png` - All territory visualizations
                        
                        ### 📊 Summary:
                        - **Polygons:** {metadata.get('drawn_polygons_count', 0)} drawn
                        - **Territory:** {"Yes ✓" if metadata.get('has_territory') else "No"}
                        - **Territory Name:** {metadata.get('territory_analyzed', 'N/A')}
                        - **Data Source:** {metadata.get('data_source', 'N/A')}
                        - **Years:** {metadata.get('analysis_year', 'N/A')} {f"to {metadata.get('comparison_year', '')}" if metadata.get('comparison_year') else ""}
                        """)
                
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
