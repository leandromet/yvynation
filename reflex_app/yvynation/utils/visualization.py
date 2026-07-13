"""
Phase 4: Visualization utilities for analysis results.
Converts DataFrame analysis results into interactive Plotly charts.
Replaces Streamlit's matplotlib-based plotting_utils.py and main.py charts.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _get_mapbiomas_colors() -> Dict[int, str]:
    """Get MapBiomas color map from config."""
    try:
        from ..config.config import MAPBIOMAS_COLOR_MAP
        return MAPBIOMAS_COLOR_MAP
    except ImportError:
        return {}


def _get_mapbiomas_labels() -> Dict[int, str]:
    """Get MapBiomas labels from config."""
    try:
        from ..config.config import MAPBIOMAS_LABELS
        return MAPBIOMAS_LABELS
    except ImportError:
        return {}


def _bar_colors_for_df(df: pd.DataFrame, id_col: str = 'Class_ID') -> List[str]:
    """Get color list matching DataFrame rows by class ID."""
    cmap = _get_mapbiomas_colors()
    if id_col not in df.columns:
        return ['#808080'] * len(df)
    return [cmap.get(int(cid), '#808080') for cid in df[id_col]]


# ---------------------------------------------------------------------------
# MapBiomas Visualizer
# ---------------------------------------------------------------------------

class MapBiomasVisualizer:
    """Generate visualizations for MapBiomas land cover analysis."""

    @staticmethod
    def create_area_bar_chart(df: pd.DataFrame, year: Optional[int] = None,
                              top_n: int = 15) -> go.Figure:
        """Horizontal bar chart of land cover area by class."""
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No data available")

            df_top = df.head(top_n).copy()
            name_col = 'Class_Name' if 'Class_Name' in df_top.columns else 'Class'
            colors = _bar_colors_for_df(df_top)

            fig = go.Figure(data=[
                go.Bar(
                    y=df_top[name_col],
                    x=df_top['Area_ha'],
                    orientation='h',
                    text=df_top['Area_ha'].round(0),
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Area: %{x:,.0f} ha<extra></extra>',
                    marker=dict(color=colors),
                    name='Area (ha)',
                )
            ])

            title = f'Land Cover Distribution - {year}' if year else 'Land Cover Distribution'
            fig.update_layout(
                title=title,
                xaxis_title='Area (hectares)',
                yaxis=dict(autorange='reversed'),
                hovermode='y unified',
                template='plotly_white',
                height=max(350, len(df_top) * 28),
                showlegend=False,
                margin=dict(l=180),
            )
            return fig
        except Exception as e:
            logger.error(f"Failed to create area bar chart: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")

    @staticmethod
    def create_pie_chart(df: pd.DataFrame, top_n: int = 12) -> go.Figure:
        """Pie chart of land cover composition."""
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No data available")

            df_top = df.head(top_n).copy()
            name_col = 'Class_Name' if 'Class_Name' in df_top.columns else 'Class'
            colors = _bar_colors_for_df(df_top)

            fig = go.Figure(data=[
                go.Pie(
                    labels=df_top[name_col],
                    values=df_top['Area_ha'],
                    hovertemplate='<b>%{label}</b><br>Area: %{value:,.0f} ha (%{percent})<extra></extra>',
                    marker=dict(colors=colors, line=dict(color='white', width=2)),
                )
            ])
            fig.update_layout(
                title='Land Cover Composition (% of Total)',
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
                                year1: int, year2: int,
                                top_n: int = 12) -> go.Figure:
        """Side-by-side grouped bar chart comparing two years."""
        try:
            if df1.empty or df2.empty:
                return go.Figure().add_annotation(text="No comparison data available")

            name_col = 'Class_Name' if 'Class_Name' in df1.columns else 'Class'
            merged = df1[[name_col, 'Area_ha']].rename(columns={'Area_ha': f'Area_{year1}'})
            merged = merged.merge(
                df2[[name_col, 'Area_ha']].rename(columns={'Area_ha': f'Area_{year2}'}),
                on=name_col, how='outer',
            ).fillna(0)
            # Keep only top classes by combined area
            merged['_total'] = merged[f'Area_{year1}'] + merged[f'Area_{year2}']
            merged = merged.nlargest(top_n, '_total')

            fig = go.Figure(data=[
                go.Bar(name=str(year1), x=merged[name_col], y=merged[f'Area_{year1}'],
                       hovertemplate='<b>%{x}</b><br>' + str(year1) + ': %{y:,.0f} ha<extra></extra>'),
                go.Bar(name=str(year2), x=merged[name_col], y=merged[f'Area_{year2}'],
                       hovertemplate='<b>%{x}</b><br>' + str(year2) + ': %{y:,.0f} ha<extra></extra>'),
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


# ---------------------------------------------------------------------------
# Gains / Losses / Change Charts
# ---------------------------------------------------------------------------

def calculate_gains_losses(df_year1: pd.DataFrame, df_year2: pd.DataFrame,
                           class_col: str = 'Class_ID',
                           area_col: str = 'Area_ha') -> pd.DataFrame:
    """
    Calculate gains and losses between two years.
    Returns DataFrame with Change_ha, Change_km2, Change_pct columns.
    """
    df1, df2 = df_year1.copy(), df_year2.copy()
    has_names = 'Class' in df1.columns and class_col != 'Class'
    name_col = 'Class_Name' if 'Class_Name' in df1.columns else ('Class' if 'Class' in df1.columns else None)

    m1 = df1[[class_col, area_col]].rename(columns={area_col: 'Area_Year1'}).drop_duplicates(subset=[class_col])
    m2 = df2[[class_col, area_col]].rename(columns={area_col: 'Area_Year2'}).drop_duplicates(subset=[class_col])

    if name_col and name_col in df1.columns:
        names = df1[[class_col, name_col]].drop_duplicates(subset=[class_col])
        m1 = m1.merge(names, on=class_col, how='left')

    comp = pd.merge(m1, m2, on=class_col, how='outer').fillna({
        'Area_Year1': 0, 'Area_Year2': 0,
    })
    comp['Change_ha'] = comp['Area_Year2'] - comp['Area_Year1']
    comp['Change_km2'] = comp['Change_ha'] / 100
    comp['Change_pct'] = (comp['Change_ha'] / (comp['Area_Year1'] + 1)) * 100
    comp['Abs_Change'] = comp['Change_ha'].abs()
    comp = comp.sort_values('Abs_Change', ascending=False)

    # Ensure a label column
    if name_col and name_col not in comp.columns:
        comp[name_col] = comp[class_col].astype(str)

    return comp


def create_gains_losses_chart(comparison_df: pd.DataFrame,
                              year1: int, year2: int,
                              top_n: int = 12) -> go.Figure:
    """Diverging horizontal bar chart: green gains, red losses."""
    try:
        if comparison_df.empty:
            return go.Figure().add_annotation(text="No change data available")

        label_col = next((c for c in ['Class_Name', 'Class', 'Class_ID'] if c in comparison_df.columns), None)
        if not label_col:
            return go.Figure().add_annotation(text="Missing class labels")

        df = comparison_df.nlargest(top_n, 'Abs_Change').sort_values('Abs_Change')
        gains = df['Change_km2'].clip(lower=0)
        losses = df['Change_km2'].clip(upper=0)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df[label_col].astype(str), x=gains, orientation='h',
            name='Gains', marker_color='#2ecc71',
            hovertemplate='<b>%{y}</b><br>Gain: %{x:+,.1f} km²<extra></extra>',
        ))
        fig.add_trace(go.Bar(
            y=df[label_col].astype(str), x=losses, orientation='h',
            name='Losses', marker_color='#e74c3c',
            hovertemplate='<b>%{y}</b><br>Loss: %{x:+,.1f} km²<extra></extra>',
        ))
        fig.update_layout(
            title=f'Class Gains and Losses ({year1} to {year2})',
            xaxis_title='Area Change (km²)',
            barmode='overlay',
            template='plotly_white',
            height=max(350, len(df) * 30),
            margin=dict(l=180),
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
        )
        fig.add_vline(x=0, line_width=1.5, line_color='black')
        return fig
    except Exception as e:
        logger.error(f"Gains/losses chart error: {e}")
        return go.Figure().add_annotation(text=f"Error: {str(e)}")


def create_change_percentage_chart(comparison_df: pd.DataFrame,
                                   year1: int, year2: int,
                                   top_n: int = 12) -> go.Figure:
    """Diverging horizontal bar chart of percentage change."""
    try:
        if comparison_df.empty:
            return go.Figure().add_annotation(text="No change data")

        label_col = next((c for c in ['Class_Name', 'Class', 'Class_ID'] if c in comparison_df.columns), None)
        if not label_col:
            return go.Figure().add_annotation(text="Missing labels")

        df = comparison_df.dropna(subset=['Change_pct']).nlargest(top_n, 'Abs_Change').sort_values('Abs_Change')
        colors = ['#2ecc71' if v > 0 else '#e74c3c' for v in df['Change_pct']]

        fig = go.Figure(data=[
            go.Bar(
                y=df[label_col].astype(str), x=df['Change_pct'], orientation='h',
                marker_color=colors,
                hovertemplate='<b>%{y}</b><br>Change: %{x:+.1f}%<extra></extra>',
            )
        ])
        fig.update_layout(
            title=f'Percentage Change ({year1} to {year2})',
            xaxis_title='Change (%)',
            template='plotly_white',
            height=max(350, len(df) * 30),
            margin=dict(l=180),
            showlegend=False,
        )
        fig.add_vline(x=0, line_width=1.5, line_color='black')
        return fig
    except Exception as e:
        logger.error(f"Change percentage chart error: {e}")
        return go.Figure().add_annotation(text=f"Error: {str(e)}")


# ---------------------------------------------------------------------------
# Sankey Transition Diagram
# ---------------------------------------------------------------------------

def create_sankey_transitions(transitions_dict: Dict,
                              year_start: int, year_end: int,
                              class_colors: Optional[Dict] = None,
                              class_names: Optional[Dict] = None) -> Optional[go.Figure]:
    """
    Create Sankey diagram showing land cover class transitions.

    Args:
        transitions_dict: {source_id: {target_id: area_ha, ...}, ...}
        year_start, year_end: Years
        class_colors: class_id -> hex color
        class_names: class_id -> display name
    """
    if not transitions_dict:
        logger.warning(f"Sankey: empty transitions dict received")
        return None
    
    logger.info(f"Sankey: Processing {len(transitions_dict)} sources, {year_start}->{year_end}")

    if class_colors is None:
        class_colors = _get_mapbiomas_colors()
    if class_names is None:
        class_names = _get_mapbiomas_labels()

    sources, targets, values, link_colors = [], [], [], []

    def _resolve_label(class_id) -> str:
        """Return a human-readable class name for an int or string class ID."""
        # Try int key first (class_names is keyed by int)
        try:
            int_id = int(class_id)
            if int_id in class_names:
                return class_names[int_id]
        except (ValueError, TypeError):
            pass
        # Fall back to direct string lookup, then the raw ID
        return class_names.get(class_id, str(class_id))

    def _resolve_color(class_id) -> str:
        try:
            return class_colors.get(int(class_id), class_colors.get(class_id, '#cccccc'))
        except (ValueError, TypeError):
            return class_colors.get(class_id, '#cccccc')

    for src_id, tgt_dict in transitions_dict.items():
        if not isinstance(tgt_dict, dict):
            continue
        for tgt_id, area in tgt_dict.items():
            if isinstance(area, (int, float)) and area > 0:
                src_label = f"{_resolve_label(src_id)} ({year_start})"
                tgt_label = f"{_resolve_label(tgt_id)} ({year_end})"
                sources.append(src_label)
                targets.append(tgt_label)
                values.append(area)
                link_colors.append(_resolve_color(src_id))

    if not sources:
        logger.warning(f"Sankey: No valid transitions found after processing")
        return None
    
    logger.info(f"Sankey: Generated {len(sources)} transitions")

    all_nodes = list(dict.fromkeys(sources + targets))  # ordered unique
    node_flow = {}
    for s, t, v in zip(sources, targets, values):
        node_flow[s] = node_flow.get(s, 0) + v
        node_flow[t] = node_flow.get(t, 0) + v

    sorted_nodes = sorted(all_nodes, key=lambda x: node_flow.get(x, 0), reverse=True)
    node_labels = [f"{n}<br>({node_flow.get(n, 0):,.0f} ha)" for n in sorted_nodes]
    node_to_idx = {n: i for i, n in enumerate(sorted_nodes)}

    node_colors = []
    for node in sorted_nodes:
        raw = node.split(' (')[0] if '(' in node else node
        color = _resolve_color(raw)
        node_colors.append(color)

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=20, thickness=20,
            line=dict(color='black', width=0.5),
            label=node_labels,
            color=node_colors,
        ),
        link=dict(
            source=[node_to_idx[s] for s in sources],
            target=[node_to_idx[t] for t in targets],
            value=values,
            color=link_colors,
            label=[f"{s} -> {t} ({v:,.1f} ha)" for s, t, v in zip(sources, targets, values)],
        ),
    )])
    fig.update_layout(
        title=f'Land Cover Transitions ({year_start} to {year_end})',
        font=dict(size=10),
        height=800,
        template='plotly_white',
    )
    return fig


# ---------------------------------------------------------------------------
# Multi-stage Sankey across N years
# ---------------------------------------------------------------------------

def create_multi_stage_sankey(
    stages: List[Tuple[int, int, Dict]],
    class_colors: Optional[Dict] = None,
    class_names: Optional[Dict] = None,
) -> Optional[go.Figure]:
    """
    Sankey diagram across an arbitrary list of years.

    Args:
        stages: ordered list of ``(year_from, year_to, transitions_dict)``
            where ``transitions_dict`` is the usual
            ``{src_id: {tgt_id: area_ha}}`` mapping. The diagram chains the
            stages: stage[i].year_to must equal stage[i+1].year_from.
        class_colors / class_names: optional overrides; default to the
            MapBiomas palette.

    Returns:
        Plotly Figure, or None when no transition data is present.
    """
    if not stages:
        return None

    if class_colors is None:
        class_colors = _get_mapbiomas_colors()
    if class_names is None:
        class_names = _get_mapbiomas_labels()

    def _resolve_label(class_id) -> str:
        try:
            int_id = int(class_id)
            if int_id in class_names:
                return class_names[int_id]
        except (ValueError, TypeError):
            pass
        return class_names.get(class_id, str(class_id))

    def _resolve_color(class_id) -> str:
        try:
            return class_colors.get(int(class_id), class_colors.get(class_id, '#cccccc'))
        except (ValueError, TypeError):
            return class_colors.get(class_id, '#cccccc')

    # Walk stages, accumulate per-year totals + raw (src, tgt, area) records.
    # Storing records first lets us decide the final node ordering once we
    # know the area totals per (year, class). Each year is counted exactly
    # once — from the *from*-side of its own stage, except the very last
    # year which only appears as a *to*-side.
    year_order = [stages[0][0]] + [s[1] for s in stages]
    year_totals: Dict[int, Dict[str, float]] = {y: {} for y in year_order}
    records: List[Tuple[int, str, int, str, float]] = []
    # records = (y_from, src_id, y_to, tgt_id, area)

    n_stages = len(stages)
    for i, (y_from, y_to, tdict) in enumerate(stages):
        if not isinstance(tdict, dict) or not tdict:
            continue
        is_last = (i == n_stages - 1)
        for src_id, tgt_dict in tdict.items():
            if not isinstance(tgt_dict, dict):
                continue
            for tgt_id, area in tgt_dict.items():
                if not isinstance(area, (int, float)) or area <= 0:
                    continue
                src_key = str(src_id)
                tgt_key = str(tgt_id)
                area = float(area)
                records.append((y_from, src_key, y_to, tgt_key, area))
                # Count this stage's source class toward y_from's total.
                year_totals[y_from][src_key] = year_totals[y_from].get(src_key, 0.0) + area
                # Last year would otherwise never be totalled — pick it up
                # from the to-side of the final stage.
                if is_last:
                    year_totals[y_to][tgt_key] = year_totals[y_to].get(tgt_key, 0.0) + area

    if not records:
        return None

    # Sort classes within each year column by area desc → largest on top
    # (Sankey y axis is 0 at the top, 1 at the bottom in Plotly).
    n_years = len(year_order)
    x_positions: Dict[int, float] = {}
    for i, y in enumerate(year_order):
        # Keep first/last columns slightly inset so labels don't clip.
        x_positions[y] = max(0.001, min(0.999, i / max(n_years - 1, 1)))

    node_index: Dict[Tuple[int, str], int] = {}
    node_labels: List[str] = []
    node_colors: List[str] = []
    node_x: List[float] = []
    node_y: List[float] = []

    GAP = 0.01  # vertical gap between stacked nodes (proportion of column)

    for y in year_order:
        classes = year_totals[y]
        if not classes:
            continue
        total = sum(classes.values()) or 1.0
        # Sort: largest first.
        ordered = sorted(classes.items(), key=lambda kv: kv[1], reverse=True)
        n = len(ordered)
        usable = max(1e-6, 1.0 - GAP * (n - 1))
        cursor = 0.0
        for cls_id, area in ordered:
            frac = area / total
            height = frac * usable
            y_center = cursor + height / 2.0
            cursor += height + GAP
            node_index[(y, cls_id)] = len(node_labels)
            node_labels.append(
                f"{_resolve_label(cls_id)} ({y})<br>{area:,.0f} ha ({frac * 100:.1f}%)"
            )
            node_colors.append(_resolve_color(cls_id))
            node_x.append(x_positions[y])
            # Clamp y to (0, 1) — Plotly rejects exact 0 / 1.
            node_y.append(max(0.001, min(0.999, y_center)))

    sources: List[int] = []
    targets: List[int] = []
    values: List[float] = []
    link_colors: List[str] = []
    for y_from, src_key, y_to, tgt_key, area in records:
        s = node_index.get((y_from, src_key))
        t = node_index.get((y_to, tgt_key))
        if s is None or t is None:
            continue
        sources.append(s)
        targets.append(t)
        values.append(area)
        link_colors.append(_resolve_color(src_key))

    if not sources:
        return None

    title = "Land Cover Transitions — " + " → ".join(str(y) for y in year_order)

    fig = go.Figure(data=[go.Sankey(
        arrangement='fixed',
        node=dict(
            pad=12, thickness=18,
            line=dict(color='black', width=0.4),
            label=node_labels,
            color=node_colors,
            x=node_x,
            y=node_y,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color=link_colors,
            label=[f"{v:,.1f} ha" for v in values],
        ),
    )])
    n_cols = len(year_order)
    fig.update_layout(
        title=title,
        font=dict(size=10),
        # Width scales with number of year columns; 130 px/column matches the
        # current look at 8-year steps (≈6 cols → ~780 px).
        # Height stays fixed — the node stacks per column don't change size
        # with step frequency, only the horizontal spread does.
        width=min(4000, max(700, 130 * n_cols)),
        height=900,
        template='plotly_white',
    )
    return fig


# ---------------------------------------------------------------------------
# Hansen Visualizer
# ---------------------------------------------------------------------------

class HansenVisualizer:
    """Generate visualizations for Hansen forest change analysis."""

    @staticmethod
    def create_loss_timeline_chart(df: pd.DataFrame) -> go.Figure:
        """Line chart of annual tree loss."""
        try:
            if df.empty or 'Year' not in df.columns:
                return go.Figure().add_annotation(text="No timeline data available")

            fig = go.Figure(data=[
                go.Scatter(
                    x=df['Year'], y=df['Loss_ha'],
                    mode='lines+markers', name='Tree Loss',
                    line=dict(color='red', width=2), marker=dict(size=6),
                    hovertemplate='<b>Year %{x}</b><br>Loss: %{y:,.0f} ha<extra></extra>',
                )
            ])
            fig.update_layout(
                title='Annual Tree Loss (2000-2023)',
                xaxis_title='Year', yaxis_title='Loss Area (hectares)',
                hovermode='x unified', template='plotly_white', height=400,
            )
            return fig
        except Exception as e:
            logger.error(f"Loss timeline error: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")

    @staticmethod
    def create_forest_balance_chart(df: pd.DataFrame) -> go.Figure:
        """Bar chart: tree cover 2000, total loss, total gain."""
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No balance data")

            row = df.iloc[0] if len(df) > 0 else {}
            cover = row.get('Tree_Cover_2000_ha', 0)
            loss = row.get('Loss_ha', 0)
            gain = row.get('Gain_ha', 0)

            cats = ['Tree Cover 2000', 'Loss (2000-2023)', 'Gain (2000-2012)']
            vals = [cover, loss, gain]
            colors = ['#2ecc71', '#e74c3c', '#a8e6cf']

            fig = go.Figure(data=[
                go.Bar(
                    x=cats, y=vals,
                    text=[f'{v:,.0f} ha' for v in vals],
                    textposition='outside',
                    marker=dict(color=colors),
                    hovertemplate='<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>',
                )
            ])
            fig.update_layout(
                title='Forest Dynamics Summary',
                yaxis_title='Area (hectares)',
                template='plotly_white', height=400,
                showlegend=False,
            )
            return fig
        except Exception as e:
            logger.error(f"Forest balance chart error: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")

    @staticmethod
    def create_area_distribution_chart(df: pd.DataFrame,
                                       year: Optional[int] = None,
                                       top_n: int = 15) -> go.Figure:
        """Horizontal bar chart for Hansen class distribution."""
        try:
            if df.empty:
                return go.Figure().add_annotation(text="No data available")

            df_top = df.head(top_n).copy()
            name_col = next((c for c in ['Name', 'Consolidated_Class', 'Class', 'Class_ID'] if c in df_top.columns), df_top.columns[0])

            fig = go.Figure(data=[
                go.Bar(
                    y=df_top[name_col].astype(str), x=df_top['Area_ha'],
                    orientation='h',
                    text=df_top['Area_ha'].round(0),
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Area: %{x:,.0f} ha<extra></extra>',
                    marker_color='#3498db',
                )
            ])
            title = f'Hansen Distribution - {year}' if year else 'Hansen Distribution'
            fig.update_layout(
                title=title,
                xaxis_title='Area (hectares)',
                yaxis=dict(autorange='reversed'),
                template='plotly_white',
                height=max(350, len(df_top) * 28),
                margin=dict(l=180),
                showlegend=False,
            )
            return fig
        except Exception as e:
            logger.error(f"Hansen distribution chart error: {e}")
            return go.Figure().add_annotation(text=f"Error: {str(e)}")


def create_sunburst_transitions(transitions_dict: Dict,
                               year_start: int = 2018,
                               year_end: int = 2023,
                               class_colors: Dict = None,
                               class_names: Dict = None) -> Optional[go.Figure]:
    """
    Create a sunburst chart showing land cover transitions between two years.
    Each segment shows how classes change from year1 to year2.
    
    Args:
        transitions_dict: Dict of {class_id_year1: {class_id_year2: area_ha, ...}, ...}
        year_start: First year
        year_end: Second year
        class_colors: Color map for classes
        class_names: Name map for classes
    
    Returns:
        Plotly Figure with sunburst chart
    """
    if not transitions_dict:
        logger.warning(f"Sunburst: empty transitions dict received")
        return None
    
    logger.info(f"Sunburst: Processing {len(transitions_dict)} sources, {year_start}->{year_end}")

    if class_colors is None:
        class_colors = _get_mapbiomas_colors()
    if class_names is None:
        class_names = _get_mapbiomas_labels()

    labels = []
    parents = []
    values = []
    colors = []
    
    # Root
    labels.append(f"Land Cover\n{year_start}→{year_end}")
    parents.append("")
    values.append(0)
    colors.append("#ffffff")
    
    def _name(class_id) -> str:
        """Resolve a class ID (str or int) to its human-readable name."""
        try:
            return class_names.get(int(class_id), class_names.get(class_id, f"Class {class_id}"))
        except (ValueError, TypeError):
            return class_names.get(class_id, f"Class {class_id}")

    def _color(class_id) -> str:
        try:
            return class_colors.get(int(class_id), class_colors.get(class_id, '#cccccc'))
        except (ValueError, TypeError):
            return class_colors.get(class_id, '#cccccc')

    # By source class
    for src_id, tgt_dict in transitions_dict.items():
        if not isinstance(tgt_dict, dict):
            continue

        total_area = sum(a for a in tgt_dict.values() if isinstance(a, (int, float)))
        if total_area <= 0:
            continue

        src_label = _name(src_id)
        full_src_label = f"{src_label}\n({year_start})"
        src_color = _color(src_id)

        labels.append(full_src_label)
        parents.append(f"Land Cover\n{year_start}→{year_end}")
        values.append(total_area)
        colors.append(src_color)

        # Target classes
        for tgt_id, area in tgt_dict.items():
            if not isinstance(area, (int, float)) or area <= 0:
                continue

            tgt_label = _name(tgt_id)
            full_tgt_label = f"{tgt_label}\n({year_end}, {area:,.0f} ha)"

            labels.append(full_tgt_label)
            parents.append(full_src_label)
            values.append(area)
            colors.append(src_color)
    
    if len(labels) < 2:
        logger.warning(f"Sunburst: No valid transitions found after processing")
        return None
    
    logger.info(f"Sunburst: Generated {len(labels)} labels")
    
    fig = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        marker=dict(
            colors=colors,
            line=dict(color='white', width=2),
        ),
        hovertemplate='<b>%{label}</b><br>Area: %{value:,.0f} ha<extra></extra>',
        textfont=dict(size=11),
    ))
    
    fig.update_layout(
        title=f'Land Cover Transitions ({year_start}→{year_end}) - Sunburst View',
        height=700,
        font=dict(size=10),
        template='plotly_white',
        margin=dict(t=80, l=0, r=0, b=0),
    )
    
    logger.info(f"Sunburst: Successfully created figure with {len(labels)} labels")
    return fig


# ---------------------------------------------------------------------------
# Faceted per-class transition treemaps
# ---------------------------------------------------------------------------

def create_class_transition_treemaps(transitions_dict: Dict,
                                     year_start: int,
                                     year_end: int,
                                     class_colors: Optional[Dict] = None,
                                     class_names: Optional[Dict] = None,
                                     top_n: int = 8,
                                     min_transition_pct: float = 1.0,
                                     max_cols: int = 3,
                                     include_others: bool = True,
                                     class_totals: Optional[Dict] = None) -> Optional[go.Figure]:
    """
    Faceted per-class transition treemaps.

    One small treemap per source class, laid out in a grid. Each facet shows
    where that class went between ``year_start`` and ``year_end`` — its
    destination classes (persistence excluded), sized by area. The persistence
    share is reported in the facet title, mirroring the original matplotlib
    ``create_class_transition_treemaps`` (where a bar carried persistence and
    the treemap carried the changes).

    Only the largest ``top_n`` source classes get their own facet; the
    remaining (smaller-area) source classes are rolled into a single trailing
    **"Others"** facet whose tiles break those classes out individually (one
    tile per class, sized by its changed area) so nothing is hidden.

    Reuses the exact transition structure that feeds the Sankey/Sunburst
    charts, so it can be driven from the same state.

    Args:
        transitions_dict: ``{source_id: {target_id: area_ha, ...}, ...}``.
            Persistence flows (``src == tgt``) are tolerated and treated as
            "stayed" rather than plotted as a transition tile.
        year_start, year_end: period bounds (used for titles only).
        class_colors: class_id -> hex color (defaults to MapBiomas palette).
        class_names: class_id -> display name (defaults to MapBiomas labels).
        top_n: number of largest source classes to give their own facet,
            clamped to the range [2, 8]. Smaller classes go to "Others".
        min_transition_pct: drop destinations below this percentage of the
            class's *changed* area (filters visual noise).
        max_cols: facets per row.
        include_others: when True (default), append the detailed "Others"
            facet for source classes beyond ``top_n``.
        class_totals: optional ``{class_id: original_area_ha}`` (e.g. the
            year-start composition). When provided, the persistence percentage
            in each facet title is computed against the class's *original*
            area — correct even when ``transitions_dict`` only carries the
            changed portion (no ``src == tgt`` flows). When omitted, the
            percentage falls back to the in-dict total (which already includes
            persistence for ``include_unchanged`` transition dicts).

    Returns:
        Plotly Figure with one treemap subplot per class (plus an optional
        "Others" facet), or None when there is no transition data to show.
    """
    if not transitions_dict:
        logger.warning("Treemap: empty transitions dict received")
        return None

    if class_colors is None:
        class_colors = _get_mapbiomas_colors()
    if class_names is None:
        class_names = _get_mapbiomas_labels()

    def _resolve_label(class_id) -> str:
        try:
            int_id = int(class_id)
            if int_id in class_names:
                return class_names[int_id]
        except (ValueError, TypeError):
            pass
        return class_names.get(class_id, str(class_id))

    def _resolve_color(class_id) -> str:
        try:
            return class_colors.get(int(class_id), class_colors.get(class_id, '#cccccc'))
        except (ValueError, TypeError):
            return class_colors.get(class_id, '#cccccc')

    def _same_class(a, b) -> bool:
        """True when two class IDs refer to the same class (int or str keyed)."""
        if a == b:
            return True
        try:
            return int(a) == int(b)
        except (ValueError, TypeError):
            return False

    def _resolve_total(class_id):
        """Original-area lookup in ``class_totals`` tolerant of int/str keys."""
        if not class_totals:
            return None
        if class_id in class_totals:
            return class_totals[class_id]
        try:
            return class_totals.get(int(class_id), class_totals.get(str(class_id)))
        except (ValueError, TypeError):
            return class_totals.get(str(class_id))

    # ---- Aggregate each source class: total / persisted / destinations ----
    facets = []  # [{"label","color","total","changed","title","dests":[(label,area,pct,color)]}]
    for src_id, tgt_dict in transitions_dict.items():
        if not isinstance(tgt_dict, dict):
            continue

        total = sum(a for a in tgt_dict.values() if isinstance(a, (int, float)) and a > 0)
        if total <= 0:
            continue

        persisted = 0.0
        raw_dests = []  # (tgt_id, area)
        for tgt_id, area in tgt_dict.items():
            if not isinstance(area, (int, float)) or area <= 0:
                continue
            if _same_class(src_id, tgt_id):
                persisted += area
            else:
                raw_dests.append((tgt_id, area))

        changed = total - persisted  # area that left the class (excl. persistence)
        if changed <= 0 or not raw_dests:
            continue  # class that only persisted — nothing to "become"

        dests = []
        for tgt_id, area in raw_dests:
            pct = 100.0 * area / changed if changed > 0 else 0.0
            if pct >= min_transition_pct:
                dests.append((_resolve_label(tgt_id), float(area), pct, _resolve_color(tgt_id)))
        if not dests:
            continue
        dests.sort(key=lambda d: -d[1])

        # Persistence % is relative to the class's ORIGINAL area. Prefer the
        # supplied year-start total (works for change-only dicts); otherwise
        # fall back to the in-dict total (correct when persistence flows are
        # present, e.g. include_unchanged multi-window dicts).
        original = _resolve_total(src_id)
        if not isinstance(original, (int, float)) or original <= 0:
            original = total
        persisted_real = max(0.0, float(original) - changed)
        pers_pct = 100.0 * persisted_real / original if original > 0 else 0.0
        facets.append({
            "label": _resolve_label(src_id),
            "color": _resolve_color(src_id),
            "total": float(total),
            "changed": float(changed),
            "title": f"{_resolve_label(src_id)} — {pers_pct:.0f}% persistent",
            "dests": dests,
        })

    if not facets:
        logger.warning("Treemap: no source classes with significant transitions")
        return None

    facets.sort(key=lambda f: -f["total"])

    # ---- Keep the largest 2–8 classes; roll the rest into a detailed "Others"
    top_n = max(2, min(8, int(top_n)))
    keep = facets[:top_n]
    rest = facets[top_n:]
    if include_others and rest:
        others_changed = sum(f["changed"] for f in rest) or 1.0
        others_dests = sorted(
            (
                (f["label"], f["changed"], 100.0 * f["changed"] / others_changed, f["color"])
                for f in rest
            ),
            key=lambda d: -d[1],
        )
        keep.append({
            "label": "Others",
            "color": "#9e9e9e",
            "total": sum(f["total"] for f in rest),
            "changed": others_changed,
            "title": f"Others — {len(rest)} smaller classes",
            "dests": others_dests,
        })
    facets = keep

    # ---- Lay facets out in a grid of treemap subplots ----------------------
    import math
    from plotly.subplots import make_subplots

    n = len(facets)
    cols = max(1, min(max_cols, n))
    rows = math.ceil(n / cols)

    subplot_titles = [f["title"] for f in facets]
    fig = make_subplots(
        rows=rows, cols=cols,
        specs=[[{"type": "domain"} for _ in range(cols)] for _ in range(rows)],
        subplot_titles=subplot_titles,
        horizontal_spacing=0.02,
        vertical_spacing=max(0.04, 0.18 / rows),
    )

    for i, f in enumerate(facets):
        r, c = i // cols + 1, i % cols + 1
        labels = [d[0] for d in f["dests"]]
        values = [d[1] for d in f["dests"]]
        pcts = [d[2] for d in f["dests"]]
        colors = [d[3] for d in f["dests"]]
        fig.add_trace(
            go.Treemap(
                labels=labels,
                parents=[""] * len(labels),
                values=values,
                customdata=pcts,
                marker=dict(colors=colors, line=dict(color="white", width=1)),
                texttemplate="%{label}<br>%{value:,.0f} ha<br>%{customdata:.0f}%",
                hovertemplate=(
                    "<b>%{label}</b><br>%{value:,.0f} ha"
                    "<br>%{customdata:.1f}% of change<extra></extra>"
                ),
                textfont=dict(size=10),
                tiling=dict(pad=1),
                branchvalues="remainder",
            ),
            row=r, col=c,
        )

    fig.update_layout(
        title=f"Land Cover Transition Treemaps by Class ({year_start}→{year_end})",
        height=max(360, rows * 300),
        template="plotly_white",
        margin=dict(t=70, l=10, r=10, b=10),
        font=dict(size=10),
    )
    # Paint each facet title with its source-class colour (as a chip, with an
    # auto-contrast text colour so pale palette entries stay legible). The
    # subplot-title annotations are emitted in facet order, so they zip 1:1.
    def _text_on(hex_color: str) -> str:
        try:
            h = hex_color.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            return '#000000' if (0.299 * r + 0.587 * g + 0.114 * b) > 140 else '#ffffff'
        except Exception:
            return '#000000'

    for ann, f in zip(fig.layout.annotations, facets):
        ann.font = dict(size=11, color=_text_on(f["color"]))
        ann.bgcolor = f["color"]
        ann.bordercolor = "#ffffff"
        ann.borderwidth = 1
        ann.borderpad = 3

    logger.info(f"Treemap: built {n} facet treemaps ({rows}x{cols})")
    return fig


# ---------------------------------------------------------------------------
# Dispatcher: choose chart from analysis_results dict
# ---------------------------------------------------------------------------

def _create_gfc_summary_chart(df: "pd.DataFrame") -> go.Figure:
    """Bar chart for the 3-row GFC summary (Tree Cover, Forest Loss, Forest Gain)."""
    try:
        metrics = df["Metric"].tolist()
        areas = df["Area_ha"].tolist()
        percents = df["Percent"].tolist() if "Percent" in df.columns else [""] * len(metrics)
        colors = ["#2ecc71", "#e74c3c", "#a8e6cf"]
        fig = go.Figure(data=[
            go.Bar(
                x=metrics,
                y=areas,
                text=[f"{a:,.0f} ha  {p}" for a, p in zip(areas, percents)],
                textposition="outside",
                marker=dict(color=colors[: len(metrics)]),
                hovertemplate="<b>%{x}</b><br>%{y:,.0f} ha<extra></extra>",
            )
        ])
        fig.update_layout(
            title="Forest Dynamics Summary (Hansen GFC)",
            yaxis_title="Area (hectares)",
            template="plotly_white",
            height=400,
            showlegend=False,
        )
        return fig
    except Exception as e:
        logger.error(f"GFC summary chart error: {e}")
        return go.Figure().add_annotation(text=f"Error: {str(e)}")


def get_chart_for_analysis(analysis_data: Dict[str, Any],
                           chart_type: str = 'bar') -> Optional[go.Figure]:
    """
    Generate appropriate chart based on analysis type and requested chart_type.

    chart_type: 'bar', 'pie', 'comparison', 'gains_losses', 'change_pct', 'sankey', 'timeline', 'balance'
    """
    try:
        if not analysis_data or 'type' not in analysis_data:
            return None

        a_type = analysis_data.get('type')
        data = analysis_data.get('data', [])
        if not data:
            return None

        df = pd.DataFrame(data)
        year = analysis_data.get('year')

        if a_type == 'mapbiomas':
            if chart_type == 'bar':
                return MapBiomasVisualizer.create_area_bar_chart(df, year=year)
            elif chart_type == 'pie':
                return MapBiomasVisualizer.create_pie_chart(df)
        elif a_type == 'hansen':
            if chart_type == 'balance':
                return HansenVisualizer.create_forest_balance_chart(df)
            elif chart_type == 'bar':
                return HansenVisualizer.create_area_distribution_chart(df)
        elif a_type == 'hansen_glad':
            # GLAD returns class distribution — show horizontal bar chart
            return HansenVisualizer.create_area_distribution_chart(df)
        elif a_type == 'hansen_gfc':
            # GFC returns 3-row summary (Metric / Area_ha / Percent / Description)
            return _create_gfc_summary_chart(df)

        # Default fallback
        if a_type == 'mapbiomas':
            return MapBiomasVisualizer.create_area_bar_chart(df, year=year)
        return HansenVisualizer.create_forest_balance_chart(df)

    except Exception as e:
        logger.error(f"Failed to generate chart: {e}")
        return None


# ---------------------------------------------------------------------------
# Deforestation / regrowth / fire timeline with political + policy context
# ---------------------------------------------------------------------------

# Demarcation stage colours (territory-specific, chronological pipeline).
# Each cell in the "Demarcation" heatmap row is coloured by the highest stage
# the territory had reached by that year.
# Dated stages (in chronological order) — used to compute per-year heatmap colour.
# "encaminhada_ri" is a FUNAI fase_ti status but has no date column in the GeoPackage,
# so it cannot appear in the per-year colour calculation; it is shown in the legend key only.
_DEMAR_STAGE_ORDER = [
    "em_estudo", "delimitada", "declarada", "homologada", "regularizada",
]
_DEMAR_STAGE_COLORS: Dict[str, str] = {
    "none":            "#eeeeee",
    "em_estudo":       "#fff3cd",
    "delimitada":      "#fde68a",
    "declarada":       "#bae4b3",
    "encaminhada_ri":  "#97d494",  # intermediate between declarada and homologada
    "homologada":      "#74c476",
    "regularizada":    "#238b45",
}
_DEMAR_STAGE_LABELS: Dict[str, str] = {
    "em_estudo":       "1 - Under Study",
    "delimitada":      "2 - Delimited",
    "declarada":       "3 - Declared",
    "encaminhada_ri":  "4 - Forwarded to RI",
    "homologada":      "4 - Approved",
    "regularizada":    "5 - Regularized",
}

# ---------------------------------------------------------------------------
# Conservation unit (UC) translations and colour palette
# ---------------------------------------------------------------------------

_UC_ESFERA_EN: Dict[str, str] = {
    "Federal":   "Federal",
    "Estadual":  "State",
    "Municipal": "Municipal",
}
_UC_GRUPO_EN: Dict[str, str] = {
    "Proteção Integral": "Strict Protection",
    "Uso Sustentável":   "Sustainable Use",
}
_UC_CATEGORIA_EN: Dict[str, str] = {
    "Estação Ecológica":                      "Ecological Station",
    "Floresta":                               "National Forest",
    "Monumento Natural":                      "Natural Monument",
    "Parque":                                 "National Park",
    "Refúgio de Vida Silvestre":              "Wildlife Refuge",
    "Reserva Biológica":                      "Biological Reserve",
    "Reserva de Desenvolvimento Sustentável": "Sustainable Dev. Reserve",
    "Reserva de Fauna":                       "Fauna Reserve",
    "Reserva Extrativista":                   "Extractive Reserve",
    "Reserva Particular do Patrimônio Natural": "Private Natural Heritage Reserve",
    "Área de Proteção Ambiental":             "Environmental Protection Area",
    "Área de Relevante Interesse Ecológico":  "Ecologically Relevant Area",
}
# Blue palette — clearly distinct from the TI green palette.
_UC_GRUPO_COLORS: Dict[str, str] = {
    "Proteção Integral": "#1e7abf",  # strong blue — strict protection
    "Uso Sustentável":   "#7ec8e3",  # light blue  — sustainable use
}


def _conservation_unit_demar_info(
    territory_name: str,
    years: List[int],
) -> Tuple[Dict[int, str], str, List[Dict]]:
    """Return (year→fillcolor, subtitle_text, milestone_list) for a UC.

    year→fillcolor: grey before creation year, grupo colour from creation year on.
    subtitle_text: English metadata string for display (e.g. in the chart title).
    milestone_list: one bold entry at the creation year.
    Returns ({}, "", []) on any failure.
    """
    try:
        from .conservation_service import get_conservation_unit_service
        info = get_conservation_unit_service().get_creation_info(territory_name)
    except Exception as exc:
        logger.debug(f"UC creation info lookup failed for '{territory_name}': {exc}")
        return {}, "", []

    if not info:
        return {}, "", []

    creation_year = info.get("creation_year")
    esfera    = _UC_ESFERA_EN.get(info.get("esfera", ""),    info.get("esfera", ""))
    grupo     = _UC_GRUPO_EN.get(info.get("grupo", ""),      info.get("grupo", ""))
    categoria = _UC_CATEGORIA_EN.get(info.get("categoria", ""), info.get("categoria", ""))

    grupo_color = _UC_GRUPO_COLORS.get(info.get("grupo", ""), "#7ec8e3")
    y_min, y_max = min(years), max(years)

    year_colors: Dict[int, str] = {}
    for y in years:
        if creation_year is not None and y >= creation_year:
            year_colors[y] = grupo_color
        else:
            year_colors[y] = "#eeeeee"

    subtitle = f"{categoria}  ·  {esfera}  ·  {grupo}"

    milestones: List[Dict] = []
    if creation_year is not None and y_min <= creation_year <= y_max:
        milestones.append({
            "year": creation_year,
            "label": f"UC established: {categoria} ({esfera})",
            "bold": True,
        })

    return year_colors, subtitle, milestones


def _territory_demar_info(
    territory_name: str,
    years: List[int],
) -> Tuple[Dict[int, str], str, List[Dict]]:
    """Return (year→fillcolor, subtitle_text, milestone_list) for a TI.

    subtitle_text: "Ethnicity: <etnia_nome>" when available, else "".
    Returns ({}, "", []) on any failure.
    """
    try:
        from .territory_service import get_territory_service
        svc = get_territory_service()
        dates = svc.get_demarcation_dates(territory_name)
        etnia = svc.get_ethnicity(territory_name)
    except Exception as exc:
        logger.debug(f"TI info lookup failed for '{territory_name}': {exc}")
        return {}, "", []

    if not dates:
        return {}, "", []

    # Per-year cell colour: highest stage reached by that year.
    year_colors: Dict[int, str] = {}
    for y in years:
        color = _DEMAR_STAGE_COLORS["none"]
        for stage in reversed(_DEMAR_STAGE_ORDER):
            yr = dates.get(stage)
            if yr is not None and yr <= y:
                color = _DEMAR_STAGE_COLORS[stage]
                break
        year_colors[y] = color

    subtitle = f"Ethnicity: {etnia}" if etnia else ""

    # Milestone entries: one bold entry per dated event within the year range.
    y_min, y_max = min(years), max(years)
    milestones: List[Dict] = []
    for stage in _DEMAR_STAGE_ORDER:
        yr = dates.get(stage)
        if yr is not None and y_min <= yr <= y_max:
            milestones.append({
                "year": yr,
                "label": f"TI: {_DEMAR_STAGE_LABELS[stage]}",
                "bold": True,
            })
    milestones.sort(key=lambda m: m["year"])
    return year_colors, subtitle, milestones


# Ideology → fill colour. Maps the integer ideology codes used by
# political_context_brazil.PRESIDENTS and GOVERNORS to a diverging palette.
_IDEOLOGY_COLOR = {
    -1: "#505050",  # left       → dark grey
     0: "#909090",  # centre     → mid grey
     1: "#bebebe",  # centre-right → light grey
     2: "#e0e0e0",  # right      → near-white grey
}

# Regime → fill colour for the policy bar (uses the regime labels from
# policy_context_brazil.build_combined_context).
_REGIME_COLOR = {
    "redemocratisation":  "#9ecae1",
    "new_republic_early": "#6baed6",
    "FHC":                "#fdae61",
    "Lula_I_II":          "#74c476",
    "Dilma":              "#31a354",
    "Temer":              "#fdae61",
    "Bolsonaro":          "#d73027",
    "Lula_III":           "#238b45",
}

# Indicator → display config
_INDICATOR_CFG = {
    "hansen_loss": {
        "label": "Hansen tree-cover loss",
        "color": "#d73027",
        "dash": "solid",
    },
    "mb_defor_primary": {
        "label": "MapBiomas primary deforestation",
        "color": "#7f0000",
        "dash": "solid",
    },
    "mb_secondary_growth": {
        "label": "MapBiomas secondary regrowth",
        "color": "#238b45",
        "dash": "dash",
    },
    "mb_fire_scar": {
        "label": "Annual burned area (MapBiomas Fire C4)",
        "color": "#fd8d3c",
        "dash": "dot",
    },
}


def _moving_average(values: List[Optional[float]], window: int) -> List[Optional[float]]:
    """Centred moving average. Returns ``None`` where the window can't fit."""
    out: List[Optional[float]] = []
    half = window // 2
    for i in range(len(values)):
        lo = i - half
        hi = i + half + 1
        if lo < 0 or hi > len(values):
            out.append(None)
            continue
        chunk = [v for v in values[lo:hi] if v is not None]
        if not chunk:
            out.append(None)
            continue
        out.append(sum(chunk) / len(chunk))
    return out


def _first_diff(values: List[Optional[float]]) -> List[Optional[float]]:
    out: List[Optional[float]] = [None]
    for i in range(1, len(values)):
        a, b = values[i - 1], values[i]
        if a is None or b is None:
            out.append(None)
        else:
            out.append(b - a)
    return out


def _political_shapes_and_annots(
    state_code: Optional[str],
    years: List[int],
    bar_y0: float = 1.04,
    bar_y1: float = 1.22,
    add_governor: bool = True,
):
    """Build (shapes, annotations) for the political-context bar above the plot.

    Uses ``political_context_brazil.build_political_context`` when a state
    code is provided, otherwise falls back to presidents only.
    """
    try:
        from .political_context_brazil import (
            build_president_series, build_political_context, GOVERNORS,
        )
    except Exception as e:
        logger.warning(f"political context import failed: {e}")
        return [], []

    shapes = []
    annots = []
    y0, y1 = bar_y0, bar_y1
    mid_y = (y0 + y1) / 2

    # Two stripes when a valid state is known: top = governor, bottom = president
    if add_governor and state_code and state_code in GOVERNORS:
        # split the bar into two stripes
        gap = (y1 - y0) * 0.05
        gov_y0, gov_y1 = y0, y0 + (y1 - y0) / 2 - gap / 2
        pres_y0, pres_y1 = y0 + (y1 - y0) / 2 + gap / 2, y1
        ctx = build_political_context(states=(state_code,), years=years)
    else:
        gov_y0 = gov_y1 = None
        pres_y0, pres_y1 = y0, y1
        ctx = None

    # Presidents: collapse consecutive years with the same president into one shape
    pres_df = build_president_series(years)
    if pres_df is not None and len(pres_df) > 0:
        groups = []
        cur = None
        for _, r in pres_df.iterrows():
            if cur is None or r["president"] != cur["president"]:
                if cur is not None:
                    groups.append(cur)
                cur = {
                    "president": r["president"],
                    "party": r["president_party"],
                    "ideo": r["president_ideology"],
                    "start": int(r["year"]),
                    "end": int(r["year"]),
                }
            else:
                cur["end"] = int(r["year"])
        if cur is not None:
            groups.append(cur)

        for g in groups:
            color = _IDEOLOGY_COLOR.get(int(g["ideo"] or 0), "#bdbdbd")
            shapes.append({
                "type": "rect", "xref": "x", "yref": "paper",
                "x0": g["start"] - 0.5, "x1": g["end"] + 0.5,
                "y0": pres_y0, "y1": pres_y1,
                "fillcolor": color, "line": {"width": 0.5, "color": "#555"},
                "opacity": 0.9, "layer": "above",
            })
            # Label centred in the rectangle if it spans ≥ 3 years
            if g["end"] - g["start"] >= 2:
                annots.append({
                    "x": (g["start"] + g["end"]) / 2,
                    "y": (pres_y0 + pres_y1) / 2,
                    "xref": "x", "yref": "paper",
                    "text": f"{g['president'].split()[-1]} ({g['party']})",
                    "showarrow": False,
                    "xanchor": "center", "yanchor": "middle",
                    "font": {"size": 10, "color": "#111"},
                })

    # Governors stripe
    if gov_y0 is not None and ctx is not None and len(ctx) > 0:
        groups = []
        cur = None
        for _, r in ctx.iterrows():
            gov = r.get("governor")
            if cur is None or gov != cur["governor"]:
                if cur is not None:
                    groups.append(cur)
                cur = {
                    "governor": gov,
                    "party": r.get("gov_party"),
                    "ideo": r.get("gov_ideology") or 0,
                    "start": int(r["year"]),
                    "end": int(r["year"]),
                }
            else:
                cur["end"] = int(r["year"])
        if cur is not None:
            groups.append(cur)

        for g in groups:
            color = _IDEOLOGY_COLOR.get(int(g["ideo"] or 0), "#bdbdbd")
            shapes.append({
                "type": "rect", "xref": "x", "yref": "paper",
                "x0": g["start"] - 0.5, "x1": g["end"] + 0.5,
                "y0": gov_y0, "y1": gov_y1,
                "fillcolor": color, "line": {"width": 0.5, "color": "#555"},
                "opacity": 0.75, "layer": "above",
            })
            if g["end"] - g["start"] >= 3 and g["governor"]:
                annots.append({
                    "x": (g["start"] + g["end"]) / 2,
                    "y": (gov_y0 + gov_y1) / 2,
                    "xref": "x", "yref": "paper",
                    "text": f"{state_code}: {str(g['governor']).split()[-1]}",
                    "showarrow": False,
                    "xanchor": "center", "yanchor": "middle",
                    "font": {"size": 9, "color": "#111"},
                })

    return shapes, annots


def _policy_shapes_and_annots(
    years: List[int],
    top_y: float = -0.06,
    row_height: float = 0.042,
    row_gap: float = 0.008,
    milestone_limit: int = 12,
    territory_demar_colors: Optional[Dict[int, str]] = None,
    demar_row_label: str = "Demarcation",
):
    """Per-year policy score heat-rows below the plot area.

    Draws four colour-coded rows (one cell per year) from
    ``policy_context_brazil.POLICY_SCORES``, top to bottom:
      1. enforcement_capacity    (0–3)
      2. forest_law_strength     (0–3)
      3. indigenous_rights_score (0–3)
      4. demarcation_posture     (−1 / 0 / +1)

    Green scale (0→3): white → light-green → mid-green → dark-green.
    Demarcation diverging: red (hostile) → grey (stalled) → green (active).
    """
    try:
        from .policy_context_brazil import POLICY_SCORES, build_milestones_df
    except Exception as e:
        logger.warning(f"policy context import failed: {e}")
        return [], []

    shapes: list = []
    annots: list = []

    _GREEN4 = ["#f7f7f7", "#bae4b3", "#74c476", "#238b45"]
    _DEMAR  = {-1: "#d73027", 0: "#969696", 1: "#1a9850"}

    ROWS = [
        ("enforcement_capacity",     "Enforcement",       _GREEN4, False),
        ("forest_law_strength",      "Forest Law",        _GREEN4, False),
        ("indigenous_rights_score",  "Indigenous Rights", _GREEN4, False),
        ("demarcation_posture",      demar_row_label,     None,    True),
    ]

    step = row_height + row_gap
    for row_idx, (dim, label, palette, diverging) in enumerate(ROWS):
        y1_row = top_y - row_idx * step           # top of this row (paper)
        y0_row = y1_row - row_height               # bottom of this row
        mid_y  = (y0_row + y1_row) / 2

        for y in years:
            scores = POLICY_SCORES.get(y)
            if scores is None:
                cell_color = "#eeeeee"
            elif diverging:
                if territory_demar_colors:
                    cell_color = territory_demar_colors.get(y, "#eeeeee")
                else:
                    val = scores.get(dim, 0)
                    cell_color = _DEMAR.get(int(val) if val is not None else 0, "#969696")
            else:
                val = scores.get(dim, 0)
                idx = max(0, min(3, int(val) if val is not None else 0))
                cell_color = palette[idx]

            shapes.append({
                "type": "rect", "xref": "x", "yref": "paper",
                "x0": y - 0.45, "x1": y + 0.45,
                "y0": y0_row, "y1": y1_row,
                "fillcolor": cell_color, "line": {"width": 0},
                "opacity": 1.0, "layer": "above",
            })

        # Row label — right-aligned against the left edge of the plot area
        annots.append({
            "x": 0, "y": mid_y,
            "xref": "paper", "yref": "paper",
            "text": label,
            "showarrow": False,
            "xanchor": "right", "yanchor": "middle",
            "font": {"size": 9, "color": "#444"},
        })

    # Milestone arrows just below the last row
    arrow_y = top_y - len(ROWS) * step - 0.025
    try:
        ms_df = build_milestones_df()
        in_range = ms_df[(ms_df["year"] >= years[0]) & (ms_df["year"] <= years[-1])]
        priority = in_range[in_range["category"].isin(["FOREST_LAW", "INDIGENOUS", "CLIMATE"])]
        picks = priority.head(milestone_limit)
        for _, r in picks.iterrows():
            annots.append({
                "x": int(r["year"]),
                "y": arrow_y,
                "xref": "x", "yref": "paper",
                "text": "▲",
                "showarrow": False,
                "font": {"size": 10, "color": "#555"},
                "hovertext": f"{int(r['year'])} — {r['instrument']}",
            })
    except Exception as e:
        logger.warning(f"policy milestones annotation failed: {e}")

    return shapes, annots


def _context_legend_shapes_and_annots(
    years: List[int],
    top_y: float = -0.31,
    milestone_limit: int = 50,
    demar_milestones: Optional[List[Dict]] = None,
    territory_type: str = "indigenous",
) -> Tuple[list, list]:
    """Color-key swatches + policy milestone list for the figure's bottom area.

    Explains the four policy-row scales and lists key milestones within the
    requested year range. Positioned in paper coordinates so it sits in the
    bottom margin regardless of the data range.
    """
    shapes: list = []
    annots: list = []

    _GREEN4 = ["#f7f7f7", "#bae4b3", "#74c476", "#238b45"]
    SCORE_LABELS = ["0 – absent", "1 – weak", "2 – moderate", "3 – strong"]
    SCORE_XS = [0.20, 0.38, 0.56, 0.74]   # left x of each swatch (paper)
    SW = 0.038                              # swatch width (paper x)
    SH = 0.018                             # swatch height (paper y)
    ROW_GAP = 0.060                        # vertical spacing between key rows (≈20px)

    # ── Section header ─────────────────────────────────────────────────────────
    annots.append({
        "x": 0.0, "y": top_y,
        "xref": "paper", "yref": "paper",
        "text": "<b>Policy context key</b>",
        "showarrow": False,
        "xanchor": "left", "yanchor": "top",
        "font": {"size": 9, "color": "#333"},
    })

    # ── Green-scale key (Enforcement / Forest Law / Indigenous Rights) ──────────
    # Extra gap after the header line (≈14 px at 340 px/paper-unit)
    row_cy = top_y - 0.042
    annots.append({
        "x": 0.0, "y": row_cy,
        "xref": "paper", "yref": "paper",
        "text": "Score (0 – 3):",
        "showarrow": False,
        "xanchor": "left", "yanchor": "middle",
        "font": {"size": 8, "color": "#555"},
    })
    for i, (color, label) in enumerate(zip(_GREEN4, SCORE_LABELS)):
        sx = SCORE_XS[i]
        shapes.append({
            "type": "rect", "xref": "paper", "yref": "paper",
            "x0": sx, "x1": sx + SW,
            "y0": row_cy - SH / 2, "y1": row_cy + SH / 2,
            "fillcolor": color,
            "line": {"width": 0.5, "color": "#aaa"},
            "opacity": 1.0, "layer": "above",
        })
        annots.append({
            "x": sx + SW + 0.01, "y": row_cy,
            "xref": "paper", "yref": "paper",
            "text": label,
            "showarrow": False,
            "xanchor": "left", "yanchor": "middle",
            "font": {"size": 8, "color": "#444"},
        })

    # ── Demarcation / UC status key ─────────────────────────────────────────────
    row_cy -= ROW_GAP
    if demar_milestones and territory_type == "conservation":
        # Conservation unit mode: simple 3-swatch key (not protected / Strict / Sustainable).
        UC_ITEMS = [
            ("#eeeeee",  "Not yet protected"),
            (_UC_GRUPO_COLORS["Proteção Integral"], "Strict Protection"),
            (_UC_GRUPO_COLORS["Uso Sustentável"],   "Sustainable Use"),
        ]
        UC_XS = [0.13, 0.40, 0.67]
        annots.append({
            "x": 0.0, "y": row_cy,
            "xref": "paper", "yref": "paper",
            "text": "UC status:",
            "showarrow": False,
            "xanchor": "left", "yanchor": "middle",
            "font": {"size": 8, "color": "#555"},
        })
        for (color, label), sx in zip(UC_ITEMS, UC_XS):
            shapes.append({
                "type": "rect", "xref": "paper", "yref": "paper",
                "x0": sx, "x1": sx + SW,
                "y0": row_cy - SH / 2, "y1": row_cy + SH / 2,
                "fillcolor": color,
                "line": {"width": 0.5, "color": "#aaa"},
                "opacity": 1.0, "layer": "above",
            })
            annots.append({
                "x": sx + SW + 0.008, "y": row_cy,
                "xref": "paper", "yref": "paper",
                "text": label,
                "showarrow": False,
                "xanchor": "left", "yanchor": "middle",
                "font": {"size": 8, "color": "#444"},
            })
        # Single row consumed — no extra sub-rows needed.
    elif demar_milestones:
        # Indigenous territory mode: 3 rows × 3 swatches covering all 6 FUNAI stages.
        STAGE_ROWS = [
            [("none", "none"),
             ("em_estudo",      _DEMAR_STAGE_LABELS["em_estudo"]),
             ("delimitada",     _DEMAR_STAGE_LABELS["delimitada"])],
            [("declarada",      _DEMAR_STAGE_LABELS["declarada"]),
             ("encaminhada_ri", _DEMAR_STAGE_LABELS["encaminhada_ri"]),
             ("homologada",     _DEMAR_STAGE_LABELS["homologada"])],
            [("regularizada",   _DEMAR_STAGE_LABELS["regularizada"])],
        ]
        STAGE_XS = [0.13, 0.40, 0.67]
        annots.append({
            "x": 0.0, "y": row_cy,
            "xref": "paper", "yref": "paper",
            "text": "Demarcation stage (this TI):",
            "showarrow": False,
            "xanchor": "left", "yanchor": "middle",
            "font": {"size": 8, "color": "#555"},
        })
        for r_idx, stage_row in enumerate(STAGE_ROWS):
            cy = row_cy - (r_idx + 1) * (SH + 0.012)
            for (stage_key, stage_lbl), sx in zip(stage_row, STAGE_XS):
                shapes.append({
                    "type": "rect", "xref": "paper", "yref": "paper",
                    "x0": sx, "x1": sx + SW,
                    "y0": cy - SH / 2, "y1": cy + SH / 2,
                    "fillcolor": _DEMAR_STAGE_COLORS.get(stage_key, "#eeeeee"),
                    "line": {"width": 0.5, "color": "#aaa"},
                    "opacity": 1.0, "layer": "above",
                })
                annots.append({
                    "x": sx + SW + 0.008, "y": cy,
                    "xref": "paper", "yref": "paper",
                    "text": stage_lbl,
                    "showarrow": False,
                    "xanchor": "left", "yanchor": "middle",
                    "font": {"size": 8, "color": "#444"},
                })
        # Consume the 3 sub-rows of vertical space so the next element is positioned correctly.
        row_cy -= 3 * (SH + 0.012)
    else:
        # National policy mode: −1 / 0 / +1 posture score.
        DEMAR_ITEMS = [
            ("#d73027", "−1 hostile (frozen)"),
            ("#969696", "0 stalled"),
            ("#1a9850", "+1 active"),
        ]
        DEMAR_XS = [0.20, 0.44, 0.68]
        annots.append({
            "x": 0.0, "y": row_cy,
            "xref": "paper", "yref": "paper",
            "text": "Demarcation:",
            "showarrow": False,
            "xanchor": "left", "yanchor": "middle",
            "font": {"size": 8, "color": "#555"},
        })
        for (color, label), sx in zip(DEMAR_ITEMS, DEMAR_XS):
            shapes.append({
                "type": "rect", "xref": "paper", "yref": "paper",
                "x0": sx, "x1": sx + SW,
                "y0": row_cy - SH / 2, "y1": row_cy + SH / 2,
                "fillcolor": color,
                "line": {"width": 0.5, "color": "#aaa"},
                "opacity": 0.9, "layer": "above",
            })
            annots.append({
                "x": sx + SW + 0.01, "y": row_cy,
                "xref": "paper", "yref": "paper",
                "text": label,
                "showarrow": False,
                "xanchor": "left", "yanchor": "middle",
                "font": {"size": 8, "color": "#444"},
            })

    # ── Top-bar note ────────────────────────────────────────────────────────────
    row_cy -= ROW_GAP
    annots.append({
        "x": 0.0, "y": row_cy,
        "xref": "paper", "yref": "paper",
        "text": "Top bars: president (bottom stripe) and state governor (top stripe) — neutral grey, darker = earlier period",
        "showarrow": False,
        "xanchor": "left", "yanchor": "middle",
        "font": {"size": 10, "color": "#555"},
    })

    # ── Key policy milestones list ──────────────────────────────────────────────
    try:
        from .policy_context_brazil import build_milestones_df
        ms_df = build_milestones_df()
        in_range = ms_df[(ms_df["year"] >= years[0]) & (ms_df["year"] <= years[-1])]
        priority = in_range[in_range["category"].isin(
            ["FOREST_LAW", "INDIGENOUS", "CLIMATE", "PLANNING", "FINANCE", "ENFORCEMENT"]
        )].sort_values("year").head(milestone_limit)

        ms_header_y = row_cy - ROW_GAP
        annots.append({
            "x": 0.0, "y": ms_header_y,
            "xref": "paper", "yref": "paper",
            "text": "<b>Key policy milestones (▲ markers above)</b>",
            "showarrow": False,
            "xanchor": "left", "yanchor": "top",
            "font": {"size": 9, "color": "#333"},
        })

        # Build the combined list: territory demarcation events (bold) merged
        # with national policy milestones, sorted by year.
        combined: List[Dict] = []
        for _, r in priority.iterrows():
            instr = r["instrument"]
            if len(instr) > 60:
                instr = instr[:57] + "…"
            combined.append({"year": int(r["year"]), "text": instr, "bold": False})
        for dm in (demar_milestones or []):
            combined.append({"year": dm["year"], "text": dm["label"], "bold": True})
        combined.sort(key=lambda e: e["year"])

        # Two-column layout: left col x=0.0, right col x=0.51.
        for i, entry in enumerate(combined):
            col = i % 2
            row_i = i // 2
            txt = f"<b>{entry['year']}  {entry['text']}</b>" if entry["bold"] \
                  else f"{entry['year']}  {entry['text']}"
            annots.append({
                "x": 0.0 if col == 0 else 0.51,
                "y": ms_header_y - 0.036 - row_i * 0.030,
                "xref": "paper", "yref": "paper",
                "text": txt,
                "showarrow": False,
                "xanchor": "left", "yanchor": "top",
                "font": {"size": 8, "color": "#333" if entry["bold"] else "#555"},
            })
    except Exception as e:
        logger.warning(f"context legend milestones failed: {e}")

    return shapes, annots


# ---------------------------------------------------------------------------
# ENSO — Oceanic Niño Index strip (NOAA CPC), drawn between the main plot
# and the policy colour table. Colours/thresholds match the reference
# implementation in prototipos/ana/dashboard-enso.jsx.
# ---------------------------------------------------------------------------

_ENSO_COLOR = {"elnino": "#c8602a", "lanina": "#1f5fa8", "neutral": "#c8d2de"}
_ONI_THRESHOLD = 0.5

_ENSO_SERIES_CACHE: Optional[List[Dict]] = None


def _load_enso_series() -> List[Dict]:
    """Seasonal ONI rows from ``enso_oni.json`` (cached after first read).

    Each row: ``{season, year, month (1–12), sstTotal, anomaly}``.
    Returns [] when the file is missing or unreadable.
    """
    global _ENSO_SERIES_CACHE
    if _ENSO_SERIES_CACHE is None:
        import json
        import os

        path = os.path.join(os.path.dirname(__file__), "enso_oni.json")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                _ENSO_SERIES_CACHE = json.load(fh).get("series", []) or []
        except Exception as exc:
            logger.warning(f"ENSO ONI series load failed: {exc}")
            _ENSO_SERIES_CACHE = []
    return _ENSO_SERIES_CACHE


def _enso_shapes_and_annots(
    years: List[int],
    top_y: float = -0.26,
    height: float = 0.22,
) -> Tuple[list, list]:
    """ONI anomaly bar strip in paper coordinates below the main plot.

    One bar per ONI season (12/year) centred on the calendar year cell used
    by the policy rows (year ± 0.5). Bars ≥ +0.5 °C are El Niño orange,
    ≤ −0.5 °C La Niña blue, otherwise neutral grey; dotted guides mark the
    ±0.5 °C CPC thresholds. Returns ([], []) when no data covers *years*.
    """
    series = [r for r in _load_enso_series() if years[0] <= r.get("year", 0) <= years[-1]]
    if not series:
        return [], []

    y_top = top_y
    y_bot = top_y - height
    y_mid = (y_top + y_bot) / 2
    half = height / 2
    max_abs = max(2.2, max(abs(float(r.get("anomaly") or 0.0)) for r in series))

    def y_of(v: float) -> float:
        return y_mid + (v / max_abs) * half

    shapes: list = []
    annots: list = []

    # Zero baseline + ±0.5 °C threshold guides across the year range
    x_lo, x_hi = years[0] - 0.5, years[-1] + 0.5
    for v in (0.0, _ONI_THRESHOLD, -_ONI_THRESHOLD):
        line = {"width": 0.8, "color": "#c8d2de" if v == 0 else "#b0bcc9"}
        if v != 0:
            line["dash"] = "dot"
        shapes.append({
            "type": "line", "xref": "x", "yref": "paper",
            "x0": x_lo, "x1": x_hi, "y0": y_of(v), "y1": y_of(v),
            "line": line, "layer": "above",
        })

    # Seasonal anomaly bars (month 1 = DJF at the year's left edge)
    bar_w = 1.0 / 12
    for r in series:
        anom = float(r.get("anomaly") or 0.0)
        active = abs(anom) >= _ONI_THRESHOLD
        if active:
            color = _ENSO_COLOR["elnino"] if anom >= 0 else _ENSO_COLOR["lanina"]
        else:
            color = _ENSO_COLOR["neutral"]
        x0 = r["year"] - 0.5 + (int(r.get("month", 1)) - 1) * bar_w
        shapes.append({
            "type": "rect", "xref": "x", "yref": "paper",
            "x0": x0, "x1": x0 + bar_w,
            "y0": min(y_of(0.0), y_of(anom)), "y1": max(y_of(0.0), y_of(anom)),
            "fillcolor": color, "line": {"width": 0},
            "opacity": 0.85 if active else 0.7, "layer": "above",
        })

    # Left row label (mirrors the policy-row labels)
    annots.append({
        "x": 0, "y": y_mid,
        "xref": "paper", "yref": "paper",
        "text": "ENSO (ONI)",
        "showarrow": False,
        "xanchor": "right", "yanchor": "middle",
        "font": {"size": 9, "color": "#444"},
    })
    # Threshold labels on the right edge
    for v in (_ONI_THRESHOLD, -_ONI_THRESHOLD):
        annots.append({
            "x": 1.0, "y": y_of(v),
            "xref": "paper", "yref": "paper",
            "text": f"{v:+.1f}°C",
            "showarrow": False,
            "xanchor": "left", "yanchor": "middle",
            "font": {"size": 8, "color": "#7a8694"},
        })
    # Compact legend caption below the strip (its own row, clear of the
    # main graph's trace legend above)
    annots.append({
        "x": 0.005, "y": y_bot - 0.015,
        "xref": "paper", "yref": "paper",
        "text": ("<span style='color:#c8602a'>■</span> El Niño ≥ +0.5°C   "
                 "<span style='color:#1f5fa8'>■</span> La Niña ≤ −0.5°C   "
                 "— Niño 3.4 SST anomaly (NOAA CPC)"),
        "showarrow": False,
        "xanchor": "left", "yanchor": "top",
        "font": {"size": 8, "color": "#7a8694"},
    })

    return shapes, annots


def create_deforestation_timeline_chart(
    timeline_data: Dict[str, Dict[int, float]],
    state_code: Optional[str],
    year_start: int,
    year_end: int,
    variant: str = "raw",
    moving_window: int = 5,
    title_suffix: str = "",
    territory_name: str = "",
    territory_type: str = "indigenous",
) -> Optional[go.Figure]:
    """Build a Plotly figure with political bar above, indicator lines, policy bar below.

    Args:
        timeline_data: ``{indicator_key: {year: ha}}`` from
            ``deforestation_timeline.collect_timeline``.
        state_code: 2-letter Brazilian state code for the governor stripe;
            ``None`` to omit the governor row.
        year_start, year_end: x-axis range (inclusive).
        variant: ``"raw"`` (default), ``"moving_avg"`` (centred N-year window
            using ``moving_window``), or ``"derivatives"`` (first and second
            differences, plotted as separate trace groups).
        moving_window: window size for the ``moving_avg`` variant.
        title_suffix: appended to the figure title (typically the territory
            name).

    Returns ``None`` if no indicator has data.
    """
    if not timeline_data:
        return None

    years = list(range(year_start, year_end + 1))

    # Pull each indicator into a list aligned to ``years``.
    raw_lines: Dict[str, List[Optional[float]]] = {}
    for key, series in timeline_data.items():
        if not series:
            continue
        raw_lines[key] = [float(series.get(y, 0.0) or 0.0) for y in years]

    if not raw_lines:
        return None

    fig = go.Figure()

    if variant == "raw":
        for key, values in raw_lines.items():
            cfg = _INDICATOR_CFG.get(key, {"label": key, "color": "#555", "dash": "solid"})
            fig.add_trace(go.Scatter(
                x=years, y=values, mode="lines+markers",
                name=cfg["label"],
                line={"color": cfg["color"], "width": 2, "dash": cfg["dash"]},
                marker={"size": 5},
                hovertemplate="<b>%{x}</b>: %{y:,.0f} ha<extra>" + cfg["label"] + "</extra>",
            ))
        y_axis_title = "Area (ha / year)"
        v_title = "raw values"

    elif variant == "moving_avg":
        for key, values in raw_lines.items():
            cfg = _INDICATOR_CFG.get(key, {"label": key, "color": "#555", "dash": "solid"})
            ma = _moving_average(values, moving_window)
            fig.add_trace(go.Scatter(
                x=years, y=ma, mode="lines",
                name=f"{cfg['label']} (MA{moving_window})",
                line={"color": cfg["color"], "width": 2.5, "dash": cfg["dash"]},
                hovertemplate="<b>%{x}</b>: %{y:,.0f} ha<extra>" + cfg["label"] + "</extra>",
                connectgaps=False,
            ))
        y_axis_title = f"Area (ha / year) — {moving_window}-yr moving average"
        v_title = f"{moving_window}-yr moving average"

    elif variant == "derivatives":
        for key, values in raw_lines.items():
            cfg = _INDICATOR_CFG.get(key, {"label": key, "color": "#555", "dash": "solid"})
            d1 = _first_diff(values)
            d2 = _first_diff(d1)
            fig.add_trace(go.Scatter(
                x=years, y=d1, mode="lines",
                name=f"Δ {cfg['label']}",
                line={"color": cfg["color"], "width": 2, "dash": "solid"},
                hovertemplate="<b>%{x}</b>: %{y:+,.0f} ha<extra>Δ " + cfg["label"] + "</extra>",
                legendgroup=key, showlegend=True,
            ))
            fig.add_trace(go.Scatter(
                x=years, y=d2, mode="lines",
                name=f"Δ² {cfg['label']}",
                line={"color": cfg["color"], "width": 1.4, "dash": "dot"},
                hovertemplate="<b>%{x}</b>: %{y:+,.0f} ha<extra>Δ² " + cfg["label"] + "</extra>",
                legendgroup=key, showlegend=True,
                opacity=0.7,
            ))
        # Zero baseline
        fig.add_hline(y=0, line_width=0.8, line_dash="dot", line_color="#888")
        y_axis_title = "Δ ha / year (1st), Δ² ha / year² (2nd)"
        v_title = "1st & 2nd derivatives"
    else:
        return None

    # Build context shapes / annotations.
    # Layout budget (height=1170, t=180, b=650 → plot area 340 px = 1 paper unit):
    #   x-axis ticks + "Year" title   ≈ −0.15  (50 px below plot)
    #   trace legend (raw/ma5)        y=−0.17  (58 px, safely below axis title)
    #   ENSO strip   top −0.26 → −0.48 (ONI seasonal bars, 75 px),
    #                own legend caption at −0.495
    #   policy rows  top_y=−0.58 → end at −0.78; arrows at −0.805
    #   context key  top_y=−0.85 → key rows end at −1.07
    #   milestones   2-col, 21 rows × 0.030 = 0.63 span → last at ≈−1.74
    #                1.74 × 340 = 592 px  (<  663 px margin ✓)
    # When the ENSO series is unavailable the strip is skipped and everything
    # keeps its original (unshifted) position.
    subtitle = ""
    if territory_name and territory_type == "conservation":
        demar_colors, subtitle, demar_milestones = _conservation_unit_demar_info(territory_name, years)
    elif territory_name:
        demar_colors, subtitle, demar_milestones = _territory_demar_info(territory_name, years)
    else:
        demar_colors, demar_milestones = {}, []

    demar_row_label = "UC Status" if territory_type == "conservation" else "Demarcation"

    enso_shapes, enso_annots = _enso_shapes_and_annots(years, top_y=-0.26, height=0.22)
    # Strip (0.22) + its legend caption row (0.04) push everything below down
    enso_shift = 0.26 if enso_shapes else 0.0

    pol_shapes, pol_annots = _political_shapes_and_annots(state_code, years)
    pcy_shapes, pcy_annots = _policy_shapes_and_annots(
        years, top_y=-0.32 - enso_shift, milestone_limit=12,
        territory_demar_colors=demar_colors or None,
        demar_row_label=demar_row_label,
    )
    leg_shapes, leg_annots = _context_legend_shapes_and_annots(
        years, top_y=-0.59 - enso_shift, milestone_limit=50,
        demar_milestones=demar_milestones or None,
        territory_type=territory_type,
    )

    title = f"Deforestation Timeline — {v_title}"
    if title_suffix:
        title += f" | {title_suffix}"
    if subtitle:
        title += f"<br><sup>{subtitle}</sup>"

    # Derivatives: 8 traces → vertical legend on the right avoids overflow.
    # Raw / moving_avg: 4 traces → horizontal legend below the axis title.
    if variant == "derivatives":
        legend_cfg = {
            "orientation": "v",
            "yanchor": "top", "y": 1.0,
            "xanchor": "left", "x": 1.01,
            "font": {"size": 10},
        }
        right_margin = 220
    else:
        legend_cfg = {
            "orientation": "h", "yanchor": "top", "y": -0.17,
            "xanchor": "center", "x": 0.5,
            "font": {"size": 10},
        }
        right_margin = 30

    # Extra bottom margin absorbs the ENSO strip's downward shift so the
    # plot area stays exactly 340 px (1 paper unit) either way.
    extra_px = int(round(enso_shift * 340 + (15 if enso_shift else 0)))
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=1080 + extra_px,
        margin={"t": 180, "b": 560 + extra_px, "l": 100, "r": right_margin},
        legend=legend_cfg,
        shapes=pol_shapes + enso_shapes + pcy_shapes + leg_shapes,
        annotations=pol_annots + enso_annots + pcy_annots + leg_annots,
        xaxis={"title": "Year",
                "range": [year_start - 0.5, year_end + 0.5],
                "dtick": 5, "tickfont": {"size": 11}},
        yaxis={"title": y_axis_title,
                "tickformat": "~s",  # SI prefixes: 1k, 10k, 100k…
                "tickfont": {"size": 11}},
    )
    return fig


# ---------------------------------------------------------------------------
# Print-ready export helpers
# ---------------------------------------------------------------------------

def create_improved_layout(
    fig: go.Figure,
    title: str,
    year_start: int = 1985,
    year_end: int = 2024,
    y_axis_title: str = "Δ ha / year (1st), Δ² ha / year² (2nd)",
) -> go.Figure:
    """Apply a compact, print-optimised layout to a deforestation timeline figure."""
    fig.update_layout(
        title={
            "text": title,
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 20, "family": "Arial, sans-serif", "weight": "bold"},
            "y": 0.98,
        },
        template="plotly_white",
        height=1800,
        width=1200,
        margin={"t": 140, "b": 200, "l": 120, "r": 50},
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -1.5,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 10},
            "bgcolor": "rgba(255,255,255,0.9)",
            "bordercolor": "#ccc",
            "borderwidth": 1,
        },
        xaxis={
            "title": {"text": "Year", "font": {"size": 14, "weight": "bold"}},
            "range": [year_start - 0.5, year_end + 0.5],
            "dtick": 5,
            "tickfont": {"size": 11},
            "gridcolor": "#e0e0e0",
            "showgrid": True,
            "zerolinecolor": "#333",
            "zerolinewidth": 1,
        },
        yaxis={
            "title": {"text": y_axis_title, "font": {"size": 14, "weight": "bold"}},
            "tickformat": "~s",
            "tickfont": {"size": 11},
            "gridcolor": "#e0e0e0",
            "showgrid": True,
            "zerolinecolor": "#333",
            "zerolinewidth": 1,
        },
        plot_bgcolor="white",
        paper_bgcolor="white",
        font={"family": "Arial, sans-serif", "size": 12, "color": "#2a3f5f"},
        hoverlabel={
            "bgcolor": "white",
            "font_size": 12,
            "font_family": "Arial",
            "bordercolor": "#ccc",
        },
        autosize=False,
        bargap=0.1,
    )

    for shape in fig.layout.shapes:
        if hasattr(shape, "opacity") and shape.opacity is not None:
            shape.opacity = min(shape.opacity * 1.2, 1.0)

    return fig


def export_print_ready(fig: go.Figure, filename: str, scale: int = 3) -> None:
    """Export figure to a high-resolution PNG suitable for printing.

    scale=3 yields ~3600×5400 px at 300 dpi (12×18 inches).
    """
    fig.write_image(
        filename,
        scale=scale,
        width=1200,
        height=1800,
    )


def create_two_part_layout(
    fig: go.Figure,
    title: str,
    policy_annots: list,
) -> Tuple[go.Figure, go.Figure]:
    """Split a timeline figure into a chart figure and a policy-table figure.

    Returns:
        (chart_fig, policy_fig) — two independent Plotly figures.
    """
    chart_fig = fig
    chart_fig.update_layout(
        title=title,
        height=800,
        width=1200,
        margin={"t": 100, "b": 100, "l": 100, "r": 50},
        legend={"orientation": "h", "y": -0.2, "x": 0.5},
    )

    policy_data = []
    for ann in policy_annots:
        text = getattr(ann, "text", None) or ann.get("text", "")
        if text and "▲" not in text:
            year = getattr(ann, "x", None) or ann.get("x")
            policy_data.append({"year": year, "text": text})

    policy_fig = go.Figure()
    policy_fig.add_trace(go.Table(
        header=dict(
            values=["Year", "Policy Milestone"],
            font=dict(size=12, color="white", family="Arial"),
            fill=dict(color="#2a3f5f"),
            align="left",
            height=30,
        ),
        cells=dict(
            values=[
                [p["year"] for p in policy_data if p["year"] is not None],
                [p["text"] for p in policy_data],
            ],
            font=dict(size=10, family="Arial"),
            align="left",
            height=25,
            fill=dict(color="white"),
            line=dict(color="#ddd"),
        ),
    ))
    policy_fig.update_layout(
        title="Policy Timeline Reference",
        height=800,
        width=1200,
        margin={"t": 50, "b": 50, "l": 50, "r": 50},
    )

    return chart_fig, policy_fig

