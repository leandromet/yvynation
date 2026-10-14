"""The selected protected area's card, and the zone list.

Adapted from camposcope's ``parcel_card.py`` (its "park" card). Every CPCAD
field is shown as published — designation, PA/OECM, governance, status — with
no ranking or colour: the register is ECCC's, and the card reports it. The
disclosure says what is *not* in the data and why (OCAP).
"""

from __future__ import annotations

import reflex as rx

from ..config import cpcad_vocab
from ..state import CanadaState as S
from .layout import BORDER, MUTED, section


def _row(label, value, *, mono: bool = False, emphasis: bool = False) -> rx.Component:
    return rx.hstack(
        rx.text(label, size="1", color=MUTED, flex="0 1 auto", min_width="0",
                style={"overflowWrap": "anywhere"}),
        rx.spacer(),
        rx.text(value, size="1",
                weight=rx.cond(emphasis, "bold", "regular"),
                font_family=rx.cond(mono, "monospace", "inherit"),
                text_align="right", flex="1 1 auto", min_width="0",
                style={"overflowWrap": "anywhere"}),
        width="100%", align="start", spacing="2",
    )


def _vocab(value, table: str):
    """A register fixed-list value in the page language (see
    ``config/cpcad_vocab.py``). English is the stored form; unknown values
    fall through unchanged."""
    def in_lang(lang: str):
        return rx.match(
            value,
            *[(en, tr[lang]) for en, tr in cpcad_vocab.TABLES[table].items()],
            value)
    return rx.match(S.language, ("pt", in_lang("pt")), ("fr", in_lang("fr")), value)


def _opt_row(label, value, table: str | None = None) -> rx.Component:
    shown = value if table is None else _vocab(value, table)
    return rx.cond(value, _row(label, shown))


def _coordinate_row() -> rx.Component:
    from_click = S.parcel["click_lat"] != 0.0
    lat = rx.cond(from_click, S.parcel["click_lat"], S.parcel["centroid_lat"])
    lon = rx.cond(from_click, S.parcel["click_lon"], S.parcel["centroid_lon"])
    label = rx.cond(from_click, S.tr["coord_clicked"], S.tr["coord_centroid"])
    return _row(label, f"{lat}, {lon}", mono=True)


def _area_block() -> rx.Component:
    return rx.vstack(
        _row(S.tr["park_area_reported"], f"{S.area_registered_ha} ha", emphasis=True),
        _row(S.tr["park_area_calculated"], f"{S.area_calculated_ha} ha"),
        rx.cond(
            S.area_flagged,
            rx.callout(
                f"{S.tr['park_area_disagreement_prefix']} "
                f"{S.area_delta_ha} ha ({S.area_delta_pct}%). "
                f"{S.tr['park_area_disagreement_suffix']}",
                icon="ruler", color_scheme="amber", size="1",
            ),
        ),
        spacing="1", width="100%",
    )


def area_card() -> rx.Component:
    return rx.cond(
        S.has_parcel,
        section(
            S.tr["area_card_title"],
            _row(S.tr["park_name"], S.parcel["identifier"], emphasis=True),
            # Only when it actually differs — CPCAD often repeats the English.
            rx.cond(S.parcel["name_fr"] != S.parcel["area_name"],
                    _opt_row(S.tr["area_name_fr"], S.parcel["name_fr"])),
            _opt_row(S.tr["area_name_ind"], S.parcel["name_ind"]),
            _coordinate_row(),
            _row(S.tr["area_province"], S.parcel["province"]),
            _row(S.tr["park_designation"], S.parcel["designation"]),
            _row(S.tr["area_pa_oecm"], _vocab(S.parcel["designation_type"], "pa_oecm")),
            _opt_row(S.tr["park_iucn_category"], S.parcel["iucn_category"], "iucn"),
            _opt_row(S.tr["park_status"], S.parcel["park_status"], "status"),
            rx.cond(S.parcel["status_year"],
                    _row(S.tr["park_status_year"], S.parcel["status_year"])),
            _row(S.tr["area_governance"], _vocab(S.parcel["governance"], "governance")),
            _opt_row(S.tr["area_owner_type"], S.parcel["owner_type"], "owner"),
            _opt_row(S.tr["park_managing_authority"], S.parcel["managing_authority"]),
            _row(S.tr["area_cpcad_id"], S.parcel["cpcad_id"], mono=True),
            _area_block(),
            rx.box(
                rx.text(S.disclosure, size="1", color=MUTED, line_height="1.45"),
                padding="2", background="var(--gray-2)", border=BORDER,
                border_radius="var(--radius-2)", margin_top="2", margin_bottom="6px",
            ),
        ),
    )


def zones_panel() -> rx.Component:
    return rx.cond(
        S.zones,
        section(
            S.tr["zones_title"],
            rx.foreach(
                S.zones,
                lambda z: rx.hstack(
                    rx.text(z["zone_label"], size="1"),
                    rx.spacer(),
                    rx.text(f"{z['area_ha']} ha", size="1", color=MUTED),
                    width="100%",
                ),
            ),
            info=S.tr["zones_note"],
        ),
    )
