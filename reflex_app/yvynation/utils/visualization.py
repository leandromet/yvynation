"""
Phase 4: Visualization utilities for analysis results.
Converts DataFrame analysis results into interactive Plotly charts.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class MapBiomasVisualizer:
    """Generate visualizations for MapBiomas land cover analysis."""
    
    @staticmethod
    def create_area_bar_chart(df: pd.DataFrame) -> go.Figure:
        """
        Create bar chart of land cover area by class.
        
        Args:
            df: DataFrame with columns ['Class_Name', 'Area_ha', 'Percentage']
        
        Returns:
            Plotly Figure with interactive bar chart
        """
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No data available")
            
            fig = go.Figure(data=[
                go.Bar(
                    x=df['Class_Name'],
                    y=df['Area_ha'],
                    text=df['Area_ha'].round(0),
                    textposition='outside',
                    hovertemplate='<b>%{x}</b><br>Area: %{y:,.0f} ha<extra></extra>',
                    marker=dict(
                        color=df['Area_ha'],
                        colorscale='Viridis',
                        showscale=False,
                    ),
                    name='Area (ha)'
                )
            ])
            
            fig.update_layout(
                title='MapBiomas Land Cover Distribution',
                xaxis_title='Land Cover Class',
                yaxis_title='Area (hectares)',
                hovermode='x unified',
                template='plotly_white',
                height=400,
                showlegend=False,
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create area bar chart: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")
    
    @staticmethod
    def create_pie_chart(df: pd.DataFrame) -> go.Figure:
        """
        Create pie chart showing land cover composition by class.
        
        Args:
            df: DataFrame with columns ['Class_Name', 'Area_ha', 'Percentage']
        
        Returns:
            Plotly Figure with interactive pie chart
        """
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No data available")
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=df['Class_Name'],
                    values=df['Area_ha'],
                    hovertemplate='<b>%{label}</b><br>Area: %{value:,.0f} ha (%{percent})<extra></extra>',
                    marker=dict(
                        line=dict(color='white', width=2),
                    )
                )
            ])
            
            fig.update_layout(
                title='Land Cover Composition (% of Total Area)',
                template='plotly_white',
                height=400,
                showlegend=True,
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create pie chart: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")
    
    @staticmethod
    def create_comparison_chart(df1: pd.DataFrame, df2: pd.DataFrame, 
                                year1: int, year2: int) -> go.Figure:
        """
        Create comparison chart between two years.
        
        Args:
            df1: DataFrame for year 1
            df2: DataFrame for year 2
            year1: First year
            year2: Second year
        
        Returns:
            Plotly Figure with side-by-side bars
        """
        try:
            if df1.empty or df2.empty:
                return go.Figure().add_annotation(text="No comparison data available")
            
            # Merge dataframes on Class_Name
            merged = df1[['Class_Name', 'Area_ha']].rename(columns={'Area_ha': f'Area_{year1}'})
            merged = merged.merge(
                df2[['Class_Name', 'Area_ha']].rename(columns={'Area_ha': f'Area_{year2}'}),
                on='Class_Name',
                how='outer'
            )
            merged = merged.fillna(0)
            
            fig = go.Figure(data=[
                go.Bar(
                    name=str(year1),
                    x=merged['Class_Name'],
                    y=merged[f'Area_{year1}'],
                    hovertemplate='<b>%{x}</b><br>' + str(year1) + ': %{y:,.0f} ha<extra></extra>'
                ),
                go.Bar(
                    name=str(year2),
                    x=merged['Class_Name'],
                    y=merged[f'Area_{year2}'],
                    hovertemplate='<b>%{x}</b><br>' + str(year2) + ': %{y:,.0f} ha<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=f'Land Cover Comparison: {year1} vs {year2}',
                xaxis_title='Land Cover Class',
                yaxis_title='Area (hectares)',
                barmode='group',
                hovermode='x unified',
                template='plotly_white',
                height=400,
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create comparison chart: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")


class HansenVisualizer:
    """Generate visualizations for Hansen forest change analysis."""
    
    @staticmethod
    def create_loss_timeline_chart(df: pd.DataFrame) -> go.Figure:
        """
        Create line chart of tree loss over time.
        
        Args:
            df: DataFrame with 'Year' and 'Loss_ha' columns
        
        Returns:
            Plotly Figure
        """
        try:
            if df.empty or 'Year' not in df.columns:
                return go.Figure().add_annotation(text="No timeline data available")
            
            fig = go.Figure(data=[
                go.Scatter(
                    x=df['Year'],
                    y=df['Loss_ha'],
                    mode='lines+markers',
                    name='Tree Loss',
                    line=dict(color='red', width=2),
                    marker=dict(size=6),
                    hovertemplate='<b>Year %{x}</b><br>Loss: %{y:,.0f} ha<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title='Annual Tree Loss (2000-2023)',
                xaxis_title='Year',
                yaxis_title='Loss Area (hectares)',
                hovermode='x unified',
                template='plotly_white',
                height=400,
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create loss timeline: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")
    
    @staticmethod
    def create_forest_balance_chart(df: pd.DataFrame) -> go.Figure:
        """
        Create chart showing tree cover, loss, and gain balance.
        
        Args:
            df: DataFrame from analyze_forest_dynamics() with summary metrics
        
        Returns:
            Plotly Figure
        """
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No balance data available")
            
            # Extract first row summary metrics
            row = df.iloc[0] if len(df) > 0 else {}
            
            cover_2000 = row.get('Tree_Cover_2000_ha', 0)
            loss_total = row.get('Loss_ha', 0)
            gain_total = row.get('Gain_ha', 0)
            
            categories = ['Tree Cover 2000', 'Loss (2000-2023)', 'Gain (2000-2012)']
            values = [cover_2000, loss_total, gain_total]
            colors = ['green', 'red', 'lightgreen']
            
            fig = go.Figure(data=[
                go.Bar(
                    x=categories,
                    y=values,
                    text=[f'{v:,.0f} ha' for v in values],
                    textposition='outside',
                    marker=dict(color=colors),
                    hovertemplate='<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title='Forest Dynamics Summary',
                yaxis_title='Area (hectares)',
                hovermode='x unified',
                template='plotly_white',
                height=400,
                showlegend=False,
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create forest balance chart: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")


def get_chart_for_analysis(analysis_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Generate appropriate chart based on analysis type.
    
    Args:
        analysis_data: Dictionary with 'type' and 'data' keys from AppState.analysis_results
    
    Returns:
        Plotly Figure or None if data is invalid
    """
    try:
        if not analysis_data or 'type' not in analysis_data:
            return None
        
        analysis_type = analysis_data.get('type')
        data = analysis_data.get('data', [])
        
        if not data:
            return None
        
        df = pd.DataFrame(data)
        
        if analysis_type == 'mapbiomas':
            return MapBiomasVisualizer.create_area_bar_chart(df)
        elif analysis_type == 'hansen':
            return HansenVisualizer.create_forest_balance_chart(df)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to generate chart: {e}")
        return None
