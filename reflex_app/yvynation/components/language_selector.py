"""
Shared language selector dropdown.

Shows the current language (flag + name) in the trigger and switches
AppState.language on change. Used in the navbars of the portal, the
geometry/territory analysis pages, and the batch processing page.

Languages must match yvynation/utils/translations/ (en, pt, es, fr).
"""

import reflex as rx

from ..state import AppState

LANGUAGES = [
    ("en", "🇬🇧 English"),
    ("pt", "🇧🇷 Português"),
    ("es", "🇪🇸 Español"),
    ("fr", "🇨🇦 Français"),
]


def language_selector(**trigger_props) -> rx.Component:
    """Dropdown bound to AppState.language; trigger shows the active language."""
    return rx.select.root(
        rx.select.trigger(
            variant="soft",
            color_scheme="green",
            **trigger_props,
        ),
        rx.select.content(
            *[rx.select.item(label, value=code) for code, label in LANGUAGES],
        ),
        value=AppState.language,
        on_change=AppState.set_language,
        size="2",
    )
