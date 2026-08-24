"""
Yvynation Reflex app definition.
This module is discovered by Reflex's module loading system.
"""
import reflex as rx
from yvynation.config import GA_MEASUREMENT_ID
from yvynation.pages.index import index
from yvynation.state import AppState
from yvynation.utils.download_routes import download_app


def _ga_head_components() -> list[rx.Component]:
    """GA4 tag, only when YVY_GA_MEASUREMENT_ID is set (empty in local dev).

    rx.el.script, not rx.script: the latter wraps react-helmet-async's
    portal-based Helmet component, which needs a HelmetProvider elsewhere in
    the tree that this app doesn't have — it silently renders nothing.
    rx.el.script is a plain native <script> element, same as the framework's
    own meta/link tags, and is what actually reaches the page.
    """
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


# Create and configure the app.
#
# api_transformer mounts Reflex's own ASGI app underneath ours, so the export
# download route is matched first and every other path falls through to Reflex
# untouched. Large exports need a streaming, same-origin endpoint — see
# utils/download_routes.py for why neither rx.download(data=…) nor a direct
# bucket URL works.
app = rx.App(api_transformer=download_app(), head_components=_ga_head_components())
app.add_page(
    index,
    route="/",
    title="Yvynation - Land Monitoring Platform",
)
