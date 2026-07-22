"""
UI utility functions for window management and widget operations.

This module provides common UI utility functions used across the application
for window positioning, widget configuration, and data display.
"""

import tkinter as tk
from tkinter import ttk

from settings.user_config import get_setting, set_setting


def save_window_geometry(win: tk.Misc, setting_key: str) -> None:
    """Persist a window's current geometry string under setting_key."""
    win.update_idletasks()
    set_setting(setting_key, win.geometry())


def restore_window_geometry(win: tk.Misc, setting_key: str) -> bool:
    """Restore a previously saved geometry. Returns True if one was applied."""
    geo = get_setting(setting_key, "")
    if not geo:
        return False
    try:
        win.geometry(geo)
        return True
    except tk.TclError:
        return False


def center_window(win: tk.Tk, width: int, height: int) -> None:
    """
    Center a Tkinter window on the screen.

    Args:
        win: The Tkinter window to center
        width: Desired window width in pixels
        height: Desired window height in pixels
    """
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw // 2) - (width // 2)
    y = (sh // 2) - (height // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def populate_treeview(tree: ttk.Treeview, columns: tuple[str, ...], rows: list[tuple]) -> None:
    """
    Configure and populate a Treeview widget with tabular data.

    Used by the Task Builder's data preview table (ui/task_builder.py). The
    batches table has its own rendering now (see ui/batches_view.py).

    Args:
        tree: The Treeview widget to populate
        columns: Tuple of column header names
        rows: List of tuples representing table rows
    """
    tree["columns"] = columns
    tree["show"] = "headings"
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="w", stretch=True, width=60, minwidth=20)

    # Clear existing rows
    for iid in tree.get_children():
        tree.delete(iid)

    # Insert new rows
    for row in rows:
        tree.insert("", "end", values=row)