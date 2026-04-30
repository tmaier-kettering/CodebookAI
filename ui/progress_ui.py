# progress_ui.py
"""
All progress-window UI for long-running operations.
Compatible with both tkinter and customtkinter.

Use:
    from progress_ui import ProgressController
    progress = ProgressController.open(parent, total_count, title="Processing…")
    progress.update(i, message="Processed i of N")
    progress.close()
"""

from typing import Optional, Union
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk


class ProgressController:
    """
    Controller for a modal progress window with status label and progress bar.

    Key details:
      - If no parent is provided, creates a hidden root and manually drives the loop.
      - Uses `.update()` (not just `.update_idletasks()`) so the window paints and
        continues to repaint during long-running work.
      - Compatible with both tkinter and customtkinter parents.
    """

    def __init__(
        self,
        progress_root: Optional[Union[tk.Tk, ctk.CTk]],
        progress_win: Union[tk.Toplevel, ctk.CTkToplevel],
        status_var: tk.StringVar,
        bar: Union[ttk.Progressbar, ctk.CTkProgressBar],
        total_count: int,
    ):
        self._root = progress_root
        self._win = progress_win
        self._status = status_var
        self._bar = bar
        self._total = max(total_count, 1)
        self._using_ctk = isinstance(bar, ctk.CTkProgressBar)

    @classmethod
    def open(
        cls, 
        parent: Optional[Union[tk.Misc, ctk.CTkBaseClass]], 
        total_count: int, 
        title: str = "Working…"
    ) -> "ProgressController":
        """
        Open a progress window.
        
        Args:
            parent: Parent window (can be tk or ctk)
            total_count: Total number of items to process
            title: Window title
            
        Returns:
            ProgressController instance
        """
        progress_root = None
        master = parent
        
        # Detect if we should use CTk or regular tk
        use_ctk = False
        if master is None:
            # No parent, create a new root
            # Try CTk first, fall back to tk if there's an issue
            try:
                progress_root = ctk.CTk()
                progress_root.withdraw()
                master = progress_root
                use_ctk = True
            except Exception:
                progress_root = tk.Tk()
                progress_root.withdraw()
                master = progress_root
        elif isinstance(master, (ctk.CTk, ctk.CTkToplevel)):
            use_ctk = True

        # Create window
        if use_ctk:
            win = ctk.CTkToplevel(master)
        else:
            win = tk.Toplevel(master)
            
        win.title(title)
        win.resizable(False, False)
        # Grab prevents clicks outside, making it modal-ish
        win.grab_set()

        # Status label
        status_var = tk.StringVar()
        if use_ctk:
            status_label = ctk.CTkLabel(win, textvariable=status_var)
            status_label.pack(fill="x", padx=12, pady=8)
        else:
            status_label = tk.Label(win, textvariable=status_var, padx=12, pady=8)
            status_label.pack(fill="x")

        # Progress bar
        if use_ctk:
            bar = ctk.CTkProgressBar(win, width=360)
            bar.pack(padx=12, pady=(0, 12), fill="x")
            bar.set(0)  # CTkProgressBar uses set(0..1)
        else:
            bar = ttk.Progressbar(win, mode="determinate", length=360)
            bar.pack(padx=12, pady=(0, 12), fill="x")
            bar["maximum"] = max(total_count, 1)
            bar["value"] = 0

        status_var.set(f"Processed 0 of {total_count} items")
        # IMPORTANT: use update() so the window really paints before work starts
        win.update()

        return cls(progress_root, win, status_var, bar, total_count)

    def update(self, index_1_based: int, message: Optional[str] = None):
        """
        Advance progress to index_1_based (1..N) and optionally set status.
        
        Args:
            index_1_based: Current item number (1-indexed)
            message: Optional status message to display
        """
        value = max(0, min(index_1_based, self._total))
        
        if self._using_ctk:
            # CTkProgressBar uses values from 0.0 to 1.0
            self._bar.set(value / self._total if self._total > 0 else 0)
        else:
            # ttk.Progressbar uses absolute values
            self._bar["value"] = value
            
        if message is None:
            self._status.set(f"Processed {value} of {self._total} items")
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
