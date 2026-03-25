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
from translations import t


def create_export_zip(
    polygon_features=None,
    polygon_analyses=None,
    territory_geom=None,
    territory_name=None,
    territory_analysis_data=None,
    territory_comparison_data=None,
    territory_figures=None,
    all_figures=None,
    map_exports=None,
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
    map_exports : dict
        Dict of {map_name: html_string} for exported map overlays
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
                    # Handle transitions data (dict) - save as JSON
                    if analysis_type.endswith('_transitions'):
                        if isinstance(results, dict):
                            json_str = json.dumps(results, indent=2, default=str)
                            clean_type = analysis_type.replace('_transitions', '')
                            zf.writestr(f'{polygon_folder}/{clean_type}_transitions.json', json_str)
                        continue
                    
                    # Handle comparison CSVs (mapbiomas_comparison_csv, hansen_comparison_csv)
                    if analysis_type.endswith('_comparison_csv'):
                        if isinstance(results, pd.DataFrame):
                            csv_str = results.to_csv(index=False)
                            clean_type = analysis_type.replace('_csv', '')
                            zf.writestr(f'{polygon_folder}/{clean_type}.csv', csv_str)
                        continue
                    
                    # Handle nested GFC analysis data (tree_cover, tree_loss, tree_gain)
                    if analysis_type in ['gfc', 'gfc_buffer']:
                        if isinstance(results, dict):
                            for gfc_component, gfc_data in results.items():
                                # gfc_component: 'tree_cover', 'tree_loss', 'tree_gain'
                                # gfc_data: {'data': DataFrame, ...}
                                if isinstance(gfc_data, dict) and gfc_data.get('data') is not None:
                                    df = gfc_data['data']
                                    if isinstance(df, pd.DataFrame):
                                        csv_str = df.to_csv(index=False)
                                        prefix = 'gfc_buffer' if analysis_type == 'gfc_buffer' else 'gfc'
                                        zf.writestr(f'{polygon_folder}/{prefix}_{gfc_component}.csv', csv_str)
                        continue
                    
                    # Write CSV data for standard analyses
                    if isinstance(results, dict) and results.get('data') is not None:
                        df = results['data']
                        if isinstance(df, pd.DataFrame):
                            csv_str = df.to_csv(index=False)
                            zf.writestr(f'{polygon_folder}/{analysis_type}_data.csv', csv_str)
                    
                    # Write figures for this polygon
                    if isinstance(results, dict) and results.get('figures'):
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
                    if name == 'territory_transitions':
                        # Write transitions data as JSON
                        if isinstance(df, dict):
                            json_str = json.dumps(df, indent=2, default=str)
                            zf.writestr(f'{territory_folder}/transitions.json', json_str)
                    elif isinstance(df, pd.DataFrame):
                        csv_str = df.to_csv(index=False)
                        zf.writestr(f'{territory_folder}/{name}.csv', csv_str)
            
            # Write comparison data as CSV
            if territory_comparison_data:
                for name, df in territory_comparison_data.items():
                    if isinstance(df, pd.DataFrame):
                        csv_str = df.to_csv(index=False)
                        zf.writestr(f'{territory_folder}/{name}.csv', csv_str)
            
            # Write territory figures as PNG (or HTML for Plotly)
            if territory_figures:
                for fig_name, fig in territory_figures.items():
                    if isinstance(fig, Figure):
                        img_buffer = io.BytesIO()
                        fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                        img_buffer.seek(0)
                        zf.writestr(f'{territory_folder}/{fig_name}.png', img_buffer.getvalue())
                        plt.close(fig)
                    elif hasattr(fig, 'to_html'):
                        # Plotly figure (e.g., Sankey diagrams) — save as interactive HTML
                        try:
                            html_str = fig.to_html(include_plotlyjs='cdn')
                            zf.writestr(f'{territory_folder}/{fig_name}.html', html_str)
                        except Exception as e:
                            print(f"Warning: Could not export Plotly figure {fig_name}: {e}")
        
        # 5. Write remaining figures at root level (both matplotlib and plotly figures)
        if all_figures:
            for name, fig in all_figures.items():
                if isinstance(fig, Figure):
                    # Matplotlib figure - save as PNG
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                    img_buffer.seek(0)
                    zf.writestr(f'figures/{name}.png', img_buffer.getvalue())
                    plt.close(fig)
                else:
                    # Check if it's a Plotly figure (has to_html method)
                    if hasattr(fig, 'to_html'):
                        try:
                            # Save Plotly figure as interactive HTML
                            html_str = fig.to_html(include_plotlyjs='cdn')
                            zf.writestr(f'figures/{name}.html', html_str)
                        except Exception as e:
                            print(f"Warning: Could not export Plotly figure {name}: {e}")
        
        # 6. Write map exports as PDF files
        if map_exports:
            maps_folder = 'maps'
            for map_name, map_figure in map_exports.items():
                try:
                    if isinstance(map_figure, Figure):
                        # Matplotlib figure - save as PDF
                        pdf_buffer = io.BytesIO()
                        map_figure.savefig(pdf_buffer, format='pdf', dpi=150, bbox_inches='tight')
                        pdf_buffer.seek(0)
                        zf.writestr(f'{maps_folder}/{map_name}.pdf', pdf_buffer.getvalue())
                        plt.close(map_figure)
                    else:
                        print(f"Warning: Map {map_name} is not a matplotlib figure")
                except Exception as e:
                    print(f"Warning: Could not export map {map_name}: {e}")
    
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
    
    # Capture buffer analysis data if available
    if session_state.get('buffer_result_mapbiomas') is not None or session_state.get('buffer_result_hansen') is not None:
        buffer_name = session_state.get('current_buffer_for_analysis', 'Unknown Buffer')
        territory_year = session_state.get('territory_year') or 'Unknown'
        
        if session_state.get('buffer_result_mapbiomas') is not None:
            territory_analysis_data[f'buffer_{buffer_name}_analysis_{territory_year}'] = session_state.buffer_result_mapbiomas
            metadata['buffer_analyzed'] = str(buffer_name)
            metadata['buffer_data_source'] = 'MapBiomas'
            
            # Add buffer comparison data if available
            if session_state.get('buffer_result_mapbiomas_y2') is not None:
                territory_year2 = session_state.get('territory_year2') or 'Unknown'
                territory_comparison_data[f'buffer_{buffer_name}_comparison_{territory_year2}'] = session_state.buffer_result_mapbiomas_y2
                metadata['buffer_comparison_year'] = str(territory_year2)
        
        elif session_state.get('buffer_result_hansen') is not None:
            territory_analysis_data[f'buffer_{buffer_name}_analysis_{territory_year}'] = session_state.buffer_result_hansen
            metadata['buffer_analyzed'] = str(buffer_name)
            metadata['buffer_data_source'] = 'Hansen'
            
            # Add buffer comparison data if available
            if session_state.get('buffer_result_hansen_y2') is not None:
                territory_year2 = session_state.get('territory_year2') or 'Unknown'
                territory_comparison_data[f'buffer_{buffer_name}_comparison_{territory_year2}'] = session_state.buffer_result_hansen_y2
                metadata['buffer_comparison_year'] = str(territory_year2)
    
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
    
    # Add MapBiomas comparison CSV if available
    if session_state.get('mapbiomas_comparison_csv') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        if 'mapbiomas' not in polygon_analyses[polygon_idx]:
            polygon_analyses[polygon_idx]['mapbiomas'] = {}
        # Store the comparison CSV
        polygon_analyses[polygon_idx]['mapbiomas_comparison_csv'] = session_state.mapbiomas_comparison_csv
    
    if session_state.get('hansen_comparison_result') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        
        result = session_state.hansen_comparison_result
        # Extract the comparison DataFrame (df_comp, not df)
        if isinstance(result, dict) and 'df_comp' in result:
            polygon_analyses[polygon_idx]['hansen'] = {
                'data': result['df_comp'],
                'year1': result.get('year1'),
                'year2': result.get('year2'),
                'df1_disp': result.get('df1_disp'),  # Year 1 display data
                'df2_disp': result.get('df2_disp'),  # Year 2 display data
            }
        elif isinstance(result, dict) and 'df' in result:
            # Fallback to 'df' if it exists
            polygon_analyses[polygon_idx]['hansen'] = {
                'data': result['df'],
                'year1': result.get('year1'),
                'year2': result.get('year2')
            }
        metadata['has_hansen_polygon_comparison'] = True
    
    # Add Hansen comparison CSV if available
    if session_state.get('hansen_comparison_csv') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        if 'hansen' not in polygon_analyses[polygon_idx]:
            polygon_analyses[polygon_idx]['hansen'] = {}
        # Store the comparison CSV
        polygon_analyses[polygon_idx]['hansen_comparison_csv'] = session_state.hansen_comparison_csv
    
    # Capture transitions data for polygons
    if session_state.get('mapbiomas_transitions') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        polygon_analyses[polygon_idx]['mapbiomas_transitions'] = session_state.mapbiomas_transitions
    
    if session_state.get('hansen_transitions') is not None:
        if polygon_idx not in polygon_analyses:
            polygon_analyses[polygon_idx] = {}
        polygon_analyses[polygon_idx]['hansen_transitions'] = session_state.hansen_transitions
    
    # Capture Hansen GFC (Global Forest Change) analysis results
    # GFC analysis is stored per area prefix (original, buffer) when analyzed
    for area_prefix in ['original', 'buffer']:
        gfc_session_key = f'hansen_gfc_results_{area_prefix}'
        gfc_results = session_state.get(gfc_session_key)
        
        if gfc_results and isinstance(gfc_results, dict):
            if polygon_idx not in polygon_analyses:
                polygon_analyses[polygon_idx] = {}
            
            gfc_storage = {}
            
            # Capture tree cover data
            if 'tree_cover' in gfc_results:
                df_cover = gfc_results['tree_cover']
                if isinstance(df_cover, pd.DataFrame) and not df_cover.empty:
                    gfc_storage['tree_cover'] = {'data': df_cover}
            
            # Capture tree loss data
            if 'tree_loss' in gfc_results:
                df_loss = gfc_results['tree_loss']
                if isinstance(df_loss, pd.DataFrame) and not df_loss.empty:
                    gfc_storage['tree_loss'] = {'data': df_loss}
            
            # Capture tree gain data
            if 'tree_gain' in gfc_results:
                df_gain = gfc_results['tree_gain']
                if isinstance(df_gain, pd.DataFrame) and not df_gain.empty:
                    gfc_storage['tree_gain'] = {'data': df_gain}
            
            # Store GFC data under appropriate prefix
            if gfc_storage:
                if area_prefix == 'original':
                    polygon_analyses[polygon_idx]['gfc'] = gfc_storage
                    metadata['has_gfc_polygon_analysis'] = True
                elif area_prefix == 'buffer':
                    polygon_analyses[polygon_idx]['gfc_buffer'] = gfc_storage
                    metadata['has_gfc_buffer_analysis'] = True
    
    # Capture territory transitions data if available
    if session_state.get('territory_transitions') is not None:
        territory_analysis_data['territory_transitions'] = session_state.territory_transitions
    
    # Capture figures organized by polygon
    if session_state.get('analysis_figures'):
        figures = session_state.analysis_figures
        
        # Territory figures
        territory_figure_keys = ['territory_comparison', 'territory_gains_losses', 
                                 'territory_change_percentage', 'territory_distribution', 'territory_sankey']
        for key in territory_figure_keys:
            if key in figures:
                territory_figures[key] = figures[key]
        
        # Buffer figures
        buffer_figure_keys = ['buffer_comparison', 'buffer_gains_losses', 
                              'buffer_change_percentage', 'buffer_distribution', 'buffer_sankey']
        for key in buffer_figure_keys:
            if key in figures:
                territory_figures[f'buffer_{key}'] = figures[key]
        
        # Polygon figures (store in polygon_analyses if we have polygon analysis)
        polygon_figure_keys = [k for k in figures.keys() if not k.startswith('territory_') and not k.startswith('buffer_')]
        for key in polygon_figure_keys:
            all_figures[key] = figures[key]
        
        # Also capture polygon-level Sankey figures (original_mapbiomas_sankey, original_hansen_sankey, etc.)
        polygon_sankey_keys = [k for k in figures.keys() 
                               if '_sankey' in k and not k.startswith('territory_') and not k.startswith('buffer_')]
        for key in polygon_sankey_keys:
            if key not in all_figures:
                all_figures[key] = figures[key]
    
    metadata['num_drawn_polygons'] = len(session_state.get('all_drawn_features', []))
    metadata['num_polygon_analyses'] = len(polygon_analyses)
    metadata['has_territory_analysis'] = session_state.get('territory_result') is not None
    
    return polygon_analyses, territory_analysis_data, territory_comparison_data, territory_figures, all_figures, metadata


def generate_export_button(session_state):
    """
    Generate an export button for the current analysis.
    Organizes exports into folders by polygon and territory.
    Includes interactive maps with polygon overlays.
    
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
        st.info(t("no_export_data"))
        return
    
    # Always-visible: show what the export will contain
    with st.expander("📋 What's included in this export", expanded=False):
        # Build live counts from session state (no export needed)
        _figures = session_state.get('analysis_figures', {})
        _n_polygons = len(session_state.get('all_drawn_features', []))
        _has_territory = session_state.get('territory_geom') is not None
        _terr_name = session_state.get('territory_name', 'N/A') or 'N/A'
        _data_source = session_state.get('territory_source', 'N/A') or 'N/A'
        _year1 = session_state.get('territory_year', 'N/A') or 'N/A'
        _year2 = session_state.get('territory_year2', '')
        _years_str = f"{_year1} → {_year2}" if _year2 else str(_year1)
        _has_buffer = session_state.get('buffer_compare_mode', False) and session_state.get('current_buffer_for_analysis')
        _buffer_meta = session_state.get('buffer_metadata', {}).get(session_state.get('current_buffer_for_analysis', ''), {})
        _buffer_km = _buffer_meta.get('buffer_size_km', '') if _has_buffer else ''
        _n_maps = len(session_state.get('prepared_map_exports', {}))
        _n_territory_figs = sum(1 for k in _figures if k.startswith('territory_'))
        _n_buffer_figs = sum(1 for k in _figures if k.startswith('buffer_'))
        _n_polygon_figs = sum(1 for k in _figures if not k.startswith('territory_') and not k.startswith('buffer_'))
        _n_sankey = sum(1 for k in _figures if 'sankey' in k)
        _has_mb_comparison = session_state.get('mapbiomas_comparison_result') is not None
        _has_hansen_comparison = session_state.get('hansen_comparison_result') is not None
        _has_gfc_original = session_state.get('hansen_gfc_results_original') is not None
        _has_gfc_buffer = session_state.get('hansen_gfc_results_buffer') is not None
        _has_territory_result = session_state.get('territory_result') is not None
        _has_territory_transitions = session_state.get('territory_transitions') is not None
        
        st.markdown(f"""
### 📁 ZIP Structure

**📄 Root Level**
| File | Description |
|---|---|
| `metadata.json` | Analysis parameters, timestamps, data sources |
| `geometries.geojson` | GeoJSON FeatureCollection with all drawn polygons and territory boundary |

---

**📍 Polygon Results** — `polygons/polygon_N/` *(one folder per drawn polygon)*
| File | Description |
|---|---|
| `mapbiomas_data.csv` | MapBiomas land cover areas by class |
| `hansen_data.csv` | Hansen/GLAD land cover areas by class |
| `gfc_tree_cover.csv` | **NEW:** Hansen GFC tree cover distribution (% canopy, 0-100) |
| `gfc_tree_loss.csv` | **NEW:** Hansen GFC tree loss by year (2001-2024) |
| `gfc_tree_gain.csv` | **NEW:** Hansen GFC tree gain (2000-2012) |
| `gfc_buffer_tree_cover.csv` | **NEW:** GFC tree cover for buffer zone (if analyzed) |
| `gfc_buffer_tree_loss.csv` | **NEW:** GFC tree loss for buffer zone (if analyzed) |
| `gfc_buffer_tree_gain.csv` | **NEW:** GFC tree gain for buffer zone (if analyzed) |
| `mapbiomas_comparison.csv` | Year-to-year change table (MapBiomas) |
| `hansen_comparison.csv` | Year-to-year change table (Hansen) |
| `mapbiomas_transitions.json` | Pixel-level class-to-class transition matrix (MapBiomas) |
| `hansen_transitions.json` | Pixel-level class-to-class transition matrix (Hansen) |
| `mapbiomas_*.png` | Distribution & comparison charts |
| `hansen_*.png` | Distribution & comparison charts |

---

**🏛️ Territory Results** — `territory/<territory_name>/` *(indigenous territory analysis)*
| File | Description |
|---|---|
| `*_analysis_*.csv` | Land cover area tables for each analyzed year |
| `*_comparison_*.csv` | Year-to-year comparison data |
| `transitions.json` | Pixel-level transition matrix for the territory |
| `territory_comparison.png` | Side-by-side area bar chart (Year 1 vs Year 2) |
| `territory_gains_losses.png` | Horizontal bar chart of gains and losses by class |
| `territory_change_percentage.png` | Percentage change chart by class |
| `territory_distribution.png` | Single-year land cover distribution |
| `territory_sankey.html` | **Interactive Sankey diagram** — land cover transitions (Plotly) |

---

**🔵 Buffer Zone Results** *(if buffer comparison was enabled)*
| File | Description |
|---|---|
| `buffer_buffer_comparison.png` | Buffer zone side-by-side comparison |
| `buffer_buffer_gains_losses.png` | Buffer zone gains & losses |
| `buffer_buffer_change_percentage.png` | Buffer zone % change |
| `buffer_buffer_sankey.html` | **Interactive Sankey diagram** — buffer zone transitions |

---

**📊 Figures** — `figures/` *(polygon-level visualizations)*
| File | Description |
|---|---|
| `original_mapbiomas_sankey.html` | **Interactive Sankey** — polygon MapBiomas transitions |
| `original_hansen_sankey.html` | **Interactive Sankey** — polygon Hansen transitions |
| `*.png` | Other polygon-level charts (matplotlib) |
| `*.html` | Other interactive charts (Plotly) |

---

**🗺️ Map Exports** — `maps/` *(high-quality PDF maps with overlays)*
| File | Description |
|---|---|
| `MapBiomas_*.pdf` | MapBiomas layers with labeled polygons |
| `Hansen_*.pdf` | Hansen layers with labeled polygons |
| `Satellite_Basemap.pdf` | Satellite imagery reference map |
| `GoogleMaps_Basemap.pdf` | Google Maps reference map |

All maps include scale bars, coordinate grid, and labeled polygon boundaries.

---

### 📊 Current Session — What Will Be Exported

| Item | Status |
|---|---|
| **Drawn polygons** | {_n_polygons} |
| **Territory** | {"✅ " + str(_terr_name) if _has_territory else "—  *(select a territory)*"} |
| **Territory analysis** | {"✅ data ready" if _has_territory_result else "—  *(run analysis first)*"} |
| **Territory transitions** | {"✅ Sankey ready" if _has_territory_transitions else "—"} |
| **Buffer zone** | {"✅ " + str(_buffer_km) + " km" if _has_buffer else "—  *(enable in sidebar)*"} |
| **MapBiomas comparison** | {"✅" if _has_mb_comparison else "—"} |
| **Hansen/GLAD comparison** | {"✅" if _has_hansen_comparison else "—"} |
| **Hansen GFC (Polygon)** | {"✅ tree cover, loss, gain" if _has_gfc_original else "—"} |
| **Hansen GFC (Buffer)** | {"✅ tree cover, loss, gain" if _has_gfc_buffer else "—"} |
| **Data source** | {_data_source} |
| **Years** | {_years_str} |
| **Territory figures** | {_n_territory_figs} |
| **Buffer figures** | {_n_buffer_figs} |
| **Polygon figures** | {_n_polygon_figs} |
| **Sankey diagrams** | {_n_sankey} interactive |
| **PDF maps** | {_n_maps} |
        """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📦 Export All Data & Visualizations", width="stretch", key="export_all"):
            with st.spinner("🔄 Preparing export package..."):
                try:
                    # Get data from session state
                    polygon_analyses, territory_data, territory_comparison, territory_figs, all_figs, metadata = capture_current_analysis_exports(session_state)
                    
                    # Use pre-prepared map exports if available (now matplotlib figures, not HTML)
                    map_exports = {}
                    if session_state.get('prepared_map_exports'):
                        map_exports = session_state.get('prepared_map_exports', {})
                        metadata['num_exported_maps'] = len(map_exports)
                        st.info(t("export_maps_prepared", count=len(map_exports)))
                    else:
                        st.info(t("export_maps_no_prepared"))
                        metadata['num_exported_maps'] = 0
                    
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
                        map_exports=map_exports if map_exports else None,
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
                
                except Exception as e:
                    st.error(f"❌ Export failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
