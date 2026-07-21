"""
Batches table: a single sortable/filterable list of all batch jobs (ongoing and
done merged, distinguished by their "status" column) with a column picker, a
detail pane for the selected batch, and a status-aware right-click menu
(Cancel / Download / Rerun).

Replaces the old two-tab (Ongoing/Done) Treeview pair in main_window.py, which
had no sort, no filter, and always showed every column.
"""

import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk

try:
    from ui_helpers import popup_menu
    from batch_operations import cancel_batch_async, call_batch_download_async, rerun_batch_async
except ImportError:  # fallback when running as a package (ui.*)
    from ui.ui_helpers import popup_menu
    from ui.batch_operations import cancel_batch_async, call_batch_download_async, rerun_batch_async

from batch_processing.batch_method import ONGOING_STATUSES, list_batches
from settings.user_config import get_setting, set_setting

COLUMNS = (
    "id", "status", "type", "dataset", "model", "rows",
    "progress", "created", "temperature", "reasoning", "max_output_tokens",
)
HEADERS = {
    "id": "ID", "status": "Status", "type": "Type", "dataset": "Dataset",
    "model": "Model", "rows": "Rows", "progress": "Progress", "created": "Created",
    "temperature": "Temp", "reasoning": "Reasoning", "max_output_tokens": "Max Tokens",
}
# Shown by default; the rest (id, temperature, reasoning, max_output_tokens) are
# still visible in the detail pane and can be toggled on via "Columns".
DEFAULT_VISIBLE = ["status", "type", "dataset", "model", "rows", "progress", "created"]

COLUMNS_SETTING_KEY = "batches_columns"

# Columns with a small, closed set of values -- rendered as a dropdown of
# whatever values are actually present in the current data (not a hardcoded
# OpenAI status enum, which could drift out of sync).
CHOICE_COLUMNS = ("status", "type", "model", "reasoning")
# Columns that hold a plain number -- rendered as a min/max entry pair.
NUMBER_COLUMNS = ("temperature", "rows", "max_output_tokens")
# Columns that hold a "YYYY-MM-DD HH:MM" timestamp -- rendered as a from/to
# entry pair, compared by date (the ISO-ish format sorts/compares lexically).
DATE_COLUMNS = ("created",)

BLANK_LABEL = "(blank)"


def _sort_key(value: str):
    """Numeric-aware sort key: numbers sort as numbers, blanks sort last,
    everything else sorts as a case-insensitive string."""
    if value == "":
        return (1, "")
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (0, value.casefold())


def _in_range(raw: str, min_s: str, max_s: str) -> bool:
    """Numeric range check for one field. Blank/non-numeric field values fail
    any *active* bound (e.g. filtering temperature excludes reasoning-model
    batches that have none). Malformed min/max entries are simply ignored."""
    min_s, max_s = min_s.strip(), max_s.strip()
    if not min_s and not max_s:
        return True
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return False
    if min_s:
        try:
            if val < float(min_s):
                return False
        except ValueError:
            pass
    if max_s:
        try:
            if val > float(max_s):
                return False
        except ValueError:
            pass
    return True


def _date_in_range(raw: str, from_s: str, to_s: str) -> bool:
    """Date range check against a 'YYYY-MM-DD HH:MM' field value, using only
    its date portion. Malformed from/to entries are ignored (that bound is
    dropped rather than the row)."""
    from_s, to_s = from_s.strip(), to_s.strip()
    if not from_s and not to_s:
        return True
    date_part = raw[:10]

    def _valid(bound: str) -> bool:
        try:
            datetime.strptime(bound, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    if from_s and _valid(from_s) and date_part < from_s:
        return False
    if to_s and _valid(to_s) and date_part > to_s:
        return False
    return True


def _center_over(win: tk.Toplevel, parent: tk.Misc) -> None:
    """Center a just-built Toplevel over the main window instead of wherever
    the window manager defaults to (top-left on Windows)."""
    win.update_idletasks()
    root = parent.winfo_toplevel()
    x = root.winfo_rootx() + (root.winfo_width() - win.winfo_width()) // 2
    y = root.winfo_rooty() + (root.winfo_height() - win.winfo_height()) // 2
    win.geometry(f"+{max(x, 0)}+{max(y, 0)}")


def _ask_rerun_count(parent: tk.Misc) -> "int | None":
    """Small modal dialog: how many times to rerun a batch. Default 1."""
    dlg = tk.Toplevel(parent)
    dlg.title("Rerun Batch")
    dlg.transient(parent.winfo_toplevel())
    dlg.grab_set()
    dlg.resizable(False, False)

    ttk.Label(dlg, text="Number of reruns:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
    count_var = tk.StringVar(value="1")
    spin = ttk.Spinbox(dlg, from_=1, to=50, textvariable=count_var, width=6)
    spin.grid(row=0, column=1, padx=(0, 10), pady=10)
    spin.focus_set()

    result: dict = {"count": None}

    def _ok(_event=None):
        try:
            n = int(count_var.get())
        except ValueError:
            n = 1
        result["count"] = max(1, min(50, n))
        dlg.destroy()

    def _cancel(_event=None):
        dlg.destroy()

    btns = ttk.Frame(dlg)
    btns.grid(row=1, column=0, columnspan=2, pady=(0, 10))
    ttk.Button(btns, text="OK", command=_ok).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="Cancel", command=_cancel).grid(row=0, column=1, padx=4)

    dlg.bind("<Return>", _ok)
    dlg.bind("<Escape>", _cancel)

    _center_over(dlg, parent)
    parent.wait_window(dlg)
    return result["count"]


class BatchesPanel(ttk.Frame):
    """Owns the batches table's data, widgets, and actions."""

    def __init__(self, parent: tk.Misc):
        super().__init__(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._rows: list[dict] = []          # full cache from the last refresh
        self._by_id: dict[str, dict] = {}    # batch id -> row dict, rebuilt each render
        self._sort_col: str | None = None
        self._sort_reverse = False
        self._visible = set(get_setting(COLUMNS_SETTING_KEY, DEFAULT_VISIBLE))

        self._choice_vars: dict[str, tk.StringVar] = {}
        self._choice_combos: dict[str, ttk.Combobox] = {}
        self._range_vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}
        self._date_vars: dict[str, tuple[tk.StringVar, tk.StringVar]] = {}

        self._build_toolbar()
        self._build_body()

    # ----- construction -----------------------------------------------

    def _build_toolbar(self):
        row1 = ttk.Frame(self)
        row1.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        row2 = ttk.Frame(self)
        row2.grid(row=1, column=0, sticky="ew", pady=(0, 6))

        # Row 1: free-text search, then a dropdown per small-closed-set column.
        ttk.Label(row1, text="Search:").pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._render())
        ttk.Entry(row1, textvariable=self._search_var, width=16).pack(side="left", padx=(4, 0))

        for col in CHOICE_COLUMNS:
            self._add_choice_control(row1, col)

        columns_btn = ttk.Menubutton(row1, text="Columns ▾")
        columns_btn.pack(side="right")
        self._columns_menu = tk.Menu(columns_btn, tearoff=False)
        columns_btn["menu"] = self._columns_menu
        self._column_vars: dict[str, tk.BooleanVar] = {}
        for col in COLUMNS:
            var = tk.BooleanVar(value=col in self._visible)
            self._column_vars[col] = var
            self._columns_menu.add_checkbutton(
                label=HEADERS[col], variable=var,
                command=lambda c=col: self._on_column_toggle(c),
            )

        # Row 2: a from/to entry pair per date column, min/max per number
        # column, and a way to reset everything at once.
        for col in DATE_COLUMNS:
            self._add_range_control(row2, col, f"{HEADERS[col]} (YYYY-MM-DD):", self._date_vars)
        for col in NUMBER_COLUMNS:
            self._add_range_control(row2, col, f"{HEADERS[col]}:", self._range_vars)

        ttk.Button(row2, text="Clear Filters", command=self._clear_filters).pack(side="right")

    def _add_choice_control(self, parent, col: str):
        ttk.Label(parent, text=f"{HEADERS[col]}:").pack(side="left", padx=(10, 2))
        var = tk.StringVar(value="All")
        combo = ttk.Combobox(parent, textvariable=var, state="readonly", width=13, values=["All"])
        combo.pack(side="left")
        # A trace (not just <<ComboboxSelected>>) so any programmatic change
        # -- e.g. _refresh_choice_options resetting a stale selection --
        # re-renders too, not just direct user picks.
        var.trace_add("write", lambda *_: self._render())
        self._choice_vars[col] = var
        self._choice_combos[col] = combo

    def _add_range_control(self, parent, col: str, label: str, store: dict):
        ttk.Label(parent, text=label).pack(side="left", padx=(10, 2))
        low, high = tk.StringVar(), tk.StringVar()
        ttk.Entry(parent, textvariable=low, width=9).pack(side="left")
        ttk.Label(parent, text="–").pack(side="left", padx=2)
        ttk.Entry(parent, textvariable=high, width=9).pack(side="left")
        low.trace_add("write", lambda *_: self._render())
        high.trace_add("write", lambda *_: self._render())
        store[col] = (low, high)

    def _build_body(self):
        body = ttk.PanedWindow(self, orient="horizontal")
        body.grid(row=2, column=0, sticky="nsew")

        tree_frame = ttk.Frame(body)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", height=12)
        for col in COLUMNS:
            self.tree.heading(col, text=HEADERS[col], command=lambda c=col: self._sort_by(c))
            self.tree.column(col, anchor="w", stretch=True, width=90, minwidth=40)
        self.tree["displaycolumns"] = self._displaycolumns()

        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.tree.bind("<<TreeviewSelect>>", lambda e: self._update_detail())
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Control-Button-1>", self._on_right_click)
        # Redistribute column widths to fill the available space whenever the
        # tree is resized (window resize, pane drag) -- ttk's own stretch
        # doesn't recompute this on its own after displaycolumns changes.
        self.tree.bind("<Configure>", self._autosize_columns)

        body.add(tree_frame, weight=3)

        self._detail_frame = ttk.Frame(body, padding=(12, 0))
        body.add(self._detail_frame, weight=1)
        self._detail_labels: dict[str, ttk.Label] = {}
        for i, col in enumerate(COLUMNS):
            ttk.Label(self._detail_frame, text=f"{HEADERS[col]}:", font=("Segoe UI", 9, "bold")).grid(
                row=i, column=0, sticky="ne", pady=2)
            value_lbl = ttk.Label(self._detail_frame, text="", wraplength=220, justify="left")
            value_lbl.grid(row=i, column=1, sticky="nw", padx=(6, 0), pady=2)
            self._detail_labels[col] = value_lbl

    def _displaycolumns(self):
        return tuple(c for c in COLUMNS if c in self._visible)

    def _autosize_columns(self, event=None):
        """Spread the visible columns evenly across the tree's current width."""
        cols = self.tree["displaycolumns"] or COLUMNS
        total = self.tree.winfo_width()
        if total <= 1:  # not yet realized (e.g. during initial construction)
            return
        width = max(total // len(cols), 40)
        for c in cols:
            self.tree.column(c, width=width, stretch=True)

    # ----- data loading --------------------------------------------------

    def refresh(self):
        """Fetch batches from the API on a background thread, then repopulate."""
        def _worker():
            try:
                rows = list_batches()
                self.after(0, lambda: self._set_rows(rows))
            except Exception as error:
                from tkinter import messagebox
                self.after(0, lambda: messagebox.showerror("Refresh Error", str(error)))
        threading.Thread(target=_worker, daemon=True).start()

    def _set_rows(self, rows: list[dict]):
        self._rows = rows
        self._refresh_choice_options()
        self._render()

    def _distinct_options(self, col: str) -> list[str]:
        values = {row.get(col, "") for row in self._rows}
        options = sorted(v for v in values if v != "")
        if "" in values:
            options.append(BLANK_LABEL)
        return ["All"] + options

    def _refresh_choice_options(self):
        """Repopulate each dropdown from the data actually on hand, so it
        always reflects real statuses/models/etc. rather than a guessed list.
        Resets a selection that no longer has any matching rows."""
        for col, combo in self._choice_combos.items():
            options = self._distinct_options(col)
            combo["values"] = options
            if self._choice_vars[col].get() not in options:
                self._choice_vars[col].set("All")

    # ----- filtering: search text, choice dropdowns, numeric/date ranges ---

    def _passes_filters(self, row: dict) -> bool:
        search = self._search_var.get().strip().lower()
        if search and search not in " ".join(str(v) for v in row.values()).lower():
            return False

        for col, var in self._choice_vars.items():
            selected = var.get()
            if selected and selected != "All":
                target = "" if selected == BLANK_LABEL else selected
                if row.get(col, "") != target:
                    return False

        for col, (min_var, max_var) in self._range_vars.items():
            if not _in_range(str(row.get(col, "")), min_var.get(), max_var.get()):
                return False

        for col, (from_var, to_var) in self._date_vars.items():
            if not _date_in_range(str(row.get(col, "")), from_var.get(), to_var.get()):
                return False

        return True

    def _clear_filters(self):
        self._search_var.set("")
        for var in self._choice_vars.values():
            var.set("All")
        for low, high in list(self._range_vars.values()) + list(self._date_vars.values()):
            low.set("")
            high.set("")

    # ----- rendering: filter + sort, then repopulate the tree ------------

    def _render(self):
        rows = [r for r in self._rows if self._passes_filters(r)]

        if self._sort_col:
            rows = sorted(rows, key=lambda r: _sort_key(str(r.get(self._sort_col, ""))),
                          reverse=self._sort_reverse)

        selected = self.tree.selection()
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        self._by_id = {}
        for row in rows:
            self.tree.insert("", "end", iid=row["id"], values=[row.get(c, "") for c in COLUMNS])
            self._by_id[row["id"]] = row

        if selected and selected[0] in self._by_id:
            self.tree.selection_set(selected[0])
        self._update_detail()

    def _sort_by(self, col: str):
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col, self._sort_reverse = col, False
        self._render()

    def _on_column_toggle(self, col: str):
        if self._column_vars[col].get():
            self._visible.add(col)
        else:
            self._visible.discard(col)
        self.tree["displaycolumns"] = self._displaycolumns()
        self._autosize_columns()
        set_setting(COLUMNS_SETTING_KEY, [c for c in COLUMNS if c in self._visible])

    # ----- detail pane -----------------------------------------------------

    def _update_detail(self):
        sel = self.tree.selection()
        row = self._by_id.get(sel[0]) if sel else None
        for col, lbl in self._detail_labels.items():
            lbl.config(text=(row.get(col, "") or "—") if row else "")

    # ----- right-click menu: Rerun always, Cancel/Download by status -------

    def _on_right_click(self, event):
        iid = self.tree.identify_row(event.y)
        row = self._by_id.get(iid)
        if row is None:
            return

        root = self.winfo_toplevel()
        menu = tk.Menu(self, tearoff=False)
        menu.add_command(label="Rerun…", command=lambda: self._on_rerun(root, row["id"]))
        if row["status"] in ONGOING_STATUSES:
            menu.add_command(label="Cancel", command=lambda: cancel_batch_async(root, row["id"]))
        elif row["status"] == "completed":
            menu.add_command(label="Download", command=lambda: call_batch_download_async(root, row["id"]))

        popup_menu(event, self.tree, menu)

    def _on_rerun(self, root, batch_id: str):
        count = _ask_rerun_count(self)
        if not count:
            return
        rerun_batch_async(root, batch_id, count)
