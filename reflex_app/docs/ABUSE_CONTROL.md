# Abuse control

**Why this exists.** Every Reflex event handler is an unauthenticated public RPC
by design — true of this app from the start. That was an acceptable risk while
starting a batch meant clicking through the territory picker by hand, one land
at a time. It is not acceptable for `run_batch_processing`: a single call runs
up to `BATCH_MAX_SELECTION` (100) territories of Earth Engine compute — GLAD,
GFC, buffers, PDF maps, the deforestation timeline — with no map interaction
required, trivial to script and loop. This module is the response, written up
during the security audit that also produced Naturametrics'
[`naturametrics/doc/13-abuse-control.md`](https://github.com/leandromet/naturametrics/blob/main/doc/13-abuse-control.md),
whose pattern this ports directly.

Two independent layers, in the order they run:

1. **The friction step** (`components/batch_action_panel.py`,
   `state/_batch.py request_batch_run`) — a UI-only "are you sure" in front
   of the Start button, showing the same territory count already on the
   button. It deters an accidental or reflexive click; it deters nothing
   scripted, since a script calling `run_batch_processing` directly over the
   WebSocket skips it entirely — which is exactly why it is not the
   enforcement.
2. **`utils/abuse_control.py`** — the actual enforcement, checked
   server-side inside `run_batch_processing` regardless of how it was
   reached.

---

## 1. The bucket

`gs://yvynation-abuse-control` — created for this specifically, **not**
shared with the export bucket (`OUTPUT_BUCKET` / `GCS_EXPORT_BUCKET`, which
holds finished ZIPs only and has no rate-limiting or logging logic in it).
Reasons a bucket rather than in-process state:

- **Cross-instance.** Cloud Run runs more than one instance under load, and
  an in-process counter would let a script spread requests across instances
  and never see a limit.
- **Survives a restart.** A deploy or a crashed instance does not reset
  anyone's cooldown or count.
- **Isolated failure domain.** A GCS hiccup on the export bucket (used on
  every successful run) must never take the rate limiter down with it, and
  vice versa — see EXPORT_DOWNLOADS.md for why the export bucket already
  carries real download traffic.

Configuration (`config/config.py`):

| Setting | Default | Meaning |
|---|---|---|
| `YVY_ABUSE_BUCKET` | `yvynation-abuse-control` | Bucket name |
| `YVY_ABUSE_SESSION_COOLDOWN_S` | `300` | Minimum time between one browser tab's batch runs |
| `YVY_ABUSE_IP_MAX_PER_WINDOW` | `3` | Batch runs one IP may start per window |
| `YVY_ABUSE_IP_WINDOW_S` | `3600` | The window, in seconds |

Bucket properties (set once, at creation — not reproduced by app code):

- **Region:** `us-west1`, matching the Cloud Run service.
- **Uniform bucket-level access + public access prevention enforced.**
  Nobody reaches this bucket except through IAM; there is no signed-URL or
  object-ACL path in or out.
- **IAM:** `roles/storage.objectAdmin`, scoped to the bucket, granted to the
  Cloud Run runtime service account only.
- **Lifecycle rule:** delete any object after 90 days. Nothing in this
  module manages retention itself — old rate-limit and log objects age out
  on their own.

## 2. What gets checked, and how

Two keys, both read-modify-write against a small JSON object with an
`if_generation_match` compare-and-swap (a handful of retries on a lost race
— rare, since it only happens under truly concurrent requests from the
*same* key):

- **Session cooldown** — `cooldown/{client_token}.json`, `{"last_at": <epoch
  seconds>}`. Keyed on the Reflex **client token**
  (`self.router.session.client_token`), not the session id: the client
  token is stable across reconnects *and page reloads* for the same browser
  tab, so refreshing the page does not reset the cooldown the way an
  in-memory session field would have.
- **IP rate limit** — `ratelimit/{ip}.json`, `{"count": int, "window_start":
  <epoch seconds>}`. Keyed on `self.router.session.client_ip` — Reflex
  already unrolls `X-Forwarded-For` into this field correctly for a service
  sitting behind Cloud Run's proxy, so no custom middleware is needed to
  get the real client address.

Both are captured inside the `async with self:` block at the top of
`run_batch_processing` (where `self.router` is reachable), then checked
outside it via `loop.run_in_executor` — the GCS round-trips are blocking
I/O and must not hold the state lock.

**Both fail open on any bucket error**, logged as a warning, not raised. A
rate limiter that takes the app down during a GCS hiccup is a worse bug
than the abuse it exists to catch — the friction step above still slows a
human down even if this backstop is briefly unavailable.

## 3. Logging

Every check — allowed or refused — writes one immutable JSON object to
`logs/{date}/{time}-{uuid}.json`:

```json
{
  "timestamp": "2026-08-19T23:53:12.64Z",
  "ip": "203.0.113.5",
  "client_token": "…",
  "session_id": "…",
  "action": "batch_run",
  "outcome": "allowed",
  "detail": {"n_territories": 12}
}
```

The IP is stored **in plain text** on purpose. The point of logging by IP
is that the app owner can read it back later to see who is hitting the
limits and, if it comes to that, block an address at the network level —
the bucket is private (§1), so hashing it here would only hide it from the
one person it is for. One object per event rather than appending to a
shared log file: GCS has no atomic append, and a unique object name per
event sidesteps the concurrent-write problem entirely instead of needing
to solve it.

To read the log:

```bash
gcloud storage cat gs://yvynation-abuse-control/logs/2026-08-19/*.json
```

## 4. Relationship to Naturametrics

This module was ported from Naturametrics'
`services/abuse_control.py` (same read-modify-write CAS pattern, same
fail-open philosophy, same log schema) once Yvynation was checked for the
same weak spot during Naturametrics' own pre-public-repo audit and found to
have no rate-limiting or logging mechanism anywhere in `state/`, `pages/`
or `components/`. Each app has **its own bucket** — `yvynation-abuse-control`
here, `naturametrics-abuse-control` there — rather than sharing one:
`run_batch_processing` and Naturametrics' `download_selection` are reached
from different Cloud Run services, and a shared bucket would mean a bug or
outage in one app's limiter logic could throttle the other's.
