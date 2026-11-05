"""Charts for the USA page: the NLCD stacked history; the Hansen loss chart is the
Canada page's, imported unchanged."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import plotly.graph_objects as go

from ...canada.components.charts import biomass_figure, fire_figure, hansen_figure  # noqa: F401  (re-exported)
from ..config import nlcd


def _order(class_ids: List[int]) -> List[int]:
    def key(c: int):
        if c in nlcd.STACK_PRIORITY:
            return (0, nlcd.STACK_PRIORITY.index(c))
        if c in nlcd.WATER:
            return (2, c)
        return (1, c)
    return sorted(class_ids, key=key)


def land_cover_figure(rows: List[Dict[str, Any]], *, lang: str = "en",
                      normalise: bool = False) -> go.Figure:
    fig = go.Figure()
    sub = pd.DataFrame.from_records(rows) if rows else pd.DataFrame()
    if sub.empty:
        fig.add_annotation(text="Sem dados" if lang == "pt" else "No data", showarrow=False,
                           font=dict(size=13, color="#888"))
    else:
        col = "area_ha"
        if normalise:
            sub = sub.copy()
            sub["area_pct"] = sub["area_ha"] / sub.groupby("year")["area_ha"].transform("sum") * 100
            col = "area_pct"
        years = sorted(sub["year"].unique())
        unit = "%" if normalise else "ha"
        for cid in _order(sorted(sub["class_id"].unique())):
            by = sub[sub["class_id"] == cid].set_index("year")
            vals = [float(by[col].get(y, 0.0)) for y in years]
            if not any(vals):
                continue
            name = nlcd.label(int(cid), lang)
            fig.add_bar(x=years, y=vals, name=name, marker_color=nlcd.color(int(cid)),
                        marker_line_width=0,
                        hovertemplate=f"<b>{name}</b><br>%{{x}}<br>%{{y:,.1f}} {unit}<extra></extra>")
    y_title = ("Área" if lang == "pt" else "Area") + (" (%)" if normalise else " (ha)")
    fig.update_layout(
        barmode="stack", bargap=0.06, template="plotly_white", height=300,
        margin=dict(l=56, r=8, t=8, b=84), hovermode="x unified", dragmode=False,
        legend=dict(orientation="h", yanchor="top", y=-0.16, x=0, font=dict(size=9),
                    itemsizing="constant", tracegroupgap=2),
        xaxis=dict(title=None, tickmode="linear", dtick=5, showgrid=False, fixedrange=True),
        yaxis=dict(title=y_title, showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                   zeroline=False, fixedrange=True),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    if normalise:
        fig.update_yaxes(range=[0, 100])
    return fig
