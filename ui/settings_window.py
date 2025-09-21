from __future__ import annotations

import importlib
import io
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from zoneinfo import available_timezones

from settings import config
from settings.secrets_store import save_api_key, load_api_key, clear_api_key


class SettingsWindow(tk.Toplevel):
    """
    A modal-ish settings editor.
    - Reads current values from the config module (non-secrets).
    - Reads/saves the API key via the OS keyring (secrets_store).
    - Writes ONLY non-secret settings back to config.py (model, max_batches).
    """
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)   # keep on top of parent
        self.resizable(False, False)

        # --- State variables ---
        # API key comes from keyring, not config.py
        self.var_api_key = tk.StringVar(value=load_api_key() or "")
        self.var_model = tk.StringVar(value=getattr(config, "model", "gpt-4o"))
        self.var_max_batches = tk.StringVar(value=str(getattr(config, "max_batches", 20)))
        self.var_timezone = tk.StringVar(value=getattr(config, "time_zone", "UTC"))
        self.var_show_key = tk.BooleanVar(value=False)

        # --- Layout ---
        pad = {"padx": 12, "pady": 8}
        frm = ttk.Frame(self, padding=16)
        frm.grid(row=0, column=0, sticky="nsew")

        # API Key
        lbl_api = ttk.Label(frm, text="OpenAI API Key:")
        lbl_api.grid(row=0, column=0, sticky="w", **pad)

        info = tk.Label(
            frm,
            text="ⓘ",
            fg="blue",
            cursor="hand2",
            font=("TkDefaultFont", 10, "underline")
        )
        info.grid(row=0, column=0, sticky="e", padx=(100, 0))  # adjust px as needed
        info.bind(
            "<Button-1>",
            lambda e: os.startfile("https://platform.openai.com/api-keys")
        )

        self.ent_api = ttk.Entry(frm, textvariable=self.var_api_key, width=48, show="•")
        self.ent_api.grid(row=0, column=1, sticky="w", **pad)

        chk = ttk.Checkbutton(
            frm,
            text="Show",
            variable=self.var_show_key,
            command=self._toggle_api_visibility
        )
        chk.grid(row=0, column=2, sticky="w", **pad)

        # Model
        ttk.Label(frm, text="Model:").grid(row=1, column=0, sticky="w", **pad)
        self.cmb_model = ttk.Combobox(
            frm,
            textvariable=self.var_model,
            width=45,
            values=[
                "gpt-4o",
                "o3",
                "gpt-4o-mini",
                "gpt-5",
                "gpt-5-mini",
                "omni-moderate",
            ],
            state="readonly"
        )
        self.cmb_model.grid(row=1, column=1, columnspan=2, sticky="w", **pad)

        # max_batches
        ttk.Label(frm, text="Max Batches:").grid(row=2, column=0, sticky="w", **pad)
        self.ent_max = ttk.Spinbox(frm, from_=1, to=1000, textvariable=self.var_max_batches, width=10)
        self.ent_max.grid(row=2, column=1, sticky="w", **pad)

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=3, column=0, columnspan=3, sticky="e", pady=(12, 0))

        # Timezone
        ttk.Label(frm, text="Time Zone:").grid(row=1, column=0, sticky="w", **pad)
        self.cmb_model = ttk.Combobox(
            frm,
            textvariable=self.var_timezone,
            width=45,
            values=sorted(available_timezones()),
            state="readonly"
        )
        self.cmb_model.grid(row=1, column=1, columnspan=2, sticky="w", **pad)

        ttk.Button(btns, text="Reset to File", command=self._reset_from_file).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Clear Key", command=self._clear_key).grid(row=0, column=1, padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=6)
        ttk.Button(btns, text="Save", style="Accent.TButton", command=self._save).grid(row=0, column=3, padx=6)

        # Make Enter=Save, Esc=Cancel
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
        """Reload non-secret settings from disk and reset UI fields. API key reloads from keyring."""
        try:
            importlib.reload(config)
            self.var_api_key.set(load_api_key() or "")
            self.var_model.set(getattr(config, "model", "gpt-4o"))
            self.var_max_batches.set(str(getattr(config, "max_batches", 20)))
            messagebox.showinfo("Settings", "Values reloaded (key from keyring, others from config.py).")
        except Exception as e:
            messagebox.showerror("Reset Error", str(e))

    def _clear_key(self):
        try:
            clear_api_key()
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
        # API key allowed to be empty here; your app can enforce it at use-time.
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            messagebox.showwarning("Invalid Input", msg)
            return

        api_key = self.var_api_key.get().strip()
        model = self.var_model.get().strip()
        max_batches = int(self.var_max_batches.get().strip())
        time_zone = self.var_timezone.get().strip()

        try:
            # 1) Save secret to secure store
            if api_key:
                save_api_key(api_key)

            # 2) Persist non-secrets to config.py
            self._write_config_file(model, max_batches, time_zone)

            # 3) Reload config for the running process
            importlib.reload(config)

            messagebox.showinfo("Settings", "Saved successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save settings:\n{e}")

    def _write_config_file(self, model: str, max_batches: int, time_zone: str) -> None:
        """
        Serialize non-secret settings and overwrite config.py with a .bak backup.
        Never writes the API key.
        """
        cfg_path = Path(getattr(config, "__file__", "config.py")).resolve()
        if cfg_path.suffix == ".pyc":
            cfg_path = cfg_path.with_suffix(".py")
        if not cfg_path.exists():
            raise FileNotFoundError(f"config.py not found at {cfg_path}")

        # Backup
        bak_path = cfg_path.with_suffix(".py.bak")
        try:
            if bak_path.exists():
                bak_path.unlink()
            cfg_path.replace(bak_path)
        except Exception as e:
            messagebox.showwarning("Backup Warning", f"Could not create backup: {e}")

        # Prepare new file contents (explicit + no secrets)
        buf = io.StringIO()
        buf.write("# Non-secret runtime settings\n")
        buf.write(f"model = {repr(model)}\n")
        buf.write(f"max_batches = {int(max_batches)}\n\n")
        buf.write(f"time_zone = {repr(time_zone)}\n")

        text = buf.getvalue()

        # Write atomically
        tmp_path = cfg_path.with_suffix(".py.tmp")
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, cfg_path)
