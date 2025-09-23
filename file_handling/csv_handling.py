"""
Universal tabular import with a small 'Import Wizard' UI.

Upgrades over prior version:
- import_csv() now supports CSV, TSV, TXT (delimited), and Excel (.xlsx/.xls)
- Adds an in-window "Import Wizard" with:
    * Instructional sentence at the top
    * Checkbox "Has headers" that live-updates the preview
    * Scrollable preview table (Treeview) that starts 5x5
      - Columns expand to match the file after selection
      - Vertical & horizontal scrolling
    * A header row of circular radio buttons (one and only one column can be selected)
      - Radio buttons horizontally scroll in sync with the table columns
- Returns values from the SINGLE selected column, respecting the header toggle.

Public API:
    import_csv(parent: Optional[tk.Misc]=None, title="Import Data") -> Optional[tuple[list[str], str]]
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple, List

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Optional pandas for robust Excel/CSV reading; gracefully degrade if unavailable
try:
    import pandas as _pd  # type: ignore
except Exception:
    _pd = None  # Falls back to csv module for text; Excel requires pandas


# -----------------------------
# Internal Tk convenience utils
# -----------------------------
def _ensure_parent(parent: Optional[tk.Misc]) -> Tuple[tk.Misc, Optional[tk.Tk]]:
    """Create/return a Tk owner widget and an optional hidden root (to be destroyed by caller)."""
    if parent is not None:
        return parent, None
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
    p = Path(path)
    return p.suffix.lower() in {".xlsx", ".xls"}


def _is_text_table(path: str) -> bool:
    p = Path(path)
    return p.suffix.lower() in {".csv", ".tsv", ".txt"}


def _read_excel(path: str, max_rows: int | None = None) -> list[list[str]]:
    if _pd is None:
        raise RuntimeError("Reading Excel requires pandas. Please install pandas.")
    try:
        df = _pd.read_excel(path, nrows=max_rows)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel: {e}")
    # Convert to list of lists of strings
    return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]


def _sniff_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
        return dialect.delimiter
    except Exception:
        # Heuristic: prefer tab if many tabs, else comma
        return "\t" if sample.count("\t") > sample.count(",") else ","


def _read_text_table(path: str, max_rows: int | None = None) -> list[list[str]]:
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
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
    except UnicodeDecodeError:
        # Retry with locale default encoding if UTF-8 fails
        with open(path, "r", newline="") as f:
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
    except Exception as e:
        raise RuntimeError(f"Failed to read delimited text: {e}")


def _load_tabular(path: str, max_rows: int | None = None) -> list[list[str]]:
    if _is_excel(path):
        return _read_excel(path, max_rows=max_rows)
    if _is_text_table(path):
        return _read_text_table(path, max_rows=max_rows)
    # Try pandas for odd formats if available (e.g., .ods via pandas/odfpy)
    if _pd is not None:
        try:
            # pandas will infer reader by suffix/engine if possible
            df = _pd.read_csv(path, nrows=max_rows)  # fallback attempt
            return [[("" if _pd.isna(v) else str(v)) for v in row] for row in df.itertuples(index=False, name=None)]
        except Exception:
            pass
    raise RuntimeError("Unsupported file type. Please select CSV/TSV/TXT or Excel (.xlsx/.xls).")


# -----------------------------
# UI Utilities
# -----------------------------
class _RadioHeader(ttk.Frame):
    """
    A horizontally scrollable header row of Radiobuttons that mirrors Treeview columns.

    - Uses a Canvas + inner Frame to host one ttk.Radiobutton per column.
    - Exposes xview/xscrollcommand to sync with an associated horizontal scrollbar / Treeview.
    """

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
        # Ensure inner width grows with canvas so scrollbar behaves nicely
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_scroll(self, *args):
        self.canvas.xview(*args)

    def xview(self, *args):
        self.canvas.xview(*args)

    def xscrollcommand(self, *args):
        self.hsb.set(*args)

    def rebuild(self, column_labels: list[str]):
        # Clear existing
        for w in self.inner.winfo_children():
            w.destroy()
        self._radios.clear()

        # Fill with Radiobuttons; one per column
        for idx, label in enumerate(column_labels):
            b = ttk.Radiobutton(
                self.inner,
                text=label,
                value=idx,
                variable=self.var,
                takefocus=False
            )
            # Pack side-by-side; give a little padding
            b.grid(row=0, column=idx, padx=(6 if idx == 0 else 12, 12), pady=4, sticky="w")
            self._radios.append(b)

        self.inner.update_idletasks()
        # Reset scroll to start
        self.canvas.xview_moveto(0.0)


# -----------------------------
# Public API: Import Wizard
# -----------------------------
def import_csv(
    parent: Optional[tk.Misc] = None,
    title: str = "Import Data",
    filetypes: Sequence[Tuple[str, str]] = (
        ("Excel files", "*.xlsx *.xls"),
        ("CSV files", "*.csv"),
        ("TSV files", "*.tsv"),
        ("Text files", "*.txt"),
        ("All files", "*.*"),
    ),
) -> Optional[Tuple[List[str], str]]:
    """
    Open an "Import Wizard" dialog, let the user select a file, preview it, choose 'has headers',
    pick exactly one column via radio buttons, and return that column's values and the file stem.

    Returns:
        (values_from_selected_column, filename_stem) or None if cancelled.
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
    for r in range(8):
        dlg.rowconfigure(r, weight=0)
    # Preview region grows
    dlg.rowconfigure(6, weight=1)

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
            _refresh_preview()

    ttk.Button(dlg, text="Browse…", command=browse_file).grid(row=1, column=2, padx=(4, 10), pady=4, sticky="w")

    # Header checkbox
    has_headers = tk.BooleanVar(master=dlg, value=False)
    header_chk = ttk.Checkbutton(
        dlg, text="File has headers (skip first row)", variable=has_headers, command=lambda: _refresh_preview()
    )
    header_chk.grid(row=2, column=1, padx=4, pady=2, sticky="w")

    # Note / helper text under checkbox
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

    # Sync xscroll between tree and radio header
    def _tree_xscroll(*args):
        tree.xview(*args)
        radio_header.xview(*args)

    def _xscroll_set(first, last):
        hscroll.set(first, last)
        radio_header.xscrollcommand(first, last)

    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=_xscroll_set)
    hscroll.configure(command=_tree_xscroll)

    # Buttons
    btns = ttk.Frame(dlg)
    btns.grid(row=7, column=0, columnspan=3, sticky="e", padx=10, pady=(0, 10))
    ttk.Button(btns, text="Cancel", command=dlg.destroy).grid(row=0, column=0, padx=5)
    process_btn = ttk.Button(btns, text="Import")
    process_btn.grid(row=0, column=1, padx=5)

    # -------------- Preview management --------------
    _loaded_rows: list[list[str]] = []
    _filename_stem: str = ""

    def _set_preview_columns(cols: list[str]):
        # Reset columns in Treeview
        tree["columns"] = [f"c{i}" for i in range(len(cols))]
        for i, label in enumerate(cols):
            cid = f"c{i}"
            tree.heading(cid, text=label)
            tree.column(cid, width=120, stretch=False, anchor="w")

        # Rebuild radio header
        radio_header.rebuild(cols)

    def _fill_preview_rows(rows: list[list[str]]):
        tree.delete(*tree.get_children())
        for r in rows:
            # pad/trim to the number of columns currently configured
            ncols = len(tree["columns"])
            padded = (r + [""] * ncols)[:ncols]
            tree.insert("", "end", values=padded)

    def _initial_blank_preview():
        _set_preview_columns([f"Column {i+1}" for i in range(5)])
        _fill_preview_rows([[""] * 5 for _ in range(5)])

    def _refresh_preview():
        path = file_var.get().strip()
        if not path:
            _initial_blank_preview()
            return

        try:
            # Load up to, say, 200 rows to allow meaningful vertical scroll, while rendering 5 row height
            rows = _load_tabular(path, max_rows=200)
        except Exception as e:
            messagebox.showerror("Load error", str(e), parent=dlg)
            _initial_blank_preview()
            return

        # Remember stem
        nonlocal _filename_stem, _loaded_rows
        _filename_stem = Path(path).stem
        _loaded_rows = rows

        # Determine headers and body according to checkbox
        if rows:
            if has_headers.get():
                header = rows[0]
                data = rows[1:]
            else:
                # Synthesize column names
                max_cols = max((len(r) for r in rows), default=1)
                header = [f"Column {i+1}" for i in range(max_cols)]
                data = rows
        else:
            header, data = [f"Column {i+1}" for i in range(5)], []

        # Adjust preview columns to actual file width (columns adjust; row height remains 5)
        _set_preview_columns([str(h) if (h is not None and str(h).strip() != "") else f"Column {i+1}"
                              for i, h in enumerate(header)])
        _fill_preview_rows(data)

        # Clamp selected column if out of range
        if selected_col.get() >= len(header):
            selected_col.set(0)

    _initial_blank_preview()  # start 5x5

    # -------------- Import handler --------------
    result_values: Optional[list[str]] = None
    result_stem: Optional[str] = None

    def _do_import():
        nonlocal result_values, result_stem
        path = file_var.get().strip()
        if not path:
            messagebox.showerror("Error", "No file selected.", parent=dlg)
            return
        if not _loaded_rows:
            try:
                rows = _load_tabular(path)  # full read
            except Exception as e:
                messagebox.showerror("Load error", str(e), parent=dlg)
                return
        else:
            rows = _loaded_rows  # we already loaded a slice; good enough for column extraction too

        # Respect header checkbox
        if has_headers.get() and rows:
            body = rows[1:]
        else:
            body = rows

        if not body:
            messagebox.showerror("Error", "The file appears to have no data rows.", parent=dlg)
            return

        col_idx = selected_col.get()
        # Gather selected column; pad missing cells with empty string
        out: list[str] = []
        for r in body:
            val = r[col_idx] if col_idx < len(r) else ""
            out.append("" if val is None else str(val))

        result_values = out
        result_stem = Path(path).stem
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
    dlg.geometry(f"760x460+{x}+{y}")

    # Block until closed
    owner.wait_window(dlg)
    _safe_destroy(created_root)

    if result_values is None or result_stem is None:
        return None
    return result_values, result_stem
