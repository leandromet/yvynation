"""
Previous Runs event handlers.

Lists finished batch/export ZIPs and any leftover run folders (in progress
or crashed mid-run) sitting under uploaded_files/exports/, so results
survive a page reload or a container restart as long as the underlying
storage does — see CLOUD_RUN_DEPLOYMENT.md: exports/ is GCS-backed in
production specifically so this page keeps working after an OOM kill.
"""

import asyncio
import logging
from typing import Any, Dict, List

import reflex as rx

logger = logging.getLogger(__name__)


class PreviousRunsMixin(rx.State, mixin=True):
    """Event handlers and state for the Previous Runs page."""

    previous_runs: List[Dict[str, Any]] = []
    previous_runs_loaded: bool = False
    #: Page that opened Previous Runs ("portal" | "batch") — the back button
    #: returns there, so leaving the page never discards a batch selection.
    #: See _ui.go_to_previous_runs / _ui.leave_previous_runs.
    previous_runs_return_to: str = "portal"
    #: Name of the run currently being zipped (disables its row's buttons)
    previous_runs_busy: str = ""
    #: Name of the run whose detail panel is open ("" = all collapsed). Only one
    #: at a time, so the details of a large archive never accumulate in state.
    previous_runs_expanded: str = ""
    #: Details for ``previous_runs_expanded`` — see export_service.read_run_details.
    #: Held as separate, concretely-typed vars rather than one Dict[str, Any]:
    #: Reflex cannot ``foreach`` over a var whose element type is ``Any``.
    previous_runs_detail_config: List[Dict[str, str]] = []
    previous_runs_detail_territories: List[Dict[str, str]] = []
    previous_runs_detail_perf: List[Dict[str, str]] = []
    previous_runs_detail_verdict: str = ""
    previous_runs_detail_report: str = ""
    previous_runs_detail_message: str = ""
    #: Name of the run whose details are being read (shows a spinner)
    previous_runs_detail_busy: str = ""

    def _clear_run_details(self):
        self.previous_runs_detail_config = []
        self.previous_runs_detail_territories = []
        self.previous_runs_detail_perf = []
        self.previous_runs_detail_verdict = ""
        self.previous_runs_detail_report = ""
        self.previous_runs_detail_message = ""

    def load_previous_runs(self):
        """Refresh the run list from disk. Safe to call on every page load."""
        from ..utils.export_service import list_export_runs
        try:
            self.previous_runs = list_export_runs()
        except Exception as e:
            logger.error(f"[PREVIOUS_RUNS] list failed: {e}", exc_info=True)
            self.error_message = f"Could not list previous runs: {e}"
        self.previous_runs_loaded = True

    @rx.event(background=True)
    async def toggle_run_details(self, name: str, kind: str):
        """Open (or close) the detail panel for one run.

        Reads ``batch_summary.json`` out of the archive off the event loop:
        opening a multi-hundred-MB ZIP on the GCS FUSE volume has to seek to
        the central directory first, which is quick but not instant.
        """
        async with self:
            if self.previous_runs_expanded == name:
                self.previous_runs_expanded = ""
                self._clear_run_details()
                return
            self.previous_runs_expanded = name
            self._clear_run_details()
            self.previous_runs_detail_busy = name

        from ..utils.export_service import read_run_details
        loop = asyncio.get_event_loop()
        try:
            details = await loop.run_in_executor(None, read_run_details, name, kind)
        except Exception as e:  # noqa: BLE001
            logger.error(f"[PREVIOUS_RUNS] details failed for {name}: {e}", exc_info=True)
            details = {"message": f"Could not read this run: {e}"}

        async with self:
            self.previous_runs_detail_busy = ""
            # A second click may have collapsed the row (or opened another one)
            # while the archive was being read — don't clobber that.
            if self.previous_runs_expanded != name:
                return
            self.previous_runs_detail_config = details.get("config") or []
            self.previous_runs_detail_territories = details.get("territories") or []
            self.previous_runs_detail_perf = details.get("performance") or []
            self.previous_runs_detail_verdict = details.get("verdict") or ""
            self.previous_runs_detail_report = details.get("report") or ""
            self.previous_runs_detail_message = details.get("message") or ""

    def copy_bucket_link(self, url: str):
        """Put a run's bucket link on the clipboard."""
        if not url:
            return
        return rx.set_clipboard(url)

    def download_previous_run(self, relpath: str):
        """Download an already-zipped run."""
        if not relpath:
            self.error_message = "This run isn't zipped yet — use 'Zip & download' first."
            return
        from ..utils.export_service import get_download_url
        return rx.download(
            url=get_download_url(relpath),
            filename=relpath.rsplit("/", 1)[-1],
        )

    @rx.event(background=True)
    async def zip_and_download_run(self, name: str):
        """Compress a still-present (in-progress/crashed) run folder on
        demand, then trigger its download."""
        async with self:
            self.previous_runs_busy = name

        from ..utils.export_service import zip_partial_run
        loop = asyncio.get_event_loop()
        try:
            relpath = await loop.run_in_executor(None, zip_partial_run, name)
        except Exception as e:
            logger.error(f"[PREVIOUS_RUNS] zip failed for {name}: {e}", exc_info=True)
            relpath = None

        async with self:
            self.previous_runs_busy = ""
            self.load_previous_runs()
            if not relpath:
                self.error_message = (
                    f"Could not build a ZIP for {name} — it may be empty "
                    "or still being written by an active run."
                )

        if relpath:
            from ..utils.export_service import get_download_url
            download_url = await loop.run_in_executor(None, get_download_url, relpath)
            yield rx.download(
                url=download_url,
                filename=relpath.rsplit("/", 1)[-1],
            )

    def delete_previous_run(self, name: str, kind: str):
        """Delete a finished ZIP or a leftover run folder to free space."""
        from ..utils.export_service import delete_export_run
        if self.previous_runs_expanded == name:
            self.previous_runs_expanded = ""
            self._clear_run_details()
        try:
            delete_export_run(name, kind)
        except Exception as e:
            logger.error(f"[PREVIOUS_RUNS] delete failed for {name}: {e}", exc_info=True)
            self.error_message = f"Could not delete {name}: {e}"
        self.load_previous_runs()
