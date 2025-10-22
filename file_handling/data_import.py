"""
Universal tabular import with a small 'Import Wizard' UI + dataset name selector.

Changes in this version:
- Keeps CSV/TSV/TXT/Excel support and the scrollable preview with column radio-select.
- Adds a "Dataset Name" section under the table with three radio options:
    1) File name (stem)
    2) Selected column header (enabled only if "File has headers" is checked)
    3) Other (free text entry)
- On Import, returns (values_from_selected_column, selected_dataset_name).

Public API:
    import_csv(parent: Optional[tk.Misc]=None, title="Import Data") -> Optional[tuple[list[str], str]]
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple, List

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Import drag-and-drop support
try:
    from ui.drag_drop import enable_file_drop
    from tkinterdnd2 import TkinterDnD
    _HAS_DND = True
except ImportError:
    enable_file_drop = None
    _HAS_DND = False

# Optional pandas for robust Excel/CSV reading; gracefully degrade if unavailable
try:
    import pandas as _pd  # type: ignore
except Exception:
    _pd = None  # Falls back to csv module for text; Excel requires pandas


# -----------------------------
# Internal Tk convenience utils
# -----------------------------
def _ensure_parent(parent: Optional[tk.Misc]) -> tuple[tk.Misc, Optional[tk.Tk]]:
    if parent is not None:
        return parent, None
    
    # Create root with DnD support if available
    if _HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass
    root.update_idletasks()
    return root, root


def _safe_destroy(maybe_root: Optional[tk.Tk]) -> None:
    if maybe_root is not None:
        try:
            maybe_root.destroy()
        except Exception:
            pass


# -----------------------------
# Tabular loading helpers
# -----------------------------
def _is_excel(path: str) -> bool:
    return Path(path).suffix.lower() in {".xlsx", ".xls"}


def _is_text_table(path: str) -> bool:
    return Path(path).suffix.lower() in {".csv", ".tsv", ".txt"}


def _read_excel(path: str, max_rows: int | None = None) -> list[list[str]]:
    if _pd is None:
        raise RuntimeError("Reading Excel requires pandas. Please install pandas.")
    try:
        df = _pd.read_excel(path, nrows=max_rows)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel: {e}")
    return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except Exception:
        return "\t" if sample.count("\t") > sample.count(",") else ","


def _read_text_table(path: str, max_rows: int | None = None) -> list[list[str]]:
    def _read_with(file, enc=None):
        if enc:
            fh = open(file, "r", encoding=enc, newline="")
        else:
            fh = open(file, "r", newline="")
        with fh as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = _sniff_delimiter(sample)
            reader = csv.reader(f, delimiter=delimiter)
            rows: list[list[str]] = []
            for i, row in enumerate(reader):
                rows.append([str(c) for c in row])
                if max_rows is not None and i + 1 >= max_rows:
                    break
            return rows

    try:
        return _read_with(path, enc="utf-8")
    except UnicodeDecodeError:
        return _read_with(path, enc=None)
    except Exception as e:
        raise RuntimeError(f"Failed to read delimited text: {e}")


def _load_tabular(path: str, max_rows: int | None = None) -> list[list[str]]:
    if _is_excel(path):
        return _read_excel(path, max_rows=max_rows)
    if _is_text_table(path):
        return _read_text_table(path, max_rows=max_rows)
    if _pd is not None:
        try:
            df = _pd.read_csv(path, nrows=max_rows)
            return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]
        except Exception:
            pass
    raise RuntimeError("Unsupported file type. Please select CSV/TSV/TXT or Excel (.xlsx/.xls).")


# -----------------------------
# UI: Scrollable radio header
# -----------------------------
class _RadioHeader(ttk.Frame):
    def __init__(self, master: tk.Widget, variable: tk.IntVar):
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
        bbox = self.canvas.bbox(self.window_id)
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.window_id, width=max(event.width, self.inner.winfo_reqwidth()))

    def _on_scroll(self, *args):
        self.canvas.xview(*args)

    def xview(self, *args):
        self.canvas.xview(*args)

    def xscrollcommand(self, *args):
        self.hsb.set(*args)

    def rebuild(self, column_labels: list[str]):
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
        self.canvas.configure(scrollregion=self.canvas.bbox(self.window_id))
        self.canvas.itemconfig(self.window_id, width=max(self.canvas.winfo_width(), self.inner.winfo_reqwidth()))
        self.canvas.xview_moveto(0.0)


# -----------------------------
# Public API: Import Wizard
# -----------------------------
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
    pick exactly one column via radio buttons, choose a dataset name, and return that
    column's values and the chosen dataset name.

    Returns:
        (values_from_selected_column, selected_dataset_name) or None if cancelled.
    """

    # ---------------- Setup window ----------------
    owner, created_root = _ensure_parent(parent)

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
    
    # Enable drag-and-drop on the file entry
    if enable_file_drop is not None:
        def _handle_drop(path):
            file_var.set(path)
            _refresh_preview()
        
        # Extract allowed extensions from filetypes
        allowed_extensions = []
        for name, pattern in filetypes:
            if pattern != "*.*":
                # Parse patterns like "*.csv *.txt" or "*.xlsx *.xls"
                exts = pattern.replace("*", "").split()
                allowed_extensions.extend(exts)
        
        enable_file_drop(file_entry, _handle_drop, 
                        allowed_extensions if allowed_extensions else None)

    def browse_file():
        path = filedialog.askopenfilename(parent=dlg, title=title, filetypes=list(filetypes))
        if path:
            file_var.set(path)
            _refresh_preview()

    ttk.Button(dlg, text="Browse…", command=browse_file).grid(row=1, column=2, padx=(4, 10), pady=4, sticky="w")

    # Header checkbox
    has_headers = tk.BooleanVar(master=dlg, value=True)
    header_chk = ttk.Checkbutton(
        dlg, text="File has headers (skip first row)", variable=has_headers, command=lambda: _refresh_preview()
    )
    header_chk.grid(row=2, column=1, padx=4, pady=2, sticky="w")

    # Helper text
    helper = ttk.Label(dlg, text="Select exactly one column to import using the round buttons below.")
    helper.grid(row=3, column=1, padx=4, pady=(0, 8), sticky="w")

    # Column select header (radio buttons) – horizontally scrollable
    selected_col = tk.IntVar(master=dlg, value=0)
    radio_header = _RadioHeader(dlg, variable=selected_col)
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

    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
    hscroll.configure(command=tree.xview)

    # ---------------- Dataset Name controls ----------------
    # Options: 0 = filename, 1 = selected column header, 2 = other (entry)
    dataset_name_mode = tk.IntVar(master=dlg, value=0)
    dataset_name_other = tk.StringVar(master=dlg, value="")
    dataset_name_preview = tk.StringVar(master=dlg, value="")

    nick_frame = ttk.LabelFrame(dlg, text="Dataset Name")
    nick_frame.grid(row=8, column=0, columnspan=3, sticky="we", padx=10, pady=(0, 10))
    for col in range(3):
        nick_frame.columnconfigure(col, weight=1)

    r_file = ttk.Radiobutton(nick_frame, text="Use file name", value=0, variable=dataset_name_mode)
    r_colh = ttk.Radiobutton(nick_frame, text="Use selected column header", value=1, variable=dataset_name_mode)
    r_other = ttk.Radiobutton(nick_frame, text="Other:", value=2, variable=dataset_name_mode)
    r_file.grid(row=0, column=0, sticky="w", padx=8, pady=6)
    r_colh.grid(row=0, column=1, sticky="w", padx=8, pady=6)
    r_other.grid(row=0, column=2, sticky="w", padx=8, pady=6)

    other_entry = ttk.Entry(nick_frame, textvariable=dataset_name_other, width=30, state="disabled")
    other_entry.grid(row=1, column=2, sticky="w", padx=30, pady=(0, 8))

    ttk.Label(nick_frame, textvariable=dataset_name_preview, foreground="#555").grid(
        row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8)
    )

    # Buttons
    btns = ttk.Frame(dlg)
    btns.grid(row=9, column=0, columnspan=3, sticky="e", padx=10, pady=(0, 10))
    ttk.Button(btns, text="Cancel", command=dlg.destroy).grid(row=0, column=0, padx=5)
    process_btn = ttk.Button(btns, text="Import")
    process_btn.grid(row=0, column=1, padx=5)

    # -------------- Preview management --------------
    _loaded_rows: list[list[str]] = []
    _filename_stem: str = ""

    def _set_preview_columns(cols: list[str]):
        tree["columns"] = [f"c{i}" for i in range(len(cols))]
        for i, label in enumerate(cols):
            cid = f"c{i}"
            tree.heading(cid, text=label)
            tree.column(cid, width=120, stretch=False, anchor="w")
        radio_header.rebuild(cols)

    def _fill_preview_rows(rows: list[list[str]]):
        tree.delete(*tree.get_children())
        for r in rows:
            ncols = len(tree["columns"])
            padded = (r + [""] * ncols)[:ncols]
            tree.insert("", "end", values=padded)

    def _initial_blank_preview():
        _set_preview_columns([f"Column {i+1}" for i in range(5)])
        _fill_preview_rows([[""] * 5 for _ in range(5)])
        _update_dataset_name_preview()

    def _current_header_labels() -> list[str]:
        # Return the labels currently shown atop the preview
        return [tree.heading(cid)["text"] for cid in tree["columns"]]

    def _selected_header_label() -> str:
        labels = _current_header_labels()
        idx = selected_col.get()
        if 0 <= idx < len(labels):
            return str(labels[idx])
        return ""

    def _update_dataset_name_controls_enabled():
        # Enable/disable "selected column header" radio based on has_headers + data present
        has_data = bool(_loaded_rows)
        enable_col_header = has_headers.get() and has_data and len(tree["columns"]) > 0
        state = "normal" if enable_col_header else "disabled"
        r_colh.configure(state=state)
        if state == "disabled" and dataset_name_mode.get() == 1:
            dataset_name_mode.set(0)  # fall back to filename
        # Enable/disable custom entry
        other_state = "normal" if dataset_name_mode.get() == 2 else "disabled"
        other_entry.configure(state=other_state)

    def _update_dataset_name_preview(*_args):
        choice = dataset_name_mode.get()
        if choice == 0:
            dataset_name_preview.set(f"Dataset Name → {(_filename_stem or '—')}")
        elif choice == 1:
            dataset_name_preview.set(f"Dataset Name → {(_selected_header_label() or '—')}")
        else:
            dataset_name_preview.set(f"Dataset Name → {(dataset_name_other.get().strip() or '—')}")
        _update_dataset_name_controls_enabled()

    def _selected_header_label() -> str:
        return _selected_header_label_cached()

    def _refresh_preview():
        path = file_var.get().strip()
        if not path:
            _initial_blank_preview()
            return

        try:
            rows = _load_tabular(path, max_rows=200)
        except Exception as e:
            messagebox.showerror("Load error", str(e), parent=dlg)
            _initial_blank_preview()
            return

        nonlocal _filename_stem, _loaded_rows, _selected_header_label_cached
        _filename_stem = Path(path).stem
        _loaded_rows = rows

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

        _set_preview_columns(header)
        _fill_preview_rows(data)

        # cache selected header label resolver (to avoid capturing stale UI state)
        def _sel_hdr():
            labels = header
            idx = selected_col.get()
            if 0 <= idx < len(labels):
                return str(labels[idx])
            return ""
        _selected_header_label_cached = _sel_hdr

        # Reset dataset_name preview (filename by default)
        _update_dataset_name_preview()

        # Clamp selected column
        if selected_col.get() >= len(header):
            selected_col.set(0)

    # placeholder for a dynamic resolver
    _selected_header_label_cached = lambda: ""

    # Reactivity hooks
    selected_col.trace_add("write", _update_dataset_name_preview)
    has_headers.trace_add("write", lambda *_: (_refresh_preview(),))
    dataset_name_mode.trace_add("write", _update_dataset_name_preview)
    dataset_name_other.trace_add("write", _update_dataset_name_preview)

    _initial_blank_preview()  # start 5x5

    # -------------- Import handler --------------
    result_values: Optional[list[str]] = None
    result_dataset_name: Optional[str] = None

    def _do_import():
        nonlocal result_values, result_dataset_name
        path = file_var.get().strip()
        if not path:
            messagebox.showerror("Error", "No file selected.", parent=dlg)
            return
        # Always load the full file without row limit for import
        # (preview may have loaded only 200 rows)
        try:
            rows = _load_tabular(path)
        except Exception as e:
            messagebox.showerror("Load error", str(e), parent=dlg)
            return

        body = rows[1:] if (has_headers.get() and rows) else rows
        if not body:
            messagebox.showerror("Error", "The file appears to have no data rows.", parent=dlg)
            return

        col_idx = selected_col.get()
        out: list[str] = []
        for r in body:
            val = r[col_idx] if col_idx < len(r) else ""
            out.append("" if val is None else str(val))

        # Resolve dataset_name
        mode = dataset_name_mode.get()
        if mode == 0:
            dataset_name = _filename_stem or "data"
        elif mode == 1:
            if not has_headers.get():
                messagebox.showerror("Dataset Name error", "Column header option requires headers to be enabled.", parent=dlg)
                return
            dataset_name = _selected_header_label()
            if not dataset_name.strip():
                messagebox.showerror("Dataset Name error", "Selected column has an empty header.", parent=dlg)
                return
        else:
            dataset_name = dataset_name_other.get().strip()
            if not dataset_name:
                messagebox.showerror("Dataset Name error", "Please type a dataset_name in the 'Other' field.", parent=dlg)
                return

        result_values = out
        result_dataset_name = dataset_name
        dlg.destroy()

    process_btn.configure(command=_do_import)

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
    _safe_destroy(created_root)

    if result_values is None or result_dataset_name is None:
        return None
    return result_values, result_dataset_name
