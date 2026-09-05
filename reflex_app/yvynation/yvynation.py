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
app = rx.App(
    api_transformer=download_app(),
    head_components=[
        *_ga_head_components(),
        # Without this, mobile browsers lay the page out at ~980px and zoom
        # out to fit — every responsive breakpoint in pages/index.py would
        # evaluate as "desktop" and the mobile sheet would never appear.
        # Ported from camposcope/naturametrics, which both carry it for the
        # same reason.
        rx.el.meta(
            name="viewport",
            content="width=device-width, initial-scale=1, viewport-fit=cover",
        ),
        rx.el.meta(name="theme-color", content="#ffffff"),
        # The desktop/mobile split in pages/index.py is width-only
        # (`display=[...]` breakpoints), and a phone rotated to landscape is
        # routinely wider than the 768px "md" cutoff (iPhone 13: 844px)
        # while still only ~390px tall — it would fall into the desktop
        # sidebar + results-drawer chrome, sized for a viewport with far
        # more height to spare. This overrides by HEIGHT instead, which is
        # the dimension actually in short supply; only a media query can ask
        # about it. The ids are set in pages/index.py.
        rx.el.style("""
            @media (max-height: 500px) and (orientation: landscape) {
              #yvy-desktop-sidebar, #yvy-sidebar-resize,
              #yvy-results-drawer { display: none !important; }
              #yvy-mobile-sheet { display: flex !important; }
              /* The batch page's own two-column / single-stage split, same
                 reasoning: side-by-side columns need height as much as width,
                 and a rotated phone has none to give. */
              #batch-wide-body { display: none !important; }
              #batch-narrow-body { display: flex !important; }
            }
        """),
        # `rx.plotly`'s `config.responsive` resizes a chart through its own
        # internal ResizeObserver on the plot's container — which watches
        # that ELEMENT's box, not the viewport, and does not reliably fire
        # for every browser/orientation-change combination. The symptom is a
        # chart that keeps the width it had in the PREVIOUS orientation.
        # This app is the most chart-heavy of the three
        # (components/analysis_tabs.py is ~2400 lines of rx.plotly) and
        # every one of them is a `.js-plotly-plot`, so one global listener
        # that force-resizes all of them is a reliable fallback that does
        # not depend on that observer at all. Ported from camposcope.
        rx.el.script("""
            (function () {
              if (window._yvyPlotlyResizeInit) return;
              window._yvyPlotlyResizeInit = true;
              var timer = null;
              function resizeAll() {
                if (!window.Plotly) return;
                document.querySelectorAll('.js-plotly-plot').forEach(function (gd) {
                  try { window.Plotly.Plots.resize(gd); } catch (err) { /* not fully mounted yet */ }
                });
              }
              function scheduleResize() {
                window.clearTimeout(timer);
                timer = window.setTimeout(resizeAll, 120);
              }
              window.addEventListener('resize', scheduleResize);
              window.addEventListener('orientationchange', scheduleResize);
            })();
        """),
        # Idle tabs otherwise keep the Reflex WebSocket reconnecting forever,
        # which pins a billed Cloud Run instance with nobody using it. Gated
        # on AppState.idle_guard_busy (via #idle-guard-marker in
        # pages/index.py) so it never fires mid-batch-run — see
        # assets/idle_guard.js and assets/paused.html.
        rx.el.script(src="/assets/idle_guard.js", defer=True),
    ],
)
app.add_page(
    index,
    route="/",
    title="Yvynation - Land Monitoring Platform",
)
