"""UI text for the USA page (English canonical, Portuguese overrides).

The Indigenous-lands notice is the Brazil page's own (``utils/translations``), so the
two pages cannot drift apart on it.
"""

from __future__ import annotations

from typing import Dict

from ...utils.translations import get_translations as _brazil_tr
from .en import TRANSLATIONS_EN
from .pt import TRANSLATIONS_PT

_SHARED = ("indigenous_data_notice_title", "indigenous_data_notice_body")


def get_translations(lang: str) -> Dict[str, str]:
    base = dict(TRANSLATIONS_EN if lang != "pt" else {**TRANSLATIONS_EN, **TRANSLATIONS_PT})
    shared = _brazil_tr("pt" if lang == "pt" else "en")
    for k in _SHARED:
        base[k] = shared[k]
    return base
