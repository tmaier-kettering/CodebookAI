import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional

try:
    import pandas as pd
except ImportError:
    raise SystemExit(
        "This tool requires pandas. Install it first:\n\n    pip install pandas openpyxl pyarrow\n"
    )

# ----------------------------
# Utilities
# ----------------------------

FILE_TYPES = [
    ("CSV files", "*.csv"),
    ("TSV files", "*.tsv *.tab"),
    ("Excel files", "*.xlsx *.xls"),
    ("Parquet files", "*.parquet"),
    ("All supported", "*.csv *.tsv *.tab *.xlsx *.xls *.parquet"),
    ("All files", "*.*"),
]

def _read_table(path: str, has_header: bool) -> pd.DataFrame:
    """
    Read CSV/TSV/Excel/Parquet by extension.
    `has_header` controls whether the first row is treated as header.
    """
    ext = os.path.splitext(path)[1].lower()
    header = 0 if has_header else None

    if ext in (".csv",):
        return pd.read_csv(path, header=header)
    if ext in (".tsv", ".tab"):
        return pd.read_csv(path, sep="\t", header=header)
    if ext in (".xlsx", ".xls"):
        # openpyxl handles .xlsx, xlrd no longer supports xls by default; pandas uses xlrd only for .xls if installed.
        # If .xls reading fails, instruct user to install 'xlrd'.
        try:
            return pd.read_excel(path, header=header)
        except ImportError as e:
            raise RuntimeError("Reading .xls requires 'xlrd'. Install with: pip install xlrd") from e
    if ext in (".parquet",):
        # Requires pyarrow or fastparquet
        return pd.read_parquet(path)
    # Fallback: try CSV
    return pd.read_csv(path, header=header)

def _coerce_preview(df: pd.DataFrame, has_header: bool) -> pd.DataFrame:
    """
    Return top 20 rows for preview. If no header, ensure generic column names.
    """
    preview = df.head(20).copy()
    if not has_header:
        # Assign generic names if pandas has numeric columns 0..N-1
        ncols = preview.shape[1]
        preview.columns = [f"Column {i+1}" for i in range(ncols)]
    return preview

def _sample_df(df: pd.DataFrame, mode: str, value: float) -> pd.DataFrame:
    """
    mode: 'rows' or 'percent'
    value: number of rows (int-like) or percent (0-100)
    """
    if df.empty:
        return df

    if mode == "rows":
        n = int(value)
        n = max(0, min(n, len(df)))  # clamp
        if n == 0:
            return df.iloc[0:0]
        return df.sample(n=n, replace=False, random_state=None)
    elif mode == "percent":
        pct = float(value)
        pct = max(0.0, min(pct, 100.0))
        if pct == 0.0:
            return df.iloc[0:0]
        frac = pct / 100.0
        # df.sample(frac=1.0) is allowed; clamp to avoid floating overshoot
        return df.sample(frac=min(frac, 1.0), replace=False, random_state=None)
    else:
        raise ValueError("Unknown sampling mode")

def _save_dataframe_dialog(df: pd.DataFrame, suggested_name: str = "sampled_data") -> Optional[str]:
    """
    Ask user where/how to save. Supports CSV and Excel (xlsx).
    Returns saved path or None if canceled.
    """
    path = filedialog.asksaveasfilename(
        title="Save sampled data",
        defaultextension=".csv",
        initialfile=f"{suggested_name}.csv",
        filetypes=[("CSV", "*.csv"), ("Excel (.xlsx)", "*.xlsx"), ("All files", "*.*")],
    )
    if not path:
        return None

    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".xlsx":
            # Requires openpyxl
            df.to_excel(path, index=False)
        else:
            # default to CSV
            df.to_csv(path, index=False)
    except Exception as e:
        messagebox.showerror("Save failed", f"Could not save file:\n{e}")
        return None
    return path

# ----------------------------
# Dialog
# ----------------------------

class ImportSampleDialog(tk.Toplevel):
    """
    Modal dialog:
      - Choose file
      - Header checkbox
      - Preview (top 20 rows)
      - Sampling controls (rows / percent)
      - OK / Cancel
    After OK, performs sampling and save dialog; closes when done.
    """

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.title("Import & Sample Data")
        self.transient(parent)
        self.grab_set()  # modal

        self.parent = parent
        self.selected_path: Optional[str] = None
        self.df_full: Optional[pd.DataFrame] = None

        # State variables
        self.var_has_header = tk.BooleanVar(value=True)
        self.var_mode = tk.StringVar(value="rows")  # 'rows' or 'percent'
        self.var_rows = tk.StringVar(value="100")
        self.var_percent = tk.StringVar(value="10")

        self._build_ui()
        self._configure_layout()
        self._bind_events()

        # Center on parent
        self.update_idletasks()
        self._center_on_parent()
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}")

    # ---------- UI builders ----------

    def _build_ui(self):
        # File row
        file_frame = ttk.Frame(self)
        file_frame.grid(row=0, column=0, padx=12, pady=(12, 8), sticky="ew")
        self.columnconfigure(0, weight=1)

        ttk.Label(file_frame, text="Selected file:").grid(row=0, column=0, sticky="w")
        self.entry_path = ttk.Entry(file_frame, width=60)
        self.entry_path.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        btn_browse = ttk.Button(file_frame, text="Browse…", command=self._browse_file)
        btn_browse.grid(row=1, column=1, sticky="e")

        file_frame.columnconfigure(0, weight=1)

        # Options row
        opts = ttk.Frame(self)
        opts.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.chk_header = ttk.Checkbutton(
            opts, text="File has header row", variable=self.var_has_header, command=self._refresh_after_header_toggle
        )
        self.chk_header.grid(row=0, column=0, sticky="w")

        # Sampling mode
        mode_frame = ttk.LabelFrame(opts, text="Sampling")
        mode_frame.grid(row=0, column=1, padx=(16, 0), sticky="w")

        self.rb_rows = ttk.Radiobutton(mode_frame, text="By rows", value="rows", variable=self.var_mode, command=self._update_sampling_entry_state)
        self.rb_pct = ttk.Radiobutton(mode_frame, text="By percent", value="percent", variable=self.var_mode, command=self._update_sampling_entry_state)
        self.rb_rows.grid(row=0, column=0, sticky="w")
        self.rb_pct.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.entry_rows = ttk.Entry(mode_frame, width=10, textvariable=self.var_rows)
        self.entry_percent = ttk.Entry(mode_frame, width=10, textvariable=self.var_percent)
        ttk.Label(mode_frame, text="Rows:").grid(row=1, column=0, sticky="w", pady=(6,0))
        self.entry_rows.grid(row=1, column=1, sticky="w", pady=(6,0))
        ttk.Label(mode_frame, text="Percent (0–100):").grid(row=2, column=0, sticky="w", pady=(6,0))
        self.entry_percent.grid(row=2, column=1, sticky="w", pady=(6,0))

        # Preview
        preview_frame = ttk.LabelFrame(self, text="Preview (top 20 rows)")
        preview_frame.grid(row=2, column=0, padx=12, pady=(0, 8), sticky="nsew")
        self.rowconfigure(2, weight=1)

        self.tree = ttk.Treeview(preview_frame, columns=(), show="headings", height=8)
        vsb = ttk.Scrollbar(preview_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(preview_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        # Buttons
        btns = ttk.Frame(self)
        btns.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="e")
        self.btn_cancel = ttk.Button(btns, text="Cancel", command=self._on_cancel)
        self.btn_cancel.grid(row=0, column=0)
        self.btn_ok = ttk.Button(btns, text="OK", command=self._on_ok, state="disabled")
        self.btn_ok.grid(row=0, column=1, padx=(0, 8))


        self._update_sampling_entry_state()

    def _configure_layout(self):
        # A bit of padding for all children
        for child in self.winfo_children():
            try:
                child.grid_configure(pady=2)
            except Exception:
                pass

    def _bind_events(self):
        self.bind("<Return>", lambda e: self._on_ok() if self.btn_ok["state"] == "normal" else None)
        self.bind("<Escape>", lambda e: self._on_cancel())
        # Validate numeric inputs on focus-out
        self.entry_rows.bind("<FocusOut>", lambda e: self._sanitize_rows())
        self.entry_percent.bind("<FocusOut>", lambda e: self._sanitize_percent())

    def _center_on_parent(self):
        self.update_idletasks()
        if self.parent and self.parent.winfo_exists():
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            w = self.winfo_width()
            h = self.winfo_height()
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
            self.geometry(f"+{max(0,x)}+{max(0,y)}")

    # ---------- Event handlers ----------

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select a data file",
            filetypes=FILE_TYPES,
        )
        if not path:
            return
        self.selected_path = path
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, path)
        self._load_dataframe()

    def _load_dataframe(self):
        if not self.selected_path:
            return
        try:
            df = _read_table(self.selected_path, self.var_has_header.get())
        except Exception as e:
            messagebox.showerror("Read error", f"Could not read file:\n{e}")
            self.df_full = None
            self._clear_preview()
            self.btn_ok.config(state="disabled")
            return

        self.df_full = df
        self._update_preview()
        self._update_ok_state()

    def _refresh_after_header_toggle(self):
        """
        Re-read the file with the new header setting to keep preview and sampling consistent.
        """
        if self.selected_path:
            self._load_dataframe()

    def _update_preview(self):
        if self.df_full is None:
            self._clear_preview()
            return

        preview = _coerce_preview(self.df_full, self.var_has_header.get())

        # Rebuild columns
        self.tree["columns"] = []
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
            self.tree.column(col, width=0)

        cols = list(preview.columns.astype(str))
        self.tree["columns"] = cols
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, stretch=True)

        # Clear rows then insert
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)

        for _, row in preview.iterrows():
            values = [row.get(c) for c in cols]
            # Convert lists / objects to string for display
            values = [str(v) if isinstance(v, (list, dict)) else v for v in values]
            self.tree.insert("", "end", values=values)

    def _clear_preview(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        for col in self.tree["columns"]:
            self.tree.heading(col, text="")
        self.tree["columns"] = []

    def _update_ok_state(self):
        valid = self.df_full is not None and not self.df_full.empty
        if valid:
            if self.var_mode.get() == "rows":
                valid = self._sanitize_rows()
            else:
                valid = self._sanitize_percent()
        self.btn_ok.config(state=("normal" if valid else "disabled"))

    def _update_sampling_entry_state(self):
        mode = self.var_mode.get()
        if mode == "rows":
            self.entry_rows.config(state="normal")
            self.entry_percent.config(state="disabled")
        else:
            self.entry_rows.config(state="disabled")
            self.entry_percent.config(state="normal")
        self._update_ok_state()

    def _sanitize_rows(self) -> bool:
        try:
            val = int(self.var_rows.get())
            if val < 0:
                raise ValueError
        except Exception:
            self.var_rows.set("0")
            return False
        return True

    def _sanitize_percent(self) -> bool:
        try:
            val = float(self.var_percent.get())
            if not (0.0 <= val <= 100.0):
                raise ValueError
        except Exception:
            self.var_percent.set("10")
            return False
        return True

    def _on_ok(self):
        if self.df_full is None or self.df_full.empty:
            messagebox.showwarning("No data", "Load a file before continuing.")
            return

        # Validate input again
        mode = self.var_mode.get()
        if mode == "rows":
            if not self._sanitize_rows():
                messagebox.showerror("Invalid input", "Please enter a non-negative integer for rows.")
                return
            sample_value = int(self.var_rows.get())
        else:
            if not self._sanitize_percent():
                messagebox.showerror("Invalid input", "Please enter a percent between 0 and 100.")
                return
            sample_value = float(self.var_percent.get())

        # Perform sampling
        try:
            sampled = _sample_df(self.df_full, mode, sample_value)
        except Exception as e:
            messagebox.showerror("Sampling error", f"Could not sample data:\n{e}")
            return

        # Save dialog
        base = os.path.splitext(os.path.basename(self.selected_path or "sampled_data"))[0]
        save_path = _save_dataframe_dialog(sampled, suggested_name=f"{base}_sample")
        if save_path:
            messagebox.showinfo("Saved", f"Sampled data saved to:\n{save_path}")
            self.destroy()  # close dialog after success

    def _on_cancel(self):
        self.destroy()

# ----------------------------
# Public API
# ----------------------------

def sample_data(parent: tk.Misc):
    """
    Open the Import & Sample dialog as modal.
    Only parameter is a parent tkinter widget (e.g., Tk or Toplevel).
    """
    dlg = ImportSampleDialog(parent)
    parent.wait_window(dlg)
