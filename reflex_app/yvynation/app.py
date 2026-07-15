"""
Main Reflex app initialization and routing.
Replaces Streamlit's streamlit_app.py
"""

import reflex as rx
from .state import AppState
from .pages.index import index
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HydrateFallback loading overlay
# Addresses the React Router 7 "💿 Hey developer" hint by loading an external
# JS file from /assets/yvy-loading.js.
#
# Using src= (external file) instead of an inline text child is critical:
# React HTML-escapes text children of <script> tags, so an inline string
# would never execute — and can even break JSX compilation.
# The external file is served by Reflex from the assets/ directory.
# ---------------------------------------------------------------------------
app = rx.App(
    head_components=[
        rx.el.script(src="/assets/yvy-loading.js"),
    ],
)

# Main index page
app.add_page(
    index,
    route="/",
    title="Yvynation - Indigenous Land Monitoring",
    on_load=[AppState.detect_browser_language, AppState.initialize_app],
)
