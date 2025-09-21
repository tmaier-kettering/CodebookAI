from __future__ import annotations

import importlib
import io
import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.apple_theme import AppleTheme
import config  # existing config.py in the same module path


class SettingsWindow(tk.Toplevel):
    """
    A modal-ish settings editor for config.py.
    - Reads current values from the imported config module.
    - Lets user edit and save back to config.py (with a .bak backup).
    - Reloads the config module in-memory after saving.
    """
    def __init__(self, parent: tk.Tk | tk.Toplevel):
        super().__init__(parent)
        self.title("Settings")
        self.transient(parent)   # keep on top of parent
        self.resizable(False, False)
        
        # Apply Apple theme to this window
        style = AppleTheme.apply_theme(self)
        self.configure(bg=AppleTheme.COLORS['grouped_background'])

        # --- State variables ---
        self.var_api_key = tk.StringVar(value=getattr(config, "OPENAI_API_KEY", ""))
        self.var_model = tk.StringVar(value=getattr(config, "model", "gpt-4o"))
        self.var_max_batches = tk.StringVar(value=str(getattr(config, "max_batches", 20)))
        self.var_show_key = tk.BooleanVar(value=False)

        # --- Main container with card styling ---
        main_container = ttk.Frame(self, style='Card.TFrame', padding=AppleTheme.SPACING['xl'])
        main_container.grid(row=0, column=0, sticky="nsew", padx=AppleTheme.SPACING['md'], pady=AppleTheme.SPACING['md'])
        
        # Title
        title_lbl = ttk.Label(main_container, text="Settings", style="Headline.TLabel")
        title_lbl.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, AppleTheme.SPACING['lg']))

        # Form grid with better spacing
        form_frame = ttk.Frame(main_container)
        form_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, AppleTheme.SPACING['lg']))
        form_frame.columnconfigure(1, weight=1)

        # API Key section
        api_label = ttk.Label(form_frame, text="OpenAI API Key", style="Body.TLabel")
        api_label.grid(row=0, column=0, sticky="w", pady=(0, AppleTheme.SPACING['xs']))
        
        api_container = ttk.Frame(form_frame)
        api_container.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, AppleTheme.SPACING['lg']))
        api_container.columnconfigure(0, weight=1)
        
        self.ent_api = ttk.Entry(api_container, textvariable=self.var_api_key, width=50, show="•",
                                font=AppleTheme.get_font('body'))
        self.ent_api.grid(row=0, column=0, sticky="ew", padx=(0, AppleTheme.SPACING['sm']))

        show_key_btn = ttk.Checkbutton(api_container, text="Show", variable=self.var_show_key,
                                      command=self._toggle_api_visibility)
        show_key_btn.grid(row=0, column=1, sticky="w")

        # Model section
        model_label = ttk.Label(form_frame, text="Model", style="Body.TLabel")
        model_label.grid(row=2, column=0, sticky="w", pady=(0, AppleTheme.SPACING['xs']))
        
        self.cmb_model = ttk.Combobox(
            form_frame,
            textvariable=self.var_model,
            width=47,
            values=[
                "gpt-4o",
                "o3",
                "gpt-4o-mini",
                "gpt-5",
                "gpt-5-mini",
                "omni-moderate",  # add/trim as needed
            ],
            state="readonly",
            font=AppleTheme.get_font('body')
        )
        self.cmb_model.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(0, AppleTheme.SPACING['lg']))

        # Max batches section
        max_batch_label = ttk.Label(form_frame, text="Max Batches", style="Body.TLabel")
        max_batch_label.grid(row=4, column=0, sticky="w", pady=(0, AppleTheme.SPACING['xs']))
        
        self.ent_max = ttk.Spinbox(form_frame, from_=1, to=1000, textvariable=self.var_max_batches, 
                                  width=15, font=AppleTheme.get_font('body'))
        self.ent_max.grid(row=5, column=0, sticky="w", pady=(0, AppleTheme.SPACING['lg']))

        # Button container with proper spacing
        btn_container = ttk.Frame(main_container)
        btn_container.grid(row=2, column=0, columnspan=3, sticky="e")

        # Use modern button styles
        reset_btn = ttk.Button(btn_container, text="Reset", style="Secondary.TButton",
                              command=self._reset_from_file)
        reset_btn.grid(row=0, column=0, padx=(0, AppleTheme.SPACING['sm']))
        
        cancel_btn = ttk.Button(btn_container, text="Cancel", style="Secondary.TButton",
                               command=self.destroy)
        cancel_btn.grid(row=0, column=1, padx=(0, AppleTheme.SPACING['sm']))
        
        save_btn = ttk.Button(btn_container, text="Save", style="Accent.TButton",
                             command=self._save)
        save_btn.grid(row=0, column=2)

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
        """Reload config from disk and reset UI fields."""
        try:
            importlib.reload(config)
            self.var_api_key.set(getattr(config, "OPENAI_API_KEY", ""))
            self.var_model.set(getattr(config, "model", "gpt-4o"))
            self.var_max_batches.set(str(getattr(config, "max_batches", 20)))
            messagebox.showinfo("Settings", "Values reset from config.py on disk.")
        except Exception as e:
            messagebox.showerror("Reset Error", str(e))

    def _validate(self) -> tuple[bool, str]:
        # max_batches must be an int >= 1
        try:
            mb = int(self.var_max_batches.get().strip())
            if mb < 1:
                return False, "Max Batches must be at least 1."
        except ValueError:
            return False, "Max Batches must be an integer."
        # API key allowed to be empty (user may rely on env var). No further checks here.
        # model: accept any string; combobox already restricts to listed options if left as-is.
        return True, ""

    def _save(self):
        ok, msg = self._validate()
        if not ok:
            messagebox.showwarning("Invalid Input", msg)
            return

        api_key = self.var_api_key.get()
        model = self.var_model.get()
        max_batches = int(self.var_max_batches.get().strip())

        try:
            self._write_config_file(api_key, model, max_batches)
            importlib.reload(config)
            messagebox.showinfo("Settings", "Saved to config.py successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save settings:\n{e}")

    def _write_config_file(self, api_key: str, model: str, max_batches: int):
        """
        Serialize to Python source and overwrite config.py with a .bak backup.
        """
        cfg_path = Path(getattr(config, "__file__", "config.py")).resolve()
        if cfg_path.suffix == ".pyc":
            # If imported from .pyc only, try the .py alongside it
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
            # If backup fails, we can still try to write, but warn the user
            messagebox.showwarning("Backup Warning", f"Could not create backup: {e}")

        # Prepare new file contents (keep it minimal and explicit)
        # Note: we use repr() for safe quoting.
        buf = io.StringIO()
        buf.write(f"OPENAI_API_KEY = {repr(api_key)}\n")
        buf.write(f"model = {repr(model)}\n")
        buf.write(f"max_batches = {int(max_batches)}\n")
        text = buf.getvalue()

        # Write atomically
        tmp_path = cfg_path.with_suffix(".py.tmp")
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, cfg_path)
