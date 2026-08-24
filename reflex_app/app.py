"""
Main Reflex app initialization and routing.
Replaces Streamlit's streamlit_app.py
"""

import reflex as rx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import components after basic setup
from yvynation.config import GA_MEASUREMENT_ID
from yvynation.state import AppState
from yvynation.pages.index import index


def _ga_head_components() -> list[rx.Component]:
    """GA4 tag, only when YVY_GA_MEASUREMENT_ID is set (empty in local dev)."""
    if not GA_MEASUREMENT_ID:
        return []
    return [
        rx.el.script(src=f"https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}", async_=True),
        rx.el.script(f"""
            window.dataLayer = window.dataLayer || [];
            function gtag(){{ dataLayer.push(arguments); }}
            gtag('js', new Date());
            gtag('config', '{GA_MEASUREMENT_ID}');
        """),
    ]


# Configure Reflex app
app = rx.App(head_components=_ga_head_components())

# Main index page
app.add_page(
    index,
    route="/",
    title="Yvynation - Indigenous Land Monitoring",
)
