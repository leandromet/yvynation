"""
Yvynation Reflex app definition.
This module is discovered by Reflex's module loading system.
"""
import reflex as rx
from yvynation.pages.index import index
from yvynation.state import AppState

# Create and configure the app
app = rx.App()
app.add_page(
    index,
    route="/",
    title="Yvynation - Indigenous Land Monitoring Platform",
)
