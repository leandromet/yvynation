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
    node_labels = [f"{n}\n({node_flow.get(n, 0):,.0f} ha)" for n in sorted_nodes]
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
                f"{_resolve_label(cls_id)} ({y}) — {area:,.0f} ha ({frac * 100:.1f}%)"
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
    fig.update_layout(
        title=title,
        font=dict(size=10),
        height=max(700, 90 * len(year_order)),
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
