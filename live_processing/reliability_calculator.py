import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
from functools import partial

from ui.ui_utils import center_window


# ----------------------------- Utility: Data Loading -----------------------------

def load_table(path: str, has_header: bool) -> pd.DataFrame:
    """
    Load CSV/TSV/TXT/Excel into a pandas DataFrame.
    If has_header is False, assign synthetic headers: Col 1, Col 2, ...
    """
    ext = os.path.splitext(path)[1].lower()
    if ext in [".csv"]:
        df = pd.read_csv(path, header=0 if has_header else None)
    elif ext in [".tsv", ".txt"]:
        try:
            df = pd.read_csv(path, sep="\t", header=0 if has_header else None)
        except Exception:
            df = pd.read_csv(path, header=0 if has_header else None)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(path, header=0 if has_header else None)
    else:
        raise ValueError("Unsupported file type. Please choose CSV, TSV/TXT, or Excel.")

    if not has_header:
        df.columns = [f"Col {i+1}" for i in range(df.shape[1])]
    return df


def compute_cohens_kappa(labels_a: pd.Series, labels_b: pd.Series) -> float:
    """
    Compute Cohen's kappa between two categorical series of equal length.
    """
    assert len(labels_a) == len(labels_b)
    cats = sorted(set(labels_a.astype(str)).union(set(labels_b.astype(str))))
    table = pd.crosstab(labels_a.astype(str), labels_b.astype(str)).reindex(index=cats, columns=cats, fill_value=0)
    n = table.values.sum()
    if n == 0:
        return float("nan")
    po = (table.values.diagonal().sum()) / n
    row_marginals = table.sum(axis=1).values / n
    col_marginals = table.sum(axis=0).values / n
    pe = (row_marginals * col_marginals).sum()
    if pe == 1.0:
        return 1.0
    return float((po - pe) / (1 - pe))


# ----------------------------- UI: Horizontal Radio List -----------------------------

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

        self.canvas.pack(side="top", fill="x", expand=True)
        self.hbar.pack(side="bottom", fill="x")

        self._radio_buttons = []

    def set_options(self, options):
        for w in self._radio_buttons:
            w.destroy()
        self._radio_buttons.clear()

        for opt in options:
            rb = ttk.Radiobutton(self.inner, text=str(opt), value=str(opt), variable=self.variable)
            rb.pack(side="left", padx=6, pady=4)
            self._radio_buttons.append(rb)

        if options and not self.variable.get():
            self.variable.set(str(options[0]))


# ----------------------------- UI: Preview Table -----------------------------

class PreviewTable(ttk.Frame):
    """
    A small Treeview table with vertical scrollbar. Shows up to top 5 rows of the current DataFrame.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, columns=(), show="headings", height=6)
        self.vbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.vbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        self.vbar.pack(side="right", fill="y")

    def show_dataframe(self, df: pd.DataFrame):
        # Clear previous
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
            self.tree.column(col, width=100, stretch=True)
        self.tree.delete(*self.tree.get_children())

        if df is None or df.empty:
            self.tree["columns"] = ()
            return

        cols = list(df.columns)
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=str(col))
            self.tree.column(col, width=max(80, min(240, int(8 * (len(str(col)) + 1)))), anchor="w", stretch=True)

        top = df.head(5)
        for _, row in top.iterrows():
            values = ["" if pd.isna(v) else str(v) for v in row.tolist()]
            self.tree.insert("", "end", values=values)


# ----------------------------- Wizard Page -----------------------------

class WizardPage(ttk.Frame):
    """
    One of the four pages. Lets the user:
      - Choose a file
      - Toggle header checkbox
      - See a horizontal list of column radio buttons
      - Preview top 5 rows
      - Cancel/Prev/Next (or OK on the last page)
    """
    def __init__(self, master, page_index: int, total_pages: int, title: str,
                 on_cancel, on_prev, on_next, on_ok=None):
        super().__init__(master, padding=12)
        self.page_index = page_index
        self.total_pages = total_pages
        self.on_cancel = on_cancel
        self.on_prev = on_prev
        self.on_next = on_next
        self.on_ok = on_ok

        # Internal state
        self.current_path = None
        self.has_header = tk.BooleanVar(value=True)
        self.selected_column = tk.StringVar(value="")

        # Title
        lbl = ttk.Label(self, text=title, style="Title.TLabel")
        lbl.pack(anchor="w", pady=(0, 8))

        # File chooser row
        row = ttk.Frame(self)
        row.pack(fill="x", pady=4)
        self.path_var = tk.StringVar(value="")
        ttk.Label(row, text="File:").pack(side="left")
        self.path_entry = ttk.Entry(row, textvariable=self.path_var)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row, text="Browse…", command=self.browse_file).pack(side="left")

        # Header checkbox
        chk = ttk.Checkbutton(self, text="First row contains headers", variable=self.has_header, command=self.refresh_after_header_toggle)
        chk.pack(anchor="w", pady=(6, 8))

        # Horizontal radio scroller for columns
        ttk.Label(self, text="Select exactly one column:").pack(anchor="w")
        self.radio_scroller = HorizontalRadioScroller(self, variable=self.selected_column)
        self.radio_scroller.pack(fill="x", pady=(2, 8))

        # Preview table
        self.preview = PreviewTable(self)
        self.preview.pack(fill="both", expand=True, pady=(4, 8))

        # Buttons — use a 4-column grid for layout consistency:
        # [Cancel] [spacer expands] [Previous (if any)] [Next/OK (always rightmost)]
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(10, 0))

        btns.columnconfigure(0, weight=0)  # Cancel
        btns.columnconfigure(1, weight=1)  # Spacer
        btns.columnconfigure(2, weight=0)  # Previous (optional)
        btns.columnconfigure(3, weight=0)  # Next/OK (rightmost)

        ttk.Button(btns, text="Cancel", command=self.on_cancel).grid(row=0, column=0, sticky="w")

        # Previous (if applicable)
        if page_index > 0:
            ttk.Button(btns, text="Previous", command=self.on_prev).grid(row=0, column=2, sticky="e", padx=(0, 6))

        # Next or OK (always rightmost)
        if page_index < total_pages - 1:
            ttk.Button(btns, text="Next", command=self.next_clicked).grid(row=0, column=3, sticky="e")
        else:
            ttk.Button(btns, text="OK", command=self.ok_clicked).grid(row=0, column=3, sticky="e")

        # DataFrame cache
        self.df_cache = None

    def browse_file(self):
        path = filedialog.askopenfilename(
            title="Choose a data file",
            filetypes=[
                ("CSV files", "*.csv"),
                ("TSV files", "*.tsv *.txt"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*"),
            ]
        )
        if not path:
            return
        self.path_var.set(path)
        self.current_path = path
        self.load_and_refresh()

    def refresh_after_header_toggle(self):
        if self.current_path:
            self.load_and_refresh()

    def load_and_refresh(self):
        try:
            df = load_table(self.current_path, self.has_header.get())
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load file:\n{e}", parent=self.winfo_toplevel())
            return

        self.df_cache = df
        self.radio_scroller.set_options(list(df.columns))
        self.preview.show_dataframe(df)

    def get_selected_series(self) -> pd.Series | None:
        if self.df_cache is None:
            return None
        colname = self.selected_column.get()
        if not colname or colname not in self.df_cache.columns:
            return None
        series = self.df_cache[colname]
        return series.reset_index(drop=True)

    def validate_ready(self) -> bool:
        if not self.current_path:
            messagebox.showwarning("Missing File", "Please choose a file.", parent=self.winfo_toplevel())
            return False
        if self.df_cache is None:
            messagebox.showwarning("Not Loaded", "File is not loaded yet.", parent=self.winfo_toplevel())
            return False
        if not self.selected_column.get():
            messagebox.showwarning("Select Column", "Please select exactly one column.", parent=self.winfo_toplevel())
            return False
        return True

    def next_clicked(self):
        if not self.validate_ready():
            return
        self.on_next()

    def ok_clicked(self):
        if not self.validate_ready():
            return
        if self.on_ok:
            self.on_ok()


# ----------------------------- Wizard Dialog -----------------------------

class FourPageWizard(tk.Toplevel):
    """
    4 pages:
      0: Dataset 1 - Text
      1: Dataset 1 - Labels (must match length of page 0 selection)
      2: Dataset 2 - Text
      3: Dataset 2 - Labels (must match length of page 2 selection; OK runs compute)
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Label Agreement Wizard")
        self.transient(parent)
        self.grab_set()
        self.geometry("900x600")
        center_window(self, 900, 600)
        self.minsize(800, 520)
        self.resizable(True, True)

        style = ttk.Style(self)
        try:
            self.tk.call("tk", "scaling", 1.2)
        except Exception:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))

        container = ttk.Frame(self, padding=8)
        container.pack(fill="both", expand=True)

        self.current_page_idx = 0
        self.pages: list[WizardPage] = []

        self.ds1_text: pd.Series | None = None
        self.ds1_label: pd.Series | None = None
        self.ds2_text: pd.Series | None = None
        self.ds2_label: pd.Series | None = None

        titles = [
            "Page 1 of 4 — Dataset 1: Text Column",
            "Page 2 of 4 — Dataset 1: Label Column (must match length of Page 1)",
            "Page 3 of 4 — Dataset 2: Text Column",
            "Page 4 of 4 — Dataset 2: Label Column (must match length of Page 3)",
        ]

        for i, title in enumerate(titles):
            page = WizardPage(
                container, i, 4, title,
                on_cancel=self.cancel_wizard,
                on_prev=self.prev_page,
                on_next=partial(self.next_page, i),
                on_ok=self.finish if i == 3 else None
            )
            self.pages.append(page)

        for p in self.pages:
            p.place(relx=0, rely=0, relwidth=1, relheight=1)
            p.lower()
        self.pages[0].lift()

        self.result = None  # {"dataframe": df, "percent_agreement": x, "kappa": y, "saved_path": path}
        self.protocol("WM_DELETE_WINDOW", self.cancel_wizard)

    # Navigation handlers

    def prev_page(self):
        idx = self.current_page_idx
        if idx == 0:
            return
        self.pages[idx].lower()
        self.current_page_idx = idx - 1
        self.pages[self.current_page_idx].lift()

    def next_page(self, from_index: int):
        if from_index != self.current_page_idx:
            return

        pg = self.pages[self.current_page_idx]
        series = pg.get_selected_series()
        if series is None:
            return

        if self.current_page_idx == 0:
            self.ds1_text = series.astype(str)
        elif self.current_page_idx == 1:
            if self.ds1_text is None:
                messagebox.showwarning("Missing Text", "Please complete Page 1 first.", parent=self)
                return
            if len(series) != len(self.ds1_text):
                messagebox.showerror("Length Mismatch", f"Labels length ({len(series)}) must match Dataset 1 Text length ({len(self.ds1_text)}).", parent=self)
                return
            self.ds1_label = series.astype(str)
        elif self.current_page_idx == 2:
            self.ds2_text = series.astype(str)

        self.pages[self.current_page_idx].lower()
        self.current_page_idx += 1
        self.pages[self.current_page_idx].lift()

    def finish(self):
        pg = self.pages[3]
        series = pg.get_selected_series()
        if series is None:
            return

        if self.ds2_text is None:
            messagebox.showwarning("Missing Text", "Please complete Page 3 first.", parent=self)
            return
        if len(series) != len(self.ds2_text):
            messagebox.showerror("Length Mismatch", f"Labels length ({len(series)}) must match Dataset 2 Text length ({len(self.ds2_text)}).", parent=self)
            return
        self.ds2_label = series.astype(str)

        if self.ds1_text is None or self.ds1_label is None:
            messagebox.showwarning("Incomplete", "Please complete Pages 1 and 2 for Dataset 1.", parent=self)
            return

        # Build dataframes
        df1 = pd.DataFrame({"text": self.ds1_text.astype(str), "label1": self.ds1_label.astype(str)})
        df2 = pd.DataFrame({"text": self.ds2_text.astype(str), "label2": self.ds2_label.astype(str)})

        # Inner join on shared text
        merged = pd.merge(df1, df2, on="text", how="inner")
        # Agreement column
        merged["agreement"] = merged["label1"] == merged["label2"]

        # Metrics
        num_rows = int(len(merged))
        percent_agree = float(merged["agreement"].mean() * 100.0) if num_rows > 0 else float("nan")
        kappa = compute_cohens_kappa(merged["label1"], merged["label2"]) if num_rows > 0 else float("nan")

        # Prepare Excel save
        save_path = filedialog.asksaveasfilename(
            title="Save results (Excel)",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx"), ("All files", "*.*")],
            initialfile="agreement_results.xlsx",
            parent=self
        )

        if save_path:
            # Build stats sheet as a tidy 2-column table
            stats_df = pd.DataFrame({
                "Metric": ["Number of Rows", "Percent Agreement", "Cohen's Kappa"],
                "Value": [num_rows, percent_agree, kappa]
            })
            # Ensure column order in data
            data_df = merged[["text", "label1", "label2", "agreement"]].copy()

            with pd.ExcelWriter(save_path, engine="openpyxl") as writer:
                stats_df.to_excel(writer, sheet_name="Reliability Statistics", index=False)
                data_df.to_excel(writer, sheet_name="Data", index=False)

        self.result = {
            "dataframe": merged,
            "percent_agreement": percent_agree,
            "kappa": kappa,
            "saved_path": save_path if save_path else None
        }
        self.destroy()

    def cancel_wizard(self):
        if messagebox.askokcancel("Cancel", "Cancel and close the wizard?", parent=self):
            self.result = None
            self.destroy()


# ----------------------------- Public Entry Point -----------------------------

def reliability_wizard_main(parent: tk.Misc):
    """
    Open the 4-page wizard as a modal dialog attached to 'parent'.
    Returns a dict with:
      - dataframe: merged DataFrame with columns [text, label1, label2, agreement]
      - percent_agreement: float
      - kappa: float
      - saved_path: str | None
    or None if cancelled.
    """
    dlg = FourPageWizard(parent)
    parent.wait_window(dlg)
    return dlg.result
