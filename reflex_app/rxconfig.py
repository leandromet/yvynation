import reflex as rx

config = rx.Config(
    app_name="yvynation",
    tailwind_config=None,  # Using custom styling
    db_url="sqlite:///reflex.db",
    log_level="info",
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
