"""
Asynchronous batch processing operations for the UI.

This module provides functions for managing batch processing jobs
in background threads to prevent UI freezing during API operations.
Compatible with both tkinter and customtkinter.
"""

import threading
import tkinter as tk
import customtkinter as ctk
from functools import partial
from typing import Union

# Import dialog wrappers
try:
    from ui.dialogs import show_error
except ImportError:
    from dialogs import show_error

# Handle imports based on how the script is run
try:
    from batch_processing import batch_method
    from batch_processing.batch_method import list_batches
    from ui.ui_utils import populate_treeview
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from batch_processing import batch_method
    from batch_processing.batch_method import list_batches
    from ui.ui_utils import populate_treeview


def call_batch_async(parent: Union[tk.Tk, ctk.CTk], type: str) -> None:
    """
    Start a new batch processing job on a background thread.

    This function launches the batch creation process in a separate thread
    to prevent the UI from freezing during file selection and API calls.

    Args:
        parent: Parent window for error dialog ownership
        type: Type of batch processing job to start
    """
    def _worker():
        try:
            result = batch_method.send_batch(parent, type)
            refresh_batches_async(parent)
            parent.after(0, lambda: print("batch_method finished:", result))
        except Exception as error:
            parent.after(0, lambda: show_error("Batch Error", str(error)))
    threading.Thread(target=_worker, daemon=True).start()


def call_batch_download_async(parent: Union[tk.Tk, ctk.CTk], batch_id: str) -> None:
    """
    Download batch processing results on a background thread.

    Args:
        parent: Parent window for error dialog ownership
        batch_id: Unique identifier of the batch job to download results from
    """
    def _worker():
        batch_method.get_batch_results(batch_id)
    threading.Thread(target=_worker, daemon=True).start()


def refresh_batches_async(parent: Union[tk.Tk, ctk.CTk]) -> None:
    """
    Refresh the batch job lists on a background thread.

    This function fetches the latest batch job status from OpenAI and
    updates both the ongoing and completed batch tables.

    Args:
        parent: Parent window containing the batch tables
    """
    def _worker():
        try:
            ongoing_batches, done_batches = list_batches()

            def _update_ui():
                cols = ("id", "status", "created_at", "model", "type", "dataset(s)")
                populate_treeview(parent.tree_ongoing, cols, ongoing_batches)
                populate_treeview(parent.tree_done, cols, done_batches)

            parent.after(0, _update_ui)
        except Exception as error:
            parent.after(0, partial(show_error, "Refresh Error", str(error)))
    threading.Thread(target=_worker, daemon=True).start()


def cancel_batch_async(parent: Union[tk.Tk, ctk.CTk], batch_id: str) -> None:
    """
    Cancel a batch processing job on a background thread.

    Args:
        parent: Parent window for error dialog ownership
        batch_id: Unique identifier of the batch job to cancel
    """
    def _worker():
        try:
            batch_method.cancel_batch(batch_id)
            parent.after(0, lambda: print("Cancel finished for batch:", batch_id))
        except Exception as error:
            parent.after(0, lambda: show_error("Cancel Error", str(error)))
    threading.Thread(target=_worker, daemon=True).start()