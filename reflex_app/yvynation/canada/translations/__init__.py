"""UI text for the Canada page.

English is canonical here — the inverse of the Brazil page, where Portuguese
is. That is not an inconsistency to tidy up: each page's source language is the
one its data speaks. ParcelMap BC, the AAFC and NTEMS legends are published in
English (and French), so English is where the vocabulary is unambiguous, and
Portuguese is the translation. On the Brazil page it is the other way round.

Missing keys fall back to English, so an incomplete language shows real text
rather than a blank or a raw key.
"""

from __future__ import annotations

from ._yvynation_en import YVY_EN
from ._yvynation_pt import YVY_PT
from .en import TRANSLATIONS_EN as _CS_EN
from .pt import TRANSLATIONS_PT as _CS_PT

#: camposcope's Canada text (en.py / pt.py, ported) with Yvynation's own
#: protected-area text layered on top (_yvynation_*.py).
TRANSLATIONS_EN = {**_CS_EN, **YVY_EN}
TRANSLATIONS_PT = {**_CS_PT, **YVY_PT}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": TRANSLATIONS_EN,
    "pt": TRANSLATIONS_PT,
}


def get_translations(lang: str) -> dict[str, str]:
    overrides = TRANSLATIONS.get(lang)
    if not overrides or lang == "en":
        return TRANSLATIONS_EN
    return {**TRANSLATIONS_EN, **overrides}


def t(key: str, lang: str) -> str:
    return get_translations(lang).get(key, key)


def missing_keys() -> dict[str, set[str]]:
    ref = set(TRANSLATIONS_EN)
    out = {}
    for lang, table in TRANSLATIONS.items():
        if lang == "en":
            continue
        diff = ref ^ set(table)
        if diff:
            out[lang] = diff
    return out
