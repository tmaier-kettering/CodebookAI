"""
Asynchronous batch processing operations for the UI.

This module provides functions for managing batch processing jobs
in background threads to prevent UI freezing during API operations.
"""

import threading
import tkinter as tk
from functools import partial
from tkinter import messagebox

# Handle imports based on how the script is run
try:
    from batch_processing import batch_method
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from batch_processing import batch_method


def call_batch_download_async(parent: tk.Tk, batch_id: str) -> None:
    """
    Download batch processing results on a background thread.

    Args:
        parent: Parent Tkinter window for error dialog ownership
        batch_id: Unique identifier of the batch job to download results from
    """
    def _worker():
        batch_method.get_batch_results(batch_id)
    threading.Thread(target=_worker, daemon=True).start()


def refresh_batches_async(parent: tk.Tk) -> None:
    """
    Refresh the batches table.

    Thin shim to the panel's own refresh (ui/batches_view.py owns the fetch
    thread and rendering now); kept so existing call sites (e.g. after a
    batch submission) don't need to know about the panel directly.

    Args:
        parent: The main window, which holds `.batches_panel`
    """
    parent.batches_panel.refresh()


def rerun_batch_async(parent: tk.Tk, batch_id: str, count: int) -> None:
    """
    Resubmit a batch with identical settings `count` times, on a background
    thread, then refresh the batches table.

    Args:
        parent: The main window, which holds `.batches_panel`
        batch_id: The batch to rerun
        count: How many times to resubmit
    """
    def _worker():
        try:
            batch_method.rerun_batch(batch_id, count)
            parent.after(0, parent.batches_panel.refresh)
        except Exception as error:
            parent.after(0, partial(messagebox.showerror, "Rerun Error", str(error)))
    threading.Thread(target=_worker, daemon=True).start()


def cancel_batch_async(parent: tk.Tk, batch_id: str) -> None:
    """
    Cancel a batch processing job on a background thread.

    Args:
        parent: Parent Tkinter window for error dialog ownership
        batch_id: Unique identifier of the batch job to cancel
    """
    def _worker():
        try:
            batch_method.cancel_batch(batch_id)
            parent.after(0, lambda: print("Cancel finished for batch:", batch_id))
        except Exception as error:
            parent.after(0, lambda: messagebox.showerror("Cancel Error", str(error)))
    threading.Thread(target=_worker, daemon=True).start()