"""
Translation and internationalization support for Reflex app.

One module per language (en.py, pt.py, es.py, fr.py). English is the
reference dictionary: every key must exist in en.py, and the other
languages fall back to English for any key they don't define — so a
missing translation renders in English instead of blank.

To add a language: create <code>.py with a TRANSLATIONS_<CODE> dict,
register it in TRANSLATIONS and get_language_options() below, and run
the coverage report:

    python -m yvynation.utils.translations
"""

from typing import Dict, Optional

from .en import TRANSLATIONS_EN
from .pt import TRANSLATIONS_PT
from .es import TRANSLATIONS_ES
from .fr import TRANSLATIONS_FR

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": TRANSLATIONS_EN,
    "pt": TRANSLATIONS_PT,
    "es": TRANSLATIONS_ES,
    "fr": TRANSLATIONS_FR,
}


def t(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Get translated string.

    Args:
        key: Translation key
        lang: Language code (defaults to 'en')
        **kwargs: Format arguments for string interpolation

    Returns:
        Translated string, falling back to English, then to the key itself.
    """
    if lang is None:
        lang = "en"

    translations = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    result = translations.get(key, TRANSLATIONS["en"].get(key, key))

    if kwargs:
        try:
            result = result.format(**kwargs)
        except KeyError:
            pass

    return result


def get_translations(lang: Optional[str]) -> Dict[str, str]:
    """
    Full translation dict for a language, with English fallback.

    Any key missing from the requested language resolves to the English
    string instead of rendering blank in the UI.
    """
    if not lang or lang == "en" or lang not in TRANSLATIONS:
        return TRANSLATIONS["en"]
    return {**TRANSLATIONS["en"], **TRANSLATIONS[lang]}


def get_language_options() -> Dict[str, str]:
    """Get available languages."""
    return {
        "en": "English",
        "pt": "Português",
        "es": "Español",
        "fr": "Français",
    }


def missing_keys() -> Dict[str, list]:
    """Keys present in English but absent from each other language."""
    en_keys = set(TRANSLATIONS["en"])
    return {
        lang: sorted(en_keys - set(keys))
        for lang, keys in TRANSLATIONS.items()
        if lang != "en"
    }


def coverage_report() -> bool:
    """Print per-language key coverage; True when all complete."""
    en_keys = set(TRANSLATIONS["en"])
    ok = True
    for lang in TRANSLATIONS:
        keys = set(TRANSLATIONS[lang])
        missing = sorted(en_keys - keys)
        extra = sorted(keys - en_keys)
        print(f"{lang}: {len(keys)} keys, {len(missing)} missing, {len(extra)} extra")
        for k in missing:
            ok = False
            print(f"  missing: {k}")
        for k in extra:
            ok = False
            print(f"  extra:   {k}")
    print("OK — all languages complete" if ok else "INCOMPLETE — fix keys above")
    return ok
