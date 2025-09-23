"""
Import dialog for tabular data with preview and column selection.

This module provides the main import_data function that opens a dialog
for users to select and preview tabular data files, choose columns,
and assign nicknames to the imported data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import from our refactored modules
try:
    from .tabular_loaders import load_tabular
    from .tk_utils import ensure_parent, safe_destroy
    from .preview_components import RadioHeader, PreviewManager
except ImportError:
    # Fallback for running from file_handling directory
    from tabular_loaders import load_tabular
    from tk_utils import ensure_parent, safe_destroy
    from preview_components import RadioHeader, PreviewManager


def import_data(
    parent: Optional[tk.Misc] = None,
    title: str = "Import Data",
    filetypes: Sequence[tuple[str, str]] = (
        ("All files", "*.*"),
        ("Excel files", "*.xlsx *.xls"),
        ("CSV files", "*.csv"),
        ("TSV files", "*.tsv"),
        ("Text files", "*.txt"),
    ),
) -> Optional[tuple[list[str], str]]:
    """
    Open an "Import Wizard" dialog: select a file, preview it, choose 'has headers',
    pick exactly one column via radio buttons, choose a nickname, and return that
    column's values and the chosen nickname.

    Args:
        parent: Parent widget for the dialog (None to create a root)
        title: Window title for the dialog
        filetypes: File type filters for the file dialog

    Returns:
        (values_from_selected_column, selected_nickname) or None if cancelled.
    """

    # ---------------- Setup window ----------------
    owner, created_root = ensure_parent(parent)

    dlg = tk.Toplevel(owner)
    dlg.title(title)
    dlg.transient(owner)
    dlg.grab_set()
    dlg.resizable(True, True)

    # Grid weights
    for c in range(3):
        dlg.columnconfigure(c, weight=1 if c == 1 else 0)
    for r in range(10):
        dlg.rowconfigure(r, weight=0)
    dlg.rowconfigure(6, weight=1)  # Preview grows

    # Instruction line
    instr = ttk.Label(dlg, text="Use this window as an import wizard.")
    instr.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 6), sticky="w")

    # File selection row
    ttk.Label(dlg, text="File:").grid(row=1, column=0, padx=(10, 4), pady=4, sticky="e")
    file_var = tk.StringVar()
    file_entry = ttk.Entry(dlg, textvariable=file_var, width=56)
    file_entry.grid(row=1, column=1, padx=4, pady=4, sticky="we")

    def browse_file():
        path = filedialog.askopenfilename(parent=dlg, title=title, filetypes=list(filetypes))
        if path:
            file_var.set(path)
            refresh_preview()

    ttk.Button(dlg, text="Browse…", command=browse_file).grid(row=1, column=2, padx=(4, 10), pady=4, sticky="w")

    # Header checkbox
    has_headers = tk.BooleanVar(master=dlg, value=False)
    header_chk = ttk.Checkbutton(
        dlg, text="File has headers (skip first row)", variable=has_headers, command=lambda: refresh_preview()
    )
    header_chk.grid(row=2, column=1, padx=4, pady=2, sticky="w")

    # Helper text
    helper = ttk.Label(dlg, text="Select exactly one column to import using the round buttons below.")
    helper.grid(row=3, column=1, padx=4, pady=(0, 8), sticky="w")

    # Column select header (radio buttons) – horizontally scrollable
    selected_col = tk.IntVar(master=dlg, value=0)
    radio_header = RadioHeader(dlg, variable=selected_col)
    radio_header.grid(row=4, column=0, columnspan=3, sticky="we", padx=10, pady=(0, 4))

    # Preview Treeview with scrollbars
    preview_frame = ttk.Frame(dlg)
    preview_frame.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=10, pady=(0, 10))
    preview_frame.rowconfigure(0, weight=1)
    preview_frame.columnconfigure(0, weight=1)

    tree = ttk.Treeview(preview_frame, show="headings", height=5)
    tree.grid(row=0, column=0, sticky="nsew")

    vscroll = ttk.Scrollbar(preview_frame, orient="vertical", command=tree.yview)
    vscroll.grid(row=0, column=1, sticky="ns")
    hscroll = ttk.Scrollbar(preview_frame, orient="horizontal")
    hscroll.grid(row=1, column=0, sticky="ew")

    def tree_xscroll(*args):
        tree.xview(*args)
        radio_header.xview(*args)

    def xscroll_set(first, last):
        hscroll.set(first, last)
        radio_header.xscrollcommand(first, last)

    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=xscroll_set)
    hscroll.configure(command=tree_xscroll)

    # Initialize preview manager
    preview_manager = PreviewManager(tree, radio_header)

    # ---------------- Nickname controls ----------------
    # Options: 0 = filename, 1 = selected column header, 2 = other (entry)
    nickname_mode = tk.IntVar(master=dlg, value=0)
    nickname_other = tk.StringVar(master=dlg, value="")
    nickname_preview = tk.StringVar(master=dlg, value="")

    nick_frame = ttk.LabelFrame(dlg, text="Nickname")
    nick_frame.grid(row=8, column=0, columnspan=3, sticky="we", padx=10, pady=(0, 10))
    for col in range(3):
        nick_frame.columnconfigure(col, weight=1)

    r_file = ttk.Radiobutton(nick_frame, text="Use file name", value=0, variable=nickname_mode)
    r_colh = ttk.Radiobutton(nick_frame, text="Use selected column header", value=1, variable=nickname_mode)
    r_other = ttk.Radiobutton(nick_frame, text="Other:", value=2, variable=nickname_mode)
    r_file.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    r_colh.grid(row=0, column=1, sticky="w", padx=8, pady=6)
    r_other.grid(row=0, column=2, sticky="w", padx=8, pady=6)

    other_entry = ttk.Entry(nick_frame, textvariable=nickname_other, width=30, state="disabled")
    other_entry.grid(row=1, column=2, sticky="w", padx=30, pady=(0, 8))

    ttk.Label(nick_frame, textvariable=nickname_preview, foreground="#555").grid(
        row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8)
    )

    # Buttons
    btns = ttk.Frame(dlg)
    btns.grid(row=9, column=0, columnspan=3, sticky="e", padx=10, pady=(0, 10))
    ttk.Button(btns, text="Cancel", command=dlg.destroy).grid(row=0, column=0, padx=5)
    process_btn = ttk.Button(btns, text="Import")
    process_btn.grid(row=0, column=1, padx=5)

    # -------------- Preview and nickname management --------------
    selected_header_label_cached = lambda: ""

    def update_nickname_controls_enabled():
        """Enable/disable nickname controls based on current state."""
        # Enable/disable "selected column header" radio based on has_headers + data present
        has_data = bool(preview_manager.loaded_rows)
        enable_col_header = has_headers.get() and has_data and len(tree["columns"]) > 0
        state = "normal" if enable_col_header else "disabled"
        r_colh.configure(state=state)
        if state == "disabled" and nickname_mode.get() == 1:
            nickname_mode.set(0)  # fall back to filename
        # Enable/disable custom entry
        other_state = "normal" if nickname_mode.get() == 2 else "disabled"
        other_entry.configure(state=other_state)

    def update_nickname_preview(*_args):
        """Update the nickname preview text."""
        choice = nickname_mode.get()
        if choice == 0:
            nickname_preview.set(f"Nickname → {(preview_manager.filename_stem or '—')}")
        elif choice == 1:
            nickname_preview.set(f"Nickname → {(selected_header_label_cached() or '—')}")
        else:
            nickname_preview.set(f"Nickname → {(nickname_other.get().strip() or '—')}")
        update_nickname_controls_enabled()

    def refresh_preview():
        """Refresh the data preview from the selected file."""
        nonlocal selected_header_label_cached
        
        path = file_var.get().strip()
        if not path:
            preview_manager.initial_blank_preview(update_nickname_preview)
            return

        try:
            rows = load_tabular(path, max_rows=200)
        except Exception as e:
            messagebox.showerror("Load error", str(e), parent=dlg)
            preview_manager.initial_blank_preview(update_nickname_preview)
            return

        preview_manager.filename_stem = Path(path).stem
        preview_manager.loaded_rows = rows

        if rows:
            if has_headers.get():
                header = rows[0]
                data = rows[1:]
            else:
                max_cols = max((len(r) for r in rows), default=1)
                header = [f"Column {i+1}" for i in range(max_cols)]
                data = rows
        else:
            header, data = [f"Column {i+1}" for i in range(5)], []

        header = [str(h) if (h is not None and str(h).strip() != "") else f"Column {i+1}"
                  for i, h in enumerate(header)]

        preview_manager.set_preview_columns(header)
        preview_manager.fill_preview_rows(data)

        # cache selected header label resolver (to avoid capturing stale UI state)
        def sel_hdr():
            labels = header
            idx = selected_col.get()
            if 0 <= idx < len(labels):
                return str(labels[idx])
            return ""
        selected_header_label_cached = sel_hdr

        # Reset nickname preview (filename by default)
        update_nickname_preview()

        # Clamp selected column
        if selected_col.get() >= len(header):
            selected_col.set(0)

    # Reactivity hooks
    selected_col.trace_add("write", update_nickname_preview)
    has_headers.trace_add("write", lambda *_: (refresh_preview(),))
    nickname_mode.trace_add("write", update_nickname_preview)
    nickname_other.trace_add("write", update_nickname_preview)

    preview_manager.initial_blank_preview(update_nickname_preview)  # start 5x5

    # -------------- Import handler --------------
    result_values: Optional[list[str]] = None
    result_nickname: Optional[str] = None

    def do_import():
        """Handle the import process."""
        nonlocal result_values, result_nickname
        path = file_var.get().strip()
        if not path:
            messagebox.showerror("Error", "No file selected.", parent=dlg)
            return
        if not preview_manager.loaded_rows:
            try:
                rows = load_tabular(path)
            except Exception as e:
                messagebox.showerror("Load error", str(e), parent=dlg)
                return
        else:
            rows = preview_manager.loaded_rows

        body = rows[1:] if (has_headers.get() and rows) else rows
        if not body:
            messagebox.showerror("Error", "The file appears to have no data rows.", parent=dlg)
            return

        col_idx = selected_col.get()
        out: list[str] = []
        for r in body:
            val = r[col_idx] if col_idx < len(r) else ""
            out.append("" if val is None else str(val))

        # Resolve nickname
        mode = nickname_mode.get()
        if mode == 0:
            nickname = preview_manager.filename_stem or "data"
        elif mode == 1:
            if not has_headers.get():
                messagebox.showerror("Nickname error", "Column header option requires headers to be enabled.", parent=dlg)
                return
            nickname = selected_header_label_cached()
            if not nickname.strip():
                messagebox.showerror("Nickname error", "Selected column has an empty header.", parent=dlg)
                return
        else:
            nickname = nickname_other.get().strip()
            if not nickname:
                messagebox.showerror("Nickname error", "Please type a nickname in the 'Other' field.", parent=dlg)
                return

        result_values = out
        result_nickname = nickname
        dlg.destroy()

    process_btn.configure(command=do_import)

    # Focus & geometry
    file_entry.focus_set()
    dlg.update_idletasks()
    try:
        x = owner.winfo_rootx() + 60
        y = owner.winfo_rooty() + 60
    except Exception:
        x = y = 100
    dlg.geometry(f"760x560+{x}+{y}")

    # Block until closed
    owner.wait_window(dlg)
    safe_destroy(created_root)

    if result_values is None or result_nickname is None:
        return None
    return result_values, result_nickname