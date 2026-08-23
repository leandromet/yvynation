"""Rate limiting and access logging in front of ``run_batch_processing``.

Every Reflex event handler is an unauthenticated public RPC by design. That
was an acceptable risk while starting a batch meant clicking through the
territory picker by hand. It stopped being acceptable once a script could
call the same handler in a loop: ``run_batch_processing`` runs up to
``BATCH_MAX_SELECTION`` territories of Earth Engine compute per call, with no
map interaction required.

Two independent layers:

1. The friction step (``components/batch_action_panel.py``,
   ``state/_batch.py request_batch_run``) — a UI-only "are you sure" that
   deters an accidental double-click but nothing scripted, since a script
   calling ``run_batch_processing`` directly over the WebSocket skips it.
2. This module — the actual enforcement, checked server-side inside
   ``run_batch_processing`` regardless of how it was reached.

Ported from ``naturametrics/services/abuse_control.py`` (same pattern, own
bucket — see ``docs/ABUSE_CONTROL.md`` for why a separate bucket rather than
reusing ``OUTPUT_BUCKET``).
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone

from ..config import (
    ABUSE_BUCKET,
    ABUSE_IP_MAX_PER_WINDOW,
    ABUSE_IP_WINDOW_S,
    ABUSE_SESSION_COOLDOWN_S,
)

logger = logging.getLogger(__name__)

_bucket = None
_UNSAFE_KEY_CHARS = re.compile(r"[^A-Za-z0-9._-]")


def _safe_key(raw: str) -> str:
    """Object-name-safe version of an IP or client token.

    Empty input maps to the literal ``"unknown"`` rather than an empty
    string — an empty object-name component would either error or, worse,
    collide every caller onto the same blob.
    """
    return _UNSAFE_KEY_CHARS.sub("_", raw) or "unknown"


def _get_bucket():
    global _bucket
    if _bucket is not None:
        return _bucket
    from google.cloud import storage

    _bucket = storage.Client().bucket(ABUSE_BUCKET)
    return _bucket


def _read_json(blob) -> tuple[dict | None, int | None]:
    try:
        raw = blob.download_as_bytes()
    except Exception:  # noqa: BLE001 — includes "not found"
        return None, None
    try:
        return json.loads(raw), blob.generation
    except (ValueError, TypeError):
        return None, blob.generation


def _cas_write(blob, generation, payload: dict) -> bool:
    """Compare-and-swap write. False means someone else won the race."""
    from google.api_core.exceptions import PreconditionFailed

    try:
        blob.upload_from_string(
            json.dumps(payload),
            content_type="application/json",
            if_generation_match=generation,
        )
        return True
    except PreconditionFailed:
        return False


def _check_window_counter(
    key_prefix: str, key: str, max_per_window: int, window_s: int
) -> tuple[bool, str]:
    if not key:
        return True, ""
    try:
        bucket = _get_bucket()
        blob = bucket.blob(f"{key_prefix}/{_safe_key(key)}.json")
        for _ in range(4):
            payload, generation = _read_json(blob)
            now = time.time()
            if payload and now - payload.get("window_start", 0) < window_s:
                count = payload.get("count", 0)
                if count >= max_per_window:
                    return False, (
                        f"Limit of {max_per_window} batch runs per "
                        f"{window_s // 60} min reached for this IP."
                    )
                new_payload = {"count": count + 1, "window_start": payload["window_start"]}
            else:
                new_payload = {"count": 1, "window_start": now}
            if _cas_write(blob, generation, new_payload):
                return True, ""
        # Lost every race — fail open rather than block a legitimate request.
        logger.warning("abuse_control: exhausted CAS retries for %s/%s", key_prefix, key)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("abuse_control: %s check failed open: %s", key_prefix, exc)
        return True, ""


def check_session_cooldown(client_token: str) -> tuple[bool, str]:
    if not client_token:
        return True, ""
    try:
        bucket = _get_bucket()
        blob = bucket.blob(f"cooldown/{_safe_key(client_token)}.json")
        for _ in range(4):
            payload, generation = _read_json(blob)
            now = time.time()
            if payload:
                elapsed = now - payload.get("last_at", 0)
                if elapsed < ABUSE_SESSION_COOLDOWN_S:
                    remaining = int(ABUSE_SESSION_COOLDOWN_S - elapsed)
                    return False, (
                        f"Please wait {remaining}s before starting another "
                        f"batch in this tab/session."
                    )
            if _cas_write(blob, generation, {"last_at": now}):
                return True, ""
        logger.warning("abuse_control: exhausted CAS retries for cooldown/%s", client_token)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("abuse_control: cooldown check failed open: %s", exc)
        return True, ""


def check_ip_rate_limit(ip: str) -> tuple[bool, str]:
    return _check_window_counter("ratelimit", ip, ABUSE_IP_MAX_PER_WINDOW, ABUSE_IP_WINDOW_S)


def log_event(
    *,
    ip: str,
    client_token: str,
    session_id: str,
    action: str,
    outcome: str,
    detail: dict | None = None,
) -> None:
    """Best-effort write of one immutable log object. Never raises.

    The IP is stored in plain text on purpose — see docs/ABUSE_CONTROL.md:
    the point of logging by IP is that the app owner can read it back, and
    the bucket is private, so hashing it here would only hide it from the
    one person it is for.
    """
    try:
        now = datetime.now(timezone.utc)
        payload = {
            "timestamp": now.isoformat(),
            "ip": ip,
            "client_token": client_token,
            "session_id": session_id,
            "action": action,
            "outcome": outcome,
            "detail": detail or {},
        }
        bucket = _get_bucket()
        date = now.strftime("%Y-%m-%d")
        name = f"logs/{date}/{now.strftime('%H%M%S')}-{uuid.uuid4().hex[:8]}.json"
        bucket.blob(name).upload_from_string(
            json.dumps(payload), content_type="application/json"
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("abuse_control: log_event failed (non-fatal): %s", exc)
