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
from yvynation.state import AppState
from yvynation.pages.index import index

# Configure Reflex app
app = rx.App()

# Main index page
app.add_page(
    index,
    route="/",
    title="Yvynation - Indigenous Land Monitoring",
)
