"""
UI components for data preview functionality.

This module provides widgets and utilities for previewing tabular data,
including a scrollable radio header for column selection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List


class RadioHeader(ttk.Frame):
    """
    A horizontally scrollable frame containing radio buttons for column selection.
    
    This widget allows users to select exactly one column from a potentially
    wide table by providing radio buttons that can be scrolled horizontally.
    """
    
    def __init__(self, master: tk.Widget, variable: tk.IntVar):
        """
        Initialize the RadioHeader widget.
        
        Args:
            master: Parent widget
            variable: IntVar to track the selected column index
        """
        super().__init__(master)
        self.var = variable
        self.canvas = tk.Canvas(self, height=28, highlightthickness=0)
        self.inner = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")

        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self._on_scroll)
        self.canvas.configure(xscrollcommand=self.hsb.set)

        self.canvas.grid(row=0, column=0, sticky="ew")
        self.hsb.grid(row=1, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)

        self._radios: list[ttk.Radiobutton] = []

        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_inner_configure(self, _event=None):
        """Handle inner frame configuration changes."""
        bbox = self.canvas.bbox(self.window_id)
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_canvas_configure(self, event):
        """Handle canvas configuration changes."""
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_scroll(self, *args):
        """Handle horizontal scrolling."""
        self.canvas.xview(*args)

    def xview(self, *args):
        """Provide horizontal view control for external scrollbars."""
        self.canvas.xview(*args)

    def xscrollcommand(self, *args):
        """Handle external scrollbar commands."""
        self.hsb.set(*args)

    def rebuild(self, column_labels: list[str]):
        """
        Rebuild the radio buttons with new column labels.
        
        Args:
            column_labels: List of column header labels
        """
        for w in self.inner.winfo_children():
            w.destroy()
        self._radios.clear()
        for idx, label in enumerate(column_labels):
            b = ttk.Radiobutton(
                self.inner,
                text=label,
                value=idx,
                variable=self.var,
                takefocus=False
            )
            b.grid(row=0, column=idx, padx=(6 if idx == 0 else 12, 12), pady=4, sticky="w")
            self._radios.append(b)
        self.inner.update_idletasks()
        self.canvas.xview_moveto(0.0)


class PreviewManager:
    """
    Manages the data preview functionality for the import dialog.
    
    This class handles loading, displaying, and updating the tabular data preview,
    including column headers and data synchronization with the radio header.
    """
    
    def __init__(self, tree: ttk.Treeview, radio_header: RadioHeader):
        """
        Initialize the preview manager.
        
        Args:
            tree: Treeview widget for displaying data
            radio_header: RadioHeader widget for column selection
        """
        self.tree = tree
        self.radio_header = radio_header
        self.loaded_rows: list[list[str]] = []
        self.filename_stem: str = ""
    
    def set_preview_columns(self, cols: list[str]):
        """
        Set the column headers for the preview.
        
        Args:
            cols: List of column header labels
        """
        self.tree["columns"] = [f"c{i}" for i in range(len(cols))]
        for i, label in enumerate(cols):
            cid = f"c{i}"
            self.tree.heading(cid, text=label)
            self.tree.column(cid, width=120, stretch=False, anchor="w")
        self.radio_header.rebuild(cols)

    def fill_preview_rows(self, rows: list[list[str]]):
        """
        Fill the preview with data rows.
        
        Args:
            rows: List of data rows to display
        """
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            ncols = len(self.tree["columns"])
            padded = (r + [""] * ncols)[:ncols]
            self.tree.insert("", "end", values=padded)

    def initial_blank_preview(self, update_callback=None):
        """
        Initialize with a blank 5x5 preview.
        
        Args:
            update_callback: Optional callback to trigger after setup
        """
        self.set_preview_columns([f"Column {i+1}" for i in range(5)])
        self.fill_preview_rows([[""] * 5 for _ in range(5)])
        if update_callback:
            update_callback()

    def current_header_labels(self) -> list[str]:
        """
        Get the current column header labels.
        
        Returns:
            List of header labels currently displayed
        """
        return [self.tree.heading(cid)["text"] for cid in self.tree["columns"]]

    def selected_header_label(self, selected_col_var: tk.IntVar) -> str:
        """
        Get the label of the currently selected column.
        
        Args:
            selected_col_var: IntVar tracking selected column index
            
        Returns:
            Label of the selected column, or empty string if invalid
        """
        labels = self.current_header_labels()
        idx = selected_col_var.get()
        if 0 <= idx < len(labels):
            return str(labels[idx])
        return ""