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
    #: Name of the run currently being zipped (disables its row's buttons)
    previous_runs_busy: str = ""

    def load_previous_runs(self):
        """Refresh the run list from disk. Safe to call on every page load."""
        from ..utils.export_service import list_export_runs
        try:
            self.previous_runs = list_export_runs()
        except Exception as e:
            logger.error(f"[PREVIOUS_RUNS] list failed: {e}", exc_info=True)
            self.error_message = f"Could not list previous runs: {e}"
        self.previous_runs_loaded = True

    def download_previous_run(self, relpath: str):
        """Download an already-zipped run."""
        if not relpath:
            self.error_message = "This run isn't zipped yet — use 'Zip & download' first."
            return
        return rx.download(
            url=rx.get_upload_url(relpath),
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
            yield rx.download(
                url=rx.get_upload_url(relpath),
                filename=relpath.rsplit("/", 1)[-1],
            )

    def delete_previous_run(self, name: str, kind: str):
        """Delete a finished ZIP or a leftover run folder to free space."""
        from ..utils.export_service import delete_export_run
        try:
            delete_export_run(name, kind)
        except Exception as e:
            logger.error(f"[PREVIOUS_RUNS] delete failed for {name}: {e}", exc_info=True)
            self.error_message = f"Could not delete {name}: {e}"
        self.load_previous_runs()
