"""The notice that goes with every Indigenous-land boundary Yvynation shows.

Boundaries of Indigenous lands (FUNAI's catalogue in Brazil, the federal PAD-US / BIA
data in the United States) are published by the national government and are open.
That does not settle how statistics about named lands may be read or quoted, so the
same short notice travels with them wherever they are selected or cited. The text is
in ``utils/translations`` (``indigenous_data_notice_*``), in all four languages.
"""

from __future__ import annotations

import reflex as rx

from ..state import AppState


def indigenous_notice(compact: bool = True, always: bool = False) -> rx.Component:
    """``always`` shows it unconditionally (citation panel); otherwise only while the
    selected territory type is Indigenous lands, not conservation units."""
    box = _box(compact)
    if always:
        return box
    return rx.cond(AppState.territory_type == "indigenous", box, rx.fragment())


def _box(compact: bool) -> rx.Component:
    return rx.box(
        rx.text(AppState.tr["indigenous_data_notice_title"], font_size="10px" if compact else "13px",
                font_weight="700", color="#6d28d9"),
        rx.text(AppState.tr["indigenous_data_notice_body"], font_size="9px" if compact else "12px",
                line_height="1.45", color="#4b5563"),
        padding="6px 8px", border_left="3px solid #8b5cf6", background="#f5f3ff",
        border_radius="4px", width="100%",
    )
