"""
Settings configuration window for CodebookAI application.

This module provides a modal settings dialog that allows users to configure:
- OpenAI API key (stored securely in system keyring)
- Maximum number of batch jobs to display
- Timezone for timestamp display

Model selection now lives per-task in the Task Builder (see ui/task_builder.py),
not here.

The settings are split between sensitive data (API keys) stored in the OS keyring
and non-sensitive configuration values stored in the config.py file.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import ttk, messagebox
from zoneinfo import available_timezones
from settings.user_config import get_setting, set_setting
from settings.models_registry import refresh_client
from settings.secrets_store import save_api_key, load_api_key, clear_api_key


class SettingsWindow(tk.Toplevel):
    """
    Modal settings configuration dialog.
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)  # keep on top of parent
        self.resizable(False, False)

        # --- State variables ---
        self.var_api_key = tk.StringVar(value=load_api_key() or "")
        self.var_max_batches = tk.StringVar(value=str(get_setting("max_batches", 20)))
        self.var_timezone = tk.StringVar(value=get_setting("time_zone", "UTC"))
        self.var_show_key = tk.BooleanVar(value=False)

        # --- Layout root frame ---
        pad = {"padx": 12, "pady": 8}
        frm = ttk.Frame(self, padding=16)
        frm.grid(row=0, column=0, sticky="nsew")

        # Column sizing
        frm.columnconfigure(0, weight=0)  # labels
        frm.columnconfigure(1, weight=1)  # main controls
        frm.columnconfigure(2, weight=0)  # trailing controls

        # ---- API Key ----
        lbl_api = ttk.Label(frm, text="OpenAI API Key:")
        lbl_api.grid(row=0, column=0, sticky="w", **pad)

        # Small clickable "info" icon to open key page
        info = tk.Label(
            frm,
            text="ⓘ",
            fg="blue",
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline")
        )
        info.grid(row=0, column=0, sticky="e", padx=(0, 4))
        info.bind("<Button-1>", lambda e: os.startfile("https://platform.openai.com/api-keys"))

        self.ent_api = ttk.Entry(frm, textvariable=self.var_api_key, width=48, show="•")
        self.ent_api.grid(row=0, column=1, sticky="we", **pad)

        chk_show = ttk.Checkbutton(
            frm,
            text="Show",
            variable=self.var_show_key,
            command=self._toggle_api_visibility
        )
        chk_show.grid(row=0, column=2, sticky="w", **pad)

        # ---- Time Zone ----
        ttk.Label(frm, text="Time Zone:").grid(row=1, column=0, sticky="w", **pad)
        self.cmb_timezone = ttk.Combobox(
            frm,
            textvariable=self.var_timezone,
            width=45,
            values=sorted(available_timezones()),
            state="readonly",
        )
        self.cmb_timezone.grid(row=1, column=1, columnspan=2, sticky="w", **pad)

        # ---- Max Batches ----
        ttk.Label(frm, text="Max Batches:").grid(row=2, column=0, sticky="w", **pad)
        self.ent_max = ttk.Spinbox(
            frm,
            from_=1,
            to=1000,
            textvariable=self.var_max_batches,
            width=10,
        )
        self.ent_max.grid(row=2, column=1, sticky="w", **pad)

        # ---- Buttons ----
        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=3, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Reset to File", command=self._reset_from_file).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Clear Key", command=self._clear_key).grid(row=0, column=1, padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=6)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self._save).grid(row=0, column=3, padx=6)

        # Keyboard shortcuts
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

        # Center over parent
        self._center_over_parent(parent)

    # ---- helpers ----
    def _center_over_parent(self, parent):
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

    def _toggle_api_visibility(self):
        self.ent_api.config(show="" if self.var_show_key.get() else "•")

    def _reset_from_file(self):
        """Reload settings from defaults and user config, reset UI fields. API key reloads from keyring."""
        try:
            self.var_api_key.set(load_api_key() or "")
            self.var_max_batches.set(str(get_setting("max_batches", 20)))
            self.var_timezone.set(get_setting("time_zone", "UTC"))
        except Exception as e:
            messagebox.showerror("Reset Error", str(e))

    def _clear_key(self):
        try:
            clear_api_key()
            refresh_client()  # Refresh the models registry client
            self.var_api_key.set("")
            messagebox.showinfo("Settings", "API key cleared from secure storage.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear key:\n{e}")

    def _validate(self) -> tuple[bool, str]:
        # max_batches must be an int >= 1
        try:
            mb = int(self.var_max_batches.get().strip())
            if mb < 1:
                return False, "Max Batches must be at least 1."
        except ValueError:
            return False, "Max Batches must be an integer."
        # API key may be empty here; enforce at point-of-use if needed.
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            messagebox.showwarning("Invalid Input", msg)
            return

        api_key = self.var_api_key.get().strip()
        max_batches = int(self.var_max_batches.get().strip())
        time_zone = self.var_timezone.get().strip()

        try:
            # 1) Save secret to secure store
            if api_key:
                save_api_key(api_key)
                # Refresh the models registry client with the new API key
                refresh_client()

            # 2) Save non-secrets to user config (JSON file in user directory)
            set_setting("max_batches", max_batches)
            set_setting("time_zone", time_zone)

            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save settings:\n{e}")
