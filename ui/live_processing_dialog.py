"""
Live processing dialog for CodebookAI application.

This module provides a modal dialog that allows users to configure live processing
options including:
- Labels CSV file selection
- Quotes CSV file selection  
- Single vs Multi-label processing mode selection

This dialog consolidates the previous separate menu options into a single
unified interface with file browser dialogs and processing mode selection.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional, Tuple


class LiveProcessingDialog(tk.Toplevel):
    """
    Modal dialog for configuring live text classification processing.
    
    This dialog provides a user interface for selecting CSV files and processing
    mode before starting live classification with the OpenAI API.
    """
    
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)
        self.title("Live Processing Configuration")
        self.transient(parent)   # keep on top of parent
        self.grab_set()          # make modal
        self.resizable(False, False)
        
        # Result storage - None means cancelled, tuple means OK clicked
        self.result: Optional[Tuple[str, str, bool]] = None
        
        # --- State variables ---
        self.var_labels_file = tk.StringVar()
        self.var_quotes_file = tk.StringVar()
        self.var_multi_label = tk.BooleanVar(value=False)  # False = single label, True = multi label
        
        # --- Layout ---
        self._create_widgets()
        self._center_over_parent(parent)
        
        # Focus on first field
        self.labels_entry.focus_set()
        
    def _create_widgets(self):
        """Create and layout all dialog widgets."""
        pad = {"padx": 12, "pady": 8}
        frm = ttk.Frame(self, padding=16)
        frm.grid(row=0, column=0, sticky="nsew")
        
        # Labels CSV selection
        ttk.Label(frm, text="Labels CSV:").grid(row=0, column=0, sticky="w", **pad)
        self.labels_entry = ttk.Entry(frm, textvariable=self.var_labels_file, width=50, state="readonly")
        self.labels_entry.grid(row=0, column=1, sticky="w", **pad)
        
        labels_browse_btn = ttk.Button(frm, text="Browse...", command=self._browse_labels_file)
        labels_browse_btn.grid(row=0, column=2, sticky="w", padx=(4, 0))
        
        # Tooltip for labels field
        self._create_tooltip(self.labels_entry, 
                           "Select a CSV file containing classification labels (one per row)")
        self._create_tooltip(labels_browse_btn,
                           "Browse for a CSV file containing your classification labels")
        
        # Quotes CSV selection  
        ttk.Label(frm, text="Quotes CSV:").grid(row=1, column=0, sticky="w", **pad)
        self.quotes_entry = ttk.Entry(frm, textvariable=self.var_quotes_file, width=50, state="readonly")
        self.quotes_entry.grid(row=1, column=1, sticky="w", **pad)
        
        quotes_browse_btn = ttk.Button(frm, text="Browse...", command=self._browse_quotes_file)
        quotes_browse_btn.grid(row=1, column=2, sticky="w", padx=(4, 0))
        
        # Tooltip for quotes field
        self._create_tooltip(self.quotes_entry,
                           "Select a CSV file containing text quotes to be classified")
        self._create_tooltip(quotes_browse_btn,
                           "Browse for a CSV file containing the text you want to classify")
        
        # Processing mode selection
        ttk.Label(frm, text="Processing Mode:").grid(row=2, column=0, sticky="w", **pad)
        
        mode_frame = ttk.Frame(frm)
        mode_frame.grid(row=2, column=1, sticky="w", **pad)
        
        self.mode_checkbox = ttk.Checkbutton(
            mode_frame,
            text="Multi-label processing",
            variable=self.var_multi_label
        )
        self.mode_checkbox.grid(row=0, column=0, sticky="w")
        
        # Tooltip for processing mode
        self._create_tooltip(self.mode_checkbox,
                           "Checked: Each quote can have multiple labels\n" +
                           "Unchecked: Each quote gets exactly one label (single-label mode)")
        
        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=3, column=0, columnspan=3, sticky="e", pady=(16, 0))
        
        ttk.Button(btn_frame, text="Cancel", command=self._on_cancel).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(btn_frame, text="OK", style="Accent.TButton", command=self._on_ok).grid(row=0, column=1)
        
        # Keyboard shortcuts
        self.bind("<Return>", lambda e: self._on_ok())
        self.bind("<Escape>", lambda e: self._on_cancel())
        
    def _browse_labels_file(self):
        """Open file dialog to select labels CSV file."""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Select Labels CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.var_labels_file.set(filename)
            
    def _browse_quotes_file(self):
        """Open file dialog to select quotes CSV file."""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Select Quotes CSV File", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.var_quotes_file.set(filename)
            
    def _on_ok(self):
        """Handle OK button click - validate inputs and store result."""
        labels_file = self.var_labels_file.get().strip()
        quotes_file = self.var_quotes_file.get().strip()
        
        # Validation
        if not labels_file:
            messagebox.showerror("Validation Error", "Please select a labels CSV file.", parent=self)
            return
            
        if not quotes_file:
            messagebox.showerror("Validation Error", "Please select a quotes CSV file.", parent=self)
            return
            
        # Store result and close
        self.result = (labels_file, quotes_file, self.var_multi_label.get())
        self.destroy()
        
    def _on_cancel(self):
        """Handle Cancel button click - close without saving."""
        self.result = None
        self.destroy()
        
    def _center_over_parent(self, parent):
        """Center this dialog over the parent window."""
        self.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")
        
    def _create_tooltip(self, widget, text):
        """Create a simple tooltip for a widget."""
        def on_enter(event):
            # Create tooltip window
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            
            label = tk.Label(
                tooltip,
                text=text,
                background="lightyellow",
                relief="solid",
                borderwidth=1,
                font=("Arial", 9),
                wraplength=300
            )
            label.pack()
            
            # Store tooltip reference
            widget._tooltip = tooltip
            
        def on_leave(event):
            # Destroy tooltip
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                delattr(widget, '_tooltip')
                
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
        
    def get_result(self) -> Optional[Tuple[str, str, bool]]:
        """
        Get the dialog result after it closes.
        
        Returns:
            None if cancelled, or (labels_file, quotes_file, is_multi_label) if OK clicked
        """
        return self.result


def show_live_processing_dialog(parent: tk.Tk | tk.Toplevel) -> Optional[Tuple[str, str, bool]]:
    """
    Show the live processing configuration dialog.
    
    Args:
        parent: Parent window for the dialog
        
    Returns:
        None if cancelled, or (labels_file, quotes_file, is_multi_label) if configured
    """
    dialog = LiveProcessingDialog(parent)
    parent.wait_window(dialog)  # Wait for dialog to close
    return dialog.get_result()