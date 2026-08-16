# Export Downloads

How a finished batch ZIP reaches the browser, and why it is served the way it
is. Relevant files: [`utils/download_routes.py`](../yvynation/utils/download_routes.py),
`utils/export_service.get_download_url`, `yvynation.py`.

## The route

```
GET /download/exports/{filename}
```

Streams the archive with `Content-Disposition: attachment`, in 1 MiB chunks,
**without** a `Content-Length` header. Mounted by passing a small Starlette app
to `rx.App(api_transformer=…)`; Reflex's own app is mounted underneath, so every
other path is untouched.

Bytes are sourced in order:

1. the local `exports/` directory — which on Cloud Run *is* the bucket, via the
   GCS FUSE volume;
2. failing that, the GCS client, so a download still works if the request lands
   on a different instance than the one that produced the file.

Both read with the runtime service account's own credentials. **The bucket does
not need to be public**, and no signed-URL IAM setup is required.

## Why not something simpler

| Approach | Why it fails |
|---|---|
| `rx.download(data=…)` | Ships the archive as a base64 data-URI over the websocket. Unreliable past a few tens of MB and ~3× the RAM. |
| Direct `https://storage.googleapis.com/…` link | **`rx.download()` rejects any URL that does not start with `/`** — it raises `ValueError: The URL argument should start with a /` inside the event handler. Separately, a public bucket URL needs `allUsers` on the objects. |
| Reflex's `/_upload` static mount | Starlette's static file serving sets `Content-Length`, and Cloud Run caps *non-streaming* responses at ~32 MiB — far below a typical 50–100 MB batch ZIP. |

### The bug this replaced

Downloads worked locally and failed in production with a bare "an error
occurred", on both the batch page and Previous Runs.

`get_download_url()` returned `rx.get_upload_url(relpath)` (→ `/_upload/…`) when
`GCS_EXPORT_BUCKET` was unset, and an absolute `https://storage.googleapis.com/…`
URL when it was set. The absolute URL tripped `rx.download`'s leading-slash
check, so the handler raised before the browser was ever involved — hence the
generic error, and hence the perfect correlation with the env var rather than
with file size or bucket permissions.

## Operational notes

* **Cloud Run request timeout** applies to the whole download. The deploy
  command in [`CLOUD_RUN_DEPLOYMENT.md`](../CLOUD_RUN_DEPLOYMENT.md) uses
  `--timeout 300`; a 90 MB archive over a slow connection can exceed five
  minutes. Raise it (`--timeout 3600`) if downloads cut off partway.
* **Progress bars are indeterminate.** Omitting `Content-Length` is what keeps
  the response chunked and out of Cloud Run's size cap; the cost is that the
  browser cannot show a percentage.
* **Pruning.** `prune_old_exports()` keeps only the newest few archives of each
  kind, so a link to an older run can legitimately 404. The endpoint returns a
  message saying so rather than a bare 404.
* **Path safety.** Only a plain filename is accepted — anything containing a
  path separator, starting with `.`, or not equal to its own basename is
  rejected with 400 before any filesystem access.

## Verification

Covered by an ASGI-level harness (not just `TestClient`, which coalesces the
response body and so cannot distinguish streaming from buffering):

* a 40 MB file is delivered complete, in 40 × 1 MiB chunks, with no
  `Content-Length`
* correct `application/zip` type and attachment filename
* `..`, `.hidden`, and encoded traversal are all rejected
* a missing file returns 404 with the pruning explanation
* the mount does not shadow Reflex — `/ping` still answers on the composed app
