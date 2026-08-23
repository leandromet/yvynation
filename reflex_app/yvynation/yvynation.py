"""
Yvynation Reflex app definition.
This module is discovered by Reflex's module loading system.
"""
import reflex as rx
from yvynation.pages.index import index
from yvynation.state import AppState
from yvynation.utils.download_routes import download_app

# Create and configure the app.
#
# api_transformer mounts Reflex's own ASGI app underneath ours, so the export
# download route is matched first and every other path falls through to Reflex
# untouched. Large exports need a streaming, same-origin endpoint — see
# utils/download_routes.py for why neither rx.download(data=…) nor a direct
# bucket URL works.
app = rx.App(api_transformer=download_app())
app.add_page(
    index,
    route="/",
    title="Yvynation - Land Monitoring Platform",
)
