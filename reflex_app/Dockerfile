# Yvynation – Cloud Run Dockerfile
# Uses Reflex's --single-port production mode: one process serves the compiled
# frontend (React/Vite) and the backend (uvicorn) on $PORT (default 8080).
# The Reflex JS runtime automatically rewrites ws://localhost:8000/_event to
# wss://<cloud-run-hostname>/_event when the page is served over HTTPS.

FROM python:3.11-slim

WORKDIR /app

# ── System dependencies ──────────────────────────────────────────────────────
# chromium: kaleido>=1.0 (Plotly → PNG for batch ZIPs and interactive exports)
# dropped its bundled renderer and drives a system Chrome/Chromium over CDP
# instead. Runs as root here, but choreographer (kaleido's browser launcher)
# already appends --no-sandbox by default, so no extra flag/env var is needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git ca-certificates build-essential unzip \
    gdal-bin libgdal-dev libpq-dev \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# ── Bun (Reflex frontend build toolchain) ────────────────────────────────────
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:$PATH"

# ── Python dependencies (layer cached before code copy) ──────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────────────────────────
COPY . .

# ── Pre-install Reflex frontend packages ─────────────────────────────────────
# This runs `bun install` inside .web/ so the heavy node_modules layer is
# cached in the image, keeping cold-start frontend builds fast (~30s vs ~3min).
ENV REFLEX_ENV=prod
RUN reflex init

# Smoke-test: ensure the Python app can be imported without errors, and that
# kaleido can actually drive the apt-installed Chromium end-to-end (catches a
# missing shared-library dependency or a sandbox/permission issue at build
# time instead of on the first user export in production).
RUN python -c "from yvynation.yvynation import app; print('Import OK')" && \
    python -c "\
import plotly.graph_objects as go; \
from yvynation.utils.export_service import _plotly_to_png_bytes; \
png = _plotly_to_png_bytes(go.Figure(go.Bar(x=['a'], y=[1])), width=200, height=200); \
assert png and png[:8] == b'\x89PNG\r\n\x1a\n', 'kaleido PNG export failed'; \
print('Kaleido PNG export OK')"

# ── Runtime configuration ────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
# PORT is set by Cloud Run (default 8080); override locally as needed.
ENV PORT=8080

EXPOSE 8080

# ── Startup ──────────────────────────────────────────────────────────────────
# --env prod        → builds the Vite frontend then runs uvicorn (no dev HMR)
# --single-port     → frontend + backend share the same port (required for Cloud Run)
# --backend-port    → read from $PORT so Cloud Run's port binding is honoured
# --backend-host    → 0.0.0.0 so Cloud Run's health checks can reach the container
CMD ["sh", "-c", "reflex run --env prod --single-port --backend-port ${PORT:-8080} --backend-host 0.0.0.0 --loglevel info"]
