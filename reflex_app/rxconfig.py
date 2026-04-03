import os
import reflex as rx

config = rx.Config(
    app_name="yvynation",
    tailwind_config=None,
    # SQLite is fine for single-instance Cloud Run.
    # For multi-instance, switch to Cloud SQL:
    #   db_url="postgresql+asyncpg://user:pass@/db?host=/cloudsql/project:region:instance"
    db_url=os.environ.get("REFLEX_DB_URL", "sqlite:///reflex.db"),
    log_level=os.environ.get("REFLEX_LOG_LEVEL", "info"),
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
    # Ports: overridable via env so Cloud Run's $PORT is respected.
    backend_port=int(os.environ.get("PORT", 8000)),
    frontend_port=int(os.environ.get("PORT", 3000)),
)
