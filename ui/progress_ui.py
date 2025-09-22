# progress_ui.py
"""
All progress-window UI for long-running operations (Tk/ttk isolated).

Use:
    from progress_ui import ProgressController
    progress = ProgressController.open(parent, total_count, title="Processing…")
    progress.update(i, message="Processed i of N")
    progress.close()
"""

from typing import Optional
import tkinter as tk
from tkinter import ttk


class ProgressController:
    """
    Controller for a modal-ish Toplevel with a status label and determinate bar.

    Key details:
      - If no parent is provided, creates a hidden root and manually drives the loop.
      - Uses `.update()` (not just `.update_idletasks()`) so the window paints and
        continues to repaint during long-running work.
    """

    def __init__(
        self,
        progress_root: Optional[tk.Tk],
        progress_win: tk.Toplevel,
        status_var: tk.StringVar,
        bar: ttk.Progressbar,
        total_count: int,
    ):
        self._root = progress_root
        self._win = progress_win
        self._status = status_var
        self._bar = bar
        self._total = max(total_count, 1)

    @classmethod
    def open(cls, parent: Optional[tk.Misc], total_count: int, title: str = "Working…") -> "ProgressController":
        progress_root = None
        master = parent
        if master is None:
            progress_root = tk.Tk()
            progress_root.withdraw()
            master = progress_root

        win = tk.Toplevel(master)
        win.title(title)
        win.resizable(False, False)
        # If you're launching from another Tk window, grab prevents clicks outside,
        # but doesn't stop paint; we keep it since you asked for a modal-ish window.
        win.grab_set()

        status_var = tk.StringVar()
        tk.Label(win, textvariable=status_var, padx=12, pady=8).pack(fill="x")

        bar = ttk.Progressbar(win, mode="determinate", length=360)
        bar.pack(padx=12, pady=(0, 12), fill="x")

        maximum = max(total_count, 1)
        bar["maximum"] = maximum
        bar["value"] = 0

        status_var.set(f"Processed 0 of {total_count} quotes")
        # IMPORTANT: use update() so the window really paints before work starts
        win.update()

        return cls(progress_root, win, status_var, bar, total_count)

    def update(self, index_1_based: int, message: Optional[str] = None):
        """Advance progress to index_1_based (1..N) and optionally set status."""
        value = max(0, min(index_1_based, self._total))
        self._bar["value"] = value
        if message is None:
            self._status.set(f"Processed {value} of {self._total} quotes")
        else:
            self._status.set(message)
        # IMPORTANT: use update() to pump events and repaint every tick
        self._win.update()

    def close(self):
        """Tear down the progress UI safely."""
        try:
            # One last paint so the final state is visible if needed
            self._win.update()
        except Exception:
            pass
        try:
            if self._win is not None:
                self._win.destroy()
        finally:
            if self._root is not None:
                try:
                    self._root.destroy()
                except Exception:
                    pass
