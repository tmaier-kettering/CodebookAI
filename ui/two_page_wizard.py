import os
import tkinter as tk
from dataclasses import dataclass
from functools import partial
from tkinter import ttk, filedialog, messagebox
from typing import Callable, Optional

import pandas as pd
from ui.ui_utils import center_window  # keep your existing helper


# ----------------------------- Utility: Data Loading -----------------------------

def load_table(path: str, has_header: bool) -> pd.DataFrame:
    """
    Load CSV/TSV/TXT/Excel into a pandas DataFrame.
    If has_header is False, assign synthetic headers: Col 1, Col 2, ...
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv", ".tsv", ".txt"):
        sep = "," if ext == ".csv" else "\t"
        if has_header:
            df = pd.read_csv(path, sep=sep, dtype=str, engine="python")
        else:
            df = pd.read_csv(path, sep=sep, header=None, dtype=str, engine="python")
            df.columns = [f"Col {i+1}" for i in range(df.shape[1])]
        return df
    elif ext in (".xlsx", ".xls", ".xlsm"):
        if has_header:
            df = pd.read_excel(path, dtype=str, engine="openpyxl")
        else:
            df = pd.read_excel(path, header=None, dtype=str, engine="openpyxl")
            df.columns = [f"Col {i+1}" for i in range(df.shape[1])]
        return df
    else:
        # try csv as fallback
        try:
            df = pd.read_csv(path, dtype=str, engine="python")
            return df
        except Exception as e:
            raise ValueError(f"Unsupported file type or failed to read file: {e}")


# ----------------------------- Result Object -----------------------------

@dataclass
class WizardResult:
    # Raw selected series
    ds1_text: pd.Series
    ds1_label: pd.Series
    ds1_name: str
    ds2_text: pd.Series
    ds2_label: pd.Series
    ds2_name: str
    # Convenience dataframes
    df1: pd.DataFrame
    df2: pd.DataFrame
    merged: pd.DataFrame


# ----------------------------- UI Components -----------------------------

class HorizontalRadioScroller(ttk.Frame):
    """
    A horizontally scrollable container that lays out ttk.Radiobuttons in a row.
    Used to display column names for selection.
    """
    def __init__(self, master, variable: tk.StringVar, **kwargs):
        super().__init__(master, **kwargs)
        self.variable = variable

        self.canvas = tk.Canvas(self, height=36, borderwidth=0, highlightthickness=0)
        self.hbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(xscrollcommand=self.hbar.set)

        self.canvas.pack(fill="x", expand=True)
        self.hbar.pack(fill="x")

        self._buttons = []

    def set_options(self, labels):
        # Clear
        for b in self._buttons:
            b.destroy()
        self._buttons.clear()

        # Add
        for col in labels:
            btn = ttk.Radiobutton(self.inner, text=str(col), value=str(col), variable=self.variable)
            btn.pack(side="left", padx=6, pady=6)
            self._buttons.append(btn)


class DatasetNameSelector(ttk.Frame):
    """
    Two radio options:
      1) Use the file name (minus extension) (default)
      2) Other: free text box
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.choice = tk.StringVar(value="file")
        self.file_based_name = tk.StringVar(value="")
        self.custom_name = tk.StringVar(value="")

        ttk.Label(self, text="Dataset Name").pack(anchor="w")

        # Radio: Use file name
        row1 = ttk.Frame(self)
        row1.pack(fill="x", pady=(4, 2))
        ttk.Radiobutton(row1, text="Use file name (minus extension)", value="file", variable=self.choice,
                        command=self._toggle).pack(side="left")
        ttk.Label(row1, textvariable=self.file_based_name, foreground="#666").pack(side="left", padx=(8, 0))

        # Radio: Other + entry
        row2 = ttk.Frame(self)
        row2.pack(fill="x", pady=(2, 0))
        ttk.Radiobutton(row2, text="Other:", value="other", variable=self.choice,
                        command=self._toggle).pack(side="left")
        self.entry = ttk.Entry(row2, textvariable=self.custom_name, width=28)
        self.entry.pack(side="left", padx=(6, 0))
        self._toggle()

    def _toggle(self):
        use_custom = self.choice.get() == "other"
        state = "normal" if use_custom else "disabled"
        self.entry.configure(state=state)

    def set_file_name(self, path: str):
        base = os.path.splitext(os.path.basename(path))[0]
        self.file_based_name.set(base)
        if self.choice.get() != "other":
            self.choice.set("file")

    def get_name(self) -> str:
        if self.choice.get() == "other":
            name = self.custom_name.get().strip()
            return name if name else self.file_based_name.get()
        return self.file_based_name.get()


class FileAndSelectionPage(ttk.Frame):
    """
    One page that lets the user:
      - choose a file
      - toggle header existence
      - preview top 5 rows
      - pick TEXT column and LABEL column via horizontal radio lists
      - choose dataset name via DatasetNameSelector
    """
    def __init__(self, master, page_index: int, total_pages: int, title: str,
                 on_cancel: Callable[[], None],
                 on_prev: Optional[Callable[[], None]],
                 on_next: Optional[Callable[[], None]],
                 on_ok: Optional[Callable[[], None]]):
        super().__init__(master)

        self.page_index = page_index
        self.total_pages = total_pages
        self.on_cancel = on_cancel
        self.on_prev = on_prev
        self.on_next = on_next
        self.on_ok = on_ok

        self.df_cache: Optional[pd.DataFrame] = None
        self.current_path: Optional[str] = None

        # State
        self.has_header = tk.BooleanVar(value=True)
        self.selected_text_col = tk.StringVar(value="")
        self.selected_label_col = tk.StringVar(value="")

        # Title
        ttk.Label(self, text=title, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(4, 8))

        # File chooser row
        file_row = ttk.Frame(self)
        file_row.pack(fill="x", pady=(0, 6))
        ttk.Button(file_row, text="Choose file…", command=self._choose_file).pack(side="left")
        ttk.Checkbutton(file_row, text="Has header row", variable=self.has_header, command=self._reload_if_possible)\
            .pack(side="left", padx=12)
        self.path_label = ttk.Label(file_row, text="", foreground="#555")
        self.path_label.pack(side="left", padx=8)

        # Preview (top 5)
        preview = ttk.LabelFrame(self, text="Preview (top 5)")
        preview.pack(fill="both", expand=True, pady=(2, 8))
        self.tree = ttk.Treeview(preview, columns=(), show="headings", height=6)
        vsb = ttk.Scrollbar(preview, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="left", fill="y")

        # Column pickers
        pickers = ttk.Frame(self)
        pickers.pack(fill="x", pady=(0, 6))
        ttk.Label(pickers, text="Select TEXT column:").pack(anchor="w")
        self.text_picker = HorizontalRadioScroller(pickers, self.selected_text_col)
        self.text_picker.pack(fill="x")
        ttk.Label(pickers, text="Select LABEL column:").pack(anchor="w", pady=(6, 0))
        self.label_picker = HorizontalRadioScroller(pickers, self.selected_label_col)
        self.label_picker.pack(fill="x")

        # Dataset name selector
        self.name_selector = DatasetNameSelector(self)
        self.name_selector.pack(fill="x", pady=(6, 0))

        # Nav buttons
        nav = ttk.Frame(self)
        nav.pack(fill="x", pady=(10, 0))
        ttk.Button(nav, text="Cancel", command=self.on_cancel).pack(side="left")
        if self.on_next:
            ttk.Button(nav, text="Next ▶", command=self._next_clicked).pack(side="right")
        if self.on_ok:
            ttk.Button(nav, text="OK", command=self._ok_clicked).pack(side="right")
        if self.on_prev:
            ttk.Button(nav, text="◀ Back", command=self.on_prev).pack(side="right", padx=(6, 0))

    # ---- File+Preview handling ----

    def _choose_file(self):
        path = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("Data files", "*.csv *.tsv *.txt *.xlsx *.xls *.xlsm"), ("All files", "*.*")]
        )
        if not path:
            return
        self.current_path = path
        self.path_label.configure(text=os.path.basename(path))
        self.name_selector.set_file_name(path)
        self._load_and_preview(path)

    def _load_and_preview(self, path: str):
        try:
            df = load_table(path, has_header=bool(self.has_header.get()))
        except Exception as e:
            messagebox.showerror("Load Error", str(e), parent=self.winfo_toplevel())
            return

        self.df_cache = df
        # Preview top 5
        head = df.head(5)
        # Setup tree columns
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(map(str, head.columns))
        for c in head.columns:
            self.tree.heading(str(c), text=str(c))
            self.tree.column(str(c), width=140, stretch=True)
        for _, row in head.iterrows():
            self.tree.insert("", "end", values=[str(x) if pd.notna(x) else "" for x in row.tolist()])

        # Update the radio lists
        cols = list(map(str, df.columns))
        self.text_picker.set_options(cols)
        self.label_picker.set_options(cols)
        # Clear previous selections if columns changed
        self.selected_text_col.set("")
        self.selected_label_col.set("")

    def _reload_if_possible(self):
        if self.current_path:
            self._load_and_preview(self.current_path)

    # ---- Accessors ----

    def get_selected_series_pair(self):
        if self.df_cache is None:
            return None, None
        tcol = self.selected_text_col.get()
        lcol = self.selected_label_col.get()
        if not tcol or tcol not in self.df_cache.columns:
            return None, None
        if not lcol or lcol not in self.df_cache.columns:
            return None, None

        text_series = self.df_cache[tcol].astype(str).reset_index(drop=True)
        label_series = self.df_cache[lcol].astype(str).reset_index(drop=True)
        return text_series, label_series

    def get_dataset_name(self) -> str:
        return self.name_selector.get_name()

    def validate_ready(self) -> bool:
        if not self.current_path:
            messagebox.showwarning("Missing File", "Please choose a file.", parent=self.winfo_toplevel())
            return False
        if self.df_cache is None:
            messagebox.showwarning("Not Loaded", "File is not loaded yet.", parent=self.winfo_toplevel())
            return False
        if not self.selected_text_col.get():
            messagebox.showwarning("Select Text Column", "Please select the TEXT column.", parent=self.winfo_toplevel())
            return False
        if not self.selected_label_col.get():
            messagebox.showwarning("Select Label Column", "Please select the LABEL column.", parent=self.winfo_toplevel())
            return False
        return True

    # ---- Navigation ----

    def _next_clicked(self):
        if self.validate_ready() and self.on_next:
            self.on_next()

    def _ok_clicked(self):
        if self.validate_ready() and self.on_ok:
            self.on_ok()


# ----------------------------- Wizard -----------------------------

class TwoPageWizard(tk.Toplevel):
    """
    Generic 2-page wizard for selecting two datasets (text + label + dataset name each).
    On OK (last page), it calls `on_finish(WizardResult, self)` and expects a bool:
      - True -> close wizard
      - False -> keep it open (e.g., validation error)
    """
    def __init__(self, parent: tk.Misc,
                 on_finish: Optional[Callable[[WizardResult, tk.Toplevel], bool]] = None):
        super().__init__(parent)
        self.title("Two Dataset Wizard")
        self.transient(parent)
        self.grab_set()
        self.resizable(True, True)

        self._on_finish = on_finish
        self.result = None  # for callers that want to inspect after closing

        # Page container
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # Page state
        self.pages: list[FileAndSelectionPage] = []

        # Dataset 1 placeholders
        self.ds1_text: Optional[pd.Series] = None
        self.ds1_label: Optional[pd.Series] = None
        self.ds1_name: Optional[str] = None

        # Create pages
        titles = ["Dataset 1", "Dataset 2"]
        for i, title in enumerate(titles):
            page = FileAndSelectionPage(
                container, i, 2, title,
                on_cancel=self.cancel_wizard,
                on_prev=self.prev_page if i == 1 else None,
                on_next=partial(self.next_page, i) if i == 0 else None,
                on_ok=self.finish if i == 1 else None
            )
            self.pages.append(page)

        # Show first
        self._show_page(0)
        try:
            center_window(self, width=900, height=600)
        except Exception:
            # Safe fallback
            self.geometry("900x600+120+80")

    # ---- Page switching ----

    def _show_page(self, index: int):
        for i, page in enumerate(self.pages):
            page.pack_forget()
        self.pages[index].pack(fill="both", expand=True)
        self.current_index = index

    def next_page(self, i):
        # Persist selections from page 0
        if i == 0:
            page = self.pages[0]
            if not page.validate_ready():
                return
            text_series, label_series = page.get_selected_series_pair()
            if text_series is None or label_series is None:
                return
            if len(text_series) != len(label_series):
                messagebox.showerror("Length Mismatch",
                                     f"Dataset 1 TEXT length ({len(text_series)}) must match LABEL length ({len(label_series)}).",
                                     parent=self)
                return
            self.ds1_text = text_series
            self.ds1_label = label_series
            self.ds1_name = page.get_dataset_name()
        self._show_page(i + 1)

    def prev_page(self):
        self._show_page(0)

    def cancel_wizard(self):
        self.result = None
        self.destroy()

    # ---- Finish ----

    def _collect_result(self) -> Optional[WizardResult]:
        # Page 2 (dataset 2)
        pg = self.pages[1]
        text_series, label_series = pg.get_selected_series_pair()
        if text_series is None or label_series is None:
            return None
        if len(text_series) != len(label_series):
            messagebox.showerror("Length Mismatch",
                                 f"Dataset 2 TEXT length ({len(text_series)}) must match LABEL length ({len(label_series)}).",
                                 parent=self)
            return None
        ds2_text = text_series
        ds2_label = label_series
        ds2_name = pg.get_dataset_name()

        # --- Ensure dataset names are not identical ---
        name1 = str(self.ds1_name)  # from page 1
        name2 = str(ds2_name)  # from page 2

        if name2 == name1:
            # If same, append " (1)". If somehow that also collides, bump the number.
            base = name2
            n = 1
            while f"{base} ({n})" == name1:
                n += 1
            name2 = f"{base} ({n})"

        if self.ds1_text is None or self.ds1_label is None:
            messagebox.showwarning("Incomplete", "Please complete Page 1 for Dataset 1.", parent=self)
            return None

        # Build dataframes
        df1 = pd.DataFrame({
            "text": self.ds1_text.astype(str),
            name1: self.ds1_label.astype(str)
        })
        df2 = pd.DataFrame({
            "text": ds2_text.astype(str),
            name2: ds2_label.astype(str)
        })

        # Add an occurrence index per text to align duplicates 1-to-1 even if order differs
        df1["occ"] = df1.groupby("text").cumcount()
        df2["occ"] = df2.groupby("text").cumcount()

        # Merge on text + occurrence, then drop the helper column
        merged = pd.merge(df1, df2, on=["text", "occ"], how="inner")
        merged = merged.drop(columns=["occ"])

        return WizardResult(
            ds1_text=self.ds1_text, ds1_label=self.ds1_label, ds1_name=name1,
            ds2_text=ds2_text, ds2_label=ds2_label, ds2_name=name2,
            df1=df1, df2=df2, merged=merged
        )

    def finish(self):
        result = self._collect_result()
        if result is None:
            return

        # Delegate to handler (if any)
        close = True
        if self._on_finish is not None:
            try:
                close = bool(self._on_finish(result, self))
            except Exception as e:
                messagebox.showerror("Handler Error", f"An error occurred in the finish handler:\n{e}", parent=self)
                close = False

        if close:
            # keep a simple dict for compatibility
            self.result = {
                "dataframe": result.merged,
                "dataset1_name": result.ds1_name,
                "dataset2_name": result.ds2_name,
            }
            self.destroy()


# ----------------------------- Public Entry -----------------------------

def open_two_page_wizard(parent: tk.Misc,
                         on_finish: Optional[Callable[[WizardResult, tk.Toplevel], bool]] = None):
    """
    Open the 2-page wizard as a modal dialog attached to 'parent'.
    If on_finish is provided, it's called with (WizardResult, toplevel) when OK is pressed.
    The handler should return True to close the wizard, False to keep it open.
    Returns the wizard .result dict (or None if cancelled).
    """
    dlg = TwoPageWizard(parent, on_finish=on_finish)
    parent.wait_window(dlg)
    return dlg.result
