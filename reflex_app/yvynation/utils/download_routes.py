"""
Same-origin streaming download endpoint for export archives.

Why this exists
---------------

Export ZIPs are routinely 50–100 MB, which rules out both of the obvious
delivery routes:

* ``rx.download(data=…)`` ships the archive as a base64 data-URI over the
  websocket — unreliable past a few tens of MB and ~3× the RAM.
* A direct ``https://storage.googleapis.com/…`` link fails twice over.
  ``rx.download()`` **rejects any URL that does not start with** ``/``
  (``ValueError: The URL argument should start with a /``), so the handler
  raises before the browser is ever involved — which is why downloads worked
  locally and failed the moment ``GCS_EXPORT_BUCKET`` was set. Even past that,
  a public bucket URL needs ``allUsers`` on the objects.
* Serving through Reflex's ``/_upload`` static mount sets ``Content-Length``,
  and Cloud Run caps *non-streaming* responses at ~32 MiB.

So exports are streamed from a route of our own: same-origin (``rx.download``
accepts it), chunked (no Content-Length, so Cloud Run's cap does not apply),
and read with the runtime service account's own credentials (no public ACL, no
signed-URL IAM setup).

Bytes are sourced in this order:

1. the local ``exports/`` directory — which on Cloud Run *is* the bucket, via
   the GCS FUSE volume;
2. failing that, the GCS client, so a download still works when it lands on a
   different instance than the one that produced the file.
"""

import logging
import os
from typing import Iterator, Optional

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse, StreamingResponse
from starlette.routing import Route

logger = logging.getLogger(__name__)

#: Mounted path. Must start with "/" so ``rx.download`` accepts it.
DOWNLOAD_PREFIX = "/download/exports"

#: 1 MiB — large enough that per-chunk overhead is irrelevant, small enough
#: that a few concurrent downloads cannot meaningfully dent an 8 GiB container.
_CHUNK = 1024 * 1024


def _safe_name(raw: str) -> Optional[str]:
    """Return *raw* if it is a plain filename, else ``None``.

    Starlette's ``{filename}`` param never matches ``/``, but ``..`` and
    absolute-looking names still arrive as-is — this endpoint reads whatever it
    is handed, so the check is the only thing standing between a crafted name
    and the rest of the filesystem.
    """
    if not raw or raw != os.path.basename(raw) or raw.startswith("."):
        return None
    return raw


def _iter_local(path) -> Iterator[bytes]:
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                return
            yield chunk


def _iter_gcs(bucket_name: str, blob_name: str) -> Iterator[bytes]:
    from google.cloud import storage

    client = storage.Client()
    blob = client.bucket(bucket_name).blob(blob_name)
    with blob.open("rb") as fh:
        while True:
            chunk = fh.read(_CHUNK)
            if not chunk:
                return
            yield chunk


async def _download_export(request: Request):
    raw = request.path_params.get("filename", "")
    name = _safe_name(raw)
    if name is None:
        logger.warning(f"[DOWNLOAD] rejected filename {raw!r}")
        return PlainTextResponse("Invalid filename", status_code=400)

    headers = {
        "Content-Disposition": f'attachment; filename="{name}"',
        # Deliberately no Content-Length: that is what keeps the response
        # chunked and out of Cloud Run's ~32 MiB non-streaming cap. The cost
        # is that browsers show an indeterminate progress bar.
        "Cache-Control": "no-store",
    }

    # 1. Local path — the GCS FUSE volume in production, the real directory
    #    in local development.
    try:
        from .export_service import get_export_dir

        path = get_export_dir() / name
        if path.is_file():
            return StreamingResponse(
                _iter_local(path), media_type="application/zip", headers=headers
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"[DOWNLOAD] local lookup for {name} failed: {exc}")

    # 2. Straight from the bucket — covers the case where the batch ran on a
    #    different Cloud Run instance and no FUSE volume is mounted.
    bucket_name = os.environ.get("GCS_EXPORT_BUCKET", "")
    if bucket_name:
        try:
            from google.cloud import storage

            client = storage.Client()
            if client.bucket(bucket_name).blob(name).exists(client):
                return StreamingResponse(
                    _iter_gcs(bucket_name, name),
                    media_type="application/zip",
                    headers=headers,
                )
            logger.warning(f"[DOWNLOAD] {name} not in gs://{bucket_name}")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"[DOWNLOAD] GCS read for {name} failed: {exc}", exc_info=True)
            return PlainTextResponse(
                "Export storage is unavailable — check the service account's "
                "access to the export bucket.",
                status_code=502,
            )

    return PlainTextResponse(
        "Export not found. It may have been pruned — only the most recent "
        "runs are kept.",
        status_code=404,
    )


def download_app() -> Starlette:
    """Starlette app carrying the download route.

    Passed to ``rx.App(api_transformer=…)``, which mounts Reflex's own app
    underneath it, so this route is matched first and everything else falls
    through to Reflex unchanged.
    """
    return Starlette(
        routes=[
            Route(
                f"{DOWNLOAD_PREFIX}/{{filename}}",
                _download_export,
                methods=["GET"],
            )
        ]
    )


def download_url_for(relpath: str) -> str:
    """App-relative download URL for an ``exports/``-relative path."""
    name = relpath[len("exports/"):] if relpath.startswith("exports/") else relpath
    return f"{DOWNLOAD_PREFIX}/{name.lstrip('/')}"
