"""
Task Builder: the flexible UI that replaces the six hardcoded LLM tools
(single/multi/keyword x batch/live).

Import one table, write a prompt with {column} / {list_name} placeholders,
define named Lists (typed or imported), define output fields (Choice /
Multi-choice bind to a List, so the same values shown in the prompt are the
ones enforced on the output), pick which columns carry through to the result
untouched, then Run Live or Submit Batch.
"""

from __future__ import annotations

import json
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import pandas as pd

from batch_processing import batch_method
from core.task import (
    DEFAULT_MODEL,
    FieldType,
    ListFormat,
    OutputField,
    Task,
    TaskList,
    TaskValidationError,
    is_reasoning_model,
    render_prompt,
    validate_task,
)
from file_handling.data_import import import_data, load_table
from live_processing.task_live import run_task_live
from settings.models_registry import get_models
from ui.drag_drop import enable_file_drop
from ui.ui_utils import center_window, populate_treeview

FIELD_TYPES: list[FieldType] = ["choice", "multi_choice", "text_list", "free_text", "number", "yes_no"]
LIST_FORMATS: list[ListFormat] = ["comma", "hyphen", "space", "newline"]
REASONING_EFFORTS = ["", "low", "medium", "high"]


def _parse_optional_float(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_optional_int(s: str) -> int | None:
    s = s.strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None

COLUMN_PILL_BG = "#dbe9ff"
LIST_PILL_BG = "#d9f2df"
UNKNOWN_PLACEHOLDER_BG = "#ffd6d6"


def open_task_builder(parent: tk.Misc, preset_task: Task | None = None) -> None:
    TaskBuilder(parent, preset_task)


# ---------------------------------------------------------------------------
# Small reusable widgets
# ---------------------------------------------------------------------------

class _ScrollableFrame(ttk.Frame):
    """A vertically scrollable frame -- the builder has more sections than
    fit in a fixed window; content goes in `.body`."""

    def __init__(self, master):
        super().__init__(master)
        canvas = tk.Canvas(self, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.body = ttk.Frame(canvas)
        self.body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.body, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        def _on_enter(_):
            canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        def _on_leave(_):
            canvas.unbind_all("<MouseWheel>")

        canvas.bind("<Enter>", _on_enter)
        canvas.bind("<Leave>", _on_leave)


class _PillRow(ttk.Frame):
    """A horizontally-scrollable row of clickable/draggable placeholder pills.
    Click inserts at the active text widget's cursor; dragging onto a text
    widget inserts at the drop point."""

    def __init__(self, master, on_pick):
        super().__init__(master)
        self.on_pick = on_pick
        self.canvas = tk.Canvas(self, height=34, highlightthickness=0)
        self.inner = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hsb.set)
        self.canvas.grid(row=0, column=0, sticky="ew")
        hsb.grid(row=1, column=0, sticky="ew")
        self.columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._on_inner_configure)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox(self.window_id))

    def set_pills(self, items: list[tuple[str, str]]):
        """items: list of (name, kind) where kind in {'column', 'list'}."""
        for w in self.inner.winfo_children():
            w.destroy()
        if not items:
            ttk.Label(self.inner, text="(none yet)", foreground="#888").grid(row=0, column=0, padx=6, pady=6)
        for i, (name, kind) in enumerate(items):
            bg = COLUMN_PILL_BG if kind == "column" else LIST_PILL_BG
            pill = tk.Label(self.inner, text=name, bg=bg, padx=8, pady=3, relief="raised", borderwidth=1, cursor="hand2")
            pill.grid(row=0, column=i, padx=4, pady=4)
            pill.bind("<ButtonRelease-1>", lambda e, n=name: self._on_release(e, n))
        self.inner.update_idletasks()
        self._on_inner_configure()

    def _on_release(self, event, name: str):
        target = event.widget.winfo_containing(event.x_root, event.y_root)
        self.on_pick(name, target)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class TaskBuilder(tk.Toplevel):
    def __init__(self, parent: tk.Misc, preset_task: Task | None = None):
        super().__init__(parent)
        self.title("Task Builder")
        self.geometry("1000x760")
        self.transient(parent)

        # ----- state -----
        self.df: "pd.DataFrame | None" = None
        self.columns: list[str] = []
        self.current_file: str = ""
        self.lists: dict[str, TaskList] = {}
        self.carry_vars: dict[str, tk.BooleanVar] = {}
        self._field_rows: list[dict] = []
        self._active_text_widget: tk.Text | None = None
        self.preview_mode = False
        self.preview_row_idx = 0

        outer = _ScrollableFrame(self)
        outer.grid(row=0, column=0, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        root = outer.body
        root.columnconfigure(0, weight=1)

        self._build_input_section(root)
        self._build_prompt_section(root)
        self._build_lists_section(root)
        self._build_output_fields_section(root)
        self._build_carry_section(root)
        self._build_model_section(root)
        self._build_run_section(root)

        if preset_task is not None:
            self._apply_task(preset_task)

        center_window(self, 1000, 760)

    # -----------------------------------------------------------------
    # Input section: import a table, show column pills, optional preview
    # -----------------------------------------------------------------
    def _build_input_section(self, root):
        frm = ttk.LabelFrame(root, text="Input", padding=10)
        frm.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="File:").grid(row=0, column=0, sticky="w")
        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(frm, textvariable=self.file_var)
        file_entry.grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(frm, text="Browse…", command=self._on_browse).grid(row=0, column=2)
        if enable_file_drop is not None:
            enable_file_drop(file_entry, self._load_file, [".csv", ".tsv", ".txt", ".xlsx", ".xls"])

        opts = ttk.Frame(frm)
        opts.grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.has_headers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts, text="File has headers", variable=self.has_headers_var,
                         command=self._reload_current_file).grid(row=0, column=0, padx=(0, 16))
        self.show_preview_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text="Show preview (top 5 rows)", variable=self.show_preview_var,
                         command=self._refresh_preview_table).grid(row=0, column=1)

        ttk.Label(frm, text="Columns (click to insert, or drag into the prompt):").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(8, 2))
        self.column_pills = _PillRow(frm, self._insert_placeholder)
        self.column_pills.grid(row=3, column=0, columnspan=3, sticky="ew")

        self.preview_tree = ttk.Treeview(frm, show="headings", height=5)
        self.preview_tree.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.preview_tree.grid_remove()

    def _on_browse(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Import Data",
            filetypes=[
                ("All supported", "*.csv *.tsv *.txt *.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.file_var.set(path)
            self._load_file(path)

    def _reload_current_file(self):
        if self.file_var.get().strip():
            self._load_file(self.file_var.get().strip())

    def _load_file(self, path: str):
        try:
            header, data = load_table(path, self.has_headers_var.get())
        except Exception as e:
            messagebox.showerror("Import Error", str(e), parent=self)
            return
        if not header:
            messagebox.showerror("Import Error", "The file appears to have no data.", parent=self)
            return

        self.file_var.set(path)
        self.current_file = path
        self.df = pd.DataFrame(data, columns=header)
        self.columns = header
        self.carry_vars = {c: tk.BooleanVar(value=True) for c in header}

        self._refresh_column_pills()
        self._refresh_carry_ui()
        self._refresh_preview_table()
        self._highlight_placeholders(self.prompt_edit)
        if self.system_var.get():
            self._highlight_placeholders(self.system_edit)

    def _refresh_preview_table(self):
        if not self.show_preview_var.get() or self.df is None:
            self.preview_tree.grid_remove()
            return
        rows = [tuple(r) for r in self.df.head(5).itertuples(index=False, name=None)]
        populate_treeview(self.preview_tree, tuple(self.columns), rows)
        self.preview_tree.grid()

    # -----------------------------------------------------------------
    # Prompt section: editor + system box + edit/preview toggle
    # -----------------------------------------------------------------
    def _build_prompt_section(self, root):
        frm = ttk.LabelFrame(root, text="Prompt", padding=10)
        frm.grid(row=1, column=0, sticky="ew", padx=10, pady=6)
        frm.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(frm)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        ttk.Label(toolbar, text="Use {column} / {list} placeholders. Everything else is sent as-is.").grid(
            row=0, column=0, sticky="w")
        self.preview_toggle_btn = ttk.Button(toolbar, text="Preview", command=self._toggle_preview)
        self.preview_toggle_btn.grid(row=0, column=1, sticky="e")

        self.prompt_container = ttk.Frame(frm)
        self.prompt_container.grid(row=1, column=0, sticky="nsew", pady=(4, 4))
        self.prompt_container.columnconfigure(0, weight=1)

        self.prompt_edit = tk.Text(self.prompt_container, height=8, wrap="word")
        self.prompt_edit.grid(row=0, column=0, sticky="nsew")
        self._configure_placeholder_tags(self.prompt_edit)
        self.prompt_edit.bind("<KeyRelease>", lambda e: self._highlight_placeholders(self.prompt_edit))
        self.prompt_edit.bind("<FocusIn>", lambda e: setattr(self, "_active_text_widget", self.prompt_edit))

        self.prompt_preview = tk.Text(self.prompt_container, height=8, wrap="word", state="disabled", bg="#f5f5f5")
        self.prompt_preview.grid(row=0, column=0, sticky="nsew")
        self.prompt_preview.grid_remove()

        self.preview_stepper = ttk.Frame(frm)
        self.preview_stepper.grid(row=2, column=0, sticky="w")
        ttk.Button(self.preview_stepper, text="◀", width=3, command=lambda: self._step_preview(-1)).grid(row=0, column=0)
        self.row_stepper_label = ttk.Label(self.preview_stepper, text="Row 0 of 0")
        self.row_stepper_label.grid(row=0, column=1, padx=8)
        ttk.Button(self.preview_stepper, text="▶", width=3, command=lambda: self._step_preview(1)).grid(row=0, column=2)
        self.preview_stepper.grid_remove()

        # System instructions -- hidden by default (progressive disclosure)
        self.system_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="+ System instructions (advanced)", variable=self.system_var,
                         command=self._toggle_system_box).grid(row=3, column=0, sticky="w", pady=(4, 0))

        self.system_frame = ttk.Frame(frm)
        self.system_frame.columnconfigure(0, weight=1)
        self.system_edit = tk.Text(self.system_frame, height=3, wrap="word")
        self.system_edit.grid(row=0, column=0, sticky="ew")
        self._configure_placeholder_tags(self.system_edit)
        self.system_edit.bind("<KeyRelease>", lambda e: self._highlight_placeholders(self.system_edit))
        self.system_edit.bind("<FocusIn>", lambda e: setattr(self, "_active_text_widget", self.system_edit))
        self.system_frame.grid(row=4, column=0, sticky="ew")
        self.system_frame.grid_remove()

    def _configure_placeholder_tags(self, widget: tk.Text):
        widget.tag_configure("column_ph", background=COLUMN_PILL_BG)
        widget.tag_configure("list_ph", background=LIST_PILL_BG)
        widget.tag_configure("unknown_ph", background=UNKNOWN_PLACEHOLDER_BG)

    def _highlight_placeholders(self, widget: tk.Text):
        for tag in ("column_ph", "list_ph", "unknown_ph"):
            widget.tag_remove(tag, "1.0", "end")
        text = widget.get("1.0", "end-1c")
        for m in re.finditer(r"\{([^{}]+)\}", text):
            name = m.group(1)
            start, end = f"1.0+{m.start()}c", f"1.0+{m.end()}c"
            if name in self.lists:
                widget.tag_add("list_ph", start, end)
            elif name in self.columns:
                widget.tag_add("column_ph", start, end)
            else:
                widget.tag_add("unknown_ph", start, end)

    def _toggle_system_box(self):
        if self.system_var.get():
            self.system_frame.grid()
        else:
            self.system_frame.grid_remove()

    def _insert_placeholder(self, name: str, drop_target: tk.Widget | None = None):
        if self.preview_mode:
            return
        widget = drop_target if drop_target in (self.prompt_edit, self.system_edit) else self._active_text_widget
        if widget is None:
            widget = self.prompt_edit
        if widget is self.system_edit and not self.system_var.get():
            self.system_var.set(True)
            self._toggle_system_box()
        if drop_target is widget:
            x = widget.winfo_pointerx() - widget.winfo_rootx()
            y = widget.winfo_pointery() - widget.winfo_rooty()
            widget.mark_set("insert", widget.index(f"@{x},{y}"))
        widget.insert("insert", f"{{{name}}}")
        widget.focus_set()
        self._highlight_placeholders(widget)

    def _toggle_preview(self):
        self.preview_mode = not self.preview_mode
        if self.preview_mode:
            self.prompt_edit.grid_remove()
            self.prompt_preview.grid()
            self.preview_stepper.grid()
            self.preview_toggle_btn.config(text="Edit")
            self.preview_row_idx = 0
            self._render_preview_row()
        else:
            self.prompt_preview.grid_remove()
            self.preview_stepper.grid_remove()
            self.prompt_edit.grid()
            self.preview_toggle_btn.config(text="Preview")

    def _step_preview(self, delta: int):
        if self.df is None or len(self.df) == 0:
            return
        self.preview_row_idx = max(0, min(self.preview_row_idx + delta, len(self.df) - 1))
        self._render_preview_row()

    def _render_preview_row(self):
        self.prompt_preview.config(state="normal")
        self.prompt_preview.delete("1.0", "end")
        if self.df is None or len(self.df) == 0:
            self.prompt_preview.insert("1.0", "(Import data to preview the rendered prompt.)")
            self.row_stepper_label.config(text="Row 0 of 0")
        else:
            preview_task = Task(prompt=self.prompt_edit.get("1.0", "end-1c"), lists=dict(self.lists))
            row = self.df.iloc[self.preview_row_idx].to_dict()
            parts = []
            if self.system_var.get():
                try:
                    parts.append("[SYSTEM]\n" + render_prompt(preview_task, row, text=self.system_edit.get("1.0", "end-1c")))
                except TaskValidationError as e:
                    parts.append(f"[SYSTEM] (cannot render: {e})")
            try:
                parts.append("[USER]\n" + render_prompt(preview_task, row))
            except TaskValidationError as e:
                parts.append(f"[USER] (cannot render: {e})")
            self.prompt_preview.insert("1.0", "\n\n".join(parts))
            self.row_stepper_label.config(text=f"Row {self.preview_row_idx + 1} of {len(self.df)}")
        self.prompt_preview.config(state="disabled")

    # -----------------------------------------------------------------
    # Lists section: named constant value sets, used in prompt + output
    # -----------------------------------------------------------------
    def _build_lists_section(self, root):
        frm = ttk.LabelFrame(root, text="Lists", padding=10)
        frm.grid(row=2, column=0, sticky="ew", padx=10, pady=6)
        frm.columnconfigure(0, weight=1)

        self.lists_rows_frame = ttk.Frame(frm)
        self.lists_rows_frame.grid(row=0, column=0, sticky="ew")
        ttk.Button(frm, text="+ Add List", command=self._on_add_list).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._list_row_widgets: dict[str, dict] = {}
        self._refresh_lists_ui()

    def _on_add_list(self):
        name = simpledialog.askstring("New List", "List name:", parent=self)
        if not name:
            return
        name = name.strip()
        if not name or name in self.lists:
            messagebox.showerror("Invalid Name", "Enter a unique, non-empty list name.", parent=self)
            return
        self.lists[name] = TaskList(values=[], format="comma")
        self._refresh_lists_ui()

    def _refresh_lists_ui(self):
        for w in self.lists_rows_frame.winfo_children():
            w.destroy()
        self._list_row_widgets.clear()

        for r, name in enumerate(self.lists):
            lst = self.lists[name]
            ttk.Label(self.lists_rows_frame, text=name, width=14).grid(row=r, column=0, sticky="w", padx=(0, 6), pady=3)

            values_var = tk.StringVar(value=", ".join(lst.values))
            entry = ttk.Entry(self.lists_rows_frame, textvariable=values_var, width=36)
            entry.grid(row=r, column=1, sticky="ew", padx=4)

            ttk.Button(self.lists_rows_frame, text="Import…", width=9,
                       command=lambda n=name: self._on_import_list(n)).grid(row=r, column=2, padx=4)

            format_var = tk.StringVar(value=lst.format)
            fmt_cmb = ttk.Combobox(self.lists_rows_frame, textvariable=format_var, values=LIST_FORMATS,
                                    state="readonly", width=8)
            fmt_cmb.grid(row=r, column=3, padx=4)

            preview_var = tk.StringVar()
            ttk.Label(self.lists_rows_frame, textvariable=preview_var, foreground="#555", width=28).grid(
                row=r, column=4, sticky="w", padx=4)

            ttk.Button(self.lists_rows_frame, text="Remove", width=8,
                       command=lambda n=name: self._on_remove_list(n)).grid(row=r, column=5, padx=4)

            def _sync(*_args, n=name, vv=values_var, fv=format_var, pv=preview_var):
                values = [v.strip() for v in vv.get().split(",") if v.strip()]
                new_list = TaskList(values=values, format=fv.get())
                self.lists[n] = new_list
                pv.set(new_list.render() if values else "(empty)")
                self._highlight_placeholders(self.prompt_edit)
                if self.system_var.get():
                    self._highlight_placeholders(self.system_edit)

            values_var.trace_add("write", _sync)
            format_var.trace_add("write", _sync)
            _sync()

            self._list_row_widgets[name] = {"values_var": values_var, "format_var": format_var}

        self.lists_rows_frame.columnconfigure(1, weight=1)
        self._refresh_column_pills()
        self._refresh_output_field_list_choices()

    def _on_import_list(self, name: str):
        result = import_data(self, f"Import values for list '{name}'")
        if result is None:
            return
        values, _nickname = result
        self._list_row_widgets[name]["values_var"].set(", ".join(values))

    def _on_remove_list(self, name: str):
        self.lists.pop(name, None)
        self._refresh_lists_ui()

    # -----------------------------------------------------------------
    # Column + list pill palette (shared between Input and Lists sections)
    # -----------------------------------------------------------------
    def _refresh_column_pills(self):
        items = [(c, "column") for c in self.columns] + [(n, "list") for n in self.lists]
        self.column_pills.set_pills(items)

    # -----------------------------------------------------------------
    # Output fields section
    # -----------------------------------------------------------------
    def _build_output_fields_section(self, root):
        frm = ttk.LabelFrame(root, text="Output Fields", padding=10)
        frm.grid(row=3, column=0, sticky="ew", padx=10, pady=6)
        frm.columnconfigure(0, weight=1)

        self.fields_rows_frame = ttk.Frame(frm)
        self.fields_rows_frame.grid(row=0, column=0, sticky="ew")
        ttk.Button(frm, text="+ Add Field", command=self._on_add_field).grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._refresh_output_fields_ui()

    def _on_add_field(self):
        self._field_rows.append({
            "name_var": tk.StringVar(value=f"field{len(self._field_rows) + 1}"),
            "type_var": tk.StringVar(value="free_text"),
            "list_var": tk.StringVar(value=""),
        })
        self._refresh_output_fields_ui()

    def _refresh_output_fields_ui(self):
        if not hasattr(self, "fields_rows_frame"):
            return  # Lists section builds before Output Fields section exists yet
        for w in self.fields_rows_frame.winfo_children():
            w.destroy()

        for r, row in enumerate(self._field_rows):
            ttk.Entry(self.fields_rows_frame, textvariable=row["name_var"], width=16).grid(
                row=r, column=0, sticky="w", padx=(0, 6), pady=3)

            type_cmb = ttk.Combobox(self.fields_rows_frame, textvariable=row["type_var"], values=FIELD_TYPES,
                                     state="readonly", width=13)
            type_cmb.grid(row=r, column=1, padx=4)

            list_cmb = ttk.Combobox(self.fields_rows_frame, textvariable=row["list_var"],
                                     values=list(self.lists), state="readonly", width=14)
            list_cmb.grid(row=r, column=2, padx=4)

            def _sync_list_visibility(_e=None, t=row["type_var"], w=list_cmb):
                w.configure(state="readonly" if t.get() in ("choice", "multi_choice") else "disabled")

            type_cmb.bind("<<ComboboxSelected>>", _sync_list_visibility)
            _sync_list_visibility()

            ttk.Button(self.fields_rows_frame, text="Remove", width=8,
                       command=lambda i=r: self._on_remove_field(i)).grid(row=r, column=3, padx=4)

        self.fields_rows_frame.columnconfigure(0, weight=1)

    def _refresh_output_field_list_choices(self):
        # Rebuild so each row's list combobox reflects current list names.
        self._refresh_output_fields_ui()

    def _on_remove_field(self, index: int):
        del self._field_rows[index]
        self._refresh_output_fields_ui()

    def _collect_output_fields(self) -> list[OutputField]:
        fields = []
        for row in self._field_rows:
            name = row["name_var"].get().strip()
            if not name:
                continue
            ftype = row["type_var"].get()
            list_ref = row["list_var"].get().strip() or None
            if ftype not in ("choice", "multi_choice"):
                list_ref = None
            fields.append(OutputField(name=name, type=ftype, list_ref=list_ref))
        return fields

    # -----------------------------------------------------------------
    # Carry-to-output section
    # -----------------------------------------------------------------
    def _build_carry_section(self, root):
        frm = ttk.LabelFrame(root, text="Carry to Output", padding=10)
        frm.grid(row=4, column=0, sticky="ew", padx=10, pady=6)
        ttk.Label(frm, text="Input columns to include untouched in the output CSV "
                             "(e.g. an existing ID column) -- independent of whether "
                             "they're used in the prompt.").grid(row=0, column=0, sticky="w")
        self.carry_checks_frame = ttk.Frame(frm)
        self.carry_checks_frame.grid(row=1, column=0, sticky="ew", pady=(6, 0))

    def _refresh_carry_ui(self):
        for w in self.carry_checks_frame.winfo_children():
            w.destroy()
        for i, (col, var) in enumerate(self.carry_vars.items()):
            row, colpos = divmod(i, 5)
            ttk.Checkbutton(self.carry_checks_frame, text=col, variable=var).grid(
                row=row, column=colpos, sticky="w", padx=6, pady=2)

    # -----------------------------------------------------------------
    # Model: which model runs this task, and its inference params. Standard
    # models take temperature; reasoning models (o1/o3/o4/gpt-5) take a
    # reasoning effort instead -- the API rejects whichever doesn't apply, so
    # the UI shows only the one that does.
    # -----------------------------------------------------------------
    def _build_model_section(self, root):
        frm = ttk.LabelFrame(root, text="Model", padding=10)
        frm.grid(row=5, column=0, sticky="ew", padx=10, pady=6)

        ttk.Label(frm, text="Model:").grid(row=0, column=0, sticky="w")
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        self.cmb_model = ttk.Combobox(
            frm, textvariable=self.model_var, values=get_models(), state="readonly", width=28)
        self.cmb_model.grid(row=0, column=1, sticky="w", padx=6)
        self.cmb_model.bind("<<ComboboxSelected>>", lambda e: self._refresh_model_params_visibility())

        ttk.Label(frm, text="Max output tokens:").grid(row=0, column=2, sticky="w", padx=(16, 0))
        self.max_tokens_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.max_tokens_var, width=10).grid(row=0, column=3, sticky="w", padx=6)

        self.temp_label = ttk.Label(frm, text="Temperature:")
        self.temperature_var = tk.StringVar()
        self.temp_entry = ttk.Entry(frm, textvariable=self.temperature_var, width=10)

        self.reasoning_label = ttk.Label(frm, text="Reasoning effort:")
        self.reasoning_var = tk.StringVar()
        self.reasoning_combo = ttk.Combobox(
            frm, textvariable=self.reasoning_var, values=REASONING_EFFORTS, state="readonly", width=10)

        self._refresh_model_params_visibility()

    def _refresh_model_params_visibility(self):
        if is_reasoning_model(self.model_var.get()):
            self.temp_label.grid_remove()
            self.temp_entry.grid_remove()
            self.reasoning_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
            self.reasoning_combo.grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))
        else:
            self.reasoning_label.grid_remove()
            self.reasoning_combo.grid_remove()
            self.temp_label.grid(row=1, column=0, sticky="w", pady=(6, 0))
            self.temp_entry.grid(row=1, column=1, sticky="w", padx=6, pady=(6, 0))

    # -----------------------------------------------------------------
    # Run / Save / Load
    # -----------------------------------------------------------------
    def _build_run_section(self, root):
        frm = ttk.Frame(root, padding=10)
        frm.grid(row=6, column=0, sticky="ew", padx=10, pady=(6, 10))
        ttk.Button(frm, text="Load Task…", command=self._on_load_task).grid(row=0, column=0, padx=4)
        ttk.Button(frm, text="Save Task…", command=self._on_save_task).grid(row=0, column=1, padx=4)
        ttk.Button(frm, text="Run Live", command=self._on_run_live).grid(row=0, column=2, padx=(24, 4))
        ttk.Button(frm, text="Submit Batch", style="Accent.TButton", command=self._on_submit_batch).grid(
            row=0, column=3, padx=4)

    def _collect_task(self) -> Task:
        prompt = self.prompt_edit.get("1.0", "end-1c")
        system = self.system_edit.get("1.0", "end-1c").strip() if self.system_var.get() else None
        carry_columns = [c for c, v in self.carry_vars.items() if v.get()]
        return Task(
            prompt=prompt,
            system=system or None,
            lists=dict(self.lists),
            output_fields=self._collect_output_fields(),
            carry_columns=carry_columns,
            model=self.model_var.get().strip() or DEFAULT_MODEL,
            temperature=_parse_optional_float(self.temperature_var.get()),
            reasoning_effort=self.reasoning_var.get().strip() or None,
            max_output_tokens=_parse_optional_int(self.max_tokens_var.get()),
        )

    def _validate_and_collect(self) -> Task | None:
        if self.df is None:
            messagebox.showerror("Task Error", "Import data first.", parent=self)
            return None
        task = self._collect_task()
        try:
            validate_task(task, self.columns)
        except TaskValidationError as e:
            messagebox.showerror("Task Error", str(e), parent=self)
            return None
        return task

    def _on_run_live(self):
        task = self._validate_and_collect()
        if task is None:
            return
        run_task_live(self, task, self.df)

    def _on_submit_batch(self):
        task = self._validate_and_collect()
        if task is None:
            return
        df = self.df
        dataset = Path(self.current_file).stem if self.current_file else None

        def _worker():
            try:
                batch_method.send_batch(task, df, dataset=dataset)
                self.after(0, self._on_batch_submitted)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Batch Error", str(e), parent=self))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_batch_submitted(self):
        messagebox.showinfo("Batch Submitted", "Batch job submitted. Check the main window's Batches list.", parent=self)
        try:
            from ui.batch_operations import refresh_batches_async
            refresh_batches_async(self.master)
        except Exception:
            pass

    def _on_save_task(self):
        task = self._collect_task()
        path = filedialog.asksaveasfilename(
            parent=self, title="Save Task", defaultextension=".json",
            filetypes=[("Task JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            Path(path).write_text(json.dumps(task.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
            messagebox.showinfo("Task Saved", f"Saved to {path}", parent=self)
        except OSError as e:
            messagebox.showerror("Save Error", str(e), parent=self)

    def _on_load_task(self):
        path = filedialog.askopenfilename(
            parent=self, title="Load Task",
            filetypes=[("Task JSON", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            task = Task.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError) as e:
            messagebox.showerror("Load Error", str(e), parent=self)
            return
        self._apply_task(task)

    def _apply_task(self, task: Task):
        self.prompt_edit.delete("1.0", "end")
        self.prompt_edit.insert("1.0", task.prompt)

        self.system_var.set(bool(task.system))
        self._toggle_system_box()
        self.system_edit.delete("1.0", "end")
        if task.system:
            self.system_edit.insert("1.0", task.system)

        self.lists = dict(task.lists)
        self._refresh_lists_ui()

        self._field_rows = [
            {
                "name_var": tk.StringVar(value=f.name),
                "type_var": tk.StringVar(value=f.type),
                "list_var": tk.StringVar(value=f.list_ref or ""),
            }
            for f in task.output_fields
        ]
        self._refresh_output_fields_ui()

        if self.df is not None:
            for c, v in self.carry_vars.items():
                v.set(c in task.carry_columns)

        self.model_var.set(task.model)
        self.temperature_var.set("" if task.temperature is None else str(task.temperature))
        self.reasoning_var.set(task.reasoning_effort or "")
        self.max_tokens_var.set("" if task.max_output_tokens is None else str(task.max_output_tokens))
        self._refresh_model_params_visibility()

        self._highlight_placeholders(self.prompt_edit)
        if self.system_var.get():
            self._highlight_placeholders(self.system_edit)
