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

# Configure Reflex app
app = rx.App()

# Main index page
app.add_page(
    index,
    route="/",
    title="Yvynation - Indigenous Land Monitoring",
)
