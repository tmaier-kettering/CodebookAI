from __future__ import annotations

import json
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from file_handling.data_conversion import save_as_csv
from file_handling.data_import import import_tabular_data
from prompt_editor.config import (
    AdditionalSourceDefinition,
    OutputDefinition,
    PlaceholderBinding,
    PrimarySourceDefinition,
    PromptTemplateConfig,
)
from prompt_editor.engine import (
    build_additional_source,
    build_primary_source,
    list_available_tokens,
    make_source_id,
    render_prompts_for_row,
    run_live_prompt,
    run_single_test_row,
    submit_batch_prompt,
)
from prompt_editor.presets import get_preset, list_presets
from prompt_editor.storage import delete_template, list_templates, load_template, save_template
from settings.models_registry import get_models, refresh_models
from settings.user_config import get_setting
from ui.batch_operations import refresh_batches_async

REASONING_OPTIONS = ["", "low", "medium", "high"]
DETAIL_OPTIONS = ["", "low", "medium", "high"]


class PlaceholderDialog(simpledialog.Dialog):
    def __init__(self, parent, config: PromptTemplateConfig, binding: PlaceholderBinding | None = None):
        self.config_model = config
        self.binding = binding
        self.result: PlaceholderBinding | None = None
        super().__init__(parent, title="Placeholder Binding")

    def body(self, master):
        ttk.Label(master, text="Token").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Source kind").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Source").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Column").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Render mode").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Constant value").grid(row=5, column=0, sticky="w", padx=8, pady=6)

        self.var_token = tk.StringVar(value="" if self.binding is None else self.binding.token)
        self.var_source_kind = tk.StringVar(value="primary" if self.binding is None else self.binding.source_kind)
        self.var_source_id = tk.StringVar(value="primary" if self.binding is None else self.binding.source_id)
        self.var_column = tk.StringVar(value="" if self.binding is None else (self.binding.column_name or ""))
        self.var_render_mode = tk.StringVar(value="row_value" if self.binding is None else self.binding.render_mode)
        self.var_constant = tk.StringVar(value="" if self.binding is None else (self.binding.constant_value or ""))

        ttk.Entry(master, textvariable=self.var_token, width=28).grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_kind = ttk.Combobox(
            master,
            textvariable=self.var_source_kind,
            values=["primary", "additional", "system"],
            state="readonly",
            width=25,
        )
        self.cmb_kind.grid(row=1, column=1, sticky="ew", padx=8, pady=6)

        self.cmb_source = ttk.Combobox(master, textvariable=self.var_source_id, state="readonly", width=25)
        self.cmb_source.grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_column = ttk.Combobox(master, textvariable=self.var_column, state="readonly", width=25)
        self.cmb_column.grid(row=3, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_mode = ttk.Combobox(
            master,
            textvariable=self.var_render_mode,
            values=["row_value", "full_column", "unique_values", "joined_text", "constant"],
            state="readonly",
            width=25,
        )
        self.cmb_mode.grid(row=4, column=1, sticky="ew", padx=8, pady=6)
        self.ent_constant = ttk.Entry(master, textvariable=self.var_constant, width=28)
        self.ent_constant.grid(row=5, column=1, sticky="ew", padx=8, pady=6)

        master.columnconfigure(1, weight=1)
        self.cmb_kind.bind("<<ComboboxSelected>>", lambda _event: self._refresh_state())
        self.cmb_source.bind("<<ComboboxSelected>>", lambda _event: self._refresh_columns())
        self.cmb_mode.bind("<<ComboboxSelected>>", lambda _event: self._refresh_state())
        self._refresh_state()
        return self.cmb_kind

    def _sources(self) -> list[tuple[str, str, list[str]]]:
        sources = [("primary", self.config_model.primary_source.dataset_name or "primary", self.config_model.primary_source.available_columns)]
        for source in self.config_model.additional_sources:
            sources.append((source.source_id, source.dataset_name, source.available_columns))
        return sources

    def _refresh_columns(self):
        selected = self.var_source_id.get()
        columns = []
        for source_id, _name, available_columns in self._sources():
            if source_id == selected:
                columns = available_columns
                break
        self.cmb_column["values"] = columns
        if columns and self.var_column.get() not in columns:
            self.var_column.set(columns[0])

    def _refresh_state(self):
        source_kind = self.var_source_kind.get()
        if source_kind == "system":
            self.cmb_source["values"] = []
            self.cmb_source.set("")
            self.cmb_column["values"] = []
            self.cmb_column.set("")
            self.cmb_mode.set("constant")
            self.cmb_mode.configure(state="disabled")
            self.cmb_source.configure(state="disabled")
            self.cmb_column.configure(state="disabled")
            self.ent_constant.configure(state="normal")
            return

        self.cmb_mode.configure(state="readonly")
        self.cmb_source.configure(state="readonly")
        self.ent_constant.configure(state="disabled")
        source_values = []
        for source_id, dataset_name, _columns in self._sources():
            if source_kind == "primary" and source_id == "primary":
                source_values.append(source_id)
            elif source_kind == "additional" and source_id != "primary":
                source_values.append(source_id)
        self.cmb_source["values"] = source_values
        if self.var_source_id.get() not in source_values:
            self.var_source_id.set(source_values[0] if source_values else "")
        self.cmb_column.configure(state="readonly")
        self._refresh_columns()

    def validate(self):
        token = self.var_token.get().strip()
        if not token:
            messagebox.showerror("Prompt Editor", "Token is required.", parent=self)
            return False
        if self.var_source_kind.get() != "system":
            if not self.var_source_id.get().strip():
                messagebox.showerror("Prompt Editor", "Source is required.", parent=self)
                return False
            if not self.var_column.get().strip():
                messagebox.showerror("Prompt Editor", "Column is required for non-system bindings.", parent=self)
                return False
        return True

    def apply(self):
        self.result = PlaceholderBinding(
            token=self.var_token.get().strip(),
            source_kind=self.var_source_kind.get().strip(),
            source_id=self.var_source_id.get().strip() or "primary",
            column_name=self.var_column.get().strip() or None,
            render_mode=self.var_render_mode.get().strip(),
            constant_value=self.var_constant.get(),
        )


class OutputDialog(simpledialog.Dialog):
    def __init__(self, parent, config: PromptTemplateConfig, output_def: OutputDefinition | None = None):
        self.config_model = config
        self.output_def = output_def
        self.result: OutputDefinition | None = None
        super().__init__(parent, title="Output Field")

    def body(self, master):
        ttk.Label(master, text="Name").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Source type").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Field type").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Required").grid(row=3, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Instructions").grid(row=4, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="Enum source").grid(row=5, column=0, sticky="w", padx=8, pady=6)
        ttk.Label(master, text="System value").grid(row=6, column=0, sticky="w", padx=8, pady=6)

        self.var_name = tk.StringVar(value="" if self.output_def is None else self.output_def.name)
        self.var_source_type = tk.StringVar(value="model_output" if self.output_def is None else self.output_def.source_type)
        self.var_field_type = tk.StringVar(value="text" if self.output_def is None else self.output_def.field_type)
        self.var_required = tk.BooleanVar(value=True if self.output_def is None else self.output_def.required)
        self.var_instructions = tk.StringVar(value="" if self.output_def is None else self.output_def.instructions)
        self.var_enum_source = tk.StringVar(
            value=""
            if self.output_def is None or not self.output_def.enum_source_id
            else f"{self.output_def.enum_source_id}:{self.output_def.enum_source_column or ''}"
        )
        self.var_system_value = tk.StringVar(value="" if self.output_def is None else (self.output_def.system_value or ""))

        ttk.Entry(master, textvariable=self.var_name, width=28).grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_source_type = ttk.Combobox(
            master,
            textvariable=self.var_source_type,
            values=["model_output", "system"],
            state="readonly",
            width=25,
        )
        self.cmb_source_type.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_field_type = ttk.Combobox(
            master,
            textvariable=self.var_field_type,
            values=["enum", "text", "integer", "boolean", "list[str]"],
            state="readonly",
            width=25,
        )
        self.cmb_field_type.grid(row=2, column=1, sticky="ew", padx=8, pady=6)
        ttk.Checkbutton(master, variable=self.var_required).grid(row=3, column=1, sticky="w", padx=8, pady=6)
        ttk.Entry(master, textvariable=self.var_instructions, width=28).grid(row=4, column=1, sticky="ew", padx=8, pady=6)
        self.cmb_enum_source = ttk.Combobox(master, textvariable=self.var_enum_source, state="readonly", width=25)
        self.cmb_enum_source.grid(row=5, column=1, sticky="ew", padx=8, pady=6)
        ttk.Entry(master, textvariable=self.var_system_value, width=28).grid(row=6, column=1, sticky="ew", padx=8, pady=6)

        master.columnconfigure(1, weight=1)
        self.cmb_source_type.bind("<<ComboboxSelected>>", lambda _event: self._refresh_state())
        self.cmb_field_type.bind("<<ComboboxSelected>>", lambda _event: self._refresh_state())
        self._refresh_state()
        return self.cmb_source_type

    def _refresh_state(self):
        enum_values = []
        sources = [self.config_model.primary_source] + self.config_model.additional_sources
        for source in sources:
            for column in source.available_columns:
                enum_values.append(f"{source.source_id}:{column}")
        self.cmb_enum_source["values"] = enum_values

        is_system = self.var_source_type.get() == "system"
        allows_enum = self.var_field_type.get() in {"enum", "list[str]"} and not is_system
        self.cmb_enum_source.configure(state="readonly" if allows_enum else "disabled")
        if not allows_enum:
            self.var_enum_source.set("")

    def validate(self):
        if not self.var_name.get().strip():
            messagebox.showerror("Prompt Editor", "Output name is required.", parent=self)
            return False
        if self.var_source_type.get() == "system" and not self.var_system_value.get():
            messagebox.showerror("Prompt Editor", "System outputs need a value.", parent=self)
            return False
        if self.var_field_type.get() == "enum" and not self.var_enum_source.get():
            messagebox.showerror("Prompt Editor", "Enum outputs need an enum source.", parent=self)
            return False
        return True

    def apply(self):
        enum_source_id = None
        enum_source_column = None
        if self.var_enum_source.get():
            enum_source_id, enum_source_column = self.var_enum_source.get().split(":", 1)

        self.result = OutputDefinition(
            name=self.var_name.get().strip(),
            source_type=self.var_source_type.get().strip(),
            field_type=self.var_field_type.get().strip(),
            required=self.var_required.get(),
            instructions=self.var_instructions.get().strip(),
            enum_source_id=enum_source_id,
            enum_source_column=enum_source_column or None,
            system_value=self.var_system_value.get() if self.var_source_type.get() == "system" else None,
        )


class PromptEditorWindow(tk.Toplevel):
    def __init__(self, parent: tk.Misc, initial_config: PromptTemplateConfig | None = None):
        super().__init__(parent)
        self.title("Prompt Editor")
        self.transient(parent)
        self.geometry("1200x860")

        self.current_config = initial_config.model_copy(deep=True) if initial_config else PromptTemplateConfig(
            template_name="Untitled Prompt",
            model=get_setting("model", "gpt-4o-mini"),
            user_prompt_template="<quote>",
        )
        self._last_prompt_widget = None

        self._build_ui()
        self._apply_config_to_ui(self.current_config)

    def _build_ui(self):
        root = ttk.Frame(self, padding=12)
        root.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        top = ttk.Frame(root)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        for column in range(8):
            top.columnconfigure(column, weight=1 if column in {1, 4} else 0)

        ttk.Label(top, text="Template").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.var_template_name = tk.StringVar()
        ttk.Entry(top, textvariable=self.var_template_name, width=28).grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(top, text="Presets").grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.var_preset = tk.StringVar()
        self.cmb_preset = ttk.Combobox(
            top,
            textvariable=self.var_preset,
            values=[label for _preset_id, label in list_presets()],
            state="readonly",
            width=30,
        )
        self.cmb_preset.grid(row=0, column=3, sticky="ew", padx=(0, 6))
        ttk.Button(top, text="Load Preset", command=self._load_selected_preset).grid(row=0, column=4, sticky="w", padx=(0, 12))

        ttk.Label(top, text="Saved").grid(row=0, column=5, sticky="w", padx=(0, 6))
        self.var_saved_template = tk.StringVar()
        self.cmb_saved_templates = ttk.Combobox(top, textvariable=self.var_saved_template, state="readonly", width=28)
        self.cmb_saved_templates.grid(row=0, column=6, sticky="ew", padx=(0, 6))
        ttk.Button(top, text="Load", command=self._load_selected_template).grid(row=0, column=7, sticky="w")

        second = ttk.Frame(root)
        second.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(second, text="Save Template", command=self._save_template).pack(side="left")
        ttk.Button(second, text="Delete Template", command=self._delete_template).pack(side="left", padx=6)
        ttk.Button(second, text="Close", command=self.destroy).pack(side="right")

        self.notebook = ttk.Notebook(root)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self.sources_tab = ttk.Frame(self.notebook, padding=10)
        self.prompt_tab = ttk.Frame(self.notebook, padding=10)
        self.outputs_tab = ttk.Frame(self.notebook, padding=10)
        self.review_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.sources_tab, text="Sources")
        self.notebook.add(self.prompt_tab, text="Prompt")
        self.notebook.add(self.outputs_tab, text="Outputs")
        self.notebook.add(self.review_tab, text="Review & Run")

        self._build_sources_tab()
        self._build_prompt_tab()
        self._build_outputs_tab()
        self._build_review_tab()
        self._refresh_templates_menu()

    def _build_sources_tab(self):
        self.sources_tab.columnconfigure(0, weight=1)
        self.sources_tab.columnconfigure(1, weight=1)
        self.sources_tab.rowconfigure(2, weight=1)

        primary_frame = ttk.LabelFrame(self.sources_tab, text="Primary source")
        primary_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        primary_frame.columnconfigure(1, weight=1)

        ttk.Button(primary_frame, text="Import primary dataset", command=self._import_primary_source).grid(
            row=0, column=0, padx=8, pady=8, sticky="w"
        )
        ttk.Button(primary_frame, text="Reload file", command=self._reload_primary_source).grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )

        self.lbl_primary_summary = ttk.Label(primary_frame, text="No primary dataset loaded.")
        self.lbl_primary_summary.grid(row=1, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 8))

        ttk.Label(primary_frame, text="Passthrough columns").grid(row=2, column=0, sticky="nw", padx=8, pady=4)
        self.lst_passthrough = tk.Listbox(primary_frame, selectmode="extended", exportselection=False, height=7)
        self.lst_passthrough.grid(row=2, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(primary_frame, text="Apply passthrough selection", command=self._apply_passthrough_columns).grid(
            row=3, column=1, sticky="w", padx=8, pady=(0, 8)
        )

        addl_frame = ttk.LabelFrame(self.sources_tab, text="Additional sources")
        addl_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        addl_frame.columnconfigure(0, weight=1)
        addl_frame.rowconfigure(0, weight=1)
        self.tree_sources = ttk.Treeview(
            addl_frame,
            columns=("source_id", "dataset", "column", "mode", "rows"),
            show="headings",
            height=10,
        )
        for column, heading in {
            "source_id": "Source ID",
            "dataset": "Dataset",
            "column": "Column",
            "mode": "Mode",
            "rows": "Rows",
        }.items():
            self.tree_sources.heading(column, text=heading)
            self.tree_sources.column(column, width=120, anchor="w")
        self.tree_sources.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        source_buttons = ttk.Frame(addl_frame)
        source_buttons.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(source_buttons, text="Add source", command=self._add_additional_source).pack(side="left")
        ttk.Button(source_buttons, text="Reload source", command=self._reload_selected_source).pack(side="left", padx=6)
        ttk.Button(source_buttons, text="Remove source", command=self._remove_selected_source).pack(side="left")

        placeholder_frame = ttk.LabelFrame(self.sources_tab, text="Placeholder bindings")
        placeholder_frame.grid(row=1, column=1, rowspan=2, sticky="nsew")
        placeholder_frame.columnconfigure(0, weight=1)
        placeholder_frame.rowconfigure(0, weight=1)
        self.tree_bindings = ttk.Treeview(
            placeholder_frame,
            columns=("token", "kind", "source", "column", "mode"),
            show="headings",
            height=18,
        )
        for column, heading in {
            "token": "Token",
            "kind": "Kind",
            "source": "Source",
            "column": "Column",
            "mode": "Mode",
        }.items():
            self.tree_bindings.heading(column, text=heading)
            self.tree_bindings.column(column, width=110, anchor="w")
        self.tree_bindings.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        binding_buttons = ttk.Frame(placeholder_frame)
        binding_buttons.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 8))
        ttk.Button(binding_buttons, text="Add binding", command=self._add_binding).pack(side="left")
        ttk.Button(binding_buttons, text="Edit binding", command=self._edit_binding).pack(side="left", padx=6)
        ttk.Button(binding_buttons, text="Remove binding", command=self._remove_binding).pack(side="left")

    def _build_prompt_tab(self):
        self.prompt_tab.columnconfigure(0, weight=1)
        self.prompt_tab.rowconfigure(1, weight=1)
        self.prompt_tab.rowconfigure(3, weight=1)

        ttk.Label(self.prompt_tab, text="System prompt").grid(row=0, column=0, sticky="w")
        self.txt_system = tk.Text(self.prompt_tab, height=10, wrap="word")
        self.txt_system.grid(row=1, column=0, sticky="nsew", pady=(4, 6))
        ttk.Button(self.prompt_tab, text="Insert Placeholder", command=lambda: self._insert_placeholder(self.txt_system)).grid(
            row=1, column=1, sticky="n", padx=(8, 0)
        )

        ttk.Label(self.prompt_tab, text="User prompt template").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.txt_user = tk.Text(self.prompt_tab, height=14, wrap="word")
        self.txt_user.grid(row=3, column=0, sticky="nsew", pady=(4, 6))
        ttk.Button(self.prompt_tab, text="Insert Placeholder", command=lambda: self._insert_placeholder(self.txt_user)).grid(
            row=3, column=1, sticky="n", padx=(8, 0)
        )

    def _build_outputs_tab(self):
        self.outputs_tab.columnconfigure(0, weight=1)
        self.outputs_tab.rowconfigure(0, weight=1)
        self.tree_outputs = ttk.Treeview(
            self.outputs_tab,
            columns=("name", "source", "field_type", "required", "details"),
            show="headings",
            height=18,
        )
        for column, heading in {
            "name": "Name",
            "source": "Source type",
            "field_type": "Field type",
            "required": "Required",
            "details": "Details",
        }.items():
            self.tree_outputs.heading(column, text=heading)
            self.tree_outputs.column(column, width=160, anchor="w")
        self.tree_outputs.grid(row=0, column=0, sticky="nsew")

        buttons = ttk.Frame(self.outputs_tab)
        buttons.grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Button(buttons, text="Add output", command=self._add_output).pack(side="left")
        ttk.Button(buttons, text="Edit output", command=self._edit_output).pack(side="left", padx=6)
        ttk.Button(buttons, text="Remove output", command=self._remove_output).pack(side="left")

    def _build_review_tab(self):
        self.review_tab.columnconfigure(0, weight=1)
        self.review_tab.rowconfigure(1, weight=1)

        controls = ttk.Frame(self.review_tab)
        controls.grid(row=0, column=0, sticky="ew")
        for column in range(8):
            controls.columnconfigure(column, weight=1 if column in {1, 3, 5} else 0)

        ttk.Label(controls, text="Model").grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.var_model = tk.StringVar()
        self.cmb_model = ttk.Combobox(controls, textvariable=self.var_model, values=get_models(), state="readonly")
        self.cmb_model.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="↻", width=3, command=self._refresh_models).grid(row=0, column=2, sticky="w", padx=(0, 8))

        ttk.Label(controls, text="Default mode").grid(row=0, column=3, sticky="w", padx=(0, 6))
        self.var_execution_mode = tk.StringVar(value="live")
        mode_frame = ttk.Frame(controls)
        mode_frame.grid(row=0, column=4, sticky="w", padx=(0, 8))
        ttk.Radiobutton(mode_frame, text="Live", value="live", variable=self.var_execution_mode).pack(side="left")
        ttk.Radiobutton(mode_frame, text="Batch", value="batch", variable=self.var_execution_mode).pack(side="left", padx=(6, 0))

        advanced = ttk.LabelFrame(self.review_tab, text="Advanced")
        advanced.grid(row=2, column=0, sticky="ew", pady=(8, 8))
        for column in range(8):
            advanced.columnconfigure(column, weight=1 if column % 2 == 1 else 0)

        ttk.Label(advanced, text="Temperature").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        self.var_temperature = tk.StringVar()
        ttk.Entry(advanced, textvariable=self.var_temperature, width=10).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        ttk.Label(advanced, text="Max output tokens").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        self.var_max_output_tokens = tk.StringVar()
        ttk.Entry(advanced, textvariable=self.var_max_output_tokens, width=10).grid(row=0, column=3, sticky="w", padx=8, pady=6)
        ttk.Label(advanced, text="Reasoning").grid(row=0, column=4, sticky="w", padx=8, pady=6)
        self.var_reasoning = tk.StringVar()
        ttk.Combobox(advanced, textvariable=self.var_reasoning, values=REASONING_OPTIONS, state="readonly", width=12).grid(
            row=0, column=5, sticky="w", padx=8, pady=6
        )
        ttk.Label(advanced, text="Detail level").grid(row=0, column=6, sticky="w", padx=8, pady=6)
        self.var_detail = tk.StringVar()
        ttk.Combobox(advanced, textvariable=self.var_detail, values=DETAIL_OPTIONS, state="readonly", width=12).grid(
            row=0, column=7, sticky="w", padx=8, pady=6
        )

        ttk.Label(self.review_tab, text="Preview / test output").grid(row=3, column=0, sticky="w")
        self.txt_preview = tk.Text(self.review_tab, height=20, wrap="word")
        self.txt_preview.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        buttons = ttk.Frame(self.review_tab)
        buttons.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(buttons, text="Render Preview", command=self._render_preview).pack(side="left")
        ttk.Button(buttons, text="Test First Row", command=self._run_test_row).pack(side="left", padx=6)
        ttk.Button(buttons, text="Run Live", command=self._run_live).pack(side="left", padx=6)
        ttk.Button(buttons, text="Run Batch", command=self._run_batch).pack(side="left", padx=6)

    def _refresh_templates_menu(self):
        template_names = [template.template_name for template in list_templates()]
        self.cmb_saved_templates["values"] = template_names

    def _apply_config_to_ui(self, config: PromptTemplateConfig):
        self.current_config = config.model_copy(deep=True)
        self.var_template_name.set(self.current_config.template_name)
        self.var_model.set(self.current_config.model)
        self.var_execution_mode.set(self.current_config.execution_mode)
        self.var_temperature.set("" if self.current_config.advanced.temperature is None else str(self.current_config.advanced.temperature))
        self.var_max_output_tokens.set(
            "" if self.current_config.advanced.max_output_tokens is None else str(self.current_config.advanced.max_output_tokens)
        )
        self.var_reasoning.set(self.current_config.advanced.reasoning_effort or "")
        self.var_detail.set(self.current_config.advanced.detail_level or "")

        self.txt_system.delete("1.0", "end")
        self.txt_system.insert("1.0", self.current_config.system_prompt)
        self.txt_user.delete("1.0", "end")
        self.txt_user.insert("1.0", self.current_config.user_prompt_template)

        self._refresh_primary_source_ui()
        self._refresh_sources_tree()
        self._refresh_bindings_tree()
        self._sync_passthrough_outputs()
        self._refresh_outputs_tree()
        self._refresh_templates_menu()

    def _config_from_ui(self) -> PromptTemplateConfig:
        temperature = self.var_temperature.get().strip()
        max_output_tokens = self.var_max_output_tokens.get().strip()
        config = self.current_config.model_copy(deep=True)
        config.template_name = self.var_template_name.get().strip() or "Untitled Prompt"
        config.model = self.var_model.get().strip() or get_setting("model", "gpt-4o-mini")
        config.execution_mode = self.var_execution_mode.get().strip() or "live"
        config.system_prompt = self.txt_system.get("1.0", "end-1c")
        config.user_prompt_template = self.txt_user.get("1.0", "end-1c")
        config.advanced.temperature = float(temperature) if temperature else None
        config.advanced.max_output_tokens = int(max_output_tokens) if max_output_tokens else None
        config.advanced.reasoning_effort = self.var_reasoning.get().strip() or None
        config.advanced.detail_level = self.var_detail.get().strip() or None
        return config

    def _refresh_primary_source_ui(self):
        primary = self.current_config.primary_source
        if not primary.rows:
            self.lbl_primary_summary.configure(text="No primary dataset loaded.")
            self.lst_passthrough.delete(0, "end")
            return

        self.lbl_primary_summary.configure(
            text=(
                f"{primary.dataset_name} | rows: {len(primary.rows)} | "
                f"prompt column: {primary.selected_column}"
            )
        )
        self.lst_passthrough.delete(0, "end")
        for column in primary.available_columns:
            self.lst_passthrough.insert("end", column)
            if column in primary.passthrough_columns:
                self.lst_passthrough.selection_set("end")

    def _refresh_sources_tree(self):
        self.tree_sources.delete(*self.tree_sources.get_children())
        for index, source in enumerate(self.current_config.additional_sources):
            self.tree_sources.insert(
                "",
                "end",
                iid=str(index),
                values=(source.source_id, source.dataset_name, source.selected_column, source.render_mode, len(source.rows)),
            )

    def _refresh_bindings_tree(self):
        self.tree_bindings.delete(*self.tree_bindings.get_children())
        for index, binding in enumerate(self.current_config.placeholder_bindings):
            self.tree_bindings.insert(
                "",
                "end",
                iid=str(index),
                values=(binding.token, binding.source_kind, binding.source_id, binding.column_name or "", binding.render_mode),
            )

    def _refresh_outputs_tree(self):
        self.tree_outputs.delete(*self.tree_outputs.get_children())
        for index, output_def in enumerate(self.current_config.output_definitions):
            detail = output_def.enum_source_id or output_def.passthrough_column or output_def.system_value or ""
            self.tree_outputs.insert(
                "",
                "end",
                iid=str(index),
                values=(output_def.name, output_def.source_type, output_def.field_type, "yes" if output_def.required else "no", detail),
            )

    def _sync_passthrough_outputs(self):
        manual_outputs = [output for output in self.current_config.output_definitions if output.source_type != "passthrough"]
        passthrough_outputs = [
            OutputDefinition(
                name=column,
                source_type="passthrough",
                field_type="text",
                required=True,
                passthrough_column=column,
            )
            for column in self.current_config.primary_source.passthrough_columns
        ]
        self.current_config.output_definitions = manual_outputs + passthrough_outputs

    def _load_selected_preset(self):
        label = self.var_preset.get().strip()
        if not label:
            return
        preset_lookup = {display: preset_id for preset_id, display in list_presets()}
        preset_id = preset_lookup[label]
        self._apply_config_to_ui(get_preset(preset_id))

    def _load_selected_template(self):
        template_name = self.var_saved_template.get().strip()
        if not template_name:
            return
        template = load_template(template_name)
        if template is None:
            messagebox.showerror("Prompt Editor", "Saved template could not be loaded.", parent=self)
            return
        self._apply_config_to_ui(template)

    def _save_template(self):
        try:
            config = self._config_from_ui()
            save_template(config)
            self.current_config = config
            self._refresh_templates_menu()
            self.var_saved_template.set(config.template_name)
            messagebox.showinfo("Prompt Editor", "Template saved.", parent=self)
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)

    def _delete_template(self):
        template_name = self.var_template_name.get().strip()
        if not template_name:
            return
        delete_template(template_name)
        self._refresh_templates_menu()
        messagebox.showinfo("Prompt Editor", "Template deleted.", parent=self)

    def _import_primary_source(self):
        imported = import_tabular_data(self, "Select the primary row dataset")
        if imported is None:
            return
        self.current_config.primary_source = build_primary_source(imported)
        if not any(binding.source_id == "primary" for binding in self.current_config.placeholder_bindings):
            self.current_config.placeholder_bindings.append(
                PlaceholderBinding(
                    token=make_source_id(imported.selected_column_name) or "quote",
                    source_id="primary",
                    source_kind="primary",
                    column_name=imported.selected_column_name,
                    render_mode="row_value",
                )
            )
        else:
            for binding in self.current_config.placeholder_bindings:
                if binding.source_id == "primary" and binding.source_kind == "primary" and not binding.column_name:
                    binding.column_name = imported.selected_column_name
        self._refresh_primary_source_ui()
        self._sync_passthrough_outputs()
        self._refresh_outputs_tree()
        self._refresh_bindings_tree()

    def _reload_primary_source(self):
        primary = self.current_config.primary_source
        if not primary.file_path:
            return
        imported = import_tabular_data(self, "Reload primary row dataset")
        if imported is None:
            return
        self.current_config.primary_source = build_primary_source(imported, passthrough_columns=primary.passthrough_columns)
        self._refresh_primary_source_ui()

    def _apply_passthrough_columns(self):
        selected = [self.lst_passthrough.get(index) for index in self.lst_passthrough.curselection()]
        self.current_config.primary_source.passthrough_columns = selected
        self._sync_passthrough_outputs()
        self._refresh_outputs_tree()

    def _add_additional_source(self):
        imported = import_tabular_data(self, "Select an additional source")
        if imported is None:
            return
        source_id = make_source_id(imported.dataset_name)
        existing_ids = {source.source_id for source in self.current_config.additional_sources}
        suffix = 2
        base_id = source_id
        while source_id in existing_ids or source_id == "primary":
            source_id = f"{base_id}-{suffix}"
            suffix += 1
        source = build_additional_source(imported, source_id=source_id)
        self.current_config.additional_sources.append(source)
        if not any(binding.source_id == source.source_id for binding in self.current_config.placeholder_bindings):
            self.current_config.placeholder_bindings.append(
                PlaceholderBinding(
                    token=source.source_id.replace("-", "_"),
                    source_id=source.source_id,
                    source_kind="additional",
                    column_name=source.selected_column,
                    render_mode=source.render_mode,
                )
            )
        self._refresh_sources_tree()
        self._refresh_bindings_tree()

    def _reload_selected_source(self):
        selection = self.tree_sources.selection()
        if not selection:
            return
        index = int(selection[0])
        imported = import_tabular_data(self, "Reload additional source")
        if imported is None:
            return
        existing = self.current_config.additional_sources[index]
        self.current_config.additional_sources[index] = build_additional_source(
            imported,
            source_id=existing.source_id,
            render_mode=existing.render_mode,
        )
        self._refresh_sources_tree()
        self._refresh_bindings_tree()

    def _remove_selected_source(self):
        selection = self.tree_sources.selection()
        if not selection:
            return
        index = int(selection[0])
        removed = self.current_config.additional_sources.pop(index)
        self.current_config.placeholder_bindings = [
            binding for binding in self.current_config.placeholder_bindings if binding.source_id != removed.source_id
        ]
        self._refresh_sources_tree()
        self._refresh_bindings_tree()

    def _add_binding(self):
        dialog = PlaceholderDialog(self, self._config_from_ui())
        if dialog.result is None:
            return
        self.current_config.placeholder_bindings.append(dialog.result)
        self._refresh_bindings_tree()

    def _edit_binding(self):
        selection = self.tree_bindings.selection()
        if not selection:
            return
        index = int(selection[0])
        dialog = PlaceholderDialog(self, self._config_from_ui(), self.current_config.placeholder_bindings[index])
        if dialog.result is None:
            return
        self.current_config.placeholder_bindings[index] = dialog.result
        self._refresh_bindings_tree()

    def _remove_binding(self):
        selection = self.tree_bindings.selection()
        if not selection:
            return
        self.current_config.placeholder_bindings.pop(int(selection[0]))
        self._refresh_bindings_tree()

    def _add_output(self):
        dialog = OutputDialog(self, self._config_from_ui())
        if dialog.result is None:
            return
        self.current_config.output_definitions.append(dialog.result)
        self._sync_passthrough_outputs()
        self._refresh_outputs_tree()

    def _edit_output(self):
        selection = self.tree_outputs.selection()
        if not selection:
            return
        index = int(selection[0])
        output_def = self.current_config.output_definitions[index]
        if output_def.source_type == "passthrough":
            messagebox.showinfo(
                "Prompt Editor",
                "Passthrough outputs are managed from the passthrough column selection in Sources.",
                parent=self,
            )
            return
        dialog = OutputDialog(self, self._config_from_ui(), output_def)
        if dialog.result is None:
            return
        self.current_config.output_definitions[index] = dialog.result
        self._sync_passthrough_outputs()
        self._refresh_outputs_tree()

    def _remove_output(self):
        selection = self.tree_outputs.selection()
        if not selection:
            return
        index = int(selection[0])
        if self.current_config.output_definitions[index].source_type == "passthrough":
            messagebox.showinfo(
                "Prompt Editor",
                "Remove passthrough outputs by changing the passthrough column selection in Sources.",
                parent=self,
            )
            return
        self.current_config.output_definitions.pop(index)
        self._refresh_outputs_tree()

    def _insert_placeholder(self, target_widget: tk.Text):
        tokens = list_available_tokens(self.current_config)
        if not tokens:
            messagebox.showinfo("Prompt Editor", "Add a placeholder binding first.", parent=self)
            return
        token = simpledialog.askstring(
            "Insert Placeholder",
            "Available tokens:\n" + "\n".join(f"<{token_name}>" for token_name in tokens) + "\n\nType the token name to insert:",
            parent=self,
        )
        if not token:
            return
        token = token.strip().strip("<>")
        if token not in tokens:
            messagebox.showerror("Prompt Editor", f"<{token}> is not a known placeholder.", parent=self)
            return
        target_widget.insert("insert", f"<{token}>")

    def _refresh_models(self):
        try:
            models = refresh_models()
            self.cmb_model["values"] = models
            if models and self.var_model.get() not in models:
                self.var_model.set(models[0])
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)

    def _write_preview(self, text: str):
        self.txt_preview.delete("1.0", "end")
        self.txt_preview.insert("1.0", text)

    def _render_preview(self):
        try:
            config = self._config_from_ui()
            system_prompt, user_prompt = render_prompts_for_row(config)
            preview = f"System prompt:\n{system_prompt or '(none)'}\n\nUser prompt:\n{user_prompt}"
            self._write_preview(preview)
            self.notebook.select(self.review_tab)
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)

    def _run_test_row(self):
        try:
            config = self._config_from_ui()
            result = run_single_test_row(config)
            self._write_preview(json.dumps(result, indent=2, ensure_ascii=False))
            self.notebook.select(self.review_tab)
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)

    def _run_live(self):
        try:
            config = self._config_from_ui()
            row_count = len(config.primary_source.rows)
            if row_count > config.live_row_warning_threshold:
                proceed = messagebox.askyesno(
                    "Prompt Editor",
                    (
                        f"This live run will process {row_count} rows. "
                        f"Batch mode is recommended above {config.live_row_warning_threshold} rows.\n\n"
                        "Run live anyway?"
                    ),
                    parent=self,
                )
                if not proceed:
                    return
            df = run_live_prompt(config, parent=self)
            save_as_csv(df)
            self._write_preview(f"Live run complete.\nRows exported: {len(df)}")
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)

    def _run_batch(self):
        try:
            config = self._config_from_ui()
            batch = submit_batch_prompt(config)
            if hasattr(self.master, "tree_ongoing"):
                refresh_batches_async(self.master)
            self._write_preview(f"Batch submitted.\nBatch ID: {batch.id}")
            messagebox.showinfo("Prompt Editor", "Batch submitted.", parent=self)
        except Exception as exc:
            messagebox.showerror("Prompt Editor", str(exc), parent=self)


def open_prompt_editor(parent: tk.Misc, preset_id: str | None = None, execution_mode: str | None = None):
    config = get_preset(preset_id) if preset_id else None
    if config is not None and execution_mode:
        config.execution_mode = execution_mode
    window = PromptEditorWindow(parent, initial_config=config)
    window.grab_set()
    return window
